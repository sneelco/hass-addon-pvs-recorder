"""Recorder module"""

import asyncio
import json
import logging
import os
import signal
import sys
from datetime import datetime
from typing import TYPE_CHECKING

from ess import ESS
from mqtt import MqttClient
from pvs import PVSVars

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

logger = logging.getLogger(__name__)

LIVEDATA_PREFIX = "/sys/livedata/"
DEVICES_PREFIX = "/sys/devices/"

# Livedata values summarized in the periodic log line
LOG_PARAMS = [
    "time",
    "site_load_p",
    "net_p",
    "pv_p",
    "site_load_en",
    "net_en",
    "pv_en",
    "ess_p",
    "ess_en",
    "soc",
]

# Individual vars published as-is. Anything not listed here or under the livedata/devices
# prefixes is ignored (notably /sys/info/ssid and /sys/info/wpa_key, which are secrets).
EXTRA_VARS = {
    "/sys/info/serialnum": "info/serialnum",
    "/sys/info/model": "info/model",
    "/sys/info/hwrev": "info/hwrev",
    "/sys/info/sw_rev": "info/sw_rev",
    "/sys/info/uptime": "info/uptime",
    "/sys/info/sys_type": "info/sys_type",
    "/sys/info/ram_usage": "info/ram_usage",
    "/sys/info/flash_usage": "info/flash_usage",
    "/sys/info/cpu_usage": "info/cpu_usage",
    "/ess/config/dcm/mode_param/control_mode": "ess_config/control_mode",
    "/ess/config/dcm/control_param/min_customer_soc": "ess_config/min_customer_soc",
}


def _sanitize_topic_part(value: str) -> str:
    """Make a value safe to use as a single MQTT topic level"""
    for char in ("/", "+", "#"):
        value = value.replace(char, "_")
    return value.strip() or "unknown"


class Recorder:
    """Manages messages from the PVS and publishes them to an MQTT broker"""

    LOG_INTERVAL = 60
    RESTART_DELAY = 5
    MAX_RESTART_DELAY = 300
    # A poll cycle normally takes seconds; well beyond any backoff means a component is hung
    HANG_TIMEOUT = 600
    WATCHDOG_INTERVAL = 30

    def __init__(self, pvs: PVSVars, mqtt: MqttClient, ess: ESS) -> None:
        """Returns instance of Recorder"""
        self.pvs = pvs
        self.mqtt = mqtt
        self.ess = ess
        self.loop = None

        self.pvs.on_message = self.publish_pvs_data
        self.ess.on_message = self.publish_ess_data

        self.last_log = 0
        self.stopping = False
        self.tasks: list[asyncio.Task] = []

    def publish_pvs_data(self, data: dict[str, str]) -> None:
        """Publish polled PVS vars to the mqtt broker

        - ``/sys/livedata/<key>`` is published to ``<key>`` (same topics the websocket used)
        - ``/sys/devices/<type>/<index>/<field>`` is published to
          ``devices/<type>/<serial>/<field>`` (falls back to the index when no serial)
        - a small set of system info / ESS config vars is published per ``EXTRA_VARS``
        """
        current = datetime.now().timestamp()  # noqa: DTZ005

        livedata: dict[str, str] = {}
        devices: dict[tuple[str, str], dict[str, str]] = {}

        for name, value in data.items():
            if name.startswith(LIVEDATA_PREFIX):
                livedata[name.removeprefix(LIVEDATA_PREFIX)] = value
            elif name.startswith(DEVICES_PREFIX):
                parts = name.removeprefix(DEVICES_PREFIX).split("/")
                if len(parts) != 3:  # noqa: PLR2004
                    continue
                dev_type, index, field = parts
                devices.setdefault((dev_type, index), {})[field] = value
            elif name in EXTRA_VARS:
                self.mqtt.publish(value, EXTRA_VARS[name])

        for key, value in livedata.items():
            self.mqtt.publish(value, _sanitize_topic_part(key))

        for (dev_type, index), fields in devices.items():
            device_id = _sanitize_topic_part(fields.get("sn") or index)
            base = f"devices/{_sanitize_topic_part(dev_type)}/{device_id}"
            for field, value in fields.items():
                self.mqtt.publish(value, f"{base}/{_sanitize_topic_part(field)}")

        msg = f"Published {len(livedata)} livedata values and {len(devices)} devices"
        logger.debug(msg)

        if (current - self.last_log) > self.LOG_INTERVAL:
            msg = ", ".join(f"{p}: {livedata[p]}" for p in LOG_PARAMS if p in livedata)
            logger.info(msg or "No livedata values received from PVS")
            self.last_log = current

    def publish_ess_data(self, data: dict[str, dict]) -> None:
        """Publish ESS data to the mqtt broker

        Values that could not be read (None) are skipped rather than published, so Home
        Assistant keeps the last good value instead of seeing an empty or zero reading.
        """
        published = skipped = 0
        for device, device_data in data.items():
            for key, value in device_data.items():
                if value is None:
                    skipped += 1
                    continue
                if not isinstance(value, (str, bytes, int, float)):
                    value = json.dumps(value, default=str)  # noqa: PLW2901
                topic = f"{device}/{key}"
                self.mqtt.publish(value, topic)
                published += 1
                msg = f"Published {topic} to MQTT: {value}"
                logger.debug(msg)

        msg = f"Published {published} ESS values ({skipped} unavailable)"
        logger.debug(msg)

    async def _supervise(self, name: str, run: "Callable[[], Awaitable[None]]") -> None:
        """Run a component forever, restarting it with a backoff if it crashes or exits"""
        delay = self.RESTART_DELAY
        while not self.stopping:
            started = asyncio.get_running_loop().time()
            try:
                await run()
            except asyncio.CancelledError:
                raise
            except Exception:
                msg = f"{name} crashed, restarting in {delay}s"
                logger.exception(msg)
            else:
                if self.stopping:
                    return
                msg = f"{name} exited unexpectedly, restarting in {delay}s"
                logger.warning(msg)

            # Reset the backoff if the component had been running fine for a while
            if asyncio.get_running_loop().time() - started > self.MAX_RESTART_DELAY:
                delay = self.RESTART_DELAY
            await asyncio.sleep(delay)
            delay = min(delay * 2, self.MAX_RESTART_DELAY)

    async def _watchdog(self) -> None:
        """Exit the process if a poller stops cycling, so the Supervisor restarts the add-on

        The pollers handle their own errors and keep cycling even when their device is
        unreachable, so a stale heartbeat means something is hung (e.g. a blocked Modbus call in
        its worker thread) that cannot be recovered in-process.
        """
        loop = asyncio.get_running_loop()
        started = loop.time()
        while not self.stopping:
            await asyncio.sleep(self.WATCHDOG_INTERVAL)
            now = loop.time()
            for name, component in (("PVS", self.pvs), ("ESS", self.ess)):
                last = component.last_cycle if component.last_cycle is not None else started
                if now - last > self.HANG_TIMEOUT and not self.stopping:
                    msg = (
                        f"{name} poller has not completed a cycle in {int(now - last)}s, "
                        "exiting so the add-on is restarted"
                    )
                    logger.critical(msg)
                    logging.shutdown()
                    # A hung worker thread would block a normal interpreter shutdown
                    os._exit(1)

    async def run(self) -> None:
        """Run the recorder"""
        self.last_log = 0
        self.stopping = False

        self.loop = asyncio.get_running_loop()

        if sys.platform != "win32":
            for sig in (signal.SIGTERM, signal.SIGINT):
                self.loop.add_signal_handler(sig, self._signal_handler)

        msg = (
            f"Polling PVS every {self.pvs.poll_interval} seconds, will log a summary no more "
            f"than once every {self.LOG_INTERVAL} seconds"
        )
        logger.info(msg)

        self.tasks = [
            asyncio.create_task(self._supervise("MQTT", self.mqtt.run)),
            asyncio.create_task(self._supervise("PVS", self.pvs.run)),
            asyncio.create_task(self._supervise("ESS", self.ess.run)),
            asyncio.create_task(self._watchdog()),
        ]

        try:
            await asyncio.gather(*self.tasks)
        except asyncio.CancelledError:
            if not self.stopping:
                raise

        logger.info("Shutdown complete")

    async def _cleanup(self) -> None:
        """Stop all components, then cancel their tasks"""
        self.stopping = True
        components = (("PVS", self.pvs.stop), ("ESS", self.ess.stop), ("MQTT", self.mqtt.stop))
        for name, stop in components:
            try:
                await asyncio.wait_for(stop(), timeout=5)
            except Exception:  # noqa: BLE001
                msg = f"Error stopping {name}"
                logger.warning(msg, exc_info=True)

        for task in self.tasks:
            task.cancel()

    def _signal_handler(self) -> None:
        """Handler for when signals are caught"""
        if self.stopping:
            return
        logger.info("Received shutdown signal")
        self.stopping = True
        self.loop.create_task(self._cleanup())

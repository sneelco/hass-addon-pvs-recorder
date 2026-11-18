"""Recorder module"""

import asyncio
import logging
import signal
import sys
from datetime import datetime

from ess import ESS
from mqtt import MqttClient
from pvs import PVSVars

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

    def __init__(self, pvs: PVSVars, mqtt: MqttClient, ess: ESS) -> None:
        """Returns instance of Recorder"""
        self.pvs = pvs
        self.mqtt = mqtt
        self.ess = ess
        self.loop = None

        self.pvs.on_message = self.publish_pvs_data
        self.ess.on_message = self.publish_ess_data

        self.last_log = 0

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

    def publish_ess_data(self, data: any) -> None:
        """Publish ESS data to the mqtt broker"""
        for device, device_data in data.items():
            for key, value in device_data.items():
                topic = f"{device}/{key}"
                self.mqtt.publish(value, topic)
                msg = f"Published {topic} to MQTT: {value}"
                logger.info(msg)

    async def run(self) -> None:
        """Run the recorder"""
        self.last_log = 0

        self.loop = asyncio.get_running_loop()

        if sys.platform != "win32":
            for sig in (signal.SIGTERM, signal.SIGINT):
                self.loop.add_signal_handler(sig, self._signal_handler)

        msg = (
            f"Polling PVS every {self.pvs.poll_interval} seconds, will log a summary no more "
            f"than once every {self.LOG_INTERVAL} seconds"
        )
        logger.info(msg)

        results = await asyncio.gather(
            self.mqtt.run(),
            self.pvs.run(),
            self.ess.run(),
            return_exceptions=True,
        )

        names = ["MQTT", "PVS", "ESS"]
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                msg = f"{names[i]} task failed: {result}"
                logger.error(msg)

    async def _cleanup(self) -> None:
        """Cleanup PVS and Mqtt and stop the main loop"""
        await self.pvs.stop()
        await self.mqtt.stop()
        await self.ess.stop()
        await asyncio.sleep(5)
        self.loop.stop()

    def _signal_handler(self) -> None:
        """Handler for when signals are caught"""
        logger.info("Received shutdown signal")
        self.loop.create_task(self._cleanup())

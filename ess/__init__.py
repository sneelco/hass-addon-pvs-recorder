"""ESS Module"""

import asyncio
import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING

from .devices import Bms, Gateway, Gateway503, Inverter, Inverter503
from .modbus import ModbusClient

if TYPE_CHECKING:
    from collections.abc import Callable

DEVICE_MAP = {
    "Gateway": {"502": Gateway, "503": Gateway503},
    "Inverter": {"502": Inverter, "503": Inverter503},
    "Bms": {"502": Bms},
}

logger = logging.getLogger(__name__)


class ESS:
    """ESS"""

    POLL_INTERVAL = 5
    MAX_BACKOFF = 60

    def __init__(
        self,
        ess_ip: str,
        ess_port502: int,
        ess_port503: int,
        device_file: str,
    ) -> None:
        """Initialize the ESS"""
        self.ess_ip = ess_ip
        self.ess_port502 = ess_port502
        self.ess_port503 = ess_port503

        with Path.open(device_file, "r") as f:
            self.device_map = json.load(f)

        self.on_message: Callable[[dict], None] | None = None
        self.running = False
        # Event loop time of the last completed poll cycle (success or failure), used by the
        # recorder to detect a hung poller
        self.last_cycle: float | None = None

        self.client502 = ModbusClient(
            ip=self.ess_ip,
            port=self.ess_port502,
        )
        self.client503 = ModbusClient(
            ip=self.ess_ip,
            port=self.ess_port503,
        )

    def _clients(self) -> list[ModbusClient]:
        """Modbus clients needed by the configured devices"""
        ports = {
            port
            for device in self.device_map
            for port in DEVICE_MAP.get(device.get("type"), {})
        }
        clients = []
        if "502" in ports:
            clients.append(self.client502)
        if "503" in ports:
            clients.append(self.client503)
        return clients

    def connect(self) -> None:
        """(Re)connect any Modbus clients that are not connected"""
        for client in self._clients():
            if not client.connected:
                client.connect()

    def _poll(self) -> dict:
        """Blocking connect + query, run in a worker thread"""
        self.connect()
        if not any(client.connected for client in self._clients()):
            msg = f"Could not connect to ESS at {self.ess_ip}"
            raise ConnectionError(msg)

        self.init_devices()
        return self.query_devices()

    async def run(self) -> None:
        """Run the ESS"""
        self.running = True
        failures = 0

        while self.running:
            try:
                # pymodbus is synchronous: run it in a thread so a slow or unreachable ESS
                # cannot stall PVS polling or MQTT
                data = await asyncio.to_thread(self._poll)
                if self.on_message is not None and self.running:
                    self.on_message(data)
                if failures:
                    logger.info("ESS polling recovered")
                failures = 0
            except Exception as e:  # noqa: BLE001
                failures += 1
                msg = f"ESS polling failed ({failures} in a row): {e!r}"
                logger.warning(msg)
                for client in self._clients():
                    client.disconnect()

            self.last_cycle = asyncio.get_running_loop().time()

            if not self.running:
                break
            # Back off when the ESS is unreachable: 5s normally, up to 60s
            await asyncio.sleep(min(self.POLL_INTERVAL * 2**failures, self.MAX_BACKOFF))

    def query_devices(self) -> dict:
        """Query all devices"""
        data = {}
        for device in self.device_map:
            device_data = {}
            for port in ("502", "503"):
                if port not in device:
                    continue
                # One misbehaving device should not prevent the others from being published
                try:
                    device_data.update(device[port].get_data())
                except Exception as e:  # noqa: BLE001
                    msg = f"Failed to read {device.get('name')} on port {port}: {e!r}"
                    logger.warning(msg)

            data[device.get("name")] = device_data

        return data

    def init_devices(self) -> None:
        """Initialize all devices"""
        for device in self.device_map:
            if "502" in DEVICE_MAP.get(device.get("type"), {}) and "502" not in device:
                device["502"] = DEVICE_MAP.get(device["type"])["502"](
                    self.client502,
                    device.get("device_id"),
                )

            if "503" in DEVICE_MAP.get(device.get("type"), {}) and "503" not in device:
                device["503"] = DEVICE_MAP.get(device["type"])["503"](
                    self.client503,
                    device.get("device_id"),
                )

    async def stop(self) -> None:
        """Stop the ESS"""
        self.running = False
        await asyncio.to_thread(self.client502.disconnect)
        await asyncio.to_thread(self.client503.disconnect)

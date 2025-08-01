"""ESS Module"""

import asyncio
import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING

from .devices import Bms, Gateway, Inverter, Inverter503
from .modbus import ModbusClient

if TYPE_CHECKING:
    from collections.abc import Callable

DEVICE_MAP = {
    "Gateway": {"502": Gateway},
    "Inverter": {"502": Inverter, "503": Inverter503},
    "Bms": {"502": Bms},
}

logger = logging.getLogger(__name__)


class ESS:
    """ESS"""

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

        self.on_message: Callable[[str], None] | None = None
        self.running = False

        self.client502 = ModbusClient(
            ip=self.ess_ip,
            port=self.ess_port502,
        )
        self.client503 = ModbusClient(
            ip=self.ess_ip,
            port=self.ess_port503,
        )

    def publish_message(self, data: any) -> None:
        """Publishes a message to the mqtt broker"""
        self.mqtt.publish(data)

    def connect(self) -> None:
        """Connect to the ESS"""
        self.client502.connect()
        self.client503.connect()

    async def run(self) -> None:
        """Run the ESS"""
        self.running = True

        while self.running:
            if not self.client502.connected or not self.client503.connected:
                self.connect()
                self.init_devices()

            data = self.query_devices()
            self.on_message(data)

            if not self.running:
                break
            await asyncio.sleep(5)

    def query_devices(self) -> dict:
        """Query all devices"""
        data = {}
        for device in self.device_map:
            data_502 = device.get("502").get_data() if "502" in device else {}
            data_503 = device.get("503").get_data() if "503" in device else {}

            data[device.get("name")] = {**data_502, **data_503}

        return data

    def init_devices(self) -> None:
        """Initialize all devices"""
        for device in self.device_map:
            if "502" in DEVICE_MAP.get(device.get("type"), None) and "502" not in device:
                device["502"] = DEVICE_MAP.get(device["type"])["502"](
                    self.client502,
                    device.get("device_id"),
                )

            if "503" in DEVICE_MAP.get(device.get("type"), None) and "503" not in device:
                device["503"] = DEVICE_MAP.get(device["type"])["503"](
                    self.client503,
                    device.get("device_id"),
                )

    async def stop(self) -> None:
        """Stop the ESS"""
        self.running = False
        self.client502.disconnect()
        self.client503.disconnect()

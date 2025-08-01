"""Recorder module"""

import asyncio
import json
import logging
import signal
import sys
from datetime import datetime

from ess import ESS
from mqtt import MqttClient
from pvs import PVSWebSocket

logger = logging.getLogger(__name__)

WS_PARAMS = [
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


class Recorder:
    """Manages messages from the PVS and publishes them to an MQTT broker"""

    WS_RECORD_INTERVAL = 10
    WS_LOG_INTERVAL = 60

    def __init__(self, pvsws: PVSWebSocket, mqtt: MqttClient, ess: ESS) -> None:
        """Returns instance of Recorder"""
        self.pvsws = pvsws
        self.mqtt = mqtt
        self.ess = ess
        self.loop = None

        self.pvsws.on_message = self.publish_message
        self.ess.on_message = self.publish_ess_data

        self.last_power = 0
        self.last_record = 0

    def publish_message(self, data: any) -> None:
        """Publishes a message to the mqtt broker"""
        current = datetime.now().timestamp()  # noqa: DTZ005

        try:
            # Parse JSON message
            data = json.loads(data)

        except json.JSONDecodeError as e:
            msg = f"Invalid JSON received: {e}"
            logger.exception(msg)
            msg = f"Raw message: {data}"
            logger.info(msg)
            return

        if data.get("notification") == "power":
            if (current - self.last_record) < self.WS_RECORD_INTERVAL:
                return

            self.last_record = current

            params = data.get("params")
            log_msgs = []

            for param in WS_PARAMS:
                if param in params:
                    self.mqtt.publish(params.get(param, 0), param)
                    log_msgs.append(f"{param}: {params.get(param, 0)}")

            if (current - self.last_power) > self.WS_LOG_INTERVAL:
                msg = ", ".join(log_msgs)
                logger.info(msg)
                self.last_power = current
            return

        # Print formatted JSON to console
        msg = json.dumps(data, indent=2, ensure_ascii=False)
        logger.info(msg)

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
        self.last_power = 0

        self.loop = asyncio.get_running_loop()

        if sys.platform != "win32":
            for sig in (signal.SIGTERM, signal.SIGINT):
                self.loop.add_signal_handler(sig, self._signal_handler)

        if self.WS_LOG_INTERVAL > 0:
            msg = (
                f"WebSocket log supression enabled, will log messages no more then once every "
                f"{self.WS_LOG_INTERVAL} seconds"
            )
            logger.info(msg)

        await asyncio.gather(
            self.mqtt.run(),
            self.pvsws.run(),
            self.ess.run(),
        )

    async def _cleanup(self) -> None:
        """Cleanup PVS and Mqtt and stop the main loop"""
        await self.pvsws.stop()
        await self.mqtt.stop()
        await self.ess.stop()
        await asyncio.sleep(5)
        self.loop.stop()

    def _signal_handler(self) -> None:
        """Handler for when signals are caught"""
        logger.info("Received shutdown signal")
        self.loop.create_task(self._cleanup())

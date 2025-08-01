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
            self.mqtt.publish(params.get("site_load_p", 0), "site_load_p")
            self.mqtt.publish(params.get("net_p", 0), "net_p")
            self.mqtt.publish(params.get("pv_p", 0), "pv_p")
            self.mqtt.publish(params.get("site_load_en", 0), "site_load_en")
            self.mqtt.publish(params.get("net_en", 0), "net_en")
            self.mqtt.publish(params.get("pv_en", 0), "pv_en")

            if (current - self.last_power) > self.WS_LOG_INTERVAL:
                msg = (
                    f"site_load_p: {params.get('site_load_p', 0)}, "
                    f"net_p: {params.get('net_p', 0)}, pv_p: {params.get('pv_p', 0)}, "
                    f"site_load_en: {params.get('site_load_en', 0)}, "
                    f"net_en: {params.get('net_en', 0)}, pv_en: {params.get('pv_en', 0)}"
                )
                logger.info(msg)
                self.last_power = current
            return

        # Print formatted JSON to console
        msg = json.dumps(data, indent=2, ensure_ascii=False)
        logger.info(msg)

    def publish_ess_data(self, data: any) -> None:
        """Publish ESS data to the mqtt broker"""

        for key, value in data.items():
            self.mqtt.publish(json.dumps(value), key, retain=True)
            msg = f"Published {key} to MQTT: {value}"
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

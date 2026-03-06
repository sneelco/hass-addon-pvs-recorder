"""MQTT Module"""

import asyncio
import logging
import sys
from typing import Any

import paho.mqtt.client as mqtt

# Configure logging
logger = logging.getLogger(__name__)
logger.propagate = True


class MqttClient:
    """A class for creating instances of a Mqtt Client"""

    def __init__(self, host, topic, username, password, port=1883) -> None:
        """Returns an instance of MqttClient"""
        self.host = host
        self.port = port
        self.topic = topic
        self.username = username
        self.password = password
        self.is_running = False
        self.client = None
        self.connected = False

    def _on_connect(
        self,
        _client: mqtt.Client,
        _userdata: Any,  # noqa: ANN401
        _flags: dict,
        reason_code: int,
        _properties: Any = None,  # noqa: ANN401
    ) -> None:
        if reason_code == 0:
            logger.info("Connected to MQTT Broker")
            sys.stdout.flush()
            self.connected = True
            # Publish online status
            self.client.publish(topic=f"{self.topic}/status", payload="online", qos=2, retain=True)
        else:
            msg = f"Failed to connect to MQTT broker. Reason code: {reason_code}"
            logger.error(msg)
            self.connected = False

    def _on_disconnect(
        self,
        _client: mqtt.Client,
        _userdata: Any,  # noqa: ANN401
        _disconnect_flags: dict,
        reason_code: int,
        _properties: Any = None,  # noqa: ANN401
    ) -> None:
        """Callback for when the client disconnects from the broker."""
        msg = f"Disconnected from MQTT Broker. Reason code: {reason_code}"
        logger.info(msg)
        self.connected = False

    def _on_publish(
        self,
        _client: mqtt.Client,
        _userdata: Any,  # noqa: ANN401
        mid: int,
        _reason_code: int,
        _properties: Any = None,  # noqa: ANN401
    ) -> None:
        """Callback for when a message is published."""
        msg = f"Published message with ID {mid}"
        logger.debug(msg)

    async def run(self) -> None:
        """Connect to the broker and start the loop"""
        self.is_running = True
        heartbeat_interval = 60
        last_heartbeat = 0

        while self.is_running:
            if self.client and self.connected:
                now = asyncio.get_event_loop().time()
                if (now - last_heartbeat) >= heartbeat_interval:
                    self.client.publish(
                        topic=f"{self.topic}/status",
                        payload="online",
                        qos=2,
                        retain=True,
                    )
                    last_heartbeat = now
                await asyncio.sleep(1)
                continue

            logger.info("Connecting to MQTT Broker...")
            self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
            if self.username is not None:
                self.client.username_pw_set(self.username, self.password)

            self.client.will_set(
                topic=f"{self.topic}/status",
                payload="offline",
                qos=2,
                retain=True,
                properties=None,
            )

            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            self.client.on_publish = self._on_publish

            try:
                self.client.connect(host=self.host, port=self.port, keepalive=60)
                self.client.loop_start()
            except Exception as e:
                msg = f"Failed to connect to MQTT broker: {e}"
                logger.error(msg)
                self.client = None

            await asyncio.sleep(5)

    def publish(
        self,
        message: str,
        topic: str | None = None,
        qos: int = 1,
        retain: bool = False,  # noqa: FBT001, FBT002
    ) -> None:
        """Publish a message"""
        publish_topic = f"{self.topic}/{topic}" if topic is not None else self.topic

        if self.connected:
            self.client.publish(publish_topic, message, qos=qos, retain=retain)
        else:
            logger.error("Could not publish due to MQTT being disconnected")

    async def stop(self) -> None:
        """Disconnect and stop the client"""
        logger.debug("Stopping MQTT client...")
        self.is_running = False

        if self.client and self.connected:
            logger.debug("Publishing offline status...")
            self.client.publish(topic=f"{self.topic}/status", payload="offline", qos=2, retain=True)

            # Wait a moment for the message to be sent
            await asyncio.sleep(0.5)

            self.client.disconnect()
            self.client.loop_stop()
            logger.debug("MQTT client stopped")

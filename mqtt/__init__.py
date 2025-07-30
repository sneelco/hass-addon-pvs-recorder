"""MQTT Module"""

import asyncio
import logging
import sys

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

    def _on_connect(self, *_args: any, **_kwargs) -> None:
        logger.info("Connected to MQTT Broker")
        sys.stdout.flush()
        self.connected = True
        self.client.will_set(topic=f"{self.topic}/status", payload="offline", qos=2, retain=True)
        self.client.publish(topic=f"{self.topic}/status", payload="online", qos=2, retain=True)

    def _on_disconnect(self, *_args: any, **_kwargs) -> None:
        logger.info("Disconnected from MQTT Broker")
        self.client.publish(topic=f"{self.topic}/status", payload="offline", qos=2, retain=True)
        self.connected = False

    async def run(self) -> None:
        """Connect to the broker and start the loop"""
        self.is_running = True

        while self.is_running:
            if self.client and self.connected:
                await asyncio.sleep(1)
                continue

            logger.info("Connecting to MQTT Broker...")
            self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
            if self.username is not None:
                self.client.username_pw_set(self.username, self.password)
            self.client.connect(host=self.host, port=self.port)
            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            self.client.loop_start()
            await asyncio.sleep(1)

    def publish(self, message: str, topic: str | None = None, qos: int = 1) -> None:
        """Publish a message"""
        publish_topic = f"{self.topic}/{topic}" if topic is not None else self.topic

        if self.connected:
            self.client.publish(publish_topic, message, qos=qos)
        else:
            logger.error("Could not publish due to MQTT being disconnected")

    async def stop(self) -> None:
        """Disconnect and stop the client"""
        self.is_running = False

        if self.client and self.connected:
            self.client.disconnect()
            self.client.loop_stop()

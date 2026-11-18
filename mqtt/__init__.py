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

    HEARTBEAT_INTERVAL = 60
    MAX_QUEUED_MESSAGES = 1000

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
        self._dropped = 0

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

    def _create_client(self) -> mqtt.Client:
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        if self.username is not None:
            client.username_pw_set(self.username, self.password)

        client.will_set(
            topic=f"{self.topic}/status",
            payload="offline",
            qos=2,
            retain=True,
            properties=None,
        )

        client.on_connect = self._on_connect
        client.on_disconnect = self._on_disconnect
        client.on_publish = self._on_publish

        # paho's network thread reconnects on its own; cap the backoff and bound the queue of
        # in-flight messages so a long broker outage cannot grow memory without limit
        client.reconnect_delay_set(min_delay=1, max_delay=60)
        client.max_queued_messages_set(self.MAX_QUEUED_MESSAGES)
        return client

    async def run(self) -> None:
        """Connect to the broker and keep the connection alive

        A single client is created for the lifetime of the process. connect_async + loop_start
        hands connection management to paho's network thread, which retries the initial
        connection and reconnects after any disconnect.
        """
        self.is_running = True
        last_heartbeat = 0.0
        loop = asyncio.get_running_loop()

        if self.client is None:
            msg = f"Connecting to MQTT Broker at {self.host}:{self.port}..."
            logger.info(msg)
            self.client = self._create_client()
            self.client.connect_async(host=self.host, port=int(self.port), keepalive=60)
            self.client.loop_start()

        while self.is_running:
            now = loop.time()
            if self.connected and (now - last_heartbeat) >= self.HEARTBEAT_INTERVAL:
                # Re-assert online status in case a retained "offline" (e.g. the will from a
                # previous session) overwrote it
                self.client.publish(
                    topic=f"{self.topic}/status",
                    payload="online",
                    qos=1,
                    retain=True,
                )
                last_heartbeat = now
            await asyncio.sleep(1)

    def publish(
        self,
        message: str,
        topic: str | None = None,
        qos: int = 1,
        retain: bool = False,  # noqa: FBT001, FBT002
    ) -> None:
        """Publish a message"""
        publish_topic = f"{self.topic}/{topic}" if topic is not None else self.topic

        if self.connected and self.client is not None:
            self.client.publish(publish_topic, message, qos=qos, retain=retain)
            self._dropped = 0
            return

        # Drop rather than queue while disconnected, and log once per outage instead of once
        # per message
        if self._dropped == 0:
            logger.warning("MQTT is disconnected, dropping messages until it reconnects")
        self._dropped += 1

    async def stop(self) -> None:
        """Disconnect and stop the client"""
        logger.debug("Stopping MQTT client...")
        self.is_running = False

        if self.client is None:
            return

        if self.connected:
            logger.debug("Publishing offline status...")
            info = self.client.publish(
                topic=f"{self.topic}/status",
                payload="offline",
                qos=1,
                retain=True,
            )
            # Give the network thread a moment to send it
            try:
                await asyncio.to_thread(info.wait_for_publish, 2)
            except (RuntimeError, ValueError) as e:
                msg = f"Could not publish offline status: {e}"
                logger.debug(msg)
            self.client.disconnect()

        self.client.loop_stop()
        self.client = None
        self.connected = False
        logger.debug("MQTT client stopped")

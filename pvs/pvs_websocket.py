"""PVS WebSocket Module"""

import asyncio
import logging
from typing import TYPE_CHECKING, Literal

import websockets

if TYPE_CHECKING:
    from collections.abc import Callable

# Configure logging
logger = logging.getLogger(__name__)


class PVSWebSocket:
    """PVSWebSocket Class"""

    def __init__(
        self,
        host: str,
        port: int,
        ws_secure=Literal["ws", "wss"],
        ws_idle_timeout: int = 60,
        ws_reconnect_delay: int = 5,
    ) -> None:
        """Initialize WebSocket client with auto-reconnect functionality."""
        ws_schema = "wss" if ws_secure == "wss" else "ws"
        self.uri = f"{ws_schema}://{host}:{port}"
        self.idle_timeout = ws_idle_timeout if ws_idle_timeout > 0 else None
        self.reconnect_delay = ws_reconnect_delay
        self.websocket = None
        self.running = False
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = None  # Set to a number to limit attempts
        self.on_message: Callable[[str], None] | None = None

    async def connect(self) -> None:
        """Establish WebSocket connection."""
        try:
            msg = f"Connecting to PVS at {self.uri}..."
            logger.info(msg)
            self.websocket = await websockets.connect(
                self.uri,
                ping_interval=20,  # Send ping every 20 seconds
                ping_timeout=10,  # Wait 10 seconds for pong
                close_timeout=10,
            )
            logger.info("Connected successfully to PVS WebSocket")
            self.reconnect_attempts = 0
        except Exception as e:
            msg = f"Connection failed: {e}"
            logger.exception(msg)

    def is_connected(self) -> None:
        """Check if WebSocket is connected."""
        return self.websocket is not None and self.websocket.state.value == 1  # OPEN state

    async def disconnect(self) -> None:
        """Close WebSocket connection."""
        if self.websocket:
            try:
                await self.websocket.close()
            except Exception as e:
                msg = f"Error during disconnect: {e}"
                logger.exception(msg)
            finally:
                self.websocket = None
                logger.info("Disconnected")

    async def handle_message(self, message: str) -> None:
        """Handle incoming JSON message.

        Override this method to customize message processing.
        """
        if self.on_message is None:
            msg = f"Raw message: {message}"
            logger.info(msg)
            return

        self.on_message(message)

    async def listen(self) -> bool:
        """Listen for messages with timeout handling."""
        try:
            if self.idle_timeout:
                # Listen with timeout
                message = await asyncio.wait_for(self.websocket.recv(), timeout=self.idle_timeout)
            else:
                # Listen without timeout
                message = await self.websocket.recv()

            await self.handle_message(message)

        except TimeoutError:
            msg = f"No messages received for {self.idle_timeout} seconds"
            logger.warning(msg)
            return False
        except websockets.exceptions.ConnectionClosed:
            logger.warning("Connection closed by server")
            return False
        except websockets.exceptions.WebSocketException as e:
            msg = f"WebSocket error: {e}"
            logger.exception(msg)
            return False
        except Exception as e:
            msg = f"Error receiving message: {e}"
            logger.exception()
            return False

        return True

    async def run(self) -> None:
        """Main run loop with auto-reconnect."""
        self.running = True

        while self.running:
            # Check reconnect attempt limit
            if (
                self.max_reconnect_attempts
                and self.reconnect_attempts >= self.max_reconnect_attempts
            ):
                logger.error("Max reconnection attempts reached")
                break

            # Connect if not connected
            if not self.is_connected() and not await self.connect():
                self.reconnect_attempts += 1
                msg = f"Reconnection attempt {self.reconnect_attempts}"
                logger.info(msg)
                await asyncio.sleep(self.reconnect_delay)
                continue

            # Listen for messages
            success = await self.listen()

            if not success:
                # Connection issue, prepare for reconnect
                await self.disconnect()
                if self.running:  # Only reconnect if still running
                    msg = f"Reconnecting in {self.reconnect_delay} seconds..."
                    logger.info(msg)
                    await asyncio.sleep(self.reconnect_delay)

    async def stop(self) -> None:
        """Stop the client gracefully."""
        logger.info("Stopping WebSocket client...")
        self.running = False
        await self.disconnect()


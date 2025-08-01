"""Query the SunPower PVS details from the internal PVS interface"""

import argparse
import asyncio

from pvs.pvs_websocket import PVSWebSocket


def on_message(message: str) -> None:
    """Handle the message"""
    print(message)  # noqa: T201


def main(host: str, ws_port: int) -> None:
    """Main function"""
    pvs_websocket = PVSWebSocket(host, ws_port)
    pvs_websocket.on_message = on_message
    asyncio.run(pvs_websocket.run())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="query_pvs_ws",
        description="Get SunPower PVS details from the internal PVS WebSocket interface",
    )
    parser.add_argument("-H", "--pvs-host", default="172.27.153.1")
    parser.add_argument("-p", "--pvs-ws-port", default="9002")
    args = parser.parse_args()

    main(args.pvs_host, args.pvs_ws_port)

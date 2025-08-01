"""Module for running retrieving data from a SunPower PVS WebSocket and publishing to MQTT"""

import argparse
import asyncio
import logging
import os

from ess import ESS
from mqtt import MqttClient
from pvs import PVSWebSocket
from recorder import Recorder

if __name__ == "__main__":
    # Install required packages:
    # pip install websockets
    parser = argparse.ArgumentParser(
        prog="pvs_recorder",
        description="Get SunPower PVS from the internal PVS interface",
    )
    parser.add_argument("--pvs-host", default=os.environ.get("PVS_HOST", "172.27.153.1"))
    parser.add_argument("--pvs-ws-port", default=os.environ.get("PVS_WS_PORT", "9002"))
    parser.add_argument("--pvs-ws-secure", action="store_true", default=False)
    parser.add_argument("--ess-host", default=os.environ.get("ESS_HOST", "172.27.153.171"))
    parser.add_argument("--ess-port", default=os.environ.get("ESS_PORT", "502"))
    parser.add_argument("--ess-port-503", default=os.environ.get("ESS_PORT_503", "503"))
    parser.add_argument(
        "--ess-device-file",
        default=os.environ.get("ESS_DEVICE_FILE", "ess_devices.json"),
    )
    parser.add_argument("-H", "--mqtt-host", default=os.environ.get("MQTT_HOST", None))
    parser.add_argument("-P", "--mqtt-port", type=int, default=os.environ.get("MQTT_PORT", "1883"))
    parser.add_argument("-t", "--mqtt-topic", default=os.environ.get("MQTT_TOPIC", "pvs"))
    parser.add_argument("-u", "--mqtt-user", default=os.environ.get("MQTT_USER", "frigate"))
    parser.add_argument("-p", "--mqtt-password", default=os.environ.get("MQTT_PASSWORD", "frigate"))
    parser.add_argument("-d", "--debug", action="store_true")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO if not args.debug else logging.DEBUG)
    log_handler = logging.StreamHandler()
    log_formatter = logging.Formatter(
        "%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s",
    )
    log_handler.setFormatter(log_formatter)

    logger = logging.getLogger("sunpower")
    logger.addHandler(log_handler)
    logger.setLevel(logging.INFO)

    if args.debug:
        logger.setLevel(logging.DEBUG)

    pvsws = PVSWebSocket(
        host=args.pvs_host,
        port=args.pvs_ws_port,
        ws_secure="wss" if args.pvs_ws_secure else "ws",
    )

    mqtt = MqttClient(
        host=args.mqtt_host,
        port=args.mqtt_port,
        topic=args.mqtt_topic,
        username=args.mqtt_user,
        password=args.mqtt_password,
    )

    ess = ESS(
        ess_ip=args.ess_host,
        ess_port502=args.ess_port,
        ess_port503=args.ess_port_503,
        device_file=args.ess_device_file,
    )

    recorder = Recorder(pvsws, mqtt, ess)

    asyncio.run(recorder.run())

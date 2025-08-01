"""Test Modbus Client"""

import argparse
import json

from ess.devices.bms import Bms
from ess.devices.gateway import Gateway
from ess.devices.gateway503 import Gateway503
from ess.devices.inverter import Inverter
from ess.devices.inverter503 import Inverter503
from ess.modbus import ModbusClient


def main(host: str, port: int, port503: int) -> None:
    """Main function"""
    client502 = ModbusClient(host, port)
    client503 = ModbusClient(host, port503)

    gateway = Gateway(client502, 1)
    gateway_503 = Gateway503(client503, 1)

    inverter1 = Inverter(client502, 10)
    inverter1_503 = Inverter503(client503, 10)

    inverter2 = Inverter(client502, 11)
    inverter2_503 = Inverter503(client503, 11)

    bms1 = Bms(client502, 230)
    bms2 = Bms(client502, 231)

    try:
        gateway_str = json.dumps(gateway.get_data() | gateway_503.get_data(), indent=4)
        inverter1_str = json.dumps(inverter1.get_data() | inverter1_503.get_data(), indent=4)
        inverter2_str = json.dumps(inverter2.get_data() | inverter2_503.get_data(), indent=4)
        bms1_str = json.dumps(bms1.get_data(), indent=4)
        bms2_str = json.dumps(bms2.get_data(), indent=4)

        output = (
            "Gateway:\n"
            f"{gateway_str}\n"
            "--------------------------------\n"
            "Inverter 1:\n"
            f"{inverter1_str}\n"
            "--------------------------------\n"
            "Inverter 2:\n"
            f"{inverter2_str}\n"
            "--------------------------------\n"
            "BMS 1:\n"
            f"{bms1_str}\n"
            "--------------------------------\n"
            "BMS 2:\n"
            f"{bms2_str}\n"
        )

        print(output)  # noqa: T201

        # Some useful commands
        # inverter1_503.reboot()

        # inverter1_503.set_max_charge_rate(20)
        # inverter2_503.set_max_charge_rate(20)

        # inverter1_503.set_max_sell_amps(0)
        # inverter2_503.set_max_sell_amps(27)

    finally:
        client502.disconnect()
        client503.disconnect()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="pvs_recorder",
        description="Get SunPower PVS from the internal PVS interface",
    )
    parser.add_argument("-H", "--ess-host", default="172.27.153.171")
    parser.add_argument("-p", "--ess-port", default="502")
    parser.add_argument("-P", "--ess-port-503", default="503")
    args = parser.parse_args()

    main(args.ess_host, args.ess_port, args.ess_port_503)

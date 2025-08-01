"""Query the SunPower PVS details from the internal PVS interface"""

import argparse

from pvs.pvs_detail import PVSDetail


def main(host: str, port: int, output_file: str | None) -> None:
    """Main function"""
    pvs_detail = PVSDetail(host, port)
    pvs_detail.get_pvs_detail()
    solar_inverters = pvs_detail.get_solar_inverters()

    for count, panel in enumerate(solar_inverters, start=1):
        print(  # noqa: T201
            f"Panel {count} ({panel.serial}): "
            f"{panel.voltage}V at {panel.current}A for {panel.power}W. "
            f"Total Production: {panel.energy}kWh",
        )

    if output_file:
        pvs_detail.write_data(output_file)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="query_pvs_details",
        description="Get SunPower PVS details from the internal PVS interface",
    )
    parser.add_argument("-H", "--pvs-host", default="172.27.153.1")
    parser.add_argument("-p", "--pvs-port", default="80")
    parser.add_argument("-o", "--output-file", default=None)
    args = parser.parse_args()

    main(args.pvs_host, args.pvs_port, args.output_file)

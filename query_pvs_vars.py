"""Query the SunPower PVS vars endpoint and print the results"""

import argparse
import asyncio
import json
import os

from pvs import PVSVars


async def main(args: argparse.Namespace) -> None:
    """Log in, fetch the vars once and print them as JSON"""
    pvs = PVSVars(
        host=args.pvs_host,
        port=args.pvs_port,
        username=args.pvs_user,
        password=args.pvs_password,
        match=args.match,
    )
    try:
        data = await pvs.fetch()
    finally:
        await pvs.stop()

    print(json.dumps(data, indent=2))  # noqa: T201


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="query_pvs_vars",
        description="Get SunPower PVS vars from the authenticated PVS interface",
    )
    parser.add_argument("-H", "--pvs-host", default=os.environ.get("PVS_HOST", "172.27.153.1"))
    parser.add_argument("-p", "--pvs-port", type=int, default=os.environ.get("PVS_PORT", "443"))
    parser.add_argument("-u", "--pvs-user", default=os.environ.get("PVS_USER", "ssm_owner"))
    parser.add_argument("-P", "--pvs-password", default=os.environ.get("PVS_PASSWORD"))
    parser.add_argument("-m", "--match", default="/", help="vars match prefix, e.g. /sys/livedata")
    args = parser.parse_args()

    if not args.pvs_password:
        parser.error("a PVS password is required (--pvs-password or PVS_PASSWORD)")

    asyncio.run(main(args))

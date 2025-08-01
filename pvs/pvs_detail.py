"""Module for retrieving PVS details from the PVS Supervisor"""

import json
from pathlib import Path

import httpx
from pydantic import BaseModel, computed_field


class PVSMeter(BaseModel):
    """Meter model"""

    ISDETAIL: bool
    SERIAL: str
    TYPE: str
    STATE: str
    STATEDESCR: str
    MODEL: str
    DESCR: str
    DEVICE_TYPE: str
    interface: str
    production_subtype_enum: str | None = None
    subtype: str
    SWVER: str
    PORT: str
    DATATIME: str
    ct_scl_fctr: str
    net_ltea_3phsum_kwh: str
    p_3phsum_kw: str
    q_3phsum_kvar: str
    s_3phsum_kva: str
    tot_pf_rto: str
    freq_hz: str
    i_a: str | None = None
    v12_v: str
    CAL0: str
    origin: str
    OPERATION: str
    CURTIME: str


class PowerMeter(BaseModel):
    """Power meter model"""

    serial: str
    model: str
    description: str


class PVSSolarInverter(BaseModel):
    """Solar inverter model"""

    ISDETAIL: bool
    SERIAL: str
    TYPE: str
    STATE: str
    STATEDESCR: str
    MODEL: str
    DESCR: str
    DEVICE_TYPE: str
    hw_version: str
    interface: str
    PANEL: str
    slave: int
    SWVER: str
    PORT: str
    MOD_SN: str
    NMPLT_SKU: str
    DATATIME: str
    ltea_3phsum_kwh: str
    p_3phsum_kw: str
    vln_3phavg_v: str
    i_3phsum_a: str
    p_mppt1_kw: float
    v_mppt1_v: float
    i_mppt1_a: float
    t_htsnk_degc: str
    freq_hz: str
    stat_ind: str
    origin: str
    OPERATION: str
    CURTIME: str

    @computed_field
    @property
    def p_mppt1_w(self) -> float:
        """Get the power"""
        return self.p_mppt1_kw * 1000


class SolarPanel(BaseModel):
    """Solar panel model"""

    serial: str
    model: str
    description: str

    power: float
    voltage: float
    current: float
    energy: float


class PVSDetail:
    """Class for retrieving PVS details from the PVS Supervisor"""

    def __init__(self, host: str, port: int = 80) -> None:
        """Initialize the PVS_Detail class"""
        self.host = host
        self.port = port
        self.pvs_detail_raw = None

        self.url = f"http://{self.host}:{self.port}/cgi-bin/dl_cgi?Command=DeviceList"

    def get_pvs_detail(self) -> dict:
        """Get the PVS detail"""
        response = httpx.get(self.url, timeout=30)
        self.pvs_detail_raw = response.json()

    def load_file(self, file_path: str) -> dict:
        """Load the file"""
        with open(file_path, "r") as file:
            self.pvs_detail_raw = json.load(file)

    def write_data(self, file_path: str) -> None:
        """Write the data to a file"""
        with Path.open(file_path, "w") as file:
            json.dump(self.pvs_detail_raw, file, indent=4)

    def get_meters(self) -> list[PVSMeter]:
        """Get the meters"""
        return [
            PVSMeter(**device)
            for device in self.pvs_detail_raw.get("devices", [])
            if device.get("DEVICE_TYPE") == "Power Meter"
        ]

    def get_solar_inverters(self) -> list[SolarPanel]:
        """Get the solar inverters"""
        solar_inverters = [
            PVSSolarInverter(**device)
            for device in self.pvs_detail_raw.get("devices", [])
            if device.get("DEVICE_TYPE") == "Inverter" and device.get("TYPE") == "SOLARBRIDGE"
        ]

        return [
            SolarPanel(
                serial=solar_inverter.SERIAL,
                model=solar_inverter.MODEL,
                description=solar_inverter.DESCR,
                power=solar_inverter.p_mppt1_w,
                voltage=solar_inverter.v_mppt1_v,
                current=solar_inverter.i_mppt1_a,
                energy=solar_inverter.ltea_3phsum_kwh,
            )
            for solar_inverter in solar_inverters
        ]


if __name__ == "__main__":
    pvs_detail = PVSDetail("10.0.1.12", 9080)
    # pvs_detail.load_file("output_example.json")
    pvs_detail.get_pvs_detail()
    pvs_detail.write_data("output_example_latest.json")
    meters = pvs_detail.get_meters()
    solar_inverters = pvs_detail.get_solar_inverters()

    count = 0
    for panel in solar_inverters:
        count += 1

        print(
            f"Panel {count} ({panel.serial}): "
            f"{panel.voltage}V at {panel.current}A for {panel.power}W. "
            f"Total Production: {panel.energy}kWh",
        )

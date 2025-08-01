"""Conext XW Inverter"""

from enum import Enum


class ChargerStatus(Enum):
    NOT_CHARGING = 768
    BULK = 769
    ABSORPTION = 770
    OVERCHARGE = 771
    EQUALIZE = 772
    FLOAT = 773
    NO_FLOAT = 774
    CONSTANT_VI = 775
    CHARGER_DISABLED = 776
    QUALIFYING_AC = 777
    QUALIFYING_APS = 778
    ENGAGING_CHARGER = 779
    CHARGE_FAULT = 780
    CHARGER_SUSPEND = 781
    AC_GOOD = 782
    APS_GOOD = 783
    AC_FAULT = 784
    CHARGE = 785
    ABSORPTION_EXIT_PENDING = 786
    GROUND_FAULT = 787
    AC_GOOD_PENDING = 788

    def __str__(self):
        return self.name.replace("_", " ").title()


class InverterStatus(Enum):
    INVERT = 1024
    AC_PASS_THROUGH = 1025
    APS_ONLY = 1026
    LOAD_SENSE = 1027
    INVERTER_DISABLED = 1028
    LOAD_SENSE_READY = 1029
    ENGAGING_INVERTER = 1030
    INVERT_FAULT = 1031
    INVERTER_STANDBY = 1032
    GRID_TIED = 1033
    GRID_SUPPORT = 1034
    GEN_SUPPORT = 1035
    SELL_TO_GRID = 1036
    LOAD_SHAVING = 1037
    GRID_FREQUENCY_STABILIZATION = 1038
    AC_COUPLING = 1039
    REVERSE_IBATT = 1040

    def __str__(self):
        return self.name.replace("_", " ").title()


class OperatingMode(Enum):
    STANDBY = 2
    OPERATING = 3

    def __str__(self):
        return self.name.replace("_", " ").title()


class Inverter:
    def __init__(self, client, device_id):
        self.client = client
        self.device_id = device_id

    @property
    def manufacturer(self):
        """"""
        return self.client.read_str(40004, 32, self.device_id)

    @property
    def model(self):
        """"""
        return self.client.read_str(40020, 32, self.device_id)

    @property
    def version(self):
        """"""
        return self.client.read_str(40044, 16, self.device_id)

    @property
    def serial(self):
        """"""
        return self.client.read_str(40052, 32, self.device_id)

    @property
    def inverter_charger_output_energy_lifetime(self):
        """Energy at the XFMR Lifetime"""
        value = self.client.read_uint32(40094, self.device_id) or 0
        return value * 0.001

    @property
    def inverter_charger_dc_current(self):
        """Inverter-charger power module DC current (A)"""
        value = self.client.read_uint16(40097, self.device_id) or 0
        return value

    @property
    def inverter_charger_dc_current_scaling(self):
        """Inverter-charger power module DC current scaling factor (A)"""
        value = self.client.read_int16(40098, self.device_id) or 0
        return value * 0.1

    @property
    def inverter_charger_dc_voltage(self):
        """Inverter-charger power module DC voltage (V)"""
        value = self.client.read_uint16(40099, self.device_id) or 0
        return value * 0.1

    @property
    def inverter_charger_dc_voltage_scaling(self):
        """Inverter-charger power module DC voltage (V)"""
        value = self.client.read_int16(40100, self.device_id) or 0
        return value * 0.1

    @property
    def inverter_charger_dc_power(self):
        """Inverter-charger power module DC power (W)"""
        value = self.client.read_int16(40101, self.device_id) or 0
        return value * 0.1

    @property
    def inverter_charger_dc_power_scaling(self):
        """Inverter-charger power module DC power scaling factor"""
        value = self.client.read_int16(40102, self.device_id) or 0
        return value * 0.1

    @property
    def continuous_output_power(self):
        """Continuous power output capability of the inverter - Max (W)"""
        return self.client.read_int16(40125, self.device_id) or 0

    @property
    def power_output_percent(self):
        """Set power output to specified level."""
        value = self.client.read_uint16(40187, self.device_id) or 0
        return value * 0.01

    @property
    def max_discharge_power_percent(self):
        """EPC Maximum Discharge Power Percent"""
        value = self.client.read_uint16(40220, self.device_id) or 0
        return value * 0.01

    def set_max_discharge_power_percent(self, value):
        """EPC Maximum Discharge Power Percent"""
        self.client.write_uint16(40220, value, self.device_id) * 100

    @property
    def max_charge_power_percent(self):
        """EPC Maximum Charge Power Percent"""
        value = self.client.read_uint16(40221, self.device_id) or 0
        return value * 0.01

    def set_max_charge_power_percent(self):
        """EPC Maximum Charge Power Percent"""
        self.client.write_uint16(40221, self.device_id) * 100

    @property
    def max_charge_power(self):
        """Max charge power (W)"""
        return self.client.read_uint16(40238, self.device_id) or 0

    @property
    def max_discharge_power(self):
        """Max discharge power (W)"""
        return self.client.read_uint16(40239, self.device_id) or 0

    @property
    def inverter_status(self):
        """Inverter status"""
        value = self.client.read_uint16(40252, self.device_id)
        return InverterStatus(value) if value is not None else None

    @property
    def charger_status(self):
        """Inverter status"""
        value = self.client.read_uint16(40253, self.device_id)
        return ChargerStatus(value) if value is not None else None

    @property
    def mode(self):
        """Operating Mode"""
        value = self.client.read_uint16(40241, self.device_id)
        return OperatingMode(value) if value is not None else None

    def set_mode(self, mode: OperatingMode):
        """Set Operating Mode"""
        self.client.write_uint16(40241, mode.value, self.device_id)

    def get_data(self):
        """Get all data"""
        return {
            "manufacturer": self.manufacturer,
            "model": self.model,
            "version": self.version,
            "serial": self.serial,
            "mode": self.mode.name,
            "inverter_status": self.inverter_status.name,
            "charger_status": self.charger_status.name,
        }

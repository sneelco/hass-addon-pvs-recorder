"""Conext XW Inverter"""

from enum import Enum

from ess.modbus import ModbusClient


class ChargerStatus(Enum):
    """Charger status"""

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

    def __str__(self) -> str:
        """String representation"""
        return self.name.replace("_", " ").title()


class InverterStatus(Enum):
    """Inverter status"""

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

    def __str__(self) -> str:
        """String representation"""
        return self.name.replace("_", " ").title()


class OperatingMode(Enum):
    """Operating mode"""

    STANDBY = 2
    OPERATING = 3

    def __str__(self) -> str:
        """String representation"""
        return self.name.replace("_", " ").title()


class Enabled(Enum):
    """Enabled"""

    DISABLED = 0
    ENABLED = 1

    def __str__(self) -> str:
        """String representation"""
        return self.name.replace("_", " ").title()


class Inverter503:
    """Inverter503 device"""

    def __init__(self, client: ModbusClient, device_id: int) -> None:
        """Initialize the Inverter503 device"""
        self.client = client
        self.device_id = device_id

    @property
    def dc_voltage(self) -> int:
        """DC voltage"""
        value = self.client.read_uint32(80, self.device_id) or 0
        return value * 0.001

    @property
    def dc_current(self) -> int:
        """DC current"""
        value = self.client.read_int32(82, self.device_id) or 0
        return value * 0.001

    @property
    def ac1_voltage(self) -> int:
        """AC1 voltage"""
        value = self.client.read_uint32(98, self.device_id) or 0
        return value * 0.001

    @property
    def ac1_current(self) -> int:
        """AC1 current"""
        value = self.client.read_int32(100, self.device_id) or 0
        return value * 0.001

    @property
    def ac1_power(self) -> int:
        """AC1 power"""
        return self.client.read_int32(102, self.device_id) or 0

    @property
    def ac1_l1_voltage(self) -> int:
        """AC1 L1 voltage"""
        value = self.client.read_uint32(110, self.device_id) or 0
        return value * 0.001

    @property
    def ac1_l2_voltage(self) -> int:
        """AC1 L2 voltage"""
        value = self.client.read_uint32(114, self.device_id) or 0
        return value * 0.001

    @property
    def ac1_l1_current(self) -> int:
        """AC1 L1 current"""
        value = self.client.read_int32(116, self.device_id) or 0
        return value * 0.001

    @property
    def ac1_l2_current(self) -> int:
        """AC1 L2 current"""
        value = self.client.read_int32(112, self.device_id) or 0
        return value * 0.001

    @property
    def ac_load_voltage(self) -> int:
        """AC load voltage"""
        value = self.client.read_uint32(140, self.device_id) or 0
        return value * 0.001

    @property
    def ac_load_current(self) -> int:
        """AC load current"""
        value = self.client.read_int32(150, self.device_id) or 0
        return value * 0.001

    @property
    def ac_load_power(self) -> int:
        """AC load power"""
        return self.client.read_int32(154, self.device_id) or 0

    @property
    def ac_load_l1_voltage(self) -> int:
        """AC load L1 voltage"""
        value = self.client.read_uint32(142, self.device_id) or 0
        return value * 0.001

    @property
    def ac_load_l2_voltage(self) -> int:
        """AC load L2 voltage"""
        value = self.client.read_uint32(144, self.device_id) or 0
        return value * 0.001

    @property
    def ac_load_l1_current(self) -> int:
        """AC load L1 current"""
        value = self.client.read_int32(146, self.device_id) or 0
        return value * 0.001

    @property
    def ac_load_l2_current(self) -> int:
        """AC load L2 current"""
        value = self.client.read_int32(148, self.device_id) or 0
        return value * 0.001

    @property
    def grid_input_energy_month(self) -> int:
        """Grid input energy month"""
        value = self.client.read_uint32(268, self.device_id) or 0
        return value * 0.001

    @property
    def grid_input_energy_year(self) -> int:
        """Grid input energy year"""
        value = self.client.read_uint32(272, self.device_id) or 0
        return value * 0.001

    @property
    def grid_output_energy_year(self) -> int:
        """Grid output energy year"""
        value = self.client.read_uint32(296, self.device_id) or 0
        return value * 0.001

    @property
    def max_charge_rate(self) -> int:
        """Maximum Charge Rate (%)"""
        return self.client.read_uint16(367, self.device_id) or 0

    def set_max_charge_rate(self, value: int) -> None:
        """Maximum Charge Rate (%)"""
        self.client.write_uint16(367, value, self.device_id)

    @property
    def charger_enabled(self) -> Enabled:
        """Charger enabled"""
        value = self.client.read_uint16(356, self.device_id) or 0
        return Enabled(value)

    def set_charger_enabled(self, enabled: Enabled) -> None:
        """Charger enabled"""
        self.client.write_uint16(356, enabled.value, self.device_id)

    @property
    def inverter_enabled(self) -> Enabled:
        """Inverter enabled"""
        value = self.client.read_uint16(353, self.device_id) or 0
        return Enabled(value)

    def set_inverter_enabled(self, enabled: Enabled) -> None:
        """Inverter enabled"""
        self.client.write_uint16(353, enabled.value, self.device_id)

    @property
    def max_discharge_current(self) -> int:
        """Maximum discharge current"""
        return self.client.read_uint16(468, self.device_id) or 0

    @property
    def max_sell_amps(self) -> float:
        """Maximum Sell Amps"""
        value = self.client.read_uint32(436, self.device_id) or 0
        return value * 0.001

    def set_max_sell_amps(self, value: float) -> None:
        """Maximum Sell Amps"""
        self.client.write_uint32(436, int(value * 1000), self.device_id)

    @property
    def load_shave_amps(self) -> float:
        """Load Shave Amps"""
        value = self.client.read_uint32(438, self.device_id) or 0
        return value * 0.001

    def reboot(self) -> None:
        """Reboot the inverter"""
        self.client.write_uint16(359, 0, self.device_id)

    def get_data(self) -> dict:
        """Get all data"""
        return {
            "dc_voltage": self.dc_voltage,
            "dc_current": self.dc_current,
            "ac1_power": self.ac1_power,
            "charger_enabled": self.charger_enabled.name,
            "max_charge_rate": self.max_charge_rate,
            "inverter_enabled": self.inverter_enabled.name,
            "max_discharge_current": self.max_discharge_current,
            "grid_input_energy_year": self.grid_input_energy_year,
            "grid_output_energy_year": self.grid_output_energy_year,
        }

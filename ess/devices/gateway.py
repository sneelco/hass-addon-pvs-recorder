"""Conext Gateway"""

from enum import Enum

from ess.modbus import ModbusClient


class BatteryState(Enum):
    """Battery state"""

    NOT_APPLICABLE = 0
    OFF = 1
    EMPTY = 2
    DISCHARGING = 3
    CHARGING = 4
    FULL = 5
    HOLDING = 6
    TESTING = 7
    UNKNOWN = 65535

    def __str__(self) -> str:
        """String representation"""
        return self.name.replace("_", " ").title()


class BatteryType(Enum):
    """Battery type"""

    NOT_APPLICABLE = 0
    LEAD_ACID = 1
    NICKEL_METAL_HYDRIDE = 2
    NICKEL_CADMIUM = 3
    LITHIUM_ION = 4
    CARBON_ZINC = 5
    ZINC_CHLORIDE = 6
    ALKALINE = 7
    RECHARGEABLE_ALKALINE = 8
    SODIUM_SULFUR = 9
    FLOW = 10
    OTHER = 99

    def __str__(self) -> str:
        """String representation"""
        return self.name.replace("_", " ").title()


class Gateway:
    """Gateway device"""

    def __init__(self, client: ModbusClient, device_id: int) -> None:
        """Initialize the Gateway device"""
        self.client = client
        self.device_id = device_id

    @property
    def manufacturer(self) -> str:
        """Manufacturer"""
        return self.client.read_str(40004, 32, self.device_id)

    @property
    def model(self) -> str:
        """Model"""
        return self.client.read_str(40020, 32, self.device_id)

    @property
    def version(self) -> str:
        """Version"""
        return self.client.read_str(40044, 16, self.device_id)

    @property
    def serial(self) -> str:
        """Serial"""
        return self.client.read_str(40052, 32, self.device_id)

    @property
    def max_power_output_watt(self) -> int:
        """Setting for maximum power output."""
        return self.client.read_uint16(40152, self.device_id)

    def set_max_power_output_watt(self, value: int) -> None:
        """Setting for maximum power output."""
        self.client.write_uint16(40152, value, self.device_id)

    @property
    def max_output_percent(self) -> int:
        """Set power output to specified level"""
        return self.client.read_uint16(40187, self.device_id)

    def set_max_output_percent(self, value: int) -> None:
        """Set power output to specified level"""
        self.client.write_uint16(40187, value, self.device_id)

    @property
    def max_charging(self) -> int:
        """Setpoint for maximum charge."""
        return self.client.read_uint16(40211, self.device_id)

    def set_max_charging(self, value: int) -> None:
        """Setpoint for maximum charge."""
        self.client.write_uint16(40211, value, self.device_id)

    @property
    def setpoint_max_charge(self) -> int:
        """Setpoint for maximum charge (W)."""
        return self.client.read_uint16(40210, self.device_id)

    def set_setpoint_max_charge(self, value: int) -> None:
        """Set setpoint for maximum charge (W)."""
        self.client.write_uint16(40210, value, self.device_id)

    @property
    def storage_control_mode(self) -> int:
        """hold/discharge/charge storage control mode."""
        return self.client.read_uint16(40213, self.device_id)

    @property
    def available_energy(self) -> int:
        """Currently available energy as a percent of the capacity rating."""
        return self.client.read_uint32(40216, self.device_id)

    @property
    def energy_capacity(self) -> int:
        """Nameplate energy capacity in DC watt-hours."""
        return self.client.read_uint16(40247, self.device_id)

    @property
    def max_reserve_1(self) -> int:
        """Setpoint for maximum reserve for storage

        As a percentage of the nominal maximum storage.
        """
        return self.client.read_uint16(40253, self.device_id)

    @property
    def max_reserve_2(self) -> int:
        """Setpoint for maximum reserve for storage

        As a percentage of the nominal maximum storage.
        """
        return self.client.read_uint16(40254, self.device_id)

    @property
    def battery_soc(self) -> int:
        """State of charge of the battery bank."""
        return self.client.read_uint16(40255, self.device_id)

    @property
    def charge_status(self) -> int:
        """Current charge status of the battery bank."""
        value = self.client.read_uint16(40260, self.device_id)

        return BatteryState(value)

    @property
    def battery_type(self) -> BatteryType:
        """Type of battery bank."""
        value = self.client.read_uint16(40265, self.device_id)
        return BatteryType(value)

    @property
    def battery_state(self) -> BatteryState:
        """Current state of the battery bank."""
        value = self.client.read_uint16(40266, self.device_id)
        return BatteryState(value)

    @property
    def battery_power(self) -> int:
        """Total power flowing to/from the battery bank."""
        return self.client.read_int16(40291, self.device_id)

    @property
    def inverter_state(self) -> int:
        """Current state of the inverter."""
        return self.client.read_uint16(40295, self.device_id)

    @property
    def inverter_ac_power(self) -> int:
        """Inverter-charger power module totalAC power"""
        return self.client.read_int16(40084, self.device_id)

    @property
    def inverter_charger_dc_power(self) -> int:
        """Inverter-charger power module DC power"""
        return self.client.read_int16(40101, self.device_id)

    @property
    def inverter_charger_output_energy_lifetime(self) -> int:
        """Inverter charger Power module Output Energy Lifetime"""
        value = self.client.read_uint32(40094, self.device_id) or 0
        return value * 0.001

    @property
    def inverter_charger_input_energy_lifetime(self) -> int:
        """Inverter charger Power module Input Energy Lifetime"""
        value = self.client.read_uint32(40310, self.device_id) or 0
        return value * 0.001

    def get_data(self) -> dict:
        """Get all data"""
        return {
            "manufacturer": self.manufacturer,
            "model": self.model,
            "version": self.version,
            "serial": self.serial,
            "battery_soc": self.battery_soc,
            "battery_state": self.battery_state.name,
        }

"""Conext BMS"""

from enum import Enum

from ess.modbus import ModbusClient


class BatteryType(Enum):
    """Battery type"""

    UNKNOWN = 0
    LEAD_ACID = 1
    NICKEL_METAL_HYDRATE = 2
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


class BatteryState(Enum):
    """Battery state"""

    NOT_AVAILABLE = 0
    DISCONNECTED = 1
    INITIALIZING = 2
    CONNECTED = 3
    STANDBY = 4
    SOC_PROTECTION = 5
    SUSPENDING = 6
    FAULT = 99
    UNKNOWN = 65535

    def __str__(self) -> str:
        """String representation"""
        return self.name.replace("_", " ").title()


class State(Enum):
    """State"""

    SELF_CHECK = 0
    SOFT_STARTING = 1
    STANDBY = 2
    CHARGING = 3
    DISCHARGING = 4
    FAULT = 5
    CONNECT = 6
    SHUT_DOWN = 7
    IDLE = 8
    ONLINE = 9
    OFFLINE = 10
    NOT_APPLICABLE = 255

    def __str__(self) -> str:
        """String representation"""
        return self.name.replace("_", " ").title()


class ControlMode(Enum):
    """Control mode"""

    REMOTE_CONTROL = 0
    LOCAL_CONTROL = 1

    def __str__(self) -> str:
        """String representation"""
        return self.name.replace("_", " ").title()


class Bms:
    """BMS device"""

    def __init__(self, client: ModbusClient, device_id: int) -> None:
        """Initialize the BMS device"""
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
    def full_charge_capacity(self) -> int:
        """Full Charge Capacity (mAh)"""
        return self.client.read_uint16(40072, self.device_id) or 0

    @property
    def energy_capacity(self) -> int:
        """Nameplate Energy Capacity"""
        return self.client.read_uint16(40073, self.device_id) or 0

    @property
    def max_charge_rate(self) -> int:
        """Nameplate Max Charge Rate"""
        return self.client.read_uint16(40074, self.device_id) or 0

    @property
    def max_discharge_rate(self) -> int:
        """Nameplate Max Discharge Rate"""
        return self.client.read_uint16(40075, self.device_id) or 0

    @property
    def soc(self) -> int:
        """State of Charge (%)"""
        return self.client.read_uint16(40081, self.device_id) or 0

    @property
    def control_mode(self) -> ControlMode:
        """Control Mode"""
        value = self.client.read_uint16(40087, self.device_id)
        return ControlMode(value) if value is not None else None

    @property
    def battery_type(self) -> BatteryType:
        """Battery Type"""
        value = self.client.read_uint16(40091, self.device_id)
        return BatteryType(value) if value is not None else None

    @property
    def battery_state(self) -> BatteryState | None:
        """Battery State"""
        value = self.client.read_uint16(40092, self.device_id)
        return BatteryState(value) if value is not None else None

    @property
    def state(self) -> State | None:
        """State"""
        value = self.client.read_uint16(40093, self.device_id)
        return State(value) if value is not None else None

    @property
    def alerm_events(self) -> dict[str, bool]:
        """Alarm Event Map 1"""
        value = self.client.read_uint32(40096, self.device_id) or 0
        bit_events = [
            "CommunicationError",
            "OverTemperatureAlarm",
            "OverTemperatureWarning",
            "UnderTemperatureAlarm",
            "UnderTemperatureWarning",
            "OverChargeCurrentAlarm",
            "OverChargeCurrentWarning",
            "OverDischargeCurrentAlarm",
            "OverDischargeCurrentWarning",
            "OverVoltageAlarm",
            "OverVoltageWarning",
            "UnderVoltageAlarm",
            "UnderVoltageWarning",
            "UnderStateofChargeMinAlarm",
            "UnderStateofChargeMinWarning",
            "OverStateofChargeMaxAlarm",
            "OverStateofChargeMaxWarning",
            "VoltageImbalanceWarning",
            "TemperatureImbalanceAlarm",
            "TemperatureImbalanceWarning",
            "ContactorError",
            "FanError",
            "GroundFaultError",
        ]
        return {event: bool((value >> i) & 1) for i, event in enumerate(bit_events)}

    @property
    def voltage(self) -> int:
        """Voltage (V)"""
        value = self.client.read_uint16(40104, self.device_id) or 0
        return value * 0.01

    @property
    def current(self) -> int:
        """Current (A)"""
        value = self.client.read_int16(40114, self.device_id) or 0
        return value * 0.01

    @property
    def power(self) -> int:
        """Power (W)"""
        value = self.client.read_int16(40115, self.device_id) or 0
        return value * 0.01

    def get_data(self) -> dict:
        """Get all data"""
        return {
            "manufacturer": self.manufacturer,
            "model": self.model,
            "version": self.version,
            "serial": self.serial,
            "battery_type": self.battery_type.name,
            "state": self.state.name,
            "voltage": self.voltage,
            "current": self.current,
            "power": self.power,
            "soc": self.soc,
        }

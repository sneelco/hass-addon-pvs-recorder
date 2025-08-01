"""Conext BMS"""

from enum import Enum


class BatteryType(Enum):
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

    def __str__(self):
        return self.name.replace("_", " ").title()


class BatteryState(Enum):
    NOT_AVAILABLE = 0
    DISCONNECTED = 1
    INITIALIZING = 2
    CONNECTED = 3
    STANDBY = 4
    SOC_PROTECTION = 5
    SUSPENDING = 6
    FAULT = 99
    UNKNOWN = 65535

    def __str__(self):
        return self.name.replace("_", " ").title()


class State(Enum):
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

    def __str__(self):
        return self.name.replace("_", " ").title()


class ControlMode(Enum):
    REMOTE_CONTROL = 0
    LOCAL_CONTROL = 1

    def __str__(self):
        return self.name.replace("_", " ").title()


class Bms:
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
    def full_charge_capacity(self):
        """Full Charge Capacity (mAh)"""
        return self.client.read_uint16(40072, self.device_id) or 0

    @property
    def energy_capacity(self):
        """Nameplate Energy Capacity"""
        return self.client.read_uint16(40073, self.device_id) or 0

    @property
    def max_charge_rate(self):
        """Nameplate Max Charge Rate"""
        return self.client.read_uint16(40074, self.device_id) or 0

    @property
    def max_discharge_rate(self):
        """Nameplate Max Discharge Rate"""
        return self.client.read_uint16(40075, self.device_id) or 0

    @property
    def soc(self):
        """State of Charge (%)"""
        return self.client.read_uint16(40081, self.device_id) or 0

    @property
    def control_mode(self):
        """Control Mode"""
        value = self.client.read_uint16(40087, self.device_id)
        return ControlMode(value) if value is not None else None

    @property
    def battery_type(self):
        """Battery Type"""
        value = self.client.read_uint16(40091, self.device_id)
        return BatteryType(value) if value is not None else None

    @property
    def battery_state(self):
        """Battery State"""
        value = self.client.read_uint16(40092, self.device_id)
        return BatteryState(value) if value is not None else None

    @property
    def state(self):
        """State"""
        value = self.client.read_uint16(40093, self.device_id)
        return State(value) if value is not None else None

    @property
    def alerm_events(self):
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
    def voltage(self):
        """Voltage (V)"""
        value = self.client.read_uint16(40104, self.device_id) or 0
        return value * 0.01

    @property
    def current(self):
        """Current (A)"""
        value = self.client.read_int16(40114, self.device_id) or 0
        return value * 0.01

    @property
    def power(self):
        """Power (W)"""
        value = self.client.read_int16(40115, self.device_id) or 0
        return value * 0.01

    def get_data(self):
        """Get all data"""
        return {
            "manufacturer": self.manufacturer,
            "model": self.model,
            "version": self.version,
            "serial": self.serial,
            "battery_type": self.battery_type.name,
            "voltage": self.voltage,
            "current": self.current,
            "power": self.power,
            "soc": self.soc,
        }

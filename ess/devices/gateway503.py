"""Conext Gateway on 503"""

from ess.modbus import ModbusClient


class Gateway503:
    """Gateway device"""

    def __init__(self, client: ModbusClient, device_id: int) -> None:
        """Initialize the Gateway device"""
        self.client = client
        self.device_id = device_id

    @property
    def grid_power(self) -> int:
        """Grid Power (W)"""
        return self.client.read_int32(110, self.device_id)

    @property
    def grid_input_energy(self) -> int:
        """GRID Input Energy (kWh)"""
        value = self.client.read_uint32(224, self.device_id) or 0
        return value * 0.001

    @property
    def grid_output_energy(self) -> int:
        """GRID Output Energy (kWh)"""
        value = self.client.read_uint32(248, self.device_id) or 0
        return value * 0.001

    @property
    def battery_bank_1_voltage(self) -> int:
        """Battery Bank 1 Voltage (V)"""
        value = self.client.read_uint32(512, self.device_id) or 0
        return value * 0.001

    @property
    def battery_bank_1_current(self) -> int:
        """Battery Bank 1 Current (A)"""
        value = self.client.read_int32(514, self.device_id) or 0
        return value * 0.001

    @property
    def battery_bank_1_soc(self) -> int:
        """Battery Bank 1 SOC"""
        return self.client.read_uint32(968, self.device_id) or 0

    @property
    def battery_bank_1_temperature(self) -> int:
        """Battery Bank 1 Temperature (°C)"""
        value = self.client.read_uint32(516, self.device_id) or 0
        return value * 0.01 - 273

    @property
    def battery_bank_2_voltage(self) -> int:
        """Battery Bank 2 Voltage (V)"""
        value = self.client.read_uint32(526, self.device_id) or 0
        return value * 0.001

    @property
    def battery_bank_2_current(self) -> int:
        """Battery Bank 2 Current (A)"""
        value = self.client.read_int32(528, self.device_id) or 0
        return value * 0.001

    @property
    def battery_bank_2_soc(self) -> int:
        """Battery Bank 2 SOC"""
        return self.client.read_uint32(978, self.device_id) or 0

    @property
    def battery_bank_2_temperature(self) -> int:
        """Battery Bank 2 Temperature (°C)"""
        value = self.client.read_uint32(530, self.device_id) or 0
        return value * 0.01 - 273

    def get_data(self) -> dict:
        """Get all data"""
        return {
            "grid_power": self.grid_power,
            "grid_input_energy": self.grid_input_energy,
            "grid_output_energy": self.grid_output_energy,
            "battery_bank_1_voltage": self.battery_bank_1_voltage,
            "battery_bank_1_current": self.battery_bank_1_current,
            "battery_bank_1_soc": self.battery_bank_1_soc,
            "battery_bank_1_temperature": self.battery_bank_1_temperature,
            "battery_bank_2_voltage": self.battery_bank_2_voltage,
            "battery_bank_2_current": self.battery_bank_2_current,
            "battery_bank_2_soc": self.battery_bank_2_soc,
            "battery_bank_2_temperature": self.battery_bank_2_temperature,
        }

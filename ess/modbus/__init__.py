"""
Modbus client for reading and writing to the Modbus TCP server.
"""

import logging
import sys
from time import sleep

from pymodbus.client import ModbusTcpClient
from pymodbus.exceptions import ConnectionException

from .decoder import PayloadDecoder
from .encoder import PayloadEncoder

logger = logging.getLogger(__name__)


class ModbusClient:
    def __init__(self, ip, port):
        self.client = ModbusTcpClient(ip, port=port)
        self.connected = False
        self.endian = ">"
        self.decoder = PayloadDecoder
        self.encoder = PayloadEncoder

    def connect(self):
        self.connected = self.client.connect()

    def disconnect(self):
        if not self.connected:
            return

        self.client.disconnect()
        self.connected = False

    def disconnect(self):
        self.client.close()
        self.connected = False

    def scan_device(self, device_id, start_address=0, end_address=65535):
        if not self.connected:
            raise Exception("Not connected to the device")

        results = []

        sys.stdout.write("Scanning device %d\n" % device_id)
        sys.stdout.flush()

        for address in range(start_address, end_address):
            if address % 100 == 0:
                progress = int(address / 65535 * 100)
                sys.stdout.write(" [%d%% %d/%d]\n" % (progress, address, end_address))
                sys.stdout.flush()

            result = self.read_holding_registers(address, 1, device_id)
            if result is None:
                sys.stdout.write(".")
                continue

            sys.stdout.write("o")
            results.append([address, result])

        sys.stdout.write(" done\n")
        return results

    def read_holding_registers(self, address, count, device_id):
        attempts = 0
        max_attempts = 3

        while attempts < max_attempts:
            if max_attempts == attempts:
                msg = f"Connection error for device {device_id}, attempt {attempts}/{max_attempts}"
                logger.exception(msg)
                return None

            try:
                result = self.client.read_holding_registers(
                    address=address, count=count, device_id=device_id
                )
                break
            except ConnectionException:
                attempts += 1
                msg = f"Connection error for device {device_id}, attempt {attempts}/{max_attempts}"
                logger.exception(msg)

                self.connect()

                sleep(1)

        if result.isError():
            return None
        else:
            return result.registers

    def _decode_string_bytearray(self, registers, string_length=32):
        byte_data = bytearray()
        for reg in registers:
            byte_data.extend(reg.to_bytes(2, "big"))

        return byte_data[:string_length].decode("utf-8").rstrip("\x00")

    def read_str(self, address, length, device_id):
        count = (length + 1) // 2
        result = self.read_holding_registers(address=address, count=count, device_id=device_id)

        if result is None:
            return None

        return self.decoder.decode_str(result, length)

    def read_int16(self, address, device_id):
        """Decode single register as signed 16-bit integer"""
        result = self.read_holding_registers(address=address, count=1, device_id=device_id)

        if result is None:
            return None

        return self.decoder.decode_int16(result)

    def read_uint16(self, address, device_id):
        """Decode single register as unsigned 16-bit integer"""
        result = self.read_holding_registers(address=address, count=1, device_id=device_id)

        if result is None:
            return None

        return self.decoder.decode_uint16(result)

    def read_int32(self, address, device_id):
        """Decode two registers as signed 32-bit integer"""
        result = self.read_holding_registers(address=address, count=2, device_id=device_id)

        if result is None:
            return None

        return self.decoder.decode_int32(result)

    def read_uint32(self, address, device_id):
        """Decode two registers as unsigned 32-bit integer"""
        result = self.read_holding_registers(address=address, count=2, device_id=device_id)

        if result is None:
            return None

        return self.decoder.decode_uint32(result)

    def write_uint16(self, address, value, device_id):
        register = self.encoder.encode_uint16(value)
        self.client.write_register(address=address, value=register, device_id=device_id)

    def write_int16(self, address, value, device_id):
        register = self.encoder.encode_int16(value)
        self.client.write_register(address=address, value=register, device_id=device_id)

    def write_uint32(self, address, value, device_id):
        registers = self.encoder.encode_uint32(value)
        self.client.write_registers(address, registers, device_id)

    def write_int32(self, address, value, device_id):
        registers = self.encoder.encode_int32(value)
        self.client.write_registers(address, registers, device_id)

    def write_str(self, address, value, device_id):
        registers = self.encoder.encode_string(value, len(value))
        self.client.write_registers(address, registers, device_id)

"""Payload decoder"""

import struct


class PayloadDecoder:
    """Payload decoder"""

    endian = ">"

    @classmethod
    def decode_str(cls, registers: list[int], length: int = 32) -> str:
        """Decode string"""
        byte_data = bytearray()
        for reg in registers:
            byte_data.extend(reg.to_bytes(2, "big"))

        return byte_data[:length].decode("utf-8").rstrip("\x00")

    @classmethod
    def decode_int16(cls, registers: list[int]) -> int:
        """Decode single register as signed 16-bit integer"""
        return struct.unpack(f"{cls.endian}h", struct.pack(f"{cls.endian}H", registers[0]))[0]

    @classmethod
    def decode_uint16(cls, registers: list[int]) -> int:
        """Decode single register as unsigned 16-bit integer"""
        return registers[0]

    @classmethod
    def decode_int32(cls, registers: list[int]) -> int:
        """Decode two registers as signed 32-bit integer"""
        combined = struct.pack(f"{cls.endian}HH", *registers)
        return struct.unpack(f"{cls.endian}l", combined)[0]

    @classmethod
    def decode_uint32(cls, registers: list[int]) -> int:
        """Decode two registers as unsigned 32-bit integer"""
        combined = struct.pack(f"{cls.endian}HH", *registers)
        return struct.unpack(f"{cls.endian}L", combined)[0]

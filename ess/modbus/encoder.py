"""Payload encoder"""

import struct

MAX_UINT16 = 65535
MAX_INT16 = 32767
MAX_UINT32 = 4294967295
MAX_INT32 = 2147483647

MIN_INT16 = -32768
MIN_UINT16 = 0
MIN_INT32 = -2147483648
MIN_UINT32 = 0


class PayloadEncoder:
    """Payload encoder"""

    endian = ">"

    @classmethod
    def encode_int16(cls, value: int) -> int:
        """Encode signed 16-bit integer to single register"""
        if not (MIN_INT16 <= value <= MAX_INT16):
            msg = f"Value {value} out of range for int16"
            raise ValueError(msg)

        packed = struct.pack(f"{cls.endian}h", value)
        return struct.unpack(f"{cls.endian}H", packed)[0]

    @classmethod
    def encode_uint16(cls, value: int) -> int:
        """Encode unsigned 16-bit integer to single register"""
        if not (MIN_UINT16 <= value <= MAX_UINT16):
            msg = f"Value {value} out of range for uint16"
            raise ValueError(msg)

        return value

    @classmethod
    def encode_int32(cls, value: int) -> list[int]:
        """Encode signed 32-bit integer to two registers"""
        if not (MIN_INT32 <= value <= MAX_INT32):
            msg = f"Value {value} out of range for int32"
            raise ValueError(msg)

        packed = struct.pack(f"{cls.endian}l", value)
        return list(struct.unpack(f"{cls.endian}HH", packed))

    @classmethod
    def encode_uint32(cls, value: int) -> list[int]:
        """Encode unsigned 32-bit integer to two registers"""
        if not (MIN_UINT32 <= value <= MAX_UINT32):
            msg = f"Value {value} out of range for uint32"
            raise ValueError(msg)

        packed = struct.pack(f"{cls.endian}L", value)
        return list(struct.unpack(f"{cls.endian}HH", packed))

    @classmethod
    def encode_float32(cls, value: float) -> list[int]:
        """Encode 32-bit float to two registers"""
        packed = struct.pack(f"{cls.endian}f", value)
        return list(struct.unpack(f"{cls.endian}HH", packed))

    @classmethod
    def encode_string(cls, text: str, length: int) -> list[int]:
        """Encode string to registers"""
        padded = text.ljust(length, "\x00")[:length]
        byte_data = padded.encode("utf-8")

        registers = []
        for i in range(0, len(byte_data), 2):
            if i + 1 < len(byte_data):
                reg_bytes = byte_data[i : i + 2]
            else:
                reg_bytes = byte_data[i : i + 1] + b"\x00"
            registers.append(struct.unpack(f"{cls.endian}H", reg_bytes)[0])

        return registers

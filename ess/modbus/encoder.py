import struct


class PayloadEncoder:
    endian = ">"

    @classmethod
    def encode_int16(cls, value):
        """Encode signed 16-bit integer to single register"""
        if not (-32768 <= value <= 32767):
            raise ValueError(f"Value {value} out of range for int16")
        packed = struct.pack(f"{cls.endian}h", value)
        return struct.unpack(f"{cls.endian}H", packed)[0]

    @classmethod
    def encode_uint16(cls, value):
        """Encode unsigned 16-bit integer to single register"""
        if not (0 <= value <= 65535):
            raise ValueError(f"Value {value} out of range for uint16")
        return value

    @classmethod
    def encode_int32(cls, value):
        """Encode signed 32-bit integer to two registers"""
        if not (-2147483648 <= value <= 2147483647):
            raise ValueError(f"Value {value} out of range for int32")
        packed = struct.pack(f"{cls.endian}l", value)
        return list(struct.unpack(f"{cls.endian}HH", packed))

    @classmethod
    def encode_uint32(cls, value):
        """Encode unsigned 32-bit integer to two registers"""
        if not (0 <= value <= 4294967295):
            raise ValueError(f"Value {value} out of range for uint32")
        packed = struct.pack(f"{cls.endian}L", value)
        return list(struct.unpack(f"{cls.endian}HH", packed))

    @classmethod
    def encode_float32(cls, value):
        """Encode 32-bit float to two registers"""
        packed = struct.pack(f"{cls.endian}f", value)
        return list(struct.unpack(f"{cls.endian}HH", packed))

    @classmethod
    def encode_string(cls, text, length):
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

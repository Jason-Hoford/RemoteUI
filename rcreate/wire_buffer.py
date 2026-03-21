"""Binary read/write buffer — equivalent to Java's WireBuffer.

All multi-byte values are big-endian, matching Java's WireBuffer
which reads/writes MSB first.
"""

import struct


class RawFloat(float):
    """Float that carries exact 32-bit IEEE 754 representation.

    Used for NaN values where the exact signaling/quiet bit must be
    preserved (e.g., JVM arithmetic qNaN from ``float + sNaN``).

    Behaves as a regular float for arithmetic but ``write_float`` /
    ``write_float_as_snan`` will emit the stored *raw_bits* unchanged.
    """
    __slots__ = ('raw_bits',)

    def __new__(cls, raw_bits: int):
        val = struct.unpack('>f', struct.pack('>I', raw_bits & 0xFFFFFFFF))[0]
        obj = super().__new__(cls, val)
        obj.raw_bits = raw_bits & 0xFFFFFFFF
        return obj


class WireBuffer:
    def __init__(self, size: int = 1024 * 1024):
        self._buffer = bytearray(size)
        self._index = 0
        self._size = 0

    # ── Read methods ─────────────────────────────────────────────

    def read_byte(self) -> int:
        v = self._buffer[self._index]
        self._index += 1
        return v

    def read_short(self) -> int:
        v = struct.unpack_from('>h', self._buffer, self._index)[0]
        self._index += 2
        return v

    def read_int(self) -> int:
        v = struct.unpack_from('>i', self._buffer, self._index)[0]
        self._index += 4
        return v

    def read_unsigned_int(self) -> int:
        v = struct.unpack_from('>I', self._buffer, self._index)[0]
        self._index += 4
        return v

    def read_float(self) -> float:
        v = struct.unpack_from('>f', self._buffer, self._index)[0]
        self._index += 4
        return v

    def read_long(self) -> int:
        v = struct.unpack_from('>q', self._buffer, self._index)[0]
        self._index += 8
        return v

    def read_utf8(self) -> str:
        length = self.read_int()
        data = self._buffer[self._index:self._index + length]
        self._index += length
        return data.decode('utf-8')

    def read_byte_array(self) -> bytes:
        length = self.read_int()
        data = bytes(self._buffer[self._index:self._index + length])
        self._index += length
        return data

    # ── Write methods ────────────────────────────────────────────

    def write_byte(self, v: int):
        self._ensure_capacity(1)
        self._buffer[self._index] = v & 0xFF
        self._index += 1
        self._update_size()

    def write_short(self, v: int):
        self._ensure_capacity(2)
        struct.pack_into('>h', self._buffer, self._index, v)
        self._index += 2
        self._update_size()

    def write_int(self, v: int):
        self._ensure_capacity(4)
        # Handle both signed and large unsigned values
        if v < 0:
            struct.pack_into('>i', self._buffer, self._index, v)
        elif v > 0x7FFFFFFF:
            struct.pack_into('>I', self._buffer, self._index, v & 0xFFFFFFFF)
        else:
            struct.pack_into('>i', self._buffer, self._index, v)
        self._index += 4
        self._update_size()

    def write_float(self, v: float):
        self._ensure_capacity(4)
        if isinstance(v, RawFloat):
            struct.pack_into('>I', self._buffer, self._index, v.raw_bits)
        elif v != v:  # NaN check (faster than math.isnan)
            bits = struct.unpack('>I', struct.pack('>f', v))[0]
            # RemoteCompose encodes IDs as signaling NaN with base 0xFF800000
            # (sign bit set). Python converts sNaN→qNaN by setting bit 22
            # (0x00400000). Only clear the quiet bit for negative NaN
            # (RemoteCompose-encoded), not positive NaN (regular float('nan')).
            if bits & 0x80000000:  # sign bit set = RemoteCompose NaN
                bits &= ~0x00400000
            struct.pack_into('>I', self._buffer, self._index, bits)
        else:
            struct.pack_into('>f', self._buffer, self._index, v)
        self._index += 4
        self._update_size()

    def write_float_raw(self, bits: int):
        """Write raw 32-bit float value without NaN bit manipulation.

        Use when exact NaN bit patterns need to be preserved, such as
        quiet NaN values from JVM arithmetic (float + sNaN = qNaN).
        """
        self._ensure_capacity(4)
        struct.pack_into('>I', self._buffer, self._index, bits & 0xFFFFFFFF)
        self._index += 4
        self._update_size()

    def write_long(self, v: int):
        self._ensure_capacity(8)
        struct.pack_into('>q', self._buffer, self._index, v)
        self._index += 8
        self._update_size()

    def write_utf8(self, s: str):
        encoded = s.encode('utf-8')
        self.write_int(len(encoded))
        self._ensure_capacity(len(encoded))
        self._buffer[self._index:self._index + len(encoded)] = encoded
        self._index += len(encoded)
        self._update_size()

    def write_byte_array(self, data: bytes):
        self.write_int(len(data))
        self._ensure_capacity(len(data))
        self._buffer[self._index:self._index + len(data)] = data
        self._index += len(data)
        self._update_size()

    def write_float_array(self, values: list):
        self.write_int(len(values))
        for v in values:
            self.write_float(v)

    # ── Buffer management ────────────────────────────────────────

    @property
    def index(self) -> int:
        return self._index

    @index.setter
    def index(self, value: int):
        self._index = value

    @property
    def size(self) -> int:
        return self._size

    def _ensure_capacity(self, needed: int):
        required = self._index + needed
        if required > len(self._buffer):
            new_size = max(len(self._buffer) * 2, required)
            new_buffer = bytearray(new_size)
            new_buffer[:len(self._buffer)] = self._buffer
            self._buffer = new_buffer

    def _update_size(self):
        if self._index > self._size:
            self._size = self._index

    def get_bytes(self) -> bytes:
        """Return data[0:size] as bytes."""
        return bytes(self._buffer[:self._size])

    def clone_bytes(self) -> bytes:
        """Return a copy of data[0:size]."""
        return bytes(self._buffer[:self._size])

    def reset(self):
        self._index = 0
        self._size = 0

    def move_bytes(self, src_start: int, src_end: int, dst: int):
        """Move a range of bytes within the buffer."""
        length = src_end - src_start
        data = bytearray(self._buffer[src_start:src_end])
        if dst < src_start:
            # Moving backward: shift intermediate bytes forward
            self._buffer[dst + length:src_end] = self._buffer[dst:src_start]
            self._buffer[dst:dst + length] = data
        else:
            # Moving forward: shift intermediate bytes backward
            self._buffer[src_start:dst] = self._buffer[src_end:dst + length]
            self._buffer[dst:dst + length] = data

    def get_size(self) -> int:
        return self._size

    def get_buffer(self) -> bytes:
        return bytes(self._buffer[:self._size])

    def get_index(self) -> int:
        return self._index

    def overwrite_int(self, offset: int, value: int):
        """Overwrite 4 bytes at the given offset without moving the write cursor."""
        struct.pack_into('>i', self._buffer, offset, value)

    def move_block(self, src_start: int, dst: int):
        """Move bytes [src_start..size) to dst, shifting intervening data."""
        length = self._size - src_start
        if length <= 0 or src_start == dst:
            return
        data = bytearray(self._buffer[src_start:self._size])
        if dst < src_start:
            self._buffer[dst + length:self._size] = self._buffer[dst:src_start]
            self._buffer[dst:dst + length] = data
        else:
            self._buffer[src_start:dst] = self._buffer[self._size:dst + length]
            self._buffer[dst:dst + length] = data

    def insert_space(self, position: int, length: int):
        """Insert empty space at position, shifting subsequent bytes forward."""
        self._ensure_capacity(length)
        # Shift bytes from position to end
        end = self._size
        self._buffer[position + length:end + length] = self._buffer[position:end]
        self._size += length

"""NaN encoding/decoding utilities for RemoteUI variable IDs.

Variable IDs are encoded as NaN floats using the pattern:
  Float.intBitsToFloat(id | 0xFF800000)

This sets the sign bit + all exponent bits, with the ID in the
lower 23 bits of the mantissa. Matches Java's Utils.asNan().
"""

import struct
import math

# The NaN base: sign=1, exponent=0xFF, mantissa=0
# In Java: -0x800000 as int = 0xFF800000 unsigned
NAN_BASE = 0xFF800000


def as_nan(id: int) -> float:
    """Encode integer ID as a NaN float. Matches Java Utils.asNan(int v)."""
    bits = (id | NAN_BASE) & 0xFFFFFFFF
    return struct.unpack('<f', struct.pack('<I', bits))[0]


def id_from_nan(f: float) -> int:
    """Extract integer ID from a NaN-encoded float.

    Uses 22-bit mask matching Java Utils.idFromNan().
    """
    bits = struct.unpack('<I', struct.pack('<f', f))[0]
    return bits & 0x3FFFFF


def from_nan(f: float) -> int:
    """Extract integer ID using 23-bit mask.

    Matches Java AnimatedFloatExpression.fromNaN() which uses & 0x7FFFFF.
    """
    bits = struct.unpack('<I', struct.pack('<f', f))[0]
    return bits & 0x7FFFFF


def is_nan_id(f: float) -> bool:
    """Check if a float is a NaN-encoded variable ID."""
    if not math.isnan(f):
        return False
    bits = struct.unpack('<I', struct.pack('<f', f))[0]
    return (bits & NAN_BASE) == NAN_BASE


def float_bits_to_int(f: float) -> int:
    """Reinterpret float bits as signed int32."""
    return struct.unpack('<i', struct.pack('<f', f))[0]


def int_bits_to_float(i: int) -> float:
    """Reinterpret int32 bits as float."""
    return struct.unpack('<f', struct.pack('<I', i & 0xFFFFFFFF))[0]

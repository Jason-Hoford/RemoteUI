"""RInt — remote integer value with operator overloading.

Builds integer expression arrays using bitmask encoding.
Equivalent to the integer expression portion of the Java creation API.

Integer expressions use a bitmask to distinguish operators/IDs from constants,
unlike float expressions which use NaN encoding.
"""

from __future__ import annotations
from ..rc import Rc


# Integer expression offset — operators are values >= OFFSET
INT_OFFSET = 0x10000
# Long offset — marks integer expression IDs vs float IDs
LONG_OFFSET = 0x100000000


class RInt:
    """Remote integer value — constant, variable reference, or RPN expression."""

    def __init__(self, writer=None, value=None):
        self.writer = writer

        if isinstance(value, (list, tuple)):
            self.values = [int(v) for v in value[0]]
            self.mask = value[1] if len(value) > 1 else 0
        elif isinstance(value, int):
            self.values = [value]
            self.mask = 0
        elif value is None:
            self.values = []
            self.mask = 0
        else:
            self.values = [int(value)]
            self.mask = 0

        self._id = None
        self._flushed = False

    @property
    def id(self) -> int:
        """Flush expression to writer and return the integer variable ID."""
        if not self._flushed:
            self._id = self.writer.integer_expression(self.values, self.mask)
            self._flushed = True
        return self._id

    def to_int(self) -> int:
        """Flush and return the integer variable ID."""
        return self.id

    def flush(self) -> 'RInt':
        """Force flush to writer."""
        self.to_int()
        return self

    # ── Infix Operators ──────────────────────────────────────────

    def __add__(self, other) -> RInt:
        return self._binary_op(other, Rc.IntegerExpression.I_ADD)

    def __radd__(self, other) -> RInt:
        return self._rbinary_op(other, Rc.IntegerExpression.I_ADD)

    def __sub__(self, other) -> RInt:
        return self._binary_op(other, Rc.IntegerExpression.I_SUB)

    def __rsub__(self, other) -> RInt:
        return self._rbinary_op(other, Rc.IntegerExpression.I_SUB)

    def __mul__(self, other) -> RInt:
        return self._binary_op(other, Rc.IntegerExpression.I_MUL)

    def __rmul__(self, other) -> RInt:
        return self._rbinary_op(other, Rc.IntegerExpression.I_MUL)

    def __floordiv__(self, other) -> RInt:
        return self._binary_op(other, Rc.IntegerExpression.I_DIV)

    def __rfloordiv__(self, other) -> RInt:
        return self._rbinary_op(other, Rc.IntegerExpression.I_DIV)

    def __mod__(self, other) -> RInt:
        return self._binary_op(other, Rc.IntegerExpression.I_MOD)

    def __rmod__(self, other) -> RInt:
        return self._rbinary_op(other, Rc.IntegerExpression.I_MOD)

    def __neg__(self) -> RInt:
        return self._unary_op(Rc.IntegerExpression.I_NEG)

    def __invert__(self) -> RInt:
        return self._unary_op(Rc.IntegerExpression.I_NOT)

    def __and__(self, other) -> RInt:
        return self._binary_op(other, Rc.IntegerExpression.I_AND)

    def __rand__(self, other) -> RInt:
        return self._rbinary_op(other, Rc.IntegerExpression.I_AND)

    def __or__(self, other) -> RInt:
        return self._binary_op(other, Rc.IntegerExpression.I_OR)

    def __ror__(self, other) -> RInt:
        return self._rbinary_op(other, Rc.IntegerExpression.I_OR)

    def __xor__(self, other) -> RInt:
        return self._binary_op(other, Rc.IntegerExpression.I_XOR)

    def __rxor__(self, other) -> RInt:
        return self._rbinary_op(other, Rc.IntegerExpression.I_XOR)

    def __lshift__(self, other) -> RInt:
        return self._binary_op(other, Rc.IntegerExpression.I_SHL)

    def __rlshift__(self, other) -> RInt:
        return self._rbinary_op(other, Rc.IntegerExpression.I_SHL)

    def __rshift__(self, other) -> RInt:
        return self._binary_op(other, Rc.IntegerExpression.I_SHR)

    def __rrshift__(self, other) -> RInt:
        return self._rbinary_op(other, Rc.IntegerExpression.I_SHR)

    # ── Math functions ───────────────────────────────────────────

    def abs(self) -> RInt:
        return self._unary_op(Rc.IntegerExpression.I_ABS)

    def sign(self) -> RInt:
        return self._unary_op(Rc.IntegerExpression.I_SIGN)

    def incr(self) -> RInt:
        return self._unary_op(Rc.IntegerExpression.I_INCR)

    def decr(self) -> RInt:
        return self._unary_op(Rc.IntegerExpression.I_DECR)

    def min(self, other) -> RInt:
        return self._binary_op(other, Rc.IntegerExpression.I_MIN)

    def max(self, other) -> RInt:
        return self._binary_op(other, Rc.IntegerExpression.I_MAX)

    def clamp(self, min_val, max_val) -> RInt:
        min_r, max_r = _coerce(min_val), _coerce(max_val)
        vals, mask = _merge(self, min_r, max_r)
        op_bit = len(vals)
        vals.append(Rc.IntegerExpression.I_CLAMP)
        mask |= (1 << op_bit)
        w = self.writer or min_r.writer or max_r.writer
        return RInt(w, (vals, mask))

    def copy_sign(self, other) -> RInt:
        return self._binary_op(other, Rc.IntegerExpression.I_COPY_SIGN)

    def mad(self, b, c) -> RInt:
        b_r, c_r = _coerce(b), _coerce(c)
        vals, mask = _merge(self, b_r, c_r)
        op_bit = len(vals)
        vals.append(Rc.IntegerExpression.I_MAD)
        mask |= (1 << op_bit)
        w = self.writer or b_r.writer or c_r.writer
        return RInt(w, (vals, mask))

    def if_else(self, then_val, else_val) -> RInt:
        then_r, else_r = _coerce(then_val), _coerce(else_val)
        vals, mask = _merge(else_r, then_r, self)
        op_bit = len(vals)
        vals.append(Rc.IntegerExpression.I_IFELSE)
        mask |= (1 << op_bit)
        w = self.writer or then_r.writer or else_r.writer
        return RInt(w, (vals, mask))

    def ushr(self, other) -> RInt:
        return self._binary_op(other, Rc.IntegerExpression.I_USHR)

    # ── Internal helpers ─────────────────────────────────────────

    def _binary_op(self, other, op: int) -> RInt:
        other = _coerce(other)
        vals, mask = _merge(self, other)
        op_bit = len(vals)
        vals.append(op)
        mask |= (1 << op_bit)
        w = self.writer or other.writer
        return RInt(w, (vals, mask))

    def _rbinary_op(self, other, op: int) -> RInt:
        other = _coerce(other)
        vals, mask = _merge(other, self)
        op_bit = len(vals)
        vals.append(op)
        mask |= (1 << op_bit)
        w = self.writer or other.writer
        return RInt(w, (vals, mask))

    def _unary_op(self, op: int) -> RInt:
        vals = list(self.values)
        mask = self.mask
        op_bit = len(vals)
        vals.append(op)
        mask |= (1 << op_bit)
        return RInt(self.writer, (vals, mask))


def _coerce(v) -> RInt:
    """Convert a plain int to an RInt constant."""
    if isinstance(v, RInt):
        return v
    return RInt(None, int(v))


def _merge(*ints: RInt) -> tuple[list[int], int]:
    """Merge multiple RInt value arrays and masks."""
    vals = []
    mask = 0
    for ri in ints:
        offset = len(vals)
        for i, v in enumerate(ri.values):
            vals.append(v)
            if ri.mask & (1 << i):
                mask |= (1 << (offset + i))
    return vals, mask


# ── Module-level functions ──────────────────────────────────────

def ri_max(a, b) -> RInt:
    a, b = _coerce(a), _coerce(b)
    return a.max(b)

def ri_min(a, b) -> RInt:
    a, b = _coerce(a), _coerce(b)
    return a.min(b)

def ri_abs(a) -> RInt:
    return _coerce(a).abs()

def ri_clamp(value, min_v, max_v) -> RInt:
    return _coerce(value).clamp(min_v, max_v)

def ri_if_else(cond, then_v, else_v) -> RInt:
    return _coerce(cond).if_else(then_v, else_v)

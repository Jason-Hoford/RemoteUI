"""RFloat — remote float value with infix operator overloading.

Builds RPN expression arrays transparently through Python operators.
Equivalent to Kotlin's RFloat class.
"""

from __future__ import annotations
from ..rc import Rc
from ..wire_buffer import RawFloat as _RawFloat


class RFloat:
    """Remote float value — either a constant, a variable reference, or an RPN expression."""

    def __init__(self, writer=None, value=None):
        self.writer = writer
        self.animation: list[float] | None = None

        if isinstance(value, (list, tuple)):
            self.array = list(value)
        elif isinstance(value, _RawFloat):
            # RawFloat — preserve exact NaN bits in the array
            self._id = float(value)  # Python float (qNaN)
            self.array = [value]     # Keep RawFloat for write_float
        elif isinstance(value, float):
            import math
            if math.isnan(value):
                self._id = value
            else:
                self._id = 0.0
            self.array = [value]
        elif isinstance(value, int):
            self.array = [float(value)]
            self._id = 0.0
        elif value is None:
            self.array = []
            self._id = 0.0
        else:
            self.array = [float(value)]
            self._id = 0.0

        if not hasattr(self, '_id'):
            self._id = 0.0

    @property
    def id(self) -> float:
        """Flush expression to writer and return NaN-encoded ID."""
        import math
        if not math.isnan(self._id):
            if self.animation is not None:
                self._id = self.writer.float_expression_with_anim(self.array, self.animation)
            else:
                self._id = self.writer.float_expression(*self.array)
        return self._id

    def to_float(self) -> float:
        """Flush and return NaN-encoded ID."""
        return self.id

    def flush(self) -> 'RFloat':
        """Force flush to writer."""
        self.to_float()
        return self

    def to_array(self) -> list[float]:
        """Return the RPN array."""
        return self.array

    # ── Infix Operators ──────────────────────────────────────────

    def __add__(self, other) -> RFloat:
        return self._binary_op(other, Rc.FloatExpression.ADD)

    def __radd__(self, other) -> RFloat:
        return self._rbinary_op(other, Rc.FloatExpression.ADD)

    def __sub__(self, other) -> RFloat:
        return self._binary_op(other, Rc.FloatExpression.SUB)

    def __rsub__(self, other) -> RFloat:
        return self._rbinary_op(other, Rc.FloatExpression.SUB)

    def __mul__(self, other) -> RFloat:
        return self._binary_op(other, Rc.FloatExpression.MUL)

    def __rmul__(self, other) -> RFloat:
        return self._rbinary_op(other, Rc.FloatExpression.MUL)

    def __truediv__(self, other) -> RFloat:
        return self._binary_op(other, Rc.FloatExpression.DIV)

    def __rtruediv__(self, other) -> RFloat:
        return self._rbinary_op(other, Rc.FloatExpression.DIV)

    def __mod__(self, other) -> RFloat:
        return self._binary_op(other, Rc.FloatExpression.MOD)

    def __rmod__(self, other) -> RFloat:
        return self._rbinary_op(other, Rc.FloatExpression.MOD)

    def __neg__(self) -> RFloat:
        # Kotlin: operator fun unaryMinus() uses array directly
        return RFloat(self.writer, list(self.array) + [-1.0, Rc.FloatExpression.MUL])

    def __pos__(self) -> RFloat:
        return self

    def __getitem__(self, index) -> RFloat:
        """Array dereference: array[index]."""
        idx = _coerce(index)
        return RFloat(self.writer, list(self.array) + _raw_array(idx) + [Rc.FloatExpression.A_DEREF])

    # ── Math functions ───────────────────────────────────────────
    # These match Kotlin's free functions (log, floor, sin, abs, etc.)
    # which use `.array` directly, NOT `toArray()`.

    def min(self, other) -> RFloat:
        return self._binary_op(other, Rc.FloatExpression.MIN)

    def max(self, other) -> RFloat:
        return self._binary_op(other, Rc.FloatExpression.MAX)

    def abs(self) -> RFloat:
        return RFloat(self.writer, list(self.array) + [Rc.FloatExpression.ABS])

    def sin(self) -> RFloat:
        return RFloat(self.writer, list(self.array) + [Rc.FloatExpression.SIN])

    def cos(self) -> RFloat:
        return RFloat(self.writer, list(self.array) + [Rc.FloatExpression.COS])

    def tan(self) -> RFloat:
        return RFloat(self.writer, list(self.array) + [Rc.FloatExpression.TAN])

    def asin(self) -> RFloat:
        return RFloat(self.writer, list(self.array) + [Rc.FloatExpression.ASIN])

    def acos(self) -> RFloat:
        return RFloat(self.writer, list(self.array) + [Rc.FloatExpression.ACOS])

    def atan(self) -> RFloat:
        return RFloat(self.writer, list(self.array) + [Rc.FloatExpression.ATAN])

    def sqrt(self) -> RFloat:
        return RFloat(self.writer, list(self.array) + [Rc.FloatExpression.SQRT])

    def sign(self) -> RFloat:
        return RFloat(self.writer, list(self.array) + [Rc.FloatExpression.SIGN])

    def exp(self) -> RFloat:
        return RFloat(self.writer, list(self.array) + [Rc.FloatExpression.EXP])

    def floor(self) -> RFloat:
        return RFloat(self.writer, list(self.array) + [Rc.FloatExpression.FLOOR])

    def ceil(self) -> RFloat:
        return RFloat(self.writer, list(self.array) + [Rc.FloatExpression.CEIL])

    def log(self) -> RFloat:
        return RFloat(self.writer, list(self.array) + [Rc.FloatExpression.LOG])

    def log2(self) -> RFloat:
        return RFloat(self.writer, list(self.array) + [Rc.FloatExpression.LOG2])

    def ln(self) -> RFloat:
        return RFloat(self.writer, list(self.array) + [Rc.FloatExpression.LN])

    def round(self) -> RFloat:
        return RFloat(self.writer, list(self.array) + [Rc.FloatExpression.ROUND])

    def cbrt(self) -> RFloat:
        return RFloat(self.writer, list(self.array) + [Rc.FloatExpression.CBRT])

    def deg(self) -> RFloat:
        return RFloat(self.writer, list(self.array) + [Rc.FloatExpression.DEG])

    def rad(self) -> RFloat:
        return RFloat(self.writer, list(self.array) + [Rc.FloatExpression.RAD])

    def square(self) -> RFloat:
        return RFloat(self.writer, list(self.array) + [Rc.FloatExpression.SQUARE])

    def inv(self) -> RFloat:
        return RFloat(self.writer, list(self.array) + [Rc.FloatExpression.INV])

    def fract(self) -> RFloat:
        return RFloat(self.writer, list(self.array) + [Rc.FloatExpression.FRACT])

    def noise_from(self) -> RFloat:
        return RFloat(self.writer, list(self.array) + [Rc.FloatExpression.NOISE_FROM])

    def change_sign(self) -> RFloat:
        return RFloat(self.writer, list(self.array) + [Rc.FloatExpression.CHANGE_SIGN])

    # ── Animation ────────────────────────────────────────────────

    def anim(self, duration: float, type: int = Rc.Animate.CUBIC_STANDARD,
             spec: list[float] | None = None, initial_value: float = float('nan'),
             wrap: float = float('nan')) -> 'RFloat':
        """Attach animation to this expression."""
        self.animation = self.writer.anim(duration, type, spec, initial_value, wrap)
        self.flush()
        return self

    def gen_text_id(self, before: int = 2, after: int = 1,
                    flags: int = Rc.TextFromFloat.PAD_AFTER_ZERO) -> int:
        """Generate a text ID from this float expression."""
        return self.writer.create_text_from_float(self.to_float(), before, after, flags)

    # ── Internal helpers ─────────────────────────────────────────

    def _binary_op(self, other, op: float) -> RFloat:
        other = _coerce(other)
        w = self.writer or other.writer
        return RFloat(w, _to_array(self) + _to_array(other) + [op])

    def _rbinary_op(self, other, op: float) -> RFloat:
        # Matches Kotlin's Float.op(RFloat) extension functions which use
        # v.array directly (always full form), NOT toArray(v).
        other = _coerce(other)
        w = self.writer or other.writer
        return RFloat(w, _to_array(other) + list(self.array) + [op])


def _coerce(v) -> RFloat:
    """Convert a plain float/int to an RFloat constant."""
    if isinstance(v, RFloat):
        return v
    return RFloat(None, v if isinstance(v, _RawFloat) else float(v))


def _to_array(v) -> list[float]:
    """Get the RPN array from an RFloat, using NaN ID if already flushed.

    Matches Kotlin's free function toArray(a: RFloat) which returns [id]
    if already flushed, else returns the full array.

    Used by RFloat operators (+, -, *, /) which correspond to Kotlin's
    member operator functions that also call toArray().
    """
    if isinstance(v, RFloat):
        import math
        if math.isnan(v._id):
            # If the array holds a RawFloat, return it to preserve exact bits
            if len(v.array) == 1 and isinstance(v.array[0], _RawFloat):
                return [v.array[0]]
            return [v._id]
        return list(v.array)
    return [float(v)]


def _raw_array(v) -> list[float]:
    """Get the raw RPN array from an RFloat — ALWAYS returns the full array.

    Matches Kotlin's direct `v.array` access used in free functions like
    max(), min(), pow(), ifElse(), abs(), sin(), etc.  These Kotlin free
    functions use `.array` directly (never `toArray()`), so they always
    inline the full expression even for flushed RFloats.
    """
    if isinstance(v, RFloat):
        return list(v.array)
    return [float(v)]


# ── Module-level math functions ──────────────────────────────────
# NOTE: These use _raw_array() to match Kotlin's free functions which
# always use `.array` directly (never `toArray()`).

def rf_max(a, b) -> RFloat:
    a, b = _coerce(a), _coerce(b)
    w = a.writer or b.writer
    return RFloat(w, _raw_array(a) + _raw_array(b) + [Rc.FloatExpression.MAX])

def rf_min(a, b) -> RFloat:
    a, b = _coerce(a), _coerce(b)
    w = a.writer or b.writer
    return RFloat(w, _raw_array(a) + _raw_array(b) + [Rc.FloatExpression.MIN])

def rf_pow(a, b) -> RFloat:
    a, b = _coerce(a), _coerce(b)
    w = a.writer or b.writer
    return RFloat(w, _raw_array(a) + _raw_array(b) + [Rc.FloatExpression.POW])

def rf_sqrt(a) -> RFloat:
    a = _coerce(a)
    return RFloat(a.writer, _raw_array(a) + [Rc.FloatExpression.SQRT])

def rf_abs(a) -> RFloat:
    a = _coerce(a)
    return RFloat(a.writer, _raw_array(a) + [Rc.FloatExpression.ABS])

def rf_sin(a) -> RFloat:
    a = _coerce(a)
    return RFloat(a.writer, _raw_array(a) + [Rc.FloatExpression.SIN])

def rf_cos(a) -> RFloat:
    a = _coerce(a)
    return RFloat(a.writer, _raw_array(a) + [Rc.FloatExpression.COS])

def rf_tan(a) -> RFloat:
    a = _coerce(a)
    return RFloat(a.writer, _raw_array(a) + [Rc.FloatExpression.TAN])

def rf_atan2(a, b) -> RFloat:
    a, b = _coerce(a), _coerce(b)
    w = a.writer or b.writer
    return RFloat(w, _raw_array(a) + _raw_array(b) + [Rc.FloatExpression.ATAN2])

def rf_hypot(a, b) -> RFloat:
    a, b = _coerce(a), _coerce(b)
    w = a.writer or b.writer
    return RFloat(w, _raw_array(a) + _raw_array(b) + [Rc.FloatExpression.HYPOT])

def rf_lerp(x, y, t) -> RFloat:
    x, y, t = _coerce(x), _coerce(y), _coerce(t)
    w = x.writer or y.writer or t.writer
    return RFloat(w, _raw_array(x) + _raw_array(y) + _raw_array(t) + [Rc.FloatExpression.LERP])

def rf_clamp(min_v, max_v, value) -> RFloat:
    min_v, max_v, value = _coerce(min_v), _coerce(max_v), _coerce(value)
    w = value.writer or min_v.writer or max_v.writer
    return RFloat(w, _raw_array(min_v) + _raw_array(max_v) + _raw_array(value) + [Rc.FloatExpression.CLAMP])

def rf_if_else(cond, then_v, else_v) -> RFloat:
    cond, then_v, else_v = _coerce(cond), _coerce(then_v), _coerce(else_v)
    w = cond.writer or then_v.writer or else_v.writer
    return RFloat(w, _raw_array(else_v) + _raw_array(then_v) + _raw_array(cond) + [Rc.FloatExpression.IFELSE])

def rf_smooth_step(value, min_v, max_v) -> RFloat:
    value, min_v, max_v = _coerce(value), _coerce(min_v), _coerce(max_v)
    w = value.writer or min_v.writer or max_v.writer
    return RFloat(w, _raw_array(value) + _raw_array(max_v) + _raw_array(min_v) + [Rc.FloatExpression.SMOOTH_STEP])

def rf_ping_pong(max_v, x) -> RFloat:
    x, max_v = _coerce(x), _coerce(max_v)
    w = x.writer or max_v.writer
    return RFloat(w, _raw_array(x) + _raw_array(max_v) + [Rc.FloatExpression.PINGPONG])

def rf_mad(a, b, c) -> RFloat:
    a, b, c = _coerce(a), _coerce(b), _coerce(c)
    w = a.writer or b.writer or c.writer
    return RFloat(w, _raw_array(a) + _raw_array(b) + _raw_array(c) + [Rc.FloatExpression.MAD])

def rf_step(a, b) -> RFloat:
    a, b = _coerce(a), _coerce(b)
    w = a.writer or b.writer
    return RFloat(w, _raw_array(a) + _raw_array(b) + [Rc.FloatExpression.STEP])

def rf_sqr_sum(a, b) -> RFloat:
    a, b = _coerce(a), _coerce(b)
    w = a.writer or b.writer
    return RFloat(w, _raw_array(a) + _raw_array(b) + [Rc.FloatExpression.SQUARE_SUM])

def rf_random(min_v, max_v) -> RFloat:
    min_v, max_v = _coerce(min_v), _coerce(max_v)
    w = min_v.writer or max_v.writer
    return RFloat(w, _raw_array(min_v) + _raw_array(max_v) + [Rc.FloatExpression.RAND_IN_RANGE])

def rf_copy_sign(a, b) -> RFloat:
    a, b = _coerce(a), _coerce(b)
    w = a.writer or b.writer
    return RFloat(w, _raw_array(a) + _raw_array(b) + [Rc.FloatExpression.COPY_SIGN])

def rf_cubic(x1, y1, x2, y2, value) -> RFloat:
    x1, y1, x2, y2, value = _coerce(x1), _coerce(y1), _coerce(x2), _coerce(y2), _coerce(value)
    w = value.writer or x1.writer or x2.writer or y1.writer or y2.writer
    return RFloat(w, _raw_array(x1) + _raw_array(y1) + _raw_array(x2) + _raw_array(y2) + _raw_array(value) + [Rc.FloatExpression.CUBIC])

# Array operations
def rf_array_max(a) -> RFloat:
    a = _coerce(a)
    return RFloat(a.writer, _raw_array(a) + [Rc.FloatExpression.A_MAX])

def rf_array_min(a) -> RFloat:
    a = _coerce(a)
    return RFloat(a.writer, _raw_array(a) + [Rc.FloatExpression.A_MIN])

def rf_array_sum(a, index=None) -> RFloat:
    a = _coerce(a)
    if index is not None:
        index = _coerce(index)
        return RFloat(a.writer, _raw_array(a) + _raw_array(index) + [Rc.FloatExpression.A_SUM_UNTIL])
    return RFloat(a.writer, _raw_array(a) + [Rc.FloatExpression.A_SUM])

def rf_array_avg(a) -> RFloat:
    a = _coerce(a)
    return RFloat(a.writer, _raw_array(a) + [Rc.FloatExpression.A_AVG])

def rf_array_len(a) -> RFloat:
    a = _coerce(a)
    return RFloat(a.writer, _raw_array(a) + [Rc.FloatExpression.A_LEN])

def rf_array_spline(a, pos) -> RFloat:
    a, pos = _coerce(a), _coerce(pos)
    return RFloat(a.writer, _raw_array(a) + _raw_array(pos) + [Rc.FloatExpression.A_SPLINE])

def rf_spline_loop(a, pos) -> RFloat:
    a, pos = _coerce(a), _coerce(pos)
    return RFloat(a.writer, _raw_array(a) + _raw_array(pos) + [Rc.FloatExpression.A_SPLINE_LOOP])

def rf_array_sum_xy(a, b) -> RFloat:
    a, b = _coerce(a), _coerce(b)
    return RFloat(a.writer, _raw_array(a) + _raw_array(b) + [Rc.FloatExpression.A_SUM_XY])

def rf_array_sum_sqr(a) -> RFloat:
    a = _coerce(a)
    return RFloat(a.writer, _raw_array(a) + [Rc.FloatExpression.A_SUM_SQR])

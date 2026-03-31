"""RPN float expression evaluator for RemoteCompose.

Ports Java AnimatedFloatExpression to Python. Evaluates float[] arrays
containing RPN-encoded expressions where NaN values encode operators
and variable references.
"""

import math
import struct
import random


# -- NaN encoding/decoding (match Java exactly) --

FLOAT_EXPR_OFFSET = 0x310000

# NanMap region constants (bits 20-21, bit 22 is cleared by from_nan)
ID_REGION_MASK = 0x300000
ID_REGION_SYSTEM = 0x000000
ID_REGION_VARIABLE = 0x100000
ID_REGION_ARRAY = 0x200000
ID_REGION_OPERATION = 0x300000


def as_nan(v: int) -> float:
    """Encode an int ID as a NaN float (match Java asNan)."""
    return struct.unpack('>f', struct.pack('>I', (v | 0xFF800000) & 0xFFFFFFFF))[0]


def from_nan(v: float) -> int:
    """Decode a NaN float back to its int ID.

    Clears bit 22 (the quiet NaN bit) which gets set when a 32-bit
    signaling NaN passes through Python's 64-bit double representation.
    All Java-encoded NaN IDs have bit 22 clear, so this is always safe.
    """
    bits = struct.unpack('>I', struct.pack('>f', v))[0]
    return bits & 0x3FFFFF


def is_nan(v: float) -> bool:
    return math.isnan(v)


def is_math_operator(v: float) -> bool:
    """Check if a NaN float is a math operator (not a variable reference)."""
    if not math.isnan(v):
        return False
    pos = from_nan(v)
    if is_data_variable(v):
        return False
    return FLOAT_EXPR_OFFSET < pos <= FLOAT_EXPR_OFFSET + 79


def is_system_variable(v: float) -> bool:
    return (from_nan(v) >> 20) == 0


def is_normal_variable(v: float) -> bool:
    return (from_nan(v) >> 20) == 1


def is_data_variable(v: float) -> bool:
    return (from_nan(v) >> 20) == 2


def is_operation_variable(v: float) -> bool:
    return (from_nan(v) >> 20) == 3


# -- Operator codes (OFFSET + N) --

_O = FLOAT_EXPR_OFFSET
OP_ADD = _O + 1
OP_SUB = _O + 2
OP_MUL = _O + 3
OP_DIV = _O + 4
OP_MOD = _O + 5
OP_MIN = _O + 6
OP_MAX = _O + 7
OP_POW = _O + 8
OP_SQRT = _O + 9
OP_ABS = _O + 10
OP_SIGN = _O + 11
OP_COPY_SIGN = _O + 12
OP_EXP = _O + 13
OP_FLOOR = _O + 14
OP_LOG = _O + 15
OP_LN = _O + 16
OP_ROUND = _O + 17
OP_SIN = _O + 18
OP_COS = _O + 19
OP_TAN = _O + 20
OP_ASIN = _O + 21
OP_ACOS = _O + 22
OP_ATAN = _O + 23
OP_ATAN2 = _O + 24
OP_MAD = _O + 25
OP_IFELSE = _O + 26
OP_CLAMP = _O + 27
OP_CBRT = _O + 28
OP_DEG = _O + 29
OP_RAD = _O + 30
OP_CEIL = _O + 31
OP_A_DEREF = _O + 32
OP_A_MAX = _O + 33
OP_A_MIN = _O + 34
OP_A_SUM = _O + 35
OP_A_AVG = _O + 36
OP_A_LEN = _O + 37
OP_A_SPLINE = _O + 38
OP_RAND = _O + 39
OP_RAND_SEED = _O + 40
OP_NOISE_FROM = _O + 41
OP_RAND_IN_RANGE = _O + 42
OP_SQUARE_SUM = _O + 43
OP_STEP = _O + 44
OP_SQUARE = _O + 45
OP_DUP = _O + 46
OP_HYPOT = _O + 47
OP_SWAP = _O + 48
OP_LERP = _O + 49
OP_SMOOTH_STEP = _O + 50
OP_LOG2 = _O + 51
OP_INV = _O + 52
OP_FRACT = _O + 53
OP_PINGPONG = _O + 54
OP_NOP = _O + 55
OP_STORE_R0 = _O + 56
OP_STORE_R1 = _O + 57
OP_STORE_R2 = _O + 58
OP_STORE_R3 = _O + 59
OP_LOAD_R0 = _O + 60
OP_LOAD_R1 = _O + 61
OP_LOAD_R2 = _O + 62
OP_LOAD_R3 = _O + 63
OP_VAR1 = _O + 70
OP_VAR2 = _O + 71
OP_VAR3 = _O + 72
OP_CHANGE_SIGN = _O + 73
OP_CUBIC = _O + 74
OP_A_SPLINE_LOOP = _O + 75
OP_A_SUM_TILL = _O + 76
OP_A_SUM_XY = _O + 77
OP_A_SUM_SQR = _O + 78
OP_A_LERP = _O + 79

_FP_TO_RAD = 57.29578  # 180/PI
_FP_TO_DEG = 0.017453292  # PI/180

_rng = None


def _get_rng():
    global _rng
    if _rng is None:
        _rng = random.Random()
    return _rng


class FloatExpressionEvaluator:
    """RPN stack-based float expression evaluator.

    Matches Java AnimatedFloatExpression.opEval exactly.
    """

    def __init__(self):
        self.r0 = 0.0
        self.r1 = 0.0
        self.r2 = 0.0
        self.r3 = 0.0
        self._easing = None  # lazy CubicEasing for OP_CUBIC

    def eval(self, exp: list, var: list = None, collections=None) -> float:
        """Evaluate an RPN float expression.

        Args:
            exp: List of floats (expression array). Modified in-place as stack.
            var: Optional variable values for VAR1/VAR2/VAR3.
            collections: Optional CollectionsAccess for array ops.

        Returns:
            The computed float result.
        """
        stack = list(exp)  # work on a copy
        sp = -1
        var = var or []
        for i in range(len(stack)):
            v = stack[i]
            if math.isnan(v):
                op_id = from_nan(v)
                region = op_id & ID_REGION_MASK
                if region == ID_REGION_ARRAY and collections is not None:
                    # Array reference — push as-is (used by array ops)
                    sp += 1
                    stack[sp] = v
                elif FLOAT_EXPR_OFFSET < op_id <= FLOAT_EXPR_OFFSET + 79:
                    sp = self._op_eval(stack, sp, op_id, var, collections)
                else:
                    # Variable reference — resolve
                    sp += 1
                    stack[sp] = v  # will be resolved by caller
            else:
                sp += 1
                if sp < len(stack):
                    stack[sp] = v
                else:
                    stack.append(v)
        result = stack[sp] if sp >= 0 else 0.0
        return 0.0 if math.isnan(result) else result

    def _op_eval(self, s, sp, op_id, var, ca) -> int:
        """Evaluate a single operator. s=stack, sp=stack pointer."""

        if op_id == OP_ADD:
            s[sp - 1] = s[sp - 1] + s[sp]
            return sp - 1

        if op_id == OP_SUB:
            s[sp - 1] = s[sp - 1] - s[sp]
            return sp - 1

        if op_id == OP_MUL:
            s[sp - 1] = s[sp - 1] * s[sp]
            return sp - 1

        if op_id == OP_DIV:
            s[sp - 1] = s[sp - 1] / s[sp] if s[sp] != 0 else float('inf')
            return sp - 1

        if op_id == OP_MOD:
            s[sp - 1] = math.fmod(s[sp - 1], s[sp]) if s[sp] != 0 else 0.0
            return sp - 1

        if op_id == OP_MIN:
            s[sp - 1] = min(s[sp - 1], s[sp])
            return sp - 1

        if op_id == OP_MAX:
            s[sp - 1] = max(s[sp - 1], s[sp])
            return sp - 1

        if op_id == OP_POW:
            try:
                s[sp - 1] = math.pow(s[sp - 1], s[sp])
            except (ValueError, OverflowError):
                s[sp - 1] = 0.0
            return sp - 1

        if op_id == OP_SQRT:
            v = s[sp]
            s[sp] = math.sqrt(max(0.0, v)) if math.isfinite(v) else 0.0
            return sp

        if op_id == OP_ABS:
            s[sp] = abs(s[sp])
            return sp

        if op_id == OP_SIGN:
            v = s[sp]
            s[sp] = (1.0 if v > 0 else (-1.0 if v < 0 else 0.0))
            return sp

        if op_id == OP_COPY_SIGN:
            s[sp - 1] = math.copysign(s[sp - 1], s[sp])
            return sp - 1

        if op_id == OP_EXP:
            v = s[sp]
            if not math.isfinite(v):
                s[sp] = 0.0
            else:
                try:
                    s[sp] = math.exp(v)
                except OverflowError:
                    s[sp] = float('inf')
            return sp

        if op_id == OP_FLOOR:
            v = s[sp]
            s[sp] = math.floor(v) if math.isfinite(v) else 0.0
            return sp

        if op_id == OP_LOG:
            v = s[sp]
            s[sp] = math.log10(v) if math.isfinite(v) and v > 0 else 0.0
            return sp

        if op_id == OP_LN:
            v = s[sp]
            s[sp] = math.log(v) if math.isfinite(v) and v > 0 else 0.0
            return sp

        if op_id == OP_ROUND:
            v = s[sp]
            s[sp] = round(v) if math.isfinite(v) else 0.0
            return sp

        if op_id == OP_SIN:
            v = s[sp]
            s[sp] = math.sin(v) if math.isfinite(v) else 0.0
            return sp

        if op_id == OP_COS:
            v = s[sp]
            s[sp] = math.cos(v) if math.isfinite(v) else 0.0
            return sp

        if op_id == OP_TAN:
            v = s[sp]
            s[sp] = math.tan(v) if math.isfinite(v) else 0.0
            return sp

        if op_id == OP_ASIN:
            s[sp] = math.asin(max(-1.0, min(1.0, s[sp])))
            return sp

        if op_id == OP_ACOS:
            s[sp] = math.acos(max(-1.0, min(1.0, s[sp])))
            return sp

        if op_id == OP_ATAN:
            s[sp] = math.atan(s[sp])
            return sp

        if op_id == OP_ATAN2:
            s[sp - 1] = math.atan2(s[sp - 1], s[sp])
            return sp - 1

        if op_id == OP_MAD:
            # mad(a, b, c) = c + b * a  (stack: a=sp-2, b=sp-1, c=sp)
            s[sp - 2] = s[sp] + s[sp - 1] * s[sp - 2]
            return sp - 2

        if op_id == OP_IFELSE:
            # ifElse(else, then, cond): cond=sp, then=sp-1, else=sp-2
            s[sp - 2] = s[sp - 1] if s[sp] > 0 else s[sp - 2]
            return sp - 2

        if op_id == OP_CLAMP:
            # clamp(val, max, min): min=sp, max=sp-1, val=sp-2
            s[sp - 2] = min(max(s[sp - 2], s[sp]), s[sp - 1])
            return sp - 2

        if op_id == OP_CBRT:
            s[sp] = math.pow(s[sp], 1.0 / 3.0) if s[sp] >= 0 else -math.pow(-s[sp], 1.0 / 3.0)
            return sp

        if op_id == OP_DEG:
            s[sp] = s[sp] * _FP_TO_RAD
            return sp

        if op_id == OP_RAD:
            s[sp] = s[sp] * _FP_TO_DEG
            return sp

        if op_id == OP_CEIL:
            v = s[sp]
            s[sp] = math.ceil(v) if math.isfinite(v) else 0.0
            return sp

        # -- Array operations --
        if op_id == OP_A_DEREF:
            if ca:
                arr_id = from_nan(s[sp - 1])
                idx = int(s[sp])
                s[sp - 1] = ca.get_float_value(arr_id, idx)
            else:
                s[sp - 1] = 0.0
            return sp - 1

        if op_id == OP_A_MAX:
            if ca:
                arr_id = from_nan(s[sp])
                arr = ca.get_floats(arr_id)
                s[sp] = max(arr) if arr else 0.0
            return sp

        if op_id == OP_A_MIN:
            if ca:
                arr_id = from_nan(s[sp])
                arr = ca.get_floats(arr_id)
                s[sp] = min(arr) if arr else 0.0
            return sp

        if op_id == OP_A_SUM:
            if ca:
                arr_id = from_nan(s[sp])
                arr = ca.get_floats(arr_id)
                s[sp] = sum(arr)
            return sp

        if op_id == OP_A_AVG:
            if ca:
                arr_id = from_nan(s[sp])
                arr = ca.get_floats(arr_id)
                s[sp] = sum(arr) / len(arr) if arr else 0.0
            return sp

        if op_id == OP_A_LEN:
            if ca:
                arr_id = from_nan(s[sp])
                s[sp] = float(ca.get_list_length(arr_id))
            return sp

        if op_id == OP_A_SPLINE:
            if ca:
                arr_id = from_nan(s[sp - 1])
                arr = ca.get_floats(arr_id)
                pos = s[sp]
                s[sp - 1] = _spline_interp(arr, pos)
            else:
                s[sp - 1] = 0.0
            return sp - 1

        # -- Random --
        if op_id == OP_RAND:
            sp += 1
            if sp >= len(s):
                s.append(0.0)
            s[sp] = _get_rng().random()
            return sp

        if op_id == OP_RAND_SEED:
            seed = s[sp]
            rng = _get_rng()
            if seed == 0:
                rng.seed()
            else:
                bits = struct.unpack('>I', struct.pack('>f', seed))[0]
                rng.seed(bits)
            return sp - 1

        if op_id == OP_NOISE_FROM:
            x = struct.unpack('>I', struct.pack('>f', s[sp]))[0]
            x = ((x << 13) ^ x) & 0xFFFFFFFF
            s[sp] = 1.0 - ((x * (x * x * 15731 + 789221) + 1376312589) & 0x7FFFFFFF) / 1.0737418e9
            return sp

        if op_id == OP_RAND_IN_RANGE:
            s[sp] = _get_rng().random() * (s[sp] - s[sp - 1]) + s[sp - 1]
            return sp

        # -- Misc --
        if op_id == OP_SQUARE_SUM:
            s[sp - 1] = s[sp - 1] * s[sp - 1] + s[sp] * s[sp]
            return sp - 1

        if op_id == OP_STEP:
            s[sp - 1] = 1.0 if s[sp - 1] > s[sp] else 0.0
            return sp - 1

        if op_id == OP_SQUARE:
            s[sp] = s[sp] * s[sp]
            return sp

        if op_id == OP_DUP:
            sp += 1
            if sp >= len(s):
                s.append(0.0)
            s[sp] = s[sp - 1]
            return sp

        if op_id == OP_HYPOT:
            s[sp - 1] = math.hypot(s[sp - 1], s[sp])
            return sp - 1

        if op_id == OP_SWAP:
            s[sp - 1], s[sp] = s[sp], s[sp - 1]
            return sp

        if op_id == OP_LERP:
            a, b, t = s[sp - 2], s[sp - 1], s[sp]
            s[sp - 2] = a + (b - a) * t
            return sp - 2

        if op_id == OP_SMOOTH_STEP:
            val, edge1, edge0 = s[sp - 2], s[sp - 1], s[sp]
            if val < edge0:
                s[sp - 2] = 0.0
            elif val > edge1:
                s[sp - 2] = 1.0
            else:
                v = (val - edge0) / (edge1 - edge0) if edge1 != edge0 else 0.0
                s[sp - 2] = v * v * (3.0 - 2.0 * v)
            return sp - 2

        if op_id == OP_LOG2:
            s[sp] = math.log(max(1e-30, s[sp])) / math.log(2.0)
            return sp

        if op_id == OP_INV:
            s[sp] = 1.0 / s[sp] if s[sp] != 0 else float('inf')
            return sp

        if op_id == OP_FRACT:
            s[sp] = s[sp] - int(s[sp])
            return sp

        if op_id == OP_PINGPONG:
            max_2 = s[sp] * 2.0
            tmp = math.fmod(s[sp - 1], max_2) if max_2 != 0 else 0.0
            s[sp - 1] = tmp if tmp < s[sp] else max_2 - tmp
            return sp - 1

        if op_id == OP_NOP:
            return sp

        # -- Register store/load --
        if op_id == OP_STORE_R0:
            self.r0 = s[sp]
            return sp - 1
        if op_id == OP_STORE_R1:
            self.r1 = s[sp]
            return sp - 1
        if op_id == OP_STORE_R2:
            self.r2 = s[sp]
            return sp - 1
        if op_id == OP_STORE_R3:
            self.r3 = s[sp]
            return sp - 1
        if op_id == OP_LOAD_R0:
            sp += 1
            if sp >= len(s):
                s.append(0.0)
            s[sp] = self.r0
            return sp
        if op_id == OP_LOAD_R1:
            sp += 1
            if sp >= len(s):
                s.append(0.0)
            s[sp] = self.r1
            return sp
        if op_id == OP_LOAD_R2:
            sp += 1
            if sp >= len(s):
                s.append(0.0)
            s[sp] = self.r2
            return sp
        if op_id == OP_LOAD_R3:
            sp += 1
            if sp >= len(s):
                s.append(0.0)
            s[sp] = self.r3
            return sp

        # -- Variables --
        if op_id == OP_VAR1:
            sp += 1
            if sp >= len(s):
                s.append(0.0)
            s[sp] = var[0] if len(var) > 0 else 0.0
            return sp
        if op_id == OP_VAR2:
            sp += 1
            if sp >= len(s):
                s.append(0.0)
            s[sp] = var[1] if len(var) > 1 else 0.0
            return sp
        if op_id == OP_VAR3:
            sp += 1
            if sp >= len(s):
                s.append(0.0)
            s[sp] = var[2] if len(var) > 2 else 0.0
            return sp

        if op_id == OP_CHANGE_SIGN:
            s[sp] = -s[sp]
            return sp

        if op_id == OP_CUBIC:
            from .easing import CubicEasing
            x1, y1, x2, y2, pos = s[sp - 4], s[sp - 3], s[sp - 2], s[sp - 1], s[sp]
            if self._easing is None:
                self._easing = CubicEasing(x1, y1, x2, y2)
            else:
                self._easing.x1, self._easing.y1 = x1, y1
                self._easing.x2, self._easing.y2 = x2, y2
            s[sp - 4] = self._easing.get(pos)
            return sp - 4

        if op_id == OP_A_SPLINE_LOOP:
            if ca:
                arr_id = from_nan(s[sp - 1])
                arr = ca.get_floats(arr_id)
                r = s[sp] - int(s[sp])
                if r < 0:
                    r += 1.0
                s[sp - 1] = _spline_interp(arr, r)
            else:
                s[sp - 1] = 0.0
            return sp - 1

        if op_id == OP_A_SUM_TILL:
            if ca:
                arr_id = from_nan(s[sp - 1])
                last = int(s[sp])
                total = 0.0
                for j in range(last + 1):
                    total += ca.get_float_value(arr_id, j)
                s[sp - 1] = total
            else:
                s[sp - 1] = 0.0
            return sp - 1

        if op_id == OP_A_SUM_XY:
            if ca:
                id_x = from_nan(s[sp - 1])
                id_y = from_nan(s[sp])
                arr_x = ca.get_floats(id_x)
                arr_y = ca.get_floats(id_y)
                total = sum(x * y for x, y in zip(arr_x, arr_y))
                s[sp - 1] = total
            else:
                s[sp - 1] = 0.0
            return sp - 1

        if op_id == OP_A_SUM_SQR:
            if ca:
                arr_id = from_nan(s[sp])
                arr = ca.get_floats(arr_id)
                s[sp] = sum(v * v for v in arr)
            return sp

        if op_id == OP_A_LERP:
            if ca:
                arr_id = from_nan(s[sp - 1])
                arr = ca.get_floats(arr_id)
                p = s[sp] * (len(arr) - 1)
                idx = int(p)
                if idx < 0:
                    s[sp - 1] = arr[0] if arr else 0.0
                elif idx >= len(arr) - 1:
                    s[sp - 1] = arr[-1] if arr else 0.0
                else:
                    t = p - idx
                    s[sp - 1] = arr[idx] + t * (arr[idx + 1] - arr[idx])
            else:
                s[sp - 1] = 0.0
            return sp - 1

        # Unknown op — no-op
        return sp


def _spline_interp(arr: list, pos: float) -> float:
    """Simple monotonic spline interpolation over array values."""
    if not arr:
        return 0.0
    n = len(arr)
    if n == 1:
        return arr[0]
    p = pos * (n - 1)
    idx = int(p)
    if idx < 0:
        return arr[0]
    if idx >= n - 1:
        return arr[-1]
    t = p - idx
    return arr[idx] + t * (arr[idx + 1] - arr[idx])

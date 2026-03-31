"""Easing curves for RemoteCompose animation.

Ports the Java easing pipeline (CubicEasing, BounceCurve, ElasticOutCurve,
FloatAnimation) to Python, matching the Java implementations exactly.
"""

import math
import struct


# Easing type constants (match Java Easing.java)
CUBIC_STANDARD = 1
CUBIC_ACCELERATE = 2
CUBIC_DECELERATE = 3
CUBIC_LINEAR = 4
CUBIC_ANTICIPATE = 5
CUBIC_OVERSHOOT = 6
CUBIC_CUSTOM = 11
SPLINE_CUSTOM = 12
EASE_OUT_BOUNCE = 13
EASE_OUT_ELASTIC = 14

# Preset cubic control points (match CubicEasing.java)
_STANDARD = (0.4, 0.0, 0.2, 1.0)
_ACCELERATE = (0.4, 0.05, 0.8, 0.7)
_DECELERATE = (0.0, 0.0, 0.2, 0.95)
_LINEAR = (1.0, 1.0, 0.0, 0.0)
_ANTICIPATE = (0.36, 0.0, 0.66, -0.56)
_OVERSHOOT = (0.34, 1.56, 0.64, 1.0)

_CUBIC_PRESETS = {
    CUBIC_STANDARD: _STANDARD,
    CUBIC_ACCELERATE: _ACCELERATE,
    CUBIC_DECELERATE: _DECELERATE,
    CUBIC_LINEAR: _LINEAR,
    CUBIC_ANTICIPATE: _ANTICIPATE,
    CUBIC_OVERSHOOT: _OVERSHOOT,
}

_ERROR = 0.01
_D_ERROR = 0.0001


class CubicEasing:
    """CSS cubic-bezier style easing, matching Java CubicEasing.java."""

    __slots__ = ('x1', 'y1', 'x2', 'y2')

    def __init__(self, x1=0.4, y1=0.0, x2=0.2, y2=1.0):
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2

    @classmethod
    def from_type(cls, etype: int) -> 'CubicEasing':
        preset = _CUBIC_PRESETS.get(etype, _STANDARD)
        return cls(*preset)

    def _get_x(self, t: float) -> float:
        t1 = 1.0 - t
        f1 = 3.0 * t1 * t1 * t
        f2 = 3.0 * t1 * t * t
        f3 = t * t * t
        return self.x1 * f1 + self.x2 * f2 + f3

    def _get_y(self, t: float) -> float:
        t1 = 1.0 - t
        f1 = 3.0 * t1 * t1 * t
        f2 = 3.0 * t1 * t * t
        f3 = t * t * t
        return self.y1 * f1 + self.y2 * f2 + f3

    def get(self, x: float) -> float:
        if x <= 0.0:
            return 0.0
        if x >= 1.0:
            return 1.0
        t = 0.5
        rng = 0.5
        while rng > _ERROR:
            tx = self._get_x(t)
            rng *= 0.5
            if tx < x:
                t += rng
            else:
                t -= rng
        x1 = self._get_x(t - rng)
        x2 = self._get_x(t + rng)
        y1 = self._get_y(t - rng)
        y2 = self._get_y(t + rng)
        if x2 == x1:
            return y1
        return (y2 - y1) * (x - x1) / (x2 - x1) + y1

    def get_diff(self, x: float) -> float:
        t = 0.5
        rng = 0.5
        while rng > _D_ERROR:
            tx = self._get_x(t)
            rng *= 0.5
            if tx < x:
                t += rng
            else:
                t -= rng
        x1 = self._get_x(t - rng)
        x2 = self._get_x(t + rng)
        y1 = self._get_y(t - rng)
        y2 = self._get_y(t + rng)
        if x2 == x1:
            return 0.0
        return (y2 - y1) / (x2 - x1)


class BounceCurve:
    """Bounce easing, matching Java BounceCurve.java."""

    _N1 = 7.5625
    _D1 = 2.75

    def get(self, x: float) -> float:
        t = x
        if t < 0:
            return 0.0
        if t < 1.0 / self._D1:
            return 1.0 / (1.0 + 1.0 / self._D1) * (self._N1 * t * t + t)
        elif t < 2.0 / self._D1:
            t -= 1.5 / self._D1
            return self._N1 * t * t + 0.75
        elif t < 2.5 / self._D1:
            t -= 2.25 / self._D1
            return self._N1 * t * t + 0.9375
        elif t <= 1.0:
            t -= 2.625 / self._D1
            return self._N1 * t * t + 0.984375
        return 1.0

    def get_diff(self, x: float) -> float:
        if x < 0:
            return 0.0
        if x < 1.0 / self._D1:
            return 2.0 * self._N1 * x / (1.0 + 1.0 / self._D1) + 1.0 / (1.0 + 1.0 / self._D1)
        elif x < 2.0 / self._D1:
            return 2.0 * self._N1 * (x - 1.5 / self._D1)
        elif x < 2.5 / self._D1:
            return 2.0 * self._N1 * (x - 2.25 / self._D1)
        elif x <= 1.0:
            return 2.0 * self._N1 * (x - 2.625 / self._D1)
        return 0.0


class ElasticOutCurve:
    """Elastic out easing, matching Java ElasticOutCurve.java."""

    _C4 = 2.0 * math.pi / 3.0

    def get(self, x: float) -> float:
        if x <= 0:
            return 0.0
        if x >= 1:
            return 1.0
        return math.pow(2.0, -10.0 * x) * math.sin((x * 10.0 - 0.75) * self._C4) + 1.0

    def get_diff(self, x: float) -> float:
        if x < 0 or x > 1:
            return 0.0
        log_8 = math.log(8.0)
        twenty_pi = 20.0 * math.pi
        f_pi = math.pi
        return (5.0 * math.pow(2.0, 1.0 - 10.0 * x)
                * (log_8 * math.cos(twenty_pi * x / 3.0)
                   + 2.0 * f_pi * math.sin(twenty_pi * x / 3.0)) / 3.0)


class StepCurve:
    """Monotonic spline easing from control points."""

    def __init__(self, params, offset, length):
        self._points = list(params[offset:offset + length]) if params else []
        if not self._points:
            self._points = [0.0, 1.0]

    def get(self, x: float) -> float:
        if x <= 0:
            return 0.0
        if x >= 1:
            return 1.0
        n = len(self._points)
        if n < 2:
            return x
        pos = x * (n - 1)
        idx = int(pos)
        if idx >= n - 1:
            return self._points[-1]
        t = pos - idx
        return self._points[idx] + t * (self._points[idx + 1] - self._points[idx])

    def get_diff(self, x: float) -> float:
        n = len(self._points)
        if n < 2:
            return 1.0
        pos = x * (n - 1)
        idx = max(0, min(int(pos), n - 2))
        return (self._points[idx + 1] - self._points[idx]) * (n - 1)


def _float_to_raw_int_bits(f: float) -> int:
    return struct.unpack('>I', struct.pack('>f', f))[0]


def _int_bits_to_float(i: int) -> float:
    return struct.unpack('>f', struct.pack('>I', i & 0xFFFFFFFF))[0]


def _create_easing(etype: int, params=None, offset=0, length=0):
    """Create an easing curve from type and optional parameters."""
    if etype in (CUBIC_STANDARD, CUBIC_ACCELERATE, CUBIC_DECELERATE,
                 CUBIC_LINEAR, CUBIC_ANTICIPATE, CUBIC_OVERSHOOT):
        return CubicEasing.from_type(etype)
    elif etype == CUBIC_CUSTOM and params and length >= 4:
        return CubicEasing(params[offset], params[offset + 1],
                           params[offset + 2], params[offset + 3])
    elif etype == EASE_OUT_BOUNCE:
        return BounceCurve()
    elif etype == EASE_OUT_ELASTIC:
        return ElasticOutCurve()
    elif etype == SPLINE_CUSTOM:
        return StepCurve(params, offset, length)
    return CubicEasing.from_type(CUBIC_STANDARD)


class FloatAnimation:
    """Animated float with easing, matching Java FloatAnimation.java.

    Parses the packed float[] animation description and provides get(t).
    """

    def __init__(self, description: list):
        self.duration = 1.0
        self.wrap = float('nan')
        self.initial_value = float('nan')
        self.target_value = float('nan')
        self.directional_snap = 0
        self.propagate = False
        self.offset = 0.0
        self.easing_curve = CubicEasing.from_type(CUBIC_STANDARD)
        self._parse(description)

    def _parse(self, spec: list):
        if not spec:
            return
        self.duration = spec[0] if spec else 1.0
        param_len = 0
        etype = CUBIC_STANDARD
        if len(spec) > 1:
            num_type = _float_to_raw_int_bits(spec[1])
            etype = num_type & 0xFF
            has_wrap = ((num_type >> 8) & 0x1) > 0
            has_init = ((num_type >> 8) & 0x2) > 0
            self.directional_snap = (num_type >> 10) & 0x3
            self.propagate = ((num_type >> 12) & 0x1) > 0
            param_len = (num_type >> 16) & 0xFFFF
            off = 2 + param_len
            if has_init and off < len(spec):
                self.initial_value = spec[off]
                off += 1
            if has_wrap and off < len(spec):
                self.wrap = spec[off]
        self.easing_curve = _create_easing(etype, spec, 2, param_len)

    def set_initial_value(self, value: float):
        if math.isnan(self.wrap):
            self.initial_value = value
        else:
            self.initial_value = value % self.wrap
        self._set_scale_offset()

    def set_target_value(self, value: float):
        self.target_value = value
        if not math.isnan(self.wrap):
            self.initial_value = _wrap(self.wrap, self.initial_value)
            self.target_value = _wrap(self.wrap, self.target_value)
            if math.isnan(self.initial_value):
                self.initial_value = self.target_value
            dist = _wrap_distance(self.wrap, self.initial_value, self.target_value)
            if dist > 0 and self.target_value < self.initial_value:
                self.target_value += self.wrap
            elif dist < 0 and self.directional_snap != 0:
                if self.directional_snap == 1 and self.target_value > self.initial_value:
                    self.initial_value = self.target_value
                if self.directional_snap == 2 and self.target_value < self.initial_value:
                    self.initial_value = self.target_value
                self.target_value -= self.wrap
        self._set_scale_offset()

    def _set_scale_offset(self):
        if not math.isnan(self.initial_value) and not math.isnan(self.target_value):
            self.offset = self.initial_value
        else:
            self.offset = 0.0

    def get(self, t: float) -> float:
        if self.directional_snap == 1 and self.target_value < self.initial_value:
            self.initial_value = self.target_value
            return self.target_value
        if self.directional_snap == 2 and self.target_value > self.initial_value:
            self.initial_value = self.target_value
            return self.target_value
        eased = self.easing_curve.get(t / self.duration)
        return eased * (self.target_value - self.initial_value) + self.initial_value


def _wrap(wrap_val: float, value: float) -> float:
    value = value % wrap_val
    if value < 0:
        value += wrap_val
    return value


def _wrap_distance(wrap_val: float, from_val: float, to_val: float) -> float:
    delta = (to_val - from_val) % 360.0
    if delta < -wrap_val / 2.0:
        delta += wrap_val
    elif delta > wrap_val / 2.0:
        delta -= wrap_val
    return delta

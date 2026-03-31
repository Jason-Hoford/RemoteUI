"""Runtime state and evaluation engine for RemoteCompose animation.

Manages time, system variables, expression evaluation, and per-frame
state updates. This is the bridge between the parsed RcDocument and
the Skia renderer — it resolves NaN-encoded variable references to
concrete float values each frame.
"""

import math
import struct
import time as _time

from .expressions import (
    FloatExpressionEvaluator, from_nan, is_nan, is_math_operator,
    is_data_variable, is_system_variable, is_normal_variable,
    ID_REGION_ARRAY, ID_REGION_MASK,
)
from .easing import FloatAnimation


# System variable IDs (match Java RemoteContext)
ID_CONTINUOUS_SEC = 1
ID_TIME_IN_SEC = 2
ID_TIME_IN_MIN = 3
ID_TIME_IN_HR = 4
ID_WINDOW_WIDTH = 5
ID_WINDOW_HEIGHT = 6
ID_COMPONENT_WIDTH = 7
ID_COMPONENT_HEIGHT = 8
ID_CALENDAR_MONTH = 9
ID_OFFSET_TO_UTC = 10
ID_WEEK_DAY = 11
ID_DAY_OF_MONTH = 12
ID_TOUCH_POS_X = 13
ID_TOUCH_POS_Y = 14
ID_TOUCH_VEL_X = 15
ID_TOUCH_VEL_Y = 16
ID_DENSITY = 27
ID_API_LEVEL = 28
ID_ANIMATION_TIME = 30
ID_ANIMATION_DELTA_TIME = 31
ID_EPOCH_SECOND = 32
ID_DAY_OF_YEAR = 34
ID_YEAR = 35


class CollectionsAccess:
    """Provides access to float arrays (DATA_PATH, float_list) for expression evaluation."""

    def __init__(self):
        self.float_arrays = {}  # id -> list[float]

    def get_floats(self, arr_id: int) -> list:
        return self.float_arrays.get(arr_id, [])

    def get_float_value(self, arr_id: int, index: int) -> float:
        arr = self.float_arrays.get(arr_id, [])
        if 0 <= index < len(arr):
            return arr[index]
        return 0.0

    def get_list_length(self, arr_id: int) -> int:
        return len(self.float_arrays.get(arr_id, []))


class _FloatExprState:
    """Per-expression runtime state (mirrors Java FloatExpression)."""

    __slots__ = ('id', 'src_value', 'src_animation', 'pre_calc',
                 'float_animation', 'last_change', 'last_calc_value',
                 'last_animated_value')

    def __init__(self, fid: int, src_value: list, src_animation: list):
        self.id = fid
        self.src_value = src_value
        self.src_animation = src_animation
        self.pre_calc = list(src_value)
        self.float_animation = None
        self.last_change = float('nan')
        self.last_calc_value = float('nan')
        self.last_animated_value = float('nan')

        if src_animation:
            if len(src_animation) > 4 and src_animation[0] == 0:
                pass  # spring — not yet supported
            else:
                self.float_animation = FloatAnimation(src_animation)


class RuntimeState:
    """Central animation runtime state.

    Manages:
    - System variables (time, dimensions, etc.)
    - Float variable store (expression results, DATA_FLOAT values)
    - Expression evaluation and animation
    - Frame stepping
    """

    def __init__(self, doc, fps: float = 60.0):
        self.doc = doc
        self.fps = fps
        self.dt = 1.0 / fps

        # Time state
        self.animation_time = 0.0
        self.delta_time = 0.0
        self.wall_time = 0.0  # real-world seconds since epoch
        self.frame_count = 0

        # Variable stores
        self.floats = {}      # id -> float (resolved values)
        self.integers = {}    # id -> int
        self.texts = {}       # id -> str

        # Expression engine
        self.evaluator = FloatExpressionEvaluator()
        self.collections = CollectionsAccess()

        # Per-expression state
        self._float_exprs = {}   # id -> _FloatExprState
        self._int_exprs = {}     # id -> expression data
        self._float_lists = {}   # id -> list[float]
        self._dynamic_float_lists = {}  # id -> list[float]

        # Initialize from document
        self._init_from_doc()

    def _init_from_doc(self):
        """Initialize state from the parsed document."""
        # Load static data
        for fid, val in self.doc.floats.items():
            self.floats[fid] = val

        for tid, text in self.doc.texts.items():
            self.texts[tid] = text

        # First pass: register data and expressions from operations
        for o in self.doc.operations:
            op = o.get('op', '')

            if op == 'data_float':
                self.floats[o['id']] = o.get('value', 0.0)

            elif op == 'data_int':
                self.integers[o['id']] = o.get('value', 0)

            elif op == 'data_path':
                pass  # handled by renderer

            elif op == 'animated_float':
                fid = o['id']
                expr = o.get('expression', [])
                anim = o.get('animation', [])
                state = _FloatExprState(fid, expr, anim)
                self._float_exprs[fid] = state
                # Initialize with default value
                if fid not in self.floats:
                    self.floats[fid] = 0.0

            elif op == 'component_value':
                # Binds a component's measured dimension to a float variable.
                # value_type: 0=width, 1=height
                # Without a layout engine, approximate with document dimensions.
                vtype = o.get('value_type', -1)
                vid = o.get('value_id', 0)
                if vtype == 0:
                    self.floats[vid] = float(self.doc.width)
                elif vtype == 1:
                    self.floats[vid] = float(self.doc.height)

            elif op == 'float_list':
                fid = o.get('id', 0)
                data = o.get('items', o.get('data', []))
                self._float_lists[fid] = list(data)
                self.collections.float_arrays[fid] = list(data)

            elif op == 'dynamic_float_list':
                fid = o.get('id', 0)
                data = o.get('items', o.get('data', []))
                self._dynamic_float_lists[fid] = list(data)
                self.collections.float_arrays[fid] = list(data)

            elif op == 'id_list':
                fid = o.get('id', 0)
                data = o.get('items', o.get('data', []))
                self.collections.float_arrays[fid] = [float(x) for x in data]

        # Set initial system variables
        self._update_system_variables()

    def _update_system_variables(self):
        """Update time-based and geometry system variables."""
        self.floats[ID_ANIMATION_TIME] = self.animation_time
        self.floats[ID_ANIMATION_DELTA_TIME] = self.delta_time
        self.floats[ID_WINDOW_WIDTH] = float(self.doc.width)
        self.floats[ID_WINDOW_HEIGHT] = float(self.doc.height)
        self.floats[ID_COMPONENT_WIDTH] = float(self.doc.width)
        self.floats[ID_COMPONENT_HEIGHT] = float(self.doc.height)
        self.floats[ID_DENSITY] = 1.0
        self.floats[ID_API_LEVEL] = 36.0

        # Real-world time (preserve sub-second precision for smooth animation)
        if self.wall_time <= 0:
            self.wall_time = _time.time()
        t = _time.localtime(self.wall_time)
        frac = self.wall_time - int(self.wall_time)  # fractional seconds

        secs_from_midnight = t.tm_hour * 3600 + t.tm_min * 60 + t.tm_sec + frac
        self.floats[ID_CONTINUOUS_SEC] = float(secs_from_midnight % 3600)
        self.floats[ID_TIME_IN_SEC] = float(secs_from_midnight)
        self.floats[ID_TIME_IN_MIN] = float(t.tm_hour * 60 + t.tm_min + (t.tm_sec + frac) / 60.0)
        self.floats[ID_TIME_IN_HR] = float(t.tm_hour)
        self.floats[ID_CALENDAR_MONTH] = float(t.tm_mon)
        self.floats[ID_WEEK_DAY] = float(t.tm_wday + 1)
        self.floats[ID_DAY_OF_MONTH] = float(t.tm_mday)
        self.floats[ID_DAY_OF_YEAR] = float(t.tm_yday)
        self.floats[ID_YEAR] = float(t.tm_year)
        self.floats[ID_EPOCH_SECOND] = float(int(self.wall_time))

        # Touch defaults (no touch)
        self.floats.setdefault(ID_TOUCH_POS_X, 0.0)
        self.floats.setdefault(ID_TOUCH_POS_Y, 0.0)
        self.floats.setdefault(ID_TOUCH_VEL_X, 0.0)
        self.floats.setdefault(ID_TOUCH_VEL_Y, 0.0)

    def get_float(self, fid: int) -> float:
        """Get current value of a float variable."""
        return self.floats.get(fid, 0.0)

    def set_float(self, fid: int, value: float):
        """Set a float variable value."""
        self.floats[fid] = value

    def resolve_float(self, v: float) -> float:
        """Resolve a potentially NaN-encoded float to its current value.

        If v is a normal float, returns it.
        If v is a NaN variable reference, looks up the current value.
        """
        if not math.isnan(v):
            return v
        fid = from_nan(v)
        if is_math_operator(v) or is_data_variable(v):
            return v  # not a variable reference
        return self.floats.get(fid, 0.0)

    def step(self, dt: float = None):
        """Advance one frame. Evaluates all expressions.

        Args:
            dt: Time delta in seconds. If None, uses 1/fps.
        """
        if dt is None:
            dt = self.dt
        self.delta_time = dt
        self.animation_time += dt
        self.wall_time += dt
        self.frame_count += 1

        self._update_system_variables()
        self._evaluate_expressions()

    def step_to(self, t: float):
        """Step to a specific animation time."""
        dt = t - self.animation_time
        if dt < 0:
            # Reset and step forward
            self.animation_time = 0.0
            self.frame_count = 0
            self._reset_expressions()
            self.step(t)
        else:
            self.step(dt)

    def _reset_expressions(self):
        """Reset expression states for re-evaluation from t=0."""
        for state in self._float_exprs.values():
            state.last_change = float('nan')
            state.last_calc_value = float('nan')
            state.last_animated_value = float('nan')
            state.pre_calc = list(state.src_value)
            if state.float_animation:
                state.float_animation = FloatAnimation(state.src_animation)

    def _evaluate_expressions(self):
        """Evaluate all float expressions for the current frame."""
        for fid, state in self._float_exprs.items():
            self._eval_float_expr(state)

    def _eval_float_expr(self, state: _FloatExprState):
        """Evaluate a single float expression, matching Java FloatExpression.apply."""
        # Phase 1: resolve variable references in the expression
        value_changed = False
        for i in range(len(state.src_value)):
            v = state.src_value[i]
            if math.isnan(v) and not is_math_operator(v) and not is_data_variable(v):
                var_id = from_nan(v)
                new_value = self.floats.get(var_id, 0.0)
                # ID_DENSITY default to 1.0
                if var_id == ID_DENSITY and new_value == 0.0:
                    new_value = 1.0
                if state.float_animation:
                    if state.pre_calc[i] != new_value:
                        value_changed = True
                        state.pre_calc[i] = new_value
                else:
                    state.pre_calc[i] = new_value
            else:
                state.pre_calc[i] = state.src_value[i]

        # Check if output changed
        if value_changed:
            v = self.evaluator.eval(state.pre_calc, collections=self.collections)
            if v != state.last_calc_value:
                state.last_change = self.animation_time
                state.last_calc_value = v
            else:
                value_changed = False

        t = self.animation_time
        if math.isnan(state.last_change):
            state.last_change = t

        # Phase 2: apply animation or direct eval
        if state.float_animation:
            if math.isnan(state.last_calc_value):
                # First evaluation
                state.last_calc_value = self.evaluator.eval(
                    state.pre_calc, collections=self.collections)
                state.float_animation.set_target_value(state.last_calc_value)
                if math.isnan(state.float_animation.initial_value):
                    state.float_animation.set_initial_value(state.last_calc_value)

            if value_changed:
                if math.isnan(state.float_animation.target_value):
                    state.float_animation.set_initial_value(state.last_calc_value)
                else:
                    state.float_animation.set_initial_value(
                        state.float_animation.target_value)
                state.float_animation.set_target_value(state.last_calc_value)

            result = state.float_animation.get(t - state.last_change)
            self.floats[state.id] = result
        else:
            # No animation — direct evaluation
            result = self.evaluator.eval(
                state.pre_calc, collections=self.collections)
            self.floats[state.id] = result

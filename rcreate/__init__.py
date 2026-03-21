"""rcreate — Python library for creating RemoteCompose binary documents.

Public API mirrors Java's remote-creation-core.
"""

from .writer import RemoteComposeWriter, DEMO7_TAG_ORDER
from .remote_UI_buffer import RemoteComposeBuffer
from .remote_UI_state import RemoteUIState
from .wire_buffer import WireBuffer, RawFloat
from .rc import Rc
from .rc_paint import RcPaint
from .paint_bundle import PaintBundle
from .shader import RemoteComposeShader
from .context import RcContext, Modifier
from . import operations as Ops

from .modifiers import (
    RecordingModifier,
    Shape, RectShape, RoundedRectShape, CircleShape,
    EXACT, FILL, WRAP, WEIGHT, EXACT_DP,
    FILL_PARENT_MAX_WIDTH, FILL_PARENT_MAX_HEIGHT,
)

from .actions import (
    Action,
    ValueFloatChange,
    ValueIntegerChange,
    ValueStringChange,
    ValueFloatExpressionChange,
    ValueIntegerExpressionChange,
    HostAction,
)

from .remote_path import RemotePath
from .types.nan_utils import as_nan, id_from_nan, int_bits_to_float
from .types.rfloat import (
    RFloat,
    rf_max, rf_min, rf_pow, rf_abs, rf_sin, rf_cos, rf_tan,
    rf_sqrt, rf_atan2, rf_hypot, rf_lerp, rf_clamp, rf_if_else,
    rf_smooth_step, rf_ping_pong, rf_mad, rf_step, rf_sqr_sum,
    rf_random, rf_copy_sign, rf_cubic,
    rf_array_max, rf_array_min, rf_array_sum, rf_array_avg,
    rf_array_len, rf_array_spline, rf_spline_loop,
    rf_array_sum_xy, rf_array_sum_sqr,
)

__all__ = [
    'RemoteComposeWriter', 'DEMO7_TAG_ORDER',
    'RemoteComposeBuffer',
    'RemoteUIState',
    'WireBuffer', 'RawFloat',
    'Rc',
    'RcPaint',
    'PaintBundle',
    'RemoteComposeShader',
    'RcContext',
    'Modifier',
    'Ops',
    'RecordingModifier',
    'Shape', 'RectShape', 'RoundedRectShape', 'CircleShape',
    'EXACT', 'FILL', 'WRAP', 'WEIGHT', 'EXACT_DP',
    'FILL_PARENT_MAX_WIDTH', 'FILL_PARENT_MAX_HEIGHT',
    'Action',
    'ValueFloatChange',
    'ValueIntegerChange',
    'ValueStringChange',
    'ValueFloatExpressionChange',
    'ValueIntegerExpressionChange',
    'HostAction',
    'RemotePath',
    'as_nan', 'id_from_nan', 'int_bits_to_float',
    'RFloat',
    'rf_max', 'rf_min', 'rf_pow', 'rf_abs', 'rf_sin', 'rf_cos', 'rf_tan',
    'rf_sqrt', 'rf_atan2', 'rf_hypot', 'rf_lerp', 'rf_clamp', 'rf_if_else',
    'rf_smooth_step', 'rf_ping_pong', 'rf_mad', 'rf_step', 'rf_sqr_sum',
    'rf_random', 'rf_copy_sign', 'rf_cubic',
    'rf_array_max', 'rf_array_min', 'rf_array_sum', 'rf_array_avg',
    'rf_array_len', 'rf_array_spline', 'rf_spline_loop',
    'rf_array_sum_xy', 'rf_array_sum_sqr',
]

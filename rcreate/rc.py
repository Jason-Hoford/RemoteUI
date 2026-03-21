"""Central constants for RemoteUI creation API — equivalent to Java's Rc.java.

All values are extracted from the Java source and must match exactly.
"""

from .types.nan_utils import as_nan

# ── Float expression operator base offset ─────────────────────
_FLOAT_OP_OFFSET = 0x310000

# ── Integer expression operator base offset ───────────────────
_INT_OP_OFFSET = 0x10000

# ── Long offset for integer expression IDs ────────────────────
_LONG_OFFSET = 0x100000000


class Rc:
    """Constants used in RemoteCompose."""

    class Profiles:
        """RcProfiles constants."""
        PROFILE_ANDROIDX = 0x200

    class FloatExpression:
        """RPN float expression operators (NaN-encoded floats)."""
        ADD = as_nan(_FLOAT_OP_OFFSET + 1)
        SUB = as_nan(_FLOAT_OP_OFFSET + 2)
        MUL = as_nan(_FLOAT_OP_OFFSET + 3)
        DIV = as_nan(_FLOAT_OP_OFFSET + 4)
        MOD = as_nan(_FLOAT_OP_OFFSET + 5)
        MIN = as_nan(_FLOAT_OP_OFFSET + 6)
        MAX = as_nan(_FLOAT_OP_OFFSET + 7)
        POW = as_nan(_FLOAT_OP_OFFSET + 8)
        SQRT = as_nan(_FLOAT_OP_OFFSET + 9)
        ABS = as_nan(_FLOAT_OP_OFFSET + 10)
        SIGN = as_nan(_FLOAT_OP_OFFSET + 11)
        COPY_SIGN = as_nan(_FLOAT_OP_OFFSET + 12)
        EXP = as_nan(_FLOAT_OP_OFFSET + 13)
        FLOOR = as_nan(_FLOAT_OP_OFFSET + 14)
        LOG = as_nan(_FLOAT_OP_OFFSET + 15)
        LN = as_nan(_FLOAT_OP_OFFSET + 16)
        ROUND = as_nan(_FLOAT_OP_OFFSET + 17)
        SIN = as_nan(_FLOAT_OP_OFFSET + 18)
        COS = as_nan(_FLOAT_OP_OFFSET + 19)
        TAN = as_nan(_FLOAT_OP_OFFSET + 20)
        ASIN = as_nan(_FLOAT_OP_OFFSET + 21)
        ACOS = as_nan(_FLOAT_OP_OFFSET + 22)
        ATAN = as_nan(_FLOAT_OP_OFFSET + 23)
        ATAN2 = as_nan(_FLOAT_OP_OFFSET + 24)
        MAD = as_nan(_FLOAT_OP_OFFSET + 25)
        IFELSE = as_nan(_FLOAT_OP_OFFSET + 26)
        CLAMP = as_nan(_FLOAT_OP_OFFSET + 27)
        CBRT = as_nan(_FLOAT_OP_OFFSET + 28)
        DEG = as_nan(_FLOAT_OP_OFFSET + 29)
        RAD = as_nan(_FLOAT_OP_OFFSET + 30)
        CEIL = as_nan(_FLOAT_OP_OFFSET + 31)
        # Array ops
        A_DEREF = as_nan(_FLOAT_OP_OFFSET + 32)
        A_MAX = as_nan(_FLOAT_OP_OFFSET + 33)
        A_MIN = as_nan(_FLOAT_OP_OFFSET + 34)
        A_SUM = as_nan(_FLOAT_OP_OFFSET + 35)
        A_AVG = as_nan(_FLOAT_OP_OFFSET + 36)
        A_LEN = as_nan(_FLOAT_OP_OFFSET + 37)
        A_SPLINE = as_nan(_FLOAT_OP_OFFSET + 38)
        RAND = as_nan(_FLOAT_OP_OFFSET + 39)
        RAND_SEED = as_nan(_FLOAT_OP_OFFSET + 40)
        NOISE_FROM = as_nan(_FLOAT_OP_OFFSET + 41)
        RAND_IN_RANGE = as_nan(_FLOAT_OP_OFFSET + 42)
        SQUARE_SUM = as_nan(_FLOAT_OP_OFFSET + 43)
        STEP = as_nan(_FLOAT_OP_OFFSET + 44)
        SQUARE = as_nan(_FLOAT_OP_OFFSET + 45)
        DUP = as_nan(_FLOAT_OP_OFFSET + 46)
        HYPOT = as_nan(_FLOAT_OP_OFFSET + 47)
        SWAP = as_nan(_FLOAT_OP_OFFSET + 48)
        LERP = as_nan(_FLOAT_OP_OFFSET + 49)
        SMOOTH_STEP = as_nan(_FLOAT_OP_OFFSET + 50)
        # Post-V6 operators
        LOG2 = as_nan(_FLOAT_OP_OFFSET + 51)
        INV = as_nan(_FLOAT_OP_OFFSET + 52)
        FRACT = as_nan(_FLOAT_OP_OFFSET + 53)
        PINGPONG = as_nan(_FLOAT_OP_OFFSET + 54)
        NOP = as_nan(_FLOAT_OP_OFFSET + 55)
        # Register ops
        STORE_R0 = as_nan(_FLOAT_OP_OFFSET + 56)
        STORE_R1 = as_nan(_FLOAT_OP_OFFSET + 57)
        STORE_R2 = as_nan(_FLOAT_OP_OFFSET + 58)
        STORE_R3 = as_nan(_FLOAT_OP_OFFSET + 59)
        LOAD_R0 = as_nan(_FLOAT_OP_OFFSET + 60)
        LOAD_R1 = as_nan(_FLOAT_OP_OFFSET + 61)
        LOAD_R2 = as_nan(_FLOAT_OP_OFFSET + 62)
        LOAD_R3 = as_nan(_FLOAT_OP_OFFSET + 63)
        # Command/variable ops
        CMD1 = as_nan(_FLOAT_OP_OFFSET + 64)
        CMD2 = as_nan(_FLOAT_OP_OFFSET + 65)
        CMD3 = as_nan(_FLOAT_OP_OFFSET + 66)
        CMD4 = as_nan(_FLOAT_OP_OFFSET + 67)
        VAR1 = as_nan(_FLOAT_OP_OFFSET + 70)
        VAR2 = as_nan(_FLOAT_OP_OFFSET + 71)
        VAR3 = as_nan(_FLOAT_OP_OFFSET + 72)
        CHANGE_SIGN = as_nan(_FLOAT_OP_OFFSET + 73)
        CUBIC = as_nan(_FLOAT_OP_OFFSET + 74)
        A_SPLINE_LOOP = as_nan(_FLOAT_OP_OFFSET + 75)
        A_SUM_UNTIL = as_nan(_FLOAT_OP_OFFSET + 76)
        A_SUM_XY = as_nan(_FLOAT_OP_OFFSET + 77)
        A_SUM_SQR = as_nan(_FLOAT_OP_OFFSET + 78)
        A_LERP = as_nan(_FLOAT_OP_OFFSET + 79)

    class IntegerExpression:
        """RPN integer expression operators (long-encoded)."""
        L_ADD = _LONG_OFFSET + _INT_OP_OFFSET + 1
        L_SUB = _LONG_OFFSET + _INT_OP_OFFSET + 2
        L_MUL = _LONG_OFFSET + _INT_OP_OFFSET + 3
        L_DIV = _LONG_OFFSET + _INT_OP_OFFSET + 4
        L_MOD = _LONG_OFFSET + _INT_OP_OFFSET + 5
        L_SHL = _LONG_OFFSET + _INT_OP_OFFSET + 6
        L_SHR = _LONG_OFFSET + _INT_OP_OFFSET + 7
        L_USHR = _LONG_OFFSET + _INT_OP_OFFSET + 8
        L_OR = _LONG_OFFSET + _INT_OP_OFFSET + 9
        L_AND = _LONG_OFFSET + _INT_OP_OFFSET + 10
        L_XOR = _LONG_OFFSET + _INT_OP_OFFSET + 11
        L_COPY_SIGN = _LONG_OFFSET + _INT_OP_OFFSET + 12
        L_MIN = _LONG_OFFSET + _INT_OP_OFFSET + 13
        L_MAX = _LONG_OFFSET + _INT_OP_OFFSET + 14
        L_NEG = _LONG_OFFSET + _INT_OP_OFFSET + 15
        L_ABS = _LONG_OFFSET + _INT_OP_OFFSET + 16
        L_INCR = _LONG_OFFSET + _INT_OP_OFFSET + 17
        L_DECR = _LONG_OFFSET + _INT_OP_OFFSET + 18
        L_NOT = _LONG_OFFSET + _INT_OP_OFFSET + 19
        L_SIGN = _LONG_OFFSET + _INT_OP_OFFSET + 20
        L_CLAMP = _LONG_OFFSET + _INT_OP_OFFSET + 21
        L_IFELSE = _LONG_OFFSET + _INT_OP_OFFSET + 22
        L_MAD = _LONG_OFFSET + _INT_OP_OFFSET + 23
        L_VAR1 = _LONG_OFFSET + _INT_OP_OFFSET + 24
        L_VAR2 = _LONG_OFFSET + _INT_OP_OFFSET + 25

    class MatrixOp:
        """Matrix expression operators (NaN-encoded)."""
        _OFFSET = 0x320000
        IDENTITY = as_nan(_OFFSET + 1)
        ROT_X = as_nan(_OFFSET + 2)
        ROT_Y = as_nan(_OFFSET + 3)
        ROT_Z = as_nan(_OFFSET + 4)
        TRANSLATE_X = as_nan(_OFFSET + 5)
        TRANSLATE_Y = as_nan(_OFFSET + 6)
        TRANSLATE_Z = as_nan(_OFFSET + 7)
        TRANSLATE2 = as_nan(_OFFSET + 8)
        TRANSLATE3 = as_nan(_OFFSET + 9)
        SCALE_X = as_nan(_OFFSET + 10)
        SCALE_Y = as_nan(_OFFSET + 11)
        SCALE_Z = as_nan(_OFFSET + 12)
        SCALE2 = as_nan(_OFFSET + 13)
        SCALE3 = as_nan(_OFFSET + 14)
        MUL = as_nan(_OFFSET + 15)
        ROT_PZ = as_nan(_OFFSET + 16)
        ROT_AXIS = as_nan(_OFFSET + 17)
        PROJECTION = as_nan(_OFFSET + 18)

    class Animate:
        """Animation easing constants."""
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

    class ColorExpression:
        """Color interpolation types."""
        COLOR_COLOR_INTERPOLATE = 0
        ID_COLOR_INTERPOLATE = 1
        COLOR_ID_INTERPOLATE = 2
        ID_ID_INTERPOLATE = 3
        HSV_MODE = 4
        ARGB_MODE = 5
        IDARGB_MODE = 6

    class ImageScale:
        """Image scaling modes."""
        NONE = 0
        INSIDE = 1
        FILL_WIDTH = 2
        FILL_HEIGHT = 3
        FIT = 4
        CROP = 5
        FILL_BOUNDS = 6
        FIXED_SCALE = 7

    class TextAnchorMask:
        """Text anchor flags."""
        TEXT_RTL = 1
        MONOSPACE_MEASURE = 2
        MEASURE_EVERY_TIME = 4
        BASELINE_RELATIVE = 8

    class Haptic:
        """Haptic feedback constants."""
        NO_HAPTICS = 0
        LONG_PRESS = 1
        VIRTUAL_KEY = 2
        KEYBOARD_TAP = 3
        CLOCK_TICK = 4
        CONTEXT_CLICK = 5
        KEYBOARD_PRESS = 6
        KEYBOARD_RELEASE = 7
        VIRTUAL_KEY_RELEASE = 8
        TEXT_HANDLE_MOVE = 9
        GESTURE_START = 10
        GESTURE_END = 11
        CONFIRM = 12
        REJECT = 13
        TOGGLE_ON = 14
        TOGGLE_OFF = 15
        GESTURE_THRESHOLD_ACTIVATE = 16
        GESTURE_THRESHOLD_DEACTIVATE = 17
        DRAG_START = 18
        SEGMENT_TICK = 19
        SEGMENT_FREQUENT_TICK = 20

    class Time:
        """System time variable IDs (NaN-encoded)."""
        CONTINUOUS_SEC = as_nan(1)
        TIME_IN_SEC = as_nan(2)
        TIME_IN_MIN = as_nan(3)
        TIME_IN_HR = as_nan(4)
        CALENDAR_MONTH = as_nan(9)
        WEEK_DAY = as_nan(11)
        DAY_OF_MONTH = as_nan(12)
        OFFSET_TO_UTC = as_nan(10)
        ANIMATION_TIME = as_nan(30)
        ANIMATION_DELTA_TIME = as_nan(31)
        INT_EPOCH_SECOND = 0x100000000 + 32
        DAY_OF_YEAR = as_nan(34)
        YEAR = as_nan(35)

    class System:
        """System variable IDs (NaN-encoded)."""
        FONT_SIZE = as_nan(33)
        WINDOW_WIDTH = as_nan(5)
        WINDOW_HEIGHT = as_nan(6)
        API_LEVEL = as_nan(28)
        DENSITY = as_nan(27)
        ID_DEREF = 1073741824  # PaintOperation.PTR_DEREFERENCE
        sLightMode = 0.0

    class Touch:
        """Touch variable IDs and stop modes."""
        POSITION_X = as_nan(13)
        POSITION_Y = as_nan(14)
        VELOCITY_X = as_nan(15)
        VELOCITY_Y = as_nan(16)
        TOUCH_EVENT_TIME = as_nan(29)
        STOP_GENTLY = 0
        STOP_INSTANTLY = 1
        STOP_ENDS = 2
        STOP_NOTCHES_EVEN = 3
        STOP_NOTCHES_PERCENTS = 4
        STOP_NOTCHES_ABSOLUTE = 5
        STOP_ABSOLUTE_POS = 6
        STOP_NOTCHES_SINGLE_EVEN = 7

    class Sensor:
        """Sensor variable IDs (NaN-encoded)."""
        ACCELERATION_X = as_nan(17)
        ACCELERATION_Y = as_nan(18)
        ACCELERATION_Z = as_nan(19)
        GYRO_ROT_X = as_nan(20)
        GYRO_ROT_Y = as_nan(21)
        GYRO_ROT_Z = as_nan(22)
        MAGNETIC_X = as_nan(23)
        MAGNETIC_Y = as_nan(24)
        MAGNETIC_Z = as_nan(25)
        LIGHT = as_nan(26)

    class DocHeader:
        """Document header property keys."""
        DOC_WIDTH = 5
        DOC_HEIGHT = 6
        DOC_DENSITY_AT_GENERATION = 7
        DOC_DESIRED_FPS = 8
        DOC_CONTENT_DESCRIPTION = 9
        DOC_SOURCE = 11
        DOC_DATA_UPDATE = 12
        HOST_EXCEPTION_HANDLER = 13
        DOC_PROFILES = 14

    class Condition:
        """Conditional operation types."""
        EQ = 0
        NEQ = 1
        LT = 2
        LTE = 3
        GT = 4
        GTE = 5

    class Text:
        """Text alignment and overflow constants."""
        ALIGN_LEFT = 1
        ALIGN_RIGHT = 2
        ALIGN_CENTER = 3
        ALIGN_JUSTIFY = 4
        ALIGN_START = 5
        ALIGN_END = 6
        OVERFLOW_CLIP = 1
        OVERFLOW_VISIBLE = 2
        OVERFLOW_ELLIPSIS = 3
        OVERFLOW_START_ELLIPSIS = 4
        OVERFLOW_MIDDLE_ELLIPSIS = 5

    class TextFromFloat:
        """Number-to-text formatting flags."""
        PAD_AFTER_SPACE = 0
        PAD_AFTER_NONE = 1
        PAD_AFTER_ZERO = 3
        PAD_PRE_SPACE = 0
        PAD_PRE_NONE = 4
        PAD_PRE_ZERO = 12
        GROUPING_NONE = 0
        GROUPING_BY3 = 16
        GROUPING_BY4 = 32
        GROUPING_BY32 = 48
        SEPARATOR_PERIOD_COMMA = 64
        SEPARATOR_COMMA_PERIOD = 0
        SEPARATOR_SPACE_COMMA = 128
        SEPARATOR_UNDER_PERIOD = 192
        OPTIONS_NONE = 0
        OPTIONS_NEGATIVE_PARENTHESES = 256
        OPTIONS_ROUNDING = 512
        LEGACY_MODE = 1024
        FULL_FORMAT = 4096

    class TextTransform:
        """Text transformation operations."""
        TEXT_TO_LOWERCASE = 1
        TEXT_TO_UPPERCASE = 2
        TEXT_TRIM = 3
        TEXT_CAPITALIZE = 4
        TEXT_UPPERCASE_FIRST_CHAR = 5

    class Paint:
        """Paint style constants."""
        STYLE_FILL = 0
        STYLE_STROKE = 1
        STYLE_FILL_AND_STROKE = 2
        CAP_BUTT = 0
        CAP_ROUND = 1
        CAP_SQUARE = 2

    class BlendMode:
        """Android BlendMode ordinals for set_blend_mode()."""
        CLEAR = 0
        SRC = 1
        DST = 2
        SRC_OVER = 3
        DST_OVER = 4
        SRC_IN = 5
        DST_IN = 6
        SRC_OUT = 7
        DST_OUT = 8
        SRC_ATOP = 9
        DST_ATOP = 10
        XOR = 11
        PLUS = 12
        MODULATE = 13
        SCREEN = 14
        OVERLAY = 15
        DARKEN = 16
        LIGHTEN = 17

    class Texture:
        """Texture tile and filter modes."""
        TILE_CLAMP = 0
        TILE_MIRROR = 1
        TILE_REPEAT = 2
        TILE_DECAL = 3
        FILTER_DEFAULT = 0
        FILTER_NEAREST = 1
        FILTER_LINEAR = 2

    class PathExpression:
        """Path expression types."""
        SPLINE_PATH = 0
        LOOP_PATH = 1
        MONOTONIC_PATH = 2
        LINEAR_PATH = 4
        POLAR_PATH = 8

    class Layout:
        """Layout alignment constants."""
        START = 1
        CENTER = 2
        END = 3
        TOP = 4
        BOTTOM = 5
        FIRST_BASELINE = as_nan(36)
        LAST_BASELINE = as_nan(37)

    class PathCommand:
        """Path append command constants."""
        MOVE = 10
        LINE = 11
        QUADRATIC = 12
        CONIC = 13
        CUBIC = 14
        CLOSE = 15
        DONE = 16
        RESET = 17

    class PathEffect:
        """Path dash effect styles."""
        PATH_DASH_TRANSLATE = 0
        PATH_DASH_ROTATE = 1
        PATH_DASH_MORPH = 2

    class Theme:
        """Theme constants."""
        DARK = -2
        LIGHT = -3
        UNSPECIFIED = -1

    class RootContent:
        """RootContentBehavior constants."""
        NONE = 0
        SCROLL_HORIZONTAL = 1
        SCROLL_VERTICAL = 2
        SIZING_LAYOUT = 1
        SIZING_SCALE = 2
        ALIGNMENT_TOP = 1
        ALIGNMENT_VERTICAL_CENTER = 2
        ALIGNMENT_BOTTOM = 4
        ALIGNMENT_START = 16
        ALIGNMENT_HORIZONTAL_CENTER = 32
        ALIGNMENT_END = 64
        ALIGNMENT_CENTER = ALIGNMENT_HORIZONTAL_CENTER + ALIGNMENT_VERTICAL_CENTER  # 34
        SCALE_FILL_WIDTH = 2
        SCALE_FILL_HEIGHT = 3
        SCALE_FIT = 4
        SCALE_FILL_BOUNDS = 6

    class TextAttribute:
        """Text measurement attribute types."""
        MEASURE_WIDTH = 0
        MEASURE_HEIGHT = 1
        MEASURE_LEFT = 2
        MEASURE_RIGHT = 3
        MEASURE_TOP = 4
        MEASURE_BOTTOM = 5
        TEXT_LENGTH = 6

    class ColorAttribute:
        """Color component attribute types."""
        HUE = 0
        SATURATION = 1
        BRIGHTNESS = 2
        RED = 3
        GREEN = 4
        BLUE = 5
        ALPHA = 6

    class TimeAttributes:
        """Time attribute query types."""
        TIME_FROM_NOW_SEC = 0
        TIME_FROM_NOW_MIN = 1
        TIME_FROM_NOW_HR = 2
        TIME_FROM_ARG_SEC = 3
        TIME_FROM_ARG_MIN = 4
        TIME_FROM_ARG_HR = 5
        TIME_IN_SEC = 6
        TIME_IN_MIN = 7
        TIME_IN_HR = 8
        TIME_DAY_OF_MONTH = 9
        TIME_MONTH_VALUE = 10
        TIME_DAY_OF_WEEK = 11
        TIME_YEAR = 12
        TIME_FROM_LOAD_SEC = 14
        TIME_DAY_OF_YEAR = 15

    class Debug:
        """Debug message types."""
        SHOW_USAGE = 1

    class Skip:
        """Skip condition types."""
        IF_API_LESS_THAN = 1
        IF_API_GREATER_THAN = 2
        IF_API_EQUAL_TO = 3
        IF_API_NOT_EQUAL_TO = 4
        IF_PROFILE_INCLUDES = 5
        IF_PROFILE_EXCLUDES = 6

    class AndroidColors:
        """Standard system color identifiers."""
        GROUP = "android"
        BACKGROUND_DARK = 0
        BACKGROUND_LIGHT = 1
        BLACK = 2
        DARKER_GRAY = 3
        HOLO_BLUE_BRIGHT = 4
        HOLO_BLUE_DARK = 5
        HOLO_BLUE_LIGHT = 6
        HOLO_GREEN_DARK = 7
        HOLO_GREEN_LIGHT = 8
        HOLO_ORANGE_DARK = 9
        HOLO_ORANGE_LIGHT = 10
        HOLO_PURPLE = 11
        HOLO_RED_DARK = 12
        HOLO_RED_LIGHT = 13
        SYSTEM_ACCENT1_0 = 14
        SYSTEM_ACCENT1_10 = 15
        SYSTEM_ACCENT1_100 = 16
        SYSTEM_ACCENT1_1000 = 17
        SYSTEM_ACCENT1_200 = 18
        SYSTEM_ACCENT1_300 = 19
        SYSTEM_ACCENT1_400 = 20
        SYSTEM_ACCENT1_50 = 21
        SYSTEM_ACCENT1_500 = 22
        SYSTEM_ACCENT1_600 = 23
        SYSTEM_ACCENT1_700 = 24
        SYSTEM_ACCENT1_800 = 25
        SYSTEM_ACCENT1_900 = 26
        SYSTEM_ACCENT2_0 = 27
        SYSTEM_ACCENT2_10 = 28
        SYSTEM_ACCENT2_100 = 29
        SYSTEM_ACCENT2_1000 = 30
        SYSTEM_ACCENT2_200 = 30  # Note: same as 1000 in Java source
        SYSTEM_ACCENT2_300 = 32
        SYSTEM_ACCENT2_400 = 33
        SYSTEM_ACCENT2_50 = 34
        SYSTEM_ACCENT2_500 = 35
        SYSTEM_ACCENT2_600 = 36
        SYSTEM_ACCENT2_700 = 37
        SYSTEM_ACCENT2_800 = 38
        SYSTEM_ACCENT2_900 = 39
        SYSTEM_ACCENT3_0 = 40
        SYSTEM_ACCENT3_10 = 41
        SYSTEM_ACCENT3_100 = 42
        SYSTEM_ACCENT3_1000 = 43
        SYSTEM_ACCENT3_200 = 44
        SYSTEM_ACCENT3_300 = 45
        SYSTEM_ACCENT3_400 = 46
        SYSTEM_ACCENT3_50 = 47
        SYSTEM_ACCENT3_500 = 48
        SYSTEM_ACCENT3_600 = 49
        SYSTEM_ACCENT3_700 = 50
        SYSTEM_ACCENT3_800 = 51
        SYSTEM_ACCENT3_900 = 52
        SYSTEM_BACKGROUND_DARK = 53
        SYSTEM_BACKGROUND_LIGHT = 54
        SYSTEM_CONTROL_ACTIVATED_DARK = 55
        SYSTEM_CONTROL_ACTIVATED_LIGHT = 56
        SYSTEM_CONTROL_HIGHLIGHT_DARK = 57
        SYSTEM_CONTROL_HIGHLIGHT_LIGHT = 58
        SYSTEM_CONTROL_NORMAL_DARK = 59
        SYSTEM_CONTROL_NORMAL_LIGHT = 60
        SYSTEM_ERROR_0 = 61
        SYSTEM_ERROR_620 = 62
        SYSTEM_ERROR_6300 = 63
        SYSTEM_ERROR_64000 = 64
        SYSTEM_ERROR_200 = 65
        SYSTEM_ERROR_300 = 66
        SYSTEM_ERROR_400 = 67
        SYSTEM_ERROR_50 = 68
        SYSTEM_ERROR_500 = 69
        SYSTEM_ERROR_600 = 70
        SYSTEM_ERROR_700 = 71
        SYSTEM_ERROR_800 = 72
        SYSTEM_ERROR_900 = 73
        SYSTEM_ERROR_CONTAINER_DARK = 74
        SYSTEM_ERROR_CONTAINER_LIGHT = 75
        SYSTEM_ERROR_DARK = 76
        SYSTEM_ERROR_LIGHT = 77
        SYSTEM_NEUTRAL78_0 = 78
        SYSTEM_NEUTRAL79_790 = 79
        SYSTEM_NEUTRAL80_8000 = 80
        SYSTEM_NEUTRAL81_81000 = 81
        SYSTEM_NEUTRAL82_200 = 82
        SYSTEM_NEUTRAL83_300 = 83
        SYSTEM_NEUTRAL84_400 = 84
        SYSTEM_NEUTRAL85_50 = 85
        SYSTEM_NEUTRAL86_500 = 86
        SYSTEM_NEUTRAL87_600 = 87
        SYSTEM_NEUTRAL88_700 = 88
        SYSTEM_NEUTRAL89_800 = 89
        SYSTEM_NEUTRAL90_900 = 90
        SYSTEM_NEUTRAL2_0 = 91
        SYSTEM_NEUTRAL2_920 = 92
        SYSTEM_NEUTRAL2_9300 = 93
        SYSTEM_NEUTRAL2_94000 = 94
        SYSTEM_NEUTRAL2_200 = 95
        SYSTEM_NEUTRAL2_300 = 96
        SYSTEM_NEUTRAL2_400 = 97
        SYSTEM_NEUTRAL2_50 = 98
        SYSTEM_NEUTRAL2_500 = 99
        SYSTEM_NEUTRAL2_600 = 100
        SYSTEM_NEUTRAL2_700 = 101
        SYSTEM_NEUTRAL2_800 = 102
        SYSTEM_NEUTRAL2_900 = 103
        SYSTEM_ON_BACKGROUND_DARK = 104
        SYSTEM_ON_BACKGROUND_LIGHT = 105
        SYSTEM_ON_ERROR_CONTAINER_DARK = 106
        SYSTEM_ON_ERROR_CONTAINER_LIGHT = 107
        SYSTEM_ON_ERROR_DARK = 108
        SYSTEM_ON_ERROR_LIGHT = 109
        SYSTEM_ON_PRIMARY_CONTAINER_DARK = 110
        SYSTEM_ON_PRIMARY_CONTAINER_LIGHT = 111
        SYSTEM_ON_PRIMARY_DARK = 112
        SYSTEM_ON_PRIMARY_FIXED = 113
        SYSTEM_ON_PRIMARY_FIXED_VARIANT = 114
        SYSTEM_ON_PRIMARY_LIGHT = 115
        SYSTEM_ON_SECONDARY_CONTAINER_DARK = 116
        SYSTEM_ON_SECONDARY_CONTAINER_LIGHT = 117
        SYSTEM_ON_SECONDARY_DARK = 118
        SYSTEM_ON_SECONDARY_FIXED = 119
        SYSTEM_ON_SECONDARY_FIXED_VARIANT = 120
        SYSTEM_ON_SECONDARY_LIGHT = 121
        SYSTEM_ON_SURFACE_DARK = 122
        SYSTEM_ON_SURFACE_DISABLED = 123
        SYSTEM_ON_SURFACE_LIGHT = 124
        SYSTEM_ON_SURFACE_VARIANT_DARK = 125
        SYSTEM_ON_SURFACE_VARIANT_LIGHT = 126
        SYSTEM_ON_TERTIARY_CONTAINER_DARK = 127
        SYSTEM_ON_TERTIARY_CONTAINER_LIGHT = 128
        SYSTEM_ON_TERTIARY_DARK = 129
        SYSTEM_ON_TERTIARY_FIXED = 130
        SYSTEM_ON_TERTIARY_FIXED_VARIANT = 131
        SYSTEM_ON_TERTIARY_LIGHT = 132
        SYSTEM_OUTLINE_DARK = 133
        SYSTEM_OUTLINE_DISABLED = 134
        SYSTEM_OUTLINE_LIGHT = 135
        SYSTEM_OUTLINE_VARIANT_DARK = 136
        SYSTEM_OUTLINE_VARIANT_LIGHT = 137
        SYSTEM_PALETTE_KEY_COLOR_NEUTRAL_DARK = 138
        SYSTEM_PALETTE_KEY_COLOR_NEUTRAL_LIGHT = 139
        SYSTEM_PALETTE_KEY_COLOR_NEUTRAL_VARIANT_DARK = 140
        SYSTEM_PALETTE_KEY_COLOR_NEUTRAL_VARIANT_LIGHT = 141
        SYSTEM_PALETTE_KEY_COLOR_PRIMARY_DARK = 142
        SYSTEM_PALETTE_KEY_COLOR_PRIMARY_LIGHT = 143
        SYSTEM_PALETTE_KEY_COLOR_SECONDARY_DARK = 144
        SYSTEM_PALETTE_KEY_COLOR_SECONDARY_LIGHT = 145
        SYSTEM_PALETTE_KEY_COLOR_TERTIARY_DARK = 146
        SYSTEM_PALETTE_KEY_COLOR_TERTIARY_LIGHT = 147
        SYSTEM_PRIMARY_CONTAINER_DARK = 148
        SYSTEM_PRIMARY_CONTAINER_LIGHT = 149
        SYSTEM_PRIMARY_DARK = 150
        SYSTEM_PRIMARY_FIXED = 151
        SYSTEM_PRIMARY_FIXED_DIM = 152
        SYSTEM_PRIMARY_LIGHT = 153
        SYSTEM_SECONDARY_CONTAINER_DARK = 154
        SYSTEM_SECONDARY_CONTAINER_LIGHT = 155
        SYSTEM_SECONDARY_DARK = 156
        SYSTEM_SECONDARY_FIXED = 157
        SYSTEM_SECONDARY_FIXED_DIM = 158
        SYSTEM_SECONDARY_LIGHT = 159
        SYSTEM_SURFACE_BRIGHT_DARK = 160
        SYSTEM_SURFACE_BRIGHT_LIGHT = 161
        SYSTEM_SURFACE_CONTAINER_DARK = 162
        SYSTEM_SURFACE_CONTAINER_HIGH_DARK = 163
        SYSTEM_SURFACE_CONTAINER_HIGH_LIGHT = 164
        SYSTEM_SURFACE_CONTAINER_HIGHEST_DARK = 165
        SYSTEM_SURFACE_CONTAINER_HIGHEST_LIGHT = 166
        SYSTEM_SURFACE_CONTAINER_LIGHT = 167
        SYSTEM_SURFACE_CONTAINER_LOW_DARK = 168
        SYSTEM_SURFACE_CONTAINER_LOW_LIGHT = 169
        SYSTEM_SURFACE_CONTAINER_LOWEST_DARK = 170
        SYSTEM_SURFACE_CONTAINER_LOWEST_LIGHT = 171
        SYSTEM_SURFACE_DARK = 172
        SYSTEM_SURFACE_DIM_DARK = 173
        SYSTEM_SURFACE_DIM_LIGHT = 174
        SYSTEM_SURFACE_DISABLED = 175
        SYSTEM_SURFACE_LIGHT = 176
        SYSTEM_SURFACE_VARIANT_DARK = 177
        SYSTEM_SURFACE_VARIANT_LIGHT = 178
        SYSTEM_TERTIARY_CONTAINER_DARK = 179
        SYSTEM_TERTIARY_CONTAINER_LIGHT = 180
        SYSTEM_TERTIARY_DARK = 181
        SYSTEM_TERTIARY_FIXED = 182
        SYSTEM_TERTIARY_FIXED_DIM = 183
        SYSTEM_TERTIARY_LIGHT = 184
        SYSTEM_TEXT_HINT_INVERSE_DARK = 185
        SYSTEM_TEXT_HINT_INVERSE_LIGHT = 186
        SYSTEM_TEXT_PRIMARY_INVERSE_DARK = 187
        SYSTEM_TEXT_PRIMARY_INVERSE_DISABLE_ONLY_DARK = 188
        SYSTEM_TEXT_PRIMARY_INVERSE_DISABLE_ONLY_LIGHT = 189
        SYSTEM_TEXT_PRIMARY_INVERSE_LIGHT = 190
        SYSTEM_TEXT_SECONDARY_AND_TERTIARY_INVERSE_DARK = 191
        SYSTEM_TEXT_SECONDARY_AND_TERTIARY_INVERSE_DISABLED_DARK = 192
        SYSTEM_TEXT_SECONDARY_AND_TERTIARY_INVERSE_DISABLED_LIGHT = 193
        SYSTEM_TEXT_SECONDARY_AND_TERTIARY_INVERSE_LIGHT = 194
        TAB_INDICATOR_TEXT = 195

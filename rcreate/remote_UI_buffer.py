"""RemoteComposeBuffer — binary protocol encoder for RemoteCompose operations.

Wraps a WireBuffer and provides typed methods to emit each operation.
Matches Java's RemoteComposeBuffer.java.
"""

import struct
import math

from .wire_buffer import WireBuffer
from . import operations as Ops
from .types.nan_utils import as_nan, id_from_nan, int_bits_to_float


# Header constants
MAGIC_NUMBER = 0x048C0000
MAJOR_VERSION = 1
MINOR_VERSION = 1
PATCH_VERSION = 0
DOCUMENT_API_LEVEL = 8

# Header data type tags (shifted left 10 bits)
DATA_TYPE_INT = 0
DATA_TYPE_FLOAT = 1
DATA_TYPE_LONG = 2
DATA_TYPE_STRING = 3

# Header property tags
DOC_WIDTH = 5
DOC_HEIGHT = 6
DOC_DENSITY_AT_GENERATION = 7
DOC_DESIRED_FPS = 8
DOC_CONTENT_DESCRIPTION = 9
DOC_SOURCE = 11
DOC_DATA_UPDATE = 12
HOST_EXCEPTION_HANDLER = 13
DOC_PROFILES = 14

# Easing constants
EASING_CUBIC_STANDARD = 1
EASING_CUBIC_ACCELERATE = 2
EASING_CUBIC_DECELERATE = 3
EASING_CUBIC_LINEAR = 4
EASING_CUBIC_ANTICIPATE = 5
EASING_CUBIC_OVERSHOOT = 6
EASING_CUBIC_CUSTOM = 11
EASING_SPLINE_CUSTOM = 12
EASING_EASE_OUT_BOUNCE = 13
EASING_EASE_OUT_ELASTIC = 14


class RemoteComposeBuffer:
    def __init__(self, api_level: int = DOCUMENT_API_LEVEL):
        self._buffer = WireBuffer()
        self._api_level = api_level
        self._profile_mask = 0
        self._last_component_id = 0
        self._generated_component_id = -1
        # All operations are valid by default in Python version
        self._valid_ops = set(range(256))

    def get_component_id(self, id: int) -> int:
        """Auto-generate component IDs matching Java's getComponentId().

        If id == -1, decrement and return a new auto-generated ID.
        Otherwise return the id as-is.
        """
        if id == -1:
            self._generated_component_id -= 1
            return self._generated_component_id
        return id

    def reset(self, expected_size: int = 1000000):
        self._buffer = WireBuffer(expected_size)
        self._last_component_id = 0
        self._generated_component_id = -1

    @property
    def buffer(self) -> WireBuffer:
        return self._buffer

    def get_last_component_id(self) -> int:
        return self._last_component_id

    def set_version(self, api_level: int, profiles: int, supported_ops: set = None):
        self._api_level = api_level
        self._profile_mask = profiles

    def _start(self, op_code: int):
        """Write the opcode byte."""
        self._buffer.write_byte(op_code)

    # ── Header ────────────────────────────────────────────────────

    def add_header(self, tags: list, values: list):
        """Write V7+ header with property map."""
        self._start(Ops.HEADER)
        if self._api_level >= 7:
            self._buffer.write_int(MAJOR_VERSION | MAGIC_NUMBER)
            self._buffer.write_int(MINOR_VERSION)
            self._buffer.write_int(PATCH_VERSION)
            self._buffer.write_int(len(tags))
            self._write_header_map(tags, values)
        elif self._api_level == 6:
            self._buffer.write_int(1)  # major (hardcoded in Java)
            self._buffer.write_int(0)  # minor (hardcoded in Java)
            self._buffer.write_int(0)  # patch (hardcoded in Java)
            width = self._get_header_int(tags, values, DOC_WIDTH)
            height = self._get_header_int(tags, values, DOC_HEIGHT)
            self._buffer.write_int(width)
            self._buffer.write_int(height)
            self._buffer.write_long(0)

    def header(self, width: int, height: int, density: float, capabilities: int):
        """Write V6 header."""
        self._start(Ops.HEADER)
        self._buffer.write_int(MAJOR_VERSION)
        self._buffer.write_int(MINOR_VERSION)
        self._buffer.write_int(PATCH_VERSION)
        self._buffer.write_int(width)
        self._buffer.write_int(height)
        self._buffer.write_long(capabilities)

    def _write_header_map(self, tags, values):
        for i in range(len(tags)):
            tag = tags[i]
            val = values[i]
            if isinstance(val, str):
                encoded_tag = tag | (DATA_TYPE_STRING << 10)
                self._buffer.write_short(encoded_tag)
                data = val.encode('utf-8')
                self._buffer.write_short(len(data) + 4)
                self._buffer.write_int(len(data))
                self._buffer._ensure_capacity(len(data))
                self._buffer._buffer[self._buffer._index:self._buffer._index + len(data)] = data
                self._buffer._index += len(data)
                self._buffer._update_size()
            elif isinstance(val, int) and not isinstance(val, bool):
                if val > 0x7FFFFFFF or val < -0x80000000:
                    # Long
                    encoded_tag = tag | (DATA_TYPE_LONG << 10)
                    self._buffer.write_short(encoded_tag)
                    self._buffer.write_short(8)
                    self._buffer.write_long(val)
                else:
                    encoded_tag = tag | (DATA_TYPE_INT << 10)
                    self._buffer.write_short(encoded_tag)
                    self._buffer.write_short(4)
                    self._buffer.write_int(val)
            elif isinstance(val, float):
                encoded_tag = tag | (DATA_TYPE_FLOAT << 10)
                self._buffer.write_short(encoded_tag)
                self._buffer.write_short(4)
                self._buffer.write_float(val)

    def _get_header_int(self, tags, values, key) -> int:
        for i in range(len(tags)):
            if tags[i] == key:
                return values[i] if isinstance(values[i], int) else 0
        return 0

    # ── Root Content Description ──────────────────────────────────

    def add_root_content_description(self, content_desc_id: int):
        if content_desc_id != 0:
            self._start(Ops.ROOT_CONTENT_DESCRIPTION)
            self._buffer.write_int(content_desc_id)

    # ── Text Data ─────────────────────────────────────────────────

    def add_text(self, id: int, text: str):
        self._start(Ops.DATA_TEXT)
        self._buffer.write_int(id)
        self._buffer.write_utf8(text)

    def text_merge(self, id: int, id1: int, id2: int) -> int:
        self._start(Ops.TEXT_MERGE)
        self._buffer.write_int(id)
        self._buffer.write_int(id1)
        self._buffer.write_int(id2)
        return id

    def text_subtext(self, id: int, txt_id: int, start: float, length: float):
        self._start(Ops.TEXT_SUBTEXT)
        self._buffer.write_int(id)
        self._buffer.write_int(txt_id)
        self._buffer.write_float(start)
        self._buffer.write_float(length)

    def text_transform(self, id: int, txt_id: int, start: float, length: float, operation: int):
        self._start(Ops.TEXT_TRANSFORM)
        self._buffer.write_int(id)
        self._buffer.write_int(txt_id)
        self._buffer.write_float(start)
        self._buffer.write_float(length)
        self._buffer.write_int(operation)

    def text_measure(self, id: int, text_id: int, mode: int):
        self._start(Ops.TEXT_MEASURE)
        self._buffer.write_int(id)
        self._buffer.write_int(text_id)
        self._buffer.write_int(mode)

    def text_length(self, id: int, text_id: int):
        self._start(Ops.TEXT_LENGTH)
        self._buffer.write_int(id)
        self._buffer.write_int(text_id)

    def text_lookup(self, id: int, array_id, index):
        from .types.nan_utils import id_from_nan
        self._start(Ops.TEXT_LOOKUP)
        self._buffer.write_int(id)
        # Java writes idFromNan(dataSet) as int, not the NaN float
        dataset_id = id_from_nan(array_id) if isinstance(array_id, float) else array_id
        self._buffer.write_int(dataset_id)
        self._buffer.write_float(float(index))

    def create_text_from_float(self, id: int, value: float, before: int, after: int, flags: int) -> int:
        self._start(Ops.TEXT_FROM_FLOAT)
        self._buffer.write_int(id)
        self._buffer.write_float(value)
        self._buffer.write_short(before)
        self._buffer.write_short(after)
        self._buffer.write_int(flags)
        return id

    # ── Named Variables ───────────────────────────────────────────

    def set_named_variable(self, id: int, name: str, var_type: int):
        self._start(Ops.NAMED_VARIABLE)
        self._buffer.write_int(id)
        self._buffer.write_int(var_type)
        self._buffer.write_utf8(name)

    # ── Draw Operations ───────────────────────────────────────────

    def add_draw_rect(self, left: float, top: float, right: float, bottom: float):
        self._start(Ops.DRAW_RECT)
        self._buffer.write_float(left)
        self._buffer.write_float(top)
        self._buffer.write_float(right)
        self._buffer.write_float(bottom)

    def add_draw_round_rect(self, left: float, top: float, right: float, bottom: float,
                            radius_x: float, radius_y: float):
        self._start(Ops.DRAW_ROUND_RECT)
        self._buffer.write_float(left)
        self._buffer.write_float(top)
        self._buffer.write_float(right)
        self._buffer.write_float(bottom)
        self._buffer.write_float(radius_x)
        self._buffer.write_float(radius_y)

    def add_draw_circle(self, center_x: float, center_y: float, radius: float):
        self._start(Ops.DRAW_CIRCLE)
        self._buffer.write_float(center_x)
        self._buffer.write_float(center_y)
        self._buffer.write_float(radius)

    def add_draw_line(self, x1: float, y1: float, x2: float, y2: float):
        self._start(Ops.DRAW_LINE)
        self._buffer.write_float(x1)
        self._buffer.write_float(y1)
        self._buffer.write_float(x2)
        self._buffer.write_float(y2)

    def add_draw_oval(self, left: float, top: float, right: float, bottom: float):
        self._start(Ops.DRAW_OVAL)
        self._buffer.write_float(left)
        self._buffer.write_float(top)
        self._buffer.write_float(right)
        self._buffer.write_float(bottom)

    def add_draw_arc(self, left: float, top: float, right: float, bottom: float,
                     start_angle: float, sweep_angle: float):
        self._start(Ops.DRAW_ARC)
        self._buffer.write_float(left)
        self._buffer.write_float(top)
        self._buffer.write_float(right)
        self._buffer.write_float(bottom)
        self._buffer.write_float(start_angle)
        self._buffer.write_float(sweep_angle)

    def add_draw_sector(self, left: float, top: float, right: float, bottom: float,
                        start_angle: float, sweep_angle: float):
        self._start(Ops.DRAW_SECTOR)
        self._buffer.write_float(left)
        self._buffer.write_float(top)
        self._buffer.write_float(right)
        self._buffer.write_float(bottom)
        self._buffer.write_float(start_angle)
        self._buffer.write_float(sweep_angle)

    def add_draw_path(self, path_id: int):
        self._start(Ops.DRAW_PATH)
        self._buffer.write_int(path_id)

    def add_draw_tween_path(self, path1_id: int, path2_id: int, tween: float,
                            start: float, stop: float):
        self._start(Ops.DRAW_TWEEN_PATH)
        self._buffer.write_int(path1_id)
        self._buffer.write_int(path2_id)
        self._buffer.write_float(tween)
        self._buffer.write_float(start)
        self._buffer.write_float(stop)

    def add_draw_bitmap(self, image_id: int, left: float, top: float,
                        right: float, bottom: float, content_desc_id: int):
        self._start(Ops.DRAW_BITMAP)
        self._buffer.write_int(image_id)
        self._buffer.write_float(left)
        self._buffer.write_float(top)
        self._buffer.write_float(right)
        self._buffer.write_float(bottom)
        self._buffer.write_int(content_desc_id)

    def draw_scaled_bitmap(self, image_id: int,
                           src_left: float, src_top: float, src_right: float, src_bottom: float,
                           dst_left: float, dst_top: float, dst_right: float, dst_bottom: float,
                           scale_type: int, scale_factor: float, content_desc_id: int):
        self._start(Ops.DRAW_BITMAP_SCALED)
        self._buffer.write_int(image_id)
        self._buffer.write_float(src_left)
        self._buffer.write_float(src_top)
        self._buffer.write_float(src_right)
        self._buffer.write_float(src_bottom)
        self._buffer.write_float(dst_left)
        self._buffer.write_float(dst_top)
        self._buffer.write_float(dst_right)
        self._buffer.write_float(dst_bottom)
        self._buffer.write_int(scale_type)
        self._buffer.write_float(scale_factor)
        self._buffer.write_int(content_desc_id)

    def add_draw_text_run(self, text_id: int, start: int, end: int,
                          context_start: int, context_end: int,
                          x: float, y: float, rtl: bool):
        self._start(Ops.DRAW_TEXT_RUN)
        self._buffer.write_int(text_id)
        self._buffer.write_int(start)
        self._buffer.write_int(end)
        self._buffer.write_int(context_start)
        self._buffer.write_int(context_end)
        self._buffer.write_float(x)
        self._buffer.write_float(y)
        self._buffer.write_byte(1 if rtl else 0)

    def draw_text_anchored(self, text_id: int, x: float, y: float,
                           pan_x: float, pan_y: float, flags: int):
        self._start(Ops.DRAW_TEXT_ANCHOR)
        self._buffer.write_int(text_id)
        self._buffer.write_float(x)
        self._buffer.write_float(y)
        self._buffer.write_float(pan_x)
        self._buffer.write_float(pan_y)
        self._buffer.write_int(flags)

    def add_draw_text_on_path(self, text_id: int, path_id: int,
                              h_offset: float, v_offset: float):
        self._start(Ops.DRAW_TEXT_ON_PATH)
        self._buffer.write_int(text_id)
        self._buffer.write_int(path_id)
        self._buffer.write_float(h_offset)
        self._buffer.write_float(v_offset)

    def add_draw_text_on_circle(self, text_id: int, center_x: float, center_y: float,
                                radius: float, start_angle: float, warp_radius_offset: float,
                                alignment, placement):
        self._start(Ops.DRAW_TEXT_ON_CIRCLE)
        self._buffer.write_int(text_id)
        self._buffer.write_float(center_x)
        self._buffer.write_float(center_y)
        self._buffer.write_float(radius)
        self._buffer.write_float(start_angle)
        self._buffer.write_float(warp_radius_offset)
        self._buffer.write_byte(alignment if isinstance(alignment, int) else alignment.value)
        self._buffer.write_byte(placement if isinstance(placement, int) else placement.value)

    def add_draw_bitmap_font_text_run(self, text_id: int, bitmap_font_id: int,
                                      start: int, end: int, x: float, y: float,
                                      glyph_spacing: float):
        self._start(Ops.DRAW_BITMAP_FONT_TEXT_RUN)
        self._buffer.write_int(text_id)
        self._buffer.write_int(bitmap_font_id)
        self._buffer.write_int(start)
        self._buffer.write_int(end)
        self._buffer.write_float(x)
        self._buffer.write_float(y)
        self._buffer.write_float(glyph_spacing)

    def draw_bitmap_text_anchored(self, text_id: int, bitmap_font_id: int,
                                  start: float, end: float, x: float, y: float,
                                  pan_x: float, pan_y: float, glyph_spacing: float):
        self._start(Ops.DRAW_BITMAP_TEXT_ANCHORED)
        self._buffer.write_int(text_id)
        self._buffer.write_int(bitmap_font_id)
        self._buffer.write_float(start)
        self._buffer.write_float(end)
        self._buffer.write_float(x)
        self._buffer.write_float(y)
        self._buffer.write_float(pan_x)
        self._buffer.write_float(pan_y)
        self._buffer.write_float(glyph_spacing)

    def draw_component_content(self):
        self._start(Ops.DRAW_CONTENT)

    # ── Paint ─────────────────────────────────────────────────────

    def add_paint(self, paint_bundle):
        """Write paint data from a PaintBundle."""
        self._start(Ops.PAINT_VALUES)
        paint_bundle.write(self._buffer)

    # ── Path Data ─────────────────────────────────────────────────

    def add_path_data(self, id: int, data: list, winding: int = 0) -> int:
        self._start(Ops.DATA_PATH)
        self._buffer.write_int(id | (winding << 24))
        self._buffer.write_float_array(data)
        return id

    def path_tween(self, out_id: int, pid1: int, pid2: int, tween: float) -> int:
        self._start(Ops.PATH_TWEEN)
        self._buffer.write_int(out_id)
        self._buffer.write_int(pid1)
        self._buffer.write_int(pid2)
        self._buffer.write_float(tween)
        return out_id

    def path_create(self, out_id: int, x: float, y: float) -> int:
        self._start(Ops.PATH_CREATE)
        self._buffer.write_int(out_id)
        self._buffer.write_float(x)
        self._buffer.write_float(y)
        return out_id

    def path_append(self, path_id: int, *data: float):
        self._start(Ops.PATH_ADD)
        self._buffer.write_int(path_id)
        self._buffer.write_int(len(data))
        for f in data:
            self._buffer.write_float(f)

    def path_combine(self, id: int, path1: int, path2: int, op: int):
        self._start(Ops.PATH_COMBINE)
        self._buffer.write_int(id)
        self._buffer.write_int(path1)
        self._buffer.write_int(path2)
        self._buffer.write_byte(op)

    def add_path_expression(self, id: int, exp_x: list, exp_y: list,
                            start: float, end: float, count: float, flags: int):
        self._start(Ops.PATH_EXPRESSION)
        self._buffer.write_int(id)
        self._buffer.write_int(flags)
        self._buffer.write_float(start)
        self._buffer.write_float(end)
        self._buffer.write_float(count)
        self._buffer.write_float_array(exp_x)
        self._buffer.write_float_array(exp_y)

    # ── Matrix ────────────────────────────────────────────────────

    def add_matrix_translate(self, dx: float, dy: float):
        self._start(Ops.MATRIX_TRANSLATE)
        self._buffer.write_float(dx)
        self._buffer.write_float(dy)

    def add_matrix_scale(self, sx: float, sy: float, cx: float = float('nan'), cy: float = float('nan')):
        self._start(Ops.MATRIX_SCALE)
        self._buffer.write_float(sx)
        self._buffer.write_float(sy)
        self._buffer.write_float(cx)
        self._buffer.write_float(cy)

    def add_matrix_rotate(self, angle: float, cx: float, cy: float):
        self._start(Ops.MATRIX_ROTATE)
        self._buffer.write_float(angle)
        self._buffer.write_float(cx)
        self._buffer.write_float(cy)

    def add_matrix_skew(self, sx: float, sy: float):
        self._start(Ops.MATRIX_SKEW)
        self._buffer.write_float(sx)
        self._buffer.write_float(sy)

    def add_matrix_save(self):
        self._start(Ops.MATRIX_SAVE)

    def add_matrix_restore(self):
        self._start(Ops.MATRIX_RESTORE)

    def set_matrix_from_path(self, path_id: int, fraction: float, v_offset: float, flags: int):
        self._start(Ops.MATRIX_FROM_PATH)
        self._buffer.write_int(path_id)
        self._buffer.write_float(fraction)
        self._buffer.write_float(v_offset)
        self._buffer.write_int(flags)

    def add_matrix_vector_math(self, matrix_id: float, op_type: int, from_vec: list, out_ids: list):
        from .types.nan_utils import id_from_nan
        self._start(Ops.MATRIX_VECTOR_MATH)
        self._buffer.write_short(op_type)
        self._buffer.write_int(id_from_nan(matrix_id))
        self._buffer.write_int(len(out_ids))
        for i in out_ids:
            self._buffer.write_int(i)
        self._buffer.write_int(len(from_vec))
        for f in from_vec:
            self._buffer.write_float(f)

    # ── Clip ──────────────────────────────────────────────────────

    def add_clip_rect(self, left: float, top: float, right: float, bottom: float):
        self._start(Ops.CLIP_RECT)
        self._buffer.write_float(left)
        self._buffer.write_float(top)
        self._buffer.write_float(right)
        self._buffer.write_float(bottom)

    def add_clip_path(self, path_id: int):
        self._start(Ops.CLIP_PATH)
        self._buffer.write_int(path_id)

    # ── Float/Integer Data ────────────────────────────────────────

    def add_float(self, id: int, value: float) -> float:
        self._start(Ops.DATA_FLOAT)
        self._buffer.write_int(id)
        self._buffer.write_float(value)
        return as_nan(id)

    def add_animated_float(self, id: int, value: list, animation: list = None):
        self._start(Ops.ANIMATED_FLOAT)
        self._buffer.write_int(id)
        length = len(value)
        if animation is not None:
            length |= (len(animation) << 16)
        self._buffer.write_int(length)
        for v in value:
            self._buffer.write_float(v)
        if animation is not None:
            for v in animation:
                self._buffer.write_float(v)

    def add_integer(self, id: int, value: int):
        self._start(Ops.DATA_INT)
        self._buffer.write_int(id)
        self._buffer.write_int(value)

    def add_integer_expression(self, id: int, mask: int, values: list):
        self._start(Ops.INTEGER_EXPRESSION)
        self._buffer.write_int(id)
        self._buffer.write_int(mask)
        self._buffer.write_int(len(values))
        for v in values:
            self._buffer.write_int(v)

    def add_long(self, id: int, value: int):
        self._start(Ops.DATA_LONG)
        self._buffer.write_int(id)
        self._buffer.write_long(value)

    def add_boolean(self, id: int, value: bool):
        self._start(Ops.DATA_BOOLEAN)
        self._buffer.write_int(id)
        self._buffer.write_byte(1 if value else 0)

    # ── Color ─────────────────────────────────────────────────────

    def add_color(self, id: int, color: int):
        self._start(Ops.COLOR_CONSTANT)
        self._buffer.write_int(id)
        self._buffer.write_int(color)

    def add_color_expression(self, id: int, *args):
        """Write a color expression. Matches Java ColorExpression.apply().

        Always writes: opcode + id(int) + param1(int) + param2(int) + param3(int) + param4(int).
        Dispatches based on arg types to match Java overloads.
        """
        import struct
        self._start(Ops.COLOR_EXPRESSIONS)
        self._buffer.write_int(id)

        if len(args) == 4 and isinstance(args[0], int) and all(isinstance(a, float) for a in args[1:]):
            # HSV with alpha: addColorExpression(id, alpha, hue, sat, value)
            HSV_MODE = 4
            alpha = args[0]
            hue, sat, value = args[1], args[2], args[3]
            mode = HSV_MODE | (alpha << 16)
            self._buffer.write_int(mode)
            self._buffer.write_float(hue)
            self._buffer.write_float(sat)
            self._buffer.write_float(value)
        elif len(args) == 3 and all(isinstance(a, float) for a in args):
            # HSV mode: addColorExpression(id, hue, sat, value) — alpha defaults to 0xFF
            HSV_MODE = 4
            hue, sat, value = args
            alpha = 0xFF
            mode = HSV_MODE | (alpha << 16)
            self._buffer.write_int(mode)
            self._buffer.write_float(hue)
            self._buffer.write_float(sat)
            self._buffer.write_float(value)
        elif len(args) == 4 and all(isinstance(a, float) for a in args):
            # ARGB mode: addColorExpression(id, alpha, red, green, blue)
            import math
            ARGB_MODE = 5
            IDARGB_MODE = 6
            alpha, red, green, blue = args
            if math.isnan(alpha):
                from .types.nan_utils import id_from_nan
                param1 = IDARGB_MODE | (id_from_nan(alpha) << 16)
            else:
                param1 = ARGB_MODE | (int(alpha * 1024) << 16)
            self._buffer.write_int(param1)
            self._buffer.write_int(struct.unpack('>I', struct.pack('>f', red))[0])
            self._buffer.write_int(struct.unpack('>I', struct.pack('>f', green))[0])
            self._buffer.write_int(struct.unpack('>I', struct.pack('>f', blue))[0])
        elif len(args) == 3 and isinstance(args[0], int) and isinstance(args[1], int) and isinstance(args[2], float):
            # COLOR_COLOR_INTERPOLATE: addColorExpression(color1, color2, tween)
            COLOR_COLOR_INTERPOLATE = 0
            self._buffer.write_int(COLOR_COLOR_INTERPOLATE)
            self._buffer.write_int(args[0])
            self._buffer.write_int(args[1])
            self._buffer.write_float(args[2])
        else:
            # Generic: mode(int), color1(int), color2(int), tween(float/int)
            for a in args:
                if isinstance(a, float):
                    self._buffer.write_float(a)
                elif isinstance(a, int):
                    self._buffer.write_int(a)

    def add_themed_color(self, id: int, group_id: int, light_id: int, dark_id: int,
                         light_fallback: int, dark_fallback: int):
        self._start(Ops.COLOR_THEME)
        self._buffer.write_int(id)
        self._buffer.write_int(group_id)
        self._buffer.write_short(light_id)
        self._buffer.write_short(dark_id)
        self._buffer.write_int(light_fallback)
        self._buffer.write_int(dark_fallback)

    def get_color_attribute(self, id: int, base_color: int, attr_type: int):
        self._start(Ops.ATTRIBUTE_COLOR)
        self._buffer.write_int(id)
        self._buffer.write_int(base_color)
        self._buffer.write_short(attr_type)

    # ── Matrix Expression ─────────────────────────────────────────

    def add_matrix_expression(self, id: int, values: list, type: int = 0):
        self._start(Ops.MATRIX_EXPRESSION)
        self._buffer.write_int(id)
        self._buffer.write_int(type)
        self._buffer.write_float_array(values)

    def add_matrix_constant(self, id: int, values: list, type: int = 0):
        self._start(Ops.MATRIX_CONSTANT)
        self._buffer.write_int(id)
        self._buffer.write_int(type)
        self._buffer.write_float_array(values)

    # ── Theme ─────────────────────────────────────────────────────

    def set_theme(self, theme: int):
        self._start(Ops.THEME)
        self._buffer.write_int(theme)

    # ── Click Area ────────────────────────────────────────────────

    def add_click_area(self, id: int, content_desc_id: int,
                       left: float, top: float, right: float, bottom: float,
                       metadata_id: int):
        self._start(Ops.CLICK_AREA)
        self._buffer.write_int(id)
        self._buffer.write_int(content_desc_id)
        self._buffer.write_float(left)
        self._buffer.write_float(top)
        self._buffer.write_float(right)
        self._buffer.write_float(bottom)
        self._buffer.write_int(metadata_id)

    # ── Content Behavior ──────────────────────────────────────────

    def set_root_content_behavior(self, scroll: int, alignment: int, sizing: int, mode: int):
        self._start(Ops.ROOT_CONTENT_BEHAVIOR)
        self._buffer.write_int(scroll)
        self._buffer.write_int(alignment)
        self._buffer.write_int(sizing)
        self._buffer.write_int(mode)

    # ── Touch ─────────────────────────────────────────────────────

    def add_touch_expression(self, id: int, def_value: float, min_val: float, max_val: float,
                             velocity_id: float, touch_effects: int, exp: list,
                             touch_mode: int, touch_spec: list = None, easing_spec: list = None):
        self._start(Ops.TOUCH_EXPRESSION)
        self._buffer.write_int(id)
        self._buffer.write_float(def_value)
        self._buffer.write_float(min_val)
        self._buffer.write_float(max_val)
        self._buffer.write_float(velocity_id)
        self._buffer.write_int(touch_effects)
        # Expression: length (int) + floats
        self._buffer.write_int(len(exp))
        for v in exp:
            self._buffer.write_float(v)
        # Stop mode + spec: packed as (touchMode << 16) | specLen
        spec_len = len(touch_spec) if touch_spec else 0
        self._buffer.write_int((touch_mode << 16) | spec_len)
        if touch_spec:
            for v in touch_spec:
                self._buffer.write_float(v)
        # Easing spec: length (int) + floats
        easing_len = len(easing_spec) if easing_spec else 0
        self._buffer.write_int(easing_len)
        if easing_spec:
            for v in easing_spec:
                self._buffer.write_float(v)

    # ── Bitmap ────────────────────────────────────────────────────

    def add_bitmap_data(self, id: int, width: int, height: int, data: bytes):
        self._start(Ops.DATA_BITMAP)
        self._buffer.write_int(id)
        self._buffer.write_int(width)
        self._buffer.write_int(height)
        self._buffer.write_byte_array(data)

    def bitmap_attribute(self, id: int, bitmap_id: int, attribute: int):
        self._start(Ops.ATTRIBUTE_IMAGE)
        self._buffer.write_int(id)
        self._buffer.write_int(bitmap_id)
        self._buffer.write_short(attribute)

    def bitmap_text_measure(self, id: int, text_id: int, bm_font_id: int,
                            measure_width: int, glyph_spacing: float):
        self._start(Ops.BITMAP_TEXT_MEASURE)
        self._buffer.write_int(id)
        self._buffer.write_int(text_id)
        self._buffer.write_int(bm_font_id)
        self._buffer.write_int(measure_width)
        self._buffer.write_float(glyph_spacing)

    # ── Text Attribute ────────────────────────────────────────────

    def text_attribute(self, id: int, text_id: int, attribute: int):
        self._start(Ops.ATTRIBUTE_TEXT)
        self._buffer.write_int(id)
        self._buffer.write_int(text_id)
        self._buffer.write_short(attribute)
        self._buffer.write_short(0)  # unused padding (matches Java)

    # ── Time Attribute ────────────────────────────────────────────

    def time_attribute(self, id: int, long_id: int, attr_type: int, args: list = None):
        self._start(Ops.ATTRIBUTE_TIME)
        self._buffer.write_int(id)
        self._buffer.write_int(long_id)
        self._buffer.write_short(attr_type)
        if args:
            self._buffer.write_int(len(args))
            for a in args:
                self._buffer.write_int(a)
        else:
            self._buffer.write_int(0)

    # ── Component Value ───────────────────────────────────────────

    def add_component_value(self, id: int, component_id: int, value_type: int):
        self._start(Ops.COMPONENT_VALUE)
        self._buffer.write_int(value_type)
        self._buffer.write_int(component_id)
        self._buffer.write_int(id)

    # ── Map ───────────────────────────────────────────────────────

    def add_map(self, id: int, names: list, types: list, ids: list):
        self._start(Ops.ID_MAP)
        self._buffer.write_int(id)
        self._buffer.write_int(len(names))
        for i in range(len(names)):
            self._buffer.write_utf8(names[i])
            self._buffer.write_byte(types[i] if types is not None else 2)
            self._buffer.write_int(ids[i])

    # ── Map Lookup ────────────────────────────────────────────────

    def map_lookup(self, id: int, map_id: int, str_id: int):
        self._start(Ops.DATA_MAP_LOOKUP)
        self._buffer.write_int(id)
        self._buffer.write_int(map_id)
        self._buffer.write_int(str_id)

    # ── ID Lookup ─────────────────────────────────────────────────

    def id_lookup(self, id: int, array_id: float, index: float):
        self._start(Ops.ID_LOOKUP)
        self._buffer.write_int(id)
        self._buffer.write_float(array_id)
        self._buffer.write_float(index)

    # ── Float as ID ───────────────────────────────────────────────

    def as_float_id(self, int_id: int) -> float:
        return as_nan(int_id)

    # ── Haptic ────────────────────────────────────────────────────

    def perform_haptic(self, feedback_constant: int):
        self._start(Ops.HAPTIC_FEEDBACK)
        self._buffer.write_int(feedback_constant)

    # ── Wake In ───────────────────────────────────────────────────

    def wake_in(self, seconds: float):
        self._start(Ops.WAKE_IN)
        self._buffer.write_float(seconds)

    # ── Conditional Operations ────────────────────────────────────

    def add_conditional_operations(self, cond_type: int, a: float, b: float):
        self._start(Ops.CONDITIONAL_OPERATIONS)
        self._buffer.write_byte(cond_type)
        self._buffer.write_float(a)
        self._buffer.write_float(b)

    def end_conditional_operations(self):
        self.add_container_end()

    # ── Layout Operations ─────────────────────────────────────────

    def add_root_start(self):
        cid = self.get_component_id(-1)
        self._start(Ops.LAYOUT_ROOT)
        self._buffer.write_int(cid)

    def add_container_end(self):
        self._start(Ops.CONTAINER_END)

    def add_content_start(self):
        cid = self.get_component_id(-1)
        self._last_component_id = cid
        self._start(Ops.LAYOUT_CONTENT)
        self._buffer.write_int(cid)

    def add_box_start(self, component_id: int, parent_id: int, horizontal: int, vertical: int):
        cid = self.get_component_id(component_id)
        self._last_component_id = cid
        self._start(Ops.LAYOUT_BOX)
        self._buffer.write_int(cid)
        self._buffer.write_int(parent_id)
        self._buffer.write_int(horizontal)
        self._buffer.write_int(vertical)

    def add_fit_box_start(self, component_id: int, parent_id: int, horizontal: int, vertical: int):
        cid = self.get_component_id(component_id)
        self._last_component_id = cid
        self._start(Ops.LAYOUT_FIT_BOX)
        self._buffer.write_int(cid)
        self._buffer.write_int(parent_id)
        self._buffer.write_int(horizontal)
        self._buffer.write_int(vertical)

    def add_row_start(self, component_id: int, parent_id: int, horizontal: int, vertical: int,
                      spaced_by: float = float('nan')):
        cid = self.get_component_id(component_id)
        self._last_component_id = cid
        self._start(Ops.LAYOUT_ROW)
        self._buffer.write_int(cid)
        self._buffer.write_int(parent_id)
        self._buffer.write_int(horizontal)
        self._buffer.write_int(vertical)
        self._buffer.write_float(spaced_by)

    def add_column_start(self, component_id: int, parent_id: int, horizontal: int, vertical: int,
                         spaced_by: float = float('nan')):
        cid = self.get_component_id(component_id)
        self._last_component_id = cid
        self._start(Ops.LAYOUT_COLUMN)
        self._buffer.write_int(cid)
        self._buffer.write_int(parent_id)
        self._buffer.write_int(horizontal)
        self._buffer.write_int(vertical)
        self._buffer.write_float(spaced_by)

    def add_collapsible_row_start(self, component_id: int, parent_id: int,
                                  horizontal: int, vertical: int,
                                  spaced_by: float = float('nan')):
        cid = self.get_component_id(component_id)
        self._last_component_id = cid
        self._start(Ops.LAYOUT_COLLAPSIBLE_ROW)
        self._buffer.write_int(cid)
        self._buffer.write_int(parent_id)
        self._buffer.write_int(horizontal)
        self._buffer.write_int(vertical)
        self._buffer.write_float(spaced_by)

    def add_collapsible_column_start(self, component_id: int, parent_id: int,
                                     horizontal: int, vertical: int,
                                     spaced_by: float = float('nan')):
        cid = self.get_component_id(component_id)
        self._last_component_id = cid
        self._start(Ops.LAYOUT_COLLAPSIBLE_COLUMN)
        self._buffer.write_int(cid)
        self._buffer.write_int(parent_id)
        self._buffer.write_int(horizontal)
        self._buffer.write_int(vertical)
        self._buffer.write_float(spaced_by)

    def add_flow_start(self, component_id: int, parent_id: int, horizontal: int, vertical: int,
                       spaced_by: float = float('nan')):
        cid = self.get_component_id(component_id)
        self._last_component_id = cid
        self._start(Ops.LAYOUT_FLOW)
        self._buffer.write_int(cid)
        self._buffer.write_int(parent_id)
        self._buffer.write_int(horizontal)
        self._buffer.write_int(vertical)
        self._buffer.write_float(spaced_by)

    def add_canvas_start(self, component_id: int, parent_id: int):
        cid = self.get_component_id(component_id)
        self._last_component_id = cid
        self._start(Ops.LAYOUT_CANVAS)
        self._buffer.write_int(cid)
        self._buffer.write_int(parent_id)

    def add_canvas_content_start(self, component_id: int):
        cid = self.get_component_id(component_id)
        self._last_component_id = cid
        self._start(Ops.LAYOUT_CANVAS_CONTENT)
        self._buffer.write_int(cid)

    def add_canvas_operations_start(self):
        self._start(Ops.CANVAS_OPERATIONS)

    def add_run_actions_start(self):
        self._start(Ops.RUN_ACTION)

    def add_image(self, component_id: int, parent_id: int, image_id: int,
                  scale_type: int, alpha: float):
        self._last_component_id = self.get_component_id(component_id)
        self._start(Ops.LAYOUT_IMAGE)
        # Java RecordingRemoteComposeBuffer passes original componentId, not resolved
        self._buffer.write_int(component_id)
        self._buffer.write_int(parent_id)
        self._buffer.write_int(image_id)
        self._buffer.write_int(scale_type)
        self._buffer.write_float(alpha)

    def add_state_layout(self, component_id: int, parent_id: int,
                         horizontal: int, vertical: int, index_id: int):
        cid = self.get_component_id(component_id)
        self._last_component_id = cid
        self._start(Ops.LAYOUT_STATE)
        self._buffer.write_int(cid)
        self._buffer.write_int(parent_id)
        self._buffer.write_int(horizontal)
        self._buffer.write_int(vertical)
        self._buffer.write_int(index_id)

    def add_text_component_start(self, component_id: int, parent_id: int,
                                 text_id: int, color: int, font_size: float,
                                 font_style: int, font_weight: float,
                                 font_family_id: int, flags: int, text_align: int,
                                 overflow: int, max_lines: int):
        cid = self.get_component_id(component_id)
        self._last_component_id = cid
        self._start(Ops.LAYOUT_TEXT)
        self._buffer.write_int(cid)
        self._buffer.write_int(parent_id)
        self._buffer.write_int(text_id)
        self._buffer.write_int(color)
        self._buffer.write_float(font_size)
        self._buffer.write_int(font_style)
        self._buffer.write_float(font_weight)
        self._buffer.write_int(font_family_id)
        self._buffer.write_short(flags)
        self._buffer.write_short(text_align)
        self._buffer.write_int(overflow)
        self._buffer.write_int(max_lines)

    # CoreText tagged-parameter defaults (matching Java TextStyle.PARAMETERS)
    _CORE_TEXT_DEFAULTS = {
        # (tag, type, default)  type: 'i'=int, 'f'=float, 'b'=boolean
        1:  ('i', -1),         # P_ID (componentId)
        2:  ('i', -1),         # P_ANIMATION_ID
        3:  ('i', 0xFF000000), # P_COLOR  (use unsigned comparison)
        4:  ('i', -1),         # P_COLOR_ID
        5:  ('f', 36.0),       # P_FONT_SIZE
        6:  ('i', 0),          # P_FONT_STYLE
        7:  ('f', 400.0),      # P_FONT_WEIGHT
        8:  ('i', -1),         # P_FONT_FAMILY
        9:  ('i', 1),          # P_TEXT_ALIGN
        10: ('i', 1),          # P_OVERFLOW
        11: ('i', 0x7FFFFFFF), # P_MAX_LINES
        12: ('f', 0.0),        # P_LETTER_SPACING
        13: ('f', 0.0),        # P_LINE_HEIGHT_ADD
        14: ('f', 1.0),        # P_LINE_HEIGHT_MULTIPLIER
        15: ('i', 0),          # P_BREAK_STRATEGY
        16: ('i', 0),          # P_HYPHENATION_FREQUENCY
        17: ('i', 0),          # P_JUSTIFICATION_MODE
        18: ('b', False),      # P_UNDERLINE
        19: ('b', False),      # P_STRIKETHROUGH
        22: ('b', False),      # P_AUTOSIZE
        23: ('i', 0),          # P_FLAGS
        24: ('i', -1),         # P_PARENT_ID (textStyleId)
        25: ('f', -1.0),       # P_MIN_FONT_SIZE
        26: ('f', -1.0),       # P_MAX_FONT_SIZE
    }

    def add_core_text_start(self, component_id: int, animation_id: int,
                            text_id: int, color: int, color_id: int,
                            font_size: float, min_font_size: float,
                            max_font_size: float, font_style: int,
                            font_weight: float, font_family_id: int,
                            text_align: int, overflow: int, max_lines: int,
                            letter_spacing: float, line_height_add: float,
                            line_height_multiplier: float,
                            line_break_strategy: int, hyphenation_frequency: int,
                            justification_mode: int, underline: bool,
                            strikethrough: bool, autosize: bool,
                            flags: int, text_style_id: int):
        """Write CORE_TEXT (opcode 239) with tagged parameters."""
        cid = self.get_component_id(component_id)
        self._last_component_id = cid

        # Build list of (tag, type, value) for non-default params
        params = [
            (1, 'i', cid),                    # P_ID
            (2, 'i', animation_id),            # P_ANIMATION_ID
            (3, 'i', color & 0xFFFFFFFF),      # P_COLOR (unsigned)
            (4, 'i', color_id),                # P_COLOR_ID
            (5, 'f', font_size),               # P_FONT_SIZE
            (25, 'f', min_font_size),           # P_MIN_FONT_SIZE
            (26, 'f', max_font_size),           # P_MAX_FONT_SIZE
            (6, 'i', font_style),              # P_FONT_STYLE
            (7, 'f', font_weight),             # P_FONT_WEIGHT
            (8, 'i', font_family_id),          # P_FONT_FAMILY
            (9, 'i', text_align),              # P_TEXT_ALIGN
            (10, 'i', overflow),               # P_OVERFLOW
            (11, 'i', max_lines),              # P_MAX_LINES
            (12, 'f', letter_spacing),         # P_LETTER_SPACING
            (13, 'f', line_height_add),        # P_LINE_HEIGHT_ADD
            (14, 'f', line_height_multiplier), # P_LINE_HEIGHT_MULTIPLIER
            (15, 'i', line_break_strategy),    # P_BREAK_STRATEGY
            (16, 'i', hyphenation_frequency),  # P_HYPHENATION_FREQUENCY
            (17, 'i', justification_mode),     # P_JUSTIFICATION_MODE
            (18, 'b', underline),              # P_UNDERLINE
            (19, 'b', strikethrough),          # P_STRIKETHROUGH
            (22, 'b', autosize),               # P_AUTOSIZE
            (23, 'i', flags),                  # P_FLAGS
            (24, 'i', text_style_id),          # P_PARENT_ID
        ]

        # Filter to non-default params
        # P_FONT_SIZE (tag 5) is always written even when it matches the default,
        # matching the Kotlin reference output behavior
        ALWAYS_WRITE = {5}  # P_FONT_SIZE
        non_default = []
        for tag, typ, val in params:
            if tag not in ALWAYS_WRITE:
                defaults = self._CORE_TEXT_DEFAULTS
                if tag in defaults:
                    def_type, def_val = defaults[tag]
                    if typ == 'i' and val == def_val:
                        continue
                    if typ == 'f' and val == def_val:
                        continue
                    if typ == 'b' and val == def_val:
                        continue
            non_default.append((tag, typ, val))

        # Write opcode + textId + count + params
        self._start(Ops.CORE_TEXT)
        self._buffer.write_int(text_id)
        self._buffer.write_short(len(non_default))
        for tag, typ, val in non_default:
            self._buffer.write_byte(tag)
            if typ == 'i':
                self._buffer.write_int(val)
            elif typ == 'f':
                self._buffer.write_float(val)
            elif typ == 'b':
                self._buffer.write_byte(1 if val else 0)

    # ── Loop ──────────────────────────────────────────────────────

    def add_loop_start(self, index_id: int, from_val: float, step: float, until: float):
        self._start(Ops.LOOP_START)
        self._buffer.write_int(index_id)
        self._buffer.write_float(from_val)
        self._buffer.write_float(step)
        self._buffer.write_float(until)

    def add_loop_end(self):
        self.add_container_end()

    # ── Modifier Operations ───────────────────────────────────────

    def add_width_modifier_operation(self, dim_type: int, value: float):
        self._start(Ops.MODIFIER_WIDTH)
        self._buffer.write_int(dim_type)
        self._buffer.write_float(value)

    def add_height_modifier_operation(self, dim_type: int, value: float):
        self._start(Ops.MODIFIER_HEIGHT)
        self._buffer.write_int(dim_type)
        self._buffer.write_float(value)

    def add_modifier_padding(self, left: float, top: float,
                              right: float, bottom: float):
        self._start(Ops.MODIFIER_PADDING)
        self._buffer.write_float(left)
        self._buffer.write_float(top)
        self._buffer.write_float(right)
        self._buffer.write_float(bottom)

    def add_modifier_background(self, r: float, g: float, b: float,
                                 a: float, shape: int):
        self._start(Ops.MODIFIER_BACKGROUND)
        self._buffer.write_int(0)       # flags
        self._buffer.write_int(0)       # colorId
        self._buffer.write_int(0)       # reserve1
        self._buffer.write_int(0)       # reserve2
        self._buffer.write_float(r)
        self._buffer.write_float(g)
        self._buffer.write_float(b)
        self._buffer.write_float(a)
        self._buffer.write_int(shape)

    def add_dynamic_modifier_background(self, color_id: int, shape: int):
        COLOR_REF = 2
        self._start(Ops.MODIFIER_BACKGROUND)
        self._buffer.write_int(COLOR_REF)  # flags
        self._buffer.write_int(color_id)   # colorId
        self._buffer.write_int(0)          # reserve1
        self._buffer.write_int(0)          # reserve2
        self._buffer.write_float(0.0)
        self._buffer.write_float(0.0)
        self._buffer.write_float(0.0)
        self._buffer.write_float(0.0)
        self._buffer.write_int(shape)

    def add_modifier_border(self, border_width: float, rounded_corner: float,
                             color: int, shape_type: int):
        r = ((color >> 16) & 0xFF) / 255.0
        g = ((color >> 8) & 0xFF) / 255.0
        b = (color & 0xFF) / 255.0
        a = ((color >> 24) & 0xFF) / 255.0
        self._start(Ops.MODIFIER_BORDER)
        self._buffer.write_int(0)       # flags
        self._buffer.write_int(0)       # colorId
        self._buffer.write_int(0)       # reserve1
        self._buffer.write_int(0)       # reserve2
        self._buffer.write_float(border_width)
        self._buffer.write_float(rounded_corner)
        self._buffer.write_float(r)
        self._buffer.write_float(g)
        self._buffer.write_float(b)
        self._buffer.write_float(a)
        self._buffer.write_int(shape_type)

    def add_modifier_dynamic_border(self, border_width: float, rounded_corner: float,
                                     color_id: int, shape_type: int):
        COLOR_REF = 2
        self._start(Ops.MODIFIER_BORDER)
        self._buffer.write_int(COLOR_REF)  # flags
        self._buffer.write_int(color_id)   # colorId
        self._buffer.write_int(0)          # reserve1
        self._buffer.write_int(0)          # reserve2
        self._buffer.write_float(border_width)
        self._buffer.write_float(rounded_corner)
        self._buffer.write_float(0.0)
        self._buffer.write_float(0.0)
        self._buffer.write_float(0.0)
        self._buffer.write_float(0.0)
        self._buffer.write_int(shape_type)

    def add_clip_rect_modifier(self):
        self._start(Ops.MODIFIER_CLIP_RECT)

    def add_round_clip_rect_modifier(self, top_start: float, top_end: float,
                                      bottom_start: float, bottom_end: float):
        self._start(Ops.MODIFIER_ROUNDED_CLIP_RECT)
        self._buffer.write_float(top_start)
        self._buffer.write_float(top_end)
        self._buffer.write_float(bottom_start)
        self._buffer.write_float(bottom_end)

    def add_modifier_offset(self, x: float, y: float):
        self._start(Ops.MODIFIER_OFFSET)
        self._buffer.write_float(x)
        self._buffer.write_float(y)

    def add_component_visibility_operation(self, value_id: int):
        self._start(Ops.MODIFIER_VISIBILITY)
        self._buffer.write_int(value_id)

    def add_modifier_z_index(self, value: float):
        self._start(Ops.MODIFIER_ZINDEX)
        self._buffer.write_float(value)

    def add_click_modifier_operation(self):
        self._start(Ops.MODIFIER_CLICK)

    def add_touch_down_modifier_operation(self):
        self._start(Ops.MODIFIER_TOUCH_DOWN)

    def add_touch_up_modifier_operation(self):
        self._start(Ops.MODIFIER_TOUCH_UP)

    def add_touch_cancel_modifier_operation(self):
        self._start(Ops.MODIFIER_TOUCH_CANCEL)

    def add_modifier_graphics_layer(self, attributes: dict):
        DATA_TYPE_FLOAT = 1
        DATA_TYPE_INT = 0
        self._start(Ops.MODIFIER_GRAPHICS_LAYER)
        self._buffer.write_int(len(attributes))
        for key, value in attributes.items():
            if isinstance(value, int):
                tag = key | (DATA_TYPE_INT << 10)
                self._buffer.write_int(tag)
                self._buffer.write_int(value)
            elif isinstance(value, float):
                tag = key | (DATA_TYPE_FLOAT << 10)
                self._buffer.write_int(tag)
                self._buffer.write_float(value)

    def add_modifier_scroll(self, direction: int, position_id: float,
                             max_val: float, notch_max: float = 0.0):
        self._start(Ops.MODIFIER_SCROLL)
        self._buffer.write_int(direction)
        self._buffer.write_float(position_id)
        self._buffer.write_float(max_val)
        self._buffer.write_float(notch_max)

    def add_modifier_ripple(self):
        self._start(Ops.MODIFIER_RIPPLE)

    def add_modifier_marquee(self, iterations: int, animation_mode: int,
                              repeat_delay_millis: float,
                              initial_delay_millis: float,
                              spacing: float, velocity: float):
        self._start(Ops.MODIFIER_MARQUEE)
        self._buffer.write_int(iterations)
        self._buffer.write_int(animation_mode)
        self._buffer.write_float(repeat_delay_millis)
        self._buffer.write_float(initial_delay_millis)
        self._buffer.write_float(spacing)
        self._buffer.write_float(velocity)

    def add_draw_content_operation(self):
        self._start(Ops.MODIFIER_DRAW_CONTENT)

    def add_modifier_align_by(self, line: float):
        self._start(Ops.MODIFIER_ALIGN_BY)
        self._buffer.write_float(line)
        self._buffer.write_int(0)  # flags

    def add_animation_spec_modifier(self, animation_id: int,
                                     motion_duration: float,
                                     motion_easing_type: int,
                                     visibility_duration: float,
                                     visibility_easing_type: int,
                                     enter_animation: int,
                                     exit_animation: int):
        self._start(Ops.ANIMATION_SPEC)
        self._buffer.write_int(animation_id)
        self._buffer.write_float(motion_duration)
        self._buffer.write_int(motion_easing_type)
        self._buffer.write_float(visibility_duration)
        self._buffer.write_int(visibility_easing_type)
        self._buffer.write_int(enter_animation)
        self._buffer.write_int(exit_animation)

    def add_collapsible_priority_modifier(self, orientation: int, priority: float):
        self._start(Ops.MODIFIER_COLLAPSIBLE_PRIORITY)
        self._buffer.write_int(orientation)
        self._buffer.write_float(priority)

    def add_width_in_modifier_operation(self, min_val: float, max_val: float):
        self._start(Ops.MODIFIER_WIDTH_IN)
        self._buffer.write_float(min_val)
        self._buffer.write_float(max_val)

    def add_height_in_modifier_operation(self, min_val: float, max_val: float):
        self._start(Ops.MODIFIER_HEIGHT_IN)
        self._buffer.write_float(min_val)
        self._buffer.write_float(max_val)

    def start_layout_compute(self, compute_type: int, bounds_id: int,
                              animate_changes: bool):
        self._start(Ops.LAYOUT_COMPUTE)
        self._buffer.write_int(compute_type)
        self._buffer.write_int(bounds_id)
        self._buffer.write_byte(1 if animate_changes else 0)

    def end_layout_compute(self):
        self.add_container_end()

    def add_semantics_modifier(self, content_description_id: int, role: int,
                                text_id: int, state_description_id: int,
                                mode: int, enabled: bool, clickable: bool):
        self._start(Ops.ACCESSIBILITY_SEMANTICS)
        self._buffer.write_int(content_description_id)
        self._buffer.write_byte(role)
        self._buffer.write_int(text_id)
        self._buffer.write_int(state_description_id)
        self._buffer.write_byte(mode)
        self._buffer.write_byte(1 if enabled else 0)
        self._buffer.write_byte(1 if clickable else 0)

    # ── Action Operations ─────────────────────────────────────────

    def add_value_string_change_action_operation(self, dest_id: int, src_id: int):
        self._start(Ops.VALUE_STRING_CHANGE_ACTION)
        self._buffer.write_int(dest_id)
        self._buffer.write_int(src_id)

    def add_value_float_change_action_operation(self, value_id: int, value: float):
        self._start(Ops.VALUE_FLOAT_CHANGE_ACTION)
        self._buffer.write_int(value_id)
        self._buffer.write_float(value)

    def add_value_integer_change_action_operation(self, value_id: int, value: int):
        self._start(Ops.VALUE_INTEGER_CHANGE_ACTION)
        self._buffer.write_int(value_id)
        self._buffer.write_int(value)

    def add_value_float_expression_change_action_operation(self, value_id: int,
                                                            value: int):
        self._start(Ops.VALUE_FLOAT_EXPRESSION_CHANGE_ACTION)
        self._buffer.write_int(value_id)
        self._buffer.write_int(value)

    def add_value_integer_expression_change_action_operation(self, dest_id: int,
                                                              src_id: int):
        self._start(Ops.VALUE_INTEGER_EXPRESSION_CHANGE_ACTION)
        self._buffer.write_long(dest_id)
        self._buffer.write_long(src_id)

    # ── List / Array Operations ───────────────────────────────────

    def add_list(self, id: int, list_ids: list):
        self._start(Ops.ID_LIST)
        self._buffer.write_int(id)
        self._buffer.write_int(len(list_ids))
        for lid in list_ids:
            self._buffer.write_int(lid)

    def add_float_array(self, id: int, values: list):
        self._start(Ops.FLOAT_LIST)
        self._buffer.write_int(id)
        self._buffer.write_int(len(values))
        for v in values:
            self._buffer.write_float(v)

    def add_dynamic_float_array(self, id: int, size: float):
        self._start(Ops.DYNAMIC_FLOAT_LIST)
        self._buffer.write_int(id)
        self._buffer.write_float(size)

    def set_array_value(self, id: int, index: float, value: float):
        self._start(Ops.UPDATE_DYNAMIC_FLOAT_LIST)
        self._buffer.write_int(id)
        self._buffer.write_float(index)
        self._buffer.write_float(value)

    # ── Font ──────────────────────────────────────────────────────

    def add_font(self, id: int, font_type: int, data: bytes):
        self._start(Ops.DATA_FONT)
        self._buffer.write_int(id)
        self._buffer.write_int(font_type)
        self._buffer.write_byte_array(data)

    def add_bitmap_font(self, id: int, glyphs: list, kerning_table: dict = None):
        """Add a bitmap font. Each glyph is a dict with keys:
        chars, bitmap_id, margin_left, margin_top, margin_right, margin_bottom,
        bitmap_width, bitmap_height."""
        VERSION_2 = 2
        self._start(Ops.DATA_BITMAP_FONT)
        self._buffer.write_int(id)
        if kerning_table:
            self._buffer.write_int(len(glyphs) + (VERSION_2 << 16))
        else:
            self._buffer.write_int(len(glyphs))
        for g in glyphs:
            self._buffer.write_utf8(g['chars'])
            self._buffer.write_int(g['bitmap_id'])
            self._buffer.write_short(g['margin_left'])
            self._buffer.write_short(g['margin_top'])
            self._buffer.write_short(g['margin_right'])
            self._buffer.write_short(g['margin_bottom'])
            self._buffer.write_short(g['bitmap_width'])
            self._buffer.write_short(g['bitmap_height'])
        if kerning_table:
            self._buffer.write_short(len(kerning_table))
            for key, val in kerning_table.items():
                self._buffer.write_utf8(key)
                self._buffer.write_short(val)

    def store_bitmap(self, image_id: int, width: int, height: int, data: bytes) -> int:
        TYPE_PNG = 1
        ENCODING_RAW = 1
        self._start(Ops.DATA_BITMAP)
        self._buffer.write_int(image_id)
        w = (TYPE_PNG << 16) | (width & 0xFFFF)
        h = (ENCODING_RAW << 16) | (height & 0xFFFF)
        self._buffer.write_int(w)
        self._buffer.write_int(h)
        self._buffer.write_byte_array(data)
        return image_id

    def store_bitmap_a8(self, image_id: int, width: int, height: int, data: bytes) -> int:
        TYPE_PNG_ALPHA_8 = 2
        ENCODING_RAW = 1
        self._start(Ops.DATA_BITMAP)
        self._buffer.write_int(image_id)
        w = (TYPE_PNG_ALPHA_8 << 16) | (width & 0xFFFF)
        h = (ENCODING_RAW << 16) | (height & 0xFFFF)
        self._buffer.write_int(w)
        self._buffer.write_int(h)
        self._buffer.write_byte_array(data)
        return image_id

    def store_bitmap_url(self, image_id: int, url: str) -> int:
        TYPE_PNG = 1
        ENCODING_URL = 2
        self._start(Ops.DATA_BITMAP)
        self._buffer.write_int(image_id)
        w = (TYPE_PNG << 16) | 1
        h = (ENCODING_URL << 16) | 1
        self._buffer.write_int(w)
        self._buffer.write_int(h)
        self._buffer.write_byte_array(url.encode('utf-8'))
        return image_id

    # ── Bitmap create / draw-on ───────────────────────────────────

    def create_bitmap(self, image_id: int, width: int, height: int) -> int:
        TYPE_RAW8888 = 3
        ENCODING_EMPTY = 3
        self._start(Ops.DATA_BITMAP)
        self._buffer.write_int(image_id)
        w = (TYPE_RAW8888 << 16) | (width & 0xFFFF)
        h = (ENCODING_EMPTY << 16) | (height & 0xFFFF)
        self._buffer.write_int(w)
        self._buffer.write_int(h)
        self._buffer.write_byte_array(b'')
        return image_id

    def draw_on_bitmap(self, bitmap_id: int, mode: int, color: int):
        self._start(Ops.DRAW_TO_BITMAP)
        self._buffer.write_int(bitmap_id)
        self._buffer.write_int(mode)
        self._buffer.write_int(color)

    # ── Skip ──────────────────────────────────────────────────────

    def begin_skip(self, skip_type: int, value: int) -> int:
        self._start(Ops.SKIP)
        self._buffer.write_int(skip_type)
        self._buffer.write_int(value)
        offset = self._buffer.get_index()
        self._buffer.write_int(0)  # placeholder for skip length
        return offset

    def end_skip(self, offset: int):
        current = self._buffer.get_index()
        self._buffer.overwrite_int(offset, current - offset - 4)

    # ── Rem ───────────────────────────────────────────────────────

    def rem(self, message: str):
        self._start(Ops.REM)
        self._buffer.write_utf8(message)

    # ── Impulse ───────────────────────────────────────────────────

    def add_impulse(self, duration: float, start: float):
        self._start(Ops.IMPULSE_START)
        self._buffer.write_float(duration)
        self._buffer.write_float(start)

    def add_impulse_process(self):
        self._start(Ops.IMPULSE_PROCESS)

    def add_impulse_end(self):
        self.add_container_end()

    # ── Float Function ────────────────────────────────────────────

    def define_float_function(self, fid: int, args: list):
        self._start(Ops.FUNCTION_DEFINE)
        self._buffer.write_int(fid)
        self._buffer.write_int(len(args))
        for a in args:
            self._buffer.write_int(a)

    def add_end_float_function_def(self):
        self.add_container_end()

    def call_float_function(self, func_id: int, args: list):
        self._start(Ops.FUNCTION_CALL)
        self._buffer.write_int(func_id)
        if args:
            self._buffer.write_int(len(args))
            for a in args:
                self._buffer.write_float(a)
        else:
            self._buffer.write_int(0)

    # ── Bitmap Name ───────────────────────────────────────────────

    def set_bitmap_name(self, id: int, name: str):
        self._start(Ops.NAMED_VARIABLE)
        self._buffer.write_int(id)
        self._buffer.write_int(3)  # IMAGE_TYPE
        self._buffer.write_utf8(name)

    # ── Bitmap Font Text on Path ──────────────────────────────────

    def add_draw_bitmap_font_text_run_on_path(self, text_id: int, bitmap_font_id: int,
                                               path_id: int, start: int, end: int,
                                               y_adj: float, glyph_spacing: float):
        self._start(Ops.DRAW_BITMAP_FONT_TEXT_RUN_ON_PATH)
        if glyph_spacing == 0.0:
            self._buffer.write_int(text_id)
        else:
            self._buffer.write_int(text_id | 0x80000000)
            self._buffer.write_float(glyph_spacing)
        self._buffer.write_int(bitmap_font_id)
        self._buffer.write_int(path_id)
        self._buffer.write_int(start)
        self._buffer.write_int(end)
        self._buffer.write_float(y_adj)

    # ── Particles ─────────────────────────────────────────────────

    def add_particles(self, id: int, var_ids: list, initial_expressions: list,
                      particle_count: int):
        self._start(Ops.PARTICLE_DEFINE)
        self._buffer.write_int(id)
        self._buffer.write_int(particle_count)
        self._buffer.write_int(len(var_ids))
        for i in range(len(var_ids)):
            self._buffer.write_int(var_ids[i])
            eq = initial_expressions[i]
            self._buffer.write_int(len(eq))
            for v in eq:
                self._buffer.write_float(v)

    def add_particles_loop(self, id: int, restart: list, expressions: list):
        self._start(Ops.PARTICLE_LOOP)
        self._buffer.write_int(id)
        if restart is not None:
            self._buffer.write_int(len(restart))
            for v in restart:
                self._buffer.write_float(v)
        else:
            self._buffer.write_int(0)
        self._buffer.write_int(len(expressions))
        for eq in expressions:
            self._buffer.write_int(len(eq))
            for v in eq:
                self._buffer.write_float(v)

    def add_particles_comparison(self, id: int, flags: int, min_val: float, max_val: float,
                                  condition: list, apply1: list, apply2: list):
        self._start(Ops.PARTICLE_COMPARE)
        self._buffer.write_int(id)
        self._buffer.write_short(flags)
        self._buffer.write_float(min_val)
        self._buffer.write_float(max_val)
        # condition
        if condition is not None:
            self._buffer.write_int(len(condition))
            for v in condition:
                self._buffer.write_float(v)
        else:
            self._buffer.write_int(0)
        # equations1
        if apply1 is not None:
            self._buffer.write_int(len(apply1))
            for eq in apply1:
                if eq is not None:
                    self._buffer.write_int(len(eq))
                    for v in eq:
                        self._buffer.write_float(v)
                else:
                    self._buffer.write_int(0)
        else:
            self._buffer.write_int(0)
        # equations2
        if apply2 is not None:
            self._buffer.write_int(len(apply2))
            for eq in apply2:
                if eq is not None:
                    self._buffer.write_int(len(eq))
                    for v in eq:
                        self._buffer.write_float(v)
                else:
                    self._buffer.write_int(0)
        else:
            self._buffer.write_int(0)

    def add_particle_loop_end(self):
        self.add_container_end()

    # ── Text Style ────────────────────────────────────────────────

    def add_text_style(self, id, color, color_id, font_size, min_font_size,
                       max_font_size, font_style, font_weight, font_family_id,
                       text_align, overflow, max_lines, letter_spacing,
                       line_height_add, line_height_multiplier,
                       line_break_strategy, hyphenation_frequency,
                       justification_mode, underline, strikethrough,
                       font_axis_tags, font_axis_values, autosize,
                       parent_id):
        # TextStyle parameter tags
        P_ID = 1
        P_COLOR = 3
        P_COLOR_ID = 4
        P_FONT_SIZE = 5
        P_FONT_STYLE = 6
        P_FONT_WEIGHT = 7
        P_FONT_FAMILY = 8
        P_TEXT_ALIGN = 9
        P_OVERFLOW = 10
        P_MAX_LINES = 11
        P_LETTER_SPACING = 12
        P_LINE_HEIGHT_ADD = 13
        P_LINE_HEIGHT_MULTIPLIER = 14
        P_BREAK_STRATEGY = 15
        P_HYPHENATION_FREQUENCY = 16
        P_JUSTIFICATION_MODE = 17
        P_UNDERLINE = 18
        P_STRIKETHROUGH = 19
        P_FONT_AXIS = 20
        P_FONT_AXIS_VALUES = 21
        P_AUTOSIZE = 22
        P_PARENT_ID = 24
        P_MIN_FONT_SIZE = 25
        P_MAX_FONT_SIZE = 26

        params = []
        if id is not None and id != -1:
            params.append(('int', P_ID, id))
        if color is not None:
            params.append(('int', P_COLOR, color))
        if color_id is not None:
            params.append(('int', P_COLOR_ID, color_id))
        if font_size is not None:
            params.append(('float', P_FONT_SIZE, font_size))
        if min_font_size is not None:
            params.append(('float', P_MIN_FONT_SIZE, min_font_size))
        if max_font_size is not None:
            params.append(('float', P_MAX_FONT_SIZE, max_font_size))
        if font_style is not None:
            params.append(('int', P_FONT_STYLE, font_style))
        if font_weight is not None:
            params.append(('float', P_FONT_WEIGHT, font_weight))
        if font_family_id is not None:
            params.append(('int', P_FONT_FAMILY, font_family_id))
        if text_align is not None:
            params.append(('int', P_TEXT_ALIGN, text_align))
        if overflow is not None:
            params.append(('int', P_OVERFLOW, overflow))
        if max_lines is not None:
            params.append(('int', P_MAX_LINES, max_lines))
        if letter_spacing is not None:
            params.append(('float', P_LETTER_SPACING, letter_spacing))
        if line_height_add is not None:
            params.append(('float', P_LINE_HEIGHT_ADD, line_height_add))
        if line_height_multiplier is not None:
            params.append(('float', P_LINE_HEIGHT_MULTIPLIER,
                           line_height_multiplier))
        if line_break_strategy is not None:
            params.append(('int', P_BREAK_STRATEGY, line_break_strategy))
        if hyphenation_frequency is not None:
            params.append(('int', P_HYPHENATION_FREQUENCY,
                           hyphenation_frequency))
        if justification_mode is not None:
            params.append(('int', P_JUSTIFICATION_MODE, justification_mode))
        if underline is not None:
            params.append(('bool', P_UNDERLINE, underline))
        if strikethrough is not None:
            params.append(('bool', P_STRIKETHROUGH, strikethrough))
        if autosize is not None:
            params.append(('bool', P_AUTOSIZE, autosize))
        if parent_id is not None:
            params.append(('int', P_PARENT_ID, parent_id))

        has_font_axis = (font_axis_tags is not None and
                         len(font_axis_tags) > 0)
        count = len(params)
        if has_font_axis:
            count += 2

        self._start(Ops.TEXT_STYLE)
        self._buffer.write_short(count)

        for ptype, tag, val in params:
            self._buffer.write_byte(tag)
            if ptype == 'int':
                self._buffer.write_int(val)
            elif ptype == 'float':
                self._buffer.write_float(val)
            elif ptype == 'bool':
                self._buffer.write_byte(1 if val else 0)

        if has_font_axis:
            self._buffer.write_byte(P_FONT_AXIS)
            self._buffer.write_short(len(font_axis_tags))
            for axis in font_axis_tags:
                self._buffer.write_int(axis)
            self._buffer.write_byte(P_FONT_AXIS_VALUES)
            self._buffer.write_short(len(font_axis_values))
            for v in font_axis_values:
                self._buffer.write_float(v)

    # ── Host Actions ──────────────────────────────────────────────

    def add_host_action(self, action_id: int):
        self._start(Ops.HOST_ACTION)
        self._buffer.write_int(action_id)

    def add_host_action_metadata(self, action_id: int, metadata_id: int):
        self._start(Ops.HOST_METADATA_ACTION)
        self._buffer.write_int(action_id)
        self._buffer.write_int(metadata_id)

    def add_host_named_action(self, text_id: int, action_type: int, value_id: int):
        self._start(Ops.HOST_NAMED_ACTION)
        self._buffer.write_int(text_id)
        self._buffer.write_int(action_type)
        self._buffer.write_int(value_id)

    # ── Debug ─────────────────────────────────────────────────────

    def add_debug_message(self, text_id: int, value: float, flags: int):
        self._start(Ops.DEBUG_MESSAGE)
        self._buffer.write_int(text_id)
        self._buffer.write_float(value)
        self._buffer.write_int(flags)

    # ── Animation Pack ────────────────────────────────────────────

    EASING_CUBIC_STANDARD = 1

    @staticmethod
    def pack_animation(duration: float, anim_type: int, spec: list = None,
                       initial_value: float = float('nan'),
                       wrap: float = float('nan')) -> list:
        """Match Java FloatAnimation.packToFloatArray exactly.

        Format: [duration?, packed_type?, spec...?, initialValue?, wrap?]
        - duration omitted when ==1 and no other fields
        - packed_type = intBitsToFloat(specLen<<16 | type | wrapBit<<8 | initBit<<9)
        - packed_type omitted when type==CUBIC_STANDARD and spec==null and
          no wrap/initialValue
        """
        CUBIC_STANDARD = 1
        spec_len = 0 if spec is None else len(spec)
        has_init = not math.isnan(initial_value)
        has_wrap = not math.isnan(wrap)

        # Count entries (matching Java's counting logic)
        count = 0
        if has_init:
            count += 1
        if spec is not None:
            count += 1
        if spec is not None or anim_type != CUBIC_STANDARD:
            count += 1
            count += spec_len
        if has_init:
            count += 1
        if has_wrap:
            count += 1
        if duration != 1.0 or count > 0:
            count += 1
        if has_wrap or has_init:
            count += 1

        ret = [0.0] * count
        pos = 0

        # Pack
        if count > 0:
            ret[pos] = duration
            pos += 1
        if count > 1:
            wrap_bit = 1 if has_wrap else 0
            init_bit = 2 if has_init else 0
            bits = anim_type | ((wrap_bit | init_bit) << 8)
            ret[pos] = int_bits_to_float(spec_len << 16 | bits)
            pos += 1
        if spec_len > 0:
            for i in range(spec_len):
                ret[pos] = spec[i]
                pos += 1
        if has_init:
            ret[pos] = initial_value
            pos += 1
        if has_wrap:
            ret[pos] = wrap
            pos += 1

        return ret

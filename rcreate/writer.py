"""RemoteComposeWriter — high-level API for building RemoteCompose documents.

Wraps RemoteComposeBuffer with ID allocation, text caching, modifier support,
and a fluent API for drawing, layout, expressions, and data operations.

Matches Java's RemoteComposeWriter.java.
"""

from __future__ import annotations
import math

from .remote_UI_buffer import RemoteComposeBuffer
from .remote_UI_state import RemoteUIState
from .modifiers.recording_modifier import RecordingModifier
from .paint_bundle import PaintBundle
from .rc_paint import RcPaint
from .types.nan_utils import as_nan, id_from_nan

DOCUMENT_API_LEVEL = 8
LONG_OFFSET = 0x100000000

# Header property tags
DOC_WIDTH = 5
DOC_HEIGHT = 6
DOC_CONTENT_DESCRIPTION = 9
DOC_PROFILES = 14

# Java HashMap iteration order for demo7() with capacity 8:
# key 9 -> bucket 1, key 5 -> bucket 5, key 6 -> bucket 6, key 14 -> bucket 6
DEMO7_TAG_ORDER = [DOC_CONTENT_DESCRIPTION, DOC_WIDTH, DOC_HEIGHT, DOC_PROFILES]


class RemoteComposeWriter:
    """Central writer for building RemoteCompose binary documents."""

    def __init__(self, width: int = 0, height: int = 0,
                 content_description: str = None,
                 api_level: int = DOCUMENT_API_LEVEL,
                 profiles: int = 0,
                 platform=None,
                 legacy_header: bool = False,
                 header_tag_order: list = None,
                 extra_tags: dict = None):
        self._state = RemoteUIState()
        # Java legacy constructor leaves mApiLevel=0; match that behavior
        if legacy_header and api_level == DOCUMENT_API_LEVEL:
            api_level = 0
        self._api_level = api_level
        self._buffer = RemoteComposeBuffer(api_level)
        self._platform = platform
        self._original_width = width
        self._original_height = height
        self._content_description = content_description
        self._painter = RcPaint(self)
        self._insert_point = -1
        self._start_global_section = -1
        self._component_values_cache = {}  # (component_id, value_type) -> nan_id

        self._buffer.set_version(api_level, profiles)

        if legacy_header:
            # Legacy V6 header: MAJOR=1, MINOR=1, PATCH=0 + width/height/capabilities
            # Matches Java RemoteComposeWriter(w, h, cd, platform) constructor
            self._buffer.header(width, height, 1.0, 0)
            if content_description:
                cd_id = self.add_text(content_description)
                self._buffer.add_root_content_description(cd_id)
        else:
            # Build tag/value map
            tag_value_map = {
                DOC_WIDTH: width,
                DOC_HEIGHT: height,
                DOC_CONTENT_DESCRIPTION: (content_description
                                          if content_description is not None
                                          else ""),
            }
            if profiles != 0:
                tag_value_map[DOC_PROFILES] = profiles
            if extra_tags:
                tag_value_map.update(extra_tags)

            if header_tag_order is not None:
                # Custom tag order (e.g. to match Java HashMap iteration)
                tags = [t for t in header_tag_order if t in tag_value_map]
                values = [tag_value_map[t] for t in tags]
            else:
                # Default explicit order: WIDTH, HEIGHT, CD, [PROFILES]
                tags = [DOC_WIDTH, DOC_HEIGHT, DOC_CONTENT_DESCRIPTION]
                values = [tag_value_map[DOC_WIDTH],
                          tag_value_map[DOC_HEIGHT],
                          tag_value_map[DOC_CONTENT_DESCRIPTION]]
                if profiles != 0:
                    tags.append(DOC_PROFILES)
                    values.append(profiles)

            self._buffer.add_header(tags, values)

            if api_level == 6 and profiles == 0:
                if content_description:
                    cd_id = self.add_text(content_description)
                    self._buffer.add_root_content_description(cd_id)

    @property
    def rc_paint(self) -> RcPaint:
        return self._painter

    # ── Encode / output ──

    def encode_to_byte_array(self) -> bytes:
        return self._buffer._buffer.clone_bytes()

    def buffer(self) -> bytes:
        return self._buffer._buffer.get_buffer()

    def buffer_size(self) -> int:
        return self._buffer._buffer.get_size()

    def get_buffer(self) -> RemoteComposeBuffer:
        return self._buffer

    # ── Reset ──

    def reset(self):
        self._buffer.reset(1000000)
        self._state.reset()
        self.header(self._original_width, self._original_height,
                    self._content_description, 1.0, 0)

    def header(self, width: int, height: int, content_description: str = None,
               density: float = 1.0, capabilities: int = 0):
        self._buffer.header(width, height, density, capabilities)
        if content_description is not None:
            cd_id = self.add_text(content_description)
            self._buffer.add_root_content_description(cd_id)

    # ── Text ──

    def add_text(self, text: str) -> int:
        existing = self._state.data_get_id(text)
        if existing != -1:
            return existing
        cid = self._state.cache_data(text)
        self._buffer.add_text(cid, text)
        return cid

    def text_create_id(self, text: str) -> int:
        return self.add_text(text)

    def text_merge(self, id1: int, id2: int) -> int:
        text_id = self.next_id()
        return self._buffer.text_merge(text_id, id1, id2)

    def text_subtext(self, txt_id: int, start: float, length: float) -> int:
        cid = self._state.create_next_available_id()
        self._buffer.text_subtext(cid, txt_id, start, length)
        return cid

    def text_transform(self, txt_id: int, start: float, length: float,
                       operation: int) -> int:
        cid = self._state.create_next_available_id()
        self._buffer.text_transform(cid, txt_id, start, length, operation)
        return cid

    def text_measure(self, text_id: int, mode: int) -> float:
        cid = self._state.cache_data(text_id + mode * 31)
        self._buffer.text_measure(cid, text_id, mode)
        return as_nan(cid)

    def text_length(self, text_id: int) -> float:
        cid = self._state.cache_data(text_id + (156 << 16))
        self._buffer.text_length(cid, text_id)
        return as_nan(cid)

    def text_lookup(self, array_id: float, index) -> int:
        import struct as _struct
        raw = (int.from_bytes(
            _struct.pack('<f', array_id), 'little') << 32) + \
            int.from_bytes(
                _struct.pack('<f', float(index)),
                'little')
        cid = self._state.cache_data(raw)
        self._buffer.text_lookup(cid, array_id, index)
        return cid

    @staticmethod
    def _float_to_string(value: float) -> str:
        """Convert float to string, preserving NaN bit patterns like Java's Utils.floatToString."""
        if math.isnan(value):
            import struct
            bits = struct.unpack('>I', struct.pack('>f', value))[0]
            return f"nan({bits:#x})"
        return str(value)

    def create_text_from_float(self, value: float, before: int,
                               after: int, flags: int) -> int:
        placeholder = f"{self._float_to_string(value)}({before},{after},{flags})"
        existing = self._state.data_get_id(placeholder)
        if existing != -1:
            return existing
        cid = self._state.cache_data(placeholder)
        return self._buffer.create_text_from_float(cid, value, before, after, flags)

    # ── Data: Float ──

    def add_float_constant(self, value: float) -> float:
        cid = self._state.cache_float(value)
        return self._buffer.add_float(cid, value)

    def reserve_float_variable(self) -> float:
        cid = self._state.create_next_available_id()
        return as_nan(cid)

    def float_expression(self, *value: float, animation: list = None) -> float:
        # Java's cacheData always allocates a new ID (float arrays use reference
        # equality so same-content arrays get different IDs).  Match that behaviour.
        cid = self._state.create_next_available_id()
        # Handle floatExpression(float[], float[]) overload:
        # When called as float_expression(list, list), first is value, second is animation
        if (len(value) == 2 and isinstance(value[0], (list, tuple))
                and isinstance(value[1], (list, tuple))):
            self._buffer.add_animated_float(cid, list(value[0]), list(value[1]))
        elif (len(value) == 1 and isinstance(value[0], (list, tuple))):
            # Single list arg: float_expression([...]) — unwrap
            self._buffer.add_animated_float(cid, list(value[0]))
        elif animation is not None:
            self._buffer.add_animated_float(cid, list(value), animation)
        else:
            self._buffer.add_animated_float(cid, list(value))
        return as_nan(cid)

    def float_expression_with_anim(self, value: list, animation: list) -> float:
        """floatExpression(float[] value, float[] animation) overload — used by RFloat.anim()."""
        cid = self._state.create_next_available_id()
        self._buffer.add_animated_float(cid, list(value), list(animation))
        return as_nan(cid)

    def matrix_expression(self, *exp: float) -> float:
        cid = self._state.create_next_available_id()
        self._buffer.add_matrix_expression(cid, list(exp))
        return as_nan(cid)

    def matrix_multiply(self, matrix_id: float, from_vec: list, out: list):
        self.add_matrix_multiply(matrix_id, 0, from_vec, out)

    def add_matrix_multiply(self, matrix_id: float, op_type: int = 0,
                            from_vec: list = None, out: list = None):
        out_ids = []
        for i in range(len(out)):
            cid = self._state.create_next_available_id()
            out_ids.append(cid)
            out[i] = as_nan(cid)
        self._buffer.add_matrix_vector_math(matrix_id, op_type, from_vec, out_ids)

    # ── Data: Integer ──

    def add_integer(self, value: int) -> int:
        cid = self._state.cache_integer(value)
        self._buffer.add_integer(cid, value)
        return cid + LONG_OFFSET

    def integer_expression(self, mask_or_values, values=None) -> int:
        if values is not None:
            mask = mask_or_values
            vals = list(values)
        else:
            v = list(mask_or_values)
            mask = 0
            for i, val in enumerate(v):
                if val > 0x7FFFFFFF:
                    mask |= 1 << i
            vals = [int(x) & 0xFFFFFFFF for x in v]
        cid = self._state.cache_data(vals)
        self._buffer.add_integer_expression(cid, mask, vals)
        return cid + LONG_OFFSET

    def as_float_id(self, long_id: int) -> float:
        return self._buffer.as_float_id(int(long_id & 0xFFFFFFF))

    # ── Data: Long / Boolean ──

    def add_long(self, value: int) -> int:
        cid = self._state.create_next_available_id()
        self._buffer.add_long(cid, value)
        return cid

    def add_boolean(self, value: bool) -> int:
        cid = self._state.create_next_available_id()
        self._buffer.add_boolean(cid, value)
        return cid

    # ── Color ──

    def add_color(self, color: int) -> int:
        cid = self._state.create_next_available_id()
        self._buffer.add_color(cid, color)
        return cid

    def add_named_color(self, name: str, color: int) -> int:
        cid = self.add_color(color)
        self._buffer.set_named_variable(cid, name, 2)  # COLOR_TYPE
        return cid

    def set_color_name(self, cid: int, name: str):
        self._buffer.set_named_variable(cid, name, 2)

    def add_color_expression(self, *args) -> int:
        cid = self._state.create_next_available_id()
        self._buffer.add_color_expression(cid, *args)
        return cid

    def add_themed_color(self, light_name: str = None, light_value: int = 0,
                         dark_name: str = None, dark_value: int = 0) -> int:
        light_id = self._state.create_next_available_id()
        dark_id = self._state.create_next_available_id()
        if light_name is not None:
            self._buffer.set_named_variable(light_id, light_name, 2)
        if dark_name is not None:
            self._buffer.set_named_variable(dark_id, dark_name, 2)
        self._buffer.add_color(light_id, light_value)
        self._buffer.add_color(dark_id, dark_value)
        return self._add_themed_color_ids(light_id, dark_id)

    def _add_themed_color_ids(self, light_id: int, dark_id: int) -> int:
        from .rc import Rc
        ret_id = self._state.create_next_available_id()
        # Java addThemedColor(short lightId, short darkId) calls:
        #   addColorExpression(retId, (short)darkId, (short)lightId, 0)
        # which dispatches to mode=3 (ID_ID_INTERPOLATE).
        # Wire format: op + id + mode(3) + darkId + lightId + tween(float)
        ID_ID_INTERPOLATE = 3
        self.set_theme(Rc.Theme.DARK)
        self.start_loop(0, 0.0, 1.0, 1.0)
        self._buffer.add_color_expression(ret_id, ID_ID_INTERPOLATE,
                                          dark_id, light_id, 0.0)
        self.end_loop()
        self.set_theme(Rc.Theme.LIGHT)
        self.start_loop(0, 0.0, 1.0, 1.0)
        self._buffer.add_color_expression(ret_id, ID_ID_INTERPOLATE,
                                          dark_id, light_id, 1.0)
        self.end_loop()
        self.set_theme(Rc.Theme.UNSPECIFIED)
        return ret_id

    def get_color_attribute(self, base_color: int, attr_type: int) -> float:
        cid = self._state.create_next_available_id()
        self._buffer.get_color_attribute(cid, base_color, attr_type)
        return as_nan(cid)

    # ── Named Variables ──

    def add_named_float(self, name: str, initial_value: float) -> float:
        cid = self._state.create_next_available_id()
        self._buffer.set_named_variable(cid, name, 1)  # FLOAT_TYPE
        self._buffer.add_float(cid, initial_value)
        self._state.update_float(cid, initial_value)
        return as_nan(cid)

    def add_named_int(self, name: str, initial_value: int) -> int:
        cid = self._state.create_next_available_id()
        self._buffer.set_named_variable(cid, name, 4)  # INT_TYPE
        self._buffer.add_integer(cid, initial_value)
        self._state.update_integer(cid, initial_value)
        return cid + LONG_OFFSET

    def add_named_string(self, name: str, initial_value: str) -> int:
        cid = self._state.create_next_available_id()
        self._buffer.set_named_variable(cid, name, 0)  # STRING_TYPE
        self._buffer.add_text(cid, initial_value)
        return cid

    def add_named_long(self, name: str, initial_value: int) -> int:
        cid = self._state.create_next_available_id()
        self._buffer.set_named_variable(cid, name, 5)  # LONG_TYPE
        self._buffer.add_long(cid, initial_value)
        return cid

    def add_named_bitmap_url(self, name: str, url: str) -> int:
        cid = self.add_bitmap_url(url)
        self._buffer.set_named_variable(cid, name, 3)  # IMAGE_TYPE
        return cid

    def set_float_name(self, cid: int, name: str):
        self._buffer.set_named_variable(cid, name, 1)

    def set_string_name(self, cid: int, name: str):
        self._buffer.set_named_variable(cid, name, 0)

    # ── Theme ──

    def set_theme(self, theme: int):
        self._buffer.set_theme(theme)

    # ── Drawing ──

    def draw_rect(self, left: float, top: float, right: float, bottom: float):
        self._buffer.add_draw_rect(left, top, right, bottom)

    def draw_round_rect(self, left: float, top: float, right: float, bottom: float,
                        radius_x: float, radius_y: float):
        self._buffer.add_draw_round_rect(left, top, right, bottom, radius_x, radius_y)

    def draw_circle(self, center_x: float, center_y: float, radius: float):
        self._buffer.add_draw_circle(center_x, center_y, radius)

    def draw_line(self, x1: float, y1: float, x2: float, y2: float):
        self._buffer.add_draw_line(x1, y1, x2, y2)

    def draw_oval(self, left: float, top: float, right: float, bottom: float):
        self._buffer.add_draw_oval(left, top, right, bottom)

    def draw_arc(self, left: float, top: float, right: float, bottom: float,
                 start_angle: float, sweep_angle: float):
        self._buffer.add_draw_arc(left, top, right, bottom, start_angle, sweep_angle)

    def draw_sector(self, left: float, top: float, right: float, bottom: float,
                    start_angle: float, sweep_angle: float):
        self._buffer.add_draw_sector(left, top, right, bottom, start_angle, sweep_angle)

    def draw_path(self, path):
        """Draw a path. Accepts either an int path_id or a RemotePath object."""
        from .remote_path import RemotePath
        if isinstance(path, RemotePath):
            path_id = self._state.data_get_id(id(path))
            if path_id == -1:
                data = path.to_float_array()
                path_id = self._state.cache_data(id(path))
                self._buffer.add_path_data(path_id, data)
            self._buffer.add_draw_path(path_id)
        else:
            self._buffer.add_draw_path(path)

    def draw_tween_path(self, path1_id: int, path2_id: int, tween: float,
                        start: float, stop: float):
        self._buffer.add_draw_tween_path(path1_id, path2_id, tween, start, stop)

    def draw_bitmap(self, image_id: int, left: float, top: float,
                    right: float, bottom: float,
                    content_description: str = None):
        cd_id = 0
        if content_description is not None:
            cd_id = self.add_text(content_description)
        self._buffer.add_draw_bitmap(image_id, left, top, right, bottom, cd_id)

    def draw_scaled_bitmap(self, image_id: int,
                           src_left: float, src_top: float,
                           src_right: float, src_bottom: float,
                           dst_left: float, dst_top: float,
                           dst_right: float, dst_bottom: float,
                           scale_type: int, scale_factor: float,
                           content_description: str = None):
        cd_id = 0
        if content_description is not None:
            cd_id = self.add_text(content_description)
        self._buffer.draw_scaled_bitmap(
            image_id, src_left, src_top, src_right, src_bottom,
            dst_left, dst_top, dst_right, dst_bottom,
            scale_type, scale_factor, cd_id)

    def draw_text_run(self, text, start: int, end: int,
                      context_start: int, context_end: int,
                      x: float, y: float, rtl: bool):
        if isinstance(text, str):
            text_id = self.add_text(text)
        else:
            text_id = text
        self._buffer.add_draw_text_run(text_id, start, end,
                                       context_start, context_end, x, y, rtl)

    def draw_text_anchored(self, text, x: float, y: float,
                           pan_x: float, pan_y: float, flags: int = 0):
        if isinstance(text, str):
            text_id = self.add_text(text)
        else:
            text_id = text
        self._buffer.draw_text_anchored(text_id, x, y, pan_x, pan_y, flags)

    def draw_text_on_path(self, text_id: int, path_id: int,
                          h_offset: float, v_offset: float):
        self._buffer.add_draw_text_on_path(text_id, path_id, h_offset, v_offset)

    def draw_text_on_circle(self, text_id: int, center_x: float, center_y: float,
                            radius: float, start_angle: float,
                            warp_radius_offset: float, alignment, placement):
        self._buffer.add_draw_text_on_circle(
            text_id, center_x, center_y, radius, start_angle,
            warp_radius_offset, alignment, placement)

    def draw_bitmap_font_text_run(self, text_id: int, bitmap_font_id: int,
                                  start: int, end: int, x: float, y: float,
                                  glyph_spacing: float):
        self._buffer.add_draw_bitmap_font_text_run(
            text_id, bitmap_font_id, start, end, x, y, glyph_spacing)

    def draw_bitmap_text_anchored(self, text, bitmap_font_id: int,
                                  start: float, end: float,
                                  x: float, y: float,
                                  pan_x: float, pan_y: float,
                                  glyph_spacing: float):
        if isinstance(text, str):
            text_id = self.add_text(text)
        else:
            text_id = text
        self._buffer.draw_bitmap_text_anchored(
            text_id, bitmap_font_id, start, end, x, y, pan_x, pan_y, glyph_spacing)

    def draw_component_content(self):
        self._buffer.draw_component_content()

    # ── Path ──

    def add_path_data(self, data: list, winding: int = 0) -> int:
        cid = self._state.create_next_available_id()
        return self._buffer.add_path_data(cid, data, winding)

    def add_path_string(self, path_str: str) -> int:
        if self._platform is not None:
            path_obj = self._platform.parse_path(path_str)
            data = self._platform.path_to_float_array(path_obj)
            cid = self._state.cache_data(path_obj)
            return self._buffer.add_path_data(cid, data)
        raise RuntimeError("No platform available for path parsing")

    def path_tween(self, pid1: int, pid2: int, tween: float) -> int:
        out = self._state.create_next_available_id()
        return self._buffer.path_tween(out, pid1, pid2, tween)

    def path_create(self, x: float, y: float) -> int:
        out = self._state.create_next_available_id()
        return self._buffer.path_create(out, x, y)

    def path_append(self, path_id: int, *data: float):
        self._buffer.path_append(path_id, *data)

    def path_append_move_to(self, path_id: int, x: float, y: float):
        self.path_append(path_id, as_nan(10), x, y)  # MOVE=10

    def path_append_line_to(self, path_id: int, x: float, y: float):
        self.path_append(path_id, as_nan(11), 0.0, 0.0, x, y)  # LINE=11

    def path_append_quad_to(self, path_id: int,
                            x1: float, y1: float, x2: float, y2: float):
        self.path_append(path_id, as_nan(12), 0.0, 0.0,
                         x1, y1, x2, y2)  # QUADRATIC=12

    def path_append_cubic_to(self, path_id: int,
                             x1: float, y1: float,
                             x2: float, y2: float,
                             x3: float, y3: float):
        self.path_append(path_id, as_nan(14), 0.0, 0.0,
                         x1, y1, x2, y2, x3, y3)  # CUBIC=14

    def path_append_close(self, path_id: int):
        self._buffer.path_append(path_id, as_nan(15))  # CLOSE_NAN

    def path_append_reset(self, path_id: int):
        self._buffer.path_append(path_id, as_nan(17))  # RESET=17

    def path_combine(self, path1: int, path2: int, op: int) -> int:
        cid = self.next_id()
        self._buffer.path_combine(cid, path1, path2, op)
        return cid

    def add_path_expression(self, exp_x: list, exp_y: list,
                            start: float, end: float, count: float,
                            flags: int) -> int:
        cid = self._state.create_next_available_id()
        self._buffer.add_path_expression(cid, exp_x, exp_y, start, end, count, flags)
        return cid

    def add_polar_path_expression(self, expression_r: list,
                                  start: float, end: float, count: float,
                                  center_x: float, center_y: float,
                                  flags: int) -> int:
        from .rc import Rc
        cid = self._state.create_next_available_id()
        self._buffer.add_path_expression(
            cid, expression_r, [center_x, center_y],
            start, end, count, Rc.PathExpression.POLAR_PATH | flags)
        return cid

    # ── Matrix ──

    def skew(self, skew_x: float, skew_y: float):
        self._buffer.add_matrix_skew(skew_x, skew_y)

    def rotate(self, angle: float, center_x: float = float('nan'),
               center_y: float = float('nan')):
        self._buffer.add_matrix_rotate(angle, center_x, center_y)

    def save(self):
        self._buffer.add_matrix_save()

    def restore(self):
        self._buffer.add_matrix_restore()

    def translate(self, dx: float, dy: float):
        self._buffer.add_matrix_translate(dx, dy)

    def scale(self, scale_x: float, scale_y: float,
              center_x: float = float('nan'), center_y: float = float('nan')):
        self._buffer.add_matrix_scale(scale_x, scale_y, center_x, center_y)

    def matrix_from_path(self, path_id: int, fraction: float,
                         v_offset: float, flags: int):
        self._buffer.set_matrix_from_path(path_id, fraction, v_offset, flags)

    def add_clip_path(self, path_id: int):
        self._buffer.add_clip_path(path_id)

    def clip_rect(self, left: float, top: float, right: float, bottom: float):
        self._buffer.add_clip_rect(left, top, right, bottom)

    # ── Click Area ──

    def add_click_area(self, area_id: int, content_description: str,
                       left: float, top: float, right: float, bottom: float,
                       metadata: str = None):
        cd_id = 0
        if content_description is not None:
            cd_id = self.add_text(content_description)
        meta_id = 0
        if metadata is not None:
            meta_id = self.add_text(metadata)
        self._buffer.add_click_area(area_id, cd_id, left, top, right, bottom, meta_id)

    # ── Root content behavior ──

    def set_root_content_behavior(self, scroll: int, alignment: int,
                                  sizing: int, mode: int):
        self._buffer.set_root_content_behavior(scroll, alignment, sizing, mode)

    # ── Layout: Root ──

    def root(self, content):
        self._insert_point = self._buffer._buffer.get_size()
        self._buffer.add_root_start()
        content()
        self._buffer.add_container_end()

    def add_content_start(self):
        self._buffer.add_content_start()

    def add_container_end(self):
        self._buffer.add_container_end()

    # ── Layout: Box ──

    def box(self, modifier: RecordingModifier, horizontal: int = 0,
            vertical: int = 0, content=None):
        if content is not None:
            self.start_box(modifier, horizontal, vertical)
            content()
            self.end_box()
        else:
            self._buffer.add_box_start(modifier.get_component_id(), -1,
                                       horizontal, vertical)
            for m in modifier.get_list():
                m.write(self)
            self._buffer.add_container_end()

    def start_box(self, modifier: RecordingModifier,
                  horizontal: int = 0, vertical: int = 0):
        self._buffer.add_box_start(modifier.get_component_id(), -1,
                                   horizontal, vertical)
        for m in modifier.get_list():
            m.write(self)
        self.add_content_start()

    def end_box(self):
        self._buffer.add_container_end()
        self._buffer.add_container_end()

    # ── Layout: FitBox ──

    def fit_box(self, modifier: RecordingModifier, horizontal: int = 0,
                vertical: int = 0, content=None):
        self.start_fit_box(modifier, horizontal, vertical)
        if content is not None:
            content()
        self.end_fit_box()

    def start_fit_box(self, modifier: RecordingModifier,
                      horizontal: int = 0, vertical: int = 0):
        self._buffer.add_fit_box_start(modifier.get_component_id(), -1,
                                       horizontal, vertical)
        for m in modifier.get_list():
            m.write(self)
        self.add_content_start()

    def end_fit_box(self):
        self._buffer.add_container_end()
        self._buffer.add_container_end()

    # ── Layout: Row ──

    def row(self, modifier: RecordingModifier, horizontal: int = 0,
            vertical: int = 0, content=None):
        self.start_row(modifier, horizontal, vertical)
        if content is not None:
            content()
        self.end_row()

    def start_row(self, modifier: RecordingModifier,
                  horizontal: int = 0, vertical: int = 0):
        self._buffer.add_row_start(modifier.get_component_id(), -1,
                                   horizontal, vertical,
                                   modifier.get_spaced_by())
        for m in modifier.get_list():
            m.write(self)
        self.add_content_start()

    def end_row(self):
        self._buffer.add_container_end()
        self._buffer.add_container_end()

    # ── Layout: Column ──

    def column(self, modifier: RecordingModifier, horizontal: int = 0,
               vertical: int = 0, content=None):
        self.start_column(modifier, horizontal, vertical)
        if content is not None:
            content()
        self.end_column()

    def start_column(self, modifier: RecordingModifier,
                     horizontal: int = 0, vertical: int = 0):
        self._buffer.add_column_start(modifier.get_component_id(), -1,
                                      horizontal, vertical,
                                      modifier.get_spaced_by())
        for m in modifier.get_list():
            m.write(self)
        self.add_content_start()

    def end_column(self):
        self._buffer.add_container_end()
        self._buffer.add_container_end()

    # ── Layout: Collapsible Row / Column ──

    def collapsible_row(self, modifier: RecordingModifier,
                        horizontal: int = 0, vertical: int = 0, content=None):
        self.start_collapsible_row(modifier, horizontal, vertical)
        if content is not None:
            content()
        self.end_collapsible_row()

    def start_collapsible_row(self, modifier: RecordingModifier,
                              horizontal: int = 0, vertical: int = 0):
        self._buffer.add_collapsible_row_start(
            modifier.get_component_id(), -1, horizontal, vertical,
            modifier.get_spaced_by())
        for m in modifier.get_list():
            m.write(self)
        self.add_content_start()

    def end_collapsible_row(self):
        self._buffer.add_container_end()
        self._buffer.add_container_end()

    def collapsible_column(self, modifier: RecordingModifier,
                           horizontal: int = 0, vertical: int = 0, content=None):
        self.start_collapsible_column(modifier, horizontal, vertical)
        if content is not None:
            content()
        self.end_collapsible_column()

    def start_collapsible_column(self, modifier: RecordingModifier,
                                 horizontal: int = 0, vertical: int = 0):
        self._buffer.add_collapsible_column_start(
            modifier.get_component_id(), -1, horizontal, vertical,
            modifier.get_spaced_by())
        for m in modifier.get_list():
            m.write(self)
        self.add_content_start()

    def end_collapsible_column(self):
        self._buffer.add_container_end()
        self._buffer.add_container_end()

    # ── Layout: Flow ──

    def flow(self, modifier: RecordingModifier, horizontal: int = 0,
             vertical: int = 0, content=None):
        self.start_flow(modifier, horizontal, vertical)
        if content is not None:
            content()
        self.end_flow()

    def start_flow(self, modifier: RecordingModifier,
                   horizontal: int = 0, vertical: int = 0):
        self._buffer.add_flow_start(modifier.get_component_id(), -1,
                                    horizontal, vertical,
                                    modifier.get_spaced_by())
        for m in modifier.get_list():
            m.write(self)
        self.add_content_start()

    def end_flow(self):
        self._buffer.add_container_end()
        self._buffer.add_container_end()

    # ── Layout: Canvas ──

    def canvas(self, modifier: RecordingModifier, content=None):
        self.start_canvas(modifier)
        if content is not None:
            content()
        self.end_canvas()

    def start_canvas(self, modifier: RecordingModifier):
        self._buffer.add_canvas_start(modifier.get_component_id(), -1)
        for m in modifier.get_list():
            m.write(self)
        self.add_content_start()
        if self._api_level <= 7:
            self._buffer.add_canvas_content_start(-1)

    def end_canvas(self):
        if self._api_level <= 7:
            self._buffer.add_container_end()
        self._buffer.add_container_end()
        self._buffer.add_container_end()

    def start_canvas_operations(self):
        self._buffer.add_canvas_operations_start()

    def end_canvas_operations(self):
        self._buffer.add_container_end()

    def start_run_actions(self):
        self._buffer.add_run_actions_start()

    def end_run_actions(self):
        self._buffer.add_container_end()

    # ── Layout: Image ──

    def image(self, modifier: RecordingModifier, image_id: int,
              scale_type: int, alpha: float):
        self._buffer.add_image(modifier.get_component_id(), -1,
                               image_id, scale_type, alpha)
        for m in modifier.get_list():
            m.write(self)
        self._buffer.add_container_end()

    # ── Layout: State ──

    def state_layout(self, modifier: RecordingModifier, index_id: int,
                     content=None):
        self.start_state_layout(modifier, index_id)
        if content is not None:
            content()
        self.end_state_layout()

    def start_state_layout(self, modifier: RecordingModifier, index_id: int):
        self._buffer.add_state_layout(modifier.get_component_id(), -1,
                                      0, 0, index_id)
        for m in modifier.get_list():
            m.write(self)
        self.add_content_start()

    def end_state_layout(self):
        self._buffer.add_container_end()
        self._buffer.add_container_end()

    # ── Layout: Text Component ──

    def text_component(self, modifier: RecordingModifier, text_id: int,
                       color: int, font_size: float, font_style: int,
                       font_weight: float, font_family: str = None,
                       text_align: int = 1, overflow: int = 1,
                       max_lines: int = 0x7FFFFFFF, content=None,
                       autosize: bool = False,
                       min_font_size: float = -1.0,
                       max_font_size: float = -1.0,
                       use_core_text: bool = False):
        self.start_text_component(modifier, text_id, color, font_size,
                                  font_style, font_weight, font_family,
                                  text_align, overflow, max_lines,
                                  autosize=autosize,
                                  min_font_size=min_font_size,
                                  max_font_size=max_font_size,
                                  use_core_text=use_core_text)
        if content is not None:
            content()
        self.end_text_component()

    def start_text_component(self, modifier: RecordingModifier, text_id: int,
                             color: int, font_size: float, font_style: int,
                             font_weight: float, font_family: str = None,
                             text_align: int = 0, overflow: int = 0,
                             max_lines: int = 0x7FFFFFFF,
                             autosize: bool = False,
                             min_font_size: float = -1.0,
                             max_font_size: float = -1.0,
                             use_core_text: bool = False):
        font_family_id = -1
        if font_family is not None:
            font_family_id = self.add_text(font_family)
        if use_core_text or autosize or min_font_size >= 0 or max_font_size >= 0:
            # Use CoreText (opcode 239) — matches Java's extended overload
            self._buffer.add_core_text_start(
                modifier.get_component_id(), -1, text_id,
                color, -1,  # colorId default
                font_size, min_font_size, max_font_size,
                font_style, font_weight, font_family_id,
                text_align, overflow, max_lines,
                0.0, 0.0, 1.0,  # letterSpacing, lineHeightAdd, lineHeightMultiplier
                0, 0, 0,  # lineBreakStrategy, hyphenationFrequency, justificationMode
                False, False, autosize,
                0, -1)  # flags, textStyleId
        else:
            # Use TextLayout (opcode 208) — matches Java's simple overload
            self._buffer.add_text_component_start(
                modifier.get_component_id(), -1, text_id, color,
                font_size, font_style, font_weight, font_family_id,
                0, text_align, overflow, max_lines)
        for m in modifier.get_list():
            m.write(self)
        self.add_content_start()

    def end_text_component(self):
        self._buffer.add_container_end()
        self._buffer.add_container_end()

    # ── Loop ──

    def start_loop(self, index_id: int, from_val: float,
                   step: float, until: float):
        self._buffer.add_loop_start(index_id, from_val, step, until)

    def start_loop_var(self, from_val: float, step: float, until: float) -> float:
        index_id = self._state.create_next_available_id()
        self._buffer.add_loop_start(index_id, from_val, step, until)
        return as_nan(index_id)

    def start_loop_count(self, count: float) -> float:
        """Start a loop from 0 to count with step 1. Returns loop var as NaN ID."""
        return self.start_loop_var(0.0, 1.0, count)

    def end_loop(self):
        self._buffer.add_loop_end()

    def loop(self, index_id: int, from_val, step, until, content):
        """Convenience: start_loop + content() + end_loop."""
        self.start_loop(index_id, float(from_val), float(step), float(until))
        content()
        self.end_loop()

    def loop_var(self, from_val: float, step: float, until: float, content) -> float:
        """Convenience: start_loop_var + content() + end_loop."""
        var = self.start_loop_var(from_val, step, until)
        content(var)
        self.end_loop()
        return var

    # ── Touch ──

    def add_touch(self, def_value: float, min_val: float, max_val: float,
                  touch_mode: int, velocity_id: float, touch_effects: int,
                  touch_spec: list = None, easing_spec: list = None,
                  *exp: float) -> float:
        cid = self._state.create_next_available_id()
        self._buffer.add_touch_expression(
            cid, def_value, min_val, max_val, velocity_id, touch_effects,
            list(exp), touch_mode, touch_spec, easing_spec)
        return as_nan(cid)

    # ── Bitmap ──

    def store_bitmap(self, image_id: int, width: int, height: int,
                     data: bytes) -> int:
        self._buffer.add_bitmap_data(image_id, width, height, data)
        return image_id

    def add_bitmap_data(self, width: int, height: int, data: bytes) -> int:
        cid = self._state.create_next_available_id()
        self._buffer.add_bitmap_data(cid, width, height, data)
        return cid

    def add_font(self, data: bytes) -> int:
        cid = self._state.create_next_available_id()
        self._buffer.add_font(cid, 0, data)
        return cid

    def add_bitmap_font(self, glyphs: list, kerning_table: dict = None) -> int:
        cid = self._state.create_next_available_id()
        self._buffer.add_bitmap_font(cid, glyphs, kerning_table)
        return cid

    def create_bitmap(self, width: int, height: int) -> int:
        cid = self._state.create_next_available_id()
        return self._buffer.create_bitmap(cid, width, height)

    def add_bitmap_png(self, width: int, height: int, png_data: bytes) -> int:
        cid = self._state.create_next_available_id()
        self._buffer.store_bitmap(cid, width, height, png_data)
        return cid

    def add_bitmap_a8(self, width: int, height: int, data: bytes) -> int:
        cid = self._state.create_next_available_id()
        self._buffer.store_bitmap_a8(cid, width, height, data)
        return cid

    def add_bitmap_url(self, url: str) -> int:
        cid = self._state.create_next_available_id()
        self._buffer.store_bitmap_url(cid, url)
        return cid

    def draw_on_bitmap(self, bitmap_id: int, mode: int = 0, color: int = 0):
        self._buffer.draw_on_bitmap(bitmap_id, mode, color)

    # ── Modifier Operations (called by modifier Element.write) ──

    def add_width_modifier_operation(self, dim_type: int, value: float):
        self._buffer.add_width_modifier_operation(dim_type, value)

    def add_height_modifier_operation(self, dim_type: int, value: float):
        self._buffer.add_height_modifier_operation(dim_type, value)

    def add_modifier_padding(self, left: float, top: float,
                             right: float, bottom: float):
        self._buffer.add_modifier_padding(left, top, right, bottom)

    def add_modifier_background(self, *args):
        self._buffer.add_modifier_background(*args)

    def add_dynamic_modifier_background(self, color_id: int, shape: int):
        self._buffer.add_dynamic_modifier_background(color_id, shape)

    def add_modifier_border(self, width: float, rounded_corner: float,
                            color: int, shape_type: int):
        self._buffer.add_modifier_border(width, rounded_corner, color, shape_type)

    def add_modifier_dynamic_border(self, width: float, rounded_corner: float,
                                    color_id: int, shape_type: int):
        self._buffer.add_modifier_dynamic_border(width, rounded_corner,
                                                 color_id, shape_type)

    def add_clip_rect_modifier(self):
        self._buffer.add_clip_rect_modifier()

    def add_round_clip_rect_modifier(self, top_start: float, top_end: float,
                                     bottom_start: float, bottom_end: float):
        self._buffer.add_round_clip_rect_modifier(top_start, top_end,
                                                  bottom_start, bottom_end)

    def add_modifier_offset(self, x: float, y: float):
        self._buffer.add_modifier_offset(x, y)

    def add_component_visibility_operation(self, value_id: int):
        self._buffer.add_component_visibility_operation(value_id)

    def add_modifier_z_index(self, value: float):
        self._buffer.add_modifier_z_index(value)

    def add_click_modifier_operation(self):
        self._buffer.add_click_modifier_operation()

    def add_touch_down_modifier_operation(self):
        self._buffer.add_touch_down_modifier_operation()

    def add_touch_up_modifier_operation(self):
        self._buffer.add_touch_up_modifier_operation()

    def add_touch_cancel_modifier_operation(self):
        self._buffer.add_touch_cancel_modifier_operation()

    def add_modifier_graphics_layer(self, attributes: dict):
        self._buffer.add_modifier_graphics_layer(attributes)

    def add_modifier_scroll(self, direction: int, position_id: float,
                            notches: int = None):
        from .types.nan_utils import id_from_nan
        from .rc import Rc
        max_val = self.reserve_float_variable()
        notch_max = self.reserve_float_variable()
        touch_dir = (Rc.Touch.POSITION_X if direction != 0
                     else Rc.Touch.POSITION_Y)
        self._buffer.add_modifier_scroll(direction, position_id, max_val,
                                         notch_max)
        if notches is not None and notches > 0:
            self._buffer.add_touch_expression(
                id_from_nan(position_id), 0.0, 0.0, max_val, 0.0, 3,
                [touch_dir, -1.0, Rc.FloatExpression.MUL],
                Rc.Touch.STOP_NOTCHES_EVEN,
                [float(notches), notch_max], None)
        else:
            self._buffer.add_touch_expression(
                id_from_nan(position_id), 0.0, 0.0, max_val, 0.0, 3,
                [touch_dir, -1.0, Rc.FloatExpression.MUL],
                Rc.Touch.STOP_GENTLY, None, None)
        self._buffer.add_container_end()

    def add_modifier_ripple(self):
        self._buffer.add_modifier_ripple()

    def add_modifier_marquee(self, iterations: int, animation_mode: int,
                             repeat_delay_millis: float,
                             initial_delay_millis: float,
                             spacing: float, velocity: float):
        self._buffer.add_modifier_marquee(iterations, animation_mode,
                                          repeat_delay_millis,
                                          initial_delay_millis,
                                          spacing, velocity)

    def add_draw_content_operation(self):
        self._buffer.add_draw_content_operation()

    def add_align_by_modifier(self, line: float):
        self._buffer.add_modifier_align_by(line)

    def add_animation_spec_modifier(self, animation_id: int,
                                    motion_duration: float,
                                    motion_easing_type: int,
                                    visibility_duration: float,
                                    visibility_easing_type: int,
                                    enter_animation: int,
                                    exit_animation: int):
        self._buffer.add_animation_spec_modifier(
            animation_id, motion_duration, motion_easing_type,
            visibility_duration, visibility_easing_type,
            enter_animation, exit_animation)

    def add_collapsible_priority_modifier(self, orientation: int,
                                          priority: float):
        self._buffer.add_collapsible_priority_modifier(orientation, priority)

    def add_width_in_modifier_operation(self, min_val: float, max_val: float):
        self._buffer.add_width_in_modifier_operation(min_val, max_val)

    def add_height_in_modifier_operation(self, min_val: float, max_val: float):
        self._buffer.add_height_in_modifier_operation(min_val, max_val)

    def add_layout_compute(self, compute_type: int, commands):
        from .types.nan_utils import as_nan
        bounds_id = self.create_id(2)  # TYPE_ARRAY (NanMap namespace 2)
        self._buffer.start_layout_compute(compute_type, bounds_id, False)
        self.add_dynamic_float_array(bounds_id, 6.0)
        commands(compute_type, bounds_id, self)
        self._buffer.end_layout_compute()

    def add_semantics_modifier(self, content_description_id: int, role: int,
                               text_id: int, state_description_id: int,
                               mode: int, enabled: bool, clickable: bool):
        self._buffer.add_semantics_modifier(
            content_description_id, role, text_id, state_description_id,
            mode, enabled, clickable)

    # ── Action Operations ──

    def add_action(self, *actions):
        for action in actions:
            action.write(self)

    def add_value_string_change_action_operation(self, dest_id: int, src_id: int):
        self._buffer.add_value_string_change_action_operation(dest_id, src_id)

    def add_value_integer_expression_change_action_operation(self, dest_id: int,
                                                             src_id: int):
        self._buffer.add_value_integer_expression_change_action_operation(dest_id, src_id)

    def add_value_float_change_action_operation(self, value_id: int, value: float):
        self._buffer.add_value_float_change_action_operation(value_id, value)

    def add_value_integer_change_action_operation(self, value_id: int, value: int):
        self._buffer.add_value_integer_change_action_operation(value_id, value)

    def add_value_float_expression_change_action_operation(self, value_id: int,
                                                           value: int):
        self._buffer.add_value_float_expression_change_action_operation(value_id, value)

    # ── Host Actions ──

    def add_host_action(self, action_id: int):
        self._buffer.add_host_action(action_id)

    def add_host_action_metadata(self, action_id: int, metadata_id: int):
        self._buffer.add_host_action_metadata(action_id, metadata_id)

    def add_host_named_action(self, text_id: int, action_type: int,
                              value_id: int):
        self._buffer.add_host_named_action(text_id, action_type, value_id)

    # ── Array / List ──

    def add_string_list(self, *strings: str) -> float:
        ids = [self.text_create_id(s) for s in strings]
        return self.add_list(ids)

    def add_list(self, list_ids: list) -> float:
        cid = self._state.cache_data(list_ids, 2)  # TYPE_ARRAY
        self._buffer.add_list(cid, list_ids)
        return as_nan(cid)

    def add_float_list(self, values: list) -> float:
        list_ids = []
        for v in values:
            fid = self._state.cache_float(v)
            self._buffer.add_float(fid, v)
            list_ids.append(fid)
        return self.add_list(list_ids)

    def add_float_array(self, values_or_size, array_id: int = None):
        if isinstance(values_or_size, (list, tuple)):
            values = values_or_size
            cid = self._state.cache_data(values, 2)
            self._buffer.add_float_array(cid, values)
            return as_nan(cid)
        elif array_id is not None:
            size = values_or_size
            values = [0.0] * int(size)
            self._state.cache_data_with_id(array_id, values)
            self._buffer.add_float_array(array_id, values)
            return as_nan(array_id)
        else:
            size = values_or_size
            values = [0.0] * int(size)
            cid = self._state.cache_data(values, 2)
            self._buffer.add_dynamic_float_array(cid, size)
            return as_nan(cid)

    def add_dynamic_float_array(self, array_id: int = None,
                                size: float = 0) -> float:
        if array_id is None:
            array_id = self.create_id(5)
        self._buffer.add_dynamic_float_array(array_id, size)
        return as_nan(array_id)

    def set_array_value(self, array_id: int, index: float, value: float):
        self._buffer.set_array_value(array_id, index, value)

    # ── Conditional ──

    def add_conditional_operations(self, cond_type: int, a: float, b: float):
        self._buffer.add_conditional_operations(cond_type, a, b)

    conditional_operations = add_conditional_operations

    def conditional_operations_block(self, cond_type: int, a: float, b: float,
                                     content):
        """conditionalOperations(type, a, b, content) — Java overload with callback."""
        self.add_conditional_operations(cond_type, a, b)
        content()
        self.end_conditional_operations()

    def end_conditional_operations(self):
        self._buffer.end_conditional_operations()

    # ── Haptic / Wake ──

    def perform_haptic(self, feedback_constant: int):
        self._buffer.perform_haptic(feedback_constant)

    def wake_in(self, seconds: float):
        self._buffer.wake_in(seconds)

    # ── Debug ──

    def add_debug_message(self, message, value: float = 0.0, flag: int = 0):
        if isinstance(message, str):
            text_id = self.add_text(message)
        else:
            text_id = message
        self._buffer.add_debug_message(text_id, value, flag)

    def rem(self, message: str):
        self._buffer.rem(message)

    # ── Skip ──

    def begin_skip(self, skip_type: int, value: int) -> int:
        return self._buffer.begin_skip(skip_type, value)

    def end_skip(self, offset: int):
        self._buffer.end_skip(offset)

    # ── Global sections ──

    def begin_global(self):
        if self._start_global_section != -1:
            raise RuntimeError("Trying to start a global section twice")
        self._start_global_section = self._buffer._buffer.get_size()

    def end_global(self):
        if self._start_global_section == -1:
            raise RuntimeError("Trying to end a global section without a begin")
        num_bytes = self._buffer._buffer.get_size() - self._start_global_section
        self._buffer._buffer.move_block(self._start_global_section,
                                        self._insert_point)
        if self._insert_point != -1:
            self._insert_point += num_bytes
        self._start_global_section = -1

    # ── ID allocation ──

    def create_id(self, type_hint: int = 0) -> int:
        return self._state.create_next_available_id(type_hint)

    def next_id(self) -> int:
        return self._state.create_next_available_id()

    def create_float_id(self) -> float:
        return self.as_float_id(self.create_id(0))

    # ── Shader ──

    def create_shader(self, shader_string: str):
        from .shader import RemoteComposeShader
        return RemoteComposeShader(shader_string, self)

    # ── Animation packing (static) ──

    @staticmethod
    def pack_animation(duration: float, easing_type: int,
                       spec: list = None, initial_value: float = float('nan'),
                       wrap: float = float('nan')) -> list:
        return RemoteComposeBuffer.pack_animation(
            duration, easing_type, spec, initial_value, wrap)

    @staticmethod
    def anim(duration: float, easing_type: int = 0, spec: list = None,
             initial_value: float = float('nan'),
             wrap: float = float('nan')) -> list:
        return RemoteComposeBuffer.pack_animation(
            duration, easing_type, spec, initial_value, wrap)

    @staticmethod
    def exp(*value: float) -> list:
        return list(value)

    # ── Component Values ──

    def add_component_value(self, component_id: int, value_type: int) -> float:
        key = (component_id, value_type)
        cached = self._component_values_cache.get(key)
        if cached is not None:
            return cached
        cid = self._state.create_next_available_id()
        self._buffer.add_component_value(cid, component_id, value_type)
        result = as_nan(cid)
        self._component_values_cache[key] = result
        return result

    def add_component_width_value(self) -> float:
        return self.add_component_value(
            self._buffer.get_last_component_id(), 0)  # WIDTH

    def add_component_height_value(self) -> float:
        return self.add_component_value(
            self._buffer.get_last_component_id(), 1)  # HEIGHT

    def add_component_x_value(self) -> float:
        return self.add_component_value(
            self._buffer.get_last_component_id(), 2)  # POS_X

    def add_component_y_value(self) -> float:
        return self.add_component_value(
            self._buffer.get_last_component_id(), 3)  # POS_Y

    def add_component_root_x_value(self) -> float:
        return self.add_component_value(
            self._buffer.get_last_component_id(), 4)  # POS_ROOT_X

    def add_component_root_y_value(self) -> float:
        return self.add_component_value(
            self._buffer.get_last_component_id(), 5)  # POS_ROOT_Y

    def add_component_content_width_value(self) -> float:
        return self.add_component_value(
            self._buffer.get_last_component_id(), 6)  # CONTENT_WIDTH

    def add_component_content_height_value(self) -> float:
        return self.add_component_value(
            self._buffer.get_last_component_id(), 7)  # CONTENT_HEIGHT

    # ── Attribute Accessors ──

    def bitmap_attribute(self, bitmap_id: int, attribute: int) -> float:
        cid = self._state.create_next_available_id()
        self._buffer.bitmap_attribute(cid, bitmap_id, attribute)
        return as_nan(cid)

    def text_attribute(self, text_id: int, attribute: int) -> float:
        cid = self._state.create_next_available_id()
        self._buffer.text_attribute(cid, text_id, attribute)
        return as_nan(cid)

    def time_attribute(self, long_id: int, attr_type: int, *args: int) -> float:
        cid = self._state.create_next_available_id()
        self._buffer.time_attribute(cid, long_id, attr_type, list(args) if args else None)
        return as_nan(cid)

    # ── Data Map ──

    # DataMapIds type constants
    DATA_MAP_TYPE_STRING = 0
    DATA_MAP_TYPE_INT = 1
    DATA_MAP_TYPE_FLOAT = 2
    DATA_MAP_TYPE_LONG = 3
    DATA_MAP_TYPE_BOOLEAN = 4

    def add_data_map(self, *entries) -> int:
        """Add a data map. Each entry is a (name, value) tuple.

        Values can be str, int, float, or bool.
        Returns the map ID.
        """
        names = []
        ids = []
        types = []
        for name, value in entries:
            if isinstance(value, str):
                vid = self.add_text(value)
                types.append(self.DATA_MAP_TYPE_STRING)
            elif isinstance(value, bool):
                vid = self.add_boolean(value)
                types.append(self.DATA_MAP_TYPE_BOOLEAN)
            elif isinstance(value, int):
                vid = self._state.cache_integer(value)
                self._buffer.add_integer(vid, value)
                types.append(self.DATA_MAP_TYPE_INT)
            elif isinstance(value, float):
                fid = self.add_float_constant(value)
                vid = id_from_nan(fid)
                types.append(self.DATA_MAP_TYPE_FLOAT)
            else:
                raise ValueError(f"Unsupported data map value type: {type(value)}")
            names.append(name)
            ids.append(vid)
        map_id = self._state.cache_data(ids, 2)
        self._buffer.add_map(map_id, names, types, ids)
        return map_id

    def add_data_map_by_ids(self, keys: list, ids: list) -> float:
        """Add a map from string keys to pre-allocated data IDs.

        Returns the map ID as a float (for use in float expressions).
        """
        map_id = self._state.cache_data(ids, 2)
        self._buffer.add_map(map_id, keys, None, ids)
        return map_id

    # ── Lookup ──

    def map_lookup(self, map_id: int, str_or_id) -> int:
        if isinstance(str_or_id, str):
            str_id = self.add_text(str_or_id)
        else:
            str_id = str_or_id
        hash_key = map_id + str_id * 33
        existing = self._state.data_get_id(hash_key)
        if existing != -1:
            return existing
        cid = self._state.cache_data(hash_key)
        self._buffer.map_lookup(cid, map_id, str_id)
        return cid

    def id_lookup(self, array_id: float, index: float) -> int:
        cid = self._state.create_next_available_id()
        self._buffer.id_lookup(cid, array_id, index)
        return cid

    # ── Animation Specs ──

    def spring(self, stiffness: float, damping: float,
               stop_threshold: float, boundary_mode: int) -> list:
        from .types.nan_utils import int_bits_to_float
        return [0.0, stiffness, damping, stop_threshold,
                int_bits_to_float(boundary_mode)]

    def easing(self, max_time: float, max_acceleration: float,
               max_velocity: float) -> list:
        return [0.0, max_time, max_acceleration, max_velocity]

    # ── Text Style ──

    def add_text_style(self, color=None, color_id=None, font_size=None,
                       min_font_size=None, max_font_size=None,
                       font_style=None, font_weight=None,
                       font_family=None, text_align=None,
                       overflow=None, max_lines=None,
                       letter_spacing=None, line_height_add=None,
                       line_height_multiplier=None,
                       line_break_strategy=None,
                       hyphenation_frequency=None,
                       justification_mode=None,
                       underline=None, strikethrough=None,
                       font_axis=None, font_axis_values=None,
                       autosize=None, parent_id: int = 0) -> int:
        cid = self._state.create_next_available_id()
        font_family_id = None
        if font_family is not None:
            font_family_id = self.add_text(font_family)
        font_axis_tags = None
        if font_axis is not None:
            font_axis_tags = [self.add_text(a) for a in font_axis]
        self._buffer.add_text_style(
            cid, color, color_id, font_size, min_font_size, max_font_size,
            font_style, font_weight, font_family_id, text_align,
            overflow, max_lines, letter_spacing, line_height_add,
            line_height_multiplier, line_break_strategy,
            hyphenation_frequency, justification_mode,
            underline, strikethrough, font_axis_tags, font_axis_values,
            autosize, parent_id)
        return cid

    # ── Impulse / Particles / Functions ──

    def impulse(self, duration: float, start: float, content=None):
        self._buffer.add_impulse(duration, start)
        if content is not None:
            content()
            self._buffer.add_impulse_end()

    def impulse_process(self, content=None):
        self._buffer.add_impulse_process()
        if content is not None:
            content()
            self._buffer.add_impulse_end()

    def impulse_end(self):
        self._buffer.add_impulse_end()

    def create_float_function(self, args: list) -> int:
        fid = self._state.create_next_available_id()
        int_args = []
        for i in range(len(args)):
            a_id = self.create_id(0)
            int_args.append(a_id)
            args[i] = self.as_float_id(a_id)
        self._buffer.define_float_function(fid, int_args)
        return fid

    def end_float_function(self):
        self._buffer.add_end_float_function_def()

    def call_float_function(self, func_id: int, *args: float):
        self._buffer.call_float_function(func_id, list(args))

    # ── Bitmap text measure ──

    def bitmap_text_measure(self, text_id: int, bm_font_id: int,
                            measure_width: int, glyph_spacing: float) -> float:
        cid = self._state.create_next_available_id()
        self._buffer.bitmap_text_measure(cid, text_id, bm_font_id,
                                         measure_width, glyph_spacing)
        return as_nan(cid)

    # ── Float map ──

    def add_float_map(self, keys: list, values: list) -> float:
        """Add a map of string keys to float values. Returns NaN-encoded ID."""
        list_ids = []
        types = []
        for v in values:
            fid = self._state.cache_float(v)
            self._buffer.add_float(fid, v)
            list_ids.append(fid)
            types.append(2)  # DataMapIds.TYPE_FLOAT
        map_id = self._state.cache_data(list_ids, 2)  # NanMap.TYPE_ARRAY
        self._buffer.add_map(map_id, keys, types, list_ids)
        return as_nan(map_id)

    # ── Time long ──

    def add_time_long(self, time: int) -> int:
        return self.add_long(time)

    # ── Bitmap naming ──

    def name_bitmap_id(self, id: int, name: str):
        self._buffer.set_bitmap_name(id, name)

    # ── Bitmap font text on path ──

    def draw_bitmap_font_text_run_on_path(self, text_id: int, bitmap_font_id: int,
                                           path_id: int, start: int, end: int,
                                           y_adj: float, glyph_spacing: float = 0.0):
        self._buffer.add_draw_bitmap_font_text_run_on_path(
            text_id, bitmap_font_id, path_id, start, end, y_adj, glyph_spacing)

    # ── Particles ──

    def create_particles(self, variables: list, initial_expressions: list,
                         particle_count: int) -> float:
        """Create a particle system.

        Args:
            variables: list of floats — will be OVERWRITTEN with NaN-encoded var IDs.
            initial_expressions: list of float lists — RPN init equations per variable.
            particle_count: number of particles.

        Returns:
            NaN-encoded particle system ID.
        """
        pid = self.create_id(0)
        index = self.as_float_id(pid)
        var_ids = []
        for i in range(len(variables)):
            vid = self.create_id(0)
            var_ids.append(vid)
            variables[i] = self.as_float_id(vid)
        self._buffer.add_particles(pid, var_ids, initial_expressions, particle_count)
        return index

    def particles_loop(self, particle_id: float, restart: list,
                       expressions: list, content=None):
        self._buffer.add_particles_loop(
            id_from_nan(particle_id), restart, expressions)
        if content is not None:
            content()
        self._buffer.add_particle_loop_end()

    def particles_comparison(self, particle_id: float, flags: int,
                              min_val: float, max_val: float,
                              condition: list, then1: list,
                              then2: list = None, content=None):
        self._buffer.add_particles_comparison(
            id_from_nan(particle_id), flags, min_val, max_val,
            condition, then1, then2)
        if content is not None:
            content()
        self._buffer.add_particle_loop_end()

"""RemoteComposeContext — Pythonic DSL for building RemoteCompose documents.

Provides a high-level API that wraps RemoteComposeWriter with a fluent,
Pythonic context-manager style interface matching the Kotlin DSL.

Usage:
    ctx = RcContext(400, 400, "MyDemo")
    with ctx.root():
        with ctx.box(Modifier().fill_max_size().background(0xFFFFFFFF)):
            ctx.text("Hello World", font_size=24.0)
    data = ctx.encode()
"""

from __future__ import annotations
from contextlib import contextmanager

from .writer import RemoteComposeWriter
from .modifiers.recording_modifier import RecordingModifier
from .rc import Rc
from .types.rfloat import RFloat, _coerce


# Convenient alias
Modifier = RecordingModifier

# Default text constants
DEFAULT_FONT_SIZE = 36.0
DEFAULT_FONT_WEIGHT = 400.0


class RcContext:
    """High-level DSL for creating RemoteCompose documents."""

    def __init__(self, width: int = 0, height: int = 0,
                 content_description: str = "",
                 api_level: int = 8,
                 profiles: int = 0x200,
                 platform=None,
                 header_tag_order: list = None,
                 extra_tags: dict = None):
        self._writer = RemoteComposeWriter(
            width, height, content_description,
            api_level, profiles, platform,
            header_tag_order=header_tag_order,
            extra_tags=extra_tags)
        self._cached_time_string = -1

    @property
    def writer(self) -> RemoteComposeWriter:
        return self._writer

    def encode(self) -> bytes:
        return self._writer.encode_to_byte_array()

    def save(self, path: str):
        with open(path, 'wb') as f:
            f.write(self.encode())

    # ── Layout context managers ──

    @contextmanager
    def root(self):
        self._writer._insert_point = self._writer._buffer._buffer.get_size()
        self._writer._buffer.add_root_start()
        try:
            yield self
        finally:
            self._writer._buffer.add_container_end()

    def box_leaf(self, modifier: RecordingModifier = None,
                 horizontal: int = Rc.Layout.CENTER,
                 vertical: int = Rc.Layout.CENTER):
        """Add a leaf box (no children). Matches Kotlin's box(modifier) overload."""
        if modifier is None:
            modifier = RecordingModifier()
        self._writer.box(modifier, horizontal, vertical)

    @contextmanager
    def box(self, modifier: RecordingModifier = None,
            horizontal: int = Rc.Layout.START,
            vertical: int = Rc.Layout.TOP):
        if modifier is None:
            modifier = RecordingModifier()
        self._writer.start_box(modifier, horizontal, vertical)
        try:
            yield self
        finally:
            self._writer.end_box()

    @contextmanager
    def row(self, modifier: RecordingModifier = None,
            horizontal: int = Rc.Layout.START,
            vertical: int = Rc.Layout.TOP):
        if modifier is None:
            modifier = RecordingModifier()
        self._writer.start_row(modifier, horizontal, vertical)
        try:
            yield self
        finally:
            self._writer.end_row()

    @contextmanager
    def column(self, modifier: RecordingModifier = None,
               horizontal: int = Rc.Layout.START,
               vertical: int = Rc.Layout.TOP):
        if modifier is None:
            modifier = RecordingModifier()
        self._writer.start_column(modifier, horizontal, vertical)
        try:
            yield self
        finally:
            self._writer.end_column()

    @contextmanager
    def flow(self, modifier: RecordingModifier = None,
             horizontal: int = Rc.Layout.START,
             vertical: int = Rc.Layout.TOP):
        if modifier is None:
            modifier = RecordingModifier()
        self._writer.start_flow(modifier, horizontal, vertical)
        try:
            yield self
        finally:
            self._writer.end_flow()

    @contextmanager
    def canvas(self, modifier: RecordingModifier = None):
        if modifier is None:
            modifier = RecordingModifier()
        self._writer.start_canvas(modifier)
        try:
            yield self
        finally:
            self._writer.end_canvas()

    @contextmanager
    def canvas_ops(self):
        self._writer.start_canvas_operations()
        try:
            yield self
        finally:
            self._writer.end_canvas_operations()

    @contextmanager
    def fit_box(self, modifier: RecordingModifier = None,
                horizontal: int = Rc.Layout.START,
                vertical: int = Rc.Layout.TOP):
        if modifier is None:
            modifier = RecordingModifier()
        self._writer.start_fit_box(modifier, horizontal, vertical)
        try:
            yield self
        finally:
            self._writer.end_fit_box()

    @contextmanager
    def collapsible_row(self, modifier: RecordingModifier = None,
                        horizontal: int = Rc.Layout.START,
                        vertical: int = Rc.Layout.TOP):
        if modifier is None:
            modifier = RecordingModifier()
        self._writer.start_collapsible_row(modifier, horizontal, vertical)
        try:
            yield self
        finally:
            self._writer.end_collapsible_row()

    @contextmanager
    def collapsible_column(self, modifier: RecordingModifier = None,
                           horizontal: int = Rc.Layout.START,
                           vertical: int = Rc.Layout.TOP):
        if modifier is None:
            modifier = RecordingModifier()
        self._writer.start_collapsible_column(modifier, horizontal, vertical)
        try:
            yield self
        finally:
            self._writer.end_collapsible_column()

    @contextmanager
    def state_layout(self, modifier: RecordingModifier = None,
                     index_id: int = 0):
        if modifier is None:
            modifier = RecordingModifier()
        self._writer.start_state_layout(modifier, index_id)
        try:
            yield self
        finally:
            self._writer.end_state_layout()

    # ── Image ──

    def image(self, modifier: RecordingModifier = None,
              image_id: int = 0, scale_mode: int = 0,
              alpha: float = 1.0):
        if modifier is None:
            modifier = RecordingModifier()
        self._writer.image(modifier, image_id, scale_mode, alpha)

    # ── Text ──

    def text(self, string: str,
             modifier: RecordingModifier = None,
             color: int = 0xFF000000,
             font_size: float = DEFAULT_FONT_SIZE,
             font_style: int = 0,
             font_weight: float = DEFAULT_FONT_WEIGHT,
             font_family: str = None,
             text_align: int = 1,
             overflow: int = 1,
             max_lines: int = 0x7FFFFFFF,
             autosize: bool = False,
             min_font_size: float = -1.0,
             max_font_size: float = -1.0,
             use_core_text: bool = False):
        if modifier is None:
            modifier = RecordingModifier()
        text_id = self._writer.add_text(string)
        self._writer.text_component(
            modifier, text_id, color, font_size,
            font_style, font_weight, font_family,
            text_align, overflow, max_lines,
            autosize=autosize,
            min_font_size=min_font_size,
            max_font_size=max_font_size,
            use_core_text=use_core_text)

    def text_by_id(self, text_id: int,
                   modifier: RecordingModifier = None,
                   color: int = 0xFF000000,
                   font_size: float = DEFAULT_FONT_SIZE,
                   font_style: int = 0,
                   font_weight: float = DEFAULT_FONT_WEIGHT,
                   font_family: str = None,
                   text_align: int = 1,
                   overflow: int = 1,
                   max_lines: int = 0x7FFFFFFF,
                   use_core_text: bool = False):
        if modifier is None:
            modifier = RecordingModifier()
        self._writer.text_component(
            modifier, text_id, color, font_size,
            font_style, font_weight, font_family,
            text_align, overflow, max_lines,
            use_core_text=use_core_text)

    # ── Drawing passthrough ──

    @property
    def paint(self):
        return self._writer.rc_paint

    def add_text(self, text: str) -> int:
        return self._writer.add_text(text)

    def add_float(self, value: float) -> float:
        return self._writer.add_float_constant(value)

    def add_integer(self, value: int) -> int:
        return self._writer.add_integer(value)

    def add_color(self, color: int) -> int:
        return self._writer.add_color(color)

    def add_color_expression(self, *args) -> int:
        return self._writer.add_color_expression(*args)

    def get_color_attribute(self, base_color: int, attr_type: int) -> float:
        return self._writer.get_color_attribute(base_color, attr_type)

    def add_bitmap_data(self, width: int, height: int, data: bytes) -> int:
        return self._writer.add_bitmap_data(width, height, data)

    def create_bitmap(self, width: int, height: int) -> int:
        return self._writer.create_bitmap(width, height)

    def float_expression(self, *value, animation=None) -> float:
        return self._writer.float_expression(*value, animation=animation)

    def integer_expression(self, *value) -> int:
        return self._writer.integer_expression(*value)

    def add_float_constant(self, value: float) -> float:
        return self._writer.add_float_constant(value)

    def add_boolean(self, value: bool) -> float:
        return self._writer.add_boolean(value)

    def text_create_id(self, text: str) -> int:
        return self._writer.text_create_id(text)

    def text_subtext(self, text_id: int, start: float, length: float) -> int:
        return self._writer.text_subtext(text_id, start, length)

    def text_length(self, text_id: int) -> float:
        return self._writer.text_length(text_id)

    def text_measure(self, text_id: int, measure_type: int) -> float:
        return self._writer.text_measure(text_id, measure_type)

    def set_theme(self, theme: int):
        self._writer.set_theme(theme)

    def add_themed_color(self, *args) -> int:
        return self._writer.add_themed_color(*args)

    def set_color_name(self, color_id: int, name: str):
        self._writer.set_color_name(color_id, name)

    def add_named_color(self, name: str, value: int) -> int:
        return self._writer.add_named_color(name, value)

    def add_named_float(self, name: str, value: float) -> float:
        return self._writer.add_named_float(name, value)

    def add_named_int(self, name: str, value: int) -> int:
        return self._writer.add_named_int(name, value)

    def add_named_string(self, name: str, value: str) -> int:
        return self._writer.add_named_string(name, value)

    def draw_rect(self, left, top, right, bottom):
        self._writer.draw_rect(left, top, right, bottom)

    def draw_circle(self, cx, cy, r):
        self._writer.draw_circle(cx, cy, r)

    def draw_line(self, x1, y1, x2, y2):
        self._writer.draw_line(x1, y1, x2, y2)

    def draw_text(self, text_id, start, end, ctx_start, ctx_end, x, y, rtl=False):
        self._writer.draw_text_run(text_id, start, end, ctx_start, ctx_end, x, y, rtl)

    def matrix_save(self):
        self._writer.save()

    def matrix_restore(self):
        self._writer.restore()

    def matrix_translate(self, dx, dy):
        self._writer.translate(dx, dy)

    def translate(self, dx, dy):
        self._writer.translate(dx, dy)

    def matrix_scale(self, sx, sy, cx=float('nan'), cy=float('nan')):
        self._writer.scale(sx, sy, cx, cy)

    def matrix_rotate(self, angle, cx, cy):
        self._writer.rotate(angle, cx, cy)

    def path_data(self, data, winding=0):
        return self._writer.add_path_data(data, winding)

    def draw_path(self, path_id):
        self._writer.draw_path(path_id)

    def draw_tween_path(self, path1_id: int, path2_id: int, tween: float,
                        start: float = 0.0, stop: float = 1.0):
        self._writer.draw_tween_path(path1_id, path2_id, tween, start, stop)

    def draw_bitmap(self, image_id: int, left: float, top: float,
                    right: float, bottom: float,
                    content_description: str = None):
        self._writer.draw_bitmap(image_id, left, top, right, bottom,
                                 content_description)

    def draw_scaled_bitmap(self, image_id: int,
                           src_left: float, src_top: float,
                           src_right: float, src_bottom: float,
                           dst_left: float, dst_top: float,
                           dst_right: float, dst_bottom: float,
                           scale_type: int = 0, scale_factor: float = 1.0,
                           content_description: str = None):
        self._writer.draw_scaled_bitmap(image_id,
                                        src_left, src_top, src_right, src_bottom,
                                        dst_left, dst_top, dst_right, dst_bottom,
                                        scale_type, scale_factor,
                                        content_description)

    def draw_bitmap_text_anchored(self, text, bitmap_font_id: int,
                                  start: float, end: float,
                                  x: float, y: float,
                                  pan_x: float = 0.0, pan_y: float = 0.0,
                                  glyph_spacing: float = 0.0):
        self._writer.draw_bitmap_text_anchored(text, bitmap_font_id,
                                               start, end, x, y,
                                               pan_x, pan_y, glyph_spacing)

    def draw_component_content(self):
        self._writer.draw_component_content()

    def draw_round_rect(self, left, top, right, bottom, rx, ry):
        self._writer.draw_round_rect(left, top, right, bottom, rx, ry)

    def draw_oval(self, left, top, right, bottom):
        self._writer.draw_oval(left, top, right, bottom)

    def draw_arc(self, left, top, right, bottom, start_angle, sweep_angle):
        self._writer.draw_arc(left, top, right, bottom, start_angle, sweep_angle)

    def draw_sector(self, left, top, right, bottom, start_angle, sweep_angle):
        self._writer.draw_sector(left, top, right, bottom, start_angle, sweep_angle)

    def draw_text_anchored(self, text_or_id, x, y, anchor_x=0.0, anchor_y=0.0, flags=0):
        self._writer.draw_text_anchored(text_or_id, x, y, anchor_x, anchor_y, flags)

    def draw_text_on_path(self, text_id: int, path_id: int,
                          h_offset: float = 0.0, v_offset: float = 0.0):
        self._writer.draw_text_on_path(text_id, path_id, h_offset, v_offset)

    def draw_text_on_circle(self, text_id: int, center_x: float, center_y: float,
                            radius: float, start_angle: float,
                            warp_radius_offset: float = 0.0,
                            alignment: int = 0, placement: int = 0):
        self._writer.draw_text_on_circle(
            text_id, center_x, center_y, radius, start_angle,
            warp_radius_offset, alignment, placement)

    # ── Canvas state ──

    def canvas_save(self):
        self._writer.save()

    def canvas_restore(self):
        self._writer.restore()

    @contextmanager
    def saved(self):
        """Context manager for save/restore pairs."""
        self._writer.save()
        try:
            yield self
        finally:
            self._writer.restore()

    def rotate(self, angle, cx, cy):
        self._writer.rotate(angle, cx, cy)

    def scale(self, sx, sy, cx=float('nan'), cy=float('nan')):
        self._writer.scale(sx, sy, cx, cy)

    def skew(self, skew_x: float, skew_y: float):
        self._writer.skew(skew_x, skew_y)

    def draw_on_bitmap(self, bitmap_id: int, mode: int = 0, color: int = 0):
        self._writer.draw_on_bitmap(bitmap_id, mode, color)

    def create_shader(self, shader_string: str):
        return self._writer.create_shader(shader_string)

    def set_root_content_behavior(self, scroll: int, alignment: int,
                                  sizing: int, mode: int):
        self._writer.set_root_content_behavior(scroll, alignment, sizing, mode)

    # ── Time accessors ──

    def continuous_sec(self) -> float:
        return Rc.Time.CONTINUOUS_SEC

    def time_in_sec(self) -> float:
        return Rc.Time.TIME_IN_SEC

    def time_in_min(self) -> float:
        return Rc.Time.TIME_IN_MIN

    def time_in_hr(self) -> float:
        return Rc.Time.TIME_IN_HR

    # ── Component dimensions ──

    def component_width(self) -> float:
        return self._writer.add_component_width_value()

    def component_height(self) -> float:
        return self._writer.add_component_height_value()

    def component_x(self) -> float:
        return self._writer.add_component_x_value()

    def component_y(self) -> float:
        return self._writer.add_component_y_value()

    def component_root_x(self) -> float:
        return self._writer.add_component_root_x_value()

    def component_root_y(self) -> float:
        return self._writer.add_component_root_y_value()

    def component_content_width(self) -> float:
        return self._writer.add_component_content_width_value()

    def component_content_height(self) -> float:
        return self._writer.add_component_content_height_value()

    # ── RFloat helpers ──

    def rf(self, value) -> RFloat:
        """Create an RFloat from a value or NaN-encoded ID.

        Matches Kotlin's rf(vararg elements: Float) which always uses
        the FloatArray constructor (id stays 0.0f).
        """
        if isinstance(value, RFloat):
            return value
        return RFloat(self._writer, [float(value)])

    def to_rf(self, value) -> RFloat:
        """Convert a number to RFloat; pass-through if already RFloat."""
        if isinstance(value, RFloat):
            return value
        return RFloat(self._writer, float(value))

    def r_fun(self, f) -> RFloat:
        """Build an expression using VAR1 as the free variable (rFun equivalent)."""
        return f(RFloat(self._writer, Rc.FloatExpression.VAR1))

    def ComponentWidth(self) -> RFloat:
        return RFloat(self._writer, self._writer.add_component_width_value())

    def ComponentHeight(self) -> RFloat:
        return RFloat(self._writer, self._writer.add_component_height_value())

    def ComponentX(self) -> RFloat:
        return RFloat(self._writer, self._writer.add_component_x_value())

    def ComponentY(self) -> RFloat:
        return RFloat(self._writer, self._writer.add_component_y_value())

    def ComponentContentWidth(self) -> RFloat:
        return RFloat(self._writer, self._writer.add_component_content_width_value())

    def ComponentContentHeight(self) -> RFloat:
        return RFloat(self._writer, self._writer.add_component_content_height_value())

    def ComponentRootX(self) -> RFloat:
        return RFloat(self._writer, self._writer.add_component_root_x_value())

    def ComponentRootY(self) -> RFloat:
        return RFloat(self._writer, self._writer.add_component_root_y_value())

    def ContinuousSec(self) -> RFloat:
        return RFloat(self._writer, Rc.Time.CONTINUOUS_SEC)

    def Hour(self) -> RFloat:
        return RFloat(self._writer, Rc.Time.TIME_IN_HR)

    def Minutes(self) -> RFloat:
        return RFloat(self._writer, Rc.Time.TIME_IN_MIN)

    def Seconds(self) -> RFloat:
        return RFloat(self._writer, Rc.Time.TIME_IN_SEC)

    def UtcOffset(self) -> RFloat:
        return RFloat(self._writer, Rc.Time.OFFSET_TO_UTC)

    def DayOfWeek(self) -> RFloat:
        return RFloat(self._writer, Rc.Time.WEEK_DAY)

    def Month(self) -> RFloat:
        return RFloat(self._writer, Rc.Time.CALENDAR_MONTH)

    def DayOfMonth(self) -> RFloat:
        return RFloat(self._writer, Rc.Time.DAY_OF_MONTH)

    def rand(self) -> RFloat:
        return RFloat(self._writer, Rc.FloatExpression.RAND)

    def index(self) -> RFloat:
        return RFloat(self._writer, Rc.FloatExpression.VAR1)

    def animationTime(self) -> RFloat:
        return RFloat(self._writer, Rc.Time.ANIMATION_TIME)

    def deltaTime(self) -> RFloat:
        return RFloat(self._writer, Rc.Time.ANIMATION_DELTA_TIME)

    def windowWidth(self) -> RFloat:
        return RFloat(self._writer, Rc.System.WINDOW_WIDTH)

    def windowHeight(self) -> RFloat:
        return RFloat(self._writer, Rc.System.WINDOW_HEIGHT)

    # ── Text operations ──

    def text_merge(self, *ids: int) -> int:
        if len(ids) == 2:
            return self._writer.text_merge(ids[0], ids[1])
        result = ids[0]
        for i in range(1, len(ids)):
            result = self._writer.text_merge(result, ids[i])
        return result

    def text_transform(self, txt_id: int, transform_type: int,
                       start: float = 0.0, length: float = -1.0) -> int:
        return self._writer.text_transform(txt_id, start, length, transform_type)

    def create_text_from_float(self, value: float, before: int,
                                after: int, flags: int = 0) -> int:
        return self._writer.create_text_from_float(value, before, after, flags)

    def text_lookup(self, array_id: float, index) -> int:
        return self._writer.text_lookup(array_id, index)

    def add_string_list(self, *strings: str) -> float:
        return self._writer.add_string_list(*strings)

    # ── Attribute Accessors ──

    def bitmap_attribute(self, bitmap_id: int, attribute: int) -> float:
        return self._writer.bitmap_attribute(bitmap_id, attribute)

    def text_attribute(self, text_id: int, attribute: int) -> float:
        return self._writer.text_attribute(text_id, attribute)

    def time_attribute(self, long_id: int, attr_type: int, *args: int) -> float:
        return self._writer.time_attribute(long_id, attr_type, *args)

    # ── Lookup ──

    def map_lookup(self, map_id: int, str_or_id) -> int:
        return self._writer.map_lookup(map_id, str_or_id)

    def id_lookup(self, array_id: float, index: float) -> int:
        return self._writer.id_lookup(array_id, index)

    # ── Animation Specs ──

    def spring(self, stiffness: float, damping: float,
               stop_threshold: float, boundary_mode: int) -> list:
        return self._writer.spring(stiffness, damping, stop_threshold, boundary_mode)

    # ── Global sections ──

    def begin_global(self):
        self._writer.begin_global()

    def end_global(self):
        self._writer.end_global()

    # ── Loop ──

    def start_loop(self, count: float, from_val: float = 0.0,
                   step: float = 1.0) -> float:
        from .types.nan_utils import as_nan, id_from_nan
        fid = self._writer.create_float_id()
        index_id = id_from_nan(fid)
        self._writer.start_loop(index_id, from_val, step, count)
        return fid

    def loop(self, index_id: int, from_val: float, step: float,
             count: float):
        self._writer.start_loop(index_id, from_val, step, count)

    def end_loop(self):
        self._writer.end_loop()

    @contextmanager
    def loop_range(self, from_val, step, until):
        """Context manager loop that yields an RFloat index variable.

        Usage:
            with ctx.loop_range(0, 1, n) as x:
                # x is an RFloat loop index
        """
        from .types.nan_utils import as_nan
        from_f = from_val.to_float() if isinstance(from_val, RFloat) else float(from_val)
        step_f = step.to_float() if isinstance(step, RFloat) else float(step)
        until_f = until.to_float() if isinstance(until, RFloat) else float(until)
        fid = self._writer.create_float_id()
        from .types.nan_utils import id_from_nan
        index_id = id_from_nan(fid)
        self._writer.start_loop(index_id, from_f, step_f, until_f)
        try:
            # Use list constructor so _id stays 0.0 (not NaN).
            # Matches Kotlin: rf(vararg) → RFloat(writer, FloatArray) which
            # does NOT set id, so toFloat() emits ANIMATED_FLOAT on first use.
            yield RFloat(self._writer, [fid])
        finally:
            self._writer.end_loop()

    # ── Conditional ──

    def conditional_operations(self, cond_type: int, a: float, b: float):
        self._writer.add_conditional_operations(cond_type, a, b)

    def end_conditional_operations(self):
        self._writer.end_conditional_operations()

    # ── Painter ──

    @property
    def painter(self):
        return self._writer.rc_paint

    # ── Path ──

    def path_create(self, x: float, y: float) -> int:
        return self._writer.path_create(x, y)

    def path_append_move_to(self, path_id: int, x: float, y: float):
        self._writer.path_append_move_to(path_id, x, y)

    def path_append_line_to(self, path_id: int, x: float, y: float):
        self._writer.path_append_line_to(path_id, x, y)

    def path_append_quad_to(self, path_id: int,
                            x1: float, y1: float, x2: float, y2: float):
        self._writer.path_append_quad_to(path_id, x1, y1, x2, y2)

    def path_append_close(self, path_id: int):
        self._writer.path_append_close(path_id)

    def path_append_reset(self, path_id: int):
        self._writer.path_append_reset(path_id)

    def add_clip_path(self, path_id: int):
        self._writer.add_clip_path(path_id)

    def clip_rect(self, left: float, top: float, right: float, bottom: float):
        self._writer.clip_rect(left, top, right, bottom)

    def path_combine(self, path1: int, path2: int, op: int) -> int:
        return self._writer.path_combine(path1, path2, op)

    def path_tween(self, pid1: int, pid2: int, tween: float) -> int:
        return self._writer.path_tween(pid1, pid2, tween)

    def add_path_expression(self, exp_x: list, exp_y: list,
                            start: float, end: float, count: float,
                            flags: int) -> int:
        return self._writer.add_path_expression(exp_x, exp_y, start, end, count, flags)

    def add_polar_path_expression(self, expression_r: list,
                                  start: float, end: float, count: float,
                                  center_x: float, center_y: float,
                                  flags: int) -> int:
        return self._writer.add_polar_path_expression(
            expression_r, start, end, count, center_x, center_y, flags)

    def add_path_data(self, data: list, winding: int = 0) -> int:
        return self._writer.add_path_data(data, winding)

    def add_path_string(self, path_str: str) -> int:
        return self._writer.add_path_string(path_str)

    # ── Actions ──

    def start_run_actions(self):
        self._writer.start_run_actions()

    def end_run_actions(self):
        self._writer.end_run_actions()

    def add_action(self, *actions):
        self._writer.add_action(*actions)

    def wake_in(self, seconds: float):
        self._writer.wake_in(seconds)

    # ── ID creation ──

    def create_float_id(self) -> float:
        return self._writer.create_float_id()

    def create_id(self, value=0) -> int:
        return self._writer.create_id(value)

    # ── Float array ──

    def add_float_array(self, data: list) -> float:
        return self._writer.add_float_array(data)

    def add_float_list(self, values: list) -> float:
        return self._writer.add_float_list(values)

    # ── Touch ──

    def add_touch(self, def_value, min_val, max_val, mode, *args):
        return self._writer.add_touch(def_value, min_val, max_val, mode, *args)

    # ── Convenience helpers ──

    def ping_pong(self, max_val: float, x: float) -> float:
        return self.float_expression(x, float(max_val), Rc.FloatExpression.PINGPONG)

    def get_time_string(self) -> int:
        if self._cached_time_string != -1:
            return self._cached_time_string
        self.begin_global()
        gap = self.add_text(":")
        sec_expr = self.float_expression(
            Rc.Time.TIME_IN_SEC, 60.0, Rc.FloatExpression.MOD)
        tid1 = self.create_text_from_float(
            sec_expr, 2, 0, Rc.TextFromFloat.PAD_PRE_ZERO)
        min_expr = self.float_expression(
            Rc.Time.TIME_IN_MIN, 60.0, Rc.FloatExpression.MOD)
        tid2 = self.create_text_from_float(
            min_expr, 2, 0, Rc.TextFromFloat.PAD_PRE_ZERO)
        hr_expr = self.float_expression(
            Rc.Time.TIME_IN_HR, 12.0, Rc.FloatExpression.MOD)
        tid3 = self.create_text_from_float(hr_expr, 2, 0, 0)
        clock = self.text_merge(tid3, gap, tid2, gap, tid1)
        self.end_global()
        self._cached_time_string = clock
        return clock

    def easing(self, duration: float, *spec: float) -> list:
        return [duration] + list(spec)

    def add_debug_message(self, message, value: float = 0.0, flag: int = 0):
        self._writer.add_debug_message(message, value, flag)

    def perform_haptic(self, feedback_constant: int):
        self._writer.perform_haptic(feedback_constant)

    # ── Click area ──

    def add_click_area(self, area_id: int, content_description: str,
                       left: float, top: float, right: float, bottom: float,
                       metadata: str = None):
        self._writer.add_click_area(area_id, content_description,
                                    left, top, right, bottom, metadata)

    # ── Text run / bitmap font ──

    def draw_text_run(self, text_id, start: int, end: int,
                      context_start: int, context_end: int,
                      x: float, y: float, rtl: bool = False):
        self._writer.draw_text_run(text_id, start, end,
                                   context_start, context_end, x, y, rtl)

    def draw_bitmap_font_text_run(self, text_id: int, bitmap_font_id: int,
                                  start: int, end: int, x: float, y: float,
                                  glyph_spacing: float = 0.0):
        self._writer.draw_bitmap_font_text_run(text_id, bitmap_font_id,
                                               start, end, x, y, glyph_spacing)

    # ── Matrix ──

    def matrix_from_path(self, path_id: int, fraction: float,
                         v_offset: float, flags: int):
        self._writer.matrix_from_path(path_id, fraction, v_offset, flags)

    def matrix_expression(self, *exp: float) -> float:
        return self._writer.matrix_expression(*exp)

    # ── Impulse system ──

    def impulse(self, duration: float, start: float, content=None):
        self._writer.impulse(duration, start, content)

    def impulse_process(self, content=None):
        self._writer.impulse_process(content)

    def impulse_end(self):
        self._writer.impulse_end()

    # ── Particle system ──

    def create_particles(self, variables: list, initial_expressions: list,
                         particle_count: int) -> float:
        return self._writer.create_particles(variables, initial_expressions,
                                             particle_count)

    def particles_loop(self, particle_id: float, restart: list,
                       expressions: list, content=None):
        self._writer.particles_loop(particle_id, restart, expressions, content)

    # ── Float functions ──

    def create_float_function(self, args: list) -> int:
        return self._writer.create_float_function(args)

    def end_float_function(self):
        self._writer.end_float_function()

    def call_float_function(self, func_id: int, *args: float):
        self._writer.call_float_function(func_id, *args)

    # ── Text style ──

    def add_text_style(self, **kwargs) -> int:
        return self._writer.add_text_style(**kwargs)

    # ── Scroll modifier ──

    def add_modifier_scroll(self, direction: int, position_id: float = None,
                            notches: int = None):
        if position_id is None:
            position_id = self._writer.create_float_id()
        self._writer.add_modifier_scroll(direction, position_id, notches)

    # ── Float map ──

    def add_float_map(self, keys: list, values: list) -> float:
        return self._writer.add_float_map(keys, values)

    # ── Time long ──

    def add_time_long(self, time: int) -> int:
        return self._writer.add_time_long(time)

    # ── Long / naming ──

    def add_long(self, value: int) -> int:
        return self._writer.add_long(value)

    def add_named_long(self, name: str, initial_value: int) -> int:
        return self._writer.add_named_long(name, initial_value)

    def set_float_name(self, cid: int, name: str):
        self._writer.set_float_name(cid, name)

    def set_string_name(self, cid: int, name: str):
        self._writer.set_string_name(cid, name)

    # ── Matrix multiply ──

    def matrix_multiply(self, matrix_id: float, *args):
        """Matrix multiply supporting both regular and projection modes.

        Regular:    matrix_multiply(matrix_id, from_vec, out)
        Projection: matrix_multiply(matrix_id, op_type, from_vec, out)
        """
        if len(args) == 2:
            from_vec, out = args
            self._writer.matrix_multiply(matrix_id, from_vec, out)
        elif len(args) == 3:
            op_type, from_vec, out = args
            self._writer.add_matrix_multiply(matrix_id, op_type, from_vec, out)
        else:
            raise ValueError("matrix_multiply expects 3 or 4 arguments")

    # ── Bitmap operations ──

    def name_bitmap_id(self, bitmap_id: int, name: str):
        self._writer.name_bitmap_id(bitmap_id, name)

    def bitmap_text_measure(self, text_id: int, bm_font_id: int,
                            measure_width: int, glyph_spacing: float) -> float:
        return self._writer.bitmap_text_measure(text_id, bm_font_id,
                                                measure_width, glyph_spacing)

    def add_font(self, data: bytes) -> int:
        return self._writer.add_font(data)

    # ── ID utilities ──

    def next_id(self) -> int:
        return self._writer.next_id()

    def as_float_id(self, long_id: int) -> float:
        return self._writer.as_float_id(long_id)

    def reserve_float_variable(self) -> float:
        return self._writer.reserve_float_variable()

    # ── Data map ──

    def add_data_map(self, *entries) -> int:
        return self._writer.add_data_map(*entries)

    # ── Touch expression ──

    def touch_expression(self, *exp: float,
                         def_value: float = 0.0, min_val: float = 0.0,
                         max_val: float = 10.0, touch_mode: int = 3,
                         velocity_id: float = 0.0, touch_effects: int = 0,
                         touch_spec: list = None, easing_spec: list = None) -> float:
        return self._writer.add_touch(def_value, min_val, max_val, touch_mode,
                                      velocity_id, touch_effects, touch_spec,
                                      easing_spec, *exp)

    # ── Conditional helpers ──

    def if_else(self, positive, true_ops, else_ops=None):
        from .rc import Rc
        val = positive.to_float() if isinstance(positive, RFloat) else float(positive)
        self.conditional_operations(Rc.Condition.GT, val, 0.0)
        true_ops()
        self.end_conditional_operations()
        if else_ops is not None:
            self.conditional_operations(Rc.Condition.LTE, val, 0.0)
            else_ops()
            self.end_conditional_operations()

    # ── Expression builder ──

    @staticmethod
    def exp(*value: float) -> list:
        return list(value)

    # ── Animation helper ──

    @staticmethod
    def anim(duration: float, easing_type: int = 0, spec: list = None,
             initial_value: float = float('nan'),
             wrap: float = float('nan')) -> list:
        from .writer import RemoteComposeWriter
        return RemoteComposeWriter.anim(duration, easing_type, spec,
                                        initial_value, wrap)

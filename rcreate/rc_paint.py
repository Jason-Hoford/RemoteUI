"""RcPaint — high-level paint builder wrapping PaintBundle.

Provides a fluent API (setColor, setStrokeWidth, etc.) that
accumulates paint changes in a PaintBundle and flushes them
to the buffer on commit().

Matches Java's RcPaint.java.
"""

from __future__ import annotations
from .paint_bundle import PaintBundle, FONT_TYPE_DEFAULT, FONT_TYPE_SANS_SERIF, \
    FONT_TYPE_SERIF, FONT_TYPE_MONOSPACE


class RcPaint:
    FONT_TYPE_DEFAULT = FONT_TYPE_DEFAULT
    FONT_TYPE_SANS_SERIF = FONT_TYPE_SANS_SERIF
    FONT_TYPE_SERIF = FONT_TYPE_SERIF
    FONT_TYPE_MONOSPACE = FONT_TYPE_MONOSPACE
    _NORMAL_WEIGHT = 400

    def __init__(self, writer):
        self._paint = PaintBundle()
        self._writer = writer

    def commit(self):
        self._writer._buffer.add_paint(self._paint)
        self._paint.reset()

    def set_anti_alias(self, aa: bool) -> 'RcPaint':
        self._paint.set_anti_alias(aa)
        return self

    def set_color(self, color: int) -> 'RcPaint':
        self._paint.set_color(color)
        return self

    def set_color_id(self, color_id: int) -> 'RcPaint':
        self._paint.set_color_id(color_id)
        return self

    def set_stroke_join(self, join: int) -> 'RcPaint':
        self._paint.set_stroke_join(join)
        return self

    def set_stroke_width(self, width: float) -> 'RcPaint':
        self._paint.set_stroke_width(width)
        return self

    def set_style(self, style: int) -> 'RcPaint':
        self._paint.set_style(style)
        return self

    def set_stroke_cap(self, cap: int) -> 'RcPaint':
        self._paint.set_stroke_cap(cap)
        return self

    def set_stroke_miter(self, miter: float) -> 'RcPaint':
        self._paint.set_stroke_miter(miter)
        return self

    def set_alpha(self, alpha: float) -> 'RcPaint':
        self._paint.set_alpha(alpha / 255.0 if alpha > 2 else alpha)
        return self

    def set_porter_duff_color_filter(self, color: int, mode: int) -> 'RcPaint':
        self._paint.set_color_filter(color, mode)
        return self

    def clear_color_filter(self) -> 'RcPaint':
        self._paint.clear_color_filter()
        return self

    def set_linear_gradient(self, start_x: float, start_y: float, end_x: float, end_y: float,
                            colors: list, positions: list = None, tile_mode: int = 0,
                            mask: int = 0) -> 'RcPaint':
        self._paint.set_linear_gradient(colors, mask, positions,
                                        start_x, start_y, end_x, end_y, tile_mode)
        return self

    def set_radial_gradient(self, center_x: float, center_y: float, radius: float,
                            colors: list, positions: list = None, tile_mode: int = 0,
                            mask: int = 0) -> 'RcPaint':
        self._paint.set_radial_gradient(colors, mask, positions,
                                        center_x, center_y, radius, tile_mode)
        return self

    def set_sweep_gradient(self, center_x: float, center_y: float,
                           colors: list, positions: list = None,
                           mask: int = 0) -> 'RcPaint':
        self._paint.set_sweep_gradient(colors, mask, positions, center_x, center_y)
        return self

    def set_shader_matrix(self, matrix_id: float) -> 'RcPaint':
        self._paint.set_shader_matrix(matrix_id)
        return self

    def set_text_size(self, size: float) -> 'RcPaint':
        self._paint.set_text_size(size)
        return self

    def set_typeface(self, font_type_or_name, weight: int = _NORMAL_WEIGHT,
                     italic: bool = False) -> 'RcPaint':
        if isinstance(font_type_or_name, str):
            font_id = self._writer.add_text(font_type_or_name)
            self._paint.set_text_style(font_id, weight, italic)
        else:
            self._paint.set_text_style(font_type_or_name, weight, italic)
        return self

    def set_typeface_id(self, font_data_id: int) -> 'RcPaint':
        self._paint.set_text_style(font_data_id, self._NORMAL_WEIGHT, False, ttf=True)
        return self

    def set_filter_bitmap(self, filter_bitmap: bool) -> 'RcPaint':
        self._paint.set_filter_bitmap(filter_bitmap)
        return self

    def set_blend_mode(self, blend_mode: int) -> 'RcPaint':
        self._paint.set_blend_mode(blend_mode)
        return self

    def set_shader(self, shader_id: int) -> 'RcPaint':
        self._paint.set_shader(shader_id)
        return self

    def set_axis(self, tags, values: list) -> 'RcPaint':
        if isinstance(tags[0], str):
            tag_ids = [self._writer.add_text(t) for t in tags]
        else:
            tag_ids = list(tags)
        self._paint.set_text_axis(tag_ids, values)
        return self

    def set_texture_shader(self, texture: int, tile_mode_x: int, tile_mode_y: int,
                           filter_mode: int, max_anisotropy: int) -> 'RcPaint':
        self._paint.set_texture_shader(texture, tile_mode_x, tile_mode_y,
                                       filter_mode, max_anisotropy)
        return self

    def set_path_effect(self, path_effect_data: list) -> 'RcPaint':
        self._paint.set_path_effect(path_effect_data)
        return self

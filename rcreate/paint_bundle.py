"""PaintBundle — delta encoding of paint changes.

Encodes paint properties as an int array. Each entry is a tag (lower 16 bits)
optionally with a value packed in the upper 16 bits. Some tags are followed
by one or more int values (reinterpreted as float bits where needed).

Matches Java's PaintBundle.java.
"""

import struct


# Tag constants
TEXT_SIZE = 1
COLOR = 4
STROKE_WIDTH = 5
STROKE_MITER = 6
STROKE_CAP = 7
STYLE = 8
SHADER = 9
IMAGE_FILTER_QUALITY = 10
GRADIENT = 11
ALPHA = 12
COLOR_FILTER = 13
ANTI_ALIAS = 14
STROKE_JOIN = 15
TYPEFACE = 16
FILTER_BITMAP = 17
BLEND_MODE = 18
COLOR_ID = 19
COLOR_FILTER_ID = 20
CLEAR_COLOR_FILTER = 21
SHADER_MATRIX = 22
FONT_AXIS = 23
TEXTURE = 24
PATH_EFFECT = 25
FALLBACK_TYPEFACE = 26

# Blend modes
BLEND_MODE_CLEAR = 0
BLEND_MODE_SRC = 1
BLEND_MODE_DST = 2
BLEND_MODE_SRC_OVER = 3
BLEND_MODE_DST_OVER = 4
BLEND_MODE_SRC_IN = 5
BLEND_MODE_DST_IN = 6
BLEND_MODE_SRC_OUT = 7
BLEND_MODE_DST_OUT = 8
BLEND_MODE_SRC_ATOP = 9
BLEND_MODE_DST_ATOP = 10
BLEND_MODE_XOR = 11
BLEND_MODE_PLUS = 12
BLEND_MODE_MODULATE = 13
BLEND_MODE_SCREEN = 14
BLEND_MODE_OVERLAY = 15
BLEND_MODE_DARKEN = 16
BLEND_MODE_LIGHTEN = 17
BLEND_MODE_COLOR_DODGE = 18
BLEND_MODE_COLOR_BURN = 19
BLEND_MODE_HARD_LIGHT = 20
BLEND_MODE_SOFT_LIGHT = 21
BLEND_MODE_DIFFERENCE = 22
BLEND_MODE_EXCLUSION = 23
BLEND_MODE_MULTIPLY = 24
BLEND_MODE_HUE = 25
BLEND_MODE_SATURATION = 26
BLEND_MODE_COLOR = 27
BLEND_MODE_LUMINOSITY = 28
BLEND_MODE_NULL = 29
PORTER_MODE_ADD = 30

# Font style
FONT_NORMAL = 0
FONT_BOLD = 1
FONT_ITALIC = 2
FONT_BOLD_ITALIC = 3

# Font type
FONT_TYPE_DEFAULT = 0
FONT_TYPE_SANS_SERIF = 1
FONT_TYPE_SERIF = 2
FONT_TYPE_MONOSPACE = 3

# Paint style
STYLE_FILL = 0
STYLE_STROKE = 1
STYLE_FILL_AND_STROKE = 2

# Gradient type
LINEAR_GRADIENT = 0
RADIAL_GRADIENT = 1
SWEEP_GRADIENT = 2


def _float_to_int_bits(f: float) -> int:
    """Reinterpret float bits as unsigned int32.

    Python on x86 converts signaling NaN → quiet NaN by setting bit 22.
    RemoteCompose encodes IDs as sNaN with base 0xFF800000 (sign bit set).
    We reverse the quiet-bit insertion for negative NaN to match Java.
    """
    bits = struct.unpack('<I', struct.pack('<f', f))[0]
    if f != f and (bits & 0x80000000):  # negative NaN = RemoteCompose ID
        bits &= ~0x00400000
    return bits


def _int_bits_to_float(i: int) -> float:
    """Reinterpret int32 bits as float."""
    return struct.unpack('<f', struct.pack('<I', i & 0xFFFFFFFF))[0]


class PaintBundle:
    """Accumulates paint property changes as an int array."""

    def __init__(self):
        self._array: list[int] = []
        self._last_shader_set: int = -1
        self._color_filter_id_set: bool = False

    def reset(self):
        """Reset the paint bundle for reuse.

        Matches Java PaintBundle.reset(): if a color filter ID was set,
        auto-clears it; if a non-zero shader was set, auto-resets to 0.
        These entries are prepended to the *next* bundle.
        """
        self._array.clear()
        if self._color_filter_id_set:
            self.clear_color_filter()
        if self._last_shader_set != -1 and self._last_shader_set != 0:
            self.set_shader(0)

    def write(self, buffer):
        """Write the bundle to a WireBuffer."""
        buffer.write_int(len(self._array))
        for v in self._array:
            buffer.write_int(v)

    # ── Property setters ──────────────────────────────────────────

    def set_text_size(self, size: float):
        self._array.append(TEXT_SIZE)
        self._array.append(_float_to_int_bits(size))

    def set_color(self, color: int):
        self._array.append(COLOR)
        self._array.append(color & 0xFFFFFFFF)

    def set_color_id(self, color_id: int):
        self._array.append(COLOR_ID)
        self._array.append(color_id)

    def set_stroke_width(self, width: float):
        self._array.append(STROKE_WIDTH)
        self._array.append(_float_to_int_bits(width))

    def set_stroke_miter(self, miter: float):
        self._array.append(STROKE_MITER)
        self._array.append(_float_to_int_bits(miter))

    def set_stroke_cap(self, cap: int):
        self._array.append(STROKE_CAP | (cap << 16))

    def set_style(self, style: int):
        self._array.append(STYLE | (style << 16))

    def set_stroke_join(self, join: int):
        self._array.append(STROKE_JOIN | (join << 16))

    def set_anti_alias(self, aa: bool):
        self._array.append(ANTI_ALIAS | ((1 if aa else 0) << 16))

    def set_filter_bitmap(self, filter_bitmap: bool):
        self._array.append(FILTER_BITMAP | ((1 if filter_bitmap else 0) << 16))

    def set_blend_mode(self, blend_mode: int):
        self._array.append(BLEND_MODE | (blend_mode << 16))

    def set_alpha(self, alpha: float):
        self._array.append(ALPHA)
        self._array.append(_float_to_int_bits(alpha))

    def set_shader(self, shader_id: int):
        self._last_shader_set = shader_id
        self._array.append(SHADER)
        self._array.append(shader_id)

    def set_shader_matrix(self, matrix_id: float):
        self._array.append(SHADER_MATRIX)
        self._array.append(_float_to_int_bits(matrix_id))

    def set_color_filter(self, color: int, mode: int):
        self._array.append(COLOR_FILTER | (mode << 16))
        self._array.append(color)
        self._color_filter_id_set = True

    def clear_color_filter(self):
        self._array.append(CLEAR_COLOR_FILTER)
        self._color_filter_id_set = False

    def set_text_style(self, font_type: int, weight: int, italic: bool, ttf: bool = False):
        style = (weight & 0x3FF) | (2048 if italic else 0) | (1024 if ttf else 0)
        self._array.append(TYPEFACE | (style << 16))
        self._array.append(font_type)

    def set_text_axis(self, tag_ids: list, values: list):
        count = min(len(tag_ids), 8)
        self._array.append(FONT_AXIS | (count << 16))
        for i in range(count):
            self._array.append(tag_ids[i])
            self._array.append(_float_to_int_bits(values[i]))

    def set_linear_gradient(self, colors: list, id_mask: int, positions: list,
                            start_x: float, start_y: float, end_x: float, end_y: float,
                            tile_mode: int):
        num_colors = len(colors)
        header = GRADIENT | (LINEAR_GRADIENT << 16)
        self._array.append(header)
        self._array.append((id_mask << 16) | num_colors)
        for c in colors:
            self._array.append(c & 0xFFFFFFFF)
        if positions is not None:
            self._array.append(len(positions))
            for p in positions:
                self._array.append(_float_to_int_bits(p))
        else:
            self._array.append(0)
        self._array.append(_float_to_int_bits(start_x))
        self._array.append(_float_to_int_bits(start_y))
        self._array.append(_float_to_int_bits(end_x))
        self._array.append(_float_to_int_bits(end_y))
        self._array.append(tile_mode)

    def set_radial_gradient(self, colors: list, id_mask: int, positions: list,
                            center_x: float, center_y: float, radius: float, tile_mode: int):
        num_colors = len(colors)
        header = GRADIENT | (RADIAL_GRADIENT << 16)
        self._array.append(header)
        self._array.append((id_mask << 16) | num_colors)
        for c in colors:
            self._array.append(c & 0xFFFFFFFF)
        if positions is not None:
            self._array.append(len(positions))
            for p in positions:
                self._array.append(_float_to_int_bits(p))
        else:
            self._array.append(0)
        self._array.append(_float_to_int_bits(center_x))
        self._array.append(_float_to_int_bits(center_y))
        self._array.append(_float_to_int_bits(radius))
        self._array.append(tile_mode)

    def set_sweep_gradient(self, colors: list, id_mask: int, positions: list,
                           center_x: float, center_y: float):
        num_colors = len(colors)
        header = GRADIENT | (SWEEP_GRADIENT << 16)
        self._array.append(header)
        self._array.append((id_mask << 16) | num_colors)
        for c in colors:
            self._array.append(c & 0xFFFFFFFF)
        if positions is not None:
            self._array.append(len(positions))
            for p in positions:
                self._array.append(_float_to_int_bits(p))
        else:
            self._array.append(0)
        self._array.append(_float_to_int_bits(center_x))
        self._array.append(_float_to_int_bits(center_y))

    def set_texture_shader(self, texture_id: int, tile_mode_x: int, tile_mode_y: int,
                           filter_mode: int, max_anisotropy: int):
        self._array.append(TEXTURE)
        self._array.append(texture_id)
        packed = (tile_mode_x & 0xFFFF) | ((tile_mode_y & 0xFFFF) << 16)
        self._array.append(packed)
        packed2 = (filter_mode & 0xFFFF) | ((max_anisotropy & 0xFFFF) << 16)
        self._array.append(packed2)

    def set_path_effect(self, data: list):
        if data is None:
            # null clears the path effect (Java writes PATH_EFFECT with length 0)
            self._array.append(PATH_EFFECT)
            return
        self._array.append(PATH_EFFECT | (len(data) << 16))
        for f in data:
            self._array.append(_float_to_int_bits(f))

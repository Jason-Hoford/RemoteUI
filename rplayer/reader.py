"""Binary .rc file reader — parses RemoteCompose documents into an operation list.

The binary format is a flat sequence of operations:
    opcode(1 byte) + payload(variable, determined by opcode)

There is no per-operation size prefix. The reader must know each opcode's
field layout in order to advance correctly through the stream. Unknown
opcodes cause a parse error because the reader cannot skip them.

Field orders in the reader MUST exactly match the writer
(rcreate/remote_UI_buffer.py). All multi-byte integers are big-endian,
matching Java's DataOutputStream format. Strings are encoded as
int(length) + UTF-8 bytes. Float arrays are int(count) + float[count].

This reader produces a flat list of operation dicts. Layout nesting is
implicit via container-start / CONTAINER_END pairs. The dict key 'op'
identifies the operation type; other keys vary by operation.
"""

import struct
import math

# Opcode constants (subset needed for reader — mirrors rcreate/operations.py)
HEADER = 0
COMPONENT_START = 2
LOAD_BITMAP = 4
ANIMATION_SPEC = 14
MODIFIER_WIDTH = 16
CLIP_PATH = 38
CLIP_RECT = 39
PAINT_VALUES = 40
DRAW_RECT = 42
DRAW_TEXT_RUN = 43
DRAW_BITMAP = 44
DATA_SHADER = 45
DRAW_CIRCLE = 46
DRAW_LINE = 47
DRAW_BITMAP_FONT_TEXT_RUN = 48
DRAW_BITMAP_FONT_TEXT_RUN_ON_PATH = 49
DRAW_ROUND_RECT = 51
DRAW_SECTOR = 52
DRAW_TEXT_ON_PATH = 53
MODIFIER_ROUNDED_CLIP_RECT = 54
MODIFIER_BACKGROUND = 55
DRAW_OVAL = 56
DRAW_TEXT_ON_CIRCLE = 57
MODIFIER_PADDING = 58
MODIFIER_CLICK = 59
THEME = 63
CLICK_AREA = 64
ROOT_CONTENT_BEHAVIOR = 65
DRAW_BITMAP_INT = 66
MODIFIER_HEIGHT = 67
DATA_FLOAT = 80
ANIMATED_FLOAT = 81
DATA_BITMAP = 101
DATA_TEXT = 102
ROOT_CONTENT_DESCRIPTION = 103
MODIFIER_BORDER = 107
MODIFIER_CLIP_RECT = 108
DATA_PATH = 123
DRAW_PATH = 124
DRAW_TWEEN_PATH = 125
MATRIX_SCALE = 126
MATRIX_TRANSLATE = 127
MATRIX_SKEW = 128
MATRIX_ROTATE = 129
MATRIX_SAVE = 130
MATRIX_RESTORE = 131
MATRIX_SET = 132
DRAW_TEXT_ANCHOR = 133
COLOR_EXPRESSIONS = 134
TEXT_FROM_FLOAT = 135
TEXT_MERGE = 136
NAMED_VARIABLE = 137
COLOR_CONSTANT = 138
DRAW_CONTENT = 139
DATA_INT = 140
DATA_BOOLEAN = 143
INTEGER_EXPRESSION = 144
ID_MAP = 145
ID_LIST = 146
FLOAT_LIST = 147
DATA_LONG = 148
DRAW_BITMAP_SCALED = 149
COMPONENT_VALUE = 150
TEXT_LOOKUP = 151
DRAW_ARC = 152
TEXT_LOOKUP_INT = 153
DATA_MAP_LOOKUP = 154
TEXT_MEASURE = 155
TEXT_LENGTH = 156
TOUCH_EXPRESSION = 157
PATH_TWEEN = 158
PATH_CREATE = 159
PATH_ADD = 160
PARTICLE_DEFINE = 161
PARTICLE_PROCESS = 162
PARTICLE_LOOP = 163
IMPULSE_START = 164
IMPULSE_PROCESS = 165
FUNCTION_CALL = 166
DATA_BITMAP_FONT = 167
FUNCTION_DEFINE = 168
ATTRIBUTE_TEXT = 170
ATTRIBUTE_IMAGE = 171
ATTRIBUTE_TIME = 172
CANVAS_OPERATIONS = 173
MODIFIER_DRAW_CONTENT = 174
PATH_COMBINE = 175
LAYOUT_FIT_BOX = 176
HAPTIC_FEEDBACK = 177
CONDITIONAL_OPERATIONS = 178
DEBUG_MESSAGE = 179
ATTRIBUTE_COLOR = 180
MATRIX_FROM_PATH = 181
TEXT_SUBTEXT = 182
BITMAP_TEXT_MEASURE = 183
DRAW_BITMAP_TEXT_ANCHORED = 184
REM = 185
MATRIX_CONSTANT = 186
MATRIX_EXPRESSION = 187
MATRIX_VECTOR_MATH = 188
DATA_FONT = 189
DRAW_TO_BITMAP = 190
WAKE_IN = 191
ID_LOOKUP = 192
PATH_EXPRESSION = 193
PARTICLE_COMPARE = 194
UPDATE = 195
COLOR_THEME = 196
DYNAMIC_FLOAT_LIST = 197
UPDATE_DYNAMIC_FLOAT_LIST = 198
TEXT_TRANSFORM = 199
LAYOUT_ROOT = 200
LAYOUT_CONTENT = 201
LAYOUT_BOX = 202
LAYOUT_ROW = 203
LAYOUT_COLUMN = 204
LAYOUT_CANVAS = 205
LAYOUT_CANVAS_CONTENT = 207
LAYOUT_TEXT = 208
HOST_ACTION = 209
HOST_NAMED_ACTION = 210
MODIFIER_VISIBILITY = 211
VALUE_INTEGER_CHANGE_ACTION = 212
VALUE_STRING_CHANGE_ACTION = 213
CONTAINER_END = 214
LOOP_START = 215
HOST_METADATA_ACTION = 216
LAYOUT_STATE = 217
VALUE_INTEGER_EXPRESSION_CHANGE_ACTION = 218
MODIFIER_TOUCH_DOWN = 219
MODIFIER_TOUCH_UP = 220
MODIFIER_OFFSET = 221
VALUE_FLOAT_CHANGE_ACTION = 222
MODIFIER_ZINDEX = 223
MODIFIER_GRAPHICS_LAYER = 224
MODIFIER_TOUCH_CANCEL = 225
MODIFIER_SCROLL = 226
VALUE_FLOAT_EXPRESSION_CHANGE_ACTION = 227
MODIFIER_MARQUEE = 228
MODIFIER_RIPPLE = 229
LAYOUT_COLLAPSIBLE_ROW = 230
MODIFIER_WIDTH_IN = 231
MODIFIER_HEIGHT_IN = 232
LAYOUT_COLLAPSIBLE_COLUMN = 233
LAYOUT_IMAGE = 234
MODIFIER_COLLAPSIBLE_PRIORITY = 235
RUN_ACTION = 236
MODIFIER_ALIGN_BY = 237
LAYOUT_COMPUTE = 238
CORE_TEXT = 239
LAYOUT_FLOW = 240
SKIP = 241
TEXT_STYLE = 242
ACCESSIBILITY_SEMANTICS = 250

MAGIC_NUMBER = 0x048C0000

# CORE_TEXT tag type map (tag -> type: 'i'=int, 'f'=float, 'b'=bool)
_CORE_TEXT_TAG_TYPES = {
    1: 'i', 2: 'i', 3: 'i', 4: 'i', 5: 'f', 6: 'i', 7: 'f', 8: 'i',
    9: 'i', 10: 'i', 11: 'i', 12: 'f', 13: 'f', 14: 'f', 15: 'i',
    16: 'i', 17: 'i', 18: 'b', 19: 'b', 22: 'b', 23: 'i', 24: 'i',
    25: 'f', 26: 'f',
}


class RcDocument:
    """Parsed RemoteCompose document."""
    __slots__ = ('width', 'height', 'description', 'operations',
                 'texts', 'floats', 'paths')

    def __init__(self):
        self.width = 0
        self.height = 0
        self.description = ''
        self.operations = []   # flat list of operation dicts
        self.texts = {}        # id -> string
        self.floats = {}       # id -> float value
        self.paths = {}        # id -> float list (path data)


class RcReader:
    """Reads a RemoteCompose .rc binary file into an RcDocument.

    Usage:
        doc = RcReader(open('demo.rc', 'rb').read()).parse()
    """

    def __init__(self, data: bytes):
        self._data = data
        self._pos = 0
        self._len = len(data)

    # -- Primitive reads (big-endian, matching Java's WireBuffer) --

    def _read_byte(self) -> int:
        v = self._data[self._pos]
        self._pos += 1
        return v

    def _read_short(self) -> int:
        v = struct.unpack_from('>h', self._data, self._pos)[0]
        self._pos += 2
        return v

    def _read_int(self) -> int:
        v = struct.unpack_from('>i', self._data, self._pos)[0]
        self._pos += 4
        return v

    def _read_unsigned_int(self) -> int:
        v = struct.unpack_from('>I', self._data, self._pos)[0]
        self._pos += 4
        return v

    def _read_float(self) -> float:
        v = struct.unpack_from('>f', self._data, self._pos)[0]
        self._pos += 4
        return v

    def _read_float_bits(self) -> int:
        """Read 4 bytes and return the raw unsigned int bits."""
        v = struct.unpack_from('>I', self._data, self._pos)[0]
        self._pos += 4
        return v

    def _read_long(self) -> int:
        v = struct.unpack_from('>q', self._data, self._pos)[0]
        self._pos += 8
        return v

    def _read_utf8(self) -> str:
        length = self._read_int()
        data = self._data[self._pos:self._pos + length]
        self._pos += length
        return data.decode('utf-8')

    def _read_byte_array(self) -> bytes:
        length = self._read_int()
        data = bytes(self._data[self._pos:self._pos + length])
        self._pos += length
        return data

    def _read_float_array(self) -> list:
        count = self._read_int()
        result = []
        for _ in range(count):
            result.append(self._read_float())
        return result

    def _read_int_array(self) -> list:
        count = self._read_int()
        result = []
        for _ in range(count):
            result.append(self._read_int())
        return result

    def _available(self) -> bool:
        return self._pos < self._len

    # -- Header parsing --

    def _read_header(self, doc: RcDocument):
        major_raw = self._read_unsigned_int()
        if major_raw >= 0x10000:
            # V7+ tagged header: major|MAGIC, minor(int), patch(int),
            # tag_count(int), then tag_count entries of:
            #   encoded_tag(short) + data_size(short) + data(variable)
            # encoded_tag = tag | (data_type << 10)
            # data_type: 0=INT, 1=FLOAT, 2=LONG, 3=STRING
            _minor = self._read_int()
            _patch = self._read_int()
            tag_count = self._read_int()
            for _ in range(tag_count):
                encoded_tag = self._read_short()
                data_size = self._read_short()
                tag = encoded_tag & 0x3FF
                data_type = (encoded_tag >> 10) & 0x3F
                if data_type == 0:      # INT
                    val = self._read_int()
                elif data_type == 1:    # FLOAT
                    val = self._read_float()
                elif data_type == 2:    # LONG
                    val = self._read_long()
                elif data_type == 3:    # STRING
                    val = self._read_utf8()
                else:
                    # Unknown type — skip data_size bytes
                    self._pos += data_size
                    continue
                if tag == 5:    # DOC_WIDTH
                    doc.width = val
                elif tag == 6:  # DOC_HEIGHT
                    doc.height = val
                elif tag == 9:  # DOC_CONTENT_DESCRIPTION
                    doc.description = val
        else:
            # V6 legacy header
            _minor = self._read_int()
            _patch = self._read_int()
            doc.width = self._read_int()
            doc.height = self._read_int()
            _capabilities = self._read_long()

    # -- Paint bundle reading --

    def _read_paint_values(self) -> dict:
        """Read a PAINT_VALUES int array and decode into a property dict."""
        values = self._read_int_array()
        paint = {}
        i = 0
        while i < len(values):
            raw = values[i]
            tag = raw & 0xFFFF
            high = (raw >> 16) & 0xFFFF
            i += 1
            if tag == 1:    # TEXT_SIZE
                paint['text_size'] = _bits_to_float(values[i]); i += 1
            elif tag == 4:  # COLOR
                paint['color'] = values[i] & 0xFFFFFFFF; i += 1
            elif tag == 5:  # STROKE_WIDTH
                paint['stroke_width'] = _bits_to_float(values[i]); i += 1
            elif tag == 6:  # STROKE_MITER
                paint['stroke_miter'] = _bits_to_float(values[i]); i += 1
            elif tag == 7:  # STROKE_CAP
                paint['stroke_cap'] = high
            elif tag == 8:  # STYLE
                paint['style'] = high
            elif tag == 9:  # SHADER
                paint['shader'] = values[i]; i += 1
            elif tag == 12: # ALPHA
                paint['alpha'] = _bits_to_float(values[i]); i += 1
            elif tag == 14: # ANTI_ALIAS
                paint['anti_alias'] = bool(high)
            elif tag == 15: # STROKE_JOIN
                paint['stroke_join'] = high
            elif tag == 16: # TYPEFACE
                paint['typeface_style'] = high
                paint['typeface_font'] = values[i]; i += 1
            elif tag == 18: # BLEND_MODE
                paint['blend_mode'] = high
            elif tag == 19: # COLOR_ID
                paint['color_id'] = values[i]; i += 1
            elif tag == 11: # GRADIENT
                paint['gradient'] = self._decode_gradient(high, values, i)
                i = paint['gradient'].pop('_next_i')
            elif tag == 21: # CLEAR_COLOR_FILTER
                paint['clear_color_filter'] = True
            elif tag == 13: # COLOR_FILTER
                paint['color_filter_mode'] = high
                paint['color_filter_color'] = values[i] & 0xFFFFFFFF; i += 1
            elif tag == 25: # PATH_EFFECT
                count = high
                pe_data = []
                for _ in range(count):
                    pe_data.append(_bits_to_float(values[i])); i += 1
                paint['path_effect'] = pe_data
            elif tag == 23: # FONT_AXIS
                count = high
                axes = []
                for _ in range(count):
                    tag_id = values[i]; i += 1
                    val = _bits_to_float(values[i]); i += 1
                    axes.append((tag_id, val))
                paint['font_axis'] = axes
            elif tag == 24: # TEXTURE
                paint['texture_id'] = values[i]; i += 1
                packed1 = values[i]; i += 1
                packed2 = values[i]; i += 1
                paint['texture_tile_x'] = packed1 & 0xFFFF
                paint['texture_tile_y'] = (packed1 >> 16) & 0xFFFF
                paint['texture_filter'] = packed2 & 0xFFFF
            elif tag == 22: # SHADER_MATRIX
                paint['shader_matrix'] = _bits_to_float(values[i]); i += 1
            elif tag == 20: # COLOR_FILTER_ID
                paint['color_filter_id'] = values[i]; i += 1
            elif tag == 26: # FALLBACK_TYPEFACE
                paint['fallback_typeface'] = values[i]; i += 1
            else:
                # Unknown tag — skip 1 value as best guess
                if i < len(values):
                    i += 1
        return paint

    def _decode_gradient(self, grad_type, values, i):
        """Decode a gradient from the paint int array."""
        info_word = values[i]; i += 1
        id_mask = (info_word >> 16) & 0xFFFF
        num_colors = info_word & 0xFFFF
        colors = []
        for _ in range(num_colors):
            colors.append(values[i] & 0xFFFFFFFF); i += 1
        num_positions = values[i]; i += 1
        positions = []
        for _ in range(num_positions):
            positions.append(_bits_to_float(values[i])); i += 1
        grad = {'type': grad_type, 'colors': colors, 'positions': positions,
                'id_mask': id_mask}
        if grad_type == 0:   # LINEAR
            grad['start_x'] = _bits_to_float(values[i]); i += 1
            grad['start_y'] = _bits_to_float(values[i]); i += 1
            grad['end_x'] = _bits_to_float(values[i]); i += 1
            grad['end_y'] = _bits_to_float(values[i]); i += 1
            grad['tile_mode'] = values[i]; i += 1
        elif grad_type == 1: # RADIAL
            grad['center_x'] = _bits_to_float(values[i]); i += 1
            grad['center_y'] = _bits_to_float(values[i]); i += 1
            grad['radius'] = _bits_to_float(values[i]); i += 1
            grad['tile_mode'] = values[i]; i += 1
        elif grad_type == 2: # SWEEP
            grad['center_x'] = _bits_to_float(values[i]); i += 1
            grad['center_y'] = _bits_to_float(values[i]); i += 1
        grad['_next_i'] = i
        return grad

    # -- Main parse loop --

    def parse(self) -> RcDocument:
        """Parse the binary data and return an RcDocument."""
        doc = RcDocument()
        while self._available():
            op = self._read_byte()
            try:
                self._dispatch(op, doc)
            except Exception as e:
                raise RuntimeError(
                    f"Parse error at byte {self._pos} (opcode {op}): {e}"
                ) from e
        return doc

    def _dispatch(self, op: int, doc: RcDocument):
        """Dispatch a single opcode."""

        if op == HEADER:
            self._read_header(doc)

        elif op == DATA_TEXT:
            tid = self._read_int()
            text = self._read_utf8()
            doc.texts[tid] = text

        elif op == DATA_FLOAT:
            fid = self._read_int()
            val = self._read_float()
            doc.floats[fid] = val

        elif op == DATA_INT:
            iid = self._read_int()
            val = self._read_int()
            doc.operations.append({'op': 'data_int', 'id': iid, 'value': val})

        elif op == DATA_LONG:
            lid = self._read_int()
            val = self._read_long()
            doc.operations.append({'op': 'data_long', 'id': lid, 'value': val})

        elif op == DATA_BOOLEAN:
            bid = self._read_int()
            val = self._read_byte()
            doc.operations.append({'op': 'data_bool', 'id': bid, 'value': bool(val)})

        elif op == DATA_PATH:
            raw_id = self._read_int()
            pid = raw_id & 0x00FFFFFF
            winding = (raw_id >> 24) & 0xFF
            data = self._read_float_array()
            doc.paths[pid] = data
            doc.operations.append({'op': 'data_path', 'id': pid,
                                   'winding': winding, 'data': data})

        elif op == DATA_BITMAP:
            self._read_data_bitmap(doc)

        elif op == DATA_SHADER:
            self._read_data_shader(doc)

        elif op == DATA_BITMAP_FONT:
            self._read_data_bitmap_font(doc)

        elif op == DATA_FONT:
            fid = self._read_int()
            ftype = self._read_int()
            fdata = self._read_byte_array()
            doc.operations.append({'op': 'data_font', 'id': fid,
                                   'font_type': ftype, 'data': fdata})

        elif op == ANIMATED_FLOAT:
            fid = self._read_int()
            packed_len = self._read_int()
            expr_count = packed_len & 0xFFFF
            anim_count = (packed_len >> 16) & 0xFFFF
            expr = [self._read_float() for _ in range(expr_count)]
            anim = [self._read_float() for _ in range(anim_count)]
            doc.operations.append({'op': 'animated_float', 'id': fid,
                                   'expression': expr, 'animation': anim})

        elif op == INTEGER_EXPRESSION:
            iid = self._read_int()
            expr = []
            count = self._read_int()
            for _ in range(count):
                expr.append(self._read_long())
            doc.operations.append({'op': 'integer_expression', 'id': iid,
                                   'expression': expr})

        elif op == COMPONENT_START:
            # No payload — just a marker
            doc.operations.append({'op': 'component_start'})

        elif op == PAINT_VALUES:
            paint = self._read_paint_values()
            doc.operations.append({'op': 'paint', **paint})

        # -- Layout containers --

        elif op == LAYOUT_ROOT:
            cid = self._read_int()
            doc.operations.append({'op': 'root', 'id': cid})

        elif op == LAYOUT_BOX:
            cid = self._read_int()
            pid = self._read_int()
            h = self._read_int()
            v = self._read_int()
            doc.operations.append({'op': 'box', 'id': cid, 'parent': pid,
                                   'horizontal': h, 'vertical': v})

        elif op == LAYOUT_ROW:
            cid = self._read_int()
            pid = self._read_int()
            h = self._read_int()
            v = self._read_int()
            spaced = self._read_float()
            doc.operations.append({'op': 'row', 'id': cid, 'parent': pid,
                                   'horizontal': h, 'vertical': v,
                                   'spaced_by': spaced})

        elif op == LAYOUT_COLUMN:
            cid = self._read_int()
            pid = self._read_int()
            h = self._read_int()
            v = self._read_int()
            spaced = self._read_float()
            doc.operations.append({'op': 'column', 'id': cid, 'parent': pid,
                                   'horizontal': h, 'vertical': v,
                                   'spaced_by': spaced})

        elif op == LAYOUT_CANVAS:
            cid = self._read_int()
            pid = self._read_int()
            doc.operations.append({'op': 'canvas', 'id': cid, 'parent': pid})

        elif op == LAYOUT_CANVAS_CONTENT:
            cid = self._read_int()
            doc.operations.append({'op': 'canvas_content', 'id': cid})

        elif op == CANVAS_OPERATIONS:
            doc.operations.append({'op': 'canvas_operations'})

        elif op == LAYOUT_CONTENT:
            cid = self._read_int()
            doc.operations.append({'op': 'content', 'id': cid})

        elif op == LAYOUT_FIT_BOX:
            cid = self._read_int()
            pid = self._read_int()
            h = self._read_int()
            v = self._read_int()
            doc.operations.append({'op': 'fit_box', 'id': cid, 'parent': pid,
                                   'horizontal': h, 'vertical': v})

        elif op == LAYOUT_FLOW:
            cid = self._read_int()
            pid = self._read_int()
            h = self._read_int()
            v = self._read_int()
            spaced = self._read_float()
            doc.operations.append({'op': 'flow', 'id': cid, 'parent': pid,
                                   'horizontal': h, 'vertical': v,
                                   'spaced_by': spaced})

        elif op == LAYOUT_STATE:
            cid = self._read_int()
            pid = self._read_int()
            h = self._read_int()
            v = self._read_int()
            idx = self._read_int()
            doc.operations.append({'op': 'state_layout', 'id': cid,
                                   'parent': pid, 'horizontal': h,
                                   'vertical': v, 'index_id': idx})

        elif op == LAYOUT_IMAGE:
            cid = self._read_int()
            pid = self._read_int()
            img = self._read_int()
            st = self._read_int()
            alpha = self._read_float()
            doc.operations.append({'op': 'image', 'id': cid, 'parent': pid,
                                   'image_id': img, 'scale_type': st,
                                   'alpha': alpha})

        elif op == CONTAINER_END:
            doc.operations.append({'op': 'end'})

        # -- Text components --

        elif op == LAYOUT_TEXT:
            doc.operations.append(self._read_layout_text())

        elif op == CORE_TEXT:
            doc.operations.append(self._read_core_text())

        elif op == TEXT_STYLE:
            doc.operations.append(self._read_text_style())

        # -- Modifiers --

        elif op == MODIFIER_WIDTH:
            dt = self._read_int()
            val = self._read_float()
            doc.operations.append({'op': 'mod_width', 'dim_type': dt, 'value': val})

        elif op == MODIFIER_HEIGHT:
            dt = self._read_int()
            val = self._read_float()
            doc.operations.append({'op': 'mod_height', 'dim_type': dt, 'value': val})

        elif op == MODIFIER_WIDTH_IN:
            dt = self._read_int()
            val = self._read_float()
            doc.operations.append({'op': 'mod_width_in', 'dim_type': dt, 'value': val})

        elif op == MODIFIER_HEIGHT_IN:
            dt = self._read_int()
            val = self._read_float()
            doc.operations.append({'op': 'mod_height_in', 'dim_type': dt, 'value': val})

        elif op == MODIFIER_PADDING:
            l = self._read_float()
            t = self._read_float()
            r = self._read_float()
            b = self._read_float()
            doc.operations.append({'op': 'mod_padding', 'left': l, 'top': t,
                                   'right': r, 'bottom': b})

        elif op == MODIFIER_BACKGROUND:
            flags = self._read_int()
            color_id = self._read_int()
            _r1 = self._read_int()
            _r2 = self._read_int()
            r = self._read_float()
            g = self._read_float()
            b = self._read_float()
            a = self._read_float()
            shape = self._read_int()
            color = _rgba_to_argb(r, g, b, a)
            doc.operations.append({'op': 'mod_background', 'flags': flags,
                                   'color_id': color_id, 'color': color,
                                   'shape': shape})

        elif op == MODIFIER_BORDER:
            flags = self._read_int()
            color_id = self._read_int()
            _r1 = self._read_int()
            _r2 = self._read_int()
            bw = self._read_float()
            rc = self._read_float()
            r = self._read_float()
            g = self._read_float()
            b = self._read_float()
            a = self._read_float()
            shape = self._read_int()
            color = _rgba_to_argb(r, g, b, a)
            doc.operations.append({'op': 'mod_border', 'flags': flags,
                                   'color_id': color_id, 'border_width': bw,
                                   'corner_radius': rc, 'color': color,
                                   'shape': shape})

        elif op == MODIFIER_CLIP_RECT:
            doc.operations.append({'op': 'mod_clip_rect'})

        elif op == MODIFIER_ROUNDED_CLIP_RECT:
            ts = self._read_float()
            te = self._read_float()
            bs = self._read_float()
            be = self._read_float()
            doc.operations.append({'op': 'mod_rounded_clip', 'top_start': ts,
                                   'top_end': te, 'bottom_start': bs,
                                   'bottom_end': be})

        elif op == MODIFIER_CLICK:
            self._read_click_modifier(doc)

        elif op == MODIFIER_TOUCH_DOWN:
            doc.operations.append({'op': 'mod_touch_down'})

        elif op == MODIFIER_TOUCH_UP:
            doc.operations.append({'op': 'mod_touch_up'})

        elif op == MODIFIER_TOUCH_CANCEL:
            doc.operations.append({'op': 'mod_touch_cancel'})

        elif op == MODIFIER_OFFSET:
            x = self._read_float()
            y = self._read_float()
            doc.operations.append({'op': 'mod_offset', 'x': x, 'y': y})

        elif op == MODIFIER_VISIBILITY:
            vis = self._read_int()
            doc.operations.append({'op': 'mod_visibility', 'visibility': vis})

        elif op == MODIFIER_ZINDEX:
            z = self._read_float()
            doc.operations.append({'op': 'mod_zindex', 'z': z})

        elif op == MODIFIER_SCROLL:
            direction = self._read_int()
            position_id = self._read_float()
            max_val = self._read_float()
            notch_max = self._read_float()
            doc.operations.append({'op': 'mod_scroll', 'direction': direction,
                                   'position_id': position_id,
                                   'max_val': max_val, 'notch_max': notch_max})

        elif op == MODIFIER_MARQUEE:
            doc.operations.append({'op': 'mod_marquee'})

        elif op == MODIFIER_GRAPHICS_LAYER:
            self._read_graphics_layer(doc)

        elif op == MODIFIER_RIPPLE:
            doc.operations.append({'op': 'mod_ripple'})

        elif op == MODIFIER_ALIGN_BY:
            align = self._read_float()
            flags = self._read_int()
            doc.operations.append({'op': 'mod_align_by', 'align': align, 'flags': flags})

        elif op == MODIFIER_COLLAPSIBLE_PRIORITY:
            orientation = self._read_int()
            p = self._read_float()
            doc.operations.append({'op': 'mod_collapsible_priority',
                                   'orientation': orientation, 'priority': p})

        elif op == MODIFIER_DRAW_CONTENT:
            doc.operations.append({'op': 'mod_draw_content'})

        # -- Draw operations --

        elif op == DRAW_RECT:
            l = self._read_float(); t = self._read_float()
            r = self._read_float(); b = self._read_float()
            doc.operations.append({'op': 'draw_rect', 'left': l, 'top': t,
                                   'right': r, 'bottom': b})

        elif op == DRAW_CIRCLE:
            cx = self._read_float(); cy = self._read_float()
            r = self._read_float()
            doc.operations.append({'op': 'draw_circle', 'cx': cx, 'cy': cy, 'r': r})

        elif op == DRAW_LINE:
            x1 = self._read_float(); y1 = self._read_float()
            x2 = self._read_float(); y2 = self._read_float()
            doc.operations.append({'op': 'draw_line', 'x1': x1, 'y1': y1,
                                   'x2': x2, 'y2': y2})

        elif op == DRAW_ROUND_RECT:
            l = self._read_float(); t = self._read_float()
            r = self._read_float(); b = self._read_float()
            rx = self._read_float(); ry = self._read_float()
            doc.operations.append({'op': 'draw_round_rect', 'left': l, 'top': t,
                                   'right': r, 'bottom': b, 'rx': rx, 'ry': ry})

        elif op == DRAW_OVAL:
            l = self._read_float(); t = self._read_float()
            r = self._read_float(); b = self._read_float()
            doc.operations.append({'op': 'draw_oval', 'left': l, 'top': t,
                                   'right': r, 'bottom': b})

        elif op == DRAW_ARC:
            l = self._read_float(); t = self._read_float()
            r = self._read_float(); b = self._read_float()
            sa = self._read_float(); sw = self._read_float()
            doc.operations.append({'op': 'draw_arc', 'left': l, 'top': t,
                                   'right': r, 'bottom': b,
                                   'start_angle': sa, 'sweep_angle': sw})

        elif op == DRAW_SECTOR:
            l = self._read_float(); t = self._read_float()
            r = self._read_float(); b = self._read_float()
            sa = self._read_float(); sw = self._read_float()
            doc.operations.append({'op': 'draw_sector', 'left': l, 'top': t,
                                   'right': r, 'bottom': b,
                                   'start_angle': sa, 'sweep_angle': sw})

        elif op == DRAW_PATH:
            pid = self._read_int()
            doc.operations.append({'op': 'draw_path', 'path_id': pid})

        elif op == DRAW_TWEEN_PATH:
            p1 = self._read_int(); p2 = self._read_int()
            tw = self._read_float()
            start = self._read_float(); stop = self._read_float()
            doc.operations.append({'op': 'draw_tween_path', 'path1': p1,
                                   'path2': p2, 'tween': tw,
                                   'start': start, 'stop': stop})

        elif op == DRAW_TEXT_RUN:
            tid = self._read_int()
            start = self._read_int(); end = self._read_int()
            cs = self._read_int(); ce = self._read_int()
            x = self._read_float(); y = self._read_float()
            rtl = self._read_byte()
            doc.operations.append({'op': 'draw_text_run', 'text_id': tid,
                                   'start': start, 'end': end,
                                   'context_start': cs, 'context_end': ce,
                                   'x': x, 'y': y, 'rtl': bool(rtl)})

        elif op == DRAW_TEXT_ANCHOR:
            tid = self._read_int()
            x = self._read_float(); y = self._read_float()
            px = self._read_float(); py = self._read_float()
            flags = self._read_int()
            doc.operations.append({'op': 'draw_text_anchor', 'text_id': tid,
                                   'x': x, 'y': y, 'pan_x': px, 'pan_y': py,
                                   'flags': flags})

        elif op == DRAW_TEXT_ON_PATH:
            tid = self._read_int(); pid = self._read_int()
            ho = self._read_float(); vo = self._read_float()
            doc.operations.append({'op': 'draw_text_on_path', 'text_id': tid,
                                   'path_id': pid, 'h_offset': ho, 'v_offset': vo})

        elif op == DRAW_TEXT_ON_CIRCLE:
            tid = self._read_int()
            cx = self._read_float(); cy = self._read_float()
            r = self._read_float(); sa = self._read_float()
            wro = self._read_float()
            align = self._read_int(); place = self._read_int()
            doc.operations.append({'op': 'draw_text_on_circle', 'text_id': tid,
                                   'cx': cx, 'cy': cy, 'radius': r,
                                   'start_angle': sa, 'warp_radius': wro,
                                   'alignment': align, 'placement': place})

        elif op == DRAW_CONTENT:
            doc.operations.append({'op': 'draw_content'})

        elif op == DRAW_BITMAP:
            img = self._read_int()
            l = self._read_float(); t = self._read_float()
            r = self._read_float(); b = self._read_float()
            cd = self._read_int()
            doc.operations.append({'op': 'draw_bitmap', 'image_id': img,
                                   'left': l, 'top': t, 'right': r, 'bottom': b,
                                   'content_desc_id': cd})

        elif op == DRAW_BITMAP_SCALED:
            img = self._read_int()
            sl = self._read_float(); st_ = self._read_float()
            sr = self._read_float(); sb = self._read_float()
            dl = self._read_float(); dt_ = self._read_float()
            dr = self._read_float(); db = self._read_float()
            stype = self._read_int(); sfact = self._read_float()
            cd = self._read_int()
            doc.operations.append({'op': 'draw_bitmap_scaled', 'image_id': img,
                                   'src_left': sl, 'src_top': st_,
                                   'src_right': sr, 'src_bottom': sb,
                                   'dst_left': dl, 'dst_top': dt_,
                                   'dst_right': dr, 'dst_bottom': db,
                                   'scale_type': stype, 'scale_factor': sfact,
                                   'content_desc_id': cd})

        elif op == DRAW_TO_BITMAP:
            bid = self._read_int()
            mode = self._read_int()
            color = self._read_int()
            doc.operations.append({'op': 'draw_to_bitmap', 'bitmap_id': bid,
                                   'mode': mode, 'color': color})

        # -- Matrix transforms --

        elif op == MATRIX_SAVE:
            doc.operations.append({'op': 'matrix_save'})

        elif op == MATRIX_RESTORE:
            doc.operations.append({'op': 'matrix_restore'})

        elif op == MATRIX_TRANSLATE:
            dx = self._read_float(); dy = self._read_float()
            doc.operations.append({'op': 'matrix_translate', 'dx': dx, 'dy': dy})

        elif op == MATRIX_SCALE:
            sx = self._read_float(); sy = self._read_float()
            cx = self._read_float(); cy = self._read_float()
            doc.operations.append({'op': 'matrix_scale', 'sx': sx, 'sy': sy,
                                   'cx': cx, 'cy': cy})

        elif op == MATRIX_ROTATE:
            angle = self._read_float()
            cx = self._read_float(); cy = self._read_float()
            doc.operations.append({'op': 'matrix_rotate', 'angle': angle,
                                   'cx': cx, 'cy': cy})

        elif op == MATRIX_SKEW:
            sx = self._read_float(); sy = self._read_float()
            doc.operations.append({'op': 'matrix_skew', 'sx': sx, 'sy': sy})

        elif op == MATRIX_SET:
            vals = []
            for _ in range(9):
                vals.append(self._read_float())
            doc.operations.append({'op': 'matrix_set', 'values': vals})

        elif op == MATRIX_FROM_PATH:
            pid = self._read_int()
            frac = self._read_float()
            vo = self._read_float()
            flags = self._read_int()
            doc.operations.append({'op': 'matrix_from_path', 'path_id': pid,
                                   'fraction': frac, 'v_offset': vo, 'flags': flags})

        # -- Clip --

        elif op == CLIP_RECT:
            l = self._read_float(); t = self._read_float()
            r = self._read_float(); b = self._read_float()
            doc.operations.append({'op': 'clip_rect', 'left': l, 'top': t,
                                   'right': r, 'bottom': b})

        elif op == CLIP_PATH:
            pid = self._read_int()
            doc.operations.append({'op': 'clip_path', 'path_id': pid})

        # -- Loop --

        elif op == LOOP_START:
            idx = self._read_int()
            frm = self._read_float()
            step = self._read_float()
            until = self._read_float()
            doc.operations.append({'op': 'loop_start', 'index_id': idx,
                                   'from': frm, 'step': step, 'until': until})

        # -- Skip --

        elif op == SKIP:
            stype = self._read_int()
            val = self._read_int()
            skip_len = self._read_int()
            doc.operations.append({'op': 'skip', 'skip_type': stype,
                                   'value': val, 'length': skip_len})

        # -- Actions / interactivity (read payload but don't interpret) --

        elif op == HOST_ACTION:
            self._read_action_block(doc, 'host_action')
        elif op == HOST_NAMED_ACTION:
            self._read_named_action_block(doc)
        elif op == HOST_METADATA_ACTION:
            self._read_metadata_action(doc)
        elif op == VALUE_FLOAT_CHANGE_ACTION:
            self._read_value_change(doc, 'float_change', 'f')
        elif op == VALUE_INTEGER_CHANGE_ACTION:
            self._read_value_change(doc, 'int_change', 'i')
        elif op == VALUE_STRING_CHANGE_ACTION:
            # Writer: int(dest_id) + int(src_id)
            dest_id = self._read_int()
            src_id = self._read_int()
            doc.operations.append({'op': 'string_change',
                                   'dest_id': dest_id, 'src_id': src_id})
        elif op == VALUE_FLOAT_EXPRESSION_CHANGE_ACTION:
            # Writer: int(value_id) + int(value)
            vid = self._read_int()
            val = self._read_int()
            doc.operations.append({'op': 'float_expr_change',
                                   'value_id': vid, 'value': val})
        elif op == VALUE_INTEGER_EXPRESSION_CHANGE_ACTION:
            # Writer: long(dest_id) + long(src_id)
            dest_id = self._read_long()
            src_id = self._read_long()
            doc.operations.append({'op': 'int_expr_change',
                                   'dest_id': dest_id, 'src_id': src_id})

        elif op == RUN_ACTION:
            doc.operations.append({'op': 'run_action'})

        # -- Misc data --

        elif op == TEXT_FROM_FLOAT:
            self._read_text_from_float(doc)
        elif op == TEXT_MERGE:
            oid = self._read_int()
            id1 = self._read_int()
            id2 = self._read_int()
            doc.operations.append({'op': 'text_merge', 'out_id': oid,
                                   'id1': id1, 'id2': id2})
        elif op == TEXT_LOOKUP:
            self._read_text_lookup(doc)
        elif op == TEXT_LOOKUP_INT:
            self._read_text_lookup_int(doc)
        elif op == TEXT_SUBTEXT:
            oid = self._read_int()
            tid = self._read_int()
            start = self._read_float()
            length = self._read_float()
            doc.operations.append({'op': 'text_subtext', 'out_id': oid,
                                   'text_id': tid, 'start': start, 'length': length})
        elif op == TEXT_TRANSFORM:
            oid = self._read_int()
            tid = self._read_int()
            start = self._read_float()
            length = self._read_float()
            operation = self._read_int()
            doc.operations.append({'op': 'text_transform', 'out_id': oid,
                                   'text_id': tid, 'start': start,
                                   'length': length, 'operation': operation})
        elif op == TEXT_MEASURE:
            oid = self._read_int()
            tid = self._read_int()
            mode = self._read_int()
            doc.operations.append({'op': 'text_measure', 'out_id': oid,
                                   'text_id': tid, 'mode': mode})
        elif op == TEXT_LENGTH:
            oid = self._read_int()
            tid = self._read_int()
            doc.operations.append({'op': 'text_length', 'out_id': oid,
                                   'text_id': tid})

        elif op == NAMED_VARIABLE:
            vid = self._read_int()
            vtype = self._read_int()
            name = self._read_utf8()
            doc.operations.append({'op': 'named_variable', 'id': vid,
                                   'name': name, 'var_type': vtype})

        elif op == COLOR_CONSTANT:
            oid = self._read_int()
            color = self._read_unsigned_int()
            doc.operations.append({'op': 'color_constant', 'id': oid,
                                   'color': color})

        elif op == COLOR_EXPRESSIONS:
            self._read_color_expression(doc)

        elif op == COLOR_THEME:
            self._read_color_theme(doc)

        elif op == ATTRIBUTE_TEXT:
            oid = self._read_int()
            tid = self._read_int()
            attr = self._read_short()
            self._read_short()  # padding
            doc.operations.append({'op': 'attr_text', 'out_id': oid,
                                   'text_id': tid, 'attribute': attr})

        elif op == ATTRIBUTE_IMAGE:
            oid = self._read_int()
            bid = self._read_int()
            attr = self._read_short()
            doc.operations.append({'op': 'attr_image', 'out_id': oid,
                                   'bitmap_id': bid, 'attribute': attr})

        elif op == ATTRIBUTE_TIME:
            self._read_time_attribute(doc)

        elif op == ATTRIBUTE_COLOR:
            oid = self._read_int()
            color_id = self._read_int()
            attr = self._read_short()
            doc.operations.append({'op': 'attr_color', 'out_id': oid,
                                   'color_id': color_id, 'attribute': attr})

        elif op == ID_MAP:
            oid = self._read_int()
            count = self._read_int()
            names = []
            types = []
            ids = []
            for _ in range(count):
                names.append(self._read_utf8())
                types.append(self._read_byte())
                ids.append(self._read_int())
            doc.operations.append({'op': 'id_map', 'id': oid,
                                   'names': names, 'types': types, 'ids': ids})

        elif op == ID_LIST:
            oid = self._read_int()
            count = self._read_int()
            items = [self._read_int() for _ in range(count)]
            doc.operations.append({'op': 'id_list', 'id': oid, 'items': items})

        elif op == FLOAT_LIST:
            oid = self._read_int()
            items = self._read_float_array()
            doc.operations.append({'op': 'float_list', 'id': oid, 'items': items})

        elif op == DYNAMIC_FLOAT_LIST:
            oid = self._read_int()
            length = self._read_float()
            doc.operations.append({'op': 'dynamic_float_list', 'id': oid,
                                   'length': length})

        elif op == UPDATE_DYNAMIC_FLOAT_LIST:
            oid = self._read_int()
            idx = self._read_int()
            val = self._read_float()
            doc.operations.append({'op': 'update_dynamic_float_list', 'id': oid,
                                   'index': idx, 'value': val})

        elif op == ID_LOOKUP:
            oid = self._read_int()
            map_id = self._read_int()
            key_id = self._read_int()
            doc.operations.append({'op': 'id_lookup', 'out_id': oid,
                                   'map_id': map_id, 'key_id': key_id})

        elif op == DATA_MAP_LOOKUP:
            oid = self._read_int()
            map_id = self._read_int()
            key_id = self._read_int()
            doc.operations.append({'op': 'data_map_lookup', 'out_id': oid,
                                   'map_id': map_id, 'key_id': key_id})

        elif op == COMPONENT_VALUE:
            # Writer: int(value_type) + int(component_id) + int(id)
            vtype = self._read_int()
            cid = self._read_int()
            vid = self._read_int()
            doc.operations.append({'op': 'component_value', 'value_type': vtype,
                                   'component_id': cid, 'value_id': vid})

        elif op == ANIMATION_SPEC:
            aid = self._read_int()
            motion_dur = self._read_float()
            motion_easing = self._read_int()
            vis_dur = self._read_float()
            vis_easing = self._read_int()
            enter_anim = self._read_int()
            exit_anim = self._read_int()
            doc.operations.append({'op': 'animation_spec', 'id': aid,
                                   'motion_duration': motion_dur,
                                   'motion_easing': motion_easing,
                                   'visibility_duration': vis_dur,
                                   'visibility_easing': vis_easing,
                                   'enter_animation': enter_anim,
                                   'exit_animation': exit_anim})

        elif op == TOUCH_EXPRESSION:
            self._read_touch_expression(doc)

        elif op == PATH_TWEEN:
            oid = self._read_int()
            p1 = self._read_int(); p2 = self._read_int()
            tw = self._read_float()
            doc.operations.append({'op': 'path_tween', 'out_id': oid,
                                   'path1': p1, 'path2': p2, 'tween': tw})

        elif op == PATH_CREATE:
            oid = self._read_int()
            x = self._read_float()
            y = self._read_float()
            doc.operations.append({'op': 'path_create', 'id': oid, 'x': x, 'y': y})

        elif op == PATH_ADD:
            pid = self._read_int()
            vals = self._read_float_array()
            doc.operations.append({'op': 'path_add', 'path_id': pid,
                                   'values': vals})

        elif op == PATH_COMBINE:
            oid = self._read_int()
            p1 = self._read_int(); p2 = self._read_int()
            combine_op = self._read_byte()
            doc.operations.append({'op': 'path_combine', 'out_id': oid,
                                   'path1': p1, 'path2': p2, 'combine_op': combine_op})

        elif op == PATH_EXPRESSION:
            self._read_path_expression(doc)

        elif op == THEME:
            tid = self._read_int()
            doc.operations.append({'op': 'theme', 'theme_id': tid})

        elif op == ROOT_CONTENT_BEHAVIOR:
            scroll = self._read_int()
            align = self._read_int()
            sizing = self._read_int()
            mode = self._read_int()
            doc.operations.append({'op': 'root_content_behavior',
                                   'scroll': scroll, 'alignment': align,
                                   'sizing': sizing, 'mode': mode})

        elif op == ROOT_CONTENT_DESCRIPTION:
            tid = self._read_int()
            doc.operations.append({'op': 'root_content_description',
                                   'text_id': tid})

        elif op == CLICK_AREA:
            cid = self._read_int()
            content_desc = self._read_int()
            l = self._read_float(); t = self._read_float()
            r = self._read_float(); b = self._read_float()
            meta_id = self._read_int()
            doc.operations.append({'op': 'click_area', 'id': cid,
                                   'content_desc_id': content_desc,
                                   'left': l, 'top': t,
                                   'right': r, 'bottom': b,
                                   'metadata_id': meta_id})

        elif op == CONDITIONAL_OPERATIONS:
            ctype = self._read_byte()
            a = self._read_float()
            b = self._read_float()
            doc.operations.append({'op': 'conditional', 'cond_type': ctype,
                                   'a': a, 'b': b})

        elif op == DEBUG_MESSAGE:
            text_id = self._read_int()
            value = self._read_float()
            flags = self._read_int()
            doc.operations.append({'op': 'debug', 'text_id': text_id,
                                   'value': value, 'flags': flags})

        elif op == HAPTIC_FEEDBACK:
            htype = self._read_int()
            doc.operations.append({'op': 'haptic', 'haptic_type': htype})

        elif op == REM:
            rem_id = self._read_int()
            doc.operations.append({'op': 'rem', 'id': rem_id})

        elif op == IMPULSE_START:
            duration = self._read_float()
            start = self._read_float()
            doc.operations.append({'op': 'impulse_start',
                                   'duration': duration, 'start': start})

        elif op == IMPULSE_PROCESS:
            doc.operations.append({'op': 'impulse_process'})

        elif op == FUNCTION_DEFINE:
            fid = self._read_int()
            count = self._read_int()
            args = [self._read_int() for _ in range(count)]
            doc.operations.append({'op': 'function_define', 'id': fid, 'args': args})

        elif op == FUNCTION_CALL:
            fid = self._read_int()
            count = self._read_int()
            args = [self._read_float() for _ in range(count)]
            doc.operations.append({'op': 'function_call', 'id': fid, 'args': args})

        elif op == UPDATE:
            uid = self._read_int()
            val = self._read_float()
            doc.operations.append({'op': 'update', 'id': uid, 'value': val})

        elif op == WAKE_IN:
            seconds = self._read_float()
            doc.operations.append({'op': 'wake_in', 'seconds': seconds})

        elif op == DRAW_BITMAP_INT:
            img = self._read_int()
            l = self._read_int(); t = self._read_int()
            r = self._read_int(); b = self._read_int()
            doc.operations.append({'op': 'draw_bitmap_int', 'image_id': img,
                                   'left': l, 'top': t, 'right': r, 'bottom': b})

        elif op == DRAW_BITMAP_FONT_TEXT_RUN:
            tid = self._read_int(); bfid = self._read_int()
            start = self._read_int(); end = self._read_int()
            x = self._read_float(); y = self._read_float()
            gs = self._read_float()
            doc.operations.append({'op': 'draw_bitmap_font_text_run',
                                   'text_id': tid, 'font_id': bfid,
                                   'start': start, 'end': end,
                                   'x': x, 'y': y, 'glyph_spacing': gs})

        elif op == DRAW_BITMAP_FONT_TEXT_RUN_ON_PATH:
            tid = self._read_int(); bfid = self._read_int()
            pid = self._read_int()
            start = self._read_int(); end = self._read_int()
            ya = self._read_float(); gs = self._read_float()
            doc.operations.append({'op': 'draw_bitmap_font_text_run_on_path',
                                   'text_id': tid, 'font_id': bfid,
                                   'path_id': pid, 'start': start, 'end': end,
                                   'y_adj': ya, 'glyph_spacing': gs})

        elif op == DRAW_BITMAP_TEXT_ANCHORED:
            tid = self._read_int(); bfid = self._read_int()
            start = self._read_float(); end = self._read_float()
            x = self._read_float(); y = self._read_float()
            px = self._read_float(); py = self._read_float()
            gs = self._read_float()
            doc.operations.append({'op': 'draw_bitmap_text_anchored',
                                   'text_id': tid, 'font_id': bfid,
                                   'start': start, 'end': end,
                                   'x': x, 'y': y, 'pan_x': px, 'pan_y': py,
                                   'glyph_spacing': gs})

        elif op == BITMAP_TEXT_MEASURE:
            oid = self._read_int()
            tid = self._read_int(); bfid = self._read_int()
            mw = self._read_int(); gs = self._read_float()
            doc.operations.append({'op': 'bitmap_text_measure', 'out_id': oid,
                                   'text_id': tid, 'font_id': bfid,
                                   'measure_width': mw, 'glyph_spacing': gs})

        elif op == MATRIX_CONSTANT:
            mid = self._read_int()
            mtype = self._read_int()
            vals = self._read_float_array()
            doc.operations.append({'op': 'matrix_constant', 'id': mid,
                                   'matrix_type': mtype, 'values': vals})

        elif op == MATRIX_EXPRESSION:
            mid = self._read_int()
            mtype = self._read_int()
            vals = self._read_float_array()
            doc.operations.append({'op': 'matrix_expression', 'id': mid,
                                   'matrix_type': mtype, 'values': vals})

        elif op == MATRIX_VECTOR_MATH:
            op_type = self._read_short()
            mid = self._read_int()
            out_count = self._read_int()
            out_ids = [self._read_int() for _ in range(out_count)]
            vec_count = self._read_int()
            from_vec = [self._read_float() for _ in range(vec_count)]
            doc.operations.append({'op': 'matrix_vector_math', 'id': mid,
                                   'op_type': op_type, 'out_ids': out_ids,
                                   'from_vec': from_vec})

        elif op == LAYOUT_COLLAPSIBLE_ROW:
            cid = self._read_int(); pid = self._read_int()
            h = self._read_int(); v = self._read_int()
            spaced = self._read_float()
            doc.operations.append({'op': 'collapsible_row', 'id': cid,
                                   'parent': pid, 'horizontal': h, 'vertical': v,
                                   'spaced_by': spaced})

        elif op == LAYOUT_COLLAPSIBLE_COLUMN:
            cid = self._read_int(); pid = self._read_int()
            h = self._read_int(); v = self._read_int()
            spaced = self._read_float()
            doc.operations.append({'op': 'collapsible_column', 'id': cid,
                                   'parent': pid, 'horizontal': h, 'vertical': v,
                                   'spaced_by': spaced})

        elif op == LAYOUT_COMPUTE:
            compute_type = self._read_int()
            bounds_id = self._read_int()
            animate = self._read_byte()
            doc.operations.append({'op': 'layout_compute', 'compute_type': compute_type,
                                   'bounds_id': bounds_id, 'animate': animate != 0})

        elif op == ACCESSIBILITY_SEMANTICS:
            content_desc_id = self._read_int()
            role = self._read_byte()
            text_id = self._read_int()
            state_desc_id = self._read_int()
            mode = self._read_byte()
            enabled = self._read_byte()
            clickable = self._read_byte()
            doc.operations.append({'op': 'accessibility',
                                   'content_desc_id': content_desc_id,
                                   'role': role, 'text_id': text_id,
                                   'state_desc_id': state_desc_id,
                                   'mode': mode, 'enabled': enabled != 0,
                                   'clickable': clickable != 0})

        elif op == PARTICLE_COMPARE:
            self._read_particle_compare(doc)

        elif op == PARTICLE_DEFINE:
            self._read_particle_define(doc)

        elif op == PARTICLE_LOOP:
            self._read_particle_loop(doc)

        elif op == LOAD_BITMAP:
            bid = self._read_int()
            doc.operations.append({'op': 'load_bitmap', 'id': bid})

        else:
            raise RuntimeError(f"Unknown opcode {op} at position {self._pos - 1}")

    # -- Helpers for complex operations --

    def _read_layout_text(self) -> dict:
        cid = self._read_int()
        pid = self._read_int()
        tid = self._read_int()
        color = self._read_unsigned_int()
        font_size = self._read_float()
        font_style = self._read_int()
        font_weight = self._read_float()
        font_family = self._read_int()
        flags = self._read_short()
        text_align = self._read_short()
        overflow = self._read_int()
        max_lines = self._read_int()
        return {'op': 'layout_text', 'id': cid, 'parent': pid,
                'text_id': tid, 'color': color, 'font_size': font_size,
                'font_style': font_style, 'font_weight': font_weight,
                'font_family': font_family, 'flags': flags,
                'text_align': text_align, 'overflow': overflow,
                'max_lines': max_lines}

    def _read_core_text(self) -> dict:
        tid = self._read_int()
        count = self._read_short()
        params = {}
        for _ in range(count):
            tag = self._read_byte()
            tag_type = _CORE_TEXT_TAG_TYPES.get(tag, 'i')
            if tag_type == 'i':
                params[tag] = self._read_int()
            elif tag_type == 'f':
                params[tag] = self._read_float()
            elif tag_type == 'b':
                params[tag] = bool(self._read_byte())
        result = {'op': 'core_text', 'text_id': tid}
        result['component_id'] = params.get(1, -1)
        result['color'] = params.get(3, 0xFF000000)
        result['font_size'] = params.get(5, 36.0)
        result['font_style'] = params.get(6, 0)
        result['font_weight'] = params.get(7, 400.0)
        result['font_family'] = params.get(8, -1)
        result['text_align'] = params.get(9, 1)
        result['overflow'] = params.get(10, 1)
        result['max_lines'] = params.get(11, 0x7FFFFFFF)
        result['flags'] = params.get(23, 0)
        result['raw_params'] = params
        return result

    def _read_text_style(self) -> dict:
        sid = self._read_int()
        count = self._read_short()
        params = {}
        for _ in range(count):
            tag = self._read_byte()
            tag_type = _CORE_TEXT_TAG_TYPES.get(tag, 'i')
            if tag_type == 'i':
                params[tag] = self._read_int()
            elif tag_type == 'f':
                params[tag] = self._read_float()
            elif tag_type == 'b':
                params[tag] = bool(self._read_byte())
        return {'op': 'text_style', 'id': sid, 'params': params}

    def _read_data_bitmap(self, doc):
        bid = self._read_int()
        w_raw = self._read_int()
        h_raw = self._read_int()
        data = self._read_byte_array()
        btype = (w_raw >> 16) & 0xFFFF
        width = w_raw & 0xFFFF
        encoding = (h_raw >> 16) & 0xFFFF
        height = h_raw & 0xFFFF
        # When type+encoding are 0, width/height were written unpacked
        if btype == 0 and encoding == 0:
            width = w_raw
            height = h_raw
        doc.operations.append({'op': 'data_bitmap', 'id': bid, 'width': width,
                               'height': height, 'bitmap_type': btype,
                               'encoding': encoding, 'data': data})

    def _read_data_shader(self, doc):
        sid = self._read_int()
        stype = self._read_int()
        data = self._read_float_array()
        doc.operations.append({'op': 'data_shader', 'id': sid,
                               'shader_type': stype, 'data': data})

    def _read_data_bitmap_font(self, doc):
        fid = self._read_int()
        count_raw = self._read_int()
        version = (count_raw >> 16) & 0xFFFF
        count = count_raw & 0xFFFF
        glyphs = []
        for _ in range(count):
            chars = self._read_utf8()
            bid = self._read_int()
            ml = self._read_short(); mt = self._read_short()
            mr = self._read_short(); mb = self._read_short()
            bw = self._read_short(); bh = self._read_short()
            glyphs.append({'chars': chars, 'bitmap_id': bid,
                           'margin_left': ml, 'margin_top': mt,
                           'margin_right': mr, 'margin_bottom': mb,
                           'bitmap_width': bw, 'bitmap_height': bh})
        kerning = {}
        if version >= 2:
            kcount = self._read_short()
            for _ in range(kcount):
                key = self._read_utf8()
                val = self._read_short()
                kerning[key] = val
        doc.operations.append({'op': 'data_bitmap_font', 'id': fid,
                               'glyphs': glyphs, 'kerning': kerning})

    def _read_click_modifier(self, doc):
        # MODIFIER_CLICK has no payload — just the opcode
        doc.operations.append({'op': 'mod_click'})

    def _read_touch_modifier(self, doc, op_name):
        var_id = self._read_int()
        stop_type = self._read_int()
        count = self._read_int()
        stop_values = [self._read_float() for _ in range(count)]
        doc.operations.append({'op': op_name, 'var_id': var_id,
                               'stop_type': stop_type, 'stop_values': stop_values})

    def _read_graphics_layer(self, doc):
        sx = self._read_float(); sy = self._read_float()
        ax = self._read_float(); ay = self._read_float()
        tx = self._read_float(); ty = self._read_float()
        rx = self._read_float(); ry = self._read_float()
        rz = self._read_float()
        cd = self._read_float()
        doc.operations.append({'op': 'mod_graphics_layer',
                               'scale_x': sx, 'scale_y': sy,
                               'anchor_x': ax, 'anchor_y': ay,
                               'translate_x': tx, 'translate_y': ty,
                               'rotation_x': rx, 'rotation_y': ry,
                               'rotation_z': rz, 'camera_distance': cd})

    def _read_action_block(self, doc, name):
        # HOST_ACTION: int(action_id) only
        action_id = self._read_int()
        doc.operations.append({'op': name, 'action_id': action_id})

    def _read_named_action_block(self, doc):
        # HOST_NAMED_ACTION: int(text_id) + int(action_type) + int(value_id)
        text_id = self._read_int()
        action_type = self._read_int()
        value_id = self._read_int()
        doc.operations.append({'op': 'host_named_action', 'text_id': text_id,
                               'action_type': action_type, 'value_id': value_id})

    def _read_metadata_action(self, doc):
        # HOST_METADATA_ACTION: int(action_id) + int(metadata_id)
        action_id = self._read_int()
        metadata_id = self._read_int()
        doc.operations.append({'op': 'host_metadata_action',
                               'action_id': action_id, 'metadata_id': metadata_id})

    def _read_value_change(self, doc, name, vtype):
        vid = self._read_int()
        if vtype == 'f':
            val = self._read_float()
        elif vtype == 'i':
            val = self._read_int()
        elif vtype == 's':
            val = self._read_utf8()
        doc.operations.append({'op': name, 'var_id': vid, 'value': val})

    def _read_expr_change(self, doc, name):
        vid = self._read_int()
        expr = self._read_float_array()
        doc.operations.append({'op': name, 'var_id': vid, 'expression': expr})

    def _read_text_from_float(self, doc):
        oid = self._read_int()
        value = self._read_float()
        before = self._read_short()
        after = self._read_short()
        flags = self._read_int()
        doc.operations.append({'op': 'text_from_float', 'out_id': oid,
                               'value': value, 'before': before,
                               'after': after, 'flags': flags})

    def _read_text_lookup(self, doc):
        text_id = self._read_int()
        data_set_id = self._read_int()
        index = self._read_float()
        doc.operations.append({'op': 'text_lookup', 'text_id': text_id,
                               'data_set_id': data_set_id, 'index': index})

    def _read_text_lookup_int(self, doc):
        text_id = self._read_int()
        data_set_id = self._read_int()
        index_id = self._read_int()
        doc.operations.append({'op': 'text_lookup_int', 'text_id': text_id,
                               'data_set_id': data_set_id, 'index_id': index_id})

    def _read_color_expression(self, doc):
        # Format: int(id) + int(mode_packed) + 3 values (always 4 ints after id)
        oid = self._read_int()
        mode_packed = self._read_int()
        v1 = self._read_int()
        v2 = self._read_int()
        v3 = self._read_int()
        doc.operations.append({'op': 'color_expression', 'out_id': oid,
                               'mode': mode_packed, 'v1': v1, 'v2': v2, 'v3': v3})

    def _read_color_theme(self, doc):
        # Format: int(id) + int(group_id) + short(light_id) + short(dark_id) +
        #         int(light_fallback) + int(dark_fallback)
        oid = self._read_int()
        group_id = self._read_int()
        light_id = self._read_short()
        dark_id = self._read_short()
        light_fallback = self._read_int()
        dark_fallback = self._read_int()
        doc.operations.append({'op': 'color_theme', 'out_id': oid,
                               'group_id': group_id,
                               'light_id': light_id, 'dark_id': dark_id,
                               'light_fallback': light_fallback,
                               'dark_fallback': dark_fallback})

    def _read_time_attribute(self, doc):
        oid = self._read_int()
        attr_type = self._read_int()
        count = self._read_int()
        args = [self._read_int() for _ in range(count)]
        doc.operations.append({'op': 'attr_time', 'out_id': oid,
                               'attr_type': attr_type, 'args': args})

    def _read_touch_expression(self, doc):
        oid = self._read_int()
        def_val = self._read_float()
        min_val = self._read_float()
        max_val = self._read_float()
        velocity_id = self._read_float()
        touch_effects = self._read_int()
        exp_len = self._read_int()
        expression = [self._read_float() for _ in range(exp_len)]
        packed = self._read_int()
        touch_mode = (packed >> 16) & 0xFFFF
        spec_len = packed & 0xFFFF
        touch_spec = [self._read_float() for _ in range(spec_len)]
        easing_len = self._read_int()
        easing_spec = [self._read_float() for _ in range(easing_len)]
        doc.operations.append({'op': 'touch_expression', 'out_id': oid,
                               'def_value': def_val, 'min': min_val,
                               'max': max_val, 'velocity_id': velocity_id,
                               'touch_effects': touch_effects,
                               'expression': expression,
                               'touch_mode': touch_mode,
                               'touch_spec': touch_spec,
                               'easing_spec': easing_spec})

    def _read_path_expression(self, doc):
        # Format: int(id) + int(flags) + float(start) + float(end) + float(count)
        #         + float_array(exp_x) + float_array(exp_y)
        oid = self._read_int()
        flags = self._read_int()
        start = self._read_float()
        end = self._read_float()
        count = self._read_float()
        exp_x = self._read_float_array()
        exp_y = self._read_float_array()
        doc.operations.append({'op': 'path_expression', 'out_id': oid,
                               'flags': flags, 'start': start, 'end': end,
                               'count': count, 'exp_x': exp_x, 'exp_y': exp_y})

    def _read_particle_compare(self, doc):
        """Read PARTICLE_COMPARE (ParticlesCompare).
        Format: int(id) + short(flags) + float(min) + float(max) +
                float_array(compare) +
                int(result1Len) + result1Len * float_array(eq) +
                int(result2Len) + result2Len * float_array(eq)
        """
        pid = self._read_int()
        flags = self._read_short()
        min_val = self._read_float()
        max_val = self._read_float()
        compare_expr = self._read_float_array()
        result1_len = self._read_int()
        equations1 = []
        for _ in range(result1_len):
            equations1.append(self._read_float_array())
        result2_len = self._read_int()
        equations2 = []
        for _ in range(result2_len):
            equations2.append(self._read_float_array())
        doc.operations.append({'op': 'particle_compare', 'id': pid,
                               'flags': flags, 'min': min_val, 'max': max_val,
                               'compare': compare_expr,
                               'equations1': equations1, 'equations2': equations2})

    def _read_particle_define(self, doc):
        """Read PARTICLE_DEFINE (ParticlesCreate).
        Format: int(id) + int(particleCount) + int(varLen) +
                varLen * (int(varId) + int(equLen) + equLen * float)
        """
        pid = self._read_int()
        particle_count = self._read_int()
        var_len = self._read_int()
        variables = []
        for _ in range(var_len):
            var_id = self._read_int()
            equ_len = self._read_int()
            equation = [self._read_float() for _ in range(equ_len)]
            variables.append({'var_id': var_id, 'equation': equation})
        doc.operations.append({'op': 'particle_define', 'id': pid,
                               'particle_count': particle_count,
                               'variables': variables})

    def _read_particle_loop(self, doc):
        """Read PARTICLE_LOOP (ParticlesLoop).
        Format: int(id) + int(restartLen) + restartLen * float +
                int(varLen) + varLen * (int(equLen) + equLen * float)
        """
        pid = self._read_int()
        restart_len = self._read_int()
        restart = [self._read_float() for _ in range(restart_len)] if restart_len > 0 else []
        var_len = self._read_int()
        equations = []
        for _ in range(var_len):
            equ_len = self._read_int()
            equation = [self._read_float() for _ in range(equ_len)]
            equations.append(equation)
        doc.operations.append({'op': 'particle_loop', 'id': pid,
                               'restart': restart, 'equations': equations})


def _bits_to_float(bits: int) -> float:
    """Reinterpret unsigned 32-bit int bits as IEEE 754 float."""
    return struct.unpack('>f', struct.pack('>I', bits & 0xFFFFFFFF))[0]


def _rgba_to_argb(r: float, g: float, b: float, a: float) -> int:
    """Convert float RGBA [0..1] to packed ARGB int."""
    ai = max(0, min(255, int(a * 255)))
    ri = max(0, min(255, int(r * 255)))
    gi = max(0, min(255, int(g * 255)))
    bi = max(0, min(255, int(b * 255)))
    return (ai << 24) | (ri << 16) | (gi << 8) | bi

"""AttributedString demo. Port of DemoAttributedString.java.

Generates attribute_string.rc — styled text using text components with
underline and strikethrough drawn via canvas operations.
"""
import sys
import os
import struct

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RemoteComposeWriter, Rc
from rcreate.modifiers import RecordingModifier

FE = Rc.FloatExpression
PROFILE_ANDROIDX = 0x200
PROFILE_EXPERIMENTAL = 0x1

# AttributeRun constants (from DemoAttributedString.java)
POSTURE = 2
FOREGROUND = 3
BACKGROUND = 4
UNDERLINE = 5
STRIKETHROUGH = 6
SUPERSCRIPT = 7
SIZE = 8
POSTURE_BOLD = 1
POSTURE_ITALIC = 2


def _make_result(rc):
    class Result:
        def encode(self): return rc.encode_to_byte_array()
        def save(self, path):
            with open(path, 'wb') as f: f.write(self.encode())
    return Result()


def _float_to_raw_int_bits(f):
    return struct.unpack('>I', struct.pack('>f', f))[0]


def _text_run(rc, text_str, key_values):
    """Emit a styled text component. Port of text() in DemoAttributedString.java."""
    m = RecordingModifier().align_by_baseline()

    underline = False
    strikethrough = False
    color = 0xFF000000
    font_size = 46.0
    font_style = 0
    font_weight = 400.0
    font_family = None
    text_align = Rc.Text.ALIGN_LEFT
    overflow = Rc.Text.OVERFLOW_CLIP
    max_lines = 0x7FFFFFFF

    i = 0
    while i < len(key_values):
        key = key_values[i]
        val = key_values[i + 1]
        if key == POSTURE:
            if val == POSTURE_BOLD:
                font_weight = 700.0
            elif val == POSTURE_ITALIC:
                font_style = 1
        elif key == FOREGROUND:
            color = val
        elif key == BACKGROUND:
            m = m.background(val)
        elif key == UNDERLINE:
            underline = True
        elif key == STRIKETHROUGH:
            strikethrough = True
        elif key == SUPERSCRIPT:
            pass  # No visual effect in the demo
        elif key == SIZE:
            font_size *= struct.unpack('>f', struct.pack('>I', val & 0xFFFFFFFF))[0]
        i += 2

    text_id = rc.text_create_id(text_str)
    rc.start_text_component(m, text_id, color, font_size, font_style, font_weight,
                            font_family, text_align, overflow, max_lines)
    rc.start_canvas_operations()
    rc.draw_component_content()

    if underline:
        w = rc.add_component_width_value()
        base = rc.float_expression(rc.add_component_height_value(), 8, FE.SUB)
        rc.draw_line(0, base, w, base)

    if strikethrough:
        w = rc.add_component_width_value()
        strike = rc.float_expression(rc.add_component_height_value(), 0.6, FE.MUL)
        rc.draw_line(0, strike, w, strike)

    rc.end_canvas_operations()
    rc.end_text_component()


def demo_attributed_string():
    """AttributedString — styled text with underline/strikethrough."""
    rc = RemoteComposeWriter(500, 500, "sd", api_level=7,
                             profiles=PROFILE_ANDROIDX | PROFILE_EXPERIMENTAL)

    # The full text from Java
    text = ('AttributedString Demo:\n'
            'This is Bold, this is Italic.\n'
            'This text is Red, this is Blue,\n'
            ' and this has a Yellow Background.\n'
            'This is Underlined, and this has a Strikethrough.\n'
            'This is Big, and this is Superscript\u00b2.')

    # Text runs as Java's AttributedCharacterIterator would produce them.
    # Each run: (start, end, key_values)
    # key_values is a list of [key, value] pairs matching the Java AttributeRun interface.
    runs = [
        (0, 31, []),                             # "AttributedString Demo:\nThis is "
        (31, 35, [POSTURE, POSTURE_BOLD]),       # "Bold"
        (35, 45, []),                             # ", this is "
        (45, 51, [POSTURE, POSTURE_ITALIC]),     # "Italic"
        (51, 66, []),                             # ".\nThis text is "
        (66, 69, [FOREGROUND, 0xFFFF0000]),      # "Red"
        (69, 79, []),                             # ", this is "
        (79, 83, [FOREGROUND, 0xFF0000FF]),      # "Blue"
        (83, 101, []),                            # ",\n and this has a "
        (101, 118, [BACKGROUND, 0xFFFFFF00]),    # "Yellow Background"
        (118, 128, []),                           # ".\nThis is "
        (128, 138, [UNDERLINE, 1]),              # "Underlined"
        (138, 155, []),                           # ", and this has a "
        (155, 168, [STRIKETHROUGH, 1]),          # "Strikethrough"
        (168, 178, []),                           # ".\nThis is "
        (178, 181, [SIZE, _float_to_raw_int_bits(2.0)]),  # "Big"
        (181, 206, []),                           # ", and this is Superscript"
        (206, 207, [SUPERSCRIPT, 1]),            # "²"
        (207, 208, []),                           # "."
    ]

    def content():
        rc.start_box(RecordingModifier().fill_max_size().background(0xFFFFFFFF).padding(4),
                     Rc.Layout.START, Rc.Layout.TOP)
        rc.start_column(RecordingModifier().fill_max_size(), 1, 1)
        rc.start_row(RecordingModifier().fill_max_width(),
                     Rc.Layout.START, Rc.Layout.TOP)

        for start, end, key_values in runs:
            substr = text[start:end]
            if '\n' in substr:
                parts = substr.split('\n')
                not_first = False
                for part in parts:
                    if not_first:
                        rc.end_row()
                        rc.start_row(RecordingModifier().fill_max_width(),
                                     Rc.Layout.START, Rc.Layout.TOP)
                    not_first = True
                    _text_run(rc, part, key_values)
            else:
                _text_run(rc, substr, key_values)

        rc.end_row()
        rc.end_column()
        rc.end_box()

    rc.root(content)
    return _make_result(rc)


if __name__ == '__main__':
    ctx = demo_attributed_string()
    data = ctx.encode()
    print(f"attributeString: {len(data)} bytes")
    ctx.save("attribute_string.rc")

"""Anchored text demo. Port of DemoAnchorText.java anchoredText().

Generates: anchored_text.rc
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RemoteComposeWriter, Rc, as_nan
from rcreate.modifiers import RecordingModifier

FE = Rc.FloatExpression
CONTINUOUS_SEC = Rc.Time.CONTINUOUS_SEC

PROFILE_ANDROIDX = Rc.Profiles.PROFILE_ANDROIDX
DKGRAY = 0xFF444444
WHITE = 0xFFFFFFFF
RED = 0xFFFF0000
BLUE = 0xFF0000FF
BLACK = 0xFF000000

STYLE_FILL = Rc.Paint.STYLE_FILL
STYLE_STROKE = Rc.Paint.STYLE_STROKE

MEASURE_EVERY_TIME = Rc.TextAnchorMask.MEASURE_EVERY_TIME
BASELINE_RELATIVE = Rc.TextAnchorMask.BASELINE_RELATIVE


def _make_result(rc):
    class Result:
        def encode(self): return rc.encode_to_byte_array()
        def save(self, path):
            with open(path, 'wb') as f: f.write(self.encode())
    return Result()


def demo_anchored_text():
    """Anchored text — port of DemoAnchorText.java anchoredText()."""
    rc = RemoteComposeWriter(500, 500, "sd", api_level=7, profiles=PROFILE_ANDROIDX)

    def content():
        # Java box(modifier) = no content, CENTER/CENTER alignment, immediate close
        rc.box(RecordingModifier().fill_max_size().background(DKGRAY).padding(4),
               Rc.Layout.CENTER, Rc.Layout.CENTER)
        rc.start_canvas(RecordingModifier().fill_max_size())

        w = rc.add_component_width_value()
        h = rc.add_component_height_value()
        cx = rc.float_expression(w, 0.5, FE.MUL)
        v1 = rc.float_expression(cx, 20.0, FE.SUB)
        v2 = rc.float_expression(cx, 20.0, FE.ADD)
        l1 = rc.float_expression(h, 0.2, FE.MUL)
        l2 = rc.float_expression(h, 0.4, FE.MUL)
        l3 = rc.float_expression(h, 0.6, FE.MUL)
        l4 = rc.float_expression(h, 0.8, FE.MUL)
        l5 = rc.float_expression(h, 0.9, FE.MUL)

        # White background
        rc.rc_paint.set_color(WHITE).commit()
        rc.draw_rect(0, 0, w, h)

        # Red guide lines
        rc.rc_paint.set_color(RED).commit()
        rc.draw_line(0, l1, w, l1)
        rc.draw_line(0, l2, w, l2)
        rc.draw_line(0, l3, w, l3)
        rc.draw_line(0, l4, w, l4)
        rc.draw_line(v1, 0, v1, h)
        rc.draw_line(v2, 0, v2, h)

        dur = 10
        sec = CONTINUOUS_SEC
        t = rc.float_expression(sec, dur * 3, FE.MOD)
        animat_x = rc.float_expression(sec, 2, FE.MUL, 2, FE.PINGPONG, 1, FE.SUB)
        animat_y = rc.float_expression(sec, 3, FE.MUL, 2, FE.PINGPONG, 1, FE.SUB)

        flag1 = MEASURE_EVERY_TIME
        flag2 = BASELINE_RELATIVE

        rc.rc_paint.set_color(BLUE).set_text_size(64.0).commit()

        str_id = rc.add_text("flip plop")

        # Conditional block 1: t < dur
        rc.conditional_operations(Rc.Condition.LT, t, dur)
        rc.draw_text_anchored("X Right top X", v1, l1, 1, 1, 0)
        rc.draw_text_anchored("X Left top X", v2, l1, -1, 1, 0)
        rc.draw_text_anchored("X Right center X", v1, l2, 1, 0, 0)
        rc.draw_text_anchored("X Left center X", v2, l2, -1, 0, 0)
        rc.draw_text_anchored("X Right bottom X", v1, l3, 1, -1, 0)
        rc.draw_text_anchored("X Left bottom X", v2, l3, -1, -1, 0)
        rc.draw_text_anchored("X Right baseline X", v1, l4, 1, 0, flag2)
        rc.draw_text_anchored("X Left baseline X", v2, l4, -1, 0, flag2)
        rc.end_conditional_operations()

        # Conditional block 2: t > dur
        rc.conditional_operations(Rc.Condition.GT, t, dur)
        rc.draw_text_anchored(str_id, v1, l1, 1, 1, 0)
        rc.draw_text_anchored(str_id, v1, l2, 1, 0, 0)
        rc.draw_text_anchored(str_id, v1, l3, 1, -1, 0)
        rc.draw_text_anchored(str_id, v1, l4, 1, 0, flag2)

        # Nested conditional: t > dur * 2
        rc.conditional_operations(Rc.Condition.GT, t, dur * 2)
        rc.rc_paint.set_color(BLUE).set_text_size(128.0).commit()
        rc.end_conditional_operations()

        rc.draw_text_anchored(str_id, v2, l1, -1, 1, flag1)
        rc.draw_text_anchored(str_id, v2, l2, -1, 0, flag1)
        rc.draw_text_anchored(str_id, v2, l3, -1, -1, flag1)
        rc.draw_text_anchored(str_id, v2, l4, -1, 0, flag2 | flag1)
        rc.draw_text_anchored(str_id, v2, l5, animat_x, animat_y, flag1)
        rc.end_conditional_operations()

        rc.rc_paint.set_color(BLACK).commit()

        rc.end_canvas()

    rc.root(content)
    return _make_result(rc)


if __name__ == '__main__':
    os.makedirs(os.path.join(os.path.dirname(__file__), '..', 'output'), exist_ok=True)
    result = demo_anchored_text()
    path = os.path.join(os.path.dirname(__file__), '..', 'output', 'anchored_text.rc')
    result.save(path)
    print(f'anchored_text: {len(result.encode())} bytes -> {path}')

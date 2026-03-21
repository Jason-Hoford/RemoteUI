"""Flick demo. Port of DemoFlick.java flickTest().

Generates: demo_flick_flick_test.rc
"""
import sys
import os
import struct

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RemoteComposeWriter, Rc, as_nan
from rcreate.modifiers import RecordingModifier

FE = Rc.FloatExpression
TOUCH_Y = Rc.Touch.POSITION_Y


def _f32(v):
    return struct.unpack('>f', struct.pack('>f', v))[0]


def _make_result(rc):
    class Result:
        def encode(self): return rc.encode_to_byte_array()
        def save(self, path):
            with open(path, 'wb') as f: f.write(self.encode())
    return Result()


def demo_flick_test():
    """Horizontal flick demo with notch stops."""
    rc = RemoteComposeWriter(500, 500, "sd", api_level=6)

    def content():
        rc.start_canvas(RecordingModifier().fill_max_size())
        w = rc.add_component_width_value()
        h = rc.add_component_height_value()
        rc.draw_rect(0, 0, w, h)
        rc.rc_paint.set_color(0xFF888888).commit()
        cx = rc.float_expression(w, 0.5, FE.MUL)
        cy = rc.float_expression(h, 0.5, FE.MUL)

        top = 20.0
        bottom = rc.float_expression(h, 20, FE.SUB)
        left = rc.float_expression(cx, 15.0, FE.SUB)
        right = rc.float_expression(cy, 15.0, FE.ADD)
        rc.rc_paint.set_color(0xFF888888).commit()
        rc.draw_round_rect(left, top, right, bottom, 2.0, 2.0)
        clicks = 5
        rc.rc_paint.set_color(0xFF444444).commit()
        for i in range(clicks + 1):
            t1 = rc.float_expression(
                bottom, top, _f32(i / clicks),
                FE.LERP, 2, FE.SUB)
            t2 = rc.float_expression(
                bottom, top, _f32(i / clicks),
                FE.LERP, 2, FE.ADD)
            rc.draw_round_rect(left, t1, right, t2, 2.0, 2.0)

        y_pos = rc.add_touch(
            top, top, bottom,
            Rc.Touch.STOP_NOTCHES_EVEN, 0.0, 0,
            [float(clicks)], None,
            TOUCH_Y, 1, FE.MUL)

        rc.rc_paint.set_color(0xFF00FF00).set_text_size(64.0).commit()
        rc.draw_text_anchored(
            rc.create_text_from_float(y_pos, 3, 1, 0),
            0, 0, -1, 1, 0)

        rc.draw_circle(cx, y_pos, 20)
        rc.end_canvas()

    rc.root(content)
    return _make_result(rc)

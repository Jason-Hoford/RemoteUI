"""Touch demos. Port of DemoTouch.kt demoTouch1, demoTouch2.

Generates: touch1.rc, touch2.rc
"""
import sys
import os
import struct

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RemoteComposeWriter, Rc, as_nan
from rcreate.modifiers import RecordingModifier
from rcreate.types.nan_utils import id_from_nan

FE = Rc.FloatExpression
TOUCH_X = Rc.Touch.POSITION_X
TOUCH_Y = Rc.Touch.POSITION_Y

# Android Color constants
BLACK = 0xFF000000
BLUE = 0xFF0000FF
RED = 0xFFFF0000
GRAY = 0xFF888888
WHITE = 0xFFFFFFFF


def _make_result(rc):
    class Result:
        def encode(self): return rc.encode_to_byte_array()
        def save(self, path):
            with open(path, 'wb') as f: f.write(self.encode())
    return Result()


def demo_touch1():
    """Horizontal slider with touch interaction."""
    rc = RemoteComposeWriter(300, 300, "Clock", api_level=6, legacy_header=True)

    def content():
        rc.start_box(RecordingModifier().fill_max_width().fill_max_height(),
                      Rc.Layout.START, Rc.Layout.START)
        rc.start_canvas(RecordingModifier().fill_max_size())

        rc.rc_paint.set_color(BLUE).commit()
        w = rc.add_component_width_value()
        h = rc.add_component_height_value()
        rc.draw_rect(0, 0, w, h)
        rc.rc_paint.set_color(RED).commit()
        cx = rc.float_expression(w, 0.5, FE.MUL)
        cy = rc.float_expression(h, 0.5, FE.MUL)

        top = rc.float_expression(cy, 10, FE.SUB)
        bottom = rc.float_expression(cy, 10, FE.ADD)
        left = 20.0
        right = rc.float_expression(w, 20, FE.SUB)
        slider_size = rc.float_expression(bottom, top, FE.SUB)
        pos = rc.add_touch(
            cx, left, right,
            Rc.Touch.STOP_INSTANTLY, 0.0, 0,
            None, None,
            TOUCH_X, 1.0, FE.MUL)
        rc.add_debug_message(">>>>> [" + str(id_from_nan(pos)) + "]", pos)
        left_slider = rc.float_expression(pos, 20, FE.SUB)
        right_slider = rc.float_expression(pos, 20, FE.ADD)
        top_slider = rc.float_expression(top, 20, FE.SUB)
        bottom_slider = rc.float_expression(bottom, 20, FE.ADD)
        id_w = rc.create_text_from_float(w, 3, 2, 0)
        id_h = rc.create_text_from_float(h, 3, 2, 0)
        space = rc.text_create_id(" . ")
        text_id = rc.text_merge(id_w, rc.text_merge(space, id_h))
        rc.rc_paint.set_color(BLACK).set_text_size(64).commit()

        rc.rc_paint.set_color(GRAY).commit()
        rc.draw_round_rect(left, top, right, bottom, 20, 20)
        rc.rc_paint.set_color(RED).commit()
        rc.draw_round_rect(left_slider, top_slider, right_slider,
                           bottom_slider, 40, 40)
        value = rc.float_expression(
            pos, 20, FE.SUB, h, 40, FE.SUB, FE.DIV)
        value_str = rc.create_text_from_float(
            value, 1, 2, Rc.TextFromFloat.PAD_AFTER_ZERO)
        rc.rc_paint.set_color(WHITE).commit()
        rc.draw_text_anchored(
            value_str, pos, cy, 0, -2,
            Rc.TextAnchorMask.MONOSPACE_MEASURE)

        rc.end_canvas()
        rc.end_box()

    rc.root(content)
    return _make_result(rc)


def demo_touch2():
    """Vertical slider with touch interaction."""
    rc = RemoteComposeWriter(300, 300, "Clock", api_level=6, legacy_header=True)

    def content():
        rc.start_box(RecordingModifier().fill_max_width().fill_max_height(),
                      Rc.Layout.START, Rc.Layout.START)
        rc.start_canvas(RecordingModifier().fill_max_size())

        rc.rc_paint.set_color(BLUE).commit()
        w = rc.add_component_width_value()
        h = rc.add_component_height_value()
        rc.draw_rect(0, 0, w, h)
        rc.rc_paint.set_color(RED).commit()
        cx = rc.float_expression(w, 0.5, FE.MUL)
        cy = rc.float_expression(h, 0.5, FE.MUL)

        left = rc.float_expression(cx, 10, FE.SUB)
        right = rc.float_expression(cx, 10, FE.ADD)
        top = 20.0
        bottom = rc.float_expression(h, 20, FE.SUB)
        pos = rc.add_touch(
            cy, top, bottom,
            Rc.Touch.STOP_GENTLY, 0.0, 4,
            None, None,
            TOUCH_Y)
        left_slider = rc.float_expression(left, 20, FE.SUB)
        right_slider = rc.float_expression(right, 20, FE.ADD)
        top_slider = rc.float_expression(pos, 20, FE.SUB)
        bottom_slider = rc.float_expression(pos, 20, FE.ADD)

        id_w = rc.create_text_from_float(w, 3, 2, 0)
        id_h = rc.create_text_from_float(h, 3, 2, 0)
        space = rc.text_create_id(" . ")
        text_id = rc.text_merge(id_w, rc.text_merge(space, id_h))
        rc.rc_paint.set_color(BLACK).set_text_size(64).commit()

        rc.draw_text_anchored(text_id, cx, 0, 0, 1, 0)
        rc.rc_paint.set_color(GRAY).commit()
        rc.draw_round_rect(left, top, right, bottom, 20, 20)
        rc.rc_paint.set_color(RED).commit()
        rc.draw_round_rect(left_slider, top_slider, right_slider,
                           bottom_slider, 40, 40)
        value = rc.float_expression(
            pos, 20, FE.SUB, h, 40, FE.SUB, FE.DIV)
        value_str = rc.create_text_from_float(
            value, 1, 2, Rc.TextFromFloat.PAD_AFTER_ZERO)
        rc.rc_paint.set_color(WHITE).commit()
        rc.draw_text_anchored(
            value_str, cx, pos, 2, 0,
            Rc.TextAnchorMask.MONOSPACE_MEASURE)

        rc.end_canvas()
        rc.end_box()

    rc.root(content)
    return _make_result(rc)

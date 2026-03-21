"""Thumbwheel demos. Port of DemoTouch.kt demoTouchThumbWheel1/2.

Generates: thumb_wheel1.rc, thumb_wheel2.rc
"""
import sys
import os
import math

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RemoteComposeWriter, Rc, as_nan
from rcreate.modifiers import RecordingModifier
from rcreate.types.nan_utils import id_from_nan

FE = Rc.FloatExpression
TOUCH_Y = Rc.Touch.POSITION_Y

TRANSPARENT = 0x00000000
BLUE = 0xFF0000FF
GRAY = 0xFF888888
LTGRAY = 0xFFCCCCCC
BLACK = 0xFF000000
GREEN = 0xFF00FF00

STYLE_STROKE = Rc.Paint.STYLE_STROKE
ID_REFERENCE = 1 << 15


def _make_result(rc):
    class Result:
        def encode(self): return rc.encode_to_byte_array()
        def save(self, path):
            with open(path, 'wb') as f: f.write(self.encode())
    return Result()


def demo_thumb_wheel1():
    """Numeric thumbwheel — port of demoTouchThumbWheel1()."""
    rc = RemoteComposeWriter(300, 300, "Clock", legacy_header=True)

    def content():
        rc.start_box(
            RecordingModifier().fill_max_width().fill_max_height().background(0xFF8899AA),
            Rc.Layout.START, Rc.Layout.START)
        rc.start_canvas(RecordingModifier().fill_max_size())

        w = rc.add_component_width_value()
        h = rc.add_component_height_value()

        cx = rc.float_expression(w, 0.5, FE.MUL)
        cy = rc.float_expression(h, 0.5, FE.MUL)

        touch = rc.add_touch(
            0.0, float('nan'), 360.0,
            Rc.Touch.STOP_NOTCHES_EVEN,
            0.0, 4,
            [10.0],
            rc.easing(10.0, 2.0, 60.0),
            TOUCH_Y, 0.2, FE.MUL)

        rc.rc_paint.set_shader(0).set_color(BLUE).set_text_size(128.0).commit()
        num = rc.float_expression(375.0, touch, FE.SUB, 36.0, FE.DIV)
        text_id = rc.create_text_from_float(num, 1, 0, 0)
        rc.draw_text_anchored(text_id, cx, cy, -6.0, 0.0, 2)

        rc.rc_paint.set_text_size(128.0).set_linear_gradient(
            0.0, 0.0, 0.0, h,
            [TRANSPARENT, 0xFF444444, BLACK, TRANSPARENT],
            positions=[0.0, 0.4, 0.8, 1.0], tile_mode=0).commit()

        index = rc.start_loop_var(0, 1.0, 10.0)
        angle = rc.float_expression(index, 36.0, FE.MUL, touch, FE.ADD, FE.RAD)
        scale = rc.float_expression(angle, FE.COS, 0.0, FE.MAX)
        py = rc.float_expression(angle, FE.SIN, cy, 0.8, FE.MUL, FE.MUL, cy, FE.ADD)
        rc.save()
        rc.scale(1.0, scale, cx, py)
        index_text = rc.create_text_from_float(index, 1, 0, 0)
        rc.draw_text_anchored(index_text, cx, py, 0.0, 0.0, 0)
        rc.restore()

        rc.end_loop()
        rr_top = rc.float_expression(cy, 64.0, FE.SUB)
        rr_bottom = rc.float_expression(cy, 64.0, FE.ADD)
        rc.rc_paint.set_color(GRAY).set_style(STYLE_STROKE).commit()
        rc.draw_round_rect(0.0, rr_top, w, rr_bottom, 60.0, 60.0)
        rc.end_canvas()
        rc.end_box()

    rc.root(content)
    return _make_result(rc)


def demo_thumb_wheel2():
    """Dual dial thumbwheel with string list — port of demoTouchThumbWheel2()."""
    rc = RemoteComposeWriter(300, 300, "Clock", legacy_header=True)

    SPACE_BETWEEN = 6
    TOP = 4
    def content():
        rc.start_row(
            RecordingModifier().fill_max_width().fill_max_height(),
            SPACE_BETWEEN, TOP)
        click_id_ref = _dial1(rc)
        _dial2(rc, click_id_ref)
        rc.end_row()

    rc.root(content)
    return _make_result(rc)


HAPTIC_LABELS = [
    "NO HAPTICS", "LONG PRESS", "VIRTUAL KEY", "KEYBOARD TAP", "CLOCK TICK",
    "CONTEXT CLICK", "KEYBOARD PRESS", "KEYBOARD RELEASE", "VIRTUAL KEY RELEASE",
    "TEXT HANDLE MOVE", "GESTURE START", "GESTURE END", "CONFIRM", "REJECT",
    "TOGGLE ON", "TOGGLE OFF", "THRESHOLD ACTIVATE", "THRESHOLD DEACTIVATE",
    "DRAG START", "SEGMENT TICK", "FREQUENT TICK",
]


def _dial1(rc):
    """Left dial with haptic labels — returns clickIdRef."""
    rc.start_canvas(RecordingModifier().width(600).fill_max_height().background(0xFFAABBCC))
    w = rc.add_component_width_value()
    h = rc.add_component_height_value()
    str_list = rc.add_string_list(*HAPTIC_LABELS)

    cx = rc.float_expression(w, 0.5, FE.MUL)
    cy = rc.float_expression(h, 0.5, FE.MUL)

    count = len(HAPTIC_LABELS)
    touch = rc.add_touch(
        0.0, float('nan'), 360.0,
        Rc.Touch.STOP_NOTCHES_EVEN,
        0.0, 4,
        [float(count)],
        rc.easing(10.0, 2.0, 60.0),
        TOUCH_Y, 0.2, FE.MUL)

    num = rc.float_expression(
        360.0, touch, FE.SUB,
        360.0 / count, FE.DIV, FE.ROUND)
    rc.rc_paint.set_shader(0).set_color(BLUE).set_text_size(128.0).commit()
    num_text = rc.create_text_from_float(num, 2, 0, 0)
    rc.draw_text_anchored(num_text, cx, cy, 0.0, 0.0, 2)

    rc.rc_paint.set_text_size(48.0).set_linear_gradient(
        0.0, 0.0, 0.0, h,
        [TRANSPARENT, 0xFF444444, BLACK, GREEN, GREEN, BLACK, BLACK, TRANSPARENT],
        positions=[0.0, 0.4, 0.45, 0.48, 0.52, 0.53, 0.8, 1.0],
        tile_mode=0).commit()

    index = rc.start_loop_var(0, 1.0, float(count))
    angle = rc.float_expression(
        index, 360.0, float(count), FE.DIV, FE.MUL,
        touch, FE.ADD, FE.RAD)
    scale = rc.float_expression(angle, FE.COS, 0.0, FE.MAX)
    py = rc.float_expression(
        angle, FE.SIN, cy, 0.8, FE.MUL, FE.MUL, cy, FE.ADD)
    text_id = rc.text_lookup(str_list, index)
    rc.save()
    rc.scale(1.0, scale, cx, py)
    rc.draw_text_anchored(text_id, cx, py, 0.0, 0.0, 0)
    rc.restore()

    rc.end_loop()
    rc.rc_paint.set_shader(0).commit()

    rc.end_canvas()
    return id_from_nan(num)


def _dial2(rc, click_id_ref):
    """Right dial with numeric display linked to left dial."""
    rc.start_canvas(RecordingModifier().width(200).fill_max_height().background(LTGRAY))
    w = rc.add_component_width_value()
    h = rc.add_component_height_value()

    cx = rc.float_expression(w, 0.5, FE.MUL)
    cy = rc.float_expression(h, 0.5, FE.MUL)

    touch = rc.add_touch(
        0.0, float('nan'), 360.0,
        Rc.Touch.STOP_NOTCHES_EVEN,
        0.0, click_id_ref | ID_REFERENCE,
        [10.0],
        rc.easing(10.0, 2.0, 60.0),
        TOUCH_Y, 0.2, FE.MUL)

    rc.rc_paint.set_text_size(128.0).set_linear_gradient(
        0.0, 0.0, 0.0, h,
        [TRANSPARENT, 0xFF444444, BLACK, TRANSPARENT],
        positions=[0.0, 0.4, 0.8, 1.0],
        tile_mode=0).commit()

    index = rc.start_loop_var(0, 1.0, 10.0)
    angle = rc.float_expression(index, 36.0, FE.MUL, touch, FE.ADD, FE.RAD)
    scale = rc.float_expression(angle, FE.COS, 0.0, FE.MAX)
    py = rc.float_expression(
        angle, FE.SIN, cy, 0.8, FE.MUL, FE.MUL, cy, FE.ADD)
    rc.save()
    rc.scale(1.0, scale, cx, py)
    index_text = rc.create_text_from_float(index, 1, 0, 0)
    rc.draw_text_anchored(index_text, cx, py, 0.0, 0.0, 0)
    rc.restore()

    rc.end_loop()
    rc.rc_paint.set_shader(0).commit()

    rc.end_canvas()

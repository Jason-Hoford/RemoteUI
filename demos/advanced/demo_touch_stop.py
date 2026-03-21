"""Touch stop-mode demos and touch_wrap. Port of DemoTouch.kt demoTouch3, touchStop*, demoTouchWrap.

Generates: stop_instantly.rc, stop_gently.rc, stop_ends.rc, stop_absolute_pos.rc,
           stop_notches_even.rc, stop_notches_percents.rc, stop_notches_absolute.rc,
           touch_wrap.rc
"""
import sys
import os
import struct
import math

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RemoteComposeWriter, Rc, as_nan
from rcreate.modifiers import RecordingModifier
from rcreate.types.nan_utils import id_from_nan

FE = Rc.FloatExpression
CS = Rc.Time.CONTINUOUS_SEC
TOUCH_X = Rc.Touch.POSITION_X
TOUCH_Y = Rc.Touch.POSITION_Y

BLACK = 0xFF000000
BLUE = 0xFF0000FF
RED = 0xFFFF0000
GRAY = 0xFF888888
WHITE = 0xFFFFFFFF
YELLOW = 0xFFFFFF00
CYAN = 0xFF00FFFF

STYLE_STROKE = Rc.Paint.STYLE_STROKE
STYLE_FILL = Rc.Paint.STYLE_FILL
CAP_ROUND = Rc.Paint.CAP_ROUND


def _f32(v):
    return struct.unpack('>f', struct.pack('>f', v))[0]


def _make_result(rc):
    class Result:
        def encode(self): return rc.encode_to_byte_array()
        def save(self, path):
            with open(path, 'wb') as f: f.write(self.encode())
    return Result()


def _demo_touch3(mode, spec, title):
    """Shared implementation for all stop-mode demos (demoTouch3 in Kotlin)."""
    rc = RemoteComposeWriter(300, 300, "demoTouch", api_level=6, legacy_header=True)

    def content():
        rc.start_box(
            RecordingModifier().fill_max_width().fill_max_height().background(0xFFAAAAAA),
            Rc.Layout.START, Rc.Layout.START)
        rc.start_canvas(
            RecordingModifier().fill_max_size().background(0xFFAA9988))

        anim = rc.float_expression(CS, 2, FE.MOD, 1, FE.SUB)

        rc.rc_paint.set_color(BLUE).commit()
        w = rc.add_component_width_value()
        h = rc.add_component_height_value()
        rc.draw_round_rect(0, 0, w, h, 60, 60)

        rc.rc_paint.set_color(RED).commit()
        cx = rc.float_expression(w, 0.5, FE.MUL)
        cy = rc.float_expression(h, 0.5, FE.MUL)

        rc.save()
        rc.scale(anim, 1, cx, cy)
        rc.rc_paint.set_color(GRAY).set_text_size(64).commit()
        rc.restore()

        # track
        rad = rc.float_expression(w, h, FE.MIN, 2, FE.DIV, 30, FE.SUB)
        left = rc.float_expression(cx, rad, FE.SUB)
        right = rc.float_expression(cx, rad, FE.ADD)
        top = rc.float_expression(cy, rad, FE.SUB)
        bottom = rc.float_expression(cy, rad, FE.ADD)
        rc.rc_paint.set_style(STYLE_STROKE).set_stroke_width(20).set_stroke_cap(CAP_ROUND).commit()
        rc.draw_arc(left, top, right, bottom, 120, 300)
        rc.rc_paint.set_stroke_width(5).commit()
        line = rc.float_expression(h, 40, FE.SUB)

        if spec is not None:
            if mode == Rc.Touch.STOP_NOTCHES_EVEN:
                angle = 30.0
                while angle <= 330:
                    rc.save()
                    rc.rotate(angle, cx, cy)
                    rc.draw_line(cx, h, cx, line)
                    rc.restore()
                    angle += (330 - 30) / spec[0]
            elif mode == Rc.Touch.STOP_NOTCHES_PERCENTS:
                for p in spec:
                    angle = _f32(_f32(p * (330 - 30)) + 30)
                    rc.save()
                    rc.rotate(angle, cx, cy)
                    rc.draw_line(cx, h, cx, line)
                    rc.restore()
            elif mode == Rc.Touch.STOP_NOTCHES_ABSOLUTE:
                for angle in spec:
                    rc.save()
                    rc.rotate(angle, cx, cy)
                    rc.draw_line(cx, h, cx, line)
                    rc.restore()
            elif mode == Rc.Touch.STOP_ENDS:
                for i in range(2):
                    angle = float(30 + (330 - 30) * i)
                    rc.save()
                    rc.rotate(angle, cx, cy)
                    rc.draw_line(cx, h, cx, line)
                    rc.restore()

        # NOTCH
        tx = TOUCH_X
        ty = TOUCH_Y
        atan_scale = _f32(-180 / _f32(3.141))

        pos = rc.add_touch(
            180, 30, 330, mode, 0.0, 4,
            spec, None,
            tx, cx, FE.SUB,
            ty, cy, FE.SUB,
            FE.ATAN2,
            atan_scale, FE.MUL,
            360, FE.ADD,
            360, FE.MOD)

        rc.rc_paint.set_color(RED).set_style(STYLE_FILL).set_stroke_width(0).commit()

        rc.save()
        rc.rotate(pos, cx, cy)
        rc.draw_circle(cx, bottom, 20)
        rc.restore()

        # Label
        value = rc.float_expression(pos, 30, FE.SUB, 300, FE.DIV)
        value_str = rc.create_text_from_float(
            value, 1, 2, Rc.TextFromFloat.PAD_AFTER_ZERO)
        rc.rc_paint.set_color(WHITE).commit()
        rc.draw_text_anchored(
            value_str, cx, cy, 0, 0,
            Rc.TextAnchorMask.MONOSPACE_MEASURE)

        display_title = title if title is not None else "NULL"
        rc.rc_paint.set_color(YELLOW).set_text_size(32).commit()
        rc.draw_text_anchored(
            display_title, cx, cy, 0, 6,
            Rc.TextAnchorMask.MONOSPACE_MEASURE)

        rc.end_canvas()
        rc.end_box()

    rc.root(content)
    return _make_result(rc)


def demo_stop_instantly():
    return _demo_touch3(Rc.Touch.STOP_INSTANTLY, None, "STOP_INSTANTLY")


def demo_stop_gently():
    return _demo_touch3(Rc.Touch.STOP_GENTLY, None, "STOP_GENTLY")


def demo_stop_ends():
    return _demo_touch3(Rc.Touch.STOP_ENDS, None, "STOP_ENDS")


def demo_stop_absolute_pos():
    return _demo_touch3(Rc.Touch.STOP_ABSOLUTE_POS, None, "STOP_ABSOLUTE_POS")


def demo_stop_notches_even():
    return _demo_touch3(Rc.Touch.STOP_NOTCHES_EVEN, [10.0], "STOP_NOTCHES_EVEN")


def demo_stop_notches_percents():
    return _demo_touch3(
        Rc.Touch.STOP_NOTCHES_PERCENTS,
        [0.0, 0.25, _f32(0.33333), 0.5, _f32(0.66666), 0.75, 1.0],
        "STOP_NOTCHES_PERCENTS")


def demo_stop_notches_absolute():
    return _demo_touch3(
        Rc.Touch.STOP_NOTCHES_ABSOLUTE,
        [30.0, 60.0, 180.0, 330.0],
        "STOP_NOTCHES_ABSOLUTE")


def demo_touch_wrap():
    """Touch wrap demo (demoTouchWrap in Kotlin)."""
    mode = Rc.Touch.STOP_NOTCHES_EVEN
    spec = [4.0]
    title = "wrap"
    rc = RemoteComposeWriter(300, 300, "Clock", api_level=6, legacy_header=True)

    def content():
        rc.start_box(
            RecordingModifier().fill_max_width().fill_max_height(),
            Rc.Layout.START, Rc.Layout.START)
        rc.start_canvas(RecordingModifier().fill_max_size())

        anim = rc.float_expression(CS, 2, FE.MOD, 1, FE.SUB)

        rc.rc_paint.set_color(BLUE).commit()
        w = rc.add_component_width_value()
        h = rc.add_component_height_value()
        rc.draw_round_rect(0, 0, w, h, 60, 60)

        rc.rc_paint.set_color(RED).commit()
        cx = rc.float_expression(w, 0.5, FE.MUL)
        cy = rc.float_expression(h, 0.5, FE.MUL)

        rc.save()
        rc.scale(anim, 1, cx, cy)
        rc.rc_paint.set_color(GRAY).set_text_size(64).commit()
        rc.restore()

        # track
        rad = rc.float_expression(w, h, FE.MIN, 2, FE.DIV, 30, FE.SUB)
        left = rc.float_expression(cx, rad, FE.SUB)
        right = rc.float_expression(cx, rad, FE.ADD)
        top = rc.float_expression(cy, rad, FE.SUB)
        bottom = rc.float_expression(cy, rad, FE.ADD)

        # NOTCH
        tx = TOUCH_X
        ty = TOUCH_Y
        atan_scale = _f32(-180 / _f32(3.141))

        pos = rc.add_touch(
            180, float('nan'), 360, mode, 0.0, 4,
            spec, rc.easing(5, 0.2, 1),
            tx, cx, FE.SUB,
            ty, cy, FE.SUB,
            FE.ATAN2,
            atan_scale, FE.MUL,
            360, FE.ADD,
            360, FE.MOD)

        rc.rc_paint.set_color(RED).set_style(STYLE_FILL).set_stroke_width(0).commit()

        rc.save()
        rc.rotate(pos, cx, cy)
        rc.draw_round_rect(left, top, right, bottom, 100, 100)
        rc.rc_paint.set_color(CYAN).set_style(STYLE_STROKE).set_stroke_width(20).commit()
        rc.draw_line(cx, cy, cx, bottom)
        rc.restore()

        # Label
        value_str = rc.create_text_from_float(
            pos, 3, 1, Rc.TextFromFloat.PAD_AFTER_ZERO)
        rc.rc_paint.set_color(WHITE).set_style(STYLE_FILL).set_stroke_width(0).commit()
        rc.draw_text_anchored(
            value_str, cx, cy, 0, 0,
            Rc.TextAnchorMask.MONOSPACE_MEASURE)

        rc.rc_paint.set_color(YELLOW).set_text_size(32).commit()
        rc.draw_text_anchored(
            title, cx, cy, 0, 6,
            Rc.TextAnchorMask.MONOSPACE_MEASURE)

        rc.end_canvas()
        rc.end_box()

    rc.root(content)
    return _make_result(rc)


def demo_simple_java_anim():
    """Simple animation with touch interaction. Port of simpleJavaAnim() in DemoTouch.kt.

    Uses RFloat DSL operators in Kotlin — manually flattened here to match
    the exact materialization order.
    """
    rc = RemoteComposeWriter(300, 300, "Clock", api_level=6, legacy_header=True)

    def content():
        rc.start_box(
            RecordingModifier().fill_max_width().fill_max_height(),
            Rc.Layout.START, Rc.Layout.START)
        rc.start_canvas(RecordingModifier().fill_max_size())

        # ComponentWidth — cached, so all calls return the same NaN ID
        w = rc.add_component_width_value()
        pos = rc.add_touch(
            0, float('nan'), 1, Rc.Touch.STOP_INSTANTLY, 0, 0,
            None, None,
            TOUCH_X, w, FE.DIV)

        # color value expression: abs(sin((pos*2-1) * 3.14 / 2)) * 0.5 + 0.5
        # In Kotlin this is one big lazy RFloat that gets materialized at
        # addColorExpression's .toFloat() call. anim is NOT yet materialized.
        col_val = rc.float_expression(
            pos, 2, FE.MUL, 1, FE.SUB,
            _f32(3.14), FE.MUL, 2, FE.DIV,
            FE.SIN, FE.ABS,
            0.5, FE.MUL, 0.5, FE.ADD)

        col = rc.add_color_expression(0.0, 0.9, col_val)
        rc.rc_paint.set_color_id(col).commit()

        rc.save()

        # anim materialized here (at scale call)
        anim = rc.float_expression(pos, 2, FE.MUL, 1, FE.SUB)
        # cx = w * 0.5, cy = w * 0.5 (both use cached w)
        cx_expr = rc.float_expression(w, 0.5, FE.MUL)
        cy_expr = rc.float_expression(w, 0.5, FE.MUL)

        rc.scale(anim, 1, cx_expr, cy_expr)

        # drawOval uses cached w for both right and bottom
        rc.draw_oval(0, 0, w, w)

        rc.restore()
        rc.end_canvas()
        rc.end_box()

    rc.root(content)
    return _make_result(rc)

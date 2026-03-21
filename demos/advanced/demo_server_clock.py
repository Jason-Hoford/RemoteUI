"""Server-side clock demo. Port of ServerSide.kt serverClock().

Generates: server_clock.rc

The Kotlin DSL uses lazy RFloat expression trees that get flattened when
.toFloat() is called. Expressions that haven't been materialized yet get
inlined into parent expressions; already-materialized ones use their NaN ID.
This demo replicates that exact materialization order.
"""
import sys
import os
import math
import struct

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RemoteComposeWriter, Rc, as_nan
from rcreate.modifiers import RecordingModifier

FE = Rc.FloatExpression
CS = Rc.Time.CONTINUOUS_SEC
MINUTES = Rc.Time.TIME_IN_MIN
HOUR = Rc.Time.TIME_IN_HR

BLUE = 0xFF0000FF
GRAY = 0xFF888888
LTGRAY = 0xFFCCCCCC
WHITE = 0xFFFFFFFF
CAP_ROUND = Rc.Paint.CAP_ROUND


def _f32(v):
    """Round to float32 precision (matches Java float arithmetic)."""
    return struct.unpack('>f', struct.pack('>f', v))[0]


def _make_result(rc):
    class Result:
        def encode(self): return rc.encode_to_byte_array()
        def save(self, path):
            with open(path, 'wb') as f: f.write(self.encode())
    return Result()


def demo_server_clock():
    """Analog clock with minute, hour, and second hands.

    Matches Kotlin lazy materialization order:
    - w, h are leaf RFloats (component values) — used directly by NaN ID
    - cx, cy, rad are lazy RFloats — NOT materialized until first .toFloat()
    - rounding materializes before drawRoundRect (inlines cx/cy/rad since
      they haven't been materialized yet)
    - cx, cy materialize for rotate() call (after minute-hand paint)
    - rad is NEVER separately materialized — always inlined
    - sec_x/sec_y build fresh w/2, h/2, rad expressions (not referencing cx/cy)
    """
    rc = RemoteComposeWriter(500, 500, "Clock", api_level=6)

    def content():
        rc.start_box(RecordingModifier().fill_max_size(),
                      Rc.Layout.START, Rc.Layout.START)
        rc.start_canvas(RecordingModifier().fill_max_size())

        w = rc.add_component_width_value()
        h = rc.add_component_height_value()

        # Background — paint BEFORE any float expressions (Kotlin order)
        rc.rc_paint.set_color(BLUE).commit()

        # rounding = min(w/2, h/2) / 4 — single combined expression
        # (cx, cy, rad not yet materialized → all inlined)
        rounding = rc.float_expression(w, 2, FE.DIV, h, 2, FE.DIV, FE.MIN,
                                        4, FE.DIV)
        rc.draw_round_rect(0, 0, w, h, rounding, rounding)

        # Minute hand
        rc.rc_paint.set_color(GRAY).set_stroke_width(32).set_stroke_cap(
            CAP_ROUND).commit()
        rc.save()
        min_angle = rc.float_expression(MINUTES, 6, FE.MUL)
        # cx and cy are materialized HERE for the rotate() call
        cx = rc.float_expression(w, 2, FE.DIV)
        cy = rc.float_expression(h, 2, FE.DIV)
        rc.rotate(min_angle, cx, cy)
        # min_end = cy - min(w/2, h/2) * 0.8
        # cy is materialized (uses NaN ID), rad is NOT (inlined)
        min_end = rc.float_expression(cy,
                                       w, 2, FE.DIV, h, 2, FE.DIV, FE.MIN,
                                       0.8, FE.MUL, FE.SUB)
        rc.draw_line(cx, cy, cx, min_end)
        rc.restore()

        # Hour hand
        rc.rc_paint.set_color(LTGRAY).set_stroke_width(16).set_stroke_cap(
            CAP_ROUND).commit()
        rc.save()
        hr_angle = rc.float_expression(HOUR, 30, FE.MUL)
        rc.rotate(hr_angle, cx, cy)
        # hr_end = cy - min(w/2, h/2) / 2
        hr_end = rc.float_expression(cy,
                                      w, 2, FE.DIV, h, 2, FE.DIV, FE.MIN,
                                      2, FE.DIV, FE.SUB)
        rc.draw_line(cx, cy, cx, hr_end)
        rc.restore()

        # Second hand
        # Java: 2 * Math.PI.toFloat() / 60f — float32 constant
        pi2_60 = _f32(2.0 * _f32(math.pi) / 60.0)
        rc.rc_paint.set_color(WHITE).set_stroke_width(4).commit()
        # sec_x = w/2 + min(w/2, h/2) * sin(CS * pi2_60)
        # In Kotlin, this creates a FRESH w/2f (not referencing cx), and
        # inlines rad since it was never separately materialized.
        sec_x = rc.float_expression(w, 2, FE.DIV,
                                     w, 2, FE.DIV, h, 2, FE.DIV, FE.MIN,
                                     CS, pi2_60, FE.MUL, FE.SIN,
                                     FE.MUL, FE.ADD)
        # sec_y = h/2 - min(w/2, h/2) * cos(CS * pi2_60)
        sec_y = rc.float_expression(h, 2, FE.DIV,
                                     w, 2, FE.DIV, h, 2, FE.DIV, FE.MIN,
                                     CS, pi2_60, FE.MUL, FE.COS,
                                     FE.MUL, FE.SUB)
        rc.draw_line(cx, cy, sec_x, sec_y)

        rc.end_canvas()
        rc.end_box()

    rc.root(content)
    return _make_result(rc)

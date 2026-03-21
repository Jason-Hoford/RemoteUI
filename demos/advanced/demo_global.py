"""Global sections demo. Port of DemoGlobal.kt / demoUseOfGlobal().

Demonstrates:
- beginGlobal/endGlobal for pre-computed time-based text
- Multiple global sections
- createTextFromFloat with time variables
- textMerge for composing clock text
- Canvas with gradients, drawSector, drawLine, matrix transforms
- setRadialGradient, setSweepGradient, setShader(0)
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import math
from rcreate import RcContext, Modifier, Rc
from rcreate.modifiers import RoundedRectShape

MOD = Rc.FloatExpression.MOD
SUB = Rc.FloatExpression.SUB
MUL = Rc.FloatExpression.MUL
DIV = Rc.FloatExpression.DIV
MIN = Rc.FloatExpression.MIN
SIN = Rc.FloatExpression.SIN
COS = Rc.FloatExpression.COS
HYPOT = Rc.FloatExpression.HYPOT
ADD = Rc.FloatExpression.ADD

WHITE = 0xFFFFFFFF
BLACK = 0xFF000000
GRAY = 0xFF888888
LTGRAY = 0xFFCCCCCC
DKGRAY = 0xFF444444


def demo_global():
    ctx = RcContext(500, 500, "DemoGlobal", api_level=6)

    with ctx.root():
        with ctx.column():
            # ── Clock face ──
            with ctx.box(Modifier().width(500).height(500)
                         .clip(RoundedRectShape(30.0, 30.0, 30.0, 30.0))):
                with ctx.canvas(Modifier().fill_max_size()):
                    w = ctx.component_width()
                    h = ctx.component_height()
                    cx = ctx.float_expression(w, 2.0, DIV)
                    cy = ctx.float_expression(h, 2.0, DIV)
                    rad = ctx.float_expression(cx, cy, MIN)
                    rad2 = ctx.float_expression(cx, cy, HYPOT)

                    # Gradient background
                    ctx.painter.set_radial_gradient(
                        cx, cy, rad2,
                        [LTGRAY, DKGRAY],
                        [0.0, 2.0], 0).commit()
                    ctx.draw_round_rect(0, 0, w, h,
                                        ctx.float_expression(rad, 4.0, DIV),
                                        ctx.float_expression(rad, 4.0, DIV))

                    # Sweeping sector
                    ctx.painter.set_color(0x99888888).set_shader(0) \
                        .set_stroke_width(32.0).set_stroke_cap(1).commit()
                    rad_neg = ctx.float_expression(rad, -1.0, MUL)
                    w_plus_rad = ctx.float_expression(w, rad, ADD)
                    h_plus_rad = ctx.float_expression(h, rad, ADD)
                    sweep = ctx.float_expression(
                        Rc.Time.CONTINUOUS_SEC, 360.0, MUL, 360.0, MOD)
                    ctx.draw_sector(rad_neg, rad_neg, w_plus_rad, h_plus_rad,
                                    -90.0, sweep)

                    # Countdown digit
                    ctx.painter.set_color(BLACK).set_text_size(512.0).commit()
                    countdown = ctx.float_expression(
                        Rc.Time.CONTINUOUS_SEC, 10.0, MOD, -1.0, MUL, 9.999, ADD)
                    tid = ctx.create_text_from_float(countdown, 1, 0, 0)
                    ctx.canvas_save()
                    sec_mod = ctx.float_expression(
                        Rc.Time.CONTINUOUS_SEC, 1.0, MOD)
                    ctx.scale(sec_mod, sec_mod, cx, cy)
                    ctx.draw_text_anchored(tid, cx, cy, 0.0, 0.0, 0)
                    ctx.canvas_restore()

                    # Second hand line
                    pi2 = 2.0 * math.pi
                    ctx.painter.set_color(WHITE).set_stroke_width(4.0).commit()
                    sin_x = ctx.float_expression(
                        Rc.Time.CONTINUOUS_SEC, pi2, MUL, SIN, rad, MUL)
                    cos_y = ctx.float_expression(
                        Rc.Time.CONTINUOUS_SEC, pi2, MUL, COS, rad, MUL)
                    line_x = ctx.float_expression(cx, sin_x, ADD)
                    line_y = ctx.float_expression(cy, cos_y, SUB)
                    ctx.draw_line(cx, cy, line_x, line_y)

            # ── Digital clock section ──
            with ctx.box(Modifier().width(500).height(120)):
                ctx.begin_global()
                space = ctx.add_text(":")
                sec_val = ctx.float_expression(
                    Rc.Time.TIME_IN_SEC, 60.0, MOD)
                tid1 = ctx.create_text_from_float(
                    sec_val, 2, 0, Rc.TextFromFloat.PAD_PRE_ZERO)
                min_val = ctx.float_expression(
                    Rc.Time.TIME_IN_MIN, 60.0, MOD)
                tid2 = ctx.create_text_from_float(
                    min_val, 2, 0, Rc.TextFromFloat.PAD_PRE_ZERO)
                ctx.end_global()
                ctx.begin_global()
                hr_val = ctx.float_expression(
                    Rc.Time.TIME_IN_HR, 12.0, MOD)
                tid3 = ctx.create_text_from_float(hr_val, 2, 0, 0)
                clock = ctx.text_merge(tid3, space, tid2, space, tid1)
                ctx.end_global()
                ctx.text_by_id(clock,
                               Modifier().fill_max_size().background(0xFF99FFFF),
                               font_size=100.0)

    return ctx


if __name__ == '__main__':
    ctx = demo_global()
    data = ctx.encode()
    print(f"DemoGlobal: {len(data)} bytes")
    ctx.save("demo_global.rc")
    print("Saved demo_global.rc")

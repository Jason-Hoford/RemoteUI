"""Port of DemoGlobal.kt / demoUseOfGlobal().

Demonstrates:
- beginGlobal/endGlobal for pre-computed time-based text
- Multiple global sections
- createTextFromFloat with time variables
- textMerge for composing clock text
- Canvas with gradients, drawSector, drawLine, matrix transforms
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import math
from rcreate import RcContext, Modifier, Rc
from rcreate.modifiers import RoundedRectShape
from rcreate.types.rfloat import rf_min, rf_hypot, rf_sin, rf_cos

# Android Color constants
LTGRAY = 0xFFCCCCCC
DKGRAY = 0xFF444444
BLACK = 0xFF000000
WHITE = 0xFFFFFFFF

# Float precision of Math.PI.toFloat() in Java/Kotlin
PI_F = 3.1415927410125732


def clock(ctx):
    """Clock face with animated second hand and countdown digit."""
    with ctx.box(Modifier().width(500).height(500)
                 .clip(RoundedRectShape(30.0, 30.0, 30.0, 30.0)),
                 horizontal=Rc.Layout.START, vertical=Rc.Layout.START):
        with ctx.canvas(Modifier().fill_max_size()):
            w = ctx.ComponentWidth()
            h = ctx.ComponentHeight()
            cx = w / 2.0
            cy = h / 2.0
            rad = rf_min(cx, cy)
            rad2 = rf_hypot(cx, cy)

            # Gradient background
            ctx.painter.set_radial_gradient(
                cx.to_float(),
                cy.to_float(),
                rad2.to_float(),
                [LTGRAY, DKGRAY],
                [0.0, 2.0],
                0,  # CLAMP
            ).commit()

            ctx.draw_round_rect(0, 0, w.to_float(), h.to_float(),
                                (rad / 4.0).to_float(),
                                (rad / 4.0).to_float())

            # Sweeping sector
            ctx.painter.set_color(0x99888888).set_shader(0) \
                .set_stroke_width(32.0).set_stroke_cap(1).commit()
            # Kotlin evaluates rad*-1f twice as separate expressions
            rad_neg1 = (rad * -1.0).to_float()
            rad_neg2 = (rad * -1.0).to_float()
            w_plus_rad = (w + rad).to_float()
            h_plus_rad = (h + rad).to_float()
            csec = ctx.ContinuousSec()
            sweep = ((csec * 360.0) % 360.0).to_float()
            ctx.draw_sector(rad_neg1, rad_neg2, w_plus_rad, h_plus_rad,
                            -90.0, sweep)

            # Countdown digit
            ctx.painter.set_color(BLACK).set_text_size(512.0).commit()
            csec2 = ctx.ContinuousSec()
            countdown = ((csec2 % 10.0) * -1.0 + 9.999).to_float()
            tid = ctx.create_text_from_float(countdown, 1, 0, 0)
            ctx.canvas_save()
            csec3 = ctx.ContinuousSec()
            sec_mod1 = (csec3 % 1.0).to_float()
            csec4 = ctx.ContinuousSec()
            sec_mod2 = (csec4 % 1.0).to_float()
            # NOTE: Kotlin bug on line 158 of RemoteComposeContextAndroid.kt:
            # scale(sx, sy, centerX, centerY) calls scale(sx, sy, centerX, centerX)
            # i.e. centerX is used for both cx and cy parameters
            ctx.scale(sec_mod1, sec_mod2, cx.to_float(), cx.to_float())
            ctx.draw_text_anchored(tid, cx.to_float(), cy.to_float(), 0.0, 0.0, 0)
            ctx.canvas_restore()

            # Second hand line
            ctx.painter.set_color(WHITE).set_stroke_width(4.0).commit()
            csec5 = ctx.ContinuousSec()
            two_pi = 2.0 * PI_F
            sin_val = rf_sin(csec5 * two_pi)
            line_x = (w / 2.0 + rad * sin_val).to_float()
            csec6 = ctx.ContinuousSec()
            cos_val = rf_cos(csec6 * two_pi)
            line_y = (h / 2.0 - rad * cos_val).to_float()
            ctx.draw_line(cx.to_float(), cy.to_float(), line_x, line_y)


def date(ctx):
    """Digital clock section using global sections."""
    with ctx.box(Modifier().width(500).height(120),
                 horizontal=Rc.Layout.START, vertical=Rc.Layout.START):
        ctx.begin_global()
        space = ctx.add_text(":")
        sec_expr = (ctx.Seconds() % 60.0).to_float()
        tid1 = ctx.create_text_from_float(
            sec_expr, 2, 0, Rc.TextFromFloat.PAD_PRE_ZERO)
        min_expr = (ctx.Minutes() % 60.0).to_float()
        tid2 = ctx.create_text_from_float(
            min_expr, 2, 0, Rc.TextFromFloat.PAD_PRE_ZERO)
        ctx.end_global()
        ctx.begin_global()  # to prove we can have multiple sections
        hr_expr = (ctx.Hour() % 12.0).to_float()
        tid3 = ctx.create_text_from_float(hr_expr, 2, 0, 0)
        clock_id = ctx.text_merge(tid3, space, tid2, space, tid1)
        ctx.end_global()
        ctx.text_by_id(clock_id,
                       Modifier().fill_max_size().background(0xFF99FFFF),
                       font_size=100.0)


def demo_use_of_global():
    ctx = RcContext(500, 500, "Simple Timer", api_level=6, profiles=0)

    with ctx.root():
        with ctx.column():
            clock(ctx)
            date(ctx)

    return ctx


if __name__ == '__main__':
    ctx = demo_use_of_global()
    data = ctx.encode()
    print(f"DemoUseOfGlobal: {len(data)} bytes")

    # Compare with reference
    ref_path = os.path.join(os.path.dirname(__file__), '..', '..',
                            'integration-tests', 'player-view-demos',
                            'src', 'main', 'res', 'raw',
                            'demo_use_of_global.rc')
    if os.path.exists(ref_path):
        with open(ref_path, 'rb') as f:
            ref = f.read()
        if data == ref:
            print("MATCH: byte-identical to reference")
        else:
            print(f"MISMATCH: generated {len(data)} bytes, reference {len(ref)} bytes")
            for i in range(min(len(data), len(ref))):
                if data[i] != ref[i]:
                    print(f"First diff at byte {i}: gen=0x{data[i]:02x} ref=0x{ref[i]:02x}")
                    break

    ctx.save("demo_use_of_global.rc")
    print("Saved demo_use_of_global.rc")

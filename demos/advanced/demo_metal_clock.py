"""Metal clock demo. Port of DemoMetalClock.kt / fancyClock2().

Demonstrates:
- Complex expression chains (POW, LN, COS, SIN, ABS)
- Squircle path generation via loop + expressions
- addClipPath for custom clip shapes
- setSweepGradient for metallic appearance
- Conditional drawing (conditionalOperations)
- createTextFromFloat with hour markers
- Loop-based tick marks with polar coordinates
- Clock hands with time variables
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import math
from rcreate import RcContext, Modifier, Rc
from rcreate.types.nan_utils import id_from_nan

MOD = Rc.FloatExpression.MOD
SUB = Rc.FloatExpression.SUB
MUL = Rc.FloatExpression.MUL
DIV = Rc.FloatExpression.DIV
MIN = Rc.FloatExpression.MIN
ADD = Rc.FloatExpression.ADD
ABS = Rc.FloatExpression.ABS
POW = Rc.FloatExpression.POW
LN = Rc.FloatExpression.LN
SIN = Rc.FloatExpression.SIN
COS = Rc.FloatExpression.COS
ROUND = Rc.FloatExpression.ROUND

WHITE = 0xFFFFFFFF
BLACK = 0xFF000000
GRAY = 0xFF888888
LTGRAY = 0xFFCCCCCC
RED = 0xFFFF0000

# Squircle metal gradient colors (Kotlin negative hex to ARGB)
METAL1 = 0xFF4E6588  # -0xb19a78
METAL2 = 0xFF182947  # -0xe7d6b9
METAL_ALPHA1 = 0x804E6588  # -0x7fb19a78
METAL_ALPHA2 = 0x80182947  # -0x7fe7d6b9


def gen_squircle_path(ctx, center_x, center_y, rad1, rad2):
    """Generate a squircle clip path."""
    second = ctx.create_float_id()

    SQRT2 = 1.4142135623730951
    pi = math.pi

    # n = 1 / (0.5 - Log2(SQRT2 + (rad2/rad1) * (1 - SQRT2)))
    n = ctx.float_expression(
        1.0, 0.5, SQRT2, rad2, rad1, DIV, 1.0, SQRT2, SUB,
        MUL, ADD, LN, 2.0, LN, DIV, SUB, DIV)
    n_inv = ctx.float_expression(1.0, n, DIV)

    # Initial path point at top
    start_y = ctx.float_expression(center_y, rad1, SUB)
    pid = ctx.path_create(center_x, start_y)

    # Loop to generate squircle outline
    idx_id = id_from_nan(second)
    ctx.loop(idx_id, 0.0, 0.2, 60.0)

    ang = ctx.float_expression(second, 2.0 * pi / 60.0, MUL, pi / 2.0, SUB)
    cos_ang = ctx.float_expression(ang, COS)
    sin_ang = ctx.float_expression(ang, SIN)
    cos4 = ctx.float_expression(cos_ang, ABS, n, POW)
    sin4 = ctx.float_expression(sin_ang, ABS, n, POW)

    polar_r = ctx.float_expression(rad1, cos4, sin4, ADD, ABS, n_inv, POW, DIV)
    offset_x = ctx.float_expression(polar_r, cos_ang, MUL, center_x, ADD)
    offset_y = ctx.float_expression(polar_r, sin_ang, MUL, center_y, ADD)
    ctx.path_append_line_to(pid, offset_x, offset_y)

    ctx.end_loop()
    ctx.path_append_close(pid)
    return pid


def draw_ticks(ctx, center_x, center_y, rad1, rad2):
    """Draw tick marks using loop + conditionals."""
    second = ctx.create_float_id()
    pi = math.pi

    ctx.painter.set_color(LTGRAY).set_text_size(80.0).commit()

    # Compute squircle exponent
    SQRT2 = 1.4142135
    n = ctx.float_expression(
        1.0, 0.5, SQRT2, rad2, rad1, DIV, 1.0, SQRT2, SUB,
        MUL, ADD, LN, 2.0, LN, DIV, SUB, DIV)
    n_inv = ctx.float_expression(1.0, n, DIV)

    idx_id = id_from_nan(second)
    ctx.loop(idx_id, 0.0, 1.0, 60.0)

    ang = ctx.float_expression(second, 2.0 * pi / 60.0, MUL, pi / 2.0, SUB)
    ang_deg = ctx.float_expression(second, 6.0, MUL)
    cos_ang = ctx.float_expression(ang, COS)
    sin_ang = ctx.float_expression(ang, SIN)
    cos4 = ctx.float_expression(cos_ang, ABS, n, POW)
    sin4 = ctx.float_expression(sin_ang, ABS, n, POW)

    polar_r = ctx.float_expression(rad1, cos4, sin4, ADD, ABS, n_inv, POW, DIV)
    offset_x = ctx.float_expression(polar_r, cos_ang, MUL, center_x, ADD)
    offset_y = ctx.float_expression(polar_r, sin_ang, MUL, center_y, ADD)

    ctx.canvas_save()
    ctx.rotate(ang_deg, offset_x, offset_y)
    pos_y = ctx.float_expression(offset_y, 6.0, ADD)
    ctx.scale(0.5, 2.0, offset_x, offset_y)
    ctx.draw_circle(offset_x, pos_y, 6.0)

    # Larger tick at every 5th mark
    ctx.conditional_operations(
        Rc.Condition.EQ, 0.0,
        ctx.float_expression(second, 5.0, MOD))
    ctx.painter.set_color(WHITE).commit()
    ctx.draw_circle(offset_x, pos_y, 10.0)
    ctx.painter.set_color(LTGRAY).commit()
    ctx.end_conditional_operations()

    ctx.canvas_restore()

    # Hour numbers at every 15th mark
    ctx.conditional_operations(
        Rc.Condition.EQ, 0.0,
        ctx.float_expression(second, 15.0, MOD))
    inset = 70.0
    txt_x = ctx.float_expression(polar_r, inset, SUB, cos_ang, MUL, center_x, ADD)
    txt_y = ctx.float_expression(polar_r, inset, SUB, sin_ang, MUL, center_y, ADD)
    hr = ctx.float_expression(
        second, 15.0, DIV, 3.0, ADD, 4.0, MOD, 1.0, ADD, 3.0, MUL, ROUND)
    tid = ctx.create_text_from_float(hr, 2, 0, 0)
    ctx.draw_text_anchored(tid, txt_x, txt_y, 0.0, 0.0, 0)
    ctx.end_conditional_operations()

    ctx.end_loop()


def draw_clock_hands(ctx, center_x, center_y):
    """Draw hour, minute, and second hands."""
    second_angle = ctx.float_expression(
        Rc.Time.CONTINUOUS_SEC, 60.0, MOD, 6.0, MUL)
    min_angle = ctx.float_expression(Rc.Time.TIME_IN_MIN, 6.0, MUL)
    hr_angle = ctx.float_expression(Rc.Time.TIME_IN_HR, 30.0, MUL)

    hour_len = ctx.float_expression(
        center_y, center_x, center_y, MIN, 0.3, MUL, SUB)
    min_len = ctx.float_expression(
        center_y, center_x, center_y, MIN, 0.7, MUL, SUB)

    # Hour hand
    ctx.canvas_save()
    ctx.painter.set_color(GRAY).set_stroke_width(12.0) \
        .set_stroke_cap(1).commit()
    ctx.draw_circle(center_x, center_y, 12.0)
    ctx.rotate(hr_angle, center_x, center_y)
    ctx.draw_line(center_x, center_y, center_x, hour_len)
    ctx.canvas_restore()

    # Minute hand
    ctx.canvas_save()
    ctx.painter.set_color(WHITE).set_stroke_width(6.0).commit()
    ctx.draw_circle(center_x, center_y, 6.0)
    ctx.rotate(min_angle, center_x, center_y)
    ctx.draw_line(center_x, center_y, center_x, min_len)
    ctx.canvas_restore()

    # Center dot
    ctx.painter.set_color(WHITE).commit()
    ctx.draw_circle(center_x, center_y, 2.0)

    # Second hand
    ctx.canvas_save()
    ctx.rotate(second_angle, center_x, center_y)
    ctx.painter.set_color(RED).set_stroke_width(4.0).commit()
    ctx.draw_line(center_x, center_y, center_x, min_len)
    ctx.canvas_restore()


def demo_metal_clock():
    ctx = RcContext(500, 500, "MetalClock", api_level=6)

    with ctx.root():
        with ctx.box(Modifier().fill_max_size()):
            with ctx.canvas(Modifier().fill_max_size()):
                w = ctx.component_width()
                h = ctx.component_height()
                cx = ctx.float_expression(w, 2.0, DIV)
                cy = ctx.float_expression(h, 2.0, DIV)
                rad = ctx.float_expression(w, h, MIN)
                clip_rad = ctx.float_expression(rad, 2.0, DIV)
                rad1 = ctx.float_expression(rad, 2.0, DIV)
                rad2 = ctx.float_expression(rad, 5.0, DIV)

                # Generate squircle clip path
                path_id = gen_squircle_path(ctx, cx, cy, clip_rad, rad2)
                ctx.add_clip_path(path_id)

                # Metallic gradient background (rotating)
                ctx.canvas_save()
                rot_angle = ctx.float_expression(
                    Rc.Time.CONTINUOUS_SEC, 360.0, MOD)
                ctx.rotate(rot_angle, cx, cy)
                ctx.painter.set_sweep_gradient(
                    cx, cy,
                    [METAL1, METAL2, METAL2, METAL2, METAL1, METAL2, METAL1],
                    None).commit()
                second_spin = ctx.float_expression(
                    Rc.Time.CONTINUOUS_SEC, 360.0, MOD, 11.0, MUL)
                ctx.draw_circle(cx, cy, rad)
                ctx.rotate(second_spin, cx, cy)
                ctx.painter.set_sweep_gradient(
                    cx, cy,
                    [METAL_ALPHA1, METAL_ALPHA2, METAL_ALPHA2,
                     METAL_ALPHA2, METAL_ALPHA1, METAL_ALPHA2, METAL_ALPHA1],
                    None).commit()
                ctx.draw_circle(cx, cy, rad)
                ctx.canvas_restore()
                ctx.painter.set_shader(0).commit()

                # Draw ticks
                draw_ticks(ctx, cx, cy, rad1, rad2)

                # Draw clock hands
                draw_clock_hands(ctx, cx, cy)

    return ctx


if __name__ == '__main__':
    ctx = demo_metal_clock()
    data = ctx.encode()
    print(f"MetalClock: {len(data)} bytes")
    ctx.save("demo_metal_clock.rc")
    print("Saved demo_metal_clock.rc")

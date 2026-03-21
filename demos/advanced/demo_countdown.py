"""Countdown demo. Port of Countdown.kt.

Demonstrates:
- Sweep gradient painting
- Float expressions with trig functions (COS, SIN)
- Color expressions from HSV with animated hue
- Canvas save/restore and scale transforms
- createTextFromFloat and textMerge for dynamic text
- Drawing circles with expression-driven positions
"""
import sys
import os
import math

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RcContext, Rc
from rcreate.rc_paint import RcPaint

# Float expression operators
MUL = Rc.FloatExpression.MUL
ADD = Rc.FloatExpression.ADD
DIV = Rc.FloatExpression.DIV
MOD = Rc.FloatExpression.MOD
COS = Rc.FloatExpression.COS
SIN = Rc.FloatExpression.SIN

# Time
CS = Rc.Time.CONTINUOUS_SEC

# Color constants (Color.hsv(h, 0.9, 0.9).toArgb())
# Computed via standard HSV->RGB: c=v*s, x=c*(1-|h/60%2-1|), m=v-c
HSV_COLORS = [
    0xFFE61717,  # H=0
    0xFFE6E617,  # H=60
    0xFF17E617,  # H=120
    0xFF17E6E6,  # H=180
    0xFF1717E6,  # H=240
    0xFFE617E6,  # H=300
    0xFFE61717,  # H=360
]

BLUE = 0xFF0000FF


def demo_countdown():
    """Port of countDown() from Countdown.kt.

    Draws animated circles with sweep gradient, HSV color expressions,
    and scaled text showing the current hue value.
    """
    ctx = RcContext(600, 600, "")

    ctx.paint.set_text_size(50.0).commit()

    pi2 = float(math.pi * 2)

    # Animated position: circle orbiting at 3x speed
    x = ctx.float_expression(CS, 3.0, MUL, COS, 200.0, MUL, 300.0, ADD)
    y = ctx.float_expression(CS, 3.0, MUL, SIN, 200.0, MUL, 300.0, ADD)

    # Hue cycles through 0..1 based on continuous time
    hue = ctx.float_expression(CS, 3.0, MUL, pi2, DIV, 1.0, MOD)

    # Sweep gradient circle
    ctx.paint.set_sweep_gradient(300.0, 300.0, HSV_COLORS, None).commit()
    ctx.draw_circle(300.0, 300.0, 200.0)

    # Clear shader
    ctx.paint.set_shader(0).commit()

    # HSV color expression for the orbiting circle
    id1 = ctx.add_color_expression(0x8F, hue, 0.9, 0.9)
    ctx.paint.set_color_id(id1).commit()
    ctx.draw_circle(x, y, 100.0)

    # Text setup
    ctx.paint.set_color(BLUE).set_text_size(100.0).set_typeface(
        RcPaint.FONT_TYPE_MONOSPACE).commit()

    # Create dynamic text: "Hue:" + formatted hue value
    text_id = ctx.create_text_from_float(hue, 1, 2, Rc.TextFromFloat.PAD_AFTER_ZERO)
    merge = ctx.text_merge(ctx.text_create_id("Hue:"), text_id)

    # Save, scale by hue around center, draw text, restore
    ctx.matrix_save()
    ctx.scale(hue, hue, 300.0, 300.0)
    ctx.draw_text_anchored(merge, 300.0, 300.0, 0.0, 0.0, 2)
    ctx.matrix_restore()

    # Draw 6 colored circles around the perimeter
    for i in range(6):
        id2 = ctx.add_color_expression(0x8F, i / 6.0, 0.9, 0.9)
        ctx.paint.set_color_id(id2).commit()
        angle = i * math.pi * 2.0 / 6
        cx = 300 + math.cos(angle) * 200
        cy = 300 + math.sin(angle) * 200
        ctx.draw_circle(float(cx), float(cy), 100.0)

    return ctx


if __name__ == '__main__':
    ctx = demo_countdown()
    data = ctx.encode()
    print(f"Countdown: {len(data)} bytes")
    ctx.save("demo_countdown.rc")
    print("Saved demo_countdown.rc")

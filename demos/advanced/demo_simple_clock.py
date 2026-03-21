"""Simple analog clock demo using canvas and expressions.

Demonstrates:
- Canvas drawing with expressions
- Time variables (CONTINUOUS_SEC, TIME_IN_MIN, TIME_IN_HR)
- Matrix transforms (save/restore/rotate)
- Painter state (color, strokeWidth, strokeCap)
- drawLine, drawCircle with expression-based coordinates
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RcContext, Modifier, Rc

WHITE = 0xFFFFFFFF
BLACK = 0xFF000000
GRAY = 0xFF888888
RED = 0xFFFF0000
LTGRAY = 0xFFCCCCCC

# FloatExpression operator constants
DIV = Rc.FloatExpression.DIV
MUL = Rc.FloatExpression.MUL
SUB = Rc.FloatExpression.SUB
MIN = Rc.FloatExpression.MIN
MOD = Rc.FloatExpression.MOD


def demo_simple_clock():
    ctx = RcContext(400, 400, "SimpleClock")

    with ctx.root():
        with ctx.box(Modifier().fill_max_size()):
            with ctx.canvas(Modifier().fill_max_size().background(WHITE)):
                w = ctx.component_width()
                h = ctx.component_height()
                cx = ctx.float_expression(w, 2.0, DIV)
                cy = ctx.float_expression(h, 2.0, DIV)
                rad = ctx.float_expression(w, h, MIN, 2.0, DIV)

                # Background circle
                ctx.painter.set_color(LTGRAY).commit()
                ctx.draw_circle(cx, cy, rad)

                # Draw tick marks
                ctx.painter.set_color(GRAY).set_stroke_width(2.0).commit()

                # Hour hand
                hr_angle = ctx.float_expression(
                    Rc.Time.TIME_IN_HR, 30.0, MUL)
                hour_len = ctx.float_expression(
                    cy, rad, 0.5, MUL, SUB)

                ctx.canvas_save()
                ctx.painter.set_color(BLACK).set_stroke_width(8.0).commit()
                ctx.rotate(hr_angle, cx, cy)
                ctx.draw_line(cx, cy, cx, hour_len)
                ctx.canvas_restore()

                # Minute hand
                min_angle = ctx.float_expression(
                    Rc.Time.TIME_IN_MIN, 6.0, MUL)
                min_len = ctx.float_expression(
                    cy, rad, 0.7, MUL, SUB)

                ctx.canvas_save()
                ctx.painter.set_color(BLACK).set_stroke_width(4.0).commit()
                ctx.rotate(min_angle, cx, cy)
                ctx.draw_line(cx, cy, cx, min_len)
                ctx.canvas_restore()

                # Second hand
                sec_angle = ctx.float_expression(
                    Rc.Time.CONTINUOUS_SEC, 60.0, MOD, 6.0, MUL)

                ctx.canvas_save()
                ctx.painter.set_color(RED).set_stroke_width(2.0).commit()
                ctx.rotate(sec_angle, cx, cy)
                ctx.draw_line(cx, cy, cx, min_len)
                ctx.canvas_restore()

                # Center dot
                ctx.painter.set_color(BLACK).commit()
                ctx.draw_circle(cx, cy, 4.0)

    return ctx


if __name__ == '__main__':
    ctx = demo_simple_clock()
    data = ctx.encode()
    print(f"SimpleClock: {len(data)} bytes")
    ctx.save("demo_simple_clock.rc")
    print("Saved demo_simple_clock.rc")

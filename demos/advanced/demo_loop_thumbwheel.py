"""Loop-based thumbwheel demo. Simplified port of demoTouchThumbWheel1().

Demonstrates:
- Loop with expression-based index
- Touch-driven rotation
- createTextFromFloat within loop
- drawTextAnchored in loop body
- scale/save/restore in loop
- Trigonometric expressions (RAD, COS, SIN)
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RcContext, Modifier, Rc

BLUE = 0xFF0000FF
GRAY = 0xFF888888
BLACK = 0xFF000000

ADD = Rc.FloatExpression.ADD
SUB = Rc.FloatExpression.SUB
MUL = Rc.FloatExpression.MUL
DIV = Rc.FloatExpression.DIV
MAX = Rc.FloatExpression.MAX
RAD = Rc.FloatExpression.RAD
COS = Rc.FloatExpression.COS
SIN = Rc.FloatExpression.SIN
ROUND = Rc.FloatExpression.ROUND


def demo_loop_thumbwheel():
    ctx = RcContext(300, 300, "LoopThumbwheel")

    with ctx.root():
        with ctx.box(Modifier().fill_max_width().fill_max_height()
                     .background(0xFF8899AA)):
            with ctx.canvas(Modifier().fill_max_size()):
                w = ctx.component_width()
                h = ctx.component_height()
                cx = ctx.float_expression(w, 0.5, MUL)
                cy = ctx.float_expression(h, 0.5, MUL)

                # Touch variable: vertical scrolling
                touch = ctx.add_touch(
                    0.0, float('nan'), 360.0,
                    Rc.Touch.STOP_NOTCHES_EVEN,
                    0.0, 4,
                    [10.0],
                    ctx.easing(10.0, 2.0, 60.0),
                    Rc.Touch.POSITION_Y,
                    0.2, MUL)

                # Digit display from touch position
                ctx.painter.set_shader(0).set_color(BLUE) \
                    .set_text_size(128.0).commit()
                num = ctx.float_expression(
                    375.0, touch, SUB, 36.0, DIV)
                num_text = ctx.create_text_from_float(num, 1, 0, 0)
                ctx.draw_text_anchored(num_text, cx, cy, -6.0, 0.0, 2)

                # Gradient text for wheel items
                ctx.painter.set_text_size(128.0) \
                    .set_linear_gradient(
                        0.0, 0.0, 0.0, h,
                        [0x00000000, 0xFF444444, BLACK, 0x00000000],
                        [0.0, 0.4, 0.8, 1.0], 0).commit()

                # Loop: draw 10 items around the wheel
                index = ctx.start_loop(10.0)

                angle = ctx.float_expression(
                    index, 36.0, MUL, touch, ADD, RAD)
                scale_val = ctx.float_expression(
                    angle, COS, 0.0, MAX)
                py = ctx.float_expression(
                    angle, SIN, cy, 0.8, MUL, MUL, cy, ADD)

                ctx.canvas_save()
                ctx.scale(1.0, scale_val, cx, py)
                index_text = ctx.create_text_from_float(index, 1, 0, 0)
                ctx.draw_text_anchored(index_text, cx, py, 0.0, 0.0, 0)
                ctx.canvas_restore()

                ctx.end_loop()

                # Selection box
                rr_top = ctx.float_expression(cy, 64.0, SUB)
                rr_bottom = ctx.float_expression(cy, 64.0, ADD)
                ctx.painter.set_color(GRAY).set_style(1).commit()
                ctx.draw_round_rect(0.0, rr_top, w, rr_bottom, 60.0, 60.0)

    return ctx


if __name__ == '__main__':
    ctx = demo_loop_thumbwheel()
    data = ctx.encode()
    print(f"LoopThumbwheel: {len(data)} bytes")
    ctx.save("demo_loop_thumbwheel.rc")
    print("Saved demo_loop_thumbwheel.rc")

"""Touch slider demo. Simplified port of DemoTouch.kt / demoTouch1().

Demonstrates:
- addTouch for creating interactive touch controls
- Horizontal slider with expression-based position
- createTextFromFloat for value display
- drawTextAnchored with ANCHOR_MONOSPACE_MEASURE
- drawRoundRect for slider track and thumb
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RcContext, Modifier, Rc

BLUE = 0xFF0000FF
RED = 0xFFFF0000
GRAY = 0xFF888888
BLACK = 0xFF000000
WHITE = 0xFFFFFFFF

ADD = Rc.FloatExpression.ADD
SUB = Rc.FloatExpression.SUB
MUL = Rc.FloatExpression.MUL
DIV = Rc.FloatExpression.DIV

ANCHOR_MONOSPACE = Rc.TextAnchorMask.MONOSPACE_MEASURE


def demo_touch_slider():
    ctx = RcContext(300, 300, "TouchSlider")

    with ctx.root():
        with ctx.box(Modifier().fill_max_width().fill_max_height()):
            with ctx.canvas(Modifier().fill_max_size()):
                # Background
                ctx.painter.set_color(BLUE).commit()
                w = ctx.component_width()
                h = ctx.component_height()
                ctx.draw_rect(0.0, 0.0, w, h)

                cx = ctx.float_expression(w, 0.5, MUL)
                cy = ctx.float_expression(h, 0.5, MUL)

                # Slider track bounds
                top = ctx.float_expression(cy, 10.0, SUB)
                bottom = ctx.float_expression(cy, 10.0, ADD)
                left = 20.0
                right = ctx.float_expression(w, 20.0, SUB)

                # Touch variable: horizontal slider
                pos = ctx.add_touch(
                    cx,       # default value
                    left,     # min
                    right,    # max
                    Rc.Touch.STOP_INSTANTLY,  # mode
                    0.0,      # velocity_id
                    0,        # touch_effects
                    None,     # touch_spec
                    None,     # easing_spec
                    Rc.Touch.POSITION_X,  # expression: use touch X
                    1.0,
                    MUL)

                # Slider thumb bounds
                left_slider = ctx.float_expression(pos, 20.0, SUB)
                right_slider = ctx.float_expression(pos, 20.0, ADD)
                top_slider = ctx.float_expression(top, 20.0, SUB)
                bottom_slider = ctx.float_expression(bottom, 20.0, ADD)

                # Draw track
                ctx.painter.set_color(GRAY).commit()
                ctx.draw_round_rect(left, top, right, bottom, 20.0, 20.0)

                # Draw thumb
                ctx.painter.set_color(RED).commit()
                ctx.draw_round_rect(left_slider, top_slider,
                                    right_slider, bottom_slider, 40.0, 40.0)

                # Value label
                value = ctx.float_expression(
                    pos, 20.0, SUB, h, 40.0, SUB, DIV)
                value_str = ctx.create_text_from_float(
                    value, 1, 2, Rc.TextFromFloat.PAD_AFTER_ZERO)
                ctx.painter.set_color(WHITE).commit()
                ctx.draw_text_anchored(
                    value_str, pos, cy, 0.0, -2.0, ANCHOR_MONOSPACE)

    return ctx


if __name__ == '__main__':
    ctx = demo_touch_slider()
    data = ctx.encode()
    print(f"TouchSlider: {len(data)} bytes")
    ctx.save("demo_touch_slider.rc")
    print("Saved demo_touch_slider.rc")

"""Color buttons demo. Port of DemoColor.kt / colorButtons().

Demonstrates:
- pingPong for bouncing animation
- addColorExpression for dynamic colors
- backgroundId and dynamicBorder modifiers
- Canvas with drawRoundRect, createTextFromFloat, drawTextAnchored
- setColorId on painter
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RcContext, Modifier, Rc

GREEN = 0xFF007700
BLUE = 0xFF000077
TEAL = 0xFF007777
DKPURPLE = 0xFF666677

MOD = Rc.FloatExpression.MOD
SUB = Rc.FloatExpression.SUB
ABS = Rc.FloatExpression.ABS
DIV = Rc.FloatExpression.DIV
MUL = Rc.FloatExpression.MUL


def demo_color_buttons():
    ctx = RcContext(500, 500, "ColorButtons", api_level=7)

    # Bouncing 0..1 value
    bounce = ctx.ping_pong(1, Rc.Time.CONTINUOUS_SEC)

    col = ctx.add_color_expression(0xFFFF0000, 0xFF00FF00, bounce)
    col2 = ctx.add_color_expression(0xFF000000, 0xFFFFFF00, bounce)

    with ctx.root():
        with ctx.box(Modifier().fill_max_size()):
            with ctx.column(Modifier().background(DKPURPLE)):
                with ctx.box(Modifier().background(GREEN).fill_max_width().height(120)):
                    pass
                with ctx.box(Modifier().background_id(col).fill_max_width().height(120)):
                    pass
                with ctx.box(Modifier().background(BLUE).fill_max_width().height(120)):
                    pass
                with ctx.box(Modifier().background_id(col)
                             .dynamic_border(10.0, 30.0, col2, 0)
                             .fill_max_width().height(120)):
                    pass
                with ctx.box(Modifier().background(TEAL).fill_max_width().height(120)):
                    pass

                # Canvas section showing API level
                with ctx.canvas(Modifier()
                                .dynamic_border(40.0, 30.0, col2, 0)
                                .fill_max_width().height(200)):
                    w = ctx.component_width()
                    h = ctx.component_height()
                    version = Rc.System.API_LEVEL
                    ctx.painter.set_color_id(col).commit()
                    ctx.draw_round_rect(0, 0, w, h, 2.0, 2.0)
                    ctx.painter.set_color(0xFFFFFFFF).set_text_size(64.0).commit()

                    text_id = ctx.create_text_from_float(version, 3, 2, 0)
                    cx = ctx.float_expression(w, 2.0, DIV)
                    ctx.draw_text_anchored(text_id, cx, 100.0, 0, 0, 0)

    return ctx


if __name__ == '__main__':
    ctx = demo_color_buttons()
    data = ctx.encode()
    print(f"ColorButtons: {len(data)} bytes")
    ctx.save("demo_color_buttons.rc")
    print("Saved demo_color_buttons.rc")

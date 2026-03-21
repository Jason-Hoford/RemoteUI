"""Color expression demo using dynamic backgrounds.

Demonstrates:
- addColorExpression for interpolated colors
- backgroundId for dynamic coloring
- dynamicBorder with color IDs
- Time-based animation with CONTINUOUS_SEC
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


def demo_color_expression():
    ctx = RcContext(500, 500, "ColorExpression")

    # Create a bouncing 0..1 value from CONTINUOUS_SEC
    bounce = ctx.float_expression(
        Rc.Time.CONTINUOUS_SEC, 2.0, MOD, 1.0, SUB, ABS)

    col = ctx.add_color_expression(0xFFFF0000, 0xFF00FF00, bounce)
    col2 = ctx.add_color_expression(0xFF000000, 0xFFFFFF00, bounce)

    with ctx.root():
        with ctx.box(Modifier().fill_max_size()):
            with ctx.column(Modifier().background(DKPURPLE)):
                with ctx.box(Modifier().background(GREEN).fill_max_width().height(100)):
                    pass
                with ctx.box(Modifier().background_id(col).fill_max_width().height(100)):
                    pass
                with ctx.box(Modifier().background(BLUE).fill_max_width().height(100)):
                    pass
                with ctx.box(Modifier().background_id(col)
                             .dynamic_border(10.0, 30.0, col2, 0)
                             .fill_max_width().height(100)):
                    pass
                with ctx.box(Modifier().background(TEAL).fill_max_width().height(100)):
                    pass

    return ctx


if __name__ == '__main__':
    ctx = demo_color_expression()
    data = ctx.encode()
    print(f"ColorExpression: {len(data)} bytes")
    ctx.save("demo_color_expression.rc")
    print("Saved demo_color_expression.rc")

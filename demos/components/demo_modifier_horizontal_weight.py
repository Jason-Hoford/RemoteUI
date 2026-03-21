"""Atomic demo for the horizontalWeight modifier. Port of DemoModifierHorizontalWeight.kt."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RcContext, Modifier

RED = 0xFFFF0000
BLUE = 0xFF0000FF


def demo_modifier_horizontal_weight():
    ctx = RcContext(400, 400)
    with ctx.root():
        with ctx.row(Modifier().fill_max_width().height(100)):
            ctx.box_leaf(Modifier().horizontal_weight(1.0).fill_max_height().background(RED))
            ctx.box_leaf(Modifier().horizontal_weight(2.0).fill_max_height().background(BLUE))
    return ctx


if __name__ == '__main__':
    ctx = demo_modifier_horizontal_weight()
    data = ctx.encode()
    print(f"DemoModifierHorizontalWeight: {len(data)} bytes")
    ctx.save("demo_modifier_horizontal_weight.rc")
    print("Saved demo_modifier_horizontal_weight.rc")

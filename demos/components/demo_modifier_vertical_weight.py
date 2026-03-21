"""Atomic demo for the verticalWeight modifier. Port of DemoModifierVerticalWeight.kt."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RcContext, Modifier

RED = 0xFFFF0000
BLUE = 0xFF0000FF


def demo_modifier_vertical_weight():
    ctx = RcContext(400, 400)
    with ctx.root():
        with ctx.column(Modifier().fill_max_height().width(100)):
            ctx.box_leaf(Modifier().fill_max_width().vertical_weight(1.0).background(RED))
            ctx.box_leaf(Modifier().fill_max_width().vertical_weight(3.0).background(BLUE))
    return ctx


if __name__ == '__main__':
    ctx = demo_modifier_vertical_weight()
    data = ctx.encode()
    print(f"DemoModifierVerticalWeight: {len(data)} bytes")
    ctx.save("demo_modifier_vertical_weight.rc")
    print("Saved demo_modifier_vertical_weight.rc")

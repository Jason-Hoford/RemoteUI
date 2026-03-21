"""Atomic demo for the border modifier. Port of DemoModifierBorder.kt."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RcContext, Modifier

RED = 0xFFFF0000
BLUE = 0xFF0000FF


def demo_modifier_border():
    ctx = RcContext(400, 400)
    with ctx.root():
        with ctx.column(Modifier().padding(20).spaced_by(20.0)):
            # Rectangular border
            ctx.box_leaf(Modifier().size(100).border(4.0, 0.1, RED, 2))
            # Rounded border
            ctx.box_leaf(Modifier().size(100).border(4.0, 0.1, BLUE, 2))
    return ctx


if __name__ == '__main__':
    ctx = demo_modifier_border()
    data = ctx.encode()
    print(f"DemoModifierBorder: {len(data)} bytes")
    ctx.save("demo_modifier_border.rc")
    print("Saved demo_modifier_border.rc")

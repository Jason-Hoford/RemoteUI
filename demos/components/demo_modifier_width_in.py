"""Atomic demo for the widthIn modifier. Port of DemoModifierWidthIn.kt."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RcContext, Modifier

RED = 0xFFFF0000
BLUE = 0xFF0000FF


def demo_modifier_width_in():
    ctx = RcContext(400, 400)
    with ctx.root():
        with ctx.column():
            # Min width constraint
            ctx.box_leaf(Modifier().width_in(100.0, 200.0).height(50).background(RED))
            # Max width constraint
            ctx.box_leaf(Modifier().width_in(50.0, 100.0).height(50).background(BLUE))
    return ctx


if __name__ == '__main__':
    ctx = demo_modifier_width_in()
    data = ctx.encode()
    print(f"DemoModifierWidthIn: {len(data)} bytes")
    ctx.save("demo_modifier_width_in.rc")
    print("Saved demo_modifier_width_in.rc")

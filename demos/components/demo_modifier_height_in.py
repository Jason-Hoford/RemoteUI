"""Atomic demo for the heightIn modifier. Port of DemoModifierHeightIn.kt."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RcContext, Modifier

RED = 0xFFFF0000
BLUE = 0xFF0000FF


def demo_modifier_height_in():
    ctx = RcContext(400, 400)
    with ctx.root():
        with ctx.row():
            # Min height constraint
            ctx.box_leaf(Modifier().width(50).height_in(100.0, 200.0).background(RED))
            # Max height constraint
            ctx.box_leaf(Modifier().width(50).height_in(100.0, 200.0).background(BLUE))
    return ctx


if __name__ == '__main__':
    ctx = demo_modifier_height_in()
    data = ctx.encode()
    print(f"DemoModifierHeightIn: {len(data)} bytes")
    ctx.save("demo_modifier_height_in.rc")
    print("Saved demo_modifier_height_in.rc")

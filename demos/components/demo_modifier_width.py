"""Atomic demo for the width modifier. Port of DemoModifierWidth.kt."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RcContext, Modifier

BLUE = 0xFF0000FF


def demo_modifier_width():
    ctx = RcContext(400, 400)
    with ctx.root():
        ctx.box_leaf(Modifier().width(250).height(100).background(BLUE))
    return ctx


if __name__ == '__main__':
    ctx = demo_modifier_width()
    data = ctx.encode()
    print(f"DemoModifierWidth: {len(data)} bytes")
    ctx.save("demo_modifier_width.rc")
    print("Saved demo_modifier_width.rc")

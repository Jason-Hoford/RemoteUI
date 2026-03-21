"""Atomic demo for the size modifier. Port of DemoModifierSize.kt."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RcContext, Modifier

RED = 0xFFFF0000
BLUE = 0xFF0000FF


def demo_modifier_size():
    ctx = RcContext(400, 400)
    with ctx.root():
        with ctx.column():
            # Square size
            ctx.box_leaf(Modifier().size(100).background(RED))
            # Rectangular size
            ctx.box_leaf(Modifier().size(200, 50).background(BLUE))
    return ctx


if __name__ == '__main__':
    ctx = demo_modifier_size()
    data = ctx.encode()
    print(f"DemoModifierSize: {len(data)} bytes")
    ctx.save("demo_modifier_size.rc")
    print("Saved demo_modifier_size.rc")

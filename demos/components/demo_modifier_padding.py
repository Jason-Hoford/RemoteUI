"""Atomic demo for the padding modifier. Port of DemoModifierPadding.kt."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RcContext, Modifier

RED = 0xFFFF0000
BLUE = 0xFF0000FF
WHITE = 0xFFFFFFFF


def demo_modifier_padding():
    ctx = RcContext(400, 400)
    with ctx.root():
        with ctx.column(Modifier().fill_max_size().background(WHITE)):
            # Uniform padding
            ctx.box_leaf(Modifier().padding(20).size(100).background(RED))
            # Individual padding (left, top, right, bottom)
            ctx.box_leaf(Modifier().padding(40, 5, 0, 10).size(100).background(BLUE))
    return ctx


if __name__ == '__main__':
    ctx = demo_modifier_padding()
    data = ctx.encode()
    print(f"DemoModifierPadding: {len(data)} bytes")
    ctx.save("demo_modifier_padding.rc")
    print("Saved demo_modifier_padding.rc")

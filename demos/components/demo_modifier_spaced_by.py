"""Atomic demo for the spacedBy modifier. Port of DemoModifierSpacedBy.kt."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RcContext, Modifier

RED = 0xFFFF0000
GREEN = 0xFF00FF00
BLUE = 0xFF0000FF


def demo_modifier_spaced_by():
    ctx = RcContext(400, 400)
    with ctx.root():
        with ctx.column(Modifier().fill_max_size().spaced_by(20.0)):
            ctx.box_leaf(Modifier().size(60).background(RED))
            ctx.box_leaf(Modifier().size(60).background(GREEN))
            ctx.box_leaf(Modifier().size(60).background(BLUE))
    return ctx


if __name__ == '__main__':
    ctx = demo_modifier_spaced_by()
    data = ctx.encode()
    print(f"DemoModifierSpacedBy: {len(data)} bytes")
    ctx.save("demo_modifier_spaced_by.rc")
    print("Saved demo_modifier_spaced_by.rc")

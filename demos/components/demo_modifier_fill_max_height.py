"""Atomic demo for the fillMaxHeight modifier. Port of DemoModifierFillMaxHeight.kt."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RcContext, Modifier

MAGENTA = 0xFFFF00FF


def demo_modifier_fill_max_height():
    ctx = RcContext(400, 400)
    with ctx.root():
        with ctx.row(Modifier().fill_max_size()):
            ctx.box_leaf(Modifier().width(100).fill_max_height().background(MAGENTA))
    return ctx


if __name__ == '__main__':
    ctx = demo_modifier_fill_max_height()
    data = ctx.encode()
    print(f"DemoModifierFillMaxHeight: {len(data)} bytes")
    ctx.save("demo_modifier_fill_max_height.rc")
    print("Saved demo_modifier_fill_max_height.rc")

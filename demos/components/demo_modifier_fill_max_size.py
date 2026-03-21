"""Atomic demo for the fillMaxSize modifier. Port of DemoModifierFillMaxSize.kt."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RcContext, Modifier

YELLOW = 0xFFFFFF00


def demo_modifier_fill_max_size():
    ctx = RcContext(400, 400)
    with ctx.root():
        ctx.box_leaf(Modifier().fill_max_size().background(YELLOW))
    return ctx


if __name__ == '__main__':
    ctx = demo_modifier_fill_max_size()
    data = ctx.encode()
    print(f"DemoModifierFillMaxSize: {len(data)} bytes")
    ctx.save("demo_modifier_fill_max_size.rc")
    print("Saved demo_modifier_fill_max_size.rc")

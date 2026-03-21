"""Atomic demo for the height modifier. Port of DemoModifierHeight.kt."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RcContext, Modifier

GREEN = 0xFF00FF00


def demo_modifier_height():
    ctx = RcContext(400, 400)
    with ctx.root():
        ctx.box_leaf(Modifier().width(100).height(250).background(GREEN))
    return ctx


if __name__ == '__main__':
    ctx = demo_modifier_height()
    data = ctx.encode()
    print(f"DemoModifierHeight: {len(data)} bytes")
    ctx.save("demo_modifier_height.rc")
    print("Saved demo_modifier_height.rc")

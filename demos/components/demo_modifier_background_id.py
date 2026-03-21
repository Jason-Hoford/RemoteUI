"""Atomic demo for the backgroundId modifier. Port of DemoModifierBackgroundId.kt."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RcContext, Modifier


def demo_modifier_background_id():
    ctx = RcContext(400, 400)
    with ctx.root():
        # Using a system/themed color ID
        ctx.box_leaf(Modifier().size(200).background_id(1).padding(10))
    return ctx


if __name__ == '__main__':
    ctx = demo_modifier_background_id()
    data = ctx.encode()
    print(f"DemoModifierBackgroundId: {len(data)} bytes")
    ctx.save("demo_modifier_background_id.rc")
    print("Saved demo_modifier_background_id.rc")

"""Atomic demo for the onTouchCancel modifier. Port of DemoModifierOnTouchCancel.kt."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RcContext, Modifier, ValueIntegerChange

DKGRAY = 0xFF444444
WHITE = 0xFFFFFFFF


def demo_modifier_on_touch_cancel():
    ctx = RcContext(500, 500, "DemoModifierOnTouchCancel", profiles=0x201)
    with ctx.root():
        state_id = ctx.add_integer(0)
        action = ValueIntegerChange(state_id, 4)
        with ctx.box(Modifier().size(200).background(DKGRAY).on_touch_cancel(action)):
            ctx.text("Touch Cancel", color=WHITE)
    return ctx


if __name__ == '__main__':
    ctx = demo_modifier_on_touch_cancel()
    data = ctx.encode()
    print(f"DemoModifierOnTouchCancel: {len(data)} bytes")
    ctx.save("demo_modifier_on_touch_cancel.rc")
    print("Saved demo_modifier_on_touch_cancel.rc")

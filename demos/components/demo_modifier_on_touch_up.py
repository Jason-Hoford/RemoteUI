"""Atomic demo for the onTouchUp modifier. Port of DemoModifierOnTouchUp.kt."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RcContext, Modifier, ValueIntegerChange

GREEN = 0xFF00FF00
WHITE = 0xFFFFFFFF


def demo_modifier_on_touch_up():
    ctx = RcContext(500, 500, "DemoModifierOnTouchUp", profiles=0x201)
    with ctx.root():
        state_id = ctx.add_integer(0)
        action = ValueIntegerChange(state_id, 3)
        with ctx.box(Modifier().size(200).background(GREEN).on_touch_up(action)):
            ctx.text("Release Up", color=WHITE)
    return ctx


if __name__ == '__main__':
    ctx = demo_modifier_on_touch_up()
    data = ctx.encode()
    print(f"DemoModifierOnTouchUp: {len(data)} bytes")
    ctx.save("demo_modifier_on_touch_up.rc")
    print("Saved demo_modifier_on_touch_up.rc")

"""Atomic demo for the onTouchDown modifier. Port of DemoModifierOnTouchDown.kt."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RcContext, Modifier, ValueIntegerChange

BLUE = 0xFF0000FF
WHITE = 0xFFFFFFFF


def demo_modifier_on_touch_down():
    ctx = RcContext(500, 500, "DemoModifierOnTouchDown", profiles=0x201)
    with ctx.root():
        state_id = ctx.add_integer(0)
        action = ValueIntegerChange(state_id, 2)
        with ctx.box(Modifier().size(200).background(BLUE).on_touch_down(action)):
            ctx.text("Press Down", color=WHITE)
    return ctx


if __name__ == '__main__':
    ctx = demo_modifier_on_touch_down()
    data = ctx.encode()
    print(f"DemoModifierOnTouchDown: {len(data)} bytes")
    ctx.save("demo_modifier_on_touch_down.rc")
    print("Saved demo_modifier_on_touch_down.rc")

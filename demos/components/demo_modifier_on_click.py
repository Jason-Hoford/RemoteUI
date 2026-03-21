"""Atomic demo for the onClick modifier. Port of DemoModifierOnClick.kt."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RcContext, Modifier, ValueIntegerChange

RED = 0xFFFF0000
WHITE = 0xFFFFFFFF


def demo_modifier_on_click():
    ctx = RcContext(500, 500, "DemoModifierOnClick", profiles=0x201)
    with ctx.root():
        state_id = ctx.add_integer(0)
        toggle_action = ValueIntegerChange(state_id, 1)
        with ctx.box(Modifier().size(200).background(RED).on_click(toggle_action)):
            ctx.text("Tap Me", color=WHITE)
    return ctx


if __name__ == '__main__':
    ctx = demo_modifier_on_click()
    data = ctx.encode()
    print(f"DemoModifierOnClick: {len(data)} bytes")
    ctx.save("demo_modifier_on_click.rc")
    print("Saved demo_modifier_on_click.rc")

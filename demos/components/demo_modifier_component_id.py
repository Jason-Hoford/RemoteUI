"""Atomic demo for the componentId modifier. Port of DemoModifierComponentId.kt."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RcContext, Modifier

RED = 0xFFFF0000


def demo_modifier_component_id():
    ctx = RcContext(400, 400)
    with ctx.root():
        ctx.box_leaf(Modifier().size(100).background(RED).component_id(101))
    return ctx


if __name__ == '__main__':
    ctx = demo_modifier_component_id()
    data = ctx.encode()
    print(f"DemoModifierComponentId: {len(data)} bytes")
    ctx.save("demo_modifier_component_id.rc")
    print("Saved demo_modifier_component_id.rc")

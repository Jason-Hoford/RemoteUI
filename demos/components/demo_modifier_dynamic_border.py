"""Atomic demo for the dynamicBorder modifier. Port of DemoModifierDynamicBorder.kt."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RcContext, Modifier


def demo_modifier_dynamic_border():
    ctx = RcContext(400, 400)
    with ctx.root():
        color_id = ctx.add_color_expression(1.0, 0.7, 0.9)
        ctx.box_leaf(Modifier().size(200).dynamic_border(5.0, 1.0, color_id, 1))
    return ctx


if __name__ == '__main__':
    ctx = demo_modifier_dynamic_border()
    data = ctx.encode()
    print(f"DemoModifierDynamicBorder: {len(data)} bytes")
    ctx.save("demo_modifier_dynamic_border.rc")
    print("Saved demo_modifier_dynamic_border.rc")

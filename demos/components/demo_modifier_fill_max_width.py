"""Atomic demo for the fillMaxWidth modifier. Port of DemoModifierFillMaxWidth.kt."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RcContext, Modifier

CYAN = 0xFF00FFFF


def demo_modifier_fill_max_width():
    ctx = RcContext(400, 400)
    with ctx.root():
        with ctx.column(Modifier().fill_max_size()):
            ctx.box_leaf(Modifier().fill_max_width().height(100).background(CYAN))
    return ctx


if __name__ == '__main__':
    ctx = demo_modifier_fill_max_width()
    data = ctx.encode()
    print(f"DemoModifierFillMaxWidth: {len(data)} bytes")
    ctx.save("demo_modifier_fill_max_width.rc")
    print("Saved demo_modifier_fill_max_width.rc")

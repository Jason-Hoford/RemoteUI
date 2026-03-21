"""Atomic demo for the fillParentMaxSize modifier. Port of DemoModifierFillParentMaxSize.kt."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RcContext, Modifier

YELLOW = 0xFFFFFF00


def demo_modifier_fill_parent_max_size():
    ctx = RcContext(400, 400)
    with ctx.root():
        with ctx.column(Modifier().fill_max_size().vertical_scroll()):
            ctx.box_leaf(Modifier().fill_parent_max_size().background(YELLOW))
    return ctx


if __name__ == '__main__':
    ctx = demo_modifier_fill_parent_max_size()
    data = ctx.encode()
    print(f"DemoModifierFillParentMaxSize: {len(data)} bytes")
    ctx.save("demo_modifier_fill_parent_max_size.rc")
    print("Saved demo_modifier_fill_parent_max_size.rc")

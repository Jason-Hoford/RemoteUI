"""Atomic demo for the fillParentMaxHeight modifier. Port of DemoModifierFillParentMaxHeight.kt."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RcContext, Modifier

LTGRAY = 0xFFCCCCCC
BLUE = 0xFF0000FF


def demo_modifier_fill_parent_max_height():
    ctx = RcContext(400, 400)
    with ctx.root():
        with ctx.column(Modifier().fill_max_size().vertical_scroll()):
            with ctx.box(Modifier().fill_max_width().fill_parent_max_height().background(LTGRAY)):
                ctx.box_leaf(Modifier().size(100).background(BLUE))
    return ctx


if __name__ == '__main__':
    ctx = demo_modifier_fill_parent_max_height()
    data = ctx.encode()
    print(f"DemoModifierFillParentMaxHeight: {len(data)} bytes")
    ctx.save("demo_modifier_fill_parent_max_height.rc")
    print("Saved demo_modifier_fill_parent_max_height.rc")

"""Atomic demo for the fillParentMaxWidth modifier. Port of DemoModifierFillParentMaxWidth.kt."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RcContext, Modifier

LTGRAY = 0xFFCCCCCC
RED = 0xFFFF0000


def demo_modifier_fill_parent_max_width():
    ctx = RcContext(400, 400)
    with ctx.root():
        with ctx.row(Modifier().fill_max_size().horizontal_scroll()):
            with ctx.box(Modifier().fill_parent_max_width().fill_max_height().background(LTGRAY)):
                ctx.box_leaf(Modifier().size(100).background(RED))
    return ctx


if __name__ == '__main__':
    ctx = demo_modifier_fill_parent_max_width()
    data = ctx.encode()
    print(f"DemoModifierFillParentMaxWidth: {len(data)} bytes")
    ctx.save("demo_modifier_fill_parent_max_width.rc")
    print("Saved demo_modifier_fill_parent_max_width.rc")

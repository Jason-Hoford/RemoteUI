"""Atomic demo for the horizontalScroll modifier. Port of DemoModifierHorizontalScroll.kt."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RcContext, Modifier

LTGRAY = 0xFFCCCCCC
RED = 0xFFFF0000
WHITE = 0xFFFFFFFF


def demo_modifier_horizontal_scroll():
    ctx = RcContext(500, 500, "DemoModifierHorizontalScroll", profiles=0x201)
    with ctx.root():
        with ctx.row(Modifier().fill_max_size().horizontal_scroll().background(LTGRAY)):
            for i in range(1, 21):
                with ctx.box(Modifier().size(100).padding(5).background(RED)):
                    ctx.text(str(i), color=WHITE)
    return ctx


if __name__ == '__main__':
    ctx = demo_modifier_horizontal_scroll()
    data = ctx.encode()
    print(f"DemoModifierHorizontalScroll: {len(data)} bytes")
    ctx.save("demo_modifier_horizontal_scroll.rc")
    print("Saved demo_modifier_horizontal_scroll.rc")

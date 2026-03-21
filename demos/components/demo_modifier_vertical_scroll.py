"""Atomic demo for the verticalScroll modifier. Port of DemoModifierVerticalScroll.kt."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RcContext, Modifier

LTGRAY = 0xFFCCCCCC


def demo_modifier_vertical_scroll():
    ctx = RcContext(500, 500, "DemoModifierVerticalScroll", profiles=0x201)
    with ctx.root():
        with ctx.column(Modifier().fill_max_size().vertical_scroll().background(LTGRAY)):
            for i in range(1, 21):
                ctx.text(f"Item {i}", modifier=Modifier().padding(10))
    return ctx


if __name__ == '__main__':
    ctx = demo_modifier_vertical_scroll()
    data = ctx.encode()
    print(f"DemoModifierVerticalScroll: {len(data)} bytes")
    ctx.save("demo_modifier_vertical_scroll.rc")
    print("Saved demo_modifier_vertical_scroll.rc")

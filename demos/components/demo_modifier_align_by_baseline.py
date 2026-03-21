"""Atomic demo for the alignByBaseline modifier. Port of DemoModifierAlignByBaseline.kt."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RcContext, Modifier

LTGRAY = 0xFFCCCCCC
BLACK = 0xFF000000


def demo_modifier_align_by_baseline():
    ctx = RcContext(500, 500, "DemoModifierAlignByBaseline", profiles=0x201)
    with ctx.root():
        with ctx.row(Modifier().fill_max_width().background(LTGRAY)):
            ctx.text("Large", font_size=60.0, modifier=Modifier().align_by_baseline(),
                     color=BLACK)
            ctx.text("Small", font_size=20.0, modifier=Modifier().align_by_baseline(),
                     color=BLACK)
    return ctx


if __name__ == '__main__':
    ctx = demo_modifier_align_by_baseline()
    data = ctx.encode()
    print(f"DemoModifierAlignByBaseline: {len(data)} bytes")
    ctx.save("demo_modifier_align_by_baseline.rc")
    print("Saved demo_modifier_align_by_baseline.rc")

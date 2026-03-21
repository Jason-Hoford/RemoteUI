"""Atomic demo for the background modifier. Port of DemoModifierBackground.kt."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RcContext, Modifier

RED = 0xFFFF0000


def demo_modifier_background():
    ctx = RcContext(400, 400)
    with ctx.root():
        with ctx.column(Modifier().fill_max_size()):
            # Int ARGB
            ctx.box_leaf(Modifier().size(100).background(RED))
            # Float ARGB (Red=0, Green=0, Blue=1, Alpha=1) — pure blue
            ctx.box_leaf(Modifier().size(100).background(0.0, 0.0, 1.0, 1.0))
    return ctx


if __name__ == '__main__':
    ctx = demo_modifier_background()
    data = ctx.encode()
    print(f"DemoModifierBackground: {len(data)} bytes")
    ctx.save("demo_modifier_background.rc")
    print("Saved demo_modifier_background.rc")

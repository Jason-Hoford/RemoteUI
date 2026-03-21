"""Atomic demo for the Row component. Port of DemoRow.kt."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RcContext, Modifier

RED = 0xFFFF0000
GREEN = 0xFF00FF00
BLUE = 0xFF0000FF
LTGRAY = 0xFFCCCCCC


def demo_row():
    ctx = RcContext(400, 400)
    with ctx.root():
        with ctx.row(Modifier().fill_max_width().background(LTGRAY)):
            ctx.box_leaf(Modifier().size(50).background(RED))
            ctx.box_leaf(Modifier().size(50).background(GREEN))
            ctx.box_leaf(Modifier().size(50).background(BLUE))
    return ctx


if __name__ == '__main__':
    ctx = demo_row()
    data = ctx.encode()
    print(f"DemoRow: {len(data)} bytes")
    ctx.save("demo_row.rc")
    print("Saved demo_row.rc")

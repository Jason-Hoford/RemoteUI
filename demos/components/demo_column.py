"""Atomic demo for the Column component. Port of DemoColumn.kt."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RcContext, Modifier

RED = 0xFFFF0000
GREEN = 0xFF00FF00
BLUE = 0xFF0000FF
LTGRAY = 0xFFCCCCCC


def demo_column():
    ctx = RcContext(400, 400)
    with ctx.root():
        with ctx.column(Modifier().fill_max_height().background(LTGRAY)):
            ctx.box_leaf(Modifier().size(50).background(RED))
            ctx.box_leaf(Modifier().size(50).background(GREEN))
            ctx.box_leaf(Modifier().size(50).background(BLUE))
    return ctx


if __name__ == '__main__':
    ctx = demo_column()
    data = ctx.encode()
    print(f"DemoColumn: {len(data)} bytes")
    ctx.save("demo_column.rc")
    print("Saved demo_column.rc")

"""Atomic demo for the CollapsibleColumn component. Port of DemoCollapsibleColumn.kt."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RcContext, Modifier

LTGRAY = 0xFFCCCCCC
RED = 0xFFFF0000
BLUE = 0xFF0000FF


def demo_collapsible_column():
    ctx = RcContext(400, 400)
    with ctx.root():
        with ctx.collapsible_column(
            Modifier().fill_max_width().height(150).background(LTGRAY),
            horizontal=1, vertical=1
        ):
            ctx.box_leaf(Modifier().fill_max_width().height(100).background(RED))
            ctx.box_leaf(Modifier().fill_max_width().height(100).background(BLUE))
    return ctx


if __name__ == '__main__':
    ctx = demo_collapsible_column()
    data = ctx.encode()
    print(f"DemoCollapsibleColumn: {len(data)} bytes")
    ctx.save("demo_collapsible_column.rc")
    print("Saved demo_collapsible_column.rc")

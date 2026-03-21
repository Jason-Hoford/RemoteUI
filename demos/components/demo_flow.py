"""Atomic demo for the Flow component. Port of DemoFlow.kt."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RcContext, Modifier

LTGRAY = 0xFFCCCCCC
RED = 0xFFFF0000


def demo_flow():
    ctx = RcContext(500, 500, "DemoFlow", profiles=0x201)
    with ctx.root():
        with ctx.flow(Modifier().fill_max_width().background(LTGRAY)):
            for i in range(1, 11):
                ctx.box_leaf(Modifier().size(60).padding(5).background(RED))
    return ctx


if __name__ == '__main__':
    ctx = demo_flow()
    data = ctx.encode()
    print(f"DemoFlow: {len(data)} bytes")
    ctx.save("demo_flow.rc")
    print("Saved demo_flow.rc")

"""Atomic demo for the Box component. Port of DemoBox.kt."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RcContext, Modifier

RED = 0xFFFF0000
PROFILE_ANDROIDX = 0x200


def demo_box():
    ctx = RcContext(400, 400, "", profiles=PROFILE_ANDROIDX)
    with ctx.root():
        ctx.box_leaf(Modifier().size(200).background(RED))
    return ctx


if __name__ == '__main__':
    ctx = demo_box()
    data = ctx.encode()
    print(f"DemoBox: {len(data)} bytes")
    ctx.save("demo_box.rc")
    print("Saved demo_box.rc")

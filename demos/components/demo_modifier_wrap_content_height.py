"""Atomic demo for the wrapContentHeight modifier. Port of DemoModifierWrapContentHeight.kt."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RcContext, Modifier

DKGRAY = 0xFF444444
WHITE = 0xFFFFFFFF


def demo_modifier_wrap_content_height():
    ctx = RcContext(400, 400)
    with ctx.root():
        with ctx.box(Modifier().width(100).wrap_content_height().background(DKGRAY)):
            ctx.box_leaf(Modifier().size(50).background(WHITE))
    return ctx


if __name__ == '__main__':
    ctx = demo_modifier_wrap_content_height()
    data = ctx.encode()
    print(f"DemoModifierWrapContentHeight: {len(data)} bytes")
    ctx.save("demo_modifier_wrap_content_height.rc")
    print("Saved demo_modifier_wrap_content_height.rc")

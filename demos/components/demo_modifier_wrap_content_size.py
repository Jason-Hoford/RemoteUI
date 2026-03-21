"""Atomic demo for the wrapContentSize modifier. Port of DemoModifierWrapContentSize.kt."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RcContext, Modifier

DKGRAY = 0xFF444444
WHITE = 0xFFFFFFFF


def demo_modifier_wrap_content_size():
    ctx = RcContext(400, 400)
    with ctx.root():
        with ctx.box(Modifier().wrap_content_size().background(DKGRAY)):
            ctx.box_leaf(Modifier().size(75).background(WHITE))
    return ctx


if __name__ == '__main__':
    ctx = demo_modifier_wrap_content_size()
    data = ctx.encode()
    print(f"DemoModifierWrapContentSize: {len(data)} bytes")
    ctx.save("demo_modifier_wrap_content_size.rc")
    print("Saved demo_modifier_wrap_content_size.rc")

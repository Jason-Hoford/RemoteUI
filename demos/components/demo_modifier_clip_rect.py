"""Atomic demo for the clip rect modifier. Port of DemoModifierClipRect.kt."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RcContext, Modifier, RectShape

RED = 0xFFFF0000


def demo_modifier_clip_rect():
    ctx = RcContext(400, 400)
    with ctx.root():
        ctx.box_leaf(Modifier().size(200).clip(RectShape(20, 20, 20, 20)).background(RED))
    return ctx


if __name__ == '__main__':
    ctx = demo_modifier_clip_rect()
    data = ctx.encode()
    print(f"DemoModifierClipRect: {len(data)} bytes")
    ctx.save("demo_modifier_clip_rect.rc")
    print("Saved demo_modifier_clip_rect.rc")

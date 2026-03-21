"""Atomic demo for the clip rounded rect modifier. Port of DemoModifierClipRoundedRect.kt."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RcContext, Modifier, RoundedRectShape

BLUE = 0xFF0000FF


def demo_modifier_clip_rounded_rect():
    ctx = RcContext(400, 400)
    with ctx.root():
        ctx.box_leaf(Modifier().size(200).clip(RoundedRectShape(40, 40, 40, 40)).background(BLUE))
    return ctx


if __name__ == '__main__':
    ctx = demo_modifier_clip_rounded_rect()
    data = ctx.encode()
    print(f"DemoModifierClipRoundedRect: {len(data)} bytes")
    ctx.save("demo_modifier_clip_rounded_rect.rc")
    print("Saved demo_modifier_clip_rounded_rect.rc")

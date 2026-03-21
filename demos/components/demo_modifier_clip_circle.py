"""Atomic demo for the clip circle modifier. Port of DemoModifierClipCircle.kt."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RcContext, Modifier, CircleShape

GREEN = 0xFF00FF00


def demo_modifier_clip_circle():
    ctx = RcContext(400, 400)
    with ctx.root():
        ctx.box_leaf(Modifier().size(200).clip(CircleShape()).background(GREEN))
    return ctx


if __name__ == '__main__':
    ctx = demo_modifier_clip_circle()
    data = ctx.encode()
    print(f"DemoModifierClipCircle: {len(data)} bytes")
    ctx.save("demo_modifier_clip_circle.rc")
    print("Saved demo_modifier_clip_circle.rc")

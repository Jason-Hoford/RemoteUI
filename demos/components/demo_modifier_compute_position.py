"""Atomic demo for the computePosition modifier. Port of DemoModifierComputePosition.kt.

Demonstrates custom placement logic: centering a box within its parent.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RcContext, Modifier

LTGRAY = 0xFFCCCCCC
BLUE = 0xFF0000FF


def demo_modifier_compute_position():
    ctx = RcContext(500, 500, "DemoModifierComputePosition", api_level=7, profiles=0x201)
    with ctx.root():
        with ctx.box(Modifier().fill_max_size().background(LTGRAY)):
            ctx.box_leaf(
                Modifier().size(100).background(BLUE)
                .compute_position(lambda c: (
                    setattr(c, 'x', (c.parent_width - c.width) / 2.0),
                    setattr(c, 'y', (c.parent_height - c.height) / 2.0),
                ))
            )
    return ctx


if __name__ == '__main__':
    ctx = demo_modifier_compute_position()
    data = ctx.encode()
    print(f"DemoModifierComputePosition: {len(data)} bytes")
    ctx.save("demo_modifier_compute_position.rc")
    print("Saved demo_modifier_compute_position.rc")

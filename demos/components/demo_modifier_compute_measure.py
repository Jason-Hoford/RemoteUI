"""Atomic demo for the computeMeasure modifier. Port of DemoModifierComputeMeasure.kt.

Demonstrates custom measurement logic: dynamically forces height to be 1.5x width.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RcContext, Modifier

RED = 0xFFFF0000


def demo_modifier_compute_measure():
    ctx = RcContext(500, 500, "DemoModifierComputeMeasure", api_level=7, profiles=0x201)
    with ctx.root():
        ctx.box_leaf(
            Modifier().background(RED)
            .compute_measure(lambda c: setattr(c, 'height', c.width * 1.5))
            .width(100)
        )
    return ctx


if __name__ == '__main__':
    ctx = demo_modifier_compute_measure()
    data = ctx.encode()
    print(f"DemoModifierComputeMeasure: {len(data)} bytes")
    ctx.save("demo_modifier_compute_measure.rc")
    print("Saved demo_modifier_compute_measure.rc")

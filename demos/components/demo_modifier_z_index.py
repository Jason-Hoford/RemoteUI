"""Atomic demo for the zIndex modifier. Port of DemoModifierZIndex.kt."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RcContext, Modifier

RED = 0xFFFF0000
BLUE = 0xFF0000FF


def demo_modifier_z_index():
    ctx = RcContext(400, 400)
    with ctx.root():
        with ctx.box(Modifier().fill_max_size()):
            # Red is added first, but Blue has higher zIndex so it appears on top.
            ctx.box_leaf(Modifier().size(200).background(RED))
            ctx.box_leaf(Modifier().size(150).padding(25).z_index(1.0).background(BLUE))
    return ctx


if __name__ == '__main__':
    ctx = demo_modifier_z_index()
    data = ctx.encode()
    print(f"DemoModifierZIndex: {len(data)} bytes")
    ctx.save("demo_modifier_z_index.rc")
    print("Saved demo_modifier_z_index.rc")

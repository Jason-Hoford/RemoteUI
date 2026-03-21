"""Atomic demo for the visibility modifier. Port of DemoModifierVisibility.kt."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RcContext, Modifier
from rcreate.rc import Rc
from rcreate.types.nan_utils import id_from_nan

RED = 0xFFFF0000


def demo_modifier_visibility():
    ctx = RcContext(400, 400)
    with ctx.root():
        # Blinking visibility (looping every 2 seconds)
        is_visible = ctx.float_expression(
            ctx.continuous_sec(), 2.0, Rc.FloatExpression.MOD)
        vis_id = id_from_nan(is_visible)
        ctx.box_leaf(Modifier().size(200).background(RED).visibility(vis_id))
    return ctx


if __name__ == '__main__':
    ctx = demo_modifier_visibility()
    data = ctx.encode()
    print(f"DemoModifierVisibility: {len(data)} bytes")
    ctx.save("demo_modifier_visibility.rc")
    print("Saved demo_modifier_visibility.rc")

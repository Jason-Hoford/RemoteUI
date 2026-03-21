"""Atomic demo for the StateLayout component. Port of DemoStateLayout.kt."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RcContext, Modifier
from rcreate.rc import Rc
from rcreate.types.nan_utils import id_from_nan

RED = 0xFFFF0000
BLUE = 0xFF0000FF


def demo_state_layout():
    ctx = RcContext(400, 400)
    with ctx.root():
        # State index loops from 0 to 1 every 2 seconds
        state = ctx.float_expression(
            ctx.continuous_sec(), 2.0, Rc.FloatExpression.MOD)
        with ctx.state_layout(Modifier().fill_max_size(), id_from_nan(state)):
            # State 0
            ctx.box_leaf(Modifier().fill_max_size().background(RED))
            # State 1
            ctx.box_leaf(Modifier().fill_max_size().background(BLUE))
    return ctx


if __name__ == '__main__':
    ctx = demo_state_layout()
    data = ctx.encode()
    print(f"DemoStateLayout: {len(data)} bytes")
    ctx.save("demo_state_layout.rc")
    print("Saved demo_state_layout.rc")

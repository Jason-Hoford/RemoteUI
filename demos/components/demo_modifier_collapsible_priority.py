"""Atomic demo for the collapsiblePriority modifier. Port of DemoModifierCollapsiblePriority.kt."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RcContext, Modifier
from rcreate.modifiers.elements import CollapsiblePriorityModifier

LTGRAY = 0xFFCCCCCC
RED = 0xFFFF0000
BLUE = 0xFF0000FF


def demo_modifier_collapsible_priority():
    ctx = RcContext(400, 400)
    with ctx.root():
        with ctx.collapsible_row(
            Modifier().fill_max_width().height(100).background(LTGRAY),
            horizontal=1, vertical=1
        ):
            # Priority 1: Hides last
            ctx.box_leaf(
                Modifier().size(100).background(RED)
                .collapsible_priority(CollapsiblePriorityModifier.HORIZONTAL, 1.0)
            )
            # Priority 2: Hides first
            ctx.box_leaf(
                Modifier().size(100).background(BLUE)
                .collapsible_priority(CollapsiblePriorityModifier.HORIZONTAL, 2.0)
            )
    return ctx


if __name__ == '__main__':
    ctx = demo_modifier_collapsible_priority()
    data = ctx.encode()
    print(f"DemoModifierCollapsiblePriority: {len(data)} bytes")
    ctx.save("demo_modifier_collapsible_priority.rc")
    print("Saved demo_modifier_collapsible_priority.rc")

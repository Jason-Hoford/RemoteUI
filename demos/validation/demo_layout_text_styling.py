"""Validation demo: combined layout, text, and styling.

Exercises:
- Nested Column > Row > Box layout
- Multiple text styles (size, weight, color)
- Background colors and padding
- fill_max_size, fill_max_width, height modifiers
- Text alignment and anchoring
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RcContext, Rc
from rcreate.modifiers import RecordingModifier

PROFILE_ANDROIDX = 0x200


def demo_layout_text_styling():
    ctx = RcContext(400, 600, "Layout+Text+Style", api_level=7,
                    profiles=PROFILE_ANDROIDX)

    with ctx.root():
        with ctx.column(RecordingModifier().fill_max_size()
                        .background(0xFFEEEEEE)):

            # Title row with dark background
            with ctx.box(RecordingModifier().fill_max_width().height(80.0)
                         .background(0xFF2244AA),
                         Rc.Layout.CENTER, Rc.Layout.CENTER):
                ctx.text("Dashboard", font_size=32.0, color=0xFFFFFFFF,
                         font_weight=700)

            # Two-column data section
            with ctx.row(RecordingModifier().fill_max_width().height(120.0)):
                # Left card
                with ctx.box(RecordingModifier().width(190.0).height(100.0)
                             .background(0xFFFFFFFF)
                             .padding(8.0),
                             Rc.Layout.START, Rc.Layout.TOP):
                    ctx.text("Temperature", font_size=14.0,
                             color=0xFF888888)
                # Right card
                with ctx.box(RecordingModifier().width(190.0).height(100.0)
                             .background(0xFFFFFFFF)
                             .padding(8.0),
                             Rc.Layout.START, Rc.Layout.TOP):
                    ctx.text("Humidity", font_size=14.0,
                             color=0xFF888888)

            # Status section
            with ctx.box(RecordingModifier().fill_max_width().height(60.0)
                         .background(0xFF44AA22),
                         Rc.Layout.CENTER, Rc.Layout.CENTER):
                ctx.text("System OK", font_size=20.0, color=0xFFFFFFFF,
                         font_weight=500)

            # Canvas section with drawn text
            with ctx.box(RecordingModifier().fill_max_size(),
                         Rc.Layout.START, Rc.Layout.START):
                with ctx.canvas(RecordingModifier().fill_max_size()
                                .background(0xFF334455)):
                    ctx.painter.set_color(0xFFFFCC00).set_text_size(24.0) \
                        .commit()
                    ctx.draw_text_anchored("Canvas Text", 200.0, 50.0,
                                           0.0, 0.0, 0)

                    # Draw colored rectangles
                    ctx.painter.set_color(0x44FF0000).commit()
                    ctx.draw_rect(20.0, 80.0, 180.0, 150.0)
                    ctx.painter.set_color(0x4400FF00).commit()
                    ctx.draw_rect(100.0, 100.0, 280.0, 170.0)
                    ctx.painter.set_color(0x440000FF).commit()
                    ctx.draw_rect(200.0, 120.0, 380.0, 190.0)

    return ctx


if __name__ == '__main__':
    ctx = demo_layout_text_styling()
    data = ctx.encode()
    outdir = os.path.join(os.path.dirname(__file__), '..', 'output')
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, 'val_layout_text_styling.rc')
    ctx.save(path)
    print(f"val_layout_text_styling: {len(data)} bytes -> {path}")

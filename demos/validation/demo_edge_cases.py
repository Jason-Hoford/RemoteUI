"""Validation demo: edge cases and stress scenarios.

Exercises:
- Very small and very large float values
- Many nested save/restore (10+ deep)
- Large number of draw operations (100+ circles)
- Empty-ish components (box with no content)
- Multiple paint commits in sequence
- Paths with many points
- Named colors
- Multiple text strings
- Overlapping elements
"""
import sys
import os
import math

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RcContext, Rc
from rcreate.modifiers import RecordingModifier

PROFILE_ANDROIDX = 0x200
STYLE_FILL = Rc.Paint.STYLE_FILL
STYLE_STROKE = Rc.Paint.STYLE_STROKE


def demo_edge_cases():
    ctx = RcContext(500, 500, "Edge Cases", api_level=7,
                    profiles=PROFILE_ANDROIDX)

    with ctx.root():
        with ctx.box(RecordingModifier().fill_max_size(),
                     Rc.Layout.START, Rc.Layout.START):
            with ctx.canvas(RecordingModifier().fill_max_size()
                            .background(0xFF111111)):

                # Test 1: Very small stroke width
                ctx.painter.set_color(0xFFFFFFFF) \
                    .set_style(STYLE_STROKE) \
                    .set_stroke_width(0.5).commit()
                ctx.draw_line(10.0, 10.0, 490.0, 10.0)

                # Test 2: Many paint state changes
                for i in range(10):
                    color = 0xFF000000 | (i * 25 << 16) | (255 - i * 25)
                    ctx.painter.set_color(color) \
                        .set_stroke_width(float(i + 1)) \
                        .set_style(STYLE_STROKE).commit()
                    ctx.draw_line(10.0, 20.0 + i * 8.0,
                                 200.0, 20.0 + i * 8.0)

                # Test 3: Deep nested save/restore (10 levels)
                ctx.painter.set_color(0xFF44FF44) \
                    .set_style(STYLE_FILL).commit()
                for depth in range(10):
                    ctx._writer.save()
                    ctx.rotate(5.0, 350.0, 60.0)
                    ctx.draw_rect(330.0, 40.0, 370.0, 80.0)
                for depth in range(10):
                    ctx._writer.restore()

                # Test 4: 100 circles in a grid pattern
                ctx.painter.set_color(0x44FFAA00) \
                    .set_style(STYLE_FILL).commit()
                for row in range(10):
                    for col in range(10):
                        x = 30.0 + col * 45.0
                        y = 150.0 + row * 30.0
                        ctx.draw_circle(x, y, 8.0)

                # Test 5: Path with many points (smooth curve)
                from rcreate import RemotePath
                curve = RemotePath()
                curve.move_to(10.0, 470.0)
                for i in range(1, 100):
                    x = 10.0 + i * 4.8
                    y = 470.0 - math.sin(i * 0.15) * 40.0
                    curve.line_to(x, y)
                curve_id = ctx.add_path_data(curve.to_float_array())
                ctx.painter.set_color(0xFFFF44FF) \
                    .set_style(STYLE_STROKE) \
                    .set_stroke_width(2.0).commit()
                ctx.draw_path(curve_id)

                # Test 6: Named color
                nc_id = ctx.writer.add_named_color(
                    "android.colorPrimary", 0xFF6200EE)
                ctx.painter.set_color_id(nc_id).set_style(STYLE_FILL) \
                    .commit()
                ctx.draw_rect(10.0, 120.0, 100.0, 145.0)

                # Test 7: Multiple text strings
                ctx.painter.set_color(0xFFCCCCCC) \
                    .set_text_size(12.0) \
                    .set_style(STYLE_FILL).commit()
                texts = ["Alpha", "Beta", "Gamma", "Delta", "Epsilon"]
                for i, t in enumerate(texts):
                    ctx.draw_text_anchored(t, 400.0, 120.0 + i * 18.0,
                                           0.0, 0.0, 0)

                # Test 8: Overlapping semi-transparent rects
                for i in range(5):
                    alpha = 0x33 + i * 0x20
                    color = (alpha << 24) | 0x0088FF
                    ctx.painter.set_color(color).commit()
                    ctx.draw_rect(200.0 + i * 15.0, 120.0,
                                  280.0 + i * 15.0, 145.0)

    return ctx


if __name__ == '__main__':
    ctx = demo_edge_cases()
    data = ctx.encode()
    outdir = os.path.join(os.path.dirname(__file__), '..', 'output')
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, 'val_edge_cases.rc')
    ctx.save(path)
    print(f"val_edge_cases: {len(data)} bytes -> {path}")

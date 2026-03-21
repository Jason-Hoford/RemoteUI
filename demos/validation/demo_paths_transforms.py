"""Validation demo: paths and matrix transforms.

Exercises:
- RemotePath with moveTo, lineTo, cubicTo, close
- Path from SVG string (add_path_string)
- Matrix save/restore nesting
- Rotate, scale, translate
- Multiple paths drawn with different styles (fill, stroke)
- Path expression (parametric curve)
"""
import sys
import os
import math

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RcContext, Rc, RemotePath
from rcreate.modifiers import RecordingModifier

PROFILE_ANDROIDX = 0x200
STYLE_FILL = Rc.Paint.STYLE_FILL
STYLE_STROKE = Rc.Paint.STYLE_STROKE
CAP_ROUND = Rc.Paint.CAP_ROUND


def demo_paths_transforms():
    ctx = RcContext(500, 500, "Paths+Transforms", api_level=7,
                    profiles=PROFILE_ANDROIDX)

    with ctx.root():
        with ctx.box(RecordingModifier().fill_max_size(),
                     Rc.Layout.START, Rc.Layout.START):
            with ctx.canvas(RecordingModifier().fill_max_size()
                            .background(0xFF1A1A2E)):
                w = ctx.ComponentWidth()
                h = ctx.ComponentHeight()
                cx = (w / 2.0).to_float()
                cy = (h / 2.0).to_float()

                # Star path using RemotePath
                star = RemotePath()
                for i in range(5):
                    angle = math.radians(i * 144 - 90)
                    x = 250 + 120 * math.cos(angle)
                    y = 250 + 120 * math.sin(angle)
                    if i == 0:
                        star.move_to(x, y)
                    else:
                        star.line_to(x, y)
                star.close()
                star_id = ctx.add_path_data(star.to_float_array())

                # Filled star
                ctx.painter.set_color(0xFFFFD700).set_style(STYLE_FILL) \
                    .commit()
                ctx.draw_path(star_id)

                # Stroked star with transform
                ctx.painter.set_color(0xFFFF4444).set_style(STYLE_STROKE) \
                    .set_stroke_width(3.0).commit()

                with ctx.saved():
                    ctx.rotate(36.0, cx, cy)
                    ctx.draw_path(star_id)

                # Heart path using RemotePath
                heart = RemotePath()
                heart.move_to(250, 150)
                heart.cubic_to(250, 80, 180, 50, 150, 100)
                heart.cubic_to(120, 150, 200, 220, 250, 280)
                heart.move_to(250, 150)
                heart.cubic_to(250, 80, 320, 50, 350, 100)
                heart.cubic_to(380, 150, 300, 220, 250, 280)
                heart.close()
                heart_id = ctx.add_path_data(heart.to_float_array())

                # Draw scaled heart in corner
                ctx.painter.set_color(0xFFFF6B9D).set_style(STYLE_FILL) \
                    .commit()
                with ctx.saved():
                    ctx.translate(0.0, 0.0)
                    ctx.scale(0.3, 0.3)
                    ctx.draw_path(heart_id)

                # Animated parametric path expression (Lissajous curve)
                t = ctx.ContinuousSec()
                equ = ctx.r_fun(
                    lambda x: (x + t * 2.0).sin() * 100.0
                )
                path_expr_id = ctx.add_path_expression(
                    ctx.r_fun(lambda x: x * 50.0 + 250.0).to_array(),
                    (equ + 250.0).to_array(),
                    -math.pi, math.pi, 64,
                    Rc.PathExpression.SPLINE_PATH)

                ctx.painter.set_color(0xFF00FFAA).set_style(STYLE_STROKE) \
                    .set_stroke_width(2.0).set_stroke_cap(CAP_ROUND) \
                    .commit()
                ctx.draw_path(path_expr_id)

                # Nested transforms: concentric rotating squares
                ctx.painter.set_color(0x88FFFFFF).set_style(STYLE_STROKE) \
                    .set_stroke_width(1.0).commit()
                for i in range(6):
                    with ctx.saved():
                        angle = (t * (30.0 + i * 10.0)).to_float()
                        ctx.rotate(angle, cx, cy)
                        half = 40 + i * 20
                        ctx.draw_rect(250.0 - half, 250.0 - half,
                                      250.0 + half, 250.0 + half)

    return ctx


if __name__ == '__main__':
    ctx = demo_paths_transforms()
    data = ctx.encode()
    outdir = os.path.join(os.path.dirname(__file__), '..', 'output')
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, 'val_paths_transforms.rc')
    ctx.save(path)
    print(f"val_paths_transforms: {len(data)} bytes -> {path}")

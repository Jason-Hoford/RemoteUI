"""Rotating wireframe cube -> wireframe_cube.rc

A 3D cube projected to 2D, rotating on X+Y axes simultaneously. Inspired
by the pygame OpenGL demo at C:/Users/jason/Downloads/hard_to_see/
pygame_noise_3d.py — minus the stencil/noise mask, which would need
shaders the format doesn't expose.

How it stays compact: the four trig values cos(θx), sin(θx), cos(θy),
sin(θy) are flushed once as shared expressions, then each of the 8
cube vertices reads them via NaN-encoded references. Each vertex's
projected (x, y) is a small linear combo of constants × those four
shared values. 12 edges = 12 draw_line calls referencing vertex IDs.
"""
import sys
import os
import math

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RcContext, Rc
from rcreate.modifiers import RecordingModifier
from rcreate.types.rfloat import rf_sin, rf_cos


PROFILE_ANDROIDX = 0x200
STYLE_FILL = Rc.Paint.STYLE_FILL
STYLE_STROKE = Rc.Paint.STYLE_STROKE
CAP_ROUND = Rc.Paint.CAP_ROUND


def demo_wireframe_cube():
    width, height = 500, 500
    ctx = RcContext(width, height, "Wireframe Cube",
                    api_level=7, profiles=PROFILE_ANDROIDX)

    cx, cy = width / 2.0, height / 2.0
    scale = 110.0

    # Rotation rates (rad/sec) — non-zero on both axes so motion is always present
    omega_x = 0.6
    omega_y = 0.9

    with ctx.root():
        with ctx.box(RecordingModifier().fill_max_size().background(0xFF050814),
                     Rc.Layout.START, Rc.Layout.START):
            with ctx.canvas(RecordingModifier().fill_max_size()):
                # Faint static background grid for spatial reference
                ctx.painter.set_color(0xFF0F1626) \
                    .set_style(STYLE_STROKE) \
                    .set_stroke_width(1.0).commit()
                for x in range(50, width, 50):
                    ctx.draw_line(float(x), 0.0, float(x), float(height))
                for y in range(50, height, 50):
                    ctx.draw_line(0.0, float(y), float(width), float(y))

                t = ctx.animationTime()

                # Flush the four trig expressions so each vertex below references
                # them by ID rather than re-computing 8x.
                cos_x = rf_cos(t * omega_x).flush()
                sin_x = rf_sin(t * omega_x).flush()
                cos_y = rf_cos(t * omega_y).flush()
                sin_y = rf_sin(t * omega_y).flush()

                # Cube unit vertices (corners of [-1,1]^3)
                corners = []
                for sx in (-1.0, 1.0):
                    for sy in (-1.0, 1.0):
                        for sz in (-1.0, 1.0):
                            corners.append((sx, sy, sz))

                # Build 8 vertex projections — flushed so each can be reused.
                # Rotation: first around Y (sx, sz mix), then around X (sy, z_rot mix).
                # 2D output uses ortho projection (drop final z).
                projected = []
                for (x, y, z) in corners:
                    # After Y-rotation:
                    x_rot = x * cos_y + z * sin_y          # RFloat
                    z_rot = z * cos_y + (-x) * sin_y       # RFloat
                    # After X-rotation:
                    y_rot = y * cos_x - z_rot * sin_x      # RFloat (y is float)
                    # Final 2D (orthographic, scaled, centered)
                    px = (cx + scale * x_rot).flush()
                    py = (cy + scale * y_rot).flush()
                    projected.append((px, py))

                # 12 edges: pairs of corner indices that differ in exactly one axis.
                # Encoding: corners[] is indexed by (sx, sy, sz) flags packed into
                # idx = ((sx==1)<<2) | ((sy==1)<<1) | (sz==1).
                def idx(sx, sy, sz):
                    return ((1 if sx > 0 else 0) << 2) | \
                           ((1 if sy > 0 else 0) << 1) | \
                           ((1 if sz > 0 else 0))

                edges = []
                for s1 in (-1, 1):
                    for s2 in (-1, 1):
                        # X-aligned edges (vary sx, fix sy=s1, sz=s2)
                        edges.append((idx(-1, s1, s2), idx(1, s1, s2)))
                        # Y-aligned edges (vary sy, fix sx=s1, sz=s2)
                        edges.append((idx(s1, -1, s2), idx(s1, 1, s2)))
                        # Z-aligned edges (vary sz, fix sx=s1, sy=s2)
                        edges.append((idx(s1, s2, -1), idx(s1, s2, 1)))

                # Edges are 36 pairs above (12 edges × 3 axes — overcounting by 3).
                # Dedupe.
                edges = list({tuple(sorted(e)) for e in edges})

                # Edge stroke
                ctx.painter.set_color(0xFF38BDF8) \
                    .set_style(STYLE_STROKE) \
                    .set_stroke_width(2.0) \
                    .set_stroke_cap(CAP_ROUND).commit()

                for (a, b) in edges:
                    ax, ay = projected[a]
                    bx, by = projected[b]
                    ctx.draw_line(ax.to_float(), ay.to_float(),
                                  bx.to_float(), by.to_float())

                # Vertex dots — small bright pip at each corner so the rotation
                # is unmistakable
                ctx.painter.set_color(0xFFFBBF24).set_style(STYLE_FILL).commit()
                for (px, py) in projected:
                    ctx.draw_circle(px.to_float(), py.to_float(), 3.0)

                # Anchor dot at center for spatial reference
                ctx.painter.set_color(0xFFEF4444).commit()
                ctx.draw_circle(cx, cy, 2.0)

    return ctx


if __name__ == '__main__':
    ctx = demo_wireframe_cube()
    data = ctx.encode()
    outdir = os.path.join(os.path.dirname(__file__), '..', 'output')
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, 'wireframe_cube.rc')
    ctx.save(path)
    print(f"wireframe_cube: {len(data)} bytes -> {path}")

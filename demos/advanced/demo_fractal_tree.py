"""Self-similar fractal tree -> fractal_tree.rc

Recursive binary tree generated at script time. Trunk + branches are
baked as static draw_line ops; only the leaves at depth 6 wobble with
time-driven jitter so the canopy gently flutters while the structure
holds still. Demonstrates the "AI generated this fractal" angle —
pure Python recursion → compact static .rc with subtle animation.
"""
import sys
import os
import math
import random

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RcContext, Rc
from rcreate.modifiers import RecordingModifier
from rcreate.types.rfloat import rf_sin, rf_cos


PROFILE_ANDROIDX = 0x200
STYLE_FILL = Rc.Paint.STYLE_FILL
STYLE_STROKE = Rc.Paint.STYLE_STROKE
CAP_ROUND = Rc.Paint.CAP_ROUND


# Tree parameters
DEPTH = 6
INITIAL_LEN = 110.0
SHRINK = 0.72
BRANCH_DEG = 22.0
WOBBLE_AMP = 5.0
WOBBLE_FREQ = 1.6  # rad/sec on the tip phase

LEAF_COLORS = [0xFF34D399, 0xFF4ADE80, 0xFFA3E635,
               0xFF22D3EE, 0xFF38BDF8, 0xFFFBBF24]


def demo_fractal_tree():
    width, height = 500, 500
    ctx = RcContext(width, height, "Fractal Tree",
                    api_level=7, profiles=PROFILE_ANDROIDX)

    base_x = width / 2.0
    base_y = float(height) - 30.0

    # Recursively collect (x0, y0, x1, y1, depth, branch_thickness) for every segment
    stems = []
    leaves = []  # tip parent (x, y), tip static (ex, ey), depth
    rng = random.Random(20260501)  # deterministic so size stays predictable

    def grow(x, y, angle_rad, length, depth):
        ex = x + math.sin(angle_rad) * length
        ey = y - math.cos(angle_rad) * length
        if depth == 0:
            # Leaf — record parent->tip; the tip will wobble at draw time.
            leaves.append((x, y, ex, ey))
            return
        stems.append((x, y, ex, ey, depth))
        # Slight asymmetry per branch — looks more organic than a perfect
        # symmetric tree. Same seed every run, same .rc bytes.
        wobble_l = rng.uniform(-3.0, 3.0) * math.pi / 180.0
        wobble_r = rng.uniform(-3.0, 3.0) * math.pi / 180.0
        len_l = length * SHRINK * rng.uniform(0.95, 1.05)
        len_r = length * SHRINK * rng.uniform(0.95, 1.05)
        grow(ex, ey, angle_rad - math.radians(BRANCH_DEG) + wobble_l, len_l, depth - 1)
        grow(ex, ey, angle_rad + math.radians(BRANCH_DEG) + wobble_r, len_r, depth - 1)

    grow(base_x, base_y, 0.0, INITIAL_LEN, DEPTH)

    with ctx.root():
        with ctx.box(RecordingModifier().fill_max_size().background(0xFF0A1118),
                     Rc.Layout.START, Rc.Layout.START):
            with ctx.canvas(RecordingModifier().fill_max_size()):
                # Faint horizon line at the base
                ctx.painter.set_color(0xFF1F2937) \
                    .set_style(STYLE_STROKE) \
                    .set_stroke_width(1.0).commit()
                ctx.draw_line(0.0, base_y, float(width), base_y)

                # Stems — group by depth so each depth-band emits a single paint op
                # then a contiguous run of draw_line calls. ~6 paints instead of 127.
                stems_by_depth = {}
                for (x0, y0, x1, y1, d) in stems:
                    stems_by_depth.setdefault(d, []).append((x0, y0, x1, y1))
                for d in sorted(stems_by_depth.keys(), reverse=True):
                    width_px = 1.0 + d * 0.9
                    blend = d / DEPTH
                    r = int(0x6E + (0x8B - 0x6E) * (1 - blend))
                    g = int(0x4F + (0x73 - 0x4F) * (1 - blend))
                    b = int(0x35 + (0x4A - 0x35) * (1 - blend))
                    color = 0xFF000000 | (r << 16) | (g << 8) | b
                    ctx.painter.set_color(color) \
                        .set_style(STYLE_STROKE) \
                        .set_stroke_width(width_px) \
                        .set_stroke_cap(CAP_ROUND).commit()
                    for (x0, y0, x1, y1) in stems_by_depth[d]:
                        ctx.draw_line(x0, y0, x1, y1)

                # Wind: one shared sway, every leaf references it via a NaN id.
                t = ctx.animationTime()
                wind_dx = (rf_sin(t * 0.9) * WOBBLE_AMP).flush()
                wind_dy = (rf_cos(t * 0.9) * (WOBBLE_AMP * 0.4)).flush()

                # Pre-flush each leaf's tip_x and tip_y exactly once so the same
                # NaN id is reused by both the leaf-stem line and the dot circle.
                tip_xs, tip_ys = [], []
                for (x0, y0, ex, ey) in leaves:
                    tip_xs.append((ex + wind_dx).flush().to_float())
                    tip_ys.append((ey + wind_dy).flush().to_float())

                # Stems (all same color, one paint op).
                ctx.painter.set_color(0xFF8B7355) \
                    .set_style(STYLE_STROKE) \
                    .set_stroke_width(1.0) \
                    .set_stroke_cap(CAP_ROUND).commit()
                for k, (x0, y0, _ex, _ey) in enumerate(leaves):
                    ctx.draw_line(x0, y0, tip_xs[k], tip_ys[k])

                # Leaf dots — group by color so we emit each set_color only once.
                ctx.painter.set_style(STYLE_FILL).commit()
                for color_idx, color in enumerate(LEAF_COLORS):
                    ctx.painter.set_color(color).commit()
                    for k in range(len(leaves)):
                        if k % len(LEAF_COLORS) != color_idx:
                            continue
                        ctx.draw_circle(tip_xs[k], tip_ys[k], 3.0)

    return ctx


if __name__ == '__main__':
    ctx = demo_fractal_tree()
    data = ctx.encode()
    outdir = os.path.join(os.path.dirname(__file__), '..', 'output')
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, 'fractal_tree.rc')
    ctx.save(path)
    print(f"fractal_tree: {len(data)} bytes -> {path}")

"""Clockwork gears -> clockwork.rc

Five interlocking gears with mechanically correct angular rates:
adjacent gears mesh, so ω_a · r_a = ω_b · r_b and they spin in opposite
directions. Each gear's teeth are drawn as small dots whose positions
are computed per-frame via RFloat expressions — sin/cos of (animation
time × ω + base angle).

Demonstrates the "sophisticated mechanical simulation" angle. Pure
vector demo, no shader. Total .rc ~6 KB for 5 gears × 18 teeth = 90
animated dots plus rotating axle marker lines.
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


def demo_clockwork():
    width, height = 700, 500
    ctx = RcContext(width, height, "Clockwork",
                    api_level=8, profiles=PROFILE_ANDROIDX)

    # Gear chain — radii chosen so adjacent pairs mesh tooth-to-tooth.
    # Centers are placed so distance between adjacent centers = r_a + r_b.
    # Direction alternates (every other gear spins backwards).
    cy = 250.0
    base_omega = 0.5  # rad/sec for the leftmost gear

    gears = []  # (cx, cy, radius, omega, color, n_teeth)
    palette = [0xFFFBBF24, 0xFF38BDF8, 0xFFEF4444, 0xFFA78BFA, 0xFF34D399]
    radii   = [70.0, 50.0, 60.0, 40.0, 55.0]
    n_teeth = [22, 18, 20, 14, 18]

    # First gear's center
    cx = 90.0 + radii[0]
    direction = 1.0
    omega = base_omega
    for i, r in enumerate(radii):
        gears.append((cx, cy, r, omega * direction, palette[i], n_teeth[i]))
        if i + 1 < len(radii):
            # Next gear's center is r + r_next away from current
            cx += r + radii[i + 1]
            # Adjacent gears spin opposite directions; ω scales by ratio
            omega = omega * (r / radii[i + 1])
            direction = -direction

    t = ctx.animationTime()

    with ctx.root():
        with ctx.box(RecordingModifier().fill_max_size().background(0xFF0F1419),
                     Rc.Layout.START, Rc.Layout.START):
            with ctx.canvas(RecordingModifier().fill_max_size()):
                # ---- Mounting plate (background panel) ----
                ctx.painter.set_color(0xFF1F2937).set_style(STYLE_FILL).commit()
                ctx.draw_round_rect(20.0, cy - 110.0,
                                    float(width) - 20.0, cy + 110.0,
                                    20.0, 20.0)
                ctx.painter.set_color(0xFF374151).set_style(STYLE_STROKE).set_stroke_width(2.0).commit()
                ctx.draw_round_rect(20.0, cy - 110.0,
                                    float(width) - 20.0, cy + 110.0,
                                    20.0, 20.0)

                # ---- For each gear ----
                for (gcx, gcy, r, w, color, nteeth) in gears:
                    # Outer body (filled disk)
                    ctx.painter.set_color(color).set_style(STYLE_FILL).commit()
                    ctx.draw_circle(gcx, gcy, r)
                    # Darker inner ring
                    ctx.painter.set_color((color & 0x00FFFFFF) | 0xFF000000) \
                        .set_color(_dim(color, 0.55)).commit()
                    ctx.draw_circle(gcx, gcy, r * 0.55)
                    # Hub
                    ctx.painter.set_color(0xFF111827).commit()
                    ctx.draw_circle(gcx, gcy, r * 0.18)
                    # Hub pivot pin
                    ctx.painter.set_color(0xFFE5E7EB).commit()
                    ctx.draw_circle(gcx, gcy, r * 0.06)

                    # Teeth — dots around perimeter rotating at angular velocity w
                    rot = (t * w).flush()        # current rotation angle (rad)
                    tooth_r_outer = r * 0.94     # tooth's distance from center
                    ctx.painter.set_color(_brighten(color, 1.15)).set_style(STYLE_FILL).commit()
                    for k in range(nteeth):
                        base_a = k * (2.0 * math.pi / nteeth)
                        ang = rot + base_a
                        tx = gcx + rf_cos(ang) * tooth_r_outer
                        ty = gcy + rf_sin(ang) * tooth_r_outer
                        ctx.draw_circle(tx.to_float(), ty.to_float(), max(2.0, r * 0.06))

                    # Spoke — short line from center to outer at base angle 0,
                    # so the eye can catch the rotation direction.
                    spoke_x = gcx + rf_cos(rot) * (r * 0.45)
                    spoke_y = gcy + rf_sin(rot) * (r * 0.45)
                    ctx.painter.set_color(0xFFFFFFFF) \
                        .set_style(STYLE_STROKE) \
                        .set_stroke_width(2.0) \
                        .set_stroke_cap(CAP_ROUND).commit()
                    ctx.draw_line(gcx, gcy, spoke_x.to_float(), spoke_y.to_float())

    return ctx


def _dim(color: int, factor: float) -> int:
    a = (color >> 24) & 0xFF
    r = int(((color >> 16) & 0xFF) * factor)
    g = int(((color >> 8)  & 0xFF) * factor)
    b = int((color         & 0xFF) * factor)
    return (a << 24) | (r << 16) | (g << 8) | b


def _brighten(color: int, factor: float) -> int:
    a = (color >> 24) & 0xFF
    r = min(255, int(((color >> 16) & 0xFF) * factor))
    g = min(255, int(((color >> 8)  & 0xFF) * factor))
    b = min(255, int((color          & 0xFF) * factor))
    return (a << 24) | (r << 16) | (g << 8) | b


if __name__ == '__main__':
    ctx = demo_clockwork()
    data = ctx.encode()
    outdir = os.path.join(os.path.dirname(__file__), '..', 'output')
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, 'clockwork.rc')
    ctx.save(path)
    print(f"clockwork: {len(data)} bytes -> {path}")

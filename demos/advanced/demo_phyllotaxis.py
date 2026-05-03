"""Phyllotaxis sunflower spiral -> phyllotaxis.rc

Golden-angle scatter (137.508°) of N=400 dots, the same packing pattern
sunflower seeds use. Dots are statically placed; a single shared time-
driven `pulse` value scales every dot's draw radius, so the whole
field "breathes" without 800+ per-dot expressions.

Tiny radial color band: dots toward the center are warmer; outer
dots are cooler. Generated entirely from k.
"""
import sys
import os
import math

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RcContext, Rc
from rcreate.modifiers import RecordingModifier
from rcreate.types.rfloat import rf_sin


PROFILE_ANDROIDX = 0x200
STYLE_FILL = Rc.Paint.STYLE_FILL


N_SEEDS = 400
GOLDEN_ANGLE_DEG = 137.50776405003785  # exact: 360 * (1 - 1/φ²)
SCALE = 11.5    # how spread out the spiral is (px per √k unit)
PULSE_FREQ = 1.5  # rad/sec on the breathing pulse


# Warm → cool palette (5 bands)
PALETTE = [0xFFFBBF24, 0xFFF59E0B, 0xFFEF4444,
           0xFFA78BFA, 0xFF38BDF8]


def demo_phyllotaxis():
    width, height = 500, 500
    ctx = RcContext(width, height, "Phyllotaxis",
                    api_level=7, profiles=PROFILE_ANDROIDX)

    cx, cy = width / 2.0, height / 2.0
    golden_rad = math.radians(GOLDEN_ANGLE_DEG)

    # Pre-compute every seed's (x, y) statically — pure geometry, no animation.
    seeds = []  # (x, y, color_idx)
    for k in range(1, N_SEEDS + 1):
        r = SCALE * math.sqrt(k)
        theta = k * golden_rad
        x = cx + r * math.cos(theta)
        y = cy + r * math.sin(theta)
        # Skip seeds that fall outside canvas
        if x < 5.0 or x > width - 5.0 or y < 5.0 or y > height - 5.0:
            continue
        # Color band by radial distance — 5 rings from center outward
        band = min(int((r / 220.0) * len(PALETTE)), len(PALETTE) - 1)
        seeds.append((x, y, band))

    with ctx.root():
        with ctx.box(RecordingModifier().fill_max_size().background(0xFF050814),
                     Rc.Layout.START, Rc.Layout.START):
            with ctx.canvas(RecordingModifier().fill_max_size()):
                # One shared "breathing" pulse — every dot's radius references it
                # via NaN id, so seeds add ~zero extra expression bytes.
                t = ctx.animationTime()
                # Pulse oscillates 2.0 .. 4.0 px (radius)
                pulse_rf = (rf_sin(t * PULSE_FREQ) + 1.0) * 1.0 + 2.0  # 2..4
                pulse_id = pulse_rf.flush().to_float()

                # Group seeds by color band so we emit each set_color once.
                ctx.painter.set_style(STYLE_FILL).commit()
                for band_idx, color in enumerate(PALETTE):
                    ctx.painter.set_color(color).commit()
                    for (x, y, band) in seeds:
                        if band != band_idx:
                            continue
                        ctx.draw_circle(x, y, pulse_id)

                # Subtle center marker — a tiny static dot to anchor the eye
                ctx.painter.set_color(0xFFFFFFFF).commit()
                ctx.draw_circle(cx, cy, 1.5)

    return ctx


if __name__ == '__main__':
    ctx = demo_phyllotaxis()
    data = ctx.encode()
    outdir = os.path.join(os.path.dirname(__file__), '..', 'output')
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, 'phyllotaxis.rc')
    ctx.save(path)
    print(f"phyllotaxis: {len(data)} bytes -> {path}")

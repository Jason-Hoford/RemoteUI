"""Galileo pendulum wave -> pendulum_wave.rc

Sixteen pendulums of progressively different lengths, all started in
phase. They drift out of phase (snake, scatter), then resync at a
60-second beat.

Math: pendulum i completes (N + i) cycles per 60 seconds, with N=14.
So all 16 are simultaneously back in phase exactly when t mod 60 = 0.
Iconic physics demo, very satisfying to watch.
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


def demo_pendulum_wave():
    width, height = 600, 400
    ctx = RcContext(width, height, "Pendulum Wave",
                    api_level=7, profiles=PROFILE_ANDROIDX)

    n_pendulums = 16
    pivot_y = 60.0
    bob_radius = 10.0
    spacing = (width - 80.0) / (n_pendulums - 1)
    start_x = 40.0

    # Length tuning: longer = slower. Period_i = 60 / (N + i) sec for resync at 60s.
    # Convert to length via T = 2π√(L/g) but here we just pick lengths that fit.
    base_period_count = 14    # i=0 completes 14 cycles in 60s (period ≈ 4.286 s)
    full_resync_period = 60.0
    max_amp_rad = math.radians(36.0)   # initial swing angle from vertical

    # Color palette — rainbow across pendulums
    palette = [
        0xFFEF4444, 0xFFF97316, 0xFFFB923C, 0xFFFBBF24,
        0xFFA3E635, 0xFF34D399, 0xFF22D3EE, 0xFF38BDF8,
        0xFF60A5FA, 0xFF818CF8, 0xFFA78BFA, 0xFFC084FC,
        0xFFE879F9, 0xFFF472B6, 0xFFFB7185, 0xFFEF4444,
    ]

    with ctx.root():
        with ctx.box(RecordingModifier().fill_max_size().background(0xFF0A0E1A),
                     Rc.Layout.START, Rc.Layout.START):
            with ctx.canvas(RecordingModifier().fill_max_size()):
                # Pivot rail
                ctx.painter.set_color(0xFF22304E) \
                    .set_style(STYLE_STROKE) \
                    .set_stroke_width(2.0).commit()
                ctx.draw_line(start_x - 10.0, pivot_y,
                              start_x + (n_pendulums - 1) * spacing + 10.0, pivot_y)

                t = ctx.animationTime()

                # Compute and flush each bob position once for reuse in line + circle.
                bob_xs, bob_ys = [], []
                for i in range(n_pendulums):
                    pivot_x = start_x + i * spacing
                    L = 80.0 + i * 12.0   # 80, 92, 104, ..., 260 px
                    cycles = base_period_count + i
                    omega = (2.0 * math.pi * cycles) / full_resync_period
                    # angle(t) = max_amp * cos(omega * t)
                    angle = rf_cos(t * omega) * max_amp_rad
                    # bob_x = pivot_x + L * sin(angle); bob_y = pivot_y + L * cos(angle)
                    bx = (pivot_x + rf_sin(angle) * L).flush()
                    by = (pivot_y + rf_cos(angle) * L).flush()
                    bob_xs.append(bx.to_float())
                    bob_ys.append(by.to_float())

                # Strings (rod from pivot to bob) — neutral color, single paint op
                ctx.painter.set_color(0xFF6B7280) \
                    .set_style(STYLE_STROKE) \
                    .set_stroke_width(1.0) \
                    .set_stroke_cap(CAP_ROUND).commit()
                for i in range(n_pendulums):
                    pivot_x = start_x + i * spacing
                    ctx.draw_line(pivot_x, pivot_y, bob_xs[i], bob_ys[i])

                # Bobs — each gets its own color
                ctx.painter.set_style(STYLE_FILL).commit()
                for i in range(n_pendulums):
                    ctx.painter.set_color(palette[i]).commit()
                    ctx.draw_circle(bob_xs[i], bob_ys[i], bob_radius)

                # Pivots
                ctx.painter.set_color(0xFFE5E7EB).commit()
                for i in range(n_pendulums):
                    pivot_x = start_x + i * spacing
                    ctx.draw_circle(pivot_x, pivot_y, 2.5)

    return ctx


if __name__ == '__main__':
    ctx = demo_pendulum_wave()
    data = ctx.encode()
    outdir = os.path.join(os.path.dirname(__file__), '..', 'output')
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, 'pendulum_wave.rc')
    ctx.save(path)
    print(f"pendulum_wave: {len(data)} bytes -> {path}")

"""Sine wave plot -> sine_wave.rc

A scientific visualization: a sine curve drawn as a continuous path,
with grid lines and an animated marker that traces the curve.

Demonstrates path expressions (Cartesian) and time-driven animation
overlaid on a static curve.

NOTE: This demo uses `add_path_expression`, which the C++ player and
Android viewer render correctly but the desktop Python `rplayer` does
NOT yet implement (its `_op_path_expression` is a no-op). To verify
visually with rplayer, see `demo_sine_wave_segments.py` for a
line-segment fallback version that renders everywhere.
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
STYLE_STROKE = Rc.Paint.STYLE_STROKE
CAP_ROUND = Rc.Paint.CAP_ROUND


def demo_sine_wave():
    ctx = RcContext(500, 400, "Sine Wave",
                    api_level=7, profiles=PROFILE_ANDROIDX)

    with ctx.root():
        with ctx.box(RecordingModifier().fill_max_size().background(0xFF0E1117),
                     Rc.Layout.START, Rc.Layout.START):
            with ctx.canvas(RecordingModifier().fill_max_size()):
                # Plot region
                x_min = 60.0
                x_max = 460.0
                y_center = 200.0
                amplitude = 100.0
                waves = 2.5  # full cycles in plot range

                # Grid
                ctx.painter.set_color(0xFF1F2937) \
                    .set_style(STYLE_STROKE) \
                    .set_stroke_width(1.0).commit()
                # Horizontal gridlines (at center, ±amplitude)
                for y in (y_center - amplitude, y_center, y_center + amplitude):
                    ctx.draw_line(x_min, y, x_max, y)
                # Vertical gridlines at quarter-cycle marks
                segments = int(waves * 4)
                for i in range(segments + 1):
                    x = x_min + (x_max - x_min) * (i / segments)
                    ctx.draw_line(x, y_center - amplitude,
                                  x, y_center + amplitude)

                # X-axis (zero line, brighter)
                ctx.painter.set_color(0xFF6B7280) \
                    .set_stroke_width(1.5).commit()
                ctx.draw_line(x_min, y_center, x_max, y_center)

                # Sine curve as a path expression.
                # Parameter t in [0, 1]:
                #   x(t) = x_min + (x_max - x_min) * t
                #   y(t) = y_center - amplitude * sin(2*pi*waves*t)
                # (negative because canvas y grows downward)
                two_pi_waves = 2.0 * math.pi * waves

                exp_x = ctx.r_fun(lambda t: x_min + (x_max - x_min) * t)
                exp_y = ctx.r_fun(
                    lambda t: y_center - amplitude * rf_sin(t * two_pi_waves))

                ctx.painter.set_color(0xFF38BDF8) \
                    .set_style(STYLE_STROKE) \
                    .set_stroke_width(3.0) \
                    .set_stroke_cap(CAP_ROUND).commit()
                path_id = ctx.add_path_expression(
                    exp_x.to_array(), exp_y.to_array(),
                    0.0, 1.0, 100, 0)
                ctx.draw_path(path_id)

                # Animated marker — a dot tracing along the curve.
                # Use ContinuousSec mod 4 / 4 to get a 0->1 ramp every 4 sec.
                t = ctx.ContinuousSec()
                u = (t * 0.25) % 1.0  # 0..1 sweep, period 4s

                marker_x = x_min + (x_max - x_min) * u
                marker_y = y_center - amplitude * rf_sin(u * two_pi_waves)

                # Marker outer ring
                ctx.painter.set_color(0xFFFBBF24) \
                    .set_style(STYLE_STROKE) \
                    .set_stroke_width(2.0).commit()
                ctx.draw_circle(marker_x.to_float(), marker_y.to_float(), 9.0)

                # Marker inner fill
                ctx.painter.set_color(0xFFFBBF24) \
                    .set_style(STYLE_FILL).commit()
                ctx.draw_circle(marker_x.to_float(), marker_y.to_float(), 4.0)

    return ctx


if __name__ == '__main__':
    ctx = demo_sine_wave()
    data = ctx.encode()
    outdir = os.path.join(os.path.dirname(__file__), '..', 'output')
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, 'sine_wave.rc')
    ctx.save(path)
    print(f"sine_wave: {len(data)} bytes -> {path}")

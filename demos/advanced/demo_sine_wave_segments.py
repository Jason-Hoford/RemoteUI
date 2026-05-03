"""Sine wave plot using line segments -> sine_wave_segments.rc

A polygonal-approximation counterpart to demo_sine_wave. Uses a small
number of pre-computed line segments (N=12) so the discrete vertices
are visible — contrasts with the smooth path-expression version,
demonstrating low-fi vs high-fi rendering for the same shape.
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


def demo_sine_wave_segments():
    ctx = RcContext(500, 400, "Sine Wave (segments)",
                    api_level=7, profiles=PROFILE_ANDROIDX)

    with ctx.root():
        with ctx.box(RecordingModifier().fill_max_size().background(0xFF0E1117),
                     Rc.Layout.START, Rc.Layout.START):
            with ctx.canvas(RecordingModifier().fill_max_size()):
                x_min, x_max = 60.0, 460.0
                y_center = 200.0
                amplitude = 100.0
                waves = 2.5
                segments = 12  # low count makes the polygonal approximation visible
                two_pi_waves = 2.0 * math.pi * waves

                # Grid
                ctx.painter.set_color(0xFF1F2937) \
                    .set_style(STYLE_STROKE) \
                    .set_stroke_width(1.0).commit()
                for y in (y_center - amplitude, y_center, y_center + amplitude):
                    ctx.draw_line(x_min, y, x_max, y)
                quarter_lines = int(waves * 4)
                for i in range(quarter_lines + 1):
                    x = x_min + (x_max - x_min) * (i / quarter_lines)
                    ctx.draw_line(x, y_center - amplitude,
                                  x, y_center + amplitude)

                # X-axis (zero line)
                ctx.painter.set_color(0xFF6B7280).set_stroke_width(1.5).commit()
                ctx.draw_line(x_min, y_center, x_max, y_center)

                # Sine curve as line segments — pre-computed in Python.
                ctx.painter.set_color(0xFF38BDF8) \
                    .set_stroke_width(3.0) \
                    .set_stroke_cap(CAP_ROUND).commit()
                for i in range(segments):
                    t0 = i / segments
                    t1 = (i + 1) / segments
                    x0 = x_min + (x_max - x_min) * t0
                    x1 = x_min + (x_max - x_min) * t1
                    y0 = y_center - amplitude * math.sin(t0 * two_pi_waves)
                    y1 = y_center - amplitude * math.sin(t1 * two_pi_waves)
                    ctx.draw_line(x0, y0, x1, y1)

                # Animated marker tracing the curve
                t = ctx.ContinuousSec()
                u = (t * 0.25) % 1.0  # 0..1 sweep, 4-second period

                marker_x = x_min + (x_max - x_min) * u
                marker_y = y_center - amplitude * rf_sin(u * two_pi_waves)

                ctx.painter.set_color(0xFFFBBF24) \
                    .set_style(STYLE_STROKE) \
                    .set_stroke_width(2.0).commit()
                ctx.draw_circle(marker_x.to_float(), marker_y.to_float(), 9.0)

                ctx.painter.set_style(STYLE_FILL).commit()
                ctx.draw_circle(marker_x.to_float(), marker_y.to_float(), 4.0)

    return ctx


if __name__ == '__main__':
    ctx = demo_sine_wave_segments()
    data = ctx.encode()
    outdir = os.path.join(os.path.dirname(__file__), '..', 'output')
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, 'sine_wave_segments.rc')
    ctx.save(path)
    print(f"sine_wave_segments: {len(data)} bytes -> {path}")

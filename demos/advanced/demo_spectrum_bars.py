"""Audio spectrum visualizer -> spectrum_bars.rc

24 vertical bars whose heights pulse with phase-shifted sine envelopes,
giving the look of a music spectrum analyzer. Each bar's height is an
expression: |sin(t*freq + phase)| * (decay envelope). Each bar gets a
different frequency and phase, so the visual is a wave running across
the bars.

This is the "AI generates a music app UI" demo — drop something this
compact into a chat client, a podcast app, a meditation timer.
"""
import sys
import os
import math

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RcContext, Rc
from rcreate.modifiers import RecordingModifier
from rcreate.types.rfloat import rf_sin, rf_abs


PROFILE_ANDROIDX = 0x200
STYLE_FILL = Rc.Paint.STYLE_FILL


def demo_spectrum_bars():
    width, height = 600, 400
    ctx = RcContext(width, height, "Spectrum",
                    api_level=7, profiles=PROFILE_ANDROIDX)

    n_bars = 24
    margin = 40.0
    floor_y = 360.0
    ceiling_y = 60.0
    max_h = floor_y - ceiling_y      # 300
    bar_gap = 4.0
    bar_w = (width - 2 * margin - bar_gap * (n_bars - 1)) / n_bars

    with ctx.root():
        with ctx.box(RecordingModifier().fill_max_size().background(0xFF0A0E1A),
                     Rc.Layout.START, Rc.Layout.START):
            with ctx.canvas(RecordingModifier().fill_max_size()):
                # Baseline gradient strip
                ctx.painter.set_color(0xFF1F2937).set_style(STYLE_FILL).commit()
                ctx.draw_rect(margin - 10, floor_y - 1.0,
                              width - margin + 10, floor_y + 2.0)

                # Time
                t = ctx.animationTime()

                # Color palette — runs cool->warm across the bars
                palette = [
                    0xFF60A5FA, 0xFF818CF8, 0xFFA78BFA, 0xFFC084FC,
                    0xFFE879F9, 0xFFF472B6, 0xFFFB7185, 0xFFFB923C,
                    0xFFFBBF24, 0xFFFACC15, 0xFFA3E635, 0xFF4ADE80,
                    0xFF34D399, 0xFF22D3EE, 0xFF38BDF8, 0xFF60A5FA,
                    0xFF818CF8, 0xFFA78BFA, 0xFFC084FC, 0xFFE879F9,
                    0xFFF472B6, 0xFFFB7185, 0xFFFB923C, 0xFFFBBF24,
                ]

                # Each bar: phase-offset sine, modulated by a slower beat envelope.
                # Per-bar height = max_h * (0.15 + 0.85 * |sin(t*freq + phase)| * beat)
                beat_freq = 0.45            # full-spectrum pulse, ~ every 2.2s
                beat = 0.7 + rf_abs(rf_sin(t * (math.pi * beat_freq))) * 0.3

                for i in range(n_bars):
                    # Per-bar frequency and phase — frequencies span 1..6 Hz
                    freq = 1.0 + (i / (n_bars - 1)) * 5.0
                    phase = i * (math.pi / 7.0)

                    osc = rf_abs(rf_sin(t * (math.pi * freq) + phase))
                    h_norm = 0.12 + osc * beat * 0.85   # 0.12..~1.0
                    bar_h = h_norm * max_h
                    top_y = floor_y - bar_h

                    x0 = margin + i * (bar_w + bar_gap)
                    x1 = x0 + bar_w

                    color = palette[i % len(palette)]

                    # Main bar
                    ctx.painter.set_color(color).set_style(STYLE_FILL).commit()
                    ctx.draw_rect(x0, top_y.to_float(), x1, floor_y)

                    # Glow cap (small bright rect at top of bar)
                    cap_color = (color & 0x00FFFFFF) | 0xFF000000  # full alpha, will overlay slightly
                    ctx.painter.set_color(0xFFFFFFFF).commit()
                    ctx.draw_rect(x0, top_y.to_float(),
                                  x1, (top_y + 3.0).to_float())

    return ctx


if __name__ == '__main__':
    ctx = demo_spectrum_bars()
    data = ctx.encode()
    outdir = os.path.join(os.path.dirname(__file__), '..', 'output')
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, 'spectrum_bars.rc')
    ctx.save(path)
    print(f"spectrum_bars: {len(data)} bytes -> {path}")

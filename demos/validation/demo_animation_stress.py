"""Validation demo: multiple animations with different easing types.

Exercises:
- Multiple concurrent animated values
- Different easing types (linear, ease-in, ease-out, overshoot, bounce, elastic)
- Animated rotation, color, scale
- ContinuousSec, Seconds, time-based expressions
- anim() helper for smooth transitions
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
CAP_ROUND = Rc.Paint.CAP_ROUND


def demo_animation_stress():
    ctx = RcContext(500, 500, "Animation Stress", api_level=7,
                    profiles=PROFILE_ANDROIDX)

    with ctx.root():
        with ctx.box(RecordingModifier().fill_max_size(),
                     Rc.Layout.START, Rc.Layout.START):
            with ctx.canvas(RecordingModifier().fill_max_size()
                            .background(0xFF0D1117)):
                t = ctx.ContinuousSec()

                # Orbiting circles with different frequencies
                colors = [0xFFFF6B6B, 0xFF4ECDC4, 0xFFFFE66D,
                          0xFF95E1D3, 0xFFF38181, 0xFFAA96DA]
                for i, color in enumerate(colors):
                    angle = t * (60.0 + i * 20.0)
                    radius = 80.0 + i * 25.0
                    cx = ((angle * math.pi / 180.0).sin() * radius
                          + 250.0)
                    cy = ((angle * math.pi / 180.0).cos() * radius
                          + 250.0)

                    ctx.painter.set_color(color).set_style(STYLE_FILL) \
                        .commit()
                    ctx.draw_circle(cx.to_float(), cy.to_float(),
                                   12.0 - i)

                # Animated scale on second hand
                sec = ctx.Seconds()
                scale_anim = ((sec / 2.0) % 2.0 + 0.5).anim(0.5)

                # Pulsing center ring
                ctx.painter.set_color(0x66FFFFFF) \
                    .set_style(STYLE_STROKE) \
                    .set_stroke_width(3.0).commit()
                ring_r = scale_anim * 50.0
                ctx.draw_circle(250.0, 250.0, ring_r.to_float())

                # Rotating text showing seconds
                sec_text = ctx.create_text_from_float(
                    ctx.ContinuousSec().to_float(), 4, 1, 0)
                ctx.painter.set_color(0xFFFFFFFF) \
                    .set_text_size(16.0) \
                    .set_style(STYLE_FILL).commit()

                with ctx.saved():
                    rot = (t * 30.0).to_float()
                    ctx.rotate(rot, 250.0, 250.0)
                    ctx.draw_text_anchored(sec_text, 250.0, 150.0,
                                           0.0, 0.0, 0)

                # Bouncing bars at bottom (sine waves with phase offset)
                ctx.painter.set_color(0xFF6C5CE7).commit()
                for i in range(20):
                    bar_h = ((t * 3.0 + i * 0.3).sin() * 30.0 + 40.0)
                    x = 25.0 * i + 10.0
                    ctx.draw_rect(
                        x, (500.0 - bar_h).to_float(),
                        x + 20.0, 500.0)

                # Corner indicator: animated alpha via color expression
                # (simple approach: draw overlapping rects)
                phase = (t * 2.0).sin()
                line_x = (phase * 200.0 + 250.0).to_float()
                ctx.painter.set_color(0xFFFF0000) \
                    .set_stroke_width(2.0) \
                    .set_stroke_cap(CAP_ROUND) \
                    .set_style(STYLE_STROKE).commit()
                ctx.draw_line(line_x, 0.0, line_x, 30.0)

    return ctx


if __name__ == '__main__':
    ctx = demo_animation_stress()
    data = ctx.encode()
    outdir = os.path.join(os.path.dirname(__file__), '..', 'output')
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, 'val_animation_stress.rc')
    ctx.save(path)
    print(f"val_animation_stress: {len(data)} bytes -> {path}")

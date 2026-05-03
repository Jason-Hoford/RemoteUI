"""Bouncing ball with energy decay -> bouncing_ball.rc

A ball falls under gravity, bounces off the floor, loses energy each
bounce, and settles. Demonstrates piecewise expressions and physics.

Math (analytical model, no integration needed in the player):
  Each bounce cycle has period T_n = T_0 * r^n, where r is the energy
  retention ratio. Within a cycle, height follows a parabola.

  We use a simpler approximation: height(t) = abs(sin(w*t)) * decay(t)
  where decay(t) = exp(-k*t) gives the energy loss.
"""
import sys
import os
import math

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RcContext, Rc
from rcreate.modifiers import RecordingModifier
from rcreate.types.rfloat import rf_sin, rf_cos, rf_abs, rf_pow


PROFILE_ANDROIDX = 0x200
STYLE_FILL = Rc.Paint.STYLE_FILL
STYLE_STROKE = Rc.Paint.STYLE_STROKE


def demo_bouncing_ball():
    ctx = RcContext(500, 500, "Bouncing Ball",
                    api_level=7, profiles=PROFILE_ANDROIDX)

    with ctx.root():
        with ctx.box(RecordingModifier().fill_max_size().background(0xFF0F1B2D),
                     Rc.Layout.START, Rc.Layout.START):
            with ctx.canvas(RecordingModifier().fill_max_size()):
                # Geometry
                floor_y = 440.0
                ceiling_y = 100.0
                ball_x = 250.0
                ball_radius = 24.0

                # Animation
                bounce_freq = 1.4   # bounces per second initially
                decay_rate = 0.18   # energy loss per second

                # Use animationTime (ID 30) — session-relative, starts at 0 on load.
                # ContinuousSec is system uptime (huge on long-running machines), which
                # makes the rf_pow(0.84, t) decay term collapse to ~0 immediately.
                t = ctx.animationTime()

                # bounce_envelope: |sin(w*t)| gives bouncing motion 0..1
                bounce = rf_abs(rf_sin(t * (math.pi * bounce_freq)))

                # decay: exp(-k*t) — model with rf_pow(0.84, t) ~ exp(-0.17*t)
                decay = rf_pow(0.84, t)

                # height varies from 0 (top) to 1 (floor)
                height = 1.0 - bounce * decay

                # Ball position
                ball_y = ceiling_y + height * (floor_y - ceiling_y)

                # Floor line
                ctx.painter.set_color(0xFF3D5A80) \
                    .set_style(STYLE_STROKE) \
                    .set_stroke_width(3.0).commit()
                ctx.draw_line(50.0, floor_y + ball_radius,
                              450.0, floor_y + ball_radius)

                # Trail markers — vertical guides
                ctx.painter.set_color(0xFF1F2E48) \
                    .set_stroke_width(1.0).commit()
                ctx.draw_line(ball_x - 1.0, ceiling_y,
                              ball_x - 1.0, floor_y + ball_radius)

                # Ball shadow on floor (squashed ellipse via filled circle)
                ctx.painter.set_color(0x44000000) \
                    .set_style(STYLE_FILL).commit()
                # Shadow gets bigger when ball is high (further away)
                ctx.draw_circle(ball_x, floor_y + ball_radius,
                                ball_radius * 0.5)

                # Ball
                ctx.painter.set_color(0xFFEE6C4D).commit()
                ctx.draw_circle(ball_x, ball_y.to_float(), ball_radius)

                # Highlight on ball (small white circle, fixed offset)
                ctx.painter.set_color(0xFFFFFFFF).commit()
                ctx.draw_circle((ball_x - 8.0),
                                (ball_y - 8.0).to_float(),
                                5.0)

    return ctx


if __name__ == '__main__':
    ctx = demo_bouncing_ball()
    data = ctx.encode()
    outdir = os.path.join(os.path.dirname(__file__), '..', 'output')
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, 'bouncing_ball.rc')
    ctx.save(path)
    print(f"bouncing_ball: {len(data)} bytes -> {path}")

"""Simple pendulum animation -> pendulum.rc

A pivot at the top of the canvas, a string, and a bob that swings under
small-angle harmonic motion.

Math:
  theta(t) = max_angle * sin(2*pi*t/period)
  bob_x = pivot_x + length * sin(theta_radians)
  bob_y = pivot_y + length * cos(theta_radians)
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


def demo_pendulum():
    """Simple swinging pendulum, harmonic motion."""
    ctx = RcContext(500, 500, "Pendulum",
                    api_level=7, profiles=PROFILE_ANDROIDX)

    with ctx.root():
        with ctx.box(RecordingModifier().fill_max_size().background(0xFF101820),
                     Rc.Layout.START, Rc.Layout.START):
            with ctx.canvas(RecordingModifier().fill_max_size()):
                # Geometry
                pivot_x = 250.0
                pivot_y = 80.0
                length = 280.0
                bob_radius = 22.0

                # Animation: harmonic motion
                # theta_deg(t) = 35 * sin(2*pi*t / 2.0)
                period = 2.0           # seconds for a full swing cycle
                amplitude_deg = 35.0   # max swing angle
                two_pi = math.pi * 2.0

                t = ctx.ContinuousSec()
                phase = (t * (two_pi / period))
                theta_rad = rf_sin(phase) * (amplitude_deg * math.pi / 180.0)

                # Bob position
                bob_x = pivot_x + length * rf_sin(theta_rad)
                bob_y = pivot_y + length * rf_cos(theta_rad)

                # 1) The string from pivot to bob
                ctx.painter.set_color(0xFFE0E0E0) \
                    .set_style(STYLE_STROKE) \
                    .set_stroke_width(3.0) \
                    .set_stroke_cap(CAP_ROUND).commit()
                ctx.draw_line(pivot_x, pivot_y,
                              bob_x.to_float(), bob_y.to_float())

                # 2) The pivot — small fixed dot at the top
                ctx.painter.set_color(0xFFFFFFFF) \
                    .set_style(STYLE_FILL).commit()
                ctx.draw_circle(pivot_x, pivot_y, 6.0)

                # 3) The bob
                ctx.painter.set_color(0xFFE94560) \
                    .set_style(STYLE_FILL).commit()
                ctx.draw_circle(bob_x.to_float(), bob_y.to_float(),
                                bob_radius)

                # 4) Highlight ring on the bob
                ctx.painter.set_color(0xFFFFFFFF) \
                    .set_style(STYLE_STROKE) \
                    .set_stroke_width(1.5).commit()
                ctx.draw_circle(bob_x.to_float(), bob_y.to_float(),
                                bob_radius)

    return ctx


if __name__ == '__main__':
    ctx = demo_pendulum()
    data = ctx.encode()
    outdir = os.path.join(os.path.dirname(__file__), '..', 'output')
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, 'pendulum.rc')
    ctx.save(path)
    print(f"pendulum: {len(data)} bytes -> {path}")

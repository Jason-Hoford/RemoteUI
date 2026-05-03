"""Live analog clock -> analog_clock.rc

A real wall-clock face: hour/minute/second hands driven by the system
clock via Hour() / ContinuousSec() variables. Renders the viewer's
local time at any moment, with smooth (non-ticking) hand motion.

Compact and self-contained — under 1 KB of `.rc`. Replaces what would
be ~100+ lines of HTML/JS plus a setInterval and Date math.
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


def demo_analog_clock():
    ctx = RcContext(500, 500, "Analog Clock",
                    api_level=7, profiles=PROFILE_ANDROIDX)

    cx, cy = 250.0, 250.0
    face_radius = 200.0
    two_pi = 2.0 * math.pi

    with ctx.root():
        with ctx.box(RecordingModifier().fill_max_size().background(0xFF0F1419),
                     Rc.Layout.START, Rc.Layout.START):
            with ctx.canvas(RecordingModifier().fill_max_size()):
                # Face
                ctx.painter.set_color(0xFF1F2937).set_style(STYLE_FILL).commit()
                ctx.draw_circle(cx, cy, face_radius)

                # Bezel ring
                ctx.painter.set_color(0xFF38BDF8) \
                    .set_style(STYLE_STROKE) \
                    .set_stroke_width(3.0).commit()
                ctx.draw_circle(cx, cy, face_radius)

                # Hour ticks (12 large)
                ctx.painter.set_color(0xFFE5E7EB) \
                    .set_stroke_width(3.0) \
                    .set_stroke_cap(CAP_ROUND).commit()
                for i in range(12):
                    ang = i * (two_pi / 12.0)
                    s, c = math.sin(ang), math.cos(ang)
                    x1 = cx + (face_radius - 22) * s
                    y1 = cy - (face_radius - 22) * c
                    x2 = cx + (face_radius - 6) * s
                    y2 = cy - (face_radius - 6) * c
                    ctx.draw_line(x1, y1, x2, y2)

                # Minute ticks (small, skip the 12 hour positions)
                ctx.painter.set_color(0xFF4B5563).set_stroke_width(1.5).commit()
                for i in range(60):
                    if i % 5 == 0:
                        continue
                    ang = i * (two_pi / 60.0)
                    s, c = math.sin(ang), math.cos(ang)
                    x1 = cx + (face_radius - 10) * s
                    y1 = cy - (face_radius - 10) * c
                    x2 = cx + (face_radius - 4) * s
                    y2 = cy - (face_radius - 4) * c
                    ctx.draw_line(x1, y1, x2, y2)

                # System time variables
                hour_24 = ctx.Hour()             # integer 0..23
                cont_sec = ctx.ContinuousSec()    # fractional, 0..3599.999, resets at top of hour

                # Hand angles (radians, clockwise from 12)
                # Hour: 360° per 12 hours; smoothed by adding fractional hour from cont_sec.
                hour_12 = hour_24 % 12.0
                hour_angle = (hour_12 + cont_sec / 3600.0) * (two_pi / 12.0)
                # Minute: 360° per hour (3600 sec).
                min_angle = cont_sec * (two_pi / 3600.0)
                # Second: 360° per minute, sweeping (not ticking).
                sec_angle = (cont_sec % 60.0) * (two_pi / 60.0)

                def hand(angle_rf, length, color, width):
                    ctx.painter.set_color(color) \
                        .set_style(STYLE_STROKE) \
                        .set_stroke_width(width) \
                        .set_stroke_cap(CAP_ROUND).commit()
                    ex = cx + rf_sin(angle_rf) * length
                    ey = cy - rf_cos(angle_rf) * length
                    ctx.draw_line(cx, cy, ex.to_float(), ey.to_float())

                # Hour hand: thick gold, shortest
                hand(hour_angle, 110.0, 0xFFFBBF24, 8.0)
                # Minute hand: medium white
                hand(min_angle,  160.0, 0xFFE5E7EB, 5.0)
                # Second hand: thin red, longest
                hand(sec_angle,  175.0, 0xFFEF4444, 2.0)

                # Center hub
                ctx.painter.set_color(0xFFEF4444) \
                    .set_style(STYLE_FILL).commit()
                ctx.draw_circle(cx, cy, 8.0)
                ctx.painter.set_color(0xFF0F1419).commit()
                ctx.draw_circle(cx, cy, 3.0)

    return ctx


if __name__ == '__main__':
    ctx = demo_analog_clock()
    data = ctx.encode()
    outdir = os.path.join(os.path.dirname(__file__), '..', 'output')
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, 'analog_clock.rc')
    ctx.save(path)
    print(f"analog_clock: {len(data)} bytes -> {path}")

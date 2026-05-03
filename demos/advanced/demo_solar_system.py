"""Solar system orrery -> solar_system.rc

Sun at center, four inner planets at increasing orbital radii and
decreasing angular speeds. Earth gets a moon. Each body is positioned
by a polar-to-cartesian RFloat expression keyed off animationTime.

Demonstrates: multi-body real-time animation in a single static .rc,
with each orbit's period encoded as a constant in the expression tree.
This is the "AI generates a physics-grounded scene" demo.
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


def demo_solar_system():
    ctx = RcContext(560, 560, "Solar System",
                    api_level=7, profiles=PROFILE_ANDROIDX)

    cx, cy = 280.0, 280.0
    two_pi = 2.0 * math.pi

    # Planet table: (label, orbital_radius_px, orbital_period_sec, body_radius_px, color)
    PLANETS = [
        ("Mercury", 60.0,  3.0, 4.0,  0xFFB0AEC0),
        ("Venus",   100.0, 6.0, 7.0,  0xFFE0B070),
        ("Earth",   150.0, 10.0, 8.0, 0xFF60A5FA),
        ("Mars",    210.0, 18.0, 6.0, 0xFFEF4444),
    ]

    with ctx.root():
        with ctx.box(RecordingModifier().fill_max_size().background(0xFF050814),
                     Rc.Layout.START, Rc.Layout.START):
            with ctx.canvas(RecordingModifier().fill_max_size()):
                # Background stars (deterministic scatter, baked at generation time)
                ctx.painter.set_color(0xFF1F2937).set_style(STYLE_FILL).commit()
                # Pseudo-random stars via prime offsets
                for k in range(60):
                    x = (k * 197 + 13) % 560
                    y = (k * 137 + 47) % 560
                    r = 0.6 + ((k * 13) % 5) * 0.3
                    ctx.draw_circle(float(x), float(y), r)

                # Orbit rings (faint static circles)
                ctx.painter.set_color(0xFF22304E) \
                    .set_style(STYLE_STROKE) \
                    .set_stroke_width(1.0).commit()
                for _, r, _, _, _ in PLANETS:
                    ctx.draw_circle(cx, cy, r)

                # Sun (with halo)
                ctx.painter.set_color(0x33FBBF24).set_style(STYLE_FILL).commit()
                ctx.draw_circle(cx, cy, 32.0)
                ctx.painter.set_color(0x66FBBF24).commit()
                ctx.draw_circle(cx, cy, 22.0)
                ctx.painter.set_color(0xFFFBBF24).commit()
                ctx.draw_circle(cx, cy, 16.0)

                # Time variable (relative to load — large absolute values are fine for sin/cos)
                t = ctx.animationTime()

                earth_x_ref = None
                earth_y_ref = None

                for label, orbit_r, period, body_r, color in PLANETS:
                    omega = two_pi / period            # angular velocity (rad/sec)
                    angle = t * omega
                    px = cx + rf_cos(angle) * orbit_r
                    py = cy + rf_sin(angle) * orbit_r

                    # Trail dot (ghosted previous position, half a period back)
                    ghost_angle = (t - period * 0.05) * omega
                    gx = cx + rf_cos(ghost_angle) * orbit_r
                    gy = cy + rf_sin(ghost_angle) * orbit_r
                    ctx.painter.set_color((color & 0x00FFFFFF) | 0x44000000) \
                        .set_style(STYLE_FILL).commit()
                    ctx.draw_circle(gx.to_float(), gy.to_float(), body_r * 0.6)

                    # Planet
                    ctx.painter.set_color(color).commit()
                    ctx.draw_circle(px.to_float(), py.to_float(), body_r)

                    if label == "Earth":
                        # Moon orbits Earth — note: pulling positions out as floats
                        # captures the NaN-encoded references, so the moon position
                        # is fully expression-driven.
                        moon_omega = two_pi / 2.0   # 2-second moon period (visible at demo speed)
                        moon_angle = t * moon_omega
                        moon_r = 18.0
                        mx = px + rf_cos(moon_angle) * moon_r
                        my = py + rf_sin(moon_angle) * moon_r
                        ctx.painter.set_color(0xFFD1D5DB).commit()
                        ctx.draw_circle(mx.to_float(), my.to_float(), 3.0)

    return ctx


if __name__ == '__main__':
    ctx = demo_solar_system()
    data = ctx.encode()
    outdir = os.path.join(os.path.dirname(__file__), '..', 'output')
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, 'solar_system.rc')
    ctx.save(path)
    print(f"solar_system: {len(data)} bytes -> {path}")

"""Drag-to-fling slingshot with ground bounce -> slingshot.rc

INTERACTIVE: drag the ball away from home, release to launch it in the
opposite direction (classic slingshot). Ball arcs under gravity, bounces
off the floor once with reduced energy, then resets to home after a few
seconds.

Launch velocity comes from the **stretch direction**:
  vx = (home_x - touch_x) · stretch_factor
  vy = (home_y - touch_y) · stretch_factor
so dragging down-left produces an up-right launch. (Earlier versions used
TOUCH_VEL_X/Y, which captures fling velocity at touch-up — that's tiny if
the user pauses before releasing, which is why the ball just fell.)

Bounce: time-of-first-floor-hit `t1` is solved analytically from the
quadratic ½g·t² + vy·t + (touch_y − floor_y) = 0. Two phases:
  Phase 1 (Δt < t1): standard projectile from release point.
  Phase 2 (Δt ≥ t1): post-bounce trajectory from (x_at_t1, floor_y) with
                     velocity (vx·0.95, −(vy + g·t1)·0.65).
`rf_if_else(Δt − t1, phase2, phase1)` selects between them.
"""
import sys
import os
import math

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RcContext, Rc
from rcreate.modifiers import RecordingModifier
from rcreate.types.rfloat import rf_if_else, rf_sqrt, rf_max, rf_min


PROFILE_ANDROIDX = 0x200
STYLE_FILL = Rc.Paint.STYLE_FILL
STYLE_STROKE = Rc.Paint.STYLE_STROKE
CAP_ROUND = Rc.Paint.CAP_ROUND


def demo_slingshot():
    width, height = 500, 500
    ctx = RcContext(width, height, "Slingshot",
                    api_level=7, profiles=PROFILE_ANDROIDX)

    home_x = width / 2.0
    home_y = height - 100.0
    floor_y = height - 40.0   # visual ground line (ball bounces off this)
    gravity = 600.0   # px/sec²
    stretch_factor = 4.0   # how strongly drag distance maps to launch speed
    bounce_retain_y = 0.65 # vertical energy retained per bounce
    bounce_retain_x = 0.95 # horizontal speed retained per bounce
    flight_window = 4.0    # seconds before resetting to home
    drag_threshold = 0.30  # seconds of "no touch" before aim guide hides

    with ctx.root():
        with ctx.box(RecordingModifier().fill_max_size().background(0xFF050814),
                     Rc.Layout.START, Rc.Layout.START):
            with ctx.canvas(RecordingModifier().fill_max_size()):
                # Static "ground" line — the floor the ball bounces off.
                ctx.painter.set_color(0xFF22304E) \
                    .set_style(STYLE_STROKE) \
                    .set_stroke_width(2.0).commit()
                ctx.draw_line(20.0, floor_y, float(width) - 20.0, floor_y)

                # Home indicator — 3 concentric static rings forming a target
                ctx.painter.set_color(0xFF1F2937).set_style(STYLE_FILL).commit()
                ctx.draw_circle(home_x, home_y, 28.0)
                ctx.painter.set_color(0xFF111827).commit()
                ctx.draw_circle(home_x, home_y, 18.0)
                ctx.painter.set_color(0xFF22304E).commit()
                ctx.draw_circle(home_x, home_y, 8.0)

                # Static hint dots — a trail of small dots from home up-and-right
                # suggesting "drag to launch". Sub-pixel dim color.
                ctx.painter.set_color(0xFF1F2937).set_style(STYLE_FILL).commit()
                for k in range(1, 8):
                    hx = home_x + k * 26.0 * math.cos(math.radians(-45))
                    hy = home_y + k * 26.0 * math.sin(math.radians(-45))
                    ctx.draw_circle(hx, hy, 1.5 + k * 0.2)

                # ---- Touch / time state ----
                t        = ctx.animationTime()
                touch_x  = ctx.to_rf(Rc.Touch.POSITION_X)
                touch_y  = ctx.to_rf(Rc.Touch.POSITION_Y)
                event_t  = ctx.to_rf(Rc.Touch.TOUCH_EVENT_TIME)

                dt = (t - event_t).flush()
                dt_sq = (dt * dt).flush()

                # Slingshot launch velocity = stretch direction × factor.
                # Drag down-left → home-touch is up-right → launch up-right.
                vx = ((home_x - touch_x) * stretch_factor).flush()
                vy = ((home_y - touch_y) * stretch_factor).flush()

                # Solve quadratic for time-to-floor t1:
                #   y(t) = touch_y + vy·t + ½ g·t² = floor_y
                #   ½g·t² + vy·t + (touch_y - floor_y) = 0
                #   t1 = (-vy + sqrt(vy² + 2g·(floor_y - touch_y))) / g
                # Guard discriminant against negative (e.g. touch below floor).
                disc = vy * vy + (2.0 * gravity) * (floor_y - touch_y)
                disc_safe = rf_max(disc, 0.0).flush()
                t1 = ((rf_sqrt(disc_safe) - vy) / gravity).flush()

                # Phase 1 (dt < t1): regular projectile from release point.
                x_p1 = touch_x + vx * dt
                y_p1 = touch_y + vy * dt + (0.5 * gravity) * dt_sq

                # Phase 2 (dt ≥ t1): post-bounce trajectory.
                #   Ball position at t1: x_at_t1, floor_y
                #   y-velocity reflects with damping: vy_b = -(vy + g·t1) · retain_y
                #   x-velocity damps:                 vx_b = vx · retain_x
                s = (dt - t1).flush()
                vy_at_floor = (vy + gravity * t1).flush()        # always > 0 (downward)
                vy_b = (vy_at_floor * (-bounce_retain_y)).flush()  # negative = upward
                vx_b = (vx * bounce_retain_x).flush()
                x_at_t1 = (touch_x + vx * t1).flush()
                x_p2 = x_at_t1 + vx_b * s
                y_p2 = floor_y + vy_b * s + (0.5 * gravity) * (s * s)

                # Phase select: dt - t1 > 0 → phase 2, else phase 1.
                bounced = (dt - t1).flush()
                proj_x = rf_if_else(bounced, x_p2, x_p1)
                proj_y = rf_if_else(bounced, y_p2, y_p1)

                # Reset to home after the flight window.
                reset_cond = (dt - flight_window).flush()
                ball_x = rf_if_else(reset_cond, home_x, proj_x).flush()
                ball_y_raw = rf_if_else(reset_cond, home_y, proj_y).flush()
                # Floor clamp as a safety net — keep ball visually above floor.
                ball_y = rf_min(ball_y_raw, floor_y).flush()

                # Aim-guide line: visible only while pointer is freshly active.
                # When dt < drag_threshold → line endpoints are (home → touch),
                # otherwise both endpoints collapse to home (zero-length, invisible).
                aim_active = (drag_threshold - dt).flush()  # > 0 while drag active
                aim_end_x = rf_if_else(aim_active, touch_x, home_x).flush()
                aim_end_y = rf_if_else(aim_active, touch_y, home_y).flush()

                # Draw the aim guide line
                ctx.painter.set_color(0xFFFBBF24) \
                    .set_style(STYLE_STROKE) \
                    .set_stroke_width(2.0) \
                    .set_stroke_cap(CAP_ROUND).commit()
                ctx.draw_line(home_x, home_y,
                              aim_end_x.to_float(), aim_end_y.to_float())

                # Ball — outer halo + main fill + inner highlight
                ball_x_f = ball_x.to_float()
                ball_y_f = ball_y.to_float()
                ctx.painter.set_color(0x44EF4444).set_style(STYLE_FILL).commit()
                ctx.draw_circle(ball_x_f, ball_y_f, 18.0)

                ctx.painter.set_color(0xFFEF4444).commit()
                ctx.draw_circle(ball_x_f, ball_y_f, 12.0)

                ctx.painter.set_color(0xFFFFFFFF).commit()
                ctx.draw_circle(ball_x_f, ball_y_f, 4.0)

    return ctx


if __name__ == '__main__':
    ctx = demo_slingshot()
    data = ctx.encode()
    outdir = os.path.join(os.path.dirname(__file__), '..', 'output')
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, 'slingshot.rc')
    ctx.save(path)
    print(f"slingshot: {len(data)} bytes -> {path}")

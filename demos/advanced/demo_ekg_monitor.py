"""Resident-Evil-style EKG monitor with state buttons -> ekg_monitor.rc

INTERACTIVE: tap one of three coloured zones at the top of the canvas
to switch the patient's status — FINE (green, ~60 BPM, full amplitude),
CAUTION (yellow, ~110 BPM), DANGER (red, ~180 BPM, weakened amplitude
to suggest a labouring heart).

Stateless trick: the active zone is whichever third of the canvas
contains TOUCH_POS_X. Initially TOUCH_POS_X = 0 → FINE. When the user
taps elsewhere, TOUCH_POS_X stays at the released position, so the
state persists until the next tap.

Three EKG paths are drawn per frame, one per colour. Each path's
base_y is gated by `rf_if_else` against its state flag — the active
state's path renders on the centre of the canvas; the others get
base_y = -2000 (way off-screen). A single shared `scroll_speed`
expression drives the pulse rate of whichever path is currently
visible. P wave dropped for the punchy "stylised heart-monitor" look.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RcContext, Rc
from rcreate.modifiers import RecordingModifier
from rcreate.types.rfloat import rf_if_else


PROFILE_ANDROIDX = 0x200
STYLE_FILL = Rc.Paint.STYLE_FILL
STYLE_STROKE = Rc.Paint.STYLE_STROKE
CAP_ROUND = Rc.Paint.CAP_ROUND


# Status colours (32-bit ARGB)
FINE_COLOR    = 0xFF34D399
CAUTION_COLOR = 0xFFFCD34D
DANGER_COLOR  = 0xFFEF4444

# Dim versions for inactive button base
FINE_DIM      = 0x4034D399
CAUTION_DIM   = 0x40FCD34D
DANGER_DIM    = 0x40EF4444


def demo_ekg_monitor():
    width, height = 700, 500
    ctx = RcContext(width, height, "EKG Monitor",
                    api_level=8, profiles=PROFILE_ANDROIDX)

    base_y = 320.0          # vertical centre of trace (lower half — buttons live above)
    visible_beats = 4.0
    grid_minor = 25.0
    grid_major = 100.0
    off_y = -2000.0         # park inactive paths far above the canvas

    # Pulse rates (beats/sec scrolling left)
    rate_fine    = 0.40   # ~60 BPM
    rate_caution = 0.75   # ~110 BPM
    rate_danger  = 1.30   # ~180 BPM (and weakened amplitude below)

    # Top buttons
    btn_top    = 18.0
    btn_bot    = 78.0
    btn_pad    = 16.0
    btn_w      = (width - 4 * btn_pad) / 3.0
    btn_lefts  = [btn_pad,
                  btn_pad * 2 + btn_w,
                  btn_pad * 3 + 2 * btn_w]
    third_w    = width / 3.0  # threshold per state zone (touch_x)

    with ctx.root():
        with ctx.box(RecordingModifier().fill_max_size().background(0xFF06140C),
                     Rc.Layout.START, Rc.Layout.START):
            with ctx.canvas(RecordingModifier().fill_max_size()):

                # ───── Touch state → mutually exclusive flags ─────
                touch_x = ctx.to_rf(Rc.Touch.POSITION_X)
                t       = ctx.animationTime()

                # is_fine    = 1 if touch_x < W/3 else 0
                # is_danger  = 1 if touch_x >= 2W/3 else 0
                # is_caution = 1 - is_fine - is_danger
                is_fine    = rf_if_else(third_w - touch_x,
                                        1.0, 0.0).flush()
                is_danger  = rf_if_else(touch_x - 2.0 * third_w,
                                        1.0, 0.0).flush()
                is_caution = (1.0 - is_fine - is_danger).flush()

                # Per-state base_y. Active state → base_y, else → off-screen.
                fine_by    = (is_fine    * base_y + (1.0 - is_fine)    * off_y).flush()
                caution_by = (is_caution * base_y + (1.0 - is_caution) * off_y).flush()
                danger_by  = (is_danger  * base_y + (1.0 - is_danger)  * off_y).flush()

                # State-dependent scroll speed
                scroll_speed = (rate_fine    * is_fine
                              + rate_caution * is_caution
                              + rate_danger  * is_danger).flush()

                # ───── Buttons (always-visible dim base) ─────
                ctx.painter.set_color(FINE_DIM).set_style(STYLE_FILL).commit()
                ctx.draw_rect(btn_lefts[0], btn_top,
                              btn_lefts[0] + btn_w, btn_bot)
                ctx.painter.set_color(CAUTION_DIM).commit()
                ctx.draw_rect(btn_lefts[1], btn_top,
                              btn_lefts[1] + btn_w, btn_bot)
                ctx.painter.set_color(DANGER_DIM).commit()
                ctx.draw_rect(btn_lefts[2], btn_top,
                              btn_lefts[2] + btn_w, btn_bot)

                # ───── Highlight rectangles (bright outline; visible iff state active) ─────
                # Trick: when active_flag = 1, rect is (l, t, l+w, b). When 0, rect is
                # (l, t, l, b) — degenerate, zero-width, invisible.
                def draw_highlight(left, color, flag):
                    right = (flag * (left + btn_w) + (1.0 - flag) * left).flush()
                    ctx.painter.set_color(color) \
                        .set_style(STYLE_STROKE) \
                        .set_stroke_width(4.0).commit()
                    ctx.draw_rect(left, btn_top, right.to_float(), btn_bot)

                draw_highlight(btn_lefts[0], FINE_COLOR,    is_fine)
                draw_highlight(btn_lefts[1], CAUTION_COLOR, is_caution)
                draw_highlight(btn_lefts[2], DANGER_COLOR,  is_danger)

                # Indicator dot inside each button (colour key)
                for left, c in zip(btn_lefts, (FINE_COLOR, CAUTION_COLOR, DANGER_COLOR)):
                    ctx.painter.set_color(c).set_style(STYLE_FILL).commit()
                    ctx.draw_circle(left + 22.0, (btn_top + btn_bot) / 2.0, 8.0)

                # ───── Grid (medical-monitor green) ─────
                grid_top    = 110.0
                grid_bottom = float(height)
                ctx.painter.set_color(0xFF0E2D1A) \
                    .set_style(STYLE_STROKE) \
                    .set_stroke_width(1.0).commit()
                gx = grid_minor
                while gx < width:
                    if abs(gx % grid_major) > 0.5:
                        ctx.draw_line(gx, grid_top, gx, grid_bottom)
                    gx += grid_minor
                gy = grid_minor + grid_top
                while gy < grid_bottom:
                    if abs((gy - grid_top) % grid_major) > 0.5:
                        ctx.draw_line(0.0, gy, float(width), gy)
                    gy += grid_minor

                ctx.painter.set_color(0xFF1F5036).set_stroke_width(1.0).commit()
                gx = grid_major
                while gx < width:
                    ctx.draw_line(gx, grid_top, gx, grid_bottom)
                    gx += grid_major
                gy = grid_top + grid_major
                while gy < grid_bottom:
                    ctx.draw_line(0.0, gy, float(width), gy)
                    gy += grid_major

                # Baseline marker through the trace centre
                ctx.painter.set_color(0xFF1F5036).set_stroke_width(1.0).commit()
                ctx.draw_line(0.0, base_y, float(width), base_y)

                # ───── EKG paths (3 stacked, one visible at a time) ─────
                exp_x = ctx.r_fun(lambda u: u * float(width))

                def make_ekg_y(by_rf, amp_scale):
                    def ekg_y(u):
                        s = u * visible_beats + t * scroll_speed
                        p = s % 1.0
                        # Sharp narrow QRS — Resident-Evil-style heartbeat
                        q_off = (p - 0.18) * (1.0 / 0.010)
                        q_w   = (-(q_off * q_off)).exp() * 28.0
                        r_off = (p - 0.20) * (1.0 / 0.015)
                        r_w   = (-(r_off * r_off)).exp() * (-130.0)
                        s_off = (p - 0.22) * (1.0 / 0.010)
                        s_w   = (-(s_off * s_off)).exp() * 30.0
                        t_off = (p - 0.42) * (1.0 / 0.07)
                        t_w   = (-(t_off * t_off)).exp() * (-34.0)
                        return by_rf + (q_w + r_w + s_w + t_w) * amp_scale
                    return ekg_y

                # FINE — green, full amplitude, slow rate
                ctx.painter.set_color(FINE_COLOR) \
                    .set_style(STYLE_STROKE) \
                    .set_stroke_width(2.0) \
                    .set_stroke_cap(CAP_ROUND).commit()
                exp_y_fine = ctx.r_fun(make_ekg_y(fine_by, 1.0))
                ctx.draw_path(ctx.add_path_expression(
                    exp_x.to_array(), exp_y_fine.to_array(),
                    0.0, 1.0, 1500, 0))

                # CAUTION — yellow, full amplitude, faster rate
                ctx.painter.set_color(CAUTION_COLOR).commit()
                exp_y_caution = ctx.r_fun(make_ekg_y(caution_by, 1.0))
                ctx.draw_path(ctx.add_path_expression(
                    exp_x.to_array(), exp_y_caution.to_array(),
                    0.0, 1.0, 1500, 0))

                # DANGER — red, weakened amplitude (labouring heart), very fast
                ctx.painter.set_color(DANGER_COLOR).commit()
                exp_y_danger = ctx.r_fun(make_ekg_y(danger_by, 0.65))
                ctx.draw_path(ctx.add_path_expression(
                    exp_x.to_array(), exp_y_danger.to_array(),
                    0.0, 1.0, 1500, 0))

                # Sweep cursor — faint vertical line at the trailing edge
                ctx.painter.set_color(0x6634D399).set_stroke_width(2.0).commit()
                ctx.draw_line(float(width) - 8.0, grid_top + 10.0,
                              float(width) - 8.0, float(height) - 10.0)

    return ctx


if __name__ == '__main__':
    ctx = demo_ekg_monitor()
    data = ctx.encode()
    outdir = os.path.join(os.path.dirname(__file__), '..', 'output')
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, 'ekg_monitor.rc')
    ctx.save(path)
    print(f"ekg_monitor: {len(data)} bytes -> {path}")

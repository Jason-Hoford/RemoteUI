"""Port of DataVizDemos.kt — 10 data visualization demos.

Target .rc files:
  - activity_rings.rc        -> demo_activity_rings()
  - heart_rate_timeline.rc   -> demo_heart_rate_timeline()
  - step_progress_arc.rc     -> demo_step_progress_arc()
  - weather_forecast_bars.rc -> demo_weather_forecast_bars()
  - sleep_quality_rings.rc   -> demo_sleep_quality_rings()
  - battery_radial_gauge.rc  -> demo_battery_radial_gauge()
  - calendar_heatmap_grid.rc -> demo_calendar_heatmap_grid()
  - stock_sparkline.rc       -> demo_stock_sparkline()
  - moon_phase_dial.rc       -> demo_moon_phase_dial()
  - hydration_wave.rc        -> demo_hydration_wave()
"""
import sys
import os
import struct

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RcContext, Modifier, Rc
from rcreate.wire_buffer import RawFloat
from rcreate.types.rfloat import (
    RFloat, rf_array_sum, rf_array_min, rf_array_max, rf_array_spline,
    rf_max, rf_min, rf_sin, rf_cos,
)

PROFILE_ANDROIDX = 0x200
STYLE_FILL = Rc.Paint.STYLE_FILL
STYLE_STROKE = Rc.Paint.STYLE_STROKE
CAP_BUTT = 0
CAP_ROUND = 1

WHITE = 0xFFFFFFFF


def _f(v):
    """Coerce a value to float. If RFloat, call .to_float()."""
    if isinstance(v, RFloat):
        return v.to_float()
    if isinstance(v, RawFloat):
        return v  # preserve exact NaN bits for write_float
    return float(v)


def _f32(v):
    """Force single-precision float rounding (match Java float arithmetic)."""
    return struct.unpack('>f', struct.pack('>f', float(v)))[0]


# =====================================================================
# 1. Activity Rings
#    Three concentric circular progress rings for daily goals
# =====================================================================
def demo_activity_rings():
    data = [78.0, 62.0, 91.0]  # Move%, Exercise%, Stand%
    ring_colors = [0xFFFF2D55, 0xFF4CD964, 0xFF5AC8FA]
    track_colors = [0x44FF2D55, 0x444CD964, 0x445AC8FA]
    labels = ["Move", "Exercise", "Stand"]

    ctx = RcContext(400, 400, "Activity Rings",
                    api_level=7, profiles=0)
    with ctx.root():
        with ctx.canvas(Modifier().fill_max_size().background(0xFF1C1C1E)):
            w = ctx.ComponentWidth()
            h = ctx.ComponentHeight()
            cx = w / 2.0
            cy = h * 0.43
            density = ctx.rf(Rc.System.DENSITY)
            size = w.min(h)
            stroke_w = size * 0.06
            ring_gap = stroke_w * 1.6

            values = ctx.rf(ctx.add_float_array(data))

            for i in range(3):
                radius = size * 0.38 - ctx.rf(float(i)) * ring_gap
                progress = values[ctx.rf(float(i))]
                sweep_angle = progress / 100.0 * 360.0

                # Background track
                ctx.painter.set_color(track_colors[i]) \
                    .set_style(STYLE_STROKE) \
                    .set_stroke_width(stroke_w.to_float()) \
                    .set_stroke_cap(CAP_ROUND).commit()
                ctx.draw_arc(
                    _f(cx - radius), _f(cy - radius),
                    _f(cx + radius), _f(cy + radius), 0, 360)

                # Progress arc from 12 o'clock
                ctx.painter.set_color(ring_colors[i]).commit()
                ctx.draw_arc(
                    _f(cx - radius), _f(cy - radius),
                    _f(cx + radius), _f(cy + radius), -90, _f(sweep_angle))

            # Labels row below rings
            ctx.painter.set_style(STYLE_FILL).set_stroke_width(0.0).commit()
            for i in range(3):
                progress = values[ctx.rf(float(i))]
                label_x = w * (0.2 + float(i) * 0.3)
                label_y = h * 0.85
                ctx.painter.set_color(ring_colors[i]) \
                    .set_text_size((density * 22.0).to_float()) \
                    .set_typeface(0, 700, False).commit()
                pct_text = ctx.create_text_from_float(
                    progress.to_float(), 3, 0, Rc.TextFromFloat.PAD_PRE_NONE)
                pct_label = ctx.text_merge(pct_text, ctx.add_text("%"))
                ctx.draw_text_anchored(pct_label, _f(label_x), _f(label_y), 0, 0, 0)

                ctx.painter.set_text_size((density * 11.0).to_float()) \
                    .set_typeface(0, 400, False).commit()
                ctx.draw_text_anchored(labels[i], _f(label_x), _f(label_y), 0, 2.5, 0)
    return ctx


# =====================================================================
# 2. Heart Rate Timeline
#    24-hour HR line graph with color zones and pulsing BPM display
# =====================================================================
def demo_heart_rate_timeline():
    hr_data = [
        62.0, 58.0, 55.0, 54.0, 56.0, 60.0, 72.0, 85.0,
        95.0, 88.0, 78.0, 82.0, 90.0, 76.0, 70.0, 68.0,
        105.0, 140.0, 130.0, 95.0, 80.0, 72.0, 65.0, 60.0,
    ]

    ctx = RcContext(500, 400, "Heart Rate Timeline",
                    api_level=7, profiles=0)
    with ctx.root():
        with ctx.canvas(Modifier().fill_max_size().background(0xFF1A1A2E)):
            w = ctx.ComponentWidth()
            h = ctx.ComponentHeight()
            density = ctx.rf(Rc.System.DENSITY)
            values = ctx.rf(ctx.add_float_array(hr_data))

            g_left = density * 20.0
            g_right = w - density * 8.0
            g_top = h * 0.28
            g_bottom = h * 0.82
            g_w = g_right - g_left
            g_h = g_bottom - g_top
            min_hr = 40.0
            max_hr = 160.0
            hr_range = max_hr - min_hr

            # Color zone backgrounds
            zones = [
                (40.0, 60.0, 0x30448AFF),   # Resting blue
                (60.0, 100.0, 0x304CD964),  # Normal green
                (100.0, 130.0, 0x30FFCC00), # Elevated yellow
                (130.0, 160.0, 0x30FF3B30), # Peak red
            ]
            ctx.painter.set_style(STYLE_FILL).set_stroke_width(0.0).commit()
            for (lo, hi, color) in zones:
                ctx.painter.set_color(color).commit()
                y1 = g_bottom - (hi - min_hr) / hr_range * g_h
                y2 = g_bottom - (lo - min_hr) / hr_range * g_h
                # Build all expressions before flushing to match Kotlin
                # evaluation order (subtraction computed before toFloat calls)
                h_arg = y2 - y1
                ctx.draw_rect(_f(g_left), _f(y1), _f(g_w), _f(h_arg))

            # HR curve via arraySpline
            start_y = g_bottom - (rf_array_spline(values, ctx.rf(0.0)) - min_hr) / hr_range * g_h
            line_path = ctx.path_create(g_left.to_float(), start_y.to_float())
            steps = 80.0
            with ctx.loop_range(1, 1, steps) as step:
                t = step / steps
                x = g_left + g_w * t
                hr_val = rf_array_spline(values, t)
                y = g_bottom - (hr_val - min_hr) / hr_range * g_h
                ctx.path_append_line_to(line_path, x.to_float(), y.to_float())
            ctx.painter.set_color(0xFFFF3B30) \
                .set_style(STYLE_STROKE) \
                .set_stroke_width((density * 2.5).to_float()) \
                .set_stroke_cap(CAP_ROUND).commit()
            ctx.draw_path(line_path)

            # Hour labels
            ctx.painter.set_color(0x99FFFFFF) \
                .set_style(STYLE_FILL) \
                .set_text_size((density * 10.0).to_float()).commit()
            for hr in [0, 6, 12, 18]:
                x = g_left + g_w * ctx.rf(float(hr)) / 23.0
                ctx.draw_text_anchored(
                    f"{hr}h", _f(x), _f(g_bottom + density * 12.0), 0, 0, 0)

            # Current BPM with pulsing effect
            pulse = rf_sin(ctx.ContinuousSec() * 8.0) * 0.15 + 1.0
            bpm_size = density * 38.0 * pulse
            ctx.painter.set_color(0xFFFF3B30) \
                .set_text_size(bpm_size.to_float()) \
                .set_typeface(0, 700, False).commit()
            bpm_text = ctx.create_text_from_float(
                values[ctx.rf(23.0)].to_float(), 3, 0, Rc.TextFromFloat.PAD_PRE_NONE)
            ctx.draw_text_anchored(
                bpm_text, _f(w * 0.75), _f(h * 0.12), 0, 0, 0)
            ctx.painter.set_text_size((density * 14.0).to_float()) \
                .set_typeface(0, 400, False) \
                .set_color(0xAAFFFFFF).commit()
            ctx.draw_text_anchored("BPM", _f(w * 0.75), _f(h * 0.12), 0, 3.0, 0)

            # Heart icon
            ctx.painter.set_color(0xFFFF3B30) \
                .set_text_size((density * 20.0 * pulse).to_float()).commit()
            ctx.draw_text_anchored(
                "\u2665", _f(w * 0.75), _f(h * 0.12), 4.0, 0, 0)
    return ctx


# =====================================================================
# 3. Step Progress Arc
#    Semicircular arc showing step count progress toward daily goal
# =====================================================================
def demo_step_progress_arc():
    data = [7250.0, 10000.0]  # currentSteps, goal

    ctx = RcContext(400, 350, "Step Progress Arc",
                    api_level=7, profiles=0)
    with ctx.root():
        with ctx.canvas(Modifier().fill_max_size().background(0xFF16213E)):
            w = ctx.ComponentWidth()
            h = ctx.ComponentHeight()
            cx = w / 2.0
            cy = h * 0.55
            density = ctx.rf(Rc.System.DENSITY)
            size = w.min(h)
            arc_radius = size * 0.4
            stroke_w = size * 0.07

            values = ctx.rf(ctx.add_float_array(data))
            current = values[ctx.rf(0.0)]
            goal = values[ctx.rf(1.0)]
            progress = rf_min(current / goal, ctx.rf(1.0))

            # Background track (semicircle, 180 deg from left to right)
            ctx.painter.set_color(0x33FFFFFF) \
                .set_style(STYLE_STROKE) \
                .set_stroke_width(stroke_w.to_float()) \
                .set_stroke_cap(CAP_ROUND).commit()
            ctx.draw_arc(
                _f(cx - arc_radius), _f(cy - arc_radius),
                _f(cx + arc_radius), _f(cy + arc_radius), 180, 180)

            # Progress arc
            ctx.painter.set_color(0xFF00D2FF).commit()
            ctx.draw_arc(
                _f(cx - arc_radius), _f(cy - arc_radius),
                _f(cx + arc_radius), _f(cy + arc_radius),
                180, _f(progress * 180.0))

            # Milestone markers at 25%, 50%, 75%, 100%
            ctx.painter.set_color(0x88FFFFFF) \
                .set_stroke_width((density * 2.0).to_float()).commit()
            tick_len = stroke_w * 0.6
            for pct in [25, 50, 75, 100]:
                angle = 180.0 + float(pct) / 100.0 * 180.0
                rad = ctx.rf(angle).rad()
                outer_r = arc_radius + stroke_w / 2.0 + density * 2.0
                inner_r = arc_radius + stroke_w / 2.0 + tick_len
                tx1 = cx + outer_r * rf_cos(rad)
                ty1 = cy + outer_r * rf_sin(rad)
                tx2 = cx + inner_r * rf_cos(rad)
                ty2 = cy + inner_r * rf_sin(rad)
                ctx.draw_line(_f(tx1), _f(ty1), _f(tx2), _f(ty2))

                # Label
                ctx.painter.set_style(STYLE_FILL) \
                    .set_text_size((density * 10.0).to_float()).commit()
                l_r = arc_radius + stroke_w / 2.0 + tick_len + density * 10.0
                ctx.draw_text_anchored(
                    f"{pct}%",
                    _f(cx + l_r * rf_cos(rad)),
                    _f(cy + l_r * rf_sin(rad)), 0, 0, 0)
                ctx.painter.set_style(STYLE_STROKE).commit()

            # Step count text
            ctx.painter.set_color(WHITE) \
                .set_style(STYLE_FILL) \
                .set_text_size((density * 40.0).to_float()) \
                .set_typeface(0, 700, False).commit()
            steps_text = ctx.create_text_from_float(
                current.to_float(), 5, 0, Rc.TextFromFloat.PAD_PRE_NONE)
            ctx.draw_text_anchored(
                steps_text, _f(cx), _f(cy - density * 15.0), 0, 0, 0)

            # Goal text
            ctx.painter.set_color(0xAAFFFFFF) \
                .set_text_size((density * 16.0).to_float()) \
                .set_typeface(0, 400, False).commit()
            goal_label = ctx.text_merge(
                ctx.add_text("/ "),
                ctx.create_text_from_float(
                    goal.to_float(), 5, 0, Rc.TextFromFloat.PAD_PRE_NONE),
                ctx.add_text(" steps"))
            ctx.draw_text_anchored(
                goal_label, _f(cx), _f(cy + density * 8.0), 0, 0, 0)
    return ctx


# =====================================================================
# 4. Weather Forecast Bars
#    Vertical bar chart showing hourly temperature + precipitation
# =====================================================================
def demo_weather_forecast_bars():
    temp_data = [18.0, 17.0, 16.0, 17.0, 19.0, 22.0,
                 25.0, 28.0, 30.0, 29.0, 27.0, 24.0]
    precip_data = [0.0, 0.0, 10.0, 20.0, 5.0, 0.0,
                   0.0, 0.0, 15.0, 40.0, 60.0, 30.0]
    hours = ["6a", "7a", "8a", "9a", "10a", "11a",
             "12p", "1p", "2p", "3p", "4p", "5p"]

    ctx = RcContext(500, 400, "Weather Forecast Bars",
                    api_level=7, profiles=0)
    with ctx.root():
        with ctx.canvas(Modifier().fill_max_size().background(0xFF0A1628)):
            w = ctx.ComponentWidth()
            h = ctx.ComponentHeight()
            density = ctx.rf(Rc.System.DENSITY)

            temps = ctx.rf(ctx.add_float_array(temp_data))
            precips = ctx.rf(ctx.add_float_array(precip_data))

            margin_l = density * 35.0
            margin_r = density * 10.0
            margin_top = density * 50.0
            margin_bot = density * 40.0
            graph_w = w - (margin_l - margin_r).flush()
            graph_h = h - margin_top - margin_bot
            graph_bottom = h - margin_bot
            bar_count = 12.0
            bar_spacing = graph_w / bar_count
            bar_width = bar_spacing * 0.6
            min_temp = 10.0
            max_temp = 35.0
            temp_range = max_temp - min_temp

            # Title
            ctx.painter.set_color(WHITE) \
                .set_style(STYLE_FILL) \
                .set_text_size((density * 16.0).to_float()) \
                .set_typeface(0, 700, False).commit()
            ctx.draw_text_anchored(
                "Hourly Forecast", _f(w / 2.0), _f(density * 18.0), 0, 0, 0)

            # Temperature bars via player-side loop
            with ctx.loop_range(0, 1, bar_count) as i:
                temp = temps[i]
                normalized_temp = ((temp - min_temp) / temp_range).flush()
                bar_h = (density * 4.0).max(normalized_temp * graph_h).flush()
                bar_x = (margin_l + i * bar_spacing
                         + (bar_spacing - bar_width) / 2.0).flush()
                bar_y = graph_bottom - bar_h

                # Color by temperature: blue(cold) to red(hot) via HSV
                hue = (1.0 - normalized_temp) * 0.66
                color_id = ctx.add_color_expression(
                    0xFF, hue.to_float(), 0.8, 0.9)
                ctx.painter.set_color_id(color_id).set_style(STYLE_FILL).commit()
                ctx.draw_round_rect(
                    _f(bar_x), _f(bar_y), _f(bar_width), _f(bar_h),
                    _f(density * 3.0), _f(density * 3.0))

                # Temperature label on top of bar
                ctx.painter.set_color(WHITE) \
                    .set_text_size((density * 10.0).to_float()) \
                    .set_typeface(0, 600, False).commit()
                temp_label = ctx.create_text_from_float(
                    temp.to_float(), 2, 0, Rc.TextFromFloat.PAD_PRE_NONE)
                temp_str = ctx.text_merge(temp_label, ctx.add_text("\u00B0"))
                ctx.draw_text_anchored(
                    temp_str, _f(bar_x + bar_width / 2.0),
                    _f(bar_y - density * 6.0), 0, 0, 0)

                # Precipitation indicator (blue dot, size = probability)
                precip = precips[i]
                dot_radius = precip / 100.0 * density * 6.0
                ctx.painter.set_color(0xAA4488FF).commit()
                ctx.draw_circle(
                    (bar_x + bar_width / 2.0).to_float(),
                    (graph_bottom + density * 10.0).to_float(),
                    dot_radius.to_float())

            # Hour labels (Python loop for string access)
            ctx.painter.set_color(0x99FFFFFF) \
                .set_text_size((density * 9.0).to_float()) \
                .set_typeface(0, 400, False).commit()
            for i in range(len(hours)):
                x = margin_l + ctx.rf(float(i)) * bar_spacing + bar_spacing / 2.0
                ctx.draw_text_anchored(
                    hours[i], _f(x),
                    _f(graph_bottom + density * 22.0), 0, 0, 0)

            # Y-axis temperature labels
            ctx.painter.set_color(0x66FFFFFF) \
                .set_text_size((density * 9.0).to_float()).commit()
            for t in [15, 20, 25, 30]:
                y = graph_bottom - (float(t) - min_temp) / temp_range * graph_h
                ctx.draw_text_anchored(
                    f"{t}\u00B0", _f(margin_l - density * 6.0), _f(y), 1.0, 0, 0)
                ctx.painter.set_color(0x22FFFFFF) \
                    .set_stroke_width(1.0) \
                    .set_style(STYLE_STROKE).commit()
                ctx.draw_line(_f(margin_l), _f(y), _f(w - margin_r), _f(y))
                ctx.painter.set_color(0x66FFFFFF).set_style(STYLE_FILL).commit()
    return ctx


# =====================================================================
# 5. Sleep Quality Rings
#    Color-coded ring segments showing sleep stages
# =====================================================================
def demo_sleep_quality_rings():
    stage_data = [110.0, 180.0, 90.0, 20.0]
    stage_colors = [
        0xFF1A237E,  # Deep - dark blue
        0xFF42A5F5,  # Light - light blue
        0xFF7E57C2,  # REM - purple
        0xFFFF7043,  # Awake - orange
    ]
    stage_labels = ["Deep", "Light", "REM", "Awake"]

    ctx = RcContext(400, 400, "Sleep Quality Rings",
                    api_level=7, profiles=0)
    with ctx.root():
        with ctx.canvas(Modifier().fill_max_size().background(0xFF0D1B2A)):
            w = ctx.ComponentWidth()
            h = ctx.ComponentHeight()
            cx = w / 2.0
            cy = h * 0.45
            density = ctx.rf(Rc.System.DENSITY)
            size = w.min(h)
            ring_radius = size * 0.35
            stroke_w = size * 0.09

            values = ctx.rf(ctx.add_float_array(stage_data))
            total = rf_array_sum(values)

            # Draw ring segments
            current_angle = -90.0  # Start from 12 o'clock (plain float)
            for i in range(len(stage_data)):
                stage_min = values[ctx.rf(float(i))]
                sweep_angle = stage_min / total * 360.0

                # Build rotate expression BEFORE flushing sweepAngle.
                # Kotlin: Float.plus(RFloat) uses v.array (full form).
                # current_angle + sweep_angle triggers __radd__ which
                # uses list(self.array) — matching Kotlin's behavior.
                rot_expr = current_angle + sweep_angle

                ctx.painter.set_color(stage_colors[i]) \
                    .set_style(STYLE_STROKE) \
                    .set_stroke_width(stroke_w.to_float()) \
                    .set_stroke_cap(CAP_BUTT).commit()
                ctx.draw_arc(
                    _f(cx - ring_radius), _f(cy - ring_radius),
                    _f(cx + ring_radius), _f(cy + ring_radius),
                    _f(current_angle), _f(sweep_angle))

                # Thin white separator
                ctx.painter.set_color(0xFF0D1B2A) \
                    .set_stroke_width((density * 2.0).to_float()).commit()
                with ctx.saved():
                    ctx.rotate(rot_expr.to_float(), _f(cx), _f(cy))
                    ctx.draw_line(
                        _f(cx), _f(cy - ring_radius - stroke_w / 2.0),
                        _f(cx), _f(cy - ring_radius + stroke_w / 2.0))

                # Accumulate angle: currentAngle += sweepAngle.toFloat()
                # On JVM x86, float + sNaN quiets the NaN (sets bit 22).
                # Use RawFloat to preserve the exact qNaN bit pattern through
                # write_float / write_float_as_snan which otherwise clear bit 22.
                sweep_nan = sweep_angle.to_float()
                nan_bits = struct.unpack('>I', struct.pack('>f', sweep_nan))[0]
                current_angle = RawFloat(nan_bits | 0x00400000)

            # Center text: total sleep time
            total_minutes = total
            hrs = (total_minutes / 60.0).floor()
            mins = total_minutes - hrs * 60.0

            ctx.painter.set_color(WHITE) \
                .set_style(STYLE_FILL) \
                .set_text_size((density * 32.0).to_float()) \
                .set_typeface(0, 700, False).commit()
            hrs_text = ctx.create_text_from_float(
                hrs.to_float(), 1, 0, Rc.TextFromFloat.PAD_PRE_NONE)
            mins_text = ctx.create_text_from_float(
                mins.to_float(), 2, 0, Rc.TextFromFloat.PAD_PRE_NONE)
            time_label = ctx.text_merge(
                hrs_text, ctx.add_text("h "), mins_text, ctx.add_text("m"))
            ctx.draw_text_anchored(time_label, _f(cx), _f(cy), 0, 0, 0)

            ctx.painter.set_color(0xAAFFFFFF) \
                .set_text_size((density * 13.0).to_float()) \
                .set_typeface(0, 400, False).commit()
            ctx.draw_text_anchored("Total Sleep", _f(cx), _f(cy), 0, 3.5, 0)

            # Legend
            for i in range(len(stage_data)):
                lx = w * 0.15 + ctx.rf(float(i)) * w * 0.2
                ly = h * 0.88
                ctx.painter.set_color(stage_colors[i]).set_style(STYLE_FILL).commit()
                ctx.draw_circle(lx.to_float(), ly.to_float(),
                                (density * 4.0).to_float())

                ctx.painter.set_color(0xCCFFFFFF) \
                    .set_text_size((density * 10.0).to_float()).commit()
                ctx.draw_text_anchored(
                    stage_labels[i], _f(lx), _f(ly + density * 12.0), 0, 0, 0)
    return ctx


# =====================================================================
# 6. Battery Radial Gauge
#    270-degree radial gauge with green-yellow-red gradient
# =====================================================================
def demo_battery_radial_gauge():
    data = [67.0, 8.5]  # percentage, estimatedHoursRemaining

    ctx = RcContext(400, 400, "Battery Radial Gauge",
                    api_level=7, profiles=0)
    with ctx.root():
        with ctx.canvas(Modifier().fill_max_size().background(0xFF1A1A2E)):
            w = ctx.ComponentWidth()
            h = ctx.ComponentHeight()
            cx = w / 2.0
            cy = h * 0.45
            density = ctx.rf(Rc.System.DENSITY)
            size = w.min(h)
            gauge_radius = size * 0.38
            stroke_w = size * 0.08

            values = ctx.rf(ctx.add_float_array(data))
            level = values[ctx.rf(0.0)]
            hours_left = values[ctx.rf(1.0)]

            # Background track (270 deg, gap at bottom)
            ctx.painter.set_color(0x33FFFFFF) \
                .set_style(STYLE_STROKE) \
                .set_stroke_width(stroke_w.to_float()) \
                .set_stroke_cap(CAP_ROUND).commit()
            ctx.draw_arc(
                _f(cx - gauge_radius), _f(cy - gauge_radius),
                _f(cx + gauge_radius), _f(cy + gauge_radius), 135, 270)

            # Active gauge arc - color from green(100%) to red(0%) via HSV
            normalized = level / 100.0
            hue = normalized * 0.33  # 0=red, 0.33=green
            gauge_color = ctx.add_color_expression(
                0xFF, hue.to_float(), 0.9, 0.9)
            ctx.painter.set_color_id(gauge_color).commit()
            ctx.draw_arc(
                _f(cx - gauge_radius), _f(cy - gauge_radius),
                _f(cx + gauge_radius), _f(cy + gauge_radius),
                135, _f(normalized * 270.0))

            # Scale ticks
            ctx.painter.set_color(0x55FFFFFF) \
                .set_stroke_width((density * 1.5).to_float()).commit()
            tick_r1 = gauge_radius + stroke_w / 2.0 + density * 3.0
            tick_r2 = tick_r1 + density * 6.0
            for pct in [0, 25, 50, 75, 100]:
                angle = 135.0 + float(pct) / 100.0 * 270.0
                rad = ctx.rf(angle).rad()
                ctx.draw_line(
                    _f(cx + tick_r1 * rf_cos(rad)),
                    _f(cy + tick_r1 * rf_sin(rad)),
                    _f(cx + tick_r2 * rf_cos(rad)),
                    _f(cy + tick_r2 * rf_sin(rad)))

            # Percentage text
            ctx.painter.set_color(WHITE) \
                .set_style(STYLE_FILL) \
                .set_text_size((density * 48.0).to_float()) \
                .set_typeface(0, 700, False).commit()
            pct_text = ctx.create_text_from_float(
                level.to_float(), 3, 0, Rc.TextFromFloat.PAD_PRE_NONE)
            pct_label = ctx.text_merge(pct_text, ctx.add_text("%"))
            ctx.draw_text_anchored(pct_label, _f(cx), _f(cy), 0, 0, 0)

            # Hours remaining
            ctx.painter.set_color(0xAAFFFFFF) \
                .set_text_size((density * 14.0).to_float()) \
                .set_typeface(0, 400, False).commit()
            hrs_text = ctx.create_text_from_float(
                hours_left.to_float(), 2, 1, Rc.TextFromFloat.PAD_PRE_NONE)
            hrs_label = ctx.text_merge(hrs_text, ctx.add_text("h remaining"))
            ctx.draw_text_anchored(hrs_label, _f(cx), _f(cy), 0, 3.5, 0)

            # Battery icon indicator
            ctx.painter.set_color_id(gauge_color) \
                .set_text_size((density * 20.0).to_float()).commit()
            ctx.draw_text_anchored("\u26A1", _f(cx), _f(cy), 0, -3.5, 0)
    return ctx


# =====================================================================
# 7. Calendar Heatmap Grid
#    7x5 grid showing activity intensity over 35 days
# =====================================================================
def demo_calendar_heatmap_grid():
    patterns = [
        0.2, 0.8, 0.6, 0.0, 0.4, 0.9, 0.1,
        0.5, 0.7, 0.3, 0.0, 0.6, 1.0, 0.2,
        0.4, 0.9, 0.8, 0.1, 0.3, 0.7, 0.0,
        0.6, 0.5, 0.7, 0.0, 0.8, 0.4, 0.3,
        0.3, 0.6, 0.9, 0.2, 0.5, 0.7, 0.8,
    ]
    activity_data = [float(x) for x in patterns]
    day_labels = ["M", "T", "W", "T", "F", "S", "S"]
    current_day_index = 33  # Highlighted day (0-indexed)

    ctx = RcContext(400, 400, "Calendar Heatmap Grid",
                    api_level=7, profiles=0)
    with ctx.root():
        with ctx.canvas(Modifier().fill_max_size().background(0xFF161B22)):
            w = ctx.ComponentWidth()
            h = ctx.ComponentHeight()
            density = ctx.rf(Rc.System.DENSITY)

            values = ctx.rf(ctx.add_float_array(activity_data))

            grid_left = w * 0.15
            grid_top = h * 0.22
            grid_w = w * 0.75
            grid_h = h * 0.6
            cols = 7.0
            rows = 5.0
            cell_w = grid_w / cols
            cell_h = grid_h / rows
            gap = density * 3.0

            # Title
            ctx.painter.set_color(WHITE) \
                .set_style(STYLE_FILL) \
                .set_text_size((density * 16.0).to_float()) \
                .set_typeface(0, 700, False).commit()
            ctx.draw_text_anchored(
                "Activity \u00B7 Past 35 Days",
                _f(w / 2.0), _f(density * 20.0), 0, 0, 0)

            # Day-of-week headers
            ctx.painter.set_color(0x99FFFFFF) \
                .set_text_size((density * 11.0).to_float()) \
                .set_typeface(0, 400, False).commit()
            for d in range(7):
                x = grid_left + ctx.rf(float(d)) * cell_w + cell_w / 2.0
                ctx.draw_text_anchored(
                    day_labels[d], _f(x),
                    _f(grid_top - density * 8.0), 0, 0, 0)

            # Heatmap cells via player-side loop
            with ctx.loop_range(0, 1, 35) as idx:
                col = idx % 7.0
                row = (idx / 7.0).floor()
                cell_x = grid_left + col * cell_w + gap / 2.0
                cell_y = grid_top + row * cell_h + gap / 2.0
                intensity = values[idx]

                # Color: dark green (low) to bright green (high)
                color_id = ctx.add_color_expression(
                    0xFF, 0.33,
                    (intensity * 0.8 + 0.1).to_float(),
                    (intensity * 0.7 + 0.15).to_float())
                ctx.painter.set_color_id(color_id).set_style(STYLE_FILL).commit()
                ctx.draw_round_rect(
                    _f(cell_x), _f(cell_y),
                    _f(cell_w - gap), _f(cell_h - gap),
                    _f(density * 3.0), _f(density * 3.0))

            # Highlight current day with border
            cur_col = current_day_index % 7
            cur_row = current_day_index // 7
            hl_x = grid_left + ctx.rf(float(cur_col)) * cell_w + gap / 2.0
            hl_y = grid_top + ctx.rf(float(cur_row)) * cell_h + gap / 2.0
            ctx.painter.set_color(WHITE) \
                .set_style(STYLE_STROKE) \
                .set_stroke_width((density * 2.0).to_float()).commit()
            ctx.draw_round_rect(
                _f(hl_x), _f(hl_y),
                _f(cell_w - gap), _f(cell_h - gap),
                _f(density * 3.0), _f(density * 3.0))

            # Legend
            ctx.painter.set_style(STYLE_FILL).commit()
            legend_y = grid_top + grid_h + density * 30.0
            ctx.painter.set_color(0x99FFFFFF) \
                .set_text_size((density * 10.0).to_float()).commit()
            ctx.draw_text_anchored("Less", _f(w * 0.3), _f(legend_y), 1.5, 0, 0)
            ctx.draw_text_anchored("More", _f(w * 0.7), _f(legend_y), -1.5, 0, 0)
            for level in range(5):
                lx = w * 0.35 + ctx.rf(float(level)) * density * 16.0
                intensity_val = float(level) / 4.0
                color_id = ctx.add_color_expression(
                    0xFF, 0.33,
                    _f32(_f32(intensity_val * 0.8) + _f32(0.1)),
                    _f32(_f32(intensity_val * 0.7) + _f32(0.15)))
                ctx.painter.set_color_id(color_id).commit()
                ctx.draw_round_rect(
                    _f(lx), _f(legend_y - density * 5.0),
                    _f(density * 10.0), _f(density * 10.0),
                    _f(density * 2.0), _f(density * 2.0))
    return ctx


# =====================================================================
# 8. Stock/Crypto Sparkline
#    Minimal line chart with gradient fill, price and change display
# =====================================================================
def demo_stock_sparkline():
    price_data = [
        42150.0, 42380.0, 42200.0, 41900.0, 41750.0, 42000.0,
        42400.0, 42800.0, 43100.0, 43050.0, 42900.0, 43200.0,
        43500.0, 43400.0, 43800.0, 44100.0, 44000.0, 43700.0,
        43900.0, 44200.0, 44500.0, 44300.0, 44600.0, 44850.0,
    ]

    ctx = RcContext(500, 350, "Stock Sparkline",
                    api_level=7, profiles=0)
    with ctx.root():
        with ctx.canvas(Modifier().fill_max_size().background(0xFF1C1C1E)):
            w = ctx.ComponentWidth()
            h = ctx.ComponentHeight()
            density = ctx.rf(Rc.System.DENSITY)

            prices = ctx.rf(ctx.add_float_array(price_data))
            price_min = rf_array_min(prices)
            price_max = rf_array_max(prices)
            price_range = rf_max(price_max - price_min, ctx.rf(1.0))
            first_price = prices[ctx.rf(0.0)]
            last_price = prices[ctx.rf(23.0)]
            change_amt = last_price - first_price
            change_pct = change_amt / first_price * 100.0

            g_left = density * 15.0
            g_right = w - density * 15.0
            g_top = h * 0.38
            g_bottom = h * 0.82
            g_w = g_right - g_left
            g_h = g_bottom - g_top

            # Current price
            ctx.painter.set_color(WHITE) \
                .set_style(STYLE_FILL) \
                .set_text_size((density * 32.0).to_float()) \
                .set_typeface(0, 700, False).commit()
            price_text = ctx.create_text_from_float(
                last_price.to_float(), 5, 0, Rc.TextFromFloat.PAD_PRE_NONE)
            ctx.draw_text_anchored(
                price_text, _f(density * 20.0), _f(h * 0.12), -1, 0, 0)

            # Change percentage
            ctx.painter.set_color(0xFF4CD964) \
                .set_text_size((density * 16.0).to_float()).commit()
            change_text = ctx.create_text_from_float(
                change_pct.to_float(), 2, 2,
                Rc.TextFromFloat.PAD_AFTER_ZERO | Rc.TextFromFloat.PAD_PRE_NONE)
            change_label = ctx.text_merge(
                ctx.add_text("\u25B2 "), change_text, ctx.add_text("%"))
            ctx.draw_text_anchored(
                change_label, _f(density * 20.0), _f(h * 0.22), -1, 0, 0)

            ctx.painter.set_color(0x66FFFFFF) \
                .set_text_size((density * 11.0).to_float()).commit()
            ctx.draw_text_anchored(
                "24h", _f(density * 20.0), _f(h * 0.30), -1, 0, 0)

            # Build sparkline path
            start_y = g_bottom - (rf_array_spline(
                prices, ctx.rf(0.0)) - price_min) / price_range * g_h
            line_path = ctx.path_create(g_left.to_float(), start_y.to_float())

            steps = 80.0
            with ctx.loop_range(1, 1, steps) as step:
                t = step / steps
                x = g_left + g_w * t
                price = rf_array_spline(prices, t)
                y = g_bottom - (price - price_min) / price_range * g_h
                ctx.path_append_line_to(
                    line_path, x.to_float(), y.to_float())

            # Draw line
            ctx.painter.set_color(0xFF4CD964) \
                .set_style(STYLE_STROKE) \
                .set_stroke_width((density * 2.0).to_float()) \
                .set_stroke_cap(CAP_ROUND).commit()
            ctx.draw_path(line_path)

            # Close path for gradient fill
            ctx.path_append_line_to(
                line_path, g_right.to_float(), g_bottom.to_float())
            ctx.path_append_line_to(
                line_path, g_left.to_float(), g_bottom.to_float())
            ctx.path_append_close(line_path)

            ctx.painter.set_style(STYLE_FILL) \
                .set_linear_gradient(
                    g_left.to_float(), g_top.to_float(),
                    g_left.to_float(), g_bottom.to_float(),
                    [0x664CD964, 0x00000000], None, 0).commit()
            ctx.draw_path(line_path)
            ctx.painter.set_shader(0).commit()

            # Min/max indicators
            ctx.painter.set_color(0x66FFFFFF) \
                .set_text_size((density * 9.0).to_float()) \
                .set_style(STYLE_FILL).commit()
            min_text = ctx.create_text_from_float(
                price_min.to_float(), 5, 0, Rc.TextFromFloat.PAD_PRE_NONE)
            max_text = ctx.create_text_from_float(
                price_max.to_float(), 5, 0, Rc.TextFromFloat.PAD_PRE_NONE)
            ctx.draw_text_anchored(
                min_text, _f(g_right), _f(g_bottom + density * 10.0), 1, 0, 0)
            ctx.draw_text_anchored(
                max_text, _f(g_right), _f(g_top - density * 4.0), 1, 0, 0)
    return ctx


# =====================================================================
# 9. Moon Phase Dial
#    Circular moon visualization with phase name and illumination
# =====================================================================
def demo_moon_phase_dial():
    data = [0.72, 3.0]  # illumination 0-1, phaseIndex 0-7
    phase_names = [
        "New Moon", "Waxing Crescent", "First Quarter", "Waxing Gibbous",
        "Full Moon", "Waning Gibbous", "Last Quarter", "Waning Crescent",
    ]

    ctx = RcContext(400, 400, "Moon Phase Dial",
                    api_level=7, profiles=0)
    with ctx.root():
        with ctx.canvas(Modifier().fill_max_size().background(0xFF0B0D17)):
            w = ctx.ComponentWidth()
            h = ctx.ComponentHeight()
            cx = w / 2.0
            cy = h * 0.42
            density = ctx.rf(Rc.System.DENSITY)
            size = w.min(h)
            moon_r = size * 0.3

            values = ctx.rf(ctx.add_float_array(data))
            illumination = values[ctx.rf(0.0)]
            phase_idx = values[ctx.rf(1.0)]
            name_list = ctx.add_string_list(*phase_names)

            # Outer glow ring
            ctx.painter.set_color(0x22FFFFFF) \
                .set_style(STYLE_STROKE) \
                .set_stroke_width((density * 8.0).to_float()).commit()
            ctx.draw_circle(
                cx.to_float(), cy.to_float(),
                (moon_r + density * 6.0).to_float())

            # Full bright moon surface
            ctx.painter.set_color(0xFFE8E8D0).set_style(STYLE_FILL).commit()
            ctx.draw_circle(cx.to_float(), cy.to_float(), moon_r.to_float())

            # Subtle surface texture (dark spots)
            ctx.painter.set_color(0x15000000).commit()
            ctx.draw_circle(
                (cx - moon_r * 0.2).to_float(),
                (cy - moon_r * 0.15).to_float(),
                (moon_r * 0.15).to_float())
            ctx.draw_circle(
                (cx + moon_r * 0.25).to_float(),
                (cy + moon_r * 0.1).to_float(),
                (moon_r * 0.1).to_float())
            ctx.draw_circle(
                (cx - moon_r * 0.1).to_float(),
                (cy + moon_r * 0.3).to_float(),
                (moon_r * 0.12).to_float())

            # Shadow overlay
            with ctx.saved():
                shadow_left = cx - moon_r
                shadow_right = cx + moon_r - illumination * moon_r * 2.0
                ctx.clip_rect(
                    shadow_left.to_float(),
                    (cy - moon_r).to_float(),
                    shadow_right.to_float(),
                    (cy + moon_r).to_float())
                ctx.painter.set_color(0xDD0B0D17).commit()
                ctx.draw_circle(
                    cx.to_float(), cy.to_float(), moon_r.to_float())

            # Moon outline
            ctx.painter.set_color(0x33FFFFFF) \
                .set_style(STYLE_STROKE) \
                .set_stroke_width((density * 1.0).to_float()).commit()
            ctx.draw_circle(cx.to_float(), cy.to_float(), moon_r.to_float())

            # Phase name
            phase_name = ctx.text_lookup(name_list, phase_idx.to_float())
            ctx.painter.set_color(WHITE) \
                .set_style(STYLE_FILL) \
                .set_text_size((density * 18.0).to_float()) \
                .set_typeface(0, 600, False).commit()
            ctx.draw_text_anchored(phase_name, _f(cx), _f(h * 0.74), 0, 0, 0)

            # Illumination percentage
            ctx.painter.set_color(0xAAFFFFFF) \
                .set_text_size((density * 14.0).to_float()) \
                .set_typeface(0, 400, False).commit()
            illum_text = ctx.create_text_from_float(
                (illumination * 100.0).to_float(), 3, 0,
                Rc.TextFromFloat.PAD_PRE_NONE)
            illum_label = ctx.text_merge(
                illum_text, ctx.add_text("% illuminated"))
            ctx.draw_text_anchored(illum_label, _f(cx), _f(h * 0.81), 0, 0, 0)

            # Decorative stars
            ctx.painter.set_color(0x66FFFFFF) \
                .set_text_size((density * 8.0).to_float()).commit()
            star_positions = [
                0.1, 0.15, 0.85, 0.2, 0.15, 0.7,
                0.9, 0.65, 0.75, 0.1, 0.3, 0.9,
            ]
            for s in range(len(star_positions) // 2):
                ctx.draw_text_anchored(
                    "\u00B7",
                    _f(w * star_positions[s * 2]),
                    _f(h * star_positions[s * 2 + 1]),
                    0, 0, 0)
    return ctx


# =====================================================================
# 10. Hydration Progress Wave
#     Animated wave/liquid fill showing water intake progress
# =====================================================================
def demo_hydration_wave():
    data = [5.0, 8.0]  # cupsConsumed, goalCups

    ctx = RcContext(400, 450, "Hydration Progress Wave",
                    api_level=7, profiles=0)
    with ctx.root():
        with ctx.canvas(Modifier().fill_max_size().background(0xFF0F172A)):
            w = ctx.ComponentWidth()
            h = ctx.ComponentHeight()
            cx = w / 2.0
            density = ctx.rf(Rc.System.DENSITY)

            values = ctx.rf(ctx.add_float_array(data))
            cups = values[ctx.rf(0.0)]
            goal = values[ctx.rf(1.0)]
            progress = rf_min(cups / goal, ctx.rf(1.0))

            # Container dimensions (glass shape)
            glass_w = w * 0.45
            glass_h = h * 0.55
            glass_left = cx - glass_w / 2.0
            glass_right = cx + glass_w / 2.0
            glass_top = h * 0.18
            glass_bottom = glass_top + glass_h
            corner_r = density * 12.0

            # Glass outline
            ctx.painter.set_color(0x44FFFFFF) \
                .set_style(STYLE_STROKE) \
                .set_stroke_width((density * 2.0).to_float()).commit()
            ctx.draw_round_rect(
                _f(glass_left), _f(glass_top), _f(glass_w), _f(glass_h),
                _f(corner_r), _f(corner_r))

            # Wave fill - animated sinusoidal surface
            fill_h = progress * glass_h
            wave_y = glass_bottom - fill_h
            wave_amp = density * 6.0
            wave_freq = 3.14159 * 4.0  # 2 full waves across glass

            # Build wave path: bottom-left -> wave surface -> bottom-right -> close
            wave_path = ctx.path_create(
                glass_left.to_float(), glass_bottom.to_float())

            # Wave surface from left to right
            wave_steps = 40.0
            with ctx.loop_range(0, 1, wave_steps + 1.0) as step:
                t = (step / wave_steps).flush()
                x = (glass_left + t * glass_w).flush()
                y = wave_y + rf_sin(t * wave_freq + ctx.ContinuousSec() * 3.0) * wave_amp
                ctx.path_append_line_to(
                    wave_path, x.to_float(), y.to_float())

            # Close: right side down, across bottom, back up
            ctx.path_append_line_to(
                wave_path, glass_right.to_float(), glass_bottom.to_float())
            ctx.path_append_close(wave_path)

            # Fill with water gradient
            ctx.painter.set_style(STYLE_FILL) \
                .set_linear_gradient(
                    glass_left.to_float(), wave_y.to_float(),
                    glass_left.to_float(), glass_bottom.to_float(),
                    [0xFF38BDF8, 0xFF0284C7], None, 0).commit()

            # Clip to glass interior
            with ctx.saved():
                ctx.clip_rect(
                    (glass_left + density * 2.0).to_float(),
                    (glass_top + density * 2.0).to_float(),
                    (glass_right - density * 2.0).to_float(),
                    (glass_bottom - density * 2.0).to_float())
                ctx.draw_path(wave_path)
            ctx.painter.set_shader(0).commit()

            # Cup count display
            ctx.painter.set_color(WHITE) \
                .set_style(STYLE_FILL) \
                .set_text_size((density * 42.0).to_float()) \
                .set_typeface(0, 700, False).commit()
            cups_text = ctx.create_text_from_float(
                cups.to_float(), 1, 0, Rc.TextFromFloat.PAD_PRE_NONE)
            ctx.draw_text_anchored(cups_text, _f(cx), _f(h * 0.83), 0, 0, 0)

            ctx.painter.set_color(0xAAFFFFFF) \
                .set_text_size((density * 16.0).to_float()) \
                .set_typeface(0, 400, False).commit()
            goal_text = ctx.create_text_from_float(
                goal.to_float(), 1, 0, Rc.TextFromFloat.PAD_PRE_NONE)
            label = ctx.text_merge(
                ctx.add_text("of "), goal_text, ctx.add_text(" cups"))
            ctx.draw_text_anchored(label, _f(cx), _f(h * 0.90), 0, 0, 0)

            # Progress percentage inside glass
            ctx.painter.set_color(0xCCFFFFFF) \
                .set_text_size((density * 20.0).to_float()) \
                .set_typeface(0, 700, False).commit()
            pct_val = progress * 100.0
            pct_text = ctx.create_text_from_float(
                pct_val.to_float(), 3, 0, Rc.TextFromFloat.PAD_PRE_NONE)
            pct_label = ctx.text_merge(pct_text, ctx.add_text("%"))
            ctx.draw_text_anchored(
                pct_label, _f(cx), _f(glass_top + glass_h * 0.4), 0, 0, 0)

            # Water drop icon
            ctx.painter.set_color(0xFF38BDF8) \
                .set_text_size((density * 24.0).to_float()).commit()
            ctx.draw_text_anchored(
                "\u2B29", _f(cx), _f(h * 0.10), 0, 0, 0)
            ctx.painter.set_color(WHITE) \
                .set_text_size((density * 14.0).to_float()).commit()
            ctx.draw_text_anchored(
                "Hydration", _f(cx), _f(h * 0.10), 0, 3.0, 0)
    return ctx


# =====================================================================
# Main: generate all demos and compare against references
# =====================================================================
if __name__ == '__main__':
    outdir = os.path.join(os.path.dirname(__file__), '..', 'output')
    os.makedirs(outdir, exist_ok=True)

    ref_dir = os.path.join(
        os.path.dirname(__file__), '..', '..',
        'integration-tests', 'player-view-demos',
        'src', 'main', 'res', 'raw')

    demos = [
        ('activity_rings', demo_activity_rings),
        ('battery_radial_gauge', demo_battery_radial_gauge),
        ('calendar_heatmap_grid', demo_calendar_heatmap_grid),
        ('heart_rate_timeline', demo_heart_rate_timeline),
        ('hydration_wave', demo_hydration_wave),
        ('moon_phase_dial', demo_moon_phase_dial),
        ('sleep_quality_rings', demo_sleep_quality_rings),
        ('step_progress_arc', demo_step_progress_arc),
        ('stock_sparkline', demo_stock_sparkline),
        ('weather_forecast_bars', demo_weather_forecast_bars),
    ]

    for name, func in demos:
        try:
            ctx = func()
            data = ctx.encode()
            path = os.path.join(outdir, f'{name}.rc')
            ctx.save(path)

            # Compare against reference
            ref_path = os.path.join(ref_dir, f'{name}.rc')
            if os.path.exists(ref_path):
                with open(ref_path, 'rb') as f:
                    ref_data = f.read()
                if data == ref_data:
                    status = "MATCH"
                else:
                    # Find first difference
                    min_len = min(len(data), len(ref_data))
                    first_diff = -1
                    for j in range(min_len):
                        if data[j] != ref_data[j]:
                            first_diff = j
                            break
                    if first_diff == -1:
                        first_diff = min_len
                    diff_count = sum(1 for a, b in zip(data, ref_data) if a != b)
                    if len(data) != len(ref_data):
                        diff_count += abs(len(data) - len(ref_data))
                    status = (f"DIFF: {len(data)} vs {len(ref_data)} bytes, "
                              f"{diff_count} byte diffs, first@{first_diff}")
            else:
                status = "NO REF"

            print(f'{name}: {len(data)} bytes -> {path} [{status}]')
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f'{name}: ERROR - {e}')

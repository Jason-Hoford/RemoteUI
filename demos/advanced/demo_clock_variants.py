"""Clock variant demos. Port of ExampleClock.kt (basicClock),
DigitalKClock.kt-style digital clock, and ClockDemo2.java (clock2).

Target .rc files:
  - clock.rc           -> basic_clock()  (ExampleClock.kt basicClock)
  - digital_clock1.rc  -> digital_clock1()  (DigitalKClock-style)
  - clock_demo2_jclock2.rc -> clock_demo2_jclock2()  (ClockDemo2.java clock2)

Demonstrates:
- Canvas drawing with expression-based coordinates
- Time variables (CONTINUOUS_SEC, TIME_IN_MIN, TIME_IN_HR)
- Matrix transforms (save/restore/rotate)
- Painter state (color, strokeWidth, strokeCap, radialGradient, sweepGradient)
- drawLine, drawCircle, drawRoundRect
- Loop with polar coordinates (superellipse path generation)
- ClipPath, drawPath, drawTweenPath
- Conditional operations
- Touch interaction with easing
- Sunrise/sunset calculations
- Text from float, text merge, text lookup
- String list and float array data
"""
import sys
import os
import math

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RcContext, Modifier, Rc, RemoteComposeWriter
from rcreate.modifiers import RecordingModifier
from rcreate.types.nan_utils import id_from_nan, as_nan

FE = Rc.FloatExpression
CONTINUOUS_SEC = Rc.Time.CONTINUOUS_SEC
TIME_IN_SEC = Rc.Time.TIME_IN_SEC
TIME_IN_MIN = Rc.Time.TIME_IN_MIN
TIME_IN_HR = Rc.Time.TIME_IN_HR
OFFSET_TO_UTC = Rc.Time.OFFSET_TO_UTC
DAY_OF_YEAR = Rc.Time.DAY_OF_YEAR
FONT_SIZE = Rc.System.FONT_SIZE

STYLE_FILL = Rc.Paint.STYLE_FILL
STYLE_STROKE = Rc.Paint.STYLE_STROKE
CAP_ROUND = Rc.Paint.CAP_ROUND

# Android color constants (matching Java Color.*)
BLACK = 0xFF000000
WHITE = 0xFFFFFFFF
GRAY = 0xFF888888
LTGRAY = 0xFFCCCCCC
DKGRAY = 0xFF444444
RED = 0xFFFF0000
BLUE = 0xFF0000FF

PI = math.pi


# ============================================================================
# Helper: make a simple result wrapper
# ============================================================================
def _make_result(rc):
    class Result:
        def encode(self):
            return rc.encode_to_byte_array()

        def save(self, path):
            with open(path, 'wb') as f:
                f.write(self.encode())
    return Result()


# ============================================================================
# DEMO 1: basic_clock  (port of ExampleClock.kt basicClock)
#   V6 writer-based analog clock with blue background, minute/hour/second hands
#   Target: clock.rc
# ============================================================================
def basic_clock():
    """Port of ExampleClock.kt basicClock().

    Simple analog clock with blue rounded-rect background, gray minute hand,
    light gray hour hand, and white second hand using sin/cos expressions.
    """
    rc = RemoteComposeWriter(500, 500, "Simple Timer", api_level=6, profiles=0)

    def content():
        rc.start_box(RecordingModifier().fill_max_size(),
                      Rc.Layout.START, Rc.Layout.START)
        rc.start_canvas(RecordingModifier().fill_max_size())

        w = rc.add_component_width_value()
        h = rc.add_component_height_value()
        cx = rc.float_expression(w, 2.0, FE.DIV)
        cy = rc.float_expression(h, 2.0, FE.DIV)
        rad = rc.float_expression(cx, cy, FE.MIN)

        # Blue rounded-rect background
        rc.rc_paint.set_color(BLUE).commit()
        rc.draw_round_rect(0, 0, w, h,
                           rc.float_expression(rad, 4.0, FE.DIV),
                           rc.float_expression(rad, 4.0, FE.DIV))

        # Minute hand
        rc.rc_paint.set_color(GRAY).set_stroke_width(32.0) \
            .set_stroke_cap(CAP_ROUND).commit()
        rc.save()
        min_angle = rc.float_expression(TIME_IN_MIN, 6.0, FE.MUL)
        rc.rotate(min_angle, cx, cy)
        rc.draw_line(cx, cy, cx,
                     rc.float_expression(cy, rad, 0.8, FE.MUL, FE.SUB))
        rc.restore()

        # Hour hand
        rc.rc_paint.set_color(LTGRAY).set_stroke_width(16.0) \
            .set_stroke_cap(CAP_ROUND).commit()
        rc.save()
        hr_angle = rc.float_expression(TIME_IN_HR, 30.0, FE.MUL)
        rc.rotate(hr_angle, cx, cy)
        rc.draw_line(cx, cy, cx,
                     rc.float_expression(cy, rad, 2.0, FE.DIV, FE.SUB))
        rc.restore()

        # Second hand (using sin/cos for smooth sweep)
        rc.rc_paint.set_color(WHITE).set_stroke_width(4.0).commit()
        two_pi_over_60 = 2.0 * PI / 60.0
        sec_x = rc.float_expression(
            w, 2.0, FE.DIV, rad,
            CONTINUOUS_SEC, two_pi_over_60, FE.MUL, FE.SIN,
            FE.MUL, FE.ADD)
        sec_y = rc.float_expression(
            h, 2.0, FE.DIV, rad,
            CONTINUOUS_SEC, two_pi_over_60, FE.MUL, FE.COS,
            FE.MUL, FE.SUB)
        rc.draw_line(cx, cy, sec_x, sec_y)

        rc.end_canvas()
        rc.end_box()

    rc.root(content)
    return _make_result(rc)


# ============================================================================
# DEMO 2: digital_clock1  (DigitalKClock-style scrolling-digit clock)
#   Target: digital_clock1.rc
# ============================================================================
def digital_clock1():
    """Port of DigitalKClock.kt kClock1() style.

    A digital clock with scrolling hour and minute digits in blue rounded
    rectangles. Uses animated float expressions with cubic overshoot.
    """
    rc = RemoteComposeWriter(500, 1500, "DClock", api_level=6, profiles=0)

    def _draw_digit_column(rc_wr, val_expr, is_hours):
        """Draw a scrolling digit column."""
        w = rc_wr.add_component_width_value()
        h = rc_wr.add_component_height_value()
        cx_val = rc_wr.float_expression(w, 0.5, FE.MUL)
        cy_val = rc_wr.float_expression(h, 0.5, FE.MUL)
        font_size = rc_wr.float_expression(w, h, FE.MIN, 2.0, FE.DIV)
        mod_val = 12 if is_hours else 60

        # Blue background
        rc_wr.rc_paint.set_color(BLUE).set_style(STYLE_FILL).commit()
        rc_wr.draw_round_rect(0.0, 0.0, w, h, 32.0, 32.0)

        rc_wr.save()
        rc_wr.clip_rect(0.0, 0.0, w, h)

        # Scroll animation
        anim = rc_wr.float_expression(val_expr, -1.0, font_size, FE.MUL, FE.MUL)
        rc_wr.translate(0.0, anim)

        rc_wr.rc_paint.set_text_size(font_size).set_color(RED) \
            .set_style(STYLE_FILL).commit()

        rc_wr.translate(0.0, rc_wr.float_expression(font_size, -4.0, FE.MUL))

        for i in range(-3, mod_val + 3):
            rc_wr.translate(0.0, font_size)
            if is_hours:
                value = ((12 + i - 1) % 12) + 1
            else:
                value = (60 + i) % 60
            text_str = f"{value:02d}"
            rc_wr.draw_text_anchored(text_str, cx_val, cy_val, 0.0, 0.0, 0)

        rc_wr.restore()

    def content():
        rc.start_row(RecordingModifier().fill_max_width().fill_max_height().padding(10),
                     Rc.Layout.START, Rc.Layout.START)

        # Hour column (left)
        rc.start_box(
            RecordingModifier().horizontal_weight(1.0).fill_max_height().padding(0, 0, 5, 0),
            Rc.Layout.START, Rc.Layout.TOP)
        rc.start_canvas(RecordingModifier().fill_max_size())

        hr_expr = rc.float_expression(
            rc.float_expression(TIME_IN_HR, 1.0, FE.SUB, 12.0, FE.MOD, 1.0, FE.ADD),
            animation=rc.anim(0.4, Rc.Animate.CUBIC_OVERSHOOT))
        _draw_digit_column(rc, hr_expr, True)

        rc.end_canvas()
        rc.end_box()

        # Minute column (right)
        rc.start_box(
            RecordingModifier().horizontal_weight(1.0).fill_max_height().padding(5, 0, 0, 0),
            Rc.Layout.START, Rc.Layout.TOP)
        rc.start_canvas(RecordingModifier().fill_max_size())

        min_expr = rc.float_expression(
            rc.float_expression(TIME_IN_MIN, 60.0, FE.MOD),
            animation=rc.anim(0.4, Rc.Animate.CUBIC_OVERSHOOT))
        _draw_digit_column(rc, min_expr, False)

        rc.end_canvas()
        rc.end_box()

        rc.end_row()

    rc.root(content)
    return _make_result(rc)


# ============================================================================
# DEMO 3: clock_demo2_jclock2  (port of ClockDemo2.java clock2)
#   Complex clock with time zones, superellipse clip path, gradients, touch
#   Target: clock_demo2_jclock2.rc
# ============================================================================

# Timezone location data (from ClockDemo2.Locations)
_LOCATIONS = [
    (-10, "Hawaii",       21.3,  -157.9),
    (-9,  "Anchorage",    61.2,  -149.9),
    (-8,  "Los_Angeles",  37.8,  -122.4),
    (-7,  "Denver",       39.7,  -104.9),
    (-6,  "Mexico",       19.4,  -99.1),
    (-5,  "New_York",     40.7,  -74.0),
    (-4,  "Caracas",      10.5,  -66.9),
    (-3,  "Buenos_Aires", -34.6, -58.4),
    (-2,  "Georgia",      -54.3, -36.5),
    (-1,  "Azores",       37.7,  -25.7),
    (0,   "London",       51.5,  0.1),
    (+1,  "Berlin",       52.5,  13.4),
    (+2,  "Cairo",        30.0,  31.2),
    (+3,  "Riyadh",       24.7,  46.7),
    (+4,  "Dubai",        25.2,  55.3),
    (+6,  "Dhaka",        23.8,  90.4),
    (+7,  "Bangkok",      13.8,  100.5),
    (+8,  "Shanghai",     31.2304, 121.4737),
    (+9,  "Tokyo",        35.7,  139.7),
    (+10, "Sydney",       -33.9, 151.2),
    (+12, "Auckland",     -36.8, 174.7),
    (+13, "Tonga",        -21.1, -175.2),
    (+14, "Line",         1.9,   -157.4),
]


def _get_offsets():
    return [float(loc[0] + 1) for loc in _LOCATIONS]  # +1 for daylight


def _get_latitudes():
    return [float(loc[2]) for loc in _LOCATIONS]


def _get_longitudes():
    return [float(loc[3]) for loc in _LOCATIONS]


def _get_names():
    return [loc[1] for loc in _LOCATIONS]


def _gen_path_cd2(rc, center_x, center_y, rad1, rad2):
    """Generate superellipse clock face path (ClockDemo2.genPath)."""
    second = rc.create_float_id()
    sqrt2 = math.sqrt(2)
    n = rc.float_expression(
        1, 0.5, sqrt2, rad2, rad1, FE.DIV, 1, sqrt2, FE.SUB,
        FE.MUL, FE.ADD, FE.LN, 2, FE.LN, FE.DIV, FE.SUB, FE.DIV)
    n1 = rc.float_expression(1, n, FE.DIV)
    pid = rc.path_create(center_x,
                         rc.float_expression(center_y, rad1, FE.SUB))

    def loop_body():
        ang = rc.float_expression(second, 2 * PI / 60, FE.MUL, PI / 2, FE.SUB)
        cos_ang = rc.float_expression(ang, FE.COS)
        sin_ang = rc.float_expression(ang, FE.SIN)
        cos4 = rc.float_expression(cos_ang, FE.ABS, n, FE.POW)
        sin4 = rc.float_expression(sin_ang, FE.ABS, n, FE.POW)
        polar_radius = rc.float_expression(
            rad1, cos4, sin4, FE.ADD, FE.ABS, n1, FE.POW, FE.DIV)
        offset_x = rc.float_expression(
            polar_radius, cos_ang, FE.MUL, center_x, FE.ADD)
        offset_y = rc.float_expression(
            polar_radius, sin_ang, FE.MUL, center_y, FE.ADD)
        rc.path_append_line_to(pid, offset_x, offset_y)

    rc.loop(id_from_nan(second), 0.0, 0.2, 60, loop_body)
    rc.path_append_close(pid)
    return pid


def _sunrise_sunset(rc, timezone_offset, latitude, longitude):
    """Calculate sunrise/sunset times (ClockDemo2.sunriseSunset)."""
    day_of_year = DAY_OF_YEAR
    # declination = 23.45 * sin(radians(360 * (284 + dayOfYear) / 365))
    declination = rc.float_expression(
        day_of_year, 284, FE.ADD, 360.0 / 365.0, FE.MUL,
        FE.RAD, FE.SIN, 23.45, FE.MUL)
    lat_rad = rc.float_expression(latitude, FE.RAD)
    decl_rad = rc.float_expression(declination, FE.RAD)
    # hourAngleArg = -tan(latRad) * tan(declRad)
    hour_angle_arg = rc.float_expression(
        0, lat_rad, FE.TAN, decl_rad, FE.TAN, FE.MUL, FE.SUB)
    hour_angle = rc.float_expression(hour_angle_arg, FE.ACOS)
    hour_angle_hours = rc.float_expression(hour_angle, FE.DEG, 15.0, FE.DIV)
    solar_noon = rc.float_expression(12.0, longitude, 15.0, FE.DIV, FE.SUB)
    sunrise_local = rc.float_expression(
        solar_noon, hour_angle_hours, FE.SUB, timezone_offset, FE.ADD)
    sunset_local = rc.float_expression(
        solar_noon, hour_angle_hours, FE.ADD, timezone_offset, FE.ADD)
    return sunrise_local, sunset_local


def _draw_time_zone(rc, city_text_id, utc_offset, cx, py, rad,
                    sunrise, sunset):
    """Draw a single timezone clock face (ClockDemo2.drawTimeZone)."""
    outer_edge = 0.2
    text_size = rc.float_expression(outer_edge, rad, FE.MUL)
    rc.rc_paint.set_text_size(text_size).commit()
    rc.save()

    # Current hour in this timezone
    hr = rc.float_expression(
        utc_offset, TIME_IN_HR, OFFSET_TO_UTC, 3600, FE.DIV,
        FE.SUB, FE.ADD, 12, FE.MOD)
    hr_id = rc.create_text_from_float(hr, 3, 0, 0)
    min_val = rc.float_expression(TIME_IN_MIN, 60, FE.MOD)
    min_id = rc.create_text_from_float(
        min_val, 2, 0, Rc.TextFromFloat.PAD_PRE_ZERO)
    colon = rc.add_text(":")
    clock_text = rc.text_merge(hr_id, colon)
    clock_text = rc.text_merge(clock_text, min_id)

    sunset_pos = rc.float_expression(sunset, 24, FE.DIV)
    sunrise_pos = rc.float_expression(sunrise, 24, FE.DIV)

    # Day/night gradient background
    rc.save()
    rc.rotate(-90, cx, py)
    rc.rc_paint.set_sweep_gradient(
        cx, py,
        [0xFF000055, 0xFF000055, 0xFF7799EE, 0xFF7799EE,
         0xFF000055, 0xFF000055],
        positions=[0.0, sunrise_pos, sunrise_pos,
                   sunset_pos, sunset_pos, 1.0]).commit()
    rc.draw_circle(cx, py, rad)
    rc.restore()

    # Dark center
    rc.rc_paint.set_shader(0).set_color(DKGRAY).commit()
    rc.draw_circle(cx, py,
                   rc.float_expression(rad, 1.0 - outer_edge, FE.MUL))

    # Clock text and city name
    rc.rc_paint.set_shader(0).set_color(LTGRAY).commit()
    rc.draw_text_anchored(clock_text, cx, py, 0, -3.0, 0)
    rc.draw_text_anchored(
        city_text_id, cx, py, 0, 0,
        Rc.TextAnchorMask.MEASURE_EVERY_TIME)

    # Sunrise/sunset text
    hr_sunrise = rc.create_text_from_float(sunrise, 2, 0, 0)
    min_sunrise = rc.create_text_from_float(
        rc.float_expression(sunrise, 1, FE.MOD, 60, FE.MUL), 2, 0, 0)
    hr_sunset = rc.create_text_from_float(sunset, 2, 0, 0)
    min_sunset = rc.create_text_from_float(
        rc.float_expression(sunset, 1, FE.MOD, 60, FE.MUL), 2, 0, 0)
    colon2 = rc.add_text(":")
    sunrise_text = rc.text_merge(rc.text_merge(hr_sunrise, colon2), min_sunrise)
    colon3 = rc.add_text(":")
    sunset_text = rc.text_merge(rc.text_merge(hr_sunset, colon3), min_sunset)
    rc.draw_text_anchored(sunrise_text, cx, py, 0, +3.0, 0)
    rc.draw_text_anchored(sunset_text, cx, py, 0, +6, 0)
    rc.restore()

    # Hour markers around the edge
    top = rc.float_expression(py, rad, FE.SUB)
    rc.save()
    for i in range(0, 24, 2):
        time_hr = 24 if i == 0 else i
        rc.rc_paint.set_color(0xFFAABB33).commit()
        rc.add_conditional_operations(Rc.Condition.GT, float(i), sunrise)
        rc.rc_paint.set_color(0xFF775533).commit()
        rc.end_conditional_operations()
        rc.add_conditional_operations(Rc.Condition.GT, float(i), sunset)
        rc.rc_paint.set_color(0xFFAABB33).commit()
        rc.end_conditional_operations()
        rc.draw_text_anchored(str(time_hr), cx, top, 0, +1.3, 0)
        rc.rotate(30, cx, py)
    rc.restore()

    # Current time indicator
    rc.save()
    rc.rc_paint.set_color(0x77FF4500).commit()
    angle = rc.float_expression(
        hr, min_val, 1.0 / 60.0, FE.MUL, FE.ADD,
        360.0 / 24.0, FE.MUL)
    rc.rotate(angle, cx, py)
    rc.translate(0, text_size)
    rc.scale(0.5, 1, cx, top)
    rc.draw_circle(cx, top, rc.float_expression(text_size, 2, FE.DIV))
    rc.restore()

    rc.rc_paint.set_color(BLACK).commit()


def _draw_time_zones(rc, path_id, w, h, cx, cy, names, utc_off, lat, lon):
    """Draw timezone clocks around the face (ClockDemo2.drawTimeZones)."""
    rad = rc.float_expression(w, h, FE.MIN, 2, FE.DIV)
    border = rc.float_expression(rad, 0.61, FE.MUL)
    str_list = rc.add_string_list(*names)
    step = 400.0

    rc.add_touch(0, float('nan'), len(names) * step,
                 Rc.Touch.STOP_NOTCHES_EVEN,
                 0, 0, [float(len(names))],
                 rc.easing(3.0, 5.0, 60.0),
                 Rc.Touch.POSITION_Y)

    gmt_rad = rc.float_expression(rad, 0.23, FE.MUL)
    rc.save()

    sun_colors = [0xFF9999FF, 0xFF9999FF, 0xFF993300,
                  0xFF000044, 0xFF000044, 0xFF993300]
    sun_pos = [0.0, 0.20, 0.40, 0.60, 0.80, 1.0]
    rc.rc_paint.set_text_size(45.0).commit()

    show_n_gmts = 8
    for i in range(show_n_gmts):
        x = rc.float_expression(
            cx, float(2 * PI * i / show_n_gmts), FE.SIN,
            border, FE.MUL, FE.ADD)
        y = rc.float_expression(
            cy, float(2 * PI * i / show_n_gmts), FE.COS,
            border, FE.MUL, FE.ADD)
        count = float(i)

        offset_calc = rc.float_expression(
            utc_off, count, FE.A_DEREF)
        day0 = _sunrise_sunset(
            rc, offset_calc,
            rc.float_expression(lat, count, FE.A_DEREF),
            rc.float_expression(lon, count, FE.A_DEREF))

        rc.rc_paint.set_sweep_gradient(x, y, sun_colors,
                                       positions=sun_pos).commit()

        city_name = rc.text_lookup(str_list, count)
        _draw_time_zone(rc, city_name, offset_calc, x, y,
                        gmt_rad, day0[0], day0[1])

    rc.restore()
    rc.rc_paint.set_shader(0).commit()


def _draw_ticks_cd2(rc, center_x, center_y, rad1, rad2, sec):
    """Draw tick marks (ClockDemo2.drawTicks)."""
    second = rc.create_float_id()
    font_size = rc.float_expression(FONT_SIZE, 2, FE.MUL)
    rc.rc_paint.set_color(LTGRAY).set_text_size(font_size).commit()

    sqrt2 = math.sqrt(2)
    n = rc.float_expression(
        1, 0.5, sqrt2, rad2, rad1, FE.DIV, 1, sqrt2, FE.SUB,
        FE.MUL, FE.ADD, FE.LN, 2, FE.LN, FE.DIV, FE.SUB, FE.DIV)
    n1 = rc.float_expression(1, n, FE.DIV)

    # Loop 1: tick dots every 1 unit
    def loop1():
        ang = rc.float_expression(
            second, 2 * PI / 60, FE.MUL, PI / 2, FE.SUB)
        ang_deg = rc.float_expression(second, 6, FE.MUL)
        cos_ang = rc.float_expression(ang, FE.COS)
        sin_ang = rc.float_expression(ang, FE.SIN)
        cos4 = rc.float_expression(cos_ang, FE.ABS, n, FE.POW)
        sin4 = rc.float_expression(sin_ang, FE.ABS, n, FE.POW)
        polar_radius = rc.float_expression(
            rad1, cos4, sin4, FE.ADD, FE.ABS, n1, FE.POW, FE.DIV)
        offset_x = rc.float_expression(
            polar_radius, cos_ang, FE.MUL, center_x, FE.ADD)
        offset_y = rc.float_expression(
            polar_radius, sin_ang, FE.MUL, center_y, FE.ADD)
        scale = rc.float_expression(
            1, sec, 60, FE.MOD, second, FE.SUB, FE.ABS,
            FE.SUB, 0, FE.MAX, 0.5, FE.ADD)
        rc.save()
        rc.rotate(ang_deg, offset_x, offset_y)
        pos_y = rc.float_expression(offset_y, 6, FE.ADD)
        rc.scale(scale, 2, offset_x, offset_y)
        rc.draw_circle(offset_x, pos_y, 6)
        rc.restore()

    rc.loop(id_from_nan(second), 0.0, 1, 60, loop1)

    rc.rc_paint.set_color(WHITE).set_text_size(font_size).commit()

    # Loop 2: 5-minute marks
    def loop2():
        ang = rc.float_expression(
            second, 2 * PI / 60, FE.MUL, PI / 2, FE.SUB)
        ang_deg = rc.float_expression(second, 6, FE.MUL)
        cos_ang = rc.float_expression(ang, FE.COS)
        sin_ang = rc.float_expression(ang, FE.SIN)
        cos4 = rc.float_expression(cos_ang, FE.ABS, n, FE.POW)
        sin4 = rc.float_expression(sin_ang, FE.ABS, n, FE.POW)
        polar_radius = rc.float_expression(
            rad1, cos4, sin4, FE.ADD, FE.ABS, n1, FE.POW, FE.DIV)
        offset_x = rc.float_expression(
            polar_radius, cos_ang, FE.MUL, center_x, FE.ADD)
        offset_y = rc.float_expression(
            polar_radius, sin_ang, FE.MUL, center_y, FE.ADD)
        rc.save()
        rc.rotate(ang_deg, offset_x, offset_y)
        pos_y = rc.float_expression(offset_y, 6, FE.ADD)
        rc.scale(0.5, 3, offset_x, offset_y)
        rc.draw_circle(offset_x, pos_y, 6)
        rc.restore()

    rc.loop(id_from_nan(second), 0.0, 5, 60, loop2)

    # Loop 3: hour numbers every 15 units
    inset = 70
    def loop3():
        ang = rc.float_expression(
            second, 2 * PI / 60, FE.MUL, PI / 2, FE.SUB)
        cos_ang = rc.float_expression(ang, FE.COS)
        sin_ang = rc.float_expression(ang, FE.SIN)
        cos4 = rc.float_expression(
            cos_ang, FE.DUP, FE.MUL, FE.DUP, FE.MUL)
        sin4 = rc.float_expression(
            sin_ang, FE.DUP, FE.MUL, FE.DUP, FE.MUL)
        polar_radius = rc.float_expression(
            rad1, cos4, sin4, FE.ADD, 0.25, FE.POW, FE.DIV, inset, FE.SUB)
        offset_x = rc.float_expression(
            polar_radius, cos_ang, FE.MUL, center_x, FE.ADD)
        offset_y = rc.float_expression(
            polar_radius, sin_ang, FE.MUL, center_y, FE.ADD)
        hr = rc.float_expression(
            second, 15, FE.DIV, 3, FE.ADD, 4, FE.MOD,
            1, FE.ADD, 3, FE.MUL, FE.ROUND)
        tid = rc.create_text_from_float(hr, 2, 0, 0)
        rc.draw_text_anchored(tid, offset_x, offset_y, 0, 0, 0)

    rc.loop(id_from_nan(second), 0.0, 15, 60, loop3)


def _draw_clock_cd2(rc, center_x, center_y):
    """Draw clock hands with second hand (ClockDemo2.drawClock)."""
    second_angle = rc.float_expression(
        CONTINUOUS_SEC, 60.0, FE.MOD, 6.0, FE.MUL)
    min_angle = rc.float_expression(TIME_IN_MIN, 6.0, FE.MUL)
    hr_angle = rc.float_expression(TIME_IN_HR, 30.0, FE.MUL)
    hour_hand_length = rc.float_expression(
        center_y, center_x, center_y, FE.MIN, 0.3, FE.MUL, FE.SUB)
    min_hand_length = rc.float_expression(
        center_y, center_x, center_y, FE.MIN, 0.7, FE.MUL, FE.SUB)
    hour_width = 12.0
    hand_width = 6.0

    # Hour hand
    rc.save()
    rc.rc_paint.set_color(GRAY).set_stroke_width(hour_width) \
        .set_stroke_cap(CAP_ROUND).commit()
    rc.draw_circle(center_x, center_y, hour_width)
    rc.rotate(hr_angle, center_x, center_y)
    rc.draw_line(center_x, center_y, center_x, hour_hand_length)
    rc.restore()

    # Minute hand
    rc.save()
    rc.rc_paint.set_color(WHITE).set_stroke_width(hand_width).commit()
    rc.draw_circle(center_x, center_y, hand_width)
    rc.rotate(min_angle, center_x, center_y)
    rc.draw_line(center_x, center_y, center_x, min_hand_length)
    rc.restore()

    # Center dot
    rc.rc_paint.set_color(WHITE).commit()
    rc.draw_circle(center_x, center_y, 2)

    # Second hand
    rc.save()
    rc.rotate(second_angle, center_x, center_y)
    rc.rc_paint.set_color(RED).set_stroke_width(4.0).commit()
    rc.draw_line(center_x, center_y, center_x, min_hand_length)
    rc.restore()


def clock_demo2_jclock2():
    """Port of ClockDemo2.java clock2().

    Complex clock with superellipse clip path, radial gradient,
    timezone displays with sunrise/sunset, touch scrolling, and
    animated tick marks.
    """
    rc = RemoteComposeWriter(500, 500, "sd", api_level=6, profiles=0)

    utc_off = rc.add_float_array(_get_offsets())
    lat = rc.add_float_array(_get_latitudes())
    lon = rc.add_float_array(_get_longitudes())

    def content():
        rc.start_box(RecordingModifier().fill_max_size(),
                      Rc.Layout.START, Rc.Layout.TOP)
        rc.start_canvas(RecordingModifier().fill_max_size())

        w = rc.add_component_width_value()
        h = rc.add_component_height_value()
        cx = rc.float_expression(w, 2, FE.DIV)
        cy = rc.float_expression(h, 2, FE.DIV)
        rad = rc.float_expression(w, h, FE.MIN)
        clip_rad1 = rc.float_expression(rad, 2.0, FE.DIV)
        rad1 = rc.float_expression(rad, 2, FE.DIV)
        rad2 = rc.float_expression(rad, 5, FE.DIV)

        pat2 = _gen_path_cd2(rc, cx, cy, clip_rad1, rad2)

        rc.add_clip_path(pat2)
        rc.save()
        a2 = rc.float_expression(CONTINUOUS_SEC, 360.0, FE.MOD)

        rc.rc_paint.set_radial_gradient(
            cx, cy, rad,
            [0xFF555500, 0xFF999999],
            tile_mode=0).commit()

        rc.draw_circle(cx, cy, rad)
        rc.rc_paint.set_shader(0).set_color(BLACK) \
            .set_style(STYLE_STROKE).set_stroke_width(62.0) \
            .set_stroke_cap(CAP_ROUND).commit()

        rc.rc_paint.set_style(STYLE_FILL).commit()
        rc.restore()
        rc.rc_paint.set_shader(0).commit()

        _draw_time_zones(rc, pat2, w, h, cx, cy,
                         _get_names(), utc_off, lat, lon)
        _draw_ticks_cd2(rc, cx, cy, rad1, rad2, a2)
        _draw_clock_cd2(rc, cx, cy)

        rc.end_canvas()
        rc.end_box()

    rc.root(content)
    return _make_result(rc)


# ============================================================================
# Main
# ============================================================================
if __name__ == '__main__':
    outdir = os.path.join(os.path.dirname(__file__), '..', 'output')
    os.makedirs(outdir, exist_ok=True)

    demos = [
        ('clock', basic_clock),
        ('digital_clock1', digital_clock1),
        ('clock_demo2_jclock2', clock_demo2_jclock2),
    ]

    for name, func in demos:
        result = func()
        path = os.path.join(outdir, f'{name}.rc')
        result.save(path)
        data = result.encode()
        print(f'{name}: {len(data)} bytes -> {path}')

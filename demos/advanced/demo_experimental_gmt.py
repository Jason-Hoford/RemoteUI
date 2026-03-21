"""Port of the experimental_gmt reference binary.

Target reference:
  integration-tests/player-view-demos/src/main/res/raw/experimental_gmt.rc (6709 bytes)

Uses V6 legacy header format with major=1, minor=0, patch=0.
Layout: root > box(fill_max_size, START, START) > canvas(fill_max_size)

Reverse-engineered from reference binary since the Kotlin source gmt() in SimpleDocs.kt
produces different output than the reference file (different hand lengths, touch expression,
icon scaling, bezel text positions, etc.).
"""
import sys
import os
import math
import struct

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RemoteComposeWriter, Rc, as_nan
from rcreate.modifiers import RecordingModifier

# Float expression operators
FE = Rc.FloatExpression
DIV = FE.DIV
MUL = FE.MUL
SUB = FE.SUB
ADD = FE.ADD
MOD = FE.MOD
MIN = FE.MIN
ATAN2 = FE.ATAN2

# Paint style/cap constants
STYLE_FILL = Rc.Paint.STYLE_FILL
STYLE_STROKE = Rc.Paint.STYLE_STROKE
STYLE_FILL_AND_STROKE = Rc.Paint.STYLE_FILL_AND_STROKE
CAP_ROUND = Rc.Paint.CAP_ROUND

# Time variables
TIME_IN_SEC = Rc.Time.TIME_IN_SEC
TIME_IN_MIN = Rc.Time.TIME_IN_MIN
TIME_IN_HR = Rc.Time.TIME_IN_HR
WEEK_DAY = Rc.Time.WEEK_DAY
DAY_OF_MONTH = Rc.Time.DAY_OF_MONTH
OFFSET_TO_UTC = Rc.Time.OFFSET_TO_UTC

# Touch variables
POSITION_X = Rc.Touch.POSITION_X
POSITION_Y = Rc.Touch.POSITION_Y


def _f32(v):
    """Round to nearest IEEE 754 32-bit float."""
    return struct.unpack('>f', struct.pack('>f', v))[0]


def _parse_svg_to_android_format(path_data):
    """Parse SVG path string and produce float array matching Android PathIterator format."""
    import re
    result = []
    cur_x, cur_y = 0.0, 0.0
    last_cp2_x, last_cp2_y = 0.0, 0.0

    commands = re.split(r'(?=[MmZzLlHhVvCcSsQqTtAa])', path_data)
    for command in commands:
        command = command.strip()
        if not command:
            continue
        cmd = command[0]
        values_str = command[1:].strip()
        if values_str:
            values = re.split(r'[,\s]+', values_str)
            values = [v for v in values if v]
        else:
            values = []

        if cmd == 'M':
            x, y = _f32(float(values[0])), _f32(float(values[1]))
            result.append(as_nan(10))  # MOVE
            result.append(x)
            result.append(y)
            cur_x, cur_y = x, y
            last_cp2_x, last_cp2_y = cur_x, cur_y
        elif cmd == 'L':
            for j in range(0, len(values), 2):
                x, y = _f32(float(values[j])), _f32(float(values[j + 1]))
                result.append(as_nan(11))  # LINE
                result.append(cur_x)
                result.append(cur_y)
                result.append(x)
                result.append(y)
                cur_x, cur_y = x, y
                last_cp2_x, last_cp2_y = cur_x, cur_y
        elif cmd == 'H':
            for v in values:
                x = _f32(float(v))
                result.append(as_nan(11))  # LINE
                result.append(cur_x)
                result.append(cur_y)
                result.append(x)
                result.append(cur_y)
                cur_x = x
                last_cp2_x, last_cp2_y = cur_x, cur_y
        elif cmd == 'C':
            for j in range(0, len(values), 6):
                x1 = _f32(float(values[j]))
                y1 = _f32(float(values[j + 1]))
                x2 = _f32(float(values[j + 2]))
                y2 = _f32(float(values[j + 3]))
                x3 = _f32(float(values[j + 4]))
                y3 = _f32(float(values[j + 5]))
                result.append(as_nan(14))  # CUBIC
                result.append(cur_x)
                result.append(cur_y)
                result.append(x1)
                result.append(y1)
                result.append(x2)
                result.append(y2)
                result.append(x3)
                result.append(y3)
                cur_x, cur_y = x3, y3
                last_cp2_x, last_cp2_y = x2, y2
        elif cmd == 'S':
            for j in range(0, len(values), 4):
                x1 = _f32(2 * cur_x - last_cp2_x)
                y1 = _f32(2 * cur_y - last_cp2_y)
                x2 = _f32(float(values[j]))
                y2 = _f32(float(values[j + 1]))
                x3 = _f32(float(values[j + 2]))
                y3 = _f32(float(values[j + 3]))
                result.append(as_nan(14))  # CUBIC
                result.append(cur_x)
                result.append(cur_y)
                result.append(x1)
                result.append(y1)
                result.append(x2)
                result.append(y2)
                result.append(x3)
                result.append(y3)
                cur_x, cur_y = x3, y3
                last_cp2_x, last_cp2_y = x2, y2
        elif cmd == 'Z':
            result.append(as_nan(15))  # CLOSE
            last_cp2_x, last_cp2_y = cur_x, cur_y

    return result


def _build_path_floats(commands):
    """Build a path float array matching Android PathIterator format.

    When coordinates use NaN-encoded expressions (runtime-computed values),
    LINE start coordinates are written as 0.0 since the actual position
    isn't known at compile time. This matches the Java PathIterator behavior.
    """
    import math
    result = []
    cur_x = 0.0
    cur_y = 0.0
    for cmd in commands:
        if cmd[0] == 'M':
            x, y = cmd[1], cmd[2]
            result.append(as_nan(10))  # MOVE
            result.append(x)
            result.append(y)
            cur_x, cur_y = x, y
        elif cmd[0] == 'L':
            x, y = cmd[1], cmd[2]
            result.append(as_nan(11))  # LINE
            # If previous position was a NaN expression, write 0.0 for start coords
            sx = 0.0 if (isinstance(cur_x, float) and cur_x != cur_x) else cur_x
            sy = 0.0 if (isinstance(cur_y, float) and cur_y != cur_y) else cur_y
            result.append(sx)
            result.append(sy)
            result.append(x)
            result.append(y)
            cur_x, cur_y = x, y
        elif cmd[0] == 'Z':
            result.append(as_nan(15))  # CLOSE
    return result


def demo_experimental_gmt():
    """Reproduce the experimental_gmt.rc reference binary exactly."""
    rc = RemoteComposeWriter(800, 800, "Clock", api_level=6)

    # Named color theme names
    bottom_bezel = "android.colorControlNormal"
    top_bezel = "android.colorAccent"
    text_color = "android.textColor"
    background_color = "android.colorPrimary"
    gmt_hand_color = "android.colorError"
    tick_color = "android.colorButtonNormal"

    # Animation spec for 4 Hz tick movement
    anim_type = Rc.Animate.SPLINE_CUSTOM
    spec = [
        0.0, 0.0, 0.0,
        0.25, 0.25, 0.25, 0.25, 0.25,
        0.5, 0.5, 0.5, 0.5, 0.5,
        0.75, 0.75, 0.75, 0.75, 0.75,
        1.0, 1.0, 1.0,
    ]

    # SVG path for Android robot icon
    path_description = (
        "M17.6,9.48"
        "L19.44,6.3"
        "C19.6,5.99,19.48,5.61,19.18,5.45"
        "C18.89,5.30,18.53,5.395,18.35,5.67"
        "L16.47,8.91"
        "C13.61,7.7,10.39,7.7,7.53,8.91"
        "L5.65,5.67"
        "C5.46,5.38,5.07,5.29,4.78,5.47"
        "C4.5,5.65,4.41,6.01,4.56,6.3"
        "L6.4,9.48"
        "C3.3,11.25,1.28,14.44,1,18"
        "H23"
        "C22.72,14.44,20.7,11.25,17.6,9.48Z"
        "M7,15.25"
        "C6.31,15.25,5.75,14.69,5.75,14"
        "C5.75,13.31,6.31,12.75,7,12.75"
        "S8.25,13.31,8.25,14"
        "C8.25,14.69,7.69,15.25,7,15.25Z"
        "M17,15.25"
        "C16.31,15.25,15.75,14.69,15.75,14"
        "C15.75,13.31,16.31,12.75,17,12.75"
        "S18.25,13.31,18.25,14"
        "C18.25,14.69,17.69,15.25,17,15.25Z"
    )

    def content():
        rc.start_box(RecordingModifier().fill_max_size(),
                      Rc.Layout.START, Rc.Layout.START)
        rc.start_canvas(RecordingModifier().fill_max_size())

        # --- Component width/height (id43, id44) ---
        w_val = rc.add_component_width_value()  # id43
        h_val = rc.add_component_height_value()  # id44

        # --- Float expressions: centerX(id45), centerY(id46), rad(id47) ---
        centerX = rc.float_expression(w_val, 2.0, DIV)      # id45
        centerY = rc.float_expression(h_val, 2.0, DIV)      # id46
        rad = rc.float_expression(centerX, centerY, MIN)     # id47

        # --- Named colors (id48-id53) ---
        bezel2Id = rc.add_named_color(bottom_bezel, 0xFF5E1A1A)    # id48
        bezel1Id = rc.add_named_color(top_bezel, 0xFF1A1A5E)       # id49
        textColorId = rc.add_named_color(text_color, 0xFFAAAAAA)   # id50
        backgroundColorId = rc.add_named_color(background_color, 0xFF323288)  # id51
        gmtColorId = rc.add_named_color(gmt_hand_color, 0xFFFF0000)  # id52
        tickColorId = rc.add_named_color(tick_color, 0xFF7A7B7B)   # id53

        # --- Angle expressions ---
        # secondAngle (id54): TIME_IN_SEC % 60 * 6, animated
        secondAngle = rc.float_expression(
            rc.exp(TIME_IN_SEC, 60.0, MOD, 6.0, MUL),
            rc.anim(1.0, anim_type, spec, float('nan'), 360.0),
        )  # id54

        # minAngle (id55)
        minAngle = rc.float_expression(TIME_IN_MIN, 6.0, MUL)  # id55

        # hrAngle (id56)
        hrAngle = rc.float_expression(TIME_IN_HR, 30.0, MUL)  # id56

        # gmtAngle (id57)
        gmtAngle = rc.float_expression(
            TIME_IN_HR,
            OFFSET_TO_UTC,
            3600.0,
            DIV,
            SUB,
            TIME_IN_MIN,
            60.0,
            MOD,
            60.0,
            DIV,
            ADD,
            15.0,
            MUL,
        )  # id57

        # --- TOUCH_EXPRESSION for bezel rotation (id58) ---
        # Expression: (POSITION_X - centerX, POSITION_Y - centerY) -> ATAN2 * (-180/3.141f) + 360 % 360
        atan_factor = _f32(-180.0 / _f32(3.141))
        bezelAngle = rc.add_touch(
            0.0,           # def_value
            float('nan'),  # min_val (NaN = no minimum limit)
            360.0,         # max_val
            Rc.Touch.STOP_NOTCHES_EVEN,  # touch_mode=3
            0.0,           # velocity_id (0 = no velocity tracking)
            4,             # touch_effects
            [float(24.0)],      # touch_spec
            [0.0, 4.0, 2.0, 4.0],  # easing_spec
            POSITION_X, centerX, SUB,
            POSITION_Y, centerY, SUB,
            ATAN2,
            atan_factor,
            MUL,
            360.0,
            ADD,
            360.0,
            MOD,
        )  # id58

        # --- Additional expressions for bezel geometry ---
        rect1 = rc.float_expression(centerX, 10.0, ADD)  # id59
        rect2 = rc.float_expression(centerX, 10.0, SUB)  # id60

        # ============== BEZEL TEXT AND CIRCLES SECTION ==============
        # SAVE for outer bezel section
        rc.save()  # 863

        # Paint: TYPEFACE(w=700,ft=1=SANS_SERIF), TEXT_SIZE=80, COLOR_ID=id53
        rc.rc_paint.set_typeface(1, 700, False).set_text_size(80.0).set_color_id(tickColorId).commit()

        # SAVE + ROTATE by bezelAngle (touch expression)
        rc.save()  # 893
        rc.rotate(bezelAngle, centerX, centerY)

        # Draw bezel 1 (top half)
        rc.rc_paint.set_color_id(bezel1Id).commit()
        rc.draw_circle(centerX, centerY, rad)

        # Draw bezel 2 (bottom half via clip)
        rc.save()
        rc.rc_paint.set_color_id(bezel2Id).commit()
        rc.clip_rect(0.0, centerY, w_val, h_val)
        rc.draw_circle(centerX, centerY, rad)
        rc.restore()

        # --- Bezel text and circles expressions ---
        bezelTextY = rc.float_expression(centerY, rad, 0.9, MUL, SUB)   # id61
        bezelR = rc.float_expression(rad, 0.1, MUL)                       # id62

        # Paint for tick mark stroke on bezel
        rc.rc_paint.set_color_id(tickColorId).set_stroke_width(2.0).commit()

        bezelTriX1 = rc.float_expression(centerX, bezelR, ADD)   # id63
        bezelTriX2 = rc.float_expression(centerX, bezelR, SUB)   # id64
        bezelTriY1 = rc.float_expression(bezelTextY, bezelR, 0.5, MUL, SUB)  # id65
        bezelTriY2 = rc.float_expression(bezelTextY, bezelR, 0.5, MUL, ADD)  # id66

        # Triangle path on bezel
        tri_path_data = _build_path_floats([
            ('M', bezelTriX1, bezelTriY1),
            ('L', bezelTriX2, bezelTriY1),
            ('L', centerX, bezelTriY2),
            ('Z',),
        ])
        tri_path_id = rc.add_path_data(tri_path_data)  # id67
        rc.draw_path(tri_path_id)

        # SAVE for bezel numbers
        rc.save()

        # Paint: TEXT_SIZE=id62 (proportional to rad)
        rc.rc_paint.set_text_size(bezelR).commit()

        # Bezel numbers: 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22 (11 numbers, 12 rotations)
        # The 12th position (24 = 0 o'clock) has no text (triangle is there)
        for i in range(12):
            rc.rotate(30.0, centerX, centerY)
            if i < 11:
                text = str((i + 1) * 2)
                tid = rc.add_text(text)
                rc.draw_text_anchored(tid, centerX, bezelTextY, 0.0, 0.0, 0)

        rc.restore()  # end bezel numbers

        # Bezel circles: rotate 15 first, then 12 circles at 30 degree intervals
        rc.rotate(15.0, centerX, centerY)
        for i in range(12):
            rc.rotate(30.0, centerX, centerY)
            rc.draw_circle(centerX, bezelTextY, 8.0)

        rc.restore()  # end bezel rotation (by bezelAngle)

        # ============== MAIN WATCH FACE ==============
        # Light gray stroke circle (outer ring)
        rc.rc_paint.set_color(0xFFCCCCCC).set_style(STYLE_STROKE).set_stroke_width(8.0).commit()
        rc.draw_circle(centerX, centerY, rad)

        # Inner circle (background)
        innerRad = rc.float_expression(rad, 0.8, MUL)   # id79
        rc.draw_circle(centerX, centerY, innerRad)
        rc.rc_paint.set_color_id(backgroundColorId).set_style(STYLE_FILL).commit()
        rc.draw_circle(centerX, centerY, innerRad)

        # ============== TICK MARKS ==============
        rc.rc_paint.set_color_id(tickColorId).set_stroke_width(2.0).commit()

        tickOuter = rc.float_expression(centerY, rad, 0.8, MUL, SUB)   # id80
        tickInner = rc.float_expression(centerY, rad, 0.75, MUL, SUB)  # id81

        rc.save()
        for i in range(60):
            rc.rotate(6.0, centerX, centerY)
            rc.draw_line(centerX, tickOuter, centerX, tickInner)
        rc.restore()

        # ============== HOUR MARKER SHAPES ==============
        # Expressions for marker rectangles/triangles
        markerTop = rc.float_expression(centerY, rad, 0.72, MUL, SUB)   # id82
        markerBot = rc.float_expression(centerY, rad, 0.6, MUL, SUB)    # id83

        rc.save()
        markerX1 = rc.float_expression(centerX, bezelR, ADD)  # id84
        markerX2 = rc.float_expression(centerX, bezelR, SUB)  # id85

        # 6 rotations of 30 each = 180 degrees, then RECT at 6h position
        for i in range(6):
            rc.rotate(30.0, centerX, centerY)
        rc.draw_rect(rect1, markerTop, rect2, markerBot)

        # 3 more rotations = 270, then RECT at 9h position
        for i in range(3):
            rc.rotate(30.0, centerX, centerY)
        rc.draw_rect(rect1, markerTop, rect2, markerBot)

        # 3 more rotations = 360, then triangle at 12h position
        for i in range(3):
            rc.rotate(30.0, centerX, centerY)
        tri2_path_data = _build_path_floats([
            ('M', markerX1, markerTop),
            ('L', markerX2, markerTop),
            ('L', centerX, markerBot),
            ('Z',),
        ])
        tri2_path_id = rc.add_path_data(tri2_path_data)  # id86
        rc.draw_path(tri2_path_id)
        rc.restore()

        # ============== DATE COMPLICATION ==============
        dateLeft = rc.float_expression(centerX, rad, 0.72, MUL, ADD)     # id87
        dateTop = rc.float_expression(centerY, bezelR, 1.0, MUL, SUB)   # id88
        dateRight = rc.float_expression(centerX, rad, 0.6, MUL, ADD)    # id89
        dateBottom = rc.float_expression(centerY, bezelR, 1.0, MUL, ADD) # id90
        dateCX = rc.float_expression(dateRight, dateLeft, ADD, 2.0, DIV)  # id91

        rc.draw_rect(dateRight, dateTop, dateLeft, dateBottom)

        # Paint for date text
        rc.rc_paint.set_typeface(3, 700, False).set_text_size(bezelR).set_color_id(backgroundColorId).commit()

        date_text_id = rc.create_text_from_float(DAY_OF_MONTH, 2, 0, 0)  # id92
        rc.draw_text_anchored(date_text_id, dateCX, centerY, 0.0, 0.0, 0)

        # ============== DAY COMPLICATION ==============
        dayLeft = rc.float_expression(dateRight, bezelR, 4.0, MUL, SUB)  # id93
        dayRight = rc.float_expression(dateRight, 2.0, SUB)              # id94
        dayCX = rc.float_expression(dayLeft, dayRight, ADD, 0.5, MUL)    # id95

        rc.save()
        rc.rc_paint.set_color_id(tickColorId).commit()
        rc.clip_rect(dayLeft, dateTop, dayRight, dateBottom)

        dayCircleR = rc.float_expression(dayRight, centerX, SUB, 5.0, ADD)  # id96
        rc.draw_circle(centerX, centerY, dayCircleR)

        # Paint for day text
        rc.rc_paint.set_color_id(backgroundColorId).set_text_size(bezelR).commit()

        angle = _f32(360.0 / 7.0)
        dayAngle = rc.float_expression(
            rc.exp(1.0, WEEK_DAY, SUB, angle, MUL),
            rc.anim(0.5, Rc.Animate.CUBIC_OVERSHOOT),
        )  # id97
        rc.rotate(dayAngle, centerX, centerY)

        days = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
        for day in days:
            tid = rc.add_text(day)
            rc.draw_text_anchored(tid, dayCX, centerY, 0.0, 0.0, 0)
            rc.rotate(angle, centerX, centerY)

        rc.restore()  # end day complication

        # ============== ICON (Android robot) ==============
        rc.save()
        iconOffY = rc.float_expression(centerY, rad, 2.0, DIV, SUB)  # id105
        rc.translate(centerX, iconOffY)
        iconScale = rc.float_expression(rad, 100.0, DIV)  # id106
        rc.scale(iconScale, iconScale)
        rc.translate(-12.0, 0.0)

        # Paint for icon
        rc.rc_paint.set_color(0xFFA4C639).set_stroke_cap(CAP_ROUND).set_style(STYLE_FILL).commit()

        icon_path_data = _parse_svg_to_android_format(path_description)
        icon_path_id = rc.add_path_data(icon_path_data)  # id107
        rc.draw_path(icon_path_id)
        rc.restore()  # end icon

        # ============== GMT HAND ==============
        rc.save()
        rc.rc_paint.set_color_id(gmtColorId) \
            .set_stroke_width(5.0) \
            .set_stroke_cap(CAP_ROUND) \
            .set_style(STYLE_FILL_AND_STROKE) \
            .commit()
        rc.rotate(gmtAngle, centerX, centerY)

        # GMT hand: line from center to markerBot, then arrow path
        rc.draw_line(centerX, centerY, centerX, markerBot)

        gmtArrowTop = rc.float_expression(markerBot, rad, 0.1, MUL, SUB)    # id108
        gmtArrowLeft = rc.float_expression(centerX, rad, 0.1, MUL, SUB)     # id109
        gmtArrowRight = rc.float_expression(centerX, rad, 0.1, MUL, ADD)    # id110

        gmt_path_data = _build_path_floats([
            ('M', centerX, centerY),
            ('L', centerX, markerBot),
            ('L', gmtArrowLeft, markerBot),
            ('L', centerX, gmtArrowTop),
            ('L', gmtArrowRight, markerBot),
            ('L', centerX, markerBot),
            ('L', centerX, centerY),
            ('Z',),
        ])
        gmt_path_id = rc.add_path_data(gmt_path_data)  # id111
        rc.draw_path(gmt_path_id)
        rc.restore()  # end GMT hand

        # ============== HOUR HAND ==============
        hourHandEnd = rc.float_expression(centerY, rad, 0.3, MUL, SUB)  # id112
        rc.rc_paint.set_color_id(textColorId) \
            .set_stroke_width(20.0) \
            .set_stroke_cap(CAP_ROUND) \
            .commit()
        rc.save()
        rc.rotate(hrAngle, centerX, centerY)
        rc.draw_line(centerX, centerY, centerX, hourHandEnd)
        rc.restore()

        # ============== MINUTE HAND ==============
        rc.save()
        minHandEnd = rc.float_expression(centerY, rad, 0.6, MUL, SUB)   # id113
        rc.rotate(minAngle, centerX, centerY)
        rc.draw_line(centerX, centerY, centerX, minHandEnd)
        rc.restore()

        # ============== SECOND HAND ==============
        rc.save()
        rc.rotate(secondAngle, centerX, centerY)
        rc.rc_paint.set_color_id(textColorId) \
            .set_stroke_width(4.0) \
            .set_stroke_cap(CAP_ROUND) \
            .commit()
        secHandEnd = rc.float_expression(centerY, rad, 0.6, MUL, SUB)   # id114
        secDotY = rc.float_expression(centerY, rad, 0.5, MUL, SUB)      # id115
        secDotR = rc.float_expression(rad, 0.02, MUL)                   # id116
        rc.draw_line(centerX, centerY, centerX, secHandEnd)
        rc.draw_circle(centerX, secDotY, secDotR)
        rc.restore()

        # ============== CENTER DOT ==============
        rc.draw_circle(centerX, centerY, 20.0)
        rc.rc_paint.set_color(0xFF000000).commit()
        rc.draw_circle(centerX, centerY, secDotR)

        rc.end_canvas()
        rc.end_box()

    rc.root(content)

    class Result:
        def encode(self):
            return rc.encode_to_byte_array()
        def save(self, path):
            with open(path, 'wb') as f:
                f.write(self.encode())
    return Result()


if __name__ == '__main__':
    result = demo_experimental_gmt()
    data = result.encode()
    outdir = os.path.join(os.path.dirname(__file__), '..', 'output')
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, 'experimental_gmt.rc')
    result.save(path)
    print(f"experimental_gmt: {len(data)} bytes -> {path}")

    ref_dir = os.path.join(os.path.dirname(__file__), '..', '..',
                           'integration-tests', 'player-view-demos',
                           'src', 'main', 'res', 'raw')
    ref_path = os.path.join(ref_dir, 'experimental_gmt.rc')
    if os.path.exists(ref_path):
        ref_data = open(ref_path, 'rb').read()
        if data == ref_data:
            print("MATCH: byte-identical to reference")
        else:
            print(f"DIFF: gen={len(data)} ref={len(ref_data)}")
            for i in range(min(len(data), len(ref_data))):
                if data[i] != ref_data[i]:
                    print(f"  First diff at byte {i}: gen=0x{data[i]:02x} ref=0x{ref_data[i]:02x}")
                    start = max(0, i - 4)
                    end = min(len(data), i + 8)
                    print(f"  gen[{start}:{end}]: {' '.join(f'{data[j]:02x}' for j in range(start, end))}")
                    end2 = min(len(ref_data), i + 8)
                    print(f"  ref[{start}:{end2}]: {' '.join(f'{ref_data[j]:02x}' for j in range(start, end2))}")
                    break
    else:
        print("Reference file not found")

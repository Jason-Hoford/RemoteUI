"""ClockDemo1 ports. Port of ClockDemo1.java clock1()/fancyClock2().

Generates: clock_demo1_clock1.rc, clock_demo2_jancy_clock2.rc
"""
import sys
import os
import math

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RemoteComposeWriter, Rc, as_nan
from rcreate.modifiers import RecordingModifier
from rcreate.types.nan_utils import id_from_nan

FE = Rc.FloatExpression
CONTINUOUS_SEC = Rc.Time.CONTINUOUS_SEC
TIME_IN_MIN = Rc.Time.TIME_IN_MIN
TIME_IN_HR = Rc.Time.TIME_IN_HR
FONT_SIZE = Rc.System.FONT_SIZE

STYLE_FILL = Rc.Paint.STYLE_FILL
STYLE_STROKE = Rc.Paint.STYLE_STROKE
CAP_ROUND = Rc.Paint.CAP_ROUND

BLACK = 0xFF000000
GRAY = 0xFF888888
LTGRAY = 0xFFCCCCCC
WHITE = 0xFFFFFFFF


def _make_result(rc):
    class Result:
        def encode(self): return rc.encode_to_byte_array()
        def save(self, path):
            with open(path, 'wb') as f: f.write(self.encode())
    return Result()


def _gen_path(rc, center_x, center_y, rad1, rad2):
    """Generate star-shaped clock face — port of genPath()."""
    second = rc.create_float_id()
    sqrt2 = math.sqrt(2)
    # n = 1 / (0.5 - Log2(SQRT2 + (rad2/rad1) * (1 - SQRT2)))
    n = rc.float_expression(1, 0.5, sqrt2, rad2, rad1, FE.DIV, 1, sqrt2, FE.SUB,
                            FE.MUL, FE.ADD, FE.LN, 2, FE.LN, FE.DIV, FE.SUB, FE.DIV)
    n1 = rc.float_expression(1, n, FE.DIV)
    pi = math.pi
    pid = rc.path_create(center_x, rc.float_expression(center_y, rad1, FE.SUB))
    rc.loop(id_from_nan(second), 0.0, 0.2, 60, lambda: _gen_path_loop(
        rc, second, pi, n, n1, rad1, center_x, center_y, pid))
    rc.path_append_close(pid)
    return pid


def _gen_path_loop(rc, second, pi, n, n1, rad1, center_x, center_y, pid):
    ang = rc.float_expression(second, 2 * pi / 60, FE.MUL, pi / 2, FE.SUB)
    cos_ang = rc.float_expression(ang, FE.COS)
    sin_ang = rc.float_expression(ang, FE.SIN)
    cos4 = rc.float_expression(cos_ang, FE.ABS, n, FE.POW)
    sin4 = rc.float_expression(sin_ang, FE.ABS, n, FE.POW)
    polar_radius = rc.float_expression(rad1, cos4, sin4, FE.ADD, FE.ABS, n1, FE.POW, FE.DIV)
    offset_x = rc.float_expression(polar_radius, cos_ang, FE.MUL, center_x, FE.ADD)
    offset_y = rc.float_expression(polar_radius, sin_ang, FE.MUL, center_y, FE.ADD)
    rc.path_append_line_to(pid, offset_x, offset_y)


def _draw_ticks(rc, center_x, center_y, rad1, rad2, sec):
    """Draw tick marks and hour numbers — port of drawTicks()."""
    second = rc.create_float_id()
    font_size = rc.float_expression(FONT_SIZE, 2, FE.MUL)
    rc.rc_paint.set_color(LTGRAY).set_text_size(font_size).commit()

    sqrt2 = math.sqrt(2)
    n = rc.float_expression(1, 0.5, sqrt2, rad2, rad1, FE.DIV, 1, sqrt2, FE.SUB,
                            FE.MUL, FE.ADD, FE.LN, 2, FE.LN, FE.DIV, FE.SUB, FE.DIV)
    n1 = rc.float_expression(1, n, FE.DIV)
    pi = math.pi

    # Loop 1: second ticks (step=1, 60 ticks)
    rc.loop(id_from_nan(second), 0.0, 1, 60, lambda: _draw_ticks_loop1(
        rc, second, pi, n, n1, rad1, center_x, center_y, sec))

    rc.rc_paint.set_color(WHITE).set_text_size(font_size).commit()

    # Loop 2: 5-minute marks (step=5)
    rc.loop(id_from_nan(second), 0.0, 5, 60, lambda: _draw_ticks_loop2(
        rc, second, pi, n, n1, rad1, center_x, center_y))

    # Loop 3: hour numbers (step=15)
    inset = 70
    rc.loop(id_from_nan(second), 0.0, 15, 60, lambda: _draw_ticks_loop3(
        rc, second, pi, rad1, center_x, center_y, inset))


def _draw_ticks_loop1(rc, second, pi, n, n1, rad1, center_x, center_y, sec):
    ang = rc.float_expression(second, 2 * pi / 60, FE.MUL, pi / 2, FE.SUB)
    ang_deg = rc.float_expression(second, 6, FE.MUL)
    cos_ang = rc.float_expression(ang, FE.COS)
    sin_ang = rc.float_expression(ang, FE.SIN)
    cos4 = rc.float_expression(cos_ang, FE.ABS, n, FE.POW)
    sin4 = rc.float_expression(sin_ang, FE.ABS, n, FE.POW)
    polar_radius = rc.float_expression(rad1, cos4, sin4, FE.ADD, FE.ABS, n1, FE.POW, FE.DIV)
    offset_x = rc.float_expression(polar_radius, cos_ang, FE.MUL, center_x, FE.ADD)
    offset_y = rc.float_expression(polar_radius, sin_ang, FE.MUL, center_y, FE.ADD)
    scale = rc.float_expression(1, sec, 60, FE.MOD, second, FE.SUB, FE.ABS, FE.SUB,
                                0, FE.MAX, 0.5, FE.ADD)
    rc.save()
    rc.rotate(ang_deg, offset_x, offset_y)
    pos_y = rc.float_expression(offset_y, 6, FE.ADD)
    rc.scale(scale, 2, offset_x, offset_y)
    rc.draw_circle(offset_x, pos_y, 6)
    rc.restore()


def _draw_ticks_loop2(rc, second, pi, n, n1, rad1, center_x, center_y):
    ang = rc.float_expression(second, 2 * pi / 60, FE.MUL, pi / 2, FE.SUB)
    ang_deg = rc.float_expression(second, 6, FE.MUL)
    cos_ang = rc.float_expression(ang, FE.COS)
    sin_ang = rc.float_expression(ang, FE.SIN)
    cos4 = rc.float_expression(cos_ang, FE.ABS, n, FE.POW)
    sin4 = rc.float_expression(sin_ang, FE.ABS, n, FE.POW)
    polar_radius = rc.float_expression(rad1, cos4, sin4, FE.ADD, FE.ABS, n1, FE.POW, FE.DIV)
    offset_x = rc.float_expression(polar_radius, cos_ang, FE.MUL, center_x, FE.ADD)
    offset_y = rc.float_expression(polar_radius, sin_ang, FE.MUL, center_y, FE.ADD)
    rc.save()
    rc.rotate(ang_deg, offset_x, offset_y)
    pos_y = rc.float_expression(offset_y, 6, FE.ADD)
    rc.scale(0.5, 3, offset_x, offset_y)
    rc.draw_circle(offset_x, pos_y, 6)
    rc.restore()


def _draw_ticks_loop3(rc, second, pi, rad1, center_x, center_y, inset):
    ang = rc.float_expression(second, 2 * pi / 60, FE.MUL, pi / 2, FE.SUB)
    cos_ang = rc.float_expression(ang, FE.COS)
    sin_ang = rc.float_expression(ang, FE.SIN)
    cos4 = rc.float_expression(cos_ang, FE.DUP, FE.MUL, FE.DUP, FE.MUL)
    sin4 = rc.float_expression(sin_ang, FE.DUP, FE.MUL, FE.DUP, FE.MUL)
    polar_radius = rc.float_expression(rad1, cos4, sin4, FE.ADD, 0.25, FE.POW, FE.DIV,
                                       inset, FE.SUB)
    offset_x = rc.float_expression(polar_radius, cos_ang, FE.MUL, center_x, FE.ADD)
    offset_y = rc.float_expression(polar_radius, sin_ang, FE.MUL, center_y, FE.ADD)
    hr = rc.float_expression(second, 15, FE.DIV, 3, FE.ADD, 4, FE.MOD, 1, FE.ADD,
                             3, FE.MUL, FE.ROUND)
    tid = rc.create_text_from_float(hr, 2, 0, 0)
    rc.draw_text_anchored(tid, offset_x, offset_y, 0, 0, 0)


def _draw_clock_v1(rc, center_x, center_y):
    """Draw hour and minute hands — port of ClockDemo1.drawClock()."""
    min_angle = rc.float_expression(TIME_IN_MIN, 6.0, FE.MUL)
    hr_angle = rc.float_expression(TIME_IN_HR, 30.0, FE.MUL)
    hour_hand_length = rc.float_expression(center_y, center_x, center_y, FE.MIN,
                                           0.3, FE.MUL, FE.SUB)
    min_hand_length = rc.float_expression(center_y, center_x, center_y, FE.MIN,
                                          0.7, FE.MUL, FE.SUB)
    hour_width = 12.0
    hand_width = 6.0

    # Hour hand
    rc.save()
    rc.rc_paint.set_color(GRAY).set_stroke_width(hour_width).set_stroke_cap(CAP_ROUND).commit()
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


RED = 0xFFFF0000


def _draw_clock_v2(rc, center_x, center_y):
    """Draw hour, minute, and second hands — port of ClockDemo2.drawClock()."""
    second_angle = rc.float_expression(CONTINUOUS_SEC, 60.0, FE.MOD, 6.0, FE.MUL)
    min_angle = rc.float_expression(TIME_IN_MIN, 6.0, FE.MUL)
    hr_angle = rc.float_expression(TIME_IN_HR, 30.0, FE.MUL)
    hour_hand_length = rc.float_expression(center_y, center_x, center_y, FE.MIN,
                                           0.3, FE.MUL, FE.SUB)
    min_hand_length = rc.float_expression(center_y, center_x, center_y, FE.MIN,
                                          0.7, FE.MUL, FE.SUB)
    hour_width = 12.0
    hand_width = 6.0

    # Hour hand
    rc.save()
    rc.rc_paint.set_color(GRAY).set_stroke_width(hour_width).set_stroke_cap(CAP_ROUND).commit()
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


def demo_clock1():
    """Clock1 — port of ClockDemo1.java clock1()."""
    rc = RemoteComposeWriter(500, 500, "sd", api_level=6)

    def content():
        rc.start_box(
            RecordingModifier().fill_max_size(),
            Rc.Layout.START, Rc.Layout.START)
        rc.start_canvas(RecordingModifier().fill_max_size())

        w = rc.add_component_width_value()
        h = rc.add_component_height_value()
        cx = rc.float_expression(w, 2, FE.DIV)
        cy = rc.float_expression(h, 2, FE.DIV)
        rad = rc.float_expression(w, h, FE.MIN)
        clip_rad1 = rc.float_expression(rad, 2.0, FE.DIV)
        rad1 = rc.float_expression(rad, 2, FE.DIV)
        rad2 = rc.float_expression(rad, 5, FE.DIV)

        pat2 = _gen_path(rc, cx, cy, clip_rad1, rad2)

        rc.add_clip_path(pat2)
        rc.save()
        a2 = rc.float_expression(CONTINUOUS_SEC, 360.0, FE.MOD)

        rc.rc_paint.set_radial_gradient(cx, cy, rad,
            [0xFF000000, 0x00000000], tile_mode=0).commit()
        rc.draw_circle(cx, cy, rad)

        rc.rc_paint.set_shader(0).set_color(BLACK).set_style(STYLE_STROKE) \
            .set_stroke_width(62.0).set_stroke_cap(CAP_ROUND).commit()
        rc.draw_path(pat2)

        rc.rc_paint.set_color(GRAY).commit()
        sub = rc.float_expression(CONTINUOUS_SEC, 60.0, FE.MOD, 60.0, FE.DIV)
        rc.draw_tween_path(pat2, pat2, 0, 0, sub)
        rc.rc_paint.set_style(STYLE_FILL).commit()
        rc.restore()
        rc.rc_paint.set_shader(0).commit()

        _draw_ticks(rc, cx, cy, rad1, rad2, a2)
        _draw_clock_v1(rc, cx, cy)

        rc.end_canvas()
        rc.end_box()

    rc.root(content)
    return _make_result(rc)


TOP = 4


def _draw_ticks_cond(rc, center_x, center_y, rad1, rad2):
    """Draw conditional tick marks — port of drawTicksCond()."""
    second = rc.create_float_id()
    rc.rc_paint.set_color(LTGRAY).set_text_size(80.0).commit()

    sqrt2 = math.sqrt(2)
    n = rc.float_expression(1, 0.5, sqrt2, rad2, rad1, FE.DIV, 1, sqrt2, FE.SUB,
                            FE.MUL, FE.ADD, FE.LN, 2, FE.LN, FE.DIV, FE.SUB, FE.DIV)
    n1 = rc.float_expression(1, n, FE.DIV)
    pi = math.pi

    def loop_body():
        ang = rc.float_expression(second, 2 * pi / 60, FE.MUL, pi / 2, FE.SUB)
        ang_deg = rc.float_expression(second, 6, FE.MUL)
        cos_ang = rc.float_expression(ang, FE.COS)
        sin_ang = rc.float_expression(ang, FE.SIN)
        cos4 = rc.float_expression(cos_ang, FE.ABS, n, FE.POW)
        sin4 = rc.float_expression(sin_ang, FE.ABS, n, FE.POW)
        polar_radius = rc.float_expression(rad1, cos4, sin4, FE.ADD, FE.ABS, n1, FE.POW, FE.DIV)
        offset_x = rc.float_expression(polar_radius, cos_ang, FE.MUL, center_x, FE.ADD)
        offset_y = rc.float_expression(polar_radius, sin_ang, FE.MUL, center_y, FE.ADD)
        rc.save()
        rc.rotate(ang_deg, offset_x, offset_y)
        pos_y = rc.float_expression(offset_y, 6, FE.ADD)
        rc.scale(0.5, 2, offset_x, offset_y)
        rc.draw_circle(offset_x, pos_y, 6)

        # Conditional: if (second % 5 == 0) draw bigger white circle
        rc.conditional_operations(Rc.Condition.EQ, 0.0,
                                  rc.float_expression(second, 5, FE.MOD))
        rc.rc_paint.set_color(WHITE).commit()
        rc.draw_circle(offset_x, pos_y, 10)
        rc.rc_paint.set_color(LTGRAY).commit()
        rc.end_conditional_operations()

        rc.restore()

        # Conditional: if (second % 15 == 0) draw hour numbers
        rc.conditional_operations(Rc.Condition.EQ, 0.0,
                                  rc.float_expression(second, 15, FE.MOD))
        inset = 70
        txt_offset_x = rc.float_expression(polar_radius, inset, FE.SUB, cos_ang, FE.MUL,
                                           center_x, FE.ADD)
        txt_offset_y = rc.float_expression(polar_radius, inset, FE.SUB, sin_ang, FE.MUL,
                                           center_y, FE.ADD)
        hr = rc.float_expression(second, 15, FE.DIV, 3, FE.ADD, 4, FE.MOD, 1, FE.ADD,
                                 3, FE.MUL, FE.ROUND)
        tid = rc.create_text_from_float(hr, 2, 0, 0)
        rc.draw_text_anchored(tid, txt_offset_x, txt_offset_y, 0, 0, 0)
        rc.end_conditional_operations()

    rc.loop(id_from_nan(second), 0.0, 1, 60, loop_body)


def demo_fancy_clock2():
    """FancyClock2 — port of ClockDemo2.java fancyClock2()."""
    rc = RemoteComposeWriter(500, 500, "sd", api_level=6)

    def content():
        rc.start_box(
            RecordingModifier().fill_max_size(),
            Rc.Layout.START, TOP)
        rc.start_canvas(RecordingModifier().fill_max_size())

        w = rc.add_component_width_value()
        h = rc.add_component_height_value()
        cx = rc.float_expression(w, 2, FE.DIV)
        cy = rc.float_expression(h, 2, FE.DIV)
        rad = rc.float_expression(w, h, FE.MIN)
        clip_rad1 = rc.float_expression(rad, 2.0, FE.DIV)
        rad1 = rc.float_expression(rad, 2, FE.DIV)
        rad2 = rc.float_expression(rad, 5, FE.DIV)

        pat2 = _gen_path(rc, cx, cy, clip_rad1, rad2)

        rc.add_clip_path(pat2)
        rc.save()
        a2 = rc.float_expression(CONTINUOUS_SEC, 360.0, FE.MOD)
        rc.rotate(a2, cx, cy)

        rc.rc_paint.set_sweep_gradient(cx, cy,
            [0xFF4E6588, 0xFF182947, 0xFF182947, 0xFF182947, 0xFF4E6588,
             0xFF182947, 0xFF4E6588]).commit()

        second_angle = rc.float_expression(CONTINUOUS_SEC, 360.0, FE.MOD, 11.0, FE.MUL)
        rc.draw_circle(cx, cy, rad)

        rc.rotate(second_angle, cx, cy)
        rc.rc_paint.set_sweep_gradient(cx, cy,
            [0x804E6588, 0x80182947, 0x80182947, 0x80182947, 0x804E6588,
             0x80182947, 0x804E6588]).commit()
        rc.draw_circle(cx, cy, rad)

        rc.restore()
        rc.rc_paint.set_shader(0).commit()

        _draw_ticks_cond(rc, cx, cy, rad1, rad2)
        _draw_clock_v2(rc, cx, cy)

        rc.end_canvas()
        rc.end_box()

    rc.root(content)
    return _make_result(rc)


if __name__ == '__main__':
    os.makedirs(os.path.join(os.path.dirname(__file__), '..', 'output'), exist_ok=True)
    for name, func in [('clock_demo1_clock1', demo_clock1),
                       ('clock_demo2_jancy_clock2', demo_fancy_clock2)]:
        result = func()
        path = os.path.join(os.path.dirname(__file__), '..', 'output', f'{name}.rc')
        result.save(path)
        print(f'{name}: {len(result.encode())} bytes -> {path}')

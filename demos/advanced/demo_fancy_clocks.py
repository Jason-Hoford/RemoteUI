"""Fancy clock demos. Port of FancyClocks.java fancyClock1/2/3.

Generates: fancy_clocks_fancy_clock1.rc, fancy_clocks_fancy_clock2.rc,
           fancy_clocks_fancy_clock3.rc
"""
import sys
import os
import math
import struct

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RemoteComposeWriter, Rc, as_nan
from rcreate.modifiers import RecordingModifier
from rcreate.types.nan_utils import id_from_nan

FE = Rc.FloatExpression
CS = Rc.Time.CONTINUOUS_SEC

GRAY = 0xFF888888
LTGRAY = 0xFFCCCCCC
WHITE = 0xFFFFFFFF
RED = 0xFFFF0000

STYLE_STROKE = Rc.Paint.STYLE_STROKE
STYLE_FILL = Rc.Paint.STYLE_FILL
CAP_ROUND = Rc.Paint.CAP_ROUND


def _f32(v):
    return struct.unpack('>f', struct.pack('>f', v))[0]


def _make_result(rc):
    class Result:
        def encode(self): return rc.encode_to_byte_array()
        def save(self, path):
            with open(path, 'wb') as f: f.write(self.encode())
    return Result()


def _gen_path(rc, center_x, center_y, rad1, rad2):
    """Generate superellipse-like path with parametric polar coordinates."""
    second = rc.create_float_id()
    sqrt2 = _f32(math.sqrt(2))
    # n = 1 / (0.5 - log2(sqrt2 + (rad2/rad1) * (1 - sqrt2)))
    n = rc.float_expression(
        1, 0.5, sqrt2, rad2, rad1, FE.DIV, 1, sqrt2, FE.SUB, FE.MUL, FE.ADD,
        FE.LN, 2, FE.LN, FE.DIV, FE.SUB, FE.DIV)
    n1 = rc.float_expression(1, n, FE.DIV)
    pi = _f32(math.pi)
    pid = rc.path_create(center_x, rc.float_expression(center_y, rad1, FE.SUB))
    rc.loop(id_from_nan(second), 0.0, 0.2, 60, lambda: _gen_path_body(
        rc, second, pi, center_x, center_y, rad1, n, n1, pid))
    rc.path_append_close(pid)
    return pid


def _gen_path_body(rc, second, pi, center_x, center_y, rad1, n, n1, pid):
    ang = rc.float_expression(second, _f32(2 * math.pi / 60), FE.MUL, _f32(math.pi / 2), FE.SUB)
    cos_ang = rc.float_expression(ang, FE.COS)
    sin_ang = rc.float_expression(ang, FE.SIN)
    cos4 = rc.float_expression(cos_ang, FE.ABS, n, FE.POW)
    sin4 = rc.float_expression(sin_ang, FE.ABS, n, FE.POW)
    polar_radius = rc.float_expression(rad1, cos4, sin4, FE.ADD, FE.ABS, n1, FE.POW, FE.DIV)
    offset_x = rc.float_expression(polar_radius, cos_ang, FE.MUL, center_x, FE.ADD)
    offset_y = rc.float_expression(polar_radius, sin_ang, FE.MUL, center_y, FE.ADD)
    rc.path_append_line_to(pid, offset_x, offset_y)


def _draw_ticks(rc, center_x, center_y, rad1, rad2):
    """Draw tick marks around the clock face."""
    second = rc.create_float_id()
    font_size = rc.float_expression(Rc.System.FONT_SIZE, 2, FE.MUL)
    rc.rc_paint.set_color(LTGRAY).set_text_size(font_size).commit()
    sqrt2 = _f32(math.sqrt(2))
    n = rc.float_expression(
        1, 0.5, sqrt2, rad2, rad1, FE.DIV, 1, sqrt2, FE.SUB, FE.MUL, FE.ADD,
        FE.LN, 2, FE.LN, FE.DIV, FE.SUB, FE.DIV)
    n1 = rc.float_expression(1, n, FE.DIV)
    pi = _f32(math.pi)

    # Small ticks every 1 unit (60 total)
    rc.loop(id_from_nan(second), 0.0, 1, 60, lambda: _draw_small_tick(
        rc, second, pi, center_x, center_y, rad1, n, n1))

    rc.rc_paint.set_color(WHITE).set_text_size(font_size).commit()

    # Medium ticks every 5 units
    rc.loop(id_from_nan(second), 0.0, 5, 60, lambda: _draw_medium_tick(
        rc, second, pi, center_x, center_y, rad1, n, n1))

    # Hour numbers every 15 units
    inset = 70.0
    rc.loop(id_from_nan(second), 0.0, 15, 60, lambda: _draw_hour_number(
        rc, second, pi, center_x, center_y, rad1, inset))


def _draw_small_tick(rc, second, pi, center_x, center_y, rad1, n, n1):
    ang = rc.float_expression(second, _f32(2 * math.pi / 60), FE.MUL, _f32(math.pi / 2), FE.SUB)
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
    rc.restore()


def _draw_medium_tick(rc, second, pi, center_x, center_y, rad1, n, n1):
    ang = rc.float_expression(second, _f32(2 * math.pi / 60), FE.MUL, _f32(math.pi / 2), FE.SUB)
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


def _draw_hour_number(rc, second, pi, center_x, center_y, rad1, inset):
    ang = rc.float_expression(second, _f32(2 * math.pi / 60), FE.MUL, _f32(math.pi / 2), FE.SUB)
    cos_ang = rc.float_expression(ang, FE.COS)
    sin_ang = rc.float_expression(ang, FE.SIN)
    cos4 = rc.float_expression(cos_ang, FE.DUP, FE.MUL, FE.DUP, FE.MUL)
    sin4 = rc.float_expression(sin_ang, FE.DUP, FE.MUL, FE.DUP, FE.MUL)
    polar_radius = rc.float_expression(rad1, cos4, sin4, FE.ADD, 0.25, FE.POW, FE.DIV, inset, FE.SUB)
    offset_x = rc.float_expression(polar_radius, cos_ang, FE.MUL, center_x, FE.ADD)
    offset_y = rc.float_expression(polar_radius, sin_ang, FE.MUL, center_y, FE.ADD)
    hr = rc.float_expression(second, 15, FE.DIV, 3, FE.ADD, 4, FE.MOD, 1, FE.ADD, 3, FE.MUL, FE.ROUND)
    tid = rc.create_text_from_float(hr, 2, 0, 0)
    rc.draw_text_anchored(tid, offset_x, offset_y, 0, 0, 0)


def _draw_clock(rc, center_x, center_y):
    """Draw clock hands."""
    second_angle = rc.float_expression(CS, 60.0, FE.MOD, 6.0, FE.MUL)
    min_angle = rc.float_expression(Rc.Time.TIME_IN_MIN, 6.0, FE.MUL)
    hr_angle = rc.float_expression(Rc.Time.TIME_IN_HR, 30.0, FE.MUL)
    hour_hand_length = rc.float_expression(center_y, center_x, center_y, FE.MIN, 0.3, FE.MUL, FE.SUB)
    min_hand_length = rc.float_expression(center_y, center_x, center_y, FE.MIN, 0.7, FE.MUL, FE.SUB)
    hour_width = 8.0
    hand_width = 4.0
    rc.save()
    rc.rc_paint.set_color(GRAY).set_stroke_width(hour_width).set_stroke_cap(CAP_ROUND).commit()
    rc.rotate(hr_angle, center_x, center_y)
    rc.draw_line(center_x, center_y, center_x, hour_hand_length)
    rc.restore()

    rc.save()
    rc.rc_paint.set_color(WHITE).set_stroke_width(hand_width).commit()
    rc.rotate(min_angle, center_x, center_y)
    rc.draw_line(center_x, center_y, center_x, min_hand_length)
    rc.restore()

    rc.save()
    rc.rotate(second_angle, center_x, center_y)
    rc.rc_paint.set_color(RED).set_stroke_width(4.0).commit()
    rc.draw_line(center_x, center_y, center_x, min_hand_length)
    rc.restore()


def demo_fancy_clock1():
    """Fancy clock with animated HSL color gradients."""
    rc = RemoteComposeWriter(500, 500, "sd", api_level=6)

    def content():
        rc.start_box(RecordingModifier().fill_max_size(), Rc.Layout.START, Rc.Layout.START)
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
        a2 = rc.float_expression(CS, 360.0, FE.MOD)
        rc.rotate(a2, cx, cy)
        hue = rc.float_expression(CS, 5, FE.DIV, 1, FE.MOD)
        col1 = rc.add_color_expression(255, hue, 0.66, 0.28)
        col2 = rc.add_color_expression(255, hue, 0.43, 0.53)
        col1a = rc.add_color_expression(128, hue, 0.66, 0.28)
        col2a = rc.add_color_expression(128, hue, 0.43, 0.53)
        rc.rc_paint.set_sweep_gradient(cx, cy,
            [col2, col1, col1, col1, col2, col1, col2], mask=127).commit()

        second_angle = rc.float_expression(CS, 360.0, FE.MOD, 11.0, FE.MUL)
        rc.draw_circle(cx, cy, rad)
        rc.rotate(second_angle, cx, cy)
        rc.rc_paint.set_sweep_gradient(cx, cy,
            [col2a, col1a, col1a, col1a, col2a, col1a, col2a], mask=127).commit()

        rc.draw_circle(cx, cy, rad)
        rc.restore()
        rc.rc_paint.set_shader(0).commit()

        _draw_ticks(rc, cx, cy, rad1, rad2)
        _draw_clock(rc, cx, cy)

        rc.end_canvas()
        rc.end_box()

    rc.root(content)
    return _make_result(rc)


def demo_fancy_clock2():
    """Fancy clock with fixed color sweep gradients."""
    rc = RemoteComposeWriter(500, 500, "sd", api_level=6)

    def content():
        rc.start_box(RecordingModifier().fill_max_size(), Rc.Layout.START, Rc.Layout.START)
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
        a2 = rc.float_expression(CS, 360.0, FE.MOD)
        rc.rotate(a2, cx, cy)
        rc.rc_paint.set_sweep_gradient(cx, cy,
            [0xFF4E6588, 0xFF182947, 0xFF182947, 0xFF182947, 0xFF4E6588,
             0xFF182947, 0xFF4E6588]).commit()
        second_angle = rc.float_expression(CS, 360.0, FE.MOD, 11.0, FE.MUL)
        rc.draw_circle(cx, cy, rad)
        rc.rotate(second_angle, cx, cy)
        rc.rc_paint.set_sweep_gradient(cx, cy,
            [0x804E6588, 0x80182947, 0x80182947, 0x80182947, 0x804E6588,
             0x80182947, 0x804E6588]).commit()
        rc.draw_circle(cx, cy, rad)
        rc.restore()
        rc.rc_paint.set_shader(0).commit()

        _draw_ticks_cond(rc, cx, cy, rad1, rad2)
        _draw_clock(rc, cx, cy)

        rc.end_canvas()
        rc.end_box()

    rc.root(content)
    return _make_result(rc)


def _draw_ticks_cond(rc, center_x, center_y, rad1, rad2):
    """Draw ticks with conditional operations for different tick sizes."""
    second = rc.create_float_id()
    rc.rc_paint.set_color(LTGRAY).set_text_size(80.0).commit()
    sqrt2 = _f32(math.sqrt(2))
    n = rc.float_expression(
        1, 0.5, sqrt2, rad2, rad1, FE.DIV, 1, sqrt2, FE.SUB, FE.MUL, FE.ADD,
        FE.LN, 2, FE.LN, FE.DIV, FE.SUB, FE.DIV)
    n1 = rc.float_expression(1, n, FE.DIV)
    pi = _f32(math.pi)

    def loop_body():
        ang = rc.float_expression(second, _f32(2 * math.pi / 60), FE.MUL, _f32(math.pi / 2), FE.SUB)
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

        # Conditional: every 5 units, draw larger white tick
        rc.conditional_operations(0, 0.0,  # TYPE_EQ = 0
            rc.float_expression(second, 5, FE.MOD))
        rc.rc_paint.set_color(WHITE).commit()
        rc.draw_circle(offset_x, pos_y, 10)
        rc.rc_paint.set_color(LTGRAY).commit()
        rc.end_conditional_operations()

        rc.restore()

        # Conditional: every 15 units, draw hour number
        rc.conditional_operations(0, 0.0,
            rc.float_expression(second, 15, FE.MOD))
        inset = 70.0
        txt_offset_x = rc.float_expression(polar_radius, inset, FE.SUB, cos_ang, FE.MUL, center_x, FE.ADD)
        txt_offset_y = rc.float_expression(polar_radius, inset, FE.SUB, sin_ang, FE.MUL, center_y, FE.ADD)
        hr = rc.float_expression(second, 15, FE.DIV, 3, FE.ADD, 4, FE.MOD, 1, FE.ADD, 3, FE.MUL, FE.ROUND)
        tid = rc.create_text_from_float(hr, 2, 0, 0)
        rc.draw_text_anchored(tid, txt_offset_x, txt_offset_y, 0, 0, 0)
        rc.end_conditional_operations()

    rc.loop(id_from_nan(second), 0.0, 1, 60, loop_body)


def demo_fancy_clock3():
    """Fancy clock with theme-based color."""
    rc = RemoteComposeWriter(500, 500, "sd", api_level=6)

    def content():
        rc.start_box(RecordingModifier().fill_max_size(), Rc.Layout.START, Rc.Layout.START)
        rc.start_canvas(RecordingModifier().fill_max_size())
        w = rc.add_component_width_value()
        h = rc.add_component_height_value()
        cx = rc.float_expression(w, 2, FE.DIV)
        cy = rc.float_expression(h, 2, FE.DIV)
        rad = rc.float_expression(w, h, FE.MIN)
        clip_rad1 = rc.float_expression(rad, 2.0, FE.DIV)
        rad1 = rc.float_expression(rad, 2, FE.DIV)
        rad2 = rc.float_expression(rad, 5, FE.DIV)

        base_color = rc.add_color(0xFFFFFF00)
        rc.set_color_name(base_color, "android.colorAccent")
        pat2 = _gen_path(rc, cx, cy, clip_rad1, rad2)
        rc.add_clip_path(pat2)
        hue = rc.get_color_attribute(base_color, Rc.ColorAttribute.HUE)
        sat = rc.get_color_attribute(base_color, Rc.ColorAttribute.SATURATION)

        rc.save()
        a2 = rc.float_expression(CS, 360.0, FE.MOD)
        rc.rotate(a2, cx, cy)
        col1 = rc.add_color_expression(255, hue, sat, 0.28)
        col2 = rc.add_color_expression(255, hue, sat, 0.53)
        col1a = rc.add_color_expression(128, hue, sat, 0.28)
        col2a = rc.add_color_expression(128, hue, sat, 0.53)
        rc.rc_paint.set_sweep_gradient(cx, cy,
            [col2, col1, col1, col1, col2, col1, col2], mask=127).commit()

        second_angle = rc.float_expression(CS, 360.0, FE.MOD, 11.0, FE.MUL)
        rc.draw_circle(cx, cy, rad)
        rc.rotate(second_angle, cx, cy)
        rc.rc_paint.set_sweep_gradient(cx, cy,
            [col2a, col1a, col1a, col1a, col2a, col1a, col2a], mask=127).commit()

        rc.draw_circle(cx, cy, rad)
        rc.restore()
        rc.rc_paint.set_shader(0).commit()

        _draw_ticks(rc, cx, cy, rad1, rad2)
        _draw_clock(rc, cx, cy)

        rc.end_canvas()
        rc.end_box()

    rc.root(content)
    return _make_result(rc)

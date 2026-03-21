"""Metal clock fancyClock2 demo. Port of DemoMetalClock.kt fancyClock2().

Generates fancy_clock2.rc — a squircle-shaped metallic clock with
sweep gradients, conditional ticks, and animated hands.
"""
import sys
import os
import math

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RemoteComposeWriter, Rc, id_from_nan
from rcreate.modifiers import RecordingModifier

FE = Rc.FloatExpression
CS = Rc.Time.CONTINUOUS_SEC


def _make_result(rc):
    class Result:
        def encode(self): return rc.encode_to_byte_array()
        def save(self, path):
            with open(path, 'wb') as f: f.write(self.encode())
    return Result()


def _gen_path(rc, center_x, center_y, rad1, rad2):
    """Generate a squircle path. Port of genPath() in DemoMetalClock.kt."""
    second = rc.create_float_id()

    SQRT2 = 1.4142135623730951
    n = rc.float_expression(
        1.0, 0.5,
        SQRT2, rad2, rad1, FE.DIV, 1.0, SQRT2, FE.SUB, FE.MUL, FE.ADD,
        FE.LN, 2.0, FE.LN, FE.DIV,
        FE.SUB, FE.DIV,
    )
    n_1 = rc.float_expression(1.0, n, FE.DIV)
    pi = math.pi

    pid = rc.path_create(center_x, rc.float_expression(center_y, rad1, FE.SUB))
    rc.loop(
        id_from_nan(second), 0.0, 0.2, 60.0,
        lambda: _gen_path_body(rc, second, pi, center_x, center_y,
                               rad1, n, n_1, pid),
    )
    rc.path_append_close(pid)
    return pid


def _gen_path_body(rc, second, pi, center_x, center_y, rad1, n, n_1, pid):
    ang = rc.float_expression(second, 2 * pi / 60, FE.MUL, pi / 2, FE.SUB)
    cos_ang = rc.float_expression(ang, FE.COS)
    sin_ang = rc.float_expression(ang, FE.SIN)
    cos4 = rc.float_expression(cos_ang, FE.ABS, n, FE.POW)
    sin4 = rc.float_expression(sin_ang, FE.ABS, n, FE.POW)

    polar_radius = rc.float_expression(rad1, cos4, sin4, FE.ADD, FE.ABS, n_1, FE.POW, FE.DIV)
    offset_x = rc.float_expression(polar_radius, cos_ang, FE.MUL, center_x, FE.ADD)
    offset_y = rc.float_expression(polar_radius, sin_ang, FE.MUL, center_y, FE.ADD)
    rc.path_append_line_to(pid, offset_x, offset_y)


def _draw_ticks_cond(rc, center_x, center_y, rad1, rad2):
    """Draw clock ticks with conditional operations. Port of drawTicksCond()."""
    second = rc.create_float_id()
    rc.rc_paint.set_color(0xFFCCCCCC).set_text_size(80.0).commit()  # Color.LTGRAY

    SQRT2 = 1.4142135
    n = rc.float_expression(
        1.0, 0.5,
        SQRT2, rad2, rad1, FE.DIV, 1.0, SQRT2, FE.SUB, FE.MUL, FE.ADD,
        FE.LN, 2.0, FE.LN, FE.DIV,
        FE.SUB, FE.DIV,
    )
    n_1 = rc.float_expression(1.0, n, FE.DIV)
    pi = math.pi

    rc.loop(
        id_from_nan(second), 0.0, 1.0, 60.0,
        lambda: _draw_ticks_body(rc, second, pi, center_x, center_y,
                                  rad1, n, n_1),
    )


def _draw_ticks_body(rc, second, pi, center_x, center_y, rad1, n, n_1):
    ang = rc.float_expression(second, 2 * pi / 60, FE.MUL, pi / 2, FE.SUB)
    ang_deg = rc.float_expression(second, 6.0, FE.MUL)
    cos_ang = rc.float_expression(ang, FE.COS)
    sin_ang = rc.float_expression(ang, FE.SIN)
    cos4 = rc.float_expression(cos_ang, FE.ABS, n, FE.POW)
    sin4 = rc.float_expression(sin_ang, FE.ABS, n, FE.POW)

    polar_radius = rc.float_expression(rad1, cos4, sin4, FE.ADD, FE.ABS, n_1, FE.POW, FE.DIV)
    offset_x = rc.float_expression(polar_radius, cos_ang, FE.MUL, center_x, FE.ADD)
    offset_y = rc.float_expression(polar_radius, sin_ang, FE.MUL, center_y, FE.ADD)
    rc.save()
    rc.rotate(ang_deg, offset_x, offset_y)
    pos_y = rc.float_expression(offset_y, 6.0, FE.ADD)
    rc.scale(0.5, 2.0, offset_x, offset_y)
    rc.draw_circle(offset_x, pos_y, 6.0)

    # Every 5th tick gets a white dot
    rc.conditional_operations(0, 0.0, rc.float_expression(second, 5.0, FE.MOD))
    rc.rc_paint.set_color(0xFFFFFFFF).commit()  # Color.WHITE
    rc.draw_circle(offset_x, pos_y, 10.0)
    rc.rc_paint.set_color(0xFFCCCCCC).commit()  # Color.LTGRAY
    rc.end_conditional_operations()

    rc.restore()

    # Every 15th tick gets a number
    rc.conditional_operations(0, 0.0, rc.float_expression(second, 15.0, FE.MOD))
    inset = 70.0
    txt_offset_x = rc.float_expression(polar_radius, inset, FE.SUB, cos_ang, FE.MUL, center_x, FE.ADD)
    txt_offset_y = rc.float_expression(polar_radius, inset, FE.SUB, sin_ang, FE.MUL, center_y, FE.ADD)
    hr = rc.float_expression(second, 15.0, FE.DIV, 3.0, FE.ADD, 4.0, FE.MOD, 1.0, FE.ADD, 3.0, FE.MUL, FE.ROUND)
    tid = rc.create_text_from_float(hr, 2, 0, 0)
    rc.draw_text_anchored(tid, txt_offset_x, txt_offset_y, 0.0, 0.0, 0)
    rc.end_conditional_operations()


def _draw_clock(rc, center_x, center_y):
    """Draw clock hands. Port of drawClock()."""
    second_angle = rc.float_expression(CS, 60.0, FE.MOD, 6.0, FE.MUL)
    min_angle = rc.float_expression(Rc.Time.TIME_IN_MIN, 6.0, FE.MUL)
    hr_angle = rc.float_expression(Rc.Time.TIME_IN_HR, 30.0, FE.MUL)
    hour_hand_length = rc.float_expression(center_y, center_x, center_y, FE.MIN, 0.3, FE.MUL, FE.SUB)
    min_hand_length = rc.float_expression(center_y, center_x, center_y, FE.MIN, 0.7, FE.MUL, FE.SUB)
    hour_width = 12.0
    hand_width = 6.0

    # Hour hand
    rc.save()
    rc.rc_paint.set_color(0xFF888888).set_stroke_width(hour_width).set_stroke_cap(
        Rc.Paint.CAP_ROUND).commit()  # Color.GRAY
    rc.draw_circle(center_x, center_y, hour_width)
    rc.rotate(hr_angle, center_x, center_y)
    rc.draw_line(center_x, center_y, center_x, hour_hand_length)
    rc.restore()

    # Minute hand
    rc.save()
    rc.rc_paint.set_color(0xFFFFFFFF).set_stroke_width(hand_width).commit()  # Color.WHITE
    rc.draw_circle(center_x, center_y, hand_width)
    rc.rotate(min_angle, center_x, center_y)
    rc.draw_line(center_x, center_y, center_x, min_hand_length)
    rc.restore()

    # Center dot
    rc.rc_paint.set_color(0xFFFFFFFF).commit()  # Color.WHITE
    rc.draw_circle(center_x, center_y, 2.0)

    # Second hand
    rc.save()
    rc.rotate(second_angle, center_x, center_y)
    rc.rc_paint.set_color(0xFFFF0000).set_stroke_width(4.0).commit()  # Color.RED
    rc.draw_line(center_x, center_y, center_x, min_hand_length)
    rc.restore()


def demo_fancy_clock2_metal():
    """Fancy clock 2 — metallic squircle clock with sweep gradients."""
    rc = RemoteComposeWriter(500, 500, "sd", api_level=6)

    def content():
        rc.start_box(RecordingModifier().fill_max_size(),
                     Rc.Layout.START, Rc.Layout.START)
        rc.start_canvas(RecordingModifier().fill_max_size())

        w = rc.add_component_width_value()
        h = rc.add_component_height_value()
        cx = rc.float_expression(w, 2.0, FE.DIV)
        cy = rc.float_expression(h, 2.0, FE.DIV)
        rad = rc.float_expression(w, h, FE.MIN)
        clip_rad1 = rc.float_expression(rad, 2.0, FE.DIV)
        rad1 = rc.float_expression(rad, 2.0, FE.DIV)
        rad2 = rc.float_expression(rad, 5.0, FE.DIV)

        pat2 = _gen_path(rc, cx, cy, clip_rad1, rad2)

        rc.add_clip_path(pat2)
        rc.save()
        a2 = rc.float_expression(CS, 360.0, FE.MOD)
        rc.rotate(a2, cx, cy)
        rc.rc_paint.set_sweep_gradient(
            cx, cy,
            [0xFF4E6588, 0xFF182947, 0xFF182947, 0xFF182947,
             0xFF4E6588, 0xFF182947, 0xFF4E6588],
            None, 0).commit()
        second_angle = rc.float_expression(CS, 360.0, FE.MOD, 11.0, FE.MUL)
        rc.draw_circle(cx, cy, rad)
        rc.rotate(second_angle, cx, cy)
        rc.rc_paint.set_sweep_gradient(
            cx, cy,
            [0x804E6588, 0x80182947, 0x80182947, 0x80182947,
             0x804E6588, 0x80182947, 0x804E6588],
            None, 0).commit()
        rc.draw_circle(cx, cy, rad)
        rc.restore()
        rc.rc_paint.set_shader(0).commit()

        _draw_ticks_cond(rc, cx, cy, rad1, rad2)
        _draw_clock(rc, cx, cy)

        rc.end_canvas()
        rc.end_box()

    rc.root(content)
    return _make_result(rc)


if __name__ == '__main__':
    ctx = demo_fancy_clock2_metal()
    data = ctx.encode()
    print(f"fancyClock2: {len(data)} bytes")
    ctx.save("fancy_clock2.rc")

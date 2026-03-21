"""Path expression demos. Port of DemoPathExpression.java.

Covers: pathTest1, pathTest2, pathTest3.
"""
import sys
import os
import math
import struct

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RemoteComposeWriter, Rc, as_nan
from rcreate.modifiers import RecordingModifier

FE = Rc.FloatExpression
PE = Rc.PathExpression
VAR1 = FE.VAR1
CS = Rc.Time.CONTINUOUS_SEC
PI2 = float(math.pi * 2)


def _f32(v):
    """Round to float32 precision (matches Java float arithmetic)."""
    return struct.unpack('>f', struct.pack('>f', v))[0]


def _make_result(rc):
    class Result:
        def encode(self): return rc.encode_to_byte_array()
        def save(self, path):
            with open(path, 'wb') as f: f.write(self.encode())
    return Result()


def demo_path_test1():
    """Path expressions and polar path expressions."""
    rc = RemoteComposeWriter(500, 500, "sd", api_level=7,
                             profiles=Rc.Profiles.PROFILE_ANDROIDX)

    def content():
        rc.start_canvas(RecordingModifier().fill_max_size())
        w = rc.add_component_width_value()
        h = rc.add_component_height_value()
        rc.rc_paint.set_color(0xFF888888).commit()
        rc.draw_rect(0, 0, w, h)

        cx = rc.float_expression(w, 0.5, FE.MUL)
        cy = rc.float_expression(h, 0.5, FE.MUL)
        rad = rc.float_expression(cx, cy, FE.MIN)
        rad2 = rc.float_expression(rad, 2, FE.DIV)
        rad3 = rc.float_expression(rad, 0.7, FE.MUL)

        bump = rc.float_expression(CS, PI2, FE.MUL, FE.SIN, 70, FE.MUL)
        rot = rc.float_expression(CS, 4, FE.MUL, PI2, FE.MOD)
        rc.rc_paint.set_color(0xFF7777FF).commit()
        rc.draw_circle(cx, cy, rad)
        rc.rc_paint.set_color(0xFF77AAFF).commit()

        # Polar path 1 (brown)
        rc.rc_paint.set_color(0xFFAA8844).set_stroke_cap(Rc.Paint.CAP_ROUND).commit()
        path_id_1 = rc.add_polar_path_expression(
            [rad3, 1, VAR1, float(math.pi), FE.ADD, FE.SIN, FE.SUB, FE.MUL],
            0, PI2, 60, cx, rc.float_expression(cy, 0.5, FE.MUL), 0)
        rc.draw_path(path_id_1)

        # Path expression (black, stroke)
        start = rc.float_expression(float(math.pi), CS, FE.ADD)
        end = rc.float_expression(start, float(math.pi), FE.ADD)
        rc.rc_paint.set_color(0xFF000000).set_stroke_width(16.0).set_style(
            Rc.Paint.STYLE_STROKE).commit()
        path_id_2 = rc.add_path_expression(
            [VAR1, FE.SIN, rad2, FE.MUL, cx, FE.ADD],
            [VAR1, FE.COS, rad2, FE.MUL, VAR1, 6, FE.MUL, rot, FE.ADD,
             FE.COS, bump, FE.MUL, cy, FE.ADD, FE.ADD],
            start, end, 60, PE.LOOP_PATH)
        rc.draw_path(path_id_2)

        # Path expression (blue, fill)
        rc.rc_paint.set_color(0xFF0000FF).commit()
        path_id_3 = rc.add_path_expression(
            [VAR1, FE.SIN, rad2, FE.MUL, cx, FE.ADD],
            [VAR1, FE.COS, rad2, FE.MUL, VAR1, 6, FE.MUL, rot, FE.ADD,
             FE.COS, bump, FE.MUL, cy, FE.ADD, FE.ADD],
            0, PI2, 60, PE.LOOP_PATH)
        rc.draw_path(path_id_3)

        # Path expression (green)
        rc.rc_paint.set_color(0xFF00FF00).commit()
        path_id_4 = rc.add_path_expression(
            [VAR1, float(math.pi), FE.DIV, 1, FE.SUB, rad2, FE.MUL, cx, FE.ADD],
            [float(math.pi), VAR1, FE.SUB, FE.SQUARE, 0.04, FE.MUL, rad2, FE.MUL,
             VAR1, 6, FE.MUL, rot, FE.ADD, FE.COS, bump, FE.MUL, cy, FE.ADD,
             FE.ADD],
            0, PI2, 60, 0)
        rc.draw_path(path_id_4)

        # Polar path (red)
        rc.rc_paint.set_color(0xFFFF0000).commit()
        path_id_5 = rc.add_polar_path_expression(
            [rad2, VAR1, 10, FE.MUL, rot, FE.ADD, FE.COS, 20, FE.MUL, FE.ADD],
            0, PI2, 60, cx, cy, PE.LOOP_PATH)
        rc.draw_path(path_id_5)

        # Polar path (yellow, partial)
        end2 = rc.float_expression(CS, float(math.pi), FE.ADD)
        rc.rc_paint.set_color(0xFFFFFF00).set_stroke_cap(Rc.Paint.CAP_ROUND).commit()
        path_id_6 = rc.add_polar_path_expression(
            [rad2, VAR1, 10, FE.MUL, rot, FE.ADD, FE.COS, 20, FE.MUL, FE.ADD,
             20, FE.ADD],
            CS, end2, 60, cx, cy, 0)
        rc.draw_path(path_id_6)

        # Polar path (white, heart shape)
        root2 = float(math.sqrt(2))
        s = 0.7
        s_sq = _f32(_f32(s) * _f32(s))
        rc.rc_paint.set_color(0xFFFFFFFF).set_stroke_cap(Rc.Paint.CAP_ROUND).commit()
        path_id_7 = rc.add_polar_path_expression(
            [rad3, root2, FE.MUL, VAR1, 2, FE.MUL, FE.SIN, FE.ABS, 0.0001, FE.ADD,
             s, FE.MUL, FE.DIV, 1, 1, s_sq, 2, VAR1, FE.MUL, FE.SIN, FE.SQUARE,
             0.0001, FE.ADD, FE.MUL, FE.SUB, FE.SQRT, FE.SUB, FE.SQRT, FE.MUL],
            1, float(math.pi) * 2 + 1, 60, cx, cy, PE.LOOP_PATH)
        rc.draw_path(path_id_7)

        rc.end_canvas()

    rc.root(content)
    return _make_result(rc)


def demo_path_test2():
    """Path morphing (tweening) between two expressions."""
    rc = RemoteComposeWriter(500, 500, "sd", api_level=7,
                             profiles=Rc.Profiles.PROFILE_ANDROIDX)

    def content():
        rc.start_canvas(RecordingModifier().fill_max_size())
        w = rc.add_component_width_value()
        h = rc.add_component_height_value()
        rc.rc_paint.set_color(0xFF888888).commit()
        rc.draw_rect(0, 0, w, h)

        cx = rc.float_expression(w, 0.5, FE.MUL)
        cy = rc.float_expression(h, 0.5, FE.MUL)
        rad = rc.float_expression(cx, cy, FE.MIN)
        rad2 = rc.float_expression(rad, 2, FE.DIV)

        rot = rc.float_expression(CS, 4, FE.MUL, PI2, FE.MOD)
        rot2 = rc.float_expression(rot, Rc.Time.ANIMATION_TIME, 10, 15,
                                   FE.SMOOTH_STEP, FE.MUL)
        rc.rc_paint.set_color(0xFF7777FF).commit()
        rc.draw_circle(cx, cy, rad)
        rc.rc_paint.set_color(0xFF77AAFF).commit()
        rc.draw_circle(cx, cy, 20)

        pi2_07 = _f32(_f32(math.pi * 2) + _f32(0.07))
        rc.rc_paint.set_style(Rc.Paint.STYLE_STROKE).set_color(0xFFFF0000).commit()
        path_id1 = rc.add_polar_path_expression(
            [rad2, VAR1, 10, FE.MUL, rot2, FE.ADD, FE.COS, 50, FE.MUL, FE.ADD],
            0.07, pi2_07, 120, cx, cy, PE.LOOP_PATH)
        rc.draw_path(path_id1)

        root2 = float(math.sqrt(2))
        s = 0.7
        s_sq = _f32(_f32(s) * _f32(s))
        rc.rc_paint.set_color(0xFF00FF00).set_stroke_cap(Rc.Paint.CAP_ROUND).commit()
        path_id3 = rc.add_polar_path_expression(
            [rad2, root2, FE.MUL, VAR1, 2, FE.MUL, FE.SIN, FE.ABS, 0.00001, FE.ADD,
             s, FE.MUL, FE.DIV, 1, 1, s_sq, 2, VAR1, FE.MUL, FE.SIN, FE.SQUARE,
             0.00001, FE.ADD, FE.MUL, FE.SUB, FE.SQRT, FE.SUB, FE.SQRT, FE.MUL],
            0.07, pi2_07, 120, cx, cy, PE.LOOP_PATH)
        rc.draw_path(path_id3)

        rock = rc.float_expression(CS, 4, FE.MOD, 2, FE.SUB, FE.ABS, 2, FE.DIV)

        rc.rc_paint.set_color(0xFFFF00FF).set_stroke_width(14.0).set_style(
            Rc.Paint.STYLE_FILL).commit()
        rc.draw_tween_path(path_id1, path_id3, rock, 0, 1)
        rc.rc_paint.set_color(0xFFFFFFFF).set_stroke_width(14.0).set_style(
            Rc.Paint.STYLE_STROKE).commit()
        rc.draw_tween_path(path_id1, path_id3, rock, 0, 1)

        rc.end_canvas()

    rc.root(content)
    return _make_result(rc)


def demo_path_test3():
    """Linear vs cubic path expression interpolation."""
    rc = RemoteComposeWriter(500, 500, "sd", api_level=7,
                             profiles=Rc.Profiles.PROFILE_ANDROIDX)

    def content():
        rc.start_canvas(RecordingModifier().fill_max_size())
        w = rc.add_component_width_value()
        h = rc.add_component_height_value()
        rc.rc_paint.set_color(0xFF888888).commit()
        rc.draw_rect(0, 0, w, h)

        cx = rc.float_expression(w, 0.5, FE.MUL)
        cy = rc.float_expression(h, 0.5, FE.MUL)
        rad = rc.float_expression(cx, cy, FE.MIN)
        rad2 = rc.float_expression(rad, 2, FE.DIV)

        rot = rc.float_expression(CS, 4, FE.MUL, PI2, FE.MOD)
        rot2 = rc.float_expression(rot, Rc.Time.ANIMATION_TIME, 10, FE.SUB, 0,
                                   FE.MAX, 1, FE.MIN, FE.MUL)
        rc.rc_paint.set_color(0xFF7777FF).commit()
        rc.draw_circle(cx, cy, rad)
        rc.rc_paint.set_color(0xFF77AAFF).commit()
        rc.draw_circle(cx, cy, 20)

        pi2_07 = _f32(_f32(math.pi * 2) + _f32(0.07))
        rc.rc_paint.set_style(Rc.Paint.STYLE_STROKE).set_color(0xFFFF0000).commit()
        path_id1 = rc.add_polar_path_expression(
            [rad2, VAR1, 10, FE.MUL, rot2, FE.ADD, FE.COS, 50, FE.MUL, FE.ADD],
            0.07, pi2_07, 20, cx, cy, PE.LOOP_PATH)
        path_id2 = rc.add_polar_path_expression(
            [rad2, VAR1, 10, FE.MUL, rot2, FE.ADD, FE.COS, 50, FE.MUL, FE.ADD],
            0.07, pi2_07, 20, cx, cy,
            PE.LOOP_PATH | PE.LINEAR_PATH)
        rc.draw_path(path_id1)

        root2 = float(math.sqrt(2))
        s = 0.7
        s_sq = _f32(_f32(s) * _f32(s))
        rc.rc_paint.set_color(0xFF00FF00).set_stroke_cap(Rc.Paint.CAP_ROUND).commit()
        path_id3 = rc.add_polar_path_expression(
            [rad2, root2, FE.MUL, VAR1, 2, FE.MUL, FE.SIN, FE.ABS, 0.00001, FE.ADD,
             s, FE.MUL, FE.DIV, 1, 1, s_sq, 2, VAR1, FE.MUL, FE.SIN, FE.SQUARE,
             0.00001, FE.ADD, FE.MUL, FE.SUB, FE.SQRT, FE.SUB, FE.SQRT, FE.MUL],
            0.07, pi2_07, 20, cx, cy,
            PE.LOOP_PATH | PE.LINEAR_PATH)
        rc.draw_path(path_id3)

        rock = rc.float_expression(CS, 4, FE.MOD, 2, FE.SUB, FE.ABS, 2, FE.DIV)

        rc.rc_paint.set_color(0xFFFF00FF).set_stroke_width(14.0).set_style(
            Rc.Paint.STYLE_FILL).commit()
        rc.draw_tween_path(path_id1, path_id2, rock, 0, 1)
        rc.rc_paint.set_color(0xFFFFFFFF).set_stroke_width(14.0).set_style(
            Rc.Paint.STYLE_STROKE).commit()
        rc.draw_tween_path(path_id1, path_id2, rock, 0, 1)

        rc.end_canvas()

    rc.root(content)
    return _make_result(rc)

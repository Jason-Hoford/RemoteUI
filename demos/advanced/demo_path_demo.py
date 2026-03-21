"""Path demos. Port of PathDemo.java.

Covers: remoteConstruction, pathTweenDemo, path2.
All three use demoCanvas helper: 300x300, api_level=6, profiles=0.
"""
import sys
import os
import math
import struct

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RemoteComposeWriter, Rc, as_nan
from rcreate.modifiers import RecordingModifier

FE = Rc.FloatExpression
CS = Rc.Time.CONTINUOUS_SEC


def _f32(v):
    """Round to float32 precision (matches Java float arithmetic)."""
    return struct.unpack('>f', struct.pack('>f', v))[0]


def _make_result(rc):
    class Result:
        def encode(self): return rc.encode_to_byte_array()
        def save(self, path):
            with open(path, 'wb') as f: f.write(self.encode())
    return Result()


def _create_circle(points, sides, radius):
    """Create a polygon path — matches Java RemotePath createCircle.

    Wire format per RemotePathBase:
      moveTo: [NaN(MOVE), x, y]           (3 floats)
      lineTo: [NaN(LINE), 0, 0, x, y]     (5 floats — 2 padding slots)
      close:  [NaN(CLOSE)]                 (1 float)
    """
    side = points // sides
    angle_step = math.radians(360.0 / sides)
    angle = 0.0

    coords = []
    first = True
    for s in range(sides):
        x1 = radius * math.sin(angle)
        y1 = -radius * math.cos(angle)
        angle += angle_step
        x2 = radius * math.sin(angle)
        y2 = -radius * math.cos(angle)
        for i in range(side):
            # Java: (float)(x1 + (x2-x1) * (i / (float)side))
            # The i/(float)side is float32 division
            frac = _f32(float(i) / float(side))
            x = _f32(x1 + (x2 - x1) * frac)
            y = _f32(y1 + (y2 - y1) * frac)
            if first:
                coords.extend([as_nan(10), x, y])  # MOVE: 3 floats
                first = False
            else:
                coords.extend([as_nan(11), 0.0, 0.0, x, y])  # LINE: 5 floats
    coords.append(as_nan(15))  # CLOSE: 1 float
    return coords


def demo_remote_construction():
    """Procedural path construction in a loop."""
    rc = RemoteComposeWriter(300, 300, "graph", api_level=6)

    def content():
        rc.start_box(RecordingModifier().fill_max_width().fill_max_height(),
                      Rc.Layout.START, Rc.Layout.START)
        rc.start_canvas(RecordingModifier().fill_max_size())

        w = rc.add_component_width_value()
        h = rc.add_component_height_value()
        cx = rc.float_expression(w, 0.5, FE.MUL)
        cy = rc.float_expression(h, 0.5, FE.MUL)
        radius = rc.float_expression(w, h, FE.MIN, 3, FE.DIV)
        top = rc.float_expression(cy, radius, FE.SUB)

        rc.rc_paint.set_stroke_width(10).set_color(0xFFFF0000).set_style(
            Rc.Paint.STYLE_STROKE).commit()
        rc.draw_circle(cx, cy, radius)

        rc.rc_paint.set_stroke_width(10).set_color(0xFF00FF00).set_alpha(0.5).set_style(
            Rc.Paint.STYLE_FILL_AND_STROKE).commit()

        path = rc.path_create(cx, top)
        step = rc.start_loop_var(0, 10, 360)
        x = rc.float_expression(cx, step, FE.RAD, FE.SIN, radius, FE.MUL, FE.ADD)
        y = rc.float_expression(cy, step, FE.RAD, FE.COS, radius, FE.MUL, FE.SUB)
        rc.path_append_line_to(path, x, y)
        rc.end_loop()
        rc.path_append_close(path)
        rc.draw_path(path)

        rc.end_canvas()
        rc.end_box()

    rc.root(content)
    return _make_result(rc)


def demo_path_tween_demo():
    """Path morphing (tweening) between triangle, square, and circle."""
    rc = RemoteComposeWriter(300, 300, "graph", api_level=6)

    def content():
        rc.start_box(RecordingModifier().fill_max_width().fill_max_height(),
                      Rc.Layout.START, Rc.Layout.START)
        rc.start_canvas(RecordingModifier().fill_max_size())

        tween1 = rc.float_expression(CS, 2, FE.MOD, 1, FE.SUB, FE.ABS)
        tween2 = rc.float_expression(CS, 8, FE.MOD, 4, FE.DIV, 1, FE.SUB, FE.ABS)
        w = rc.add_component_width_value()
        h = rc.add_component_height_value()
        cx = rc.float_expression(w, 0.5, FE.MUL)
        cy = rc.float_expression(h, 0.5, FE.MUL)

        path1_data = _create_circle(60, 3, 150)
        path2_data = _create_circle(60, 4, 150)
        path3_data = _create_circle(60, 60, 150)
        pid1 = rc.add_path_data(path1_data)
        pid2 = rc.add_path_data(path2_data)
        pid3 = rc.add_path_data(path3_data)
        pid12 = rc.path_tween(pid1, pid2, tween1)
        pid123 = rc.path_tween(pid12, pid3, tween2)

        delta = 300.0
        rc.translate(cx, cy)
        rc.translate(-delta, -delta)
        rc.rc_paint.set_color(0xFFFF0000).set_stroke_width(3).commit()
        rc.draw_path(pid1)

        color1 = rc.add_color_expression(0xFFFF0000, 0xFF00FF00, tween1)
        rc.rc_paint.set_color_id(color1).set_stroke_width(3).commit()
        rc.translate(delta, 0)
        rc.draw_path(pid12)

        rc.rc_paint.set_color(0xFF00FF00).set_stroke_width(3).commit()
        rc.translate(delta, 0)
        rc.draw_path(pid2)

        color2 = rc.add_color_expression(color1, 0xFF0000FF, tween2)
        rc.rc_paint.set_color_id(color2).set_stroke_width(3).commit()
        rc.translate(-delta, delta)
        rc.draw_path(pid123)

        rc.rc_paint.set_color(0xFF0000FF).set_stroke_width(3).commit()
        rc.translate(0, delta)
        rc.draw_path(pid3)

        rc.end_canvas()
        rc.end_box()

    rc.root(content)
    return _make_result(rc)


def demo_path2():
    """Path2 — path tween with float array, loop, and graph axes."""
    rc = RemoteComposeWriter(300, 300, "graph", api_level=6)

    def content():
        rc.start_box(RecordingModifier().fill_max_width().fill_max_height(),
                      Rc.Layout.START, Rc.Layout.START)
        rc.start_canvas(RecordingModifier().fill_max_size())

        tween1 = rc.float_expression(CS, 2, FE.MOD, 1, FE.SUB, FE.ABS)
        tween2 = rc.float_expression(CS, 8, FE.MOD, 4, FE.DIV, 1, FE.SUB, FE.ABS)
        w = rc.add_component_width_value()
        h = rc.add_component_height_value()
        cx = rc.float_expression(w, 0.5, FE.MUL)
        cy = rc.float_expression(h, 0.5, FE.MUL)
        margin = rc.float_expression(w, h, FE.MIN, 0.1, FE.MUL)

        line_bottom = rc.float_expression(h, margin, FE.SUB)
        line_right = rc.float_expression(w, margin, FE.SUB)
        data = [2.0, 3.0, 5.0, 12.0, 3.0, 1.0]
        rc.rc_paint.set_stroke_width(10).set_color(0xFF444444).set_style(
            Rc.Paint.STYLE_STROKE).commit()
        rc.draw_line(margin, margin, margin, line_bottom)
        rc.draw_line(margin, line_bottom, line_right, line_bottom)

        array_id = rc.add_float_array(data)
        rc.float_expression(array_id, FE.A_MAX)
        rc.float_expression(array_id, FE.A_MIN)
        loop_len = float(len(data))
        rc.start_loop_var(loop_len, 0, 1.0)

        path1_data = _create_circle(60, 3, 150)
        path2_data = _create_circle(60, 4, 150)
        path3_data = _create_circle(60, 60, 150)
        pid1 = rc.add_path_data(path1_data)
        pid2 = rc.add_path_data(path2_data)
        pid3 = rc.add_path_data(path3_data)
        pid12 = rc.path_tween(pid1, pid2, tween1)
        pid123 = rc.path_tween(pid12, pid3, tween2)

        delta = 300.0
        rc.translate(cx, cy)
        rc.translate(-delta, -delta)
        rc.rc_paint.set_color(0xFFFF0000).set_stroke_width(3).commit()
        rc.draw_path(pid1)

        color1 = rc.add_color_expression(0xFFFF0000, 0xFF00FF00, tween1)
        rc.rc_paint.set_color_id(color1).set_stroke_width(3).commit()
        rc.translate(delta, 0)
        rc.draw_path(pid12)

        rc.rc_paint.set_color(0xFF00FF00).set_stroke_width(3).commit()
        rc.translate(delta, 0)
        rc.draw_path(pid2)

        color2 = rc.add_color_expression(color1, 0xFF0000FF, tween2)
        rc.rc_paint.set_color_id(color2).set_stroke_width(3).commit()
        rc.translate(-delta, delta)
        rc.draw_path(pid123)

        rc.rc_paint.set_color(0xFF0000FF).set_stroke_width(3).commit()
        rc.translate(0, delta)
        rc.draw_path(pid3)

        rc.end_canvas()
        rc.end_box()

    rc.root(content)
    return _make_result(rc)

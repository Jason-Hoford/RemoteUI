"""Raw graph demos. Port of Graph.java graph1()/graph2().

Generates: graph_graph1.rc, graph_graph2.rc
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RemoteComposeWriter, Rc, as_nan
from rcreate.modifiers import RecordingModifier

FE = Rc.FloatExpression

GRAY = 0xFF888888
DKGRAY = 0xFF444444
WHITE = 0xFFFFFFFF
BLACK = 0xFF000000
BLUE = 0xFF0000FF
GREEN = 0xFF00FF00
RED = 0xFFFF0000

STYLE_FILL = Rc.Paint.STYLE_FILL
STYLE_STROKE = Rc.Paint.STYLE_STROKE


def _make_result(rc):
    class Result:
        def encode(self): return rc.encode_to_byte_array()
        def save(self, path):
            with open(path, 'wb') as f: f.write(self.encode())
    return Result()


def demo_graph1():
    """Bar graph + spline graph — port of Graph.java graph1()."""
    rc = RemoteComposeWriter(300, 300, "Graph", api_level=6)

    def content():
        rc.start_box(
            RecordingModifier().fill_max_width().fill_max_height(),
            Rc.Layout.START, Rc.Layout.START)
        rc.start_canvas(RecordingModifier().fill_max_size())
        w = rc.add_component_width_value()
        h = rc.add_component_height_value()
        margin = rc.float_expression(w, h, FE.MIN, 0.1, FE.MUL)
        line_bottom = rc.float_expression(h, margin, FE.SUB)
        line_right = rc.float_expression(w, margin, FE.SUB)
        rc.rc_paint.set_color(GRAY).set_style(STYLE_FILL).commit()
        rc.draw_rect(0, 0, w, h)
        data = [2.0, 3.0, 5.0, 12.0, 3.0, 1.0, 8.0, 4.0, 2.0]
        rc.rc_paint.set_stroke_width(10).set_color(DKGRAY).set_style(STYLE_STROKE).commit()
        rc.draw_line(margin, margin, margin, line_bottom)
        rc.draw_line(margin, line_bottom, line_right, line_bottom)
        array = rc.add_float_array(data)
        a_max = rc.float_expression(array, FE.A_MAX)
        a_min = rc.float_expression(array, FE.A_MIN, 1, FE.SUB)
        a_len = rc.float_expression(array, FE.A_LEN)
        gr_height = rc.float_expression(h, margin, 2, FE.MUL, FE.SUB)
        gr_width = rc.float_expression(w, margin, 2, FE.MUL, FE.SUB)
        scale = rc.float_expression(gr_height, a_max, a_min, FE.SUB, FE.DIV)
        rc.rc_paint.set_text_size(60).commit()

        # Bar chart loop
        xstep = rc.float_expression(gr_width, a_len, FE.DIV)
        index = rc.start_loop_var(0, 1.0, a_len)
        x_pos1 = rc.float_expression(xstep, index, FE.MUL, margin, FE.ADD)
        x_pos2 = rc.float_expression(x_pos1, xstep, FE.ADD)
        y_val = rc.float_expression(array, index, FE.A_DEREF)
        line_top = rc.float_expression(gr_height, scale, y_val, a_min, FE.SUB, FE.MUL, FE.SUB,
                                       margin, FE.ADD)
        rc.rc_paint.set_color(BLUE).set_style(STYLE_FILL).set_stroke_width(1).commit()
        rc.draw_rect(x_pos1, line_top, x_pos2, line_bottom)
        text_id = rc.create_text_from_float(y_val, 2, 0, 0)
        rc.rc_paint.set_color(WHITE).set_style(STYLE_STROKE).set_stroke_width(2).commit()
        rc.draw_rect(x_pos1, line_top, x_pos2, line_bottom)
        x_pos_center = rc.float_expression(x_pos1, x_pos2, FE.ADD, 2, FE.DIV)
        rc.rc_paint.set_style(STYLE_FILL).commit()
        rc.draw_text_anchored(text_id, x_pos_center, line_top, 0, 2, 0)
        rc.end_loop()

        # Spline overlay loop
        rc.rc_paint.set_stroke_width(10).set_color(GREEN).set_style(STYLE_STROKE).set_stroke_width(4).commit()
        step = 10.0
        x_off = rc.float_expression(margin, gr_width, a_len, FE.DIV, 2, FE.DIV, FE.ADD)
        x_scale = rc.float_expression(1, gr_width, gr_width, a_len, FE.DIV, FE.SUB, FE.DIV)
        y_off = rc.float_expression(gr_height, scale, a_min, FE.MUL, FE.SUB, margin, FE.ADD)
        sx1 = rc.start_loop_var(margin, step, rc.float_expression(w, margin, FE.SUB))
        sx2 = rc.float_expression(sx1, step, FE.ADD)
        x1 = rc.float_expression(sx1, x_off, FE.SUB, x_scale, FE.MUL)
        x2 = rc.float_expression(sx2, x_off, FE.SUB, x_scale, FE.MUL)
        y1 = rc.float_expression(y_off, scale, array, x1, FE.A_SPLINE, FE.MUL, FE.SUB)
        y2 = rc.float_expression(y_off, scale, array, x2, FE.A_SPLINE, FE.MUL, FE.SUB)
        rc.draw_line(sx1, y1, sx2, y2)
        rc.end_loop()

        rc.end_canvas()
        rc.end_box()

    rc.root(content)
    return _make_result(rc)


def demo_graph2():
    """Spline graph with linear gradient fill — port of Graph.java graph2()."""
    rc = RemoteComposeWriter(300, 300, "Graph2", api_level=6)

    def content():
        rc.start_box(
            RecordingModifier().fill_max_width().fill_max_height(),
            Rc.Layout.START, Rc.Layout.START)
        rc.start_canvas(RecordingModifier().fill_max_size())
        w = rc.add_component_width_value()
        h = rc.add_component_height_value()
        margin = rc.float_expression(w, h, FE.MIN, 0.1, FE.MUL)
        line_bottom = rc.float_expression(h, margin, FE.SUB)
        line_right = rc.float_expression(w, margin, FE.SUB)
        rc.rc_paint.set_color(WHITE).set_style(STYLE_FILL).commit()
        rc.draw_rect(0, 0, w, h)
        data = [2.0, 3.0, 5.0, 12.0, 3.0, 1.0, 8.0, 4.0, 2.0]

        array = rc.add_float_array(data)
        a_max = rc.float_expression(array, FE.A_MAX)
        a_min = rc.float_expression(array, FE.A_MIN, 1, FE.SUB)
        a_len = rc.float_expression(array, FE.A_LEN)
        gr_height = rc.float_expression(h, margin, 2, FE.MUL, FE.SUB)
        gr_width = rc.float_expression(w, margin, 2, FE.MUL, FE.SUB)
        scale = rc.float_expression(gr_height, a_max, a_min, FE.SUB, FE.DIV)
        rc.rc_paint.set_text_size(60).commit()

        xstep = rc.float_expression(gr_width, a_len, FE.DIV)
        index = rc.start_loop_var(0, 1.0, a_len)
        x_pos1 = rc.float_expression(xstep, index, FE.MUL, margin, FE.ADD)
        x_pos2 = rc.float_expression(x_pos1, xstep, FE.ADD)
        y_val = rc.float_expression(array, index, FE.A_DEREF)
        line_top = rc.float_expression(gr_height, scale, y_val, a_min, FE.SUB, FE.MUL, FE.SUB,
                                       margin, FE.ADD)
        rc.rc_paint.set_color(BLUE).set_style(STYLE_FILL).set_stroke_width(1).commit()
        rc.draw_rect(x_pos1, line_top, x_pos2, line_bottom)
        text_id = rc.create_text_from_float(y_val, 2, 0, 0)
        rc.rc_paint.set_color(WHITE).set_style(STYLE_STROKE).set_stroke_width(2).commit()
        rc.draw_rect(x_pos1, line_top, x_pos2, line_bottom)
        x_pos_center = rc.float_expression(x_pos1, x_pos2, FE.ADD, 2, FE.DIV)
        rc.rc_paint.set_style(STYLE_FILL).commit()
        rc.draw_text_anchored(text_id, x_pos_center, line_top, 0, 2, 0)
        rc.end_loop()

        # Spline path with gradient fill
        rc.rc_paint.set_stroke_width(10).set_color(GREEN).set_style(STYLE_STROKE).commit()
        step = 10.0
        x_off = rc.float_expression(margin, gr_width, a_len, FE.DIV, 2, FE.DIV, FE.ADD)
        x_scale_val = rc.float_expression(1, gr_width, gr_width, a_len, FE.DIV, FE.SUB, FE.DIV)
        y_off = rc.float_expression(gr_height, scale, a_min, FE.MUL, FE.SUB, margin, FE.ADD)
        end = rc.float_expression(w, margin, FE.SUB)
        path = rc.path_create(margin, line_bottom)
        sx1 = rc.start_loop_var(margin, step, end)
        x1 = rc.float_expression(sx1, x_off, FE.SUB, x_scale_val, FE.MUL)
        y1 = rc.float_expression(y_off, scale, array, x1, FE.A_SPLINE, FE.MUL, FE.SUB)
        rc.path_append_line_to(path, sx1, y1)
        rc.end_loop()
        rc.path_append_line_to(path, end, line_bottom)
        rc.path_append_close(path)
        rc.rc_paint.set_style(STYLE_FILL).set_linear_gradient(
            0, 0, 0, h, [0xAAFF0000, 0x44FF0000], tile_mode=0).commit()
        top = rc.float_expression(margin, 1, FE.ADD)
        left = rc.float_expression(margin, 10, FE.ADD)
        bottom = rc.float_expression(line_bottom, 10, FE.SUB)
        right = rc.float_expression(end, 20, FE.SUB)
        rc.save()
        rc.clip_rect(left, top, right, bottom)
        rc.draw_path(path)
        rc.rc_paint.set_stroke_width(10).set_shader(0).set_style(STYLE_STROKE).set_color(RED).commit()
        rc.draw_path(path)
        rc.restore()

        # Axis lines
        rc.rc_paint.set_stroke_width(10).set_color(BLACK).set_style(STYLE_STROKE).commit()
        rc.draw_line(margin, margin, margin, line_bottom)
        rc.draw_line(margin, line_bottom, line_right, line_bottom)

        rc.end_canvas()
        rc.end_box()

    rc.root(content)
    return _make_result(rc)

"""Basic procedural demos. Port of BasicProceduralDemos.java.

Covers: simple1-5, simpleClockSlow, simpleClockFast, centerText1,
        version, gradient1-4.
"""
import sys
import os
import math

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RemoteComposeWriter, Rc, as_nan
from rcreate.modifiers import RecordingModifier

FE = Rc.FloatExpression
RC = Rc.RootContent
WW = Rc.System.WINDOW_WIDTH
WH = Rc.System.WINDOW_HEIGHT
CS = Rc.Time.CONTINUOUS_SEC


def demo_simple1():
    """Draw a circle."""
    rc = RemoteComposeWriter(600, 600, "Clock", api_level=6, profiles=0)
    rc.draw_circle(150, 150, 150)

    class Result:
        def encode(self): return rc.encode_to_byte_array()
        def save(self, path):
            with open(path, 'wb') as f: f.write(self.encode())
    return Result()


def demo_simple2():
    """Draw an oval that fits the window."""
    rc = RemoteComposeWriter(300, 300, "Clock", api_level=6, profiles=0)
    rc.set_root_content_behavior(RC.NONE, RC.ALIGNMENT_CENTER,
                                  RC.SIZING_SCALE, RC.SCALE_FIT)
    rc.draw_oval(0, 0, WW, WH)

    class Result:
        def encode(self): return rc.encode_to_byte_array()
        def save(self, path):
            with open(path, 'wb') as f: f.write(self.encode())
    return Result()


def demo_simple3():
    """Draw a red oval with click area."""
    rc = RemoteComposeWriter(300, 300, "Clock", api_level=6, profiles=0)
    rc.set_root_content_behavior(RC.NONE, RC.ALIGNMENT_CENTER,
                                  RC.SIZING_SCALE, RC.SCALE_FILL_BOUNDS)
    rc.rc_paint.set_color(0xFFFF0000).commit()
    rc.add_click_area(232, "foo", 0, 0, 300, 300, "bar")
    rc.draw_oval(0, 0, WW, WH)

    class Result:
        def encode(self): return rc.encode_to_byte_array()
        def save(self, path):
            with open(path, 'wb') as f: f.write(self.encode())
    return Result()


def demo_simple4():
    """Rounded rect with animated radius."""
    rc = RemoteComposeWriter(300, 300, "Clock", api_level=6, profiles=0)
    rc.set_root_content_behavior(RC.NONE, RC.ALIGNMENT_CENTER,
                                  RC.SIZING_SCALE, RC.SCALE_FILL_BOUNDS)
    rc.rc_paint.set_color(0xFFFF0000).commit()
    rad = rc.float_expression(CS, 100, FE.MUL, 100, FE.MOD,
                              50, FE.SUB, FE.ABS)
    rc.draw_round_rect(0, 0, WW, WH, rad, rad)

    class Result:
        def encode(self): return rc.encode_to_byte_array()
        def save(self, path):
            with open(path, 'wb') as f: f.write(self.encode())
    return Result()


def demo_simple5():
    """Oval with animated scaling."""
    rc = RemoteComposeWriter(300, 300, "Clock", api_level=6, profiles=0)
    rc.set_root_content_behavior(RC.NONE, RC.ALIGNMENT_CENTER,
                                  RC.SIZING_SCALE, RC.SCALE_FILL_BOUNDS)
    rc.rc_paint.set_color(0xFFFF0000).commit()
    cx = rc.float_expression(WW, 0.5, FE.MUL)
    cy = rc.float_expression(WH, 0.5, FE.MUL)
    anim = rc.float_expression(CS, 2, FE.MOD, 1, FE.SUB)
    rc.save()
    rc.scale(anim, 1, cx, cy)
    rc.draw_oval(0, 0, WW, WH)
    rc.restore()

    class Result:
        def encode(self): return rc.encode_to_byte_array()
        def save(self, path):
            with open(path, 'wb') as f: f.write(self.encode())
    return Result()


def demo_center_text1():
    """Centered text with animated background."""
    rc = RemoteComposeWriter(300, 300, "Clock", api_level=6, profiles=0)
    rc.set_root_content_behavior(RC.NONE, RC.ALIGNMENT_CENTER,
                                  RC.SIZING_SCALE, RC.SCALE_FILL_BOUNDS)
    rc.rc_paint.set_color(0xFFFF0000).set_text_size(64.0).commit()
    cx = rc.float_expression(WW, 0.5, FE.MUL)
    cy = rc.float_expression(WH, 0.5, FE.MUL)
    anim = rc.float_expression(CS, 2, FE.MOD, 1, FE.SUB)
    rc.save()
    rc.scale(anim, 1, cx, cy)
    rc.draw_oval(0, 0, WW, WH)
    rc.restore()
    count = rc.float_expression(99.0, Rc.Time.TIME_IN_SEC, 100, FE.MOD, FE.SUB)
    text_id = rc.create_text_from_float(count, 3, 0, Rc.TextFromFloat.PAD_AFTER_ZERO)
    text_width = rc.text_measure(text_id, 0)
    text_height = rc.text_measure(text_id, 1)
    left = rc.float_expression(cx, text_width, 2, FE.DIV, FE.SUB)
    top = rc.float_expression(cy, text_height, 2, FE.DIV, FE.SUB)
    bottom = rc.float_expression(top, text_height, FE.ADD)
    right = rc.float_expression(left, text_width, FE.ADD)
    rc.rc_paint.set_style(Rc.Paint.STYLE_STROKE).set_stroke_width(2.0).set_color(
        0xFF000000).commit()
    rc.draw_rect(left, top, right, bottom)
    rc.rc_paint.set_color(0xFF0000FF).set_style(Rc.Paint.STYLE_FILL).commit()
    rc.draw_text_anchored(text_id, cx, cy, 0, 0, 0)

    class Result:
        def encode(self): return rc.encode_to_byte_array()
        def save(self, path):
            with open(path, 'wb') as f: f.write(self.encode())
    return Result()


def demo_version():
    """Show API level version."""
    rc = RemoteComposeWriter(300, 300, "Clock", api_level=6, profiles=0)
    rc.set_root_content_behavior(RC.NONE, RC.ALIGNMENT_CENTER,
                                  RC.SIZING_SCALE, RC.SCALE_FILL_BOUNDS)
    rc.rc_paint.set_color(0xFFFF0000).commit()
    cx = rc.float_expression(WW, 0.5, FE.MUL)
    cy = rc.float_expression(WH, 0.5, FE.MUL)
    anim = rc.float_expression(CS, 2, FE.MOD, 1, FE.SUB)
    rc.save()
    rc.scale(anim, 1, cx, cy)
    rc.draw_oval(0, 0, WW, WH)
    rc.restore()
    rc.rc_paint.set_color(0xFF000000).set_text_size(32).commit()
    vid = rc.create_text_from_float(Rc.System.API_LEVEL, 2, 2, 0)
    rc.draw_text_anchored("Version", cx, cy, 0, -2, 0)
    rc.draw_text_anchored(vid, cx, cy, 0, 2, 0)

    class Result:
        def encode(self): return rc.encode_to_byte_array()
        def save(self, path):
            with open(path, 'wb') as f: f.write(self.encode())
    return Result()


def demo_gradient1():
    """Linear gradient."""
    rc = RemoteComposeWriter(300, 300, "Clock", api_level=6, profiles=0)
    rc.set_root_content_behavior(RC.NONE, RC.ALIGNMENT_CENTER,
                                  RC.SIZING_SCALE, RC.SCALE_FILL_BOUNDS)
    height = WH
    rc.rc_paint.set_linear_gradient(
        0, 0, 0, height, [0xFF00FF00, 0xFF0022FF],
        tile_mode=1).set_text_size(64.0).commit()
    cx = rc.float_expression(WW, 0.5, FE.MUL)
    cy = rc.float_expression(WH, 0.5, FE.MUL)
    anim = rc.float_expression(CS, 2, FE.MOD, 1, FE.SUB)
    rc.save()
    rc.scale(anim, 1, cx, cy)
    rc.draw_oval(0, 0, WW, WH)
    rc.restore()
    rc.draw_text_anchored("gradient", cx, cy, 0, 0, 0)

    class Result:
        def encode(self): return rc.encode_to_byte_array()
        def save(self, path):
            with open(path, 'wb') as f: f.write(self.encode())
    return Result()


def demo_gradient2():
    """Linear gradient with animated color."""
    rc = RemoteComposeWriter(300, 300, "Clock", api_level=6, profiles=0)
    rc.set_root_content_behavior(RC.NONE, RC.ALIGNMENT_CENTER,
                                  RC.SIZING_SCALE, RC.SCALE_FILL_BOUNDS)
    height = WH
    hue = rc.float_expression(CS, float(math.pi * 2), FE.DIV, 1.0, FE.MOD)
    color = rc.add_color_expression(0x8F, hue, 0.9, 0.9)
    rc.rc_paint.set_linear_gradient(
        0, 0, 0, height, [color, 0xFF0022FF],
        tile_mode=1).set_text_size(64.0).commit()
    cx = rc.float_expression(WW, 0.5, FE.MUL)
    cy = rc.float_expression(WH, 0.5, FE.MUL)
    anim = rc.float_expression(CS, 2, FE.MOD, 1, FE.SUB)
    rc.save()
    rc.scale(anim, 1, cx, cy)
    rc.draw_oval(0, 0, WW, WH)
    rc.restore()
    rc.draw_text_anchored("gradient", cx, cy, 0, 0, 0)

    class Result:
        def encode(self): return rc.encode_to_byte_array()
        def save(self, path):
            with open(path, 'wb') as f: f.write(self.encode())
    return Result()


def demo_gradient3():
    """Radial gradient with animated color."""
    rc = RemoteComposeWriter(300, 300, "Clock", api_level=6, profiles=0)
    rc.set_root_content_behavior(RC.NONE, RC.ALIGNMENT_CENTER,
                                  RC.SIZING_SCALE, RC.SCALE_FILL_BOUNDS)
    height = WH
    hue = rc.float_expression(CS, float(math.pi * 2), FE.DIV, 1.0, FE.MOD)
    cx = rc.float_expression(WW, 0.5, FE.MUL)
    cy = rc.float_expression(WH, 0.5, FE.MUL)
    color = rc.add_color_expression(0x8F, hue, 0.9, 0.9)
    rc.rc_paint.set_radial_gradient(
        cx, cy, height, [color, 0xFF0022FF],
        tile_mode=1).set_text_size(64.0).commit()
    anim = rc.float_expression(CS, 2, FE.MOD, 1, FE.SUB)
    rc.save()
    rc.scale(anim, 1, cx, cy)
    rc.draw_oval(0, 0, WW, WH)
    rc.restore()
    rc.draw_text_anchored("gradient", cx, cy, 0, 0, 0)

    class Result:
        def encode(self): return rc.encode_to_byte_array()
        def save(self, path):
            with open(path, 'wb') as f: f.write(self.encode())
    return Result()


def demo_gradient4():
    """Sweep gradient with animated color."""
    rc = RemoteComposeWriter(300, 300, "Clock", api_level=6, profiles=0)
    rc.set_root_content_behavior(RC.NONE, RC.ALIGNMENT_CENTER,
                                  RC.SIZING_SCALE, RC.SCALE_FILL_BOUNDS)
    hue = rc.float_expression(CS, float(math.pi * 2), FE.DIV, 1.0, FE.MOD)
    cx = rc.float_expression(WW, 0.5, FE.MUL)
    cy = rc.float_expression(WH, 0.5, FE.MUL)
    color = rc.add_color_expression(0x8F, hue, 0.9, 0.9)
    rc.rc_paint.set_sweep_gradient(
        cx, cy, [0xFF0022FF, color, 0xFF0022FF]).set_text_size(64.0).commit()
    anim = rc.float_expression(CS, 2, FE.MOD, 1, FE.SUB)
    rc.save()
    rc.scale(anim, 1, cx, cy)
    rc.draw_oval(0, 0, WW, WH)
    rc.restore()
    rc.draw_text_anchored("gradient", cx, cy, 0, 0, 0)

    class Result:
        def encode(self): return rc.encode_to_byte_array()
        def save(self, path):
            with open(path, 'wb') as f: f.write(self.encode())
    return Result()


# Path segment NaN markers
PATH_MOVE = as_nan(10)
PATH_LINE = as_nan(11)
PATH_QUAD = as_nan(12)
PATH_CUBIC = as_nan(14)
PATH_CLOSE = as_nan(15)


def demo_basic_path():
    """Basic path with a cubic curve."""
    rc = RemoteComposeWriter(300, 300, "Clock", api_level=6, profiles=0)
    rc.set_root_content_behavior(RC.NONE, RC.ALIGNMENT_CENTER,
                                  RC.SIZING_SCALE, RC.SCALE_FIT)
    rc.rc_paint.set_stroke_width(30.0).set_color(0xFF3232FF).set_style(
        Rc.Paint.STYLE_STROKE).commit()
    # Path: moveTo(200,100), cubicTo(100,200, 100,200, 0,100)
    path_data = [
        PATH_MOVE, 200.0, 100.0,
        PATH_CUBIC, 200.0, 100.0, 100.0, 200.0, 100.0, 200.0, 0.0, 100.0,
    ]
    pid = rc.add_path_data(path_data)
    rc.draw_path(pid)

    class Result:
        def encode(self): return rc.encode_to_byte_array()
        def save(self, path):
            with open(path, 'wb') as f: f.write(self.encode())
    return Result()


def demo_all_path():
    """Path with various segments (cubic, line, quad)."""
    rc = RemoteComposeWriter(300, 300, "Clock", api_level=6, profiles=0)
    rc.set_root_content_behavior(RC.NONE, RC.ALIGNMENT_CENTER,
                                  RC.SIZING_SCALE, RC.SCALE_FIT)
    rc.rc_paint.set_stroke_width(30.0).set_color(0xFF3232FF).set_style(
        Rc.Paint.STYLE_STROKE).commit()
    # Path: moveTo(200,100), cubicTo(100,200, 100,200, 0,100),
    #        moveTo(200,70), lineTo(0,70),
    #        moveTo(200,50), quadTo(100,0, 0,50)
    path_data = [
        PATH_MOVE, 200.0, 100.0,
        PATH_CUBIC, 200.0, 100.0, 100.0, 200.0, 100.0, 200.0, 0.0, 100.0,
        PATH_MOVE, 200.0, 70.0,
        PATH_LINE, 200.0, 70.0, 0.0, 70.0,
        PATH_MOVE, 200.0, 50.0,
        PATH_QUAD, 200.0, 50.0, 100.0, 0.0, 0.0, 50.0,
    ]
    pid = rc.add_path_data(path_data)
    rc.draw_path(pid)

    class Result:
        def encode(self): return rc.encode_to_byte_array()
        def save(self, path):
            with open(path, 'wb') as f: f.write(self.encode())
    return Result()


def demo_simple_clock_slow():
    """Slow refresh clock demo."""
    rc = RemoteComposeWriter(300, 300, "slow_clock", api_level=6, profiles=0)
    rc.set_root_content_behavior(RC.NONE, RC.ALIGNMENT_CENTER,
                                  RC.SIZING_SCALE, RC.SCALE_FILL_BOUNDS)
    cx = rc.float_expression(WW, 0.5, FE.MUL)
    cy = rc.float_expression(WH, 0.5, FE.MUL)
    angle = rc.float_expression(CS, 360, FE.MUL, 360, FE.MOD)
    rc.rc_paint.set_color(0xFF000000).commit()
    rc.draw_round_rect(0, 0, WW, WH, WW, WH)
    rc.rc_paint.set_color(0xFF00FF00).set_stroke_width(10.0).commit()
    rc.rotate(angle, cx, cy)
    rc.draw_line(cx, cy, cx, 10)

    class Result:
        def encode(self): return rc.encode_to_byte_array()
        def save(self, path):
            with open(path, 'wb') as f: f.write(self.encode())
    return Result()


def demo_simple_clock_fast():
    """Fast refresh clock demo."""
    rc = RemoteComposeWriter(300, 300, "slow_clock", api_level=6, profiles=0)
    rc.set_root_content_behavior(RC.NONE, RC.ALIGNMENT_CENTER,
                                  RC.SIZING_SCALE, RC.SCALE_FILL_BOUNDS)
    cx = rc.float_expression(WW, 0.5, FE.MUL)
    cy = rc.float_expression(WH, 0.5, FE.MUL)
    angle = rc.float_expression(CS, 360, FE.MUL, 360, FE.MOD)
    rc.rc_paint.set_color(0xFF000000).commit()
    rc.draw_round_rect(0, 0, WW, WH, WW, WH)
    rc.rc_paint.set_color(0xFF00FF00).set_stroke_width(10.0).commit()
    rc.rotate(angle, cx, cy)
    rc.draw_line(cx, cy, cx, 10)

    class Result:
        def encode(self): return rc.encode_to_byte_array()
        def save(self, path):
            with open(path, 'wb') as f: f.write(self.encode())
    return Result()


def demo_look_up1():
    """Data map lookup demo."""
    rc = RemoteComposeWriter(300, 300, "Clock", api_level=6, profiles=0)
    rc.set_root_content_behavior(RC.NONE, RC.ALIGNMENT_CENTER,
                                  RC.SIZING_SCALE, RC.SCALE_FILL_BOUNDS)
    rc.rc_paint.set_color(0xFFFF0000).set_text_size(64.0).commit()
    map_id = rc.add_data_map(("First", "John"), ("Last", "David"), ("DOB", 32))
    cx = rc.float_expression(WW, 0.5, FE.MUL)
    cy = rc.float_expression(WH, 0.5, FE.MUL)
    anim = rc.float_expression(CS, 2, FE.MOD, 1, FE.SUB)
    rc.save()
    rc.scale(anim, 1, cx, cy)
    rc.draw_oval(0, 0, WW, WH)
    rc.restore()
    text_id = rc.map_lookup(map_id, "First")
    text_width = rc.text_measure(text_id, 0)
    text_height = rc.text_measure(text_id, 1)
    left = rc.float_expression(cx, text_width, 2, FE.DIV, FE.SUB)
    top = rc.float_expression(cy, text_height, 2, FE.DIV, FE.SUB)
    bottom = rc.float_expression(top, text_height, FE.ADD)
    right = rc.float_expression(left, text_width, FE.ADD)
    rc.rc_paint.set_style(Rc.Paint.STYLE_STROKE).set_stroke_width(2.0).set_color(
        0xFF000000).commit()
    rc.draw_rect(left, top, right, bottom)
    rc.rc_paint.set_color(0xFF0000FF).set_style(Rc.Paint.STYLE_FILL).commit()
    rc.draw_text_anchored(text_id, cx, cy, 0, 0, 0)

    class Result:
        def encode(self): return rc.encode_to_byte_array()
        def save(self, path):
            with open(path, 'wb') as f: f.write(self.encode())
    return Result()


def _demo_canvas(name, draw_fn):
    """Helper matching Java's RCDemo.demoCanvas: root -> box(fmw,fmh) -> canvas(fms)."""
    rc = RemoteComposeWriter(300, 300, name, api_level=6, profiles=0)
    rc.root(lambda: _demo_canvas_body(rc, draw_fn))

    class Result:
        def encode(self): return rc.encode_to_byte_array()
        def save(self, path):
            with open(path, 'wb') as f: f.write(self.encode())
    return Result()


def _demo_canvas_body(rc, draw_fn):
    rc.start_box(RecordingModifier().fill_max_width().fill_max_height(),
                  Rc.Layout.START, Rc.Layout.START)
    rc.start_canvas(RecordingModifier().fill_max_size())
    draw_fn(rc)
    rc.end_canvas()
    rc.end_box()


def demo_acc_sensor1():
    """Accelerometer sensor demo."""
    def draw(rc):
        rc.rc_paint.set_color(0xFF0000FF).commit()
        w = rc.add_component_width_value()
        h = rc.add_component_height_value()
        cx = rc.float_expression(w, 0.5, FE.MUL)
        cy = rc.float_expression(h, 0.5, FE.MUL)
        accX = rc.float_expression(Rc.Sensor.ACCELERATION_X, -9.8 * 2, FE.DIV,
                                    w, FE.MUL, w, 0.5, FE.MUL, FE.ADD)
        accY = rc.float_expression(Rc.Sensor.ACCELERATION_Y, 9.8 * 2, FE.DIV,
                                    w, FE.MUL, w, 0.5, FE.MUL, FE.ADD)
        accZ = rc.float_expression(Rc.Sensor.ACCELERATION_Z, 9.8 * 2, FE.DIV,
                                    w, FE.MUL, w, 0.5, FE.MUL, FE.ADD)
        rc.draw_rect(0, 0, w, h)
        rc.rc_paint.set_color(0xFF00FFFF).set_stroke_width(40).set_stroke_cap(
            Rc.Paint.CAP_ROUND).commit()
        rc.draw_line(cx, cy, accX, accY)
        rc.rc_paint.set_color(0xFFFFFFFF).commit()
        rc.draw_circle(cx, cy, 20)
        rc.rc_paint.set_color(0xFFFF0000).commit()
        rc.draw_circle(accX, cy, 20)
        rc.rc_paint.set_color(0xFF00FF00).commit()
        rc.draw_circle(cx, accY, 20)
        rc.rc_paint.set_color(0xFFFFFF00).commit()
        rc.draw_circle(accZ, accZ, 20)
    return _demo_canvas("Clock", draw)


def demo_gyro_sensor1():
    """Gyroscope sensor demo."""
    def draw(rc):
        rc.rc_paint.set_color(0xFF0000FF).commit()
        w = rc.add_component_width_value()
        h = rc.add_component_height_value()
        cx = rc.float_expression(w, 0.5, FE.MUL)
        cy = rc.float_expression(h, 0.5, FE.MUL)
        gyroX = rc.float_expression(Rc.Sensor.GYRO_ROT_X, 100, FE.MUL)
        gyroY = rc.float_expression(Rc.Sensor.GYRO_ROT_Y, 100, FE.MUL)
        gyroZ = rc.float_expression(Rc.Sensor.GYRO_ROT_Z, 100, FE.MUL)
        rc.draw_rect(0, 0, w, h)
        rc.rc_paint.set_stroke_width(40).set_stroke_cap(Rc.Paint.CAP_ROUND).commit()
        rc.save()
        rc.rc_paint.set_color(0xFFFFFFFF).commit()
        rc.rotate(gyroZ, cx, cy)
        rc.draw_line(cx, cy, cx, h)
        rc.restore()
        rc.save()
        rc.rc_paint.set_color(0xFF00FF00).commit()
        rc.rotate(gyroY, cx, cy)
        rc.draw_line(cx, cy, cx, h)
        rc.restore()
        rc.save()
        rc.rc_paint.set_color(0xFFFF0000).commit()
        rc.rotate(gyroX, cx, cy)
        rc.draw_line(cx, cy, cx, h)
        rc.restore()
    return _demo_canvas("Clock", draw)


def demo_mag_sensor1():
    """Magnetometer sensor demo."""
    def draw(rc):
        rc.rc_paint.set_color(0xFF0000FF).commit()
        w = rc.add_component_width_value()
        h = rc.add_component_height_value()
        cx = rc.float_expression(w, 0.5, FE.MUL)
        cy = rc.float_expression(h, 0.5, FE.MUL)
        accX = rc.float_expression(Rc.Sensor.MAGNETIC_X, -0.02, FE.MUL, w, FE.MUL,
                                    w, 0.5, FE.MUL, FE.ADD)
        accY = rc.float_expression(Rc.Sensor.MAGNETIC_Y, 0.02, FE.MUL, w, FE.MUL,
                                    w, 0.5, FE.MUL, FE.ADD)
        accZ = rc.float_expression(Rc.Sensor.MAGNETIC_Z, 0.02, FE.MUL, w, FE.MUL,
                                    w, 0.5, FE.MUL, FE.ADD)
        rc.draw_rect(0, 0, w, h)
        rc.rc_paint.set_color(0xFF00FFFF).set_stroke_width(40).set_stroke_cap(
            Rc.Paint.CAP_ROUND).commit()
        rc.draw_line(cx, cy, accX, accY)
        rc.rc_paint.set_color(0xFFFFFFFF).commit()
        rc.draw_circle(cx, cy, 20)
        rc.rc_paint.set_color(0xFFFF0000).commit()
        rc.draw_circle(accX, cy, 20)
        rc.rc_paint.set_color(0xFF00FF00).commit()
        rc.draw_circle(cx, accY, 20)
        rc.rc_paint.set_color(0xFFFFFF00).commit()
        rc.draw_circle(accZ, accZ, 20)
    return _demo_canvas("Clock", draw)


def demo_compass():
    """Compass using magnetometer data."""
    rc = RemoteComposeWriter(300, 300, "Clock", api_level=6, profiles=0)
    ctx = {}  # shared state between canvas and outer scope
    def content():
        rc.start_box(RecordingModifier().fill_max_width().fill_max_height(),
                      Rc.Layout.START, Rc.Layout.START)
        rc.start_canvas(RecordingModifier().fill_max_size())
        rc.float_expression(CS)  # required for animation system
        ctx['angle'] = rc.float_expression(
            rc.exp(Rc.Sensor.MAGNETIC_X, Rc.Sensor.MAGNETIC_Y, FE.ATAN2, FE.DEG),
            rc.spring(3.0, 3.0, 0.01, 0))
        w = rc.add_component_width_value()
        h = rc.add_component_height_value()
        ctx['cx'] = rc.float_expression(w, 0.5, FE.MUL)
        ctx['cy'] = rc.float_expression(h, 0.5, FE.MUL)
        cx, cy, angle = ctx['cx'], ctx['cy'], ctx['angle']
        rc.rc_paint.set_color(0xFF0000FF).set_stroke_width(40).set_style(
            Rc.Paint.STYLE_FILL).set_stroke_cap(Rc.Paint.CAP_ROUND).commit()
        rc.draw_circle(cx, cy, 200)
        rc.rc_paint.set_color(0xFF000000).set_stroke_width(40).set_style(
            Rc.Paint.STYLE_FILL).set_stroke_cap(Rc.Paint.CAP_ROUND).commit()
        rc.save()
        rc.rotate(angle, cx, cy)
        rc.draw_line(cx, cy, cx, 100)
        rc.restore()
        rc.end_canvas()
        rc.end_box()
        rc.rc_paint.set_color(0xFF00FFFF).set_style(Rc.Paint.STYLE_FILL).set_text_size(
            64.0).commit()
        light_number = rc.create_text_from_float(ctx['angle'], 4, 2, 0)
        rc.draw_text_anchored(light_number, ctx['cx'], ctx['cy'], 0, 0, 0)
    rc.root(content)

    class Result:
        def encode(self): return rc.encode_to_byte_array()
        def save(self, path):
            with open(path, 'wb') as f: f.write(self.encode())
    return Result()


def demo_light_sensor1():
    """Light sensor demo with spring animation and sector drawing."""
    rc = RemoteComposeWriter(300, 300, "Clock", api_level=6, legacy_header=True)

    def content():
        rc.start_box(RecordingModifier().fill_max_width().fill_max_height(),
                      Rc.Layout.START, Rc.Layout.START)
        rc.start_canvas(RecordingModifier().fill_max_size())
        rc.rc_paint.set_color(0xFF0000FF).commit()
        w = rc.add_component_width_value()
        h = rc.add_component_height_value()
        cx = rc.float_expression(w, 0.5, FE.MUL)
        cy = rc.float_expression(h, 0.5, FE.MUL)
        light_bar = rc.float_expression(
            [Rc.Sensor.LIGHT], rc.spring(3.0, 1.0, 0.01, 0))

        rc.draw_round_rect(0, 0, w, h, 100, 100)
        rc.rc_paint.set_color(0xFF888888).commit()
        arc = rc.float_expression(light_bar, 6, FE.MUL)
        rc.draw_sector(0, 0, w, h, -180, arc)

        rc.rc_paint.set_color(0xFF000000).set_stroke_width(40).set_style(
            Rc.Paint.STYLE_FILL).set_stroke_cap(Rc.Paint.CAP_ROUND).commit()
        _draw_line_at(rc, 0, cx, cy, 40)
        rc.rc_paint.set_color(0xFFFFFFFF).commit()
        _draw_line_at(rc, 30, cx, cy, 40)
        rc.rc_paint.set_color(0xFFFF0000).commit()
        _draw_line_at(rc, light_bar, cx, cy, 50)
        rc.rc_paint.set_color(0xFF0000FF).commit()
        rc.draw_circle(cx, cy, 100.0)
        rc.rc_paint.set_color(0xFF00FFFF).set_style(
            Rc.Paint.STYLE_FILL).set_text_size(64).commit()
        light_number = rc.create_text_from_float(light_bar, 4, 2, 0)
        rc.draw_text_anchored(light_number, cx, cy, 0, 0, 0)
        rc.end_canvas()
        rc.end_box()

    rc.root(content)

    class Result:
        def encode(self): return rc.encode_to_byte_array()
        def save(self, path):
            with open(path, 'wb') as f: f.write(self.encode())
    return Result()


def _draw_line_at(rc, light_bar, cx, cy, rad):
    rc.save()
    sub = rc.float_expression(light_bar, 6, FE.MUL, 90, FE.SUB)
    rc.rotate(sub, cx, cy)
    rc.draw_line(cx, cy, cx, rad)
    rc.restore()


def demo_spline_demo1():
    """Spline animation demo — component-level."""
    rc = RemoteComposeWriter(300, 300, "Clock", api_level=6, profiles=0)
    rc.root(lambda: _spline_demo1_content(rc))

    class Result:
        def encode(self): return rc.encode_to_byte_array()
        def save(self, path):
            with open(path, 'wb') as f: f.write(self.encode())
    return Result()


def _spline_demo1_content(rc):
    rc.start_box(RecordingModifier().fill_max_width().fill_max_height(),
                  Rc.Layout.START, Rc.Layout.START)
    rc.start_canvas(RecordingModifier().fill_max_size())
    w = rc.add_component_width_value()
    h = rc.add_component_height_value()
    cx = rc.float_expression(w, 0.5, FE.MUL)
    cy = rc.float_expression(h, 0.5, FE.MUL)
    data = [1.0, 1.0, 1.0, 0.5, 0.8, 1.0, 0.8, 1.0]
    array = rc.add_float_array(data)
    rc.rc_paint.set_text_size(256.0).commit()
    scale = rc.float_expression(array, CS, 1.8, FE.MOD, 1.8, FE.DIV, FE.A_SPLINE)
    rc.save()
    rc.scale(scale, scale, cx, cy)
    rc.draw_text_anchored("\u2764", cx, cy, 0, 0, 0)
    rc.restore()
    rc.end_canvas()
    rc.end_box()


def demo_simple6():
    """Clock demo using RemotePath with SVG parsing and rotation."""
    from rcreate import RemotePath

    # Build SVG path and translate it
    svg = ("M 0.503 0.224 C 0.503 0.266 0.457 0.296 0.438 0.33 "
           "C 0.418 0.365 0.414 0.42 0.379 0.44 "
           "C 0.345 0.46 0.296 0.436 0.254 0.436 "
           "C 0.212 0.436 0.163 0.459 0.129 0.44 "
           "C 0.094 0.42 0.09 0.365 0.07 0.33 "
           "C 0.05 0.296 0.005 0.266 0.005 0.224 "
           "C 0.005 0.182 0.051 0.152 0.07 0.118 "
           "C 0.09 0.083 0.094 0.029 0.129 0.008 "
           "C 0.163 -0.012 0.212 0.012 0.254 0.012 "
           "C 0.296 0.012 0.345 -0.011 0.379 0.008 "
           "C 0.414 0.028 0.418 0.083 0.438 0.118 "
           "C 0.458 0.152 0.503 0.182 0.503 0.224 Z")
    r_poly = RemotePath(svg)
    r_poly.transform(RemotePath.translate_matrix(-0.255, -0.225))

    rc = RemoteComposeWriter(300, 300, "Clock", api_level=6, profiles=0)
    rc.set_root_content_behavior(RC.NONE, RC.ALIGNMENT_CENTER,
                                  RC.SIZING_SCALE, RC.SCALE_FIT)

    rc.rc_paint.set_color(0xFFFF0000).commit()

    center_x = rc.float_expression(WW, 0.5, FE.MUL)
    center_y = rc.float_expression(WH, 0.5, FE.MUL)
    scale = rc.float_expression(WW, WH, FE.MIN, 2.0, FE.MUL)
    hour_hand_length = rc.float_expression(center_x, center_y, FE.MIN, 0.4, FE.MUL)
    min_hand_length = rc.float_expression(center_x, center_y, FE.MIN, 0.3, FE.MUL)
    second_angle = rc.float_expression(CS, 60.0, FE.MOD, 60.0, FE.MUL)
    min_angle = rc.float_expression(Rc.Time.TIME_IN_MIN, 6.0, FE.MUL)
    hr_angle = rc.float_expression(Rc.Time.TIME_IN_HR, 30.0, FE.MUL)
    hour_width = 8.0
    hand_width = 4.0

    base_color_id = rc.add_named_color("android.colorAccent", 0xFF1A1A5E)
    rc.rc_paint.set_color_id(base_color_id).set_style(Rc.Paint.STYLE_FILL).commit()
    rc.save()
    rc.translate(center_x, center_y)
    rc.scale(scale, scale)
    rc.draw_path(r_poly)
    rc.restore()

    # Hour hand
    rc.save()
    rc.rc_paint.set_color(0xFF888888).set_stroke_width(hour_width).set_stroke_cap(
        Rc.Paint.CAP_ROUND).commit()
    rc.rotate(hr_angle, center_x, center_y)
    rc.draw_line(center_x, center_y, center_x, hour_hand_length)
    rc.restore()

    # Minute hand
    rc.save()
    rc.rc_paint.set_color(0xFFFFFFFF).set_stroke_width(hand_width).commit()
    rc.rotate(min_angle, center_x, center_y)
    rc.draw_line(center_x, center_y, center_x, min_hand_length)
    rc.restore()

    # Second hand
    rc.save()
    rc.rotate(second_angle, center_x, center_y)
    rc.rc_paint.set_color(0xFFFF0000).set_stroke_width(4.0).commit()
    rc.draw_line(center_x, center_y, center_x, min_hand_length)
    rc.restore()

    # Cap
    rc.draw_circle(center_x, center_y, hand_width / 2)

    class Result:
        def encode(self): return rc.encode_to_byte_array()
        def save(self, path):
            with open(path, 'wb') as f: f.write(self.encode())
    return Result()


if __name__ == '__main__':
    demos = [
        ("procedure_simple1", demo_simple1),
        ("procedure_simple2", demo_simple2),
        ("procedure_simple3", demo_simple3),
        ("procedure_simple4", demo_simple4),
        ("procedure_simple5", demo_simple5),
        ("procedure_simple6", demo_simple6),
        ("procedure_center_text1", demo_center_text1),
        ("procedure_version", demo_version),
        ("procedure_gradient1", demo_gradient1),
        ("procedure_gradient2", demo_gradient2),
        ("procedure_gradient3", demo_gradient3),
        ("procedure_gradient4", demo_gradient4),
        ("procedure_look_up1", demo_look_up1),
        ("procedure_simple_clock_slow", demo_simple_clock_slow),
        ("procedure_simple_clock_fast", demo_simple_clock_fast),
        ("path_procedural_checks_basic_path", demo_basic_path),
        ("path_procedural_checks_all_path", demo_all_path),
        ("spline_demo_spline_demo1", demo_spline_demo1),
    ]
    for name, func in demos:
        r = func()
        data = r.encode()
        out = os.path.join(os.path.dirname(__file__), '..', 'output',
                           f'{name}.rc')
        r.save(out)
        print(f"{name}: {len(data)} bytes -> {out}")

"""Winding rule demo. Port of DemoWindingRule.java pathWinding().

Generates: demo_winding_rule_path_winding.rc
"""
import sys
import os
import math
import struct

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RemoteComposeWriter, Rc, as_nan
from rcreate.modifiers import RecordingModifier

FE = Rc.FloatExpression

PATH_MOVE = as_nan(10)
PATH_LINE = as_nan(11)
PATH_CLOSE = as_nan(15)


def _f32(v):
    return struct.unpack('>f', struct.pack('>f', v))[0]


def _spiral():
    """Build a spiral path as a float array, matching Java's float32 arithmetic.

    Java code:
      double angle = 3 * 2 * Math.PI * i / 100f;
      float x = (float)(Math.sin(angle) * (1 + i)) + 100f;
      float y = (float)(Math.cos(angle) * (1 + i)) + 100f;
    Note: 100f in denominator means division is double (100f promotes to double).
    The cast (float) truncates the full double product to float32.
    Then + 100f is float32 addition.
    """
    data = []
    prev_x = prev_y = None
    for i in range(101):
        # angle computed in double (100f → 100.0 in double context)
        angle = 3.0 * 2.0 * math.pi * i / 100.0
        # (float)(Math.sin(angle) * (1 + i)) — cast double product to float
        sin_prod = _f32(math.sin(angle) * (1 + i))
        cos_prod = _f32(math.cos(angle) * (1 + i))
        # + 100f — float32 addition
        x = _f32(sin_prod + 100.0)
        y = _f32(cos_prod + 100.0)
        if i == 0:
            data.extend([PATH_MOVE, x, y])
        else:
            data.extend([PATH_LINE, prev_x, prev_y, x, y])
        prev_x, prev_y = x, y
    data.append(PATH_CLOSE)
    return data


def _make_result(rc):
    class Result:
        def encode(self): return rc.encode_to_byte_array()
        def save(self, path):
            with open(path, 'wb') as f: f.write(self.encode())
    return Result()


def demo_path_winding():
    """Path winding rule demo with 4 quadrants showing different fill rules."""
    rc = RemoteComposeWriter(500, 500, "sd", api_level=7, profiles=Rc.Profiles.PROFILE_ANDROIDX)

    def content():
        rc.start_canvas(RecordingModifier().fill_max_size())
        w = rc.add_component_width_value()
        h = rc.add_component_height_value()
        rc.rc_paint.set_color(0xFF888888).commit()

        rc.draw_rect(0, 0, w, h)

        cx = rc.float_expression(w, 0.5, FE.MUL)
        cy = rc.float_expression(h, 0.5, FE.MUL)
        rad = rc.float_expression(cx, cy, FE.MIN, 2, FE.DIV)

        rc.rc_paint.set_color(0xFF7777FF).commit()
        rc.draw_circle(cx, cy, rad)
        rc.rc_paint.set_color(0xFF77AAFF).commit()

        spiral_data = _spiral()
        for i in range(4):
            path_id = rc.add_path_data(spiral_data, i)
            rc.save()

            if i == 0:
                rc.translate(0, 0)
            elif i == 1:
                rc.translate(cx, 0)
            elif i == 2:
                rc.translate(0, cy)
            elif i == 3:
                rc.translate(cx, cy)

            rc.scale(0.01, 0.01)
            rc.scale(rad, rad)
            rc.clip_rect(0, 0, 200, 200)
            if i == 0:
                color = 0xFF5555FF
            elif i == 1:
                color = 0xFF55FF55
            elif i == 2:
                color = 0xFFFF5555
            else:
                color = 0xFFFFFF55
            rc.rc_paint.set_color(0xFFCCCCCC).set_style(Rc.Paint.STYLE_FILL).commit()
            rc.draw_circle(100, 100, 100)
            rc.rc_paint.set_color(color).set_style(Rc.Paint.STYLE_FILL).set_stroke_width(0.1).commit()

            rc.draw_path(path_id)
            rc.restore()

        rc.rc_paint.set_color(0xFF7777FF).commit()

        rc.end_canvas()

    rc.root(content)
    return _make_result(rc)

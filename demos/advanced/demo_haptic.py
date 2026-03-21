"""Haptic demo. Port of HapticDemo.java demoHaptic1().

Generates: haptic_demo_demo_haptic1.rc
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RemoteComposeWriter, Rc, as_nan
from rcreate.modifiers import RecordingModifier

FE = Rc.FloatExpression
TOUCH_X = Rc.Touch.POSITION_X
TOUCH_Y = Rc.Touch.POSITION_Y

HAPTIC_LABELS = [
    "NO HAPTICS", "LONG PRESS", "VIRTUAL KEY", "KEYBOARD TAP", "CLOCK TICK",
    "CONTEXT CLICK", "KEYBOARD PRESS", "KEYBOARD RELEASE", "VIRTUAL KEY RELEASE",
    "TEXT HANDLE MOVE", "GESTURE START", "GESTURE END", "CONFIRM", "REJECT",
    "TOGGLE ON", "TOGGLE OFF", "THRESHOLD ACTIVATE", "THRESHOLD DEACTIVATE",
    "DRAG START", "SEGMENT TICK", "FREQUENT TICK",
]


def _make_result(rc):
    class Result:
        def encode(self): return rc.encode_to_byte_array()
        def save(self, path):
            with open(path, 'wb') as f: f.write(self.encode())
    return Result()


def demo_haptic1():
    """Haptic feedback demo with buttons."""
    rc = RemoteComposeWriter(1024, 1204, "Clock", api_level=6)

    def content():
        rc.start_box(
            RecordingModifier().fill_max_width().fill_max_height().background(0xFF888888),
            Rc.Layout.START, Rc.Layout.START)
        rc.start_canvas(RecordingModifier().fill_max_size())
        w = rc.add_component_width_value()
        h = rc.add_component_height_value()
        event = Rc.Touch.TOUCH_EVENT_TIME

        button_width = rc.float_expression(w, 3, FE.DIV, 10, FE.SUB)
        button_height = rc.float_expression(h, 7, FE.DIV, 20, FE.SUB)
        layout_step_x = rc.float_expression(button_width, 10, FE.ADD)
        layout_step_y = rc.float_expression(button_height, 10, FE.ADD)
        button_center_x = rc.float_expression(w, 6, FE.DIV)
        button_center_y = rc.float_expression(h, 14, FE.DIV)

        tx = rc.add_touch(0, 0, w, Rc.Touch.STOP_ABSOLUTE_POS, 0, 0, None, None,
                          TOUCH_X)
        ty = rc.add_touch(0, 0, w, Rc.Touch.STOP_ABSOLUTE_POS, 0, 0, None, None,
                          TOUCH_Y)
        rc.rc_paint.set_text_size(32.0).commit()

        rc.save()
        i = 0
        for y in range(7):
            rc.save()
            for x in range(len(HAPTIC_LABELS) // 6):
                if i < len(HAPTIC_LABELS):
                    rc.rc_paint.set_color(0xFF0000FF).commit()
                    rc.draw_round_rect(4, 4, button_width, button_height, 32, 32)
                    rc.rc_paint.set_color(0xFFFFFFFF).commit()
                    rc.draw_text_anchored(
                        HAPTIC_LABELS[i], button_center_x, button_center_y, 0, 0, 0)
                    rc.translate(layout_step_x, 0)
                    i += 1
            rc.restore()
            rc.translate(0, layout_step_y)

        rc.restore()
        rc.impulse(0.1, event)
        rc.perform_haptic(8)
        rc.impulse_process()
        rc.rc_paint.set_color(0xFF00FF00).commit()
        rc.draw_circle(tx, ty, 60)
        rc.impulse_end()
        rc.impulse_end()
        rc.end_canvas()
        rc.end_box()

    rc.root(content)
    return _make_result(rc)

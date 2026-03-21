"""Impulse demos. Port of ImpulseDemo.java.

Covers: heartsDemo (touch-triggered hearts particle system).
confettiDemo requires a bitmap and cannot be byte-identical without
matching the Android PNG encoder.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RemoteComposeWriter, Rc, as_nan
from rcreate.modifiers import RecordingModifier

FE = Rc.FloatExpression
WINDOW_W = Rc.System.WINDOW_WIDTH
WINDOW_H = Rc.System.WINDOW_HEIGHT
TOUCH_POS_X = Rc.Touch.POSITION_X
TOUCH_POS_Y = Rc.Touch.POSITION_Y
TOUCH_VEL_X = Rc.Touch.VELOCITY_X
TOUCH_VEL_Y = Rc.Touch.VELOCITY_Y
TOUCH_EVENT = Rc.Touch.TOUCH_EVENT_TIME
DT = Rc.Time.ANIMATION_DELTA_TIME
CS = Rc.Time.CONTINUOUS_SEC
SQRT = FE.SQRT
RAND = FE.RAND
ADD = FE.ADD
SUB = FE.SUB
MUL = FE.MUL
DIV = FE.DIV
MOD = FE.MOD


def _make_result(rc):
    class Result:
        def encode(self): return rc.encode_to_byte_array()
        def save(self, path):
            with open(path, 'wb') as f: f.write(self.encode())
    return Result()


def demo_hearts():
    """Touch-triggered hearts particle animation."""
    rc = RemoteComposeWriter(300, 300, "HeartsDemo", api_level=6)

    def content():
        rc.start_box(RecordingModifier().fill_max_width().fill_max_height(),
                     Rc.Layout.START, Rc.Layout.START)
        rc.start_canvas(RecordingModifier().fill_max_size())

        cx = rc.float_expression(WINDOW_W, 0.5, MUL)
        cy = rc.float_expression(WINDOW_H, 0.5, MUL)
        anim = rc.float_expression(CS, 2, MOD, 1, SUB)

        ty = rc.add_touch(cy, 0.0, WINDOW_H,
                          Rc.Touch.STOP_ABSOLUTE_POS, 0.0, 0, None, None,
                          TOUCH_POS_Y)
        tx = rc.add_touch(cx, 0.0, WINDOW_W,
                          Rc.Touch.STOP_ABSOLUTE_POS, 0.0, 0, None, None,
                          TOUCH_POS_X)

        rc.rc_paint.set_color(0xFF0000FF).set_style(Rc.Paint.STYLE_FILL).commit()

        event = TOUCH_EVENT

        rc.rc_paint.set_color(0xFF00FF00).set_alpha(0.3).set_text_size(64.0).commit()
        rc.save()
        rc.scale(anim, 1, cx, cy)
        rc.draw_oval(0, 0, WINDOW_W, WINDOW_H)
        rc.restore()

        text_id = rc.create_text_from_float(500, 3, 0, Rc.TextFromFloat.PAD_AFTER_ZERO)

        rc.rc_paint.set_style(Rc.Paint.STYLE_STROKE).set_stroke_width(2.0).set_color(
            0xFF000000).commit()
        rc.rc_paint.set_color(0xFF0000FF).set_style(Rc.Paint.STYLE_FILL).commit()

        rc.draw_text_anchored(text_id, cx, cy, 0, 0, 0)

        # Hearts particle engine
        rc.rc_paint.set_text_size(64.0).commit()
        rc.impulse(7.9, event)

        variables = [0.0] * 6
        ps = rc.create_particles(variables,
            [
                [tx, RAND, 300.0, MUL, 150, SUB, ADD],       # x
                [ty, RAND, 300.0, MUL, 150, SUB, ADD],       # y
                [RAND, SQRT, RAND, SQRT, SUB, 10.0, MUL,
                 TOUCH_VEL_X, ADD],                           # dx
                [RAND, SQRT, RAND, SQRT, SUB, 10.0, MUL,
                 TOUCH_VEL_Y, ADD],                           # dy
                [RAND, 2, MUL],                                # h (scale)
                [1.0],                                         # alpha
            ], 50)
        x, y, dx, dy, h, alpha = variables

        rc.impulse_process()
        rc.particles_loop(ps,
            [y, WINDOW_H, SUB],  # restart condition
            [
                [x, dx, ADD],                               # x += dx
                [y, dy, ADD],                               # y += dy
                [dx],                                        # dx unchanged
                [dy, 9.8, DT, MUL, ADD],                    # dy += gravity
                [h],                                         # h unchanged
                [alpha, 0.99, MUL],                          # alpha *= 0.99
            ],
            lambda: _hearts_draw(rc, x, y, h, alpha))
        rc.impulse_end()
        rc.impulse_end()

        rc.end_canvas()
        rc.end_box()

    rc.root(content)
    return _make_result(rc)


def _hearts_draw(rc, x, y, h, alpha):
    rc.rc_paint.set_alpha(alpha).commit()
    rc.save()
    rc.scale(h, h, x, y)
    rc.draw_text_run("\u2764", 0, 1, 0, 0, x, y, False)
    rc.restore()


if __name__ == '__main__':
    ctx = demo_hearts()
    data = ctx.encode()
    print(f"heartsDemo: {len(data)} bytes")
    ctx.save("impulse_demo_hearts_demo.rc")

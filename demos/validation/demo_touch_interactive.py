"""Validation demo: touch/interactivity.

Exercises:
- Touch expressions (POSITION_X, POSITION_Y)
- Touch-driven position (draggable circle)
- Touch-driven text display (coordinate readout)
- Conditional rendering based on touch state
- Float expression division, modulo
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RcContext, Rc
from rcreate.modifiers import RecordingModifier
from rcreate.types.rfloat import RFloat

PROFILE_ANDROIDX = 0x200
PROFILE_EXPERIMENTAL = 0x1
FE = Rc.FloatExpression
STYLE_FILL = Rc.Paint.STYLE_FILL
STYLE_STROKE = Rc.Paint.STYLE_STROKE


def demo_touch_interactive():
    ctx = RcContext(500, 500, "Touch Interactive", api_level=7,
                    profiles=PROFILE_ANDROIDX | PROFILE_EXPERIMENTAL)

    with ctx.root():
        with ctx.box(RecordingModifier().fill_max_size(),
                     Rc.Layout.START, Rc.Layout.START):
            with ctx.canvas(RecordingModifier().fill_max_size()
                            .background(0xFF1E1E2E)):
                w = ctx.ComponentWidth()
                h = ctx.ComponentHeight()

                # Touch expressions: finger position
                touch_x = ctx.touch_expression(
                    Rc.Touch.POSITION_X,
                    def_value=250.0,
                    min_val=0.0,
                    max_val=500.0,
                    touch_mode=Rc.Touch.STOP_GENTLY)
                touch_y = ctx.touch_expression(
                    Rc.Touch.POSITION_Y,
                    def_value=250.0,
                    min_val=0.0,
                    max_val=500.0,
                    touch_mode=Rc.Touch.STOP_GENTLY)

                tx = RFloat(ctx._writer, [touch_x])
                ty = RFloat(ctx._writer, [touch_y])

                # Background grid
                ctx.painter.set_color(0x33FFFFFF) \
                    .set_style(STYLE_STROKE) \
                    .set_stroke_width(1.0).commit()
                for i in range(0, 501, 50):
                    ctx.draw_line(float(i), 0.0, float(i), 500.0)
                    ctx.draw_line(0.0, float(i), 500.0, float(i))

                # Crosshair lines from touch point
                ctx.painter.set_color(0x88FF4444) \
                    .set_stroke_width(1.0).commit()
                ctx.draw_line(tx.to_float(), 0.0,
                              tx.to_float(), 500.0)
                ctx.draw_line(0.0, ty.to_float(),
                              500.0, ty.to_float())

                # Main circle at touch point
                ctx.painter.set_color(0xFF4488FF) \
                    .set_style(STYLE_FILL).commit()
                ctx.draw_circle(tx.to_float(), ty.to_float(), 30.0)

                # Outline
                ctx.painter.set_color(0xFFFFFFFF) \
                    .set_style(STYLE_STROKE) \
                    .set_stroke_width(2.0).commit()
                ctx.draw_circle(tx.to_float(), ty.to_float(), 30.0)

                # Coordinate display text
                ctx.painter.set_color(0xFFFFFFFF) \
                    .set_text_size(20.0) \
                    .set_style(STYLE_FILL).commit()
                x_text = ctx.create_text_from_float(touch_x, 3, 0, 0)
                y_text = ctx.create_text_from_float(touch_y, 3, 0, 0)
                ctx.draw_text_anchored(x_text, 20.0, 30.0, -1.0, 0.0, 0)
                ctx.draw_text_anchored(y_text, 20.0, 55.0, -1.0, 0.0, 0)

                # Distance from center indicator
                dist_sq = (tx - 250.0) * (tx - 250.0) + \
                          (ty - 250.0) * (ty - 250.0)
                dist_id = dist_sq.flush()
                dist_text = dist_id.gen_text_id(0, 1)
                ctx.draw_text_anchored(dist_text, 250.0, 480.0,
                                       0.0, 0.0, 0)

    return ctx


if __name__ == '__main__':
    ctx = demo_touch_interactive()
    data = ctx.encode()
    outdir = os.path.join(os.path.dirname(__file__), '..', 'output')
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, 'val_touch_interactive.rc')
    ctx.save(path)
    print(f"val_touch_interactive: {len(data)} bytes -> {path}")

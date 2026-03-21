"""Bitmap drawing demos. Port of DemoBitmapDrawing.java.

Covers: bitDraw1 (createBitmap, drawOnBitmap, drawScaledBitmap),
        bitDraw2 (same + blendMode).
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RemoteComposeWriter, Rc
from rcreate.modifiers import RecordingModifier

FE = Rc.FloatExpression
PROFILE_ANDROIDX = 0x200


def _make_result(rc):
    class Result:
        def encode(self): return rc.encode_to_byte_array()
        def save(self, path):
            with open(path, 'wb') as f: f.write(self.encode())
    return Result()


def demo_bit_draw1():
    """Drawing on a bitmap and rendering it tiled."""
    rc = RemoteComposeWriter(500, 500, "sd", api_level=7,
                             profiles=PROFILE_ANDROIDX)

    def content():
        rc.start_box(RecordingModifier().fill_max_size(),
                     Rc.Layout.START, Rc.Layout.START)
        rc.start_canvas(RecordingModifier().fill_max_size())

        w = rc.add_component_width_value()
        h = rc.add_component_height_value()
        cx = rc.float_expression(w, 2, FE.DIV)
        cy = rc.float_expression(h, 2, FE.DIV)
        rad = rc.float_expression(w, h, FE.MIN, 2.0, FE.DIV)

        bitmap_id = rc.create_bitmap(256, 256)
        rc.rc_paint.set_color(0xFF888888).commit()  # Color.GRAY
        rc.draw_circle(cx, cy, rad)

        rc.draw_on_bitmap(bitmap_id, 0, 0)
        rc.save()
        angle = rc.float_expression(Rc.Time.CONTINUOUS_SEC, 30, FE.MUL)
        rc.rotate(angle, 128, 128)
        rc.rc_paint.set_color(0xFFFF0000).commit()  # Color.RED
        rc.draw_circle(128, 128, 64)
        rc.rc_paint.set_color(0xFF00FF00).commit()  # Color.GREEN
        rc.save()
        rc.scale(0.5, 2, 128, 128)
        rc.draw_circle(128, 128, 64)
        rc.restore()
        rc.save()
        rc.scale(2, 0.5, 128, 128)
        rc.rc_paint.set_color(0xFF0000FF).commit()  # Color.BLUE
        rc.draw_circle(128, 128, 64)
        rc.restore()
        rc.restore()
        rc.draw_on_bitmap(0, 0, 0)

        for i in range(64):
            n = 8
            top = (i // n) * 150.0
            bottom = (i // n) * 150.0 + 128.0
            left = (i % n) * 150.0
            right = (i % n) * 150.0 + 128.0
            rc.draw_scaled_bitmap(
                bitmap_id,
                0, 0, 256, 256,
                left, top, right, bottom,
                Rc.ImageScale.FIT, 0, "")

        rc.end_canvas()
        rc.end_box()

    rc.root(content)
    return _make_result(rc)


def demo_bit_draw2():
    """Drawing on a bitmap with blend modes."""
    rc = RemoteComposeWriter(500, 500, "sd", api_level=7,
                             profiles=PROFILE_ANDROIDX)

    def content():
        rc.start_box(RecordingModifier().fill_max_size(),
                     Rc.Layout.START, Rc.Layout.START)
        rc.start_canvas(RecordingModifier().fill_max_size())

        w = rc.add_component_width_value()
        h = rc.add_component_height_value()
        cx = rc.float_expression(w, 2, FE.DIV)
        cy = rc.float_expression(h, 2, FE.DIV)
        rad = rc.float_expression(w, h, FE.MIN, 2.0, FE.DIV)

        bitmap_id = rc.create_bitmap(256, 256)
        rc.rc_paint.set_color(0xFF888888).commit()  # Color.GRAY
        rc.draw_circle(cx, cy, rad)

        rc.rc_paint.set_color(0x00000000).set_blend_mode(
            Rc.BlendMode.SRC_OUT).commit()
        rc.draw_circle(cx, cy, 400)

        rc.draw_on_bitmap(bitmap_id, 0, 0xFFFFFF00)
        rc.rc_paint.set_color(0x00000000).set_blend_mode(
            Rc.BlendMode.SRC_OUT).commit()
        rc.draw_circle(128, 128, 128)
        rc.draw_on_bitmap(0)

        rc.rc_paint.set_color(0xFF000000).set_blend_mode(
            Rc.BlendMode.SRC_OVER).commit()

        for i in range(64):
            n = 8
            top = (i // n) * 150.0
            bottom = (i // n) * 150.0 + 128.0
            left = (i % n) * 150.0
            right = (i % n) * 150.0 + 128.0
            rc.draw_scaled_bitmap(
                bitmap_id,
                0, 0, 256, 256,
                left, top, right, bottom,
                Rc.ImageScale.FIT, 0, "")

        rc.end_canvas()
        rc.end_box()

    rc.root(content)
    return _make_result(rc)


if __name__ == '__main__':
    for name, func in [("bitDraw1", demo_bit_draw1),
                        ("bitDraw2", demo_bit_draw2)]:
        ctx = func()
        data = ctx.encode()
        print(f"{name}: {len(data)} bytes")
        ctx.save(f"demo_bitmap_drawing_{name}.rc")

"""Port of basicTimer() from ExampleTimer.kt → countdown.rc

Target .rc files:
  - countdown.rc -> demo_countdown_kt()
"""
import sys
import os
import math

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RcContext, Modifier, Rc
from rcreate.modifiers import RecordingModifier
from rcreate.types.rfloat import rf_min, rf_hypot, rf_sin, rf_cos

# Android Color constants
BLACK = 0xFF000000
WHITE = 0xFFFFFFFF
LTGRAY = 0xFFCCCCCC
DKGRAY = 0xFF444444

STYLE_FILL = Rc.Paint.STYLE_FILL
STYLE_STROKE = Rc.Paint.STYLE_STROKE
CAP_ROUND = 1


def demo_countdown_kt():
    """Port of basicTimer() from ExampleTimer.kt → countdown.rc.

    V6 format, apiLevel=6, profiles=0.
    """
    ctx = RcContext(500, 500, "Simple Timer", api_level=6, profiles=0)

    with ctx.root():
        with ctx.box(RecordingModifier().fill_max_size(),
                     Rc.Layout.START, Rc.Layout.START):
            with ctx.canvas(RecordingModifier().fill_max_size()):
                w = ctx.ComponentWidth()
                h = ctx.ComponentHeight()
                cx = w / 2.0
                cy = h / 2.0
                rad = rf_min(cx, cy)
                rad2 = rf_hypot(cx, cy)

                # Radial gradient background
                ctx.painter.set_radial_gradient(
                    cx.to_float(), cy.to_float(), rad2.to_float(),
                    [LTGRAY, DKGRAY], [0.0, 2.0], 0).commit()

                ctx.draw_round_rect(0, 0, w.to_float(), h.to_float(),
                                    (rad / 4.0).to_float(),
                                    (rad / 4.0).to_float())

                # Sector (sweeping arc)
                ctx.painter.set_color(0x99888888) \
                    .set_shader(0) \
                    .set_stroke_width(32.0) \
                    .set_stroke_cap(CAP_ROUND).commit()
                ctx.draw_sector(
                    (rad * -1.0).to_float(),
                    (rad * -1.0).to_float(),
                    (w + rad).to_float(),
                    (h + rad).to_float(),
                    -90.0,
                    ((ctx.ContinuousSec() * 360.0) % 360.0).to_float())

                # Text: countdown number
                ctx.painter.set_color(BLACK).set_text_size(512.0).commit()
                text_id = ctx.create_text_from_float(
                    ((ctx.ContinuousSec() % 10.0) * -1.0 + 9.999).to_float(),
                    1, 0, 0)

                ctx.matrix_save()
                ctx.scale((ctx.ContinuousSec() % 1.0).to_float(),
                          (ctx.ContinuousSec() % 1.0).to_float(),
                          cx.to_float(), cx.to_float())  # Kotlin bug: centerX used for both
                ctx.draw_text_anchored(text_id,
                                       cx.to_float(), cy.to_float(),
                                       0.0, 0.0, 0)
                ctx.matrix_restore()

                # Second hand line
                pi2 = 2.0 * math.pi
                ctx.painter.set_color(WHITE).set_stroke_width(4.0).commit()
                ctx.draw_line(
                    cx.to_float(),
                    cy.to_float(),
                    (w / 2.0 + rad * rf_sin(
                        ctx.ContinuousSec() * pi2)).to_float(),
                    (h / 2.0 - rad * rf_cos(
                        ctx.ContinuousSec() * pi2)).to_float())

    return ctx


if __name__ == '__main__':
    ctx = demo_countdown_kt()
    data = ctx.encode()
    outdir = os.path.join(os.path.dirname(__file__), '..', 'output')
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, 'countdown.rc')
    ctx.save(path)
    print(f"countdown: {len(data)} bytes -> {path}")

    ref_dir = os.path.join(os.path.dirname(__file__), '..', '..',
                           'integration-tests', 'player-view-demos',
                           'src', 'main', 'res', 'raw')
    ref_path = os.path.join(ref_dir, 'countdown.rc')
    if os.path.exists(ref_path):
        ref_data = open(ref_path, 'rb').read()
        if data == ref_data:
            print("MATCH: byte-identical")
        else:
            print(f"DIFF: gen={len(data)} ref={len(ref_data)}")

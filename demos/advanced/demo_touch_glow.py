"""Interactive touch-follow glow -> touch_glow.rc

A pulsing multi-layered glow that tracks the pointer. Drag anywhere
on the canvas — the rings follow, sized by a time-driven pulse so the
glow breathes while moving.

Demonstrates RemoteCompose's touch input pipeline: ID_TOUCH_POS_X /
ID_TOUCH_POS_Y are populated by the TS player from pointer events,
and they participate in expressions just like any other variable.
This is the proof-of-life that .rc artifacts can power *interactive*
UI, not just animations.

Tip: in the web deck the canvas backing buffer is 500x500, so touch
coords land directly in the demo's drawing space.
"""
import sys
import os
import math

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RcContext, Rc
from rcreate.modifiers import RecordingModifier
from rcreate.types.rfloat import rf_sin


PROFILE_ANDROIDX = 0x200
STYLE_FILL = Rc.Paint.STYLE_FILL
STYLE_STROKE = Rc.Paint.STYLE_STROKE


def demo_touch_glow():
    ctx = RcContext(500, 500, "Touch Glow",
                    api_level=7, profiles=PROFILE_ANDROIDX)

    with ctx.root():
        with ctx.box(RecordingModifier().fill_max_size().background(0xFF0A0E1A),
                     Rc.Layout.START, Rc.Layout.START):
            with ctx.canvas(RecordingModifier().fill_max_size()):
                # Static decoration: cross-hair grid so the empty canvas
                # gives the eye something to track even before you click.
                ctx.painter.set_color(0xFF1F2937) \
                    .set_style(STYLE_STROKE) \
                    .set_stroke_width(1.0).commit()
                for x in range(50, 500, 50):
                    ctx.draw_line(float(x), 0.0, float(x), 500.0)
                for y in range(50, 500, 50):
                    ctx.draw_line(0.0, float(y), 500.0, float(y))

                # Hint label as a row of dots — drawing real text is heavier;
                # this row of dots reads as a "drag here" affordance.
                ctx.painter.set_color(0xFF4B5563).set_style(STYLE_FILL).commit()
                for x in range(160, 350, 20):
                    ctx.draw_circle(float(x), 250.0, 1.5)

                # System variables
                tx = ctx.to_rf(Rc.Touch.POSITION_X)   # ID 13
                ty = ctx.to_rf(Rc.Touch.POSITION_Y)   # ID 14
                t  = ctx.animationTime()

                # Breathing pulse (0..1), period ~0.9s
                pulse = (rf_sin(t * 7.0) + 1.0) * 0.5

                # Three concentric rings — sized by base + pulse, centered on touch.
                # Colors are RGBA with alpha, painted over the dark bg as soft glows.
                for base_r, color in [
                    (70.0, 0x22FBBF24),   # outer warm halo
                    (45.0, 0x4438BDF8),   # mid blue
                    (22.0, 0xAAEF4444),   # inner red
                ]:
                    r_rf = base_r + pulse * 12.0
                    ctx.painter.set_color(color).set_style(STYLE_FILL).commit()
                    ctx.draw_circle(tx.to_float(), ty.to_float(), r_rf.to_float())

                # Bright center dot — always visible
                ctx.painter.set_color(0xFFFFFFFF).set_style(STYLE_FILL).commit()
                ctx.draw_circle(tx.to_float(), ty.to_float(), 4.0)

                # Crosshair lines from edges to the touch point — gives a
                # "tracking sight" feel. Drawn in a faint accent color so
                # they're not too busy.
                ctx.painter.set_color(0x4438BDF8) \
                    .set_style(STYLE_STROKE) \
                    .set_stroke_width(1.0).commit()
                ctx.draw_line(0.0, ty.to_float(),   500.0, ty.to_float())
                ctx.draw_line(tx.to_float(), 0.0,  tx.to_float(),  500.0)

    return ctx


if __name__ == '__main__':
    ctx = demo_touch_glow()
    data = ctx.encode()
    outdir = os.path.join(os.path.dirname(__file__), '..', 'output')
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, 'touch_glow.rc')
    ctx.save(path)
    print(f"touch_glow: {len(data)} bytes -> {path}")

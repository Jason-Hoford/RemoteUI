"""Lissajous curve with morphing phase -> lissajous.rc

Classic 3:2 Lissajous figure traced as a closed parametric path:
  x(u) = cx + A·sin(3u + δ)
  y(u) = cy + A·sin(2u)
where δ is a slow function of animationTime, so the figure morphs
continuously through a family of shapes.

Demonstrates `add_path_expression` with a time-driven phase parameter
inside the lambda — the renderer re-samples the path each frame,
producing a smoothly evolving curve from a static expression.
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
CAP_ROUND = Rc.Paint.CAP_ROUND


def demo_lissajous():
    ctx = RcContext(500, 500, "Lissajous",
                    api_level=7, profiles=PROFILE_ANDROIDX)

    cx, cy = 250.0, 250.0
    amp = 170.0
    a = 3.0    # x-frequency
    b = 2.0    # y-frequency
    two_pi = 2.0 * math.pi

    with ctx.root():
        with ctx.box(RecordingModifier().fill_max_size().background(0xFF0A0E1A),
                     Rc.Layout.START, Rc.Layout.START):
            with ctx.canvas(RecordingModifier().fill_max_size()):
                # Bounding box guide
                ctx.painter.set_color(0xFF1F2937) \
                    .set_style(STYLE_STROKE) \
                    .set_stroke_width(1.0).commit()
                ctx.draw_rect(cx - amp, cy - amp, cx + amp, cy + amp)

                # Crosshair through the center
                ctx.painter.set_color(0xFF22304E).set_stroke_width(1.0).commit()
                ctx.draw_line(cx - amp, cy, cx + amp, cy)
                ctx.draw_line(cx, cy - amp, cx, cy + amp)

                # Phase delta: slowly varying with time
                t = ctx.animationTime()
                delta = t * 0.4  # rad/sec — completes a full morph cycle every 2π/0.4 ≈ 15.7 s

                # Parametric path
                exp_x = ctx.r_fun(lambda u: cx + amp * rf_sin(u * a + delta))
                exp_y = ctx.r_fun(lambda u: cy + amp * rf_sin(u * b))

                # Glow underlayer — wider stroke, low alpha
                ctx.painter.set_color(0x4438BDF8) \
                    .set_style(STYLE_STROKE) \
                    .set_stroke_width(8.0) \
                    .set_stroke_cap(CAP_ROUND).commit()
                glow_id = ctx.add_path_expression(
                    exp_x.to_array(), exp_y.to_array(),
                    0.0, two_pi, 240, 0)
                ctx.draw_path(glow_id)

                # Main curve — tight cyan stroke
                ctx.painter.set_color(0xFF38BDF8) \
                    .set_style(STYLE_STROKE) \
                    .set_stroke_width(2.5).commit()
                main_id = ctx.add_path_expression(
                    exp_x.to_array(), exp_y.to_array(),
                    0.0, two_pi, 240, 0)
                ctx.draw_path(main_id)

                # Tracer dot riding the curve at parameter u = (animationTime mod 4) / 4 * 2π
                u_t = (t % 4.0) * (two_pi / 4.0)
                trace_x = cx + amp * rf_sin(u_t * a + delta)
                trace_y = cy + amp * rf_sin(u_t * b)

                # Outer ring
                ctx.painter.set_color(0xFFFBBF24) \
                    .set_style(STYLE_STROKE) \
                    .set_stroke_width(2.0).commit()
                ctx.draw_circle(trace_x.to_float(), trace_y.to_float(), 9.0)
                # Inner fill
                ctx.painter.set_style(STYLE_FILL).commit()
                ctx.draw_circle(trace_x.to_float(), trace_y.to_float(), 4.0)

    return ctx


if __name__ == '__main__':
    ctx = demo_lissajous()
    data = ctx.encode()
    outdir = os.path.join(os.path.dirname(__file__), '..', 'output')
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, 'lissajous.rc')
    ctx.save(path)
    print(f"lissajous: {len(data)} bytes -> {path}")

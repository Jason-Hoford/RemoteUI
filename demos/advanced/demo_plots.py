"""Port of Demo.kt (plot2, plot3, plot4) and PlotWave.kt (plotWave).

Target .rc files:
  - plot2.rc  -> demo_plot2()
  - plot3.rc  -> demo_plot3()
  - plot4.rc  -> demo_plot4()
  - plot_wave.rc -> demo_plot_wave()
"""
import sys
import os
import math

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RcContext, Modifier, Rc
from rcreate.types.rfloat import RFloat, _coerce, _to_array, rf_if_else

FE = Rc.FloatExpression
PROFILE_ANDROIDX = 0x200
STYLE_FILL = Rc.Paint.STYLE_FILL
STYLE_STROKE = Rc.Paint.STYLE_STROKE

# Android colors
BLACK = 0xFF000000
WHITE = 0xFFFFFFFF
GRAY = 0xFF888888
LTGRAY = 0xFFCCCCCC
DKGRAY = 0xFF444444
YELLOW = 0xFFFFFF00


# ============================================================================
# plot2 — simple sin(x) plot with touch interaction
# ============================================================================
def demo_plot2():
    ctx = RcContext(500, 500, "Simple Timer",
                    api_level=7, profiles=PROFILE_ANDROIDX)
    with ctx.root():
        with ctx.box(Modifier().fill_max_size(), Rc.Layout.START, Rc.Layout.START):
            with ctx.canvas(Modifier().fill_max_size().background(0xFF127799)):
                ctx.painter.set_color(0xFFFF9966).set_text_size(64.0).commit()
                minX = -10.0
                maxX = 10.0

                scaleY = (ctx.ComponentHeight() - 100.0) / -10.0
                offsetY = ctx.ComponentHeight() / 2.0
                scaleX = (ctx.ComponentWidth() - 100.0) / (maxX - minX)
                offsetX = ctx.rf(50.0) - ctx.rf(minX) * scaleX

                ctx.painter.set_stroke_width(10.0).set_style(STYLE_STROKE).commit()
                equ = ctx.r_fun(lambda x: x.sin())
                x_expr = ctx.r_fun(lambda x: x * scaleX + offsetX)

                path_id = ctx.add_path_expression(
                    x_expr.to_array(),
                    (equ * scaleY + offsetY).to_array(),
                    minX, maxX, 64, Rc.PathExpression.SPLINE_PATH)
                ctx.draw_path(path_id)

                # Evaluate scaleX for touch WITHOUT modifying the RFloat
                # (matches Kotlin where toFloat() evaluates but array stays)
                scaleX_val = ctx._writer.float_expression(*scaleX.to_array())
                touchX = ctx.rf(ctx.add_touch(
                    (minX + maxX) / 2, minX, maxX,
                    Rc.Touch.STOP_INSTANTLY, 0.0, 0,
                    None, None,
                    Rc.Touch.POSITION_X,
                    scaleX_val, FE.DIV))

                sPos = touchX * scaleX + offsetX
                ctx.draw_line(sPos.to_float(), 0,
                              sPos.to_float(), ctx.ComponentHeight().to_float())
    return ctx


# ============================================================================
# plot3 — animated sin(x + time) with scale text
# ============================================================================
def demo_plot3():
    ctx = RcContext(500, 500, "Simple Timer",
                    api_level=7, profiles=PROFILE_ANDROIDX)
    with ctx.root():
        with ctx.box(Modifier().fill_max_size(), Rc.Layout.START, Rc.Layout.START):
            with ctx.canvas(Modifier().fill_max_size().background(0xFF127799)):
                ctx.painter.set_color(0xFFFF9966).set_text_size(64.0).commit()
                minX = -10.0
                maxX = 10.0
                scale = ((ctx.Seconds() / 2.0) % 2.0 + 1.0).anim(0.5)
                scaleY = scale * (ctx.ComponentHeight() - 100.0) / -10.0
                offsetY = ctx.ComponentHeight() / 2.0
                scaleX = (ctx.ComponentWidth() - 100.0) / (maxX - minX)
                offsetX = ctx.rf(50.0) - ctx.rf(minX) * scaleX
                tid = scale.gen_text_id(1, 1)
                ctx.draw_text_anchored(tid,
                                       (ctx.ComponentWidth() / 2.0).to_float(),
                                       100.0, 0, 0, 0)
                ctx.painter.set_stroke_width(10.0).set_style(STYLE_STROKE).commit()
                equ = ctx.r_fun(lambda x: (x + ctx.ContinuousSec() * 3.0).sin())

                path_id = ctx.add_path_expression(
                    ctx.r_fun(lambda x: x * scaleX + offsetX).to_array(),
                    (equ * scaleY + offsetY).to_array(),
                    minX, maxX, 64, Rc.PathExpression.SPLINE_PATH)
                ctx.draw_path(path_id)
    return ctx


# ============================================================================
# plot4 — polar path plot with animated scale
# ============================================================================
def demo_plot4():
    ctx = RcContext(500, 500, "Simple Timer",
                    api_level=7, profiles=PROFILE_ANDROIDX)
    with ctx.root():
        with ctx.box(Modifier().fill_max_size(), Rc.Layout.START, Rc.Layout.START):
            with ctx.canvas(Modifier().fill_max_size().background(0xFF127799)):
                ctx.painter.set_color(0xFFFF9966).set_text_size(64.0).commit()
                minX = 0
                maxX = math.pi * 2.0
                scale = ((ctx.Seconds() / 2.0) % 2.0 + 1.0).anim(
                    0.5, Rc.Animate.CUBIC_DECELERATE)
                tid = scale.gen_text_id(1, 1)
                ctx.draw_text_anchored(tid,
                                       (ctx.ComponentWidth() / 2.0).to_float(),
                                       100.0, 0, 0, 0)

                equ = ctx.r_fun(
                    lambda x: ctx.rf(100.0) + ctx.rf(10.0) * (
                        x * 10.0 + ctx.ContinuousSec() * 3.0).sin())

                # Build RFloat objects first (triggers COMPONENT_VALUE for CH),
                # then call to_float() — matches Kotlin evaluation order.
                cx = ctx.ComponentWidth() / 2.0
                cy = ctx.ComponentHeight() / 2.0
                path_id = ctx.add_polar_path_expression(
                    (equ * scale).to_array(),
                    minX, maxX, 64,
                    cx.to_float(),
                    cy.to_float(),
                    Rc.PathExpression.SPLINE_PATH)
                ctx.draw_path(path_id)
    return ctx


# ============================================================================
# plot_wave — complex multi-equation plot with grid, loops, color expressions
# ============================================================================
def demo_plot_wave():
    ctx = RcContext(500, 500, "Simple Timer",
                    api_level=7, profiles=PROFILE_ANDROIDX)
    with ctx.root():
        with ctx.box(Modifier().fill_max_size(), Rc.Layout.START, Rc.Layout.START):
            with ctx.canvas(Modifier().fill_max_size()):
                w = ctx.ComponentWidth()
                h = ctx.ComponentHeight()

                ctx.painter.set_color(0xFF000077).commit()
                ctx.draw_round_rect(0, 0, w.to_float(), h.to_float(), 2.0, 2.0)

                minX = -2.0
                maxX = 2.0
                majorStepX = 0.1
                minorStepX = 0.5
                insertX = 100.0
                insertY = 100.0

                scaleX = (h - insertX * 2.0) / (maxX - minX)
                offsetX = ctx.rf(insertX) - ctx.rf(minX) * scaleX

                # minor vertical lines
                ctx.painter.set_color(DKGRAY).set_stroke_width(4.0).set_text_size(48.0).commit()
                with ctx.loop_range(minX, majorStepX, maxX) as x:
                    posX = x * scaleX + offsetX
                    ctx.draw_line(posX.to_float(), insertY,
                                  posX.to_float(), (h - insertY).to_float())

                # major vertical lines with labels
                ctx.painter.set_color(GRAY).commit()
                bottom = h - insertY
                with ctx.loop_range(minX, minorStepX, maxX) as x:
                    posX = x * scaleX + offsetX
                    tid = x.gen_text_id(1, 1)
                    ctx.draw_text_anchored(tid, posX.to_float(),
                                           bottom.to_float(), 0, 1.5, 0)
                    ctx.draw_line(posX.to_float(), insertY,
                                  posX.to_float(), bottom.to_float())

                # zero line
                ctx.painter.set_color(LTGRAY).commit()
                ctx.draw_line(offsetX.to_float(), insertY,
                              offsetX.to_float(), bottom.to_float())

                # Horizontal lines
                minY = -2.0
                maxY = 2.0
                majorStepY = 0.1
                minorStepY = 0.5
                scaleY = (h - insertY * 2.0) / (minY - maxY)
                offsetY = (h - insertY) - (scaleY * ctx.rf(minY))

                ctx.painter.set_color(DKGRAY).set_stroke_width(4.0).commit()
                with ctx.loop_range(minY, majorStepY, maxY) as y:
                    yPos = y * scaleY + offsetY
                    ctx.draw_line(insertX, yPos.to_float(),
                                  (w - insertX).to_float(), yPos.to_float())

                ctx.painter.set_color(GRAY).commit()
                with ctx.loop_range(minY, minorStepY, maxY) as y:
                    yPos = y * scaleY + offsetY
                    tid = y.gen_text_id(1, 1)
                    ctx.draw_text_anchored(tid, insertX, yPos.to_float(),
                                           1.5, 0, 0)
                    ctx.draw_line(insertX, yPos.to_float(),
                                  (w - insertX).to_float(), yPos.to_float())

                ctx.painter.set_color(WHITE).commit()
                ctx.draw_line(insertX, offsetY.to_float(),
                              (w - insertX).to_float(), offsetY.to_float())

                # Equations
                ctx.painter.set_color(YELLOW).set_style(STYLE_STROKE) \
                    .set_stroke_width(12.0).commit()

                equations = [
                    ctx.r_fun(lambda x: x.sin()),
                    ctx.r_fun(lambda x: x.cos()),
                    ctx.r_fun(lambda x: x.sin() * x.sin()),
                    rf_if_else(
                        RFloat(ctx._writer, FE.VAR1),
                        RFloat(ctx._writer, 0.1),
                        RFloat(ctx._writer, 0.9)),
                ]
                titles = [
                    "sin(x)",
                    "cos(x)",
                    "sin(x) * sin(x)",
                    "ifElse( x, rf(0.1f), rf(0.9f))",
                ]

                for i, equation in enumerate(equations):
                    color_id = ctx.add_color_expression(
                        i / (1.5 * len(equations)), 0.9, 0.9)
                    ctx.painter.set_color_id(color_id).set_style(STYLE_FILL).commit()
                    ctx.draw_text_anchored(
                        titles[i],
                        (w - insertX + 10.0).to_float(),
                        (h * 0.75).to_float(),
                        1.0, 4 - i * 2.0, 0)
                    ctx.painter.set_style(STYLE_STROKE).commit()
                    _plot(ctx, equation, scaleX, offsetX, scaleY, offsetY,
                          minX, maxX)
    return ctx


def _plot(ctx, equation, scaleX, offsetX, scaleY, offsetY, minX, maxX):
    """Plot a function expression (equivalent to Kotlin plot())."""
    x_expr = ctx.r_fun(lambda x: x * scaleX + offsetX)
    y_expr = equation * scaleY + offsetY
    path_id = ctx.add_path_expression(
        x_expr.to_array(), y_expr.to_array(),
        float(minX), float(maxX), 300, Rc.PathExpression.LINEAR_PATH)
    ctx.draw_path(path_id)


if __name__ == '__main__':
    outdir = os.path.join(os.path.dirname(__file__), '..', 'output')
    os.makedirs(outdir, exist_ok=True)

    for name, func in [('plot2', demo_plot2), ('plot3', demo_plot3),
                        ('plot4', demo_plot4), ('plot_wave', demo_plot_wave)]:
        ctx = func()
        data = ctx.encode()
        path = os.path.join(outdir, f'{name}.rc')
        ctx.save(path)
        print(f'{name}: {len(data)} bytes -> {path}')

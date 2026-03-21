"""Graph demos. Port of DemoGraphs.kt.

Demonstrates:
- rcPlotXY with data array (demo_graphs1)
- rcPlotXY with FunctionPlot + animated scale (demo_graphs2)
"""
import sys
import os
import math

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RcContext, Rc, RecordingModifier, RFloat, DEMO7_TAG_ORDER
from rcreate.xy_graph import rc_plot_xy, FunctionPlot, XYGraphProperties
from rcreate.types.rfloat import rf_min, rf_abs


def demo_graphs1():
    """Simple data array plot — port of demoGraphs().

    DemosCreation.java: getp("0/A/demoGraphs1", DemoGraphsKt::demoGraphs)
    """
    ctx = RcContext(500, 500, "Simple Timer", api_level=7, profiles=0x200,
                    header_tag_order=DEMO7_TAG_ORDER)

    density = ctx.rf(Rc.System.DENSITY)

    with ctx.root():
        with ctx.column():
            ctx.text_by_id(
                ctx.create_text_from_float(Rc.System.WINDOW_WIDTH, 4, 2, 0))
            ctx.text_by_id(
                ctx.create_text_from_float(Rc.System.WINDOW_HEIGHT, 4, 2, 0))
            ctx.text_by_id(
                ctx.create_text_from_float(Rc.System.DENSITY, 4, 2, 0))
            ctx.text_by_id(
                ctx.create_text_from_float(Rc.System.FONT_SIZE, 4, 2, 0))

            with ctx.box(RecordingModifier().fill_max_size(),
                         Rc.Layout.START, Rc.Layout.START):
                with ctx.canvas(
                        RecordingModifier().fill_max_size().background(
                            0xFF112244)):
                    w = ctx.ComponentWidth()
                    h = ctx.ComponentHeight()

                    data = [math.sin(x / 3.14) + 0.5 for x in range(32)]
                    values = ctx.rf(ctx.add_float_array(data))

                    rc_plot_xy(
                        ctx,
                        10.0 * density, 10.0 * density,
                        w - 10.0 * density, h - 10.0 * density,
                        plot=values)
    return ctx


def demo_graphs2():
    """Animated function plot — port of demoGraphs2().

    Note: demo_graphs2.rc has no reference — demo_graphs0 maps to demoGraphs2.
    """
    ctx = RcContext(500, 500, "Simple Timer", api_level=7, profiles=0x200,
                    header_tag_order=DEMO7_TAG_ORDER)

    density = ctx.rf(Rc.System.DENSITY)

    with ctx.root():
        with ctx.box(RecordingModifier().fill_max_size(),
                     Rc.Layout.START, Rc.Layout.START):
            with ctx.canvas(
                    RecordingModifier().fill_max_size().background(
                        0xFF112244)):
                w = ctx.ComponentWidth()
                h = ctx.ComponentHeight()

                scale = rf_abs(
                    (ctx.ContinuousSec().sin() + 1.5) * 10.0).flush()

                equ = ctx.r_fun(lambda x:
                    rf_min(scale, 15.0) * (x * 0.3 + ctx.ContinuousSec()).sin() * (x * 7.0).sin()
                )

                function = FunctionPlot(
                    equ,
                    ctx.rf(-10.0), ctx.rf(10.0),
                    -1.0 * scale, scale)

                rc_plot_xy(
                    ctx,
                    10.0 * density, 10.0 * density,
                    w, h,
                    plot=function)
    return ctx


if __name__ == '__main__':
    for name, func in [("demo_graphs1", demo_graphs1),
                        ("demo_graphs2", demo_graphs2)]:
        r = func()
        data = r.encode()
        print(f"{name}: {len(data)} bytes")
        out = os.path.join(os.path.dirname(__file__), '..', 'output',
                           f'{name}.rc')
        r.save(out)
        print(f"Saved {out}")

"""Port of DemoGraphs.kt demoGraphs2() function.

Note: DemosCreation.java maps "demoGraphs0" -> DemoGraphsKt::demoGraphs2

Target .rc file: demo_graphs0.rc
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RcContext, Rc, DEMO7_TAG_ORDER
from rcreate.modifiers.recording_modifier import RecordingModifier
from rcreate.xy_graph import rc_plot_xy, FunctionPlot
from rcreate.types.rfloat import rf_abs, rf_sin, rf_min

PROFILE_ANDROIDX = 0x200


def demo_graphs0():
    """Animated function plot — port of demoGraphs2().

    DemosCreation.java: getp("0/A/demoGraphs0", DemoGraphsKt::demoGraphs2)
    """
    ctx = RcContext(500, 500, "Simple Timer",
                    api_level=7, profiles=PROFILE_ANDROIDX,
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
                cx = w / 2.0
                cy = h / 2.0
                scale = rf_abs(
                    (rf_sin(ctx.ContinuousSec()) + 1.5) * 10.0).flush()
                equ = ctx.r_fun(lambda x:
                    rf_min(scale, 15.0) * rf_sin(x * 0.3 + ctx.ContinuousSec()) * rf_sin(x * 7.0))

                function = FunctionPlot(
                    equ,
                    ctx.rf(-10.0), ctx.rf(10.0),
                    -1.0 * scale, scale)

                rc_plot_xy(ctx,
                           10.0 * density, 10.0 * density,
                           w, h,
                           plot=function)
    return ctx


if __name__ == '__main__':
    ctx = demo_graphs0()
    data = ctx.encode()
    outdir = os.path.join(os.path.dirname(__file__), '..', 'output')
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, 'demo_graphs0.rc')
    ctx.save(path)
    print(f"demo_graphs0: {len(data)} bytes -> {path}")

    ref_dir = os.path.join(os.path.dirname(__file__), '..', '..',
                           'integration-tests', 'player-view-demos',
                           'src', 'main', 'res', 'raw')
    ref_path = os.path.join(ref_dir, 'demo_graphs0.rc')
    if os.path.exists(ref_path):
        ref_data = open(ref_path, 'rb').read()
        if data == ref_data:
            print("MATCH: byte-identical")
        else:
            print(f"DIFF: gen={len(data)} ref={len(ref_data)}")
            for i in range(min(len(data), len(ref_data))):
                if data[i] != ref_data[i]:
                    print(f"  First diff at byte {i}: gen=0x{data[i]:02x} ref=0x{ref_data[i]:02x}")
                    break

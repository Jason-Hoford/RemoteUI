"""Linear regression demo. Port of LinearRegression.kt.

Demonstrates:
- Float array operations (arrayLength, arraySum, arraySumSqr, arraySumXY)
- RFloat arithmetic for computing slope/intercept
- Custom PlotBase for scatter plot
- FunctionPlot for regression line
- rc_plot_xy for combined graph with axes
- createTextFromFloat and textMerge for formula display

Target .rc file: linear_regression.rc
NOTE: Will not byte-match reference due to random data generation.
"""
import sys
import os
import random

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RcContext, Modifier, Rc, RFloat
from rcreate.types.rfloat import (
    rf_array_len, rf_array_sum, rf_array_sum_sqr, rf_array_sum_xy,
)
from rcreate.xy_graph import (
    rc_plot_xy, FunctionPlot, XYGraphProperties, PlotBase, PlotParams, Range,
    _to_float,
)

PROFILE_ANDROIDX = 0x200
STYLE_FILL = Rc.Paint.STYLE_FILL
STYLE_STROKE = Rc.Paint.STYLE_STROKE

# Android color constants
BLACK = 0xFF000000
BLUE = 0xFF0000FF


def demo_linear_regression():
    """Port of demoLinearRegression() from LinearRegression.kt -> linear_regression.rc."""
    n_points = 50
    true_slope = 0.5
    true_intercept = 10.0
    noise_scale = 2.0

    x_data = [float(i) + (random.random() - 0.5) * noise_scale
              for i in range(n_points)]
    y_data = [true_slope * i + true_intercept + (random.random() - 0.5) * noise_scale * 4.0
              for i in range(n_points)]

    ctx = RcContext(500, 500, "Linear Regression Demo",
                    api_level=7, profiles=PROFILE_ANDROIDX)

    density = ctx.rf(Rc.System.DENSITY)

    with ctx.root():
        with ctx.box(Modifier().fill_max_size(), Rc.Layout.START, Rc.Layout.START):
            with ctx.canvas(Modifier().fill_max_size().background(0xFFF8F8F8)):
                w = ctx.ComponentWidth()
                h = ctx.ComponentHeight()

                rx = ctx.rf(ctx.add_float_array(x_data))
                ry = ctx.rf(ctx.add_float_array(y_data))

                n = rf_array_len(rx)
                sum_x = rf_array_sum(rx).flush()
                sum_y = rf_array_sum(ry).flush()
                sum_xx = rf_array_sum_sqr(rx)
                sum_xy = rf_array_sum_xy(rx, ry)

                # slope = (n * sumXY - sumX * sumY) / (n * sumXX - sumX * sumX)
                slope = ((n * sum_xy - sum_x * sum_y) /
                         (n * sum_xx - sum_x * sum_x)).flush()
                # intercept = (sumY - slope * sumX) / n
                intercept = ((sum_y - slope * sum_x) / n).flush()

                graph_prop = XYGraphProperties()

                # Custom scatter plot
                class ScatterPlot(PlotBase):
                    def calc_range(self, rc):
                        return Range(
                            rc.rf(0.0),
                            rc.rf(float(n_points)),
                            rc.rf(0.0),
                            rc.rf(40.0))

                    def plot(self, rc, params):
                        rc.painter.set_color(BLACK).set_style(STYLE_FILL).commit()
                        with rc.loop_range(0, 1, n.to_float()) as i:
                            vx = rx[i]
                            vy = ry[i]
                            sx = vx * params.scale_x + params.offset_x
                            sy = vy * params.scale_y + params.offset_y
                            rc.draw_circle(
                                sx.to_float(),
                                sy.to_float(),
                                _to_float(3.0 * density),
                            )

                scatter_plot = ScatterPlot()

                regression_line = FunctionPlot(
                    ctx.r_fun(lambda x: x * slope + intercept),
                    0.0,
                    float(n_points),
                    0.0,
                    40.0,
                )

                # Combined plot: scatter + regression line
                class CombinedPlot(PlotBase):
                    def calc_range(self, rc):
                        return Range(
                            rc.rf(0.0),
                            rc.rf(float(n_points)),
                            rc.rf(0.0),
                            rc.rf(40.0))

                    def plot(self, rc, params):
                        scatter_plot.plot(rc, params)
                        params.prop.set_plot_paint(
                            rc.painter,
                            _to_float(2.0 * RFloat(rc.writer, Rc.System.DENSITY)),
                        ).set_color(BLUE).commit()
                        regression_line.plot(rc, params)

                combined_plot = CombinedPlot()

                rc_plot_xy(
                    ctx,
                    20.0 * density,
                    20.0 * density,
                    w - 20.0 * density,
                    h - 20.0 * density,
                    graph_prop,
                    combined_plot,
                )

                # Display the formula
                ctx.painter.set_color(BLACK).set_text_size(
                    _to_float(16.0 * density)).commit()
                slope_text = ctx.create_text_from_float(slope.to_float(), 5, 2, 0)
                intercept_text = ctx.create_text_from_float(
                    intercept.to_float(), 5, 2, 0)
                formula_id = ctx.text_create_id("y = ")
                plus_id = ctx.text_create_id("x + ")
                full_formula = ctx.text_merge(
                    formula_id,
                    ctx.text_merge(
                        slope_text,
                        ctx.text_merge(plus_id, intercept_text)))

                ctx.draw_text_anchored(
                    full_formula,
                    _to_float(50.0 * density),
                    _to_float(50.0 * density),
                    0.0, 0.0, 0)

    return ctx


if __name__ == '__main__':
    ref_dir = os.path.join(os.path.dirname(__file__), '..', '..',
                           'integration-tests', 'player-view-demos',
                           'src', 'main', 'res', 'raw')
    out_dir = os.path.join(os.path.dirname(__file__), '..', 'output')
    os.makedirs(out_dir, exist_ok=True)

    ctx = demo_linear_regression()
    data = ctx.encode()
    print(f"linear_regression: {len(data)} bytes")

    out_path = os.path.join(out_dir, 'linear_regression.rc')
    ctx.save(out_path)
    print(f"Saved {out_path}")

    # Compare against reference
    ref_path = os.path.join(ref_dir, 'linear_regression.rc')
    if os.path.exists(ref_path):
        ref_data = open(ref_path, 'rb').read()
        if data == ref_data:
            print("MATCH: byte-identical to reference linear_regression.rc")
        else:
            print(f"DIFF: generated {len(data)} bytes vs reference {len(ref_data)} bytes")
            print("  (Expected: random data differs between runs)")
            for i in range(min(len(data), len(ref_data))):
                if data[i] != ref_data[i]:
                    print(f"  First diff at byte {i}: got 0x{data[i]:02X} vs ref 0x{ref_data[i]:02X}")
                    break
    else:
        print(f"No reference file at {ref_path}")

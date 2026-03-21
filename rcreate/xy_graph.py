"""XY Graph plotting infrastructure for RemoteCompose.

Port of XYGraph.kt — provides PlotParams, XYGraphProperties, Range,
PlotBase, FunctionPlot, Plot, and rc_plot_xy().
"""

from __future__ import annotations
import math

from .rc import Rc
from .types.rfloat import (
    RFloat, _coerce, _to_array,
    rf_max, rf_min, rf_pow, rf_if_else,
    rf_array_max, rf_array_min, rf_array_len, rf_array_spline,
)
from .types.nan_utils import as_nan, id_from_nan


# ── Color constants (Android Color equivalents) ──
COLOR_DKGRAY = 0xFF444444
COLOR_GRAY = 0xFF888888
COLOR_YELLOW = 0xFFFFFF00
COLOR_RED = 0xFFFF0000
COLOR_BLUE = 0xFF0000FF

# Android Paint style constants
STYLE_STROKE = Rc.Paint.STYLE_STROKE
STYLE_FILL = Rc.Paint.STYLE_FILL


def _to_float(v) -> float:
    """Convert RFloat or number to float for wire calls."""
    if isinstance(v, RFloat):
        return v.to_float()
    return float(v)


class XYGraphProperties:
    """Visual properties for XY graph axes and plot."""

    def __init__(self):
        self.minor_v_axis_color: int = COLOR_DKGRAY
        self.minor_v_axis_color_is_id: bool = False
        self.minor_h_axis_color: int = COLOR_DKGRAY
        self.minor_h_axis_color_is_id: bool = False

        self.major_v_axis_color: int = COLOR_GRAY
        self.major_v_axis_color_is_id: bool = False
        self.major_h_axis_color: int = COLOR_GRAY
        self.major_h_axis_color_is_id: bool = False

        self.minor_v_tick_size: float = 2.0
        self.minor_h_tick_size: float = 2.0
        self.major_v_tick_size: float = 4.0
        self.major_h_tick_size: float = 4.0

        self.v_axis_color: int = COLOR_YELLOW
        self.v_axis_color_is_id: bool = False
        self.h_axis_color: int = COLOR_YELLOW
        self.h_axis_color_is_id: bool = False
        self.axis_size: float = 4.0
        self.plot_color: int = COLOR_RED

    def set_v_minor_axis(self, paint):
        if self.minor_v_axis_color_is_id:
            paint.set_color_id(self.minor_v_axis_color)
        else:
            paint.set_color(self.minor_v_axis_color)
        paint.set_stroke_width(self.minor_v_tick_size)
        return paint

    def set_minor_axis(self, paint):
        if self.minor_h_axis_color_is_id:
            paint.set_color_id(self.minor_h_axis_color)
        else:
            paint.set_color(self.minor_h_axis_color)
        paint.set_stroke_width(self.minor_h_tick_size)
        return paint

    def set_v_major_axis(self, paint):
        if self.major_v_axis_color_is_id:
            paint.set_color_id(self.major_v_axis_color)
        else:
            paint.set_color(self.major_v_axis_color)
        paint.set_stroke_width(self.major_v_tick_size)
        return paint

    def set_major_h_axis(self, paint):
        if self.major_h_axis_color_is_id:
            paint.set_color_id(self.major_h_axis_color)
        else:
            paint.set_color(self.major_h_axis_color)
        paint.set_stroke_width(self.major_h_tick_size)
        return paint

    def set_v_axis(self, paint):
        if self.v_axis_color_is_id:
            paint.set_color_id(self.v_axis_color)
        else:
            paint.set_color(self.v_axis_color)
        paint.set_stroke_width(self.axis_size)
        return paint

    def set_h_axis(self, paint):
        if self.h_axis_color_is_id:
            paint.set_color_id(self.h_axis_color)
        else:
            paint.set_color(self.h_axis_color)
        paint.set_stroke_width(self.axis_size)
        return paint

    def set_plot_paint(self, paint, stroke_width=2.0):
        paint.set_shader(0)
        paint.set_color(self.plot_color)
        paint.set_style(STYLE_STROKE)
        paint.set_stroke_width(stroke_width)
        return paint

    def set_plot_fill(self, paint, start_x, start_y, end_x, end_y):
        paint.set_style(STYLE_FILL)
        paint.set_linear_gradient(
            _to_float(start_x), _to_float(start_y),
            _to_float(end_x), _to_float(end_y),
            [self.plot_color, 0x00],
            tile_mode=2,  # MIRROR
        )
        return paint


class Range:
    """Axis range with min/max for both X and Y."""

    def __init__(self, min_x: RFloat, max_x: RFloat,
                 min_y: RFloat, max_y: RFloat):
        self.min_x = min_x
        self.max_x = max_x
        self.min_y = min_y
        self.max_y = max_y


class PlotParams:
    """Computed plotting parameters (scales, offsets, insets)."""

    def __init__(self, prop: XYGraphProperties,
                 left: RFloat, top: RFloat,
                 right: RFloat, bottom: RFloat,
                 range_: Range):
        self.prop = prop
        self.left = left
        self.top = top
        self.right = right
        self.bottom = bottom
        self.data_x_min = range_.min_x
        self.data_x_max = range_.max_x
        self.data_y_max = range_.max_y
        self.data_y_min = range_.min_y
        self.x_range = (self.data_x_max - self.data_x_min).flush()
        self.y_range = (self.data_y_max - self.data_y_min).flush()
        pad = 0.05
        self.graph_max = (self.data_y_max + pad * self.y_range).flush()
        self.graph_min = (self.data_y_min - pad * self.y_range).flush()
        w = self.data_x_max.writer
        self.density = RFloat(w, Rc.System.DENSITY)
        self.insert_left = 30.0 * self.density
        self.insert_top = 10.0 * self.density
        self.insert_right = 10.0 * self.density
        self.insert_bottom = 50.0 * self.density
        # These are set by _axis()
        self.scale_x: RFloat = None
        self.scale_y: RFloat = None
        self.offset_x: RFloat = None
        self.offset_y: RFloat = None


class PlotBase:
    """Abstract base for plot types."""

    def calc_range(self, ctx) -> Range:
        raise NotImplementedError

    def plot(self, ctx, params: PlotParams):
        raise NotImplementedError


class FunctionPlot(PlotBase):
    """Plot a function expression (rFun result)."""

    def __init__(self, function: RFloat,
                 start_x, end_x, start_y, end_y):
        self.function = function
        w = function.writer
        self.start_x = start_x if isinstance(start_x, RFloat) else RFloat(w, float(start_x))
        self.end_x = end_x if isinstance(end_x, RFloat) else RFloat(w, float(end_x))
        self.start_y = start_y if isinstance(start_y, RFloat) else RFloat(w, float(start_y))
        self.end_y = end_y if isinstance(end_y, RFloat) else RFloat(w, float(end_y))

    def calc_range(self, ctx) -> Range:
        return Range(self.start_x, self.end_x, self.start_y, self.end_y)

    def plot(self, ctx, params: PlotParams):
        w = ctx.writer
        density = RFloat(w, Rc.System.DENSITY)
        params.prop.set_plot_paint(
            ctx.painter, _to_float(2.0 * density)).commit()

        exp_x = ctx.r_fun(lambda x: x * params.scale_x + params.offset_x)
        exp_y = self.function * params.scale_y + params.offset_y

        path_id = ctx.add_path_expression(
            exp_x.to_array(), exp_y.to_array(),
            params.data_x_min.to_float(), params.data_x_max.to_float(),
            128, Rc.PathExpression.LINEAR_PATH)
        ctx.draw_path(path_id)


class Plot(PlotBase):
    """Plot an array of data values."""

    def __init__(self, data: RFloat):
        self.data = data

    def calc_range(self, ctx) -> Range:
        w = self.data.writer
        min_x = RFloat(w, 0.0)
        max_x = rf_array_len(self.data).flush()
        max_y = rf_array_max(self.data).flush()
        min_y = rf_array_min(self.data).flush()
        return Range(min_x, max_x, min_y, max_y)

    def plot(self, ctx, params: PlotParams):
        self._plot_data(ctx, self.data, params)

    def _plot_data(self, ctx, values: RFloat, params: PlotParams):
        w = ctx.writer
        width = params.right - params.left
        height = params.bottom - params.top

        y = params.offset_y + params.scale_y * rf_array_spline(
            values, RFloat(w, 0.0))
        x = params.offset_x + params.scale_x * params.data_x_min
        path_id = ctx.path_create(_to_float(x), _to_float(y))

        with ctx.loop_range(0, 1, width) as xi:
            pos = xi / width
            yi = params.offset_y + params.scale_y * rf_array_spline(values, pos)
            x1 = params.offset_x + params.scale_x * (
                pos * params.x_range + params.data_x_min)
            ctx.path_append_line_to(path_id, _to_float(x1), _to_float(yi))

        # Draw the plot line
        params.prop.set_plot_paint(ctx.painter).commit()
        ctx.draw_path(path_id)

        # Close path for fill
        end_x = params.offset_x + params.scale_x * params.data_x_max
        start_x = params.offset_x + params.scale_x * params.data_x_min
        ctx.path_append_line_to(
            path_id, _to_float(end_x), _to_float(params.offset_y))
        ctx.path_append_line_to(
            path_id, _to_float(start_x), _to_float(params.offset_y))
        ctx.path_append_close(path_id)

        # Draw fill
        r_left = params.insert_left
        params.prop.set_plot_fill(
            ctx.painter, r_left, params.insert_top,
            r_left, params.offset_y).commit()
        ctx.draw_path(path_id)
        ctx.painter.set_shader(0).commit()


def _plot_increment(range_: RFloat, min_steps: int) -> RFloat:
    """Compute nice tick increment for an axis range."""
    max_inc = range_ / float(min_steps)
    n = max_inc.log().floor()
    power_of_10 = rf_pow(10.0, n)
    power_of_10.flush()
    norm_inc = max_inc / power_of_10
    ret = rf_if_else(
        norm_inc - 5.0,
        power_of_10 * 5.0,
        rf_if_else(norm_inc - 2.0, power_of_10 * 2.0, power_of_10))
    return rf_max(2.0, ret)


def _nice_increment(range_: RFloat, min_steps: int) -> RFloat:
    """Compute nice tick increment (no floor clamp)."""
    max_inc = range_ / float(min_steps)
    n = max_inc.log().floor()
    power_of_10 = rf_pow(10.0, n)
    power_of_10.flush()
    norm_inc = max_inc / power_of_10
    return rf_if_else(
        norm_inc - 5.0,
        power_of_10 * 5.0,
        rf_if_else(norm_inc - 2.0, power_of_10 * 2.0, power_of_10))


def _axis(ctx, params: PlotParams):
    """Draw axes, grid lines, and tick labels."""
    w = params.right - params.left
    h = params.bottom - params.top

    x_range = params.x_range
    y_range = params.y_range

    major_step_x = _plot_increment(x_range, 3)
    insert_x = params.insert_left
    insert_y = params.insert_bottom

    params.scale_x = ((w - params.insert_left - params.insert_right) / x_range).flush()
    params.offset_x = (insert_x - (params.data_x_min * params.scale_x)).flush()
    params.scale_y = ((params.insert_top + params.insert_bottom - h) / y_range).flush()
    params.offset_y = ((h - insert_y) - (params.scale_y * params.data_y_min)).flush()

    density = RFloat(ctx.writer, Rc.System.DENSITY)

    ctx.painter.set_color(COLOR_BLUE).set_text_size(
        _to_float(density * 16.0)).commit()
    params.prop.set_v_minor_axis(ctx.painter).commit()

    # Minor vertical grid
    minor_step_x = _plot_increment(x_range, 20)
    y1 = (params.data_y_min * params.scale_y + params.offset_y).flush()
    y2 = (params.data_y_max * params.scale_y + params.offset_y).flush()

    with ctx.loop_range(params.data_x_min.to_float(), _to_float(minor_step_x),
                        params.data_x_max.to_float()) as x:
        sx = x * params.scale_x + params.offset_x
        ctx.draw_line(_to_float(sx), y1.to_float(), _to_float(sx), y2.to_float())

    # Minor horizontal grid
    params.prop.set_minor_axis(ctx.painter).commit()
    minor_step_y = _nice_increment(y_range, 20)

    x1 = (params.data_x_min * params.scale_x + params.offset_x).flush()
    x2 = (params.data_x_max * params.scale_x + params.offset_x).flush()

    with ctx.loop_range(params.data_y_min.to_float(), _to_float(minor_step_y),
                        _to_float(params.data_y_max + 0.01)) as y:
        sy = y * params.scale_y + params.offset_y
        ctx.draw_line(x1.to_float(), _to_float(sy), x2.to_float(), _to_float(sy))

    # Major vertical grid + labels
    params.prop.set_v_major_axis(ctx.painter).commit()
    bottom = y1
    with ctx.loop_range(params.data_x_min.to_float(), _to_float(major_step_x),
                        _to_float(params.data_x_max + 0.01)) as x:
        pos_x = x * params.scale_x + params.offset_x
        tid = ctx.create_text_from_float(
            _to_float(x), 5, 1,
            Rc.TextFromFloat.PAD_AFTER_ZERO | Rc.TextFromFloat.PAD_PRE_NONE)
        ctx.draw_text_anchored(tid, _to_float(pos_x), bottom.to_float(),
                               0.0, 1.5, 0)
        ctx.draw_line(_to_float(pos_x), y1.to_float(),
                      _to_float(pos_x), y2.to_float())

    # Major horizontal grid + labels
    params.prop.set_major_h_axis(ctx.painter).commit()
    major_step_y = _nice_increment(y_range, 5)
    # Dead code in Kotlin — allocates an expression that is never used,
    # but must be present to keep expression IDs in sync.
    _end = (params.data_x_min * params.scale_x + params.offset_x).flush()

    with ctx.loop_range(params.data_y_min.to_float(), _to_float(major_step_y),
                        _to_float(params.data_y_max + 0.01)) as y:
        y_pos = y * params.scale_y + params.offset_y
        tid = ctx.create_text_from_float(
            _to_float(y), 5, 1,
            Rc.TextFromFloat.PAD_AFTER_ZERO | Rc.TextFromFloat.PAD_PRE_NONE)
        ctx.draw_text_anchored(tid, _to_float(insert_x), _to_float(y_pos),
                               1.5, 0.0, 0)
        ctx.draw_line(x1.to_float(), _to_float(y_pos),
                      x2.to_float(), _to_float(y_pos))

    # Draw axis lines
    params.prop.set_v_axis(ctx.painter).commit()
    ctx.draw_line(params.offset_x.to_float(), y1.to_float(),
                  params.offset_x.to_float(), y2.to_float())

    params.prop.set_h_axis(ctx.painter).commit()
    ctx.draw_line(x1.to_float(), params.offset_y.to_float(),
                  x2.to_float(), params.offset_y.to_float())


def rc_plot_xy(ctx, left, top, right, bottom,
               prop: XYGraphProperties = None,
               plot=None):
    """Plot XY data on a graph with axes.

    Args:
        ctx: RcContext
        left, top, right, bottom: graph bounds (RFloat or number)
        prop: XYGraphProperties (defaults to standard)
        plot: RFloat data array, PlotBase instance, or FunctionPlot
    """
    if prop is None:
        prop = XYGraphProperties()

    w = ctx.writer
    density = RFloat(w, Rc.System.DENSITY)
    margin = 2.0 * density

    # Convert to RFloat
    def _rf(v):
        if isinstance(v, RFloat):
            return v
        return RFloat(w, float(v))

    # If plot is a plain RFloat (data array), wrap in Plot
    if isinstance(plot, RFloat):
        plot = Plot(plot)

    left_r = _rf(left) + margin
    top_r = _rf(top) + margin
    right_r = _rf(right) - margin
    bottom_r = _rf(bottom) - margin

    params = PlotParams(prop, left_r, top_r, right_r, bottom_r,
                        plot.calc_range(ctx))

    ctx.canvas_save()
    ctx.translate(_to_float(params.left), _to_float(params.top))
    _axis(ctx, params)
    plot.plot(ctx, params)
    ctx.canvas_restore()

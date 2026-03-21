"""Port of RCPlayerInfo.kt info() — display system/time/sensor variables."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RcContext, Modifier
from rcreate.rc import Rc

PROFILE_ANDROIDX = 0x200


def _print_var_value(ctx, var_name, value, line, cx):
    """Print a variable name and its runtime value (4-arg printVar)."""
    var_value = ctx.create_text_from_float(value, 5, 5, Rc.TextFromFloat.PAD_PRE_NONE)
    flags = Rc.TextAnchorMask.BASELINE_RELATIVE | Rc.TextAnchorMask.MONOSPACE_MEASURE
    ctx.draw_text_anchored(var_name, cx, line, 1, 0, flags)
    ctx.draw_text_anchored(var_value, cx, line, -1, 0, flags)


def _print_var_header(ctx, var_name, line, cx):
    """Print a section header (3-arg printVar)."""
    flags = Rc.TextAnchorMask.BASELINE_RELATIVE | Rc.TextAnchorMask.MONOSPACE_MEASURE
    ctx.draw_text_anchored(var_name, cx, line, 0, 0, flags)


def demo_player_info():
    ctx = RcContext(500, 500, "Pressure Gauge",
                    api_level=7, profiles=PROFILE_ANDROIDX)
    with ctx.root():
        density = ctx.rf(Rc.System.DENSITY)
        ctx.add_debug_message("  density = ", density.to_float())

        with ctx.column(Modifier().vertical_scroll().fill_max_width()):
            with ctx.canvas(Modifier().fill_max_width().height(
                    (density * 18.0 * 35.0).to_float()).background(0xFFAABBCC)):
                ctx.add_debug_message("  density = ", density.to_float())

                centerX = ctx.windowWidth() / 2.0 + 100.0
                cx = centerX.to_float()
                line = ctx.rf(Rc.System.DENSITY) * 18.0

                font_size = ctx.rf(Rc.System.FONT_SIZE)
                fontScale = font_size / density / 14.0

                ctx.painter.set_color(0xFF000000).set_text_size(line.to_float()).commit()
                lineNo = 4.0

                _print_var_header(ctx, "System", (line * lineNo).to_float(), cx)
                lineNo += 1
                _print_var_value(ctx, "fontScale : ", fontScale.to_float(),
                                 (line * lineNo).to_float(), cx)
                lineNo += 1
                _print_var_value(ctx, "DENSITY : ", Rc.System.DENSITY,
                                 (line * lineNo).to_float(), cx)
                lineNo += 1
                _print_var_value(ctx, "FONT_SIZE : ", Rc.System.FONT_SIZE,
                                 (line * lineNo).to_float(), cx)
                lineNo += 1
                _print_var_value(ctx, "API_LEVEL : ", Rc.System.API_LEVEL,
                                 (line * lineNo).to_float(), cx)
                lineNo += 1
                _print_var_value(ctx, "WINDOW_HEIGHT : ", Rc.System.WINDOW_HEIGHT,
                                 (line * lineNo).to_float(), cx)
                lineNo += 1
                _print_var_value(ctx, "WINDOW_HEIGHT : ", Rc.System.WINDOW_WIDTH,
                                 (line * lineNo).to_float(), cx)
                lineNo += 1
                _print_var_header(ctx, "Time", (line * lineNo).to_float(), cx)
                lineNo += 1

                _print_var_value(ctx, "TIME_IN_SEC : ", Rc.Time.TIME_IN_SEC,
                                 (line * lineNo).to_float(), cx)
                lineNo += 1
                _print_var_value(ctx, "TIME_IN_MIN : ", Rc.Time.TIME_IN_MIN,
                                 (line * lineNo).to_float(), cx)
                lineNo += 1
                _print_var_value(ctx, "TIME_IN_HR : ", Rc.Time.TIME_IN_HR,
                                 (line * lineNo).to_float(), cx)
                lineNo += 1
                _print_var_value(ctx, "DAY_OF_YEAR : ", Rc.Time.DAY_OF_YEAR,
                                 (line * lineNo).to_float(), cx)
                lineNo += 1
                _print_var_value(ctx, "CALENDAR_MONTH : ", Rc.Time.CALENDAR_MONTH,
                                 (line * lineNo).to_float(), cx)
                lineNo += 1
                _print_var_value(ctx, "WEEK_DAY : ", Rc.Time.WEEK_DAY,
                                 (line * lineNo).to_float(), cx)
                lineNo += 1
                _print_var_value(ctx, "YEAR : ", Rc.Time.YEAR,
                                 (line * lineNo).to_float(), cx)
                lineNo += 1
                _print_var_value(ctx, "OFFSET_TO_UTC : ", Rc.Time.OFFSET_TO_UTC,
                                 (line * lineNo).to_float(), cx)
                lineNo += 1
                _print_var_value(ctx, "CONTINUOUS_SEC : ", Rc.Time.CONTINUOUS_SEC,
                                 (line * lineNo).to_float(), cx)
                lineNo += 1
                _print_var_value(ctx, "ANIMATION_TIME : ", Rc.Time.ANIMATION_TIME,
                                 (line * lineNo).to_float(), cx)
                lineNo += 1
                _print_var_value(ctx, "ANIMATION_DELTA_TIME : ", Rc.Time.ANIMATION_DELTA_TIME,
                                 (line * lineNo).to_float(), cx)
                lineNo += 1
                _print_var_header(ctx, "Sensors", (line * lineNo).to_float(), cx)
                lineNo += 1
                _print_var_value(ctx, "ACCELERATION_X : ", Rc.Sensor.ACCELERATION_X,
                                 (line * lineNo).to_float(), cx)
                lineNo += 1
                _print_var_value(ctx, "ACCELERATION_Y : ", Rc.Sensor.ACCELERATION_Y,
                                 (line * lineNo).to_float(), cx)
                lineNo += 1
                _print_var_value(ctx, "ACCELERATION_Z : ", Rc.Sensor.ACCELERATION_Z,
                                 (line * lineNo).to_float(), cx)
                lineNo += 1
                _print_var_value(ctx, "GYRO_ROT_X : ", Rc.Sensor.GYRO_ROT_X,
                                 (line * lineNo).to_float(), cx)
                lineNo += 1
                _print_var_value(ctx, "GYRO_ROT_Y : ", Rc.Sensor.GYRO_ROT_Y,
                                 (line * lineNo).to_float(), cx)
                lineNo += 1
                _print_var_value(ctx, "GYRO_ROT_Z : ", Rc.Sensor.GYRO_ROT_Z,
                                 (line * lineNo).to_float(), cx)
                lineNo += 1
                _print_var_value(ctx, "MAGNETIC_X : ", Rc.Sensor.MAGNETIC_X,
                                 (line * lineNo).to_float(), cx)
                lineNo += 1
                _print_var_value(ctx, "MAGNETIC_Y : ", Rc.Sensor.MAGNETIC_Y,
                                 (line * lineNo).to_float(), cx)
                lineNo += 1
                _print_var_value(ctx, "MAGNETIC_Z : ", Rc.Sensor.MAGNETIC_Z,
                                 (line * lineNo).to_float(), cx)
                lineNo += 1
                _print_var_value(ctx, "LIGHT : ", Rc.Sensor.LIGHT,
                                 (line * lineNo).to_float(), cx)
    return ctx


if __name__ == '__main__':
    ctx = demo_player_info()
    data = ctx.encode()
    outdir = os.path.join(os.path.dirname(__file__), '..', 'output')
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, 'player_info.rc')
    ctx.save(path)
    print(f"player_info: {len(data)} bytes -> {path}")

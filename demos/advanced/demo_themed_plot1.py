"""Port of plot1() from Demo.kt -> themed_plot1.rc

Target .rc file:
  - themed_plot1.rc -> demo_themed_plot1()
"""
import sys
import os
import struct

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RcContext, Modifier, Rc
from rcreate.modifiers import RecordingModifier
from rcreate.types.rfloat import RFloat, rf_sin
from rcreate.types.nan_utils import int_bits_to_float

FE = Rc.FloatExpression
PROFILE_ANDROIDX = 0x200
PROFILE_EXPERIMENTAL = 0x1
STYLE_FILL = Rc.Paint.STYLE_FILL
STYLE_STROKE = Rc.Paint.STYLE_STROKE


def _dash(phase, *intervals):
    """PaintPathEffects.dash(phase, *intervals) encoding.

    Creates: [int_bits_to_float(DASH=1), phase, int_bits_to_float(len), ...intervals]
    """
    return [int_bits_to_float(1), phase,
            int_bits_to_float(len(intervals))] + list(intervals)


def demo_themed_plot1():
    """Port of plot1() from Demo.kt -> themed_plot1.rc.

    V7+ format, apiLevel=7, profiles=PROFILE_ANDROIDX|PROFILE_EXPERIMENTAL.
    """
    ctx = RcContext(500, 500, "Simple Timer", api_level=7,
                    profiles=PROFILE_ANDROIDX | PROFILE_EXPERIMENTAL)

    # Themed colors are added BEFORE root (matches Kotlin order)
    background_id = ctx.writer.add_themed_color(
        "color.system_accent2_10", 0xFFDDDDDD,
        "color.system_accent2_900", 0xFF222222)
    title_id = ctx.writer.add_themed_color(
        "color.system_neutral1_900", 0xFF111111,
        "color.system_neutral1_50", 0xFF111111)
    axis_id = ctx.writer.add_themed_color(
        "color.system_neutral2_200", 0xFF999999,
        "color.system_neutral2_700", 0xFF999999)
    curve_id = ctx.writer.add_themed_color(
        "color.system_accent1_100", 0xFF994422,
        "color.system_accent1_500", 0xFF994422)

    with ctx.root():
        with ctx.box(RecordingModifier().fill_max_size(),
                     Rc.Layout.START, Rc.Layout.START):
            with ctx.canvas(RecordingModifier().fill_max_size()
                            .background(0xFF99AAFF)):
                ctx.painter.set_color_id(background_id) \
                    .set_text_size(64.0).commit()
                ctx.draw_rect(
                    20.0, 20.0,
                    (ctx.ComponentWidth() - 20.0).to_float(),
                    (ctx.ComponentHeight() - 20.0).to_float())

                minX = -10.0
                maxX = 10.0
                scale = ((ctx.Seconds() / 2.0) % 2.0 + 1.0).anim(0.5)
                scaleY = scale * (ctx.ComponentHeight() - 100.0) / -10.0
                offsetY = ctx.ComponentHeight() / 2.0
                scaleX = (ctx.ComponentWidth() - 100.0) / (maxX - minX)
                offsetX = 50.0 - minX * scaleX
                tid = scale.gen_text_id(1, 1)
                ctx.draw_text_anchored(
                    tid,
                    (ctx.ComponentWidth() / 2.0).to_float(),
                    100.0, 0, 0, 0)
                ctx.painter.set_stroke_width(10.0) \
                    .set_style(STYLE_STROKE).commit()
                equ = ctx.r_fun(
                    lambda x: (x + ctx.ContinuousSec() * 3.0).sin())

                ctx.painter.set_color_id(curve_id).commit()

                path_id = ctx.add_path_expression(
                    ctx.r_fun(lambda x: x * scaleX + offsetX).to_array(),
                    (equ * scaleY + offsetY).to_array(),
                    minX, maxX, 64, Rc.PathExpression.SPLINE_PATH)
                ctx.draw_path(path_id)

                # Touch expression: TOUCH_POS_X / scaleX
                # Evaluate scaleX without flushing the RFloat object
                # (Kotlin's Float.times(RFloat) uses v.array directly, not toArray)
                scaleX_val = ctx._writer.float_expression(*scaleX.to_array())
                touchX = ctx.touch_expression(
                    Rc.Touch.POSITION_X,
                    scaleX_val,
                    FE.DIV,
                    def_value=(minX + maxX) / 2,
                    min_val=minX,
                    max_val=maxX,
                    touch_mode=Rc.Touch.STOP_INSTANTLY)

                # touchX is a plain float (NaN-encoded ID)
                # Use list constructor so _id stays 0 (matches Kotlin Float behavior)
                touchX_rf = RFloat(ctx._writer, [touchX])
                sPos = touchX_rf * scaleX + offsetX
                ctx.painter.set_color_id(axis_id) \
                    .set_stroke_width(3.0) \
                    .set_path_effect(_dash(0.0, 10.0, 10.0)) \
                    .commit()

                ctx.draw_line(sPos.to_float(), 0,
                              sPos.to_float(),
                              ctx.ComponentHeight().to_float())

                value = (RFloat(ctx._writer, [touchX])
                         + ctx.ContinuousSec() * 3.0).sin().gen_text_id(0, 2)
                mx = (RFloat(ctx._writer, [touchX])
                      * scaleX + offsetX).flush()
                my = ((RFloat(ctx._writer, [touchX])
                       + ctx.ContinuousSec() * 3.0).sin()
                      * scaleY + offsetY)
                deltaX = (100.0
                           * (mx - ctx.ComponentHeight() / 2.0).sign()
                           ).anim(0.5)
                cx = mx - deltaX
                cy = (my + ctx.ComponentHeight()) / 2.0
                ctx.painter.set_color_id(axis_id) \
                    .set_style(STYLE_FILL) \
                    .set_path_effect(None) \
                    .commit()

                ctx.draw_line(mx.to_float(), my.to_float(),
                              cx.to_float(), cy.to_float())
                width = ctx.text_attribute(value,
                                           Rc.TextAttribute.MEASURE_WIDTH)
                ctx.draw_round_rect(
                    (cx - 64 * 2).to_float(),
                    (cy - 32.0).to_float(),
                    (cx + 64 * 2).to_float(),
                    (cy + 32.0).to_float(),
                    10.0, 10)
                ctx.painter.set_color_id(title_id) \
                    .set_path_effect(None).commit()

                ctx.draw_text_anchored(value,
                                       cx.to_float(), cy.to_float(),
                                       0, 0, 0)

    return ctx


if __name__ == '__main__':
    ctx = demo_themed_plot1()
    data = ctx.encode()
    outdir = os.path.join(os.path.dirname(__file__), '..', 'output')
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, 'themed_plot1.rc')
    ctx.save(path)
    print(f"themed_plot1: {len(data)} bytes -> {path}")

    ref_dir = os.path.join(os.path.dirname(__file__), '..', '..',
                           'integration-tests', 'player-view-demos',
                           'src', 'main', 'res', 'raw')
    ref_path = os.path.join(ref_dir, 'themed_plot1.rc')
    if os.path.exists(ref_path):
        ref_data = open(ref_path, 'rb').read()
        if data == ref_data:
            print("MATCH: byte-identical")
        else:
            print(f"DIFF: gen={len(data)} ref={len(ref_data)}")
            for i in range(min(len(data), len(ref_data))):
                if data[i] != ref_data[i]:
                    print(f"  First diff at byte {i}: gen=0x{data[i]:02x} ref=0x{ref_data[i]:02x}")
                    # Show context
                    start = max(0, i - 4)
                    end = min(len(data), i + 8)
                    print(f"  gen[{start}:{end}]: {data[start:end].hex()}")
                    end_r = min(len(ref_data), i + 8)
                    print(f"  ref[{start}:{end_r}]: {ref_data[start:end_r].hex()}")
                    break

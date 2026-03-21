"""Port of MClock() from MClock.kt -> clock.rc

Target .rc file:
  - clock.rc -> demo_clock()
"""
import sys
import os
import math

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RcContext, Modifier, Rc
from rcreate.modifiers import RecordingModifier
from rcreate.types.rfloat import RFloat, rf_min, rf_cos


PROFILE_ANDROIDX = 0x200
STYLE_FILL = Rc.Paint.STYLE_FILL
STYLE_STROKE = Rc.Paint.STYLE_STROKE
CAP_ROUND = Rc.Paint.CAP_ROUND


def _add_themed_color(ctx, light_name, light_value, dark_name, dark_value):
    """Equivalent to MClockColorPack property getter:
    rc.beginGlobal()
    val color = rc.writer.addThemedColor(lightName, lightValue, darkName, darkValue)
    rc.endGlobal()
    return color
    """
    ctx.begin_global()
    color_id = ctx.writer.add_themed_color(light_name, light_value,
                                           dark_name, dark_value)
    ctx.end_global()
    return color_id


def demo_clock():
    """Port of MClock() from MClock.kt -> clock.rc.

    V7+ format, apiLevel=7, profiles=PROFILE_ANDROIDX.
    """
    ctx = RcContext(500, 500, "Simple Timer", api_level=7,
                    profiles=PROFILE_ANDROIDX)

    with ctx.root():
        day_names_id = ctx.add_string_list("Mon", "Tue", "Wed", "Thu",
                                           "Fri", "Sat", "Sun")
        # val day: Int = textLookup(dayNamesId, (DayOfWeek() - 1).toFloat())
        day = ctx.text_lookup(day_names_id,
                              (ctx.DayOfWeek() - 1.0).to_float())
        # val dom = createTextFromFloat(DayOfMonth(), 2, 0, 0)
        dom = ctx.create_text_from_float(ctx.DayOfMonth().to_float(),
                                         2, 0, 0)
        # val date = textMerge(day, dom)
        date = ctx.text_merge(day, dom)

        with ctx.box(RecordingModifier().fill_max_size(),
                     Rc.Layout.START, Rc.Layout.START):
            with ctx.canvas(RecordingModifier().fill_max_size()):
                minX = 0
                maxX = math.pi * 2.0
                w = ctx.ComponentWidth()
                h = ctx.ComponentHeight()
                cx = (w / 2.0).flush()
                cy = (h / 2.0).flush()
                # Kotlin free min(a,b) uses a.array directly (not toArray),
                # so even flushed RFloats use their full expression arrays.
                rad = RFloat(cx.writer,
                             list(cx.array) + list(cy.array) +
                             [Rc.FloatExpression.MIN])
                rad.flush()
                stroke_width = (rad / 6.0).to_float()
                equ = ctx.r_fun(
                    lambda x: rad * (0.97 + 0.03 * rf_cos(x * 12.0)))

                text_size = rad / 5.0  # RFloat, NOT flushed yet

                # painter.setColorId(color.backgroundId.toInt())
                # In Kotlin, accessing color.backgroundId triggers the
                # themed color getter (beginGlobal + addThemedColor + endGlobal).
                # textSize.toFloat() is called AFTER, during setTextSize.
                background_id = _add_themed_color(
                    ctx,
                    "color.system_accent2_50", 0xFF113311 & 0xFFFFFFFF,
                    "color.system_accent2_800", 0xFFFF9966 & 0xFFFFFFFF)
                ctx.painter.set_color_id(background_id) \
                    .set_text_size(text_size.to_float()).commit()

                # addPolarPathExpression(equ, minX, maxX, 64, ...)
                path_id = ctx.add_polar_path_expression(
                    equ.to_array(),
                    minX, maxX, 64,
                    cx.to_float(), cy.to_float(),
                    Rc.PathExpression.SPLINE_PATH)
                ctx.draw_path(path_id)

                # Hr hand
                hr_id = _add_themed_color(
                    ctx,
                    "color.system_accent2_700", 0xFF113311 & 0xFFFFFFFF,
                    "color.system_accent2_400", 0xFFFF9966 & 0xFFFFFFFF)
                ctx.painter.set_color_id(hr_id) \
                    .set_stroke_width(stroke_width) \
                    .set_stroke_cap(CAP_ROUND).commit()

                # val hrHand = (Hour() + (Minutes() % 60f) / 60f) * 30f
                hr_hand = (ctx.Hour() + (ctx.Minutes() % 60.0) / 60.0) * 30.0

                with ctx.saved():
                    ctx.rotate(hr_hand.to_float(),
                               cx.to_float(), cy.to_float())
                    ctx.draw_line(cx.to_float(), cy.to_float(),
                                 cx.to_float(),
                                 (cy - rad / 3.0).to_float())

                # Minute hand
                minutes_color_id = _add_themed_color(
                    ctx,
                    "color.system_accent1_500", 0xFF113311 & 0xFFFFFFFF,
                    "color.system_accent1_100", 0xFFFF9966 & 0xFFFFFFFF)
                ctx.painter.set_color_id(minutes_color_id) \
                    .set_stroke_width(stroke_width) \
                    .set_stroke_cap(CAP_ROUND).commit()

                with ctx.saved():
                    ctx.rotate((ctx.Minutes() * 6.0).to_float(),
                               cx.to_float(), cy.to_float())
                    ctx.draw_line(cx.to_float(), cy.to_float(),
                                 cx.to_float(),
                                 (cy - rad * 0.6).to_float())

                # textPath polar path expression for text
                text_path = ctx.add_polar_path_expression(
                    ctx.r_fun(lambda y: rad * 0.7).to_array(),
                    minX, maxX, 64,
                    cx.to_float(), cy.to_float(),
                    Rc.PathExpression.SPLINE_PATH)

                with ctx.saved():
                    ctx.rotate((ctx.Seconds() * 6.0).to_float(),
                               cx.to_float(), cy.to_float())
                    radius = rad * 0.1

                    # Dot
                    dot_color_id = _add_themed_color(
                        ctx,
                        "color.system_accent3_500", 0xFF113311 & 0xFFFFFFFF,
                        "color.system_accent3_100", 0xFFFF9966 & 0xFFFFFFFF)
                    ctx.painter.set_style(STYLE_FILL) \
                        .set_color_id(dot_color_id).commit()
                    ctx.draw_circle(cx.to_float(),
                                   (cy - rad + (2.0 * radius)).to_float(),
                                   radius.to_float())

                    ctx.rotate(70.0, cx.to_float(), cy.to_float())

                    # Text on path
                    text_color_id = _add_themed_color(
                        ctx,
                        "color.system_on_surface_light", 0xFF113311 & 0xFFFFFFFF,
                        "color.system_on_surface_dark", 0xFFFF9966 & 0xFFFFFFFF)
                    ctx.painter.set_color_id(text_color_id).commit()
                    ctx.draw_text_on_path(date, text_path, 0.0, 0.0)

                # Version text: writer.createTextFromFloat(FLOAT_API_LEVEL, 2, 2, 0)
                version_id = ctx.writer.create_text_from_float(
                    Rc.System.API_LEVEL, 2, 2, 0)
                ctx.draw_text_anchored(version_id,
                                       cx.to_float(),
                                       ((cy + h) / 2.0).to_float(),
                                       0, 0, 0)

    return ctx


if __name__ == '__main__':
    ctx = demo_clock()
    data = ctx.encode()
    outdir = os.path.join(os.path.dirname(__file__), '..', 'output')
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, 'clock.rc')
    ctx.save(path)
    print(f"clock: {len(data)} bytes -> {path}")

    ref_dir = os.path.join(os.path.dirname(__file__), '..', '..',
                           'integration-tests', 'player-view-demos',
                           'src', 'main', 'res', 'raw')
    ref_path = os.path.join(ref_dir, 'clock.rc')
    if os.path.exists(ref_path):
        ref_data = open(ref_path, 'rb').read()
        if data == ref_data:
            print("MATCH: byte-identical")
        else:
            print(f"DIFF: gen={len(data)} ref={len(ref_data)}")
            # Find first difference
            for i in range(min(len(data), len(ref_data))):
                if data[i] != ref_data[i]:
                    print(f"  First diff at byte {i}: gen=0x{data[i]:02x} ref=0x{ref_data[i]:02x}")
                    break

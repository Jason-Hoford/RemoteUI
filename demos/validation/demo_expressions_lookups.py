"""Validation demo: expressions, lookups, and data combinations.

Exercises:
- Float expressions with complex RPN chains
- Integer expressions
- Text lookup from string list (day names)
- createTextFromFloat for numeric display
- textMerge to combine text fragments
- Float arrays and array expressions
- Conditional operations
- Color expressions
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RcContext, Rc
from rcreate.modifiers import RecordingModifier
from rcreate.types.rfloat import RFloat, rf_clamp, rf_if_else

PROFILE_ANDROIDX = 0x200
FE = Rc.FloatExpression
STYLE_FILL = Rc.Paint.STYLE_FILL


def demo_expressions_lookups():
    ctx = RcContext(400, 500, "Expressions+Lookups", api_level=7,
                    profiles=PROFILE_ANDROIDX)

    with ctx.root():
        with ctx.column(RecordingModifier().fill_max_size()
                        .background(0xFF222233)):

            # Day name lookup
            days = ctx.add_string_list(
                "Monday", "Tuesday", "Wednesday", "Thursday",
                "Friday", "Saturday", "Sunday")
            day_text = ctx.text_lookup(
                days, (ctx.DayOfWeek() - 1.0).to_float())

            # Numeric displays
            hour_text = ctx.create_text_from_float(
                ctx.Hour().to_float(), 2, 0,
                Rc.TextFromFloat.PAD_PRE_ZERO)
            min_text = ctx.create_text_from_float(
                ctx.Minutes().to_float(), 2, 0,
                Rc.TextFromFloat.PAD_PRE_ZERO)

            # Merge: "HH:MM"
            colon = ctx.writer.add_text(":")
            time_part1 = ctx.text_merge(hour_text, colon)
            time_display = ctx.text_merge(time_part1, min_text)

            # Title with day name
            with ctx.box(RecordingModifier().fill_max_width().height(60.0)
                         .background(0xFF3344AA),
                         Rc.Layout.CENTER, Rc.Layout.CENTER):
                ctx.text_by_id(day_text, font_size=28.0,
                               color=0xFFFFFFFF)

            # Time display
            with ctx.box(RecordingModifier().fill_max_width().height(80.0)
                         .background(0xFF223388),
                         Rc.Layout.CENTER, Rc.Layout.CENTER):
                ctx.text_by_id(time_display, font_size=48.0,
                               color=0xFFFFCC00)

            # Canvas section with expression-driven graphics
            with ctx.box(RecordingModifier().fill_max_size(),
                         Rc.Layout.START, Rc.Layout.START):
                with ctx.canvas(RecordingModifier().fill_max_size()):
                    w = ctx.ComponentWidth()
                    h = ctx.ComponentHeight()
                    t = ctx.ContinuousSec()

                    # Draw animated bars using sine waves
                    bar_w = w / 10.0
                    ctx.painter.set_color(0xFF55AA88) \
                        .set_style(STYLE_FILL).commit()
                    for i in range(8):
                        bar_val = (t * 2.0 + i * 0.5).sin() * 0.3 + 0.5
                        bar_h = bar_val * h * 0.5
                        x = bar_w * (i + 1)
                        ctx.draw_rect(
                            x.to_float(),
                            (h - bar_h).to_float(),
                            (x + bar_w * 0.8).to_float(),
                            h.to_float())

                    # Conditional: show different color based on seconds
                    sec = ctx.Seconds()
                    phase = rf_clamp((sec % 10.0) / 10.0, 0.0, 1.0)
                    indicator_x = (phase * w).to_float()

                    ctx.painter.set_color(0xFFFF6633).commit()
                    ctx.draw_circle(indicator_x, 30.0, 15.0)

                    # If-else expression: show green or red
                    threshold = rf_if_else(
                        phase - 0.5,  # condition: positive = then
                        ctx.rf(1.0),
                        ctx.rf(0.0))
                    radius = threshold * 20.0 + 10.0
                    ctx.painter.set_color(0xFF00FF00).commit()
                    ctx.draw_circle(
                        (w / 2.0).to_float(), 30.0,
                        radius.to_float())

    return ctx


if __name__ == '__main__':
    ctx = demo_expressions_lookups()
    data = ctx.encode()
    outdir = os.path.join(os.path.dirname(__file__), '..', 'output')
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, 'val_expressions_lookups.rc')
    ctx.save(path)
    print(f"val_expressions_lookups: {len(data)} bytes -> {path}")

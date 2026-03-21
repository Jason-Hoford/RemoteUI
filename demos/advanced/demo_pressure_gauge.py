"""Port of PressureGauge.kt — circular pressure gauge demo."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RcContext, Modifier, DEMO7_TAG_ORDER
from rcreate.rc import Rc

WHITE = 0xFFFFFFFF
PROFILE_ANDROIDX = 0x200
STYLE_STROKE = Rc.Paint.STYLE_STROKE
STYLE_FILL = Rc.Paint.STYLE_FILL
CAP_BUTT = 0
CAP_ROUND = 1


def demo_pressure_gauge():
    ctx = RcContext(500, 500, "Pressure Gauge",
                    api_level=7, profiles=PROFILE_ANDROIDX,
                    header_tag_order=DEMO7_TAG_ORDER)
    with ctx.root():
        with ctx.canvas(Modifier().fill_max_size().background(0xFF4A6DA7)):
            w = ctx.ComponentWidth()
            h = ctx.ComponentHeight()
            cx = w / 2.0
            cy = h / 2.0
            density = ctx.rf(Rc.System.DENSITY)
            radius = w.min(h) / 2.0
            pressure = ctx.ContinuousSec().sin() * 50.0 + 750.0
            delta_pressure = ctx.ContinuousSec().cos()
            max_pressure = 800.0
            min_pressure = 700.0

            ctx.painter.set_color(0xFF6A8DC7).set_text_size(
                (density * 24.0).to_float()).commit()
            ctx.draw_text_anchored("PRESSURE", 50.0, 40.0, -1, 1, 0)

            ctx.painter.set_style(STYLE_STROKE).set_stroke_width(
                (density * 6.0).to_float()).commit()
            dial_y = cy + radius * 0.1
            dial_radius = radius * 0.8
            tick_length = radius * 0.2

            # Draw a sweep of ticks
            with ctx.saved():
                ctx.rotate(-135, cx.to_float(), dial_y.to_float())
                with ctx.loop_range(0, 5, 265) as angle:
                    ctx.rotate(5, cx.to_float(), dial_y.to_float())
                    ctx.draw_line(
                        cx.to_float(),
                        (dial_y - dial_radius + tick_length).to_float(),
                        cx.to_float(),
                        (dial_y - dial_radius).to_float())

            # convert pressure to angle
            pressure_angle = (
                (pressure - min_pressure) / (max_pressure - min_pressure)
                * 270.0 - 135.0
            )

            # draw a motion blur gradient
            ctx.painter.set_sweep_gradient(
                cx.to_float(), dial_y.to_float(),
                [0x00FFFFFF, 0x99FFFFFF, 0x00FFFFFF],
                [0.01, 0.05, 0.09]
            ).set_style(STYLE_STROKE).set_stroke_width(
                tick_length.to_float()
            ).set_stroke_cap(CAP_BUTT).commit()
            gap = 18.0
            draw_radius = dial_radius - tick_length / 2.0
            with ctx.saved():
                ctx.rotate(
                    (pressure_angle - 90.0 - gap).to_float(),
                    cx.to_float(), dial_y.to_float())
                ctx.draw_arc(
                    (cx - draw_radius).to_float(),
                    (dial_y - draw_radius).to_float(),
                    (cx + draw_radius).to_float(),
                    (dial_y + draw_radius).to_float(),
                    gap,
                    (delta_pressure * (-30.0 + gap)).to_float())

            # Draw the line
            ctx.painter.set_shader(0).set_color(WHITE).set_style(
                STYLE_STROKE).set_stroke_width(
                (density * 8.0).to_float()
            ).set_stroke_cap(CAP_ROUND).commit()
            with ctx.saved():
                ctx.rotate(
                    pressure_angle.to_float(),
                    cx.to_float(), dial_y.to_float())
                ctx.draw_line(
                    cx.to_float(),
                    (dial_y - dial_radius + tick_length).to_float(),
                    cx.to_float(),
                    (dial_y - dial_radius).to_float())

            ctx.painter.set_shader(0).set_text_size(
                (density * 64.0).to_float()
            ).set_color(0xFFFFFFFF).set_style(
                STYLE_FILL).set_stroke_width(0.0).commit()

            # draw arrow based on pressure direction
            ctx.conditional_operations(
                Rc.Condition.LT, 0.0, delta_pressure.to_float())
            ctx.draw_text_anchored(
                "\u2191", cx.to_float(), dial_y.to_float(), 0, -3, 0)
            ctx.end_conditional_operations()

            ctx.conditional_operations(
                Rc.Condition.GTE, 0.0, delta_pressure.to_float())
            ctx.draw_text_anchored(
                "\u2193", cx.to_float(), dial_y.to_float(), 0, -3, 0)
            ctx.end_conditional_operations()

            # Draw the text pressure
            text_id = ctx.create_text_from_float(
                pressure.to_float(), 3, 0, Rc.TextFromFloat.PAD_AFTER_ZERO)
            ctx.draw_text_anchored(
                text_id, cx.to_float(), dial_y.to_float(), 0, 0, 0)

            # draw labels
            ctx.painter.set_text_size((density * 32.0).to_float()).commit()
            ctx.draw_text_anchored(
                "mmHg", cx.to_float(), dial_y.to_float(), 0, 4, 0)
            ctx.draw_text_anchored(
                "Low",
                (cx - dial_radius * 0.6).to_float(),
                (dial_y + dial_radius * 0.9).to_float(),
                0, 0, 0)
            ctx.draw_text_anchored(
                "High",
                (cx + dial_radius * 0.6).to_float(),
                (dial_y + dial_radius * 0.9).to_float(),
                0, 0, 0)
    return ctx


if __name__ == '__main__':
    ctx = demo_pressure_gauge()
    data = ctx.encode()
    print(f"PressureGauge: {len(data)} bytes")
    ctx.save("pressure_gauge.rc")

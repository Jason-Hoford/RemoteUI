"""Bar chart from data -> bar_chart.rc

A horizontal bar chart driven by a Python data list. Demonstrates how a
single Python script generates a bespoke `.rc` from arbitrary data —
the foundation of the "make 50 election diagrams from this dataset"
generation pattern.

Each bar's color, width, and label are computed from the data list at
generation time and baked into the `.rc` as static draw operations.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RcContext, Rc
from rcreate.modifiers import RecordingModifier


PROFILE_ANDROIDX = 0x200
STYLE_FILL = Rc.Paint.STYLE_FILL


# Sample data — could be loaded from CSV/JSON in a real generator.
DATA = [
    ("Mon",  72),
    ("Tue",  85),
    ("Wed",  61),
    ("Thu",  93),
    ("Fri",  78),
    ("Sat",  44),
    ("Sun",  29),
]


def demo_bar_chart():
    ctx = RcContext(500, 400, "Bar Chart",
                    api_level=7, profiles=PROFILE_ANDROIDX)

    # Layout constants
    margin_left = 70.0
    margin_right = 30.0
    margin_top = 50.0
    margin_bottom = 80.0
    chart_width = 500.0 - margin_left - margin_right   # 400
    chart_height = 400.0 - margin_top - margin_bottom  # 270

    bar_count = len(DATA)
    bar_gap = 10.0
    bar_width = (chart_width - bar_gap * (bar_count - 1)) / bar_count

    max_value = max(v for _, v in DATA)
    floor_y = margin_top + chart_height

    with ctx.root():
        with ctx.box(RecordingModifier().fill_max_size().background(0xFF111827),
                     Rc.Layout.START, Rc.Layout.START):
            with ctx.canvas(RecordingModifier().fill_max_size()):
                # Background panel
                ctx.painter.set_color(0xFF1F2937) \
                    .set_style(STYLE_FILL).commit()
                ctx.draw_rect(margin_left - 10.0, margin_top - 10.0,
                              margin_left + chart_width + 10.0,
                              floor_y + 10.0)

                # Y-axis baseline
                ctx.painter.set_color(0xFF4B5563).commit()
                ctx.draw_rect(margin_left - 2.0, floor_y - 1.0,
                              margin_left + chart_width, floor_y + 1.0)

                # Bars — each bar's height is proportional to its value
                bar_palette = [
                    0xFF60A5FA, 0xFF34D399, 0xFFFBBF24, 0xFFEF4444,
                    0xFFA78BFA, 0xFFF472B6, 0xFF22D3EE,
                ]
                for i, (label, value) in enumerate(DATA):
                    x0 = margin_left + i * (bar_width + bar_gap)
                    x1 = x0 + bar_width
                    h = (value / max_value) * chart_height
                    y0 = floor_y - h
                    y1 = floor_y

                    color = bar_palette[i % len(bar_palette)]
                    ctx.painter.set_color(color) \
                        .set_style(STYLE_FILL).commit()
                    ctx.draw_rect(x0, y0, x1, y1)

                # Title bar — tiny accent line at the top
                ctx.painter.set_color(0xFF38BDF8).commit()
                ctx.draw_rect(margin_left, margin_top - 28.0,
                              margin_left + 60.0, margin_top - 22.0)

    return ctx


if __name__ == '__main__':
    ctx = demo_bar_chart()
    data = ctx.encode()
    outdir = os.path.join(os.path.dirname(__file__), '..', 'output')
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, 'bar_chart.rc')
    ctx.save(path)
    print(f"bar_chart: {len(data)} bytes -> {path}")
    print(f"  data points: {len(DATA)}, max value: {max(v for _, v in DATA)}")

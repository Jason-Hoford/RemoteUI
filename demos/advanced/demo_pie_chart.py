"""Port of PieChart.kt — Pie Chart demos using procedural creation APIs.

Target .rc files:
  - good_pie_chart.rc -> demo_pie_chart_good()
  - pie_chart.rc      -> demo_pie_chart()
  - pie_chart2.rc     -> demo_pie_chart2()
"""
import sys
import os
import math
import struct

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RcContext, Modifier, Rc
from rcreate.types.rfloat import RFloat, rf_array_len, rf_array_sum

STYLE_FILL = Rc.Paint.STYLE_FILL
STYLE_STROKE = Rc.Paint.STYLE_STROKE

# Android Color constants
BLACK = 0xFF000000
WHITE = 0xFFFFFFFF


def _f32(x):
    """Truncate a Python double to float32 precision (matches Kotlin float)."""
    return struct.unpack('>f', struct.pack('>f', x))[0]


def _get_distributed_color(ctx, i, alpha, sat, value):
    """Port of getDistributedColor extension function.

    Computes a color from the golden-ratio-distributed hue.
    """
    golden_ratio_conjugate = 0.618033988749895
    hue = (i * golden_ratio_conjugate) % 1.0
    return ctx.add_color_expression(alpha, hue.to_float(), float(sat), float(value))


# ============================================================================
# demoPieChart_good — dynamic pie chart using loop/save/rotate
# ============================================================================
def demo_pie_chart_good():
    data = [30.0, 20.0, 15.0, 25.0, 10.0]
    names = ["Android", "iOS", "Web", "Desktop", "Other"]

    ctx = RcContext(500, 500, "Pie Chart Demo",
                    api_level=7, profiles=0)
    with ctx.root():
        with ctx.box(Modifier().fill_max_size().background(0xFFF0F0F0),
                     Rc.Layout.START, Rc.Layout.START):
            with ctx.canvas(Modifier().fill_max_size()):
                w = ctx.ComponentWidth()
                h = ctx.ComponentHeight()
                cx = w / 2.0
                cy = h / 2.0
                radius = w.min(h) * 0.4

                values = ctx.rf(ctx.add_float_array(data))
                names_id = ctx.add_string_list(*names)
                length = rf_array_len(values)
                total = rf_array_sum(values)

                with ctx.saved():
                    ctx.rotate(-90, cx.to_float(), cy.to_float())
                    with ctx.loop_range(0, 1, length) as i:
                        value = values[i]

                        name = ctx.text_lookup(names_id, i.to_float())
                        sweepAngle = (value / total) * 360.0

                        color_id = _get_distributed_color(
                            ctx, i, 0xff, 56.6 / 100.0, 80 / 100.0)

                        ctx.painter.set_color_id(color_id).set_style(
                            STYLE_FILL).commit()

                        ctx.draw_sector(
                            (cx - radius).to_float(),
                            (cy - radius).to_float(),
                            (cx + radius).to_float(),
                            (cy + radius).to_float(),
                            0,
                            sweepAngle.to_float(),
                        )

                        # Draw border
                        ctx.painter.set_color(WHITE).set_style(
                            STYLE_STROKE).set_stroke_width(2.0).commit()

                        ctx.draw_sector(
                            (cx - radius).to_float(),
                            (cy - radius).to_float(),
                            (cx + radius).to_float(),
                            (cy + radius).to_float(),
                            0,
                            sweepAngle.to_float(),
                        )
                        ctx.rotate(sweepAngle.to_float(),
                                   cx.to_float(), cy.to_float())
    return ctx


# ============================================================================
# demoPieChart — static pie chart with unrolled for-loops
# ============================================================================
def demo_pie_chart():
    data = [30.0, 20.0, 15.0, 25.0, 10.0]
    names = ["Android", "iOS", "Web", "Desktop", "Other"]
    colors = [
        0xFF4CAF50,  # Green
        0xFF2196F3,  # Blue
        0xFFFFC107,  # Amber
        0xFFE91E63,  # Pink
        0xFF9C27B0,  # Purple
    ]

    ctx = RcContext(500, 500, "Pie Chart Demo",
                    api_level=7, profiles=0)
    with ctx.root():
        with ctx.box(Modifier().fill_max_size().background(0xFFF0F0F0),
                     Rc.Layout.START, Rc.Layout.START):
            with ctx.canvas(Modifier().fill_max_size()):
                w = ctx.ComponentWidth()
                h = ctx.ComponentHeight()
                cx = w / 2.0
                cy = h / 2.0
                radius = w.min(h) * 0.4

                # All constant arithmetic uses float32 to match Kotlin/Java
                total = _f32(sum(data))
                currentAngle = _f32(-90.0)  # Start from top

                for i in range(len(data)):
                    sweepAngle = _f32(_f32(data[i] / total) * 360.0)

                    # Draw slice
                    ctx.painter.set_color(
                        colors[i % len(colors)]).set_style(
                        STYLE_FILL).commit()

                    ctx.draw_sector(
                        (cx - radius).to_float(),
                        (cy - radius).to_float(),
                        (cx + radius).to_float(),
                        (cy + radius).to_float(),
                        currentAngle,
                        sweepAngle,
                    )

                    # Draw border
                    ctx.painter.set_color(WHITE).set_style(
                        STYLE_STROKE).set_stroke_width(2.0).commit()

                    ctx.draw_sector(
                        (cx - radius).to_float(),
                        (cy - radius).to_float(),
                        (cx + radius).to_float(),
                        (cy + radius).to_float(),
                        currentAngle,
                        sweepAngle,
                    )

                    # Draw Label — match Kotlin float32 arithmetic
                    labelAngle = _f32(
                        _f32(_f32(currentAngle + sweepAngle / 2.0)
                             * _f32(math.pi)) / 180.0)
                    labelRadius = radius * 0.7
                    lx = cx + labelRadius * _f32(math.cos(labelAngle))
                    ly = cy + labelRadius * _f32(math.sin(labelAngle))

                    ctx.painter.set_color(WHITE).set_text_size(
                        24.0).set_style(STYLE_FILL).set_typeface(
                        0, 700, False).commit()

                    text_id = ctx.add_text(names[i])
                    ctx.draw_text_anchored(text_id, lx.to_float(),
                                           ly.to_float(), 0.5, 0.5, 0)

                    currentAngle = _f32(currentAngle + sweepAngle)

                # Draw Legend
                legendX = 20.0
                legendY = 20.0
                for i in range(len(data)):
                    ctx.painter.set_color(
                        colors[i % len(colors)]).set_style(
                        STYLE_FILL).commit()
                    ctx.draw_rect(legendX, legendY, 20.0, 20.0)

                    ctx.painter.set_color(BLACK).set_text_size(20.0).commit()
                    text_id = ctx.add_text(
                        names[i] + " (" + str(int(data[i])) + "%)")
                    ctx.draw_text_anchored(text_id, legendX + 30.0,
                                           legendY + 15.0, 0.0, 0.5, 0)

                    legendY = _f32(legendY + 30.0)
    return ctx


# ============================================================================
# demoPieChart2 — dynamic pie chart with loop, sumAngle, text labels
# ============================================================================
def demo_pie_chart2():
    data = [30.0, 20.0, 15.0, 25.0, 10.0]
    names = ["Android", "iOS", "Web", "Desktop", "Other"]

    ctx = RcContext(500, 500, "Pie Chart Demo",
                    api_level=7, profiles=0)
    with ctx.root():
        with ctx.box(Modifier().fill_max_size().background(0xFFF0F0F0),
                     Rc.Layout.START, Rc.Layout.START):
            with ctx.canvas(Modifier().fill_max_size()):
                w = ctx.ComponentWidth()
                h = ctx.ComponentHeight()
                density = ctx.rf(Rc.System.DENSITY)

                cx = w / 2.0
                cy = h / 2.0
                radius = w.min(h) * 0.4

                values = ctx.rf(ctx.add_float_array(data))
                names_id = ctx.add_string_list(*names)
                length = rf_array_len(values)
                total = rf_array_sum(values)

                with ctx.loop_range(0, 1, length) as i:
                    value = values[i]
                    sum_val = rf_array_sum(values, i - 1.0).flush()
                    ctx.add_debug_message("sum ", sum_val.to_float())
                    ctx.add_debug_message("value ", value.to_float())
                    name = ctx.text_lookup(names_id, i.to_float())
                    sweepAngle = (value / total) * 360.0
                    sumAngle = (sum_val / total) * 360.0

                    color_id = _get_distributed_color(
                        ctx, i, 0xff, 56.6 / 100.0, 80 / 100.0)

                    ctx.painter.set_color_id(color_id).set_style(
                        STYLE_FILL).commit()

                    ctx.draw_sector(
                        (cx - radius).to_float(),
                        (cy - radius).to_float(),
                        (cx + radius).to_float(),
                        (cy + radius).to_float(),
                        sumAngle.to_float(),
                        sweepAngle.to_float(),
                    )

                    # Draw border
                    ctx.painter.set_color(WHITE).set_style(
                        STYLE_STROKE).set_stroke_width(2.0).commit()

                    ctx.draw_sector(
                        (cx - radius).to_float(),
                        (cy - radius).to_float(),
                        (cx + radius).to_float(),
                        (cy + radius).to_float(),
                        sumAngle.to_float(),
                        sweepAngle.to_float(),
                    )

                    ctx.painter.set_text_size(
                        (16.0 * density).to_float()).set_style(
                        STYLE_FILL).commit()
                    angleRad = (sumAngle + sweepAngle * 0.5).rad()
                    pieCenterX = cx + radius * angleRad.cos() * 0.66
                    pieCenterY = cy + radius * angleRad.sin() * 0.66
                    ctx.draw_text_anchored(name, pieCenterX.to_float(),
                                           pieCenterY.to_float(), 0, 0, 0)
    return ctx


if __name__ == '__main__':
    outdir = os.path.join(os.path.dirname(__file__), '..', 'output')
    os.makedirs(outdir, exist_ok=True)

    ref_dir = os.path.join(os.path.dirname(__file__), '..', '..',
                           'integration-tests', 'player-view-demos',
                           'src', 'main', 'res', 'raw')

    for name, func, ref_name in [
        ('good_pie_chart', demo_pie_chart_good, 'good_pie_chart'),
        ('pie_chart', demo_pie_chart, 'pie_chart'),
        ('pie_chart2', demo_pie_chart2, 'pie_chart2'),
    ]:
        ctx = func()
        data = ctx.encode()
        path = os.path.join(outdir, f'{name}.rc')
        ctx.save(path)
        print(f'{name}: {len(data)} bytes -> {path}')

        # Compare with reference
        ref_path = os.path.join(ref_dir, f'{ref_name}.rc')
        if os.path.exists(ref_path):
            with open(ref_path, 'rb') as f:
                ref_data = f.read()
            if data == ref_data:
                print(f'  MATCH: byte-identical to {ref_name}.rc')
            else:
                print(f'  DIFF: {len(data)} bytes vs {len(ref_data)} bytes (ref)')
                # Find first difference
                for j in range(min(len(data), len(ref_data))):
                    if data[j] != ref_data[j]:
                        print(f'  First diff at byte {j}: '
                              f'got 0x{data[j]:02x}, expected 0x{ref_data[j]:02x}')
                        break
        else:
            print(f'  Reference file not found: {ref_path}')

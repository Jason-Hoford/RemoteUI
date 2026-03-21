"""Port of ExampleNumbers.kt spreadSheet() function.

Target .rc file: spread_sheet.rc
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RcContext, Modifier, Rc

# Android color constants
BLUE = 0xFF0000FF
WHITE = 0xFFFFFFFF
LTGRAY = 0xFFCCCCCC
BLACK = 0xFF000000
MAGENTA = 0xFFFF00FF


def demo_spreadsheet():
    ctx = RcContext(500, 500, "Simple Timer", api_level=6, profiles=0)

    with ctx.root():
        with ctx.box(Modifier().fill_max_size(), Rc.Layout.START, Rc.Layout.START):
            with ctx.canvas(Modifier().fill_max_size()):
                w = ctx.ComponentWidth()
                h = ctx.ComponentHeight()
                cx = w / 2.0
                cy = h / 2.0
                rad = cx.min(cy)
                round_ = rad / 8.0

                ctx.painter.set_color(BLUE).commit()
                ctx.draw_round_rect(0, 0, w.to_float(), h.to_float(),
                                    round_.to_float(), round_.to_float())

                ctx.painter.set_color(WHITE).commit()
                ctx.draw_rect(10.0, 10, (w - 10.0).to_float(),
                              (h - round_).to_float())

                ctx.painter.set_color(LTGRAY).set_stroke_width(5.0) \
                    .set_text_size(30.0).commit()

                header0 = ctx.add_string_list("", "", "", "GROUPING_BY3")
                header1 = ctx.add_string_list(
                    "default", "PAD_AFTER_ZERO", "PAD_AFTER_ZERO",
                    "PAD_AFTER_ZERO")
                header2 = ctx.add_string_list(
                    "", "PAD_PRE_NONE", "PAD_PRE_ZERO", "PAD_PRE_ZERO")

                cellWidth = w / 4.0
                cellHeight = 80.0

                # Horizontal lines top half
                with ctx.loop_range(
                        (round_ + cellHeight).to_float(),
                        cellHeight,
                        cy.to_float()) as k:
                    ctx.draw_line(0, k.to_float(), w.to_float(), k.to_float())

                # Horizontal lines bottom half
                with ctx.loop_range(
                        (cy + cellHeight * 2.0).to_float(),
                        cellHeight,
                        h.to_float()) as k:
                    ctx.draw_line(0, k.to_float(), w.to_float(), k.to_float())

                # Column headers
                with ctx.loop_range(0, 1, 4) as k:
                    colPos = k * cellWidth
                    ctx.painter.set_color(LTGRAY).commit()
                    ctx.draw_line(colPos.to_float(), round_.to_float(),
                                  colPos.to_float(), (h - round_).to_float())

                    id0 = ctx.text_lookup(header0, k.to_float())
                    id1 = ctx.text_lookup(header1, k.to_float())
                    id2 = ctx.text_lookup(header2, k.to_float())

                    ctx.painter.set_color(MAGENTA).commit()
                    centerText = colPos + cellWidth / 2.0
                    ctx.draw_text_anchored(
                        id0, centerText.to_float(),
                        (round_ + cellHeight / 2.0).to_float(),
                        0, -3.5, 0)
                    ctx.draw_text_anchored(
                        id1, centerText.to_float(),
                        (round_ + cellHeight / 2.0).to_float(),
                        0, -1, 0)
                    ctx.draw_text_anchored(
                        id2, centerText.to_float(),
                        (round_ + cellHeight / 2.0).to_float(),
                        0, 1.5, 0)

                # Data rows top half
                ctx.painter.set_color(BLACK).set_text_size(34.0).commit()
                with ctx.loop_range(1, 1, 5) as y:
                    yPos = y * cellHeight + cellHeight / 2.0 + round_
                    num = y.sin() * 1000.0 - 500.0

                    # Column 1: default
                    centerText = cellWidth * 0.5
                    mode = 0
                    tid = ctx.create_text_from_float(
                        num.to_float(), 6, 2, mode)
                    ctx.draw_text_anchored(
                        tid, centerText.to_float(), yPos.to_float(), 0, 0, 0)

                    # Column 2: PAD_AFTER_ZERO | PAD_PRE_NONE
                    mode = (Rc.TextFromFloat.PAD_AFTER_ZERO |
                            Rc.TextFromFloat.PAD_PRE_NONE)
                    centerText = cellWidth * 1.5
                    tid = ctx.create_text_from_float(
                        num.to_float(), 6, 2, mode)
                    ctx.draw_text_anchored(
                        tid, centerText.to_float(), yPos.to_float(), 0, 0, 0)

                    # Column 3: PAD_AFTER_ZERO | PAD_PRE_ZERO
                    mode = (Rc.TextFromFloat.PAD_AFTER_ZERO |
                            Rc.TextFromFloat.PAD_PRE_ZERO)
                    centerText = cellWidth * 2.5
                    tid = ctx.create_text_from_float(
                        num.to_float(), 6, 2, mode)
                    ctx.draw_text_anchored(
                        tid, centerText.to_float(), yPos.to_float(), 0, 0, 0)

                    # Column 4: PAD_AFTER_ZERO | PAD_PRE_NONE | GROUPING_BY3
                    mode = (Rc.TextFromFloat.PAD_AFTER_ZERO |
                            Rc.TextFromFloat.PAD_PRE_NONE |
                            Rc.TextFromFloat.GROUPING_BY3)
                    centerText = cellWidth * 3.5
                    tid = ctx.create_text_from_float(
                        num.to_float(), 6, 2, mode)
                    ctx.draw_text_anchored(
                        tid, centerText.to_float(), yPos.to_float(), 0, 0, 0)

                # Second set of headers
                ctx.painter.set_color(LTGRAY).set_stroke_width(5.0) \
                    .set_text_size(30.0).commit()

                header20 = ctx.add_string_list(
                    "PAD_AFTER_ZERO", "PAD_AFTER_ZERO",
                    "PAD_AFTER_ZERO", "PAD_AFTER_ZERO")
                header21 = ctx.add_string_list(
                    "PAD_PRE_NONE", "PAD_PRE_NONE",
                    "PAD_PRE_ZERO", "PAD_PRE_ZERO")
                header22 = ctx.add_string_list(
                    "GROUPING_BY4", "GROUPING_BY32",
                    "GROUPING_BY3", "GROUPING_BY3")
                header23 = ctx.add_string_list(
                    "PERIOD_COMMA", "COMMA_PERIOD",
                    "SPACE_COMMA", "UNDER_PERIOD")

                with ctx.loop_range(0, 1, 4) as k:
                    colPos = k * cellWidth

                    id0 = ctx.text_lookup(header20, k.to_float())
                    id1 = ctx.text_lookup(header21, k.to_float())
                    id2 = ctx.text_lookup(header22, k.to_float())
                    id3 = ctx.text_lookup(header23, k.to_float())

                    ctx.painter.set_color(MAGENTA).commit()
                    centerText = colPos + cellWidth / 2.0
                    ctx.draw_text_anchored(
                        id0, centerText.to_float(),
                        (cy + 50.0).to_float(), 0, -3.5, 0)
                    ctx.draw_text_anchored(
                        id1, centerText.to_float(),
                        (cy + 50.0).to_float(), 0, -1, 0)
                    ctx.draw_text_anchored(
                        id2, centerText.to_float(),
                        (cy + 50.0).to_float(), 0, 1.5, 0)
                    ctx.draw_text_anchored(
                        id3, centerText.to_float(),
                        (cy + 50.0).to_float(), 0, 4.0, 0)

                # Data rows bottom half
                ctx.painter.set_color(BLACK).set_text_size(34.0).commit()
                with ctx.loop_range(1, 1, 5) as y:
                    yPos = y * cellHeight + cellHeight / 2.0 + round_ + cy
                    num = ((y % 5.0) - 2) * 1234567.8

                    # Column 1
                    centerText = cellWidth * 0.5
                    mode = (Rc.TextFromFloat.PAD_AFTER_ZERO |
                            Rc.TextFromFloat.PAD_PRE_NONE |
                            Rc.TextFromFloat.GROUPING_BY4 |
                            Rc.TextFromFloat.SEPARATOR_PERIOD_COMMA)
                    tid = ctx.create_text_from_float(
                        num.to_float(), 10, 2, mode)
                    ctx.draw_text_anchored(
                        tid, centerText.to_float(), yPos.to_float(), 0, 0, 0)

                    # Column 2
                    mode = (Rc.TextFromFloat.PAD_AFTER_ZERO |
                            Rc.TextFromFloat.PAD_PRE_NONE |
                            Rc.TextFromFloat.GROUPING_BY32 |
                            Rc.TextFromFloat.SEPARATOR_COMMA_PERIOD)
                    centerText = cellWidth * 1.5
                    tid = ctx.create_text_from_float(
                        num.to_float(), 10, 2, mode)
                    ctx.draw_text_anchored(
                        tid, centerText.to_float(), yPos.to_float(), 0, 0, 0)

                    # Column 3
                    mode = (Rc.TextFromFloat.PAD_AFTER_ZERO |
                            Rc.TextFromFloat.PAD_PRE_NONE |
                            Rc.TextFromFloat.GROUPING_BY3 |
                            Rc.TextFromFloat.SEPARATOR_SPACE_COMMA)
                    centerText = cellWidth * 2.5
                    tid = ctx.create_text_from_float(
                        num.to_float(), 10, 2, mode)
                    ctx.draw_text_anchored(
                        tid, centerText.to_float(), yPos.to_float(), 0, 0, 0)

                    # Column 4
                    mode = (Rc.TextFromFloat.PAD_AFTER_ZERO |
                            Rc.TextFromFloat.PAD_PRE_NONE |
                            Rc.TextFromFloat.GROUPING_BY3 |
                            Rc.TextFromFloat.SEPARATOR_UNDER_PERIOD)
                    centerText = cellWidth * 3.5
                    tid = ctx.create_text_from_float(
                        num.to_float(), 10, 2, mode)
                    ctx.draw_text_anchored(
                        tid, centerText.to_float(), yPos.to_float(), 0, 0, 0)

    return ctx


if __name__ == '__main__':
    ctx = demo_spreadsheet()
    data = ctx.encode()
    print(f"spread_sheet: {len(data)} bytes")
    outdir = os.path.join(os.path.dirname(__file__), '..', 'output')
    os.makedirs(outdir, exist_ok=True)
    ctx.save(os.path.join(outdir, 'spread_sheet.rc'))

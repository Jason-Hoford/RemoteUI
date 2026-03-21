"""Text transform demo. Port of DemoTextTransform.kt.

Demonstrates:
- TextTransform operations (uppercase, lowercase, trim, capitalize, uppercase first)
- textMerge for building compound text
- beginGlobal/endGlobal for pre-computed data
- addColorExpression with pingPong
- Canvas with drawRoundRect, drawCircle, drawTextAnchored
- getTimeString helper
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RcContext, Modifier, Rc

MOD = Rc.FloatExpression.MOD
SUB = Rc.FloatExpression.SUB
ABS = Rc.FloatExpression.ABS
DIV = Rc.FloatExpression.DIV
MUL = Rc.FloatExpression.MUL

# Colors for text rows (extracted from Kotlin reference — Kotlin uses Random.nextInt())
ROW_COLORS = [0x2E425E3B, 0x604BD49B, 0x2F680C9D, 0xB50FB6A7, 0x106C88FD, 0x7CD52B75]


def demo_text_transform():
    ctx = RcContext(500, 500, "Simple Timer", api_level=7, profiles=0x201)

    bounce = ctx.ping_pong(1, Rc.Time.CONTINUOUS_SEC)
    col = ctx.add_color_expression(0xFFFF0000, 0xFF00FF00, bounce)

    with ctx.root():
        with ctx.box(Modifier().fill_max_size(), horizontal=Rc.Layout.START, vertical=Rc.Layout.START):
            with ctx.column(Modifier().background_id(col)):
                # Time string at top
                time_str = ctx.get_time_string()
                ctx.text_by_id(time_str,
                               Modifier().fill_max_width().height(240)
                               .background(0xFF99FFFF),
                               font_size=100.0, color=0xFF000000,
                               text_align=Rc.Text.ALIGN_CENTER)

                # Text transform operations
                ctx.begin_global()
                basic = ctx.add_text(" hard work John ")
                upper = ctx.text_merge(
                    ctx.add_text("upper:"),
                    ctx.text_transform(basic, Rc.TextTransform.TEXT_TO_UPPERCASE))
                lower = ctx.text_merge(
                    ctx.add_text("lower:"),
                    ctx.text_transform(basic, Rc.TextTransform.TEXT_TO_LOWERCASE))
                trim = ctx.text_merge(
                    ctx.add_text("trim:"),
                    ctx.text_transform(basic, Rc.TextTransform.TEXT_TRIM))
                capitalize = ctx.text_merge(
                    ctx.add_text("capitalize:"),
                    ctx.text_transform(basic, Rc.TextTransform.TEXT_CAPITALIZE))
                sentence = ctx.text_merge(
                    ctx.add_text("Sentence:"),
                    ctx.text_transform(basic, Rc.TextTransform.TEXT_UPPERCASE_FIRST_CHAR))
                ctx.end_global()

                # Display each transform
                for i, tid in enumerate([basic, upper, lower, trim, capitalize, sentence]):
                    ctx.text_by_id(tid,
                                   Modifier().fill_max_width().height(100)
                                   .background(ROW_COLORS[i % len(ROW_COLORS)]),
                                   font_size=80.0, color=0xFF000000,
                                   text_align=Rc.Text.ALIGN_LEFT)

                # Canvas with color expression and time
                with ctx.canvas(Modifier().fill_max_width().height(400)):
                    w = ctx.component_width()
                    h = ctx.component_height()
                    ctx.painter.set_color(0x87EEFDA3).commit()
                    ctx.draw_round_rect(0, 0, w, h, 2.0, 2.0)
                    ctx.painter.set_color_id(col).commit()
                    ctx.draw_circle(
                        ctx.float_expression(w, 2.0, DIV),
                        ctx.float_expression(h, 2.0, DIV),
                        100.0)
                    ctx.painter.set_color(0xFF000000).set_text_size(100.0).commit()
                    time_str2 = ctx.get_time_string()
                    ctx.draw_text_anchored(
                        time_str2,
                        ctx.float_expression(w, 2.0, DIV),
                        ctx.float_expression(h, 2.0, DIV),
                        0, 0, 0)

    return ctx


if __name__ == '__main__':
    ctx = demo_text_transform()
    data = ctx.encode()
    print(f"TextTransform: {len(data)} bytes")
    ctx.save("demo_text_transform.rc")
    print("Saved demo_text_transform.rc")

"""Digital clock demo using text expressions.

Demonstrates:
- beginGlobal/endGlobal for global sections
- createTextFromFloat to format numbers
- textMerge to concatenate text IDs
- Time variables (TIME_IN_HR, TIME_IN_MIN, TIME_IN_SEC)
- Text component with expression-generated text
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RcContext, Modifier, Rc

BLACK = 0xFF000000
WHITE = 0xFFFFFFFF
LTCYAN = 0xFF99FFFF

MOD = Rc.FloatExpression.MOD


def demo_digital_clock():
    ctx = RcContext(500, 200, "DigitalClock")

    ctx.begin_global()
    colon = ctx.add_text(":")
    # Seconds: TIME_IN_SEC % 60
    sec_val = ctx.float_expression(Rc.Time.TIME_IN_SEC, 60.0, MOD)
    tid_sec = ctx.create_text_from_float(sec_val, 2, 0, Rc.TextFromFloat.PAD_PRE_ZERO)
    # Minutes: TIME_IN_MIN % 60
    min_val = ctx.float_expression(Rc.Time.TIME_IN_MIN, 60.0, MOD)
    tid_min = ctx.create_text_from_float(min_val, 2, 0, Rc.TextFromFloat.PAD_PRE_ZERO)
    # Hours: TIME_IN_HR % 12
    hr_val = ctx.float_expression(Rc.Time.TIME_IN_HR, 12.0, MOD)
    tid_hr = ctx.create_text_from_float(hr_val, 2, 0, 0)
    # Merge: "HH:MM:SS"
    clock_text = ctx.text_merge(tid_hr, colon, tid_min, colon, tid_sec)
    ctx.end_global()

    with ctx.root():
        with ctx.box(Modifier().fill_max_size().background(LTCYAN)):
            ctx.text_by_id(clock_text,
                           modifier=Modifier().fill_max_size(),
                           color=BLACK, font_size=100.0)

    return ctx


if __name__ == '__main__':
    ctx = demo_digital_clock()
    data = ctx.encode()
    print(f"DigitalClock: {len(data)} bytes")
    ctx.save("demo_digital_clock.rc")
    print("Saved demo_digital_clock.rc")

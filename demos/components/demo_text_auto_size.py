"""Atomic demo for text auto-sizing. Port of DemoTextAutoSize.kt."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RcContext, Modifier

LTGRAY = 0xFFCCCCCC
BLACK = 0xFF000000


def demo_text_auto_size():
    ctx = RcContext(500, 500, "DemoTextAutoSize", profiles=0x201)
    with ctx.root():
        with ctx.box(Modifier().size(200, 50).background(LTGRAY)):
            ctx.text("This text scales to fit",
                     modifier=Modifier().fill_max_size(),
                     autosize=True,
                     min_font_size=10.0,
                     max_font_size=100.0)
    return ctx


if __name__ == '__main__':
    ctx = demo_text_auto_size()
    data = ctx.encode()
    print(f"DemoTextAutoSize: {len(data)} bytes")
    ctx.save("demo_text_auto_size.rc")
    print("Saved demo_text_auto_size.rc")

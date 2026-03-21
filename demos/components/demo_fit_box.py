"""Atomic demo for the FitBox component. Port of DemoFitBox.kt."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RcContext, Modifier

LTGRAY = 0xFFCCCCCC
BLUE = 0xFF0000FF
WHITE = 0xFFFFFFFF


def demo_fit_box():
    ctx = RcContext(500, 500, "DemoFitBox", profiles=0x201)
    with ctx.root():
        # Content is 1000x1000, but FitBox scales it to fit
        with ctx.fit_box(Modifier().fill_max_size().background(LTGRAY)):
            with ctx.box(Modifier().size(1000).background(BLUE)):
                ctx.text("SCALED", font_size=150.0, color=WHITE)
    return ctx


if __name__ == '__main__':
    ctx = demo_fit_box()
    data = ctx.encode()
    print(f"DemoFitBox: {len(data)} bytes")
    ctx.save("demo_fit_box.rc")
    print("Saved demo_fit_box.rc")

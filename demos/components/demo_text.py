"""Atomic demo for the Text component. Port of DemoText.kt."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RcContext, Modifier

BLACK = 0xFF000000
BLUE = 0xFF0000FF
WHITE = 0xFFFFFFFF

PROFILE_ANDROIDX = 0x200
PROFILE_EXPERIMENTAL = 0x001


def demo_text():
    ctx = RcContext(500, 500, "DemoText",
                    profiles=PROFILE_ANDROIDX | PROFILE_EXPERIMENTAL)
    with ctx.root():
        with ctx.column(Modifier().fill_max_size().padding(20).background(WHITE)):
            ctx.text("Basic Text", font_size=40.0, font_weight=700.0,
                     color=BLACK)
            ctx.text("Italic Blue", font_size=30.0, font_style=1,
                     color=BLUE)
    return ctx


if __name__ == '__main__':
    ctx = demo_text()
    data = ctx.encode()
    print(f"DemoText: {len(data)} bytes")
    ctx.save("demo_text.rc")
    print("Saved demo_text.rc")

"""Text baseline demo. Port of RcTextDemo() from Text.kt.

Generates: text_baseline.rc

Demonstrates baseline alignment of text components at different font sizes
across three rows with TOP, CENTER, and BOTTOM vertical alignment,
all using SPACE_EVENLY horizontal distribution.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RcContext, Modifier, Rc

# Android Color constants
YELLOW = 0xFFFFFF00

# Layout constants not yet in Rc.Layout
SPACE_EVENLY = 7
TOP = Rc.Layout.TOP       # 4
CENTER = Rc.Layout.CENTER  # 2
BOTTOM = Rc.Layout.BOTTOM  # 5


def _baseline_row(ctx, horizontal, vertical):
    """Emit a row of six text items, each with alignByBaseline()."""
    with ctx.row(Modifier().fill_max_size(),
                 horizontal=horizontal,
                 vertical=vertical):
        ctx.text("Hello", modifier=Modifier().align_by_baseline(),
                 use_core_text=True)
        ctx.text("World", modifier=Modifier().align_by_baseline(),
                 font_size=100.0, use_core_text=True)
        ctx.text("the", modifier=Modifier().align_by_baseline(),
                 font_size=12.0, use_core_text=True)
        ctx.text("quick", modifier=Modifier().align_by_baseline(),
                 font_size=64.0, use_core_text=True)
        ctx.text("brown", modifier=Modifier().align_by_baseline(),
                 font_size=72.0, use_core_text=True)
        ctx.text("fox", modifier=Modifier().align_by_baseline(),
                 use_core_text=True)


def demo_text_baseline():
    """Port of RcTextDemo() from Text.kt -> text_baseline.rc"""
    ctx = RcContext(600, 600, "Demo", api_level=7, profiles=0x201)

    with ctx.root():
        with ctx.box(Modifier().fill_max_size().background(YELLOW)):
            _baseline_row(ctx, SPACE_EVENLY, TOP)
            _baseline_row(ctx, SPACE_EVENLY, CENTER)
            _baseline_row(ctx, SPACE_EVENLY, BOTTOM)

    return ctx


if __name__ == '__main__':
    ctx = demo_text_baseline()
    data = ctx.encode()
    print(f"TextBaseline: {len(data)} bytes")

    ref_path = os.path.join(
        os.path.dirname(__file__), '..', '..',
        'integration-tests', 'player-view-demos',
        'src', 'main', 'res', 'raw', 'text_baseline.rc')
    if os.path.exists(ref_path):
        with open(ref_path, 'rb') as f:
            ref = f.read()
        if data == ref:
            print("MATCH: byte-identical to Kotlin reference")
        else:
            print(f"MISMATCH: got {len(data)} bytes, ref {len(ref)} bytes")
            for i, (a, b) in enumerate(zip(data, ref)):
                if a != b:
                    print(f"  first diff at byte {i}: got 0x{a:02x}, ref 0x{b:02x}")
                    break
    else:
        print(f"Reference not found at {ref_path}")

    ctx.save("text_baseline.rc")
    print("Saved text_baseline.rc")

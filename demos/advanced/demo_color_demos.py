"""Port of DemoColor.kt — colorButtons() demo.

The Kotlin function colorButtons() in DemoColor.kt produces the reference file
``color.rc`` (mapped via DemosCreation.java as "1/Example/color").

It demonstrates:
- pingPong for bouncing animation (0..1 oscillation from CONTINUOUS_SEC)
- addColorExpression for dynamic color interpolation
- backgroundId and dynamicBorder modifiers
- Canvas drawing with drawRoundRect, createTextFromFloat, drawTextAnchored
- setColorId on the painter
- ComponentWidth/ComponentHeight for layout-relative dimensions
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RcContext, Modifier, Rc

# Color constants
GREEN = 0xFF007700
BLUE = 0xFF000077
TEAL = 0xFF007777
DKPURPLE = 0xFF666677
WHITE = 0xFFFFFFFF

# Float expression operators
DIV = Rc.FloatExpression.DIV


def demo_color():
    """Port of colorButtons() from DemoColor.kt -> color.rc.

    Creates a RemoteComposeContextAndroid with:
        width=500, height=500, contentDescription="Simple Timer",
        apiLevel=7, profiles=RcProfiles.PROFILE_ANDROIDX (0x200)

    Layout structure:
        root
          box(fillMaxSize, horizontal=START, vertical=START)
            column(background=0xFF666677)
              box(background=0xFF007700, fillMaxWidth, height=120)
              box(backgroundId=col, fillMaxWidth, height=120)
              box(background=0xFF000077, fillMaxWidth, height=120)
              box(backgroundId=col, dynamicBorder(10,30,col2,0), fillMaxWidth, height=120)
              box(background=0xFF007777, fillMaxWidth, height=120)
              canvas(dynamicBorder(40,30,col2,0), fillMaxWidth, height=200)
                painter.setColorId(col).commit()
                drawRoundRect(0, 0, w, h, 2, 2)
                painter.setColor(white).setTextSize(64).commit()
                id = createTextFromFloat(API_LEVEL, 3, 2, 0)
                drawTextAnchored(id, w/2, 100, 0, 0, 0)
    """
    ctx = RcContext(500, 500, "Simple Timer",
                    api_level=7, profiles=0x200)

    # pingPong(1, ContinuousSec()) -- bouncing 0..1 value driven by time
    bounce = ctx.ping_pong(1, Rc.Time.CONTINUOUS_SEC)

    # Two color expressions driven by the bounce value
    col = ctx.add_color_expression(0xFFFF0000, 0xFF00FF00, bounce)
    col2 = ctx.add_color_expression(0xFF000000, 0xFFFFFF00, bounce)

    with ctx.root():
        # Outer box: fillMaxSize, horizontal=START(1), vertical=START(1)
        # This is the container box with children, so use ctx.box()
        with ctx.box(Modifier().fill_max_size(),
                     horizontal=Rc.Layout.START,
                     vertical=Rc.Layout.START):
            with ctx.column(Modifier().background(DKPURPLE)):
                # Leaf boxes: Kotlin box(modifier) defaults to CENTER/CENTER
                # Use box_leaf() which matches the Kotlin leaf box overload
                ctx.box_leaf(Modifier().background(GREEN)
                             .fill_max_width().height(120))
                ctx.box_leaf(Modifier().background_id(col)
                             .fill_max_width().height(120))
                ctx.box_leaf(Modifier().background(BLUE)
                             .fill_max_width().height(120))
                ctx.box_leaf(Modifier().background_id(col)
                             .dynamic_border(10.0, 30.0, col2, 0)
                             .fill_max_width().height(120))
                ctx.box_leaf(Modifier().background(TEAL)
                             .fill_max_width().height(120))

                # Canvas section: dynamic border, shows API level text
                with ctx.canvas(Modifier()
                                .dynamic_border(40.0, 30.0, col2, 0)
                                .fill_max_width().height(200)):
                    w = ctx.component_width()
                    h = ctx.component_height()
                    version = Rc.System.API_LEVEL

                    # Fill round rect with the dynamic color
                    ctx.painter.set_color_id(col).commit()
                    ctx.draw_round_rect(0, 0, w, h, 2.0, 2.0)

                    # Draw API level text in white
                    ctx.painter.set_color(WHITE).set_text_size(64.0).commit()
                    text_id = ctx.create_text_from_float(version, 3, 2, 0)
                    cx = ctx.float_expression(w, 2.0, DIV)
                    ctx.draw_text_anchored(text_id, cx, 100.0, 0, 0, 0)

    return ctx


if __name__ == '__main__':
    ctx = demo_color()
    data = ctx.encode()
    print(f"demo_color (colorButtons): {len(data)} bytes")
    out_path = os.path.join(os.path.dirname(__file__), '..', 'output',
                            'demo_color.rc')
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    ctx.save(out_path)
    print(f"Saved {out_path}")

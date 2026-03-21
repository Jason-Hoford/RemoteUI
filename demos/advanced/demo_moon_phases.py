"""Port of MoonPhases.kt demoMoonPhases() — moon phases demo with touch interaction."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RcContext, Modifier
from rcreate.rc import Rc
from rcreate.types.nan_utils import as_nan
from rcreate.types.rfloat import RFloat

PROFILE_ANDROIDX = 0x200
STYLE_FILL = Rc.Paint.STYLE_FILL
FE = Rc.FloatExpression


def demo_moon_phases():
    ctx = RcContext(500, 500, "Moon Phases Demo",
                    api_level=7, profiles=PROFILE_ANDROIDX)
    with ctx.root():
        density = ctx.rf(Rc.System.DENSITY)
        with ctx.box(Modifier().fill_max_size().background(0xFF111111),
                     Rc.Layout.CENTER, Rc.Layout.CENTER):
            with ctx.canvas(Modifier().fill_max_size()):
                w = ctx.ComponentWidth()
                h = ctx.ComponentHeight()
                cx = w / 2.0
                cy = h / 2.0
                moonRadius = ctx.rf(150.0) * density

                # Drag up/down to change date (1 pixel = 0.1 days)
                # Use array constructor [value] to match Kotlin rf(vararg) behavior:
                # id stays 0 so toFloat() emits ANIMATED_FLOAT
                touch_val = ctx.touch_expression(
                    Rc.Touch.POSITION_Y,
                    -0.1,
                    FE.MUL,
                    def_value=0.0,
                    min_val=-32.0,
                    max_val=32.0,
                    touch_mode=Rc.Touch.STOP_GENTLY,
                )
                daysOffset = RFloat(ctx._writer, [touch_val])

                # 1738144800 is a New Moon (Jan 29, 2025)
                refTime = 1738144800.0
                secondsPerDay = 86400.0
                lunarCycle = 29.53059

                # Use array constructor to match Kotlin rf(vararg) behavior
                currentTimeSeconds = RFloat(ctx._writer, [as_nan(32)])
                targetTimeSeconds = currentTimeSeconds + daysOffset * secondsPerDay

                daysSinceRef = (targetTimeSeconds - refTime) / secondsPerDay
                phase = (daysSinceRef % lunarCycle + lunarCycle) % lunarCycle
                normalizedPhase = phase / lunarCycle  # 0 to 1

                # Draw Moon Background (Dark side)
                ctx.painter.set_color(0xFF333333).set_style(STYLE_FILL).commit()
                ctx.draw_circle(cx.to_float(), cy.to_float(), moonRadius.to_float())

                # Draw Illuminated Part
                ctx.painter.set_color(0xFFCCCCCC).set_style(STYLE_FILL).commit()

                # The terminator is an ellipse with width varying by cos
                terminatorW = (normalizedPhase * 2.0 * 3.14159).cos().abs() * moonRadius

                ctx.if_else(
                    normalizedPhase - 0.5,
                    lambda: _waning(ctx, cx, cy, moonRadius, normalizedPhase, terminatorW),
                    lambda: _waxing(ctx, cx, cy, moonRadius, normalizedPhase, terminatorW),
                )

                # Date display
                ctx.painter.set_color(0xFFFFFFFF).set_text_size(
                    (ctx.rf(24.0) * density).to_float()).commit()
                offset_text = ctx.text_merge(
                    ctx.text_create_id("Days Offset: "),
                    ctx.create_text_from_float(daysOffset.to_float(), 4, 1, 0),
                )
                ctx.draw_text_anchored(
                    offset_text,
                    cx.to_float(),
                    (cy + moonRadius + ctx.rf(40.0) * density).to_float(),
                    0.5, 0.0, 0)

    return ctx


def _waning(ctx, cx, cy, moonRadius, normalizedPhase, terminatorW):
    """Waning (Left side illuminated) - phase > 0.5"""
    ctx.draw_sector(
        (cx - moonRadius).to_float(),
        (cy - moonRadius).to_float(),
        (cx + moonRadius).to_float(),
        (cy + moonRadius).to_float(),
        90.0, 180.0)
    ctx.if_else(
        normalizedPhase - 0.75,
        lambda: _waning_crescent(ctx, cx, cy, moonRadius, terminatorW),
        lambda: _waning_gibbous(ctx, cx, cy, moonRadius, terminatorW),
    )


def _waning_crescent(ctx, cx, cy, moonRadius, terminatorW):
    """0.75 to 1.0 (Crescent)"""
    ctx.painter.set_color(0xFF333333).commit()
    ctx.draw_oval(
        (cx - terminatorW).to_float(),
        (cy - moonRadius).to_float(),
        (cx + terminatorW).to_float(),
        (cy + moonRadius).to_float())


def _waning_gibbous(ctx, cx, cy, moonRadius, terminatorW):
    """0.5 to 0.75 (Gibbous)"""
    ctx.draw_oval(
        (cx - terminatorW).to_float(),
        (cy - moonRadius).to_float(),
        (cx + terminatorW).to_float(),
        (cy + moonRadius).to_float())


def _waxing(ctx, cx, cy, moonRadius, normalizedPhase, terminatorW):
    """Waxing (Right side illuminated) - phase <= 0.5"""
    ctx.draw_sector(
        (cx - moonRadius).to_float(),
        (cy - moonRadius).to_float(),
        (cx + moonRadius).to_float(),
        (cy + moonRadius).to_float(),
        270.0, 180.0)
    ctx.if_else(
        normalizedPhase - 0.25,
        lambda: _waxing_gibbous(ctx, cx, cy, moonRadius, terminatorW),
        lambda: _waxing_crescent(ctx, cx, cy, moonRadius, terminatorW),
    )


def _waxing_gibbous(ctx, cx, cy, moonRadius, terminatorW):
    """0.25 to 0.5 (Gibbous)"""
    ctx.draw_oval(
        (cx - terminatorW).to_float(),
        (cy - moonRadius).to_float(),
        (cx + terminatorW).to_float(),
        (cy + moonRadius).to_float())


def _waxing_crescent(ctx, cx, cy, moonRadius, terminatorW):
    """0 to 0.25 (Crescent)"""
    ctx.painter.set_color(0xFF333333).commit()
    ctx.draw_oval(
        (cx - terminatorW).to_float(),
        (cy - moonRadius).to_float(),
        (cx + terminatorW).to_float(),
        (cy + moonRadius).to_float())


if __name__ == '__main__':
    ctx = demo_moon_phases()
    data = ctx.encode()
    outdir = os.path.join(os.path.dirname(__file__), '..', 'output')
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, 'moon_phases.rc')
    ctx.save(path)
    print(f"moon_phases: {len(data)} bytes -> {path}")

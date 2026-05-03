"""Interactive Mandelbrot fractal -> shader_mandelbrot.rc

INTERACTIVE: drag to pan around the fractal. The view auto-zooms in
and out slowly via `iTime` so you can park anywhere and watch detail
emerge / unfold.

For each pixel the shader iterates z = z² + c up to 96 times, counts
when |z| > 2, and maps the iteration count to a smooth color gradient.
Mapped through a spectrum (blue → cyan → yellow → orange → white) so
the structure of the fractal is legible.

`iMouse` is bound to TOUCH_POS_X/Y. While no touch ever, the view
defaults to a classic seahorse-valley region (-0.745, 0.105). Drag the
canvas to move the view center anywhere on the complex plane.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RcContext, Rc
from rcreate.modifiers import RecordingModifier


PROFILE_ANDROIDX = 0x200


MANDELBROT_AGSL = """
uniform float2 iResolution;
uniform float iTime;
uniform float2 iMouse;

half4 main(float2 fragCoord) {
    // Centered, aspect-corrected plane coords
    float2 uv = (fragCoord - 0.5 * iResolution.xy) / iResolution.y;

    // Slow breathing zoom: scale oscillates 0.6..1.6 over ~13 sec.
    // Smaller scale = deeper zoom.
    float zoom = 1.1 + 0.5 * sin(iTime * 0.18);

    // Pan: until the user touches, anchor to a classic seahorse-valley center.
    // Touch position lerps the view center.
    float2 mouse = iMouse / iResolution.xy;          // 0..1
    float touched = step(1.0, length(iMouse));        // 0 if iMouse == (0,0)
    float2 default_center = float2(-0.745, 0.105);
    float2 touch_center = float2((mouse.x - 0.5) * 3.0 - 0.5,
                                 (mouse.y - 0.5) * 2.0);
    float2 c_center = mix(default_center, touch_center, touched);

    float2 c = uv * zoom + c_center;

    float2 z = float2(0.0, 0.0);
    float iter = 0.0;
    float max_iter = 96.0;
    for (int i = 0; i < 96; i++) {
        if (dot(z, z) > 4.0) break;
        z = float2(z.x * z.x - z.y * z.y, 2.0 * z.x * z.y) + c;
        iter += 1.0;
    }

    // Inside the set: deep navy.
    // Outside: smooth gradient by iteration fraction.
    float t = iter / max_iter;

    float3 col;
    if (iter >= max_iter) {
        col = float3(0.04, 0.04, 0.10);
    } else {
        // Smooth band — five-stop palette.
        float3 c1 = float3(0.05, 0.10, 0.30);   // deep blue
        float3 c2 = float3(0.10, 0.55, 0.90);   // cyan
        float3 c3 = float3(0.95, 0.85, 0.30);   // yellow
        float3 c4 = float3(1.00, 0.45, 0.10);   // orange
        float3 c5 = float3(1.00, 1.00, 1.00);   // white
        if (t < 0.25)      col = mix(c1, c2, t / 0.25);
        else if (t < 0.55) col = mix(c2, c3, (t - 0.25) / 0.30);
        else if (t < 0.80) col = mix(c3, c4, (t - 0.55) / 0.25);
        else               col = mix(c4, c5, (t - 0.80) / 0.20);
    }

    return half4(col, 1.0);
}
"""


def demo_shader_mandelbrot():
    width, height = 500, 500
    ctx = RcContext(width, height, "Mandelbrot",
                    api_level=8, profiles=PROFILE_ANDROIDX)

    shader_id = ctx.create_shader(MANDELBROT_AGSL) \
        .set_float_uniform("iResolution", float(width), float(height)) \
        .set_float_uniform("iTime", Rc.Time.CONTINUOUS_SEC) \
        .set_float_uniform("iMouse", Rc.Touch.POSITION_X, Rc.Touch.POSITION_Y) \
        .commit()

    with ctx.root():
        with ctx.box(RecordingModifier().fill_max_size().background(0xFF000000),
                     Rc.Layout.START, Rc.Layout.START):
            with ctx.canvas(RecordingModifier().fill_max_size()):
                ctx.painter.set_shader(shader_id).commit()
                ctx.draw_rect(0.0, 0.0, float(width), float(height))
                ctx.painter.set_shader(0).commit()

    return ctx


if __name__ == '__main__':
    ctx = demo_shader_mandelbrot()
    data = ctx.encode()
    outdir = os.path.join(os.path.dirname(__file__), '..', 'output')
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, 'shader_mandelbrot.rc')
    ctx.save(path)
    print(f"shader_mandelbrot: {len(data)} bytes -> {path}")

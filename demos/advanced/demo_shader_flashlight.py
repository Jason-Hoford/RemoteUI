"""Shader flashlight — drag the cursor to reveal the field.

INTERACTIVE shader demo. The fragment shader takes (iMouse.x, iMouse.y)
as a uniform bound to the live TOUCH_POS_X / TOUCH_POS_Y variables.
Pixels far from the cursor are dim; pixels close to the cursor reveal
a noisy animated field underneath.

This is the "spirit of pygame_noise_3d" done properly — with a real
fragment shader, not faked with vector primitives. Background is a
Voronoi-like cell pattern (cheap pure-noise via dot+fract); the
flashlight is a smooth radial gate computed from distance to (iMouse).

Tiny: shader source is ~25 lines of AGSL; total .rc well under 2 KB.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RcContext, Rc
from rcreate.modifiers import RecordingModifier


PROFILE_ANDROIDX = 0x200


FLASHLIGHT_AGSL = """
uniform float2 iResolution;
uniform float2 iMouse;
uniform float iTime;

// Hash → pseudo-random 2D vector in [0,1)
float2 hash22(float2 p) {
    float n = sin(dot(p, float2(127.1, 311.7))) * 43758.5453;
    return fract(float2(n, n * 1.31));
}

// Animated value-noise: sample 4 cell corners and bilerp
float vnoise(float2 p, float t) {
    float2 i = floor(p);
    float2 f = fract(p);
    float2 u = f * f * (3.0 - 2.0 * f);
    float a = hash22(i + float2(0.0, 0.0)).x;
    float b = hash22(i + float2(1.0, 0.0)).x;
    float c = hash22(i + float2(0.0, 1.0)).x;
    float d = hash22(i + float2(1.0, 1.0)).x;
    // Slight time wobble
    a += 0.1 * sin(t + a * 6.0);
    b += 0.1 * sin(t * 1.1 + b * 6.0);
    c += 0.1 * sin(t * 0.9 + c * 6.0);
    d += 0.1 * sin(t * 1.2 + d * 6.0);
    return mix(mix(a, b, u.x), mix(c, d, u.x), u.y);
}

half4 main(float2 fragCoord) {
    float2 uv = fragCoord / iResolution.xy;

    // Field — multi-octave noise, animates with iTime
    float n = 0.0;
    n += 0.55 * vnoise(uv * 6.0,  iTime * 0.5);
    n += 0.30 * vnoise(uv * 14.0, iTime * 0.7);
    n += 0.15 * vnoise(uv * 28.0, iTime * 0.4);

    // Color the field: cool→warm gradient
    float3 cool = float3(0.10, 0.30, 0.55);
    float3 warm = float3(0.95, 0.55, 0.20);
    float3 field = mix(cool, warm, n);

    // Flashlight: distance from cursor (in pixels)
    float2 m = iMouse;
    // If TOUCH_POS hasn't been set yet (m == 0,0), park the light off-screen.
    if (m.x < 1.0 && m.y < 1.0) m = float2(-9999.0, -9999.0);
    float d = length(fragCoord - m);

    // Smooth gate: full brightness within `inner`, fades to `dim` at `outer`.
    float inner = 60.0;
    float outer = 220.0;
    float gate = 1.0 - smoothstep(inner, outer, d);

    // Floor brightness (so the rest of the canvas isn't pitch black)
    float dim = 0.08;
    float bright = mix(dim, 1.0, gate);

    return half4(field * bright, 1.0);
}
"""


def demo_shader_flashlight():
    width, height = 500, 500
    ctx = RcContext(width, height, "Flashlight Shader",
                    api_level=8, profiles=PROFILE_ANDROIDX)

    # iMouse takes the live touch position. Each component is a NaN-encoded
    # variable id; the shader receives the live value each frame.
    shader_id = ctx.create_shader(FLASHLIGHT_AGSL) \
        .set_float_uniform("iResolution", float(width), float(height)) \
        .set_float_uniform("iMouse", Rc.Touch.POSITION_X, Rc.Touch.POSITION_Y) \
        .set_float_uniform("iTime", Rc.Time.CONTINUOUS_SEC) \
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
    ctx = demo_shader_flashlight()
    data = ctx.encode()
    outdir = os.path.join(os.path.dirname(__file__), '..', 'output')
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, 'shader_flashlight.rc')
    ctx.save(path)
    print(f"shader_flashlight: {len(data)} bytes -> {path}")

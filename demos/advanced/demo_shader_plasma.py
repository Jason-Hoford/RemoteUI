"""Animated plasma shader -> shader_plasma.rc

Classic shadertoy-style plasma effect: per-pixel color computed from a
small AGSL fragment shader. The shader's `iTime` uniform is bound to
the live ContinuousSec system variable, so the field animates without
any per-frame work on the .rc side.

Demonstrates: end-to-end AGSL pipeline. The .rc embeds the shader source
as text; the TS player transpiles AGSL → GLSL ES, compiles to WebGL2,
binds uniforms each frame, renders to an offscreen canvas, composites
back. Pure GPU work after the initial compile.

Replaces the wireframe-cube as the headliner for "RemoteCompose can do
shaders, not just vector animation."
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RcContext, Rc
from rcreate.modifiers import RecordingModifier


PROFILE_ANDROIDX = 0x200


PLASMA_AGSL = """
uniform float2 iResolution;
uniform float iTime;

half4 main(float2 fragCoord) {
    float2 uv = fragCoord / iResolution.xy;
    float2 p = uv * 2.0 - 1.0;
    p.x *= iResolution.x / iResolution.y;

    float t = iTime * 0.6;

    // Layered sines — classic plasma
    float v = 0.0;
    v += sin(p.x * 6.0 + t);
    v += sin(p.y * 4.0 + t * 1.3);
    v += sin((p.x + p.y) * 5.0 + t * 0.9);
    v += sin(length(p) * 8.0 - t * 1.6);
    v *= 0.25;  // -1..1

    // Map to a warm/cool gradient
    float3 col = float3(0.55 + 0.45 * sin(v * 3.14159),
                        0.40 + 0.45 * sin(v * 3.14159 + 2.094),
                        0.55 + 0.45 * sin(v * 3.14159 + 4.188));

    // Subtle vignette
    float d = length(p);
    col *= 1.0 - 0.35 * d * d;

    return half4(col, 1.0);
}
"""


def demo_shader_plasma():
    width, height = 500, 500
    ctx = RcContext(width, height, "Plasma Shader",
                    api_level=8, profiles=PROFILE_ANDROIDX)

    # Build the shader and bind iTime to the live time variable.
    # iResolution is bound as a literal — canvas size doesn't change at runtime.
    shader_id = ctx.create_shader(PLASMA_AGSL) \
        .set_float_uniform("iResolution", float(width), float(height)) \
        .set_float_uniform("iTime", Rc.Time.CONTINUOUS_SEC) \
        .commit()

    with ctx.root():
        with ctx.box(RecordingModifier().fill_max_size().background(0xFF000000),
                     Rc.Layout.START, Rc.Layout.START):
            with ctx.canvas(RecordingModifier().fill_max_size()):
                # Bind the shader to the painter, then draw a rect that fills
                # the canvas — the rect's interior is rendered by the shader.
                ctx.painter.set_shader(shader_id).commit()
                ctx.draw_rect(0.0, 0.0, float(width), float(height))

                # Reset shader so any subsequent draw isn't tinted by it.
                ctx.painter.set_shader(0).commit()

    return ctx


if __name__ == '__main__':
    ctx = demo_shader_plasma()
    data = ctx.encode()
    outdir = os.path.join(os.path.dirname(__file__), '..', 'output')
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, 'shader_plasma.rc')
    ctx.save(path)
    print(f"shader_plasma: {len(data)} bytes -> {path}")

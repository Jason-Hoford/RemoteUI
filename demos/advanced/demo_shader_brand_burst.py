"""Animated brand-burst mark -> shader_brand_burst.rc

A procedural radiating-petal mark with a glowing center, slowly rotating,
each petal's reach pulsing on its own phase so the bloom breathes.

This is a "spirit-of-Anthropic" generic brand burst — not claiming to BE
the official logo, but evokes the AI-energy aesthetic. Useful as a
deck opener: "the AI just generated this brand mark in 1.5 KB of code."

Pure shader, sub-2 KB.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RcContext, Rc
from rcreate.modifiers import RecordingModifier


PROFILE_ANDROIDX = 0x200


BURST_AGSL = """
uniform float2 iResolution;
uniform float iTime;

half4 main(float2 fragCoord) {
    float2 center = iResolution.xy * 0.5;
    float2 p = fragCoord - center;
    float r = length(p);
    float ang = atan(p.y, p.x);            // [-π, π]

    float N = 12.0;
    float spin = iTime * 0.18;             // slow rotation
    float a = ang + spin;

    // Petal phase: 0..1 within the current petal wedge
    float petalGrid  = a * N / 6.2832 + 0.5;
    float petalPhase = fract(petalGrid);
    float petalIdx   = floor(petalGrid);

    // Each petal pulses with its own offset
    float pulse = 0.5 + 0.5 * sin(iTime * 1.4 + petalIdx * 0.55);

    // Bell-shaped petal silhouette — 1 at axis, 0 at edges
    float petalShape = sin(petalPhase * 3.1416);
    petalShape = pow(petalShape, 1.6);

    // Petal max radius (in px)
    float maxR = (130.0 + pulse * 70.0) * petalShape;

    // Radial intensity inside the petal
    float petalI = 1.0 - smoothstep(0.0, maxR, r);

    // Central glowing core
    float core = 1.0 - smoothstep(15.0, 90.0, r);

    // Combine
    float intensity = max(petalI, core);

    // Two-stop warm palette: orange-red outer, gold at the centre
    float3 outerCol = float3(1.00, 0.42, 0.08);
    float3 innerCol = float3(1.00, 0.92, 0.55);
    float3 col = mix(outerCol, innerCol, core);

    // Subtle dark wash for the unlit area
    float3 bg = float3(0.06, 0.04, 0.02);
    col = col * intensity + bg * (1.0 - intensity);

    // Soft inner ring at ~50 px to give the centre a "lens" feel
    float ring = exp(-pow((r - 48.0) / 8.0, 2.0)) * 0.6;
    col += float3(ring * 0.9, ring * 0.7, ring * 0.4);

    return half4(col, 1.0);
}
"""


def demo_shader_brand_burst():
    width, height = 500, 500
    ctx = RcContext(width, height, "Brand Burst",
                    api_level=8, profiles=PROFILE_ANDROIDX)

    shader_id = ctx.create_shader(BURST_AGSL) \
        .set_float_uniform("iResolution", float(width), float(height)) \
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
    ctx = demo_shader_brand_burst()
    data = ctx.encode()
    outdir = os.path.join(os.path.dirname(__file__), '..', 'output')
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, 'shader_brand_burst.rc')
    ctx.save(path)
    print(f"shader_brand_burst: {len(data)} bytes -> {path}")

"""Matrix-style code rain shader -> shader_matrix_rain.rc

Vertical streams of glyph-sized cells fall down the screen at varying
speeds. Each column has its own seed (column index → speed, head offset).
Per-cell flicker on a slower clock makes individual cells "blink" like
they're refreshing.

Pure shader, sub-1 KB. Reads instantly as "AI generating code."
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RcContext, Rc
from rcreate.modifiers import RecordingModifier


PROFILE_ANDROIDX = 0x200


MATRIX_AGSL = """
uniform float2 iResolution;
uniform float iTime;

float hash11(float p) {
    return fract(sin(p * 73.13) * 43758.5453);
}

float hash21(float2 p) {
    return fract(sin(dot(p, float2(127.1, 311.7))) * 43758.5453);
}

half4 main(float2 fragCoord) {
    // Column / row cell grid
    float colW = 14.0;
    float rowH = 16.0;
    float2 cell = float2(floor(fragCoord.x / colW),
                         floor(fragCoord.y / rowH));

    // Each column has its own speed and head offset
    float colSeed   = hash11(cell.x);
    float speed     = 90.0 + colSeed * 240.0;
    float headOff   = colSeed * 1500.0;

    // Head position (vertical) for this column, wrapping past the bottom
    float trackLen  = iResolution.y + 350.0;
    float headY     = mod(iTime * speed + headOff, trackLen) - 175.0;

    // Distance from this pixel to the head (positive = pixel is above head's wake)
    float distToHead = headY - fragCoord.y;
    float trail = 320.0;

    // Brightness fades from 1 at head down to 0 over `trail` pixels
    float bright = 0.0;
    if (distToHead >= 0.0 && distToHead < trail) {
        bright = 1.0 - distToHead / trail;
    }

    // Per-cell flicker: each cell refreshes its glyph every ~0.15 s
    float flickT  = floor(iTime * (4.0 + colSeed * 6.0));
    float cellRand = hash21(cell + float2(0.0, flickT));
    // Random characters use varying brightness — some bright, some dim
    float cellBright = 0.30 + cellRand * 0.70;

    // Glyph silhouette — within each cell, leave a vertical stripe pattern
    // so cells look like discrete "characters" rather than smooth blocks.
    float2 fcell = fract(fragCoord / float2(colW, rowH));
    float glyph = step(0.10, fcell.x) * step(fcell.x, 0.90)
                * step(0.10, fcell.y) * step(fcell.y, 0.90);

    // The very head pixel is white-ish, trailing fades green
    float v = bright * cellBright * glyph;
    float headHot = smoothstep(0.0, 24.0, distToHead) * (1.0 - smoothstep(0.0, 24.0, distToHead));
    // headHot is non-zero only near the head — boost for white tip
    float white = headHot * 2.5 * glyph;

    float r = v * 0.20 + white * 0.80;
    float g = v * 1.00 + white * 1.00;
    float b = v * 0.30 + white * 0.60;

    return half4(r, g, b, 1.0);
}
"""


def demo_shader_matrix_rain():
    width, height = 500, 600
    ctx = RcContext(width, height, "Matrix Rain",
                    api_level=8, profiles=PROFILE_ANDROIDX)

    shader_id = ctx.create_shader(MATRIX_AGSL) \
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
    ctx = demo_shader_matrix_rain()
    data = ctx.encode()
    outdir = os.path.join(os.path.dirname(__file__), '..', 'output')
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, 'shader_matrix_rain.rc')
    ctx.save(path)
    print(f"shader_matrix_rain: {len(data)} bytes -> {path}")

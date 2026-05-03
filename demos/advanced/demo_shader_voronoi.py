"""Animated Voronoi cells -> shader_voronoi.rc

A grid of cells (Worley noise) where each cell's site point drifts in
a small loop driven by `iTime`. Pixel color is determined by which
cell it falls in; thin dark borders trace the cell boundaries.

Pure shader, ~1.5 KB. Hypnotic / organic aesthetic — different from
the cool/scientific look of the rest of the deck.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RcContext, Rc
from rcreate.modifiers import RecordingModifier


PROFILE_ANDROIDX = 0x200


VORONOI_AGSL = """
uniform float2 iResolution;
uniform float iTime;

// 2D hash → 2D vector in [0,1)²
float2 hash22(float2 p) {
    p = float2(dot(p, float2(127.1, 311.7)),
               dot(p, float2(269.5, 183.3)));
    return fract(sin(p) * 43758.5453);
}

half4 main(float2 fragCoord) {
    // 7 cells across the longer dimension
    float scale = 7.0;
    float2 uv = fragCoord / iResolution.y * scale;

    float2 i_cell = floor(uv);
    float2 f_cell = fract(uv);

    // Closest and second-closest distances + the closest cell's id.
    float d1 = 9.0;
    float d2 = 9.0;
    float2 closest_id = float2(0.0, 0.0);

    // Float-counter loops dodge an AGSL-transpiler bug:
    // `int y = -1` becomes `int y = -1.0` because `-` and `1` tokenize
    // separately and the int-context heuristic only looks one token back.
    for (float yy = -1.0; yy <= 1.0; yy += 1.0) {
        for (float xx = -1.0; xx <= 1.0; xx += 1.0) {
            float2 neighbor = float2(xx, yy);
            float2 cell_id = i_cell + neighbor;

            // Each cell's site point oscillates in a small circle.
            float2 rnd = hash22(cell_id);
            float2 site = neighbor + 0.5 +
                          0.45 * sin(iTime * 0.6 + 6.2832 * rnd);

            float d = length(f_cell - site);
            if (d < d1) {
                d2 = d1;
                d1 = d;
                closest_id = cell_id;
            } else if (d < d2) {
                d2 = d;
            }
        }
    }

    // Color from cell id — cosine palette gives nicely separated hues.
    float h = hash22(closest_id).x;
    float3 col = 0.55 + 0.40 * cos(6.2832 * (h + float3(0.00, 0.33, 0.67)));

    // Border emphasis: dark line where d1 ≈ d2 (cell boundary).
    float border = smoothstep(0.0, 0.05, d2 - d1);
    col *= 0.15 + 0.85 * border;

    // Subtle radial vignette toward the cell center.
    col *= 0.65 + 0.35 * smoothstep(0.0, 0.5, d1);

    return half4(col, 1.0);
}
"""


def demo_shader_voronoi():
    width, height = 500, 500
    ctx = RcContext(width, height, "Voronoi",
                    api_level=8, profiles=PROFILE_ANDROIDX)

    shader_id = ctx.create_shader(VORONOI_AGSL) \
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
    ctx = demo_shader_voronoi()
    data = ctx.encode()
    outdir = os.path.join(os.path.dirname(__file__), '..', 'output')
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, 'shader_voronoi.rc')
    ctx.save(path)
    print(f"shader_voronoi: {len(data)} bytes -> {path}")

"""Pygame-style noise WIREFRAME cube — drag to reveal -> shader_noise_cube.rc

Faithful to pygame_noise_3d. In the original the cube wireframe is drawn
to STENCIL with line width 15, so cube_color only renders along the EDGE
bands — the interior shows bg_color. The cube appears as 12 noisy outlines
of drifted noise against a static bg.

Our shader does the same with a fragment-shader edge SDF:
  * Slab-method ray vs cube to find the front-face hit and back-face hit.
  * For each hit point, edgeDist = the SECOND-smallest distance to a face
    plane (smallest is the face we hit, second tells us how close we are
    to the edge of that face).
  * Pixel is "on a wireframe edge" iff either hit_front or hit_back has
    edgeDist below threshold → all 12 edges visible (front + back).

Drift is identical to pygame's sliding mode: bg = hash(fragCell);
fg = hash(fragCell + drift·iDriftTime). When idle, uActive=0 → the edges
sample bg too → cube vanishes (matches `final_cube_color = bg_color`
on pause).
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RcContext, Rc
from rcreate.modifiers import RecordingModifier
from rcreate.types.rfloat import rf_min, rf_max


PROFILE_ANDROIDX = 0x200


NOISE_CUBE_AGSL = """
uniform float2 iResolution;
uniform float iTime;
uniform float iDriftTime;
uniform float uActive;

float hash(float2 p) {
    return fract(sin(dot(p, float2(127.1, 311.7))) * 43758.5453);
}

mat3 rotX(float a) {
    float c = cos(a);
    float s = sin(a);
    return mat3(1.0, 0.0, 0.0,
                0.0,  c , -s ,
                0.0,  s ,  c );
}
mat3 rotY(float a) {
    float c = cos(a);
    float s = sin(a);
    return mat3( c , 0.0,  s ,
                0.0, 1.0, 0.0,
                -s , 0.0,  c );
}

// Distance from a hit point on the cube surface to the nearest cube edge.
// Smallest dtf component is the face we hit (~0); we return the
// SECOND-smallest, which tells us how close to an edge of that face.
float edgeDist(float3 p, float h) {
    float3 dtf = h - abs(p);
    float a = min(min(dtf.x, dtf.y), dtf.z);                // smallest
    float c = max(max(dtf.x, dtf.y), dtf.z);                // largest
    float b = dtf.x + dtf.y + dtf.z - a - c;                // middle
    return b;
}

half4 main(float2 fragCoord) {
    float2 uv = fragCoord / iResolution.xy;
    float2 p = (uv - 0.5) * 2.0;
    p.x *= iResolution.x / iResolution.y;

    // Rotation runs continuously; we just hide the cube via uActive when idle.
    mat3 R = rotX(iTime * 0.45) * rotY(iTime * 0.7);
    mat3 Rinv = transpose(R);
    float3 ro = Rinv * float3(p.x, p.y, 2.0);
    float3 rd = Rinv * float3(0.0, 0.0, -1.0);

    // Slab method against the unit cube.
    float h = 0.6;
    float3 invD = 1.0 / rd;
    float3 t0 = (float3(-h) - ro) * invD;
    float3 t1 = (float3( h) - ro) * invD;
    float3 tEnter3 = min(t0, t1);
    float3 tExit3  = max(t0, t1);
    float tEnter = max(max(tEnter3.x, tEnter3.y), tEnter3.z);
    float tExit  = min(min(tExit3.x,  tExit3.y),  tExit3.z);
    float in_silhouette = step(tEnter, tExit);

    // Front-face and back-face hit points in cube-local space.
    float3 hit_f = ro + tEnter * rd;
    float3 hit_b = ro + tExit  * rd;

    // Wireframe edge mask — pixel is on an edge if either hit point is
    // within `edge_thick` of two face planes simultaneously. Both front
    // and back hits contribute, so all 12 cube edges are visible.
    // 0.06 in cube-local ≈ 15 px on a 500-wide canvas — matches pygame's
    // glLineWidth(15.0).
    float edge_thick = 0.06;
    float ed_f = edgeDist(hit_f, h);
    float ed_b = edgeDist(hit_b, h);
    float on_edge_f = 1.0 - step(edge_thick, ed_f);
    float on_edge_b = 1.0 - step(edge_thick, ed_b);
    float edge = max(on_edge_f, on_edge_b) * in_silhouette;

    // Same chunky cell-hash everywhere; inside drifts by iDriftTime.
    // Pure vertical scroll matches pygame's default direction (0, 1).
    // Wireframe rotation provides the 3D illusion; the noise itself
    // moves only in 2D — let the eye combine the two.
    float cellSize = 6.0;
    float2 driftVec = float2(0.0, 250.0);
    float2 outerCell = floor(fragCoord / cellSize);
    float2 innerCell = floor((fragCoord + driftVec * iDriftTime) / cellSize);
    float bg = hash(outerCell);
    float fg = hash(innerCell);

    // Edges show drifted noise; interior shows bg. Idle → uActive=0 → bg
    // everywhere → cube vanishes (matches pygame's pause behaviour).
    float alpha = edge * uActive;
    float v = mix(bg, fg, alpha);

    // Continuous grayscale (no quantization) — matches pygame's float32 → 256-level
    // texture. Each cell still gets one constant value (chunky 6-px blocks),
    // but the brightness covers the full grayscale gradient like the original.
    v = clamp(v, 0.0, 1.0);

    return half4(v, v, v, 1.0);
}
"""


def demo_shader_noise_cube():
    width, height = 500, 500
    ctx = RcContext(width, height, "Noise Cube",
                    api_level=8, profiles=PROFILE_ANDROIDX)

    # Build uActive = clamp(1 − (animationTime − TOUCH_EVENT_TIME) / 0.7, 0, 1)
    # as a flushed expression. Pass its NaN id as a float uniform; the engine
    # re-evaluates it each frame and the shader sees a live 0..1 number.
    t       = ctx.animationTime()
    event_t = ctx.to_rf(Rc.Touch.TOUCH_EVENT_TIME)
    dt      = (t - event_t).flush()
    threshold = 0.7
    u_active = rf_min(1.0, rf_max(0.0, 1.0 - dt / threshold)).flush()

    shader_id = ctx.create_shader(NOISE_CUBE_AGSL) \
        .set_float_uniform("iResolution", float(width), float(height)) \
        .set_float_uniform("iTime",      Rc.Time.CONTINUOUS_SEC) \
        .set_float_uniform("iDriftTime", Rc.Touch.TOUCH_EVENT_TIME) \
        .set_float_uniform("uActive",    u_active.to_float()) \
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
    ctx = demo_shader_noise_cube()
    data = ctx.encode()
    outdir = os.path.join(os.path.dirname(__file__), '..', 'output')
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, 'shader_noise_cube.rc')
    ctx.save(path)
    print(f"shader_noise_cube: {len(data)} bytes -> {path}")

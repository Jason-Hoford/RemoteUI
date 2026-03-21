"""Port of Cube3D.kt cube3d() — 3D cube with projection, matrix, and backface culling."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RcContext, Modifier, Rc
from rcreate.rc import Rc
from rcreate.types.rfloat import RFloat, rf_min
from rcreate.types.rmatrix import RMatrix
from rcreate.remote_path import RemotePath

PROFILE_ANDROIDX = 0x200
STYLE_FILL = Rc.Paint.STYLE_FILL
STYLE_STROKE = Rc.Paint.STYLE_STROKE
FE = Rc.FloatExpression
MO = Rc.MatrixOp

# Compose Color constants (toArgb)
COLOR_DARK_GRAY = 0xFF444444
COLOR_LIGHT_GRAY = 0xFFCCCCCC
COLOR_BLACK = 0xFF000000
COLOR_RED = 0xFFFF0000
COLOR_GREEN = 0xFF00FF00
COLOR_BLUE = 0xFF0000FF
COLOR_YELLOW = 0xFFFFFF00
COLOR_MAGENTA = 0xFFFF00FF
COLOR_CYAN = 0xFF00FFFF

# Header tag constants
DOC_WIDTH = 5
DOC_HEIGHT = 6
DOC_DESIRED_FPS = 8
DOC_CONTENT_DESCRIPTION = 9


def demo_cube3d():
    vertices = [
        [-1.0, -1.0, -1.0],
        [ 1.0, -1.0, -1.0],
        [ 1.0,  1.0, -1.0],
        [-1.0,  1.0, -1.0],
        [-1.0, -1.0,  1.0],
        [ 1.0, -1.0,  1.0],
        [ 1.0,  1.0,  1.0],
        [-1.0,  1.0,  1.0],
    ]
    # tv is the transformed vertices array (will hold float expression results)
    tv = [
        [0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0],
    ]

    faces = [
        0, 1, 2, 3,  # Front face
        1, 5, 6, 2,  # Right face
        5, 4, 7, 6,  # Back face
        4, 0, 3, 7,  # Left face
        3, 2, 6, 7,  # Top face
        4, 5, 1, 0,  # Bottom face
    ]

    # The Kotlin code uses addHeaderParam to modify global state.
    # The reference file was generated with params containing:
    # DOC_DESIRED_FPS=120, DOC_CONTENT_DESCRIPTION="Cube",
    # DOC_WIDTH=400, DOC_HEIGHT=400 (default demo7 params).
    # No DOC_PROFILES in the params.
    # HashMap iteration order for keys {5,6,8,9} with capacity>=16:
    # bucket 5, 6, 8, 9 -> DOC_WIDTH, DOC_HEIGHT, DOC_DESIRED_FPS, DOC_CONTENT_DESCRIPTION

    # The reference .rc was generated with residual global state from prior demos:
    # DOC_WIDTH=500, DOC_HEIGHT=500, DOC_PROFILES=0x200 (from demoGraphs2).
    # cube3d only sets DOC_CONTENT_DESCRIPTION="Cube" and DOC_DESIRED_FPS=120.
    # HashMap iteration order with keys {5,6,8,9,14} at capacity 16:
    # bucket 5,6,8,9,14 -> DOC_WIDTH, DOC_HEIGHT, DOC_DESIRED_FPS, DOC_CONTENT_DESCRIPTION, DOC_PROFILES
    DOC_PROFILES = 14
    ctx = RcContext(500, 500, "Cube",
                    api_level=7, profiles=PROFILE_ANDROIDX,
                    extra_tags={DOC_DESIRED_FPS: 120},
                    header_tag_order=[DOC_DESIRED_FPS, DOC_CONTENT_DESCRIPTION,
                                     DOC_WIDTH, DOC_HEIGHT, DOC_PROFILES])

    with ctx.root():
        with ctx.box(Modifier().fill_max_width().fill_max_height()):
            with ctx.canvas(Modifier().fill_max_width().fill_max_height()):
                width = ctx.ComponentWidth()
                height = ctx.ComponentHeight()

                centerX = width / 2.0
                centerY = height / 2.0
                radius = rf_min(centerX, centerY)

                cx = centerX.to_float()
                cy = centerY.to_float()
                ctx.painter.set_color(COLOR_DARK_GRAY).set_style(STYLE_FILL).commit()
                ctx.draw_circle(cx, cy, radius.to_float())

                # =============== Fixed String Draw on Path ==============
                spin = ctx.rf(Rc.Time.CONTINUOUS_SEC) * 2.0
                rot = ((spin * 20.0) % 360.0).to_float()

                t1 = ((spin / 18.0).round() + 1.0) % 3.0
                t1 = t1.sign()
                t2 = ((spin / 18.0).round()) % 3.0
                t2 = t2.sign()

                rotX = (ctx.rf(rot) * t1).to_float()
                rotY = (ctx.rf(rot) * t2).to_float()

                world = RMatrix(ctx,
                    6.0, MO.TRANSLATE_Z,
                    rotX, MO.ROT_X,
                    rotY, MO.ROT_Y,
                )

                fov = 60.0
                aspect = 1.0
                near = 0.1
                far = 100.0
                sx = (ctx.rf(cx) * 0.4).to_float()
                sy = (ctx.rf(cx) * -0.4).to_float()
                pMatrix = RMatrix(ctx,
                    fov, aspect, near, far, MO.PROJECTION,
                    sx, sy, MO.SCALE2,
                )

                i = 0
                while i < len(vertices):
                    v3 = world.mult3(vertices[i][0], vertices[i][1], vertices[i][2])
                    pm = pMatrix.projection_mult(v3.x, v3.y, v3.z)
                    tv[i][0] = (ctx.rf(pm[0]) + ctx.rf(cx)).to_float()
                    tv[i][1] = (ctx.rf(pm[1]) + ctx.rf(cy)).to_float()
                    tv[i][2] = pm[2]
                    i += 1

                i = 0
                paths = []
                dir_arr = [0.0] * 6

                while i < len(faces):
                    f1 = faces[i]
                    f2 = faces[i + 1]
                    f3 = faces[i + 2]
                    f4 = faces[i + 3]

                    path = RemotePath()
                    path.move_to(tv[f1][0], tv[f1][1])
                    path.line_to(tv[f2][0], tv[f2][1])
                    path.line_to(tv[f3][0], tv[f3][1])
                    path.line_to(tv[f4][0], tv[f4][1])
                    path.close()
                    paths.append(ctx.add_path_data(path.to_float_array()))

                    fx1 = ctx.rf(tv[f1][0])
                    fy1 = ctx.rf(tv[f1][1])
                    fx2 = ctx.rf(tv[f2][0])
                    fy2 = ctx.rf(tv[f2][1])
                    fx3 = ctx.rf(tv[f3][0])
                    fy3 = ctx.rf(tv[f3][1])

                    dir_arr[i // 4] = (
                        (fx1 - fx2) * (fy3 - fy2) - (fy1 - fy2) * (fx3 - fx2)
                    ).to_float()

                    i += 4

                ctx.painter.set_shader(0).set_color(COLOR_LIGHT_GRAY).set_style(STYLE_FILL).commit()
                colors = [
                    COLOR_RED,
                    COLOR_GREEN,
                    COLOR_BLUE,
                    COLOR_YELLOW,
                    COLOR_MAGENTA,
                    COLOR_CYAN,
                ]
                for p in range(6):
                    ctx.conditional_operations(Rc.Condition.GT, dir_arr[p], 0.0)
                    ctx.painter.set_color(colors[p]).commit()
                    ctx.draw_path(paths[p])
                    ctx.end_conditional_operations()

                ctx.painter \
                    .set_color(COLOR_BLACK) \
                    .set_stroke_join(1) \
                    .set_stroke_width(5.0) \
                    .set_style(STYLE_STROKE) \
                    .commit()

                for p in range(6):
                    ctx.conditional_operations(Rc.Condition.GT, dir_arr[p], 0.0)
                    ctx.draw_path(paths[p])
                    ctx.end_conditional_operations()

    return ctx


if __name__ == '__main__':
    ctx = demo_cube3d()
    data = ctx.encode()
    outdir = os.path.join(os.path.dirname(__file__), '..', 'output')
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, 'cube3d.rc')
    ctx.save(path)
    print(f"cube3d: {len(data)} bytes -> {path}")

    # Compare with reference
    ref_path = os.path.join(os.path.dirname(__file__), '..', '..',
                            'integration-tests', 'player-view-demos',
                            'src', 'main', 'res', 'raw', 'cube3d.rc')
    if os.path.exists(ref_path):
        with open(ref_path, 'rb') as f:
            ref = f.read()
        if data == ref:
            print("MATCH: byte-identical to reference")
        else:
            print(f"DIFF: generated {len(data)} bytes vs reference {len(ref)} bytes")
            # Find first difference
            for i in range(min(len(data), len(ref))):
                if data[i] != ref[i]:
                    print(f"  First diff at byte {i}: generated 0x{data[i]:02x} vs reference 0x{ref[i]:02x}")
                    break
    else:
        print(f"Reference not found: {ref_path}")

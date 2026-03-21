"""Maze/particle demos. Port of DemoParticles.kt: maze(), pmaze1(), pmaze2().

Generates: maze.rc, maze1.rc, maze2.rc

Demonstrates:
- Maze generation (ported from ExampleUtils.Maze Java code)
- Particle systems with wall collision
- Accelerometer input (gravity-driven particles)
- Path drawing (maze walls)
- Float arrays for wall lookup tables
- particlesComparison for bounce detection
- Color expressions (HSV) for per-particle coloring
"""
import sys
import os
import math
import struct
import random

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RcContext, Modifier, Rc, RemoteComposeWriter
from rcreate.modifiers import RecordingModifier
from rcreate.types.nan_utils import as_nan, id_from_nan
from rcreate.types.rfloat import RFloat, rf_clamp, rf_min, rf_max, rf_abs, _to_array

PROFILE_ANDROIDX = 0x200
PROFILE_EXPERIMENTAL = 0x1

FE = Rc.FloatExpression
STYLE_FILL = Rc.Paint.STYLE_FILL
STYLE_STROKE = Rc.Paint.STYLE_STROKE


def _f32(v):
    """Round to float32 precision (matches Java float arithmetic)."""
    return struct.unpack('>f', struct.pack('>f', v))[0]


# ============================================================================
# Maze generation — ported from ExampleUtils.Maze (Java)
# ============================================================================

MASK_LEFT = 1
MASK_RIGHT = 2
MASK_TOP = 4
MASK_BOTTOM = 8


def gen_maze(w, h, seed):
    """Generate a maze. Returns byte array with wall bits (1=left, 2=right, 4=top, 8=bottom)."""
    left_id = 1
    right_id = 2
    top_id = 4
    bottom_id = 8
    dir_table = [-1, 1, -w, w]
    dir_bit = [left_id, right_id, top_id, bottom_id]
    op_dir_bit = [right_id, left_id, bottom_id, top_id]
    visited = 16
    size = w * h
    maze = bytearray([left_id | right_id | top_id | bottom_id] * size)

    for x in range(w):
        maze[x] &= ~top_id & 0xFF
        maze[x + (h - 1) * w] &= ~bottom_id & 0xFF
    for y in range(h):
        maze[y * w] &= ~left_id & 0xFF
        maze[y * w + (w - 1)] &= ~right_id & 0xFF

    surface = [0] * size
    count = 0
    r = random.Random(seed)
    start = r.randint(0, size - 1)
    surface[count] = start
    maze[start] |= visited
    count += 1

    while count < size:
        point = r.randint(0, count * 4 - 1)
        d = point % 4
        point //= 4
        s = surface[point]
        if (maze[s] & dir_bit[d]) == 0:
            continue
        neighbour = s + dir_table[d]
        if (maze[neighbour] & visited) != 0:
            continue
        maze[neighbour] |= visited
        maze[neighbour] &= ~op_dir_bit[d] & 0xFF
        maze[s] &= ~dir_bit[d] & 0xFF
        surface[count] = neighbour
        count += 1

    for x in range(w):
        maze[x] |= top_id
        maze[x + (h - 1) * w] |= bottom_id
    for y in range(h):
        maze[y * w] |= left_id
        maze[y * w + (w - 1)] |= right_id

    return bytes(maze)


def gen_path(maze, mw, mh):
    """Generate path data from maze. Returns list of floats (RemotePath format)."""
    w = 1000
    h = 1000
    wx = _f32(w / mw)
    wy = _f32(h / mh)

    coords = []
    for y in range(mh):
        for x in range(mw):
            p = x + mw * y
            m = maze[p]
            has_left = (m & 1) != 0
            has_right = (m & 2) != 0
            has_top = (m & 4) != 0
            has_bottom = (m & 8) != 0
            px = _f32(x * wx)
            py = _f32(y * wy)

            if has_left:
                coords.extend([as_nan(10), px, py])  # MOVE
                coords.extend([as_nan(11), 0.0, 0.0, px, _f32(py + wy)])  # LINE
            if has_right:
                coords.extend([as_nan(10), _f32(px + wx), py])  # MOVE
                coords.extend([as_nan(11), 0.0, 0.0, _f32(px + wx), _f32(py + wy)])  # LINE
            if has_bottom:
                coords.extend([as_nan(10), px, _f32(py + wy)])  # MOVE
                coords.extend([as_nan(11), 0.0, 0.0, _f32(px + wx), _f32(py + wy)])  # LINE
            if has_top:
                coords.extend([as_nan(10), px, py])  # MOVE
                coords.extend([as_nan(11), 0.0, 0.0, _f32(px + wx), py])  # LINE
    return coords


def gen_walls(maze, mw, mh):
    """Generate wall positions from maze. Returns [left, right, top, bottom] float arrays."""
    w = 1000
    h = 1000
    wall = [[0.0] * (mw * mh) for _ in range(4)]

    wx = _f32(w / mw)
    wy = _f32(h / mh)

    for y in range(mh):
        for x in range(mw):
            p = x + mw * y
            m = maze[p]
            has_left = (m & 1) != 0
            has_right = (m & 2) != 0
            has_top = (m & 4) != 0
            has_bottom = (m & 8) != 0
            px = _f32(x * wx)
            py = _f32(y * wy)
            wall[0][p] = px if has_left else wall[0][p - 1]
            wall[1][p] = _f32(px + wx) if has_right else float('nan')
            wall[2][p] = _f32(py + wy) if has_bottom else float('nan')
            wall[3][p] = py if has_top else wall[3][p - mw]

    # Fill NaN gaps for right walls (scan right to left)
    for y in range(mh):
        for x in range(mw - 2, -1, -1):
            p = x + mw * y
            if math.isnan(wall[1][p]):
                wall[1][p] = wall[1][p + 1]

    # Fill NaN gaps for bottom walls (scan bottom to top)
    for y in range(mh - 2, -1, -1):
        for x in range(mw):
            p = x + mw * y
            if math.isnan(wall[2][p]):
                wall[2][p] = wall[2][p + mw]

    return wall


# ============================================================================
# Helper functions for wall lookup and repulsion
# ============================================================================

def lookup(rc, array_nan, x, y, gap, max_val):
    """Look up wall position from array using grid coordinates.

    Matches Kotlin lookup() which uses * 10f for dim.
    """
    index = rf_clamp(0.0, max_val, (x / gap).floor()) + rf_clamp(0.0, max_val, (y / gap).floor()) * 10.0
    arr = RFloat(rc._writer, float(array_nan))
    return arr[index]


def lookup2(rc, array_nan, x, y, gap, max_val, dim):
    """Look up wall position from array using grid coordinates.

    Matches Kotlin lookup2() which uses dim for the multiplier.
    """
    index = rf_clamp(0.0, max_val, (x / gap).floor()) + rf_clamp(0.0, max_val, (y / gap).floor()) * float(dim)
    arr = RFloat(rc._writer, float(array_nan))
    return arr[index]


def h_wall_repel(rc, walls, x1, y1, gap, m_dim, w, h):
    """Horizontal wall repulsion force."""
    left, right, top, bottom = walls
    l_wall = lookup(rc, left, x1, y1, gap, m_dim - 1.0) * w / 1000.0
    r_wall = lookup(rc, right, x1, y1, gap, m_dim - 1.0) * w / 1000.0
    return 50.0 / (x1 - rc.rf(l_wall.to_float())).abs() - 50.0 / (x1 - rc.rf(r_wall.to_float())).abs()


def v_wall_repel(rc, walls, x1, y1, gap, m_dim, w, h):
    """Vertical wall repulsion force."""
    left, right, top, bottom = walls
    t_wall = lookup(rc, top, x1, y1, gap, m_dim - 1.0) * h / 1000.0
    b_wall = lookup(rc, bottom, x1, y1, gap, m_dim - 1.0) * h / 1000.0
    return 50.0 / (y1 - rc.rf(t_wall.to_float())).abs() - 50.0 / (y1 - rc.rf(b_wall.to_float())).abs()


def draw_related_walls(rc, walls, x1, y1, gap, m_dim, w, h):
    """Draw wall indicators near the ball position."""
    left, right, top, bottom = walls
    wr = rc._writer

    l_wall = lookup(rc, left, x1, y1, gap, m_dim - 1.0) * w / 1000.0
    wr.draw_rect(
        (l_wall - 2.0).to_float(),
        (y1 - gap / 2.0).to_float(),
        (l_wall + 3.0).to_float(),
        (y1 + gap / 2.0).to_float(),
    )

    r_wall = lookup(rc, right, x1, y1, gap, m_dim - 1.0) * h / 1000.0
    wr.draw_rect(
        (r_wall - 2.0).to_float(),
        (y1 - gap / 2.0).to_float(),
        (r_wall + 3.0).to_float(),
        (y1 + gap / 2.0).to_float(),
    )

    t_wall = lookup(rc, top, x1, y1, gap, m_dim - 1.0) * h / 1000.0
    wr.draw_rect(
        (x1 - gap / 2.0).to_float(),
        (t_wall - 2.0).to_float(),
        (x1 + gap / 2.0).to_float(),
        (t_wall + 3.0).to_float(),
    )

    b_wall = lookup(rc, bottom, x1, y1, gap, m_dim - 1.0) * h / 1000.0
    wr.draw_rect(
        (x1 - gap / 2.0).to_float(),
        (b_wall - 2.0).to_float(),
        (x1 + gap / 2.0).to_float(),
        (b_wall + 3.0).to_float(),
    )

    rc.painter.set_color(0x4F3D4572).commit()
    wr.draw_round_rect(
        l_wall.to_float(), t_wall.to_float(),
        r_wall.to_float(), b_wall.to_float(),
        500.0, 500.0,
    )


def draw_related_walls2(rc, walls, x1, y1, gap, m_dim, w, h):
    """Draw wall indicators for psMaze2 (uses lookup2 with dim parameter)."""
    left, right, top, bottom = walls
    wr = rc._writer

    l_wall = lookup2(rc, left, x1, y1, gap, m_dim - 1.0, m_dim) * w / 1000.0
    wr.draw_rect(
        (l_wall - 2.0).to_float(),
        (y1 - gap / 2.0).to_float(),
        (l_wall + 3.0).to_float(),
        (y1 + gap / 2.0).to_float(),
    )

    r_wall = lookup2(rc, right, x1, y1, gap, m_dim - 1.0, m_dim) * h / 1000.0
    wr.draw_rect(
        (r_wall - 2.0).to_float(),
        (y1 - gap / 2.0).to_float(),
        (r_wall + 3.0).to_float(),
        (y1 + gap / 2.0).to_float(),
    )

    t_wall = lookup2(rc, top, x1, y1, gap, m_dim - 1.0, m_dim) * h / 1000.0
    wr.draw_rect(
        (x1 - gap / 2.0).to_float(),
        (t_wall - 2.0).to_float(),
        (x1 + gap / 2.0).to_float(),
        (t_wall + 3.0).to_float(),
    )

    b_wall = lookup2(rc, bottom, x1, y1, gap, m_dim - 1.0, m_dim) * h / 1000.0
    wr.draw_rect(
        (x1 - gap / 2.0).to_float(),
        (b_wall - 2.0).to_float(),
        (x1 + gap / 2.0).to_float(),
        (b_wall + 3.0).to_float(),
    )

    rc.painter.set_color(0x4F3D4572).commit()
    wr.draw_round_rect(
        l_wall.to_float(), t_wall.to_float(),
        r_wall.to_float(), b_wall.to_float(),
        500.0, 500.0,
    )


# ============================================================================
# maze() — Port of DemoParticles.kt maze()
# ============================================================================

def demo_maze():
    """Maze with particle bouncing off walls using accelerometer."""
    rc = RemoteComposeWriter(500, 500, "sd", api_level=6, profiles=0)
    time_id = rc.create_text_from_float(
        Rc.Time.ANIMATION_TIME, 3, 1, Rc.TextFromFloat.PAD_PRE_ZERO)

    ctx = RcContext.__new__(RcContext)
    ctx._writer = rc
    ctx._cached_time_string = -1

    def content():
        rc.start_column(
            RecordingModifier().fill_max_width().fill_max_height(), 1, 1)

        rc.start_text_component(
            RecordingModifier().fill_max_width().height(122.0).background(0xFF444444),
            time_id,
            0xFFFFFF00,  # Yellow
            100.0,
            0,
            1.0,
            None,
            3,
            0,
            1,
        )
        rc.end_text_component()

        rc.start_canvas(RecordingModifier().fill_max_size())

        rc.rc_paint.set_color(0xFF000000).set_alpha(1.0).commit()

        w = ctx.ComponentWidth()
        h = ctx.ComponentWidth()  # NOTE: Kotlin uses ComponentWidth for h too
        rc.add_conditional_operations(Rc.Condition.GT, w.to_float(), 10.0)
        m_dim = 10

        rc.draw_round_rect(0.0, 0.0, w.to_float(), h.to_float(), 10.0, 10.0)

        r = random.Random()
        maze = gen_maze(m_dim, m_dim, r.randint(-2**31, 2**31 - 1))
        maze_path = gen_path(maze, 10, 10)
        maze_walls = gen_walls(maze, 10, 10)

        gap = w / float(m_dim)
        y1 = ((ctx.ContinuousSec() / 13.0).sin() * 0.5 + 0.5) * h
        x1 = ((ctx.ContinuousSec() / 7.0).sin() * 0.5 + 0.5) * w

        # Roaming ball
        rc.rc_paint.set_color(0x881C4606).commit()
        rc.draw_circle(x1.to_float(), y1.to_float(), (gap / 5.0).to_float())

        left_arr = rc.add_float_array(maze_walls[0])
        right_arr = rc.add_float_array(maze_walls[1])
        top_arr = rc.add_float_array(maze_walls[2])
        bottom_arr = rc.add_float_array(maze_walls[3])
        walls = [left_arr, right_arr, top_arr, bottom_arr]

        rc.rc_paint.set_color(0xFF09A804).commit()
        draw_related_walls(ctx, walls, x1, y1, gap, m_dim, w, h)
        gap.to_float()  # Force flush (matches Kotlin)

        rc.rc_paint.set_color(0xFF866767).set_stroke_width(10.0).set_style(
            STYLE_STROKE).commit()
        path_id = rc.add_path_data(maze_path)

        rc.save()
        rc.scale((w / 1000.0).to_float(), (h / 1000.0).to_float())
        rc.draw_path(path_id)
        rc.restore()

        cx = w / 2.0
        cy = h / 2.0

        # Accelerometer-driven particle
        ax = ctx.rf(Rc.Sensor.ACCELERATION_X) * -1.0
        ay = ctx.rf(Rc.Sensor.ACCELERATION_Y) * 1.0
        p_count = 1

        rc.rc_paint.set_color(0xFF002AFF).set_alpha(1.0).set_style(
            STYLE_FILL).set_shader(0).commit()

        event = ctx.ContinuousSec().to_float()

        rc.impulse(20000.0, event)

        variables = [0.0] * 6
        ps = rc.create_particles(
            variables,
            [
                [0.0],                               # wx
                [0.0],                               # wy
                _to_array(0.0 * (ctx.rand() - 0.5)),  # dx
                _to_array(0.0 * (ctx.rand() - 0.5)),  # dy
                _to_array(cx * (ctx.rand() - 0.5) / 2.0),  # px
                _to_array(cy * (ctx.rand() - 0.5) / 2.0),  # py
            ],
            p_count,
        )
        wx = RFloat(rc, variables[0])
        wy = RFloat(rc, variables[1])
        dx = RFloat(rc, variables[2])
        dy = RFloat(rc, variables[3])
        px = RFloat(rc, variables[4])
        py = RFloat(rc, variables[5])

        dt = ctx.deltaTime() * 33.0

        rc.impulse_process()

        rc.particles_loop(
            ps,
            None,  # no restart
            [
                _to_array(h_wall_repel(ctx, walls, px, py, gap, m_dim, w, h)),
                _to_array(v_wall_repel(ctx, walls, px, py, gap, m_dim, w, h)),
                _to_array(dx + (ax - dx * 0.2 + wx) * dt),
                _to_array(dy + (ay - dy * 0.2 - wy) * dt),
                _to_array(rf_clamp(40.0, w - 40.0, px + dx * dt / 2.0)),
                _to_array(rf_clamp(40.0, h - 40.0, py + dy * dt / 2.0)),
            ],
            lambda: _maze_draw_particle(rc, px, py),
        )

        rc.impulse_end()
        rc.impulse_end()

        rc.end_conditional_operations()
        rc.end_canvas()
        rc.end_column()

    rc.root(content)
    return rc


def _maze_draw_particle(rc, px, py):
    """Draw a single particle in the maze demo."""
    rc.rc_paint.set_color(0x99B4BBDE).commit()
    rc.draw_circle(px.to_float(), py.to_float(), 16.0)


# ============================================================================
# psMaze2() — Core function for pmaze1 and pmaze2
# ============================================================================

def ps_maze2(p_count=120, draw_walls=False, haptics=False, maze_dim=6,
             random_maze=True, time_scale=3.0, gravity=30.0,
             friction=0.02, elastic=0.6, brownian=3.0):
    """Particle maze simulation with bounce physics.

    Matches Kotlin psMaze2() from DemoParticles.kt.
    """
    rc = RemoteComposeWriter(
        500, 500, "sd", api_level=7,
        profiles=PROFILE_ANDROIDX | PROFILE_EXPERIMENTAL)
    time_id = rc.create_text_from_float(
        Rc.Time.ANIMATION_TIME, 3, 1, Rc.TextFromFloat.PAD_PRE_ZERO)

    ctx = RcContext.__new__(RcContext)
    ctx._writer = rc
    ctx._cached_time_string = -1

    def content():
        rc.start_column(
            RecordingModifier().fill_max_width().fill_max_height(), 1, 1)

        rc.start_canvas(RecordingModifier().fill_max_size())

        rc.rc_paint.set_color(0xFF000000).set_alpha(1.0).commit()

        w = ctx.ComponentWidth()
        h = ctx.ComponentHeight() - 4.0
        rc.add_conditional_operations(Rc.Condition.GT, w.to_float(), 10.0)
        dim = maze_dim
        dim1 = dim - 1.0

        rc.draw_round_rect(0.0, 0.0, w.to_float(), h.to_float(), 10.0, 10.0)

        r = random.Random() if random_maze else random.Random(4567)
        maze = gen_maze(dim, dim, r.randint(-2**31, 2**31 - 1))
        maze_path = gen_path(maze, dim, dim)
        maze_walls = gen_walls(maze, dim, dim)

        gap = w / float(dim)

        rc.rc_paint.set_color(0x881C4606).commit()
        left_arr = rc.add_float_array(maze_walls[0])
        right_arr = rc.add_float_array(maze_walls[1])
        top_arr = rc.add_float_array(maze_walls[2])
        bottom_arr = rc.add_float_array(maze_walls[3])
        walls = [left_arr, right_arr, top_arr, bottom_arr]

        gap.to_float()  # Force flush

        rc.rc_paint.set_color(0x8B1A50B0).set_stroke_width(10.0).set_style(
            STYLE_STROKE).commit()
        path_id = rc.add_path_data(maze_path)

        rc.save()
        rc.scale((w / 1000.0).to_float(), (h / 1000.0).to_float())
        rc.draw_path(path_id)
        rc.restore()

        rc.rc_paint.set_color(0xFFA13636).set_stroke_width(5.0).set_style(
            STYLE_STROKE).commit()

        ball_rad = 16.0
        ax = ctx.rf(Rc.Sensor.ACCELERATION_X) * -gravity
        ay = ctx.rf(Rc.Sensor.ACCELERATION_Y) * gravity

        rc.rc_paint.set_color(0xFF002AFF).set_alpha(1.0).set_style(
            STYLE_FILL).set_shader(0).commit()

        event = ctx.ContinuousSec().to_float()

        rc.impulse(20000.0, event)

        variables = [0.0] * 5
        ps = rc.create_particles(
            variables,
            [
                _to_array(ctx.rand() * 120.0 - 5.0),    # dx
                _to_array(ctx.rand() * 120.0 - 5.0),    # dy
                _to_array(w * ctx.rand()),                # px (x)
                [50.0],                                    # py (y)
                _to_array(ctx.index() / float(p_count)),  # hue
            ],
            p_count,
        )
        dx = RFloat(rc, variables[0])
        dy = RFloat(rc, variables[1])
        px = RFloat(rc, variables[2])
        py = RFloat(rc, variables[3])
        hue = RFloat(rc, variables[4])

        dt = ctx.deltaTime() * time_scale

        rc.impulse_process()

        # Particle comparisons for wall bouncing
        rc.rc_paint.set_color(0xFD01EF06).commit()
        min_val = -1.0
        max_val = -1.0

        # ===== below (top wall collision) =====
        top_wall = lookup2(ctx, walls[2], px, py, gap, dim1, dim) * w / 1000.0
        condition_below = py + ball_rad - top_wall
        then_below_top = lookup2(ctx, walls[2], px, py, gap, dim1, dim) * w / 1000.0
        then_below = [
            _to_array(dx),
            _to_array(dy * -elastic),
            _to_array(px),
            _to_array(then_below_top - ball_rad - 1.0),
            _to_array(hue),
        ]
        rc.particles_comparison(
            ps, 0, min_val, max_val,
            _to_array(condition_below),
            then_below,
            None,
            lambda: rc.draw_circle(px.to_float(), (py + ball_rad).to_float(), 5.0),
        )

        # ===== above (bottom wall collision) =====
        bottom_wall = lookup2(ctx, walls[3], px, py, gap, dim1, dim) * w / 1000.0
        condition_above = bottom_wall + ball_rad - py
        then_above_bottom = lookup2(ctx, walls[3], px, py, gap, dim1, dim) * w / 1000.0
        then_above = [
            _to_array(dx),
            _to_array(dy * -elastic),
            _to_array(px),
            _to_array(then_above_bottom + ball_rad + 1.0),
            _to_array(hue),
        ]

        def _draw_above():
            rc.draw_circle(px.to_float(), (py - ball_rad).to_float(), 5.0)
            if haptics:
                rc.perform_haptic(2)

        rc.particles_comparison(
            ps, 0, min_val, max_val,
            _to_array(condition_above),
            then_above,
            None,
            _draw_above,
        )

        # ===== left wall collision =====
        left_wall = lookup2(ctx, walls[0], px, py, gap, dim1, dim) * w / 1000.0
        condition_left = left_wall + ball_rad - px
        then_left_wall = lookup2(ctx, walls[0], px, py, gap, dim1, dim) * w / 1000.0
        then_left = [
            _to_array(dx * -elastic),
            _to_array(dy),
            _to_array(then_left_wall + ball_rad + 1.0),
            _to_array(py),
            _to_array(hue),
        ]

        def _draw_left():
            rc.draw_circle((px - ball_rad).to_float(), py.to_float(), 5.0)
            if haptics:
                rc.perform_haptic(2)

        rc.particles_comparison(
            ps, 0, min_val, max_val,
            _to_array(condition_left),
            then_left,
            None,
            _draw_left,
        )

        # ===== right wall collision =====
        right_wall = lookup2(ctx, walls[1], px, py, gap, dim1, dim) * w / 1000.0
        condition_right = px + ball_rad - right_wall
        then_right_wall = lookup2(ctx, walls[1], px, py, gap, dim1, dim) * w / 1000.0
        then_right = [
            _to_array(dx * -elastic),
            _to_array(dy),
            _to_array(then_right_wall - ball_rad - 1.0),
            _to_array(py),
            _to_array(hue),
        ]

        def _draw_right():
            rc.draw_circle((px + ball_rad).to_float(), py.to_float(), 5.0)
            if haptics:
                rc.perform_haptic(2)

        rc.particles_comparison(
            ps, 0, min_val, max_val,
            _to_array(condition_right),
            then_right,
            None,
            _draw_right,
        )

        # Main particle loop
        rc.particles_loop(
            ps,
            None,  # no restart
            [
                _to_array(dx + (ax - dx * friction) * dt + (ctx.rand() - 0.5) * brownian),
                _to_array(dy + (ay - dy * friction) * dt + (ctx.rand() - 0.5) * brownian),
                _to_array(px + dx * dt / 2.0),
                _to_array(py + dy * dt / 2.0),
                _to_array(hue),
            ],
            lambda: _ps_maze2_draw(rc, ctx, px, py, hue, ball_rad,
                                    draw_walls, walls, gap, maze_dim, w, h),
        )

        rc.impulse_end()
        rc.impulse_end()

        rc.end_conditional_operations()
        rc.end_canvas()
        rc.end_column()

    rc.root(content)
    return rc


def _ps_maze2_draw(rc, ctx, px, py, hue, ball_rad, draw_walls_flag,
                    walls, gap, maze_dim, w, h):
    """Draw a single colored particle in psMaze2."""
    col = rc.add_color_expression(244, hue.to_float(), 0.8, 0.9)
    rc.rc_paint.set_color_id(col).commit()
    rc.draw_circle(px.to_float(), py.to_float(), ball_rad)
    if draw_walls_flag:
        draw_related_walls2(ctx, walls, px, py, gap, maze_dim, w, h)


# ============================================================================
# Public demo functions
# ============================================================================

def demo_maze1():
    """Single particle in 20x20 maze. Matches Kotlin pmaze1()."""
    return ps_maze2(p_count=1, draw_walls=False, maze_dim=20)


def demo_maze2():
    """120 particles in 10x10 maze. Matches Kotlin pmaze2()."""
    return ps_maze2(p_count=120, draw_walls=False, maze_dim=10)


# ============================================================================
# Result wrapper
# ============================================================================

class _Result:
    def __init__(self, rc):
        self._rc = rc

    def encode(self):
        return self._rc.encode_to_byte_array()

    def save(self, path):
        with open(path, 'wb') as f:
            f.write(self.encode())


# ============================================================================
class _WriterAdapter:
    """Wrap RemoteComposeWriter to match RcContext interface for run_all.py."""
    def __init__(self, writer):
        self._writer = writer
    def encode(self):
        return self._writer.encode_to_byte_array()
    def save(self, path):
        with open(path, 'wb') as f:
            f.write(self.encode())

def demo_maze_w():
    return _WriterAdapter(demo_maze())

def demo_maze1_w():
    return _WriterAdapter(demo_maze1())

def demo_maze2_w():
    return _WriterAdapter(demo_maze2())


# Main
# ============================================================================

if __name__ == '__main__':
    out_dir = os.path.dirname(__file__)

    # maze.rc
    rc = demo_maze()
    data = rc.encode_to_byte_array()
    path = os.path.join(out_dir, 'maze.rc')
    with open(path, 'wb') as f:
        f.write(data)
    print(f"maze.rc: {len(data)} bytes -> {path}")

    # maze1.rc
    rc = demo_maze1()
    data = rc.encode_to_byte_array()
    path = os.path.join(out_dir, 'maze1.rc')
    with open(path, 'wb') as f:
        f.write(data)
    print(f"maze1.rc: {len(data)} bytes -> {path}")

    # maze2.rc
    rc = demo_maze2()
    data = rc.encode_to_byte_array()
    path = os.path.join(out_dir, 'maze2.rc')
    with open(path, 'wb') as f:
        f.write(data)
    print(f"maze2.rc: {len(data)} bytes -> {path}")

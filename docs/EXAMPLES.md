# rcreate by Example — patterns for writing `.rc` files

A pattern cookbook for writing Python that generates `.rc` binary documents
using the `rcreate` package. Each pattern is a runnable snippet showing the
right way to do it. Read this *before* trying to write a demo — the patterns
here cover almost every demo in `demos/`.

If you need depth on the binary format, see [ARCHITECTURE.md](ARCHITECTURE.md).

---

## 1. Hello world — the simplest valid `.rc`

```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RcContext, Modifier

PROFILE_ANDROIDX = 0x200

def demo_hello():
    ctx = RcContext(400, 400, "Hello", profiles=PROFILE_ANDROIDX)
    with ctx.root():
        ctx.box_leaf(Modifier().size(200).background(0xFFFF0000))
    return ctx

if __name__ == '__main__':
    ctx = demo_hello()
    ctx.save("hello.rc")
```

That produces a ~140-byte `.rc` with a 200×200 red box. Every demo follows
this skeleton — `RcContext` → `with ctx.root():` → content → `ctx.save()`.

**The five things every demo needs:**
1. `RcContext(width, height, description, profiles=PROFILE_ANDROIDX)` — `profiles=0x200`
   selects the v7+ format used by the modern Android player.
2. `with ctx.root():` — opens the root layout. Required.
3. Some content inside the `with` block.
4. `ctx.save(path)` to write the file.
5. `api_level=7` if you use system variables, themed colors, or expressions
   (omit for static layouts only).

---

## 2. Drawing on a canvas

Drawing operations (circles, lines, paths, text) only work inside a
`ctx.canvas()` block. The canvas itself goes inside a layout container like
`ctx.box()`.

```python
from rcreate import RcContext, Rc
from rcreate.modifiers import RecordingModifier

PROFILE_ANDROIDX = 0x200
STYLE_FILL = Rc.Paint.STYLE_FILL
STYLE_STROKE = Rc.Paint.STYLE_STROKE

def demo_shapes():
    ctx = RcContext(500, 500, "Shapes",
                    api_level=7, profiles=PROFILE_ANDROIDX)
    with ctx.root():
        with ctx.box(RecordingModifier().fill_max_size().background(0xFF101820),
                     Rc.Layout.START, Rc.Layout.START):
            with ctx.canvas(RecordingModifier().fill_max_size()):
                # Each ctx.painter chain ends with .commit()
                ctx.painter.set_color(0xFFE94560).set_style(STYLE_FILL).commit()
                ctx.draw_circle(250.0, 250.0, 80.0)

                ctx.painter.set_color(0xFFFFFFFF) \
                    .set_style(STYLE_STROKE).set_stroke_width(3.0).commit()
                ctx.draw_line(100.0, 100.0, 400.0, 400.0)

                ctx.painter.set_style(STYLE_FILL).commit()
                ctx.draw_rect(50.0, 50.0, 150.0, 100.0)
    return ctx
```

Available draw ops: `draw_circle`, `draw_line`, `draw_rect`, `draw_round_rect`,
`draw_arc`, `draw_oval`, `draw_path`, `draw_text_anchored`, `draw_text_on_path`,
`draw_bitmap`. All take `float` coordinates.

---

## 3. The painter pattern — `.set_X().set_Y().commit()`

Paint state is sticky between draws. You set properties via a chained call
on `ctx.painter` and **must** call `.commit()` to apply them. Forgetting
`.commit()` means subsequent draws use the *previous* paint state.

```python
# Right
ctx.painter.set_color(0xFFFF0000).set_style(STYLE_FILL).commit()
ctx.draw_circle(100.0, 100.0, 50.0)  # red

# Wrong — commit missing
ctx.painter.set_color(0xFFFF0000).set_style(STYLE_FILL)
ctx.draw_circle(100.0, 100.0, 50.0)  # color silently ignored
```

Properties to know:
- `set_color(int)` — 0xAARRGGBB
- `set_color_id(int)` — themed color (see §8)
- `set_style(STYLE_FILL | STYLE_STROKE)`
- `set_stroke_width(float)`
- `set_stroke_cap(CAP_ROUND | CAP_BUTT | CAP_SQUARE)`
- `set_text_size(float)`
- `set_alpha(float)` — 0..1

---

## 4. System variables (time, geometry)

`RcContext` exposes time and geometry as `RFloat` expressions. You build math
expressions with them; the player evaluates each frame.

```python
ctx.ContinuousSec()    # monotonic seconds, smooth animation source
ctx.animationTime()    # animation time (resets per loop)
ctx.deltaTime()        # seconds since last frame
ctx.Hour()             # wall-clock hour (0-23)
ctx.Minutes()          # wall-clock minutes (0-59)
ctx.Seconds()          # wall-clock seconds (0-59)
ctx.DayOfWeek()        # 1-7
ctx.DayOfMonth()       # 1-31
ctx.Month()            # 1-12

ctx.ComponentWidth()   # width of containing component
ctx.ComponentHeight()  # height of containing component
ctx.windowWidth()      # window width
ctx.windowHeight()     # window height
```

Use `ContinuousSec()` for continuous animation, `Hour/Minutes/Seconds` for
clocks, `Component*` for layout-relative geometry.

---

## 5. RFloat — building math expressions

`RFloat` represents a math expression evaluated at render time. You build
expressions with operators and free functions. Two forms:

```python
from rcreate.types.rfloat import (
    rf_sin, rf_cos, rf_min, rf_max, rf_pow, rf_sqrt, rf_abs,
    rf_atan2, rf_hypot, rf_lerp, rf_clamp, rf_if_else,
    rf_smooth_step, rf_ping_pong, rf_step, rf_random,
)

t = ctx.ContinuousSec()

# Operators (work like Python floats)
phase = t * 6.28          # multiply
y = (t + 1.0) / 2.0       # add and divide
inv = -t                  # negate
mod = t % 1.0             # modulo

# Free functions for everything else
s = rf_sin(t)             # NOT t.sin() in expressions — use rf_sin
c = rf_cos(t * 2.0)
m = rf_min(t, 5.0)        # min/max take 2 args
clamped = rf_clamp(0.0, 1.0, t)  # (min, max, value)
```

**Sharp edge — operators vs free functions:**
- *Operators* (`+`, `-`, `*`, `/`) on a flushed RFloat use a compact NaN
  reference. Cheap.
- *Free functions* (`rf_sin`, `rf_min`, etc.) inline the full expression
  array even for flushed RFloats. Slightly less efficient but always correct.

Most demos don't notice this; just use the right form for what you need.

### Passing an RFloat to a draw operation

Draw ops want a `float`. Convert with `.to_float()`:

```python
bob_x = 250.0 + 200.0 * rf_sin(t)         # RFloat
ctx.draw_circle(bob_x.to_float(), 250.0, 20.0)  # .to_float() turns it
                                                # into the NaN ref the
                                                # writer expects
```

If you forget `.to_float()`, the writer will reject the RFloat as not a
number. Always `.to_float()` at the call site.

### Flushing

`.flush()` materializes an expression into a single ID. Use it when you'll
reference the same value many times:

```python
cx = (ctx.ComponentWidth() / 2.0).flush()
cy = (ctx.ComponentHeight() / 2.0).flush()
# Now cx and cy can be reused without re-emitting the math each time
```

---

## 6. Worked example — pendulum (animated, 432 bytes)

Full source: [`demos/advanced/demo_pendulum.py`](../demos/advanced/demo_pendulum.py).

```python
import math
from rcreate import RcContext, Rc
from rcreate.modifiers import RecordingModifier
from rcreate.types.rfloat import rf_sin, rf_cos

PROFILE_ANDROIDX = 0x200
STYLE_FILL = Rc.Paint.STYLE_FILL
STYLE_STROKE = Rc.Paint.STYLE_STROKE
CAP_ROUND = Rc.Paint.CAP_ROUND

def demo_pendulum():
    ctx = RcContext(500, 500, "Pendulum",
                    api_level=7, profiles=PROFILE_ANDROIDX)

    with ctx.root():
        with ctx.box(RecordingModifier().fill_max_size().background(0xFF101820),
                     Rc.Layout.START, Rc.Layout.START):
            with ctx.canvas(RecordingModifier().fill_max_size()):
                pivot_x, pivot_y = 250.0, 80.0
                length, bob_radius = 280.0, 22.0
                period, amplitude_deg = 2.0, 35.0
                two_pi = math.pi * 2.0

                # theta(t) = amplitude * sin(2*pi*t / period)
                t = ctx.ContinuousSec()
                phase = t * (two_pi / period)
                theta_rad = rf_sin(phase) * (amplitude_deg * math.pi / 180.0)

                bob_x = pivot_x + length * rf_sin(theta_rad)
                bob_y = pivot_y + length * rf_cos(theta_rad)

                # String
                ctx.painter.set_color(0xFFE0E0E0).set_style(STYLE_STROKE) \
                    .set_stroke_width(3.0).set_stroke_cap(CAP_ROUND).commit()
                ctx.draw_line(pivot_x, pivot_y,
                              bob_x.to_float(), bob_y.to_float())

                # Pivot
                ctx.painter.set_color(0xFFFFFFFF).set_style(STYLE_FILL).commit()
                ctx.draw_circle(pivot_x, pivot_y, 6.0)

                # Bob
                ctx.painter.set_color(0xFFE94560).commit()
                ctx.draw_circle(bob_x.to_float(), bob_y.to_float(), bob_radius)
    return ctx
```

The key trick: build `bob_x` and `bob_y` as RFloat expressions over `t`. The
player evaluates them every frame, so the bob position updates smoothly
without you writing a frame loop.

---

## 7. Common patterns

### Rotating something around a center

```python
with ctx.saved():
    angle_deg = (ctx.ContinuousSec() * 90.0).to_float()  # 90°/s
    ctx.rotate(angle_deg, cx, cy)
    ctx.draw_line(cx, cy, cx, cy - 200.0)  # rotated line
# After 'with ctx.saved():', the rotation is undone.
```

### Bouncing a value between 0 and 1

```python
from rcreate.types.rfloat import rf_ping_pong
t = ctx.ContinuousSec()
bounce = rf_ping_pong(1.0, t * 0.5)  # 0..1..0..1 over 4 seconds
y = 200.0 + 100.0 * bounce
```

### Periodic 0→1 ramp (sawtooth)

```python
t = ctx.ContinuousSec()
ramp = (t / 2.0) % 1.0   # 0..1 every 2s, jumps back to 0
```

### Polar paths (used by clock faces)

```python
t = ctx.ContinuousSec()
rad = 100.0
# Circle traced parametrically — the player walks 64 sample points
path_id = ctx.add_polar_path_expression(
    ctx.r_fun(lambda x: rad).to_array(),  # constant radius
    0.0, math.pi * 2.0, 64,
    cx.to_float(), cy.to_float(),
    Rc.PathExpression.SPLINE_PATH,
)
ctx.draw_path(path_id)
```

---

## 8. Themed colors (light/dark)

For Android Material colors:

```python
ctx.begin_global()
color_id = ctx.writer.add_themed_color(
    "color.system_accent1_500", 0xFFE94560,   # light theme value
    "color.system_accent1_100", 0xFFFFAABB)   # dark theme value
ctx.end_global()

ctx.painter.set_color_id(color_id).commit()  # not set_color(...)
```

Color IDs and direct ARGB colors can be mixed freely.

---

## 9. Saving and inspecting

```python
ctx.save("demo.rc")             # writes the binary
data = ctx.encode()              # raw bytes if you want to inspect
print(f"{len(data)} bytes")

# Render to PNG with rplayer (single frame at t seconds)
# python -m rplayer demo.rc -t 0.5

# Render an animated sequence
# python -m rplayer demo.rc -d 5 -f 10  (5 seconds at 10 fps)
```

For verifying a generated file parses cleanly:

```python
from rplayer.reader import RcReader
doc = RcReader(open("demo.rc", "rb").read()).parse()
print(f"{doc.width}x{doc.height}, {len(doc.operations)} ops")
```

---

## 10. Pitfalls — what NOT to do

**Forgetting `.commit()` on the painter.**
The chain has no effect until commit. Symptoms: every shape drawn in the
previous color/style.

**Forgetting `.to_float()` on an RFloat passed to a draw op.**
Symptom: `TypeError` or unexpected output. Rule: any RFloat going into
`draw_*` or `rotate`/`translate` needs `.to_float()`.

**Using `RFloat.sin()` instead of `rf_sin(rfloat)` in an expression.**
Member methods (`.sin()`, `.cos()`, `.abs()`) only work for RFloats — and
they have subtle semantic differences from operators (they inline the full
expression). When in doubt, use the free function form (`rf_sin`, `rf_cos`,
`rf_abs`).

**Drawing outside a `ctx.canvas(...)` block.**
Layout containers (`box`, `column`, `row`) accept layout children. Draw ops
need a canvas. Putting `draw_circle` inside a `box` (without a nested
`canvas`) won't render.

**Using `profiles=0` and expecting v7+ features.**
Themed colors, system variables, and many expressions need
`profiles=PROFILE_ANDROIDX` (`0x200`) and `api_level=7`. If your demo
"silently doesn't animate," check those.

**Missing `with` block.**
Every `ctx.root()`, `ctx.box(...)`, `ctx.canvas(...)`, `ctx.column(...)`
returns a context manager. You **must** use `with`. Calling them without
`with` leaves containers unclosed and produces malformed `.rc` files.

**Hard-coding 500x500 then forgetting to set `RcContext` to match.**
The `RcContext(width, height, ...)` numbers and the layout's
`ComponentWidth/Height` must agree, or absolute coordinates will fall
outside the visible region.

---

## 11. When you're stuck

- **Look at an existing demo close to what you want.** `demos/advanced/`
  has 40+ demos covering clocks, gauges, charts, animations, paths, touch
  interactivity. Find one that's close, copy the structure.
- **The clock demos** (`demo_clock.py`, `demo_fancy_clocks.py`) are the most
  thorough examples of expressions, paths, and themed colors.
- **The simplest demos** (`demos/components/demo_box.py`, `demo_column.py`)
  are good for layout patterns.
- **`docs/ARCHITECTURE.md`** explains the binary format if you need to
  understand what's actually being written.
- **`docs/KNOWN_LIMITATIONS.md`** lists features that aren't ported (rare;
  the writer is fully complete).

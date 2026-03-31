# rplayer — Python Player/Renderer for RemoteCompose

**An experimental Python renderer and animated player for `.rc` binary files, using skia-python for Skia-native rendering.**

> **Maturity note:** rplayer is under active development. It correctly renders many demos — clocks, charts, paths, color expressions, animations — but does not yet implement all runtime features. In particular, there is no layout engine (column/row positioning), so demos that rely on layout will render with overlapping content. It is useful for testing, visualization, and demo rendering, but is not yet a complete RemoteCompose player.

---

## What It Is

`rplayer` is a desktop tool that reads RemoteCompose `.rc` binary files and renders them using skia-python. It provides three interfaces:

1. **Desktop viewer** (`viewer`) — GUI app with file browser, animation playback, time scrubber, and frame export. **Recommended for interactive testing.**
2. **Animated CLI player** (`player`) — command-line renderer that evaluates expressions and outputs PNG frame sequences
3. **Static batch renderer** (`render_demo`) — renders a single snapshot per file, no expression evaluation

---

## What Works

- **Float expression evaluation**: RPN stack-based evaluator with 40+ operators (arithmetic, trig, conditionals, array ops, easing curves). Covers the operators used by the demo set; some rarely-used operators may have edge cases.
- **Animation runtime**: Time-stepping, system variables (animation_time, delta_time, continuous_sec, window dimensions), per-frame expression re-evaluation inside loops and conditionals
- **Easing curves**: CubicEasing (6 presets + custom), bounce, elastic, step/spline curves — matching Java's easing pipeline
- **NaN float resolution**: Resolves NaN-encoded variable references through the runtime at render time
- **Frame sequences**: Render at arbitrary time points or at a fixed fps/duration
- **Live preview**: Real-time windowed playback with vsync, keyboard controls (Escape to exit)
- **Skia rendering**: Draw operations (rect, circle, oval, arc, line, sector), paths (static and runtime-constructed), gradients (linear/radial/sweep), transforms, clips, text anchoring, blend modes, paint state, HSV/interpolate/select color expressions

## Known Limitations

- **No layout engine**: Container operations (Box, Row, Column) are parsed for stream sync but no layout algorithm is applied. Demos relying on column/row positioning will render with overlapping content.
- **No bitmap font rendering**: Bitmap data is parsed and stored but bitmap font text runs are not drawn.
- **No touch/sensor input**: Touch coordinates default to 0; sensor data is not connected. Touch-driven demos render in their default state.
- **Integer expressions**: Partially implemented. Float expressions are the primary focus.
- **Some system variables**: Density, some sensor IDs use default values.

---

## Architecture

```
rplayer/
├── __init__.py          # Package exports + lazy imports for player functions
├── __main__.py          # python -m rplayer entry point (shortcut for player)
├── reader.py            # Binary .rc parser → RcDocument (V6 + V7+ headers, ~100+ opcodes)
├── renderer.py          # Skia offscreen renderer with runtime NaN resolution
├── render_demo.py       # Static batch CLI (no expressions)
├── player.py            # Animated player CLI (expressions + time stepping)
├── runtime.py           # Animation state: system vars, expression eval, time management
├── expressions.py       # RPN float expression evaluator (79 operators)
└── easing.py            # Easing curves: cubic, bounce, elastic, step/spline
```

### Data Flow

```
.rc file → reader.py (parse) → RcDocument
                                    ↓
                    runtime.py (create RuntimeState)
                                    ↓
              for each time t: runtime.step_to(t)
                                    ↓
                    renderer.py (render with NaN resolution) → PNG
```

---

## Dependencies

| Package | Required | Purpose |
|---------|----------|---------|
| `skia-python` | Yes | Skia rendering engine (matches Android's Skia backend) |
| `glfw` | No | Live preview window (optional; falls back to frame rendering) |

Python 3.10+ required. No other dependencies.

### Installation

```bash
pip install skia-python

# Optional: for live preview window
pip install glfw
```

---

## Desktop Viewer (Recommended)

The viewer is a GUI application for interactively testing `.rc` files. It wraps the same Skia rendering pipeline used by the CLI tools.

### Launch

```bash
# Open empty (use File > Open)
python -m rplayer.viewer

# Open a specific file
python -m rplayer.viewer demos/output/demo_metal_clock.rc

# Open a folder (browse with Page Up / Page Down)
python -m rplayer.viewer demos/output/
```

### Features

- **File browser**: Open individual files or entire folders of `.rc` demos
- **Animation playback**: Play/Pause, Stop, step forward/backward by frame
- **Time scrubber**: Drag the slider to seek to any point in the animation
- **Folder navigation**: Page Up/Down to cycle through all `.rc` files in a folder
- **Frame export**: Save the current frame as PNG, or export a 3-second sequence
- **Status display**: Shows file name, dimensions, operation count, expression count, and whether the file is STATIC or ANIMATED
- **Reload**: Re-read the current file from disk (Ctrl+R) — useful when editing generators

### Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `Space` | Play / Pause |
| `Right` | Step forward one frame |
| `Left` | Step backward one frame |
| `Home` / `Escape` | Stop and reset to t=0 |
| `Page Down` | Next file in folder |
| `Page Up` | Previous file in folder |
| `Ctrl+O` | Open file |
| `Ctrl+R` | Reload current file |
| `Ctrl+S` | Export current frame |
| `Ctrl+Q` | Quit |

### How It Works

The viewer does not duplicate any rendering logic. It uses the exact same pipeline as the CLI tools:

```
.rc file → reader.py (parse) → RcDocument + RuntimeState
    → runtime.step_to(t) → renderer.render() → skia.Image
    → encodeToData() → PNG bytes → tkinter PhotoImage → display
```

Each frame is rendered offscreen by Skia, encoded to PNG, and displayed in a tkinter canvas. This adds ~5-15ms of overhead per frame compared to raw Skia, but is sufficient for 30fps playback of most demos.

### Limitations

- No GPU acceleration (offscreen CPU rendering)
- Frame rate depends on document complexity (simple demos: 30fps, complex: 10-20fps)
- No touch/mouse interaction forwarded to `.rc` content
- Platform-native tkinter appearance (functional, not polished)

---

## CLI Usage

### Entry Points

There are four ways to run rplayer:

| Command | What it does |
|---------|-------------|
| `python -m rplayer.viewer` | **Desktop GUI viewer (recommended)** |
| `python -m rplayer` | Animated CLI player (shortcut) |
| `python -m rplayer.player` | Animated CLI player (explicit) |
| `python -m rplayer.render_demo` | Static batch renderer (no expressions) |

### Animated Player Commands

```bash
# Render 3 seconds at 30fps (defaults) → rplayer_frames/
python -m rplayer demo.rc

# Render 5 seconds at 10fps
python -m rplayer demo.rc -d 5 -f 10

# Render at specific times only
python -m rplayer demo.rc -t 0 1.5 3.0

# Render at 2x scale to a custom output directory
python -m rplayer demo.rc -s 2.0 -o my_frames/

# Live preview window (requires glfw)
python -m rplayer demo.rc -m live

# Live preview at 2x speed for 10 seconds
python -m rplayer demo.rc -m live --speed 2.0 -d 10
```

**All options:**

| Flag | Default | Description |
|------|---------|-------------|
| `file` | (required) | Path to `.rc` file |
| `-m`, `--mode` | `frames` | `frames` (PNG sequence) or `live` (preview window) |
| `-d`, `--duration` | `3.0` | Animation duration in seconds |
| `-f`, `--fps` | `30.0` | Frames per second |
| `-s`, `--scale` | `1.0` | Render scale factor |
| `-o`, `--output` | `rplayer_frames` | Output directory for PNG frames |
| `--speed` | `1.0` | Playback speed multiplier (live mode) |
| `-t`, `--times` | (none) | Explicit time points to render (overrides -d and -f) |

### Static Batch Renderer

```bash
# Render a single file
python -m rplayer.render_demo demos/output/c_box.rc

# Render multiple files
python -m rplayer.render_demo demos/output/*.rc -o rendered/

# Render at 2x scale
python -m rplayer.render_demo demos/output/c_box.rc -s 2.0
```

The static renderer produces a single snapshot per file with no expression evaluation. NaN-encoded values render as 0.0.

---

## Output

### Frame mode (default)

Output PNGs are saved to the output directory (default `rplayer_frames/`) with names encoding the frame index and time:

```
rplayer_frames/
├── demo_metal_clock_f0000_t0.000s.png
├── demo_metal_clock_f0001_t0.200s.png
├── demo_metal_clock_f0002_t0.400s.png
└── ...
```

Pattern: `{basename}_f{index:04d}_t{time:.3f}s.png`

### Live mode

Opens a window titled `rplayer: {filename}` showing real-time animation. Press Escape or close the window to exit. Prints frame count and average FPS on exit.

If `glfw` is not installed, live mode automatically falls back to frame rendering (at reduced fps/duration).

---

## Testing with Demos

Good test files from `demos/output/`:

```bash
# Static demo (simple shapes, no expressions)
python -m rplayer demos/output/demo_box.rc -t 0

# Text with transforms
python -m rplayer demos/output/demo_text_transform.rc -t 0 0.5 1.0

# Animated clock (time-dependent expressions)
python -m rplayer demos/output/demo_metal_clock.rc -d 1 -f 5

# Compare static vs animated render of same file
python -m rplayer.render_demo demos/output/demo_box.rc -o compare/
python -m rplayer demos/output/demo_box.rc -t 0 -o compare/
```

Reference `.rc` files from Kotlin demos are in:
```
integration-tests/player-view-demos/src/main/res/raw/
```

---

## Programmatic API

```python
from rplayer.player import render_frames, render_time_samples, live_preview, load_rc

# Load and inspect an .rc file
doc, runtime = load_rc('demo.rc')
print(f'{doc.width}x{doc.height}, {len(doc.operations)} ops')

# Render specific time samples
results = render_time_samples('demo.rc', [0, 0.5, 1.0, 2.0])
for t, path in results:
    print(f't={t}s -> {path}')

# Render fps/duration sequence
results = render_frames('demo.rc', fps=10, duration=2.0, output_dir='out/')

# Live preview (if glfw available)
live_preview('demo.rc', duration=5.0, speed=1.5)
```

---

## How It Fits in the Validation Workflow

```
rcreate (Python writer)
    ↓ generates .rc bytes
demos/output/*.rc
    ↓
┌─────────────────────────────────────────────┐
│ Validation                                  │
│                                             │
│ 1. Byte-identical: compare vs Kotlin refs   │
│ 2. rplayer: render to PNG for visual check   │
│ 3. Android emulator: load in RemoteCompose  │
│    Player on device                         │
└─────────────────────────────────────────────┘
```

The animated player adds the ability to validate time-dependent behavior (clocks, gauges, animated transitions) that static rendering cannot verify.

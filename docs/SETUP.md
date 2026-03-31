# rplayer Setup and Test Guide

## Prerequisites

- Python 3.10+ (tested with 3.11.9)
- Windows 10/11

## Create Virtual Environment

```
cd C:\Users\jason\Downloads\RemoteUI-main
python -m venv .venv
```

## Activate the Virtual Environment

**CMD:**
```
.venv\Scripts\activate.bat
```

**PowerShell:**
```
.venv\Scripts\Activate.ps1
```

If PowerShell blocks the script, run this first (one time only):
```
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## Install Dependencies

With the venv activated:

```
pip install skia-python
```

That's the only required dependency. It pulls in `numpy` and `pybind11` automatically.

For optional live preview support:
```
pip install glfw
```

## Verify Installation

```
python -m rplayer --help
```

You should see the help text with options for `-m`, `-d`, `-f`, `-s`, `-o`, `-t`, `--speed`.

## Desktop Viewer (Recommended)

The easiest way to test `.rc` files is the GUI viewer:

```
python -m rplayer.viewer
```

Or open a file directly:
```
python -m rplayer.viewer demos\output\demo_metal_clock.rc
```

Or browse a whole folder:
```
python -m rplayer.viewer demos\output\
```

Use Space to play/pause, arrow keys to step, Page Up/Down to browse files.

No additional dependencies needed — the viewer uses tkinter (included with Python).

## CLI Test Commands

All commands assume the venv is activated and you're in `C:\Users\jason\Downloads\RemoteUI-main`.

### Single frame at t=0

```
python -m rplayer demos\output\demo_box.rc -t 0
```

Output: `rplayer_frames\demo_box_f0000_t0.000s.png`

### Multiple time samples

```
python -m rplayer demos\output\demo_text_transform.rc -t 0 0.5 1.0
```

Output: 3 PNGs in `rplayer_frames\`

### Animated sequence (1 second at 5 fps)

```
python -m rplayer demos\output\demo_metal_clock.rc -d 1 -f 5
```

Output: 6 PNGs in `rplayer_frames\`

### Custom output directory

```
python -m rplayer demos\output\demo_box.rc -t 0 -o my_frames
```

Output: `my_frames\demo_box_f0000_t0.000s.png`

### Live preview (requires glfw)

```
python -m rplayer demos\output\demo_metal_clock.rc -m live -d 5
```

Opens a window. Press Escape or close it to exit. If glfw is not installed, it falls back to rendering frames.

### Static renderer (no expression evaluation)

```
python -m rplayer.render_demo demos\output\demo_box.rc
```

Output: `rplayer_frames\demo_box.png` (single snapshot, no time stepping)

## Output

- Default output directory: `rplayer_frames\` (created automatically)
- Frame naming: `{name}_f{index}_t{time}s.png`
- Static renderer naming: `{name}.png`

## What Success Looks Like

- Commands print frame progress: `[1/6] t=0.000s -> filename.png`
- PNGs appear in the output directory
- Opening a PNG shows rendered shapes, text, or clock faces
- For animated demos (clocks), frames at different times should show different hand positions

## Dependencies Summary

| Package | Required | Purpose |
|---------|----------|---------|
| skia-python | Yes | Skia rendering (matches Android) |
| glfw | No | Live preview window only |
| numpy | Yes (auto) | Pulled in by skia-python |
| pybind11 | Yes (auto) | Pulled in by skia-python |

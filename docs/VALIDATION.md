# Validation Workflow

## Overview

The Python RemoteCompose generator is validated at three levels:
1. **Unit tests** — individual encoding correctness
2. **Byte-identical matching** — against Java/Kotlin reference `.rc` files
3. **Android end-to-end** — visual rendering in the RemoteCompose player

## 1. Unit Tests (`tests/verify_encoding.py`)

79 tests verify low-level encoding: wire buffer operations, NaN encoding,
opcode serialization, modifier encoding, paint state, header format, etc.

Run: `python -m pytest tests/verify_encoding.py -v`

## 2. Demo Generation (`demos/run_all.py`)

Generates all demos and reports pass/fail. Currently 219 demos across:
- `demos/components/` — 47 component demos + 9 CORE_TEXT variants
- `demos/advanced/` — 20+ advanced demos (clocks, graphs, touch, animation)
- `demos/validation/` — 6 stress-test demos (no Java reference; Python-only)

Run: `python demos/run_all.py`

All demos write to `demos/output/`. Each demo function returns an `RcContext`
or `RemoteComposeWriter` and the runner calls `encode()` + `save()`.

## 3. Reference Matching (`demos/check_references.py`)

Compares generated `.rc` files byte-for-byte against Kotlin reference files in
`integration-tests/player-view-demos/src/main/res/raw/`.

### Current Status: 145/171 matches

| Category | Count | Notes |
|----------|-------|-------|
| Byte-identical | 145 | Exact match (68 same-name + 77 cross-name) |
| Bitmap-dependent | 8 | Need Android Bitmap API (texture, wake, etc.) |
| Context API only | ~12 | Kotlin DSL layout wrapping, no matching source |
| Path from text | 3 | Need `buildPathFromText` (font rasterization) |
| Known diffs | 4 | Explained: denormalized zero (2), stale ref (1), different source (1) |

### Name Mapping

Some demos map to differently-named references:
- `demo_modifier_width_in` → `cm_odifier_width_in` (typo in reference)
- `demo_modifier_z_index` → `c_modifier_zindex`
- Many `demo_X` → `X` (prefix stripped)

The check script handles this via explicit name maps and fuzzy matching.

## 4. Android End-to-End Testing

### Setup

Android viewer app: `C:\Users\jason\AndroidStudioProjects\MyFirstAppRC`
- Uses `RemoteComposePlayer.setDocument(bytes)` to render
- Auto-discovers `.rc` files from `res/raw/` via `R.raw` reflection

### Adding Test Files

1. Copy `.rc` files to `app/src/main/res/raw/`
2. Build: `cd MyFirstAppRC && ./gradlew :app:assembleDebug`
3. Install: `adb install -r app/build/outputs/apk/debug/app-debug.apk`
4. Launch app, search for demo name, verify rendering

### Validation Demo Results (2026-03-21)

All 6 validation demos verified rendering correctly:

| Demo | Exercises | Result |
|------|-----------|--------|
| `val_animation_stress` | Orbiting circles, pulsing ring, rotating text, sine bars | PASS |
| `val_edge_cases` | Thin strokes, deep nesting, 100 circles, 100-point path | PASS |
| `val_expressions_lookups` | Time display, day lookup, animated bars, conditionals | PASS |
| `val_layout_text_styling` | Nested layout, text styles, canvas drawing | PASS |
| `val_paths_transforms` | Star/heart paths, transforms, Lissajous curve | PASS |
| `val_touch_interactive` | Touch-driven circle, crosshairs, coordinate text | PASS |

## 5. Python Player Verification (`verify_player.py`)

The Python rplayer renders all 223 `.rc` demos and classifies output quality.

### Running

```
source .venv/Scripts/activate   # or .venv\Scripts\activate.bat on CMD
python verify_player.py
```

Output:
- Frames: `verify_output/python/` (PNGs at t=0, t=0.5, t=1.0)
- Reports: `verify_output/report.txt`, `verify_output/report.json`

### Current Status: 147/222 visually OK (66%)

| Classification | Count | Description |
|----------------|-------|-------------|
| OK | 147 | Non-blank, animated demos show frame differences |
| BLANK | 14 | >99% white pixels |
| ANIM_FROZEN | 61 | Non-blank but identical across time samples |
| PARSE_ERROR | 1 | `demo_digital_clock` (writer bug in rcreate) |

### BLANK Demos — Root Causes (14)

| Demos | Count | Root Cause |
|-------|-------|------------|
| wrap_content_* | 6 | Requires layout engine (wrap_content sizing) |
| c_text, demo_text | 2 | Text renders but occupies <1% area (no column layout) |
| background_id | 2 | References Android theme color IDs (unavailable) |
| dynamic_border | 2 | Border width from expression not applied |
| path_demo_path_tween_demo | 1 | path_tween operation not implemented |
| shader_calendar | 1 | DATA_SHADER corrupts document dimensions |

### ANIM_FROZEN Demos — Classification (61)

| Category | Count | Demos (examples) | Expected? |
|----------|-------|-------------------|-----------|
| Touch-only | 8 | demo_touch1/2, touch1/2, touch_wrap, val_touch_interactive, demo_touch_slider, demo_flick_flick_test | Yes — needs touch input |
| Sensor-only | 5 | sensor_demo_acc/compass/gyro/light/mag | Yes — needs sensor data |
| Stop animations | 7 | stop_absolute_pos, stop_ends, stop_gently, stop_instantly, stop_notches_* | Yes — touch/gesture driven |
| Dimension-reactive | ~10 | activity_rings, battery_radial_gauge, step_progress_arc, sleep_quality_rings, pie_chart, maze1/2 | Yes — only change on resize |
| Layout-dependent | ~8 | c_modifier_visibility, c_state_layout, demo_color_expression, attribute_string, anchored_text | Yes — needs layout engine |
| Needs matrix ops | ~4 | cube3d, demo_path_expression_path_test1/2/3 | No — matrix_expression not implemented |
| Needs function_call | ~4 | demo_global, demo_use_of_global, flow_control_checks1/2 | No — function_define/call not implemented |
| Other | ~15 | digital_clock1, player_info, plot2, moon_phase_dial, etc. | Mixed |

### Bugs Fixed During Verification (Session 5)

1. **Parser bugs (6)**: MODIFIER_COLLAPSIBLE_PRIORITY, DYNAMIC_FLOAT_LIST, TEXT_LOOKUP, TEXT_LOOKUP_INT, ATTRIBUTE_COLOR, PARTICLE_COMPARE — reduced parse errors 14→1
2. **Path NaN encoding**: Path commands (MOVE=10, LINE=11, etc.) stored as NaN-encoded floats — _build_path now decodes them
3. **float_list key mismatch**: Reader stores `items`, runtime read `data` — fixed with fallback
4. **color_constant + color_expression**: Implemented color constant storage, SELECT mode (3), HSV mode (4)
5. **Gradient color ID resolution**: Gradients with `id_mask` now resolve color IDs through _colors dict
6. **Conditional/loop execution**: Complete rewrite of execute() with proper block nesting
7. **Text operations**: text_merge, text_transform, text_lookup, text_measure, text_length
8. **mod_background color_id**: Dynamic background colors from expressions
9. **paint color_id**: Dynamic paint colors from color expressions

### Progress Over Debugging Iterations

| Metric | Initial | Final | Delta |
|--------|---------|-------|-------|
| Parse errors | 14 | 1 | -13 |
| Visually OK | 117 | 147 | +30 |
| BLANK | 18 | 14 | -4 |
| ANIM_FROZEN | 74 | 61 | -13 |

## 6. Regression Prevention

Before making changes:
1. Run `python demos/run_all.py` — all 219 demos must pass
2. Run `python -m pytest tests/verify_encoding.py` — all 79 tests must pass
3. Run `python demos/check_references.py` — match count must not decrease

After making changes, repeat all three checks.

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

## 5. Regression Prevention

Before making changes:
1. Run `python demos/run_all.py` — all 219 demos must pass
2. Run `python -m pytest tests/verify_encoding.py` — all 79 tests must pass
3. Run `python demos/check_references.py` — match count must not decrease

After making changes, repeat all three checks.

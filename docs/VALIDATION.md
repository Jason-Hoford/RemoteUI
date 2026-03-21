# Validation Workflow

## Overview

The Python RemoteCompose generator is validated at three levels:
1. **Unit tests** — individual encoding correctness
2. **Byte-identical matching** — against Java/Kotlin reference `.rc` files
3. **Android end-to-end** — visual rendering in the RemoteCompose player

## 1. Unit Tests (`demos/verify_encoding.py`)

79 tests verify low-level encoding: wire buffer operations, NaN encoding,
opcode serialization, modifier encoding, paint state, header format, etc.

Run:

```bash
python demos/verify_encoding.py
```

## 2. Demo Generation (`demos/run_all.py`)

Generates all demos and reports pass/fail. Currently 219 demos across:
- `demos/components/` — 47 component demos + 9 CORE_TEXT variants
- `demos/advanced/` — 57 advanced demos (clocks, graphs, touch, animation, paths, sensors)
- `demos/validation/` — 6 stress-test demos (no Java reference; Python-only)

Run:

```bash
python demos/run_all.py
```

All demos write to `demos/output/`. Each demo function returns an `RcContext`
or `RemoteComposeWriter` and the runner calls `encode()` + `save()`.

## 3. Reference Matching

Generated `.rc` files can be compared byte-for-byte against Kotlin reference
files. Place reference `.rc` files in `demos/reference_rc/` and compare them
against the generated output in `demos/output/` using standard tools
(e.g., `diff`, `cmp`, or a custom comparison script).

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

## 4. Android End-to-End Testing

### Setup

Any Android app that uses `RemoteComposePlayer` can render generated `.rc`
files. The workflow:

1. Copy `.rc` files to the Android app's `res/raw/` directory
2. Build and install the app
3. Load the `.rc` file bytes and pass to `RemoteComposePlayer.setDocument(bytes)`
4. Visually confirm rendering matches expectations

### Validation Demo Results

All 6 validation demos verified rendering correctly on an Android emulator:

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
2. Run `python demos/verify_encoding.py` — all 79 tests must pass
3. If reference `.rc` files are available, verify match count does not decrease

After making changes, repeat all checks.

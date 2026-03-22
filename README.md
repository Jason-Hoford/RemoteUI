# RemoteUI

**A Python generator for RemoteCompose binary documents, ported from the Java/Kotlin creation stack.**

RemoteUI lets you programmatically create `.rc` binary files — the serialization format used by Android's [Remote Compose](https://android.googlesource.com/platform/frameworks/support/+/refs/heads/main/compose/remote/) project — using pure Python with no external dependencies. The generated documents are byte-for-byte identical to the output of the original Java/Kotlin creation library and can be rendered by any compliant RemoteCompose player, including the official Android `RemoteComposePlayer`.

---

## Why This Exists

The upstream RemoteCompose creation library is written in Java/Kotlin and tightly coupled to JVM tooling and Android build infrastructure. This project provides a standalone Python port of the **creation side** of that stack, enabling:

- **Server-side `.rc` generation** without JVM dependencies
- **Cross-platform tooling** — generate documents from CI pipelines, Python services, or scripts
- **Rapid prototyping** — build and iterate on RemoteCompose UIs from Python
- **Validation and testing** — compare Python output byte-for-byte against Kotlin reference files

The Python port targets the portable generator surface (the public API of `RemoteComposeWriter` and `RemoteComposeContext`). It does not include the Android rendering runtime — that remains on the Java/Kotlin side.

---

## Current Status

The generator is **strongly validated** and the portable Java public API surface is **fully ported**.

| Metric | Result |
|--------|--------|
| Demo generation | **219 / 219** pass |
| Encoding unit tests | **79 / 79** pass |
| Byte-identical reference matches | **145 / 171** (85%) |
| Android rendering verification | **11 demos** visually confirmed |
| External dependencies | **None** (Python 3.10+ stdlib only) |

The 26 non-matching references are fully accounted for: 8 use Android app resource bitmaps not available as standalone files, 3 require font rasterization (`buildPathFromText`), ~12 lack matching upstream source, and the remaining few have explained differences (denormalized float zeros, stale references, RNG divergence). See [Known Limitations](docs/KNOWN_LIMITATIONS.md) for the complete breakdown.

---

## Feature Overview

### Generator (`rcreate/`)

The `rcreate` package provides two levels of API:

- **`RemoteComposeWriter`** — Low-level writer matching Java's `RemoteComposeWriter.java`. ~190 methods covering layout components, draw operations, expressions, text, paths, paint, modifiers, animations, touch, sensors, theming, and actions.
- **`RcContext`** — High-level Pythonic DSL with context managers (`root()`, `box()`, `column()`, `canvas()`, etc.) matching Kotlin's `RemoteComposeContext`. Includes expression builders (`RFloat`, `RInt`) with operator overloading for building animated, data-driven UIs.

Both APIs produce identical binary output. Key capabilities:

- Layout components: Box, Row, Column, Canvas, Flow, FitBox, StateLayout
- Draw operations: rect, circle, oval, arc, line, path, text, bitmap, round rect
- Expressions: float/integer expression trees with 40+ math operations, animation, conditional logic
- Paths: `RemotePath` builder, SVG-style path data, parametric path expressions, path tweening
- Paint: stroke/fill styles, gradients (linear, radial, sweep), shaders, color filters, text styling
- Modifiers: background, padding, border, clip, scroll, size, weight, visibility, z-index, touch handlers
- Interactivity: touch expressions, click/touch actions, host actions, impulse, haptic feedback
- Data: named colors, themed colors, string lists, text lookup, text merge, sensors, time expressions

### Demos (`demos/`)

219 demos organized across multiple categories:

| Category | Count | Description |
|----------|-------|-------------|
| `components/` | 47 | Layout components and modifier combinations |
| `advanced/` | 57 | Clocks, graphs, touch, animation, paths, sensors |
| `validation/` | 6 | Stress tests: edge cases, deep nesting, large draw counts |
| Core text variants | 9 | CORE_TEXT (op 239) encoding of component demos |
| Cross-name aliases | Various | Same demo output under different names for reference matching |

Every demo generates a valid `.rc` binary and passes header verification on each run.

### Validation

Three-level validation pipeline:

1. **Unit tests** (`demos/verify_encoding.py`) — 79 tests verifying wire buffer encoding, NaN encoding, opcode serialization, modifier encoding, paint state, and header format
2. **Byte-identical matching** — Generated `.rc` files compared against 171 Kotlin reference files. 145 match exactly; remaining gaps are documented and explained.
3. **Android end-to-end** — Representative demos loaded and rendered in the Android `RemoteComposePlayer` on a real emulator, with visual confirmation of correct layout, drawing, animation, touch, and expression evaluation

### Android Rendering Verification

Python-generated `.rc` files have been loaded into a working Android viewer app and rendered via `RemoteComposePlayer.setDocument(bytes)`. 11 demos have been visually verified on an Android emulator, including 6 purpose-built validation demos that exercise edge cases not covered by the reference-matching pipeline (deep nesting, 100+ draw operations, multi-expression animation, touch interactivity).

---

## Repository Structure

```
RemoteUI/
├── rcreate/                    # Python generator package
│   ├── __init__.py             # Public API exports
│   ├── writer.py               # RemoteComposeWriter (~190 methods)
│   ├── context.py              # RcContext DSL with context managers
│   ├── remote_UI_buffer.py     # ~70 opcode serialization methods
│   ├── remote_UI_state.py      # ID allocation and data caching
│   ├── wire_buffer.py          # Big-endian binary read/write
│   ├── rc.py                   # Constants (Layout, Paint, Time, Touch, etc.)
│   ├── rc_paint.py             # Paint state tracking and delta encoding
│   ├── paint_bundle.py         # Paint property bundle for modifiers
│   ├── remote_path.py          # RemotePath builder (move, line, cubic, close)
│   ├── shader.py               # Shader support (linear, radial, sweep gradients)
│   ├── xy_graph.py             # XY graph helper
│   ├── operations.py           # Opcode constant definitions
│   ├── types/                  # Expression types
│   │   ├── nan_utils.py        #   NaN encoding/decoding for variable IDs
│   │   ├── rfloat.py           #   RFloat expression builder (40+ operations)
│   │   ├── rint.py             #   RInt integer expression builder
│   │   └── rmatrix.py          #   Matrix expression support
│   ├── modifiers/              # Modifier system
│   │   ├── recording_modifier.py  # RecordingModifier with fluent API
│   │   ├── shapes.py           #   Clip shapes (rect, rounded rect, circle)
│   │   └── elements.py         #   Modifier element types
│   ├── actions/                # Action types for interactivity
│   │   ├── action.py           #   Base action
│   │   ├── host_action.py      #   Host-side action callback
│   │   └── value_*_change.py   #   Value change actions (float, int, string, expr)
│   └── platform/               # Platform abstraction (path parsing, etc.)
├── demos/                      # Demo scripts and validation
│   ├── run_all.py              # Generate all 219 demos with header verification
│   ├── verify_encoding.py      # 79 encoding unit tests
│   ├── components/             # Component demos (box, row, column, text, modifiers)
│   ├── advanced/               # Advanced demos (clocks, graphs, touch, animation)
│   ├── validation/             # Stress-test demos (Python-only, no Java reference)
│   ├── output/                 # Generated .rc files (git-ignored)
│   └── reference_rc/           # Place Kotlin reference .rc files here for comparison
├── docs/                       # Project documentation
│   ├── ARCHITECTURE.md         # Layer stack, module descriptions, binary format
│   ├── VALIDATION.md           # Validation workflow and results
│   └── KNOWN_LIMITATIONS.md    # Unported APIs, non-matching references, platform diffs
└── LICENSE                     # Apache 2.0
```

---

## Getting Started

### Prerequisites

- **Python 3.10+** (tested with 3.11; no external packages required)

### Setup

```bash
git clone https://github.com/Jason-Hoford/RemoteUI.git
cd RemoteUI
```

No installation step is needed. The `rcreate` package is used directly from the repository root.

### Quick Test

```bash
# Generate all 219 demos and verify headers
python demos/run_all.py

# Run 79 encoding unit tests
python demos/verify_encoding.py
```

Both commands should report zero failures.

---

## Usage

### Generating a Document

```python
from rcreate import RcContext, Rc
from rcreate.modifiers import RecordingModifier

ctx = RcContext(400, 400, "Hello World", api_level=7, profiles=0x200)

with ctx.root():
    with ctx.column(RecordingModifier().fill_max_size().background(0xFF1A1A2E)):
        with ctx.box(RecordingModifier().fill_max_width().height(80.0)
                     .background(0xFF2244AA),
                     Rc.Layout.CENTER, Rc.Layout.CENTER):
            ctx.text("Hello", font_size=32.0, color=0xFFFFFFFF)

        with ctx.box(RecordingModifier().fill_max_size(),
                     Rc.Layout.START, Rc.Layout.START):
            with ctx.canvas(RecordingModifier().fill_max_size()):
                ctx.painter.set_color(0xFFFF6633).commit()
                ctx.draw_circle(200.0, 200.0, 50.0)

# Save the binary document
ctx.save("hello.rc")
```

### Using the Low-Level Writer

```python
from rcreate import RemoteComposeWriter, Rc, RecordingModifier

w = RemoteComposeWriter(400, 300, "Low-Level Demo", api_level=7, profiles=0x200)

def build():
    mod = RecordingModifier()
    w.start_box(mod, Rc.Layout.START, Rc.Layout.TOP)
    w.start_canvas(mod)
    w.rc_paint.set_color(0xFFFF0000).set_style(Rc.Paint.STYLE_FILL).commit()
    w.draw_circle(200.0, 150.0, 40.0)
    w.end_canvas()
    w.end_box()

w.root(build)

with open("low_level.rc", "wb") as f:
    f.write(w.encode_to_byte_array())
```

---

## Running Demos

```bash
# Generate all demos (output goes to demos/output/)
python demos/run_all.py
```

This generates 219 `.rc` files and verifies each one has a valid header. Output:

```
Running 219 demos...
  [OK] demo_box: 123 bytes -> demos/output/demo_box.rc
  [OK] demo_row: 348 bytes -> demos/output/demo_row.rc
  ...
Results: 219 passed, 0 failed out of 219
```

Individual demos can also be run standalone:

```bash
python demos/components/demo_box.py
python demos/advanced/demo_simple_clock.py
python demos/validation/demo_edge_cases.py
```

---

## Validation

### Encoding Tests

```bash
python demos/verify_encoding.py
```

Runs 79 tests covering wire buffer operations, NaN encoding, opcode correctness, modifier encoding, paint state, and header format. All tests should pass.

### Reference Comparison

Generated `.rc` files can be compared byte-for-byte against Kotlin-generated reference files. The reference `.rc` files are produced by the upstream Kotlin creation library and can be placed in `demos/reference_rc/` for local comparison. When compared against the full set of 171 upstream references, 145 match exactly. The comparison accounts for name mapping (some Python demo names differ from their Kotlin reference names) and cross-name aliases.

The 26 non-matching references fall into documented categories:
- **8** use bitmaps loaded from Android app resources (image data not available as standalone files)
- **3** require `buildPathFromText` (font rasterization)
- **~12** lack matching upstream source code
- **4** have explained byte-level differences (denormalized zeros, stale references)

See [docs/VALIDATION.md](docs/VALIDATION.md) for the full validation workflow.

### Android End-to-End Testing

Python-generated `.rc` files can be loaded into an Android viewer app that uses `RemoteComposePlayer` to render them. The workflow:

1. Copy `.rc` files to the Android app's `res/raw/` directory
2. Build and install the app
3. Browse or search for the demo by name
4. Visually confirm rendering matches expectations

11 demos have been verified this way, including 6 purpose-built validation demos that stress layout nesting, path transforms, touch interactivity, animation timing, expression evaluation, and edge cases (thin strokes, 100+ circles, deep save/restore nesting).

---

## Known Limitations

**Bitmap support:**
Bitmap data support is fully implemented — the wire protocol stores PNG bytes, not Android `Bitmap` objects. Use `add_bitmap_png()`, `add_bitmap_from_png()`, `add_bitmap_from_file()`, or `add_bitmap_data()` to add images. The Java convenience methods `addBitmap(Object)` / `addNamedBitmap(name, Object)` are not ported because they accept Android-specific `Bitmap` objects, but the Python equivalents accept PNG bytes directly. 8 reference demos remain unmatched because their Kotlin source loads bitmaps from Android app resources not available as standalone files.

**Unported platform-specific APIs:**
- `buildPathFromText()` — requires font rasterization (3 reference demos affected)

**Platform differences:**
- Python's `random` module produces different sequences than Java's `java.util.Random` (maze demos generate correct format but different content)
- Python uses 64-bit `float` internally; values are truncated to 32-bit IEEE 754 at serialization (no observed precision issues in practice)

**Not included:**
- Android rendering runtime (stays on Java/Kotlin side)
- Compose-level DSL (`RemoteRow`, `RemoteColumn`) — the Context API covers all creation use cases

See [docs/KNOWN_LIMITATIONS.md](docs/KNOWN_LIMITATIONS.md) for the complete list.

---

## Documentation

| Document | Description |
|----------|-------------|
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Layer stack, module descriptions, binary format, key conventions |
| [docs/VALIDATION.md](docs/VALIDATION.md) | Three-level validation workflow, current results, regression prevention |
| [docs/KNOWN_LIMITATIONS.md](docs/KNOWN_LIMITATIONS.md) | Unported APIs, non-matching references, platform differences |

---

## Future Work

- **Path from text**: Investigate FreeType or similar for `buildPathFromText()` without heavy dependencies
- **Remaining Kotlin references**: Port individual demo scripts for the ~12 references that require matching exact Kotlin DSL calls
- **CI integration**: Automate demo generation and reference comparison in a CI pipeline
- **Documentation**: Expand API reference documentation for `RcContext` and `RemoteComposeWriter`

---

## Developer Notes

**Regression checks before making changes:**

```bash
python demos/run_all.py           # All 219 demos must pass
python demos/verify_encoding.py   # All 79 tests must pass
```

**Key implementation details:**

- All binary encoding is **big-endian**, matching Java's `DataOutputStream`
- Variable IDs are encoded as **NaN-based float sentinels** (details in [Architecture](docs/ARCHITECTURE.md))
- Data IDs increment from 42; component IDs decrement from −1 (matching Java's allocation scheme)
- Container end operations emit `addContainerEnd()` twice per container (matching Java)
- The `header_tag_order` parameter exists to match Java `HashMap` iteration order for byte-identical output

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the full technical reference.

---

## License

Apache 2.0 — see [LICENSE](LICENSE).

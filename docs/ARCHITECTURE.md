# rcreate — Architecture Overview

Python port of the Java/Kotlin RemoteCompose creation library.
Generates `.rc` binary files that are byte-identical to the Java output.

## Layer Stack

```
┌─────────────────────────────────────┐
│  RcContext (context.py)             │  Pythonic DSL with context managers
│  ctx.root(), ctx.box(), ctx.text()  │  Wraps writer with layout nesting
├─────────────────────────────────────┤
│  RemoteComposeWriter (writer.py)    │  High-level API (~190 methods)
│  add_text(), draw_circle(), etc.    │  ID allocation, caching, modifiers
├─────────────────────────────────────┤
│  RemoteComposeBuffer                │  ~70 opcode methods
│  (remote_UI_buffer.py)              │  Serializes typed opcodes to wire
├─────────────────────────────────────┤
│  WireBuffer (wire_buffer.py)        │  Raw binary read/write
│  write_float(), write_int(), etc.   │  Big-endian, IEEE 754
└─────────────────────────────────────┘
```

### RcContext (`context.py`)

Top-level entry point. Provides `@contextmanager` methods (`root()`, `box()`,
`column()`, `row()`, `canvas()`) that emit matching start/end opcodes. Also
exposes expression builders (`ContinuousSec()`, `ComponentWidth()`, etc.) that
return `RFloat` objects for building expression trees.

### RemoteComposeWriter (`writer.py`)

Mirrors Java's `RemoteComposeWriter.java`. Owns a `RemoteUIState` for ID
allocation and a `RemoteComposeBuffer` for serialization. Handles:
- Text caching (`add_text()` deduplicates strings)
- Modifier serialization (walks `RecordingModifier` op lists)
- Paint state management (`RcPaint` / `PaintBundle`)
- Document header (V6 legacy or V7+ tagged format)
- Component ID generation (separate decrementing counter)

### RemoteComposeBuffer (`remote_UI_buffer.py`)

One method per opcode. Each method writes a size-prefixed operation:
1. `start_op(opcode)` — writes opcode byte, reserves 2 bytes for size
2. Writes payload fields via `WireBuffer`
3. `end_op()` — patches the size field

Key opcodes: HEADER(0), DATA_TEXT(2), DATA_FLOAT(3), DATA_FLOAT_ARRAY(7),
LAYOUT_ROOT(200), LAYOUT_BOX(202), LAYOUT_COLUMN(203), LAYOUT_ROW(204),
LAYOUT_CANVAS(205), CONTAINER_END(214), DRAW_CIRCLE(30), DRAW_RECT(28), etc.

### WireBuffer (`wire_buffer.py`)

Lowest layer. A growable `bytearray` with cursor-based read/write.
All multi-byte values are **big-endian** (matching Java's `DataOutputStream`).
Includes `RawFloat` — a float subclass that carries exact 32-bit IEEE 754 bits
for preserving NaN encodings.

## Supporting Modules

### ID Allocation (`remote_UI_state.py`)

Three ID namespaces: general (starts at 42), variable (`0x10002A`), array
(`0x20002A`). Text and data are cached (same content → same ID). Float IDs are
always freshly allocated (matching Java behavior). Component IDs use a separate
decrementing counter in the writer (`_generated_component_id`, starts at −1).

### Expression System (`types/rfloat.py`, `types/rint.py`)

`RFloat` wraps a float expression chain as a list of NaN-encoded operation IDs.
Operator overloads (`+`, `*`, `.sin()`, etc.) append expression ops to the
writer and return new `RFloat` instances. `to_float()` flushes the chain and
returns a single NaN float ID. `RInt` provides integer expressions via
`LONG_OFFSET` marker.

### NaN Encoding (`types/nan_utils.py`)

IDs are encoded as signaling NaN floats: `as_nan(v) = intBitsToFloat(v | 0xFF800000)`.
This is the Java convention (negative NaN with low bits = ID). The quiet bit
is explicitly cleared to produce sNaN values that the runtime interprets as
references rather than literal floats.

### Paint System (`rc_paint.py`, `paint_bundle.py`)

`RcPaint` tracks dirty fields and emits only changed paint properties on
`commit()`. `PaintBundle` is a simpler data-only container for recording paint
state in modifiers.

### Modifiers (`modifiers/recording_modifier.py`)

`RecordingModifier` records a list of `(op_code, args)` tuples via fluent
methods (`.width()`, `.background()`, `.padding()`, etc.). The writer replays
these during layout serialization. Shapes (rect, rounded rect, circle) are
encoded as modifier ops.

### Actions (`actions/`)

Six action types for interactive documents: `ValueFloatChange`,
`ValueIntegerChange`, `ValueStringChange`, `ValueFloatExpressionChange`,
`ValueIntegerExpressionChange`, `HostAction`.

## Binary Format Summary

```
┌──────────────────────────┐
│  Header (version, tags)  │
├──────────────────────────┤
│  Data section            │  TEXT, FLOAT, FLOAT_ARRAY, etc.
│  (text, paths, arrays)   │
├──────────────────────────┤
│  Layout tree             │  ROOT → BOX → COLUMN → ROW → CANVAS
│  (nested components)     │  Each closed by CONTAINER_END
├──────────────────────────┤
│  Draw operations         │  Inside CANVAS: circle, rect, line,
│  (inside canvas)         │  path, text, paint changes
└──────────────────────────┘
```

Each operation is: `[opcode: 1 byte] [size: 2 bytes] [payload: N bytes]`

Size field = payload byte count (excludes opcode + size bytes themselves).

## Key Conventions

- All coordinates are floats (or NaN-encoded expression IDs)
- Colors are 32-bit ARGB integers (0xAARRGGBB)
- Container end ops call `addContainerEnd()` TWICE (matching Java)
- V7+ header encodes `major | MAGIC_NUMBER (0x048C0000)` in first field
- Component IDs decrement from −1 (separate from data IDs which increment from 42)

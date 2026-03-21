"""Verify binary encoding correctness of the Python RC library.

Tests individual operation encoding against known-good byte patterns
derived from the Java implementation.
"""
import sys
import os
import struct
import math

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from rcreate import (RemoteComposeWriter, RemoteComposeBuffer,
                      RecordingModifier, Rc, Ops,
                      as_nan, id_from_nan)
from rcreate.wire_buffer import WireBuffer

PASS = 0
FAIL = 0


def check(name, condition, detail=""):
    global PASS, FAIL
    if condition:
        PASS += 1
    else:
        FAIL += 1
        msg = f"  FAIL: {name}"
        if detail:
            msg += f" — {detail}"
        print(msg)


def test_wire_buffer():
    """Test WireBuffer read/write primitives."""
    buf = WireBuffer(256)

    # Byte
    buf.write_byte(0x42)
    buf.write_byte(0xFF)
    # Short
    buf.write_short(0x1234)
    buf.write_short(-1)
    # Int
    buf.write_int(0x12345678)
    buf.write_int(-1)
    buf.write_int(0xFFFFFFFF)
    # Float
    buf.write_float(3.14)
    buf.write_float(float('nan'))
    # Long
    buf.write_long(0x123456789ABCDEF0)
    # UTF8
    buf.write_utf8("hello")

    # Read back
    data = buf.clone_bytes()
    r = WireBuffer(len(data))
    r._buffer[:len(data)] = data
    r._size = len(data)

    check("byte 0x42", r.read_byte() == 0x42)
    check("byte 0xFF", r.read_byte() == 0xFF)
    check("short 0x1234", r.read_short() == 0x1234)
    check("short -1", r.read_short() == -1)
    check("int 0x12345678", r.read_int() == 0x12345678)
    check("int -1 signed", r.read_int() == -1)
    # 0xFFFFFFFF as unsigned
    v = r.read_unsigned_int()
    check("int 0xFFFFFFFF unsigned", v == 0xFFFFFFFF, f"got {v:#x}")
    f = r.read_float()
    check("float 3.14", abs(f - 3.14) < 0.001, f"got {f}")
    f2 = r.read_float()
    check("float NaN", math.isnan(f2))
    lng = r.read_long()
    check("long", lng == 0x123456789ABCDEF0, f"got {lng:#x}")
    s = r.read_utf8()
    check("utf8", s == "hello", f"got {s!r}")


def test_nan_encoding():
    """Test NaN encoding for IDs."""
    for val in [42, 100, 255, 1000, 65535]:
        nan_f = as_nan(val)
        check(f"as_nan({val}) is NaN", math.isnan(nan_f))
        decoded = id_from_nan(nan_f)
        check(f"id_from_nan round-trip {val}", decoded == val,
              f"got {decoded}")


def test_header_v7():
    """Test V7+ header encoding."""
    buf = RemoteComposeBuffer(api_level=8)
    tags = [5, 6]  # DOC_WIDTH, DOC_HEIGHT
    values = [400, 300]
    buf.add_header(tags, values)

    data = buf._buffer.clone_bytes()
    # opcode 0
    check("header opcode", data[0] == 0)
    # major | magic
    major_magic = struct.unpack_from('>I', data, 1)[0]
    check("header magic", major_magic == (1 | 0x048C0000),
          f"got {major_magic:#010x}")
    # minor = 1
    minor = struct.unpack_from('>I', data, 5)[0]
    check("header minor", minor == 1, f"got {minor}")
    # patch = 0
    patch = struct.unpack_from('>I', data, 9)[0]
    check("header patch", patch == 0)
    # count = 2 (two tags)
    count = struct.unpack_from('>I', data, 13)[0]
    check("header tag count", count == 2, f"got {count}")


def test_modifier_width():
    """Test width modifier wire format."""
    buf = RemoteComposeBuffer()
    buf.add_width_modifier_operation(0, 100.0)  # EXACT=0, value=100

    data = buf._buffer.clone_bytes()
    check("width opcode", data[0] == Ops.MODIFIER_WIDTH)
    dim_type = struct.unpack_from('>i', data, 1)[0]
    check("width type EXACT", dim_type == 0)
    value = struct.unpack_from('>f', data, 5)[0]
    check("width value 100", value == 100.0, f"got {value}")


def test_modifier_padding():
    """Test padding modifier wire format."""
    buf = RemoteComposeBuffer()
    buf.add_modifier_padding(10.0, 20.0, 30.0, 40.0)

    data = buf._buffer.clone_bytes()
    check("padding opcode", data[0] == Ops.MODIFIER_PADDING)
    left = struct.unpack_from('>f', data, 1)[0]
    top = struct.unpack_from('>f', data, 5)[0]
    right = struct.unpack_from('>f', data, 9)[0]
    bottom = struct.unpack_from('>f', data, 13)[0]
    check("padding left", left == 10.0)
    check("padding top", top == 20.0)
    check("padding right", right == 30.0)
    check("padding bottom", bottom == 40.0)


def test_modifier_background():
    """Test background modifier wire format."""
    buf = RemoteComposeBuffer()
    buf.add_modifier_background(1.0, 0.0, 0.0, 1.0, 0)  # red, shape=RECT

    data = buf._buffer.clone_bytes()
    check("bg opcode", data[0] == Ops.MODIFIER_BACKGROUND)
    # flags=0, colorId=0, res1=0, res2=0
    flags = struct.unpack_from('>i', data, 1)[0]
    check("bg flags", flags == 0)
    # r at offset 17
    r = struct.unpack_from('>f', data, 17)[0]
    check("bg red", r == 1.0, f"got {r}")
    g = struct.unpack_from('>f', data, 21)[0]
    check("bg green", g == 0.0)
    # shape at offset 33
    shape = struct.unpack_from('>i', data, 33)[0]
    check("bg shape", shape == 0)


def test_modifier_border():
    """Test border modifier wire format."""
    buf = RemoteComposeBuffer()
    buf.add_modifier_border(2.0, 4.0, 0xFFFF0000, 0)  # red border

    data = buf._buffer.clone_bytes()
    check("border opcode", data[0] == Ops.MODIFIER_BORDER)
    # borderWidth at offset 17
    bw = struct.unpack_from('>f', data, 17)[0]
    check("border width", bw == 2.0, f"got {bw}")
    rc = struct.unpack_from('>f', data, 21)[0]
    check("border corner", rc == 4.0, f"got {rc}")
    # red at offset 25
    r = struct.unpack_from('>f', data, 25)[0]
    check("border red", r == 1.0, f"got {r}")


def test_clip_rect():
    """Test clip rect modifier."""
    buf = RemoteComposeBuffer()
    buf.add_clip_rect_modifier()
    data = buf._buffer.clone_bytes()
    check("clip rect opcode", data[0] == Ops.MODIFIER_CLIP_RECT)
    check("clip rect size", len(data) == 1)


def test_rounded_clip():
    """Test rounded clip rect modifier."""
    buf = RemoteComposeBuffer()
    buf.add_round_clip_rect_modifier(10.0, 10.0, 10.0, 10.0)
    data = buf._buffer.clone_bytes()
    check("rounded clip opcode", data[0] == Ops.MODIFIER_ROUNDED_CLIP_RECT)
    ts = struct.unpack_from('>f', data, 1)[0]
    check("rounded clip top_start", ts == 10.0)


def test_click_touch_modifiers():
    """Test click/touch modifiers are just opcodes."""
    buf = RemoteComposeBuffer()
    buf.add_click_modifier_operation()
    data = buf._buffer.clone_bytes()
    check("click opcode", data[0] == Ops.MODIFIER_CLICK)

    buf2 = RemoteComposeBuffer()
    buf2.add_touch_down_modifier_operation()
    data2 = buf2._buffer.clone_bytes()
    check("touch down opcode", data2[0] == Ops.MODIFIER_TOUCH_DOWN)

    buf3 = RemoteComposeBuffer()
    buf3.add_touch_up_modifier_operation()
    data3 = buf3._buffer.clone_bytes()
    check("touch up opcode", data3[0] == Ops.MODIFIER_TOUCH_UP)

    buf4 = RemoteComposeBuffer()
    buf4.add_touch_cancel_modifier_operation()
    data4 = buf4._buffer.clone_bytes()
    check("touch cancel opcode", data4[0] == Ops.MODIFIER_TOUCH_CANCEL)


def test_ripple():
    """Test ripple modifier."""
    buf = RemoteComposeBuffer()
    buf.add_modifier_ripple()
    data = buf._buffer.clone_bytes()
    check("ripple opcode", data[0] == Ops.MODIFIER_RIPPLE)
    check("ripple size", len(data) == 1)


def test_draw_content():
    """Test draw content modifier."""
    buf = RemoteComposeBuffer()
    buf.add_draw_content_operation()
    data = buf._buffer.clone_bytes()
    check("draw content opcode", data[0] == Ops.MODIFIER_DRAW_CONTENT)


def test_container_end():
    """Test container end operation."""
    buf = RemoteComposeBuffer()
    buf.add_container_end()
    data = buf._buffer.clone_bytes()
    check("container end opcode", data[0] == Ops.CONTAINER_END)
    check("container end size", len(data) == 1)


def test_text_data():
    """Test text data encoding."""
    buf = RemoteComposeBuffer()
    buf.add_text(42, "hello")
    data = buf._buffer.clone_bytes()
    check("text opcode", data[0] == Ops.DATA_TEXT)
    tid = struct.unpack_from('>i', data, 1)[0]
    check("text id", tid == 42)
    slen = struct.unpack_from('>i', data, 5)[0]
    check("text str length", slen == 5)
    text = data[9:14].decode('utf-8')
    check("text content", text == "hello", f"got {text!r}")


def test_float_data():
    """Test float data encoding."""
    buf = RemoteComposeBuffer()
    result = buf.add_float(42, 3.14)
    data = buf._buffer.clone_bytes()
    check("float opcode", data[0] == Ops.DATA_FLOAT)
    fid = struct.unpack_from('>i', data, 1)[0]
    check("float id", fid == 42)
    val = struct.unpack_from('>f', data, 5)[0]
    check("float value", abs(val - 3.14) < 0.001)
    check("float result is NaN", math.isnan(result))


def test_integer_data():
    """Test integer data encoding."""
    buf = RemoteComposeBuffer()
    buf.add_integer(42, 100)
    data = buf._buffer.clone_bytes()
    check("int opcode", data[0] == Ops.DATA_INT)
    iid = struct.unpack_from('>i', data, 1)[0]
    check("int id", iid == 42)
    val = struct.unpack_from('>i', data, 5)[0]
    check("int value", val == 100)


def test_action_operations():
    """Test action operation encoding."""
    buf = RemoteComposeBuffer()
    buf.add_value_float_change_action_operation(10, 3.14)
    data = buf._buffer.clone_bytes()
    check("float change opcode", data[0] == Ops.VALUE_FLOAT_CHANGE_ACTION)
    vid = struct.unpack_from('>i', data, 1)[0]
    check("float change id", vid == 10)
    val = struct.unpack_from('>f', data, 5)[0]
    check("float change value", abs(val - 3.14) < 0.001)

    buf2 = RemoteComposeBuffer()
    buf2.add_value_integer_change_action_operation(20, 42)
    data2 = buf2._buffer.clone_bytes()
    check("int change opcode", data2[0] == Ops.VALUE_INTEGER_CHANGE_ACTION)

    buf3 = RemoteComposeBuffer()
    buf3.add_value_string_change_action_operation(30, 31)
    data3 = buf3._buffer.clone_bytes()
    check("string change opcode", data3[0] == Ops.VALUE_STRING_CHANGE_ACTION)


def test_list_and_array():
    """Test list and array encoding."""
    buf = RemoteComposeBuffer()
    buf.add_list(10, [1, 2, 3])
    data = buf._buffer.clone_bytes()
    check("list opcode", data[0] == Ops.ID_LIST)
    lid = struct.unpack_from('>i', data, 1)[0]
    check("list id", lid == 10)
    count = struct.unpack_from('>i', data, 5)[0]
    check("list count", count == 3)

    buf2 = RemoteComposeBuffer()
    buf2.add_float_array(20, [1.0, 2.0, 3.0])
    data2 = buf2._buffer.clone_bytes()
    check("float array opcode", data2[0] == Ops.FLOAT_LIST)


def test_full_document():
    """Test creating a full document and verifying structure."""
    w = RemoteComposeWriter(400, 300, "Test")
    text_id = w.add_text("Hello")
    w.root(lambda:
        w.box(
            RecordingModifier().fill_max_size().background(0xFFFFFFFF),
            Rc.Layout.START, Rc.Layout.TOP,
            lambda: w.text_component(
                RecordingModifier(),
                text_id, 0xFF000000, 24.0, 0, 400.0
            )
        )
    )
    data = w.encode_to_byte_array()
    check("full doc not empty", len(data) > 50)
    check("full doc header", data[0] == 0)  # HEADER opcode
    magic = struct.unpack_from('>I', data, 1)[0]
    check("full doc magic", magic == (1 | 0x048C0000))


def main():
    print("Running encoding verification tests...\n")

    test_wire_buffer()
    test_nan_encoding()
    test_header_v7()
    test_modifier_width()
    test_modifier_padding()
    test_modifier_background()
    test_modifier_border()
    test_clip_rect()
    test_rounded_clip()
    test_click_touch_modifiers()
    test_ripple()
    test_draw_content()
    test_container_end()
    test_text_data()
    test_float_data()
    test_integer_data()
    test_action_operations()
    test_list_and_array()
    test_full_document()

    print(f"\nResults: {PASS} passed, {FAIL} failed out of {PASS + FAIL}")
    return 0 if FAIL == 0 else 1


if __name__ == '__main__':
    sys.exit(main())

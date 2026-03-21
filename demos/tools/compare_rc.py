"""Compare two .rc files at the operation level."""
import struct
import sys


def parse_rc(data):
    ops = []
    pos = 0
    while pos < len(data):
        op = data[pos]
        start = pos
        pos += 1

        if op == 0:  # HEADER
            majmagic = struct.unpack_from('>I', data, pos)[0]; pos += 4
            minor = struct.unpack_from('>I', data, pos)[0]; pos += 4
            patch = struct.unpack_from('>I', data, pos)[0]; pos += 4
            num_entries = struct.unpack_from('>I', data, pos)[0]; pos += 4
            for _ in range(num_entries):
                if pos + 4 > len(data):
                    break
                tag_encoded = struct.unpack_from('>H', data, pos)[0]
                entry_size = struct.unpack_from('>H', data, pos + 2)[0]
                pos += 4 + entry_size
            ops.append((start, f'HEADER(v={majmagic>>16}.{minor}.{patch}, n={num_entries})', pos - start, data[start:pos]))

        elif op == 2:  # DATA_TEXT
            text_id = struct.unpack_from('>i', data, pos)[0]; pos += 4
            str_len = struct.unpack_from('>i', data, pos)[0]; pos += 4
            text = data[pos:pos+str_len].decode('utf-8', errors='replace'); pos += str_len
            ops.append((start, f'DATA_TEXT(id={text_id}, "{text}")', pos - start, data[start:pos]))

        elif op == 3:  # DATA_FLOAT_CONST
            fid = struct.unpack_from('>i', data, pos)[0]; pos += 4
            val = struct.unpack_from('>f', data, pos)[0]; pos += 4
            ops.append((start, f'DATA_FLOAT(id={fid})', pos - start, data[start:pos]))

        elif op == 4:  # DATA_COLOR_EXPR
            pos += 20
            ops.append((start, 'COLOR_EXPR', pos - start, data[start:pos]))

        elif op == 7:  # ANIM_FLOAT
            fid = struct.unpack_from('>i', data, pos)[0]; pos += 4
            pos += 12  # v1, v2, op
            ops.append((start, f'ANIM_FLOAT(id={fid})', pos - start, data[start:pos]))

        elif op == 8:
            ops.append((start, 'GLOBAL_START', 1, data[start:pos]))
        elif op == 9:
            ops.append((start, 'GLOBAL_END', 1, data[start:pos]))

        elif op == 40:  # TXT_MERGE
            mid = struct.unpack_from('>i', data, pos)[0]; pos += 12
            ops.append((start, f'TXT_MERGE(id={mid})', pos - start, data[start:pos]))

        elif op == 41:  # TXT_TRANSFORM
            tid = struct.unpack_from('>i', data, pos)[0]; pos += 20
            ops.append((start, f'TXT_TRANSFORM(id={tid})', pos - start, data[start:pos]))

        elif op == 42:  # TXT_FROM_FLOAT
            tid = struct.unpack_from('>i', data, pos)[0]; pos += 20
            ops.append((start, f'TXT_FROM_FLOAT(id={tid})', pos - start, data[start:pos]))

        elif op == 100:  # MOD_WIDTH
            pos += 8
            ops.append((start, 'MOD_WIDTH', pos - start, data[start:pos]))
        elif op == 101:  # MOD_HEIGHT
            pos += 8
            ops.append((start, 'MOD_HEIGHT', pos - start, data[start:pos]))
        elif op == 102:
            ops.append((start, 'MOD_WIDTH_FILL', 1, data[start:pos]))
        elif op == 103:
            ops.append((start, 'MOD_HEIGHT_FILL', 1, data[start:pos]))

        elif op == 104:  # MOD_BACKGROUND = 36 bytes body
            pos += 36
            ops.append((start, 'MOD_BACKGROUND', pos - start, data[start:pos]))

        elif op == 208:  # TEXT_LAYOUT = 48 bytes body
            cid = struct.unpack_from('>i', data, pos)[0]
            tid = struct.unpack_from('>i', data, pos + 8)[0]
            fsz = struct.unpack_from('>f', data, pos + 16)[0]
            ta = struct.unpack_from('>i', data, pos + 32)[0]
            pos += 48
            ops.append((start, f'TEXT_LAYOUT(cid={cid}, tid={tid}, fsz={fsz}, ta={ta})', pos - start, data[start:pos]))

        elif op == 209:  # CONTENT
            pos += 4
            ops.append((start, 'CONTENT', pos - start, data[start:pos]))

        elif op == 210:
            ops.append((start, 'ROOT', 1, data[start:pos]))

        elif op == 213:  # COLUMN = 20 bytes body
            cid = struct.unpack_from('>i', data, pos)[0]
            pos += 20
            ops.append((start, f'COLUMN(cid={cid})', pos - start, data[start:pos]))

        elif op == 214:  # BOX = 16 bytes body
            cid = struct.unpack_from('>i', data, pos)[0]
            pos += 16
            ops.append((start, f'BOX(cid={cid})', pos - start, data[start:pos]))

        elif op == 204:  # CANVAS
            pos += 4
            ops.append((start, 'CANVAS', pos - start, data[start:pos]))

        elif op == 226:  # PAINT_VALUES
            num = struct.unpack_from('>i', data, pos)[0]; pos += 4
            for _ in range(num):
                ptag = data[pos]; pos += 1
                pos += 4  # all paint params are 4 bytes
            ops.append((start, f'PAINT_VALUES(n={num})', pos - start, data[start:pos]))

        elif op == 233:  # DRAW_ROUND_RECT
            pos += 24
            ops.append((start, 'DRAW_ROUND_RECT', pos - start, data[start:pos]))

        elif op == 234:  # DRAW_CIRCLE
            pos += 12
            ops.append((start, 'DRAW_CIRCLE', pos - start, data[start:pos]))

        elif op == 237:  # DRAW_TEXT_ANCHORED
            pos += 24
            ops.append((start, 'DRAW_TEXT_ANCHORED', pos - start, data[start:pos]))

        elif op == 239:  # CORE_TEXT
            tid = struct.unpack_from('>i', data, pos)[0]; pos += 4
            count = struct.unpack_from('>H', data, pos)[0]; pos += 2
            for _ in range(count):
                tag = data[pos]; pos += 1
                if tag in (18, 19, 22):  # bool tags
                    pos += 1
                elif tag == 20:  # fontAxis array
                    arr_len = struct.unpack_from('>H', data, pos)[0]; pos += 2
                    pos += arr_len * 4
                elif tag == 21:  # fontAxisValues array
                    arr_len = struct.unpack_from('>H', data, pos)[0]; pos += 2
                    pos += arr_len * 4
                else:
                    pos += 4
            ops.append((start, f'CORE_TEXT(tid={tid}, params={count})', pos - start, data[start:pos]))

        elif op == 243:
            pos += 4
            ops.append((start, 'COMP_WIDTH', pos - start, data[start:pos]))
        elif op == 244:
            pos += 4
            ops.append((start, 'COMP_HEIGHT', pos - start, data[start:pos]))

        elif op == 255:
            ops.append((start, 'CONTAINER_END', 1, data[start:pos]))

        else:
            ops.append((start, f'UNKNOWN_OP_{op}', 1, data[start:pos]))

    return ops


def main():
    py_path = sys.argv[1] if len(sys.argv) > 1 else 'demo_text_transform.rc'
    kt_path = sys.argv[2] if len(sys.argv) > 2 else 'integration-tests/player-view-demos/src/main/res/raw/demo_text_transform.rc'

    with open(py_path, 'rb') as f:
        py_data = f.read()
    with open(kt_path, 'rb') as f:
        kt_data = f.read()

    py_ops = parse_rc(py_data)
    kt_ops = parse_rc(kt_data)

    print(f'PY: {len(py_ops)} ops, {len(py_data)} bytes')
    print(f'KT: {len(kt_ops)} ops, {len(kt_data)} bytes')
    print()

    max_i = max(len(py_ops), len(kt_ops))
    for i in range(max_i):
        py = py_ops[i] if i < len(py_ops) else None
        kt = kt_ops[i] if i < len(kt_ops) else None

        if py and kt:
            py_off, py_name, py_sz, py_body = py
            kt_off, kt_name, kt_sz, kt_body = kt
            match = (py_body == kt_body)
            flag = '  ' if match else '>>'
            if not match:
                print(f'{flag} [{i:3d}] PY @{py_off:4d} sz={py_sz:3d} {py_name}')
                print(f'         KT @{kt_off:4d} sz={kt_sz:3d} {kt_name}')
                if py_body != kt_body:
                    for j in range(min(len(py_body), len(kt_body))):
                        if py_body[j] != kt_body[j]:
                            print(f'         First body diff at byte {j}: PY=0x{py_body[j]:02x} KT=0x{kt_body[j]:02x}')
                            break
                    if len(py_body) != len(kt_body):
                        print(f'         Body size: PY={len(py_body)} KT={len(kt_body)}')
        elif py:
            py_off, py_name, py_sz, _ = py
            print(f'>> [{i:3d}] PY @{py_off:4d} sz={py_sz:3d} {py_name} | KT: <missing>')
        else:
            kt_off, kt_name, kt_sz, _ = kt
            print(f'>> [{i:3d}] PY: <missing> | KT @{kt_off:4d} sz={kt_sz:3d} {kt_name}')


if __name__ == '__main__':
    main()

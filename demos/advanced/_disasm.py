"""Disassemble a .rc binary file."""
import struct
import sys

def fmt_f(data, offset):
    raw = struct.unpack('>I', data[offset:offset+4])[0]
    if raw & 0x7F800000 == 0x7F800000 and raw & 0x007FFFFF != 0:
        nan_id = raw & 0x003FFFFF
        if nan_id >= 0x310000:
            op_off = nan_id - 0x310000
            op_map = {1:'ADD',2:'SUB',3:'MUL',4:'DIV',5:'MOD',6:'MIN',7:'MAX',8:'POW',
                      9:'SQRT',10:'ABS',11:'SIGN',12:'CSIGN',13:'EXP',14:'FLOOR',15:'LOG',
                      16:'LN',17:'ROUND',18:'SIN',19:'COS',20:'TAN',21:'ASIN',22:'ACOS',
                      23:'ATAN',24:'ATAN2',25:'MAD',26:'IFELSE',27:'CLAMP',28:'CBRT',
                      29:'DEG',30:'DUP'}
            return op_map.get(op_off, f'OP{op_off}')
        return f'id{nan_id}'
    v = struct.unpack('>f', data[offset:offset+4])[0]
    return f'{v:g}'

def read_paint(data, pos):
    cnt = struct.unpack('>i', data[pos:pos+4])[0]
    result = f'cnt={cnt}'
    j = pos + 4
    for k in range(cnt):
        tag = struct.unpack('>H', data[j:j+2])[0]
        j += 2
        result += f' {tag}:{fmt_f(data, j)}'
        j += 4
    return result, j

def disasm(path):
    ref = open(path, 'rb').read()
    i = 0
    while i < len(ref):
        op = ref[i]
        if i == 0 and op == 0:
            print(f'[{i:4d}] HEADER (29 bytes)')
            i = 29; continue
        if op == 102:
            tid = struct.unpack('>i', ref[i+1:i+5])[0]
            tlen = struct.unpack('>i', ref[i+5:i+9])[0]
            text = ref[i+9:i+9+tlen].decode('utf-8', errors='replace')
            print(f'[{i:4d}] TEXT id={tid} "{text}"')
            i += 9 + tlen
        elif op == 103:
            rid = struct.unpack('>i', ref[i+1:i+5])[0]
            print(f'[{i:4d}] ROOT_CD id={rid}')
            i += 5
        elif op == 200:
            cid = struct.unpack('>i', ref[i+1:i+5])[0]
            print(f'[{i:4d}] ROOT cid={cid}')
            i += 5
        elif op == 202:
            cid = struct.unpack('>i', ref[i+1:i+5])[0]
            pid = struct.unpack('>i', ref[i+5:i+9])[0]
            h2 = struct.unpack('>i', ref[i+9:i+13])[0]
            v2 = struct.unpack('>i', ref[i+13:i+17])[0]
            print(f'[{i:4d}] BOX cid={cid} pid={pid} h={h2} v={v2}')
            i += 17
        elif op == 16:
            mt = struct.unpack('>i', ref[i+1:i+5])[0]
            mv = fmt_f(ref, i+5)
            print(f'[{i:4d}] MOD_W type={mt} val={mv}')
            i += 9
        elif op == 67:
            mt = struct.unpack('>i', ref[i+1:i+5])[0]
            mv = fmt_f(ref, i+5)
            print(f'[{i:4d}] MOD_H type={mt} val={mv}')
            i += 9
        elif op == 201:
            cid = struct.unpack('>i', ref[i+1:i+5])[0]
            print(f'[{i:4d}] CONTENT_START cid={cid}')
            i += 5
        elif op == 205:
            cid = struct.unpack('>i', ref[i+1:i+5])[0]
            pid = struct.unpack('>i', ref[i+5:i+9])[0]
            print(f'[{i:4d}] CANVAS cid={cid} pid={pid}')
            i += 9
        elif op == 207:
            cid = struct.unpack('>i', ref[i+1:i+5])[0]
            print(f'[{i:4d}] CANVAS_CONTENT cid={cid}')
            i += 5
        elif op == 150:
            vt = struct.unpack('>i', ref[i+1:i+5])[0]
            ow = struct.unpack('>i', ref[i+5:i+9])[0]
            did = struct.unpack('>i', ref[i+9:i+13])[0]
            print(f'[{i:4d}] COMP_VAL type={vt} owner={ow} did={did}')
            i += 13
        elif op == 81:
            aid = struct.unpack('>i', ref[i+1:i+5])[0]
            lw = struct.unpack('>I', ref[i+5:i+9])[0]
            vc = lw & 0xFFFF
            ac = (lw >> 16) & 0xFFFF
            vals = [fmt_f(ref, i+9+j*4) for j in range(vc)]
            an = f' +anim[{ac}]' if ac else ''
            print(f'[{i:4d}] AF id={aid} = {vals}{an}')
            i += 9 + (vc + ac) * 4
        elif op == 138:
            cid = struct.unpack('>i', ref[i+1:i+5])[0]
            color = struct.unpack('>I', ref[i+5:i+9])[0]
            print(f'[{i:4d}] COLOR id={cid} 0x{color:08X}')
            i += 9
        elif op == 137:
            vid = struct.unpack('>i', ref[i+1:i+5])[0]
            vtype = struct.unpack('>i', ref[i+5:i+9])[0]
            nlen = struct.unpack('>i', ref[i+9:i+13])[0]
            name = ref[i+13:i+13+nlen].decode('utf-8', errors='replace')
            print(f'[{i:4d}] NAMED id={vid} type={vtype} "{name}"')
            i += 13 + nlen
        elif op == 157:
            aid = struct.unpack('>i', ref[i+1:i+5])[0]
            # Read full touch expression to get size
            j = i + 1 + 4 + 4 + 4 + 4 + 4 + 4  # skip id, def, min, max, vel, effects
            ec = struct.unpack('>i', ref[j:j+4])[0]; j += 4
            j += ec * 4  # skip exp
            packed = struct.unpack('>i', ref[j:j+4])[0]; j += 4
            sl = packed & 0xFFFF
            j += sl * 4  # skip touch spec
            eac = struct.unpack('>i', ref[j:j+4])[0]; j += 4
            j += eac * 4  # skip easing spec
            sz = j - i
            print(f'[{i:4d}] TOUCH_EXPR id={aid} ({sz} bytes)')
            i = j
        elif op == 40:
            result, new_pos = read_paint(ref, i+1)
            print(f'[{i:4d}] PAINT {result}')
            i = new_pos
        elif op == 46:
            vals = [fmt_f(ref, i+1+j*4) for j in range(3)]
            print(f'[{i:4d}] CIRCLE({vals[0]}, {vals[1]}, {vals[2]})')
            i += 13
        elif op == 130:
            print(f'[{i:4d}] SAVE')
            i += 1
        elif op == 131:
            print(f'[{i:4d}] RESTORE')
            i += 1
        elif op == 39:
            vals = [fmt_f(ref, i+1+j*4) for j in range(4)]
            print(f'[{i:4d}] CLIP_RECT({vals[0]}, {vals[1]}, {vals[2]}, {vals[3]})')
            i += 17
        elif op == 129:
            vals = [fmt_f(ref, i+1+j*4) for j in range(3)]
            print(f'[{i:4d}] ROTATE({vals[0]}, {vals[1]}, {vals[2]})')
            i += 13
        elif op == 47:
            vals = [fmt_f(ref, i+1+j*4) for j in range(4)]
            print(f'[{i:4d}] LINE({vals[0]}, {vals[1]}, {vals[2]}, {vals[3]})')
            i += 17
        elif op == 42:
            vals = [fmt_f(ref, i+1+j*4) for j in range(4)]
            print(f'[{i:4d}] RECT({vals[0]}, {vals[1]}, {vals[2]}, {vals[3]})')
            i += 17
        elif op == 123:
            pid_raw = struct.unpack('>i', ref[i+1:i+5])[0]
            pid = pid_raw & 0xFFFFFF
            winding = (pid_raw >> 24) & 0xFF
            cnt = struct.unpack('>i', ref[i+5:i+9])[0]
            print(f'[{i:4d}] PATH id={pid} wind={winding} floats={cnt}')
            i += 9 + cnt * 4
        elif op == 124:
            pid = struct.unpack('>i', ref[i+1:i+5])[0]
            print(f'[{i:4d}] DRAW_PATH id={pid}')
            i += 5
        elif op == 133:
            tid = struct.unpack('>i', ref[i+1:i+5])[0]
            x = fmt_f(ref, i+5)
            y = fmt_f(ref, i+9)
            ax = fmt_f(ref, i+13)
            ay = fmt_f(ref, i+17)
            flags = struct.unpack('>i', ref[i+21:i+25])[0]
            print(f'[{i:4d}] TEXT_ANCHOR tid={tid} ({x},{y}) a=({ax},{ay}) f={flags}')
            i += 25
        elif op == 135:
            tid = struct.unpack('>i', ref[i+1:i+5])[0]
            val = fmt_f(ref, i+5)
            d = struct.unpack('>i', ref[i+9:i+13])[0]
            md = struct.unpack('>i', ref[i+13:i+17])[0]
            flags = struct.unpack('>i', ref[i+17:i+21])[0]
            print(f'[{i:4d}] TEXT_FROM_FLOAT id={tid} val={val} d={d} md={md} f={flags}')
            i += 21
        elif op == 127:
            vals = [fmt_f(ref, i+1+j*4) for j in range(2)]
            print(f'[{i:4d}] TRANSLATE({vals[0]}, {vals[1]})')
            i += 9
        elif op == 126:
            vals = [fmt_f(ref, i+1+j*4) for j in range(2)]
            print(f'[{i:4d}] SCALE({vals[0]}, {vals[1]})')
            i += 9
        elif op == 214:
            print(f'[{i:4d}] END')
            i += 1
        else:
            print(f'[{i:4d}] OP{op}(0x{op:02x})')
            i += 1

if __name__ == '__main__':
    path = sys.argv[1] if len(sys.argv) > 1 else 'C:/Users/jason/Downloads/RemoteUI-main/integration-tests/player-view-demos/src/main/res/raw/experimental_gmt.rc'
    disasm(path)

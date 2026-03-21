"""Small animated demo. Port of SmallAnimated.java.

Demonstrates:
- createTextFromFloat with CONTINUOUS_SEC
- drawTextAnchored
- No root/layout — direct canvas operations
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RemoteComposeWriter, Rc


def demo_small_animated():
    rc = RemoteComposeWriter(500, 500, "sd", api_level=7, profiles=0x200)
    tid = rc.create_text_from_float(Rc.Time.CONTINUOUS_SEC, 2, 2, 0)
    rc.rc_paint.set_text_size(120.0).commit()
    rc.draw_text_anchored(tid, 0, 0, -1, 1, 0)

    class Result:
        def encode(self):
            return rc.encode_to_byte_array()
        def save(self, path):
            with open(path, 'wb') as f:
                f.write(self.encode())

    return Result()


if __name__ == '__main__':
    r = demo_small_animated()
    data = r.encode()
    print(f"SmallAnimated: {len(data)} bytes")
    out = os.path.join(os.path.dirname(__file__), '..', 'output', 'small_animated.rc')
    r.save(out)
    print(f"Saved {out}")

"""RemotePath — Python port of Java's RemotePathBase + RemotePath.

Manages a path buffer of float values with NaN-encoded type markers.
Supports SVG path parsing, matrix transforms, and serialization to
float arrays for addPathData().
"""
import math
import re
import struct

from .types.nan_utils import as_nan, id_from_nan


def _f32(v: float) -> float:
    """Round to nearest IEEE 754 32-bit float, matching Java's float precision."""
    return struct.unpack('>f', struct.pack('>f', v))[0]


# Path command constants (match Java PathData)
MOVE = 10
LINE = 11
QUADRATIC = 12
CONIC = 13
CUBIC = 14
CLOSE = 15
DONE = 16


class RemotePath:
    """Port of RemotePathBase + RemotePath.jvm.kt."""

    def __init__(self, path_data: str = None, buffer_size: int = 1024):
        self._max_size = buffer_size
        self._path = [0.0] * self._max_size
        self._size = 0
        self._cx = 0.0
        self._cy = 0.0
        if path_data is not None:
            self._parse_path_data(path_data)

    # ── Internal helpers ──

    def _resize(self, need: int):
        if self._size + need >= self._max_size:
            self._max_size = max(self._max_size * 2, self._size + need)
            self._path.extend([0.0] * (self._max_size - len(self._path)))

    def _add_type(self, cmd_type: int):
        """Add a single type marker (used for CLOSE, DONE)."""
        self._resize(1)
        self._path[self._size] = as_nan(cmd_type)
        self._size += 1

    def _add_move(self, cmd_type: int, a1: float, a2: float):
        """Add type + 2 coords (used for MOVE — NO padding)."""
        self._resize(3)
        self._path[self._size] = as_nan(cmd_type)
        self._size += 1
        self._path[self._size] = _f32(a1)
        self._size += 1
        self._path[self._size] = _f32(a2)
        self._size += 1

    def _add2(self, cmd_type: int, a1: float, a2: float):
        """Add type + 2-slot padding + 2 coords (LINE)."""
        self._resize(5)
        self._path[self._size] = as_nan(cmd_type)
        self._size += 1
        self._size += 2  # flaw padding
        self._path[self._size] = _f32(a1)
        self._size += 1
        self._path[self._size] = _f32(a2)
        self._size += 1

    def _add4(self, cmd_type: int, a1: float, a2: float, a3: float, a4: float):
        """Add type + 2-slot padding + 4 coords (QUADRATIC)."""
        self._resize(7)
        self._path[self._size] = as_nan(cmd_type)
        self._size += 1
        self._size += 2  # flaw padding
        self._path[self._size] = _f32(a1)
        self._size += 1
        self._path[self._size] = _f32(a2)
        self._size += 1
        self._path[self._size] = _f32(a3)
        self._size += 1
        self._path[self._size] = _f32(a4)
        self._size += 1

    def _add5(self, cmd_type: int, a1: float, a2: float, a3: float, a4: float, a5: float):
        """Add type + 2-slot padding + 5 coords (CONIC)."""
        self._resize(8)
        self._path[self._size] = as_nan(cmd_type)
        self._size += 1
        self._size += 2  # flaw padding
        self._path[self._size] = _f32(a1)
        self._size += 1
        self._path[self._size] = _f32(a2)
        self._size += 1
        self._path[self._size] = _f32(a3)
        self._size += 1
        self._path[self._size] = _f32(a4)
        self._size += 1
        self._path[self._size] = _f32(a5)
        self._size += 1

    def _add6(self, cmd_type: int, a1: float, a2: float, a3: float, a4: float,
              a5: float, a6: float):
        """Add type + 2-slot padding + 6 coords (CUBIC)."""
        self._resize(9)
        self._path[self._size] = as_nan(cmd_type)
        self._size += 1
        self._size += 2  # flaw padding
        self._path[self._size] = _f32(a1)
        self._size += 1
        self._path[self._size] = _f32(a2)
        self._size += 1
        self._path[self._size] = _f32(a3)
        self._size += 1
        self._path[self._size] = _f32(a4)
        self._size += 1
        self._path[self._size] = _f32(a5)
        self._size += 1
        self._path[self._size] = _f32(a6)
        self._size += 1

    # ── Public path operations ──

    def move_to(self, x: float, y: float):
        self._add_move(MOVE, x, y)
        self._cx = x
        self._cy = y

    def r_move_to(self, dx: float, dy: float):
        self._cx += dx
        self._cy += dy
        self._add_move(MOVE, self._cx, self._cy)

    def line_to(self, x: float, y: float):
        self._add2(LINE, x, y)
        self._cx = x
        self._cy = y

    def r_line_to(self, dx: float, dy: float):
        self._cx += dx
        self._cy += dy
        self._add2(LINE, self._cx, self._cy)

    def quad_to(self, x1: float, y1: float, x2: float, y2: float):
        self._add4(QUADRATIC, x1, y1, x2, y2)
        self._cx = x2
        self._cy = y2

    def r_quad_to(self, dx1: float, dy1: float, dx2: float, dy2: float):
        self._add4(QUADRATIC, dx1 + self._cx, dy1 + self._cy,
                   dx2 + self._cx, dy2 + self._cy)
        self._cx += dx2
        self._cy += dy2

    def conic_to(self, x1: float, y1: float, x2: float, y2: float, weight: float):
        self._add5(CONIC, x1, y1, x2, y2, weight)
        self._cx = x2
        self._cy = y2

    def r_conic_to(self, dx1: float, dy1: float, dx2: float, dy2: float, weight: float):
        self._add5(CONIC, dx1 + self._cx, dy1 + self._cy,
                   dx2 + self._cx, dy2 + self._cy, weight)
        self._cx += dx2
        self._cy += dy2

    def cubic_to(self, x1: float, y1: float, x2: float, y2: float,
                 x3: float, y3: float):
        self._add6(CUBIC, x1, y1, x2, y2, x3, y3)
        self._cx = x3
        self._cy = y3

    def r_cubic_to(self, dx1: float, dy1: float, dx2: float, dy2: float,
                   dx3: float, dy3: float):
        self._add6(CUBIC, dx1 + self._cx, dy1 + self._cy,
                   dx2 + self._cx, dy2 + self._cy,
                   dx3 + self._cx, dy3 + self._cy)
        self._cx += dx3
        self._cy += dy3

    def close(self):
        self._add_type(CLOSE)

    def reset(self):
        self._size = 0

    def rewind(self):
        self._size = 0

    def is_empty(self) -> bool:
        return self._size == 0

    @property
    def current_x(self) -> float:
        return self._cx

    @property
    def current_y(self) -> float:
        return self._cy

    @property
    def size(self) -> int:
        return self._size

    # ── Serialization ──

    def to_float_array(self) -> list:
        return self._path[:self._size]

    # ── Transform ──

    def transform(self, matrix):
        """Apply an affine transform to all coordinate points.

        matrix should be a 2x3 or 3x3 list/tuple:
          [[a, b, tx], [c, d, ty]] or similar.
        Uses the same traversal logic as RemotePath.jvm.kt transform().
        """
        a, b, tx = _f32(matrix[0][0]), _f32(matrix[0][1]), _f32(matrix[0][2])
        c, d, ty = _f32(matrix[1][0]), _f32(matrix[1][1]), _f32(matrix[1][2])
        i = 0
        p = self._path
        while i < self._size:
            cmd = id_from_nan(p[i])
            if cmd == MOVE:
                i += 1
                self._transform_points(p, i, 1, a, b, tx, c, d, ty)
                i += 2
            elif cmd == LINE:
                i += 3
                self._transform_points(p, i, 1, a, b, tx, c, d, ty)
                i += 2
            elif cmd == QUADRATIC:
                i += 3
                self._transform_points(p, i, 2, a, b, tx, c, d, ty)
                i += 4
            elif cmd == CONIC:
                i += 3
                self._transform_points(p, i, 2, a, b, tx, c, d, ty)
                i += 5  # 4 coords + weight
            elif cmd == CUBIC:
                i += 3
                self._transform_points(p, i, 3, a, b, tx, c, d, ty)
                i += 6
            elif cmd in (CLOSE, DONE):
                i += 1
            else:
                break

    @staticmethod
    def _transform_points(p, offset, n_points, a, b, tx, c, d, ty):
        for k in range(n_points):
            idx = offset + k * 2
            x = p[idx]
            y = p[idx + 1]
            p[idx] = _f32(_f32(_f32(a * x) + _f32(b * y)) + tx)
            p[idx + 1] = _f32(_f32(_f32(c * x) + _f32(d * y)) + ty)

    # ── SVG Path Parsing ──

    def _parse_path_data(self, path_data: str):
        cords = [0.0] * 6
        commands = re.split(r'(?=[MmZzLlHhVvCcSsQqTtAa])', path_data)
        for command in commands:
            command = command.strip()
            if not command:
                continue
            cmd = command[0]
            values_str = command[1:].strip()
            if values_str:
                values = re.split(r'[,\s]+', values_str)
                values = [v for v in values if v]
            else:
                values = []
            if cmd == 'M':
                self.move_to(float(values[0]), float(values[1]))
            elif cmd == 'L':
                for j in range(0, len(values), 2):
                    self.line_to(float(values[j]), float(values[j + 1]))
            elif cmd == 'H':
                for v in values:
                    self.line_to(float(v), cords[1])
            elif cmd == 'C':
                for j in range(0, len(values), 6):
                    self.cubic_to(
                        float(values[j]), float(values[j + 1]),
                        float(values[j + 2]), float(values[j + 3]),
                        float(values[j + 4]), float(values[j + 5]))
            elif cmd == 'S':
                for j in range(0, len(values), 4):
                    self.cubic_to(
                        2 * cords[0] - cords[2],
                        2 * cords[1] - cords[3],
                        float(values[j]), float(values[j + 1]),
                        float(values[j + 2]), float(values[j + 3]))
            elif cmd == 'Q':
                for j in range(0, len(values), 4):
                    self.quad_to(
                        float(values[j]), float(values[j + 1]),
                        float(values[j + 2]), float(values[j + 3]))
            elif cmd == 'Z':
                self.close()
            else:
                raise ValueError(f"Unsupported SVG path command: {cmd}")
            if cmd not in ('Z', 'H') and values:
                cords[0] = float(values[-2])
                cords[1] = float(values[-1])
                if cmd in ('C', 'S'):
                    cords[2] = float(values[-4])
                    cords[3] = float(values[-3])

    # ── Convenience matrix constructors ──

    @staticmethod
    def translate_matrix(tx: float, ty: float):
        return [[1.0, 0.0, tx], [0.0, 1.0, ty]]

    @staticmethod
    def scale_matrix(sx: float, sy: float):
        return [[sx, 0.0, 0.0], [0.0, sy, 0.0]]

    @staticmethod
    def rotate_matrix(degrees: float):
        r = math.radians(degrees)
        cos_r = math.cos(r)
        sin_r = math.sin(r)
        return [[cos_r, -sin_r, 0.0], [sin_r, cos_r, 0.0]]

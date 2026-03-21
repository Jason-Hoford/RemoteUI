"""RMatrix — remote matrix expression wrapper.

Wraps a matrix expression ID and provides multiply operations.
Equivalent to Kotlin's Matrix class.
"""

from __future__ import annotations
from dataclasses import dataclass


@dataclass
class Vector2:
    x: float
    y: float


@dataclass
class Vector3:
    x: float
    y: float
    z: float


@dataclass
class Vector4:
    x: float
    y: float
    z: float
    w: float


class RMatrix:
    """Remote matrix expression — wraps a NaN-encoded matrix ID."""

    def __init__(self, context, *exp: float):
        self.context = context
        self.id: float = context.matrix_expression(*exp)

    def mult2(self, x: float, y: float) -> Vector2:
        """Multiply the matrix by a 2D vector."""
        out = [0.0, 0.0]
        self.context.matrix_multiply(self.id, [x, y], out)
        return Vector2(out[0], out[1])

    def mult3(self, x: float, y: float, z: float) -> Vector3:
        """Multiply the matrix by a 3D vector."""
        out = [0.0, 0.0, 0.0]
        self.context.matrix_multiply(self.id, [x, y, z], out)
        return Vector3(out[0], out[1], out[2])

    def mult4(self, x: float, y: float, z: float, w: float) -> Vector4:
        """Multiply the matrix by a 4D vector."""
        out = [0.0, 0.0, 0.0, 0.0]
        self.context.matrix_multiply(self.id, [x, y, z, w], out)
        return Vector4(out[0], out[1], out[2], out[3])

    def projection_mult(self, x: float, y: float, z: float) -> tuple[float, float, float]:
        """Projection multiply (dividing by w)."""
        out = [0.0, 0.0, 0.0]
        self.context.matrix_multiply(self.id, 1, [x, y, z], out)
        return (out[0], out[1], out[2])

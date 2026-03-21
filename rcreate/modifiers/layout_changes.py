"""LayoutChanges — provides getters/setters for component layout bounds.

Used by compute_measure and compute_position modifiers to allow
dynamic layout adjustments via RFloat expressions.

Matches Java's InternalComponentLayoutChanges.
"""

from __future__ import annotations
from typing import TYPE_CHECKING

from ..types.rfloat import RFloat
from ..types.nan_utils import as_nan, id_from_nan
from ..rc import Rc

if TYPE_CHECKING:
    from ..writer import RemoteComposeWriter

TYPE_MEASURE = 0
TYPE_POSITION = 1


class LayoutChanges:

    def __init__(self, compute_type: int, bounds_id: int,
                 writer: 'RemoteComposeWriter'):
        self._type = compute_type
        self._bounds = as_nan(bounds_id)
        self._bounds_id = bounds_id
        self._writer = writer

    def _get(self, index: float) -> RFloat:
        return RFloat(self._writer, [self._bounds, index, Rc.FloatExpression.A_DEREF])

    def _set(self, index: int, value):
        if self._type == TYPE_MEASURE and index < 2:
            raise RuntimeError("Trying to set position value in a compute measure")
        if self._type == TYPE_POSITION and index > 1:
            raise RuntimeError("Trying to set measure value in a compute position")
        if isinstance(value, RFloat):
            value.writer = self._writer
            self._writer.set_array_value(self._bounds_id, float(index), value.to_float())
        else:
            self._writer.set_array_value(self._bounds_id, float(index), float(value))

    # ── Getters (return RFloat for expression building) ──

    @property
    def x(self) -> RFloat:
        return self._get(0.0)

    @property
    def y(self) -> RFloat:
        return self._get(1.0)

    @property
    def width(self) -> RFloat:
        return self._get(2.0)

    @property
    def height(self) -> RFloat:
        return self._get(3.0)

    @property
    def parent_width(self) -> RFloat:
        return self._get(4.0)

    @property
    def parent_height(self) -> RFloat:
        return self._get(5.0)

    # ── Setters ──

    @x.setter
    def x(self, value):
        self._set(0, value)

    @y.setter
    def y(self, value):
        self._set(1, value)

    @width.setter
    def width(self, value):
        self._set(2, value)

    @height.setter
    def height(self, value):
        self._set(3, value)

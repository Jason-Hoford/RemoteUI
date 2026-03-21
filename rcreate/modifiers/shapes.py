"""Shape classes for clip and border modifiers."""

from __future__ import annotations


class Shape:
    pass


class RectShape(Shape):
    def __init__(self, left: float = 0, top: float = 0,
                 right: float = 0, bottom: float = 0):
        self.left = left
        self.top = top
        self.right = right
        self.bottom = bottom


class RoundedRectShape(Shape):
    def __init__(self, top_start: float, top_end: float,
                 bottom_start: float, bottom_end: float):
        self.top_start = top_start
        self.top_end = top_end
        self.bottom_start = bottom_start
        self.bottom_end = bottom_end


class CircleShape(Shape):
    pass

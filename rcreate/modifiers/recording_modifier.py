"""RecordingModifier — accumulates modifier elements for layout components.

Provides a fluent API for adding modifiers (width, height, padding, background, etc.)
that are later written to the wire buffer during layout serialization.

Matches Java's RecordingModifier.java.
"""

from __future__ import annotations
import math
from typing import TYPE_CHECKING

from .elements import (
    Element, WidthModifier, HeightModifier, PaddingModifier,
    SolidBackgroundModifier, DynamicSolidBackgroundModifier,
    BorderModifier, DynamicBorderModifier, ClipModifier,
    OffsetModifier, VisibilityModifier, ZIndexModifier,
    ClickActionModifier, TouchActionModifier,
    GraphicsLayerModifier, ScrollModifier, RippleModifier,
    MarqueeModifier, DrawWithContentModifier, AlignByModifier,
    AnimateSpecModifier, CollapsiblePriorityModifier,
    WidthInModifier, HeightInModifier, SemanticsModifier,
    ComponentLayoutComputeModifier, UnsupportedModifier,
    EXACT, FILL, WRAP, WEIGHT, FILL_PARENT_MAX_WIDTH, FILL_PARENT_MAX_HEIGHT,
)
from .shapes import Shape, RectShape, RoundedRectShape

if TYPE_CHECKING:
    from ..actions.action import Action


class RecordingModifier:

    def __init__(self):
        self._list: list[Element] = []
        self._id: int = -1
        self._spaced_by: float = 0.0

    def get_list(self) -> list[Element]:
        return self._list

    def get_component_id(self) -> int:
        return self._id

    def get_spaced_by(self) -> float:
        return self._spaced_by

    # ── Component ID ──

    def component_id(self, cid: int) -> 'RecordingModifier':
        self._id = cid
        return self

    # ── Spaced By ──

    def spaced_by(self, value: float) -> 'RecordingModifier':
        self._spaced_by = value
        return self

    # ── Dimension helpers ──

    def _find_width_modifier(self) -> WidthModifier | None:
        for m in self._list:
            if isinstance(m, WidthModifier):
                return m
        return None

    def _set_width_modifier(self, dim_type: int, value: float):
        wm = self._find_width_modifier()
        if wm is None:
            self._list.append(WidthModifier(dim_type, value))
        else:
            wm.update(dim_type, value)

    def _find_height_modifier(self) -> HeightModifier | None:
        for m in self._list:
            if isinstance(m, HeightModifier):
                return m
        return None

    def _set_height_modifier(self, dim_type: int, value: float):
        hm = self._find_height_modifier()
        if hm is None:
            self._list.append(HeightModifier(dim_type, value))
        else:
            hm.update(dim_type, value)

    # ── Width / Height ──

    def width(self, value) -> 'RecordingModifier':
        self._set_width_modifier(EXACT, float(value))
        return self

    def height(self, value) -> 'RecordingModifier':
        self._set_height_modifier(EXACT, float(value))
        return self

    def size(self, width_or_value, height=None) -> 'RecordingModifier':
        if height is None:
            return self.width(width_or_value).height(width_or_value)
        return self.width(width_or_value).height(height)

    def wrap_content_size(self) -> 'RecordingModifier':
        self._set_width_modifier(WRAP, 0)
        self._set_height_modifier(WRAP, 0)
        return self

    def wrap_content_width(self) -> 'RecordingModifier':
        self._set_width_modifier(WRAP, 0)
        return self

    def wrap_content_height(self) -> 'RecordingModifier':
        self._set_height_modifier(WRAP, 0)
        return self

    def horizontal_weight(self, value: float) -> 'RecordingModifier':
        self._set_width_modifier(WEIGHT, value)
        return self

    def vertical_weight(self, value: float) -> 'RecordingModifier':
        self._set_height_modifier(WEIGHT, value)
        return self

    def fill_max_width(self, fraction: float = float('nan')) -> 'RecordingModifier':
        self._set_width_modifier(FILL, fraction)
        return self

    def fill_max_height(self, fraction: float = float('nan')) -> 'RecordingModifier':
        self._set_height_modifier(FILL, fraction)
        return self

    def fill_max_size(self, fraction: float = float('nan')) -> 'RecordingModifier':
        return self.fill_max_width(fraction).fill_max_height(fraction)

    def fill_parent_max_width(self, fraction: float = 1.0) -> 'RecordingModifier':
        self._set_width_modifier(FILL_PARENT_MAX_WIDTH, fraction)
        return self

    def fill_parent_max_height(self, fraction: float = 1.0) -> 'RecordingModifier':
        self._set_height_modifier(FILL_PARENT_MAX_HEIGHT, fraction)
        return self

    def fill_parent_max_size(self, fraction: float = 1.0) -> 'RecordingModifier':
        return self.fill_parent_max_width(fraction).fill_parent_max_height(fraction)

    def width_in(self, min_val: float, max_val: float) -> 'RecordingModifier':
        self.then_element(WidthInModifier(min_val, max_val))
        return self

    def height_in(self, min_val: float, max_val: float) -> 'RecordingModifier':
        self.then_element(HeightInModifier(min_val, max_val))
        return self

    # ── Weight / Fill queries ──

    def get_horizontal_weight(self) -> float:
        wm = self._find_width_modifier()
        if wm is not None and wm.dim_type == WEIGHT:
            return wm.value
        return float('nan')

    def get_vertical_weight(self) -> float:
        hm = self._find_height_modifier()
        if hm is not None and hm.dim_type == WEIGHT:
            return hm.value
        return float('nan')

    def get_fill_max_width(self) -> bool:
        wm = self._find_width_modifier()
        return wm is not None and wm.dim_type == FILL

    def get_fill_max_height(self) -> bool:
        hm = self._find_height_modifier()
        return hm is not None and hm.dim_type == FILL

    # ── Padding ──

    def padding(self, start_or_all, top=None, end=None, bottom=None) -> 'RecordingModifier':
        if top is None:
            v = float(start_or_all)
            self._list.append(PaddingModifier(v, v, v, v))
        else:
            self._list.append(PaddingModifier(
                float(start_or_all), float(top), float(end), float(bottom)))
        return self

    # ── Background ──

    def background(self, color_or_r, g=None, b=None, a=None) -> 'RecordingModifier':
        if g is not None:
            self._list.append(SolidBackgroundModifier(color_or_r, g, b, a))
        else:
            self._list.append(SolidBackgroundModifier(color_or_r))
        return self

    def background_id(self, color_id: int) -> 'RecordingModifier':
        self._list.append(DynamicSolidBackgroundModifier(color_id))
        return self

    # ── Border ──

    def border(self, width: float, rounded_corner: float,
               color: int, shape: int = 0) -> 'RecordingModifier':
        self._list.append(BorderModifier(width, rounded_corner, color, shape))
        return self

    def dynamic_border(self, width: float, rounded_corner: float,
                       color_id: int, shape: int = 0) -> 'RecordingModifier':
        self._list.append(DynamicBorderModifier(width, rounded_corner, color_id, shape))
        return self

    # ── Clip ──

    def clip(self, shape: Shape) -> 'RecordingModifier':
        self._list.append(ClipModifier(shape))
        return self

    # ── Offset ──

    def offset(self, x: float, y: float) -> 'RecordingModifier':
        self._list.append(OffsetModifier(x, y))
        return self

    # ── Visibility ──

    def visibility(self, value_id: int) -> 'RecordingModifier':
        self._list.append(VisibilityModifier(value_id))
        return self

    # ── Z-Index ──

    def z_index(self, value: float) -> 'RecordingModifier':
        self._list.append(ZIndexModifier(value))
        return self

    # ── Click / Touch actions ──

    def on_click(self, *actions: 'Action') -> 'RecordingModifier':
        self._list.append(ClickActionModifier(list(actions)))
        return self

    def on_touch_down(self, *actions: 'Action') -> 'RecordingModifier':
        self._list.append(TouchActionModifier(TouchActionModifier.DOWN, list(actions)))
        return self

    def on_touch_up(self, *actions: 'Action') -> 'RecordingModifier':
        self._list.append(TouchActionModifier(TouchActionModifier.UP, list(actions)))
        return self

    def on_touch_cancel(self, *actions: 'Action') -> 'RecordingModifier':
        self._list.append(TouchActionModifier(TouchActionModifier.CANCEL, list(actions)))
        return self

    # ── Scroll ──

    def horizontal_scroll(self) -> 'RecordingModifier':
        self._list.append(ClipModifier(RectShape(0, 0, 0, 0)))
        self._list.append(ScrollModifier(ScrollModifier.HORIZONTAL, 0.0, 0))
        return self

    def vertical_scroll(self, position: float = 0.0) -> 'RecordingModifier':
        self._list.append(ClipModifier(RectShape(0, 0, 0, 0)))
        self._list.append(ScrollModifier(ScrollModifier.VERTICAL, position, 0))
        return self

    # ── Ripple ──

    def ripple(self) -> 'RecordingModifier':
        self._list.append(RippleModifier())
        return self

    # ── Marquee ──

    def marquee(self, iterations: int, animation_mode: int,
                repeat_delay_millis: float, initial_delay_millis: float,
                spacing: float, velocity: float) -> 'RecordingModifier':
        self._list.append(MarqueeModifier(
            iterations, animation_mode,
            repeat_delay_millis, initial_delay_millis,
            spacing, velocity))
        return self

    # ── Draw with content ──

    def draw_with_content(self) -> 'RecordingModifier':
        self._list.append(DrawWithContentModifier())
        return self

    # ── Graphics Layer ──

    def graphics_layer(self) -> GraphicsLayerModifier:
        gl = GraphicsLayerModifier()
        self._list.append(gl)
        return gl

    # ── Align by baseline ──

    def align_by_baseline(self) -> 'RecordingModifier':
        from ..rc import Rc
        self._list.append(AlignByModifier(Rc.Layout.FIRST_BASELINE))
        return self

    def align_by(self, line: float) -> 'RecordingModifier':
        self._list.append(AlignByModifier(line))
        return self

    # ── Animation Spec ──

    def animate_spec(self, animation_id: int, motion_duration: float,
                     motion_easing_type: int, visibility_duration: float,
                     visibility_easing_type: int, enter_animation: int,
                     exit_animation: int) -> 'RecordingModifier':
        self._list.append(AnimateSpecModifier(
            animation_id, motion_duration, motion_easing_type,
            visibility_duration, visibility_easing_type,
            enter_animation, exit_animation))
        return self

    # ── Collapsible Priority ──

    def collapsible_priority(self, orientation: int,
                             priority: float) -> 'RecordingModifier':
        self._list.append(CollapsiblePriorityModifier(orientation, priority))
        return self

    # ── Semantics ──

    def semantics(self, semantics_obj) -> 'RecordingModifier':
        self._list.append(SemanticsModifier(semantics_obj))
        return self

    # ── Layout Compute ──

    def layout_compute(self, compute_type: int, commands) -> 'RecordingModifier':
        self._list.append(ComponentLayoutComputeModifier(compute_type, commands))
        return self

    def compute_measure(self, callback) -> 'RecordingModifier':
        """Add a compute-measure modifier. callback receives a LayoutChanges object."""
        def commands(compute_type, bounds_id, writer):
            from .layout_changes import LayoutChanges
            c = LayoutChanges(compute_type, bounds_id, writer)
            callback(c)
        self._list.append(ComponentLayoutComputeModifier(0, commands))  # TYPE_MEASURE=0
        return self

    def compute_position(self, callback) -> 'RecordingModifier':
        """Add a compute-position modifier. callback receives a LayoutChanges object."""
        def commands(compute_type, bounds_id, writer):
            from .layout_changes import LayoutChanges
            c = LayoutChanges(compute_type, bounds_id, writer)
            callback(c)
        self._list.append(ComponentLayoutComputeModifier(1, commands))  # TYPE_POSITION=1
        return self

    # ── Composition ──

    def then(self, other: 'RecordingModifier') -> 'RecordingModifier':
        self._list.extend(other._list)
        return self

    def then_element(self, element: Element) -> 'RecordingModifier':
        self._list.append(element)
        return self

    # ── Find ──

    def find(self, element_type: type) -> Element | None:
        for element in self._list:
            if isinstance(element, element_type):
                return element
        return None

    def write(self, buffer):
        pass

    def __repr__(self):
        return f"RecordingModifier{{list={self._list}}}"

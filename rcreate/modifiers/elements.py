"""Modifier element classes — individual modifiers that write to the buffer.

Each Element has a write(writer) method that delegates to the writer's
buffer-writing methods. Matches Java's modifier Element implementations.
"""

from __future__ import annotations
from typing import TYPE_CHECKING
from .shapes import Shape, RectShape, RoundedRectShape, CircleShape

if TYPE_CHECKING:
    from ..writer import RemoteComposeWriter

# DimensionModifierOperation.Type ordinals (must match Java enum)
EXACT = 0
FILL = 1
WRAP = 2
WEIGHT = 3
INTRINSIC_MIN = 4
INTRINSIC_MAX = 5
EXACT_DP = 6
FILL_PARENT_MAX_WIDTH = 7
FILL_PARENT_MAX_HEIGHT = 8


class Element:
    """Base interface for modifier elements."""
    def write(self, writer: 'RemoteComposeWriter'):
        raise NotImplementedError


class WidthModifier(Element):
    def __init__(self, dim_type: int = EXACT, value: float = float('nan')):
        self.dim_type = dim_type
        self.value = value

    def update(self, dim_type: int, value: float):
        self.dim_type = dim_type
        self.value = value

    def write(self, writer: 'RemoteComposeWriter'):
        writer.add_width_modifier_operation(self.dim_type, self.value)


class HeightModifier(Element):
    def __init__(self, dim_type: int = EXACT, value: float = float('nan')):
        self.dim_type = dim_type
        self.value = value

    def update(self, dim_type: int, value: float):
        self.dim_type = dim_type
        self.value = value

    def write(self, writer: 'RemoteComposeWriter'):
        writer.add_height_modifier_operation(self.dim_type, self.value)


class PaddingModifier(Element):
    def __init__(self, left: float, top: float, right: float, bottom: float):
        self.left = left
        self.top = top
        self.right = right
        self.bottom = bottom

    def write(self, writer: 'RemoteComposeWriter'):
        writer.add_modifier_padding(self.left, self.top, self.right, self.bottom)


class SolidBackgroundModifier(Element):
    def __init__(self, color_or_r, g: float = None, b: float = None, a: float = None):
        if g is not None:
            self.red = color_or_r
            self.green = g
            self.blue = b
            self.alpha = a
        else:
            color = color_or_r & 0xFFFFFFFF
            self.red = ((color >> 16) & 0xFF) / 255.0
            self.green = ((color >> 8) & 0xFF) / 255.0
            self.blue = (color & 0xFF) / 255.0
            self.alpha = ((color >> 24) & 0xFF) / 255.0

    def write(self, writer: 'RemoteComposeWriter'):
        writer.add_modifier_background(self.red, self.green, self.blue, self.alpha, 0)


class DynamicSolidBackgroundModifier(Element):
    def __init__(self, color_id: int):
        self.color_id = color_id

    def write(self, writer: 'RemoteComposeWriter'):
        writer.add_dynamic_modifier_background(self.color_id, 0)


class BorderModifier(Element):
    def __init__(self, width: float, rounded_corner: float, color: int, shape_type: int = 0):
        self.width = width
        self.rounded_corner = rounded_corner
        self.color = color
        self.shape_type = shape_type

    def write(self, writer: 'RemoteComposeWriter'):
        writer.add_modifier_border(self.width, self.rounded_corner,
                                   self.color, self.shape_type)


class DynamicBorderModifier(Element):
    def __init__(self, width: float, rounded_corner: float,
                 color_id: int, shape_type: int = 0):
        self.width = width
        self.rounded_corner = rounded_corner
        self.color_id = color_id
        self.shape_type = shape_type

    def write(self, writer: 'RemoteComposeWriter'):
        writer.add_modifier_dynamic_border(self.width, self.rounded_corner,
                                           self.color_id, self.shape_type)


class ClipModifier(Element):
    def __init__(self, shape: Shape):
        self.shape = shape

    def write(self, writer: 'RemoteComposeWriter'):
        if isinstance(self.shape, CircleShape):
            # Java ClipModifier.write() does nothing for CircleShape —
            # it's not a RectShape or RoundedRectShape, so write() is a no-op
            pass
        elif isinstance(self.shape, RoundedRectShape):
            writer.add_round_clip_rect_modifier(
                self.shape.top_start, self.shape.top_end,
                self.shape.bottom_start, self.shape.bottom_end)
        else:
            writer.add_clip_rect_modifier()


class OffsetModifier(Element):
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

    def write(self, writer: 'RemoteComposeWriter'):
        writer.add_modifier_offset(self.x, self.y)


class VisibilityModifier(Element):
    def __init__(self, value_id: int):
        self.value_id = value_id

    def write(self, writer: 'RemoteComposeWriter'):
        writer.add_component_visibility_operation(self.value_id)


class ZIndexModifier(Element):
    def __init__(self, value: float):
        self.value = value

    def write(self, writer: 'RemoteComposeWriter'):
        writer.add_modifier_z_index(self.value)


class ClickActionModifier(Element):
    def __init__(self, actions: list):
        self.actions = list(actions)

    def write(self, writer: 'RemoteComposeWriter'):
        writer.add_click_modifier_operation()
        for action in self.actions:
            action.write(writer)
        writer.add_container_end()


class TouchActionModifier(Element):
    DOWN = 0
    UP = 1
    CANCEL = 2

    def __init__(self, touch_type: int, actions: list):
        self.touch_type = touch_type
        self.actions = list(actions)

    def write(self, writer: 'RemoteComposeWriter'):
        if self.touch_type == self.DOWN:
            writer.add_touch_down_modifier_operation()
        elif self.touch_type == self.UP:
            writer.add_touch_up_modifier_operation()
        else:
            writer.add_touch_cancel_modifier_operation()
        for action in self.actions:
            action.write(writer)
        writer.add_container_end()


class GraphicsLayerModifier(Element):
    def __init__(self):
        self.attributes: dict[int, object] = {}

    def set_float_attribute(self, attr_id: int, value: float):
        self.attributes[attr_id] = value

    def set_int_attribute(self, attr_id: int, value: int):
        self.attributes[attr_id] = value

    def write(self, writer: 'RemoteComposeWriter'):
        writer.add_modifier_graphics_layer(self.attributes)


class ScrollModifier(Element):
    VERTICAL = 0
    HORIZONTAL = 1

    def __init__(self, direction: int, position_id: float = 0.0, notches: int = 0):
        self.direction = direction
        self.position_id = position_id
        self.notches = notches

    def write(self, writer: 'RemoteComposeWriter'):
        if self.position_id <= 0.0:
            variable = writer.add_float_constant(0.0)
            writer.add_modifier_scroll(self.direction, variable)
        elif self.notches <= 0:
            writer.add_modifier_scroll(self.direction, self.position_id)
        else:
            writer.add_modifier_scroll(self.direction, self.position_id, self.notches)


class RippleModifier(Element):
    def write(self, writer: 'RemoteComposeWriter'):
        writer.add_modifier_ripple()


class MarqueeModifier(Element):
    def __init__(self, iterations: int, animation_mode: int,
                 repeat_delay_millis: float, initial_delay_millis: float,
                 spacing: float, velocity: float):
        self.iterations = iterations
        self.animation_mode = animation_mode
        self.repeat_delay_millis = repeat_delay_millis
        self.initial_delay_millis = initial_delay_millis
        self.spacing = spacing
        self.velocity = velocity

    def write(self, writer: 'RemoteComposeWriter'):
        writer.add_modifier_marquee(
            self.iterations, self.animation_mode,
            self.repeat_delay_millis, self.initial_delay_millis,
            self.spacing, self.velocity)


class DrawWithContentModifier(Element):
    def write(self, writer: 'RemoteComposeWriter'):
        writer.add_draw_content_operation()


class AlignByModifier(Element):
    def __init__(self, line: float):
        self.line = line

    def write(self, writer: 'RemoteComposeWriter'):
        writer.add_align_by_modifier(self.line)


class AnimateSpecModifier(Element):
    def __init__(self, animation_id: int, motion_duration: float,
                 motion_easing_type: int, visibility_duration: float,
                 visibility_easing_type: int, enter_animation: int,
                 exit_animation: int):
        self.animation_id = animation_id
        self.motion_duration = motion_duration
        self.motion_easing_type = motion_easing_type
        self.visibility_duration = visibility_duration
        self.visibility_easing_type = visibility_easing_type
        self.enter_animation = enter_animation
        self.exit_animation = exit_animation

    def write(self, writer: 'RemoteComposeWriter'):
        writer.add_animation_spec_modifier(
            self.animation_id, self.motion_duration,
            self.motion_easing_type, self.visibility_duration,
            self.visibility_easing_type, self.enter_animation,
            self.exit_animation)


class CollapsiblePriorityModifier(Element):
    HORIZONTAL = 0
    VERTICAL = 1

    def __init__(self, orientation: int, priority: float):
        self.orientation = orientation
        self.priority = priority

    def write(self, writer: 'RemoteComposeWriter'):
        writer.add_collapsible_priority_modifier(self.orientation, self.priority)


class WidthInModifier(Element):
    def __init__(self, min_val: float, max_val: float):
        self.min_val = min_val
        self.max_val = max_val

    def write(self, writer: 'RemoteComposeWriter'):
        writer.add_width_in_modifier_operation(self.min_val, self.max_val)


class HeightInModifier(Element):
    def __init__(self, min_val: float, max_val: float):
        self.min_val = min_val
        self.max_val = max_val

    def write(self, writer: 'RemoteComposeWriter'):
        writer.add_height_in_modifier_operation(self.min_val, self.max_val)


class SemanticsModifier(Element):
    def __init__(self, semantics):
        self.semantics = semantics

    def write(self, writer: 'RemoteComposeWriter'):
        writer._buffer._buffer.start(self.semantics.op_code)
        self.semantics.write(writer._buffer._buffer)


class ComponentLayoutComputeModifier(Element):
    def __init__(self, compute_type: int, commands):
        self.compute_type = compute_type
        self.commands = commands

    def write(self, writer: 'RemoteComposeWriter'):
        writer.add_layout_compute(self.compute_type, self.commands)


class UnsupportedModifier(Element):
    def __init__(self, name: str):
        self.name = name

    def write(self, writer: 'RemoteComposeWriter'):
        pass

    def __repr__(self):
        return f"UnsupportedModifier{{name='{self.name}'}}"

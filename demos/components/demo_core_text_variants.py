"""Context API demos using CORE_TEXT (opcode 239) for text components.

These produce c_ prefix .rc files that match the Kotlin
RemoteComposeContextAndroid output which uses CoreText encoding.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate.context import RcContext

# Save originals
_original_text = RcContext.text
_original_text_by_id = RcContext.text_by_id


def _core_text(self, *args, **kwargs):
    kwargs['use_core_text'] = True
    return _original_text(self, *args, **kwargs)


def _core_text_by_id(self, *args, **kwargs):
    kwargs['use_core_text'] = True
    return _original_text_by_id(self, *args, **kwargs)


def _with_core_text(demo_func):
    """Run a demo function with CORE_TEXT mode enabled for all text calls."""
    RcContext.text = _core_text
    RcContext.text_by_id = _core_text_by_id
    try:
        return demo_func()
    finally:
        RcContext.text = _original_text
        RcContext.text_by_id = _original_text_by_id


# Import the base demo functions
from demos.components.demo_text import demo_text
from demos.components.demo_fit_box import demo_fit_box
from demos.components.demo_modifier_align_by_baseline import demo_modifier_align_by_baseline
from demos.components.demo_modifier_on_click import demo_modifier_on_click
from demos.components.demo_modifier_on_touch_cancel import demo_modifier_on_touch_cancel
from demos.components.demo_modifier_on_touch_down import demo_modifier_on_touch_down
from demos.components.demo_modifier_on_touch_up import demo_modifier_on_touch_up
from demos.components.demo_modifier_horizontal_scroll import demo_modifier_horizontal_scroll
from demos.components.demo_modifier_vertical_scroll import demo_modifier_vertical_scroll
from demos.components.demo_box import demo_box
from demos.components.demo_collapsible_column import demo_collapsible_column
from demos.components.demo_collapsible_row import demo_collapsible_row
from demos.components.demo_column import demo_column
from demos.components.demo_flow import demo_flow
from demos.components.demo_image import demo_image
from demos.components.demo_modifier_background import demo_modifier_background
from demos.components.demo_modifier_background_id import demo_modifier_background_id
from demos.components.demo_modifier_border import demo_modifier_border
from demos.components.demo_modifier_clip_circle import demo_modifier_clip_circle
from demos.components.demo_modifier_clip_rect import demo_modifier_clip_rect
from demos.components.demo_modifier_clip_rounded_rect import demo_modifier_clip_rounded_rect
from demos.components.demo_modifier_collapsible_priority import demo_modifier_collapsible_priority
from demos.components.demo_modifier_component_id import demo_modifier_component_id
from demos.components.demo_modifier_compute_measure import demo_modifier_compute_measure
from demos.components.demo_modifier_compute_position import demo_modifier_compute_position
from demos.components.demo_modifier_dynamic_border import demo_modifier_dynamic_border
from demos.components.demo_modifier_fill_max_height import demo_modifier_fill_max_height
from demos.components.demo_modifier_fill_max_size import demo_modifier_fill_max_size
from demos.components.demo_modifier_fill_max_width import demo_modifier_fill_max_width
from demos.components.demo_modifier_fill_parent_max_height import demo_modifier_fill_parent_max_height
from demos.components.demo_modifier_fill_parent_max_size import demo_modifier_fill_parent_max_size
from demos.components.demo_modifier_fill_parent_max_width import demo_modifier_fill_parent_max_width
from demos.components.demo_modifier_height import demo_modifier_height
from demos.components.demo_modifier_height_in import demo_modifier_height_in
from demos.components.demo_modifier_horizontal_weight import demo_modifier_horizontal_weight
from demos.components.demo_modifier_padding import demo_modifier_padding
from demos.components.demo_modifier_size import demo_modifier_size
from demos.components.demo_modifier_spaced_by import demo_modifier_spaced_by
from demos.components.demo_modifier_vertical_weight import demo_modifier_vertical_weight
from demos.components.demo_modifier_visibility import demo_modifier_visibility
from demos.components.demo_modifier_width import demo_modifier_width
from demos.components.demo_modifier_wrap_content_height import demo_modifier_wrap_content_height
from demos.components.demo_modifier_wrap_content_size import demo_modifier_wrap_content_size
from demos.components.demo_modifier_wrap_content_width import demo_modifier_wrap_content_width
from demos.components.demo_modifier_width_in import demo_modifier_width_in
from demos.components.demo_modifier_z_index import demo_modifier_z_index
from demos.components.demo_row import demo_row
from demos.components.demo_state_layout import demo_state_layout
from demos.components.demo_text_auto_size import demo_text_auto_size


# ── Original 9 variants ──

def c_text():
    return _with_core_text(demo_text)


def c_fit_box():
    return _with_core_text(demo_fit_box)


def c_modifier_align_by_baseline():
    return _with_core_text(demo_modifier_align_by_baseline)


def c_modifier_on_click():
    return _with_core_text(demo_modifier_on_click)


def c_modifier_on_touch_cancel():
    return _with_core_text(demo_modifier_on_touch_cancel)


def c_modifier_on_touch_down():
    return _with_core_text(demo_modifier_on_touch_down)


def c_modifier_on_touch_up():
    return _with_core_text(demo_modifier_on_touch_up)


def c_modifier_horizontal_scroll():
    return _with_core_text(demo_modifier_horizontal_scroll)


def c_modifier_vertical_scroll():
    return _with_core_text(demo_modifier_vertical_scroll)


# ── New 30 variants ──

def c_box():
    return _with_core_text(demo_box)


def c_collapsible_column():
    return _with_core_text(demo_collapsible_column)


def c_collapsible_row():
    return _with_core_text(demo_collapsible_row)


def c_column():
    return _with_core_text(demo_column)


def c_flow():
    return _with_core_text(demo_flow)


def c_image():
    return _with_core_text(demo_image)


def c_modifier_background():
    return _with_core_text(demo_modifier_background)


def c_modifier_background_id():
    return _with_core_text(demo_modifier_background_id)


def c_modifier_border():
    return _with_core_text(demo_modifier_border)


def c_modifier_clip_circle():
    return _with_core_text(demo_modifier_clip_circle)


def c_modifier_clip_rect():
    return _with_core_text(demo_modifier_clip_rect)


def c_modifier_clip_rounded_rect():
    return _with_core_text(demo_modifier_clip_rounded_rect)


def c_modifier_collapsible_priority():
    return _with_core_text(demo_modifier_collapsible_priority)


def c_modifier_component_id():
    return _with_core_text(demo_modifier_component_id)


def c_modifier_compute_measure():
    return _with_core_text(demo_modifier_compute_measure)


def c_modifier_compute_position():
    return _with_core_text(demo_modifier_compute_position)


def c_modifier_dynamic_border():
    return _with_core_text(demo_modifier_dynamic_border)


def c_modifier_fill_max_height():
    return _with_core_text(demo_modifier_fill_max_height)


def c_modifier_fill_max_size():
    return _with_core_text(demo_modifier_fill_max_size)


def c_modifier_fill_max_width():
    return _with_core_text(demo_modifier_fill_max_width)


def c_modifier_fill_parent_max_height():
    return _with_core_text(demo_modifier_fill_parent_max_height)


def c_modifier_fill_parent_max_size():
    return _with_core_text(demo_modifier_fill_parent_max_size)


def c_modifier_fill_parent_max_width():
    return _with_core_text(demo_modifier_fill_parent_max_width)


def c_modifier_height():
    return _with_core_text(demo_modifier_height)


def c_modifier_height_in():
    return _with_core_text(demo_modifier_height_in)


def c_modifier_horizontal_weight():
    return _with_core_text(demo_modifier_horizontal_weight)


def c_modifier_padding():
    return _with_core_text(demo_modifier_padding)


def c_modifier_size():
    return _with_core_text(demo_modifier_size)


def c_modifier_spaced_by():
    return _with_core_text(demo_modifier_spaced_by)


def c_modifier_vertical_weight():
    return _with_core_text(demo_modifier_vertical_weight)


def c_modifier_visibility():
    return _with_core_text(demo_modifier_visibility)


def c_modifier_width():
    return _with_core_text(demo_modifier_width)


def c_modifier_wrap_content_height():
    return _with_core_text(demo_modifier_wrap_content_height)


def c_modifier_wrap_content_size():
    return _with_core_text(demo_modifier_wrap_content_size)


def c_modifier_wrap_content_width():
    return _with_core_text(demo_modifier_wrap_content_width)


def c_modifier_width_in():
    return _with_core_text(demo_modifier_width_in)


def c_modifier_zindex():
    return _with_core_text(demo_modifier_z_index)


def c_row():
    return _with_core_text(demo_row)


def c_state_layout():
    return _with_core_text(demo_state_layout)


def c_text_auto_size():
    return _with_core_text(demo_text_auto_size)

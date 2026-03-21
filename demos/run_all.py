"""Generate all demo .rc files and run verification checks."""
import sys
import os
import struct

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from demos.components.demo_box import demo_box
from demos.components.demo_row import demo_row
from demos.components.demo_column import demo_column
from demos.components.demo_text import demo_text
from demos.components.demo_modifier_background import demo_modifier_background
from demos.components.demo_modifier_width import demo_modifier_width
from demos.components.demo_modifier_height import demo_modifier_height
from demos.components.demo_modifier_padding import demo_modifier_padding
from demos.components.demo_modifier_border import demo_modifier_border
from demos.components.demo_modifier_size import demo_modifier_size
from demos.components.demo_modifier_clip_rect import demo_modifier_clip_rect
from demos.components.demo_modifier_clip_rounded_rect import demo_modifier_clip_rounded_rect
from demos.components.demo_modifier_clip_circle import demo_modifier_clip_circle
from demos.components.demo_modifier_on_click import demo_modifier_on_click
from demos.components.demo_modifier_on_touch_down import demo_modifier_on_touch_down
from demos.components.demo_modifier_on_touch_up import demo_modifier_on_touch_up
from demos.components.demo_modifier_on_touch_cancel import demo_modifier_on_touch_cancel
from demos.components.demo_modifier_visibility import demo_modifier_visibility
from demos.components.demo_modifier_z_index import demo_modifier_z_index
from demos.components.demo_modifier_fill_max_width import demo_modifier_fill_max_width
from demos.components.demo_modifier_fill_max_height import demo_modifier_fill_max_height
from demos.components.demo_modifier_fill_max_size import demo_modifier_fill_max_size
from demos.components.demo_modifier_wrap_content_width import demo_modifier_wrap_content_width
from demos.components.demo_modifier_wrap_content_height import demo_modifier_wrap_content_height
from demos.components.demo_modifier_wrap_content_size import demo_modifier_wrap_content_size
from demos.components.demo_modifier_fill_parent_max_width import demo_modifier_fill_parent_max_width
from demos.components.demo_modifier_fill_parent_max_height import demo_modifier_fill_parent_max_height
from demos.components.demo_modifier_fill_parent_max_size import demo_modifier_fill_parent_max_size
from demos.components.demo_modifier_horizontal_weight import demo_modifier_horizontal_weight
from demos.components.demo_modifier_vertical_weight import demo_modifier_vertical_weight
from demos.components.demo_modifier_horizontal_scroll import demo_modifier_horizontal_scroll
from demos.components.demo_modifier_vertical_scroll import demo_modifier_vertical_scroll
from demos.components.demo_modifier_spaced_by import demo_modifier_spaced_by
from demos.components.demo_modifier_width_in import demo_modifier_width_in
from demos.components.demo_modifier_height_in import demo_modifier_height_in
from demos.components.demo_modifier_background_id import demo_modifier_background_id
from demos.components.demo_modifier_dynamic_border import demo_modifier_dynamic_border
from demos.components.demo_modifier_collapsible_priority import demo_modifier_collapsible_priority
from demos.components.demo_modifier_component_id import demo_modifier_component_id
from demos.components.demo_modifier_align_by_baseline import demo_modifier_align_by_baseline
from demos.components.demo_flow import demo_flow
from demos.components.demo_fit_box import demo_fit_box
from demos.components.demo_image import demo_image
from demos.components.demo_collapsible_row import demo_collapsible_row
from demos.components.demo_collapsible_column import demo_collapsible_column
from demos.components.demo_state_layout import demo_state_layout
from demos.components.demo_text_auto_size import demo_text_auto_size
from demos.components.demo_modifier_compute_measure import demo_modifier_compute_measure
from demos.components.demo_modifier_compute_position import demo_modifier_compute_position
from demos.components.demo_core_text_variants import (
    c_text, c_fit_box, c_modifier_align_by_baseline,
    c_modifier_on_click, c_modifier_on_touch_cancel,
    c_modifier_on_touch_down, c_modifier_on_touch_up,
    c_modifier_horizontal_scroll, c_modifier_vertical_scroll,
    c_box, c_collapsible_column, c_collapsible_row, c_column, c_flow,
    c_image, c_modifier_background, c_modifier_background_id,
    c_modifier_border, c_modifier_clip_circle, c_modifier_clip_rect,
    c_modifier_clip_rounded_rect, c_modifier_collapsible_priority,
    c_modifier_component_id, c_modifier_compute_measure,
    c_modifier_compute_position, c_modifier_dynamic_border,
    c_modifier_fill_max_height, c_modifier_fill_max_size,
    c_modifier_fill_max_width, c_modifier_fill_parent_max_height,
    c_modifier_fill_parent_max_size, c_modifier_fill_parent_max_width,
    c_modifier_height, c_modifier_height_in, c_modifier_horizontal_weight,
    c_modifier_padding, c_modifier_size, c_modifier_spaced_by,
    c_modifier_vertical_weight, c_modifier_visibility, c_modifier_width,
    c_modifier_wrap_content_height, c_modifier_wrap_content_size,
    c_modifier_wrap_content_width, c_modifier_width_in,
    c_modifier_zindex,
    c_row, c_state_layout, c_text_auto_size,
)

from demos.advanced.demo_simple_clock import demo_simple_clock
from demos.advanced.demo_color_expression import demo_color_expression
from demos.advanced.demo_digital_clock import demo_digital_clock
from demos.advanced.demo_color_buttons import demo_color_buttons
from demos.advanced.demo_text_transform import demo_text_transform
from demos.advanced.demo_global import demo_global
from demos.advanced.demo_metal_clock import demo_metal_clock
from demos.advanced.demo_touch_slider import demo_touch_slider
from demos.advanced.demo_touch import demo_touch1, demo_touch2
from demos.advanced.demo_touch_stop import (
    demo_stop_instantly, demo_stop_gently, demo_stop_ends, demo_stop_absolute_pos,
    demo_stop_notches_even, demo_stop_notches_percents, demo_stop_notches_absolute,
    demo_touch_wrap, demo_simple_java_anim,
)
from demos.advanced.demo_loop_thumbwheel import demo_loop_thumbwheel
from demos.advanced.demo_small_animated import demo_small_animated
from demos.advanced.demo_graphs import demo_graphs1, demo_graphs2
from demos.advanced.demo_procedural import (
    demo_simple1, demo_simple2, demo_simple3, demo_simple4, demo_simple5, demo_simple6,
    demo_center_text1, demo_version,
    demo_gradient1, demo_gradient2, demo_gradient3, demo_gradient4,
    demo_look_up1, demo_simple_clock_slow, demo_simple_clock_fast,
    demo_basic_path, demo_all_path, demo_spline_demo1,
    demo_acc_sensor1, demo_gyro_sensor1, demo_mag_sensor1, demo_compass,
    demo_light_sensor1,
)
from demos.advanced.demo_flow_control import (
    demo_test_conditional, demo_flow_control_checks1, demo_flow_control_checks2,
)
from demos.advanced.demo_path_expression import (
    demo_path_test1, demo_path_test2, demo_path_test3,
)
from demos.advanced.demo_path_demo import (
    demo_remote_construction, demo_path_tween_demo, demo_path2,
)
from demos.advanced.demo_bitmap_drawing import demo_bit_draw1, demo_bit_draw2
from demos.advanced.demo_impulse import demo_hearts
from demos.advanced.demo_flick import demo_flick_test
from demos.advanced.demo_haptic import demo_haptic1
from demos.advanced.demo_winding_rule import demo_path_winding
from demos.advanced.demo_server_clock import demo_server_clock
from demos.advanced.demo_fancy_clocks import demo_fancy_clock1, demo_fancy_clock2, demo_fancy_clock3
from demos.advanced.demo_graph_raw import demo_graph1, demo_graph2
from demos.advanced.demo_thumbwheel import demo_thumb_wheel1, demo_thumb_wheel2
from demos.advanced.demo_clock_demo1 import demo_clock1, demo_fancy_clock2 as demo_jancy_clock2
from demos.advanced.demo_anchor_text import demo_anchored_text
from demos.advanced.demo_metal_clock2 import demo_fancy_clock2_metal
from demos.advanced.demo_attributed_string import demo_attributed_string
from demos.advanced.demo_pressure_gauge import demo_pressure_gauge
from demos.advanced.demo_color_demos import demo_color
from demos.advanced.demo_countdown import demo_countdown
from demos.advanced.demo_text_baseline import demo_text_baseline
from demos.advanced.demo_use_of_global import demo_use_of_global
from demos.advanced.demo_clock import demo_clock
from demos.advanced.demo_clock_variants import basic_clock, digital_clock1, clock_demo2_jclock2
from demos.advanced.demo_plots import demo_plot2, demo_plot3, demo_plot4, demo_plot_wave
from demos.advanced.demo_themed_plot1 import demo_themed_plot1
from demos.advanced.demo_moon_phases import demo_moon_phases
from demos.advanced.demo_player_info import demo_player_info
from demos.advanced.demo_pie_chart import demo_pie_chart_good, demo_pie_chart, demo_pie_chart2
from demos.advanced.demo_spreadsheet import demo_spreadsheet
from demos.advanced.demo_graphs0 import demo_graphs0
from demos.advanced.demo_color_check import demo_color_list, demo_color_table
from demos.advanced.demo_countdown2 import demo_countdown_kt
from demos.advanced.demo_linear_regression import demo_linear_regression
from demos.advanced.demo_cube3d import demo_cube3d
from demos.advanced.demo_maze import demo_maze_w, demo_maze1_w, demo_maze2_w
from demos.advanced.demo_experimental_gmt import demo_experimental_gmt
from demos.advanced.demo_data_viz import (
    demo_activity_rings, demo_heart_rate_timeline, demo_step_progress_arc,
    demo_weather_forecast_bars, demo_sleep_quality_rings,
    demo_battery_radial_gauge, demo_calendar_heatmap_grid,
    demo_stock_sparkline, demo_moon_phase_dial, demo_hydration_wave,
)
from demos.validation.demo_layout_text_styling import demo_layout_text_styling
from demos.validation.demo_paths_transforms import demo_paths_transforms
from demos.validation.demo_touch_interactive import demo_touch_interactive
from demos.validation.demo_animation_stress import demo_animation_stress
from demos.validation.demo_expressions_lookups import demo_expressions_lookups
from demos.validation.demo_edge_cases import demo_edge_cases

MAGIC_NUMBER = 0x048C0000
MAJOR_VERSION = 1

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), 'output')


def verify_header(data: bytes, name: str) -> bool:
    """Verify the RC file header is valid."""
    if len(data) < 13:
        print(f"  FAIL: {name} too small ({len(data)} bytes)")
        return False

    # First byte = opcode 0 (HEADER)
    if data[0] != 0:
        print(f"  FAIL: {name} first byte is {data[0]:#x}, expected 0x00 (HEADER)")
        return False

    # Next 4 bytes = MAJOR | MAGIC (V7+) or just MAJOR (V6)
    major_magic = struct.unpack_from('>I', data, 1)[0]
    expected_v7 = MAJOR_VERSION | MAGIC_NUMBER
    if major_magic != expected_v7 and major_magic != MAJOR_VERSION:
        print(f"  FAIL: {name} major|magic = {major_magic:#010x}, "
              f"expected {expected_v7:#010x} (V7+) or {MAJOR_VERSION:#010x} (V6)")
        return False

    return True


def run_demo(name: str, demo_func, output_dir: str) -> bool:
    """Run a demo and save the output."""
    try:
        ctx = demo_func()
        data = ctx.encode()
        ok = verify_header(data, name)

        path = os.path.join(output_dir, f"{name}.rc")
        ctx.save(path)

        status = "OK" if ok else "FAIL"
        print(f"  [{status}] {name}: {len(data)} bytes -> {path}")
        return ok
    except Exception as e:
        print(f"  [FAIL] {name}: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    demos = [
        ("demo_box", demo_box),
        ("demo_row", demo_row),
        ("demo_column", demo_column),
        ("demo_text", demo_text),
        ("demo_modifier_background", demo_modifier_background),
        ("demo_modifier_width", demo_modifier_width),
        ("demo_modifier_height", demo_modifier_height),
        ("demo_modifier_padding", demo_modifier_padding),
        ("demo_modifier_border", demo_modifier_border),
        ("demo_modifier_size", demo_modifier_size),
        ("demo_modifier_clip_rect", demo_modifier_clip_rect),
        ("demo_modifier_clip_rounded_rect", demo_modifier_clip_rounded_rect),
        ("demo_modifier_clip_circle", demo_modifier_clip_circle),
        ("demo_modifier_on_click", demo_modifier_on_click),
        ("demo_modifier_on_touch_down", demo_modifier_on_touch_down),
        ("demo_modifier_on_touch_up", demo_modifier_on_touch_up),
        ("demo_modifier_on_touch_cancel", demo_modifier_on_touch_cancel),
        ("demo_modifier_visibility", demo_modifier_visibility),
        ("demo_modifier_z_index", demo_modifier_z_index),
        ("demo_modifier_fill_max_width", demo_modifier_fill_max_width),
        ("demo_modifier_fill_max_height", demo_modifier_fill_max_height),
        ("demo_modifier_fill_max_size", demo_modifier_fill_max_size),
        ("demo_modifier_wrap_content_width", demo_modifier_wrap_content_width),
        ("demo_modifier_wrap_content_height", demo_modifier_wrap_content_height),
        ("demo_modifier_wrap_content_size", demo_modifier_wrap_content_size),
        ("demo_modifier_fill_parent_max_width", demo_modifier_fill_parent_max_width),
        ("demo_modifier_fill_parent_max_height", demo_modifier_fill_parent_max_height),
        ("demo_modifier_fill_parent_max_size", demo_modifier_fill_parent_max_size),
        ("demo_modifier_horizontal_weight", demo_modifier_horizontal_weight),
        ("demo_modifier_vertical_weight", demo_modifier_vertical_weight),
        ("demo_modifier_horizontal_scroll", demo_modifier_horizontal_scroll),
        ("demo_modifier_vertical_scroll", demo_modifier_vertical_scroll),
        ("demo_modifier_spaced_by", demo_modifier_spaced_by),
        ("demo_modifier_width_in", demo_modifier_width_in),
        ("demo_modifier_height_in", demo_modifier_height_in),
        ("demo_modifier_background_id", demo_modifier_background_id),
        ("demo_modifier_dynamic_border", demo_modifier_dynamic_border),
        ("demo_modifier_collapsible_priority", demo_modifier_collapsible_priority),
        ("demo_modifier_component_id", demo_modifier_component_id),
        ("demo_modifier_align_by_baseline", demo_modifier_align_by_baseline),
        ("demo_flow", demo_flow),
        ("demo_fit_box", demo_fit_box),
        ("demo_image", demo_image),
        ("demo_collapsible_row", demo_collapsible_row),
        ("demo_collapsible_column", demo_collapsible_column),
        ("demo_state_layout", demo_state_layout),
        ("demo_text_auto_size", demo_text_auto_size),
        ("demo_modifier_compute_measure", demo_modifier_compute_measure),
        ("demo_modifier_compute_position", demo_modifier_compute_position),
        # Advanced demos
        ("demo_simple_clock", demo_simple_clock),
        ("demo_color_expression", demo_color_expression),
        ("demo_digital_clock", demo_digital_clock),
        ("demo_color_buttons", demo_color_buttons),
        ("demo_text_transform", demo_text_transform),
        ("demo_global", demo_global),
        ("demo_metal_clock", demo_metal_clock),
        ("demo_touch_slider", demo_touch_slider),
        ("demo_touch1", demo_touch1),
        ("demo_touch2", demo_touch2),
        ("stop_instantly", demo_stop_instantly),
        ("stop_gently", demo_stop_gently),
        ("stop_ends", demo_stop_ends),
        ("stop_absolute_pos", demo_stop_absolute_pos),
        ("stop_notches_even", demo_stop_notches_even),
        ("stop_notches_percents", demo_stop_notches_percents),
        ("stop_notches_absolute", demo_stop_notches_absolute),
        ("touch_wrap", demo_touch_wrap),
        ("simple_java_anim", demo_simple_java_anim),
        ("demo_loop_thumbwheel", demo_loop_thumbwheel),
        ("small_animated", demo_small_animated),
        ("demo_graphs1", demo_graphs1),
        ("demo_graphs2", demo_graphs2),
        # Procedural demos
        ("procedure_simple1", demo_simple1),
        ("procedure_simple2", demo_simple2),
        ("procedure_simple3", demo_simple3),
        ("procedure_simple4", demo_simple4),
        ("procedure_simple5", demo_simple5),
        ("procedure_simple6", demo_simple6),
        ("procedure_center_text1", demo_center_text1),
        ("procedure_version", demo_version),
        ("procedure_gradient1", demo_gradient1),
        ("procedure_gradient2", demo_gradient2),
        ("procedure_gradient3", demo_gradient3),
        ("procedure_gradient4", demo_gradient4),
        ("procedure_look_up1", demo_look_up1),
        ("procedure_simple_clock_slow", demo_simple_clock_slow),
        ("procedure_simple_clock_fast", demo_simple_clock_fast),
        ("path_procedural_checks_basic_path", demo_basic_path),
        ("path_procedural_checks_all_path", demo_all_path),
        ("spline_demo_spline_demo1", demo_spline_demo1),
        ("sensor_demo_acc_sensor1", demo_acc_sensor1),
        ("sensor_demo_gyro_sensor1", demo_gyro_sensor1),
        ("sensor_demo_mag_sensor1", demo_mag_sensor1),
        ("sensor_demo_compass", demo_compass),
        ("sensor_demo_light_sensor1", demo_light_sensor1),
        # Flow control demos
        ("flow_control_checks_test_conditional", demo_test_conditional),
        ("flow_control_checks_flow_control_checks1", demo_flow_control_checks1),
        ("flow_control_checks_flow_control_checks2", demo_flow_control_checks2),
        # Path expression demos
        ("demo_path_expression_path_test1", demo_path_test1),
        ("demo_path_expression_path_test2", demo_path_test2),
        ("demo_path_expression_path_test3", demo_path_test3),
        # Path demos
        ("path_demo_remote_construction", demo_remote_construction),
        ("path_demo_path_tween_demo", demo_path_tween_demo),
        ("path_demo_path2", demo_path2),
        # Bitmap drawing demos
        ("demo_bitmap_drawing_bit_draw1", demo_bit_draw1),
        ("demo_bitmap_drawing_bit_draw2", demo_bit_draw2),
        # Impulse demo
        ("impulse_demo_hearts_demo", demo_hearts),
        # Flick demo
        ("demo_flick_flick_test", demo_flick_test),
        # Haptic demo
        ("haptic_demo_demo_haptic1", demo_haptic1),
        # Winding rule demo
        ("demo_winding_rule_path_winding", demo_path_winding),
        # Server-side demos
        ("server_clock", demo_server_clock),
        # Fancy clock demos
        ("fancy_clocks_fancy_clock1", demo_fancy_clock1),
        ("fancy_clocks_fancy_clock2", demo_fancy_clock2),
        ("fancy_clocks_fancy_clock3", demo_fancy_clock3),
        # Graph demos (Graph.java)
        ("graph_graph1", demo_graph1),
        ("graph_graph2", demo_graph2),
        # Thumbwheel demos
        ("thumb_wheel1", demo_thumb_wheel1),
        ("thumb_wheel2", demo_thumb_wheel2),
        # Clock demos (ClockDemo1/2.java)
        ("clock_demo1_clock1", demo_clock1),
        ("clock_demo2_jancy_clock2", demo_jancy_clock2),
        # Anchor text demo
        ("anchored_text", demo_anchored_text),
        # Metal clock fancyClock2
        ("fancy_clock2", demo_fancy_clock2_metal),
        # Attributed string demo
        ("attribute_string", demo_attributed_string),
        # Pressure gauge demo
        ("pressure_gauge", demo_pressure_gauge),
        # Color demo (DemoColor.kt)
        ("color", demo_color),
        # Countdown demo (Countdown.kt)
        ("count_down", demo_countdown),
        # Text baseline demo (Text.kt)
        ("text_baseline", demo_text_baseline),
        # Global demo (DemoGlobal.kt)
        ("demo_use_of_global", demo_use_of_global),
        # Clock (MClock.kt)
        ("clock", demo_clock),
        ("digital_clock1", digital_clock1),
        ("clock_demo2_jclock2", clock_demo2_jclock2),
        # Plot demos (Demo.kt plot2/3/4, PlotWave.kt plotWave)
        ("plot2", demo_plot2),
        ("plot3", demo_plot3),
        ("plot4", demo_plot4),
        ("plot_wave", demo_plot_wave),
        ("themed_plot1", demo_themed_plot1),
        ("moon_phases", demo_moon_phases),
        ("player_info", demo_player_info),
        ("good_pie_chart", demo_pie_chart_good),
        ("pie_chart", demo_pie_chart),
        ("pie_chart2", demo_pie_chart2),
        ("spread_sheet", demo_spreadsheet),
        ("demo_graphs0", demo_graphs0),
        ("activity_rings", demo_activity_rings),
        ("heart_rate_timeline", demo_heart_rate_timeline),
        ("step_progress_arc", demo_step_progress_arc),
        ("weather_forecast_bars", demo_weather_forecast_bars),
        ("sleep_quality_rings", demo_sleep_quality_rings),
        ("battery_radial_gauge", demo_battery_radial_gauge),
        ("calendar_heatmap_grid", demo_calendar_heatmap_grid),
        ("stock_sparkline", demo_stock_sparkline),
        ("moon_phase_dial", demo_moon_phase_dial),
        ("hydration_wave", demo_hydration_wave),
        ("color_list", demo_color_list),
        ("color_table", demo_color_table),
        ("countdown", demo_countdown_kt),
        ("linear_regression", demo_linear_regression),
        ("cube3d", demo_cube3d),
        ("maze", demo_maze_w),
        ("maze1", demo_maze1_w),
        ("maze2", demo_maze2_w),
        ("experimental_gmt", demo_experimental_gmt),
        # Cross-name aliases (same function, different output name to match reference)
        ("touch1", demo_touch1),
        ("touch2", demo_touch2),
        # CoreText (opcode 239) variants — match Kotlin Context API output
        ("c_text", c_text),
        ("c_fit_box", c_fit_box),
        ("c_modifier_align_by_baseline", c_modifier_align_by_baseline),
        ("c_modifier_on_click", c_modifier_on_click),
        ("c_modifier_on_touch_cancel", c_modifier_on_touch_cancel),
        ("c_modifier_on_touch_down", c_modifier_on_touch_down),
        ("c_modifier_on_touch_up", c_modifier_on_touch_up),
        ("c_modifier_horizontal_scroll", c_modifier_horizontal_scroll),
        ("c_modifier_vertical_scroll", c_modifier_vertical_scroll),
        ("c_box", c_box),
        ("c_collapsible_column", c_collapsible_column),
        ("c_collapsible_row", c_collapsible_row),
        ("c_column", c_column),
        ("c_flow", c_flow),
        ("c_image", c_image),
        ("c_modifier_background", c_modifier_background),
        ("c_modifier_background_id", c_modifier_background_id),
        ("c_modifier_border", c_modifier_border),
        ("c_modifier_clip_circle", c_modifier_clip_circle),
        ("c_modifier_clip_rect", c_modifier_clip_rect),
        ("c_modifier_clip_rounded_rect", c_modifier_clip_rounded_rect),
        ("c_modifier_collapsible_priority", c_modifier_collapsible_priority),
        ("c_modifier_component_id", c_modifier_component_id),
        ("c_modifier_compute_measure", c_modifier_compute_measure),
        ("c_modifier_compute_position", c_modifier_compute_position),
        ("c_modifier_dynamic_border", c_modifier_dynamic_border),
        ("c_modifier_fill_max_height", c_modifier_fill_max_height),
        ("c_modifier_fill_max_size", c_modifier_fill_max_size),
        ("c_modifier_fill_max_width", c_modifier_fill_max_width),
        ("c_modifier_fill_parent_max_height", c_modifier_fill_parent_max_height),
        ("c_modifier_fill_parent_max_size", c_modifier_fill_parent_max_size),
        ("c_modifier_fill_parent_max_width", c_modifier_fill_parent_max_width),
        ("c_modifier_height", c_modifier_height),
        ("c_modifier_height_in", c_modifier_height_in),
        ("c_modifier_horizontal_weight", c_modifier_horizontal_weight),
        ("c_modifier_padding", c_modifier_padding),
        ("c_modifier_size", c_modifier_size),
        ("c_modifier_spaced_by", c_modifier_spaced_by),
        ("c_modifier_vertical_weight", c_modifier_vertical_weight),
        ("c_modifier_visibility", c_modifier_visibility),
        ("c_modifier_width", c_modifier_width),
        ("c_modifier_wrap_content_height", c_modifier_wrap_content_height),
        ("c_modifier_wrap_content_size", c_modifier_wrap_content_size),
        ("c_modifier_wrap_content_width", c_modifier_wrap_content_width),
        ("cm_odifier_width_in", c_modifier_width_in),
        ("c_modifier_zindex", c_modifier_zindex),
        ("c_row", c_row),
        ("c_state_layout", c_state_layout),
        ("c_text_auto_size", c_text_auto_size),
        # Validation demos (Python-only, no Java reference)
        ("val_layout_text_styling", demo_layout_text_styling),
        ("val_paths_transforms", demo_paths_transforms),
        ("val_touch_interactive", demo_touch_interactive),
        ("val_animation_stress", demo_animation_stress),
        ("val_expressions_lookups", demo_expressions_lookups),
        ("val_edge_cases", demo_edge_cases),
    ]

    print(f"Running {len(demos)} demos...")
    passed = 0
    failed = 0

    for name, func in demos:
        if run_demo(name, func, OUTPUT_DIR):
            passed += 1
        else:
            failed += 1

    print(f"\nResults: {passed} passed, {failed} failed out of {len(demos)}")
    return 0 if failed == 0 else 1


if __name__ == '__main__':
    sys.exit(main())

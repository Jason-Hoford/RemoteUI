"""Color check demos. Port of ColorCheck.kt.

Demonstrates:
- Named colors, themed colors, color attributes
- CustomScroller (custom scroll modifier with touch expression)
- beginGlobal/endGlobal sections
- Color list display (colorList) and color table display (colorTable)

Target .rc files:
  - color_list.rc  -> demo_color_list()
  - color_table.rc -> demo_color_table()
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RcContext, Modifier, Rc, RecordingModifier
from rcreate.modifiers.elements import Element
from rcreate.types.nan_utils import id_from_nan

# Float expression operators
MUL = Rc.FloatExpression.MUL
ADD = Rc.FloatExpression.ADD
DIV = Rc.FloatExpression.DIV
MOD = Rc.FloatExpression.MOD

PROFILE_ANDROIDX = 0x200
PROFILE_EXPERIMENTAL = 0x1  # RcProfiles.PROFILE_EXPERIMENTAL

# ── Color name arrays (match Kotlin exactly) ──

system_accent1 = [
    "system_accent1_0",
    "system_accent1_10",
    "system_accent1_100",
    "system_accent1_1000",
    "system_accent1_200",
    "system_accent1_300",
    "system_accent1_400",
    "system_accent1_50",
    "system_accent1_500",
    "system_accent1_600",
    "system_accent1_700",
    "system_accent1_800",
    "system_accent1_900",
]

system_accent2 = [
    "system_accent2_0",
    "system_accent2_10",
    "system_accent2_100",
    "system_accent2_1000",
    "system_accent2_200",
    "system_accent2_300",
    "system_accent2_400",
    "system_accent2_50",
    "system_accent2_500",
    "system_accent2_600",
    "system_accent2_700",
    "system_accent2_800",
    "system_accent2_900",
]

system_accent3 = [
    "system_accent3_0",
    "system_accent3_10",
    "system_accent3_100",
    "system_accent3_1000",
    "system_accent3_200",
    "system_accent3_300",
    "system_accent3_400",
    "system_accent3_50",
    "system_accent3_500",
    "system_accent3_600",
    "system_accent3_700",
    "system_accent3_800",
    "system_accent3_900",
]

system_error = [
    "system_error_0",
    "system_error_10",
    "system_error_100",
    "system_error_1000",
    "system_error_200",
    "system_error_300",
    "system_error_400",
    "system_error_50",
    "system_error_500",
    "system_error_600",
    "system_error_700",
    "system_error_800",
    "system_error_900",
]

system_neutral1 = [
    "system_neutral1_0",
    "system_neutral1_10",
    "system_neutral1_100",
    "system_neutral1_1000",
    "system_neutral1_200",
    "system_neutral1_300",
    "system_neutral1_400",
    "system_neutral1_50",
    "system_neutral1_500",
    "system_neutral1_600",
    "system_neutral1_700",
    "system_neutral1_800",
    "system_neutral1_900",
]

system_neutral2 = [
    "system_neutral2_0",
    "system_neutral2_10",
    "system_neutral2_100",
    "system_neutral2_1000",
    "system_neutral2_200",
    "system_neutral2_300",
    "system_neutral2_400",
    "system_neutral2_50",
    "system_neutral2_500",
    "system_neutral2_600",
    "system_neutral2_700",
    "system_neutral2_800",
    "system_neutral2_900",
]

nameList = [
    "background_dark",
    "background_light",
    "black",
    "darker_gray",
    "holo_blue_bright",
    "holo_blue_dark",
    "holo_blue_light",
    "holo_green_dark",
    "holo_green_light",
    "holo_orange_dark",
    "holo_orange_light",
    "holo_purple",
    "holo_red_dark",
    "holo_red_light",
    "system_background_dark",
    "system_background_light",
    "system_control_activated_dark",
    "system_control_activated_light",
    "system_control_highlight_dark",
    "system_control_highlight_light",
    "system_control_normal_dark",
    "system_control_normal_light",
    "system_error_container_dark",
    "system_error_container_light",
    "system_error_dark",
    "system_error_light",
    "system_on_background_dark",
    "system_on_background_light",
    "system_on_error_container_dark",
    "system_on_error_container_light",
    "system_on_error_dark",
    "system_on_error_light",
    "system_on_primary_container_dark",
    "system_on_primary_container_light",
    "system_on_primary_dark",
    "system_on_primary_fixed",
    "system_on_primary_fixed_variant",
    "system_on_primary_light",
    "system_on_secondary_container_dark",
    "system_on_secondary_container_light",
    "system_on_secondary_dark",
    "system_on_secondary_fixed",
    "system_on_secondary_fixed_variant",
    "system_on_secondary_light",
    "system_on_surface_dark",
    "system_on_surface_disabled",
    "system_on_surface_light",
    "system_on_surface_variant_dark",
    "system_on_surface_variant_light",
    "system_on_tertiary_container_dark",
    "system_on_tertiary_container_light",
    "system_on_tertiary_dark",
    "system_on_tertiary_fixed",
    "system_on_tertiary_fixed_variant",
    "system_on_tertiary_light",
    "system_outline_dark",
    "system_outline_disabled",
    "system_outline_light",
    "system_outline_variant_dark",
    "system_outline_variant_light",
    "system_palette_key_color_neutral_dark",
    "system_palette_key_color_neutral_light",
    "system_palette_key_color_neutral_variant_dark",
    "system_palette_key_color_neutral_variant_light",
    "system_palette_key_color_primary_dark",
    "system_palette_key_color_primary_light",
    "system_palette_key_color_secondary_dark",
    "system_palette_key_color_secondary_light",
    "system_palette_key_color_tertiary_dark",
    "system_palette_key_color_tertiary_light",
    "system_primary_container_dark",
    "system_primary_container_light",
    "system_primary_dark",
    "system_primary_fixed",
    "system_primary_fixed_dim",
    "system_primary_light",
    "system_secondary_container_dark",
    "system_secondary_container_light",
    "system_secondary_dark",
    "system_secondary_fixed",
    "system_secondary_fixed_dim",
    "system_secondary_light",
    "system_surface_bright_dark",
    "system_surface_bright_light",
    "system_surface_container_dark",
    "system_surface_container_high_dark",
    "system_surface_container_high_light",
    "system_surface_container_highest_dark",
    "system_surface_container_highest_light",
    "system_surface_container_light",
    "system_surface_container_low_dark",
    "system_surface_container_low_light",
    "system_surface_container_lowest_dark",
    "system_surface_container_lowest_light",
    "system_surface_dark",
    "system_surface_dim_dark",
    "system_surface_dim_light",
    "system_surface_disabled",
    "system_surface_light",
    "system_surface_variant_dark",
    "system_surface_variant_light",
    "system_tertiary_container_dark",
    "system_tertiary_container_light",
    "system_tertiary_dark",
    "system_tertiary_fixed",
    "system_tertiary_fixed_dim",
    "system_tertiary_light",
    "system_text_hint_inverse_dark",
    "system_text_hint_inverse_light",
    "system_text_primary_inverse_dark",
    "system_text_primary_inverse_disable_only_dark",
    "system_text_primary_inverse_disable_only_light",
    "system_text_primary_inverse_light",
    "system_text_secondary_and_tertiary_inverse_dark",
    "system_text_secondary_and_tertiary_inverse_disabled_dark",
    "system_text_secondary_and_tertiary_inverse_disabled_light",
    "system_text_secondary_and_tertiary_inverse_light",
]


# ── CustomScroller modifier element ──

class CustomScrollerElement(Element):
    """Custom scroll modifier matching Kotlin CustomScroller.

    Writes:
    1. MODIFIER_SCROLL(direction, scrollPosition, max, notchMax)
    2. TOUCH_EXPRESSION(...)
    3. CONTAINER_END
    4. DEBUG_MESSAGE
    """

    VERTICAL = 0
    HORIZONTAL = 1

    def __init__(self, mode, direction, touch_position, scroll_position,
                 notches, max_val):
        self.mode = mode
        self.direction = direction
        self.touch_position = touch_position
        self.scroll_position = scroll_position
        self.notches = notches
        self.max_val = max_val

    def write(self, writer):
        direction = self.direction
        scroll_position = self.scroll_position
        touch_position = self.touch_position
        notches = self.notches
        max_val = self.max_val
        mode = self.mode

        notch_max = writer.reserve_float_variable()
        touch_dir = (Rc.Touch.POSITION_X if direction != 0
                     else Rc.Touch.POSITION_Y)

        # ScrollModifierOperation.apply(buffer, direction, scrollPosition, max, notchMax)
        writer._buffer.add_modifier_scroll(direction, scroll_position,
                                           max_val, notch_max)

        # Build expression array
        exp = [
            touch_dir,
            max_val,
            Rc.FloatExpression.DIV,
            float(notches + 1),
            MUL,
            -1.0,
            MUL,
        ]

        # min value: 0.0 or NaN depending on mode bit 0
        import math
        min_val = float('nan') if (mode & 1) != 0 else 0.0
        max_notch = float(notches + (1 if (mode & 1) != 0 else 0))

        # touch mode: STOP_NOTCHES_EVEN or STOP_NOTCHES_SINGLE_EVEN
        touch_mode = (Rc.Touch.STOP_NOTCHES_SINGLE_EVEN if (mode & 2) != 0
                      else Rc.Touch.STOP_NOTCHES_EVEN)

        touch_spec = [max_notch]
        easing_spec = writer.easing(0.5, 10.0, 0.1)

        writer._buffer.add_touch_expression(
            id_from_nan(touch_position),
            0.0,           # def_value
            min_val,        # min
            max_notch,      # max
            0.0,           # velocity_id
            3,             # touch_effects
            exp,
            touch_mode,
            touch_spec,
            easing_spec,
        )
        writer._buffer.add_container_end()
        # Java: "scroll " + touchPosition -> Float.toString(NaN) = "NaN"
        import math
        tp_str = "NaN" if math.isnan(touch_position) else str(touch_position)
        writer.add_debug_message("scroll " + tp_str)


# ── ColorSet class matching Kotlin ──

class ColorSet:
    """Matches Kotlin ColorSet class.

    Creates light/dark themed color pair via the writer.
    """

    def __init__(self, writer, light, light_name, dark, dark_name):
        self.light = light
        self.light_name = light_name
        self.dark = dark
        self.dark_name = dark_name
        self.id = 0
        self.light_id = 0
        self.dark_id = 0

        # Init block — matches Kotlin's init { with(writer) { ... } }
        writer.begin_global()
        self.light_id = writer.add_color(light)
        self.dark_id = writer.add_color(dark)
        writer.set_color_name(self.light_id, "color." + light_name)
        writer.set_color_name(self.dark_id, "color." + dark_name)
        self.id = writer._add_themed_color_ids(self.light_id, self.dark_id)
        writer.end_global()


def make_color_set(ctx, color_list):
    """Port of makeColorSet. Creates ColorSet objects for paired colors."""
    writer = ctx.writer
    ret = []
    n = len(color_list) // 2
    for i in range(n):
        ri = n - i
        light_color = (0x101000 * ((ri * 255) // n)) | 0xFF000000
        # Ensure it fits in signed 32-bit (Java int)
        light_color = light_color & 0xFFFFFFFF
        if light_color >= 0x80000000:
            light_color -= 0x100000000

        dark_color = (0x000010 * ((i * 255) // n)) | 0xFF000000
        dark_color = dark_color & 0xFFFFFFFF
        if dark_color >= 0x80000000:
            dark_color -= 0x100000000

        ret.append(ColorSet(writer, int(light_color), color_list[ri],
                            int(dark_color), color_list[i]))
    return ret


def make_color_list_ids(ctx, color_list):
    """Port of makeColorList. Creates named color IDs."""
    writer = ctx.writer
    ret = []
    writer.begin_global()
    for i in range(len(color_list)):
        color_name = color_list[i]
        cid = writer.add_color(0xFF00FF00 & 0xFFFFFFFF)
        writer.set_color_name(cid, "color." + color_name)
        ret.append(cid)
    writer.end_global()
    return ret


def make_color_tab(ctx, color_list):
    """Port of makeColorTab. Displays color pairs as tabs."""
    c_set = make_color_set(ctx, color_list)

    # Black separator
    with ctx.box(Modifier().background(0xFF000000).fill_max_width().height(4)):
        pass

    pad = 0
    for i in range(len(c_set)):
        c = c_set[i]
        with ctx.row(Modifier().padding(pad, 8, 4, 0)
                     .background(0xFF999999).fill_max_width()):
            dim = 48.0
            with ctx.box(Modifier().padding(4)
                         .background_id(c.id).width(dim * 2).height(dim * 2)):
                pass
            with ctx.column():
                with ctx.row():
                    with ctx.box(Modifier().padding(4)
                                 .background_id(c.light_id)
                                 .width(dim).height(dim - 8)):
                        pass
                    ctx.text(c.light_name, Modifier(), font_size=dim,
                            use_core_text=True)
                with ctx.row():
                    with ctx.box(Modifier().padding(4)
                                 .background_id(c.dark_id)
                                 .width(dim).height(dim - 8)):
                        pass
                    ctx.text(c.dark_name, Modifier(), font_size=48.0,
                            use_core_text=True)
        pad = 4


def make_color_rows(ctx, color_list):
    """Port of makeColorRows. Displays colors as rows with attribute text."""
    cids = make_color_list_ids(ctx, color_list)

    # Black separator
    with ctx.box(Modifier().background(0xFF000000).fill_max_width().height(4)):
        pass

    pad = 0
    for i in range(len(cids)):
        c = cids[i]
        name = color_list[i]
        with ctx.row(Modifier().padding(pad, 0, 4, 0)
                     .background(0xFF999999).fill_max_width()):
            dim = 48.0
            with ctx.box(Modifier().padding(8, 0, 8, 0)
                         .background_id(c).width(dim).height(dim)):
                pass
            ctx.text(name, Modifier(), font_size=dim,
                    use_core_text=True)

            ctx.begin_global()
            blue = ctx.get_color_attribute(c, Rc.ColorAttribute.RED)
            blue_txt = ctx.create_text_from_float(blue, 1, 3, 0)
            ctx.end_global()

            # Kotlin text(blueTxt, modifier, fontSize=dim) matches the simple
            # text(stringId:Int,...) overload -> LAYOUT_TEXT (not CORE_TEXT)
            ctx.text_by_id(blue_txt, Modifier().background_id(c), font_size=dim)

        pad = 4


def demo_color_list():
    """Port of colorList() from ColorCheck.kt -> color_list.rc."""
    ctx = RcContext(500, 500, "Simple Timer",
                    api_level=7,
                    profiles=PROFILE_ANDROIDX | PROFILE_EXPERIMENTAL)

    # Compute len (number of half-lists)
    length = len(system_accent1) // 2
    length += len(system_accent2) // 2
    length += len(system_accent3) // 2
    length += len(system_error) // 2
    length += len(system_neutral1) // 2
    length += len(system_neutral2) // 2
    length += len(nameList) // 2

    touch_position = ctx.add_float_constant(0.0)
    computed_height = ctx.add_float_constant(103.0)
    scroll_size = ctx.float_expression(computed_height, float(length), MUL)
    vis_float = ctx.add_float_constant(1.0)
    vis = id_from_nan(vis_float)
    not_vis_float = ctx.add_float_constant(0.0)
    not_vis = id_from_nan(not_vis_float)
    scroll_position = ctx.float_expression(
        touch_position, computed_height, 20.0, ADD, MUL)

    with ctx.root():
        with ctx.box(Modifier().background(0xFFAAAAAA).fill_max_size(),
                     Rc.Layout.START, Rc.Layout.START):
            with ctx.column(
                    Modifier().fill_max_size().then_element(
                        CustomScrollerElement(
                            0,
                            CustomScrollerElement.VERTICAL,
                            touch_position,
                            scroll_position,
                            length - 5,
                            scroll_size,
                        )
                    )):
                make_color_tab(ctx, system_accent1)
                make_color_tab(ctx, system_accent2)
                make_color_tab(ctx, system_accent3)
                make_color_tab(ctx, system_error)
                make_color_tab(ctx, system_neutral1)
                make_color_tab(ctx, system_neutral2)
                make_color_tab(ctx, nameList)

    return ctx


def demo_color_table():
    """Port of colorTable() from ColorCheck.kt -> color_table.rc."""
    ctx = RcContext(500, 500, "Simple Timer",
                    api_level=7,
                    profiles=PROFILE_ANDROIDX | PROFILE_EXPERIMENTAL)

    # Compute len
    length = len(system_accent1) // 2
    length += len(system_accent2) // 2
    length += len(system_accent3) // 2
    length += len(system_error) // 2
    length += len(system_neutral1) // 2
    length += len(system_neutral2) // 2
    length += len(nameList) // 2

    touch_position = ctx.add_float_constant(0.0)
    computed_height = ctx.add_float_constant(103.0)
    scroll_size = ctx.float_expression(computed_height, float(length), MUL)
    vis_float = ctx.add_float_constant(1.0)
    vis = id_from_nan(vis_float)
    not_vis_float = ctx.add_float_constant(0.0)
    not_vis = id_from_nan(not_vis_float)
    scroll_position = ctx.float_expression(
        touch_position, computed_height, 20.0, ADD, MUL)

    with ctx.root():
        with ctx.box(Modifier().background(0xFFAAAAAA).fill_max_size(),
                     Rc.Layout.START, Rc.Layout.START):
            with ctx.column(
                    Modifier().fill_max_size().then_element(
                        CustomScrollerElement(
                            0,
                            CustomScrollerElement.VERTICAL,
                            touch_position,
                            scroll_position,
                            length - 5,
                            scroll_size,
                        )
                    )):
                make_color_rows(ctx, system_accent1)
                make_color_rows(ctx, system_accent2)
                make_color_rows(ctx, system_accent3)
                make_color_rows(ctx, system_error)
                make_color_rows(ctx, system_neutral1)
                make_color_rows(ctx, system_neutral2)
                make_color_rows(ctx, nameList)

    return ctx


if __name__ == '__main__':
    ref_dir = os.path.join(os.path.dirname(__file__), '..', '..',
                           'integration-tests', 'player-view-demos',
                           'src', 'main', 'res', 'raw')
    out_dir = os.path.join(os.path.dirname(__file__), '..', 'output')
    os.makedirs(out_dir, exist_ok=True)

    for name, func in [('color_list', demo_color_list),
                        ('color_table', demo_color_table)]:
        ctx = func()
        data = ctx.encode()
        print(f"{name}: {len(data)} bytes")

        out_path = os.path.join(out_dir, f'{name}.rc')
        ctx.save(out_path)
        print(f"Saved {out_path}")

        # Compare against reference
        ref_path = os.path.join(ref_dir, f'{name}.rc')
        if os.path.exists(ref_path):
            ref_data = open(ref_path, 'rb').read()
            if data == ref_data:
                print(f"  MATCH: byte-identical to reference {name}.rc")
            else:
                print(f"  DIFF: generated {len(data)} bytes vs reference {len(ref_data)} bytes")
                for i in range(min(len(data), len(ref_data))):
                    if data[i] != ref_data[i]:
                        print(f"    First diff at byte {i}: got 0x{data[i]:02X} vs ref 0x{ref_data[i]:02X}")
                        break
        else:
            print(f"  No reference file at {ref_path}")

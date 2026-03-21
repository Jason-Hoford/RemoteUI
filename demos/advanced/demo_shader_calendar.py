"""Port of ShaderCalendar.kt ShaderCalendar() — shader calendar with wave background."""
import sys
import os
import calendar
import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from rcreate import RcContext, Modifier, Rc
from rcreate.types.nan_utils import as_nan

PROFILE_ANDROIDX = 0x200
PROFILE_DEPRECATED = 0x2

# android.graphics.Color.BLACK
COLOR_BLACK = 0xFF000000

def _load_wave_shader():
    """Load the WAVE_SHADER string from the Kotlin source to preserve exact whitespace."""
    kt_path = os.path.join(os.path.dirname(__file__), '..', '..',
                           'integration-tests', 'player-view-demos',
                           'src', 'main', 'java', 'androidx', 'compose',
                           'remote', 'integration', 'view', 'demos',
                           'examples', 'ShaderCalendar.kt')
    if os.path.exists(kt_path):
        with open(kt_path, 'r') as f:
            content = f.read()
        start = content.find('val WAVE_SHADER =')
        tq_start = content.find('"""', start)
        tq_end = content.find('"""', tq_start + 3)
        return content[tq_start + 3:tq_end]
    # Fallback: inline string (trailing whitespace on lines 6, 49, 55, 67 must be preserved)
    return (
        "\n// modified version of https://www.shadertoy.com/view/ltGSWD\n"
        "\n"
        "uniform float2 iResolution;\n"
        "uniform float iTime;\n"
        "uniform int iMonth;\n"
        "                    \n"
        "float gradient(float p)\n"
        "{\n"
        "    vec2 pt0 = vec2(0.00,0.0);\n"
        "    vec2 pt1 = vec2(0.86,0.1);\n"
        "    vec2 pt2 = vec2(0.955,0.40);\n"
        "    vec2 pt3 = vec2(0.99,1.0);\n"
        "    vec2 pt4 = vec2(1.00,0.0);\n"
        "    if (p < pt0.x) return pt0.y;\n"
        "    if (p < pt1.x) return mix(pt0.y, pt1.y, (p-pt0.x) / (pt1.x-pt0.x));\n"
        "    if (p < pt2.x) return mix(pt1.y, pt2.y, (p-pt1.x) / (pt2.x-pt1.x));\n"
        "    if (p < pt3.x) return mix(pt2.y, pt3.y, (p-pt2.x) / (pt3.x-pt2.x));\n"
        "    if (p < pt4.x) return mix(pt3.y, pt4.y, (p-pt3.x) / (pt4.x-pt3.x));\n"
        "    return pt4.y;\n"
        "}\n"
        "\n"
        "float waveN(vec2 uv, vec2 s12, vec2 t12, vec2 f12, vec2 h12)\n"
        "{\n"
        "    vec2 x12 = sin((iTime * s12 + t12 + uv.x) * f12) * h12;\n"
        "    float g = gradient(uv.y / (0.5 + x12.x + x12.y));\n"
        "\treturn g * 0.27;\n"
        "}\n"
        "\n"
        "float wave1(vec2 uv)\n"
        "{\n"
        "    return waveN(vec2(uv.x,uv.y-0.25), vec2(0.03,0.06), vec2(0.00,0.02), vec2(8.0,3.7), vec2(0.06,0.05));\n"
        "}\n"
        "\n"
        "float wave2(vec2 uv)\n"
        "{\n"
        "    return waveN(vec2(uv.x,uv.y-0.25), vec2(0.04,0.07), vec2(0.16,-0.37), vec2(6.7,2.89), vec2(0.06,0.05));\n"
        "}\n"
        "\n"
        "float wave3(vec2 uv)\n"
        "{\n"
        "    return waveN(vec2(uv.x,0.75-uv.y), vec2(0.035,0.055), vec2(-0.09,0.27), vec2(7.4,2.51), vec2(0.06,0.05));\n"
        "}\n"
        "\n"
        "float wave4(vec2 uv)\n"
        "{\n"
        "    return waveN(vec2(uv.x,0.75-uv.y), vec2(0.032,0.09), vec2(0.08,-0.22), vec2(6.5,3.89), vec2(0.06,0.05));\n"
        "}\n"
        "\n"
        "half4 main(vec2 fragCoord) { \n"
        "    vec2 uv = fragCoord.xy / iResolution.xy;\n"
        "    float month = float(iMonth);\n"
        "    float pos  = (uv.y - month) * 10 ;\n"
        "    uv.y = mod(uv.y, 1);\n"
        "    float waves = wave1(uv) + wave2(uv) + wave3(uv) + wave4(uv);\n"
        "    \n"
        "\tfloat x = uv.x;\n"
        "\tfloat y = abs(uv.y*2-1.0);\n"
        "    y = 1 - y * y;\n"
        "    float con = - pos /(1 + abs(pos));\n"
        "    con = 0.5 * con * con * con;\n"
        "    float sat = 0.3;\n"
        "    vec3 base = vec3( sat+con,sat, sat-con);\n"
        "    vec3 bg = mix(vec3(0.05, 0.05, 0.3), base, (x + y) * 0.55);\n"
        "    vec3 ac = bg + vec3(1.0, 1.0, 1.0) * waves;\n"
        "\n"
        "    return vec4(ac, 1.0);\n"
        "} \n"
    )


WAVE_SHADER = _load_wave_shader()


def month(month_offset, now=None):
    """Generate calendar text lines for a given month offset.

    Faithfully ports the Kotlin month() function from ShaderCalendar.kt.
    Uses the same logic: header uses absolute month index (set),
    grid uses relative offset from current month (add).
    """
    ret = []
    gap = " "

    if now is None:
        now = datetime.datetime.now()

    # Header: cal.set(Calendar.MONTH, monthOffset)
    # Java Calendar.MONTH is 0-based, Python months are 1-based
    # When monthOffset=12, Java wraps to January of next year
    header_month = month_offset  # 0-based
    header_year = now.year
    if header_month > 11:
        header_month -= 12
        header_year += 1
    # Java SimpleDateFormat("LLLL yyyy") gives standalone month name + year
    header_date = datetime.date(header_year, header_month + 1, 1)
    cal_date = header_date.strftime("%B %Y")

    # Center the date header
    sp = (7 * (len(gap) + 2) - len(cal_date)) // 2
    pad = "                          "[:sp]
    ret.append(pad + cal_date)

    # Day-of-week header
    days = "SMTWTFS"
    line = ""
    for ch in days:
        line += gap + " " + ch

    # Grid: cal.add(Calendar.MONTH, monthOffset) from current time
    # Python equivalent: add month_offset months to current month
    grid_month = now.month + month_offset  # 1-based
    grid_year = now.year
    while grid_month > 12:
        grid_month -= 12
        grid_year += 1

    # Get first day of week (Java: Calendar.DAY_OF_WEEK, 1=Sunday)
    # Python: calendar.weekday returns 0=Monday. We need 0=Sunday.
    first_weekday = calendar.weekday(grid_year, grid_month, 1)
    # Convert from Python (0=Mon) to Java (0=Sun): (weekday + 1) % 7
    offset = (first_weekday + 1) % 7

    # Last day of month
    last_day = calendar.monthrange(grid_year, grid_month)[1]

    for pos in range(42):
        row = pos % 7
        if row == 0:
            ret.append(line)
            line = ""

        if offset > pos or pos - offset >= last_day:
            line += gap + "  "
        else:
            num = pos - offset + 1
            if num > 9:
                line += gap + str(num)
            else:
                line += gap + " " + str(num)

    ret.append(line)
    return ret


def _f(v):
    """Truncate to float32 to match Java float arithmetic."""
    import struct
    return struct.unpack('>f', struct.pack('>f', v))[0]


def demo_shader_calendar():
    # Use float32 arithmetic throughout to match Java/Kotlin float computations.
    font_size = _f(48.0)
    line_size = _f(font_size * 1.5)
    block = _f(line_size * 8.6)
    tw = _f(1000.0)
    th = _f(_f(block * 11) - line_size)

    # Use the same reference date as when the Kotlin reference was generated
    # (February 2026) so the output is byte-identical.
    ref_now = datetime.datetime(2026, 2, 1)

    # Java Calendar.MONTH is 0-based
    current_month = ref_now.month - 1

    # RemoteComposeContextAndroid(1000, th.toInt(), "Demo", 8, 0x202, platform)
    ctx = RcContext(1000, int(th), "Demo",
                    api_level=8,
                    profiles=PROFILE_ANDROIDX | PROFILE_DEPRECATED)

    # Kotlin Context API: no explicit root() — operations are written directly
    # setRootContentBehavior(SCROLL_VERTICAL, ALIGNMENT_START+ALIGNMENT_TOP, SIZING_SCALE, SCALE_FIT)
    ctx.set_root_content_behavior(
        Rc.RootContent.SCROLL_VERTICAL,
        Rc.RootContent.ALIGNMENT_START + Rc.RootContent.ALIGNMENT_TOP,
        Rc.RootContent.SIZING_SCALE,
        Rc.RootContent.SCALE_FIT)

    # createShader(WAVE_SHADER)
    #   .setFloatUniform("iTime", TIME_IN_SEC)    <- in Kotlin context, TIME_IN_SEC = FLOAT_CONTINUOUS_SEC = as_nan(1)
    #   .setFloatUniform("iResolution", 1000f, block)
    #   .setIntUniform("iMonth", month)
    #   .commit()
    # Java HashMap iteration order: "iResolution" (bucket 5) before "iTime" (bucket 9)
    shader_id = ctx.create_shader(WAVE_SHADER) \
        .set_float_uniform("iResolution", 1000.0, block) \
        .set_float_uniform("iTime", Rc.Time.CONTINUOUS_SEC) \
        .set_int_uniform("iMonth", current_month) \
        .commit()

    # painter.setShader(id).commit()
    ctx.painter.set_shader(shader_id).commit()

    # drawRect(0f, 0f, tw, th * 2)
    ctx.draw_rect(0.0, 0.0, tw, _f(th * 2))

    # painter.setShader(0).setColor(0x63FFFFFF).commit()
    ctx.painter.set_shader(0).set_color(0x63FFFFFF).commit()

    # Draw rounded rectangles for each month block
    for i in range(13):
        top = _f(_f(i * block) + _f(font_size / 2))
        bottom = _f(_f(top + block) - _f(font_size / 2))
        ctx.draw_round_rect(0.0, top, tw, bottom, 60.0, 60.0)

    # Calculate x offset for centering text
    x_offset = _f(_f(tw - _f(2 * 7 * font_size)) / 2)

    # Draw calendar text for each month
    for i in range(13):
        # painter.setTypeface(3, 700, false).setColor(Color.BLACK).setTextSize(font_size).commit()
        ctx.painter \
            .set_typeface(3, 700, False) \
            .set_color(COLOR_BLACK) \
            .set_text_size(font_size) \
            .commit()

        k = _f(_f(block * i) + _f(font_size * 2))
        lines = month(i, ref_now)
        for j, line in enumerate(lines):
            if j == 2:
                # painter.setTypeface(Typeface.MONOSPACE).commit()
                # Typeface.MONOSPACE = 3, default weight=400, italic=false
                ctx.painter.set_typeface(3).commit()

            # drawTextRun(line, 0, line.length, 0, line.length, xOffset, k, false)
            text_id = ctx.add_text(line)
            ctx.draw_text_run(text_id, 0, len(line), 0, len(line), x_offset, k, False)
            k = _f(k + line_size)

    return ctx


if __name__ == '__main__':
    ctx = demo_shader_calendar()
    data = ctx.encode()
    outdir = os.path.join(os.path.dirname(__file__), '..', 'output')
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, 'shader_calendar.rc')
    ctx.save(path)
    print(f"shader_calendar: {len(data)} bytes -> {path}")

    # Compare with reference
    ref_path = os.path.join(os.path.dirname(__file__), '..', '..',
                            'integration-tests', 'player-view-demos',
                            'src', 'main', 'res', 'raw', 'shader_calendar.rc')
    if os.path.exists(ref_path):
        with open(ref_path, 'rb') as f:
            ref = f.read()
        if data == ref:
            print("MATCH: byte-identical to reference")
        else:
            print(f"DIFF: generated {len(data)} bytes vs reference {len(ref)} bytes")
            # Find first difference
            for i in range(min(len(data), len(ref))):
                if data[i] != ref[i]:
                    print(f"  First diff at byte {i}: generated 0x{data[i]:02x} vs reference 0x{ref[i]:02x}")
                    break
    else:
        print(f"Reference not found: {ref_path}")

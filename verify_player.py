#!/usr/bin/env python3
"""Batch verification harness for the rplayer Python player/runtime.

Renders ALL .rc demos, analyzes the output images, and produces a
structured verification report. Designed to be run repeatedly during
debugging to measure progress.

Usage:
    python verify_player.py                    # render + analyze all demos
    python verify_player.py --report-only      # just re-analyze existing PNGs
    python verify_player.py --filter clock     # only demos matching 'clock'

Output:
    verify_output/python/          — rendered PNG files
    verify_output/report.txt       — human-readable report
    verify_output/report.json      — machine-readable results
"""

import os
import sys
import json
import time
import struct
import zlib
import math
import argparse
import traceback

# Ensure rplayer is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

DEMO_DIR = os.path.join(os.path.dirname(__file__), 'demos', 'output')
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), 'verify_output', 'python')
REPORT_DIR = os.path.join(os.path.dirname(__file__), 'verify_output')


# ── PNG pixel analysis (stdlib only, no Pillow) ────────────────────

def read_png_info(path):
    """Read a PNG file and return pixel statistics without external deps.

    Returns dict with: width, height, total_pixels, non_white_count,
    white_pct, unique_colors (capped at 1000), avg_rgb, is_blank, is_suspicious
    """
    try:
        with open(path, 'rb') as f:
            sig = f.read(8)
            if sig != b'\x89PNG\r\n\x1a\n':
                return {'error': 'not a valid PNG'}

            width = height = 0
            bit_depth = color_type = 0
            idat_chunks = []

            while True:
                header = f.read(8)
                if len(header) < 8:
                    break
                length = struct.unpack('>I', header[:4])[0]
                chunk_type = header[4:8]
                data = f.read(length)
                f.read(4)  # CRC

                if chunk_type == b'IHDR':
                    width = struct.unpack('>I', data[0:4])[0]
                    height = struct.unpack('>I', data[4:8])[0]
                    bit_depth = data[8]
                    color_type = data[9]
                elif chunk_type == b'IDAT':
                    idat_chunks.append(data)
                elif chunk_type == b'IEND':
                    break

            if width == 0 or height == 0:
                return {'error': 'invalid dimensions'}

            # Only handle RGBA (color_type=6) or RGB (color_type=2)
            channels = 4 if color_type == 6 else 3
            stride = width * channels

            raw = zlib.decompress(b''.join(idat_chunks))

            total = width * height
            white_count = 0
            non_white_count = 0
            color_set = set()
            r_sum = g_sum = b_sum = 0

            pos = 0
            prev_row = bytearray(stride)
            for y in range(height):
                if pos >= len(raw):
                    break
                filt = raw[pos]
                pos += 1
                row = bytearray(raw[pos:pos + stride])
                pos += stride

                # Apply PNG filters
                if filt == 1:  # Sub
                    for i in range(stride):
                        a = row[i - channels] if i >= channels else 0
                        row[i] = (row[i] + a) & 0xFF
                elif filt == 2:  # Up
                    for i in range(stride):
                        row[i] = (row[i] + prev_row[i]) & 0xFF
                elif filt == 3:  # Average
                    for i in range(stride):
                        a = row[i - channels] if i >= channels else 0
                        b = prev_row[i]
                        row[i] = (row[i] + (a + b) // 2) & 0xFF
                elif filt == 4:  # Paeth
                    for i in range(stride):
                        a = row[i - channels] if i >= channels else 0
                        b = prev_row[i]
                        c = prev_row[i - channels] if i >= channels else 0
                        p = a + b - c
                        pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                        if pa <= pb and pa <= pc:
                            pr = a
                        elif pb <= pc:
                            pr = b
                        else:
                            pr = c
                        row[i] = (row[i] + pr) & 0xFF

                for x in range(width):
                    off = x * channels
                    r, g, b = row[off], row[off + 1], row[off + 2]
                    if r == 255 and g == 255 and b == 255:
                        white_count += 1
                    else:
                        non_white_count += 1
                    r_sum += r
                    g_sum += g
                    b_sum += b
                    if len(color_set) < 1000:
                        color_set.add((r, g, b))

                prev_row = row

            white_pct = 100.0 * white_count / total if total > 0 else 100.0

            return {
                'width': width,
                'height': height,
                'total_pixels': total,
                'non_white_count': non_white_count,
                'white_pct': round(white_pct, 1),
                'unique_colors': len(color_set) if len(color_set) < 1000 else '1000+',
                'avg_rgb': (r_sum // total, g_sum // total, b_sum // total) if total else (0, 0, 0),
                'is_blank': white_pct > 99.0,
                'is_suspicious': white_pct > 90.0 and non_white_count < 500,
            }
    except Exception as e:
        return {'error': str(e)}


def compare_pngs(path_a, path_b):
    """Compare two PNGs by reading raw pixel data and computing difference.

    Returns dict with: bytes_differ, diff_pct, identical
    """
    try:
        with open(path_a, 'rb') as f:
            data_a = f.read()
        with open(path_b, 'rb') as f:
            data_b = f.read()
        if data_a == data_b:
            return {'identical': True, 'bytes_differ': 0, 'diff_pct': 0.0}

        total = max(len(data_a), len(data_b))
        diff = sum(1 for a, b in zip(data_a, data_b) if a != b)
        diff += abs(len(data_a) - len(data_b))
        return {
            'identical': False,
            'bytes_differ': diff,
            'diff_pct': round(100.0 * diff / total, 2) if total else 0.0,
        }
    except Exception as e:
        return {'error': str(e)}


# ── Rendering ──────────────────────────────────────────────────────

def render_demo(rc_path, output_dir, times=None):
    """Render an .rc file at specified times, returning results.

    Returns list of dicts with: time, png_path, status, error, analysis
    """
    from rplayer.reader import RcReader
    from rplayer.renderer import RcRenderer
    from rplayer.runtime import RuntimeState

    if times is None:
        times = [0.0]

    name = os.path.splitext(os.path.basename(rc_path))[0]
    results = []

    try:
        with open(rc_path, 'rb') as f:
            data = f.read()
        doc = RcReader(data).parse()
    except Exception as e:
        for t in times:
            results.append({
                'time': t, 'png_path': None,
                'status': 'PARSE_ERROR', 'error': str(e),
            })
        return results, False

    try:
        runtime = RuntimeState(doc)
        renderer = RcRenderer(doc, scale=1.0, runtime=runtime)
        has_expressions = bool(runtime._float_exprs)
    except Exception as e:
        for t in times:
            results.append({
                'time': t, 'png_path': None,
                'status': 'RUNTIME_ERROR', 'error': str(e),
            })
        return results, False

    for t in times:
        suffix = f'_t{t:.3f}s' if len(times) > 1 else ''
        png_path = os.path.join(output_dir, f'{name}{suffix}.png')

        try:
            # Reset and step to time
            runtime.animation_time = 0.0
            runtime.frame_count = 0
            runtime.wall_time = 0.0
            runtime._reset_expressions()
            runtime.step(max(t, 0.001))

            image = renderer.render()
            image.save(png_path)

            results.append({
                'time': t, 'png_path': png_path,
                'status': 'OK', 'error': None,
            })
        except Exception as e:
            results.append({
                'time': t, 'png_path': None,
                'status': 'RENDER_ERROR', 'error': str(e),
            })

    return results, has_expressions


# ── Main harness ───────────────────────────────────────────────────

def run_verification(demo_dir, output_dir, filter_str=None, report_only=False):
    """Run the full verification pipeline."""
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(os.path.join(REPORT_DIR), exist_ok=True)

    # Enumerate demos
    rc_files = sorted([
        os.path.join(demo_dir, f)
        for f in os.listdir(demo_dir)
        if f.endswith('.rc')
    ])

    if filter_str:
        rc_files = [f for f in rc_files if filter_str.lower() in
                    os.path.basename(f).lower()]

    print(f'Found {len(rc_files)} .rc files to verify')
    print(f'Output: {output_dir}')
    print()

    all_results = {}
    counters = {
        'total': len(rc_files),
        'render_ok': 0, 'render_error': 0, 'parse_error': 0,
        'blank': 0, 'suspicious': 0, 'anim_frozen': 0,
        'visually_ok': 0, 'animated': 0,
    }

    for i, rc_path in enumerate(rc_files):
        name = os.path.splitext(os.path.basename(rc_path))[0]
        sys.stdout.write(f'\r  [{i + 1}/{len(rc_files)}] {name:50s}')
        sys.stdout.flush()

        if report_only:
            # Just analyze existing PNGs
            png_path = os.path.join(output_dir, f'{name}.png')
            if os.path.exists(png_path):
                analysis = read_png_info(png_path)
                classification = _classify(analysis, [])
                all_results[name] = {
                    'renders': [{'time': 0, 'png_path': png_path, 'status': 'OK'}],
                    'analysis': analysis,
                    'classification': classification,
                }
                if classification == 'OK':
                    counters['visually_ok'] += 1
                elif classification == 'BLANK':
                    counters['blank'] += 1
                elif classification == 'SUSPICIOUS':
                    counters['suspicious'] += 1
            continue

        # Determine times to render
        # First pass: always render t=0
        # If animated, also render t=0.5 and t=1.0
        renders, has_expressions = render_demo(rc_path, output_dir, times=[0.0])

        if has_expressions:
            counters['animated'] += 1
            extra_renders, _ = render_demo(rc_path, output_dir,
                                           times=[0.0, 0.5, 1.0])
            # Replace with multi-time renders for animated demos
            renders = extra_renders

        # Check results
        any_ok = any(r['status'] == 'OK' for r in renders)
        if not any_ok:
            if renders[0]['status'] == 'PARSE_ERROR':
                counters['parse_error'] += 1
            else:
                counters['render_error'] += 1
            all_results[name] = {
                'renders': renders,
                'classification': renders[0]['status'],
                'has_expressions': has_expressions,
            }
            continue

        counters['render_ok'] += 1

        # Analyze the t=0 render (or the only render)
        t0_render = next((r for r in renders if r['status'] == 'OK'), None)
        analysis = {}
        if t0_render and t0_render['png_path']:
            analysis = read_png_info(t0_render['png_path'])

        # Check animation frame differences
        frame_diffs = []
        if has_expressions and len(renders) > 1:
            ok_renders = [r for r in renders if r['status'] == 'OK' and r['png_path']]
            for j in range(1, len(ok_renders)):
                diff = compare_pngs(ok_renders[0]['png_path'],
                                    ok_renders[j]['png_path'])
                frame_diffs.append(diff)

        classification = _classify(analysis, frame_diffs)

        if classification == 'OK':
            counters['visually_ok'] += 1
        elif classification == 'BLANK':
            counters['blank'] += 1
        elif classification == 'SUSPICIOUS':
            counters['suspicious'] += 1
        elif classification == 'ANIM_FROZEN':
            counters['anim_frozen'] += 1

        all_results[name] = {
            'renders': [{k: v for k, v in r.items()} for r in renders],
            'analysis': analysis,
            'frame_diffs': frame_diffs,
            'classification': classification,
            'has_expressions': has_expressions,
        }

    print('\n')

    # Generate report
    _print_report(all_results, counters)
    _save_reports(all_results, counters)

    return all_results, counters


def _classify(analysis, frame_diffs):
    """Classify a demo's rendering quality."""
    if not analysis or 'error' in analysis:
        return 'ERROR'

    if analysis.get('is_blank', False):
        return 'BLANK'

    if analysis.get('is_suspicious', False):
        return 'SUSPICIOUS'

    # Check for frozen animation
    if frame_diffs:
        all_identical = all(d.get('identical', False) for d in frame_diffs)
        if all_identical:
            return 'ANIM_FROZEN'

    return 'OK'


def _print_report(results, counters):
    """Print a human-readable report to stdout."""
    print('=' * 70)
    print('  PYTHON PLAYER VERIFICATION REPORT')
    print('=' * 70)
    print()
    print(f'  Total demos:            {counters["total"]}')
    print(f'  Animated demos:         {counters["animated"]}')
    print(f'  Render succeeded:       {counters["render_ok"]}')
    print(f'  Parse errors:           {counters["parse_error"]}')
    print(f'  Render errors:          {counters["render_error"]}')
    print()
    print(f'  Visually OK:            {counters["visually_ok"]}')
    print(f'  BLANK (>99% white):     {counters["blank"]}')
    print(f'  SUSPICIOUS:             {counters["suspicious"]}')
    print(f'  ANIM FROZEN:            {counters["anim_frozen"]}')
    print()

    # List failures by category
    blanks = [n for n, r in results.items() if r.get('classification') == 'BLANK']
    suspicious = [n for n, r in results.items()
                  if r.get('classification') == 'SUSPICIOUS']
    frozen = [n for n, r in results.items()
              if r.get('classification') == 'ANIM_FROZEN']
    errors = [n for n, r in results.items()
              if r.get('classification') in ('PARSE_ERROR', 'RENDER_ERROR', 'RUNTIME_ERROR', 'ERROR')]

    if blanks:
        print(f'--- BLANK renders ({len(blanks)}) ---')
        for n in sorted(blanks):
            a = results[n].get('analysis', {})
            nw = a.get('non_white_count', '?')
            print(f'  {n:50s}  non_white={nw}')
        print()

    if suspicious:
        print(f'--- SUSPICIOUS renders ({len(suspicious)}) ---')
        for n in sorted(suspicious):
            a = results[n].get('analysis', {})
            wp = a.get('white_pct', '?')
            nw = a.get('non_white_count', '?')
            print(f'  {n:50s}  white={wp}%  non_white={nw}')
        print()

    if frozen:
        print(f'--- ANIMATED but FROZEN ({len(frozen)}) ---')
        for n in sorted(frozen):
            print(f'  {n}')
        print()

    if errors:
        print(f'--- ERRORS ({len(errors)}) ---')
        for n in sorted(errors):
            r = results[n]
            err = ''
            if r.get('renders'):
                err = r['renders'][0].get('error', '')
            print(f'  {n:50s}  {err[:60]}')
        print()


def _save_reports(results, counters):
    """Save reports to files."""
    # JSON report
    json_path = os.path.join(REPORT_DIR, 'report.json')
    # Make JSON-serializable
    clean = {}
    for name, data in results.items():
        clean[name] = {
            'classification': data.get('classification', 'UNKNOWN'),
            'has_expressions': data.get('has_expressions', False),
        }
        if 'analysis' in data:
            a = data['analysis']
            clean[name]['analysis'] = {
                'width': a.get('width'),
                'height': a.get('height'),
                'non_white_count': a.get('non_white_count'),
                'white_pct': a.get('white_pct'),
                'unique_colors': a.get('unique_colors'),
                'is_blank': a.get('is_blank'),
            }
        if 'frame_diffs' in data:
            clean[name]['frame_diffs'] = data['frame_diffs']

    report = {'counters': counters, 'results': clean}
    with open(json_path, 'w') as f:
        json.dump(report, f, indent=2)

    # Text report
    txt_path = os.path.join(REPORT_DIR, 'report.txt')
    with open(txt_path, 'w') as f:
        f.write('PYTHON PLAYER VERIFICATION REPORT\n')
        f.write(f'Generated: {time.strftime("%Y-%m-%d %H:%M:%S")}\n')
        f.write(f'Total: {counters["total"]}, OK: {counters["visually_ok"]}, '
                f'Blank: {counters["blank"]}, Suspicious: {counters["suspicious"]}, '
                f'Frozen: {counters["anim_frozen"]}, '
                f'Errors: {counters["parse_error"] + counters["render_error"]}\n\n')

        for name in sorted(results.keys()):
            r = results[name]
            cls = r.get('classification', '?')
            a = r.get('analysis', {})
            line = f'{cls:15s} {name}'
            if a.get('non_white_count') is not None:
                line += f'  nw={a["non_white_count"]}  white={a.get("white_pct")}%'
            f.write(line + '\n')

    print(f'Reports saved to:')
    print(f'  {txt_path}')
    print(f'  {json_path}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Verify rplayer rendering')
    parser.add_argument('--report-only', action='store_true',
                        help='Only analyze existing PNGs, do not re-render')
    parser.add_argument('--filter', type=str, default=None,
                        help='Only test demos matching this substring')
    parser.add_argument('--demo-dir', type=str, default=DEMO_DIR,
                        help='Directory containing .rc files')
    parser.add_argument('--output-dir', type=str, default=OUTPUT_DIR,
                        help='Directory for rendered PNGs')
    args = parser.parse_args()

    run_verification(args.demo_dir, args.output_dir,
                     filter_str=args.filter, report_only=args.report_only)

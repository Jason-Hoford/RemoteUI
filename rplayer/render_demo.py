"""CLI tool to render .rc files to PNG for validation.

Usage:
    python -m rplayer.render_demo demos/output/c_box.rc
    python -m rplayer.render_demo demos/output/c_box.rc -o rendered/
    python -m rplayer.render_demo demos/output/*.rc -o rendered/

The renderer supports a subset of operations. Files with unsupported
opcodes will report a parse error. Files that parse but use dynamic
expressions will render with static defaults (no expression evaluation).
"""

import sys
import os
import glob
import argparse

# Add parent directory to path so rplayer can be imported
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from rplayer.reader import RcReader
from rplayer.renderer import RcRenderer


def render_file(rc_path: str, output_dir: str, scale: float = 1.0) -> dict:
    """Render a single .rc file to PNG. Returns status dict."""
    basename = os.path.splitext(os.path.basename(rc_path))[0]
    png_path = os.path.join(output_dir, f"{basename}.png")

    try:
        with open(rc_path, 'rb') as f:
            data = f.read()

        doc = RcReader(data).parse()
        renderer = RcRenderer(doc, scale=scale)
        size = renderer.save_png(png_path)

        return {'status': 'ok', 'path': png_path, 'size': size,
                'doc_size': f"{doc.width}x{doc.height}",
                'ops': len(doc.operations)}

    except Exception as e:
        return {'status': 'error', 'error': str(e)}


def main():
    parser = argparse.ArgumentParser(
        description='Render RemoteCompose .rc files to PNG')
    parser.add_argument('files', nargs='+',
                        help='.rc files or glob patterns')
    parser.add_argument('-o', '--output', default='rplayer_output',
                        help='Output directory (default: rplayer_output)')
    parser.add_argument('-s', '--scale', type=float, default=1.0,
                        help='Scale factor (default: 1.0)')
    args = parser.parse_args()

    # Expand glob patterns
    rc_files = []
    for pattern in args.files:
        expanded = glob.glob(pattern)
        if expanded:
            rc_files.extend(expanded)
        else:
            rc_files.append(pattern)

    os.makedirs(args.output, exist_ok=True)

    ok_count = 0
    err_count = 0

    for path in sorted(rc_files):
        name = os.path.basename(path)
        result = render_file(path, args.output, args.scale)

        if result['status'] == 'ok':
            print(f"  [OK] {name}: {result['doc_size']}, "
                  f"{result['ops']} ops -> {result['path']} "
                  f"({result['size']} bytes)")
            ok_count += 1
        else:
            print(f"  [ERR] {name}: {result['error']}")
            err_count += 1

    print(f"\nResults: {ok_count} rendered, {err_count} errors "
          f"out of {ok_count + err_count}")
    return 0 if err_count == 0 else 1


if __name__ == '__main__':
    sys.exit(main())

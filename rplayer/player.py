"""Playback modes for animated RemoteCompose rendering.

Provides two modes:
1. Offscreen frame sequence — render PNG frames at specified times
2. Live preview window — real-time playback using glfw + Skia GL

Usage:
    # Offscreen frames
    from rplayer.player import render_frames
    render_frames('demo.rc', times=[0, 0.5, 1.0, 2.0], output_dir='frames/')

    # Live preview
    from rplayer.player import live_preview
    live_preview('demo.rc', duration=5.0)
"""

import os
import sys
import time as _time

from .reader import RcReader
from .renderer import RcRenderer
from .runtime import RuntimeState


def load_rc(path: str):
    """Load and parse an .rc file, returning (doc, runtime)."""
    with open(path, 'rb') as f:
        data = f.read()
    doc = RcReader(data).parse()
    runtime = RuntimeState(doc)
    return doc, runtime


def render_frames(
    rc_path: str,
    times: list = None,
    fps: float = 30.0,
    duration: float = 3.0,
    output_dir: str = 'rplayer_frames',
    scale: float = 1.0,
    prefix: str = None,
) -> list:
    """Render an .rc file at multiple time points, saving PNG frames.

    Args:
        rc_path: Path to .rc file.
        times: Explicit list of times (seconds) to render. If None,
               renders at fps intervals for duration seconds.
        fps: Frames per second (used when times is None).
        duration: Total duration in seconds (used when times is None).
        output_dir: Directory for output PNGs.
        scale: Render scale factor.
        prefix: Filename prefix (default: basename of rc_path).

    Returns:
        List of (time, png_path) tuples.
    """
    doc, runtime = load_rc(rc_path)

    if times is None:
        times = [i / fps for i in range(int(duration * fps) + 1)]

    if prefix is None:
        prefix = os.path.splitext(os.path.basename(rc_path))[0]

    os.makedirs(output_dir, exist_ok=True)
    renderer = RcRenderer(doc, scale=scale, runtime=runtime)

    results = []
    for i, t in enumerate(times):
        # Step runtime to this time
        runtime.step_to(t)
        image = renderer.render()

        frame_name = f'{prefix}_f{i:04d}_t{t:.3f}s.png'
        frame_path = os.path.join(output_dir, frame_name)
        image.save(frame_path)
        results.append((t, frame_path))
        print(f'  [{i+1}/{len(times)}] t={t:.3f}s -> {frame_name}')

    print(f'\n{len(results)} frames saved to {output_dir}/')
    return results


def render_time_samples(
    rc_path: str,
    sample_times: list,
    output_dir: str = 'rplayer_frames',
    scale: float = 1.0,
) -> list:
    """Render at specific time samples (convenience for testing).

    Args:
        rc_path: Path to .rc file.
        sample_times: List of float times in seconds.
        output_dir: Output directory.
        scale: Scale factor.

    Returns:
        List of (time, png_path) tuples.
    """
    return render_frames(rc_path, times=sample_times, output_dir=output_dir,
                         scale=scale)


def live_preview(
    rc_path: str,
    duration: float = 10.0,
    fps: float = 60.0,
    scale: float = 1.0,
    speed: float = 1.0,
    output_dir: str = 'rplayer_frames',
):
    """Live animated preview using glfw + Skia.

    Opens a window showing the .rc file animating in real time.
    Close the window or press Escape to exit.

    Requires: pip install glfw
    If glfw is not installed, falls back to offscreen frame rendering.

    Args:
        rc_path: Path to .rc file.
        duration: How long to play (0 = until closed).
        fps: Target frame rate.
        scale: Render scale.
        speed: Playback speed multiplier.
        output_dir: Output directory for fallback frame rendering.
    """
    try:
        import glfw
    except ImportError:
        print('Live preview requires glfw: pip install glfw')
        print('Falling back to offscreen frame render...')
        render_frames(rc_path, fps=min(fps, 10), duration=min(duration, 3),
                      scale=scale, output_dir=output_dir)
        return

    import skia

    doc, runtime = load_rc(rc_path)
    w = max(1, int(doc.width * scale))
    h = max(1, int(doc.height * scale))

    if not glfw.init():
        print('Failed to initialize GLFW')
        return

    glfw.window_hint(glfw.VISIBLE, True)
    glfw.window_hint(glfw.RESIZABLE, False)
    title = f'rplayer: {os.path.basename(rc_path)}'
    window = glfw.create_window(w, h, title, None, None)
    if not window:
        glfw.terminate()
        print('Failed to create GLFW window')
        return

    glfw.make_context_current(window)
    glfw.swap_interval(1)  # vsync

    # Create Skia GL context
    gl_context = skia.GrDirectContext.MakeGL()
    if not gl_context:
        glfw.destroy_window(window)
        glfw.terminate()
        print('Failed to create Skia GL context')
        return

    fb_width, fb_height = glfw.get_framebuffer_size(window)
    backend_render_target = skia.GrBackendRenderTarget(
        fb_width, fb_height, 0, 0,
        skia.GrGLFramebufferInfo(0, 0x8058)  # GL_RGBA8
    )
    surface = skia.Surface.MakeFromBackendRenderTarget(
        gl_context, backend_render_target,
        skia.kBottomLeft_GrSurfaceOrigin,
        skia.kRGBA_8888_ColorType,
        skia.ColorSpace.MakeSRGB()
    )
    if not surface:
        gl_context.abandonContext()
        glfw.destroy_window(window)
        glfw.terminate()
        print('Failed to create Skia surface')
        return

    renderer = RcRenderer(doc, scale=scale, runtime=runtime)

    start_time = _time.monotonic()
    frame_dt = 1.0 / fps
    frame_count = 0

    def key_callback(win, key, scancode, action, mods):
        if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
            glfw.set_window_should_close(win, True)

    glfw.set_key_callback(window, key_callback)

    try:
        while not glfw.window_should_close(window):
            now = _time.monotonic()
            elapsed = (now - start_time) * speed

            if duration > 0 and elapsed > duration:
                break

            # Step runtime
            runtime.step(frame_dt * speed)

            # Render to surface
            canvas = surface.getCanvas()
            canvas.clear(skia.ColorWHITE)
            if scale != 1.0:
                canvas.save()
                canvas.scale(scale, scale)

            from .renderer import _RenderContext
            paint = skia.Paint(AntiAlias=True)
            paint.setColor(skia.ColorBLACK)
            ctx = _RenderContext(canvas, paint, doc, runtime=runtime)
            ctx.execute(doc.operations)

            if scale != 1.0:
                canvas.restore()

            surface.flushAndSubmit()
            glfw.swap_buffers(window)
            glfw.poll_events()

            frame_count += 1

            # Frame timing
            frame_end = _time.monotonic()
            sleep_time = frame_dt - (frame_end - now)
            if sleep_time > 0:
                _time.sleep(sleep_time)

    except KeyboardInterrupt:
        pass
    finally:
        elapsed = _time.monotonic() - start_time
        avg_fps = frame_count / elapsed if elapsed > 0 else 0
        print(f'\nPlayed {frame_count} frames in {elapsed:.1f}s '
              f'(avg {avg_fps:.1f} fps)')
        gl_context.abandonContext()
        glfw.destroy_window(window)
        glfw.terminate()


def main():
    """CLI entry point for player."""
    import argparse

    parser = argparse.ArgumentParser(
        prog='python -m rplayer.player',
        description='Animated renderer for RemoteCompose .rc files.\n'
                    'Evaluates expressions and renders PNG frames at specified times.',
        epilog='Examples:\n'
               '  python -m rplayer.player demo.rc\n'
               '      Render 3 seconds at 30fps -> rplayer_frames/\n\n'
               '  python -m rplayer.player demo.rc -d 5 -f 10\n'
               '      Render 5 seconds at 10fps -> rplayer_frames/\n\n'
               '  python -m rplayer.player demo.rc -t 0 1.5 3.0\n'
               '      Render only at t=0s, t=1.5s, t=3.0s\n\n'
               '  python -m rplayer.player demo.rc -m live\n'
               '      Open a live preview window (requires: pip install glfw)\n',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument('file', help='path to .rc file')
    parser.add_argument('-m', '--mode', choices=['frames', 'live'],
                        default='frames',
                        help='playback mode (default: frames)')
    parser.add_argument('-d', '--duration', type=float, default=3.0,
                        help='animation duration in seconds (default: 3.0)')
    parser.add_argument('-f', '--fps', type=float, default=30.0,
                        help='frames per second (default: 30)')
    parser.add_argument('-s', '--scale', type=float, default=1.0,
                        help='render scale factor (default: 1.0)')
    parser.add_argument('-o', '--output', default='rplayer_frames',
                        help='output directory (default: rplayer_frames)')
    parser.add_argument('--speed', type=float, default=1.0,
                        help='playback speed multiplier (default: 1.0)')
    parser.add_argument('-t', '--times', nargs='+', type=float,
                        help='render at specific times in seconds '
                             '(overrides -d and -f)')
    args = parser.parse_args()

    if args.mode == 'live':
        live_preview(args.file, duration=args.duration, fps=args.fps,
                     scale=args.scale, speed=args.speed,
                     output_dir=args.output)
    else:
        render_frames(args.file, times=args.times, fps=args.fps,
                      duration=args.duration, output_dir=args.output,
                      scale=args.scale)


if __name__ == '__main__':
    main()

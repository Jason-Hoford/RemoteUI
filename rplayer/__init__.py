"""rplayer — Python player/renderer for RemoteCompose .rc binary files.

Uses skia-python for rendering, matching Android's Skia-based pipeline.
Supports expression evaluation, animation, and animated playback.

Entry points:
    python -m rplayer.viewer       — desktop GUI viewer (recommended)
    python -m rplayer.player       — animated CLI renderer
    python -m rplayer.render_demo  — static batch render (no expressions)
    python -m rplayer              — shortcut for animated CLI player
"""

from .reader import RcReader, RcDocument
from .renderer import RcRenderer
from .runtime import RuntimeState
from .expressions import FloatExpressionEvaluator
from .easing import FloatAnimation, CubicEasing


def __getattr__(name):
    """Lazy import for player functions to avoid RuntimeWarning
    when running python -m rplayer.player directly."""
    if name in ('render_frames', 'live_preview', 'load_rc'):
        from . import player
        return getattr(player, name)
    raise AttributeError(f"module 'rplayer' has no attribute {name!r}")

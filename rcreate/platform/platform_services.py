"""Platform services abstraction — equivalent to Java's RcPlatformServices."""


class PlatformServices:
    """Abstract platform services for image/path utilities.

    The Python port uses a minimal implementation since it doesn't
    need Android-specific services.
    """

    def load_image(self, path: str) -> bytes:
        with open(path, 'rb') as f:
            return f.read()

    def get_image_dimensions(self, data: bytes) -> tuple[int, int]:
        """Return (width, height) from image data.

        Uses pure-Python PNG header parsing. Falls back to Pillow for
        non-PNG formats.
        """
        dims = _parse_png_dimensions(data)
        if dims is not None:
            return dims
        try:
            from PIL import Image
            import io
            img = Image.open(io.BytesIO(data))
            return img.size
        except ImportError:
            raise RuntimeError(
                "Image is not a PNG and Pillow is not installed. "
                "Install Pillow for non-PNG formats: pip install Pillow"
            )

    def encode_path(self, svg_path: str) -> list[float]:
        """Parse SVG path string into float array. Basic implementation."""
        return _parse_svg_path(svg_path)


def _parse_png_dimensions(data: bytes):
    """Extract (width, height) from a PNG file header. Returns None if not PNG.

    PNG layout: 8-byte signature, then IHDR chunk with width at bytes 16-19
    and height at bytes 20-23, both as 4-byte big-endian unsigned ints.
    """
    import struct
    if len(data) < 24 or data[:8] != b'\x89PNG\r\n\x1a\n':
        return None
    width, height = struct.unpack('>II', data[16:24])
    return (width, height)


def _parse_svg_path(svg_path: str) -> list[float]:
    """Parse a subset of SVG path data into float coordinates."""
    import re
    floats = []
    # Extract all numbers from the path string
    tokens = re.findall(r'[MmLlHhVvCcSsQqTtAaZz]|[-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?', svg_path)
    cmd_map = {
        'M': 0.0, 'm': 1.0,
        'L': 2.0, 'l': 3.0,
        'H': 4.0, 'h': 5.0,
        'V': 6.0, 'v': 7.0,
        'C': 8.0, 'c': 9.0,
        'S': 10.0, 's': 11.0,
        'Q': 12.0, 'q': 13.0,
        'T': 14.0, 't': 15.0,
        'A': 16.0, 'a': 17.0,
        'Z': 18.0, 'z': 18.0,
    }
    for token in tokens:
        if token in cmd_map:
            floats.append(cmd_map[token])
        else:
            floats.append(float(token))
    return floats

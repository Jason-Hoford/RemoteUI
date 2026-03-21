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
        """Return (width, height) from image data. Requires Pillow."""
        try:
            from PIL import Image
            import io
            img = Image.open(io.BytesIO(data))
            return img.size
        except ImportError:
            raise RuntimeError("Pillow is required for image operations: pip install Pillow")

    def encode_path(self, svg_path: str) -> list[float]:
        """Parse SVG path string into float array. Basic implementation."""
        return _parse_svg_path(svg_path)


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

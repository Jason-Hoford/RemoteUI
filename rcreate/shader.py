"""RemoteComposeShader — shader creation and uniform binding.

Matches Java's RemoteComposeShader.java.
"""

from __future__ import annotations
from typing import TYPE_CHECKING

from . import operations as Ops

if TYPE_CHECKING:
    from .writer import RemoteComposeWriter


class RemoteComposeShader:

    def __init__(self, shader: str, writer: 'RemoteComposeWriter'):
        self._shader = shader
        self._writer = writer
        self._shader_id = 0
        self._shader_text_id = writer.add_text(shader)
        self._uniform_float_map: dict[str, list[float]] | None = None
        self._uniform_int_map: dict[str, list[int]] | None = None
        self._uniform_bitmap_map: dict[str, int] | None = None

    @property
    def shader(self) -> str:
        return self._shader

    @property
    def shader_id(self) -> int:
        return self._shader_id

    @shader_id.setter
    def shader_id(self, value: int):
        self._shader_id = value

    @property
    def shader_text_id(self) -> int:
        return self._shader_text_id

    # ── Int uniforms ──

    def set_int_uniform(self, name: str, *values: int) -> 'RemoteComposeShader':
        if self._uniform_int_map is None:
            self._uniform_int_map = {}
        self._uniform_int_map[name] = list(values)
        return self

    # ── Float uniforms ──

    def set_float_uniform(self, name: str, *values: float) -> 'RemoteComposeShader':
        if self._uniform_float_map is None:
            self._uniform_float_map = {}
        self._uniform_float_map[name] = list(values)
        return self

    # ── Bitmap uniform ──

    def set_bitmap_uniform(self, name: str, bitmap_id: int) -> 'RemoteComposeShader':
        if self._uniform_bitmap_map is None:
            self._uniform_bitmap_map = {}
        self._uniform_bitmap_map[name] = bitmap_id
        return self

    # ── Commit ──

    def commit(self) -> int:
        state = self._writer._state
        self._shader_id = state.data_get_id(id(self))
        if self._shader_id == -1:
            self._shader_id = state.cache_data(id(self))

        buf = self._writer._buffer._buffer
        buf.write_byte(Ops.DATA_SHADER)
        buf.write_int(self._shader_id)
        buf.write_int(self._shader_text_id)

        float_size = len(self._uniform_float_map) if self._uniform_float_map else 0
        int_size = len(self._uniform_int_map) if self._uniform_int_map else 0
        bitmap_size = len(self._uniform_bitmap_map) if self._uniform_bitmap_map else 0
        sizes = float_size | (int_size << 8) | (bitmap_size << 16)
        buf.write_int(sizes)

        if float_size > 0:
            for name, values in self._uniform_float_map.items():
                buf.write_utf8(name)
                buf.write_int(len(values))
                for v in values:
                    buf.write_float(v)

        if int_size > 0:
            for name, values in self._uniform_int_map.items():
                buf.write_utf8(name)
                buf.write_int(len(values))
                for v in values:
                    buf.write_int(v)

        if bitmap_size > 0:
            for name, bitmap_id in self._uniform_bitmap_map.items():
                buf.write_utf8(name)
                buf.write_int(bitmap_id)

        return self._shader_id

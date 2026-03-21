"""ID allocation and data caching — equivalent to Java's RemoteComposeState."""

import struct


def _cache_key(obj):
    if isinstance(obj, (list, tuple)):
        return tuple(obj)
    if isinstance(obj, bytes):
        return obj
    return obj


class RemoteUIState:
    START_ID = 42
    BITMAP_TEXTURE_ID_OFFSET = 2000
    # Separate ID namespaces matching Java's NanMap
    # TYPE_VARIABLE = 1, TYPE_ARRAY = 2
    START_VAR = (1 << 20) + START_ID    # 0x10002A
    START_ARRAY = (2 << 20) + START_ID  # 0x20002A

    def __init__(self):
        self._next_id = self.START_ID
        self._id_maps = [self.START_ID, self.START_VAR, self.START_ARRAY]
        self._data_cache: dict = {}
        self._float_cache: dict[int, int] = {}
        self._integer_cache: dict[int, int] = {}
        self._next_bitmap_id = self.BITMAP_TEXTURE_ID_OFFSET

    def reset(self):
        self._next_id = self.START_ID
        self._id_maps = [self.START_ID, self.START_VAR, self.START_ARRAY]
        self._data_cache.clear()
        self._float_cache.clear()
        self._integer_cache.clear()

    def create_next_available_id(self, type_hint: int = 0) -> int:
        if type_hint == 0:
            cid = self._next_id
            self._next_id += 1
            return cid
        cid = self._id_maps[type_hint]
        self._id_maps[type_hint] += 1
        return cid

    # ── Text / data caching ──

    def data_get_id(self, obj) -> int:
        key = _cache_key(obj)
        return self._data_cache.get(key, -1)

    def cache_data(self, obj, type_hint: int = 0) -> int:
        key = _cache_key(obj)
        existing = self._data_cache.get(key)
        if existing is not None:
            return existing
        cid = self.create_next_available_id(type_hint)
        self._data_cache[key] = cid
        return cid

    def cache_data_with_id(self, cid: int, obj):
        key = _cache_key(obj)
        self._data_cache[key] = cid

    # ── Float caching ──

    def cache_float(self, value: float) -> int:
        # Java's cacheFloat() always allocates a new ID (no deduplication).
        # It stores the value in mFloatMap keyed by id for later lookup,
        # but does NOT reuse existing IDs for the same float value.
        cid = self.create_next_available_id()
        bits = struct.unpack('<I', struct.pack('<f', value))[0]
        self._float_cache[bits] = cid
        return cid

    def update_float(self, cid: int, value: float):
        bits = struct.unpack('<I', struct.pack('<f', value))[0]
        self._float_cache[bits] = cid

    # ── Integer caching ──

    def cache_integer(self, value: int) -> int:
        existing = self._integer_cache.get(value)
        if existing is not None:
            return existing
        cid = self.create_next_available_id()
        self._integer_cache[value] = cid
        return cid

    def update_integer(self, cid: int, value: int):
        self._integer_cache[value] = cid

    def update_object(self, cid: int, obj):
        key = _cache_key(obj)
        self._data_cache[key] = cid

    def create_next_bitmap_id(self) -> int:
        cid = self._next_bitmap_id
        self._next_bitmap_id += 1
        return cid

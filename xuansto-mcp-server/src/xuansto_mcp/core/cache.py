from __future__ import annotations

import threading
from collections import OrderedDict
from typing import Any


class LRUCache:
    def __init__(self, maxsize: int = 128) -> None:
        self._maxsize = max(1, maxsize)
        self._cache: OrderedDict[str, Any] = OrderedDict()
        self._lock = threading.Lock()

    def get(self, key: str) -> Any | None:
        with self._lock:
            if key not in self._cache:
                return None
            self._cache.move_to_end(key)
            return self._cache[key]

    def put(self, key: str, value: Any) -> None:
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
                self._cache[key] = value
            else:
                self._cache[key] = value
                if len(self._cache) > self._maxsize:
                    self._cache.popitem(last=False)

    def delete(self, key: str) -> bool:
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def contains(self, key: str) -> bool:
        with self._lock:
            return key in self._cache

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()

    def size(self) -> int:
        with self._lock:
            return len(self._cache)

    def keys(self) -> list[str]:
        with self._lock:
            return list(self._cache.keys())

    def items(self) -> list[tuple[str, Any]]:
        with self._lock:
            return list(self._cache.items())

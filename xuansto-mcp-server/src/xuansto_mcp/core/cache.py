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

    def __getitem__(self, key: str) -> Any:
        with self._lock:
            if key not in self._cache:
                raise KeyError(key)
            self._cache.move_to_end(key)
            return self._cache[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.put(key, value)

    def __delitem__(self, key: str) -> None:
        if not self.delete(key):
            raise KeyError(key)

    def __len__(self) -> int:
        return self.size()

    def __contains__(self, key: str) -> bool:
        return self.contains(key)

    def __iter__(self):
        with self._lock:
            return iter(list(self._cache.keys()))

from __future__ import annotations

import threading

import pytest

from xuansto_mcp.core.cache import LRUCache


def test_get_missing_key():
    cache = LRUCache(maxsize=10)
    assert cache.get("nonexistent") is None


def test_put_and_get():
    cache = LRUCache(maxsize=10)
    cache.put("key1", "value1")
    assert cache.get("key1") == "value1"


def test_put_overwrites():
    cache = LRUCache(maxsize=10)
    cache.put("key1", "value1")
    cache.put("key1", "value2")
    assert cache.get("key1") == "value2"


def test_eviction_when_maxsize_exceeded():
    cache = LRUCache(maxsize=3)
    cache.put("a", 1)
    cache.put("b", 2)
    cache.put("c", 3)
    cache.put("d", 4)
    assert cache.get("a") is None
    assert cache.get("b") == 2
    assert cache.get("c") == 3
    assert cache.get("d") == 4


def test_lru_eviction_order():
    cache = LRUCache(maxsize=3)
    cache.put("a", 1)
    cache.put("b", 2)
    cache.put("c", 3)
    cache.get("a")
    cache.put("d", 4)
    assert cache.get("a") == 1
    assert cache.get("b") is None
    assert cache.get("c") == 3
    assert cache.get("d") == 4


def test_maxsize_one():
    cache = LRUCache(maxsize=1)
    cache.put("a", 1)
    cache.put("b", 2)
    assert cache.get("a") is None
    assert cache.get("b") == 2


def test_delete_existing():
    cache = LRUCache(maxsize=10)
    cache.put("key1", "value1")
    result = cache.delete("key1")
    assert result is True
    assert cache.get("key1") is None


def test_delete_nonexistent():
    cache = LRUCache(maxsize=10)
    result = cache.delete("nonexistent")
    assert result is False


def test_clear():
    cache = LRUCache(maxsize=10)
    cache.put("a", 1)
    cache.put("b", 2)
    cache.clear()
    assert cache.get("a") is None
    assert cache.get("b") is None
    assert cache.size() == 0


def test_contains():
    cache = LRUCache(maxsize=10)
    cache.put("key1", "value1")
    assert cache.contains("key1") is True
    assert cache.contains("nonexistent") is False


def test_size():
    cache = LRUCache(maxsize=10)
    assert cache.size() == 0
    cache.put("a", 1)
    assert cache.size() == 1
    cache.put("b", 2)
    assert cache.size() == 2
    cache.delete("a")
    assert cache.size() == 1


def test_keys():
    cache = LRUCache(maxsize=10)
    cache.put("a", 1)
    cache.put("b", 2)
    keys = cache.keys()
    assert set(keys) == {"a", "b"}


def test_items():
    cache = LRUCache(maxsize=10)
    cache.put("a", 1)
    cache.put("b", 2)
    items = cache.items()
    assert len(items) == 2
    assert ("a", 1) in items
    assert ("b", 2) in items


def test_thread_safety():
    cache = LRUCache(maxsize=100)
    errors = []

    def writer(start, count):
        try:
            for i in range(start, start + count):
                cache.put(f"key_{i}", i)
        except Exception as e:
            errors.append(e)

    def reader(start, count):
        try:
            for i in range(start, start + count):
                cache.get(f"key_{i}")
        except Exception as e:
            errors.append(e)

    threads = [
        threading.Thread(target=writer, args=(0, 50)),
        threading.Thread(target=writer, args=(50, 50)),
        threading.Thread(target=reader, args=(0, 50)),
        threading.Thread(target=reader, args=(50, 50)),
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=10)
    assert len(errors) == 0, f"Thread safety errors: {errors}"


def test_maxsize_minimum_one():
    cache = LRUCache(maxsize=0)
    assert cache._maxsize == 1


def test_negative_maxsize():
    cache = LRUCache(maxsize=-5)
    assert cache._maxsize == 1


def test_put_same_key_does_not_increase_size():
    cache = LRUCache(maxsize=3)
    cache.put("a", 1)
    cache.put("a", 2)
    cache.put("a", 3)
    assert cache.size() == 1

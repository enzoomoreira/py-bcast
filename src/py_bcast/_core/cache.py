"""Response caching layer for py_bcast.

Provides in-memory (default) and disk-persistent cache backends.
Cache is keyed on (endpoint, params) — session token is excluded so
the same market data is shared regardless of auth credentials.

Usage is via the ``@cached`` decorator on lower-level fetch helpers.
"""

from __future__ import annotations

import hashlib
import json
import threading
import time
from typing import Any

from .config import get_settings, _resolve_cache_dir
from .logging import get_logger

logger = get_logger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Memory backend
# ─────────────────────────────────────────────────────────────────────────────


class _MemoryCache:
    """Thread-safe in-memory cache with per-entry TTL."""

    def __init__(self) -> None:
        self._store: dict[str, tuple[float, Any]] = {}
        self._lock = threading.Lock()

    def get(self, key: str) -> Any | None:
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            expires, value = entry
            if time.time() > expires:
                del self._store[key]
                return None
            return value

    def set(self, key: str, value: Any, ttl: int) -> None:
        with self._lock:
            self._store[key] = (time.time() + ttl, value)

    def invalidate(self, prefix: str | None = None) -> int:
        """Remove entries. If prefix given, only matching keys. Returns count removed."""
        with self._lock:
            if prefix is None:
                count = len(self._store)
                self._store.clear()
                return count
            keys = [k for k in self._store if k.startswith(prefix)]
            for k in keys:
                del self._store[k]
            return len(keys)


# ─────────────────────────────────────────────────────────────────────────────
# Disk backend
# ─────────────────────────────────────────────────────────────────────────────


class _DiskCache:
    """Disk-persistent cache using diskcache."""

    def __init__(self) -> None:
        self._cache: Any = None

    def _ensure_open(self) -> Any:
        if self._cache is None:
            import diskcache
            cache_dir = _resolve_cache_dir()
            self._cache = diskcache.Cache(cache_dir)
            logger.debug("Disk cache opened at %s", cache_dir)
        return self._cache

    def get(self, key: str) -> Any | None:
        cache = self._ensure_open()
        return cache.get(key)

    def set(self, key: str, value: Any, ttl: int) -> None:
        cache = self._ensure_open()
        cache.set(key, value, expire=ttl)

    def invalidate(self, prefix: str | None = None) -> int:
        cache = self._ensure_open()
        if prefix is None:
            count = len(cache)
            cache.clear()
            return count
        # diskcache doesn't support prefix scan efficiently, iterate
        keys = [k for k in cache if isinstance(k, str) and k.startswith(prefix)]
        for k in keys:
            del cache[k]
        return len(keys)


# ─────────────────────────────────────────────────────────────────────────────
# Unified interface
# ─────────────────────────────────────────────────────────────────────────────

_memory_cache = _MemoryCache()
_disk_cache = _DiskCache()


def _get_backend():
    """Return the active cache backend based on settings."""
    settings = get_settings()
    if settings.cache_backend == "disk":
        return _disk_cache
    return _memory_cache


def make_cache_key(endpoint: str, params: dict[str, str]) -> str:
    """Build a deterministic cache key from endpoint and params.

    The session token (param "10039") is excluded from the key.
    """
    filtered = {k: v for k, v in sorted(params.items()) if k != "10039"}
    raw = f"{endpoint}|{json.dumps(filtered, separators=(',', ':'))}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def cache_get(endpoint: str, params: dict[str, str]) -> Any | None:
    """Attempt to retrieve a cached response."""
    settings = get_settings()
    if not settings.cache_enabled:
        return None
    key = make_cache_key(endpoint, params)
    result = _get_backend().get(key)
    if result is not None:
        logger.debug("Cache HIT: %s", endpoint)
    return result


def cache_set(endpoint: str, params: dict[str, str], value: Any, ttl: int | None = None) -> None:
    """Store a response in the cache."""
    settings = get_settings()
    if not settings.cache_enabled:
        return
    if ttl is None:
        ttl = settings.cache_ttl
    key = make_cache_key(endpoint, params)
    _get_backend().set(key, value, ttl)
    logger.debug("Cache SET: %s (ttl=%ds)", endpoint, ttl)


def invalidate(prefix: str | None = None) -> int:
    """Clear cache entries.

    Parameters
    ----------
    prefix : str | None
        If provided, only clear entries whose key starts with this prefix.
        If None, clear all entries.

    Returns
    -------
    int
        Number of entries removed.
    """
    count = _memory_cache.invalidate(prefix)
    count += _disk_cache.invalidate(prefix)
    logger.info("Cache invalidated: %d entries removed", count)
    return count

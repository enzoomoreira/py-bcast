"""Central configuration for py_bcast.

Provides a ``Settings`` dataclass and a ``configure()`` function to tune
library behavior (timeouts, retry, cache, rate limiting) without touching
internals.

Usage::

    from py_bcast import configure

    configure(timeout=15, cache_backend="disk", rate_limit_calls=5)
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Literal


@dataclass
class Settings:
    """Library-wide configuration.

    All values have sensible defaults. Override via ``configure()``.
    """

    # ── Network ──────────────────────────────────────────────────────────────
    base_url: str = "http://cp.ae.com.br:44780"
    user_agent: str = "bcsys32/7.0"
    platform: str = "4"
    timeout: int = 30

    # ── Retry ────────────────────────────────────────────────────────────────
    max_retries: int = 3
    retry_wait_min: float = 1.0
    retry_wait_max: float = 4.0

    # ── Cache ────────────────────────────────────────────────────────────────
    cache_enabled: bool = True
    cache_backend: Literal["memory", "disk"] = "memory"
    cache_dir: str | None = None  # None = auto (APPDATA/py_bcast/cache)
    cache_ttl: int = 300  # seconds — historical data
    cache_ttl_reference: int = 3600  # seconds — reference/static data
    cache_ttl_realtime: int = 5  # seconds — quotes
    cache_ttl_news: int = 60  # seconds — news articles

    # ── Rate Limiting ────────────────────────────────────────────────────────
    rate_limit_calls: int = 10  # max requests per period
    rate_limit_period: float = 1.0  # period in seconds

    # ── Terminal routing ─────────────────────────────────────────────────────
    # "auto"   — detecta automaticamente: Plus se disponivel, legacy caso contrario
    # "legacy" — sempre usa bcsys32.exe + ContentProxy
    # "plus"   — sempre usa Broadcast+.exe + svc.aebroadcast.com.br
    terminal: Literal["auto", "legacy", "plus"] = "auto"

    # ── Broadcast+ credentials (optional — for ECDH headless login) ──────────
    # Used when neither BROADCAST_PLUS_TOKEN env var nor Broadcast+.exe
    # memory scan yields a valid JWT.
    plus_login: str | None = None
    plus_password: str | None = field(default=None, repr=False)  # never printed


# Module-level singleton
_settings = Settings()


def get_settings() -> Settings:
    """Return the active global settings instance."""
    return _settings


def configure(**kwargs: object) -> None:
    """Update library settings.

    Only the provided keys are modified; unspecified keys retain their
    current values.

    Parameters
    ----------
    **kwargs
        Any attribute of ``Settings`` (e.g., ``timeout=10``,
        ``cache_backend="disk"``).

    Raises
    ------
    TypeError
        If an unknown setting key is passed.

    Example
    -------
    >>> from py_bcast import configure
    >>> configure(timeout=15, cache_enabled=False)
    """
    for key, value in kwargs.items():
        if not hasattr(_settings, key):
            raise TypeError(f"Unknown setting: {key!r}")
        setattr(_settings, key, value)
    if "terminal" in kwargs:
        # Reset auto-detection cache so next call re-probes availability
        try:
            from .routing import reset_terminal_cache  # noqa: PLC0415
        except ImportError:
            pass
        else:
            reset_terminal_cache()


def _resolve_cache_dir() -> str:
    """Return the effective cache directory path."""
    if _settings.cache_dir:
        return _settings.cache_dir
    base = os.environ.get("APPDATA") or os.path.expanduser("~")
    return os.path.join(base, "py_bcast", "cache")

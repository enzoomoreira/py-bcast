"""Terminal backend routing.

Resolves which backend (legacy ContentProxy or Broadcast+) should be used
for the current call, based on configure(terminal=...) and live availability.

Usage::

    from py_bcast._core.routing import get_active_terminal

    if get_active_terminal() == "plus":
        # use _plus/ functions
    else:
        # use legacy ContentProxy functions
"""

from __future__ import annotations

import os
from typing import Literal

from .config import get_settings
from .logging import get_logger

logger = get_logger(__name__)

# Auto-detection result cached for the process lifetime.
# Reset by reset_terminal_cache() whenever configure(terminal=...) is called.
_cached: str | None = None


def get_active_terminal() -> Literal["legacy", "plus"]:
    """Return the active terminal backend for the current process.

    Resolution order:
        1. ``configure(terminal="legacy"|"plus")`` — explicit override
        2. ``terminal="auto"`` (default):
           a. ``BROADCAST_PLUS_TOKEN`` env var set → "plus"
           b. ``Broadcast+.exe`` process detected → "plus"
           c. fallback → "legacy"

    The auto-detection result is cached after the first call. It is reset
    automatically when ``configure(terminal=...)`` is called.

    Returns:
        ``"plus"`` or ``"legacy"``.
    """
    global _cached

    settings = get_settings()
    if settings.terminal == "legacy":
        return "legacy"
    if settings.terminal == "plus":
        return "plus"

    # "auto" mode — check cache first
    if _cached is not None:
        return _cached  # type: ignore[return-value]

    _cached = _detect()
    logger.debug("Terminal auto-detected: %s", _cached)
    return _cached  # type: ignore[return-value]


def reset_terminal_cache() -> None:
    """Clear the auto-detection cache.

    Called automatically by ``configure(terminal=...)`` so the next call to
    ``get_active_terminal()`` re-probes availability.
    """
    global _cached
    _cached = None


def _detect() -> Literal["legacy", "plus"]:
    """Probe availability and return the preferred terminal."""
    # 1. Env var — zero cost
    if os.environ.get("BROADCAST_PLUS_TOKEN"):
        return "plus"

    # 2. Broadcast+.exe running — one tasklist call (~5 ms), done once per process
    try:
        from .memory import find_process_pid

        if find_process_pid("Broadcast+.exe") is not None:
            return "plus"
    except Exception:
        pass

    return "legacy"

"""Shared test fixtures and resource-aware skip logic.

Tests declare what they need with markers; this file detects which resources
are actually available on the host and skips accordingly. No fake tokens are
injected — if a test needs a backend, it must say so with a marker.

Markers:
    legacy_session  — needs a real BROADCAST_SESSION (env var or bcsys32.exe running)
    legacy_db       — needs aetp_17.dat on disk (i.e. bcsys32.exe has run here)
    plus            — needs Broadcast+ access (BROADCAST_PLUS_TOKEN or Broadcast+.exe running)
"""

import os
import sys
from pathlib import Path

import pytest

from py_bcast._core.constants import INSTRUMENT_DB_FILENAME, INSTRUMENT_DB_RELPATH


def _find_pid_safe(image_name: str) -> int | None:
    """Return PID of a process, or None on any failure (including non-Windows)."""
    if sys.platform != "win32":
        return None
    try:
        from py_bcast._core.memory import find_process_pid
    except ImportError:
        return None
    try:
        return find_process_pid(image_name)
    except Exception:
        return None


def _legacy_session_available() -> bool:
    """A usable legacy session exists: BROADCAST_SESSION in env OR bcsys32.exe running."""
    if os.environ.get("BROADCAST_SESSION", "").strip():
        return True
    return _find_pid_safe("bcsys32.exe") is not None


def _legacy_db_available() -> bool:
    """The local instrument database file is present."""
    appdata = os.environ.get("APPDATA", "")
    if not appdata:
        return False
    return (Path(appdata) / INSTRUMENT_DB_RELPATH / INSTRUMENT_DB_FILENAME).exists()


def _plus_available() -> bool:
    """A usable Plus JWT can be obtained: BROADCAST_PLUS_TOKEN in env OR Broadcast+.exe running."""
    if os.environ.get("BROADCAST_PLUS_TOKEN", "").strip():
        return True
    return _find_pid_safe("Broadcast+.exe") is not None


def pytest_collection_modifyitems(config, items):
    """Skip tests whose declared resource markers are not available on this host."""
    has_session = _legacy_session_available()
    has_db = _legacy_db_available()
    has_plus = _plus_available()

    skip_no_session = pytest.mark.skip(
        reason="legacy session unavailable: set BROADCAST_SESSION or start bcsys32.exe"
    )
    skip_no_db = pytest.mark.skip(
        reason=f"{INSTRUMENT_DB_FILENAME} not on disk (bcsys32.exe must have run here at least once)"
    )
    skip_no_plus = pytest.mark.skip(
        reason="plus backend unavailable: set BROADCAST_PLUS_TOKEN or start Broadcast+.exe"
    )

    for item in items:
        if "legacy_session" in item.keywords and not has_session:
            item.add_marker(skip_no_session)
        if "legacy_db" in item.keywords and not has_db:
            item.add_marker(skip_no_db)
        if "plus" in item.keywords and not has_plus:
            item.add_marker(skip_no_plus)

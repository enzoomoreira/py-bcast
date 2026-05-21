"""Automatic BCAA session token discovery from running Broadcast terminal.

Strategies (in order):
1. Explicit argument or BROADCAST_SESSION environment variable
2. Scan bcsys32.exe process memory for valid session token
"""

from __future__ import annotations

import ctypes
import ctypes.wintypes as wt
import os
import re
import subprocess
import sys

if sys.platform != "win32":
    raise ImportError("Session discovery requires Windows")

from .exceptions import SessionError
from .logging import get_logger

logger = get_logger(__name__)

# Cached token (survives for the process lifetime)
_cached_token: str | None = None

# Windows API constants
PROCESS_VM_READ = 0x0010
PROCESS_QUERY_INFORMATION = 0x0400
MEM_COMMIT = 0x1000
PAGE_GUARD = 0x100
PAGE_NOACCESS = 0x01

_kernel32 = ctypes.windll.kernel32


class _MEMORY_BASIC_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("BaseAddress", ctypes.c_void_p),
        ("AllocationBase", ctypes.c_void_p),
        ("AllocationProtect", wt.DWORD),
        ("RegionSize", ctypes.c_size_t),
        ("State", wt.DWORD),
        ("Protect", wt.DWORD),
        ("Type", wt.DWORD),
    ]


# Token pattern: uppercase hex letter + 32 lowercase hex chars (33 total)
_TOKEN_PATTERN = re.compile(rb"[A-F][0-9a-f]{32}")


def _find_bcsys32_pid() -> int | None:
    """Find PID of bcsys32.exe via tasklist."""
    try:
        result = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq bcsys32.exe", "/FO", "CSV", "/NH"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        for line in result.stdout.strip().splitlines():
            parts = line.strip('"').split('","')
            if len(parts) >= 2 and parts[0].lower() == "bcsys32.exe":
                return int(parts[1])
    except (subprocess.TimeoutExpired, OSError, ValueError):
        pass
    return None


def _scan_process_memory(pid: int) -> list[str]:
    """Scan process virtual memory for session token candidates."""
    handle = _kernel32.OpenProcess(
        PROCESS_VM_READ | PROCESS_QUERY_INFORMATION, False, pid
    )
    if not handle:
        return []

    found: set[str] = set()
    addr = 0
    mbi = _MEMORY_BASIC_INFORMATION()
    buf = ctypes.create_string_buffer(65536)

    try:
        while addr < 0x7FFFFFFFFFFF:
            ret = _kernel32.VirtualQueryEx(
                handle, ctypes.c_void_p(addr), ctypes.byref(mbi), ctypes.sizeof(mbi)
            )
            if ret == 0:
                break

            base = mbi.BaseAddress or 0
            size = mbi.RegionSize or 0
            if size == 0:
                break

            if (
                mbi.State == MEM_COMMIT
                and mbi.Protect not in (PAGE_GUARD, PAGE_NOACCESS, 0)
                and not (mbi.Protect & PAGE_GUARD)
            ):
                offset = 0
                while offset < size:
                    chunk_size = min(65536, size - offset)
                    bytes_read = ctypes.c_size_t(0)
                    success = _kernel32.ReadProcessMemory(
                        handle,
                        ctypes.c_void_p(base + offset),
                        buf,
                        chunk_size,
                        ctypes.byref(bytes_read),
                    )
                    if success and bytes_read.value > 0:
                        for m in _TOKEN_PATTERN.findall(buf.raw[: bytes_read.value]):
                            found.add(m.decode("ascii"))
                    offset += chunk_size

            addr = base + size
    finally:
        _kernel32.CloseHandle(handle)

    return sorted(found)


def _validate_token(token: str) -> bool:
    """Validate a candidate token with a lightweight HTTP request."""
    import httpx

    try:
        r = httpx.get(
            "http://cp.ae.com.br:44780/BaseHistoricaNumerica/HistoricoFechamentos",
            params={
                "10023": "4",
                "10039": token,
                "10113": "PETR4",
                "DatasTolerancia": "20260101",
                "TipoResposta": "xml",
            },
            headers={"User-Agent": "bcsys32/7.0"},
            timeout=5,
            verify=False,
        )
        valid = "<STATUS>success</STATUS>" in r.text
        logger.debug("Token validation %s: %s", "passed" if valid else "failed", token[:8] + "...")
        return valid
    except Exception as exc:
        logger.warning("Token validation request failed: %s", exc)
        return False


def discover_session_token() -> str:
    """Auto-discover session token from the running Broadcast terminal.

    Searches bcsys32.exe process memory for valid BCAA session tokens.
    Requires the Broadcast terminal to be running under the same user.

    Returns:
        Valid session token string.

    Raises:
        RuntimeError: If terminal is not running or token cannot be found.
    """
    pid = _find_bcsys32_pid()
    if pid is None:
        raise SessionError(
            "Broadcast terminal (bcsys32.exe) is not running. "
            "Start the terminal and try again."
        )

    candidates = _scan_process_memory(pid)
    if not candidates:
        raise SessionError(
            f"Could not read session token from bcsys32.exe (PID {pid}). "
            "The process may require elevated privileges."
        )

    logger.info("Found %d token candidates, validating...", len(candidates))
    for token in candidates:
        if _validate_token(token):
            logger.info("Valid session token discovered.")
            return token

    raise SessionError(
        f"Found {len(candidates)} token candidates in bcsys32.exe memory "
        "but none validated successfully. The session may have expired."
    )


def get_session_token(session_token: str | None = None) -> str:
    """Resolve session token: explicit > env var > cached > auto-discovery.

    Args:
        session_token: Explicit token (highest priority).

    Returns:
        Valid BCAA session token.

    Raises:
        SessionError: If auto-discovery fails and no token provided.
    """
    global _cached_token

    # 1. Explicit argument
    if session_token:
        return session_token

    # 2. Environment variable
    env_token = os.environ.get("BROADCAST_SESSION", "")
    if env_token:
        return env_token

    # 3. Previously discovered token
    if _cached_token:
        return _cached_token

    # 4. Auto-discover from running terminal (expensive ~5s)
    _cached_token = discover_session_token()
    return _cached_token


def clear_token_cache() -> None:
    """Clear the cached session token, forcing re-discovery on next call."""
    global _cached_token
    _cached_token = None

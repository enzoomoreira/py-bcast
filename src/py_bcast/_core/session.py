"""Automatic BCAA session token discovery from running Broadcast terminal.

Strategies (in order):
1. Explicit argument or BROADCAST_SESSION environment variable
2. Scan bcsys32.exe process memory for valid session token
"""

from __future__ import annotations

import os
import re

from .exceptions import SessionError
from .logging import get_logger
from .memory import find_process_pid, scan_process_memory

logger = get_logger(__name__)

# Cached token (survives for the process lifetime)
_cached_token: str | None = None

# Token pattern: uppercase hex letter + 32 lowercase hex chars (33 total)
_TOKEN_PATTERN = re.compile(rb"[A-F][0-9a-f]{32}")


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
        logger.debug(
            "Token validation %s: %s",
            "passed" if valid else "failed",
            token[:8] + "...",
        )
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
    pid = find_process_pid("bcsys32.exe")
    if pid is None:
        raise SessionError(
            "Broadcast terminal (bcsys32.exe) is not running. "
            "Start the terminal and try again."
        )

    candidates = scan_process_memory(pid, _TOKEN_PATTERN)
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

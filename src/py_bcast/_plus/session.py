"""Broadcast+ JWT session management.

Auth priority chain (in order):
1. BROADCAST_PLUS_TOKEN env var
2. In-memory cached JWT (from prior scan or login in this process)
3. Auto-refresh via cached refresh token (transparent — no user action needed)
4. Memory scan of Broadcast+.exe for a valid JWT (requires terminal running)
5. ECDH P-384 login with credentials from configure(plus_login=..., plus_password=...)
6. BroadcastPlusAuthError

Tokens are kept in-memory only (not persisted to disk). Each Python process
starts fresh. Use the BROADCAST_PLUS_TOKEN env var for headless/CI scenarios.
"""

from __future__ import annotations

import os
import re

import httpx

from .._core.constants import PLUS_APP_ID, PLUS_BASE_URL, plus_base_headers
from .._core.exceptions import BroadcastPlusAuthError
from .._core.logging import get_logger
from .._core.memory import find_process_pid, scan_process_memory
from .crypto import do_key_exchange, encrypt_password

logger = get_logger(__name__)

# ── In-memory token cache (process lifetime only) ─────────────────────────────

_jwt_token: str | None = None
_refresh_token: str | None = None

# JWT pattern: base64url header.payload.signature — all three parts must have
# realistic minimum lengths to avoid matching short random strings.
_JWT_PATTERN = re.compile(
    rb"eyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]{20,}"
)


# ── Internal helpers ──────────────────────────────────────────────────────────


def _validate_plus_token(token: str) -> bool:
    """Check token validity via GET /authentication/v1/keep. Returns True if valid."""
    try:
        r = httpx.get(
            f"{PLUS_BASE_URL}/authentication/v1/keep",
            headers={**plus_base_headers(), "Authorization": f"Bearer {token}"},
            timeout=5,
            verify=False,
        )
        valid = r.status_code != 401
        logger.debug("Plus token validation %s", "passed" if valid else "failed")
        return valid
    except Exception as exc:
        logger.warning("Plus token validation request failed: %s", exc)
        return False


def _do_ecdh_login(login: str, password: str) -> tuple[str, str]:
    """Full ECDH P-384 + AES-GCM login flow.

    Args:
        login: User email (lowercased automatically).
        password: Plaintext password (encrypted before transmission).

    Returns:
        (jwt_token, refresh_token)

    Raises:
        BroadcastPlusAuthError: On invalid credentials or server rejection.
        httpx.HTTPError: On network/server error.
    """
    with httpx.Client(verify=False, trust_env=False, timeout=15) as s:
        aes_key, session_id = do_key_exchange(s, plus_base_headers())
        encrypted_pw = encrypt_password(password, aes_key, session_id)

        r = s.post(
            f"{PLUS_BASE_URL}/authentication/v1/login",
            json={
                "login": login.lower(),
                "password": encrypted_pw,
                "applicationId": PLUS_APP_ID,
            },
            headers=plus_base_headers(),
            timeout=15,
        )
    r.raise_for_status()
    data = r.json()

    if not data.get("success") or not data.get("token"):
        msg = data.get("message", "Login failed")
        raise BroadcastPlusAuthError(
            f"Broadcast+ login rejected: {msg}",
            endpoint="/authentication/v1/login",
            server_message=msg,
        )
    return data["token"], data["refreshToken"]


def _do_refresh(current_jwt: str, refresh_tok: str) -> tuple[str, str] | None:
    """Attempt a silent JWT refresh. Returns (new_jwt, new_refresh) or None."""
    try:
        with httpx.Client(verify=False, trust_env=False, timeout=10) as s:
            r = s.post(
                f"{PLUS_BASE_URL}/authentication/v1/refresh",
                json={"token": current_jwt, "refreshToken": refresh_tok},
                headers=plus_base_headers(),
                timeout=10,
            )
        if r.status_code != 200:
            return None
        data = r.json()
        tok = data.get("token")
        ref = data.get("refreshToken")
        if tok and ref:
            return tok, ref
        return None
    except Exception as exc:
        logger.warning("Plus token refresh failed: %s", exc)
        return None


# ── Public API ────────────────────────────────────────────────────────────────


def get_plus_token() -> str:
    """Resolve a valid Broadcast+ JWT via the auth priority chain.

    Priority:
        1. ``BROADCAST_PLUS_TOKEN`` environment variable
        2. In-memory cached JWT (valid from prior call in this process)
        3. Auto-refresh via cached refresh token
        4. Memory scan of ``Broadcast+.exe`` process (requires terminal running)
        5. ECDH login with ``configure(plus_login=..., plus_password=...)``
        6. :class:`BroadcastPlusAuthError`

    Returns:
        Valid JWT string.

    Raises:
        BroadcastPlusAuthError: If every strategy in the chain fails.
    """
    global _jwt_token, _refresh_token

    # 1. Environment variable — highest priority, no caching
    env_token = os.environ.get("BROADCAST_PLUS_TOKEN", "")
    if env_token:
        return env_token

    # 2. In-memory cache
    if _jwt_token:
        return _jwt_token

    # 3. Silent refresh (if we have a refresh token from a prior ECDH login)
    if _refresh_token:
        result = _do_refresh(_jwt_token or "", _refresh_token)
        if result:
            _jwt_token, _refresh_token = result
            logger.info("Broadcast+ JWT refreshed successfully.")
            return _jwt_token

    # 4. Memory scan of Broadcast+.exe
    pid = find_process_pid("Broadcast+.exe")
    if pid is not None:
        candidates = scan_process_memory(pid, _JWT_PATTERN)
        logger.info("Broadcast+ memory scan: %d JWT candidates found.", len(candidates))
        for candidate in candidates:
            if _validate_plus_token(candidate):
                _jwt_token = candidate
                logger.info("Valid JWT discovered from Broadcast+.exe memory.")
                return _jwt_token
        logger.debug("Memory scan found no valid JWT candidates.")
    else:
        logger.debug("Broadcast+.exe not running — skipping memory scan.")

    # 5. ECDH login with configured credentials
    from .._core.config import get_settings

    settings = get_settings()
    if settings.plus_login and settings.plus_password:
        logger.info("Authenticating with Broadcast+ via ECDH login...")
        _jwt_token, _refresh_token = _do_ecdh_login(
            settings.plus_login, settings.plus_password
        )
        logger.info("Broadcast+ ECDH login successful.")
        return _jwt_token

    # 6. Nothing worked
    raise BroadcastPlusAuthError(
        "Cannot obtain a Broadcast+ JWT. Provide one via:\n"
        "  1. export BROADCAST_PLUS_TOKEN=<jwt>          (headless/CI)\n"
        "  2. Start Broadcast+.exe                        (desktop)\n"
        "  3. configure(plus_login='...', plus_password='...')  (headless login)"
    )


def refresh_plus_token() -> str:
    """Force token re-acquisition (called automatically on 401 responses).

    Clears the cached JWT and re-runs the full auth chain.

    Returns:
        New valid JWT string.

    Raises:
        BroadcastPlusAuthError: If re-authentication fails.
    """
    global _jwt_token
    _jwt_token = None
    return get_plus_token()


def clear_plus_token_cache() -> None:
    """Clear the in-memory Plus JWT and refresh token (forces re-auth on next call)."""
    global _jwt_token, _refresh_token
    _jwt_token = None
    _refresh_token = None


def discover_plus_token() -> str:
    """Discover a JWT by scanning the running Broadcast+.exe process memory.

    Useful for explicit pre-warming or debugging. Caches the discovered token
    for the current process lifetime.

    Returns:
        Valid JWT string.

    Raises:
        BroadcastPlusAuthError: If terminal not running or no valid JWT found.
    """
    global _jwt_token

    pid = find_process_pid("Broadcast+.exe")
    if pid is None:
        raise BroadcastPlusAuthError(
            "Broadcast+.exe is not running. Start the terminal and retry."
        )

    candidates = scan_process_memory(pid, _JWT_PATTERN)
    if not candidates:
        raise BroadcastPlusAuthError(
            f"Could not read JWT from Broadcast+.exe (PID {pid}). "
            "The process may require elevated privileges."
        )

    logger.info("Found %d JWT candidates, validating...", len(candidates))
    for candidate in candidates:
        if _validate_plus_token(candidate):
            _jwt_token = candidate
            logger.info("Valid JWT discovered and cached.")
            return candidate

    raise BroadcastPlusAuthError(
        f"Found {len(candidates)} JWT candidates in Broadcast+.exe memory "
        "but none validated. The session may have expired — restart the terminal."
    )

"""Ticker → CVM and indicator name → ID resolution with caching."""

from __future__ import annotations

import unicodedata

import pandas as pd

from .._core.exceptions import NotFoundError, ValidationError
from .._core.logging import get_logger

logger = get_logger(__name__)

# Module-level caches (persist for process lifetime)
_cvm_cache: dict[str, int] = {}
_indicator_meta_cache: list[dict] | None = None


def resolve_cvm(ticker: str, session_token: str | None = None) -> int:
    """Resolve a ticker symbol to its CVM company code.

    Uses bquote() internally. Results are cached for the process lifetime.

    Args:
        ticker: B3 ticker symbol (e.g., "PETR4", "VALE3").
        session_token: Optional explicit BCAA session token.

    Returns:
        CVM numeric code (e.g., 9512 for PETR4).

    Raises:
        NotFoundError: If the ticker cannot be resolved.
    """
    key = ticker.strip().upper()
    if key in _cvm_cache:
        return _cvm_cache[key]

    # Lazy import to avoid circular dependency
    from ..fundamental.reference import _quote_one

    quote = _quote_one(key, session_token=session_token)
    return _cvm_from_quote(key, quote)


async def aresolve_cvm(ticker: str, session_token: str | None = None) -> int:
    """Async version of ``resolve_cvm`` (shares the same process cache).

    Mirrors the sync resolver but awaits the async quote primitive, so the
    event loop is never blocked on a synchronous HTTP call.
    """
    key = ticker.strip().upper()
    if key in _cvm_cache:
        return _cvm_cache[key]

    # Lazy import to avoid circular dependency
    from .._async.fundamental import _abquote_one

    quote = await _abquote_one(key, session_token=session_token)
    return _cvm_from_quote(key, quote)


def _cvm_from_quote(key: str, quote: pd.DataFrame) -> int:
    """Extract and cache the CVM code from a one-row quote frame."""
    if quote.empty or "cvm_code" not in quote.columns:
        raise NotFoundError(key, kind="ticker")
    cvm_raw = quote["cvm_code"].iloc[0]
    if cvm_raw is None or (
        isinstance(cvm_raw, float) and cvm_raw != cvm_raw
    ):  # NaN check
        raise NotFoundError(
            key,
            kind="ticker",
            message=f"Ticker '{key}' has no associated CVM code in quote data.",
        )
    cvm = int(float(cvm_raw))
    _cvm_cache[key] = cvm
    logger.debug("Resolved %s → CVM %d", key, cvm)
    return cvm


def _strip_accents(s: str) -> str:
    """Remove unicode accents for fuzzy matching."""
    nfkd = unicodedata.normalize("NFKD", s)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def resolve_indicator(name_or_id: str | int, session_token: str | None = None) -> int:
    """Resolve an indicator name or ID to its numeric ID.

    Accepts:
        - int or digit string → returned directly
        - str → fuzzy-matched against bindicator_meta() names

    Matching priority: exact match > startswith > contains.
    Case-insensitive, accent-insensitive.

    Args:
        name_or_id: Indicator ID (int) or name (str, e.g. "EBITDA", "ROE").
        session_token: Optional explicit BCAA session token.

    Returns:
        Numeric indicator ID.

    Raises:
        ValidationError: If the name is ambiguous or not found.
    """
    # Fast path: already numeric
    if isinstance(name_or_id, int):
        return name_or_id
    s = str(name_or_id).strip()
    if s.isdigit():
        return int(s)

    # Load and cache indicator metadata
    global _indicator_meta_cache
    if _indicator_meta_cache is None:
        from ..fundamental.reference import bindicator_meta

        _indicator_meta_cache = _build_indicator_cache(
            bindicator_meta(session_token=session_token)
        )

    return _match_indicator(s)


async def aresolve_indicator(
    name_or_id: str | int, session_token: str | None = None
) -> int:
    """Async version of ``resolve_indicator`` (shares the same process cache)."""
    if isinstance(name_or_id, int):
        return name_or_id
    s = str(name_or_id).strip()
    if s.isdigit():
        return int(s)

    global _indicator_meta_cache
    if _indicator_meta_cache is None:
        from .._async.fundamental import abindicator_meta

        _indicator_meta_cache = _build_indicator_cache(
            await abindicator_meta(session_token=session_token)
        )

    return _match_indicator(s)


def _build_indicator_cache(meta_df: pd.DataFrame) -> list[dict]:
    """Project the indicator metadata frame to the active (id, name) cache."""
    return [
        {"id": int(row["indicator_id"]), "name": row["name"]}
        for _, row in meta_df.iterrows()
        if row.get("active") == "S"
    ]


def _match_indicator(s: str) -> int:
    """Fuzzy-match a name against the loaded indicator cache.

    Priority: exact > startswith > contains. Case- and accent-insensitive.
    Assumes ``_indicator_meta_cache`` is already populated.
    """
    query = _strip_accents(s.lower())

    # Priority 1: exact match
    for item in _indicator_meta_cache:
        if _strip_accents(item["name"].lower()) == query:
            return item["id"]

    # Priority 2: startswith
    starts = [
        item
        for item in _indicator_meta_cache
        if _strip_accents(item["name"].lower()).startswith(query)
    ]
    if len(starts) == 1:
        return starts[0]["id"]

    # Priority 3: contains
    contains = [
        item
        for item in _indicator_meta_cache
        if query in _strip_accents(item["name"].lower())
    ]
    if len(contains) == 1:
        return contains[0]["id"]
    if len(contains) > 1:
        names = [c["name"] for c in contains[:5]]
        raise ValidationError(
            f"Ambiguous indicator name '{s}' — matches: {names}. "
            f"Use the numeric ID or a more specific name."
        )

    # Also try startswith if multiple
    if len(starts) > 1:
        names = [c["name"] for c in starts[:5]]
        raise ValidationError(
            f"Ambiguous indicator name '{s}' — matches: {names}. "
            f"Use the numeric ID or a more specific name."
        )

    raise NotFoundError(
        s,
        kind="indicator",
        message=f"Indicator '{s}' not found. Use bindicator_meta() to list available indicators.",
    )

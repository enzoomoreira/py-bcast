"""Ticker → CVM and indicator name → ID resolution with caching."""

from __future__ import annotations

import unicodedata

from .exceptions import NotFoundError, ValidationError
from .logging import get_logger

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
        ValidationError: If the ticker cannot be resolved.
    """
    key = ticker.strip().upper()
    if key in _cvm_cache:
        return _cvm_cache[key]

    # Lazy import to avoid circular dependency
    from ..fundamental.reference import bquote

    quote = bquote(key, session_token=session_token)
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

        meta_df = bindicator_meta(session_token=session_token)
        _indicator_meta_cache = [
            {"id": int(row["indicator_id"]), "name": row["name"]}
            for _, row in meta_df.iterrows()
            if row.get("active") == "S"
        ]

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


def clear_resolve_cache() -> None:
    """Clear all resolution caches (CVM and indicator)."""
    global _indicator_meta_cache
    _cvm_cache.clear()
    _indicator_meta_cache = None

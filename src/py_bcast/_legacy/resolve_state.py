"""Shared state and pure helpers for ticker/indicator resolution.

The sync and async resolvers (``_legacy/_sync/resolve.py`` generated from
``_legacy/_async/resolve.py``) share one process-lifetime cache per kind, so
this state lives outside the generated trees — both import it from here.
"""

from __future__ import annotations

import unicodedata

import pandas as pd

from .._core.exceptions import NotFoundError, ValidationError
from .._core.logging import get_logger

logger = get_logger(__name__)

# Process-lifetime caches, shared by the sync and async resolvers.
cvm_cache: dict[str, int] = {}
_indicator_cache: list[dict] | None = None


def cvm_from_quote(key: str, quote: pd.DataFrame) -> int:
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
    cvm_cache[key] = cvm
    logger.debug("Resolved %s → CVM %d", key, cvm)
    return cvm


def indicator_cache_loaded() -> bool:
    """Whether the indicator (id, name) cache has been populated."""
    return _indicator_cache is not None


def load_indicator_cache(meta_df: pd.DataFrame) -> None:
    """Project the indicator metadata frame to the active (id, name) cache."""
    global _indicator_cache
    _indicator_cache = [
        {"id": int(row["indicator_id"]), "name": row["name"]}
        for _, row in meta_df.iterrows()
        if row.get("active") == "S"
    ]


def _strip_accents(s: str) -> str:
    """Remove unicode accents for fuzzy matching."""
    nfkd = unicodedata.normalize("NFKD", s)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def match_indicator(s: str) -> int:
    """Fuzzy-match a name against the loaded indicator cache.

    Priority: exact > startswith > contains. Case- and accent-insensitive.
    Assumes the cache is already populated (``indicator_cache_loaded()``).
    """
    query = _strip_accents(s.lower())

    # Priority 1: exact match
    for item in _indicator_cache:
        if _strip_accents(item["name"].lower()) == query:
            return item["id"]

    # Priority 2: startswith
    starts = [
        item
        for item in _indicator_cache
        if _strip_accents(item["name"].lower()).startswith(query)
    ]
    if len(starts) == 1:
        return starts[0]["id"]

    # Priority 3: contains
    contains = [
        item
        for item in _indicator_cache
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

"""Credit default swap (CDS) data via the Markit feed of the legacy terminal."""

from __future__ import annotations

import pandas as pd

from .._core.validation import DateParam, validate_params
from .._legacy.markit import normalize_cds_type, to_iso_date
from .._legacy._sync.markit import bcds_core, bcds_indices_core


@validate_params
def bcds(
    entity: str | None = None,
    date: DateParam | None = None,
    cds_type: str = "S",
    tier: str | None = None,
    docclause: str | None = None,
    session_token: str | None = None,
) -> pd.DataFrame:
    """Fetch a CDS term-structure curve (or list available entities) from Markit.

    Sovereign and corporate credit default swap data published through the
    legacy terminal's MarkitOutput2 feed. With ``entity`` given, returns the
    full term structure (one row per tenor: 6M, 1Y, 2Y, 3Y, 4Y, 5Y, 7Y, 10Y)
    for that entity on ``date``. Without ``entity``, returns the entities
    available on ``date`` (both sovereign and corporate; filter the
    ``cds_type`` column yourself).

    The Markit (tier, docclause) listing pair is resolved automatically from
    the entity name — when an entity lists more than one doc clause, the ISDA
    2014 (``*14``) clause wins; pass ``tier=``/``docclause=`` to override.

    Args:
        entity:    CDS entity code or display name, case/accent-insensitive
                   (e.g. "BRASIL", "Alemanha", "Banco do Brasil"). None lists
                   the available entities instead.
        date:      Curve date (YYYYMMDD, date, datetime, or Timestamp). None
                   resolves to the most recent date the feed has data for.
        cds_type:  "S" (sovereign, default) or "C" (corporate). Only used to
                   resolve ``entity``; ignored for the entity listing.
        tier:      Explicit Markit tier (e.g. "SNRFOR") when the automatic
                   resolution is ambiguous.
        docclause: Explicit doc clause (e.g. "CR14") when the automatic
                   resolution is ambiguous.
        session_token: BCAA session token.

    Returns:
        Flat DataFrame (RangeIndex). Curve columns: ``date``, ``entity``,
        ``name``, ``cds_type``, ``tier``, ``docclause``, ``tenor``, ``spread``,
        ``change_day``, ``change_month``, ``bid_ask``, ``region``, ``country``,
        ``sector``, ``currency``, ``recovery``, ``curve_rating``,
        ``implied_rating``, ``depth_5y``, ``liquidity_score``. Spreads are in
        basis points, parsed from BR decimal format. Empty DataFrame with the
        same schema for a valid date with no coverage.

    Raises:
        NotFoundError: ``entity`` does not exist in the date's listing.
        ValidationError: ``cds_type`` invalid, or the entity's listing is
            ambiguous and needs ``tier=``/``docclause=``.

    Example:
        >>> from py_bcast import bcds
        >>> bcds()                       # entities available on the latest date
        >>> df = bcds("BRASIL")          # sovereign curve, latest date
        >>> df[["tenor", "spread"]]
    """
    return bcds_core(
        entity,
        to_iso_date(date) if date is not None else None,
        normalize_cds_type(cds_type),
        tier,
        docclause,
        session_token=session_token,
    )


@validate_params
def bcds_indices(
    date: DateParam | None = None,
    session_token: str | None = None,
) -> pd.DataFrame:
    """Fetch the Markit CDS index term-structure table from the legacy feed.

    Tradable CDS indices (CDXEM, iTraxx, etc.) — distinct from the single-name
    curves of ``bcds`` — with their composite price/spread, bid/ask, daily and
    monthly changes, RED code, maturity and depth.

    Args:
        date: Curve date (YYYYMMDD, date, datetime, or Timestamp). None
            resolves to the most recent date the feed has data for.
        session_token: BCAA session token.

    Returns:
        Flat DataFrame (RangeIndex), one row per index series: ``date``,
        ``name``, ``redcode``, ``maturity`` (raw Markit form), ``composite_price``,
        ``bid_ask_price``, ``composite_spread``, ``bid_ask_spread``,
        ``change_day``, ``change_month`` and ``depth``. Empty DataFrame with the
        same schema for a valid date with no coverage.

    Example:
        >>> from py_bcast import bcds_indices
        >>> df = bcds_indices()
        >>> df[["name", "composite_spread"]].head()
    """
    return bcds_indices_core(
        to_iso_date(date) if date is not None else None,
        session_token=session_token,
    )

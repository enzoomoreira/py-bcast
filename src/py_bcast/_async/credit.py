"""Async credit (CDS) functions."""

from __future__ import annotations

import pandas as pd

from .._core.validation import DateParam, validate_params
from .._legacy.markit import normalize_cds_type, to_iso_date
from .._legacy._async.markit import bcds_core


@validate_params
async def abcds(
    entity: str | None = None,
    date: DateParam | None = None,
    cds_type: str = "S",
    tier: str | None = None,
    docclause: str | None = None,
    session_token: str | None = None,
) -> pd.DataFrame:
    """Async version of ``bcds``.

    One row per tenor of the entity's CDS term structure (or the entity
    listing when ``entity`` is None), RangeIndex.
    """
    return await bcds_core(
        entity,
        to_iso_date(date) if date is not None else None,
        normalize_cds_type(cds_type),
        tier,
        docclause,
        session_token=session_token,
    )

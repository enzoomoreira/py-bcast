"""Scalar quote primitive — shared by the public bquote and the CVM resolver."""

from __future__ import annotations

import pandas as pd

from ..aetp import rows_to_dicts
from ..columns import QUOTE_FIELDS, QUOTE_SCHEMA
from ..output import Index, finalize_frame
from .transport import aetp_request


async def quote_one(
    ticker: str,
    session_token: str | None = None,
) -> pd.DataFrame:
    """Fetch the quote for a single symbol (one row, or empty with schema).

    Soft (empty_ok default): an unknown ticker yields an empty block rather
    than raising — ``resolve_cvm`` turns that into NotFoundError, so this must
    never depend on the list-returning public ``bquote``.
    """
    parsed = await aetp_request(
        "fundamental/ativo/cotacao", {"10068": ticker}, session_token
    )
    rows = rows_to_dicts(parsed)
    record = rows[0] if rows else {}
    return finalize_frame(
        record, index=Index.RECORD, rename=QUOTE_FIELDS, schema=QUOTE_SCHEMA
    )

"""DataFrame output construction layer.

Converts raw API responses (a ``list[dict[str, str]]`` or a single record
``dict``) into typed pandas DataFrames with the right index and numeric
coercion. A single :func:`finalize_frame` entry point selects the index policy
via the :class:`Index` enum.
"""

from __future__ import annotations

from enum import Enum, auto

import pandas as pd


# Server sentinels for "no value" that must not poison numeric coercion.
# A column of numbers plus one of these (e.g. a no-trade tolerance row whose
# value is "n/d") is still numeric; the sentinel cells become NaN. Matched
# case-insensitively against the stripped cell value.
MISSING_VALUE_SENTINELS: frozenset[str] = frozenset({"n/d", "n/a", "nd", "-", "--"})


class Index(Enum):
    """Index policy for :func:`finalize_frame`.

    - ``RANGE``: default RangeIndex (reference/event tables).
    - ``DATETIME``: parse ``date_col`` (YYYYMMDD) into a DatetimeIndex.
    - ``DATETIME_TIME``: combine ``date_col`` + ``time_col`` into a DatetimeIndex.
    - ``RECORD``: a single record dict materialized as a one-row frame.
    """

    RANGE = auto()
    DATETIME = auto()
    DATETIME_TIME = auto()
    RECORD = auto()


def coerce_numeric_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Coerce each wholly-numeric column to a numeric dtype, in place.

    A column is treated as numeric when every non-blank cell parses as a
    number; its blank cells ('' or NA) then become NaN. If any non-blank cell
    fails to parse, the column is genuine text and is left untouched (blanks
    stay as the empty strings the server sent).

    Known missing-value sentinels (``MISSING_VALUE_SENTINELS``, e.g. the "n/d"
    a no-trade tolerance row carries) are treated as blanks, not coercion
    failures, so a column that is all-numeric apart from those sentinels still
    coerces (the sentinel cells become NaN). A column with genuine text stays
    text.

    Identifier columns whose tokens carry a significant leading zero (CNPJ,
    CPF, zero-padded codes) are left as text even though they parse as numbers:
    coercing them would drop the leading zero and corrupt the id. A genuine
    quantity never starts with a zero before another digit, so "0.5"/"0" still
    coerce; "08773135000100"/"00000000000000" do not.

    Replaces the old ``to_numeric(...).fillna(original)`` pattern, which
    restored blank strings into otherwise-numeric columns and forced the whole
    column back to ``object`` dtype (the binflation "all object" bug). Inputs
    here are US-formatted (dot decimal, scientific notation); BR-formatted
    scalar strings from the DDE/WebSocket paths are handled separately.
    """
    for col in df.columns:
        coerced = pd.to_numeric(df[col], errors="coerce")
        stripped = df[col].astype("string").str.strip()
        is_sentinel = stripped.str.lower().isin(MISSING_VALUE_SENTINELS)
        blank = (stripped.isna() | (stripped == "") | is_sentinel).fillna(True)
        failed = coerced.isna() & ~blank
        if bool(failed.any()):
            continue
        # A wholly-numeric column whose tokens carry a significant leading zero
        # (CNPJ, CPF, zero-padded codes) is an identifier, not a quantity:
        # coercing it drops the leading zero and corrupts the id (e.g.
        # "08773135000100" -> 8773135000100.0, "00000000000000" -> 0.0). A real
        # number never has a leading zero before another digit ("0.5"/"0" do
        # not), so the guard is "leading 0 followed by a digit". Dates
        # (YYYYMMDD) have no leading zero and still coerce to int — a known,
        # non-corrupting limitation, not handled here.
        if bool(stripped.str.match(r"0\d", na=False).any()):
            continue
        df[col] = coerced
    return df


def _strip_bvmf_suffix(df: pd.DataFrame) -> pd.DataFrame:
    """Strip the server-appended ".BVMF" from the ticker column, in place.

    The canonical output ticker is bare ("PETR4"), matching what callers
    type; only the local-exchange suffix the server echoes is removed.
    International symbols keep whatever internal form the server emits, and
    non-string cells (e.g. a CVM-code lookup key) pass through untouched.
    """
    if "ticker" in df.columns:
        df["ticker"] = df["ticker"].map(
            lambda v: v.removesuffix(".BVMF") if isinstance(v, str) else v
        )
    return df


def _apply_rename(
    df: pd.DataFrame, rename: dict[str, str | None] | None
) -> pd.DataFrame:
    """Rename and drop columns based on a mapping.

    Keys mapping to None are dropped. Keys mapping to a string are renamed.
    Columns not in the mapping pass through unchanged.
    """
    if rename is None:
        return df
    drop_cols = [col for col in df.columns if rename.get(col) is None and col in rename]
    if drop_cols:
        df = df.drop(columns=drop_cols)
    name_map = {k: v for k, v in rename.items() if v is not None and k in df.columns}
    if name_map:
        df = df.rename(columns=name_map)
    return df


def _empty_frame(schema: dict[str, str] | None) -> pd.DataFrame:
    """Build a typed empty DataFrame from a column -> dtype schema."""
    return pd.DataFrame({col: pd.Series(dtype=dt) for col, dt in schema.items()})


def _build_datetime_index(
    df: pd.DataFrame, date_col: str, time_col: str | None
) -> pd.DataFrame:
    """Parse a date (and optional time) column into a DatetimeIndex.

    If ``date_col`` is absent the frame is returned untouched (RangeIndex), so
    a malformed response degrades to a plain frame instead of raising.
    """
    if date_col not in df.columns:
        return df

    if time_col and time_col in df.columns:
        # Time format may be HH:MM:SS.mmm (colon-separated) or HHMMSS
        sample_time = df[time_col].iloc[0] if len(df) > 0 else ""
        if ":" in sample_time:
            # Colon-separated: "10:06:33.359" — combine with space
            dt_strings = df[date_col] + " " + df[time_col]
            # Strip optional milliseconds for consistent parsing
            dt_strings = dt_strings.str.replace(r"\.\d+$", "", regex=True)
            df.index = pd.to_datetime(
                dt_strings, format="%Y%m%d %H:%M:%S", errors="coerce"
            )
        else:
            dt_strings = df[date_col] + df[time_col]
            fmt = "%Y%m%d%H%M%S" if len(sample_time) >= 6 else "%Y%m%d%H%M"
            df.index = pd.to_datetime(dt_strings, format=fmt, errors="coerce")
        df = df.drop(columns=[date_col, time_col])
    else:
        df.index = pd.to_datetime(df[date_col], format="%Y%m%d", errors="coerce")
        df = df.drop(columns=[date_col])
    df.index.name = None
    return df


def finalize_frame(
    data: list[dict[str, str]] | dict[str, str],
    *,
    index: Index,
    rename: dict[str, str | None] | None = None,
    schema: dict[str, str] | None = None,
    date_col: str = "dat",
    time_col: str | None = None,
    ticker: str | None = None,
) -> pd.DataFrame:
    """Build a typed DataFrame from raw rows under one index policy.

    The ``index`` enum selects the behaviour:

    - ``RANGE`` / ``DATETIME`` / ``DATETIME_TIME`` take a ``list[dict]``.
    - ``RECORD`` takes a single ``dict`` (one entity).

    All non-empty paths run :func:`coerce_numeric_columns` then the ``rename``
    mapping. An empty input yields a bare ``pd.DataFrame()`` when ``schema`` is
    None, or a schema-preserving empty frame otherwise (with an empty
    DatetimeIndex for the datetime policies). ``ticker`` is only consulted for
    ``RECORD`` (inserted as the first column when the record carries none).

    Args:
        data: Row dicts (list policies) or a single record dict (RECORD).
        index: Index policy (see :class:`Index`).
        rename: Column rename/drop mapping (keys -> None are dropped).
        schema: Column -> dtype map used only to type an empty result.
        date_col: Date column name for the datetime policies (default "dat").
        time_col: Time column name for ``DATETIME_TIME``.
        ticker: For ``RECORD`` only: inserted as ``ticker`` if absent.

    Returns:
        A typed DataFrame following the requested index policy.
    """
    if index is Index.RECORD:
        # RECORD takes a single record dict; an empty dict means "no entity".
        rows: list[dict[str, str]] = [data] if data else []  # type: ignore[list-item]
    else:
        rows = data  # type: ignore[assignment]

    if not rows:
        if schema is None:
            return pd.DataFrame()
        empty = _empty_frame(schema)
        if index in (Index.DATETIME, Index.DATETIME_TIME):
            empty.index = pd.DatetimeIndex([])
        return empty

    df = pd.DataFrame(rows)

    if index is Index.DATETIME:
        df = _build_datetime_index(df, date_col, None)
    elif index is Index.DATETIME_TIME:
        df = _build_datetime_index(df, date_col, time_col)

    df = coerce_numeric_columns(df)
    df = _apply_rename(df, rename)
    df = _strip_bvmf_suffix(df)

    if index is Index.RECORD and ticker is not None and "ticker" not in df.columns:
        df.insert(0, "ticker", ticker)
    return df


def empty_history_frame(schema: dict[str, str]) -> pd.DataFrame:
    """Empty flat history frame: ticker column + schema on a DatetimeIndex.

    Shared by the sync and async ``bhistory`` for the inverted-window
    early exit (the close endpoint rejects start > end with a server error
    instead of the family's usual no-records reply).
    """
    df = finalize_frame([], index=Index.DATETIME, schema=schema)
    df.insert(0, "ticker", pd.Series(dtype="object"))
    return df

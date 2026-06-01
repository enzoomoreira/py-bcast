"""DataFrame output construction layer.

Converts raw API responses (list[dict[str, str]]) into typed pandas DataFrames
with proper DatetimeIndex and numeric coercion.
"""

from __future__ import annotations

import pandas as pd

from .columns import CONTENT_PROXY_RENAME


def coerce_numeric_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Coerce each wholly-numeric column to a numeric dtype, in place.

    A column is treated as numeric when every non-blank cell parses as a
    number; its blank cells ('' or NA) then become NaN. If any non-blank cell
    fails to parse, the column is genuine text and is left untouched (blanks
    stay as the empty strings the server sent).

    Replaces the old ``to_numeric(...).fillna(original)`` pattern, which
    restored blank strings into otherwise-numeric columns and forced the whole
    column back to ``object`` dtype (the binflation "all object" bug). Inputs
    here are US-formatted (dot decimal, scientific notation); BR-formatted
    scalar strings from the DDE/WebSocket paths are handled separately.
    """
    for col in df.columns:
        coerced = pd.to_numeric(df[col], errors="coerce")
        stripped = df[col].astype("string").str.strip()
        blank = (stripped.isna() | (stripped == "")).fillna(True)
        failed = coerced.isna() & ~blank
        if bool(failed.any()):
            continue
        df[col] = coerced
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


def to_dataframe(
    rows: list[dict[str, str]],
    date_col: str = "dat",
    time_col: str | None = None,
    rename: dict[str, str | None] | None = CONTENT_PROXY_RENAME,
    schema: dict[str, str] | None = None,
) -> pd.DataFrame:
    """Convert a list of row dicts into a DataFrame with DatetimeIndex.

    Parses the date column (and optionally time column) into a DatetimeIndex,
    coerces all remaining columns to numeric where possible, and renames
    columns according to the rename mapping.

    Args:
        rows: List of dicts from API response.
        date_col: Name of the date column (default "dat", format YYYYMMDD).
        time_col: If set, name of the time column (e.g. "hor") to combine
                  with date_col for intraday DatetimeIndex.
        rename: Column rename mapping. Keys → None are dropped; keys → str
                are renamed. Default: CONTENT_PROXY_RENAME. Pass None to skip.
        schema: Column → dtype map used only when ``rows`` is empty, to return
                an empty DataFrame with the right columns and a DatetimeIndex
                (instead of a bare, schema-less frame). The populated frame
                keeps its coercion-inferred dtypes.

    Returns:
        DataFrame with DatetimeIndex and numeric columns.
        Empty DataFrame (with schema + DatetimeIndex if ``schema`` is given)
        if rows is empty.
    """
    if not rows:
        if schema is None:
            return pd.DataFrame()
        df = _empty_frame(schema)
        df.index = pd.DatetimeIndex([])
        return df

    df = pd.DataFrame(rows)

    # Build DatetimeIndex
    if date_col in df.columns:
        if time_col and time_col in df.columns:
            # Combine date + time for intraday index
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
                # Determine format based on time_col length
                if len(sample_time) >= 6:
                    fmt = "%Y%m%d%H%M%S"
                else:
                    fmt = "%Y%m%d%H%M"
                df.index = pd.to_datetime(dt_strings, format=fmt, errors="coerce")
            df = df.drop(columns=[date_col, time_col])
        else:
            df.index = pd.to_datetime(df[date_col], format="%Y%m%d", errors="coerce")
            df = df.drop(columns=[date_col])
        df.index.name = None

    df = coerce_numeric_columns(df)
    return _apply_rename(df, rename)


def to_multi_dataframe(
    data: dict[str, list[dict[str, str]]],
    date_col: str = "dat",
) -> dict[str, pd.DataFrame]:
    """Convert multi-ticker results to dict of DataFrames.

    Args:
        data: Dict mapping symbol -> list of row dicts.
        date_col: Name of the date column.

    Returns:
        Dict mapping symbol -> DataFrame with DatetimeIndex.
    """
    return {
        symbol: to_dataframe(rows, date_col=date_col) for symbol, rows in data.items()
    }


def to_reference_dataframe(
    rows: list[dict[str, str]],
    rename: dict[str, str | None] | None = None,
    schema: dict[str, str] | None = None,
) -> pd.DataFrame:
    """Convert reference/event data to a DataFrame without DatetimeIndex.

    Uses RangeIndex (default). Coerces numeric columns where possible.

    Args:
        rows: List of dicts from API response.
        rename: Rename mapping. Default: None (no rename — AETP endpoints
                pass their own per-endpoint map).
        schema: Column → dtype map used only when ``rows`` is empty, to return
                an empty DataFrame with the right columns (instead of a bare,
                schema-less frame). The populated frame keeps its
                coercion-inferred dtypes.

    Returns:
        DataFrame with RangeIndex and numeric columns where applicable.
    """
    if not rows:
        return pd.DataFrame() if schema is None else _empty_frame(schema)

    df = pd.DataFrame(rows)

    df = coerce_numeric_columns(df)
    return _apply_rename(df, rename)


def to_record_dataframe(
    record: dict[str, str],
    rename: dict[str, str | None] | None = CONTENT_PROXY_RENAME,
    schema: dict[str, str] | None = None,
    ticker: str | None = None,
) -> pd.DataFrame:
    """Convert a single server record to a one-row DataFrame (RangeIndex).

    Single-entity reference endpoints (quote, shares, consensus) return one
    record; this materializes it as a one-row DataFrame so every tabular
    endpoint speaks the same type.

    Args:
        record: Dict of field -> string value (one entity).
        rename: Column rename mapping (same semantics as to_dataframe).
        schema: Column → dtype map used only when ``record`` is empty.
        ticker: If given and the record carries no ``ticker`` column, insert
                it as the first column (so the entity key is explicit).

    Returns:
        One-row DataFrame, or an empty DataFrame (with schema if given) when
        the record is empty.
    """
    if not record:
        return pd.DataFrame() if schema is None else _empty_frame(schema)
    df = pd.DataFrame([record])
    df = coerce_numeric_columns(df)
    df = _apply_rename(df, rename)
    if ticker is not None and "ticker" not in df.columns:
        df.insert(0, "ticker", ticker)
    return df

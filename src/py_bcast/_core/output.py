"""DataFrame output construction layer.

Converts raw API responses (list[dict[str, str]]) into typed pandas DataFrames
with proper DatetimeIndex and numeric coercion.
"""

from __future__ import annotations

import pandas as pd


def to_dataframe(
    rows: list[dict[str, str]],
    date_col: str = "dat",
    time_col: str | None = None,
) -> pd.DataFrame:
    """Convert a list of row dicts into a DataFrame with DatetimeIndex.

    Parses the date column (and optionally time column) into a DatetimeIndex,
    and coerces all remaining columns to numeric where possible.

    Args:
        rows: List of dicts from API response.
        date_col: Name of the date column (default "dat", format YYYYMMDD).
        time_col: If set, name of the time column (e.g. "hor") to combine
                  with date_col for intraday DatetimeIndex.

    Returns:
        DataFrame with DatetimeIndex and numeric columns.
        Returns empty DataFrame if rows is empty.
    """
    if not rows:
        return pd.DataFrame()

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
                df.index = pd.to_datetime(dt_strings, format="%Y%m%d %H:%M:%S", errors="coerce")
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

    # Coerce numeric columns
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(df[col])

    return df


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
        symbol: to_dataframe(rows, date_col=date_col)
        for symbol, rows in data.items()
    }


def to_series(record: dict[str, str]) -> pd.Series:
    """Convert a single-record dict to a pandas Series with numeric coercion.

    Args:
        record: Dict of field_name -> string value.

    Returns:
        Series with values coerced to numeric where possible.
        Returns empty Series if record is empty.
    """
    if not record:
        return pd.Series(dtype="object")
    s = pd.Series(record)
    # Try numeric coercion per-element
    return s.apply(pd.to_numeric, errors="coerce").fillna(s)


def to_reference_dataframe(rows: list[dict[str, str]]) -> pd.DataFrame:
    """Convert reference/event data to a DataFrame without DatetimeIndex.

    Uses RangeIndex (default). Coerces numeric columns where possible.

    Args:
        rows: List of dicts from API response.

    Returns:
        DataFrame with RangeIndex and numeric columns where applicable.
    """
    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)

    # Coerce numeric columns
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(df[col])

    return df

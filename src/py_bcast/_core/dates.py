"""Date normalization utilities.

Accepts flexible date inputs (str, date, datetime, pd.Timestamp) and
normalizes to the string formats required by the Broadcast API.
"""

from __future__ import annotations

import datetime
from typing import Union
from zoneinfo import ZoneInfo

import pandas as pd

# Type alias for any date-like input
DateLike = Union[str, datetime.date, datetime.datetime, pd.Timestamp]

# The exchange wall-clock timezone the intraday windows are expressed in.
SAO_PAULO_TZ = ZoneInfo("America/Sao_Paulo")


def to_date_str(value: DateLike) -> str:
    """Normalize a date-like value to YYYYMMDD string.

    Args:
        value: A date in any common format:
            - str: "YYYYMMDD" or "YYYY-MM-DD"
            - datetime.date or datetime.datetime
            - pd.Timestamp

    Returns:
        Date as YYYYMMDD string.

    Raises:
        ValueError: If the input cannot be interpreted as a valid date.
    """
    if isinstance(value, str):
        clean = value.replace("-", "").replace("/", "")
        if len(clean) != 8 or not clean.isdigit():
            raise ValueError(
                f"Invalid date string '{value}'. Expected YYYYMMDD or YYYY-MM-DD."
            )
        # Validate by parsing
        datetime.datetime.strptime(clean, "%Y%m%d")
        return clean
    if isinstance(value, pd.Timestamp):
        return value.strftime("%Y%m%d")
    if isinstance(value, datetime.datetime):
        return value.strftime("%Y%m%d")
    if isinstance(value, datetime.date):
        return value.strftime("%Y%m%d")
    raise TypeError(f"Cannot convert {type(value).__name__} to date string.")


def to_datetime_str(value: DateLike) -> str:
    """Normalize a datetime-like value to YYYYMMDDHHMMSS string.

    Args:
        value: A datetime in any common format:
            - str: "YYYYMMDDHHMMSS" (14 digits)
            - datetime.datetime or pd.Timestamp (time portion used)
            - datetime.date (time defaults to 00:00:00)

    Returns:
        Datetime as YYYYMMDDHHMMSS string (14 digits).

    Raises:
        ValueError: If the input cannot be interpreted as a valid datetime.
    """
    if isinstance(value, str):
        clean = (
            value.replace("-", "")
            .replace("/", "")
            .replace(":", "")
            .replace(" ", "")
            .replace("T", "")
        )
        if len(clean) == 8:
            clean += "000000"
        if len(clean) != 14 or not clean.isdigit():
            raise ValueError(
                f"Invalid datetime string '{value}'. Expected YYYYMMDDHHMMSS."
            )
        datetime.datetime.strptime(clean, "%Y%m%d%H%M%S")
        return clean
    if isinstance(value, pd.Timestamp):
        return value.strftime("%Y%m%d%H%M%S")
    if isinstance(value, datetime.datetime):
        return value.strftime("%Y%m%d%H%M%S")
    if isinstance(value, datetime.date):
        return datetime.datetime.combine(value, datetime.time()).strftime(
            "%Y%m%d%H%M%S"
        )
    raise TypeError(f"Cannot convert {type(value).__name__} to datetime string.")


def to_utc_datetime_str(value: DateLike) -> str:
    """Read a São Paulo wall-clock datetime and return the UTC wire string.

    The intraday endpoints (bdt/bticks) take their window in UTC, but the
    public API speaks Brasília time: a caller's ``...100000`` means 10:00 in
    São Paulo. This interprets the value in ``America/Sao_Paulo`` and converts
    it to the UTC ``YYYYMMDDHHMMSS`` the server expects (Brazil has no DST, so
    it is a fixed -03:00, but the zone handles historical transitions).
    """
    naive = to_datetime_str(value)
    ts = pd.Timestamp(datetime.datetime.strptime(naive, "%Y%m%d%H%M%S"))
    return ts.tz_localize(SAO_PAULO_TZ).tz_convert("UTC").strftime("%Y%m%d%H%M%S")


def default_end_date() -> str:
    """Return today's date as YYYYMMDD string."""
    return datetime.date.today().strftime("%Y%m%d")


def default_tick_end(start_str: str) -> str:
    """Default ``bdt``/``abdt`` window end: start + 1 hour (YYYYMMDDHHMMSS)."""
    dt = datetime.datetime.strptime(start_str, "%Y%m%d%H%M%S")
    return (dt + datetime.timedelta(hours=1)).strftime("%Y%m%d%H%M%S")


def business_days(start: DateLike, end: DateLike) -> list[str]:
    """Generate list of business days (Mon-Fri) between start and end inclusive.

    Args:
        start: Start date (any DateLike format)
        end: End date (any DateLike format)

    Returns:
        List of YYYYMMDD strings for each weekday in range.
    """
    start_str = to_date_str(start)
    end_str = to_date_str(end)

    d = datetime.datetime.strptime(start_str, "%Y%m%d").date()
    end_d = datetime.datetime.strptime(end_str, "%Y%m%d").date()

    dates: list[str] = []
    while d <= end_d:
        if d.weekday() < 5:
            dates.append(d.strftime("%Y%m%d"))
        d += datetime.timedelta(days=1)
    return dates

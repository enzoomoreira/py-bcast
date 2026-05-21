"""Input validation for public API functions.

Provides pydantic-based annotated types and a ``validate_params`` decorator
that wraps ``pydantic.validate_call`` while converting pydantic's
``ValidationError`` into ``py_bcast.ValidationError``.
"""

from __future__ import annotations

import datetime
import functools
from typing import Annotated, Any, Union

import pandas as pd
from pydantic import (
    AfterValidator,
    BeforeValidator,
    Field,
    validate_call,
)
from pydantic import ValidationError as PydanticValidationError

from py_bcast._core.exceptions import ValidationError

# ---------------------------------------------------------------------------
# Coercion helpers
# ---------------------------------------------------------------------------


def _coerce_date(value: Any) -> str:
    """Coerce flexible date inputs to YYYYMMDD string."""
    if isinstance(value, pd.Timestamp):
        return value.strftime("%Y%m%d")
    if isinstance(value, datetime.datetime):
        return value.strftime("%Y%m%d")
    if isinstance(value, datetime.date):
        return value.strftime("%Y%m%d")
    if isinstance(value, str):
        clean = value.replace("-", "").replace("/", "")
        if len(clean) == 8 and clean.isdigit():
            datetime.datetime.strptime(clean, "%Y%m%d")  # validate
            return clean
    raise ValueError(f"Invalid date: {value!r}. Expected YYYYMMDD, YYYY-MM-DD, date, or Timestamp.")


def _coerce_datetime(value: Any) -> str:
    """Coerce flexible datetime inputs to YYYYMMDDHHMMSS string."""
    if isinstance(value, pd.Timestamp):
        return value.strftime("%Y%m%d%H%M%S")
    if isinstance(value, datetime.datetime):
        return value.strftime("%Y%m%d%H%M%S")
    if isinstance(value, datetime.date):
        return datetime.datetime.combine(value, datetime.time()).strftime("%Y%m%d%H%M%S")
    if isinstance(value, str):
        clean = value.replace("-", "").replace("/", "").replace(":", "").replace(" ", "").replace("T", "")
        if len(clean) == 8:
            clean += "000000"
        if len(clean) == 14 and clean.isdigit():
            datetime.datetime.strptime(clean, "%Y%m%d%H%M%S")  # validate
            return clean
    raise ValueError(f"Invalid datetime: {value!r}. Expected YYYYMMDDHHMMSS or datetime.")


def _coerce_ticker_list(value: Any) -> list[str]:
    """Coerce str | list[str] to a non-empty list of uppercase ticker strings."""
    if isinstance(value, str):
        value = [value]
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"Expected str or list[str], got {type(value).__name__}")
    result = [t.strip().upper() for t in value if t and t.strip()]
    if not result:
        raise ValueError("Ticker list must not be empty.")
    return result


def _coerce_cvm_code(value: Any) -> str:
    """Coerce int | str to a CVM code string."""
    s = str(value).strip()
    if not s or not s.isdigit():
        raise ValueError(f"Invalid CVM code: {value!r}. Expected numeric string or int.")
    return s


def _validate_ticker(value: str) -> str:
    """Validate a single ticker string."""
    v = value.strip().upper()
    if not v:
        raise ValueError("Ticker must not be empty.")
    return v


# ---------------------------------------------------------------------------
# Annotated types for use in function signatures
# ---------------------------------------------------------------------------

DateParam = Annotated[Union[str, datetime.date, datetime.datetime, pd.Timestamp], BeforeValidator(_coerce_date)]
"""Date-like parameter coerced to YYYYMMDD string."""

DateTimeParam = Annotated[
    Union[str, datetime.date, datetime.datetime, pd.Timestamp], BeforeValidator(_coerce_datetime)
]
"""DateTime-like parameter coerced to YYYYMMDDHHMMSS string."""

Ticker = Annotated[str, AfterValidator(_validate_ticker)]
"""Single ticker string (uppercased, non-empty)."""

TickerList = Annotated[Union[str, list[str]], BeforeValidator(_coerce_ticker_list)]
"""One or more tickers coerced to list[str]."""

CvmCode = Annotated[Union[str, int], BeforeValidator(_coerce_cvm_code)]
"""CVM company code coerced to string."""

PositiveInt = Annotated[int, Field(gt=0)]
"""Positive integer (> 0)."""


# ---------------------------------------------------------------------------
# Decorator
# ---------------------------------------------------------------------------


def validate_params(fn: Any = None, /) -> Any:
    """Decorator that applies pydantic ``validate_call`` and re-raises as ``py_bcast.ValidationError``.

    Usage::

        @validate_params
        def bdh(tickers: TickerList, start_date: DateParam, ...) -> ...:
            ...
    """

    def decorator(func: Any) -> Any:
        validated = validate_call(
            validate_return=False,
            config={"arbitrary_types_allowed": True},
        )(func)

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return validated(*args, **kwargs)
            except PydanticValidationError as exc:
                raise ValidationError(str(exc)) from exc

        return wrapper

    if fn is not None:
        return decorator(fn)
    return decorator

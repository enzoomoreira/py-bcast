"""Input validation for public API functions.

Provides pydantic-based annotated types and a ``validate_params`` decorator
that wraps ``pydantic.validate_call`` while converting pydantic's
``ValidationError`` into ``py_bcast.ValidationError``.
"""

from __future__ import annotations

import datetime
import functools
import inspect
from typing import Annotated, Any, Union

import pandas as pd
from pydantic import (
    AfterValidator,
    BeforeValidator,
    validate_call,
)
from pydantic import ValidationError as PydanticValidationError

from py_bcast._core.dates import to_date_str, to_datetime_str
from py_bcast._core.exceptions import ValidationError

# ---------------------------------------------------------------------------
# Coercion helpers
# ---------------------------------------------------------------------------


def _coerce_date(value: Any) -> str:
    """Coerce flexible date inputs to YYYYMMDD string.

    Delegates to ``to_date_str`` (single source of date parsing) and normalizes
    its ValueError/TypeError into a ValueError so pydantic wraps it as a
    ``ValidationError`` (pydantic does not convert a raw TypeError).
    """
    try:
        return to_date_str(value)
    except (ValueError, TypeError) as exc:
        raise ValueError(
            f"Invalid date: {value!r}. Expected YYYYMMDD, YYYY-MM-DD, date, or Timestamp."
        ) from exc


def _coerce_datetime(value: Any) -> str:
    """Coerce flexible datetime inputs to YYYYMMDDHHMMSS string.

    Delegates to ``to_datetime_str`` (single source of datetime parsing) and
    normalizes its ValueError/TypeError into a ValueError so pydantic wraps it
    as a ``ValidationError``.
    """
    try:
        return to_datetime_str(value)
    except (ValueError, TypeError) as exc:
        raise ValueError(
            f"Invalid datetime: {value!r}. Expected YYYYMMDDHHMMSS or datetime."
        ) from exc


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
        raise ValueError(
            f"Invalid CVM code: {value!r}. Expected numeric string or int."
        )
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

DateParam = Annotated[
    Union[str, datetime.date, datetime.datetime, pd.Timestamp],
    BeforeValidator(_coerce_date),
]
"""Date-like parameter coerced to YYYYMMDD string."""

DateTimeParam = Annotated[
    Union[str, datetime.date, datetime.datetime, pd.Timestamp],
    BeforeValidator(_coerce_datetime),
]
"""DateTime-like parameter coerced to YYYYMMDDHHMMSS string."""

Ticker = Annotated[str, AfterValidator(_validate_ticker)]
"""Single ticker string (uppercased, non-empty)."""

TickerList = Annotated[Union[str, list[str]], BeforeValidator(_coerce_ticker_list)]
"""One or more tickers coerced to list[str]."""

CvmCode = Annotated[Union[str, int], BeforeValidator(_coerce_cvm_code)]
"""CVM company code coerced to string."""


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

        if inspect.iscoroutinefunction(func):

            @functools.wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                # Argument validation for a coroutine function happens when the
                # returned coroutine is awaited, so the await must sit inside the
                # try/except — otherwise pydantic's error escapes uncaught.
                try:
                    return await validated(*args, **kwargs)
                except PydanticValidationError as exc:
                    raise ValidationError(str(exc)) from exc

            return async_wrapper

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

"""Centralized exception hierarchy for py_bcast."""

from __future__ import annotations


class PyBcastError(Exception):
    """Base exception for all py_bcast errors."""


class SessionError(PyBcastError):
    """Token discovery or validation failure."""


class ContentProxyError(PyBcastError):
    """HTTP-level error from the Broadcast server (status != 200, error tags).

    Attributes:
        endpoint: The API endpoint that failed (e.g. "BaseHistoricaNumerica/...").
        server_message: The error message extracted from the XML <MESSAGE> element.
        status_code: HTTP status code, if available.
    """

    def __init__(
        self,
        message: str = "",
        *,
        endpoint: str | None = None,
        server_message: str | None = None,
        status_code: int | None = None,
    ):
        self.endpoint = endpoint
        self.server_message = server_message
        self.status_code = status_code
        super().__init__(message)


class ProtocolError(PyBcastError):
    """Binary SOH protocol parsing failure (malformed response).

    Attributes:
        error_tag: The error message extracted from tag 10037, if present.
        record_count: Number of records found when the response was malformed.
    """

    def __init__(
        self,
        message: str = "",
        *,
        error_tag: str | None = None,
        record_count: int | None = None,
    ):
        self.error_tag = error_tag
        self.record_count = record_count
        super().__init__(message)


class DDEError(PyBcastError):
    """DDE initialization, connection, or advise failure."""


class DDEAdviseError(DDEError):
    """DDE advise (subscription) failure for a specific item.

    Raised when a DDE advise transaction fails, typically because the
    ticker doesn't exist or the field is not applicable.

    Attributes:
        item: The full DDE item string (e.g. "EMBR3.ULT").
        ticker: The ticker portion (e.g. "EMBR3").
        field: The field portion (e.g. "ULT").
        error_code: The DDEML error code (e.g. 0x4009 for advise ack timeout).
    """

    def __init__(
        self,
        message: str = "",
        *,
        item: str = "",
        ticker: str = "",
        field: str = "",
        error_code: int = 0,
    ):
        self.item = item
        self.ticker = ticker
        self.field = field
        self.error_code = error_code
        super().__init__(message)


class ValidationError(PyBcastError, ValueError):
    """Input parameter validation failure.

    Inherits from ValueError so ``except ValueError`` still catches it,
    preserving backward-compatible catch patterns.
    """

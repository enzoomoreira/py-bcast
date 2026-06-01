"""Centralized exception hierarchy for py_bcast."""

from __future__ import annotations

# Known server error messages → actionable English hints
_ERROR_HINTS: dict[str, str] = {
    "0": "Server returned empty response — check parameters or date range",
    "não foram encontrados registros": "No records found for the given criteria",
    "registro não encontrado": "No records found for the given criteria",
    "sessão inválida": "Session token expired — call clear_token_cache() and retry",
    "token expirado": "Session token expired — call clear_token_cache() and retry",
    "erro interno": "Internal server error — retry later",
    "parâmetro inválido": "Invalid parameter sent to endpoint",
    "ativo não encontrado": "Ticker/asset not found in the database",
    "empresa não encontrada": "Company not found — verify CVM code",
}


def _get_hint(message: str | None) -> str | None:
    """Look up an actionable hint for a server error message."""
    if not message:
        return None
    lower = message.strip().lower()
    for key, hint in _ERROR_HINTS.items():
        if key in lower or lower == key:
            return hint
    return None


# Server messages that mean "the requested entity does not exist" (bad input).
_NOT_FOUND_MARKERS = (
    "não existe",
    "ativo não encontrado",
    "empresa não encontrada",
)
# Server messages that mean "a valid query simply matched no rows".
_NO_RECORDS_MARKERS = (
    "não foram encontrados registros",
    "registro não encontrado",
    # Range entirely before the instrument's history start: a valid query
    # over a window with no data, not a bad symbol or a transport failure.
    "data de início do histórico",
)


def is_not_found(message: str | None) -> bool:
    """True if the server message means the looked-up entity does not exist."""
    if not message:
        return False
    low = message.strip().lower()
    return any(m in low for m in _NOT_FOUND_MARKERS)


def is_no_records(message: str | None) -> bool:
    """True if the server message means a valid query returned zero rows.

    Note this is ambiguous on the AETP binary path (the server returns the
    same message for an unknown entity and an empty-but-valid range), so AETP
    callers disambiguate with an explicit ``empty_ok`` flag rather than relying
    on the message alone.
    """
    if not message:
        return False
    low = message.strip().lower()
    return any(m in low for m in _NO_RECORDS_MARKERS)


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

    def __str__(self) -> str:
        parts = [super().__str__()]
        hint = _get_hint(self.server_message)
        if hint:
            parts.append(f"Hint: {hint}")
        if self.endpoint:
            parts.append(f"Endpoint: {self.endpoint}")
        return " | ".join(p for p in parts if p)


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

    def __str__(self) -> str:
        parts = [super().__str__()]
        hint = _get_hint(self.error_tag)
        if hint:
            parts.append(f"Hint: {hint}")
        return " | ".join(p for p in parts if p)


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


class NotFoundError(PyBcastError):
    """The requested entity does not exist on the server.

    Raised for a well-formed but non-existent input — an unknown ticker, CVM
    code, broker, or indicator. This is distinct from:
        - ValidationError: the input itself was malformed.
        - an empty result: a valid query that simply matched no rows, which
          returns an empty DataFrame with schema instead of raising.

    Attributes:
        identifier: The value that was looked up (e.g. "PETR99", 99999999).
        kind: The kind of entity (e.g. "ticker", "symbol", "cvm_code",
              "broker", "indicator").
    """

    def __init__(
        self,
        identifier: object = None,
        *,
        kind: str = "entity",
        message: str | None = None,
    ):
        self.identifier = identifier
        self.kind = kind
        if message is None:
            message = f"{kind} not found: {identifier!r}"
        super().__init__(message)


class BroadcastPlusError(PyBcastError):
    """HTTP-level error from the Broadcast+ API (svc.aebroadcast.com.br).

    Attributes:
        endpoint: The API path that failed (e.g. "/stock/v1/quote/symbol").
        server_message: Message extracted from the JSON error body.
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

    def __str__(self) -> str:
        parts = [super().__str__()]
        if self.endpoint:
            parts.append(f"Endpoint: {self.endpoint}")
        if self.server_message:
            parts.append(f"Server: {self.server_message}")
        return " | ".join(p for p in parts if p)


class BroadcastPlusAuthError(BroadcastPlusError):
    """Authentication failure for Broadcast+ (JWT unavailable or rejected).

    Raised when the full auth chain (env var -> memory scan -> ECDH login)
    is exhausted without producing a valid token.
    """

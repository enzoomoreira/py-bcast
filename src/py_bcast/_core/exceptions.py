"""Centralized exception hierarchy for py_bcast."""

from __future__ import annotations


class PyBcastError(Exception):
    """Base exception for all py_bcast errors."""


class SessionError(PyBcastError):
    """Token discovery or validation failure."""


class ContentProxyError(PyBcastError):
    """HTTP-level error from the Broadcast server (status != 200, error tags)."""


class ProtocolError(PyBcastError):
    """Binary SOH protocol parsing failure (malformed response)."""


class DDEError(PyBcastError):
    """DDE initialization, connection, or advise failure."""


class ValidationError(PyBcastError, ValueError):
    """Input parameter validation failure.

    Inherits from ValueError so ``except ValueError`` still catches it,
    preserving backward-compatible catch patterns.
    """

"""Input normalization utilities."""

from __future__ import annotations


def ensure_list(value: str | list[str]) -> list[str]:
    """Coerce a string-or-list argument to a list.

    Args:
        value: Single string or list of strings.

    Returns:
        List of strings.
    """
    if isinstance(value, str):
        return [value]
    return list(value)


def ensure_str(value: str | int) -> str:
    """Coerce an int-or-string argument to string.

    Args:
        value: String or integer (e.g., CVM code, broker ID).

    Returns:
        String representation.
    """
    return str(value)

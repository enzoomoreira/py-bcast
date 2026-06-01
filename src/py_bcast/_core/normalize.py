"""Input normalization utilities."""

from __future__ import annotations

import re

# A Brazilian-formatted number: optional sign, an integer part that is either a
# plain digit run or dot-grouped thousands (1.234, 1.234.567), and an optional
# comma decimal part. Anchored so partial junk never matches.
_BR_NUMBER_RE = re.compile(r"^[+-]?(\d{1,3}(\.\d{3})+|\d+)(,\d+)?$")


def parse_br_number(value: str) -> float | str:
    """Parse a Brazilian-formatted numeric string to float, else return as-is.

    Brazilian market feeds (the DDE terminal and the Broadcast+ WebSocket)
    format numbers with a decimal comma and dot thousands separators, e.g.
    ``"42,46"`` or ``"1.234,56"``. This converts those to float.

    A bare run of digits with neither a decimal comma nor dot grouping (e.g.
    ``"20260519"``, ``"63786"``) is deliberately left as a string: structurally
    it is indistinguishable from a date stamp or an identifier, so coercing it
    would risk silently corrupting a non-numeric field. The practical effect is
    that prices and percentages (which always carry a decimal comma) become
    float, while bare trade/quote counts stay strings. Non-numeric values (text,
    times such as ``"10:06:33"``) are returned unchanged.
    """
    if not isinstance(value, str):
        return value
    s = value.strip()
    if "," not in s and "." not in s:
        # Bare integer or text: ambiguous with dates/identifiers — leave as-is.
        return s
    if not _BR_NUMBER_RE.match(s):
        return s
    return float(s.replace(".", "").replace(",", "."))


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


def ensure_id_list(value: str | int | list[str | int]) -> list[str | int]:
    """Coerce a scalar-or-list of ticker-or-cvm identifiers to a list.

    Like ``ensure_list`` but tolerant of bare ``int`` CVM codes (which are not
    iterable), so a single ``9512`` stays ``[9512]`` instead of raising.
    """
    if isinstance(value, (list, tuple)):
        return list(value)
    return [value]


def ensure_str(value: str | int) -> str:
    """Coerce an int-or-string argument to string.

    Args:
        value: String or integer (e.g., CVM code, broker ID).

    Returns:
        String representation.
    """
    return str(value)

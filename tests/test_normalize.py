"""Unit tests for value/input normalization helpers (no backend required)."""

import pytest

from py_bcast._core.normalize import ensure_list, ensure_str, parse_br_number


class TestParseBrNumber:
    @pytest.mark.parametrize(
        "raw, expected",
        [
            ("42,46", 42.46),  # price
            ("1,0952", 1.0952),  # percent points (VAR)
            ("1.234,56", 1234.56),  # grouped thousands + decimal
            ("1.234", 1234.0),  # grouped thousands integer
            ("1.234.567", 1234567.0),  # multiple groups
            ("-0,5", -0.5),  # negative
            ("42,40", 42.4),
            ("0,19%", 0.19),  # WS percentage (percent points, % stripped)
            ("1,0952%", 1.0952),  # percentage with more decimals
            ("50%", 50.0),  # bare-integer percentage: % overrides date guard
        ],
    )
    def test_br_numbers_become_float(self, raw, expected):
        result = parse_br_number(raw)
        assert isinstance(result, float)
        assert result == expected

    @pytest.mark.parametrize(
        "raw",
        [
            "20260519",  # date-like bare integer: must NOT be coerced
            "63786",  # bare count: ambiguous with a date, stays str
            "10:06:33",  # time
            "PETROBRAS PN",  # text
            "1.23",  # malformed grouping (not 3-digit group)
            "42.46",  # US-style dot decimal (DDE never sends this)
            "",  # empty
        ],
    )
    def test_non_br_numbers_stay_string(self, raw):
        result = parse_br_number(raw)
        assert isinstance(result, str)
        assert result == raw

    def test_non_string_passthrough(self):
        assert parse_br_number(None) is None  # type: ignore[arg-type]


class TestEnsureHelpers:
    def test_ensure_list_from_str(self):
        assert ensure_list("PETR4") == ["PETR4"]

    def test_ensure_list_from_list(self):
        assert ensure_list(["PETR4", "VALE3"]) == ["PETR4", "VALE3"]

    def test_ensure_str_from_int(self):
        assert ensure_str(9512) == "9512"

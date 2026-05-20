"""Tests for automatic session token discovery."""

import os
from unittest.mock import patch, MagicMock

import pytest

from py_bcast._session import get_session_token, discover_session_token, _find_bcsys32_pid


class TestGetSessionToken:
    """Test the priority-based token resolution."""

    def test_explicit_token_takes_priority(self):
        """Explicit argument wins over everything."""
        token = get_session_token("EXPLICIT_TOKEN_123456789012345678")
        assert token == "EXPLICIT_TOKEN_123456789012345678"

    def test_env_var_used_when_no_explicit(self, monkeypatch):
        """BROADCAST_SESSION env var is second priority."""
        monkeypatch.setenv("BROADCAST_SESSION", "ENV_TOKEN_12345678901234567890")
        token = get_session_token()
        assert token == "ENV_TOKEN_12345678901234567890"

    def test_auto_discovery_when_no_env(self, monkeypatch):
        """Falls back to auto-discovery when no env var set."""
        monkeypatch.delenv("BROADCAST_SESSION", raising=False)
        with patch("py_bcast._session.discover_session_token", return_value="AUTO_DISCOVERED"):
            token = get_session_token()
            assert token == "AUTO_DISCOVERED"

    def test_auto_discovery_error_propagates(self, monkeypatch):
        """RuntimeError from discovery propagates to caller."""
        monkeypatch.delenv("BROADCAST_SESSION", raising=False)
        with patch(
            "py_bcast._session.discover_session_token",
            side_effect=RuntimeError("not running"),
        ):
            with pytest.raises(RuntimeError, match="not running"):
                get_session_token()


class TestFindPid:
    """Test PID discovery."""

    def test_finds_running_process(self):
        """Should find bcsys32.exe if running."""
        pid = _find_bcsys32_pid()
        # On CI this might be None, on dev machine with terminal it should be int
        assert pid is None or isinstance(pid, int)

    def test_returns_none_when_not_running(self):
        """Returns None when process not found."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout='INFO: No tasks are running\n')
            assert _find_bcsys32_pid() is None


class TestDiscoverSessionToken:
    """Test the full discovery flow."""

    def test_raises_when_terminal_not_running(self):
        """Clear error when bcsys32.exe is not found."""
        with patch("py_bcast._session._find_bcsys32_pid", return_value=None):
            with pytest.raises(RuntimeError, match="not running"):
                discover_session_token()

    def test_raises_when_memory_unreadable(self):
        """Clear error when process memory cannot be read."""
        with patch("py_bcast._session._find_bcsys32_pid", return_value=12345):
            with patch("py_bcast._session._scan_process_memory", return_value=[]):
                with pytest.raises(RuntimeError, match="Could not read"):
                    discover_session_token()

    def test_raises_when_no_valid_token(self):
        """Clear error when candidates don't validate."""
        with patch("py_bcast._session._find_bcsys32_pid", return_value=12345):
            with patch("py_bcast._session._scan_process_memory", return_value=["A" * 33]):
                with patch("py_bcast._session._validate_token", return_value=False):
                    with pytest.raises(RuntimeError, match="none validated"):
                        discover_session_token()

    def test_returns_first_valid_token(self):
        """Returns first candidate that validates."""
        with patch("py_bcast._session._find_bcsys32_pid", return_value=12345):
            with patch(
                "py_bcast._session._scan_process_memory",
                return_value=["A" * 33, "F9bca84c7cb51fbdb4456a86c6548fb13"],
            ):
                with patch(
                    "py_bcast._session._validate_token",
                    side_effect=lambda t: t == "F9bca84c7cb51fbdb4456a86c6548fb13",
                ):
                    token = discover_session_token()
                    assert token == "F9bca84c7cb51fbdb4456a86c6548fb13"


@pytest.mark.integration
class TestLiveDiscovery:
    """Integration test — requires running Broadcast terminal."""

    def test_live_discovery(self):
        """Discover token from actual running bcsys32.exe."""
        pid = _find_bcsys32_pid()
        if pid is None:
            pytest.skip("bcsys32.exe not running")
        token = discover_session_token()
        assert len(token) == 33
        assert token[0] in "ABCDEF"

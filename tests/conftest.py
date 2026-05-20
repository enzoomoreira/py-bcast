"""Shared test fixtures for py_bcast integration tests."""

import os
import pytest


@pytest.fixture(autouse=True)
def _set_session_token():
    """Ensure BROADCAST_SESSION is set for all tests."""
    token = os.environ.get("BROADCAST_SESSION", "F9bca84c7cb51fbdb4456a86c6548fb13")
    os.environ["BROADCAST_SESSION"] = token
    yield


def pytest_collection_modifyitems(config, items):
    """Skip DDE tests if not on Windows or bcsys32 not running."""
    import sys
    if sys.platform != "win32":
        skip = pytest.mark.skip(reason="DDE only available on Windows")
        for item in items:
            if "dde" in item.keywords:
                item.add_marker(skip)

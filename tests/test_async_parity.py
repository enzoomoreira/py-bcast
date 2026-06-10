"""Sync/async public API parity.

Guards the two-package mirror (``py_bcast`` vs ``py_bcast._async``): every public
sync data function must have an async twin with an identical call signature, and
every async export must map back to a public sync function.

The I/O layer underneath is drift-proof by construction (``_legacy/_sync/`` is
generated from ``_legacy/_async/`` — see ``scripts/gen_sync.py`` and
``tests/test_unasync.py``); the thin public facades remain hand-written on both
sides for idiomatic docstrings, and this test is what prevents drift between
those facade pairs.
"""

from __future__ import annotations

import inspect

import pytest

import py_bcast
from py_bcast import async_api

# Public sync symbols that intentionally have NO async twin. Kept explicit and
# commented so a future sync data function added without a twin fails loudly.
SYNC_WITHOUT_ASYNC_TWIN = {
    "bdp",  # DDE point-lookup, polymorphic (scalar/dict/None) -- not an HTTP path
    "bsearch",  # local instrument DB lookup -- no network, no async path
}

# Non-data public symbols: classes, config, exceptions, resolvers, namespaces.
# Excluded from the data-function parity sweep. resolve_cvm/resolve_indicator are
# public but their async forms (_legacy/_async/resolve.py) are internal and not
# in _async.__all__.
NON_DATA_SYMBOLS = {
    "BroadcastClient",
    "BroadcastPlusClient",
    "BroadcastPlusAsyncClient",
    "InstrumentDB",
    "Ticker",
    "MULTIMEDIA_CATEGORIES",
    "discover_session_token",
    "clear_token_cache",
    "discover_plus_token",
    "clear_plus_token_cache",
    "resolve_cvm",
    "resolve_indicator",
    "PyBcastError",
    "SessionError",
    "ContentProxyError",
    "ProtocolError",
    "DDEError",
    "DDEAdviseError",
    "ValidationError",
    "NotFoundError",
    "BroadcastPlusError",
    "BroadcastPlusAuthError",
    "DMLERR_ADVACKTIMEOUT",
    "DMLERR_NAMES",
    "configure_logging",
    "configure",
    "get_settings",
    "Settings",
    "cache_invalidate",
    "async_api",
}


def _sync_data_functions() -> dict[str, object]:
    """Public sync data functions: ``__all__`` minus non-data and documented exceptions."""
    return {
        name: getattr(py_bcast, name)
        for name in py_bcast.__all__
        if name not in NON_DATA_SYMBOLS and name not in SYNC_WITHOUT_ASYNC_TWIN
    }


def _params(fn: object) -> list[tuple[str, object, object, object]]:
    """Comparable parameter list (name, kind, default, annotation); return type ignored.

    ``inspect.signature`` follows ``__wrapped__`` through the ``@validate_params`` and
    ``@http_retry`` decorators (both use ``functools.wraps``), so this resolves the
    real declared signature, not the wrapper's ``(*args, **kwargs)``.
    """
    return [
        (p.name, p.kind, p.default, p.annotation)
        for p in inspect.signature(fn).parameters.values()
    ]


def test_every_sync_data_function_has_async_twin() -> None:
    missing = [
        (name, "a" + name)
        for name in _sync_data_functions()
        if ("a" + name) not in async_api.__all__
    ]
    assert not missing, (
        f"sync data functions without an async twin in async_api.__all__: {missing}"
    )


def test_every_async_export_maps_to_a_public_sync_function() -> None:
    orphans = []
    for twin in async_api.__all__:
        assert twin.startswith("a"), (
            f"async export {twin!r} does not follow the a-prefix convention"
        )
        name = twin[1:]  # abdh -> bdh
        if name not in py_bcast.__all__:
            orphans.append((twin, name))
    assert not orphans, f"async exports with no public sync counterpart: {orphans}"


@pytest.mark.parametrize("name", sorted(_sync_data_functions()))
def test_sync_and_async_signatures_match(name: str) -> None:
    sync_fn = getattr(py_bcast, name)
    async_fn = getattr(async_api, "a" + name)
    assert _params(sync_fn) == _params(async_fn), (
        f"signature drift between {name} and a{name}:\n"
        f"  sync:  {_params(sync_fn)}\n"
        f"  async: {_params(async_fn)}"
    )

"""I/O layer for the Broadcast+ backend (sync/async twin trees).

The async tree (``_plus/_async/``) is the hand-written source; the sync tree
(``_plus/_sync/``) is GENERATED from it by ``scripts/gen_sync.py`` — never
edit the sync tree by hand, edit the async source and regenerate.
Cross-boundary swap: ``get_plus_async_http_client`` -> ``get_plus_http_client``.

The auth chain (``_plus/session.py``: memory scan, ECDH login, JWT refresh)
is sync-only by nature (win32 + local crypto); the async transport calls it
directly — token refresh is rare and short, matching how the legacy async
tree consumes the sync ``get_session_token``.
"""

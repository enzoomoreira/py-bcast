"""Asyncio twin of the Broadcast+ WebSocket streaming client.

Hand-written counterpart of ``realtime.py`` — NOT part of the unasync codegen:
the sync client is built on ``websocket-client`` (callbacks + threads) while
this one is built on ``websockets`` (native asyncio), so the two state
machines cannot share a token-replaced source. Protocol knowledge (actions,
handshake, keep-alive cadence) is shared via the constants imported from
``realtime.py``; see that module's docstring for the wire protocol.
"""

from __future__ import annotations

import asyncio
import contextlib
import inspect
import json
import ssl
from collections.abc import Callable
from typing import Any

import websockets

from .._core.constants import PLUS_VERSION
from .._core.exceptions import BroadcastPlusAuthError
from .._core.logging import get_logger
from .._core.normalize import ensure_list, parse_br_number
from .realtime import (
    _DEFAULT_FIELDS,
    _MAX_RECONNECTS,
    _PING_INTERVAL,
    _RECONNECT_DELAY,
    _WS_URL,
    _ensure_int_list,
)
from .session import get_plus_token, refresh_plus_token

logger = get_logger(__name__)

_WS_ORIGIN = "https://svc.aebroadcast.com.br"


def _insecure_ssl_context() -> ssl.SSLContext:
    """SSL context matching the sync client (no hostname/cert verification)."""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


class BroadcastPlusAsyncClient:
    """Asyncio twin of :class:`~py_bcast._plus.realtime.BroadcastPlusClient`.

    Same protocol and lifecycle (auth chain, app-level ping/pong, token
    refresh, reconnect with backoff), but everything runs on the caller's
    event loop — no threads. Callbacks may be sync functions or coroutine
    functions; coroutine callbacks are awaited inline on the stream task.

    The blocking parts of the auth chain (memory scan / ECDH login) run in
    ``asyncio.to_thread`` so they never stall the loop.

    Usage::

        async def on_quote(data: dict) -> None:
            print(data["COD"], data["ULT"], data["VAR"])

        async with BroadcastPlusAsyncClient() as client:
            await client.subscribe(["PETR4", "VALE3"], callback=on_quote)
            await client.run(duration=60)  # streams for 60 seconds

    To stream alongside other work, wrap ``run()`` in a task::

        task = asyncio.create_task(client.run())
        ...
        await client.stop()
        await task
    """

    def __init__(self) -> None:
        self._ws: websockets.ClientConnection | None = None
        self._stop_event = asyncio.Event()
        self._auth_ok = False
        self._pending_token: str | None = None

        # subscription state (ticker -> callback)
        self._subscriptions: dict[str, Callable[[dict[str, Any]], Any]] = {}
        self._global_callback: Callable[[dict[str, Any]], Any] | None = None
        self._extra_fields: list[str] = []

        # market-table subscription state (set of ids + one shared callback)
        self._market_ids: set[int] = set()
        self._market_callback: Callable[[dict[str, Any]], Any] | None = None

        self._reconnect_count = 0

    # ── Context manager ───────────────────────────────────────────────────────

    async def __aenter__(self) -> BroadcastPlusAsyncClient:
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.stop()

    # ── Public API ────────────────────────────────────────────────────────────

    async def subscribe(
        self,
        tickers: str | list[str],
        callback: Callable[[dict[str, Any]], Any],
        fields: list[str] | None = None,
    ) -> None:
        """Subscribe to real-time quote updates for one or more tickers.

        Can be called before or after run(). If called while the stream is
        authenticated, the subscription is sent immediately.

        Args:
            tickers:  Single ticker or list (e.g. "PETR4" or ["PETR4","VALE3"]).
            callback: Called on each quote update with a dict of field values.
                      May be a plain function or a coroutine function; the
                      latter is awaited on the stream task.
            fields:   Extra WS fields to request beyond the default set. None
                      means use the default 13 fields from the Broadcast+ app.
        """
        tickers_upper = [t.strip().upper() for t in ensure_list(tickers)]
        for t in tickers_upper:
            self._subscriptions[t] = callback
        self._global_callback = callback  # last wins for mixed-ticker events
        if fields:
            self._extra_fields = list(set(self._extra_fields + fields))

        if self._auth_ok and self._ws:
            await self._send({"action": "startStreamQuote", "symbols": tickers_upper})
            if fields:
                await self._send(
                    {"action": "addFields", "fields": fields, "symbols": None}
                )

    async def unsubscribe(self, tickers: str | list[str]) -> None:
        """Unsubscribe from quote updates for the given tickers."""
        tickers_list = [t.strip().upper() for t in ensure_list(tickers)]
        for t in tickers_list:
            self._subscriptions.pop(t, None)
        if self._auth_ok and self._ws:
            await self._send({"action": "stopStreamQuote", "symbols": tickers_list})

    async def unsubscribe_all(self) -> None:
        """Unsubscribe from all active subscriptions."""
        tickers = list(self._subscriptions.keys())
        self._subscriptions.clear()
        if tickers and self._auth_ok and self._ws:
            await self._send({"action": "stopStreamQuote", "symbols": tickers})

    async def subscribe_market(
        self,
        market_ids: int | list[int],
        callback: Callable[[dict[str, Any]], Any],
    ) -> None:
        """Subscribe to live market-statistics tables (top gainers/losers, etc.).

        Async twin of :meth:`BroadcastPlusClient.subscribe_market`. The
        available ids are fixed by the server (Bovespa): 0 top gainers (cash),
        1 top losers (cash), 2 top gainers (index), 3 top losers (index), 4 most
        traded by financial volume, 5 traded volume, 6 Ibovespa evolution.

        A single ``callback`` (sync function or coroutine function) receives
        every subscribed table's updates; route by the payload's ``header`` /
        ``type`` rather than by id (the server does not echo the numeric id on
        every push).

        Args:
            market_ids: One id or a list (e.g. 0 or [0, 1]).
            callback:   Called on each table update with a dict carrying
                        ``header``, ``columns``, ``rows`` (numeric cells parsed
                        to float), and ``type``/``id``.
        """
        ids = _ensure_int_list(market_ids)
        self._market_ids.update(ids)
        self._market_callback = callback
        if self._auth_ok and self._ws:
            for mid in ids:
                await self._send(
                    {"action": "startStreamMarket", "id": mid, "requestId": str(mid)}
                )

    async def unsubscribe_market(
        self, market_ids: int | list[int] | None = None
    ) -> None:
        """Unsubscribe from market tables. None unsubscribes from all of them."""
        ids = (
            list(self._market_ids)
            if market_ids is None
            else _ensure_int_list(market_ids)
        )
        for mid in ids:
            self._market_ids.discard(mid)
        if ids and self._auth_ok and self._ws:
            for mid in ids:
                await self._send({"action": "stopStreamMarket", "id": mid})

    async def run(self, duration: float | None = None) -> None:
        """Connect and stream until ``duration`` seconds elapse or stop() is called.

        Reconnects with exponential backoff on connection loss (up to the same
        attempt budget as the sync client).

        Args:
            duration: Seconds to run. None means run until stop().
        """
        self._stop_event.clear()
        if duration is None:
            await self._run_loop()
            return
        try:
            await asyncio.wait_for(self._run_loop(), timeout=duration)
        except TimeoutError:
            pass
        finally:
            await self.stop()

    async def stop(self) -> None:
        """Stop streaming and close the WebSocket connection."""
        self._stop_event.set()
        if self._ws is not None:
            try:
                await self._ws.close()
            except Exception:
                pass
        self._auth_ok = False

    # ── Internal — connection lifecycle ───────────────────────────────────────

    async def _run_loop(self) -> None:
        """Connect/consume until stopped, reconnecting with backoff."""
        while not self._stop_event.is_set():
            try:
                await self._connect_and_consume()
            except (OSError, websockets.exceptions.WebSocketException) as exc:
                logger.warning("BroadcastPlusAsyncClient: connection error: %s", exc)
            if self._stop_event.is_set():
                return
            if self._reconnect_count >= _MAX_RECONNECTS:
                logger.error(
                    "BroadcastPlusAsyncClient: max reconnect attempts reached."
                )
                self._stop_event.set()
                return
            delay = _RECONNECT_DELAY * (2**self._reconnect_count)
            self._reconnect_count += 1
            logger.info(
                "BroadcastPlusAsyncClient: reconnecting in %.1fs (attempt %d/%d).",
                delay,
                self._reconnect_count,
                _MAX_RECONNECTS,
            )
            await asyncio.sleep(delay)

    async def _connect_and_consume(self) -> None:
        """One connection lifetime: open, handshake via messages, consume."""
        self._pending_token = await asyncio.to_thread(get_plus_token)
        async with websockets.connect(
            _WS_URL,
            origin=_WS_ORIGIN,
            additional_headers={"x-version": PLUS_VERSION},
            ssl=_insecure_ssl_context(),
            ping_interval=None,  # server uses app-level {"action": "ping"} JSON
        ) as ws:
            self._ws = ws
            logger.debug("BroadcastPlusAsyncClient: WebSocket opened.")
            ping_task = asyncio.create_task(self._ping_loop())
            try:
                async for raw in ws:
                    await self._handle_message(raw)
                    if self._stop_event.is_set():
                        break
            finally:
                ping_task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await ping_task
                self._ws = None
                self._auth_ok = False

    async def _ping_loop(self) -> None:
        """App-level keep-alive, mirroring the sync client's ping thread."""
        while True:
            await asyncio.sleep(_PING_INTERVAL)
            if self._auth_ok:
                await self._send({"action": "ping"})

    # ── Internal — protocol ───────────────────────────────────────────────────

    async def _handle_message(self, raw: str | bytes) -> None:
        try:
            msg = json.loads(raw)
        except json.JSONDecodeError:
            logger.warning("BroadcastPlusAsyncClient: non-JSON message: %s", raw[:80])
            return

        action = msg.get("action")

        if action == "requireInitialData":
            await self._do_auth()

        elif action == "initialData":
            if msg.get("success"):
                logger.info("BroadcastPlusAsyncClient: authenticated.")
                self._auth_ok = True
                self._reconnect_count = 0
                await self._resubscribe_all()
            else:
                logger.error(
                    "BroadcastPlusAsyncClient: initialData failed — refreshing token."
                )
                try:
                    self._pending_token = await asyncio.to_thread(refresh_plus_token)
                    await self._do_auth()
                except BroadcastPlusAuthError as exc:
                    logger.error(
                        "BroadcastPlusAsyncClient: auth refresh failed: %s", exc
                    )
                    await self.stop()

        elif action == "streamQuote":
            data = msg.get("data") or {}
            if not data:
                return
            cod = data.get("COD") or data.get("ATIVO") or data.get("CODG", "")
            # Values arrive BR-formatted ("42,08", "0,19%"); parse numerics to
            # float, leave codes/names/times as strings.
            data = {
                k: parse_br_number(v) if isinstance(v, str) else v
                for k, v in data.items()
            }
            cb = self._subscriptions.get(cod) or self._global_callback
            if cb:
                try:
                    result = cb(data)
                    if inspect.isawaitable(result):
                        await result
                except Exception as exc:
                    logger.warning("BroadcastPlusAsyncClient: callback raised: %s", exc)

        elif action == "streamMarket":
            data = msg.get("data") or {}
            if not data:
                return
            rows = data.get("rows")
            if isinstance(rows, list):
                # Cells arrive BR-formatted ("0,11", "17.499"); parse numerics
                # to float, leave codes/times as strings.
                data = {
                    **data,
                    "rows": [
                        [parse_br_number(c) if isinstance(c, str) else c for c in row]
                        for row in rows
                    ],
                }
            cb = self._market_callback
            if cb:
                try:
                    result = cb(data)
                    if inspect.isawaitable(result):
                        await result
                except Exception as exc:
                    logger.warning(
                        "BroadcastPlusAsyncClient: market callback raised: %s", exc
                    )

        elif action == "requireUpdateToken":
            logger.info("BroadcastPlusAsyncClient: token refresh requested by server.")
            try:
                new_token = await asyncio.to_thread(refresh_plus_token)
                await self._send({"action": "updateToken", "token": new_token})
            except BroadcastPlusAuthError as exc:
                logger.error("BroadcastPlusAsyncClient: token refresh failed: %s", exc)
                await self.stop()

        elif action == "updateToken":
            if not msg.get("success"):
                logger.warning(
                    "BroadcastPlusAsyncClient: updateToken rejected — reconnecting."
                )
                if self._ws is not None:
                    await self._ws.close()  # _run_loop reconnects with backoff

        elif action == "pong":
            pass  # keep-alive acknowledged

        elif action == "ping":
            await self._send({"action": "pong"})

        else:
            logger.debug("BroadcastPlusAsyncClient: unhandled action %r", action)

    async def _do_auth(self) -> None:
        """Send the initialData handshake with the current JWT."""
        fields = _DEFAULT_FIELDS + [
            f for f in self._extra_fields if f not in _DEFAULT_FIELDS
        ]
        await self._send(
            {"action": "initialData", "token": self._pending_token, "fields": fields}
        )

    async def _resubscribe_all(self) -> None:
        """Re-send startStreamQuote for all active subscriptions after (re)auth."""
        tickers = list(self._subscriptions.keys())
        if tickers:
            await self._send({"action": "startStreamQuote", "symbols": tickers})
        if self._extra_fields:
            await self._send(
                {"action": "addFields", "fields": self._extra_fields, "symbols": None}
            )
        for mid in list(self._market_ids):
            await self._send(
                {"action": "startStreamMarket", "id": mid, "requestId": str(mid)}
            )

    async def _send(self, payload: dict[str, Any]) -> None:
        """Serialize and send a JSON message. Silently ignores closed connections."""
        if self._ws is None:
            return
        try:
            await self._ws.send(json.dumps(payload))
        except Exception as exc:
            logger.debug("BroadcastPlusAsyncClient: send failed: %s", exc)

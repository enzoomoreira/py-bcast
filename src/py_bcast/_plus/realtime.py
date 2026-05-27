"""Real-time market data via Broadcast+ WebSocket.

Provides BroadcastPlusClient — a WebSocket-based streaming client that
connects to wss://svc.aebroadcast.com.br:44761/stock/ws and pushes live
quote updates to user-supplied callbacks.

No local terminal required if BROADCAST_PLUS_TOKEN is set or credentials
are configured via configure(plus_login=..., plus_password=...).

Protocol (from Broadcast+.exe v7.4.4 app.asar reverse engineering):

  1. Connect (no auth headers — JWT sent via message)
  2. Server  → {"action": "requireInitialData"}
  3. Client  → {"action": "initialData", "token": "<JWT>", "fields": [...]}
  4. Server  → {"action": "initialData", "success": true}
  5. Client  → {"action": "startStreamQuote", "symbols": ["PETR4"]}
  6. Server  → {"action": "streamQuote", "data": {...}} (on each tick)
  7. Client  → {"action": "ping"}  (every 10s)
  8. Server  → {"action": "pong"}
  9. Server  → {"action": "requireUpdateToken"}  (when token near expiry)
  10. Client → {"action": "updateToken", "token": "<new_JWT>"}
"""

from __future__ import annotations

import json
import threading
from collections.abc import Callable
from typing import Any

import websocket

from .._core.constants import PLUS_VERSION, PLUS_WS_URL
from .._core.exceptions import BroadcastPlusAuthError
from .._core.logging import get_logger
from .._core.normalize import ensure_list
from .session import get_plus_token, refresh_plus_token

logger = get_logger(__name__)

# Default fields requested in the initialData handshake (from app.asar)
_DEFAULT_FIELDS = [
    "COD",
    "ULT",
    "VAR",
    "ABE",
    "MAX",
    "MIN",
    "HOR",
    "NOM",
    "DSC",
    "TND",
    "ATZ",
    "EST",
    "PTR",
]
_WS_URL = f"{PLUS_WS_URL}/stock/ws"
_PING_INTERVAL = 10  # seconds
_MAX_RECONNECTS = 3
_RECONNECT_DELAY = 2  # seconds (doubled each attempt)


class BroadcastPlusClient:
    """Real-time market data streaming via Broadcast+ WebSocket.

    Connects to svc.aebroadcast.com.br and pushes live quote updates to
    user-supplied callbacks. Authentication is handled automatically via
    the standard Plus auth chain (env var / memory scan / ECDH login).

    Mirrors the interface of BroadcastClient where practical, but uses
    a dict-per-tick callback instead of per-field callbacks.

    Usage (context manager, recommended)::

        def on_quote(data: dict) -> None:
            print(data["COD"], data["ULT"], data["VAR"])

        with BroadcastPlusClient() as client:
            client.subscribe(["PETR4", "VALE3"], callback=on_quote)
            client.run(duration=60)  # blocks for 60 seconds

    Usage (manual)::

        client = BroadcastPlusClient()
        client.subscribe(["PETR4"], callback=on_quote)
        t = client.run_async()
        time.sleep(30)
        client.stop()
        t.join()
    """

    def __init__(self) -> None:
        self._ws: websocket.WebSocketApp | None = None
        self._ws_thread: threading.Thread | None = None
        self._ping_thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._auth_event = threading.Event()  # set when initialData succeeds
        self._auth_ok = False

        # subscription state (ticker -> callback)
        self._subscriptions: dict[str, Callable[[dict[str, Any]], None]] = {}
        self._global_callback: Callable[[dict[str, Any]], None] | None = None
        self._extra_fields: list[str] = []
        self._lock = threading.Lock()

        self._reconnect_count = 0

    # ── Context manager ───────────────────────────────────────────────────────

    def __enter__(self) -> BroadcastPlusClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.stop()

    # ── Public API ────────────────────────────────────────────────────────────

    def subscribe(
        self,
        tickers: str | list[str],
        callback: Callable[[dict[str, Any]], None],
        fields: list[str] | None = None,
    ) -> None:
        """Subscribe to real-time quote updates for one or more tickers.

        Can be called before or after run()/run_async(). If called while the
        stream is active, the subscription is sent immediately.

        Args:
            tickers:  Single ticker or list (e.g. "PETR4" or ["PETR4","VALE3"]).
            callback: Called on each quote update with a dict of field values.
                      Signature: ``callback(data: dict) -> None``
                      Keys include: COD, ULT, VAR, ABE, MAX, MIN, HOR, NOM, etc.
            fields:   Extra WS fields to request beyond the default set. None
                      means use the default 13 fields from the Broadcast+ app.
        """
        tickers_list = ensure_list(tickers)
        tickers_upper = [t.strip().upper() for t in tickers_list]

        with self._lock:
            for t in tickers_upper:
                self._subscriptions[t] = callback
            self._global_callback = callback  # last wins for mixed-ticker events
            if fields:
                self._extra_fields = list(set(self._extra_fields + fields))

        if self._auth_ok and self._ws:
            self._send({"action": "startStreamQuote", "symbols": tickers_upper})
            if fields:
                self._send({"action": "addFields", "fields": fields, "symbols": None})

    def unsubscribe(self, tickers: str | list[str]) -> None:
        """Unsubscribe from quote updates for the given tickers."""
        tickers_list = [t.strip().upper() for t in ensure_list(tickers)]
        with self._lock:
            for t in tickers_list:
                self._subscriptions.pop(t, None)
        if self._auth_ok and self._ws:
            self._send({"action": "stopStreamQuote", "symbols": tickers_list})

    def unsubscribe_all(self) -> None:
        """Unsubscribe from all active subscriptions."""
        with self._lock:
            tickers = list(self._subscriptions.keys())
            self._subscriptions.clear()
        if tickers and self._auth_ok and self._ws:
            self._send({"action": "stopStreamQuote", "symbols": tickers})

    def run(self, duration: float | None = None) -> None:
        """Start streaming and block until duration seconds or stop() is called.

        Args:
            duration: Seconds to run. None means run indefinitely until stop().
        """
        self._stop_event.clear()
        self._start_ws()
        try:
            self._stop_event.wait(timeout=duration)
        finally:
            self.stop()

    def run_async(self, duration: float | None = None) -> threading.Thread:
        """Start streaming in a background thread. Returns the thread.

        Args:
            duration: Seconds to run. None means run until stop() is called.

        Returns:
            The background thread (already started). Call ``.join()`` to wait.
        """
        self._stop_event.clear()
        self._start_ws()
        t = threading.Thread(
            target=self._stop_event.wait, args=(duration,), daemon=True
        )
        t.start()
        return t

    def stop(self) -> None:
        """Stop streaming and close the WebSocket connection."""
        self._stop_event.set()
        if self._ws:
            try:
                self._ws.close()
            except Exception:
                pass
        if self._ws_thread and self._ws_thread.is_alive():
            self._ws_thread.join(timeout=5)
        self._ws = None
        self._auth_ok = False
        self._auth_event.clear()

    # ── Internal — WebSocket lifecycle ────────────────────────────────────────

    def _start_ws(self) -> None:
        """Open the WebSocket connection in a daemon thread."""
        token = get_plus_token()
        ws = websocket.WebSocketApp(
            _WS_URL,
            header={
                "x-version": PLUS_VERSION,
                "Origin": "https://svc.aebroadcast.com.br",
            },
            on_open=self._on_open,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close,
        )
        # Store current token so _on_open can use it
        self._pending_token = token
        self._ws = ws

        self._ws_thread = threading.Thread(
            target=ws.run_forever,
            kwargs={
                "ping_interval": 0,
                "sslopt": {"check_hostname": False, "cert_reqs": 0},
            },
            daemon=True,
        )
        self._ws_thread.start()

    def _on_open(self, ws: websocket.WebSocketApp) -> None:
        logger.debug("BroadcastPlusClient: WebSocket opened.")
        # Server will immediately send requireInitialData; handled in _on_message

    def _on_message(self, ws: websocket.WebSocketApp, raw: str) -> None:
        try:
            msg = json.loads(raw)
        except json.JSONDecodeError:
            logger.warning("BroadcastPlusClient: non-JSON message: %s", raw[:80])
            return

        action = msg.get("action")

        if action == "requireInitialData":
            self._do_auth(ws)

        elif action == "initialData":
            if msg.get("success"):
                logger.info("BroadcastPlusClient: authenticated.")
                self._auth_ok = True
                self._auth_event.set()
                self._reconnect_count = 0
                self._resubscribe_all()
                self._start_ping()
            else:
                logger.error(
                    "BroadcastPlusClient: initialData failed — refreshing token."
                )
                try:
                    self._pending_token = refresh_plus_token()
                    self._do_auth(ws)
                except BroadcastPlusAuthError as exc:
                    logger.error("BroadcastPlusClient: auth refresh failed: %s", exc)
                    self.stop()

        elif action == "streamQuote":
            data = msg.get("data") or {}
            if not data:
                return
            cod = data.get("COD") or data.get("ATIVO") or data.get("CODG", "")
            with self._lock:
                cb = self._subscriptions.get(cod) or self._global_callback
            if cb:
                try:
                    cb(data)
                except Exception as exc:
                    logger.warning("BroadcastPlusClient: callback raised: %s", exc)

        elif action == "requireUpdateToken":
            logger.info("BroadcastPlusClient: token refresh requested by server.")
            try:
                new_token = refresh_plus_token()
                self._send({"action": "updateToken", "token": new_token})
            except BroadcastPlusAuthError as exc:
                logger.error("BroadcastPlusClient: token refresh failed: %s", exc)
                self.stop()

        elif action == "updateToken":
            if not msg.get("success"):
                logger.warning(
                    "BroadcastPlusClient: updateToken rejected — reconnecting."
                )
                self._reconnect()

        elif action == "pong":
            pass  # keep-alive acknowledged

        elif action == "ping":
            self._send({"action": "pong"})

        else:
            logger.debug("BroadcastPlusClient: unhandled action %r", action)

    def _on_error(self, ws: websocket.WebSocketApp, error: Exception) -> None:
        logger.warning("BroadcastPlusClient: WebSocket error: %s", error)

    def _on_close(
        self,
        ws: websocket.WebSocketApp,
        close_status_code: int | None,
        close_msg: str | None,
    ) -> None:
        logger.info(
            "BroadcastPlusClient: connection closed (code=%s msg=%s).",
            close_status_code,
            close_msg,
        )
        self._auth_ok = False
        self._auth_event.clear()

        if not self._stop_event.is_set() and self._reconnect_count < _MAX_RECONNECTS:
            delay = _RECONNECT_DELAY * (2**self._reconnect_count)
            self._reconnect_count += 1
            logger.info(
                "BroadcastPlusClient: reconnecting in %.1fs (attempt %d/%d).",
                delay,
                self._reconnect_count,
                _MAX_RECONNECTS,
            )
            threading.Timer(delay, self._reconnect).start()
        elif not self._stop_event.is_set():
            logger.error("BroadcastPlusClient: max reconnect attempts reached.")
            self._stop_event.set()

    def _reconnect(self) -> None:
        if self._stop_event.is_set():
            return
        if self._ws:
            try:
                self._ws.close()
            except Exception:
                pass
        self._start_ws()

    # ── Internal — protocol helpers ───────────────────────────────────────────

    def _do_auth(self, ws: websocket.WebSocketApp) -> None:
        """Send the initialData handshake with the current JWT."""
        fields = _DEFAULT_FIELDS + [
            f for f in self._extra_fields if f not in _DEFAULT_FIELDS
        ]
        self._send(
            {"action": "initialData", "token": self._pending_token, "fields": fields},
            ws=ws,
        )

    def _resubscribe_all(self) -> None:
        """Re-send startStreamQuote for all active subscriptions after reconnect."""
        with self._lock:
            tickers = list(self._subscriptions.keys())
        if tickers:
            self._send({"action": "startStreamQuote", "symbols": tickers})
        if self._extra_fields:
            self._send(
                {"action": "addFields", "fields": self._extra_fields, "symbols": None}
            )

    def _send(
        self,
        payload: dict[str, Any],
        ws: websocket.WebSocketApp | None = None,
    ) -> None:
        """Serialize and send a JSON message. Silently ignores closed connections."""
        target = ws or self._ws
        if target is None:
            return
        try:
            target.send(json.dumps(payload))
        except Exception as exc:
            logger.debug("BroadcastPlusClient: send failed: %s", exc)

    def _start_ping(self) -> None:
        """Start the keep-alive ping thread if not already running."""
        if self._ping_thread and self._ping_thread.is_alive():
            return

        def _ping_loop() -> None:
            while not self._stop_event.wait(timeout=_PING_INTERVAL):
                if self._auth_ok:
                    self._send({"action": "ping"})

        self._ping_thread = threading.Thread(target=_ping_loop, daemon=True)
        self._ping_thread.start()

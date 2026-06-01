"""DDE client for real-time and snapshot market data."""

from __future__ import annotations

import ctypes
import ctypes.wintypes
import threading
import time
from dataclasses import dataclass
from typing import Callable, Optional

# win32ui must be imported before dde: importing it initializes the MFC runtime
# that the dde module requires. It is never referenced by name, hence the noqa.
import win32ui  # noqa: F401
import dde

from .._core.constants import (
    DDE_SERVICE,
    DDE_TOPIC_REALTIME,
    DDE_TOPIC_SNAPSHOT,
    SNAPSHOT_FIELDS,
    DMLERR_NAMES,
)
from .._core.exceptions import DDEError, DDEAdviseError
from .._core.logging import get_logger
from .._core.normalize import parse_br_number
from .._legacy.dde import (
    APPCMD_CLIENTONLY,
    CF_TEXT,
    CP_WINUNICODE,
    DDECALLBACK,
    HSZ,
    XTYP_ADVDATA,
    XTYP_ADVSTART,
    XTYP_ADVSTOP,
    DdeClientTransaction,
    DdeConnect,
    DdeCreateStringHandleW,
    DdeDisconnect,
    DdeFreeStringHandle,
    DdeGetData,
    DdeGetLastError,
    DdeInitializeW,
    DdeQueryStringW,
    DdeUninitialize,
    DispatchMessageW,
    PeekMessageW,
    TranslateMessage,
)

logger = get_logger(__name__)

SubscriptionCallback = Callable[[str, str, str], None]  # (ticker, field, value)


@dataclass
class Subscription:
    ticker: str
    field: str
    callback: SubscriptionCallback


class BroadcastClient:
    """
    Python client for Broadcast terminal data via DDE.

    Supports two modes:
    1. Request mode (pywin32 dde) — simple one-shot queries
    2. Streaming mode (DDEML ctypes) — real-time push via DDE Advise
    """

    def __init__(self, client_name: str = "PyBC"):
        self._client_name = client_name
        self._server = None
        self._conv_cot = None
        self._conv_ativo = None
        self._streaming = False
        self._inst_id = None
        self._h_conv = None
        self._subscriptions: dict[str, Subscription] = {}
        self._lock = threading.Lock()
        self._stop_event = threading.Event()

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *args):
        self.disconnect()

    def connect(self):
        """Establish DDE connections for request mode."""
        self._server = dde.CreateServer()
        self._server.Create(self._client_name)
        self._conv_cot = dde.CreateConversation(self._server)
        self._conv_cot.ConnectTo(DDE_SERVICE, DDE_TOPIC_REALTIME)

    def disconnect(self):
        """Clean up all DDE connections."""
        if self._streaming:
            self.unsubscribe_all()
        if self._server:
            self._server.Shutdown()
            self._server = None
            self._conv_cot = None
            self._conv_ativo = None

    # ─── Request mode (one-shot) ─────────────────────────────────────────────

    def request(
        self, ticker: str, fields: str | list[str]
    ) -> str | float | None | dict[str, str | float | None]:
        """
        Request current value(s) for a ticker.

        Args:
            ticker: Asset code (e.g. "PETR4", "IBOV", "USDBRL")
            fields: Single field name or list of field names

        Returns:
            Single value if a single field, dict keyed by field if a list.
            Brazilian-formatted numbers (prices, percentages) are parsed to
            float; bare counts, codes, and text stay strings. Returns None for
            fields that return N/A or NOK.
        """
        if isinstance(fields, str):
            return self._request_single(ticker, fields)

        result: dict[str, str | float | None] = {}
        for f in fields:
            result[f] = self._request_single(ticker, f)
        return result

    def _request_single(self, ticker: str, field: str) -> str | float | None:
        item = f"{ticker}.{field}"
        try:
            data = self._conv_cot.Request(item)
        except dde.error as exc:
            logger.debug("DDE request failed for %s: %s", item, exc)
            return None
        if data and "NOK" not in data and data != "N/A" and data.strip():
            return parse_br_number(data.strip())
        return None

    def snapshot(self, ticker: str) -> dict[str, str]:
        """
        Get a full snapshot of all available fields for a ticker.
        Uses the ATIVO topic which returns all fields in one call.

        Returns:
            Dict mapping field names to values. Empty fields excluded.
        """
        if self._conv_ativo is None:
            self._conv_ativo = dde.CreateConversation(self._server)
            self._conv_ativo.ConnectTo(DDE_SERVICE, DDE_TOPIC_SNAPSHOT)

        try:
            raw = self._conv_ativo.Request(ticker)
        except dde.error as exc:
            logger.debug("DDE snapshot failed for %s: %s", ticker, exc)
            return {}
        if not raw or "N/A" == raw.strip():
            return {}

        parts = raw.split("\t")
        result = {}
        for i, val in enumerate(parts):
            if val.strip():
                name = SNAPSHOT_FIELDS[i] if i < len(SNAPSHOT_FIELDS) else f"F{i + 1}"
                result[name] = val
        return result

    # ─── Streaming mode (DDE Advise) ────────────────────────────────────────

    def subscribe(
        self,
        tickers: str | list[str],
        fields: str | list[str],
        callback: SubscriptionCallback,
        skip_unavailable: bool = False,
    ) -> list[DDEAdviseError]:
        """
        Subscribe to real-time streaming updates.

        Args:
            tickers: Single ticker or list of tickers
            fields: Single field or list of fields
            callback: Function called with (ticker, field, value) on each update
            skip_unavailable: If True, advise failures (e.g. invalid tickers)
                are collected and returned instead of raising. If False (default),
                the first failure raises immediately.

        Returns:
            List of DDEAdviseError for items that could not be subscribed
            (empty when all succeed or when skip_unavailable=False).

        Raises:
            DDEAdviseError: When an advise transaction fails and skip_unavailable=False.
        """
        if isinstance(tickers, str):
            tickers = [tickers]
        if isinstance(fields, str):
            fields = [fields]

        if not self._streaming:
            self._init_streaming()

        skipped: list[DDEAdviseError] = []
        for ticker in tickers:
            for fld in fields:
                item = f"{ticker}.{fld}"
                self._subscriptions[item] = Subscription(ticker, fld, callback)
                h_item = self._make_str(item)
                result = DdeClientTransaction(
                    None,
                    0,
                    self._h_conv,
                    h_item,
                    CF_TEXT,
                    XTYP_ADVSTART,
                    5000,
                    None,
                )
                DdeFreeStringHandle(self._inst_id.value, h_item)
                if not result:
                    err = DdeGetLastError(self._inst_id.value)
                    del self._subscriptions[item]
                    err_name = DMLERR_NAMES.get(err, f"0x{err:04X}")
                    exc = DDEAdviseError(
                        f"Advise failed for {item} (error={err}, {err_name})",
                        item=item,
                        ticker=ticker,
                        field=fld,
                        error_code=err,
                    )
                    if skip_unavailable:
                        skipped.append(exc)
                        logger.warning(
                            "Advise skipped: %s (error=%d, %s)", item, err, err_name
                        )
                    else:
                        raise exc
        return skipped

    def unsubscribe(self, tickers: str | list[str], fields: str | list[str]):
        """Stop streaming for specified tickers/fields."""
        if isinstance(tickers, str):
            tickers = [tickers]
        if isinstance(fields, str):
            fields = [fields]

        for ticker in tickers:
            for fld in fields:
                item = f"{ticker}.{fld}"
                if item in self._subscriptions:
                    h_item = self._make_str(item)
                    DdeClientTransaction(
                        None,
                        0,
                        self._h_conv,
                        h_item,
                        CF_TEXT,
                        XTYP_ADVSTOP,
                        2000,
                        None,
                    )
                    DdeFreeStringHandle(self._inst_id.value, h_item)
                    del self._subscriptions[item]

    def unsubscribe_all(self):
        """Stop all streaming subscriptions and clean up DDEML."""
        if not self._streaming:
            return
        for item in list(self._subscriptions.keys()):
            h_item = self._make_str(item)
            DdeClientTransaction(
                None,
                0,
                self._h_conv,
                h_item,
                CF_TEXT,
                XTYP_ADVSTOP,
                2000,
                None,
            )
            DdeFreeStringHandle(self._inst_id.value, h_item)
        self._subscriptions.clear()
        if self._h_conv:
            DdeDisconnect(self._h_conv)
        if self._inst_id:
            DdeUninitialize(self._inst_id.value)
        self._streaming = False
        self._h_conv = None
        self._inst_id = None

    def run(self, duration: Optional[float] = None):
        """
        Run the Windows message pump to receive streaming updates.
        Blocks until duration expires or stop() is called.

        Args:
            duration: Seconds to run (None = run until stop() is called)
        """
        self._stop_event.clear()
        MSG = ctypes.wintypes.MSG()
        start = time.time()

        while not self._stop_event.is_set():
            if duration and (time.time() - start >= duration):
                break
            while PeekMessageW(ctypes.byref(MSG), 0, 0, 0, 1):
                TranslateMessage(ctypes.byref(MSG))
                DispatchMessageW(ctypes.byref(MSG))
            time.sleep(0.01)

    def run_async(self, duration: Optional[float] = None) -> threading.Thread:
        """Run the message pump in a background thread. Returns the thread."""
        t = threading.Thread(target=self.run, args=(duration,), daemon=True)
        t.start()
        return t

    def stop(self):
        """Signal the message pump to stop."""
        self._stop_event.set()

    # ─── Internal ────────────────────────────────────────────────────────────

    def _init_streaming(self):
        """Initialize DDEML for streaming callbacks."""
        self._inst_id = ctypes.c_ulong(0)

        @DDECALLBACK
        def callback(uType, uFmt, hConv, hsz1, hsz2, hData, dwData1, dwData2):
            if uType == XTYP_ADVDATA:
                buf = ctypes.create_unicode_buffer(256)
                DdeQueryStringW(self._inst_id.value, hsz2, buf, 256, CP_WINUNICODE)
                item_name = buf.value

                data_str = ""
                if hData:
                    size = DdeGetData(hData, None, 0, 0)
                    if size > 0:
                        data_buf = ctypes.create_string_buffer(size)
                        DdeGetData(hData, data_buf, size, 0)
                        data_str = data_buf.value.decode(
                            "latin-1", errors="replace"
                        ).strip("\x00")

                sub = self._subscriptions.get(item_name)
                if sub:
                    try:
                        sub.callback(sub.ticker, sub.field, data_str)
                    except Exception as exc:
                        logger.warning(
                            "Subscription callback error for %s: %s", item_name, exc
                        )
                return 1
            return 0

        self._callback = callback  # prevent GC

        rc = DdeInitializeW(
            ctypes.byref(self._inst_id),
            self._callback,
            APPCMD_CLIENTONLY,
            0,
        )
        if rc != 0:
            raise DDEError(f"DdeInitialize failed: {rc}")

        h_svc = self._make_str(DDE_SERVICE)
        h_top = self._make_str(DDE_TOPIC_REALTIME)
        self._h_conv = DdeConnect(self._inst_id.value, h_svc, h_top, None)
        DdeFreeStringHandle(self._inst_id.value, h_svc)
        DdeFreeStringHandle(self._inst_id.value, h_top)

        if not self._h_conv:
            raise DDEError("DdeConnect for streaming failed")

        self._streaming = True
        logger.info("DDE streaming initialized successfully")

    def _make_str(self, text: str) -> HSZ:
        return DdeCreateStringHandleW(self._inst_id.value, text, CP_WINUNICODE)


# ─────────────────────────────────────────────────────────────────────────────
# Convenience functions
# ─────────────────────────────────────────────────────────────────────────────


def bdp(
    ticker: str | list[str],
    fields: str | list[str],
) -> (
    str
    | float
    | None
    | dict[str, str | float | None]
    | dict[str, str | float | None | dict[str, str | float | None]]
):
    """Bloomberg-style bdp (Broadcast Data Point). One-shot DDE request.

    Polymorphic on both axes:
        - one ticker, one field   -> a scalar value
        - one ticker, many fields -> dict keyed by field
        - many tickers            -> dict keyed by ticker, each value following
                                     the single-ticker rules above

    Numeric values (prices, percentages) come back as float; counts, codes,
    and text stay strings. None for unavailable fields.

    Example:
        >>> bdp("PETR4", "ULT")                  # 42.46
        >>> bdp("PETR4", ["ULT", "VAR"])         # {"ULT": 42.46, "VAR": 0.81}
        >>> bdp(["PETR4", "VALE3"], "ULT")       # {"PETR4": 42.46, "VALE3": 61.2}
    """
    with BroadcastClient("PyBDP") as bc:
        if isinstance(ticker, str):
            return bc.request(ticker, fields)
        return {t: bc.request(t, fields) for t in ticker}

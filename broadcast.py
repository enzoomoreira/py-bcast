"""
broadcast.py
Python client for AE Broadcast terminal market data via Windows DDE.

Provides a clean, blpapi-like interface for:
- One-shot reference data requests (like bdp/ReferenceDataRequest)
- Real-time streaming subscriptions (like Subscribe)
- Full ticker snapshots

Usage:
    from broadcast import BroadcastClient

    with BroadcastClient() as bc:
        # One-shot request
        price = bc.request("PETR4", "ULT")

        # Multiple fields
        data = bc.request("PETR4", ["ULT", "VAR", "MAX", "MIN", "FEC"])

        # Full snapshot (all available fields)
        snap = bc.snapshot("PETR4")

        # Real-time streaming
        bc.subscribe(["PETR4", "VALE3"], ["ULT", "VAR", "NEG"],
                     callback=lambda ticker, field, value: print(f"{ticker}.{field} = {value}"))
        bc.run(duration=60)  # pump messages for 60 seconds
"""
import ctypes
import ctypes.wintypes
from ctypes import wintypes
import threading
import time
from typing import Callable, Optional
from dataclasses import dataclass, field
from contextlib import contextmanager

import win32ui
import dde


# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────

DDE_SERVICE = "BC"
DDE_TOPIC_REALTIME = "COT"
DDE_TOPIC_SNAPSHOT = "ATIVO"

FIELDS_REALTIME = [
    "ATIVO", "ULT", "HOR", "VAR", "MAX", "MIN", "ABE", "FEC",
    "OCP", "OVD", "NEG", "QUL", "MED", "VTT", "QTT", "DAT",
    "QCP", "QVD", "EST", "NOM", "SIT", "LOT",
]

# ATIVO topic returns 56 tab-separated columns in this order
SNAPSHOT_FIELDS = [
    "ATIVO", "ULT", "HOR", "VAR", "MAX", "MIN", "FEC", "ABE",
    "OCP", "OVD", "NEG", "QUL", "MED", "QCP_TOTAL", "QVD_TOTAL", "QTT",
    "SINAL", "EST", "ULT_C1", "HOR_C1", "QUL_C1", "ULT_V1", "HOR_V1", "QUL_V1",
    "ULT_C2", "HOR_C2", "QUL_C2", "ULT_V2", "HOR_V2", "QUL_V2",
    "SIT", "NOM", "COD_ISIN", "DAT", "F35", "F36", "LOTE_PAD", "DEC",
    "QUL_MIN", "QUL_MAX", "LOT", "F42", "F43", "FEC_ANT", "DAT_ANT",
    "F46", "F47", "AFTER_MKT", "VOL_FIN", "F50", "DAT_HOJ", "F52",
    "F53", "F54", "ISIN", "F56",
]


# ─────────────────────────────────────────────────────────────────────────────
# DDE DDEML low-level (for Advise streaming)
# ─────────────────────────────────────────────────────────────────────────────

_user32 = ctypes.windll.user32

CP_WINUNICODE = 1200
CF_TEXT = 1
XTYP_ADVDATA = 0x4010
XTYP_ADVSTART = 0x1030
XTYP_ADVSTOP = 0x1040
XTYP_DISCONNECT = 0x00C2
APPCMD_CLIENTONLY = 0x00000010

HDDEDATA = ctypes.c_ssize_t
HCONV = ctypes.c_ssize_t
HSZ = ctypes.c_ssize_t

_user32.DdeGetData.argtypes = [HDDEDATA, ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD]
_user32.DdeGetData.restype = wintypes.DWORD
_user32.DdeQueryStringW.argtypes = [wintypes.DWORD, HSZ, ctypes.c_wchar_p, wintypes.DWORD, ctypes.c_int]
_user32.DdeQueryStringW.restype = wintypes.DWORD
_user32.DdeCreateStringHandleW.restype = HSZ
_user32.DdeCreateStringHandleW.argtypes = [wintypes.DWORD, ctypes.c_wchar_p, ctypes.c_int]
_user32.DdeConnect.restype = HCONV
_user32.DdeConnect.argtypes = [wintypes.DWORD, HSZ, HSZ, ctypes.c_void_p]
_user32.DdeClientTransaction.restype = HDDEDATA
_user32.DdeClientTransaction.argtypes = [
    ctypes.c_void_p, wintypes.DWORD, HCONV, HSZ,
    wintypes.UINT, wintypes.UINT, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)
]
_user32.DdeFreeStringHandle.argtypes = [wintypes.DWORD, HSZ]
_user32.DdeDisconnect.argtypes = [HCONV]

DDECALLBACK = ctypes.WINFUNCTYPE(
    ctypes.c_ssize_t,
    ctypes.c_uint, ctypes.c_uint,
    ctypes.c_ssize_t, ctypes.c_ssize_t, ctypes.c_ssize_t,
    ctypes.c_ssize_t, ctypes.c_ssize_t, ctypes.c_ssize_t,
)


# ─────────────────────────────────────────────────────────────────────────────
# Client
# ─────────────────────────────────────────────────────────────────────────────

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

    def request(self, ticker: str, fields: str | list[str]) -> str | dict[str, str]:
        """
        Request current value(s) for a ticker.

        Args:
            ticker: Asset code (e.g. "PETR4", "IBOV", "USDBRL")
            fields: Single field name or list of field names

        Returns:
            String value if single field, dict if multiple fields.
            Returns None for fields that return N/A or NOK.
        """
        if isinstance(fields, str):
            return self._request_single(ticker, fields)

        result = {}
        for f in fields:
            val = self._request_single(ticker, f)
            result[f] = val
        return result

    def _request_single(self, ticker: str, field: str) -> Optional[str]:
        item = f"{ticker}.{field}"
        try:
            data = self._conv_cot.Request(item)
            if data and "NOK" not in data and data != "N/A" and data.strip():
                return data.strip()
            return None
        except Exception:
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
            if not raw or "N/A" == raw.strip():
                return {}
        except Exception:
            return {}

        parts = raw.split('\t')
        result = {}
        for i, val in enumerate(parts):
            if val.strip():
                name = SNAPSHOT_FIELDS[i] if i < len(SNAPSHOT_FIELDS) else f"F{i+1}"
                result[name] = val
        return result

    # ─── Streaming mode (DDE Advise) ────────────────────────────────────────

    def subscribe(
        self,
        tickers: str | list[str],
        fields: str | list[str],
        callback: SubscriptionCallback,
    ):
        """
        Subscribe to real-time streaming updates.

        Args:
            tickers: Single ticker or list of tickers
            fields: Single field or list of fields
            callback: Function called with (ticker, field, value) on each update
        """
        if isinstance(tickers, str):
            tickers = [tickers]
        if isinstance(fields, str):
            fields = [fields]

        if not self._streaming:
            self._init_streaming()

        for ticker in tickers:
            for fld in fields:
                item = f"{ticker}.{fld}"
                self._subscriptions[item] = Subscription(ticker, fld, callback)
                h_item = self._make_str(item)
                result = _user32.DdeClientTransaction(
                    None, 0, self._h_conv, h_item, CF_TEXT,
                    XTYP_ADVSTART, 5000, None
                )
                _user32.DdeFreeStringHandle(self._inst_id.value, h_item)
                if not result:
                    err = _user32.DdeGetLastError(self._inst_id.value)
                    raise RuntimeError(f"Advise failed for {item} (error={err})")

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
                    _user32.DdeClientTransaction(
                        None, 0, self._h_conv, h_item, CF_TEXT,
                        XTYP_ADVSTOP, 2000, None
                    )
                    _user32.DdeFreeStringHandle(self._inst_id.value, h_item)
                    del self._subscriptions[item]

    def unsubscribe_all(self):
        """Stop all streaming subscriptions and clean up DDEML."""
        if not self._streaming:
            return
        for item in list(self._subscriptions.keys()):
            h_item = self._make_str(item)
            _user32.DdeClientTransaction(
                None, 0, self._h_conv, h_item, CF_TEXT,
                XTYP_ADVSTOP, 2000, None
            )
            _user32.DdeFreeStringHandle(self._inst_id.value, h_item)
        self._subscriptions.clear()
        if self._h_conv:
            _user32.DdeDisconnect(self._h_conv)
        if self._inst_id:
            _user32.DdeUninitialize(self._inst_id.value)
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
            while _user32.PeekMessageW(ctypes.byref(MSG), 0, 0, 0, 1):
                _user32.TranslateMessage(ctypes.byref(MSG))
                _user32.DispatchMessageW(ctypes.byref(MSG))
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
                _user32.DdeQueryStringW(self._inst_id.value, hsz2, buf, 256, CP_WINUNICODE)
                item_name = buf.value

                data_str = ""
                if hData:
                    size = _user32.DdeGetData(hData, None, 0, 0)
                    if size > 0:
                        data_buf = ctypes.create_string_buffer(size)
                        _user32.DdeGetData(hData, data_buf, size, 0)
                        data_str = data_buf.value.decode('latin-1', errors='replace').strip('\x00')

                sub = self._subscriptions.get(item_name)
                if sub:
                    try:
                        sub.callback(sub.ticker, sub.field, data_str)
                    except Exception:
                        pass
                return 1
            return 0

        # Must keep reference to prevent GC
        self._callback = callback

        rc = _user32.DdeInitializeW(
            ctypes.byref(self._inst_id), self._callback, APPCMD_CLIENTONLY, 0
        )
        if rc != 0:
            raise RuntimeError(f"DdeInitialize failed: {rc}")

        h_svc = self._make_str(DDE_SERVICE)
        h_top = self._make_str(DDE_TOPIC_REALTIME)
        self._h_conv = _user32.DdeConnect(self._inst_id.value, h_svc, h_top, None)
        _user32.DdeFreeStringHandle(self._inst_id.value, h_svc)
        _user32.DdeFreeStringHandle(self._inst_id.value, h_top)

        if not self._h_conv:
            raise RuntimeError("DdeConnect for streaming failed")

        self._streaming = True

    def _make_str(self, text: str) -> HSZ:
        return _user32.DdeCreateStringHandleW(self._inst_id.value, text, CP_WINUNICODE)


# ─────────────────────────────────────────────────────────────────────────────
# Convenience functions (module-level)
# ─────────────────────────────────────────────────────────────────────────────

def bdp(ticker: str, fields: str | list[str]) -> str | dict[str, str]:
    """Bloomberg-style bdp (Broadcast Data Point). One-shot request."""
    with BroadcastClient("PyBDP") as bc:
        return bc.request(ticker, fields)


def bdps(tickers: list[str], fields: list[str]) -> dict[str, dict[str, str]]:
    """Batch request: multiple tickers, multiple fields."""
    with BroadcastClient("PyBDPS") as bc:
        result = {}
        for ticker in tickers:
            result[ticker] = bc.request(ticker, fields)
        return result


# ---------------------------------------------------------------------------
# Historical data via ContentProxy HTTP API
# ---------------------------------------------------------------------------

def bdh(
    tickers: str | list[str],
    start_date: str,
    end_date: str | None = None,
    session_token: str | None = None,
    fields: list[str] | None = None,
) -> dict[str, list[dict[str, str]]]:
    """
    Bloomberg-style BDH (Broadcast Data History).

    Fetches historical closing prices from AE Broadcast ContentProxy.

    Args:
        tickers: Single ticker or list of tickers (e.g., "PETR4" or ["PETR4", "VALE3"])
        start_date: Start date as YYYYMMDD string
        end_date: End date as YYYYMMDD string (default: today)
        session_token: BCAA session token (tag 10039). If None, reads from
                       BROADCAST_SESSION env var.
        fields: Not used yet (server returns fixed fields: LAST, SETTLE, etc.)

    Returns:
        Dict mapping "SYMBOL.EXCHANGE" -> list of dicts with keys:
        {date, last, settle, settle_rate, yield, dattol}

    Example:
        >>> data = bdh("PETR4", "20260501", "20260519")
        >>> for row in data["PETR4.BVMF"]:
        ...     print(row["date"], row["last"])
    """
    import datetime
    import os
    import xml.etree.ElementTree as ET

    import requests
    import urllib3

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    if isinstance(tickers, str):
        tickers = [tickers]

    if session_token is None:
        session_token = os.environ.get("BROADCAST_SESSION", "")
    if not session_token:
        raise ValueError("session_token required (or set BROADCAST_SESSION env var)")

    if end_date is None:
        end_date = datetime.date.today().strftime("%Y%m%d")

    # Generate business days in range
    dates = []
    d = datetime.datetime.strptime(start_date, "%Y%m%d").date()
    end = datetime.datetime.strptime(end_date, "%Y%m%d").date()
    while d <= end:
        if d.weekday() < 5:
            dates.append(d.strftime("%Y%m%d"))
        d += datetime.timedelta(days=1)

    if not dates:
        return {}

    BASE = "http://cp.ae.com.br:44780"
    s = requests.Session()
    s.headers["User-Agent"] = "bcsys32/7.0"
    s.trust_env = False

    # Fetch in chunks of 250 dates (URL length limit)
    CHUNK = 250
    results: dict[str, list[dict[str, str]]] = {}

    for i in range(0, len(dates), CHUNK):
        chunk_dates = dates[i : i + CHUNK]
        params = {
            "10023": "4",
            "10039": session_token,
            "10113": ";".join(tickers),
            "TipoResposta": "xml",
            "DatasTolerancia": ";".join(chunk_dates),
        }
        r = s.get(
            f"{BASE}/BaseHistoricaNumerica/HistoricoFechamentos",
            params=params,
            timeout=30,
            verify=False,
        )

        root = ET.fromstring(r.text)
        if root.findtext("STATUS") != "success":
            msg = root.findtext("MESSAGE") or "Unknown error"
            raise RuntimeError(f"ContentProxy error: {msg}")

        for tick in root.findall(".//TICK"):
            sym = tick.findtext("SYMBOL") or ""
            row = {
                "date": tick.findtext("DAT") or "",
                "last": tick.findtext("LAST") or "",
                "settle": tick.findtext("SETTLE") or "",
                "settle_rate": tick.findtext("SETTLE_RATE") or "",
                "yield": tick.findtext("YIELD") or "",
                "dattol": tick.findtext("DATTOL") or "",
            }
            results.setdefault(sym, []).append(row)

    # Sort by date
    for sym in results:
        results[sym].sort(key=lambda r: r["date"])

    return results


def bdh_ohlcv(
    ticker: str,
    date: str,
    session_token: str | None = None,
) -> dict[str, str]:
    """
    Get full OHLCV data for a single ticker on a single date.

    Uses HistoricoData endpoint which returns: DAT, LAST, SETTLE, LOW, HIGH,
    OPEN, NEG, QTT, TOTAL_VALUE, OPEN_INTEREST, VWAP, TOTAL_NEG.

    Args:
        ticker: Single ticker (e.g., "PETR4")
        date: Date as YYYYMMDD string
        session_token: BCAA session token

    Returns:
        Dict with OHLCV fields, or empty dict if no data.
    """
    import os
    import xml.etree.ElementTree as ET

    import requests
    import urllib3

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    if session_token is None:
        session_token = os.environ.get("BROADCAST_SESSION", "")
    if not session_token:
        raise ValueError("session_token required (or set BROADCAST_SESSION env var)")

    BASE = "http://cp.ae.com.br:44780"
    s = requests.Session()
    s.headers["User-Agent"] = "bcsys32/7.0"
    s.trust_env = False

    params = {
        "305": ticker,
        "10023": "4",
        "10039": session_token,
        "10077": date,
        "TipoResposta": "xml",
        "Precisao": "2",
    }
    r = s.get(
        f"{BASE}/BaseHistoricaNumerica/HistoricoData",
        params=params,
        timeout=15,
        verify=False,
    )

    root = ET.fromstring(r.text)
    if root.findtext("STATUS") != "success":
        return {}

    tick = root.find(".//TICK")
    if tick is None:
        return {}

    return {child.tag.lower(): (child.text or "") for child in tick}

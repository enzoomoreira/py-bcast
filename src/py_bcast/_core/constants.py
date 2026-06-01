"""Constants shared across py_bcast modules."""

# ─────────────────────────────────────────────────────────────────────────────
# DDE
# ─────────────────────────────────────────────────────────────────────────────

DDE_SERVICE = "BC"
DDE_TOPIC_REALTIME = "COT"
DDE_TOPIC_SNAPSHOT = "ATIVO"

# DDEML error codes (from ddeml.h). DMLERR_ADVACKTIMEOUT is re-exported via the
# package root; the rest are surfaced only through DMLERR_NAMES (by value).
DMLERR_ADVACKTIMEOUT = 0x4009  # 16393 — server didn't ACK the advise

DMLERR_NAMES: dict[int, str] = {
    0x4001: "DMLERR_BUSY",
    0x4002: "DMLERR_DATAACKTIMEOUT",
    0x4005: "DMLERR_EXECACKTIMEOUT",
    0x4009: "DMLERR_ADVACKTIMEOUT",
    0x400A: "DMLERR_NO_CONV_ESTABLISHED",
    0x400B: "DMLERR_POKEACKTIMEOUT",
    0x400E: "DMLERR_SERVER_DIED",
    0x4010: "DMLERR_UNADVACKTIMEOUT",
}

# ATIVO topic returns 56 tab-separated columns in this order
SNAPSHOT_FIELDS = [
    "ATIVO",
    "ULT",
    "HOR",
    "VAR",
    "MAX",
    "MIN",
    "FEC",
    "ABE",
    "OCP",
    "OVD",
    "NEG",
    "QUL",
    "MED",
    "QCP_TOTAL",
    "QVD_TOTAL",
    "QTT",
    "SINAL",
    "EST",
    "ULT_C1",
    "HOR_C1",
    "QUL_C1",
    "ULT_V1",
    "HOR_V1",
    "QUL_V1",
    "ULT_C2",
    "HOR_C2",
    "QUL_C2",
    "ULT_V2",
    "HOR_V2",
    "QUL_V2",
    "SIT",
    "NOM",
    "COD_ISIN",
    "DAT",
    "F35",
    "F36",
    "LOTE_PAD",
    "DEC",
    "QUL_MIN",
    "QUL_MAX",
    "LOT",
    "F42",
    "F43",
    "FEC_ANT",
    "DAT_ANT",
    "F46",
    "F47",
    "AFTER_MKT",
    "VOL_FIN",
    "F50",
    "DAT_HOJ",
    "F52",
    "F53",
    "F54",
    "ISIN",
    "F56",
]

# ─────────────────────────────────────────────────────────────────────────────
# HTTP ContentProxy (legacy terminal — bcsys32.exe)
# ─────────────────────────────────────────────────────────────────────────────

BASE_URL = "http://cp.ae.com.br:44780"

# ─────────────────────────────────────────────────────────────────────────────
# Broadcast+ (new terminal — Broadcast+.exe v7.4.4)
# ─────────────────────────────────────────────────────────────────────────────

PLUS_BASE_URL = "https://svc.aebroadcast.com.br:44761"
PLUS_WS_URL = "wss://svc.aebroadcast.com.br:44761"
PLUS_VERSION = "7.4.4"
PLUS_APP_ID = "broadcast-nt"


def plus_base_headers() -> dict[str, str]:
    """Headers for unauthenticated Broadcast+ API calls (no Bearer token)."""
    return {
        "content-type": "application/json",
        "accept": "application/json",
        "x-version": PLUS_VERSION,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Instrument database
# ─────────────────────────────────────────────────────────────────────────────

INSTRUMENT_DB_XOR_KEY = 0xAE
INSTRUMENT_DB_FILENAME = "aetp_17.dat"
INSTRUMENT_DB_RELPATH = r"Agencia Estado\Broadcast\DataFiles"

# Maps Plus exchange "name" (e.g. "Bovespa") to legacy code (e.g. "BVMF").
# Unknown names are returned unchanged by normalize_exchange().
PLUS_EXCHANGE_NAME_TO_CODE: dict[str, str] = {
    "Bovespa": "BVMF",
    "BMF": "BVMF",
    "BM&F": "BVMF",
    "CME": "CME",
    "CBOT": "CBOT",
    "NYMEX": "NYMEX",
    "COMEX": "COMEX",
    "ICE Europe": "ICEEU",
    "ICE US": "ICEUS",
    "CBOE": "CBOEI",
    "NYSE": "NYSE",
    "NASDAQ": "NASDAQ",
}


def normalize_exchange(name_or_code: str) -> str:
    """Normalize a Plus exchange name (e.g. "Bovespa") to legacy code (e.g. "BVMF").

    Pass-through for codes already in legacy format or unknown names — caller
    decides whether to warn on unmapped values.
    """
    if not name_or_code:
        return ""
    return PLUS_EXCHANGE_NAME_TO_CODE.get(name_or_code, name_or_code)

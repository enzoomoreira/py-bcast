"""Constants shared across py_bcast modules."""

# ─────────────────────────────────────────────────────────────────────────────
# DDE
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
# HTTP ContentProxy
# ─────────────────────────────────────────────────────────────────────────────

BASE_URL = "http://cp.ae.com.br:44780"
HTTP_USER_AGENT = "bcsys32/7.0"
HTTP_PLATFORM = "4"

# ─────────────────────────────────────────────────────────────────────────────
# Instrument database
# ─────────────────────────────────────────────────────────────────────────────

INSTRUMENT_DB_XOR_KEY = 0xAE
INSTRUMENT_DB_FILENAME = "aetp_17.dat"
INSTRUMENT_DB_RELPATH = r"Agencia Estado\Broadcast\DataFiles"

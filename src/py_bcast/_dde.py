"""Low-level Windows DDEML bindings for 64-bit DDE streaming."""

import ctypes
import ctypes.wintypes
from ctypes import wintypes

_user32 = ctypes.windll.user32

# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────

CP_WINUNICODE = 1200
CF_TEXT = 1
XTYP_ADVDATA = 0x4010
XTYP_ADVSTART = 0x1030
XTYP_ADVSTOP = 0x1040
XTYP_DISCONNECT = 0x00C2
APPCMD_CLIENTONLY = 0x00000010

# ─────────────────────────────────────────────────────────────────────────────
# Handle types (pointer-sized for 64-bit)
# ─────────────────────────────────────────────────────────────────────────────

HDDEDATA = ctypes.c_ssize_t
HCONV = ctypes.c_ssize_t
HSZ = ctypes.c_ssize_t

# ─────────────────────────────────────────────────────────────────────────────
# Function prototypes
# ─────────────────────────────────────────────────────────────────────────────

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
    wintypes.UINT, wintypes.UINT, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD),
]

_user32.DdeFreeStringHandle.argtypes = [wintypes.DWORD, HSZ]
_user32.DdeDisconnect.argtypes = [HCONV]

# ─────────────────────────────────────────────────────────────────────────────
# Callback type (all params pointer-sized for 64-bit correctness)
# ─────────────────────────────────────────────────────────────────────────────

DDECALLBACK = ctypes.WINFUNCTYPE(
    ctypes.c_ssize_t,
    ctypes.c_uint, ctypes.c_uint,
    ctypes.c_ssize_t, ctypes.c_ssize_t, ctypes.c_ssize_t,
    ctypes.c_ssize_t, ctypes.c_ssize_t, ctypes.c_ssize_t,
)

# ─────────────────────────────────────────────────────────────────────────────
# Convenience wrappers
# ─────────────────────────────────────────────────────────────────────────────

DdeInitializeW = _user32.DdeInitializeW
DdeUninitialize = _user32.DdeUninitialize
DdeConnect = _user32.DdeConnect
DdeDisconnect = _user32.DdeDisconnect
DdeClientTransaction = _user32.DdeClientTransaction
DdeCreateStringHandleW = _user32.DdeCreateStringHandleW
DdeFreeStringHandle = _user32.DdeFreeStringHandle
DdeGetData = _user32.DdeGetData
DdeQueryStringW = _user32.DdeQueryStringW
DdeGetLastError = _user32.DdeGetLastError
PeekMessageW = _user32.PeekMessageW
TranslateMessage = _user32.TranslateMessage
DispatchMessageW = _user32.DispatchMessageW

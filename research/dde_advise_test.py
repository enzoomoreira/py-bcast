"""Quick test of DDE Advise streaming with fixed 64-bit ctypes."""
import sys
import time
import threading
import ctypes
import ctypes.wintypes
from ctypes import wintypes
from datetime import datetime

user32 = ctypes.windll.user32

CP_WINUNICODE = 1200
CF_TEXT = 1
XTYP_ADVDATA = 0x4010
XTYP_ADVSTART = 0x1030
XTYP_ADVSTOP = 0x1040
XTYP_DISCONNECT = 0x00C2
APPCMD_CLIENTONLY = 0x00000010

# Pointer-sized types for 64-bit handles
HDDEDATA = ctypes.c_ssize_t
HCONV = ctypes.c_ssize_t
HSZ = ctypes.c_ssize_t

# Set proper function signatures
user32.DdeGetData.argtypes = [HDDEDATA, ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD]
user32.DdeGetData.restype = wintypes.DWORD
user32.DdeQueryStringW.argtypes = [wintypes.DWORD, HSZ, ctypes.c_wchar_p, wintypes.DWORD, ctypes.c_int]
user32.DdeQueryStringW.restype = wintypes.DWORD
user32.DdeCreateStringHandleW.restype = HSZ
user32.DdeCreateStringHandleW.argtypes = [wintypes.DWORD, ctypes.c_wchar_p, ctypes.c_int]
user32.DdeConnect.restype = HCONV
user32.DdeConnect.argtypes = [wintypes.DWORD, HSZ, HSZ, ctypes.c_void_p]
user32.DdeClientTransaction.restype = HDDEDATA
user32.DdeClientTransaction.argtypes = [
    ctypes.c_void_p, wintypes.DWORD, HCONV, HSZ,
    wintypes.UINT, wintypes.UINT, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)
]
user32.DdeFreeStringHandle.argtypes = [wintypes.DWORD, HSZ]
user32.DdeDisconnect.argtypes = [HCONV]

updates = []
lock = threading.Lock()

DDECALLBACK = ctypes.WINFUNCTYPE(
    ctypes.c_ssize_t,
    ctypes.c_uint, ctypes.c_uint,
    ctypes.c_ssize_t, ctypes.c_ssize_t, ctypes.c_ssize_t,
    ctypes.c_ssize_t, ctypes.c_ssize_t, ctypes.c_ssize_t,
)

@DDECALLBACK
def dde_callback(uType, uFmt, hConv, hsz1, hsz2, hData, dwData1, dwData2):
    if uType == XTYP_ADVDATA:
        buf = ctypes.create_unicode_buffer(256)
        user32.DdeQueryStringW(inst_id.value, hsz2, buf, 256, CP_WINUNICODE)
        item_name = buf.value

        data_str = ""
        if hData:
            size = user32.DdeGetData(hData, None, 0, 0)
            if size > 0:
                data_buf = ctypes.create_string_buffer(size)
                user32.DdeGetData(hData, data_buf, size, 0)
                data_str = data_buf.value.decode('latin-1', errors='replace').strip('\x00')

        ts = datetime.now().strftime('%H:%M:%S.%f')[:-3]
        with lock:
            updates.append((ts, item_name, data_str))
        print(f"  [STREAM] {ts} {item_name} = {data_str}", flush=True)
        return 1
    elif uType == XTYP_DISCONNECT:
        print("  [DISCONNECTED]", flush=True)
    return 0

# Initialize
inst_id = ctypes.c_ulong(0)
rc = user32.DdeInitializeW(ctypes.byref(inst_id), dde_callback, APPCMD_CLIENTONLY, 0)
if rc != 0:
    print(f"DdeInitialize failed: {rc}")
    sys.exit(1)

print(f"DDEML initialized (inst={inst_id.value})")

def make_str(text):
    return user32.DdeCreateStringHandleW(inst_id.value, text, CP_WINUNICODE)

# Connect
h_svc = make_str("BC")
h_top = make_str("COT")
h_conv = user32.DdeConnect(inst_id.value, h_svc, h_top, None)
user32.DdeFreeStringHandle(inst_id.value, h_svc)
user32.DdeFreeStringHandle(inst_id.value, h_top)

if not h_conv:
    print(f"Connect failed (err={user32.DdeGetLastError(inst_id.value)})")
    sys.exit(1)

print(f"Connected to BC|COT")

# Start advise
items = ["PETR4.ULT", "PETR4.VAR", "PETR4.NEG", "VALE3.ULT", "IBOV.ULT", "IBOV.VAR"]
for item in items:
    h_item = make_str(item)
    result = user32.DdeClientTransaction(None, 0, h_conv, h_item, CF_TEXT, XTYP_ADVSTART, 5000, None)
    user32.DdeFreeStringHandle(inst_id.value, h_item)
    status = "OK" if result else f"FAIL(err={user32.DdeGetLastError(inst_id.value)})"
    print(f"  Advise {item}: {status}", flush=True)
    time.sleep(0.1)

# Message pump for 20s
print(f"\nListening for 20 seconds...\n", flush=True)
MSG = ctypes.wintypes.MSG()
start = time.time()
last_report = start

while time.time() - start < 20:
    while user32.PeekMessageW(ctypes.byref(MSG), 0, 0, 0, 1):
        user32.TranslateMessage(ctypes.byref(MSG))
        user32.DispatchMessageW(ctypes.byref(MSG))
    now = time.time()
    if now - last_report >= 5:
        print(f"  ... {int(now-start)}s, {len(updates)} updates", flush=True)
        last_report = now
    time.sleep(0.02)

# Stop advise and cleanup
for item in items:
    h_item = make_str(item)
    user32.DdeClientTransaction(None, 0, h_conv, h_item, CF_TEXT, XTYP_ADVSTOP, 2000, None)
    user32.DdeFreeStringHandle(inst_id.value, h_item)

user32.DdeDisconnect(h_conv)
user32.DdeUninitialize(inst_id.value)

print(f"\n{'='*50}")
print(f"Total updates: {len(updates)}")
unique_items = set(item for _, item, _ in updates)
print(f"Unique items updated: {unique_items}")
if updates:
    print(f"\nLast 15 updates:")
    for ts, item, val in updates[-15:]:
        print(f"  {ts} {item} = {val}")

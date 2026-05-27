"""Windows process memory scanning utilities.

Shared infrastructure for discovering tokens from running terminal processes
(bcsys32.exe for legacy, Broadcast+.exe for Plus).

Usage::

    from py_bcast._core.memory import find_process_pid, scan_process_memory

    pid = find_process_pid("Broadcast+.exe")
    if pid is not None:
        candidates = scan_process_memory(pid, MY_TOKEN_PATTERN)
"""

from __future__ import annotations

import ctypes
import ctypes.wintypes as wt
import re
import subprocess
import sys

if sys.platform != "win32":
    raise ImportError("Process memory scanning requires Windows")

from .logging import get_logger

logger = get_logger(__name__)

# ── Windows API constants ────────────────────────────────────────────────────

PROCESS_VM_READ = 0x0010
PROCESS_QUERY_INFORMATION = 0x0400
MEM_COMMIT = 0x1000
PAGE_GUARD = 0x100
PAGE_NOACCESS = 0x01

_kernel32 = ctypes.windll.kernel32


class _MEMORY_BASIC_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("BaseAddress", ctypes.c_void_p),
        ("AllocationBase", ctypes.c_void_p),
        ("AllocationProtect", wt.DWORD),
        ("RegionSize", ctypes.c_size_t),
        ("State", wt.DWORD),
        ("Protect", wt.DWORD),
        ("Type", wt.DWORD),
    ]


# ── Public API ───────────────────────────────────────────────────────────────


def find_process_pid(image_name: str) -> int | None:
    """Find PID of a process by image name via ``tasklist``.

    Args:
        image_name: Exact process name (e.g. ``"bcsys32.exe"``, ``"Broadcast+.exe"``).

    Returns:
        PID of the first matching process, or ``None`` if not found.
    """
    try:
        result = subprocess.run(
            ["tasklist", "/FI", f"IMAGENAME eq {image_name}", "/FO", "CSV", "/NH"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        for line in result.stdout.strip().splitlines():
            parts = line.strip('"').split('","')
            if len(parts) >= 2 and parts[0].lower() == image_name.lower():
                return int(parts[1])
    except (subprocess.TimeoutExpired, OSError, ValueError):
        pass
    return None


def scan_process_memory(pid: int, pattern: re.Pattern[bytes]) -> list[str]:
    """Scan committed virtual memory regions of a process for token candidates.

    Reads 64 KiB chunks from all committed, non-guarded memory regions and
    applies ``pattern`` to find matches.  Each match is decoded as ASCII.

    Args:
        pid: Target process ID (must be readable by the current user).
        pattern: Compiled bytes regex (e.g. ``re.compile(rb"eyJ[A-Za-z0-9_\\-]{10,}")``).

    Returns:
        Sorted list of unique matched strings.
    """
    handle = _kernel32.OpenProcess(
        PROCESS_VM_READ | PROCESS_QUERY_INFORMATION, False, pid
    )
    if not handle:
        return []

    found: set[str] = set()
    addr = 0
    mbi = _MEMORY_BASIC_INFORMATION()
    buf = ctypes.create_string_buffer(65536)

    try:
        while addr < 0x7FFFFFFFFFFF:
            ret = _kernel32.VirtualQueryEx(
                handle, ctypes.c_void_p(addr), ctypes.byref(mbi), ctypes.sizeof(mbi)
            )
            if ret == 0:
                break

            base = mbi.BaseAddress or 0
            size = mbi.RegionSize or 0
            if size == 0:
                break

            if (
                mbi.State == MEM_COMMIT
                and mbi.Protect not in (PAGE_GUARD, PAGE_NOACCESS, 0)
                and not (mbi.Protect & PAGE_GUARD)
            ):
                offset = 0
                while offset < size:
                    chunk_size = min(65536, size - offset)
                    bytes_read = ctypes.c_size_t(0)
                    ok = _kernel32.ReadProcessMemory(
                        handle,
                        ctypes.c_void_p(base + offset),
                        buf,
                        chunk_size,
                        ctypes.byref(bytes_read),
                    )
                    if ok and bytes_read.value > 0:
                        for m in pattern.findall(buf.raw[: bytes_read.value]):
                            found.add(m.decode("ascii"))
                    offset += chunk_size

            addr = base + size
    finally:
        _kernel32.CloseHandle(handle)

    return sorted(found)

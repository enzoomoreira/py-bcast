"""Proof of concept: find BCAA session token in bcsys32.exe process memory."""
import ctypes
import ctypes.wintypes as wt
import re

# Windows API constants
PROCESS_VM_READ = 0x0010
PROCESS_QUERY_INFORMATION = 0x0400
MEM_COMMIT = 0x1000
PAGE_GUARD = 0x100
PAGE_NOACCESS = 0x01

kernel32 = ctypes.windll.kernel32


class MEMORY_BASIC_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("BaseAddress", ctypes.c_void_p),
        ("AllocationBase", ctypes.c_void_p),
        ("AllocationProtect", wt.DWORD),
        ("RegionSize", ctypes.c_size_t),
        ("State", wt.DWORD),
        ("Protect", wt.DWORD),
        ("Type", wt.DWORD),
    ]


def find_bcsys32_pid() -> int | None:
    """Find PID of bcsys32.exe using Windows API."""
    import subprocess
    result = subprocess.run(
        ["tasklist", "/FI", "IMAGENAME eq bcsys32.exe", "/FO", "CSV", "/NH"],
        capture_output=True, text=True
    )
    for line in result.stdout.strip().splitlines():
        parts = line.strip('"').split('","')
        if len(parts) >= 2 and parts[0].lower() == "bcsys32.exe":
            return int(parts[1])
    return None


def scan_process_memory(pid: int) -> list[str]:
    """Scan process memory for session token candidates."""
    handle = kernel32.OpenProcess(PROCESS_VM_READ | PROCESS_QUERY_INFORMATION, False, pid)
    if not handle:
        raise OSError(f"Cannot open process {pid}: error {ctypes.get_last_error()}")

    # Pattern: uppercase hex letter followed by 32 lowercase hex chars
    pattern = re.compile(rb"[A-F][0-9a-f]{32}")
    found = set()
    addr = 0
    mbi = MEMORY_BASIC_INFORMATION()
    buf = ctypes.create_string_buffer(65536)
    scanned = 0

    try:
        while addr < 0x7FFFFFFFFFFF:
            ret = kernel32.VirtualQueryEx(
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
                    read_addr = base + offset
                    success = kernel32.ReadProcessMemory(
                        handle, ctypes.c_void_p(read_addr), buf, chunk_size, ctypes.byref(bytes_read)
                    )
                    if success and bytes_read.value > 0:
                        data = buf.raw[: bytes_read.value]
                        matches = pattern.findall(data)
                        for m in matches:
                            found.add(m.decode("ascii"))
                        scanned += bytes_read.value
                    offset += chunk_size

            addr = base + size
    finally:
        kernel32.CloseHandle(handle)

    print(f"Scanned {scanned / 1024 / 1024:.1f} MB of process memory")
    return sorted(found)


def validate_token(token: str) -> bool:
    """Test if a token is a valid BCAA session by making a lightweight HTTP call."""
    import httpx
    try:
        r = httpx.get(
            "http://cp.ae.com.br:44780/BaseHistoricaNumerica/HistoricoFechamentos",
            params={"10023": "4", "10039": token, "10113": "PETR4", "DatasTolerancia": "20260519", "TipoResposta": "xml"},
            headers={"User-Agent": "bcsys32/7.0"},
            timeout=5,
            verify=False,
        )
        return "<STATUS>success</STATUS>" in r.text
    except Exception:
        return False


if __name__ == "__main__":
    import urllib3
    urllib3.disable_warnings()

    pid = find_bcsys32_pid()
    if not pid:
        print("ERROR: bcsys32.exe not running")
        exit(1)

    print(f"Found bcsys32.exe PID: {pid}")
    candidates = scan_process_memory(pid)
    print(f"Found {len(candidates)} candidate tokens")

    # Validate each candidate
    for token in candidates:
        valid = validate_token(token)
        status = "VALID" if valid else "invalid"
        print(f"  {token} -> {status}")
        if valid:
            print(f"\n*** WORKING SESSION TOKEN: {token} ***")
            break

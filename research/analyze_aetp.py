"""
Analyze AETP binary data files to understand the protocol format.
"""
import re
import struct

FILES = {
    "aetp_36.dat": r"C:\Users\i455561\AppData\Roaming\Agencia Estado\Broadcast\DataFiles\aetp_36.dat",
    "aetp_18.dat": r"C:\Users\i455561\AppData\Roaming\Agencia Estado\Broadcast\DataFiles\aetp_18.dat",
    "aetp_17.cfg": r"C:\Users\i455561\AppData\Roaming\Agencia Estado\Broadcast\DataFiles\aetp_17.cfg",
}


def ascii_strings(data, min_len=5):
    return [m.group().decode("latin-1", errors="replace")
            for m in re.finditer(rb"[ -~]{%d,}" % min_len, data)]


def wide_strings(data, min_len=5):
    results = []
    i = 0
    while i < len(data) - 2:
        start = i
        chars = []
        while i < len(data) - 1:
            lo, hi = data[i], data[i + 1]
            if hi == 0 and 0x20 <= lo <= 0x7E:
                chars.append(chr(lo))
                i += 2
            else:
                break
        if len(chars) >= min_len:
            results.append("".join(chars))
        else:
            i = start + 1
    return results


def hexdump(data, n=256):
    lines = []
    for i in range(0, min(n, len(data)), 16):
        chunk = data[i:i+16]
        hex_part = " ".join(f"{b:02X}" for b in chunk)
        asc_part = "".join(chr(b) if 0x20 <= b <= 0x7E else "." for b in chunk)
        lines.append(f"  {i:04X}  {hex_part:<47}  {asc_part}")
    return "\n".join(lines)


def try_parse_aetp_frames(data):
    """Try to find AETP frames starting with known magic bytes."""
    # Try magic 1a fe ce fa
    magic = b"\x1a\xfe\xce\xfa"
    pos = 0
    frames = []
    while pos < len(data) - 8:
        idx = data.find(magic, pos)
        if idx < 0:
            break
        if idx + 8 < len(data):
            length = struct.unpack_from("<I", data, idx + 4)[0]
            checksum = data[idx + 8]
            payload_start = idx + 9
            payload_end = payload_start + length - 1
            payload = data[payload_start:payload_end] if payload_end <= len(data) else b""
            frames.append((idx, length, checksum, payload))
        pos = idx + 1
    return frames


for name, path in FILES.items():
    print(f"\n{'='*60}")
    print(f"  FILE: {name}")
    print(f"{'='*60}")
    try:
        data = open(path, "rb").read()
    except FileNotFoundError:
        print(f"  [not found]")
        continue

    print(f"  Size: {len(data)} bytes")
    print(f"  First 256 bytes:")
    print(hexdump(data, 256))

    strs = ascii_strings(data)
    print(f"\n  ASCII strings ({len(strs)} total):")
    for s in strs[:60]:
        print(f"    {s}")

    wstrs = wide_strings(data)
    if wstrs:
        print(f"\n  Wide strings ({len(wstrs)} total):")
        for s in wstrs[:30]:
            print(f"    {s}")

    frames = try_parse_aetp_frames(data)
    if frames:
        print(f"\n  AETP frames (magic 1afacefa): {len(frames)}")
        for i, (off, length, csum, payload) in enumerate(frames[:5]):
            print(f"    [{i}] offset={off} len={length} csum=0x{csum:02X} payload={payload[:40].hex()}")
    else:
        print("\n  No AETP magic 1afacefa found")
        # Try other common binary protocols
        for magic_b in [b"\xFF\xFE", b"\xFE\xFF", b"\x00\x00\x00", b"AETP", b"BCTP"]:
            idx = data.find(magic_b)
            if idx >= 0:
                print(f"  Found bytes {magic_b.hex()} at offset {idx}")

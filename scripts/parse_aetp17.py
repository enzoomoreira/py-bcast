"""
Parse aetp_17.dat — the full instrument master database.
Format: TSV (tab-separated), XOR-encrypted with key 0xAE.
First line = tag headers, subsequent lines = instrument records.
"""
import os
from pathlib import Path
from collections import Counter, defaultdict

DATA_DIR = Path(os.environ["APPDATA"]) / "Agencia Estado" / "Broadcast" / "DataFiles"
aetp_path = DATA_DIR / "aetp_17.dat"


def xor_decode(data: bytes, key: int = 0xAE) -> bytes:
    return bytes([b ^ key for b in data])


print(f"Decoding aetp_17.dat ({aetp_path.stat().st_size / 1024 / 1024:.1f} MB)...")

with open(aetp_path, "rb") as f:
    raw = f.read()

decoded = xor_decode(raw)
text = decoded.decode("latin-1")
lines = text.split('\n')

print(f"Total lines: {len(lines)}")

# First line is header (tag numbers)
header_line = lines[0]
tags = header_line.strip().split('\t')
print(f"Columns (tags): {len(tags)}")
print(f"Tags: {tags}")

# Important tags:
# 305 = full symbol (TICKER.EXCHANGE)
# 10068 = short ticker  
# 303 = ISIN
# 10045 = name
# 10086 = some ID
# 10092 = exchange numeric ID?

tag_305_idx = tags.index("305") if "305" in tags else None
tag_10068_idx = tags.index("10068") if "10068" in tags else None
tag_303_idx = tags.index("303") if "303" in tags else None
tag_10045_idx = tags.index("10045") if "10045" in tags else None
tag_10086_idx = tags.index("10086") if "10086" in tags else None
tag_10092_idx = tags.index("10092") if "10092" in tags else None

print(f"\nKey column indices:")
print(f"  305 (full symbol): col {tag_305_idx}")
print(f"  10068 (short ticker): col {tag_10068_idx}")
print(f"  303 (ISIN): col {tag_303_idx}")
print(f"  10045 (name): col {tag_10045_idx}")
print(f"  10086 (id?): col {tag_10086_idx}")
print(f"  10092 (exchange?): col {tag_10092_idx}")

# Parse records
print(f"\nParsing {len(lines) - 1} records...")

instruments = []
exchange_counter = Counter()

for i, line in enumerate(lines[1:], 1):
    if not line.strip():
        continue
    fields = line.split('\t')
    if len(fields) < max(tag_305_idx or 0, tag_10068_idx or 0, tag_10045_idx or 0) + 1:
        continue
    
    full_sym = fields[tag_305_idx] if tag_305_idx is not None and tag_305_idx < len(fields) else ""
    short_ticker = fields[tag_10068_idx] if tag_10068_idx is not None and tag_10068_idx < len(fields) else ""
    isin = fields[tag_303_idx] if tag_303_idx is not None and tag_303_idx < len(fields) else ""
    name = fields[tag_10045_idx] if tag_10045_idx is not None and tag_10045_idx < len(fields) else ""
    exchange_id = fields[tag_10092_idx] if tag_10092_idx is not None and tag_10092_idx < len(fields) else ""
    
    # Extract exchange suffix from full symbol
    exchange = ""
    if "." in full_sym:
        exchange = full_sym.split(".")[-1]
    elif "\\" in full_sym:
        exchange = full_sym.split("\\")[-1]
    
    instruments.append({
        "full_sym": full_sym,
        "ticker": short_ticker,
        "name": name,
        "isin": isin,
        "exchange": exchange,
        "exchange_id": exchange_id,
    })
    exchange_counter[exchange] += 1

print(f"Total instruments parsed: {len(instruments)}")

# ============================================================
# Exchange distribution
# ============================================================
print("\n" + "=" * 60)
print("Exchanges (top 30)")
print("=" * 60)
for ex, count in exchange_counter.most_common(30):
    # Show sample ticker
    sample = next((i for i in instruments if i["exchange"] == ex), None)
    sample_str = f"  ex: {sample['ticker']}" if sample else ""
    print(f"  {ex:20s} {count:>6} instruments{sample_str}")

# ============================================================
# Search for known symbols
# ============================================================
print("\n" + "=" * 60)
print("Symbol Search")
print("=" * 60)

search_terms = ["PETR4", "VALE3", "IBOV", "USDBRL", "EURUSD", "GOLD", "SILVER",
                "WTI", "DAX", "FTSE", "VIX", "DXY", "SP500", "DJIA", "NASDAQ",
                "WDOM25", "WINM25", "DOLM25", "DI1F27", "HGLG11", "US10Y", "BRENT",
                "NIKKEI", "BTC", "ETH"]

for term in search_terms:
    # Search in both ticker and full_sym
    matches = [i for i in instruments if term == i["ticker"] or term in i["full_sym"]]
    if not matches:
        # Partial match
        matches = [i for i in instruments if term.lower() in i["ticker"].lower() or term.lower() in i["full_sym"].lower()]
    
    if matches:
        print(f"\n  {term}:")
        for m in matches[:5]:
            print(f"    {m['full_sym']:35s} ticker={m['ticker']:15s} name={m['name'][:60]}")
    else:
        # Search in name
        name_matches = [i for i in instruments if term.lower() in i["name"].lower()]
        if name_matches:
            print(f"\n  {term} (by name):")
            for m in name_matches[:3]:
                print(f"    {m['full_sym']:35s} ticker={m['ticker']:15s} name={m['name'][:60]}")
        else:
            print(f"\n  {term}: NOT FOUND")

# ============================================================
# Sample: BVMF exchange instruments (BR stocks)
# ============================================================
print("\n\n" + "=" * 60)
print("BVMF Exchange — Sample Instruments")
print("=" * 60)

bvmf = [i for i in instruments if i["exchange"] == "BVMF"]
print(f"Total BVMF: {len(bvmf)}")

# Common BR stocks
known_br = ["PETR4", "VALE3", "ITUB4", "BBDC4", "ABEV3", "B3SA3", "WEGE3",
            "RENT3", "SUZB3", "JBSS3", "HGLG11", "MXRF11"]
print("\nKnown BR stocks in aetp_17:")
for sym in known_br:
    m = next((i for i in bvmf if i["ticker"] == sym), None)
    if m:
        print(f"  {m['ticker']:12s} -> {m['full_sym']:20s} | {m['name'][:50]}")

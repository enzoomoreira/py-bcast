import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["BROADCAST_SESSION"] = "F9bca84c7cb51fbdb4456a86c6548fb13"

from broadcast import bdh, bdh_ohlcv

print("=== BDH (closing prices, multi-symbol, date range) ===")
data = bdh(["PETR4", "VALE3"], "20260512", "20260519")
for sym, rows in data.items():
    print(f"\n{sym} ({len(rows)} rows):")
    for row in rows:
        print(f"  {row['date']}: LAST={row['last']}")

print("\n=== OHLCV (single day, full candle) ===")
ohlcv = bdh_ohlcv("PETR4", "20260519")
for k, v in ohlcv.items():
    print(f"  {k}: {v}")

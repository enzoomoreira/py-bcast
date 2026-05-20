"""Test the broadcast.py client module."""
import time
from broadcast import BroadcastClient, bdp, bdps

print("=" * 60)
print("  broadcast.py Client Test")
print("=" * 60)

# 1. Simple one-shot request (bdp-style)
print("\n[1] bdp() - Single field request")
price = bdp("PETR4", "ULT")
print(f"    PETR4 ULT = {price}")

# 2. Multiple fields
print("\n[2] bdp() - Multiple fields")
data = bdp("PETR4", ["ULT", "VAR", "MAX", "MIN", "ABE", "FEC", "NEG", "NOM"])
for k, v in data.items():
    print(f"    {k:6s} = {v}")

# 3. Batch request (multiple tickers)
print("\n[3] bdps() - Batch request")
result = bdps(
    ["PETR4", "VALE3", "ITUB4", "IBOV", "USDBRL"],
    ["ULT", "VAR"]
)
for ticker, fields in result.items():
    print(f"    {ticker:8s} ULT={fields.get('ULT', 'N/A'):>12s}  VAR={fields.get('VAR', 'N/A'):>8s}")

# 4. Full snapshot
print("\n[4] snapshot() - Full ticker data")
with BroadcastClient("PySnap") as bc:
    snap = bc.snapshot("PETR4")
    print(f"    {len(snap)} fields returned:")
    for k, v in list(snap.items())[:15]:
        print(f"    {k:12s} = {v}")

# 5. Streaming subscription
print("\n[5] subscribe() - Real-time streaming (10 seconds)")
updates = []

def on_update(ticker, field, value):
    ts = time.strftime('%H:%M:%S')
    updates.append((ts, ticker, field, value))
    if len(updates) <= 20:
        print(f"    {ts} {ticker}.{field} = {value}", flush=True)

with BroadcastClient("PyStream") as bc:
    bc.subscribe(
        ["PETR4", "VALE3", "IBOV"],
        ["ULT", "VAR"],
        callback=on_update
    )
    bc.run(duration=10)

print(f"\n    Total updates in 10s: {len(updates)}")
unique = set((t, f) for _, t, f, _ in updates)
print(f"    Unique subscriptions that fired: {len(unique)}")
for t, f in sorted(unique):
    count = sum(1 for _, tt, ff, _ in updates if tt == t and ff == f)
    vals = [v for _, tt, ff, v in updates if tt == t and ff == f]
    print(f"      {t}.{f}: {count} updates, last={vals[-1]}")

print(f"\nDone!")

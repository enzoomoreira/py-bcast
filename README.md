# py-bcast

Python client for **AE Broadcast** (Agência Estado) market data terminal — a Bloomberg `blpapi`/`xbbg`-like interface for the Broadcast+ ecosystem.

## Features

- **Real-time streaming** via DDE (bdp, subscribe, snapshot)
- **Historical data** via HTTP (daily OHLCV, tick-by-tick)
- **Instrument database** — search 623K+ instruments across 30+ exchanges
- Proper Python package with `src/` layout and type annotations

## Requirements

- Windows 10/11
- Python 3.12+
- Terminal Broadcast running (`bcsys32.exe`)
- `BROADCAST_SESSION` env var set for historical data

## Installation

```bash
pip install -e ".[dde]"
```

Or for HTTP-only usage (no pywin32 needed):
```bash
pip install -e .
```

## Quick Start

```python
import os
os.environ["BROADCAST_SESSION"] = "<your_session_token>"

from py_bcast import bdp, bdh, bdt, bsearch, BroadcastClient

# Real-time quote
price = bdp("PETR4", "ULT")

# Historical daily (works for ALL instruments)
data = bdh("PETR4", "20260501", "20260520")
for row in data["PETR4.BVMF"]:
    print(row["date"], row["last"])

# OHLCV single day
bar = bdh_ohlcv("PETR4", "20260519")

# Tick data (international instruments)
ticks = bdt("USDBRL", "20260519100000", "20260519110000")

# Instrument search (623K+ instruments)
bsearch("PETR", exchange="BVMF")
bsearch("VIX", exchange="CBOEI")

# Real-time streaming
with BroadcastClient() as bc:
    bc.subscribe(["PETR4", "VALE3"], ["ULT", "VAR"],
                 callback=lambda t, f, v: print(f"{t}.{f} = {v}"))
    bc.run(duration=60)
```

## Supported Assets

| Class | Examples | Real-time | Daily History | Tick Data |
|-------|----------|-----------|---------------|-----------|
| B3 Stocks | PETR4, VALE3, ITUB4 | ✅ | ✅ | ❌ |
| FIIs | HGLG11, MXRF11 | ✅ | ✅ | ❌ |
| BDRs | AAPL34, MSFT34 | ✅ | ✅ | ❌ |
| Indices | IBOV, IFIX, SMLL | ✅ | ✅ | ❌ |
| FX | USDBRL, EURUSD, GBPUSD | ✅ | ✅ | ✅ |
| Metals | GOLD, SILVER | ✅ | ✅ | ✅ |
| Energy | WTI, BRENT | ✅ | ✅ | ✅ |
| Global Indices | DAX, FTSE, VIX, DXY | ✅ | ✅ | ✅ |
| Treasuries | US10Y, US2Y | ✅ | ✅ | ✅ |
| DI Futures | DI1F27 | ✅ | ✅ | ❌ |

## Project Structure

```
src/py_bcast/
├── __init__.py         # Public API
├── _constants.py       # Service names, fields, URLs
├── _dde.py             # DDEML ctypes bindings
├── _http.py            # HTTP session factory
├── client.py           # BroadcastClient, bdp, bdps
├── historical.py       # bdh, bdh_ohlcv, bdt
└── instruments.py      # InstrumentDB, bsearch
tests/
├── test_historical.py  # HTTP integration tests
└── test_instruments.py # Instrument DB tests
scripts/                # Utilities for data regeneration
docs/
├── architecture.md     # System architecture & protocols
├── api.md              # Full API reference
├── instruments.md      # Instrument database details
├── limitations.md      # Known limitations & workarounds
└── fields.md           # DDE field reference (56 fields)
```

## Documentation

- [Architecture](docs/architecture.md) — data channels, protocols, auth
- [API Reference](docs/api.md) — all functions with examples
- [Instruments](docs/instruments.md) — 623K instruments, exchanges, symbols
- [Limitations](docs/limitations.md) — what doesn't work and why
- [Fields](docs/fields.md) — complete DDE field mapping

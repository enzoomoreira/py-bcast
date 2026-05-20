# py-bcast

Python client for **AE Broadcast** (Agência Estado) market data terminal — a Bloomberg `blpapi`/`xbbg`-like interface for the Broadcast+ ecosystem.

## Features

- **Real-time streaming** via DDE (bdp, subscribe, snapshot)
- **Historical data** via HTTP (daily OHLCV, intraday bars, tick-by-tick)
- **Macroeconomic series** — FX, indices, commodities, CDI, inflation, returns
- **Fundamental data** — analyst consensus, indicators (Market Cap, Beta), company metadata
- **Corporate events** — dividends, JCP, calendar, dividend yield, broker portfolios
- **Reference data** — 1020 companies, 37 indices, 38 sectors, real-time quotes
- **News & multimedia** — full-text articles, Dow Jones wires, podcasts (no auth needed)
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

from py_bcast import bdp, bdh, bdi, bmacro, bconsensus, bdividends, bsearch

# Real-time quote
price = bdp("PETR4", "ULT")

# Historical daily (works for ALL instruments)
data = bdh("PETR4", "20260501", "20260520")
for row in data["PETR4.BVMF"]:
    print(row["date"], row["last"])

# Intraday 2-min bars (ALL instruments)
bars = bdi("PETR4", "20260520")

# Macro series (FX, indices, commodities, rates)
fx = bmacro("USDBRL", "20260101", "20260520")

# Analyst consensus
data = bconsensus("PETR4")
print(data["buy"], data["target_mean"])

# Dividends history (CVM code + ticker)
divs = bdividends(9512, "PETR4")

# Instrument search (623K+ instruments)
bsearch("PETR", exchange="BVMF")
bsearch("VIX", exchange="CBOEI")

# Real-time streaming
from py_bcast import BroadcastClient
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
├── __init__.py         # Public API (33 exported functions)
├── _core/              # Private infrastructure
│   ├── session.py      # Auto-discovery of session token
│   ├── http.py         # HTTP session factory (httpx)
│   ├── dde.py          # DDEML ctypes bindings
│   ├── constants.py    # Service names, fields, URLs
│   ├── binary.py       # SOH binary protocol decoder
│   ├── aetp.py         # Shared aetp/output helpers
│   └── xml_helpers.py  # Shared XML helpers
├── realtime/
│   └── client.py       # BroadcastClient, bdp, bdps
├── historical/
│   ├── prices.py       # bdh, bdh_ohlcv
│   └── intraday.py     # bdi, bdt
├── macro/
│   └── indicators.py   # bmacro, bdi_cdi, breturn, bvolume, binflation
├── fundamental/
│   ├── consensus.py    # bconsensus
│   ├── reference.py    # bcompany, bindices, bsectors, bquote, btickers, bshares, bindicators
│   └── events.py       # bcalendar, bdividends, bdy, bportfolios, bportfolio
├── news/
│   └── api.py          # bnews, bnews_latest, bnews_search
└── instruments/
    └── db.py           # InstrumentDB, bsearch
tests/
├── test_historical.py  # HTTP integration tests
├── test_intraday.py    # Intraday bars tests
├── test_macro.py       # Macro/CDI/inflation tests
├── test_reference.py   # Reference data tests
├── test_events.py      # Events/dividends tests
├── test_fundamental.py # Consensus tests
├── test_instruments.py # Instrument DB tests
└── test_session.py     # Session discovery tests
scripts/                # Utilities for data regeneration
docs/
├── architecture.md     # System architecture & protocols
├── api.md              # Full API reference
├── compatibility.md    # 227-endpoint status checklist
├── instruments.md      # Instrument database details
├── limitations.md      # Known limitations & workarounds
└── fields.md           # DDE field reference (56 fields)
```

## Documentation

- [Architecture](docs/architecture.md) — data channels, protocols, auth
- [API Reference](docs/api.md) — all functions with examples
- [Compatibility](docs/compatibility.md) — 227-endpoint status checklist (what works, what's blocked, why)
- [Instruments](docs/instruments.md) — 623K instruments, exchanges, symbols
- [Limitations](docs/limitations.md) — what doesn't work and why
- [Fields](docs/fields.md) — complete DDE field mapping

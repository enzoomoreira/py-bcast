# py-bcast

Python client for **AE Broadcast** (Agência Estado) market data terminal — a Bloomberg `blpapi`/`xbbg`-like interface. Suporta os dois terminais em paralelo: **Antigo** (`bcsys32.exe`, DDE + ContentProxy) e **Novo** (`Broadcast+.exe`, JWT + WebSocket).

## Features

**Terminal Antigo (`bcsys32.exe`)**
- **Real-time streaming** via DDE (`bdp`, `subscribe`, `snapshot`)
- **Historical data** via HTTP (daily OHLCV, intraday bars, tick-by-tick)
- **Macroeconomic series** — FX, indices, commodities, CDI, inflation, returns
- **Fundamental data** — analyst consensus, indicators (Market Cap, Beta), company metadata
- **Corporate events** — dividends, JCP, calendar, dividend yield, broker portfolios
- **Reference data** — 1020 companies, 37 indices, 38 sectors, real-time quotes
- **News & multimedia** — full-text articles, Dow Jones wires, podcasts (no auth needed)
- **Instrument database** — 623K+ instruments across 30+ exchanges (local `aetp_17.dat`)

**Terminal Novo (`Broadcast+.exe`)**
- **Real-time streaming** via WebSocket (`BroadcastPlusClient`) com auth refresh transparente
- **Times & trades** (`btrades`) — ultimos 500 trades em fuso `America/Sao_Paulo`
- **Headless login** via ECDH P-384 + AES-GCM (`configure(plus_login=..., plus_password=...)`)
- **Token discovery** — memory scan do `Broadcast+.exe` ou `BROADCAST_PLUS_TOKEN` env var

**Compartilhado entre os backends**
- **Routing automatico** — `configure(terminal="auto"|"legacy"|"plus")`; `bsearch()` ja roteia
- **Async API** — `async_api` namespace com versoes async de todas as funcoes HTTP
- **Caching** — memoria (default) e disco (`diskcache`) com TTL configuravel
- **Rate limiting** — token-bucket e connection pooling
- Proper Python package com `src/` layout, type annotations, Pydantic validation, structured logging

## Requirements

- Windows 10/11
- Python 3.12+
- Pelo menos um dos dois:
  - **Legacy**: `bcsys32.exe` rodando (ou `BROADCAST_SESSION` env var)
  - **Plus**: `Broadcast+.exe` rodando (ou `BROADCAST_PLUS_TOKEN` env var, ou credenciais via `configure`)

## Installation

```bash
pip install -e ".[dde]"
```

Or for HTTP-only usage (no pywin32 needed):
```bash
pip install -e .
```

## Quick Start

### Terminal Antigo (`bcsys32.exe`)

```python
import os
os.environ["BROADCAST_SESSION"] = "<your_session_token>"

from py_bcast import bdp, bdh, bdi, bmacro, bconsensus, bdividends, bsearch

# Real-time quote
price = bdp("PETR4", "ULT")

# Historical daily (works for ALL instruments) — flat DataFrame, ticker column
df = bdh("PETR4", "20260501", "20260520")
print(df["close"].tail())

# Intraday 2-min bars
bars = bdi("PETR4", "20260520")

# Macro series (FX, indices, commodities, rates)
fx = bmacro("USDBRL", "20260101", "20260520")

# Analyst consensus (DataFrame, one row per ticker)
df = bconsensus("PETR4")
print(df["buy"].iloc[0], df["target_mean"].iloc[0])

# Dividends history (ticker; CVM auto-resolved)
divs = bdividends("PETR4")

# Instrument search — retorna pd.DataFrame (schema unificado entre backends)
df = bsearch("PETR", exchange="BVMF")
print(df[["ticker", "name", "exchange"]].head())

# Real-time streaming
from py_bcast import BroadcastClient
with BroadcastClient() as bc:
    bc.subscribe(["PETR4", "VALE3"], ["ULT", "VAR"],
                 callback=lambda t, f, v: print(f"{t}.{f} = {v}"))
    bc.run(duration=60)
```

### Terminal Novo (`Broadcast+.exe`)

```python
from py_bcast import BroadcastPlusClient, btrades, bsearch, configure

# Headless: define BROADCAST_PLUS_TOKEN no ambiente, ou:
configure(plus_login="user@example.com", plus_password="...")

# Forca o backend Plus (ou deixa "auto" para detectar Broadcast+.exe rodando)
configure(terminal="plus")

# Instrument search via API
df = bsearch("PETR", max_results=5)
print(df[["ticker", "name", "exchange", "has_intraday"]])

# Times & trades intraday (DataFrame com DatetimeIndex em America/Sao_Paulo)
trades = btrades("PETR4", "20260525")
print(trades[["last", "size", "tendency"]].head())

# Streaming WebSocket
def on_quote(data: dict) -> None:
    print(data["COD"], data["ULT"], data["VAR"])

with BroadcastPlusClient() as client:
    client.subscribe(["PETR4", "VALE3"], callback=on_quote)
    client.run(duration=60)
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
├── __init__.py         # Public API (~45 exported symbols + async_api namespace)
├── _core/              # Shared infrastructure (both backends)
│   ├── config.py       # Settings dataclass + configure() (incl. terminal=, plus_login=, plus_password=)
│   ├── routing.py      # get_active_terminal() — picks legacy vs plus per call
│   ├── memory.py       # Win32 helpers: find_process_pid + scan_process_memory
│   ├── exceptions.py   # PyBcastError, SessionError, BroadcastPlusError, BroadcastPlusAuthError, …
│   ├── session.py      # Legacy session token discovery (memory scan of bcsys32.exe)
│   ├── constants.py    # Service names, URLs (legacy + plus), exchange normalization
│   ├── http.py         # Legacy ContentProxy httpx client pool
│   ├── cache.py        # Response cache (memory + diskcache)
│   ├── ratelimit.py    # Token-bucket rate limiter
│   ├── retry.py        # Tenacity retry decorator
│   ├── validation.py   # Pydantic types + @validate_params
│   └── (logging, dates, normalize, output, columns, resolve, xml_helpers, ...)
├── _plus/              # Broadcast+ backend
│   ├── session.py      # JWT auth chain: env → cache → refresh → memory scan → ECDH login
│   ├── crypto.py       # ECDH P-384 + AES-GCM-256 (matching app.asar buildEncryptedResult)
│   ├── http.py         # plus_request() with 401-refresh; singleton httpx.Client
│   ├── realtime.py     # BroadcastPlusClient (WebSocket /stock/ws)
│   └── intraday.py     # btrades() — POST /stock/v1/timesAndTrades
├── _async/             # Async versions of all legacy HTTP data functions
├── realtime/client.py  # Legacy DDE: BroadcastClient, bdp (one or many tickers)
├── historical/         # bdh, bdh_ohlcv, bdi, bdt (legacy ContentProxy)
├── macro/indicators.py # bmacro, bdi_cdi, breturn, bvolume, binflation
├── fundamental/        # bconsensus, bcompany, bindices, …, bcalendar, bdividends, …
├── news/api.py         # bnews, bnews_recent, bnews_multimedia
└── instruments/db.py   # InstrumentDB + bsearch (auto-routing legacy/plus)
tests/
├── conftest.py         # Resource-aware skips (legacy_session, legacy_db, plus markers)
├── test_session.py     # Session discovery + memory scanning
├── test_instruments.py # bsearch + InstrumentDB (legacy_db + plus)
├── test_historical.py, test_intraday.py, test_macro.py,
├── test_reference.py, test_events.py, test_fundamental.py  # legacy_session
└── ...
scripts/                # Utilities for data regeneration / probing
docs/
├── architecture.md         # Dual-backend overview + shared core
├── compatibility.md        # Legacy vs Plus feature mapping
├── legacy/                 # Terminal Antigo (bcsys32.exe)
│   ├── api.md              # API reference
│   ├── endpoints.md        # 227-endpoint status catalog
│   ├── internals.md        # DDE, ContentProxy, protocols
│   ├── fields.md           # DDE field reference (644 fields)
│   ├── instruments.md      # Instrument database details
│   ├── limitations.md      # Known limitations & workarounds
│   └── roadmap.md          # Implementation backlog
└── plus/                   # Terminal Novo (Broadcast+.exe)
    ├── api.md              # API reference (Plus functions)
    ├── endpoints.md        # Discovered endpoint catalog
    ├── internals.md        # Auth ECDH/JWT, WebSocket, schemas
    ├── limitations.md      # Known limitations & blockers
    └── roadmap.md          # Implementation backlog
```

## Documentation

- [Architecture](docs/architecture.md) — dual-backend overview, shared core
- [Compatibility](docs/compatibility.md) — Legacy vs Plus feature mapping
- **Terminal Antigo:** [API](docs/legacy/api.md) | [Endpoints](docs/legacy/endpoints.md) | [Internals](docs/legacy/internals.md) | [Limitations](docs/legacy/limitations.md) | [Roadmap](docs/legacy/roadmap.md)
- **Terminal Novo:** [API](docs/plus/api.md) | [Endpoints](docs/plus/endpoints.md) | [Internals](docs/plus/internals.md) | [Limitations](docs/plus/limitations.md) | [Roadmap](docs/plus/roadmap.md)

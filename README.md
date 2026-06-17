# py-bcast

Python client for **AE Broadcast** (Agência Estado) market data terminal — a Bloomberg `blpapi`/`xbbg`-like interface. Suporta os dois terminais em paralelo: **Antigo** (`bcsys32.exe`, DDE + ContentProxy) e **Novo** (`Broadcast+.exe`, JWT + WebSocket).

## Features

**Terminal Antigo (`bcsys32.exe`)**
- **Real-time streaming** via DDE (`bdp`, `subscribe`, `snapshot`)
- **Historical data** via HTTP — daily close/OHLCV range (`bhistory`/`bclose`), intraday bars (`bdi`), tick-by-tick (`bdt`)
- **Times & trades with top-of-book** (`bticks`) — TRD/QTE rows, broker ids, sessao corrente
- **Macroeconomic series** — FX, indices, commodities, CDI (`bmacro("CDI",...)`), inflation, returns
- **Fixed income** — Tesouro prices/yields (`btreasury`/`btreasury_history`), pre-fixado accrual (`baccrual`), poupanca (`bsavings`)
- **Market stats snapshot** (`bstats`) — DY, last dividend, 52-week range, avg volumes, para qualquer simbolo B3
- **Intraday snapshot** (`bsnapshot`) — OHLCV near-real-time sem DDE
- **Investment funds** — historico de cotas (`bfund_history`), retornos por janela (`bfund_returns`)
- **Spot FX conversion** (`bfx`) — taxa atual entre quaisquer pares
- **Fundamental data** — analyst consensus, indicators (Market Cap, Beta), company metadata, free float (`bfree_float`), top fund holders (`bfund_holders`), first close (`bfirst_close`)
- **Corporate events** — dividends, JCP, calendar, dividend yield, broker portfolios (`bportfolio`/`bportfolios_with`), shareholder dates (`bshareholder_dates`), filings S3 links (`bfilings`)
- **Credit** — sovereign/corporate CDS term-structure curves via Markit (`bcds`)
- **Reference data** — 1020 companies, 37 indices, 38 sectors, real-time quotes
- **News & multimedia** — full-text articles, Dow Jones wires, podcasts (no auth needed)
- **Instrument database** — 623K+ instruments across 30+ exchanges (local `aetp_17.dat`)

**Terminal Novo (`Broadcast+.exe`)**
- **Real-time streaming** via WebSocket (`BroadcastPlusClient` / asyncio `BroadcastPlusAsyncClient`) com auth refresh transparente
- **Market stats streaming** — `subscribe_market` transmite tabelas ao vivo da Bovespa: maiores altas/baixas, volume financeiro, evolucao do Ibovespa
- **Instrument metadata** (`binfo`) — nome, tipo, exchange, flags, CVM code; nunca retorna preco (preco exclusivo via WebSocket)
- **Times & trades** (`btrades`) — ultimos 500 trades em fuso `America/Sao_Paulo`; `ask_broker_id`/`bid_broker_id` fazem join com `bbrokers()`
- **Index composition** (`bindexes` + `bindex_members`) — lista de indices e composicao com pesos de relevancia; sem equivalente no terminal antigo
- **Instrument logo** (`blogo`) — bytes PNG do logo; sem equivalente no terminal antigo
- **Broker & exchange registries** (`bbrokers` + `bexchanges`) — corretoras (id, nome) e bolsas (id, nome, delay); decodificam os ids de `btrades` e `binfo`
- **Corporate events with adjustment factors** (`bcorpevents`) — dividendos, JCP, splits + `add_factor`, `calculated_factor`, `multiplicative_factor` que o `bdividends` legado nao expoe
- **Investment funds** (`bfunds` / `bfund`) — busca e detalhe: rentabilidade, taxas, CNPJ, ANBIMA; sem equivalente no terminal antigo
- **News (Plus feed)** (`bsections` + `bheadlines` + `bnews_content`) — 121 secoes, manchetes paginadas, corpo HTML + tagging estruturado (autores, entidades, topicos, localizacoes)
- **Holiday catalog** (`bholidays`) — catalogo de tabelas de feriados por pais/bolsa
- **Headless login** via ECDH P-384 + AES-GCM (`configure(plus_login=..., plus_password=...)`)
- **Token discovery** — memory scan do `Broadcast+.exe` ou `BROADCAST_PLUS_TOKEN` env var

**Compartilhado entre os backends**
- **Routing automatico** — `configure(terminal="auto"|"legacy"|"plus")`; `bsearch()` ja roteia
- **Async API** — `async_api` namespace com versoes async de todas as funcoes HTTP (prefixo `a`: `abinfo`, `abindex_members`, `abfunds`, `abcorpevents`, `abheadlines`, etc.)
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
pip install -e .
```

Todas as dependências (incluindo `pywin32`, necessário para DDE) são instaladas
automaticamente.

## Quick Start

### Terminal Antigo (`bcsys32.exe`)

```python
import os
os.environ["BROADCAST_SESSION"] = "<your_session_token>"

from py_bcast import bdp, bhistory, bdi, bmacro, bconsensus, bdividends, bsearch

# Real-time quote
price = bdp("PETR4", "ULT")

# Historical daily (works for ALL instruments) — flat DataFrame, ticker column
df = bhistory("PETR4", "20260501", "20260520")
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
from py_bcast import (
    BroadcastPlusClient,
    binfo, bindexes, bindex_members, blogo,
    bbrokers, bexchanges,
    bfunds, bfund,
    bsections, bheadlines, bnews_content,
    bcorpevents, bholidays,
    btrades, bsearch,
    configure,
)

# Headless: define BROADCAST_PLUS_TOKEN no ambiente, ou:
configure(plus_login="user@example.com", plus_password="...")

# Forca o backend Plus (ou deixa "auto" para detectar Broadcast+.exe rodando)
configure(terminal="plus")

# Metadata de instrumento (nunca preco — preco exclusivo via WebSocket)
df = binfo(["PETR4", "USDBRL"])
print(df[["name", "type", "currency"]])

# Indices disponiveis e composicao com pesos
print(bindexes()["index"].tolist())
df = bindex_members("IBOV")
print(df.sort_values("relevance", ascending=False).head())

# Logo PNG
open("petr4.png", "wb").write(blogo("PETR4"))

# Fundos de investimento
hits = bfunds("Verde")
print(hits[["id", "company", "profit_1y"]].head())
detail = bfund(hits["id"].iloc[0])

# Noticias Plus (secoes, manchetes, conteudo)
sections = bsections()
headlines = bheadlines(sections["id"].iloc[0], count=10)
article = bnews_content(headlines["id"].iloc[0])
print(article["title"], article["tagging"]["entities"])

# Eventos corporativos com fatores de ajuste
df = bcorpevents("PETR4")
print(df[["type", "effective_date", "calculated_factor"]])

# Catalogo de feriados (datas por tabela indisponiveis — param nao descoberto)
print(bholidays()[["id", "name"]])

# Times & trades intraday
trades = btrades("PETR4", "20260525")
print(trades[["price", "size", "tendency"]].head())

# Instrument search via API
df = bsearch("PETR", max_results=5)
print(df[["ticker", "name", "exchange", "has_intraday"]])

# Quote streaming
def on_quote(data: dict) -> None:
    print(data["COD"], data["ULT"], data["VAR"])

# Market stats streaming (tabelas ao vivo da Bovespa)
def on_market(data: dict) -> None:
    print(data["header"], data["rows"][:2])

with BroadcastPlusClient() as client:
    client.subscribe(["PETR4", "VALE3"], callback=on_quote)
    client.subscribe_market([0, 1], callback=on_market)  # maiores altas/baixas
    client.run(duration=60)
```

## DataFrame layout & `Ticker` objects

Every tabular function returns a **flat/long DataFrame with a `ticker` column** —
not a column MultiIndex like xbbg or `yfinance.download()`. Flat/long is the
canonical layout: it makes `groupby("ticker")`, `concat`, and Parquet/SQL
persistence trivial, and keeps the empty-result schema stable.

If you prefer the **wide** layout (`df["PETR4"]` selects one instrument), use the
opt-in `.bcast` accessor — it is a pure reshape, the default stays flat:

```python
df = bhistory(["PETR4", "VALE3"], "20260501", "20260520")   # flat: ticker column
wide = df.bcast.wide()          # column MultiIndex (ticker, field)
wide["PETR4"]["close"]          # select one instrument
wide.bcast.long()               # inverse, back to flat
```

`wide()` suits time-series frames (`bhistory`, `bmacro`, `breturn`, ...) where each
`(date, ticker)` pair is unique.

For an object-oriented style (like yfinance's `Ticker`), `Ticker` is a thin
facade over the `b*` functions — no new logic, just discoverability:

```python
from py_bcast import Ticker

petr = Ticker("PETR4")
petr.history("20260501", "20260520")   # -> bhistory
petr.dividends                          # -> bdividends
petr.quote                              # -> bquote
petr.indicators("EBITDA", "20260101", "20260520")  # -> bindicators
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
├── __init__.py         # Public API (93 exported symbols + async_api namespace)
├── _core/              # Backend-agnostic infrastructure (both backends)
│   ├── config.py       # Settings dataclass + configure() (incl. terminal=, plus_login=, plus_password=)
│   ├── routing.py      # get_active_terminal() — picks legacy vs plus per call
│   ├── memory.py       # Win32 helpers: find_process_pid + scan_process_memory
│   ├── exceptions.py   # PyBcastError, SessionError, BroadcastPlusError, BroadcastPlusAuthError, …
│   ├── constants.py    # Service names, URLs (legacy + plus), exchange normalization
│   ├── cache.py        # Response cache (memory + diskcache)
│   ├── ratelimit.py    # Token-bucket rate limiter
│   ├── retry.py        # Tenacity retry decorator
│   ├── validation.py   # Pydantic types + @validate_params
│   └── (logging, dates, normalize)
├── _legacy/            # Legacy protocol stack (DDE + ContentProxy; never imported by _plus)
│   ├── dde.py          # DDE conversations with bcsys32.exe
│   ├── http.py         # Legacy ContentProxy httpx client pool (sync + async singletons)
│   ├── session.py      # Legacy session token discovery (memory scan of bcsys32.exe)
│   ├── aetp.py         # Pure AETP protocol helpers (rows_to_dicts, entity tags)
│   ├── binary.py       # Binary response parser
│   ├── xml_helpers.py  # Pure ContentProxy XML parsing (parse_ticks, status policy)
│   ├── resolve_state.py # Shared sync/async resolution caches + pure matchers
│   ├── columns.py      # Column schemas + rename maps
│   ├── spec.py         # EndpointSpec / ParamBind declarative endpoint descriptors
│   ├── endpoints.py    # EndpointSpec catalog (one spec per migrated endpoint)
│   ├── output.py       # DataFrame finalization (finalize_frame, empty_history_frame)
│   ├── multi.py        # vectorize / vectorize_async multi-ticker fan-out
│   ├── _async/         # I/O layer SOURCE (async-first): transport, executor, resolve, quote, historical
│   └── _sync/          # I/O layer GENERATED from _async/ by scripts/gen_sync.py — do not edit
├── _plus/              # Broadcast+ backend
│   ├── session.py      # JWT auth chain: env → cache → refresh → memory scan → ECDH login
│   ├── crypto.py       # ECDH P-384 + AES-GCM-256 (matching app.asar buildEncryptedResult)
│   ├── http.py         # Plus httpx client singletons (sync + async) + auth headers
│   ├── realtime.py     # BroadcastPlusClient (WebSocket /stock/ws) — quotes + market stats
│   ├── intraday.py     # btrades() facade — POST /stock/v1/timesAndTrades
│   ├── reference.py    # binfo, bindexes, bindex_members, blogo, bholidays, bbrokers, bexchanges
│   ├── funds.py        # bfunds, bfund — POST /funds/v1/search, GET /funds/v1/{id}
│   ├── news.py         # bsections, bheadlines, bnews_content
│   ├── corporate.py    # bcorpevents — POST /stock/v1/corporateevents/{symbol}
│   ├── _async/         # Plus I/O SOURCE (async-first): plus_request, trades core
│   └── _sync/          # Plus I/O GENERATED from _async/ by scripts/gen_sync.py — do not edit
├── _async/             # Async versions of all legacy HTTP data functions
├── realtime/client.py  # Legacy DDE: BroadcastClient, bdp (one or many tickers)
├── historical/         # bhistory, bclose, bdi, bdt, bticks, bfirst_close (legacy ContentProxy)
├── fixedincome.py      # btreasury, btreasury_history, baccrual, bsavings
├── funds.py            # bfund_history, bfund_returns
├── macro/indicators.py # bmacro (inclui CDI), breturn, bvolume, binflation, bstats, bsnapshot, bfx
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

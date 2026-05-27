# API Reference — Terminal Antigo (bcsys32.exe)

Referencia da API publica da lib para o backend do Terminal Antigo (`bcsys32.exe` + ContentProxy `cp.ae.com.br:44780`).

Para equivalentes no Terminal Novo, ver [`../plus/api.md`](../plus/api.md).

---

## Real-Time Data (DDE)

Requires `bcsys32.exe` running on the same machine.

### `bdp(ticker, fields)`

One-shot reference data request (like Bloomberg's BDP).

```python
from py_bcast import bdp

price = bdp("PETR4", "ULT")           # "45.99"
data = bdp("PETR4", ["ULT", "VAR"])   # {"ULT": "45.99", "VAR": "-1.2"}
```

### `bdps(tickers, fields)`

Batch request for multiple tickers.

```python
from py_bcast import bdps

result = bdps(["PETR4", "VALE3", "ITUB4"], ["ULT", "VAR"])
# {"PETR4": {"ULT": "45.99", ...}, "VALE3": {...}, ...}
```

### `BroadcastClient`

Full-featured client with streaming support.

```python
from py_bcast import BroadcastClient

with BroadcastClient() as bc:
    # One-shot
    price = bc.request("PETR4", "ULT")
    snap = bc.snapshot("PETR4")  # all 56 fields

    # Streaming
    bc.subscribe(["PETR4", "VALE3"], ["ULT", "VAR"],
                 callback=lambda t, f, v: print(f"{t}.{f} = {v}"))
    bc.run(duration=60)

    # Skip invalid tickers instead of raising
    from py_bcast import DDEAdviseError
    errors = bc.subscribe(["PETR4", "INVALID999"], ["ULT"],
                          callback=my_callback, skip_unavailable=True)
    if errors:
        print(f"Could not subscribe: {[e.item for e in errors]}")
```

**Methods:**

| Method | Description |
|--------|-------------|
| `connect()` | Establish DDE connection |
| `disconnect()` | Clean up connections |
| `request(ticker, fields)` | One-shot value request |
| `snapshot(ticker)` | Full 56-field snapshot |
| `subscribe(tickers, fields, callback, skip_unavailable=False)` | Start streaming; returns `list[DDEAdviseError]` for failed items |
| `unsubscribe(tickers, fields)` | Stop specific streams |
| `unsubscribe_all()` | Stop all streams |
| `run(duration=None)` | Blocking message pump |
| `run_async(duration=None)` | Non-blocking (background thread) |
| `stop()` | Signal pump to stop |

---

## Historical Data (HTTP)

Requires `BROADCAST_SESSION` environment variable set with a valid BCAA session token.

### `bdh(tickers, start_date, end_date)`

Historical daily closing prices. Works for **all** instruments.

```python
from py_bcast import bdh

# Single ticker
data = bdh("PETR4", "20260501", "20260520")
df = data["PETR4.BVMF"]   # DataFrame with DatetimeIndex
print(df["close"])          # closing price series

# Multiple tickers
data = bdh(["PETR4", "VALE3", "USDBRL"], "20260515", "20260520")
```

**Returns:** `dict[symbol, DataFrame]` — each DataFrame has a DatetimeIndex and columns: `close`, `settle`, `settle_rate`, `yield`.

### `bdh_ohlcv(ticker, date)`

Full OHLCV for a single ticker on a single date.

```python
from py_bcast import bdh_ohlcv

bar = bdh_ohlcv("PETR4", "20260519")
print(bar["close"], bar["high"], bar["low"], bar["open"])
print(bar["trades"], bar["volume"], bar["turnover"])
```

**Returns:** `Series` with index: `close`, `settle`, `settle_rate`, `low`, `high`, `open`, `trades`, `volume`, `turnover`, `open_interest`, `vwap`, `cum_trades`. Empty Series if no data.

### `bdi(ticker, start_date)`

Intraday 2-minute OHLCV bars. Works for **all instruments** (B3 + international).

```python
from py_bcast import bdi

# Today's intraday bars for PETR4
df = bdi("PETR4", "20260520")   # DataFrame with DatetimeIndex
print(df[["open", "high", "low", "close", "volume", "trades"]].tail())

# Multiple days of intraday data
df = bdi("USDBRL", "20260515")  # from May 15 to now
```

**Returns:** `DataFrame` with DatetimeIndex and columns: `open`, `high`, `low`, `close`, `volume`, `trades`, `turnover`, `open_interest`, `cum_trades`, `session_type`.

**Notes:**
- Bars are 2-minute candles (server-determined granularity)
- `session_type`: 1=regular session, 5=after-hours, 9=closing auction
- Can go back up to ~1.5 years (77K+ bars for B3 stocks)
- Data is from `start_date` up to the current time

### `bdt(ticker, start, end=None)`

Tick-by-tick trade data. Works for **international instruments only**.

```python
from py_bcast import bdt

df = bdt("USDBRL", "20260519100000", "20260519110000")
print(df["close"])  # tick prices with DatetimeIndex
```

**Returns:** `DataFrame` with DatetimeIndex and columns: `close`, `size`, `trades`, `open_interest`, `calendar_days`, `working_days`.

**Supported symbols:** USDBRL, EURUSD, GBPUSD, USDJPY, AUDUSD, USDCAD, USDCHF, NZDUSD, USDCNY, USDMXN, EURBRL, GBPBRL, JPYBRL, CHFBRL, AUDBRL, CADBRL, GOLD, SILVER, WTI, DAX, FTSE, VIX, DXY, US10Y, US2Y.

---

## Fundamental Data (HTTP)

### `bconsensus(ticker)`

Analyst consensus recommendations and target prices.

```python
from py_bcast import bconsensus

data = bconsensus("PETR4")
# {'buy': '3', 'hold': '2', 'sell': '0', 'total_analysts': '5',
#  'target_low': '43.00', 'target_high': '64.00',
#  'target_mean': '48.60', 'target_median': '45.00', 'upside_pct': '8.7350'}
```

**Returns:** `dict` with keys: buy, hold, sell, total_analysts, target_low, target_high, target_mean, target_median, upside_pct. Empty dict if no data.

---

## Macroeconomic & Fixed Income (HTTP)

### `bmacro(ticker, start_date, end_date)`

Macroeconomic/index historical series — FX, indices, commodities, rates, AETAXAS indicators.

```python
from py_bcast import bmacro

# FX history
df = bmacro("USDBRL", "20260101", "20260520")
print(df["close"].tail())

# Inflation index (AETAXAS)
df = bmacro("AEIPCA", "20250101", "20260520")

# Commodities
df = bmacro("GOLD", "20200101", "20260520")
```

**Supported symbols:** USDBRL, EURUSD, IBOV, SPX, DAX, GOLD, WTI, DI1F27, AEIPCA, AEIGPM, AECTIP, AEB052, AEB200, AEFS10, and many more.

**Returns:** `DataFrame` with DatetimeIndex sorted chronologically. Columns vary but typically include: `close`, `open`, `high`, `low`, `settle`, `change_pct`, `trades`, `volume`.

### `bdi_cdi(start_date, end_date)`

Accumulated CDI (DI-CETIP) series. Data available since 1986.

```python
from py_bcast import bdi_cdi

df = bdi_cdi("20260101", "20260520")
print(df["close"].iloc[-1])  # accumulated %
```

**Returns:** `DataFrame` with DatetimeIndex sorted chronologically. Columns: `close`, `change_pct`, `accumulated`.

### `breturn(ticker, start_date, end_date)`

Adjusted daily returns for a symbol.

```python
from py_bcast import breturn

df = breturn("PETR4", "20260101", "20260520")
print(df["close"].tail())
```

**Returns:** `DataFrame` with DatetimeIndex sorted chronologically. Columns: `close`.

### `bvolume(tickers)`

Average volume statistics (1m/2m/3m/6m averages).

```python
from py_bcast import bvolume

df = bvolume(["PETR4", "VALE3"])
print(df[["avg_volume", "avg_turnover", "avg_trades", "months"]])
```

**Returns:** `DataFrame` indexed by symbol with columns: `avg_volume`, `avg_turnover`, `avg_trades`, `months`.

### `binflation()`

Snapshot of inflation indices with monthly and accumulated periods.

```python
from py_bcast import binflation

df = binflation()  # ~17 indices (IPCA, IGP-M, INPC, etc.)
print(df[["close", "return_3m", "return_6m", "return_12m", "return_ytd"]])
```

**Returns:** `DataFrame` with columns: `close`, `return_3m`, `return_6m`, `return_12m`, `return_ytd`.

---

## Reference Data (HTTP — aetp/output binary)

### `bcompany(cvm_code=None)`

Company metadata. Without argument returns all ~1020 companies; with CVM code returns detail.

```python
from py_bcast import bcompany

companies = bcompany()         # all companies (1020)
petr = bcompany(9512)          # Petrobras detail
```

**CVM codes:** PETR=9512, VALE=4170, ITUB=19348, BBDC=906.

### `bindices()`

List of B3 market indices (~37: IBOV, IBRX, SMLL, IDIV, etc.).

```python
from py_bcast import bindices

df = bindices()
print(df[["ticker", "name"]])
```

### `bsectors()`

B3 sector/subsector/segment classification (~38 sectors).

```python
from py_bcast import bsectors

sectors = bsectors()
```

### `bquote(ticker)`

Current quote (price, volume) for a symbol via aetp.

```python
from py_bcast import bquote

q = bquote("PETR4")
print(q["close"], q["volume"])  # 46.09, 1500000
```

### `btickers(ticker_or_cvm)`

All tickers (stocks/units) for a company. Accepts a ticker string (CVM auto-resolved) or a CVM code directly.

```python
from py_bcast import btickers

df = btickers("PETR4")  # auto-resolves CVM
df = btickers(9512)     # direct CVM code — same result
print(df["ticker"].tolist())  # ['PETR3', 'PETR4']
```

### `bshares(ticker)`

Shares outstanding for a ticker.

```python
from py_bcast import bshares

data = bshares("PETR4")
```

### `bindicators(ticker_or_cvm, indicator, start_date, end_date)`

Daily fundamental indicator history.

Accepts a **ticker string or CVM code** and an **indicator name or numeric ID**. Use `bindicator_meta()` to discover all available indicators.

```python
from py_bcast import bindicators

# By ticker + indicator name (recommended)
ebitda = bindicators("PETR4", "EBITDA", "20260101", "20260520")
beta   = bindicators("PETR4", "Beta AE", "20260101", "20260520")
roe    = bindicators("VALE3", "ROE", "20260101", "20260520")

# By CVM code + numeric ID (still works)
mcap   = bindicators(9512, 32, "20260101", "20260520")
```

**Indicator name matching:** case-insensitive, accent-insensitive. Exact match preferred over prefix/contains. Raises `ValidationError` if ambiguous.

### `bindicator_meta()`

Metadata for all ~80 available fundamental indicators.

```python
from py_bcast import bindicator_meta

meta = bindicator_meta()
```

---

## Corporate Events & Dividends (HTTP — aetp/output binary)

### `bcalendar(start_date, end_date)`

Corporate events calendar (dividends, JCP, splits, AGMs, etc.).

```python
from py_bcast import bcalendar

events = bcalendar("20260101", "20260520")  # ~1600+ events
```

### `bdividends(ticker, cvm_code=None)`

Dividend/JCP payment history for a company. CVM code is auto-resolved from the ticker if not provided.

```python
from py_bcast import bdividends

divs = bdividends("PETR4")           # ticker-only (recommended)
divs = bdividends("PETR4", 9512)     # explicit CVM — skips resolution
```

### `bdy(ticker, start_date, end_date, cvm_code=None)`

Dividend yield historical series. CVM code is auto-resolved from the ticker if not provided.

```python
from py_bcast import bdy

dy = bdy("PETR4", "20250101", "20260520")           # ticker-only (recommended)
dy = bdy("PETR4", "20250101", "20260520", cvm_code=9512)  # explicit CVM
```

### `bportfolios()`

List of brokers that publish model portfolios.

```python
from py_bcast import bportfolios

brokers = bportfolios()
print(brokers[["broker_id", "name"]])
```

### `bportfolio(broker_id)`

Latest recommended portfolio from a specific broker.

```python
from py_bcast import bportfolio

holdings = bportfolio(27)
```

---

## News & Multimedia (HTTP — CentralMultimidia)

No authentication required. Access all Broadcast news (AE-News, Dow Jones, Press Releases, Trading News, podcasts, etc.) via sequential numeric IDs.

### `bnews(news_id)`

Fetch a single news article by its numeric ID.

```python
from py_bcast import bnews

article = bnews(56134402)
print(article["title"])    # "Fique de Olho: Azzas contrata Itau BBA..."
print(article["content"])  # HTML body text
print(article["files"])    # [{"filename": "...", "extension": "mp4", "url": "..."}]
```

**Returns:** `dict` with keys: title, content, files. Empty dict if ID doesn't exist.

**Notes:**
- IDs are sequential integers (currently ~56M range)
- Covers ALL content types: text news, Dow Jones newswires, press releases, podcasts, multimedia
- Content is HTML (may contain `<br/>`, `<PRE>`, `<span>` tags)
- Files list contains attached media (mp4, png) with direct download URLs

### `bnews_latest(count=10)`

Fetch the most recent news articles.

```python
from py_bcast import bnews_latest

for article in bnews_latest(5):
    print(f"[{article['id']}] {article['title'][:60]}")
```

**Returns:** `list[dict]` with keys: id, title, content, files. Most recent first. Max 100.

**Notes:**
- Uses binary search to find the current ID ceiling, then scans backwards
- First call may take a few seconds (binary search); subsequent IDs are sequential

### `bnews_search(category, days_ago=60, limit=20)`

List multimedia/podcast content from a specific category.

```python
from py_bcast import bnews_search, MULTIMEDIA_CATEGORIES

# List available categories
for cat_id, name in MULTIMEDIA_CATEGORIES.items():
    print(f"{cat_id}: {name}")

# Get recent podcasts
items = bnews_search(748)  # 748 = Podcast
for item in items:
    print(f"[{item['id']}] {item['date']} {item['title']}")

# Get full content for a listed item
article = bnews(items[0]["id"])
for f in article["files"]:
    if f["extension"] == "mp4":
        print(f"Audio: {f['url']}")
```

**Parameters:**
- `category` — Category ID (see `MULTIMEDIA_CATEGORIES` dict)
- `days_ago` — How far back to look (default 60)
- `limit` — Max results (default 20)

**Returns:** `list[dict]` with keys: id, title, date, time.

**Available categories:** Comentario Financeiro (567), Comentario Agricola (566), Podcast (748), Comentario Politico (848), Cabeca de Gestor (849), E-Investidor-Midia (857), Capital Insights (1133), Credito Privado 360 (1160).

---

## Utilities

### `resolve_cvm(ticker)`

Resolve a B3 ticker to its CVM company code. Results are cached for the process lifetime.

```python
from py_bcast import resolve_cvm

cvm = resolve_cvm("PETR4")  # 9512
cvm = resolve_cvm("VALE3")  # 4170

# Useful when you need the CVM code for other purposes
from py_bcast import bcompany
detail = bcompany(resolve_cvm("ITUB4"))
```

Raises `ValidationError` if the ticker cannot be resolved.

### `resolve_indicator(name_or_id)`

Resolve an indicator name to its numeric ID. Accepts exact names, prefixes, or substrings (case/accent insensitive).

```python
from py_bcast import resolve_indicator

resolve_indicator("EBITDA")          # 11
resolve_indicator("roe")             # 24  (case-insensitive)
resolve_indicator("Beta AE")         # 52
resolve_indicator(32)                # 32  (passthrough for ints)
```

Raises `ValidationError` if the name is ambiguous or not found. Use `bindicator_meta()` to list all available indicators.

### `clear_token_cache()`

Force re-discovery of the session token on the next API call. Useful when the Broadcast terminal is restarted and the cached token becomes stale.

```python
from py_bcast import clear_token_cache

clear_token_cache()  # next call will re-scan bcsys32.exe memory
```

---

## Configuration

### `configure(**kwargs)`

Adjust library-wide settings at runtime. All keyword arguments correspond to fields on `Settings`.

```python
from py_bcast import configure

configure(
    timeout=60,              # HTTP request timeout in seconds (default 30)
    max_retries=5,           # Tenacity retry attempts (default 3)
    cache_enabled=True,      # Enable response caching (default True)
    cache_backend="memory",  # "memory" | "disk" (default "memory")
    cache_ttl=600,           # Default TTL in seconds (default 300)
    cache_ttl_realtime=5,    # TTL for real-time quotes (default 5)
    rate_limit_calls=10,     # Max requests per period (default 20)
    rate_limit_period=1.0,   # Period in seconds (default 1.0)
)
```

### `get_settings()` / `Settings`

Inspect current settings.

```python
from py_bcast import get_settings

s = get_settings()
print(s.timeout, s.cache_enabled, s.cache_backend)
```

### `cache_invalidate(key=None)`

Clear cached responses. Without arguments clears the entire cache.

```python
from py_bcast import cache_invalidate

cache_invalidate()                          # clear all
cache_invalidate("bdh:PETR4:...")           # clear specific key
```

---

## Async API

All HTTP data functions have async equivalents in the `py_bcast._async` namespace, prefixed with `a` (e.g. `abdh`, `abmacro`). They share the same connection pool, cache, and rate limiter as the sync API.

```python
import asyncio
from py_bcast._async import abdh, abmacro, abconsensus, abnews_latest

async def main():
    # Historical prices
    data = await abdh(["PETR4", "VALE3"], "20260501", "20260520")

    # Macro series
    fx = await abmacro("USDBRL", "20260101", "20260520")

    # Analyst consensus
    c = await abconsensus("PETR4")

    # Parallel fetch (asyncio.gather)
    data, fx, c = await asyncio.gather(
        abdh("PETR4", "20260501", "20260520"),
        abmacro("USDBRL", "20260101", "20260520"),
        abconsensus("PETR4"),
    )

asyncio.run(main())
```

Alternatively via the namespace:

```python
from py_bcast import async_api

data = asyncio.run(async_api.abdh("PETR4", "20260501", "20260520"))
```

**Available async functions:**

| Async | Sync equivalent | Module |
|-------|----------------|--------|
| `abdh` | `bdh` | `_async.historical` |
| `abdh_ohlcv` | `bdh_ohlcv` | `_async.historical` |
| `abdi` | `bdi` | `_async.historical` |
| `abdt` | `bdt` | `_async.historical` |
| `abmacro` | `bmacro` | `_async.macro` |
| `abdi_cdi` | `bdi_cdi` | `_async.macro` |
| `abreturn` | `breturn` | `_async.macro` |
| `abvolume` | `bvolume` | `_async.macro` |
| `abinflation` | `binflation` | `_async.macro` |
| `abconsensus` | `bconsensus` | `_async.fundamental` |
| `abcompany` | `bcompany` | `_async.fundamental` |
| `abquote` | `bquote` | `_async.fundamental` |
| `abtickers` | `btickers` | `_async.fundamental` | accepts ticker or CVM code |
| `abshares` | `bshares` | `_async.fundamental` |
| `abnews` | `bnews` | `_async.news` |
| `abnews_latest` | `bnews_latest` | `_async.news` |
| `abnews_search` | `bnews_search` | `_async.news` |

> **Note:** `abnews_latest` uses `asyncio.gather` internally for parallel article fetches, which is significantly faster than the sequential sync version.

---

## Instrument Database

### `bsearch(query, exchange=None, max_results=20)`

Search 623K+ instruments by ticker, name, or ISIN. **Roteia automaticamente** entre Legacy (banco local `aetp_17.dat`) e Plus (`POST /stock/v1/quote/symbol/search`) — ver [`configure(terminal=...)`](../plus/api.md#roteamento-de-backend).

**Retorna:** `pd.DataFrame` com schema unificado entre os dois backends. Colunas exclusivas de um backend ficam como `pd.NA` quando o outro responde.

| Coluna | Tipo | Origem |
|--------|------|--------|
| `ticker` | `string` | Ambos |
| `name` | `string` | Ambos |
| `exchange` | `string` (codigo: `"BVMF"`, `"CME"`, ...) | Ambos — Plus normalizado via `normalize_exchange()` |
| `backend` | `category` (`"legacy"` ou `"plus"`) | Ambos |
| `full_symbol` | `string` (`"PETR4.BVMF"`) | Legacy |
| `isin` | `string` | Legacy |
| `cvm_code` | `Int64` | Plus |
| `type_id`, `market_id`, `exchange_id` | `Int64` | Plus |
| `has_intraday`, `has_daily`, `is_realtime` | `boolean` | Plus |

```python
from py_bcast import bsearch

df = bsearch("PETR", exchange="BVMF")
df.iloc[0]["ticker"]         # 'PETR4'
df[df.ticker == "PETR4"]      # filtros pandas idiomaticos

bsearch("VIX", exchange="CBOEI")
bsearch("BRPETRACNPR6")       # busca por ISIN (Legacy)
```

A constante `INSTRUMENT_COLUMNS` em `py_bcast.instruments.db` define a ordem estavel das colunas.

### `InstrumentDB`

Acesso direto ao singleton do banco local de instrumentos (Legacy). Carrega lazy na primeira chamada de `.get()`.

```python
from py_bcast import InstrumentDB

db = InstrumentDB.get()
inst = db.lookup("PETR4")
# {'ticker': 'PETR4', 'name': 'PETROLEO BRASILEIRO...', 'exchange': 'BVMF',
#  'backend': 'legacy', 'full_symbol': 'PETR4.BVMF', 'isin': 'BRPETRACNPR6',
#  'cvm_code': None, 'has_intraday': None, ...}

db.search("PETR", exchange="BVMF")   # mesmo schema do bsearch (pd.DataFrame)
len(db)                              # 623247
db.exchanges                         # {"PR": 189985, "BVMF": 138181, ...}
```

`lookup()` retorna um `dict` (single instrument) com as mesmas chaves do DataFrame — campos Plus-only ficam como `None`.

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `BROADCAST_SESSION` | For HTTP functions (except news) | BCAA session token (hex string). If not set, auto-discovered from running `bcsys32.exe` process memory (one-time cost ~5s; result is cached for the process lifetime). |

> **Tip:** Set `BROADCAST_SESSION` in your shell profile or `.env` to eliminate the startup cost entirely.

> **Note:** News functions (`bnews`, `bnews_latest`, `bnews_search`) do NOT require a session token.

## Error Handling

All exceptions inherit from `PyBcastError`.

| Exception | Raised when |
|-----------|-------------|
| `SessionError` | Session token is missing or invalid |
| `ContentProxyError` | ContentProxy HTTP endpoint returned an error status |
| `ProtocolError` | Binary SOH response is malformed or contains an error |
| `DDEError` | DDE connection failed or request timed out |
| `DDEAdviseError` | DDE advise (subscription) failed for a specific item (subclass of `DDEError`) |
| `ValidationError` | Input parameter validation failed (also a `ValueError`) |
| `FileNotFoundError` | Instrument database not found (`bcsys32` never ran) |

**Structured exception attributes:**

`ContentProxyError` exposes:
- `.endpoint` — API path that failed (e.g. `"BaseHistoricaNumerica/HistoricoFechamentos"`)
- `.server_message` — raw `<MESSAGE>` text from the XML response
- `.status_code` — HTTP status code, if available

`ProtocolError` exposes:
- `.error_tag` — error message extracted from tag 10037 in the binary response
- `.record_count` — number of records found when the response was malformed

Both exceptions append an English **hint** to their `str()` output when the server message matches a known pattern (e.g. `"Nao foram encontrados registros..."` -> `"No records found for the given criteria"`).

`DDEAdviseError` exposes:
- `.item` — full DDE item string (e.g. `"EMBR3.ULT"`)
- `.ticker` / `.field` — parsed portions of `.item`
- `.error_code` — DDEML error code; look up name with `DMLERR_NAMES[e.error_code]`

```python
from py_bcast import ContentProxyError, SessionError, DDEAdviseError, DMLERR_NAMES

try:
    data = bdh("PETR4", "20260501", "20260520")
except SessionError:
    print("Set BROADCAST_SESSION env var")
except ContentProxyError as e:
    print(f"Server error on {e.endpoint}: {e.server_message}")

# Inspect DDE advise failures
try:
    bc.subscribe(["PETR4"], ["ULT"], callback=cb)
except DDEAdviseError as e:
    print(f"{e.item} failed: {DMLERR_NAMES.get(e.error_code, hex(e.error_code))}")
```

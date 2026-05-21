# API Reference

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

### `btickers(cvm_code)`

All tickers (stocks/units) for a company by CVM code.

```python
from py_bcast import btickers

df = btickers(9512)
print(df[["ticker", "type"]])  # PETR3, PETR4
```

### `bshares(ticker)`

Shares outstanding for a ticker.

```python
from py_bcast import bshares

data = bshares("PETR4")
```

### `bindicators(cvm_code, indicator_id, start_date, end_date)`

Daily fundamental indicator history. Known IDs: 32=Market Cap, 52=Beta.

```python
from py_bcast import bindicators

mcap = bindicators(9512, 32, "20260101", "20260520")  # Market Cap daily
beta = bindicators(9512, 52, "20260101", "20260520")  # Beta daily
```

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

### `bdividends(cvm_code, ticker)`

Dividend/JCP payment history for a company.

```python
from py_bcast import bdividends

divs = bdividends(9512, "PETR4")
for d in divs:
    print(d)
```

### `bdy(cvm_code, ticker, start_date, end_date)`

Dividend yield historical series.

```python
from py_bcast import bdy

dy = bdy(9512, "PETR4", "20250101", "20260520")
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
print(article["title"])    # "Fique de Olho: Azzas contrata Itaú BBA..."
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

**Available categories:** Comentário Financeiro (567), Comentário Agrícola (566), Podcast (748), Comentário Político (848), Cabeça de Gestor (849), E-Investidor-Mídia (857), Capital Insights (1133), Crédito Privado 360 (1160).

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
| `abtickers` | `btickers` | `_async.fundamental` |
| `abshares` | `bshares` | `_async.fundamental` |
| `abnews` | `bnews` | `_async.news` |
| `abnews_latest` | `bnews_latest` | `_async.news` |
| `abnews_search` | `bnews_search` | `_async.news` |

> **Note:** `abnews_latest` uses `asyncio.gather` internally for parallel article fetches, which is significantly faster than the sequential sync version.

---

## Instrument Database

### `bsearch(query, exchange=None, max_results=20)`

Search 623K+ instruments by ticker, name, or ISIN.

```python
from py_bcast import bsearch

bsearch("PETR", exchange="BVMF")
# [{'ticker': 'PETR3', 'full_symbol': 'PETR3.BVMF',
#   'name': 'PETROLEO BRASILEIRO...', 'isin': 'BRPETRACNOR2', 'exchange': 'BVMF'}, ...]

bsearch("VIX", exchange="CBOEI")
# [{'ticker': 'VIX', 'full_symbol': 'I:VIX.CBOEI', ...}]

bsearch("BRPETRACNPR6")  # search by ISIN
# [{'ticker': 'PETR4', ...}]
```

### `InstrumentDB`

Direct access to the instrument database singleton.

```python
from py_bcast import InstrumentDB

db = InstrumentDB.get()
db.lookup("PETR4")    # exact match → dict or None
len(db)               # 623247
db.exchanges          # {"PR": 189985, "BVMF": 138181, ...}
```

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `BROADCAST_SESSION` | For HTTP functions (except news) | BCAA session token (hex string) |

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

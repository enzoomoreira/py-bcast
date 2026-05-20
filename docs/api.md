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
```

**Methods:**

| Method | Description |
|--------|-------------|
| `connect()` | Establish DDE connection |
| `disconnect()` | Clean up connections |
| `request(ticker, fields)` | One-shot value request |
| `snapshot(ticker)` | Full 56-field snapshot |
| `subscribe(tickers, fields, callback)` | Start streaming |
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
for row in data["PETR4.BVMF"]:
    print(row["date"], row["last"])  # "20260502" "36.50"

# Multiple tickers
data = bdh(["PETR4", "VALE3", "USDBRL"], "20260515", "20260520")
```

**Returns:** `dict[symbol, list[{date, last, settle, settle_rate, yield, dattol}]]`

### `bdh_ohlcv(ticker, date)`

Full OHLCV for a single ticker on a single date.

```python
from py_bcast import bdh_ohlcv

bar = bdh_ohlcv("PETR4", "20260519")
# {'dat': '20260519', 'last': '46.09', 'high': '46.3',
#  'low': '45.59', 'open': '45.99', 'neg': '68632', ...}
```

**Returns:** `dict` with keys: dat, last, settle, low, high, open, neg, qtt, total_value, open_interest, vwap, total_neg. Empty dict if no data.

### `bdi(ticker, start_date)`

Intraday 2-minute OHLCV bars. Works for **all instruments** (B3 + international).

```python
from py_bcast import bdi

# Today's intraday bars for PETR4
bars = bdi("PETR4", "20260520")
for bar in bars[-3:]:
    print(f"{bar['hor']} O={bar['open']} H={bar['high']} L={bar['low']} C={bar['last']}")

# Multiple days of intraday data
bars = bdi("USDBRL", "20260515")  # from May 15 to now
```

**Returns:** `list[{dat, hor, open, high, low, last, qtt, neg, total_value, open_interest, total_neg, tipo_intervalo}]`

**Notes:**
- Bars are 2-minute candles (server-determined granularity)
- `tipo_intervalo`: 1=regular session, 5=after-hours, 9=closing auction
- Can go back up to ~1.5 years (77K+ bars for B3 stocks)
- Data is from `start_date` up to the current time

### `bdt(ticker, start, end=None)`

Tick-by-tick trade data. Works for **international instruments only**.

```python
from py_bcast import bdt

ticks = bdt("USDBRL", "20260519100000", "20260519110000")
for t in ticks:
    print(f"{t['hor']} {t['last']}")  # "10:01:28.632 4.9948"
```

**Returns:** `list[{dat, hor, last, size, neg, open_interest, calendar_days, working_days}]`

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
| `BROADCAST_SESSION` | For HTTP functions | BCAA session token (hex string) |

## Error Handling

- `ValueError` — missing session token
- `RuntimeError` — ContentProxy returned error status
- `FileNotFoundError` — instrument database not found (bcsys32 never ran)
- `ConnectionError` — HTTP endpoint unreachable

# API Reference — Terminal Antigo (bcsys32.exe)

Referencia da API publica da lib para o backend do Terminal Antigo (`bcsys32.exe` + ContentProxy `cp.ae.com.br:44780`).

Para equivalentes no Terminal Novo, ver [`../plus/api.md`](../plus/api.md).

---

## Real-Time Data (DDE)

Requires `bcsys32.exe` running on the same machine.

### `bdp(ticker, fields)`

One-shot reference data request (like Bloomberg's BDP). Accepts a single ticker
**or a list**. Numeric values (prices, percentages) come back as `float`; codes
and text stay strings; unavailable fields are `None`.

```python
from py_bcast import bdp

price = bdp("PETR4", "ULT")            # 45.99
data  = bdp("PETR4", ["ULT", "VAR"])   # {"ULT": 45.99, "VAR": -1.2}

# Many tickers -> dict keyed by ticker
batch = bdp(["PETR4", "VALE3", "ITUB4"], ["ULT", "VAR"])
# {"PETR4": {"ULT": 45.99, ...}, "VALE3": {...}, ...}
```

> **Changed in 0.6.0:** `bdps` was removed — `bdp` now accepts a list of tickers
> and returns a dict keyed by ticker. Numeric values are parsed to `float`
> (Brazilian-formatted strings like `"1.234,56"` become `1234.56`).

> **Contract note:** `bdp` is the **one deliberate exception** to the library's
> "every tabular function returns a flat DataFrame with a `ticker` column" rule.
> Like Bloomberg's `BDP`, it is a scalar/point lookup and returns a scalar, a
> dict of fields, or a dict-of-dicts keyed by ticker — never a DataFrame. Every
> other public data function (`bhistory`, `bmacro`, `bconsensus`, …) follows the
> DataFrame+`ticker` contract.

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

### `bhistory(tickers, start_date, end_date, fields="close")`

Historico de precos diarios para um ou mais tickers. Ponto de entrada unificado (Bloomberg-BDH-like).

```python
from py_bcast import bhistory, bclose

# Close/settle (default) — 1 request por ticker para a janela toda
df = bhistory("PETR4", "20260501", "20260520")
print(df["close"].tail())

# Multiple tickers — flat frame, uma coluna ticker
df = bhistory(["PETR4", "VALE3", "USDBRL"], "20260515", "20260520")

# OHLCV range
ohlcv = bhistory("PETR4", "20260501", "20260519", fields="ohlcv")

# bclose: atalho para fields="close"
df = bclose(["PETR4", "VALE3"], "20260101")
```

**Retorna (`fields="close"`):** `DataFrame` com `DatetimeIndex`, um bloco por ticker. Colunas: `ticker`, `close`, `settle`, `settle_rate`, `yield`, `net_asset` (fundos). DataFrame vazio com o schema se sem dados.

**Retorna (`fields="ohlcv"`):** `DataFrame` com `DatetimeIndex`, um bloco por ticker. Colunas: `ticker`, `close`, `settle`, `settle_rate`, `low`, `high`, `open`, `trades`, `volume`, `turnover`, `open_interest`, `vwap`, `cum_trades`.

> **Alterado em 0.7.0 (BREAKING):** `bdh` e `bdh_ohlcv` foram removidos; substitua por `bhistory` ou `bclose`. Ver [`../../compatibility.md`](../../compatibility.md). O ticker de saida e bare (ex.: `PETR4`, nao `PETR4.BVMF`). A perna ohlcv tambem corrige um bug latente do antigo `bdh_ohlcv` que lia apenas o primeiro tick (pregao mais recente, nao a data pedida).

### `bdi(ticker, start_date)`

Intraday 2-minute OHLCV bars. Works for **all instruments** (B3 + international).

```python
from py_bcast import bdi

# Today's intraday bars for PETR4
df = bdi("PETR4", "20260520")   # DataFrame with DatetimeIndex
print(df[["open", "high", "low", "close", "volume", "trades"]].tail())

# Multiple days of intraday data
df = bdi("USDBRL", "20260515")  # from May 15 to now

# Multiple symbols -> one flat frame, distinguished by the ticker column
df = bdi(["PETR4", "VALE3"], "20260520")
```

**Returns:** `DataFrame` with DatetimeIndex and columns: `ticker`, `open`, `high`, `low`, `close`, `volume`, `trades`, `turnover`, `open_interest`, `cum_trades`, `session_type`.

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

# Multiple symbols -> one flat frame with a ticker column
df = bdt(["USDBRL", "EURUSD"], "20260519100000", "20260519110000")
```

**Returns:** `DataFrame` with DatetimeIndex and columns: `ticker`, `close`, `size`, `trades`, `open_interest`, `calendar_days`, `working_days`.

**Supported symbols:** USDBRL, EURUSD, GBPUSD, USDJPY, AUDUSD, USDCAD, USDCHF, NZDUSD, USDCNY, USDMXN, EURBRL, GBPBRL, JPYBRL, CHFBRL, AUDBRL, CADBRL, GOLD, SILVER, WTI, DAX, FTSE, VIX, DXY, US10Y, US2Y.

---

## Fundamental Data (HTTP)

### `bconsensus(ticker)`

Analyst consensus recommendations and target prices. Accepts a single ticker or
a list.

```python
from py_bcast import bconsensus

df = bconsensus("PETR4")
print(df["buy"].iloc[0], df["target_mean"].iloc[0])

# Multiple tickers -> one flat frame
df = bconsensus(["PETR4", "VALE3"])
```

**Returns:** a one-row-per-ticker `DataFrame` with columns: `ticker`, `buy`, `hold`, `sell`, `total_analysts`, `target_low`, `target_high`, `target_mean`, `target_median`, `upside_pct`. Empty DataFrame with that schema when a (valid) ticker has no analyst coverage.

> **Changed in 0.6.0:** previously returned a `dict`; now a DataFrame.

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

# Multiple symbols -> one flat frame with a ticker column
df = bmacro(["USDBRL", "IBOV"], "20260101", "20260520")
```

**Supported symbols:** USDBRL, EURUSD, IBOV, SPX, DAX, GOLD, WTI, DI1F27, AEIPCA, AEIGPM, AECTIP, AEB052, AEB200, AEFS10, and many more.

**Returns:** `DataFrame` with DatetimeIndex sorted chronologically and a `ticker` column. Other columns vary by symbol but typically include: `close`, `open`, `high`, `low`, `settle`, `change_pct`, `trades`, `volume`.

### CDI via `bmacro("CDI", ...)`

A serie CDI/DI-CETIP acumulado (desde 1986) e acessada via `bmacro` com o simbolo especial `"CDI"`:

```python
from py_bcast import bmacro

cdi = bmacro("CDI", "20260101", "20260520")
print(cdi["accumulated"].iloc[-1])
```

**Returns:** `DataFrame` with DatetimeIndex. Columns: `ticker` (`"CDI"`), `close`, `change_pct`, `accumulated`.

> **Alterado em 0.7.0 (BREAKING):** `bdi_cdi` foi removido. Use `bmacro("CDI", start, end)`. Ver [`../../compatibility.md`](../../compatibility.md).

### `breturn(ticker, start_date, end_date)`

Adjusted daily returns for a symbol.

```python
from py_bcast import breturn

df = breturn("PETR4", "20260101", "20260520")
print(df["close"].tail())

# Multiple symbols -> one flat frame with a ticker column
df = breturn(["PETR4", "VALE3"], "20260101", "20260520")
```

**Returns:** `DataFrame` with DatetimeIndex sorted chronologically and columns: `ticker`, `change_pct`, `close`.

### `bvolume(tickers)`

Average volume statistics (1m/2m/3m/6m averages).

```python
from py_bcast import bvolume

df = bvolume(["PETR4", "VALE3"])
print(df[df["ticker"] == "PETR4"])
```

**Returns:** a flat `DataFrame` (RangeIndex), one row per (ticker, averaging window), with columns: `ticker`, `avg_volume`, `avg_turnover`, `avg_trades`, `months`, `date`.

> **Changed in 0.6.0:** `symbol` is now a regular column (it repeats per averaging window, so it can never be a unique index) instead of the DataFrame index.
> **Changed in 0.7.0:** column `dat` renamed to `date`; column `symbol` renamed to `ticker`.

### `binflation()`

Snapshot of inflation indices with monthly and accumulated periods.

```python
from py_bcast import binflation

df = binflation()  # ~17 indices (IPCA, IGP-M, INPC, etc.)
print(df[["ticker", "return_3m", "return_6m", "return_12m", "return_ytd"]])
```

**Returns:** a flat `DataFrame` (RangeIndex) with columns: `ticker` (index name, e.g. "IPCA"), `mes0`..`mes11` (monthly values), `return_3m`, `return_6m`, `return_12m`, `return_ytd`.

---

### `binflation_history(symbol, start_date, end_date)`

Accumulated-inflation **time series** for one or more inflation indices (vs. `binflation`, the latest monthly snapshot). Uses the CalculoInflacao endpoint with the synthetic AE symbols (`AEIPCA`, `AEIGPM`, `AEINPC`, ... — the same family `bmacro` accepts).

```python
from py_bcast import binflation_history

df = binflation_history("AEIPCA", "20250101")
print(df["accumulated"].iloc[-1])
```

**Returns:** a flat `DataFrame` with a `DatetimeIndex` and a `ticker` column (one block per symbol) plus `accumulated` (% since `start_date`).

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

### `bsector_members(sector_id)`

Every company classified under a B3 sector — useful for sector screening (pair with `bcompany` / `bindicators` / `bstats` over the returned `cvm_code` / ticker). Uses EmpresasPorSetores (173). Takes a **top-level** `sector_id` (the `sector_id` column of `bsectors()`); subsector/segment ids return an empty frame.

```python
from py_bcast import bsector_members

df = bsector_members(1)   # ver bsectors() para os ids de setor
print(df[["cvm_code", "trade_name", "segment"]].head())
```

**Returns:** a flat `DataFrame` (RangeIndex), one row per company: `cvm_code`, `trade_name`, `corporate_name`, `cnpj`, the B3 sector/subsector/segment names and ids, `ref_year`, `ref_quarter`, `period_start`/`period_end`, `logo_url`.

### `bquote(ticker)`

Current quote (price, volume) for one or more symbols via aetp. Accepts a single
ticker or a list.

```python
from py_bcast import bquote

q = bquote("PETR4")
print(q["close"].iloc[0])

# Multiple tickers -> one flat frame
df = bquote(["PETR4", "VALE3"])
```

**Returns:** a one-row-per-symbol `DataFrame` with a `ticker` column and quote fields (`close`, `volume`, `cvm_code`, etc.). This is also the ticker -> CVM resolution primitive, so it stays "soft": an unknown ticker yields an empty block (with schema) rather than raising.

> **Changed in 0.6.0:** previously returned a `Series`; now a DataFrame.

### `btickers(ticker_or_cvm)`

All tickers (stocks/units) for one or more companies. Accepts a ticker string (CVM auto-resolved), a CVM code directly, or a list mixing both.

```python
from py_bcast import btickers

df = btickers("PETR4")        # auto-resolves CVM
df = btickers(9512)           # direct CVM code — same result
df = btickers(["PETR4", 4170])  # mixed list
print(df["ticker"].tolist())  # ['PETR3', 'PETR4']
```

> **Note:** the endpoint emits its own `ticker` column (the company's symbols), so for a list use the `cvm_code` column to tell the companies apart.

### `bshares(ticker)`

Shares outstanding for one or more tickers. Accepts a single ticker or a list.

```python
from py_bcast import bshares

df = bshares("PETR4")
print(df["total_shares"].iloc[0])

# Multiple tickers -> one flat frame
df = bshares(["PETR4", "VALE3"])
```

**Returns:** a one-row-per-ticker `DataFrame` with a `ticker` column. Raises `NotFoundError` for an unknown ticker (fail-fast across a list).

> **Changed in 0.6.0:** previously returned a `Series`; now a DataFrame.

### `bindicators(ticker_or_cvm, indicator, start_date, end_date)`

Daily fundamental indicator history.

Accepts a **ticker string or CVM code** (or a list mixing both) and an **indicator name or numeric ID**. With a list, the result is one flat DataFrame with a `ticker` column. Use `bindicator_meta()` to discover all available indicators.

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

Dividend/JCP payment history for one or more companies. CVM code is auto-resolved from the ticker if not provided. Accepts a single ticker or a list (with a list, `cvm_code` is ignored and each ticker resolves its own).

```python
from py_bcast import bdividends

divs = bdividends("PETR4")            # ticker-only (recommended)
divs = bdividends("PETR4", 9512)      # explicit CVM — skips resolution
divs = bdividends(["PETR4", "VALE3"]) # list -> one flat frame, ticker column
```

### `bdy(ticker, start_date, end_date, cvm_code=None)`

Dividend yield historical series for one or more companies. CVM code is auto-resolved from the ticker if not provided. Accepts a single ticker or a list (with a list, `cvm_code` is ignored and each ticker resolves its own).

```python
from py_bcast import bdy

dy = bdy("PETR4", "20250101", "20260520")                 # ticker-only (recommended)
dy = bdy("PETR4", "20250101", "20260520", cvm_code=9512)  # explicit CVM
dy = bdy(["PETR4", "VALE3"], "20250101", "20260520")      # list -> one flat frame
```

> **Contract (desde 0.7.0):** retorna `RangeIndex` (nao `DatetimeIndex`) com uma coluna `date` (string). O multi-ticker vetoriza por empresa; os blocos sobrepoem em datas (DatetimeIndex seria nao-unico).

### `bportfolio(broker_id=None, date=None)`

Carteiras recomendadas: lista de corretoras, composicao atual ou composicao historica.

```python
from py_bcast import bportfolio

brokers = bportfolio()              # lista de corretoras (sem broker_id)
holdings = bportfolio(27)           # composicao atual do broker 27
old = bportfolio(107, "20240102")   # composicao vigente em 02/jan/2024
```

**Retorna (sem `broker_id`):** `DataFrame` com `broker_id`, `name`, `last_update`.

**Retorna (com `broker_id`):** `DataFrame` flat, uma row por acao mantida. Colunas: `broker_id`, `date`, `ticker`, `portfolio_name`, `recommendation`, `target_price`, `dy_pct`, `company`, dados de setor e indicadores fundamentais.

**Com `date`:** retorna a composicao vigente naquela data (ultima revisao <= date). Rows ecoam a data real da revisao. Data anterior a primeira carteira retorna vazio.

> **Alterado em 0.7.0 (BREAKING):** `bportfolios()` foi removido; use `bportfolio()` (sem args). Ver [`../../compatibility.md`](../../compatibility.md).

### `bportfolios_with(ticker)`

Composicao completa de todas as carteiras recomendadas que contem um ticker.

```python
from py_bcast import bportfolios_with

df = bportfolios_with("PETR4")
# filtre pela coluna ticker para ver so as rows do PETR4:
df[df["ticker"] == "PETR4"][["broker_id", "portfolio_name", "date"]]
```

**Retorna:** `DataFrame` com o mesmo schema do `bportfolio` (todos os holdings de cada carteira que inclui o ticker). Vazio com schema se nenhuma carteira contem o ticker.

---

## Credit (HTTP — MarkitOutput2)

### `bcds(entity=None, date=None, cds_type="S", tier=None, docclause=None)`

CDS (credit default swap) term-structure curves from the Markit feed —
sovereign and corporate credit spreads in basis points.

```python
from py_bcast import bcds

bcds()                              # entities available on the latest date
df = bcds("BRASIL")                 # sovereign curve, one row per tenor
df[["tenor", "spread"]]             # 6M, 1Y, 2Y, 3Y, 4Y, 5Y, 7Y, 10Y
bcds("Banco do Brasil", cds_type="C")   # corporate curve
bcds("ALEMANHA", docclause="CR")    # override the automatic ISDA-2014 pick
```

Returns a flat DataFrame (RangeIndex), one row per tenor, with the spread
(``spread``), daily/monthly changes, bid/ask, and entity metadata (region,
sector, currency, recovery, composite and implied ratings). ``date=None``
resolves to the most recent date the feed carries; the resolved date is in the
``date`` column. ``entity`` matches the Markit code or the display name,
case- and accent-insensitively. When an entity lists more than one
(tier, docclause) pair, the ISDA 2014 (``*14``) clause is picked
automatically; pass ``tier=``/``docclause=`` to override. Raises
``NotFoundError`` for an unknown entity; a valid date with no Markit coverage
returns an empty DataFrame with schema.

---

### `bcds_indices(date=None)`

Markit CDS **index** term-structure table — tradable indices (CDXEM, iTraxx, ...), distinct from the single-name curves of `bcds`. Uses MarkitIndices (92); `date=None` resolves to the most recent date the feed has data for.

```python
from py_bcast import bcds_indices

df = bcds_indices()
print(df[["name", "composite_spread"]].head())
```

**Returns:** a flat `DataFrame` (RangeIndex), one row per index series: `date`, `name`, `redcode`, `maturity`, `composite_price`, `bid_ask_price`, `composite_spread`, `bid_ask_spread`, `change_day`, `change_month`, `depth`.

## Market Statistics & Intraday Snapshot (HTTP)

### `bstats(tickers)`

Snapshot de estatisticas de mercado para um ou mais simbolos.

```python
from py_bcast import bstats

df = bstats(["HGLG11", "PETR4"])
print(df[["ticker", "dividend_yield_pct", "high_52w", "low_52w"]])
```

Usa FIIAnbimaBovespa (150) — apesar do nome, serve QUALQUER simbolo B3 (acoes, FIIs, units). Multi via join numa unica request.

**Retorna:** `DataFrame` (RangeIndex), uma row por simbolo. Colunas: `ticker`, `bid`, `bid_date`, `ask`, `ask_date`, `last_dividend`, `last_dividend_date`, `dividend_yield_pct`, `shares_outstanding`, `low_52w`, `low_52w_date`, `high_52w`, `high_52w_date`, `turnover_last`, `avg_turnover_30d`, `avg_turnover_100d`, `avg_turnover_180d`, `source`, `net_assets` (FIIs), `avg_trades_180d`. Simbolos desconhecidos sao omitidos.

### `bsnapshot(tickers)`

Snapshot intraday near-real-time para um ou mais simbolos.

```python
from py_bcast import bsnapshot

df = bsnapshot(["PETR4", "VALE3"])
print(df[["ticker", "close", "volume", "trades"]])
```

Usa UltimosIntraday (125). Nao requer canal DDE. Multi via join.

**Retorna:** `DataFrame` (RangeIndex), uma row por simbolo. Colunas: `ticker`, `date`, `time`, `close`, `low`, `high`, `open`, `volume`, `trades`, `turnover`, `open_interest`.

---

## Times & Trades (HTTP)

### `bticks(ticker, start, end=None)`

Times-and-trades com book de topo para simbolos B3.

```python
from py_bcast import bticks

# 10:00-10:10 Brasilia = 13:00-13:10 UTC
df = bticks("PETR4", "20260610130000", "20260610131000")
trades = df[df["type"] == "TRD"]
quotes = df[df["type"] == "QTE"]
print(trades[["price", "size", "bid_participant", "ask_participant"]].head())
```

Usa TimesTrades (41). A janela e interpretada em **UTC** (como `bdt`). Retencao: somente a sessao corrente — dias anteriores retornam vazio. Dado denso (~2k rows/5min em PETR4). Multi via fan-out.

**Retorna:** `DataFrame` com index `DatetimeIndex` tz-aware `America/Sao_Paulo`, ordenado cronologicamente, uma coluna `ticker`. Colunas: `type` (`"TRD"` ou `"QTE"`), `price`, `size`, `bid_price`, `bid_size`, `ask_price`, `ask_size`, `bid_participant`, `ask_participant`, `seq_num`.

---

## Fixed Income (HTTP)

### `btreasury(symbols)`

Ultimo preco de referencia para titulos do Tesouro Nacional.

```python
from py_bcast import btreasury

df = btreasury(["LTN260701.ANBIMA", "NTNB270515.ANBIMA"])
print(df[["ticker", "rate", "unit_price"]])
```

Usa TitulosPublicosUltimos (141) com ids ANBIMA (`<papel><vencimento AAMMDD>.ANBIMA`). Ticker bare (ex: `LTN`) resolve para o instrumento errado — ver limitacoes. Multi via join.

**Retorna:** `DataFrame` (RangeIndex), uma row por titulo. Colunas: `ticker` (bare, ex: `LTN260701`), `date`, `rate` (taxa % a.a.), `unit_price` (PU).

### `btreasury_history(symbol, start, end=None)`

Historico OTC de taxas de negociacao para titulos do Tesouro.

```python
from py_bcast import btreasury_history

df = btreasury_history("NTNBK27.TRDM", "20260101")
print(df[["ticker", "close", "working_days"]])
```

Usa TitulosPublicos (77) com simbolos Trademate (`<papel><mes><AA>.TRDM` — descobertos via `bsearch(exchange="TRDM")`). Os valores OHLC sao TAXAS em % a.a. Negociacao OTC e esparsa.

**Retorna:** `DataFrame` com `DatetimeIndex`, uma coluna `ticker`. Colunas: `close`, `high`, `open`, `low` (taxas % a.a.), `calendar_days`, `working_days`, `expiration_date`, `unit_price`, `stddev`.

### `baccrual(rate, start, end=None)`

Acumulacao de uma taxa pre-fixada em dias uteis (calculadora server-side).

```python
from py_bcast import baccrual

df = baccrual(14.65, "20260101", "20260601")
print(df["accumulated"].iloc[-1])
```

Usa CalculoTaxaPre (136). O param `13539` e a taxa anual em % — o servidor capitaliza pela convencao du/252. Verificado exato: 100% a.a. em 15 du = 2**(15/252)-1 = 4.21%.

**Retorna:** `DataFrame` com `DatetimeIndex`, uma coluna `accumulated` (% acumulado desde `start_date`).

### `bsavings(start, end)`

Poupanca acumulada sobre uma janela.

```python
from py_bcast import bsavings

df = bsavings("20260101", "20260601")
print(df["accumulated"].iloc[-1])
```

Usa CalculoPoupanca (114) via `DataInicio`/`DataFim` (NAO usar `961` — HTTP 500).

**Retorna:** `DataFrame` com `DatetimeIndex`, uma coluna `accumulated` (% acumulado).

---

### `bunit_price(symbol, start_date, end_date=None)`

Daily unit-price (PU) series for fixed-income reference symbols. Complements `btreasury` (last snapshot) and `btreasury_history` (trading yields). Uses the CalculoPreco endpoint with ANBIMA daily reference ids (`<paper><maturity>.ANBIMA`, e.g. `LTN260701.ANBIMA`) or Trademate (`.TRDM`) symbols.

```python
from py_bcast import bunit_price

df = bunit_price("LTN260701.ANBIMA", "20260101")
print(df[["ticker", "unit_price"]].tail())
```

**Returns:** a flat `DataFrame` with a `DatetimeIndex` and a `ticker` column (one block per symbol). Columns: `accumulated_return` (% since start), `unit_price` (PU), `change_pct` (day-over-day).

## Investment Funds — Legacy (HTTP)

### `bfund_history(fund, start, end=None)`

Historico diario de cotas para fundos de investimento.

```python
from py_bcast import bfund_history

# Por id ANBIMA (os mesmos que bfunds do Plus retorna)
df = bfund_history("214248.ANBIMA", "20260101")
print(df[["ticker", "close", "net_asset"]].tail())

# Por ticker de bolsa (ETF/FII)
df = bfund_history("BBSD11", "20260101")
```

Usa Fundos (76). Ids ANBIMA populam `net_asset`, `inflows`, `outflows`, `quote_holders`; tickers de bolsa so carregam a cota.

**Retorna:** `DataFrame` com `DatetimeIndex`, uma coluna `ticker`. Colunas: `close`, `net_asset`, `inflows`, `outflows`, `total_assets`, `quote_holders`, `open`, `high`, `low`.

### `bfund_returns(fund)`

Retornos acumulados por janela para fundos de investimento.

```python
from py_bcast import bfund_returns

df = bfund_returns(["BBSD11", "214248.ANBIMA"])
print(df[["ticker", "return_12m"]])
```

Usa FundosRentabilidade (82). `return_12m` verificado como a janela de 12 meses.

**Retorna:** `DataFrame` (RangeIndex), uma row por fundo. Colunas: `ticker`, `return_1d`, `return_1m`, `return_3m`, `return_6m`, `return_12m`, `return_18m`, `return_2y`, `return_3y`, `return_5y` (todos em %).

---

### `bfund_list(query=None)`

Legacy fund universe (~45k CVM funds), optionally filtered by name. The `symbol` column is the `<id>.ANBIMA` form consumed by `bfund_history` / `bfund_returns`, so this is the discovery path for those on the legacy backend. Uses BuscarFundosAutoComplete (one cached call); `query` filters client-side by a case/accent-insensitive name substring.

```python
from py_bcast import bfund_list, bfund_history

funds = bfund_list("Tesouro Selic")
hist = bfund_history(funds["symbol"].iloc[0], "20260101")
```

**Returns:** a flat `DataFrame` (RangeIndex), one row per fund: `name`, `legal_name`, `anbima_id`, `cnpj`, `symbol` (`<id>.ANBIMA`), `anbima_class`.

## Macro — Conversao de Moeda

### `bfx(from_currency, to_currency, amount=1.0)`

Conversao spot entre moedas (calculadora server-side).

```python
from py_bcast import bfx

rate = bfx("USD", "BRL")        # taxa spot atual
converted = bfx("USD", "BRL", 100)  # 100 USD em BRL
```

Usa ConversorMoedas (131). Data e inerte — sempre retorna a taxa spot atual, sem conversao historica. Par invalido levanta `NotFoundError`.

**Retorna:** `float` com o valor convertido.

---

## Additional Reference Data (HTTP — aetp/output)

### `bfree_float(ticker_or_cvm)`

Classes de acoes com free float e composicao de units.

```python
from py_bcast import bfree_float

df = bfree_float("PETR4")   # PETR3 + PETR4 rows
df = bfree_float("SANB11")  # SANB3 + SANB4 + SANB11 (UNIT) rows
```

Usa EmpresaAcoesUnits (183). Para UNITs, `unit_on`/`unit_pn` indicam a composicao (ex: SANB11 = 1 ON + 1 PN). Fail-fast para identificadores desconhecidos.

**Retorna:** `DataFrame` (RangeIndex). Colunas: `ticker` (classe), `share_type`, `total_shares`, `float_shares`, `treasury_shares`, `float_pct` (milhares), `unit_on`, `unit_pn`.

### `bfund_holders(ticker_or_cvm)`

Top fundos de investimento que detem acoes de uma empresa.

```python
from py_bcast import bfund_holders

df = bfund_holders("PETR4")
print(df[["fund_trade_name", "position_value", "pct_of_fund"]].head())
```

Usa CarteiraTopFundos (187). Retorna vazio (soft) se nenhum fundo detem o ativo.

**Retorna:** `DataFrame` (RangeIndex). Colunas: `ticker`, `fund_id` (ANBIMA), `fund_trade_name`, `fund_corporate_name`, `cnpj`, `administrator`, `manager`, `category`, `position_value`, `position_quantity`, `pct_of_fund`, `reference_year`, `reference_month`.

### `bshareholder_dates(ticker_or_cvm)`

Datas das composicoes acionarias publicadas para empresas.

```python
from py_bcast import bshareholder_dates

df = bshareholder_dates("PETR4")
print(df[["reference_date", "position_date"]])
```

Usa AcionistaDatas (193). `reference_date` = 1 de janeiro do ano-base; `position_date` = data real da composicao.

**Retorna:** `DataFrame` (RangeIndex). Colunas: `ticker`, `reference_date`, `position_date` (strings ISO date).

### `bfilings(ticker_or_cvm, start, end)`

Links S3 para PDFs de ITR/DFP de empresas.

```python
from py_bcast import bfilings

df = bfilings("PETR4", "20260101", "20260610")
for url in df["url"]:
    print(url)
```

Usa ArquivosDemonstrativos (205).

**Retorna:** `DataFrame` (RangeIndex). Colunas: `ticker`, `date`, `url`.

### `bstatement_dates(ticker_or_cvm)`

Dates of a company's latest financial statements (the *dates*, not the figures — legacy has no DRE/BP/FC; see [`limitations.md`](./limitations.md)). Uses DemonstrativoUltimo (164). One row per company with the most recent annual (DFP) and quarterly (ITR) statements.

```python
from py_bcast import bstatement_dates

df = bstatement_dates("PETR4")
print(df[["ticker", "quarter_period_end", "quarter_disclosed"]])
```

**Returns:** a flat `DataFrame` (RangeIndex), each row tagged with a `ticker` column. Columns: `annual_period_start`, `annual_period_end`, `annual_disclosed`, `quarter`, `quarter_period_start`, `quarter_period_end`, `quarter_disclosed`, `basis` (C/I), `last_type` (A/T), `last_disclosed`. Raises `NotFoundError` if any identifier is unknown.

### `bfirst_close(ticker)`

Primeiro fechamento historico ajustado para um ou mais tickers.

```python
from py_bcast import bfirst_close

df = bfirst_close("PETR4")   # PETR4 -> 1994-07-04, 0.17
print(df[["ticker", "date", "close"]])
```

Usa FechamentoPrimeiro (204). So aceita ticker B3 bare (sem sufixo).

**Retorna:** `DataFrame` (RangeIndex). Colunas: `ticker`, `date` (int YYYYMMDD), `close`.

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

### `bnews_recent(count=10)`

Fetch the most recent news articles.

```python
from py_bcast import bnews_recent

for article in bnews_recent(5):
    print(f"[{article['id']}] {article['title'][:60]}")
```

**Returns:** `list[dict]` with keys: id, title, content, files. Most recent first. Max 100.

**Notes:**
- Uses binary search to find the current ID ceiling, then scans backwards
- First call may take a few seconds (binary search); subsequent IDs are sequential

### `bnews_multimedia(category, days_ago=60, limit=20)`

List multimedia/podcast content from a specific category. (Renamed from
`bnews_search` in 0.6.0 — it lists a category's multimedia, it is not a text
search.)

```python
from py_bcast import bnews_multimedia, MULTIMEDIA_CATEGORIES

# List available categories
for cat_id, name in MULTIMEDIA_CATEGORIES.items():
    print(f"{cat_id}: {name}")

# Get recent podcasts
items = bnews_multimedia(748)  # 748 = Podcast
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

Raises `NotFoundError` if the ticker cannot be resolved.

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
cache_invalidate("bhistory:PETR4:...")       # clear specific key
```

---

## Async API

All HTTP data functions have async equivalents in the `py_bcast._async` namespace, prefixed with `a` (e.g. `abhistory`, `abmacro`). They share the same connection pool, cache, and rate limiter as the sync API, and speak the **same contract**: flat DataFrame with a `ticker` column, multi-ticker input, `NotFoundError` for unknown inputs, empty-with-schema for valid-but-empty queries. (The list cores run concurrently via `asyncio.gather`.)

```python
import asyncio
from py_bcast._async import abhistory, abmacro, abconsensus, abnews_recent

async def main():
    # Historical prices
    data = await abhistory(["PETR4", "VALE3"], "20260501", "20260520")

    # Macro series
    fx = await abmacro("USDBRL", "20260101", "20260520")

    # Analyst consensus
    c = await abconsensus("PETR4")

    # Parallel fetch (asyncio.gather)
    data, fx, c = await asyncio.gather(
        abhistory("PETR4", "20260501", "20260520"),
        abmacro("USDBRL", "20260101", "20260520"),
        abconsensus("PETR4"),
    )

asyncio.run(main())
```

Alternatively via the namespace:

```python
from py_bcast import async_api

data = asyncio.run(async_api.abhistory("PETR4", "20260501", "20260520"))
```

**Available async functions:**

| Async | Sync equivalent | Module |
|-------|----------------|--------|
| `abhistory` | `bhistory` | `_async.historical` |
| `abclose` | `bclose` | `_async.historical` |
| `abdi` | `bdi` | `_async.historical` |
| `abdt` | `bdt` | `_async.historical` |
| `abticks` | `bticks` | `_async.historical` |
| `abfirst_close` | `bfirst_close` | `_async.historical` |
| `abmacro` | `bmacro` | `_async.macro` |
| `abreturn` | `breturn` | `_async.macro` |
| `abvolume` | `bvolume` | `_async.macro` |
| `abinflation` | `binflation` | `_async.macro` |
| `abstats` | `bstats` | `_async.macro` |
| `absnapshot` | `bsnapshot` | `_async.macro` |
| `abfx` | `bfx` | `_async.macro` |
| `abtreasury` | `btreasury` | `_async.fixedincome` |
| `abtreasury_history` | `btreasury_history` | `_async.fixedincome` |
| `abaccrual` | `baccrual` | `_async.fixedincome` |
| `absavings` | `bsavings` | `_async.fixedincome` |
| `abfund_history` | `bfund_history` | `_async.funds` |
| `abfund_returns` | `bfund_returns` | `_async.funds` |
| `abconsensus` | `bconsensus` | `_async.fundamental` |
| `abcompany` | `bcompany` | `_async.fundamental` |
| `abquote` | `bquote` | `_async.fundamental` |
| `abtickers` | `btickers` | `_async.fundamental` |
| `abshares` | `bshares` | `_async.fundamental` |
| `abindices` | `bindices` | `_async.fundamental` |
| `absectors` | `bsectors` | `_async.fundamental` |
| `abindicators` | `bindicators` | `_async.fundamental` |
| `abindicator_meta` | `bindicator_meta` | `_async.fundamental` |
| `abfree_float` | `bfree_float` | `_async.fundamental` |
| `abfund_holders` | `bfund_holders` | `_async.fundamental` |
| `abshareholder_dates` | `bshareholder_dates` | `_async.fundamental` |
| `abfilings` | `bfilings` | `_async.fundamental` |
| `abcalendar` | `bcalendar` | `_async.events` |
| `abdividends` | `bdividends` | `_async.events` |
| `abdy` | `bdy` | `_async.events` |
| `abportfolio` | `bportfolio` | `_async.events` |
| `abportfolios_with` | `bportfolios_with` | `_async.events` |
| `abnews` | `bnews` | `_async.news` |
| `abnews_recent` | `bnews_recent` | `_async.news` |
| `abnews_multimedia` | `bnews_multimedia` | `_async.news` |

> **Note:** `abnews_recent` uses `asyncio.gather` internally for parallel article fetches, which is significantly faster than the sequential sync version.

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

> **Note:** News functions (`bnews`, `bnews_recent`, `bnews_multimedia`) do NOT require a session token.

## Error Handling

All exceptions inherit from `PyBcastError`.

**Error policy (since 0.6.0).** Three distinct situations, three distinct outcomes:
- **Input does not exist** (unknown ticker / CVM / broker / indicator) -> raises `NotFoundError`. In a multi-input call, the first bad input raises (fail-fast); bad inputs are never silently dropped. Exception: `bquote`/`bconsensus` are "soft" (a valid query with no coverage yields an empty block, not a raise).
- **Valid query, zero rows** (e.g. an empty date range) -> returns an **empty DataFrame with the right columns/schema**, never raises.
- **Transport / protocol / auth failure** -> the specific exception below.

| Exception | Raised when |
|-----------|-------------|
| `SessionError` | Session token is missing or invalid |
| `NotFoundError` | A well-formed but non-existent entity was looked up (unknown ticker, CVM, broker, indicator). Exposes `.identifier` and `.kind` |
| `ContentProxyError` | ContentProxy HTTP endpoint returned an error status |
| `ProtocolError` | Binary SOH response is malformed or contains an error |
| `DDEError` | DDE connection failed or request timed out |
| `DDEAdviseError` | DDE advise (subscription) failed for a specific item (subclass of `DDEError`) |
| `ValidationError` | Input parameter was malformed (also a `ValueError`); also ambiguous indicator names |
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
    data = bhistory("PETR4", "20260501", "20260520")
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

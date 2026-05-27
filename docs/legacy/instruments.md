# Instrument Database

## Overview

py_bcast provides access to 623,247 instruments across 30+ exchanges via the local `aetp_17.dat` file maintained by the Broadcast terminal.

## Exchanges

| Exchange | Count | Description |
|----------|-------|-------------|
| PR | 189,985 | Private/proprietary instruments |
| BVMF | 138,181 | B3 (Brasil Bolsa Balcão) — stocks, FIIs, options, futures, BDRs |
| CMX | 51,902 | COMEX (gold, silver futures) |
| ANBIMA | 43,515 | Brazilian fixed income (debentures, CRI, CRA) |
| ECBT | 36,332 | Eurex (European derivatives) |
| CMEM | 14,190 | CME Micro contracts |
| NYBOT | 13,482 | ICE Futures US (commodities) |
| TRDM | 13,413 | Trade Machine instruments |
| NDQO | 12,727 | Nasdaq listed stocks |
| FMD | 12,687 | Fund Management data |
| GTISFX | 9,804 | ICE Data Services FX (spot + forwards) |
| NYSE | 8,924 | NYSE listed stocks |
| ICEEU | 6,128 | ICE Futures Europe (Brent, etc.) |
| CME | 5,670 | CME Group futures |
| NYMX | 4,543 | NYMEX (energy futures) |
| BER | 3,833 | Berliner Börse (DAX, etc.) |
| GTISME | 3,682 | ICE precious metals |
| TPGB | 2,619 | Government bonds (US Treasury, etc.) |
| NIKK | 1,200+ | Tokyo Stock Exchange (Nikkei) |
| CBOEI | 800+ | CBOE indices (VIX, etc.) |
| DJI | 500+ | Dow Jones indices |
| ICEUS | 200+ | ICE US indices (DXY) |

## Symbol Conventions

| Pattern | Meaning | Example |
|---------|---------|---------|
| `TICKER.EXCHANGE` | Full symbol | `PETR4.BVMF` |
| `X:STICKER.GTISFX` | FX spot | `X:SUSDBRL.GTISFX` |
| `X:FTICKER\\TERM.GTISFX` | FX forward | `X:FAEDUSD\\01M.GTISFX` |
| `C:STICKER\\SP.GTISME` | Commodity spot | `C:SXAUUSDOZ\\SP.GTISME` |
| `I:TICKER.EXCHANGE` | Index | `I:VIX.CBOEI`, `I:DAX.BER` |
| `F2:TICKER\\CODE.EXCHANGE` | Futures | `F2:4GC\\G27.CMX` |
| `TICKER.BVMF` | B3 equities | `PETR4.BVMF`, `VALE3.BVMF` |

## Common Symbol Mappings

| DDE Ticker | Full Symbol | Name |
|-----------|-------------|------|
| PETR4 | PETR4.BVMF | Petrobras PN |
| VALE3 | VALE3.BVMF | Vale ON |
| ITUB4 | ITUB4.BVMF | Itaú Unibanco PN |
| USDBRL | X:SUSDBRL.GTISFX | USD/BRL spot |
| EURUSD | X:SEURUSD.GTISFX | EUR/USD spot |
| GOLD | C:SXAUUSDOZ\SP.GTISME | Gold spot (USD/oz) |
| SILVER | C:SXAGUSDOZ\SP.GTISME | Silver spot (USD/oz) |
| WTI | C:EWTIUSDBR\SP.GTISEN | WTI crude oil |
| DAX | I:DAX.BER | German DAX index |
| FTSE | I:UKX.FTSE | UK FTSE 100 |
| VIX | I:VIX.CBOEI | CBOE Volatility Index |
| DXY | I:DXY0.ICEUS | US Dollar Index |
| DJIA | I:DJI.DJI | Dow Jones Industrial |
| NASDAQ | I:COMP.NDQI | Nasdaq Composite |
| NIKKEI | I:N225.NIKK | Nikkei 225 |
| US10Y | TMUBMUSD10Y.TPGB | US 10-Year Treasury |
| BRENT | I:BRN\N26\BWAVE.ICEEU | Brent Oil Index |
| DI1F27 | DI1F27.BVMF | DI futuro Jan/27 |

## Database File Format

**Location:** `%APPDATA%\Agencia Estado\Broadcast\DataFiles\aetp_17.dat`

**Decoding:**
1. Read raw bytes
2. XOR each byte with `0xAE`
3. Decode as Latin-1
4. Parse as TSV (first row = tag numbers as headers)

**Header tags (43 columns):**
```
10086, 10092, 10088, 10045, 324, 10050, 4887, 10057, 10058, 10059,
10070, 10093, 305, 10068, 303, 12005, 12016, 14136, 14137, 14138,
12006, 12007, 12008, 12096, 10053, 12012, 12018, 12019, 12058, 12057,
13004, 12059, 12060, 12080, 13395, 13396, 13397, 13398, 10048, 13399,
13400, 13401, 13402
```

## Usage

```python
from py_bcast import bsearch, InstrumentDB

# Quick search — retorna pd.DataFrame
df = bsearch("PETR", exchange="BVMF")
df = bsearch("USD", exchange="GTISFX")
df = bsearch("BRPETRACNPR6")        # by ISIN

# Direct database access
db = InstrumentDB.get()
inst = db.lookup("PETR4")
# {'ticker': 'PETR4', 'name': 'PETROLEO BRASILEIRO S.A. PETROBRAS, PN, A Vista',
#  'exchange': 'BVMF', 'backend': 'legacy',
#  'full_symbol': 'PETR4.BVMF', 'isin': 'BRPETRACNPR6',
#  'cvm_code': None, 'type_id': None, ...}
```

Schema completo do `bsearch` (DataFrame) e do `lookup` (dict): [`api.md#bsearch`](./api.md#bsearchquery-exchangenone-max_results20).

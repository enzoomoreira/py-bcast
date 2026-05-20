"""Quick test: discover working futures/options/FII/BDR ticker names."""
import time
import win32ui
import dde

server = dde.CreateServer()
server.Create('PyBCTickers')
conv = dde.CreateConversation(server)
conv.ConnectTo('BC', 'COT')

# Exhaustive ticker variants for futures and other asset classes
tickers = [
    # Mini dólar variants
    "WDO", "WDOM25", "WDON25", "WDOQ25", "WDO M25", "WDOJ25",
    "WDOFUT", "WDO FUT",
    # Dólar cheio
    "DOL", "DOLM25", "DOLN25", "DOLFUT", "DOL FUT",
    # Mini índice
    "WIN", "WINM25", "WINN25", "WINQ25", "WINFUT", "WIN FUT",
    # Índice cheio
    "IND", "INDM25", "INDN25", "INDFUT", "IND FUT",
    # DI futuro
    "DI1", "DI1F25", "DI1F26", "DI1F27", "DI1F28", "DI1F30",
    "DI1 F26", "DIF26",
    # DDI
    "DDI", "DDIF26",
    # FIIs
    "HGLG11", "MXRF11", "KNRI11", "XPML11", "VISC11",
    # BDRs
    "AAPL34", "MSFT34", "AMZO34", "GOGL34", "NVDC34",
    # ETFs
    "BOVA11", "IVVB11", "SMAL11", "HASH11",
    # Forex
    "USDBRL", "EURBRL", "GBPBRL", "JPYBRL",
    "EURUSD", "GBPUSD", "USDJPY",
    # Indices
    "IBOV", "IFIX", "SMLL", "IDIV", "IBXX", "IGCX", "ICON",
    # Commodities
    "OURO", "GOLD", "BRENT", "WTI", "SOJA",
    # Crypto
    "BTCBRL", "BTC", "BITCOIN",
    # Rates
    "SELIC", "CDI", "IPCA", "IGP-M",
    # Other derivatives
    "PETRH80", "PETRH44",  # options format?
    "PETRA450", "PETRA500",  # options?
]

print("Testing tickers via BC|COT  (TICKER.ULT)")
print("-" * 50)

found = []
for ticker in tickers:
    try:
        data = conv.Request(f"{ticker}.ULT")
        if data and "NOK" not in data and data.strip() and data != "N/A" and data != " ":
            print(f"  {ticker:12s} = {data}")
            found.append((ticker, data))
    except:
        pass
    time.sleep(0.03)

print(f"\n{'='*50}")
print(f"Found {len(found)} tickers with data:")
for t, v in found:
    print(f"  {t:12s} = {v}")

# Also try ATIVO topic for futures
print(f"\n\nATIVO topic for futures tickers:")
conv2 = dde.CreateConversation(server)
conv2.ConnectTo('BC', 'ATIVO')

for ticker in ["WDOM25", "DOLM25", "WINM25", "INDM25", "DI1F26", "HGLG11", "BOVA11"]:
    try:
        data = conv2.Request(ticker)
        if data and "NOK" not in data and data.strip():
            parts = data.split('\t')
            # Show first few meaningful fields
            print(f"  {ticker}: {parts[:5]}")
    except:
        print(f"  {ticker}: Error")
    time.sleep(0.05)

server.Shutdown()

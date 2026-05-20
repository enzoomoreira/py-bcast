"""
Working ContentProxy API client for AE Broadcast historical data.
Uses BCAA session token and nginx Basic Auth (bypassed by token in query).

Endpoints verified working:
- /BaseHistoricaNumerica/HistoricoFechamentos (closing prices)
- /aeterminal/services.xml (API registry)

Protocol:
- GET with query params: 10023=4 (platform), 10039=<BCAA_SESSION> (session token)
- TipoResposta=xml (response format)
- DatasTolerancia=YYYYMMDD (date for closing prices)
- 10113=SYMBOL (ticker like PETR4, VALE3)
"""
import httpx
import datetime
import xml.etree.ElementTree as ET

BASE = "http://cp.ae.com.br:44780"


class ContentProxyClient:
    def __init__(self, session_token: str, platform: int = 4):
        self.session_token = session_token
        self.platform = str(platform)
        self.session = httpx.Client(
            headers={"User-Agent": "bcsys32/7.0"},
            verify=False,
            trust_env=False,
        )

    def _base_params(self):
        return {"10023": self.platform, "10039": self.session_token, "TipoResposta": "xml"}

    def get_fechamentos(self, symbols: list[str], date: str) -> dict:
        """
        Get closing prices for symbols on a given date.
        
        Args:
            symbols: List of ticker symbols (e.g., ["PETR4", "VALE3"])
            date: Date in YYYYMMDD format
            
        Returns:
            Dict with symbol -> {DAT, LAST, SETTLE, SETTLE_RATE, YIELD}
        """
        params = self._base_params()
        params["10113"] = ";".join(symbols)
        params["DatasTolerancia"] = date
        
        r = self.session.get(
            f"{BASE}/BaseHistoricaNumerica/HistoricoFechamentos",
            params=params, timeout=15, verify=False
        )
        
        root = ET.fromstring(r.text)
        status = root.findtext("STATUS")
        if status != "success":
            msg = root.findtext("MESSAGE") or "Unknown error"
            raise RuntimeError(f"API error: {msg}")
        
        # Parse ticks
        results = {}
        for tick in root.findall(".//TICK"):
            sym = tick.findtext("SYMBOL")
            results[sym] = {
                "date": tick.findtext("DAT"),
                "last": tick.findtext("LAST"),
                "settle": tick.findtext("SETTLE"),
                "settle_rate": tick.findtext("SETTLE_RATE"),
                "yield": tick.findtext("YIELD"),
            }
        return results

    def get_bolsas(self):
        """Get list of exchanges."""
        params = self._base_params()
        r = self.session.get(
            f"{BASE}/AEInstrumentos/output/BolsaServlet",
            params=params, timeout=15, verify=False
        )
        return r.text


# === Test ===
if __name__ == "__main__":
    BCAA_SESSION = "F9bca84c7cb51fbdb4456a86c6548fb13"
    client = ContentProxyClient(BCAA_SESSION)

    print("=== Closing prices 2026-05-19 ===")
    try:
        data = client.get_fechamentos(["PETR4", "VALE3", "ITUB4", "BBDC4", "ABEV3"], "20260519")
        for sym, vals in data.items():
            print(f"  {sym}: LAST={vals['last']}, SETTLE={vals['settle']}, DATE={vals['date']}")
    except Exception as e:
        print(f"  Error: {e}")

    # Try multiple dates (one per call)
    print("\n=== PETR4 last 5 trading days ===")
    dates = ["20260519", "20260516", "20260515", "20260514", "20260513"]
    for date in dates:
        try:
            data = client.get_fechamentos(["PETR4"], date)
            for sym, vals in data.items():
                print(f"  {date}: {sym} LAST={vals['last']}")
        except Exception as e:
            print(f"  {date}: Error: {e}")

    # Try DI futures
    print("\n=== DI futures 2026-05-19 ===")
    try:
        data = client.get_fechamentos(["DI1F27", "DI1F28", "DI1F30"], "20260519")
        for sym, vals in data.items():
            print(f"  {sym}: LAST={vals['last']}, SETTLE={vals['settle']}")
    except Exception as e:
        print(f"  Error: {e}")

"""
dde_explore_topics.py
Deep exploration of all DDE topics and item formats.
Parses the ATIVO topic's tab-separated response, discovers DOLAR/LIVRO formats.
"""
import time
import win32ui
import dde

def explore():
    server = dde.CreateServer()
    server.Create('PyBCExplore2')

    print("=" * 60)
    print("  DDE Topic & Item Exploration")
    print("=" * 60)

    # ─── 1. ATIVO topic: returns all fields as tab-separated row ───
    print("\n\n[1] BC|ATIVO - Full ticker snapshot\n")
    try:
        conv = dde.CreateConversation(server)
        conv.ConnectTo('BC', 'ATIVO')

        # Known fields from BCFields.htm in order
        # The ATIVO topic returns ALL fields tab-separated when you request just the ticker
        raw = conv.Request('PETR4')
        fields = raw.split('\t')
        print(f"  PETR4 raw fields ({len(fields)} columns):")

        # From the CHM docs, the order should be:
        # ATIVO, ULT, HOR, VAR, MAX, MIN, FEC, ABE, OCP, OVD, NEG, QUL, MED, ...
        field_names = [
            "ATIVO", "ULT", "HOR", "VAR", "MAX", "MIN", "FEC", "ABE",
            "OCP", "OVD", "NEG", "QUL", "MED", "?14", "?15", "QTT",
            "?17", "EST", "?19", "?20", "?21", "?22", "?23", "?24",
            "?25", "?26", "?27", "?28", "?29", "?30", "SIT", "NOM",
            "?33", "DAT", "?35", "?36", "?37", "?38", "?39", "?40",
            "?41", "?42", "?43", "?44", "?45", "?46", "?47", "?48",
            "?49", "?50", "?51", "?52", "?53", "?54", "?55",
        ]

        for i, val in enumerate(fields):
            name = field_names[i] if i < len(field_names) else f"?{i+1}"
            if val.strip():
                print(f"    [{i:2d}] {name:8s} = {val!r}")

        # Try other tickers via ATIVO
        print(f"\n  Testing other tickers via ATIVO:")
        for ticker in ["VALE3", "IBOV", "USDBRL", "DOLAR", "WDOFUT", "WDOM25", "DOLFUT", "DI1F26", "WINM25"]:
            try:
                data = conv.Request(ticker)
                if data and "NOK" not in data:
                    parts = data.split('\t')
                    ult = parts[1] if len(parts) > 1 else "?"
                    name = parts[31] if len(parts) > 31 else "?"
                    print(f"    {ticker:10s} -> ULT={ult:>12s}  NOM={name}")
                else:
                    print(f"    {ticker:10s} -> {data[:60] if data else 'empty'}")
            except Exception as e:
                print(f"    {ticker:10s} -> Error: {e}")
            time.sleep(0.1)
    except Exception as e:
        print(f"  Error: {e}")

    # ─── 2. DOLAR topic - try different item formats ───
    print("\n\n[2] BC|DOLAR - Discovering item format\n")
    try:
        conv2 = dde.CreateConversation(server)
        conv2.ConnectTo('BC', 'DOLAR')

        # Try many formats
        dolar_items = [
            "USDBRL.ULT", "USDBRL", "ULT", "DOLAR",
            "COMERCIAL", "PTAX", "TURISMO",
            "COMERCIAL.COMPRA", "COMERCIAL.VENDA",
            "PTAX.COMPRA", "PTAX.VENDA",
            "USD.ULT", "BRL.ULT",
            "DÓLAR", "DOLAR.ULT",
            # Maybe it's just a different service name?
            "PETR4.ULT",  # test if COT format works here
            # Futures format
            "WDOFUT.ULT", "WDOM25.ULT",
            "DOL.ULT", "DOLFUT.ULT",
        ]
        for item in dolar_items:
            try:
                data = conv2.Request(item)
                if data and "NOK" not in data and data.strip():
                    print(f"    {item:25s} = {data!r}")
                else:
                    nok_msg = data[:50] if data else "empty"
                    print(f"    {item:25s} -> {nok_msg}")
            except Exception as e:
                print(f"    {item:25s} -> Error")
            time.sleep(0.05)
    except Exception as e:
        print(f"  Cannot connect to BC|DOLAR: {e}")

    # ─── 3. LIVRO topic (order book) ───
    print("\n\n[3] BC|LIVRO - Order book\n")
    try:
        conv3 = dde.CreateConversation(server)
        conv3.ConnectTo('BC', 'LIVRO')

        livro_items = [
            "PETR4", "PETR4.COMPRA", "PETR4.VENDA",
            "PETR4.OCP1", "PETR4.OVD1", "PETR4.QCP1", "PETR4.QVD1",
            "PETR4.C1", "PETR4.V1", "PETR4.C2", "PETR4.V2",
            "PETR4.BID1", "PETR4.ASK1",
            "PETR4.1", "PETR4.2", "PETR4.3",
            "PETR4.PC1", "PETR4.PV1",  # Preço compra/venda nível 1
            "PETR4.QC1", "PETR4.QV1",  # Qtd compra/venda nível 1
            "PETR4.NC1", "PETR4.NV1",  # Num ofertas compra/venda nível 1
        ]
        for item in livro_items:
            try:
                data = conv3.Request(item)
                if data and "NOK" not in data and data.strip():
                    print(f"    {item:25s} = {data!r}")
                else:
                    print(f"    {item:25s} -> {data[:50] if data else 'empty'}")
            except:
                print(f"    {item:25s} -> Error")
            time.sleep(0.05)
    except Exception as e:
        print(f"  Cannot connect to BC|LIVRO: {e}")

    # ─── 4. Try other service names (not just BC) ───
    print("\n\n[4] Other service names\n")
    services_to_try = ["BCH", "BCS", "BROADCAST", "AE", "Broadcast"]
    topics_to_try = ["COT", "ATIVO", "HIST", "DADOS"]

    for svc in services_to_try:
        for topic in topics_to_try:
            try:
                conv4 = dde.CreateConversation(server)
                conv4.ConnectTo(svc, topic)
                print(f"  [OK] {svc}|{topic} connected!", flush=True)
                try:
                    data = conv4.Request("PETR4.ULT")
                    print(f"       PETR4.ULT = {data!r}")
                except:
                    try:
                        data = conv4.Request("PETR4")
                        print(f"       PETR4 = {data[:80]!r}...")
                    except:
                        print(f"       (no items responded)")
            except:
                pass  # silently skip failed connections
            time.sleep(0.05)

    # ─── 5. COT topic - broader ticker exploration ───
    print("\n\n[5] BC|COT - Broader ticker universe\n")
    try:
        conv5 = dde.CreateConversation(server)
        conv5.ConnectTo('BC', 'COT')

        # Try various asset classes
        tickers = [
            # Stocks
            ("PETR4", "Petrobras PN"), ("VALE3", "Vale ON"), ("ITUB4", "Itaú PN"),
            ("BBDC4", "Bradesco PN"), ("ABEV3", "Ambev ON"), ("B3SA3", "B3 ON"),
            # Indices
            ("IBOV", "Ibovespa"), ("IFIX", "Índice FIIs"), ("SMLL", "Small Caps"),
            ("IDIV", "Dividendos"),
            # Forex
            ("USDBRL", "Dólar/Real"), ("EURBRL", "Euro/Real"),
            # Commodities
            ("OURO", "Ouro"),
            # Futures
            ("WDOFUT", "Mini Dólar"), ("WDOM25", "Mini Dólar Jun25"),
            ("WINFUT", "Mini Índice"), ("WINM25", "Mini Índice Jun25"),
            ("DOLFUT", "Dólar Futuro"), ("INDFUT", "Índice Futuro"),
            ("DI1F26", "DI Jan26"), ("DI1F27", "DI Jan27"),
            # FIIs
            ("HGLG11", "CSHG Logística"), ("MXRF11", "Maxi Renda"),
            # BDRs
            ("AAPL34", "Apple BDR"), ("MSFT34", "Microsoft BDR"),
        ]

        for ticker, desc in tickers:
            try:
                data = conv5.Request(f"{ticker}.ULT")
                if data and "NOK" not in data and data.strip() and data != "N/A":
                    print(f"    {ticker:10s} ({desc:20s}) ULT = {data}")
                elif data == "N/A":
                    print(f"    {ticker:10s} ({desc:20s}) = N/A (not available)")
                else:
                    pass  # skip NOK silently
            except:
                pass
            time.sleep(0.05)
    except Exception as e:
        print(f"  Error: {e}")

    # ─── 6. BC|COT with SysItems (DDE standard introspection) ───
    print("\n\n[6] DDE SysItems introspection\n")
    try:
        conv6 = dde.CreateConversation(server)
        conv6.ConnectTo('BC', 'COT')

        sys_items = ["SysItems", "Topics", "TopicItemList", "Formats", "Status", "ItemList"]
        for item in sys_items:
            try:
                data = conv6.Request(item)
                if data and "NOK" not in data:
                    print(f"    {item:20s} = {data[:200]!r}")
                else:
                    print(f"    {item:20s} -> NOK")
            except:
                print(f"    {item:20s} -> Error")
            time.sleep(0.05)
    except Exception as e:
        print(f"  Error: {e}")

    server.Shutdown()
    print("\n\nDone.")

if __name__ == "__main__":
    explore()

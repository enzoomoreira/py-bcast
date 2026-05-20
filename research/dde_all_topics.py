"""
dde_all_topics.py
Exploração sistemática e exaustiva de tópicos DDE do terminal Broadcast+.

Objetivos:
  1. Confirmar tópicos já conhecidos (COT, ATIVO)
  2. Descobrir tópicos desconhecidos com itens úteis
  3. Mapear todos os campos disponíveis por tópico
  4. Investigar formatos alternativos de item para futuros BM&F
  5. Testar tópico LIVRO (book de ofertas) com formatos diferentes

Requer: pywin32
"""
import time
import sys

try:
    import win32ui
    import dde
except ImportError:
    print("pywin32 não instalado.")
    sys.exit(1)


# ─────────────────────────────────────────────────────────────────────────────
# Ativos de teste (variedade de classes)
# ─────────────────────────────────────────────────────────────────────────────

TICKERS_TEST = {
    "acao":    ["PETR4", "VALE3", "ITUB4", "BBDC4", "B3SA3"],
    "fii":     ["HGLG11", "MXRF11"],
    "bdr":     ["AAPL34", "MSFT34"],
    "indice":  ["IBOV", "IFIX", "SMLL", "IDIV", "IBXX"],
    "cambio":  ["USDBRL", "EURBRL", "GBPBRL"],
    "futuro":  ["WDOM25", "WINM25", "DOLFUT", "INDFUT", "DI1F26", "DI1F27"],
    "opcao":   ["PETRG200", "PETRH200"],  # formatos hipotéticos
}

# Todos os tickers em uma lista plana para testes rápidos
TICKERS_ALL = [t for group in TICKERS_TEST.values() for t in group]
TICKERS_QUICK = ["PETR4", "IBOV", "USDBRL", "WDOM25", "DI1F26"]


# ─────────────────────────────────────────────────────────────────────────────
# Tópicos DDE para testar
# ─────────────────────────────────────────────────────────────────────────────

# Tópicos conhecidos e candidatos a explorar
DDE_TOPICS_CANDIDATES = [
    # Confirmados
    "COT",          # cotações tempo real — funciona
    "ATIVO",        # snapshot completo — funciona

    # Da documentação CHM / análise anterior
    "DOLAR",        # provavelmente câmbio — conecta mas sem formato de item
    "LIVRO",        # book de ofertas — conecta mas retorna vazio
    "ONLINE",       # status — conecta, NOK

    # Candidatos não testados
    "HIST",         # histórico?
    "NEWS",         # notícias?
    "NOTICIAS",
    "NOT",
    "AGENDA",
    "IND",          # índice?
    "FUT",          # futuro?
    "OPC",          # opções?
    "BCH",          # BCH via DDE? (improvável mas vale testar)
    "BCS",
    "STATUS",
    "INFO",
    "DADOS",
    "MERCADO",
    "BOLSA",
    "B3",
    "BMFBOVESPA",
    "DERIVATIVOS",
    "OPCOES",
    "RENDA_FIXA",
    "RF",
    "CDB",
    "LCI",
    "LCA",
    "DI",
    "CDI",
    "SELIC",
    "IPCA",
    "IGP",
    "INDICADORES",
]


# ─────────────────────────────────────────────────────────────────────────────
# Formatos de item para LIVRO (book de ofertas)
# ─────────────────────────────────────────────────────────────────────────────

LIVRO_ITEM_FORMATS = [
    # Formato ponto (padrão COT)
    "PETR4.LIVRO", "PETR4.BOOK", "PETR4.OFT",
    # Sem campo (só ticker)
    "PETR4",
    # Com campo numérico (nível do book)
    "PETR4.C1", "PETR4.V1", "PETR4.C2", "PETR4.V2",
    "PETR4.OC1", "PETR4.OV1",
    "PETR4.B1", "PETR4.A1", "PETR4.B2", "PETR4.A2",
    # Formato alternativo
    "PETR4/C1", "PETR4/V1",
    # Só campo
    "C1", "V1", "OCP1", "OVD1",
    # Com ponto e número
    "PETR4.1", "PETR4.2",
]


# ─────────────────────────────────────────────────────────────────────────────
# Formatos de item para futuros BM&F
# ─────────────────────────────────────────────────────────────────────────────

FUTURO_ITEM_FORMATS = [
    # Formatos padrão (já testados — retornam N/A)
    "WDOM25.ULT", "WINM25.ULT", "DOLFUT.ULT",

    # Com prefixo/sufixo diferente
    "WIN.ULT", "WDO.ULT", "DOL.ULT", "IND.ULT",
    "MINI.ULT",

    # Formato B3: vencimento MMMAA
    "WDOJ25.ULT", "WDOG25.ULT",  # Janeiro, Fevereiro...
    "WINJ25.ULT", "WING25.ULT",
    "DOLJ25.ULT", "DOLG25.ULT",
    "INDJ25.ULT", "INDG25.ULT",

    # Contratos cheios com nome completo
    "DOLFUT25.ULT", "INDFUT25.ULT",
    "DOL1!.ULT", "IND1!.ULT",  # formato continuous contract

    # BMF codes
    "BGI.ULT",   # boi gordo
    "WSP.ULT",   # soja
    "CCM.ULT",   # milho
    "ICF.ULT",   # café arábica

    # DI Futuro com outros vencimentos
    "DI1F25.ULT", "DI1G25.ULT", "DI1H25.ULT",
    "DI1F26.ULT", "DI1F27.ULT", "DI1F28.ULT",
    "DI1F30.ULT", "DI1F35.ULT",
]


# ─────────────────────────────────────────────────────────────────────────────
# Helper DDE
# ─────────────────────────────────────────────────────────────────────────────

def dde_request(conv, item, timeout_ms=2000):
    """Faz uma requisição DDE e retorna (value, error)."""
    try:
        val = conv.Request(item)
        if val is None:
            return None, "None"
        val = val.strip() if isinstance(val, str) else str(val)
        if not val or val == "N/A" or "NOK" in val:
            return None, val or "empty"
        return val, None
    except Exception as e:
        return None, str(e)


def try_connect(server, service, topic):
    """Tenta conectar a um tópico DDE. Retorna conv ou None."""
    try:
        conv = dde.CreateConversation(server)
        conv.ConnectTo(service, topic)
        return conv
    except Exception as e:
        return None


# ─────────────────────────────────────────────────────────────────────────────
# Seção 1: Scan de tópicos
# ─────────────────────────────────────────────────────────────────────────────

def scan_topics(server):
    print(f"\n{'═'*60}")
    print("  [1] Scan de tópicos DDE")
    print(f"{'═'*60}")
    print(f"  Testando {len(DDE_TOPICS_CANDIDATES)} tópicos no service 'BC'...\n")

    working_topics = []

    for topic in DDE_TOPICS_CANDIDATES:
        conv = try_connect(server, "BC", topic)
        if conv is None:
            print(f"  ✗ {topic:20s}  [não conecta]")
            continue

        # Conectou — testa um item básico
        val, err = dde_request(conv, "PETR4.ULT")
        if val:
            print(f"  ✓ {topic:20s}  PETR4.ULT = {val}")
            working_topics.append((topic, "PETR4.ULT", val))
        else:
            # Tenta só ticker sem campo
            val2, err2 = dde_request(conv, "PETR4")
            if val2:
                print(f"  ✓ {topic:20s}  PETR4 = {val2[:60]}")
                working_topics.append((topic, "PETR4", val2))
            else:
                print(f"  ~ {topic:20s}  [conecta, sem dados: {err or err2}]")

    print(f"\n  Tópicos com dados: {[t[0] for t in working_topics]}")
    return working_topics


# ─────────────────────────────────────────────────────────────────────────────
# Seção 2: Mapeamento completo de campos por tópico COT
# ─────────────────────────────────────────────────────────────────────────────

# Campos documentados e suspeitos para testar
FIELDS_TO_TEST = [
    # Confirmados
    "ATIVO", "ULT", "HOR", "VAR", "MAX", "MIN", "ABE", "FEC",
    "OCP", "OVD", "NEG", "QUL", "MED", "VTT", "QTT", "DAT",
    "QCP", "QVD", "EST", "NOM", "SIT", "LOT",
    # Da doc CHM
    "DES", "MER", "TPA", "PRA", "VEN", "PCO", "COD", "EMI",
    "CUP", "JUR", "IND", "IDE", "PAG", "TAX", "REF", "BAD", "BAO",
    "ISIN", "LOTE", "LOTE_PAD",
    # Campos históricos que podem existir no real-time
    "VTT", "VOL", "CAPT", "QCOT", "PATR", "RESG",
    # Campos de snapshot encontrados (F35, F36, etc.)
    "SINAL", "AFTER_MKT", "VOL_FIN", "FEC_ANT", "DAT_ANT", "DAT_HOJ",
    # Outros candidatos
    "LIM_INF", "LIM_SUP", "LIMITE", "LTA", "LTB",
    "THEO", "TEOPRICE", "STRIKE", "EXPIRY",
    "PU", "DUR", "YIELD", "TAXA",
    "BGT", "BID", "ASK", "MID",
    "OPEN", "CLOSE", "HIGH", "LOW",  # inglês
    "LAST", "CHANGE", "VOLUME",
]


def map_fields_cot(server):
    print(f"\n{'═'*60}")
    print("  [2] Mapeamento de campos — Topic=COT")
    print(f"{'═'*60}")

    conv = try_connect(server, "BC", "COT")
    if not conv:
        print("  [ERRO] Não conectou ao tópico COT")
        return

    found_fields = {}
    for ticker in ["PETR4", "IBOV", "USDBRL", "DI1F26"]:
        print(f"\n  Ticker: {ticker}")
        fields_this = {}
        for field in FIELDS_TO_TEST:
            item = f"{ticker}.{field}"
            val, err = dde_request(conv, item)
            if val:
                fields_this[field] = val
                print(f"    {field:12s} = {val}")
        found_fields[ticker] = fields_this

    return found_fields


# ─────────────────────────────────────────────────────────────────────────────
# Seção 3: Book de ofertas (LIVRO)
# ─────────────────────────────────────────────────────────────────────────────

def probe_livro(server):
    print(f"\n{'═'*60}")
    print("  [3] Book de Ofertas — Topic=LIVRO")
    print(f"{'═'*60}")

    # Tenta o tópico LIVRO com vários formatos de item
    conv_livro = try_connect(server, "BC", "LIVRO")
    if not conv_livro:
        print("  [ERRO] Não conectou ao tópico LIVRO")
    else:
        print(f"  Conectado ao tópico LIVRO. Testando formatos de item:")
        for item in LIVRO_ITEM_FORMATS:
            val, err = dde_request(conv_livro, item)
            if val:
                print(f"  ✓ item={item!r:25s}  valor={val[:100]}")
            else:
                print(f"  ✗ item={item!r:25s}  [{err}]")

    # Também tenta via COT com campos de book
    print(f"\n  Book via COT (campos de oferta):")
    conv_cot = try_connect(server, "BC", "COT")
    if conv_cot:
        book_fields = ["OCP", "OVD", "QCP", "QVD",
                       "OCP1", "OVD1", "OCP2", "OVD2", "OCP3", "OVD3",
                       "QCP1", "QVD1", "QCP2", "QVD2",
                       "C1", "V1", "C2", "V2", "C3", "V3",
                       "B1", "A1", "B2", "A2", "B3", "A3"]
        for field in book_fields:
            val, err = dde_request(conv_cot, f"PETR4.{field}")
            if val:
                print(f"  ✓ PETR4.{field:10s} = {val}")


# ─────────────────────────────────────────────────────────────────────────────
# Seção 4: Futuros BM&F
# ─────────────────────────────────────────────────────────────────────────────

def probe_futuros(server):
    print(f"\n{'═'*60}")
    print("  [4] Futuros BM&F")
    print(f"{'═'*60}")

    conv_cot = try_connect(server, "BC", "COT")
    conv_ativo = try_connect(server, "BC", "ATIVO")

    if not conv_cot:
        print("  [ERRO] Não conectou ao tópico COT")
        return

    print(f"\n  Formatos de item via COT:")
    for item in FUTURO_ITEM_FORMATS:
        val, err = dde_request(conv_cot, item)
        if val:
            print(f"  ✓ {item:25s} = {val}")
        elif err not in ("N/A", "None", "empty"):
            print(f"  ? {item:25s} [{err[:60]}]")

    if conv_ativo:
        print(f"\n  Snapshot (ATIVO) de futuros:")
        for ticker in ["WDOM25", "WINM25", "DOLFUT", "INDFUT", "DI1F26",
                       "WIN", "WDO", "DOL", "IND",
                       "WDOJ25", "WINJ25"]:
            val, err = dde_request(conv_ativo, ticker)
            if val:
                parts = val.split('\t')
                nome = parts[31] if len(parts) > 31 else "?"
                ult = parts[1] if len(parts) > 1 else "?"
                print(f"  ✓ {ticker:12s}  ULT={ult:>12s}  NOM={nome}")
            else:
                print(f"  ✗ {ticker:12s}  [{err}]")


# ─────────────────────────────────────────────────────────────────────────────
# Seção 5: Tópico DOLAR — formato de item
# ─────────────────────────────────────────────────────────────────────────────

def probe_dolar(server):
    print(f"\n{'═'*60}")
    print("  [5] Tópico DOLAR")
    print(f"{'═'*60}")

    conv = try_connect(server, "BC", "DOLAR")
    if not conv:
        print("  [ERRO] Não conectou ao tópico DOLAR")
        return

    # Formatos possíveis de item no tópico DOLAR
    items_test = [
        "DOLAR", "USD", "BRL", "USDBRL", "PTAX",
        "PTAX.ULT", "USD.ULT", "BRL.ULT",
        "USDBRL.ULT", "USDBRL.OCP", "USDBRL.OVD",
        "ULT", "OCP", "OVD", "VAR", "FEC",
        "1", "BID", "ASK",
        # Códigos B3 de câmbio
        "DOL", "DOL.ULT", "PTAXV.ULT", "PTAXC.ULT",
        "USD/BRL", "EURUSD",
    ]

    print(f"  Testando {len(items_test)} formatos de item:")
    for item in items_test:
        val, err = dde_request(conv, item)
        if val:
            print(f"  ✓ {item:20s} = {val}")
        else:
            print(f"  ✗ {item:20s} [{err}]")


# ─────────────────────────────────────────────────────────────────────────────
# Seção 6: Snapshot ATIVO — mapeamento dos campos desconhecidos
# ─────────────────────────────────────────────────────────────────────────────

def map_snapshot_unknowns(server):
    print(f"\n{'═'*60}")
    print("  [6] Snapshot ATIVO — campos desconhecidos por tipo de ativo")
    print(f"{'═'*60}")

    conv = try_connect(server, "BC", "ATIVO")
    if not conv:
        print("  [ERRO] Não conectou ao tópico ATIVO")
        return

    SNAPSHOT_KNOWN = {
        0: "ATIVO", 1: "ULT", 2: "HOR", 3: "VAR", 4: "MAX", 5: "MIN",
        6: "FEC", 7: "ABE", 8: "OCP", 9: "OVD", 10: "NEG", 11: "QUL",
        12: "MED", 13: "QCP_TOTAL", 14: "QVD_TOTAL", 15: "QTT",
        16: "SINAL", 17: "EST",
        18: "ULT_C1", 19: "HOR_C1", 20: "QUL_C1",
        21: "ULT_V1", 22: "HOR_V1", 23: "QUL_V1",
        24: "ULT_C2", 25: "HOR_C2", 26: "QUL_C2",
        27: "ULT_V2", 28: "HOR_V2", 29: "QUL_V2",
        30: "SIT", 31: "NOM", 32: "COD_ISIN", 33: "DAT",
        36: "LOTE_PAD", 37: "DEC", 38: "QUL_MIN", 39: "QUL_MAX", 40: "LOT",
        43: "FEC_ANT", 44: "DAT_ANT",
        47: "AFTER_MKT", 48: "VOL_FIN", 50: "DAT_HOJ", 54: "ISIN",
    }

    unknown_cols = [i for i in range(56) if i not in SNAPSHOT_KNOWN]
    print(f"  Campos desconhecidos: {unknown_cols}")

    print(f"\n  Valores por tipo de ativo (colunas desconhecidas):")
    for tipo, tickers in TICKERS_TEST.items():
        ticker = tickers[0]
        val, err = dde_request(conv, ticker)
        if not val:
            print(f"\n  {tipo:10s} {ticker:8s}: [sem dados: {err}]")
            continue

        parts = val.split('\t')
        print(f"\n  {tipo:10s} {ticker:8s} ({len(parts)} colunas):")
        for i in unknown_cols:
            if i < len(parts) and parts[i].strip():
                nome = SNAPSHOT_KNOWN.get(i, f"F{i+1}")
                print(f"    [{i:2d}] F{i+1:2d} = {parts[i]!r}")


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("  Broadcast+ DDE Topics — Exploração Completa")
    print("=" * 60)

    server = dde.CreateServer()
    server.Create("PyBCExplore")

    try:
        scan_topics(server)
        map_fields_cot(server)
        probe_livro(server)
        probe_futuros(server)
        probe_dolar(server)
        map_snapshot_unknowns(server)
    finally:
        server.Shutdown()

    print(f"\n{'='*60}")
    print("  Exploração concluída.")
    print("=" * 60)


if __name__ == "__main__":
    main()

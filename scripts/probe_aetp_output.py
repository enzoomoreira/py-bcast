"""Probe aetp/output endpoints - the largest unexplored area."""

import httpx
import datetime

from py_bcast._core.session import get_session_token

BASE = "http://cp.ae.com.br:44780"
SESSION = get_session_token()
s = httpx.Client(
    headers={"User-Agent": "bcsys32/7.0"},
    verify=False,
    trust_env=False,
)

today = datetime.date.today().strftime("%Y%m%d")


def probe(url, extra_params=None, label=""):
    params = {"10023": "4", "10039": SESSION}
    if extra_params:
        params.update(extra_params)
    try:
        r = s.get(f"{BASE}{url}", params=params, timeout=15, verify=False)
    except Exception as e:
        print(f"  [{label}] ERROR: {e}")
        return None

    ct = r.headers.get("Content-Type", "?")
    size = len(r.content)

    # Detect response format
    if b"\x01" in r.content[:50]:
        # Binary SOH protocol
        records = r.content.split(b"\x01")
        # Check for error
        if len(records) > 2:
            err_fields = records[1].split(b"\x00")
            err_code = (
                err_fields[0].decode("latin-1", errors="replace") if err_fields else "?"
            )
            if err_code != "0":
                # Error - extract message
                field_rec = records[2].split(b"\x00")
                decoded = [
                    f.decode("latin-1", errors="replace") for f in field_rec if f
                ]
                msg = ""
                for i, d in enumerate(decoded):
                    if d == "10037" and i + 1 < len(decoded):
                        msg = decoded[i + 1]
                        break
                if not msg and len(decoded) > 3:
                    msg = str(decoded[:5])
                print(f"  [{label}] BINARY ERROR: {msg[:80]}")
                return None
            else:
                # Success!
                field_rec = records[2].split(b"\x00")
                field_tags = [f.decode("latin-1") for f in field_rec[1:] if f]
                data_records = [r for r in records[3:] if r != b"\x03" and r != b""]
                print(
                    f"  [{label}] BINARY OK! {len(data_records)} rows, fields={field_tags[:10]}"
                )
                # Show first row
                if data_records:
                    first_row = [
                        v.decode("latin-1", errors="replace")
                        for v in data_records[0].split(b"\x00")
                        if v
                    ]
                    print(f"    Row 0: {first_row[:10]}")
                if len(data_records) > 1:
                    second_row = [
                        v.decode("latin-1", errors="replace")
                        for v in data_records[1].split(b"\x00")
                        if v
                    ]
                    print(f"    Row 1: {second_row[:10]}")
                return {"fields": field_tags, "rows": len(data_records)}
    elif r.status_code == 404:
        print(f"  [{label}] 404 Not Found")
        return None
    elif r.status_code == 500:
        print(f"  [{label}] 500 Server Error: {r.text[:100]}")
        return None
    elif "xml" in ct or r.text.strip().startswith("<"):
        if "<STATUS>success" in r.text:
            ticks = r.text.count("<TICK>")
            print(f"  [{label}] XML OK! {ticks} ticks. First 200: {r.text[:200]}")
            return True
        else:
            print(f"  [{label}] XML ERROR: {r.text[:150]}")
            return None
    else:
        # Text/unknown
        text = r.text[:200] if r.text else repr(r.content[:100])
        print(f"  [{label}] Status={r.status_code} CT={ct} Size={size}: {text}")
        return r
    return None


print("=" * 70)
print("  PHASE 1: Metadata endpoints (no ticker needed)")
print("=" * 70)

# These need ONLY 10023 + 10039
simple_endpoints = [
    ("/aetp/output/fundamental/indicador/metadado", "IndicadorMetadado"),
    ("/aetp/output/fundamental/setor", "SetorSubsetorSegmento"),
    ("/aetp/output/fundamental/arquivos/categoria", "ArquivosCategorias"),
    ("/aetp/output/fundamental/arquivos/especie", "ArquivosEspecies"),
    ("/aetp/output/fundamental/arquivos/tipo", "ArquivosTipos"),
    ("/aetp/output/fundamental/empresa/metadado", "EmpresaMetadado"),
    ("/aetp/output/fundamental/indicador/ticker-preco-volume", "TickerPrecoVolume"),
    ("/aetp/output/fundamental/indicador/categoria", "IndicadorCategorias"),
    (
        "/aetp/output/fundamental/empresa/carteira-recomendada/corretoras",
        "CartRecomCorretoras",
    ),
    ("/aetp/output/fundamental/indicador/agrupado", "IndicadorAgrupado"),
    ("/aetp/output/fundamental/indicador/periodo/lista", "IndicadorPeriodoLista"),
    ("/aetp/output/fundamental/ativo/simbolo", "AtivoSimbolo"),
    ("/aetp/output/fundamental/ativo/cotacao", "AtivoCotacao"),
    ("/aetp/output/fundamental/ativo/quantidade", "AtivoQuantidade"),
    ("/aetp/output/fundamental/arquivos/demonstrativos", "ArquivosDemonstrativos"),
    ("/aetp/output/fundamental/carteira/fundos/datas", "CarteiraDatas"),
    ("/aetp/output/ativos/indice", "Indices"),
]

for url, label in simple_endpoints:
    probe(url, label=label)

print("\n" + "=" * 70)
print("  PHASE 2: Company-specific endpoints (13004=PETR4, 10068=PETR4)")
print("=" * 70)

company_endpoints = [
    (
        "/aetp/output/fundamental/demonstrativo/ultimo",
        {"13004": "PETR4"},
        "DemoUltimo PETR4",
    ),
    ("/aetp/output/fundamental/empresa", {"13004": "PETR4"}, "Empresa PETR4"),
    ("/aetp/output/fundamental/empresa/acao", {"13004": "PETR4"}, "EmpresaAcao PETR4"),
    (
        "/aetp/output/fundamental/empresa/eventos/jcp-dividendos",
        {"13004": "PETR4", "10068": "PETR4"},
        "Dividendos PETR4",
    ),
    (
        "/aetp/output/fundamental/carteira/top-fundos",
        {"13004": "PETR4"},
        "TopFundos PETR4",
    ),
    (
        "/aetp/output/fundamental/investimentos/distribuicao",
        {"13004": "PETR4"},
        "Distribuicao PETR4",
    ),
    (
        "/aetp/output/fundamental/acionista/datas",
        {"13004": "PETR4"},
        "AcionistaDatas PETR4",
    ),
    ("/aetp/output/fundamental/empresa/setores", {"13798": "1"}, "EmpresasPorSetores"),
    ("/aetp/output/fundamental/empresa/ranking", {"13760": "1"}, "RankingIndicador"),
]

for url, params, label in company_endpoints:
    probe(url, params, label)

print("\n" + "=" * 70)
print("  PHASE 3: Indicadores (the prize)")
print("=" * 70)

# 13004=company, 13006=tipo periodo, 13007=ano inicio, 13008=ano fim
indic_endpoints = [
    (
        "/aetp/output/fundamental/indicador/periodo",
        {"13004": "PETR4", "13006": "A", "13007": "2023", "13008": "2025"},
        "Periodo PETR4 A",
    ),
    (
        "/aetp/output/fundamental/indicador/periodo",
        {"13004": "PETR4", "13006": "T", "13007": "2023", "13008": "2025"},
        "Periodo PETR4 T",
    ),
    (
        "/aetp/output/fundamental/indicador/periodo",
        {"13004": "PETR4", "13006": "1", "13007": "2023", "13008": "2025"},
        "Periodo PETR4 1",
    ),
    (
        "/aetp/output/fundamental/indicador/ticker",
        {"10068": "PETR4", "13780": "1"},
        "Ticker PETR4 13780=1",
    ),
    (
        "/aetp/output/fundamental/indicador/ticker",
        {"10068": "PETR4", "13780": "P_L"},
        "Ticker PETR4 P_L",
    ),
    (
        "/aetp/output/fundamental/indicador/ticker",
        {"10068": "PETR4", "13780": "PL"},
        "Ticker PETR4 PL",
    ),
    (
        "/aetp/output/fundamental/indicador/ticker-fixo",
        {"13780": "1"},
        "TickerFixo 13780=1",
    ),
    (
        "/aetp/output/fundamental/indicador/ticker-fixo",
        {"13780": "P_L"},
        "TickerFixo P_L",
    ),
    (
        "/aetp/output/fundamental/indicador/historico-diario",
        {"13004": "PETR4", "10057": "20240101", "10058": "20250520", "13760": "1"},
        "HistDiario PETR4",
    ),
    (
        "/aetp/output/fundamental/indicador/historico",
        {
            "13004": "PETR4",
            "13786": "2023",
            "13787": "2025",
            "13006": "A",
            "13007": "2023",
            "13760": "1",
        },
        "Historico PETR4",
    ),
]

for url, params, label in indic_endpoints:
    probe(url, params, label)

print("\n" + "=" * 70)
print("  PHASE 4: Carteira recomendada / Eventos / Calendar")
print("=" * 70)

other_endpoints = [
    (
        "/aetp/output/fundamental/empresa/carteira-recomendada/ultima",
        {"10087": "1"},
        "CartRecom ultima 10087=1",
    ),
    (
        "/aetp/output/fundamental/empresa/carteira-recomendada/ticker",
        {"10113": "PETR4"},
        "CartRecom ticker PETR4",
    ),
    (
        "/aetp/output/fundamental/empresa/carteira-recomendada/ticker",
        {"10113": "PETR4;VALE3;ITUB4"},
        "CartRecom multi",
    ),
    (
        "/aetp/output/fundamental/empresa/eventos/agrupados",
        {
            "13004": "PETR4",
            "10068": "PETR4",
            "10057": "20200101",
            "10058": "20260101",
            "10029": "1",
        },
        "EventosAgrupados PETR4",
    ),
    (
        "/aetp/output/fundamental/empresa/eventos/dividend-yield",
        {
            "13004": "PETR4",
            "10068": "PETR4",
            "10057": "20200101",
            "10058": "20260101",
            "10029": "1",
        },
        "DY PETR4",
    ),
    (
        "/aetp/output/fundamental/calendario-eventos-corporativos",
        {"10057": "20260101", "10058": "20260601"},
        "CalendarioEventos",
    ),
    (
        "/aetp/output/fundamental/empresa/ranking-mais-acessadas",
        {"10057": "20260101", "10058": "20260520"},
        "RankingEmpresas",
    ),
    (
        "/aetp/output/fundamental/ticker-external-fields",
        {"10113": "PETR4"},
        "TickersEmpresas PETR4",
    ),
    (
        "/aetp/output/ativos/indice/composicao",
        {"13158": "IBOV", "10098": "1", "10099": "20"},
        "ComposicaoIBOV",
    ),
    (
        "/aetp/output/ativos/indice/composicao",
        {"13158": "1", "10098": "1", "10099": "20"},
        "ComposicaoIndice 1",
    ),
]

for url, params, label in other_endpoints:
    probe(url, params, label)

print("\n" + "=" * 70)
print("  PHASE 5: BaseHistoricaNumerica extras")
print("=" * 70)

bhn_endpoints = [
    (
        "/BaseHistoricaNumerica/Inflacao",
        {"305": "IPCA", "TipoResposta": "xml"},
        "Inflacao IPCA",
    ),
    (
        "/BaseHistoricaNumerica/Inflacao",
        {"305": "CDI", "TipoResposta": "xml"},
        "Inflacao CDI",
    ),
    (
        "/BaseHistoricaNumerica/Inflacao",
        {"TipoResposta": "xml"},
        "Inflacao (no symbol)",
    ),
    (
        "/BaseHistoricaNumerica/DiCetipAcumulado",
        {"961": "DiCetipAcumulado", "TipoResposta": "xml"},
        "DiCetipAcumulado",
    ),
    (
        "/BaseHistoricaNumerica/DiCetipAcumulado",
        {"TipoResposta": "xml"},
        "DiCetipAcumulado no 961",
    ),
    (
        "/BaseHistoricaNumerica/ConversorDeMoedas",
        {"TipoResposta": "xml"},
        "ConversorMoedas",
    ),
    (
        "/BaseHistoricaNumerica/VolumesMedios",
        {"10113": "PETR4;VALE3", "TipoResposta": "xml"},
        "VolumesMedios",
    ),
    (
        "/BaseHistoricaNumerica/RetornoDiario",
        {"305": "PETR4", "961": "RetornoDiario", "TipoResposta": "xml"},
        "RetornoDiario",
    ),
    (
        "/BaseHistoricaNumerica/RetornoDiario",
        {"305": "PETR4", "TipoResposta": "xml"},
        "RetornoDiario no 961",
    ),
    (
        "/BaseHistoricaNumerica/FechamentoPrimeiro",
        {"305": "PETR4", "TipoResposta": "xml"},
        "FechamentoPrimeiro",
    ),
    (
        "/BaseHistoricaNumerica/Volatilidades",
        {"10113": "PETR4", "12078": "20", "TipoResposta": "xml"},
        "Volatilidades",
    ),
]

for url, params, label in bhn_endpoints:
    probe(url, params, label)

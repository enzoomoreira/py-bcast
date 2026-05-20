"""
Systematic probe of ALL untested Broadcast ContentProxy endpoints.
Sends one GET per endpoint with minimal required params, classifies the response.
"""

import json
import time
import httpx

BASE = "http://cp.ae.com.br:44780"
SESSION = "F9bca84c7cb51fbdb4456a86c6548fb13"
PLATFORM = "4"
TIMEOUT = 10

# Common tag values for probing
TICKER = "PETR4"
TICKER_INTL = "USDBRL"
DATE_TODAY = "20260520"
DATE_RANGE_START = "20260101"
DATE_RANGE_END = "20260520"
EMPRESA_COD = "9512"  # Petrobras company code in aefundamental


def base_params():
    return {"10023": PLATFORM, "10039": SESSION, "TipoResposta": "xml"}


def classify_response(r: httpx.Response) -> dict:
    """Classify a response by format and content."""
    info = {
        "status": r.status_code,
        "size": len(r.content),
        "format": "unknown",
        "preview": "",
        "error": "",
    }
    
    if r.status_code != 200:
        info["format"] = "error"
        info["preview"] = r.text[:200] if r.text else ""
        return info
    
    content = r.content
    text = ""
    try:
        text = r.text
    except Exception:
        pass
    
    if content and content[0:1] == b'<' or (text and text.strip().startswith('<')):
        info["format"] = "xml"
        # Check for error in XML
        if "ERROR" in text[:500].upper() or "error" in text[:500]:
            info["error"] = "xml_error"
        if "<STATUS>error</STATUS>" in text:
            info["error"] = "api_error"
        # Get a meaningful preview
        preview = text[:300].replace('\n', ' ').replace('\r', '')
        info["preview"] = preview[:200]
    elif text and text.strip().startswith('{'):
        info["format"] = "json"
        info["preview"] = text[:200]
    elif text and text.strip().startswith('['):
        info["format"] = "json_array"
        info["preview"] = text[:200]
    elif content and b'\x01' in content[:100]:
        info["format"] = "binary_soh"
        info["preview"] = repr(content[:100])
    elif content and b'\x00' in content[:50]:
        info["format"] = "binary"
        info["preview"] = repr(content[:80])
    elif text:
        info["format"] = "text"
        info["preview"] = text[:200]
    else:
        info["format"] = "empty"
    
    return info


# ─────────────────────────────────────────────────────────────────────────────
# Define ALL endpoints to probe with their required params
# ─────────────────────────────────────────────────────────────────────────────

ENDPOINTS = [
    # === BaseHistoricaNumerica ===
    {
        "id": 13, "name": "HistoricoData",
        "url": f"{BASE}/BaseHistoricaNumerica/HistoricoData",
        "params": {**base_params(), "305": TICKER, "10077": DATE_TODAY},
    },
    {
        "id": 40, "name": "Players",
        "url": f"{BASE}/BaseHistoricaNumerica/Players",
        "params": {**base_params(), "961": DATE_RANGE_START, "10086": "BVMF"},
    },
    {
        "id": 41, "name": "TimesTrades",
        "url": f"{BASE}/BaseHistoricaNumerica/TimesTrades",
        "params": {**base_params(), "305": TICKER},
    },
    {
        "id": 75, "name": "HistoricoDiarioSimbolos",
        "url": f"{BASE}/BaseHistoricaNumerica/HistoricoDiarioSimbolos",
        "params": {**base_params(), "961": DATE_RANGE_START, "10113": TICKER},
    },
    {
        "id": 76, "name": "Fundos",
        "url": f"{BASE}/BaseHistoricaNumerica/Fundos",
        "params": {**base_params(), "305": "BBSD11", "961": DATE_RANGE_START},
    },
    {
        "id": 77, "name": "TitulosPublicos",
        "url": f"{BASE}/BaseHistoricaNumerica/TitulosPublicos",
        "params": {**base_params(), "305": "LTN", "961": DATE_RANGE_START},
    },
    {
        "id": 81, "name": "FundosIndicadores",
        "url": f"{BASE}/BaseHistoricaNumerica/FundosIndicadores",
        "params": {**base_params(), "305": "BBSD11", "961": DATE_RANGE_START},
    },
    {
        "id": 82, "name": "FundosRentabilidade",
        "url": f"{BASE}/BaseHistoricaNumerica/FundosRentabilidade",
        "params": {**base_params(), "305": "BBSD11"},
    },
    {
        "id": 83, "name": "FechamentoFormula",
        "url": f"{BASE}/BaseHistoricaNumerica/FechamentoFormula",
        "params": {**base_params(), "10113": TICKER, "12004": "ULT"},
    },
    {
        "id": 84, "name": "VolumesMedios",
        "url": f"{BASE}/BaseHistoricaNumerica/VolumesMedios",
        "params": {**base_params(), "10113": TICKER},
    },
    {
        "id": 95, "name": "MacroEconomicos",
        "url": f"{BASE}/BaseHistoricaNumerica/MacroEconomicos",
        "params": {**base_params(), "305": "SELIC", "961": DATE_RANGE_START},
    },
    {
        "id": 114, "name": "CalculoPoupanca",
        "url": f"{BASE}/BaseHistoricaNumerica/CalculoPoupanca",
        "params": {**base_params(), "961": DATE_RANGE_START},
    },
    {
        "id": 125, "name": "UltimosIntraday",
        "url": f"{BASE}/BaseHistoricaNumerica/UltimosIntraday",
        "params": {**base_params(), "10113": TICKER},
    },
    {
        "id": 126, "name": "Inflacao",
        "url": f"{BASE}/BaseHistoricaNumerica/Inflacao",
        "params": {**base_params()},
    },
    {
        "id": 131, "name": "ConversorDeMoedas",
        "url": f"{BASE}/BaseHistoricaNumerica/ConversorMoedas",
        "params": {**base_params()},
    },
    {
        "id": 135, "name": "CalculoPreco",
        "url": f"{BASE}/BaseHistoricaNumerica/CalculoPreco",
        "params": {**base_params(), "305": "LTN", "961": DATE_RANGE_START},
    },
    {
        "id": 136, "name": "CalculoTaxaPre",
        "url": f"{BASE}/BaseHistoricaNumerica/CalculoTaxaPre",
        "params": {**base_params(), "13539": "100", "961": DATE_RANGE_START},
    },
    {
        "id": 137, "name": "DiCetipAcumulado",
        "url": f"{BASE}/BaseHistoricaNumerica/DiCetipAcumulado",
        "params": {**base_params(), "961": DATE_RANGE_START},
    },
    {
        "id": 138, "name": "TabelaRetorno",
        "url": f"{BASE}/BaseHistoricaNumerica/TabelaRetorno",
        "params": {**base_params(), "13571": TICKER},
    },
    {
        "id": 139, "name": "TabelaRentabilidade",
        "url": f"{BASE}/BaseHistoricaNumerica/TabelaRentabilidade",
        "params": {**base_params(), "13571": TICKER, "13487": "1"},
    },
    {
        "id": 140, "name": "RetornoDiario",
        "url": f"{BASE}/BaseHistoricaNumerica/RetornoDiario",
        "params": {**base_params(), "305": TICKER, "961": DATE_RANGE_START},
    },
    {
        "id": 141, "name": "TitulosPublicosUltimos",
        "url": f"{BASE}/BaseHistoricaNumerica/TitulosPublicosUltimos",
        "params": {**base_params(), "10113": "LTN"},
    },
    {
        "id": 142, "name": "DiarioEx",
        "url": f"{BASE}/BaseHistoricaNumerica/DiarioEx",
        "params": {**base_params(), "305": TICKER, "961": DATE_RANGE_START, "1789": DATE_RANGE_END, "10029": "2"},
    },
    {
        "id": 143, "name": "CalcServer",
        "url": f"{BASE}/CalcServer",
        "params": {**base_params(), "13545": "PETR4"},
    },
    {
        "id": 144, "name": "CalculoCarteira",
        "url": f"{BASE}/BaseHistoricaNumerica/CalculoCarteira",
        "params": {**base_params(), "13571": TICKER, "961": DATE_RANGE_START},
    },
    {
        "id": 145, "name": "CalculoInflacao",
        "url": f"{BASE}/BaseHistoricaNumerica/CalculoInflacao",
        "params": {**base_params(), "305": "IPCA", "961": DATE_RANGE_START},
    },
    {
        "id": 150, "name": "FIIAnbimaBovespa",
        "url": f"{BASE}/BaseHistoricaNumerica/FIIAnbimaBovespa",
        "params": {**base_params(), "10113": "HGLG11"},
    },
    {
        "id": 151, "name": "SimbolosVolume",
        "url": f"{BASE}/BaseHistoricaNumerica/SimbolosVolumeServlet",
        "params": {**base_params()},
    },
    {
        "id": 154, "name": "EmpresasHistorico",
        "url": f"{BASE}/BaseHistoricaNumerica/Empresas",
        "params": {**base_params(), "305": TICKER, "961": DATE_RANGE_START},
    },
    {
        "id": 204, "name": "FechamentoPrimeiro",
        "url": f"{BASE}/BaseHistoricaNumerica/FechamentoPrimeiro",
        "params": {**base_params()},
    },
    {
        "id": 207, "name": "VolumesMediosSemMesAno",
        "url": f"{BASE}/BaseHistoricaNumerica/VolumesMediosSemMesAno",
        "params": {**base_params(), "10113": TICKER, "12078": "21"},
    },
    {
        "id": 208, "name": "Volatilidades",
        "url": f"{BASE}/BaseHistoricaNumerica/Volatilidades",
        "params": {**base_params(), "10113": TICKER, "12078": "21"},
    },

    # === AEInstrumentos ===
    {
        "id": 14, "name": "Eventos",
        "url": f"{BASE}/AEInstrumentos/output/EventoServlet",
        "params": {**base_params(), "305": TICKER},
    },
    {
        "id": 17, "name": "SecurityList",
        "url": f"{BASE}/AEInstrumentos/output/InstrumentoServlet",
        "params": {**base_params()},
    },
    {
        "id": 18, "name": "Bolsas",
        "url": f"{BASE}/AEInstrumentos/output/BolsaServlet",
        "params": {**base_params()},
    },
    {
        "id": 19, "name": "Mercados",
        "url": f"{BASE}/AEInstrumentos/output/MercadoServlet",
        "params": {**base_params()},
    },
    {
        "id": 20, "name": "Simbologias",
        "url": f"{BASE}/AEInstrumentos/output/SimbologiaServlet",
        "params": {**base_params()},
    },
    {
        "id": 21, "name": "Setores",
        "url": f"{BASE}/AEInstrumentos/output/SetorServlet",
        "params": {**base_params()},
    },
    {
        "id": 22, "name": "Classes",
        "url": f"{BASE}/AEInstrumentos/output/ClasseServlet",
        "params": {**base_params()},
    },
    {
        "id": 23, "name": "SubClasses",
        "url": f"{BASE}/AEInstrumentos/output/SubClasseServlet",
        "params": {**base_params()},
    },
    {
        "id": 24, "name": "Corretoras",
        "url": f"{BASE}/AEInstrumentos/output/CorretoraServlet",
        "params": {**base_params()},
    },
    {
        "id": 25, "name": "ComposicaoDeIndice",
        "url": f"{BASE}/AEInstrumentos/output/IndicesServlet",
        "params": {**base_params(), "305": "IBOV"},
    },
    {
        "id": 33, "name": "TabelasFeriados",
        "url": f"{BASE}/AEInstrumentos/output/TabelasFeriadosServlet",
        "params": {**base_params()},
    },
    {
        "id": 34, "name": "Feriados",
        "url": f"{BASE}/AEInstrumentos/output/FeriadosServlet",
        "params": {**base_params(), "12012": "1"},
    },
    {
        "id": 35, "name": "TiposDeInstrumento",
        "url": f"{BASE}/AEInstrumentos/output/TipoInstrumentoServlet",
        "params": {**base_params()},
    },
    {
        "id": 36, "name": "Timezones",
        "url": f"{BASE}/AEInstrumentos/output/TimezoneServlet",
        "params": {**base_params()},
    },
    {
        "id": 37, "name": "Horarios",
        "url": f"{BASE}/AEInstrumentos/output/HorarioServlet",
        "params": {**base_params()},
    },
    {
        "id": 38, "name": "HorarioData",
        "url": f"{BASE}/AEInstrumentos/output/HorarioDataServlet",
        "params": {**base_params(), "12018": "1"},
    },
    {
        "id": 39, "name": "Sequencial",
        "url": f"{BASE}/AEInstrumentos/output/SequencialServlet",
        "params": {**base_params(), "12026": "1", "12027": "1"},
    },
    {
        "id": 50, "name": "Acionistas",
        "url": f"{BASE}/AEInstrumentos/output/EmpresaAcionistasServlet",
        "params": {**base_params()},
    },
    {
        "id": 68, "name": "Empresas",
        "url": f"{BASE}/AEInstrumentos/output/EmpresaServlet",
        "params": {**base_params()},
    },
    {
        "id": 69, "name": "EmpresaDados",
        "url": f"{BASE}/AEInstrumentos/output/EmpresaDadosServlet",
        "params": {**base_params(), "13004": EMPRESA_COD},
    },
    {
        "id": 70, "name": "TipoIntervalo",
        "url": f"{BASE}/AEInstrumentos/output/TipoIntervaloServlet",
        "params": {**base_params()},
    },
    {
        "id": 85, "name": "BolsaDados",
        "url": f"{BASE}/AEInstrumentos/output/BolsaDadosServlet",
        "params": {**base_params(), "10086": "BVMF"},
    },
    {
        "id": 86, "name": "InstrumentoDados",
        "url": f"{BASE}/AEInstrumentos/output/InstrumentoDadosServlet",
        "params": {**base_params(), "305": TICKER},
    },
    {
        "id": 87, "name": "IndicadorPais",
        "url": f"{BASE}/AEInstrumentos/output/IndicadorPaisServlet",
        "params": {**base_params()},
    },
    {
        "id": 88, "name": "IndicadorTipo",
        "url": f"{BASE}/AEInstrumentos/output/IndicadorTipoServlet",
        "params": {**base_params()},
    },
    {
        "id": 89, "name": "Indicador",
        "url": f"{BASE}/AEInstrumentos/output/IndicadorServlet",
        "params": {**base_params()},
    },
    {
        "id": 96, "name": "IndicadorPeriodicidade",
        "url": f"{BASE}/AEInstrumentos/output/IndicadorPeriodicidadeServlet",
        "params": {**base_params()},
    },
    {
        "id": 97, "name": "IndicadorUnidade",
        "url": f"{BASE}/AEInstrumentos/output/IndicadorUnidadeServlet",
        "params": {**base_params()},
    },
    {
        "id": 98, "name": "Moeda",
        "url": f"{BASE}/AEInstrumentos/output/MoedaServlet",
        "params": {**base_params()},
    },
    {
        "id": 101, "name": "Contrato",
        "url": f"{BASE}/AEInstrumentos/output/ContratoServlet",
        "params": {**base_params()},
    },
    {
        "id": 117, "name": "Metodologia",
        "url": f"{BASE}/AEInstrumentos/output/MetodologiaServlet",
        "params": {**base_params()},
    },
    {
        "id": 118, "name": "Periodicidade",
        "url": f"{BASE}/AEInstrumentos/output/PeriodicidadeServlet",
        "params": {**base_params()},
    },
    {
        "id": 119, "name": "Benchmark",
        "url": f"{BASE}/AEInstrumentos/output/BenchmarkServlet",
        "params": {**base_params()},
    },
    {
        "id": 124, "name": "IndicadorTipoGrupo",
        "url": f"{BASE}/AEInstrumentos/output/IndicadorTipoGrupoServlet",
        "params": {**base_params()},
    },
    {
        "id": 146, "name": "BenchmarksFixos",
        "url": f"{BASE}/AEInstrumentos/output/BenchmarksFixosServlet",
        "params": {**base_params()},
    },
    {
        "id": 147, "name": "BenchmarksConfiguraveis",
        "url": f"{BASE}/AEInstrumentos/output/BenchmarksConfiguraveisServlet",
        "params": {**base_params()},
    },
    {
        "id": 148, "name": "AliquotasIR",
        "url": f"{BASE}/AEInstrumentos/output/AliquotasIRServlet",
        "params": {**base_params()},
    },
    {
        "id": 149, "name": "TitulosPublicosDados",
        "url": f"{BASE}/AEInstrumentos/output/TitulosPublicosDadosServlet",
        "params": {**base_params()},
    },
    {
        "id": 155, "name": "EmpresaAcoes",
        "url": f"{BASE}/AEInstrumentos/output/EmpresaAcoesServlet",
        "params": {**base_params(), "13004": EMPRESA_COD},
    },
    {
        "id": 156, "name": "EmpresaSetores",
        "url": f"{BASE}/AEInstrumentos/output/EmpresaSetoresServlet",
        "params": {**base_params()},
    },
    {
        "id": 157, "name": "MarketCapAcoes",
        "url": f"{BASE}/AEInstrumentos/output/MarketCapAcoesServlet",
        "params": {**base_params()},
    },

    # === aefundamental ===
    {
        "id": 45, "name": "OrgaosAdministracao",
        "url": f"{BASE}/aefundamental/{EMPRESA_COD}/diretores/orgaos",
        "params": {**base_params(), "13003": EMPRESA_COD, "13004": DATE_TODAY},
    },
    {
        "id": 46, "name": "Administradores",
        "url": f"{BASE}/aefundamental/{EMPRESA_COD}/diretores/administradores",
        "params": {**base_params(), "13003": EMPRESA_COD, "13004": DATE_TODAY, "13250": "1"},
    },
    {
        "id": 48, "name": "ExerciciosSociais",
        "url": f"{BASE}/aefundamental/{EMPRESA_COD}/diretores/exercicios",
        "params": {**base_params(), "13003": EMPRESA_COD, "13004": DATE_TODAY},
    },
    {
        "id": 58, "name": "Arquivos",
        "url": f"{BASE}/aefundamental/{EMPRESA_COD}/arquivos",
        "params": {**base_params(), "13003": EMPRESA_COD, "13004": DATE_TODAY, "13008": "1"},
    },
    {
        "id": 59, "name": "ArquivosFiltros",
        "url": f"{BASE}/aefundamental/{EMPRESA_COD}/arquivos/filtros",
        "params": {**base_params(), "13003": EMPRESA_COD, "13004": DATE_TODAY},
    },
    {
        "id": 60, "name": "ConsensoAtivos",
        "url": f"{BASE}/aefundamental/{EMPRESA_COD}/consenso/ativos",
        "params": {**base_params(), "13003": EMPRESA_COD, "13004": DATE_TODAY},
    },

    # === MarkitOutput2 ===
    {
        "id": 90, "name": "MarkitListaDatas",
        "url": f"{BASE}/MarkitOutput2/ListaDatas",
        "params": {**base_params(), "13336": "BR"},
    },
    {
        "id": 91, "name": "MarkitListaTipoCDS",
        "url": f"{BASE}/MarkitOutput2/ListaTipoCDS",
        "params": {**base_params()},
    },
    {
        "id": 92, "name": "MarkitIndices",
        "url": f"{BASE}/MarkitOutput2/Indices",
        "params": {**base_params(), "10047": "BR"},
    },
    {
        "id": 93, "name": "MarkitListaCDS",
        "url": f"{BASE}/MarkitOutput2/ListaCDS",
        "params": {**base_params(), "10047": "BR"},
    },
    {
        "id": 94, "name": "MarkitCDS",
        "url": f"{BASE}/MarkitOutput2/CDS",
        "params": {**base_params(), "10047": "BR", "13349": "5Y", "13339": "SR", "13350": DATE_TODAY, "13351": DATE_TODAY},
    },

    # === IntegracaoTabelas ===
    {
        "id": 105, "name": "ListaCategorias",
        "url": f"{BASE}/IntegracaoTabelas/ListaCategorias",
        "params": {**base_params()},
    },
    {
        "id": 107, "name": "CategoriaPreco",
        "url": f"{BASE}/IntegracaoTabelas/CategoriaPreco",
        "params": {**base_params()},
    },
    {
        "id": 111, "name": "ListaFormulas",
        "url": f"{BASE}/IntegracaoTabelas/ListaFormulas",
        "params": {**base_params()},
    },

    # === AEContent (tentativas alternativas) ===
    {
        "id": 108, "name": "CountNoticias",
        "url": f"{BASE}/AEContent/output/CountNewsServlet",
        "params": {**base_params(), "10095": "1"},
    },
    {
        "id": 110, "name": "topNewsLista",
        "url": f"{BASE}/AEContent/output/TopNewsListaServlet",
        "params": {**base_params(), "10095": "1"},
    },

    # === aetp/output (NEW API) ===
    {
        "id": 152, "name": "MaisLidasLista",
        "url": f"{BASE}/aetp/output/maislidas/lista",
        "params": {"10095": "1"},
    },
    {
        "id": 164, "name": "FundamentalDemonstrativoUltimo",
        "url": f"{BASE}/aetp/output/fundamental/demonstrativo/ultimo",
        "params": {**base_params(), "13004": EMPRESA_COD},
    },
    {
        "id": 165, "name": "FundamentalIndicadorMetadado",
        "url": f"{BASE}/aetp/output/fundamental/indicador/metadado",
        "params": {**base_params()},
    },
    {
        "id": 166, "name": "FundamentalIndicadorPeriodo",
        "url": f"{BASE}/aetp/output/fundamental/indicador/periodo",
        "params": {**base_params(), "13004": EMPRESA_COD, "13006": "1", "13007": "2025", "13008": "1"},
    },
    {
        "id": 167, "name": "FundamentalIndicadorHistorico",
        "url": f"{BASE}/aetp/output/fundamental/indicador/historico",
        "params": {**base_params(), "13004": EMPRESA_COD, "13786": "2020", "13787": "2025", "13006": "1", "13007": "2025", "13760": "1"},
    },
    {
        "id": 168, "name": "FundamentalIndicadorTicker",
        "url": f"{BASE}/aetp/output/fundamental/indicador/ticker",
        "params": {**base_params(), "10068": TICKER, "13780": "1"},
    },
    {
        "id": 170, "name": "FundamentalIndicadorTickerFixo",
        "url": f"{BASE}/aetp/output/fundamental/indicador/ticker-fixo",
        "params": {**base_params(), "13780": "1"},
    },
    {
        "id": 171, "name": "FundamentalIndicadorHistoricoDiario",
        "url": f"{BASE}/aetp/output/fundamental/indicador/historico-diario",
        "params": {**base_params(), "13004": EMPRESA_COD, "10057": DATE_RANGE_START, "10058": DATE_RANGE_END, "13760": "1"},
    },
    {
        "id": 172, "name": "FundamentalSetorSubsetorSegmento",
        "url": f"{BASE}/aetp/output/fundamental/setor",
        "params": {**base_params()},
    },
    {
        "id": 173, "name": "FundamentalEmpresasPorSetores",
        "url": f"{BASE}/aetp/output/fundamental/empresa/setores",
        "params": {**base_params(), "13798": "1"},
    },
    {
        "id": 175, "name": "FundamentalArquivosCategorias",
        "url": f"{BASE}/aetp/output/fundamental/arquivos/categoria",
        "params": {**base_params()},
    },
    {
        "id": 176, "name": "FundamentalArquivosEspecies",
        "url": f"{BASE}/aetp/output/fundamental/arquivos/especie",
        "params": {**base_params()},
    },
    {
        "id": 177, "name": "FundamentalArquivosTipos",
        "url": f"{BASE}/aetp/output/fundamental/arquivos/tipo",
        "params": {**base_params()},
    },
    {
        "id": 179, "name": "FundamentalEmpresaMetadado",
        "url": f"{BASE}/aetp/output/fundamental/empresa/metadado",
        "params": {**base_params()},
    },
    {
        "id": 180, "name": "FundamentalEmpresaDados",
        "url": f"{BASE}/aetp/output/fundamental/empresa",
        "params": {**base_params(), "13004": EMPRESA_COD},
    },
    {
        "id": 181, "name": "FundamentalEmpresaRankingIndicador",
        "url": f"{BASE}/aetp/output/fundamental/empresa/ranking",
        "params": {**base_params(), "13760": "1"},
    },
    {
        "id": 183, "name": "FundamentalEmpresaAcoesUnits",
        "url": f"{BASE}/aetp/output/fundamental/empresa/acao",
        "params": {**base_params(), "13004": EMPRESA_COD},
    },
    {
        "id": 184, "name": "FundamentalEmpresaTickerPrecoVolume",
        "url": f"{BASE}/aetp/output/fundamental/indicador/ticker-preco-volume",
        "params": {**base_params()},
    },
    {
        "id": 185, "name": "FundamentalEmpresaIndicadorCategorias",
        "url": f"{BASE}/aetp/output/fundamental/indicador/categoria",
        "params": {**base_params()},
    },
    {
        "id": 186, "name": "FundamentalEventosJcpDividendos",
        "url": f"{BASE}/aetp/output/fundamental/empresa/eventos/jcp-dividendos",
        "params": {**base_params(), "13004": EMPRESA_COD, "10068": TICKER},
    },
    {
        "id": 187, "name": "FundamentalCarteiraTopFundos",
        "url": f"{BASE}/aetp/output/fundamental/carteira/top-fundos",
        "params": {**base_params(), "13004": EMPRESA_COD},
    },
    {
        "id": 188, "name": "FundamentalEmpresaDistribuicao",
        "url": f"{BASE}/aetp/output/fundamental/investimentos/distribuicao",
        "params": {**base_params(), "13004": EMPRESA_COD},
    },
    {
        "id": 191, "name": "FundamentalEventosAgrupados",
        "url": f"{BASE}/aetp/output/fundamental/empresa/eventos/agrupados",
        "params": {**base_params(), "13004": EMPRESA_COD, "10068": TICKER, "10057": "20200101", "10058": DATE_RANGE_END, "10029": "2"},
    },
    {
        "id": 192, "name": "FundamentalEventosDy",
        "url": f"{BASE}/aetp/output/fundamental/empresa/eventos/dividend-yield",
        "params": {**base_params(), "13004": EMPRESA_COD, "10068": TICKER, "10057": "20200101", "10058": DATE_RANGE_END, "10029": "2"},
    },
    {
        "id": 193, "name": "FundamentalAcionistaDatas",
        "url": f"{BASE}/aetp/output/fundamental/acionista/datas",
        "params": {**base_params(), "13004": EMPRESA_COD},
    },
    {
        "id": 194, "name": "FundamentalCarteiraRecomendadaUltima",
        "url": f"{BASE}/aetp/output/fundamental/empresa/carteira-recomendada/ultima",
        "params": {**base_params(), "10087": "1"},
    },
    {
        "id": 195, "name": "FundamentalCarteiraRecomendadaTicker",
        "url": f"{BASE}/aetp/output/fundamental/empresa/carteira-recomendada/ticker",
        "params": {**base_params(), "10113": TICKER},
    },
    {
        "id": 197, "name": "FundamentalCarteiraRecomendadaMudancas",
        "url": f"{BASE}/aetp/output/fundamental/empresa/carteira-recomendada/mudancas",
        "params": {**base_params(), "10087": "1"},
    },
    {
        "id": 198, "name": "FundamentalCarteiraRecomendadaCorretoras",
        "url": f"{BASE}/aetp/output/fundamental/empresa/carteira-recomendada/corretoras",
        "params": {**base_params()},
    },
    {
        "id": 199, "name": "FundamentalIndicadorAgrupado",
        "url": f"{BASE}/aetp/output/fundamental/indicador/agrupado",
        "params": {**base_params()},
    },
    {
        "id": 200, "name": "FundamentalIndicadorPeriodoLista",
        "url": f"{BASE}/aetp/output/fundamental/indicador/periodo/lista",
        "params": {**base_params()},
    },
    {
        "id": 201, "name": "FundamentalAtivoSimbolo",
        "url": f"{BASE}/aetp/output/fundamental/ativo/simbolo",
        "params": {**base_params()},
    },
    {
        "id": 202, "name": "FundamentalAtivoCotacao",
        "url": f"{BASE}/aetp/output/fundamental/ativo/cotacao",
        "params": {**base_params()},
    },
    {
        "id": 203, "name": "FundamentalAtivoQuantidade",
        "url": f"{BASE}/aetp/output/fundamental/ativo/quantidade",
        "params": {**base_params()},
    },
    {
        "id": 205, "name": "FundamentalArquivosDemonstrativos",
        "url": f"{BASE}/aetp/output/fundamental/arquivos/demonstrativos",
        "params": {**base_params()},
    },
    {
        "id": 210, "name": "RankingEmpresas",
        "url": f"{BASE}/aetp/output/fundamental/empresa/ranking-mais-acessadas",
        "params": {**base_params(), "10057": "20260101", "10058": DATE_RANGE_END},
    },
    {
        "id": 211, "name": "CalendarioEventosCorporativos",
        "url": f"{BASE}/aetp/output/fundamental/calendario-eventos-corporativos",
        "params": {**base_params(), "10057": "20260501", "10058": DATE_RANGE_END},
    },
    {
        "id": 212, "name": "TickersEmpresas",
        "url": f"{BASE}/aetp/output/fundamental/ticker-external-fields",
        "params": {**base_params(), "10113": TICKER},
    },
    {
        "id": 213, "name": "Indices",
        "url": f"{BASE}/aetp/output/ativos/indice",
        "params": {**base_params()},
    },
    {
        "id": 214, "name": "ComposicaoIndices",
        "url": f"{BASE}/aetp/output/ativos/indice/composicao",
        "params": {**base_params(), "13158": "IBOV", "10098": "1", "10099": "100"},
    },

    # === aetp/output Fundos ===
    {
        "id": 158, "name": "FundosListaTipoAtivo",
        "url": f"{BASE}/aetp/output/fundos/tipoativo",
        "params": {**base_params()},
    },
    {
        "id": 159, "name": "FundosListaTipoAplicacao",
        "url": f"{BASE}/aetp/output/fundos/tipoaplicacao",
        "params": {**base_params()},
    },
    {
        "id": 222, "name": "FundosBuscaRapida",
        "url": f"{BASE}/aetp/output/fundos/buscarapida",
        "params": {**base_params()},
    },

    # === contentProxyOutput (quick check if still broken) ===
    {
        "id": 133, "name": "CDIRentabilidade",
        "url": f"{BASE}/contentProxyOutput/ContentProxyServlet/Fundos/CDIRentabilidade/getRentabilidadePorData",
        "params": {**base_params(), "10077": DATE_TODAY},
    },

    # === Energia ===
    {
        "id": 174, "name": "EnergiaHorarioIntraday",
        "url": f"{BASE}/aetp/output/energia/search-datetime",
        "params": {**base_params(), "10113": "PLD", "10074": "202605200000", "10075": "202605201800"},
    },
]


def main():
    session = httpx.Client(
        headers={"User-Agent": "bcsys32/7.0"},
        verify=False,
        trust_env=False,
    )

    results = []
    total = len(ENDPOINTS)
    
    print(f"Probing {total} endpoints...\n")
    print(f"{'#':<4} {'ID':<4} {'ENDPOINT':<38} {'STATUS':<6} {'FMT':<12} {'SIZE':<8} {'NOTES'}")
    print("-" * 120)

    for i, ep in enumerate(ENDPOINTS, 1):
        name = ep["name"]
        try:
            r = session.get(ep["url"], params=ep["params"], timeout=TIMEOUT)
            info = classify_response(r)
        except httpx.TimeoutException:
            info = {"status": "TIMEOUT", "format": "—", "size": 0, "preview": "", "error": "timeout"}
        except Exception as e:
            info = {"status": "EXCEPT", "format": "—", "size": 0, "preview": str(e)[:100], "error": str(e)[:50]}

        # Determine notes
        notes = ""
        if info.get("error"):
            notes = info["error"]
        elif info["format"] in ("xml", "json", "json_array") and info["size"] > 100:
            notes = "HAS DATA"
        elif info["format"] == "binary_soh" and info["size"] > 20:
            notes = "BINARY DATA"
        elif info["size"] < 50:
            notes = "empty/minimal"

        status_str = str(info["status"])
        size_str = f"{info['size']}B" if isinstance(info["size"], int) else "—"
        
        print(f"{i:<4} {ep['id']:<4} {name:<38} {status_str:<6} {info['format']:<12} {size_str:<8} {notes}")
        
        results.append({
            "id": ep["id"],
            "name": name,
            "url": ep["url"],
            "status": info["status"],
            "format": info["format"],
            "size": info["size"],
            "error": info.get("error", ""),
            "preview": info.get("preview", ""),
        })

        time.sleep(0.1)  # Be nice to the server

    # Summary
    print("\n" + "=" * 120)
    print("SUMMARY")
    print("=" * 120)
    
    working = [r for r in results if r["status"] == 200 and r["size"] > 100 and not r["error"]]
    errors = [r for r in results if r["status"] != 200 or r.get("error")]
    empty = [r for r in results if r["status"] == 200 and r["size"] <= 100 and not r.get("error")]
    
    print(f"\n✅ WORKING ({len(working)} endpoints with data):")
    for r in working:
        print(f"   [{r['id']:>3}] {r['name']:<38} {r['format']:<10} {r['size']}B")
    
    print(f"\n⚠️ EMPTY/MINIMAL ({len(empty)} endpoints):")
    for r in empty:
        print(f"   [{r['id']:>3}] {r['name']:<38} {r['format']:<10} {r['size']}B")
    
    print(f"\n❌ ERRORS ({len(errors)} endpoints):")
    for r in errors:
        print(f"   [{r['id']:>3}] {r['name']:<38} HTTP {r['status']:<5} {r['error'][:50]}")

    # Save detailed results
    with open("scripts/probe_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nDetailed results saved to scripts/probe_results.json")


if __name__ == "__main__":
    main()

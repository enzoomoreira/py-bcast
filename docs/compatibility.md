# Broadcast+ Feature Compatibility Checklist

Mapeamento completo de funcionalidades do ecossistema Broadcast+ vs. cobertura da lib `py-bcast`.

**Fontes de dados cruzadas:**
- CHM do Add-In Excel (funções BC, BCH, BCS, BCLink)
- `services_parsed.json` (227 endpoints HTTP registrados no backend)
- Varredura automática (`scripts/probe_all_endpoints.py`) executada em 2025-05-20

**Legenda:**
- ✅ Implementado e testado na lib
- ✓ Endpoint confirmado funcional (retorna dados), mas não implementado na lib
- ❌ Bloqueado/quebrado — ver motivo na coluna
- 🚫 Fora de escopo (contribuição, admin, UI-only)

**Categorias de falha:**
- `PROPRIETARY` — Protocolo binário proprietário (88007). Inacessível sem reverse-engineering do protocolo Java
- `DEAD_BACKEND` — Backend AWS/GraphQL offline ou retornando 500. Pode voltar no futuro
- `AETP_ONLY` — Requer pré-registro de query via protocolo AETP TCP:8100 (Query=NONE)
- `PARAMS` — Parâmetros corretos desconhecidos; possivelmente funcional com params certos
- `BUG` — Bug no servidor (SQL, etc.)

---

## 1. Funções do Add-In Excel (CHM)

### 1.1 `=BC(ativo; campo)` — Cotação Tempo Real

| Funcionalidade | Status | py-bcast | Notas |
|---|---|---|---|
| Cotação em tempo real (streaming) | ✅ | `bdp()` | Via DDE, Service=BC, Topic=COT |
| Multi-ativo simultâneo | ✅ | `bdps()` | Lista de tickers |
| Campos: ULT, VAR, MAX, MIN, ABE, FEC, OCP, OVD | ✅ | `bdp()` | Todos os campos DDE |
| Campos: NEG, QUL, MED, QTT, VTT, VOC, VOV | ✅ | `bdp()` | |
| Campos: CNG, CAB, AJU (mercadorias/futuros) | ✅ | `bdp()` | |
| Campos: HOR, HOC, HOV (timestamps) | ✅ | `bdp()` | |
| Campos: TND, DIF, DIFSEM, DIFMES, etc. | ✅ | `bdp()` | Variações calculadas |
| Campos: NOM (nome do ativo) | ✅ | `bdp()` | |
| Topic ATIVO (dados cadastrais via DDE) | ✅ | `bdp()` | Topic diferente de COT |

### 1.2 `=BCH(ativo; campo; data)` — Histórico

| Funcionalidade | Status | py-bcast | Notas |
|---|---|---|---|
| Histórico de fechamento por data | ✅ | `bdh()` | HTTP HistoricoFechamentos |
| Range de datas (data_ini, data_fim) | ✅ | `bdh()` | Loop automático por dia |
| PERIODO=D (diário) | ✅ | `bdh()` | Padrão |
| PERIODO=I (intradiário 1-240 min) | ✅ | `bdi()` | HTTP HistoricoIntraday, 2-min bars |
| PERIODO=S (semanal) / PERIODO=M (mensal) | ✓ | — | Endpoint suporta, não exposto na lib |
| NOMINAL=S (série nominal, sem ajuste) | ✓ | — | Endpoint `DiarioEx` bloqueado (Query=NONE) |
| Campos: ULT, FEC, MAX, MIN, ABE, MED, DRF, NEG, QTT, VTT | ✅ | `bdh()`/`bdi()` | |
| Campos: CAB, AJU, CNG (futuros) | ✅ | `bdh()` | Retornados quando aplicável |
| ASC/DESC/TITULO/LINHAS (ordenação, headers, limite) | 🚫 | — | Client-side (trivial via Python) |

### 1.3 `=BCS(ativo; consulta)` — Consultas Estruturadas

| Funcionalidade | Status | py-bcast | Notas |
|---|---|---|---|
| EVENTOS (eventos corporativos) | ❌ | — | `EventoServlet` retorna error 88007 (binary-only) |
| CARTEIRA (composição de índices) | ❌ | — | `IndicesServlet` retorna error 88007 |

> **Nota**: Ambas funcionalidades do BCS dependem do `AEInstrumentos` que usa protocolo binário proprietário inacessível. Porém dados equivalentes existem via `aetp/output/` (ver seção 5).

### 1.4 `=BCMONITOR` — Contribuição (Broadcast Link)

| Funcionalidade | Status | py-bcast | Notas |
|---|---|---|---|
| BCMONITOR, BCSTATUS, BCSTART, BCSTOP | 🚫 | — | Write-only, fora de escopo |

---

## 2. BaseHistoricaNumerica — Histórico de Preços (XML)

Todos retornam XML com `<RESPONSE><STATUS>success</STATUS>...<TICKS>`.

### 2.1 Confirmados Funcionais

| ID | Endpoint | Status | Dados | Params Chave |
|---|----------|--------|-------|--------------|
| 10 | HistoricoDiario | ❌ | — | `AETP_ONLY` — Requer query pré-registrada |
| 11 | **HistoricoIntraday** | ✅ | 2-min OHLCV bars | `305`=ticker, `10074`=YYYYMMDDHHMM |
| 12 | **HistoricoTick** | ✅ | Tick-by-tick (intl only) | `305`=ticker, `10071/10072`=YYYYMMDDHHMMSS |
| 13 | **HistoricoData** | ✅ | OHLCV+VWAP para 1 data | `305`=ticker, `10077`=YYYYMMDD |
| 32 | **HistoricoFechamentos** | ✅ | Closing prices | `10113`=tickers, `DatasTolerancia`=YYYYMMDD |
| 75 | **HistoricoDiarioSimbolos** | ✓ | Multi-ticker daily (17KB) | `10113`=tickers sep `;`, `961`=start_date |
| 84 | **VolumesMedios** | ✅ | Avg vol 1/2/3/6/12 meses | `10113`=ticker |
| 95 | **MacroEconomicos** | ✅ | Séries macro (FX, índices, AETAXAS) | `305`=ticker, `DataInicio`/`DataFim`=YYYYMMDD |
| 125 | **UltimosIntraday** | ✓ | Último snapshot intraday | `10113`=ticker |
| 126 | **Inflacao** | ✅ | 17 índices de inflação, 12 meses | Sem params extras |
| 137 | **DiCetipAcumulado** | ✅ | CDI/DI acumulado diário (desde 1986) | `DataInicio`/`DataFim`=YYYYMMDD |
| 140 | **RetornoDiario** | ✅ | Retorno diário ajustado | `305`=ticker, `DataInicio`/`DataFim`=YYYYMMDD |
| 150 | **FIIAnbimaBovespa** | ✓ | FII: DY, last div, vol médio, etc. | `10113`=ticker (ex: HGLG11) |
| 154 | **EmpresasHistorico** | ✓ | Balanço completo trimestral (1.2MB!) | `305`=ticker, `961`=start_date |
| 208 | **Volatilidades** | ✓ | Volatilidade histórica | `10113`=ticker, `12078`=dias |

### 2.2 Renda Fixa / Cálculos

| ID | Endpoint | Status | Dados | Params Chave |
|---|----------|--------|-------|--------------|
| 76 | **Fundos** | ✓ | Histórico de cotas (OHLC, 24KB) | `305`=ticker, `961`=start |
| 77 | **TitulosPublicos** | ✓ | Títulos do Tesouro | `305`=LTN/NTN, `961`=start |
| 82 | **FundosRentabilidade** | ✓ | Rentabilidade do fundo | `305`=ticker |
| 114 | **CalculoPoupanca** | ✓ | Rendimento poupança diário (5.7KB) | `961`=start |
| 135 | **CalculoPreco** | ✓ | Preço unitário renda fixa | `305`=titulo, `961`=start |
| 136 | **CalculoTaxaPre** | ✓ | Curva de taxa pré acumulada (6.5KB) | `13539`=notional, `961`=start |
| 141 | **TitulosPublicosUltimos** | ✓ | Últimos preços de títulos | `10113`=ticker |
| 207 | **VolumesMediosSemMesAno** | ✓ | Volumes médios históricos | `10113`=ticker, `12078`=dias |

### 2.3 Bloqueados / Com Erro

| ID | Endpoint | Erro | Categoria |
|---|----------|------|--------|
| 26 | HistoricoUltimosPregoes | `Query=NONE` | `AETP_ONLY` |
| 40 | Players | SQL bug | `BUG` — "field BVMF not found in tick descriptor" |
| 41 | TimesTrades | Empty ticks | `PARAMS` — formato OK mas sem dados para B3 |
| 81 | FundosIndicadores | `api_error` | `PARAMS` |
| 83 | FechamentoFormula | `api_error` | `PARAMS` |
| 131 | ConversorDeMoedas | `api_error` | `PARAMS` |
| 138 | TabelaRetorno | `api_error` | `PARAMS` |
| 139 | TabelaRentabilidade | `api_error` | `PARAMS` |
| 142 | DiarioEx | `Query=NONE` | `AETP_ONLY` |
| 144 | CalculoCarteira | `api_error` | `PARAMS` |
| 145 | CalculoInflacao | `api_error` | `PARAMS` |
| 204 | FechamentoPrimeiro | `api_error` | `PARAMS` |

---

## 3. AEInstrumentos — Dados de Referência

**TODOS bloqueados** (`PROPRIETARY`): retornam `ErrorCode=88007, Tipo de resposta indisponível ou inválido`.
Protocolo binário proprietário Java que não aceita `TipoResposta=xml`.
Estes endpoints só são acessíveis pelo terminal desktop (Java/Swing client).
**Dados equivalentes disponíveis via `aetp/output/`** (seção 5).

| ID | Endpoint | Status | Dados que teria |
|---|----------|--------|-----------------|
| 14 | EventoServlet | ❌ | Eventos corporativos |
| 17 | InstrumentoServlet | ❌ | Lista de instrumentos |
| 18 | BolsaServlet | ❌ | Lista de bolsas |
| 19 | MercadoServlet | ❌ | Lista de mercados |
| 20 | SimbologiaServlet | ❌ | Mapa de símbolos |
| 21 | SetorServlet | ❌ | Setores |
| 22 | ClasseServlet | ❌ | Classes de ativos (404) |
| 23 | SubClasseServlet | ❌ | Subclasses (404) |
| 24 | CorretoraServlet | ❌ | Lista corretoras |
| 25 | IndicesServlet | ❌ | Composição de índices |
| 33-39 | Feriados, Horarios, etc. | ❌ | Dados de referência |
| 50 | EmpresaAcionistasServlet | ❌ | Estrutura acionária |
| 68-70 | Empresas, TipoIntervalo | ❌ | Cadastro de empresas |
| 85-89 | BolsaDados, Indicadores | ❌ | Dados de bolsa/indicadores |
| 96-101 | Periodicidade, Moeda, Contrato | ❌ | Referência |
| 117-119 | Metodologia, Periodicidade, Benchmark | ❌ | Referência |
| 146-149 | Benchmarks, AliquotasIR, TitulosPublicosDados | ❌ | Referência |
| 155-157 | EmpresaAcoes, EmpresaSetores, MarketCap | ❌ | Referência |

---

## 4. aefundamental — Dados Fundamentalistas (Binary SOH)

Protocolo: SOH (0x01) separa records, NULL (0x00) separa fields. Mesmo decoder do `bconsensus()`.

### 4.1 Confirmados Funcionais

| ID | Endpoint | Status | Dados | Size |
|---|----------|--------|-------|------|
| 52 | **Consenso** | ✅ | Buy/Hold/Sell, target prices | ~200B |
| 58 | **Arquivos** | ✓ | Lista de documentos/filings | 3.2KB |
| 60 | **Consenso Ativos** | ✓ | Lista ativos com consenso | 102B |
| 45 | **Orgaos Administracao** | ✓ | Órgãos da diretoria | 102B |
| 46 | **Administradores** | ✓ | Membros da diretoria | 102B |
| 48 | **Exercicios Sociais** | ✓ | Exercícios fiscais | 102B |
| 69 | **EmpresaDados** | ✓ | Dados da empresa (binary SOH) | 1KB |

### 4.2 Bloqueados

| ID | Endpoint | Erro | Motivo |
|---|----------|------|--------|
| 51 | Demonstracao detalhado | Backend offline | GraphQL (AWS ELB) unreachable |
| 53-54 | Marketcap Diario/Historico | No data | Retorna instrumento errado |
| 55-57 | Indicadores (Resumido/Detalhado/Ativo) | 404 | Endpoints não existem |

---

## 5. aetp/output — API Nova (Binary SOH)

**Maior descoberta da varredura**: ~40 endpoints funcionais com dados ricos.
Todos usam o mesmo protocolo binary SOH do `bconsensus()`.

### 5.1 Fundamental — Empresa

| ID | Endpoint | Status | Dados | Size |
|---|----------|--------|-------|------|
| 164 | **DemonstrativoUltimo** | ✓ | Datas do último balanço/ITR | 394B |
| 172 | **SetorSubsetorSegmento** | ✅ | Classificação setorial B3 (42 setores) | 1.4KB |
| 173 | **EmpresasPorSetores** | ✓ | Todas empresas de um setor | 14.5KB |
| 179 | **EmpresaMetadado** | ✅ | Metadados de TODAS as empresas | 101KB |
| 180 | **EmpresaDados** | ✅ | Empresa: CNPJ, nome, setor, IPO date | 1.2KB |
| 183 | **EmpresaAcoesUnits** | ✓ | Ações ON/PN, free float | 348B |

### 5.2 Fundamental — Dividendos / Eventos

| ID | Endpoint | Status | Dados | Size |
|---|----------|--------|-------|------|
| 186 | **EventosJcpDividendos** | ✅ | Histórico completo JCP+Div (desde 1995!) | 274B+ |
| 192 | **EventosDividendYield** | ✅ | DY histórico por ex-date | 2.6KB |
| 193 | **AcionistaDatas** | ✓ | Datas de composição acionária | 1.6KB |
| 211 | **CalendarioEventosCorporativos** | ✅ | Agenda de eventos (AGO, ITR, etc.) | **72KB** |

### 5.3 Fundamental — Carteira Recomendada

| ID | Endpoint | Status | Dados | Size |
|---|----------|--------|-------|------|
| 194 | **CarteiraRecomendadaUltima** | ✅ | Última carteira de uma corretora | 9.3KB |
| 195 | **CarteiraRecomendadaTicker** | ✓ | Em quais carteiras o ticker está | 7.9KB |
| 197 | **CarteiraRecomendadaMudancas** | ✓ | Mudanças na carteira | 144B |
| 198 | **CarteiraRecomendadaCorretoras** | ✅ | Lista de corretoras com carteiras | 318B |

### 5.4 Fundamental — Indicadores

| ID | Endpoint | Status | Erro |
|---|----------|--------|------|
| 165 | **IndicadorMetadado** | ✅ | 84 indicadores metadata (24.6KB) |
| 171 | **IndicadorHistoricoDiario** | ✅ | Market Cap, Beta diário — funciona! |
| 166 | IndicadorPeriodo | ❌ | `DEAD_BACKEND` — GraphQL: "Bad Request" |
| 167 | IndicadorHistorico | ❌ | `DEAD_BACKEND` — GraphQL: "Bad Request" |
| 168/170 | IndicadorTicker/TickerFixo | ❌ | `PARAMS` — "Não foram encontrados registros" |
| 182 | DemonstrativoFiltros | ❌ | `DEAD_BACKEND` — GraphQL: "Bad Request" |
| 214 | ComposicaoIndices | ❌ | `DEAD_BACKEND` — GraphQL: "Bad Request" |

> **Nota**: O backend GraphQL da AWS (`ab684f71...elb.us-east-1.amazonaws.com`) está offline.
> Todos os endpoints que dependem de queries de indicadores financeiros (P/L, ROE, DRE) estão indisponíveis.

### 5.5 Fundamental — Metadados / Classificação

| ID | Endpoint | Status | Dados | Size |
|---|----------|--------|-------|------|
| 175 | **ArquivosCategorias** | ✓ | Categorias de filings | 4KB |
| 176 | **ArquivosEspecies** | ✓ | Espécies de documentos | 2.2KB |
| 177 | **ArquivosTipos** | ✓ | Tipos de documentos | 4.4KB |
| 185 | **IndicadorCategorias** | ✓ | Categorias de indicadores | 252B |
| 205 | **ArquivosDemonstrativos** | ✓ | Lista de demonstrativos | 139B |
| 212 | **TickersEmpresas** | ✓ | Campos externos de um ticker | 109B |

### 5.6 Fundamental — Fundos

| ID | Endpoint | Status | Dados | Size |
|---|----------|--------|-------|------|
| 187 | **CarteiraTopFundos** | ✓ | Top fundos que investem no ativo | 8.5KB |
| 188 | EmpresaDistribuicao | ✓ | Distribuição investimentos | 91B (vazio) |

### 5.7 Ativos / Índices

| ID | Endpoint | Status | Dados | Size |
|---|----------|--------|-------|------|
| 201 | **AtivoSimbolo** | ✅ | Lookup de ativo | 139B |
| 202 | **AtivoCotacao** | ✅ | Cotação de ativo | 136B |
| 203 | **AtivoQuantidade** | ✅ | Qtd ações do ativo | 136B |
| 213 | **Indices** | ✅ | Lista de 38 índices B3 (IBOV, IFIX, SMLL...) | 244B |

### 5.8 Fundos (aetp)

| ID | Endpoint | Status | Dados | Size |
|---|----------|--------|-------|------|
| 158 | **FundosListaTipoAtivo** | ✓ | Tipos de ativo para fundos | 2KB |
| 159 | **FundosListaTipoAplicacao** | ✓ | Tipos de aplicação | 1.6KB |
| 222 | FundosBuscaRapida | ✓ | Busca de fundos | 115B |

### 5.9 Energia

| ID | Endpoint | Status | Dados | Size |
|---|----------|--------|-------|------|
| 174 | EnergiaHorarioIntraday | ✓ | Mercado de energia | 118B (sem dados úteis) |

---

## 6. AEContent — Notícias

### 6.1 Protocolo Binário (BLOQUEADO)

Endpoints AETP originais para notícias — todos bloqueados por subscrição (error 88007).

| ID | Endpoint | Status | Notas |
|---|----------|--------|-------|
| 27 | Noticias (NewsServlet) | ❌ | Error 88007 |
| 28 | Conteudo (ContentServlet) | ❌ | Error 88007 |
| 29 | Cadernos (CadernoServlet) | ❌ | Error 88007 |
| 30 | Arquivo (FileServlet) | ❌ | Error 88007 |
| 108 | CountNoticias | ❌ | Binary SOH, 81B (contém apenas error code) |
| 110 | topNewsLista | ❌ | Binary SOH, 81B (contém apenas error code) |
| 152 | MaisLidasLista (aetp) | ❌ | Binary SOH, 63B (apenas header) |
| 153 | Noticias Relacionadas | ❌ | Error 88007 |

### 6.2 CentralMultimidia (FUNCIONAL — sem autenticação!) ✅

API ASP.NET descoberta em `/CentralMultimidia/`. Retorna **todas** as notícias do Broadcast
por ID sequencial (atualmente ~56M), incluindo texto, Dow Jones, press releases, podcasts.
**Não requer sessão, token ou assinatura.**

| Endpoint | Método | Status | Dados |
|----------|--------|--------|-------|
| `/CentralMultimidia/Handlers/MultimediaCenterHandler.ashx` | GET | ✅ | Listagem por categoria (XML) |
| `/CentralMultimidia/Default.aspx/GetVideoContent` | POST | ✅ | Conteúdo completo por ID (JSON) |
| `/CentralMultimidia/` | GET | ✅ | Página HTML com categorias |

**py-bcast**: `bnews(id)`, `bnews_latest(n)`, `bnews_search(category)`

**Categorias de multimídia disponíveis:**

| ID | Categoria | Tipo |
|----|-----------|------|
| 567 | Comentário Financeiro | Podcast/Video |
| 566 | Comentário Agrícola | Podcast/Video |
| 748 | Podcast | Podcast |
| 848 | Comentário Político | Podcast/Video |
| 849 | Cabeça de Gestor | Podcast/Video |
| 857 | E-Investidor-Mídia | Podcast/Video |
| 1133 | Capital Insights | Podcast/Video |
| 1160 | Crédito Privado 360 | Podcast/Video |

**Nota**: O endpoint `GetVideoContent` aceita ANY ID numérico — não só multimídia.
IDs são sequenciais e cobrem AE-News, Dow Jones Newswires, Trading News, Press Releases, etc.

---

## 7. contentProxyOutput — Fundos CVM

**TODOS retornam HTTP 500** (Server Error). Backend Java/Tomcat com stack trace.

| IDs | Endpoints | Status |
|---|----------|--------|
| 61-67, 73-74, 100, 115-116, 120-123, 127-130, 132, 134 | Todos os Fundos CVM | ❌ 500 |
| 133 | CDIRentabilidade | ❌ 500 |

---

## 8. MarkitOutput2 — CDS / Crédito

| ID | Endpoint | Status | Notas |
|---|----------|--------|-------|
| 91 | **MarkitListaTipoCDS** | ✓ | Retorna tipos de CDS (268B XML) |
| 90 | MarkitListaDatas | ❌ | api_error |
| 92 | MarkitIndices | ❌ | api_error |
| 93 | MarkitListaCDS | ❌ | api_error |
| 94 | MarkitCDS | ❌ | api_error |

---

## 9. IntegracaoTabelas — Commodities / Tabelas

| ID | Endpoint | Status | Dados | Size |
|---|----------|--------|-------|------|
| 105 | **ListaCategorias** | ✓ | Categorias (Área, Volume, Produtividade) | 876B |
| 107 | **CategoriaPreco** | ✓ | Moedas/símbolos de preço | 1KB |
| 111 | **ListaFormulas** | ✓ | Fórmulas disponíveis | 358B |
| 102-104, 106 | Filtros, Conteúdo, Proporção | ✓ | Requer IDs específicos | — |

---

## 10. Acesso Local (sem HTTP)

| Funcionalidade | Status | py-bcast | Notas |
|---|---|---|---|
| Banco de instrumentos (aetp_17.dat) | ✅ | `InstrumentDB`, `bsearch()` | 623K instrumentos, XOR(0xAE) |
| DDE streaming (subscribe + callback) | ✅ | `bdp()`, `bdps()` | Requer bcsys32.exe |
| AETP TCP:8100 | ❌ | — | Protocolo binário interno, não cracked |
| SPC .NET (AESpcNET.dll) | ❌ | — | Dead end |

---

## Resumo Quantitativo (pós-varredura)

| Status | Count | Descrição |
|--------|-------|-----------|
| ✅ Implementado na lib | **27 funções** | bdp, bdps, bdh, bdh_ohlcv, bdi, bdt, bmacro, bdi_cdi, breturn, bvolume, binflation, bconsensus, bcompany, bindices, bsectors, bquote, btickers, bshares, bindicators, bindicator_meta, bcalendar, bdividends, bdy, bportfolios, bportfolio, bsearch, InstrumentDB |
| ✓ Funcional, não implementado | **~35** | Endpoints que retornam dados reais (FIIs, Fundos, Financials, TitulosPublicos, etc.) |
| ❌ Bloqueado/Quebrado | ~70 | Ver categorias abaixo |
| 🚫 Fora de escopo | ~8 | Contribuição, admin, banners |

### Categorias de Falha

| Categoria | Count | Endpoints | Possibilidade de Resolver |
|-----------|-------|-----------|---------------------------|
| `PROPRIETARY` | ~58 | AEInstrumentos, AEContent | ❌ Requer reverse-engineering do protocolo Java binário |
| `DEAD_BACKEND` | ~37 | contentProxyOutput (500s), GraphQL (AWS offline) | ⏳ Pode voltar se backend for restaurado |
| `AETP_ONLY` | ~3 | HistoricoDiario, DiarioEx, UltimosPregoes | ❌ Requer suporte ao protocolo AETP TCP:8100 |
| `PARAMS` | ~8 | Vários BaseHistoricaNumerica | 🔄 Possivelmente funcional com params corretos |
| `BUG` | ~1 | Players (SQL error) | ❌ Bug no servidor |

---

## Próximos Endpoints Para Implementar (Prioridade)

Ranqueados por valor para investidores (dos que confirmamos funcionais mas não implementamos):

| # | Endpoint | Tipo | O que retorna |
|---|----------|------|---------------|
| 1 | **EmpresasHistorico** (id=154) | xml | Balanço trimestral completo (1.2MB, 80+ campos!) |
| 2 | **FIIAnbimaBovespa** (id=150) | xml | FII: div yield, últ dividendo, vol médio |
| 3 | **CarteiraTopFundos** (id=187) | binary | Quais fundos investem no ativo |
| 4 | **EmpresaAcoesUnits** (id=183) | binary | Ações ON/PN, free float |
| 5 | **Volatilidades** (id=208) | xml | Volatilidade histórica por janela |
| 6 | **Fundos** (id=76) | xml | Histórico de cotas de fundos |
| 7 | **TitulosPublicos** (id=77) | xml | Histórico títulos do Tesouro |
| 8 | **CalculoTaxaPre** (id=136) | xml | Curva de taxa pré-fixada |
| 9 | **CalculoPoupanca** (id=114) | xml | Rendimento poupança diário |
| 10 | **HistoricoDiarioSimbolos** (id=75) | xml | Multi-ticker daily (alternativa ao bdh) |

---

## Observações Técnicas

### Protocolo Binary SOH (aetp/output e aefundamental)

Formato de resposta:
```
Record[0]: [version, ?, ?, ?]          — header
Record[1]: [metadata_count, k1, v1..] — "0" = no metadata, N = N key-value pairs
Record[2]: [field_count, tag1, tag2..] — field definitions
Record[3+]: [val1, val2, ...]          — data rows (\x02 = repeat prev value)
Last:       [\x03]                     — ETX terminator
```

Erros são detectados pela presença do tag `10037` nos dados brutos (contém mensagem de erro).

O decoder já existe em `src/py_bcast/fundamental.py` (`_parse_binary_response()`).

### Símbolos para MacroEconomicos

Usa params `305`=ticker + `DataInicio`/`DataFim`=YYYYMMDD (NÃO usa tag 961).

| Símbolo | Dado |
|---------|------|
| `USDBRL`, `EURUSD`, etc. | Câmbio (funcionam diretamente) |
| `IBOV`, `SPX`, `DAX`, `NASDAQ` | Índices (funcionam diretamente) |
| `GOLD`, `WTI`, `BRENT` | Commodities (funcionam diretamente) |
| `DI1F27`, `DI1F28` | DI Futuro (funcionam diretamente) |
| `AESLIC` | Taxa SELIC (reunião COPOM) |
| `AECTIP` | CDI/DI CETIP diário |
| `AEIPCA` | IPCA mensal |
| `AEIGPM` | IGP-M mensal |
| `AEINPC` | INPC mensal |
| `AEB052` | Índice B3 DI pré 252du |
| `AEB200` | Índice B3 S&P 500 |
| `AEFS10` | Índice B3 DI pré 10 anos |

### Backend GraphQL (offline)

O bloco `aetp/output/fundamental/indicador/*` (P/L, ROE, Dívida Líquida, etc.) depende de um backend GraphQL hospedado na AWS (`ab684f71...elb.us-east-1.amazonaws.com`) que está **offline**.

Endpoints afetados: 166, 167, 168, 169, 170, 182, 214.

**NÃO afetados** (funcionam normalmente):
- IndicadorMetadado (165) — 80 indicadores, metadata ✅
- IndicadorHistoricoDiario (171) — Market Cap, Beta diário ✅

Estes potencialmente voltarão a funcionar se/quando o backend for restaurado.

### AEInstrumentos vs aetp/output

O `AEInstrumentos` (protocolo antigo) está 100% bloqueado (`PROPRIETARY`), mas dados equivalentes existem via `aetp/output`:
- Setores → `fundamental/setor` (id=172) ✅ implementado: `bsectors()`
- Empresas → `fundamental/empresa` (id=180) ✅ implementado: `bcompany()`
- Índices → `ativos/indice` (id=213) ✅ implementado: `bindices()`
- Ações empresa → `fundamental/empresa/acao` (id=183)

### Tags HTTP Mais Importantes

| Tag | Significado | Formato |
|-----|-------------|---------|
| `305` | Ticker/símbolo | String (PETR4, AESLIC) |
| `961` | Data início série | YYYYMMDD |
| `1789` | Data fim série | YYYYMMDD |
| `10057` | Data início range | YYYYMMDD |
| `10058` | Data fim range | YYYYMMDD |
| `10068` | Ticker (contexto fundamental) | String |
| `10071` | Datetime início | YYYYMMDDHHMMSS |
| `10072` | Datetime fim | YYYYMMDDHHMMSS |
| `10074` | Datetime início (intraday) | YYYYMMDDHHMM |
| `10077` | Data específica | YYYYMMDD |
| `10087` | ID da corretora | Int |
| `10113` | Tickers (multi, sep `;`) | String |
| `12078` | Número de dias | Int |
| `13004` | Código CVM empresa | Int (9512=Petrobras) |
| `13539` | Notional/valor | Float |
| `13798` | ID do setor | Int |

# Catalogo de Endpoints — Terminal Antigo (bcsys32.exe)

Catalogo completo de todos os endpoints HTTP descobertos no ContentProxy (`cp.ae.com.br:44780`), incluindo status por endpoint, dados retornados e funcao correspondente na lib quando implementada.

**Legenda:**
- Implementado — funcao publica na lib, testada
- Confirmado — endpoint retorna dados reais, sem adapter na lib ainda
- Bloqueado — erro definitivo, ver motivo
- Fora de escopo — contribuicao, admin, UI-only

**Categorias de falha:**
- `PROPRIETARY` — Protocolo binario proprietario (error 88007). Inacessivel sem reverse-engineering do protocolo Java
- `DEAD_BACKEND` — Backend AWS/GraphQL offline ou retornando 500
- `AETP_ONLY` — Requer pre-registro via protocolo AETP TCP:8100 (Query=NONE)
- `PARAMS` — Parametros corretos desconhecidos; possivelmente funcional
- `BUG` — Bug no servidor (SQL, etc.)

**Fontes:** CHM do Add-In Excel, `services_parsed.json` (227 endpoints), varredura automatica (`scripts/probe_all_endpoints.py`) executada em 2025-05-20.

---

## 1. Funcoes do Add-In Excel (CHM)

### 1.1 `=BC(ativo; campo)` — Cotacao Tempo Real

| Funcionalidade | Status | py-bcast | Notas |
|---|---|---|---|
| Cotacao em tempo real (streaming) | Implementado | `bdp()` | Via DDE, Service=BC, Topic=COT |
| Multi-ativo simultaneo | Implementado | `bdp()` | Aceita lista de tickers |
| Campos: ULT, VAR, MAX, MIN, ABE, FEC, OCP, OVD | Implementado | `bdp()` | Todos os campos DDE |
| Campos: NEG, QUL, MED, QTT, VTT, VOC, VOV | Implementado | `bdp()` | |
| Campos: CNG, CAB, AJU (mercadorias/futuros) | Implementado | `bdp()` | |
| Campos: HOR, HOC, HOV (timestamps) | Implementado | `bdp()` | |
| Campos: TND, DIF, DIFSEM, DIFMES, etc. | Implementado | `bdp()` | Variacoes calculadas |
| Campos: NOM (nome do ativo) | Implementado | `bdp()` | |
| Topic ATIVO (dados cadastrais via DDE) | Implementado | `bdp()` | Topic diferente de COT |

### 1.2 `=BCH(ativo; campo; data)` — Historico

| Funcionalidade | Status | py-bcast | Notas |
|---|---|---|---|
| Historico de fechamento por data | Implementado | `bdh()` | HTTP HistoricoFechamentos |
| Range de datas (data_ini, data_fim) | Implementado | `bdh()` | Loop automatico por dia |
| PERIODO=D (diario) | Implementado | `bdh()` | Padrao |
| PERIODO=I (intradia 1-240 min) | Implementado | `bdi()` | HTTP HistoricoIntraday, 2-min bars |
| PERIODO=S (semanal) / PERIODO=M (mensal) | Confirmado | — | Endpoint suporta, nao exposto na lib |
| NOMINAL=S (serie nominal, sem ajuste) | Confirmado | — | Endpoint `DiarioEx` bloqueado (Query=NONE) |
| Campos: ULT, FEC, MAX, MIN, ABE, MED, DRF, NEG, QTT, VTT | Implementado | `bdh()`/`bdi()` | |
| Campos: CAB, AJU, CNG (futuros) | Implementado | `bdh()` | Retornados quando aplicavel |
| ASC/DESC/TITULO/LINHAS (ordenacao, headers, limite) | Fora de escopo | — | Client-side (trivial via Python) |

### 1.3 `=BCS(ativo; consulta)` — Consultas Estruturadas

| Funcionalidade | Status | py-bcast | Notas |
|---|---|---|---|
| EVENTOS (eventos corporativos) | Bloqueado | — | `EventoServlet` retorna error 88007 (binary-only) |
| CARTEIRA (composicao de indices) | Bloqueado | — | `IndicesServlet` retorna error 88007 |

> Ambas funcionalidades do BCS dependem do `AEInstrumentos` que usa protocolo binario proprietario inacessivel. Dados equivalentes existem via `aetp/output/` (secao 5).

### 1.4 `=BCMONITOR` — Contribuicao (Broadcast Link)

| Funcionalidade | Status | py-bcast | Notas |
|---|---|---|---|
| BCMONITOR, BCSTATUS, BCSTART, BCSTOP | Fora de escopo | — | Write-only, fora de escopo |

---

## 2. BaseHistoricaNumerica — Historico de Precos (XML)

Todos retornam XML com `<RESPONSE><STATUS>success</STATUS>...<TICKS>`.

### 2.1 Confirmados Funcionais

| ID | Endpoint | Status | Dados | Params Chave |
|---|----------|--------|-------|--------------|
| 10 | HistoricoDiario | Bloqueado | — | `AETP_ONLY` — Requer query pre-registrada |
| 11 | **HistoricoIntraday** | Implementado | 2-min OHLCV bars | `305`=ticker, `10074`=YYYYMMDDHHMM |
| 12 | **HistoricoTick** | Implementado | Tick-by-tick (intl only) | `305`=ticker, `10071/10072`=YYYYMMDDHHMMSS |
| 13 | **HistoricoData** | Implementado | OHLCV+VWAP para 1 data | `305`=ticker, `10077`=YYYYMMDD |
| 32 | **HistoricoFechamentos** | Implementado | Closing prices | `10113`=tickers, `DatasTolerancia`=YYYYMMDD |
| 75 | **HistoricoDiarioSimbolos** | Confirmado | Multi-ticker daily (17KB) | `10113`=tickers sep `;`, `961`=start_date |
| 84 | **VolumesMedios** | Implementado | Avg vol 1/2/3/6/12 meses | `10113`=ticker |
| 95 | **MacroEconomicos** | Implementado | Series macro (FX, indices, AETAXAS) | `305`=ticker, `DataInicio`/`DataFim`=YYYYMMDD |
| 125 | **UltimosIntraday** | Confirmado | Ultimo snapshot intraday | `10113`=ticker |
| 126 | **Inflacao** | Implementado | 17 indices de inflacao, 12 meses | Sem params extras |
| 137 | **DiCetipAcumulado** | Implementado | CDI/DI acumulado diario (desde 1986) | `DataInicio`/`DataFim`=YYYYMMDD |
| 140 | **RetornoDiario** | Implementado | Retorno diario ajustado | `305`=ticker, `DataInicio`/`DataFim`=YYYYMMDD |
| 150 | **FIIAnbimaBovespa** | Confirmado | FII: DY, last div, vol medio, etc. | `10113`=ticker (ex: HGLG11) |
| 154 | **EmpresasHistorico** | Confirmado | Balanco completo trimestral (1.2MB!) | `305`=ticker, `961`=start_date |
| 208 | **Volatilidades** | Confirmado | Volatilidade historica | `10113`=ticker, `12078`=dias |

### 2.2 Renda Fixa / Calculos

| ID | Endpoint | Status | Dados | Params Chave |
|---|----------|--------|-------|--------------|
| 76 | **Fundos** | Confirmado | Historico de cotas (OHLC, 24KB) | `305`=ticker, `961`=start |
| 77 | **TitulosPublicos** | Confirmado | Titulos do Tesouro | `305`=LTN/NTN, `961`=start |
| 82 | **FundosRentabilidade** | Confirmado | Rentabilidade do fundo | `305`=ticker |
| 114 | **CalculoPoupanca** | Confirmado | Rendimento poupanca diario (5.7KB) | `961`=start |
| 135 | **CalculoPreco** | Confirmado | Preco unitario renda fixa | `305`=titulo, `961`=start |
| 136 | **CalculoTaxaPre** | Confirmado | Curva de taxa pre acumulada (6.5KB) | `13539`=notional, `961`=start |
| 141 | **TitulosPublicosUltimos** | Confirmado | Ultimos precos de titulos | `10113`=ticker |
| 207 | **VolumesMediosSemMesAno** | Confirmado | Volumes medios historicos | `10113`=ticker, `12078`=dias |

### 2.3 Bloqueados / Com Erro

| ID | Endpoint | Erro | Categoria |
|---|----------|------|-----------|
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

## 3. AEInstrumentos — Dados de Referencia

**TODOS bloqueados** (`PROPRIETARY`): retornam `ErrorCode=88007, Tipo de resposta indisponivel ou invalido`.
Protocolo binario proprietario Java que nao aceita `TipoResposta=xml`.
Estes endpoints so sao acessiveis pelo terminal desktop (Java/Swing client).
**Dados equivalentes disponiveis via `aetp/output/`** (secao 5).

| ID | Endpoint | Status | Dados que teria |
|---|----------|--------|-----------------|
| 14 | EventoServlet | Bloqueado | Eventos corporativos |
| 17 | InstrumentoServlet | Bloqueado | Lista de instrumentos |
| 18 | BolsaServlet | Bloqueado | Lista de bolsas |
| 19 | MercadoServlet | Bloqueado | Lista de mercados |
| 20 | SimbologiaServlet | Bloqueado | Mapa de simbolos |
| 21 | SetorServlet | Bloqueado | Setores |
| 22 | ClasseServlet | Bloqueado | Classes de ativos (404) |
| 23 | SubClasseServlet | Bloqueado | Subclasses (404) |
| 24 | CorretoraServlet | Bloqueado | Lista corretoras |
| 25 | IndicesServlet | Bloqueado | Composicao de indices |
| 33-39 | Feriados, Horarios, etc. | Bloqueado | Dados de referencia |
| 50 | EmpresaAcionistasServlet | Bloqueado | Estrutura acionaria |
| 68-70 | Empresas, TipoIntervalo | Bloqueado | Cadastro de empresas |
| 85-89 | BolsaDados, Indicadores | Bloqueado | Dados de bolsa/indicadores |
| 96-101 | Periodicidade, Moeda, Contrato | Bloqueado | Referencia |
| 117-119 | Metodologia, Periodicidade, Benchmark | Bloqueado | Referencia |
| 146-149 | Benchmarks, AliquotasIR, TitulosPublicosDados | Bloqueado | Referencia |
| 155-157 | EmpresaAcoes, EmpresaSetores, MarketCap | Bloqueado | Referencia |

---

## 4. aefundamental — Dados Fundamentalistas (Binary SOH)

Protocolo: SOH (0x01) separa records, NULL (0x00) separa fields. Mesmo decoder do `bconsensus()`.

### 4.1 Confirmados Funcionais

| ID | Endpoint | Status | Dados | Size |
|---|----------|--------|-------|------|
| 52 | **Consenso** | Implementado | Buy/Hold/Sell, target prices | ~200B |
| 58 | **Arquivos** | Confirmado | Lista de documentos/filings | 3.2KB |
| 60 | **Consenso Ativos** | Confirmado | Lista ativos com consenso | 102B |
| 45 | **Orgaos Administracao** | Confirmado | Orgaos da diretoria | 102B |
| 46 | **Administradores** | Confirmado | Membros da diretoria | 102B |
| 48 | **Exercicios Sociais** | Confirmado | Exercicios fiscais | 102B |
| 69 | **EmpresaDados** | Confirmado | Dados da empresa (binary SOH) | 1KB |

### 4.2 Bloqueados

| ID | Endpoint | Erro | Motivo |
|---|----------|------|--------|
| 51 | Demonstracao detalhado | Backend offline | GraphQL (AWS ELB) inacessivel |
| 53-54 | Marketcap Diario/Historico | No data | Retorna instrumento errado |
| 55-57 | Indicadores (Resumido/Detalhado/Ativo) | 404 | Endpoints nao existem |

---

## 5. aetp/output — API Nova (Binary SOH)

**Maior descoberta da varredura**: ~40 endpoints funcionais com dados ricos.
Todos usam o mesmo protocolo binary SOH do `bconsensus()`.

### 5.1 Fundamental — Empresa

| ID | Endpoint | Status | Dados | Size |
|---|----------|--------|-------|------|
| 164 | **DemonstrativoUltimo** | Confirmado | Datas do ultimo balanco/ITR | 394B |
| 172 | **SetorSubsetorSegmento** | Implementado | Classificacao setorial B3 (42 setores) | 1.4KB |
| 173 | **EmpresasPorSetores** | Confirmado | Todas empresas de um setor | 14.5KB |
| 179 | **EmpresaMetadado** | Implementado | Metadados de TODAS as empresas | 101KB |
| 180 | **EmpresaDados** | Implementado | Empresa: CNPJ, nome, setor, IPO date | 1.2KB |
| 183 | **EmpresaAcoesUnits** | Confirmado | Acoes ON/PN, free float | 348B |

### 5.2 Fundamental — Dividendos / Eventos

| ID | Endpoint | Status | Dados | Size |
|---|----------|--------|-------|------|
| 186 | **EventosJcpDividendos** | Implementado | Historico completo JCP+Div (desde 1995!) | 274B+ |
| 192 | **EventosDividendYield** | Implementado | DY historico por ex-date | 2.6KB |
| 193 | **AcionistaDatas** | Confirmado | Datas de composicao acionaria | 1.6KB |
| 211 | **CalendarioEventosCorporativos** | Implementado | Agenda de eventos (AGO, ITR, etc.) | **72KB** |

### 5.3 Fundamental — Carteira Recomendada

| ID | Endpoint | Status | Dados | Size |
|---|----------|--------|-------|------|
| 194 | **CarteiraRecomendadaUltima** | Implementado | Ultima carteira de uma corretora | 9.3KB |
| 195 | **CarteiraRecomendadaTicker** | Confirmado | Em quais carteiras o ticker esta | 7.9KB |
| 197 | **CarteiraRecomendadaMudancas** | Confirmado | Mudancas na carteira | 144B |
| 198 | **CarteiraRecomendadaCorretoras** | Implementado | Lista de corretoras com carteiras | 318B |

### 5.4 Fundamental — Indicadores

| ID | Endpoint | Status | Erro |
|---|----------|--------|------|
| 165 | **IndicadorMetadado** | Implementado | 84 indicadores metadata (24.6KB) |
| 171 | **IndicadorHistoricoDiario** | Implementado | Market Cap, Beta diario — funciona! |
| 166 | IndicadorPeriodo | Bloqueado | `DEAD_BACKEND` — GraphQL: "Bad Request" |
| 167 | IndicadorHistorico | Bloqueado | `DEAD_BACKEND` — GraphQL: "Bad Request" |
| 168/170 | IndicadorTicker/TickerFixo | Bloqueado | `PARAMS` — "Nao foram encontrados registros" |
| 182 | DemonstrativoFiltros | Bloqueado | `DEAD_BACKEND` — GraphQL: "Bad Request" |
| 214 | ComposicaoIndices | Bloqueado | `DEAD_BACKEND` — GraphQL: "Bad Request" |

> O backend GraphQL da AWS (`ab684f71...elb.us-east-1.amazonaws.com`) esta offline.
> Todos os endpoints de indicadores financeiros (P/L, ROE, DRE) estao indisponiveis.

### 5.5 Fundamental — Metadados / Classificacao

| ID | Endpoint | Status | Dados | Size |
|---|----------|--------|-------|------|
| 175 | **ArquivosCategorias** | Confirmado | Categorias de filings | 4KB |
| 176 | **ArquivosEspecies** | Confirmado | Especies de documentos | 2.2KB |
| 177 | **ArquivosTipos** | Confirmado | Tipos de documentos | 4.4KB |
| 185 | **IndicadorCategorias** | Confirmado | Categorias de indicadores | 252B |
| 205 | **ArquivosDemonstrativos** | Confirmado | Lista de demonstrativos | 139B |
| 212 | **TickersEmpresas** | Confirmado | Campos externos de um ticker | 109B |

### 5.6 Fundamental — Fundos

| ID | Endpoint | Status | Dados | Size |
|---|----------|--------|-------|------|
| 187 | **CarteiraTopFundos** | Confirmado | Top fundos que investem no ativo | 8.5KB |
| 188 | EmpresaDistribuicao | Confirmado | Distribuicao investimentos | 91B (vazio) |

### 5.7 Ativos / Indices

| ID | Endpoint | Status | Dados | Size |
|---|----------|--------|-------|------|
| 201 | **AtivoSimbolo** | Implementado | Lookup de ativo | 139B |
| 202 | **AtivoCotacao** | Implementado | Cotacao de ativo | 136B |
| 203 | **AtivoQuantidade** | Implementado | Qtd acoes do ativo | 136B |
| 213 | **Indices** | Implementado | Lista de 38 indices B3 (IBOV, IFIX, SMLL...) | 244B |

### 5.8 Fundos (aetp)

| ID | Endpoint | Status | Dados | Size |
|---|----------|--------|-------|------|
| 158 | **FundosListaTipoAtivo** | Confirmado | Tipos de ativo para fundos | 2KB |
| 159 | **FundosListaTipoAplicacao** | Confirmado | Tipos de aplicacao | 1.6KB |
| 222 | FundosBuscaRapida | Confirmado | Busca de fundos | 115B |

### 5.9 Energia

| ID | Endpoint | Status | Dados | Size |
|---|----------|--------|-------|------|
| 174 | EnergiaHorarioIntraday | Confirmado | Mercado de energia | 118B (sem dados uteis) |

---

## 6. AEContent — Noticias

### 6.1 Protocolo Binario (BLOQUEADO)

Endpoints AETP originais para noticias — todos bloqueados por subscricao (error 88007).

| ID | Endpoint | Status | Notas |
|---|----------|--------|-------|
| 27 | Noticias (NewsServlet) | Bloqueado | Error 88007 |
| 28 | Conteudo (ContentServlet) | Bloqueado | Error 88007 |
| 29 | Cadernos (CadernoServlet) | Bloqueado | Error 88007 |
| 30 | Arquivo (FileServlet) | Bloqueado | Error 88007 |
| 108 | CountNoticias | Bloqueado | Binary SOH, 81B (contém apenas error code) |
| 110 | topNewsLista | Bloqueado | Binary SOH, 81B (contém apenas error code) |
| 152 | MaisLidasLista (aetp) | Bloqueado | Binary SOH, 63B (apenas header) |
| 153 | Noticias Relacionadas | Bloqueado | Error 88007 |

### 6.2 CentralMultimidia (FUNCIONAL — sem autenticacao!)

API ASP.NET descoberta em `/CentralMultimidia/`. Retorna **todas** as noticias do Broadcast
por ID sequencial (atualmente ~56M), incluindo texto, Dow Jones, press releases, podcasts.
**Nao requer sessao, token ou assinatura.**

| Endpoint | Metodo | Status | Dados |
|----------|--------|--------|-------|
| `/CentralMultimidia/Handlers/MultimediaCenterHandler.ashx` | GET | Implementado | Listagem por categoria (XML) |
| `/CentralMultimidia/Default.aspx/GetVideoContent` | POST | Implementado | Conteudo completo por ID (JSON) |
| `/CentralMultimidia/` | GET | Implementado | Pagina HTML com categorias |

**py-bcast**: `bnews(id)`, `bnews_recent(n)`, `bnews_multimedia(category)`

**Categorias de multimidia disponiveis:**

| ID | Categoria | Tipo |
|----|-----------|------|
| 567 | Comentario Financeiro | Podcast/Video |
| 566 | Comentario Agricola | Podcast/Video |
| 748 | Podcast | Podcast |
| 848 | Comentario Politico | Podcast/Video |
| 849 | Cabeca de Gestor | Podcast/Video |
| 857 | E-Investidor-Midia | Podcast/Video |
| 1133 | Capital Insights | Podcast/Video |
| 1160 | Credito Privado 360 | Podcast/Video |

**Nota**: O endpoint `GetVideoContent` aceita ANY ID numerico — nao so multimidia.
IDs sao sequenciais e cobrem AE-News, Dow Jones Newswires, Trading News, Press Releases, etc.

---

## 7. contentProxyOutput — Fundos CVM

**TODOS retornam HTTP 500** (Server Error). Backend Java/Tomcat com stack trace.

| IDs | Endpoints | Status |
|---|----------|--------|
| 61-67, 73-74, 100, 115-116, 120-123, 127-130, 132, 134 | Todos os Fundos CVM | Bloqueado (500) |
| 133 | CDIRentabilidade | Bloqueado (500) |

---

## 8. MarkitOutput2 — CDS / Credito

| ID | Endpoint | Status | Notas |
|---|----------|--------|-------|
| 91 | **MarkitListaTipoCDS** | Confirmado | Retorna tipos de CDS (268B XML) |
| 90 | MarkitListaDatas | Bloqueado | api_error |
| 92 | MarkitIndices | Bloqueado | api_error |
| 93 | MarkitListaCDS | Bloqueado | api_error |
| 94 | MarkitCDS | Bloqueado | api_error |

---

## 9. IntegracaoTabelas — Commodities / Tabelas

| ID | Endpoint | Status | Dados | Size |
|---|----------|--------|-------|------|
| 105 | **ListaCategorias** | Confirmado | Categorias (Area, Volume, Produtividade) | 876B |
| 107 | **CategoriaPreco** | Confirmado | Moedas/simbolos de preco | 1KB |
| 111 | **ListaFormulas** | Confirmado | Formulas disponiveis | 358B |
| 102-104, 106 | Filtros, Conteudo, Proporcao | Confirmado | Requer IDs especificos | — |

---

## 10. Acesso Local (sem HTTP)

| Funcionalidade | Status | py-bcast | Notas |
|---|---|---|---|
| Banco de instrumentos (aetp_17.dat) | Implementado | `InstrumentDB`, `bsearch()` | 623K instrumentos, XOR(0xAE) |
| DDE streaming (subscribe + callback) | Implementado | `bdp()` | Requer bcsys32.exe |
| AETP TCP:8100 | Bloqueado | — | Protocolo binario interno, nao cracked |
| SPC .NET (AESpcNET.dll) | Bloqueado | — | Dead end |

---

## Status de Exploracao de Protocolos

| Protocolo | Status | Notas |
|----------|--------|-------|
| DDE (Service=BC) | Funcional | Real-time + snapshot |
| HTTP BaseHistoricaNumerica | Funcional | ~18 endpoints, 9 implementados |
| HTTP aefundamental | Parcial | Consensus + binary parser |
| HTTP aetp/output | **~40 funcionais, 14 implementados** | Binary SOH, fonte mais rica |
| HTTP IntegracaoTabelas | Parcial | 4 endpoints de commodities/formulas |
| HTTP AEInstrumentos | 100% bloqueado | `PROPRIETARY` — error 88007 |
| HTTP AEContent | 100% bloqueado | `PROPRIETARY` — error 88007 |
| HTTP contentProxyOutput | 100% quebrado | `DEAD_BACKEND` — HTTP 500 |
| HTTP MarkitOutput2 | Majoritariamente quebrado | Apenas ListaTipoCDS funciona |
| AETP TCP:8100 | Nao cracked | Protocolo binario, framing customizado |
| SPC .NET (AESpcNET.dll) | Dead end | Servidor nao roteia dados para clientes externos |
| RTD COM | Indisponivel | Broadcast nao tem servidor RTD (usa DDE) |

---

## Resumo Quantitativo

| Status | Count | Descricao |
|--------|-------|-----------|
| Implementado na lib | **26 funcoes** | bdp, bdh, bdh_ohlcv, bdi, bdt, bmacro, bdi_cdi, breturn, bvolume, binflation, bconsensus, bcompany, bindices, bsectors, bquote, btickers, bshares, bindicators, bindicator_meta, bcalendar, bdividends, bdy, bportfolios, bportfolio, bsearch, InstrumentDB |
| Funcional, nao implementado | **~35** | Endpoints que retornam dados reais (FIIs, Fundos, Financials, TitulosPublicos, etc.) |
| Bloqueado/Quebrado | ~70 | Ver categorias abaixo |
| Fora de escopo | ~8 | Contribuicao, admin, banners |

### Categorias de Falha

| Categoria | Count | Endpoints | Possibilidade de Resolver |
|-----------|-------|-----------|---------------------------|
| `PROPRIETARY` | ~58 | AEInstrumentos, AEContent | Requer reverse-engineering do protocolo Java binario |
| `DEAD_BACKEND` | ~37 | contentProxyOutput (500s), GraphQL (AWS offline) | Pode voltar se backend for restaurado |
| `AETP_ONLY` | ~3 | HistoricoDiario, DiarioEx, UltimosPregoes | Requer suporte ao protocolo AETP TCP:8100 |
| `PARAMS` | ~8 | Varios BaseHistoricaNumerica | Possivelmente funcional com params corretos |
| `BUG` | ~1 | Players (SQL error) | Bug no servidor |

---

## Observacoes Tecnicas

### Simbolos para MacroEconomicos

Usa params `305`=ticker + `DataInicio`/`DataFim`=YYYYMMDD (NAO usa tag 961).

| Simbolo | Dado |
|---------|------|
| `USDBRL`, `EURUSD`, etc. | Cambio (funcionam diretamente) |
| `IBOV`, `SPX`, `DAX`, `NASDAQ` | Indices (funcionam diretamente) |
| `GOLD`, `WTI`, `BRENT` | Commodities (funcionam diretamente) |
| `DI1F27`, `DI1F28` | DI Futuro (funcionam diretamente) |
| `AESLIC` | Taxa SELIC (reuniao COPOM) |
| `AECTIP` | CDI/DI CETIP diario |
| `AEIPCA` | IPCA mensal |
| `AEIGPM` | IGP-M mensal |
| `AEINPC` | INPC mensal |
| `AEB052` | Indice B3 DI pre 252du |
| `AEB200` | Indice B3 S&P 500 |
| `AEFS10` | Indice B3 DI pre 10 anos |

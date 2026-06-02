# Catalogo de Endpoints — Terminal Antigo (bcsys32.exe)

Catalogo completo de todos os endpoints HTTP descobertos no ContentProxy (`cp.ae.com.br:44780`), incluindo status por endpoint, dados retornados e funcao correspondente na lib quando implementada.

**Legenda:**
- Implementado — funcao publica na lib, testada
- Confirmado — endpoint retorna dados reais, sem adapter na lib ainda
- Vazio/Casca — endpoint responde HTTP 200 mas sem dado utilizavel: ou `STATUS=success` com celulas/linhas vazias (casca), ou erro de "sem registros" (`in_88000`/`mo_88000`). Vivo, porem sem dado
- Bloqueado — erro definitivo, ver motivo
- Fora de escopo — contribuicao, admin, UI-only

**Categorias de falha:**
- `PROPRIETARY` — Protocolo binario proprietario (error 88007). Inacessivel sem reverse-engineering do protocolo Java
- `DEAD_BACKEND` — Backend AWS/GraphQL offline ou retornando 500
- `AETP_ONLY` — Requer pre-registro via protocolo AETP TCP:8100 (Query=NONE)
- `PARAMS` — Parametros corretos desconhecidos; possivelmente funcional
- `BUG` — Bug no servidor (SQL, etc.)

**Fontes:** CHM do Add-In Excel, `services_parsed.json` (227 endpoints), varredura automatica (`scripts/probe_all_endpoints.py`) executada em 2025-05-20.

> **Re-verificacao empirica de 2026-06-02.** Uma re-verificacao endpoint-a-endpoint contra o
> terminal ao vivo (`cp.ae.com.br:44780`, token valido confirmado por controle positivo)
> corrigiu erros materiais da varredura de 2025-05-20. Os status, params e exemplos abaixo
> ja refletem esses vereditos. A varredura original cometeu **4 erros sistematicos** — uteis
> de ter em mente em futuras revisoes:
>
> 1. **Params errados** (fuso BRT vs UTC; `BR` vs data; `IPCA` vs `AEIPCA`; param obrigatorio
>    ausente) -> falso-NEGATIVO (endpoint vivo lido como bloqueado/api_error).
> 2. **Contar bytes/linhas sem validar CELULAS** — um header de erro de 1 linha OU uma casca
>    de schema-vazio foram lidos como "Confirmado" -> falso-POSITIVO.
> 3. **Simbolo "pelado" resolve para instrumento errado** (`LTN` -> `LTN.NYSE`) -> `STATUS=success`
>    com `<TICKS>` vazio, enganoso. Afeta tambem usuarios da lib hoje.
> 4. **Param documentado quebra** (ex.: `114` com `961` -> HTTP 500). Afeta usuarios da lib.
>
> Bug metodologico relacionado: detectar bloqueio por *substring* `88000` casa dentro de CNPJ
> no payload, gerando falso "bloqueado". A re-verificacao usou match de campo-exato e priorizou
> contagem de linhas reais (`rows>0`).

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
| 150 | **FIIAnbimaBovespa** | Confirmado | FII: DY, last div, vol medio, etc. (HGLG11: DVYLD=9.24, ULDV=1.1, QTCT=33.7M) | `10113`=ticker (ex: HGLG11) |
| 154 | **EmpresasHistorico** | Vazio/Casca | **CASCA VAZIA** — schema de 222 campos (DRE/BP/FC) mas 0 celula financeira | `305`=ticker, `961`=start_date |
| 208 | **Volatilidades** | Vazio/Casca | `STATUS=success` porem `<TICKS>` sempre vazio (dataset vazio no servidor) | `10113`=ticker, `12078`=dias |

> **154 EmpresasHistorico — casca vazia (era falso-positivo).** A varredura de 2025 viu ~1.2MB
> e classificou como "balanco completo trimestral". Na re-verificacao (2026-06-02), o endpoint
> responde `HTTP 200`/`STATUS=success` com ate 7776 linhas `<TICK>` (1 por pregao, schema de 222
> colunas DRE/BP/FC), mas a varredura COMPLETA das 1597 linhas da janela `961=20200101` (~6 anos)
> achou **0 celula financeira preenchida**: so `DAT` populado, `QUARTER`/`FISCAL_QUARTER`='nanT',
> `YEAR`='', todos os `ASSET_RETURN`/`BOOK_BALANCE`/`CAPITAL`/`EBITDA`/... vazios. Os "1.2MB" eram
> schema largo x linhas vazias, nao dados. Param correto: `305`=ticker + `961`=start (`10113` erra
> "Instrumento nao encontrado"); o `success` NAO e param-gap, e dataset esvaziado no servidor. **Nao
> e a fonte de financials que substituiria o GraphQL morto** (ver secao 5.4 e `limitations.md`).

> **207/208 — dataset vazio (eram falso-positivos).** `VolumesMediosSemMesAno` (207) e
> `Volatilidades` (208) usam `10113`=ticker + `12078`=janela em dias. Ambos respondem
> `STATUS=success` com o simbolo resolvido (`PETR4.BVMF` em `<SYMBOLS>`), mas `<TICKS>` vem
> SEMPRE vazio — testados todos os eixos (`12078` in {1,10,20,21,40,252}, so `10113`, `+961`,
> `+DataInicio/Fim`, VALE3). Datas recentes SAO o eixo correto aqui (vol/volume derivam do preco
> corrente, cujo endpoint 125 esta vivo), logo a ausencia **nao** e efeito de retencao; e dataset
> vazio no servidor. `305` em vez de `10113` retorna erro deterministico de tag (nao instabilidade).

### 2.2 Renda Fixa / Calculos

| ID | Endpoint | Status | Dados | Params Chave |
|---|----------|--------|-------|--------------|
| 76 | **Fundos** | Confirmado | Historico de cotas (OHLC, 24KB) | `305`=ticker, `961`=start |
| 77 | **TitulosPublicos** | Confirmado | OHLC de titulo do Tesouro (popula via `.TRDM`) | `305`=`LTNF28.TRDM` (NAO bare `LTN`), `961`=start |
| 82 | **FundosRentabilidade** | Confirmado | Rentabilidade do fundo | `305`=ticker |
| 114 | **CalculoPoupanca** | Confirmado | Rendimento poupanca diario (5.7KB) | `DataInicio`/`DataFim` (NAO `961` — `961` -> HTTP 500) |
| 135 | **CalculoPreco** | Confirmado | Preco unitario renda fixa (popula via `.ANBIMA`) | `305`=`LTN260701.ANBIMA` (NAO bare `LTN`), `961`=start |
| 136 | **CalculoTaxaPre** | Confirmado | Curva de taxa pre acumulada (6.5KB) | `13539`=notional, `961`=start |
| 141 | **TitulosPublicosUltimos** | Confirmado | Ultimos precos de titulos (popula via `.ANBIMA`) | `10113` ou `305`=`LTN260701.ANBIMA` (NAO bare `LTN`) |
| 207 | **VolumesMediosSemMesAno** | Vazio/Casca | `STATUS=success` porem `<TICKS>` sempre vazio (dataset vazio no servidor) | `10113`=ticker, `12078`=dias |

> **Armadilha de simbolo (77/135/141).** Tesouro BR vive em DUAS bolsas no `InstrumentDB`; o
> simbolo "pelado" NAO basta — `305=LTN` resolve para `LTN.NYSE` (acao US), retornando
> `STATUS=success` com `<TICKS>` vazio (mesma classe de erro do `HistoricoTick`). Os sufixos
> populam diferente por endpoint:
> - **`.ANBIMA`** = precos de referencia diarios (ex.: `LTN260701.ANBIMA`, `NTNB270515.ANBIMA`).
>   Popula **135** (PU, 22 ticks) e **141** (1 tick). Para **77**, da `success` + 0 ticks.
> - **`.TRDM`** = Trademate/balcao (ex.: `LTNF28.TRDM`, `NTNBK27.TRDM`). Popula **77** (OHLC +
>   `WORKING_DAYS` + `EXPIRATION_DATE`). Tambem popula 135.
>
> **114 CalculoPoupanca — param documentado quebrava.** O catalogo de 2025 listava `961=start`,
> mas com `961` o endpoint retorna **HTTP 500** (JBoss error report). Funciona apenas com
> `DataInicio`/`DataFim` (22 ticks `DAT`/`ACUM`; `sym=AENPOP.AETAXAS`).

### 2.3 Bloqueados / Com Erro

| ID | Endpoint | Erro | Categoria |
|---|----------|------|-----------|
| 26 | HistoricoUltimosPregoes | `Query=NONE` | `AETP_ONLY` — confirmado: validacao satisfeita (`QuantidadePregoes`+`Precisao`) e ainda assim `Query=NONE` |
| 40 | Players | SQL bug | `BUG` — "field BVMF not found in tick descriptor" |
| 81 | FundosIndicadores | `api_error` | `PARAMS` (nao re-testado nesta rodada) |
| 83 | FechamentoFormula | api_error | `PARAMS` — parede server-side: `Instrumentos`/`12004` aceitos, mas `DataInicio` e rejeitado como "nao encontrado" MESMO presente |
| 138 | TabelaRetorno | api_error | `PARAMS` — exige "Tipo de calculo"; nome do param nao descoberto (`13487` e variantes nao satisfazem) |
| 139 | TabelaRentabilidade | api_error | `PARAMS` — mesma parede do 138 (`13487` != tipo de calculo) |
| 142 | DiarioEx | `Query=NONE` | `AETP_ONLY` |
| 144 | CalculoCarteira | api_error | `PARAMS` — `13571`+`961` aceitos; falta "Tipo de calculo" (enum nao descoberto apos ~284 tentativas; provavelmente so no Add-In Excel) |

> **AETP_ONLY genuino (10, 26, 142).** A re-verificacao refutou a hipotese de "so falta param":
> com a validacao de parametros TOTALMENTE satisfeita (10/26 ainda pediam `Precisao` e
> `QuantidadePregoes`; adicionados), o servidor persiste em `Nao foi possivel recuperar os campos
> de saida : Query=NONE`. A query de saida nao esta registrada server-side -> confirma o rotulo
> `AETP_ONLY`, NAO e flip. (10 = HistoricoDiario, na secao 2.1; 142 = DiarioEx.)

> **83/138/139/144 — paredes de parametro (nao crackadas).** Ficam em `PARAMS`. 138/139/144
> exigem um "Tipo de calculo" cujo nome/enum nao foi descoberto (~284 combinacoes testadas no
> 144 sem avancar a mensagem); provavelmente um codigo so conhecido pelo Add-In Excel. O 83 e
> uma inconsistencia do servidor: ele LE `Instrumentos` (validou simbolo) mas rejeita `DataInicio`
> como ausente mesmo quando enviado no formato correto (`YYYYMMDD`).

### 2.4 Recuperados na re-verificacao (eram falso-negativos `PARAMS`)

Endpoints que o catalogo de 2025 marcava `api_error`/bloqueado mas que **funcionam** com os
parametros corretos (verificado 2026-06-02, dados reais):

| ID | Endpoint | Status | Dados | Params Chave |
|---|----------|--------|-------|--------------|
| 41 | **TimesTrades** | Confirmado | Times & trades B3/intl (janela UTC) | `305`=ticker, `10071`/`10072`=`YYYYMMDDHHMMSS` **em UTC** |
| 131 | **ConversorMoedas** | Confirmado | Conversao de moeda **spot** (1 tick, campo `LAST`) | `Instrumento`=de, `Instrumento2`=para, `Valor`=quantia |
| 145 | **CalculoInflacao** | Confirmado | Serie de inflacao (22 ticks `DAT`/`ACUM`) | `305`=`AEIPCA` (NAO bare `IPCA`), `961`=start |
| 204 | **FechamentoPrimeiro** | Confirmado | Primeiro fechamento historico do ativo | `Instrumento`=ticker B3 bare (ex.: `PETR4`, NAO `.BVMF`) |

> - **41 TimesTrades**: o "empty ticks para B3" da varredura de 2025 era o **erro de fuso** — a
>   janela `10071`/`10072` e interpretada em **UTC**, nao BRT. Com janela UTC cobrindo o pregao
>   (`13:00`–`14:00` UTC = `10:00`–`11:00` BRT), PETR4 e USDBRL retornam ticks. Ver
>   [`limitations.md`](./limitations.md#timestrades--historicotick--14-digit-datetime).
> - **131 ConversorMoedas**: a cadeia de erros revelou `Instrumento` -> `Instrumento2` -> `Valor`.
>   Ex.: `USD`/`BRL`/`100` -> `LAST=501.09` (exatamente 100x a taxa spot -> calcula, nao ecoa).
>   **E spot**: parametros de data sao inertes (sempre a taxa atual, sem conversao historica).
> - **145 CalculoInflacao**: usa a familia de simbolos internos AE (igual ao `bmacro`). `305=IPCA`
>   da "simbolo nao existe na base"; `305=AEIPCA` retorna a serie. Ver tabela de simbolos em
>   `MacroEconomicos` (secao "Observacoes Tecnicas").
> - **204 FechamentoPrimeiro**: aceita so o ticker **bare** (`PETR4` -> `DAT=19940704`,
>   `LAST=0.17117`); `PETR4.BVMF` nao resolve e `Instrumento=USD` da `success` com 0 ticks (usar
>   ticker de acao B3).

---

## 3. AEInstrumentos — Dados de Referencia

**TODOS bloqueados** (`PROPRIETARY`): retornam `ErrorCode=88007, Tipo de resposta indisponivel ou invalido`.
Protocolo binario proprietario Java que nao aceita resposta em XML/JSON.
Estes endpoints so sao acessiveis pelo terminal desktop (Java/Swing client).
**Dados equivalentes disponiveis via `aetp/output/`** (secao 5).

> **Re-verificado (2026-06-02) — bloqueio comprovado, antes presumido.** A varredura de 2025
> sempre injetava `TipoResposta=xml` e nunca testou sem o param. A re-verificacao exercitou as 3
> variacoes (`xml`, `json`, ausente) em 9 servlets representativos (17, 18, 19, 21, 24, 25, 34,
> 68, 98): corpo IDENTICO byte-a-byte (73B de texto puro, `ErrorCode=88007`) nos tres casos,
> sempre `HTTP 200` (rota existe). Com controle positivo (token vivo via `Inflacao`/126), o 88007
> e bloqueio especifico do endpoint, nao artefato de sessao. Isto e **fechamento de lacuna**, nao
> divergencia: o rotulo do catalogo se confirma.

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
| 195 | **CarteiraRecomendadaTicker** | Confirmado | Em quais carteiras o ticker esta (54 linhas, ref-date real) | `10113`=ticker |
| 197 | **CarteiraRecomendadaMudancas** | A investigar | Mudancas na carteira — vivo, mas sem registros nas datas testadas | `13784`=dataReferencia + `10087`=idCorretora (ambos obrigatorios) |
| 198 | **CarteiraRecomendadaCorretoras** | Implementado | Lista de corretoras com carteiras | 318B |

> **197 CarteiraRecomendadaMudancas — a investigar (nao e falso-positivo simples).** Os "144B
> Confirmados" pela varredura de 2025 eram um **header de erro de validacao** (campo obrigatorio
> faltando), nao dados. O endpoint esta **vivo**: exige DOIS params obrigatorios — `13784`
> (dataReferencia) + `10087` (idCorretora) — e so com `10087` retorna `Campo obrigatorio nao
> enviado! ...dataReferencia`. Com ambos, responde `Nao foram encontrados registros` (109B, erro
> bem-formado) para as datas testadas (2026-06-01). Como mudancas de carteira sao eventos esparsos
> e o par corretora/data nao foi cruzado contra um sibling com registro real (195 expoe ref-date
> `2025-01-13`), "sem registros" **nao e conclusivo**: NAO confirmavel como funcional, mas tambem
> **nao bloqueado**. Fica como `A investigar`.

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
>
> **Re-verificado (2026-06-02): segue morto.** 166/167/182/214 retornam `in_88008` /
> `Erro inesperado ao acessar os dados` + tag `13899=Bad Request` (o front AETP repassa o erro do
> backend GraphQL). 168/170 retornam `in_88000` "Nao foram encontrados registros". Combinado com a
> casca vazia do 154 (secao 2.1), **nao ha fonte de demonstracoes financeiras / indicadores
> historicos via terminal antigo** — ver [`limitations.md`](./limitations.md).

### 5.5 Fundamental — Metadados / Classificacao

| ID | Endpoint | Status | Dados | Size |
|---|----------|--------|-------|------|
| 175 | **ArquivosCategorias** | Confirmado | Categorias de filings (89 linhas) | 4KB |
| 176 | **ArquivosEspecies** | Confirmado | Especies de documentos (54 linhas) | 2.2KB |
| 177 | **ArquivosTipos** | Confirmado | Tipos de documentos (106 linhas) | 4.4KB |
| 185 | **IndicadorCategorias** | Confirmado | Categorias de indicadores (12 linhas) | 252B |
| 205 | **ArquivosDemonstrativos** | Confirmado | Lista de demonstrativos (URLs S3 de PDFs) | requer `13004`=codigoCvm + `13916`=datasIni + `13917`=datasFim |
| 212 | **TickersEmpresas** | Vazio/Casca | Sem registros (`in_88000`) para PETR4/VALE3 | — |

> **205 era falso-positivo de bytes, mas FUNCIONA com os params certos.** Os "139B Confirmados"
> de 2025 eram um header de erro (`in_88008`, faltava `codigoCvm`). A cadeia de erros revelou 3
> params obrigatorios — `13004` (codigoCvm) + `13916` (datasIni) + `13917` (datasFim) — e com os
> tres o endpoint retorna linhas reais (ex.: URL de PDF de ITR em `agenciaestado-fundamental.s3...`).
> **212 TickersEmpresas, ao contrario, e genuinamente vazio**: os "109B" eram o erro `in_88000`
> "Nao foram encontrados registros", reproduzido para PETR4 e VALE3.

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
| 158 | **FundosListaTipoAtivo** | Confirmado | Tipos de ativo para fundos (78 linhas) | 2KB |
| 159 | **FundosListaTipoAplicacao** | Confirmado | Tipos de aplicacao (52 linhas) | 1.6KB |
| 222 | FundosBuscaRapida | Bloqueado | **GraphQL-only** — rejeita xml/sem-TipoResposta com `in_88008` `AllowedResponseTypes=[GQL]` |

### 5.9 Energia

| ID | Endpoint | Status | Dados | Size |
|---|----------|--------|-------|------|
| 174 | EnergiaHorarioIntraday | Confirmado | Mercado de energia | 118B (sem dados uteis) |

---

## 6. AEContent — Noticias

### 6.1 Protocolo Binario (BLOQUEADO)

Endpoints AETP originais para noticias — todos bloqueados por subscricao (error 88007).
**Re-verificado (2026-06-02): seguem bloqueados** (com controle positivo via `Inflacao`/126).

| ID | Endpoint | Status | Notas |
|---|----------|--------|-------|
| 27 | Noticias (NewsServlet) | Bloqueado | `tp_88007` (tag `10037`) |
| 28 | Conteudo (ContentServlet) | Bloqueado | `tp_88007` (tag `10037`) |
| 29 | Cadernos (CadernoServlet) | Bloqueado | `tp_88007` (tag `10037`) |
| 30 | Arquivo (FileServlet) | Bloqueado | `tp_88007` (tag `10037`) |
| 108 | CountNoticias | Bloqueado | Binary SOH, 81B (`tp_88007`, sem dados) |
| 110 | topNewsLista | Bloqueado | Binary SOH, 81B (`tp_88007`, sem dados) |
| 152 | MaisLidasLista (aetp) | Bloqueado | Binary SOH, 63B — envelope vazio (so field-defs, 0 linhas); difere em TIPO do 88007 |
| 153 | Noticias Relacionadas | Bloqueado | `tp_88007` (tag `10037`) |

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

**Parcialmente quebrado — NAO uniformemente 500.** A re-verificacao (2026-06-02) refutou a
generalizacao de 2025 ("TODOS HTTP 500"): a maioria dos endpoints de Fundos CVM de fato retorna
HTTP 500 (JBoss/Tomcat error report), mas pelo menos dois respondem `HTTP 200` com dados binarios
SOH validos. Verifique caso a caso antes de presumir bloqueio.

| IDs | Endpoints | Status |
|---|----------|--------|
| 62 ListaCategorias, 63 ListaTiposFundos, 74 BuscarFundos, 133 CDIRentabilidade | (amostra re-testada) | Bloqueado (HTTP 500) |
| 61, 64-67, 73, 100, 115, 121-123, 127-130, 134 | Demais Fundos CVM | Bloqueado (HTTP 500, nao re-testados individualmente) |
| 132 | FundosTabelaRentabilidade | `HTTP 200` `in_88000` "sem registros" — e BaseHistoricaNumerica (`nao-cp`), nao um 500 |
| 120 | **ClasseAnbima** | **Confirmado** — `HTTP 200`, 146B, binary SOH, 11 linhas (classes Anbima: Acoes, FIP, Multimercados, OffShore, ...) |
| 116 | **BuscarFundosAutoComplete** | **Confirmado** — `HTTP 200`, ~1MB+ binary SOH, 11 campos, >31 linhas (autocomplete de fundos) |

> **120 e 116 eram falso-negativos** (catalogados "500"). Hoje retornam `HTTP 200` com SOH valido
> e zero tokens de erro. A varredura de 2025 generalizou um 500 observado em outros endpoints do
> grupo para o grupo inteiro — corrigido aqui.

---

## 8. MarkitOutput2 — CDS / Credito

A varredura de 2025 marcou quase tudo como `DEAD_BACKEND`/`api_error`; a re-verificacao
(2026-06-02) mostra o backend **vivo** — eram falso-negativos por **param errado** (`BR` em vez
de uma data/tipo valido). Os params diferem por endpoint (NAO ha um `10047` uniforme):

| ID | Endpoint | Status | Params Chave / Notas |
|---|----------|--------|----------------------|
| 91 | **MarkitListaTipoCDS** | Confirmado | sem params (2 tipos de CDS, 268B XML) |
| 90 | **MarkitListaDatas** | Confirmado | `13336`=`C` (260 linhas); `13336=BR` -> erro "TipoListaDatas invalido" |
| 92 | **MarkitIndices** | Confirmado | `10047`=data `YYYY-MM-DD` (394 linhas, 135KB); `10047=BR` -> "Data invalida" |
| 93 | **MarkitListaCDS** | Confirmado | `10047`=data `YYYY-MM-DD` (58 linhas) |
| 94 | **MarkitCDS** | Confirmado | curva de termo CDS de 1 entidade (SPREAD 6M-10Y + VAR/BID_ASK + recovery/rating). Params: `10047`=data, `13339`=S/C, `13349`=IDCDS, `13350`=TIER, `13351`=DOCCLAUSE — a tripla (IDCDS,TIER,DOCCLAUSE) deve ser coerente com o 93 (ex.: BRASIL usa `CR14`, nao `CR`) |

> **Correcao da generalizacao**: o erro de 2025 (`api_error`) era o servidor rejeitando o
> placeholder `BR`. **90 NAO usa `10047`** — usa `13336` (tipo de lista de datas; `C` valido).
> **92/93/94** usam `10047`=data. Com inputs validos, 90/92/93 retornam centenas de linhas;
> 94 retorna 1 RECORD = a curva de CDS da entidade (verificado 2026-06-02: Alemanha SPREAD_5Y=5,83;
> Brasil 135,30), passando a tripla coerente (IDCDS,TIER,DOCCLAUSE) colhida do 93.

---

## 9. IntegracaoTabelas — Commodities / Tabelas

| ID | Endpoint | Status | Dados | Size |
|---|----------|--------|-------|------|
| 105 | **ListaCategorias** | Confirmado | Categorias (Area, Volume, Produtividade) — 6 linhas | 876B |
| 107 | **CategoriaPreco** | Confirmado | Moedas/simbolos de preco — 6 linhas | 1KB |
| 111 | **ListaFormulas** | Confirmado | Formulas disponiveis — 3 linhas | 358B |
| 106 | **CategoriaProporcao** | Confirmado | Proporcao por categoria — 5 linhas (`13438`=categoriaId) | 571B |
| 102 | SelecaoFiltro | Vazio/Casca | `13431`=categoriaId; `STATUS=error` "sem registros" para os IDs testados | 181B |
| 103 | ConteudoFiltro | Vazio/Casca | `13431`+`13433`; `STATUS=error` "sem registros" | 181B |
| 104 | ConteudoTabela | Vazio/Casca | `13431`+`13435`+`13436`+`13437`; `STATUS=error` "sem registros" | 181B |

> Re-verificado (2026-06-02): 105/107/111/106 retornam `success` + linhas reais. 102/103/104,
> mesmo com IDs colhidos de 105/111, retornam `STATUS=error` "Nao foram encontrados registros" —
> exigem combinacoes de filtro especificas nao mapeadas.

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
| HTTP AEInstrumentos | 100% bloqueado | `PROPRIETARY` — error 88007 (comprovado em 3 variacoes de `TipoResposta`) |
| HTTP AEContent | 100% bloqueado | `PROPRIETARY` — error 88007 (News); CentralMultimidia (ASP.NET) e separado e funcional |
| HTTP contentProxyOutput | Majoritariamente quebrado | Maioria HTTP 500, MAS 120 (ClasseAnbima) e 116 (BuscarFundosAutoComplete) retornam 200+dados |
| HTTP MarkitOutput2 | Funcional | Backend vivo: 90/91/92/93/94 funcionam com params validos (94 = curva CDS da entidade via tripla coerente do 93) |
| AETP TCP:8100 | Nao cracked | Protocolo binario, framing customizado |
| SPC .NET (AESpcNET.dll) | Dead end | Servidor nao roteia dados para clientes externos |
| RTD COM | Indisponivel | Broadcast nao tem servidor RTD (usa DDE) |

---

## Resumo Quantitativo

> Contagens revisadas apos a re-verificacao de 2026-06-02. Permanecem aproximadas (`~`): a
> re-verificacao tocou um subconjunto, nao todos os 227 endpoints. So foram ajustadas as
> categorias que mudaram de forma demonstravel.

| Status | Count | Descricao |
|--------|-------|-----------|
| Implementado na lib | **26 funcoes** | bdp, bdh, bdh_ohlcv, bdi, bdt, bmacro, bdi_cdi, breturn, bvolume, binflation, bconsensus, bcompany, bindices, bsectors, bquote, btickers, bshares, bindicators, bindicator_meta, bcalendar, bdividends, bdy, bportfolios, bportfolio, bsearch, InstrumentDB |
| Funcional, nao implementado | **~38** | Endpoints com dados reais (FIIs, Fundos, TitulosPublicos, Markit/CDS, ClasseAnbima, ConversorMoedas, TimesTrades, etc.). **Sem demonstracoes financeiras** — ver abaixo |
| Vazio/Casca | **~5** | Vivos mas sem dado utilizavel: 154, 207, 208, 212 (e 102-104 parciais). Nao confirmavel: 197 |
| Bloqueado/Quebrado | ~68 | Ver categorias abaixo |
| Fora de escopo | ~8 | Contribuicao, admin, banners |

> **Sem demonstracoes financeiras (DRE/BP/FC, P/L, ROE historicos) via terminal antigo.** O 154
> (EmpresasHistorico) e casca vazia e o backend GraphQL de indicadores (166/167/182/214) esta
> morto. Fundamentais legacy = so consenso (52), indicadores diarios (market cap/beta via 171),
> dividendos/eventos e metadados. Para financials, investigar o backend **Plus**.

### Categorias de Falha

| Categoria | Count | Endpoints | Possibilidade de Resolver |
|-----------|-------|-----------|---------------------------|
| `PROPRIETARY` | ~58 | AEInstrumentos, AEContent (News) | Requer reverse-engineering do protocolo Java binario |
| `DEAD_BACKEND` | ~34 | contentProxyOutput (maioria 500, exceto 120/116), GraphQL indicadores (AWS offline) | Pode voltar se backend for restaurado |
| `AETP_ONLY` | ~3 | HistoricoDiario (10), DiarioEx (142), UltimosPregoes (26) | Confirmado: `Query=NONE` mesmo com validacao OK. Requer protocolo AETP TCP:8100 |
| `PARAMS` | ~5 | 81, 83, 138, 139, 144 (BaseHistoricaNumerica) | Parede de parametro nao crackada (enum/param so no Add-In) |
| `BUG` | ~1 | Players (SQL error) | Bug no servidor |

> Reducoes vs 2025: `DEAD_BACKEND` e `PARAMS` cairam porque varios "bloqueados" eram
> falso-negativos (120/116, Markit 90/92/93, e os flips `PARAMS`->funcional 41/131/145/204).

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

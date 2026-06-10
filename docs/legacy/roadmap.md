# Roadmap — Terminal Antigo (bcsys32.exe)

Backlog de endpoints funcionais que ainda nao tem adapter na lib, mais decisoes de API
deferidas. Status de cada endpoint re-verificado ao vivo em 2026-06-02 (a varredura original
de 2025 continha erros sistematicos — ver a nota metodologica em [`endpoints.md`](./endpoints.md)).

Ver [`endpoints.md`](./endpoints.md) para o catalogo completo com status e params de cada endpoint.

---

## Reformulacao de API planejada (deferida para um release deliberado)

O 0.6.0 conformou o **contrato** (DataFrame achatado + coluna `ticker`, multi-ticker,
`NotFoundError` vs vazio-com-schema, parse BR -> float, paridade sync/async completa) e a
**arquitetura** (catalogo `EndpointSpec` declarativo; camada de I/O async-first com a arvore
sync gerada via unasync — ver [`../architecture.md`](../architecture.md)). Ficou **deferida**
uma camada de reformulacao puramente nominal/estrutural, que e *breaking* e por isso merece um
release proprio (ex.: 0.7.0). Nenhum item abaixo corrige bug — sao melhorias de clareza/ergonomia.

| # | Mudanca | Estado atual | Proposta | Risco |
|---|---------|--------------|----------|-------|
| 1 | **Naming de historico** | `bdh` retorna so close+settle; `bdh_ohlcv` retorna OHLCV de 1 dia | Ver "Decisao em aberto" abaixo | Breaking nominal |
| 2 | **Fundir `bdi_cdi` em `bmacro`** | endpoint/funcao separada (`DiCetipAcumulado`) | rotear `bmacro("CDI", ...)` internamente; remover `bdi_cdi` do `__all__` | Breaking nominal |
| 3 | **Unificar `bportfolios`/`bportfolio`** | duas funcoes | `bportfolio(broker=None)` (lista quando `None`), padrao de `bcompany(cvm=None)` | Breaking nominal |
| 4 | **Renomear colunas cripticas** | algumas colunas seguem nomes do servidor | nomes finance-standard onde ainda ha residuo | Breaking nominal |
| 5 | **Decisao D — ticker canonico de saida** | so `bdh`/`bvolume` emitem sufixo `.BVMF` (vem do SYMBOL do servidor); o resto e bare | decidir UMA convencao e aplicar no `finalize_frame` (o ponto de aplicacao ja existe) | Breaking de valor |
| 6 | **Index do `bdy`** | docstring diz DatetimeIndex, codigo usa RangeIndex (preservado na migracao por frame-equality) | decidir o correto; CUIDADO: bdy vetoriza+concat por ticker, DatetimeIndex seria nao-unico entre blocos (como bmacro) | Breaking de valor |
| 7 | **`@validate_params` uniforme** | parte das publicas sync usa `ensure_*` ad-hoc em vez do decorator | unificar; muda coercao/upper de input — verificar o novo comportamento isoladamente | Comportamental |

### Decisao em aberto — naming de historico (item 1)

Duas direcoes incompativeis ja propostas, a reconciliar **antes** de executar:

- **Opcao A (renomeio simples):** `bdh -> bclose`, `bdh_ohlcv -> bdh`. Honesto com Bloomberg
  (BDH = historico), baixo esforco, mas mantem `bdh_ohlcv` como single-day.
- **Opcao B (unificacao, recomendada):** introduzir `bhistory(tickers, start, end, fields=...)`
  cobrindo close-only e OHLCV multi-dia num so ponto; manter `bclose` como atalho. Resolve a
  limitacao single-day do `bdh_ohlcv` de uma vez, ao custo de mais desenho.

Recomendacao: **Opcao B**, num release 0.7.0 dedicado, com periodo de deprecation curto (o repo
nao tem consumidores externos, entao o churn e so interno + docs + tests).

---

## Pendencias conhecidas (bugs de contrato, nao reformulacao)

- **`bindicators` viola o eixo valid-but-empty**: levanta `ProtocolError` ("Server returned
  empty response") para janelas indicador/range que simplesmente nao tem dados (ex.: indicador
  32 em certos ranges), em vez do empty-frame-with-schema que o contrato promete.

---

## Prioridade Alta (transporte/parser ja existem, so mapear campos)

| # | Endpoint | ID | Tipo | O que retorna | Esforco |
|---|----------|-----|------|---------------|---------|
| 1 | **`bcds` — MarkitOutput2 (CDS/credito)** | 90-94 | XML | Curva de termo de CDS soberano/corporativo (58 entidades + 394 indices). Params 100% decodificados — ver `endpoints.md` sec. 8 e o design abaixo | Baixo — engenharia de params ja feita |
| 2 | **FIIAnbimaBovespa** | 150 | XML | FII: dividend yield, ultimo dividendo, vol medio (HGLG11: DY 9,2%) | Baixo |
| 3 | **CarteiraTopFundos** | 187 | Binary SOH | Quais fundos investem no ativo (top holders, com %) | Baixo |
| 4 | **HistoricoDiarioSimbolos** | 75 | XML | Multi-ticker daily alternativo ao bdh (`10113`=tickers `;`, `961`=start) | Baixo |
| 5 | **EmpresaAcoesUnits** | 183 | Binary SOH | Acoes ON/PN, free float | Baixo |

### Design proposto — `bcds(entity, date=None, tipo="S")`

Derivado da coleta empirica de 2026-06-02 (terminal vivo); params e schema completos em
`endpoints.md` sec. 8 (fluxo 91 tipos -> 90 datas -> 93 entidades -> 94 curva).

- Retorna DataFrame **LONG**: uma linha por tenor (6M, 1Y, 2Y, 3Y, 4Y, 5Y, 7Y, 10Y).
  Colunas: `entity, tenor, spread, var_dia, var_mes, bid_ask` + metadados repetidos
  (recovery, rating implicito, regiao, moeda). RangeIndex + coluna `tenor` (e curva de
  uma data, nao serie temporal).
- **Resolucao automatica da tripla** (IDCDS, TIER, DOCCLAUSE), como `resolve_cvm` faz para
  ticker: dado `entity` (+`tipo`), consultar 93 ListaCDS(date) e pegar a tripla valida —
  ela varia por entidade (ex.: BRASIL usa `CR14`, nao `CR`). Mais de uma tripla -> exigir
  desambiguacao.
- `bcds()` sem entity -> listar entidades disponiveis (93) ou datas (90).
- Valores BR com virgula -> `_core/normalize.parse_br_number` (ja existe).
- Cabe no transporte ContentProxy XML existente; modulo de dominio proprio (ex.: `credit/`).

---

## Prioridade Media (renda fixa e fundos)

| # | Endpoint | ID | Tipo | O que retorna |
|---|----------|-----|------|---------------|
| 6 | **Fundos** | 76 | XML | Historico de cotas de fundos (OHLC, 24KB) |
| 7 | **TitulosPublicos** | 77 | XML | Historico de titulos do Tesouro — usar simbolo `.ANBIMA`/`.TRDM` (bare `LTN` resolve para `LTN.NYSE`, instrumento errado) |
| 8 | **TitulosPublicosUltimos** | 141 | XML | Ultimos precos de titulos publicos (mesma nuance de simbolo) |
| 9 | **CalculoTaxaPre** | 136 | XML | Curva de taxa pre-fixada acumulada (6.5KB) |
| 10 | **CalculoPoupanca** | 114 | XML | Rendimento poupanca diario (5.7KB) |
| 11 | **FundosRentabilidade** | 82 | XML | Rentabilidade de fundo por CNPJ/codigo |
| 12 | **ConversorMoedas** | 131 | XML | Conversao spot calculada (`Instrumento`+`Instrumento2`+`Valor`) |

---

## Prioridade Baixa (metadados e referencia)

| # | Endpoint | ID | Tipo | O que retorna |
|---|----------|-----|------|---------------|
| 13 | **CarteiraRecomendadaTicker** | 195 | Binary SOH | Em quais carteiras de corretoras um ticker esta presente |
| 14 | **UltimosIntraday** | 125 | XML | Ultimo snapshot intraday para um ticker |
| 15 | **FechamentoPrimeiro** | 204 | XML | Primeiro fechamento historico (`Instrumento`=ticker) |
| 16 | **AcionistaDatas** | 193 | XML | Datas de posicoes acionarias |
| 17 | **ArquivosDemonstrativos** | 205 | XML | PDFs de ITR/demonstrativos (links S3) |
| 18 | **TimesTrades** | 41 | XML | Times & trades alternativo ao bdt (janela `10071`/`10072` em **UTC**) |

---

## Params nao crackados (NAO sao mortos — falta descobrir o parametro)

| Endpoint | ID | Estado |
|----------|-----|--------|
| `FechamentoFormula` | 83 | Inconsistencia no servidor entre chamadas |
| `TabelaRetorno` / `TabelaRentabilidade` | 138/139 | Params de benchmark desconhecidos |
| `CalculoCarteira` | 144 | Provavel enum "Tipo de calculo" do Add-In Excel |
| `FundosIndicadores` | 81 | Nao re-testado na rodada de 2026-06 |
| `CarteiraRecomendadaMudancas` | 197 | Vivo (exige `13784`) mas sem registros nas datas testadas; confirmar com broker/data reais |

---

## Nao Implementaveis (sem perspectiva de mudanca)

| Categoria | Endpoints | Motivo |
|-----------|-----------|--------|
| Casca vazia | EmpresasHistorico (154) | Schema de 222 campos (DRE/BP/FC) mas **0 celulas** — financials NAO existem via legacy; para demonstracoes financeiras, auditar o backend Plus |
| Dataset vazio | VolumesMediosSemMesAno (207), Volatilidades (208) | `success` + `<TICKS>` vazio, definitivo |
| `PROPRIETARY` | AEInstrumentos (~58), news AETP (27-30, 108, 110, 152, 153) | Protocolo binario proprietario Java (error 88007) |
| `DEAD_BACKEND` | GraphQL indicadores (166, 167, 182, 214); fundos CVM 133/62/63/74 | Backend offline (500) |
| `AETP_ONLY` | HistoricoDiario (10), UltimosPregoes (26), DiarioEx (142) | `Query=NONE` mesmo com validacao OK — requer pre-registro via AETP TCP:8100 |
| `BUG` | Players (40) | Bug SQL no servidor |

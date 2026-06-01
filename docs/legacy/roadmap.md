# Roadmap — Terminal Antigo (bcsys32.exe)

Backlog de endpoints funcionais descobertos na varredura do ContentProxy que ainda nao tem adapter na lib. Todos retornam dados reais quando chamados diretamente.

Ver [`endpoints.md`](./endpoints.md) para o catalogo completo com status de cada endpoint.

---

## Reformulacao de API planejada (deferida para um release deliberado)

O 0.6.0 conformou o **contrato** (DataFrame achatado + coluna `ticker`, multi-ticker,
`NotFoundError` vs vazio-com-schema, parse BR -> float, paridade sync/async completa). Ficou
**deferida** uma camada de reformulacao puramente nominal/estrutural, que e *breaking* e por
isso merece um release proprio (ex.: 0.7.0). Nenhum item abaixo corrige bug — sao melhorias de
clareza/ergonomia.

| # | Mudanca | Estado atual | Proposta | Risco |
|---|---------|--------------|----------|-------|
| 1 | **Naming de historico** | `bdh` retorna so close+settle; `bdh_ohlcv` retorna OHLCV de 1 dia | Ver "Decisao em aberto" abaixo | Breaking nominal |
| 2 | **Fundir `bdi_cdi` em `bmacro`** | endpoint/funcao separada (`DiCetipAcumulado`) | rotear `bmacro("CDI", ...)` internamente; remover `bdi_cdi` do `__all__` | Breaking nominal |
| 3 | **Unificar `bportfolios`/`bportfolio`** | duas funcoes | `bportfolio(broker=None)` (lista quando `None`), padrao de `bcompany(cvm=None)` | Breaking nominal |
| 4 | **Decorator `@accepts_ticker_or_cvm`** | 4 copias do check `isinstance(int) or isdigit() -> resolve_cvm` em `btickers`/`bdividends`/`bdy`/`bindicators` | extrair para `_legacy/resolve.py` | Interno, nao-breaking |
| 5 | **Renomear colunas cripticas** | algumas colunas seguem nomes do servidor | nomes finance-standard onde ainda ha residuo | Breaking nominal |
| 6 | **`@http_retry` no caminho async** | os helpers async (`async_content_proxy_get`, `async_aetp_request`, `abdh` inline) nao tem retry | decorator async equivalente a tenacity, ou `AsyncRetrying` | Interno, nao-breaking |

### Decisao em aberto — naming de historico (item 1)

O `PLAN.md` original (gitignorado) propunha **`bdh` -> `bclose`** e **`bdh_ohlcv` -> `bdh`**.
A intencao mais recente e **unificar num `bhistory` multi-dia** (um historico OHLCV com range de
datas, em vez de `bdh_ohlcv` ser single-day). As duas direcoes sao incompativeis e precisam ser
reconciliadas **antes** de executar:

- **Opcao A (renomeio simples):** `bdh -> bclose`, `bdh_ohlcv -> bdh`. Honesto com Bloomberg
  (BDH = historico), baixo esforco, mas mantem `bdh_ohlcv` como single-day.
- **Opcao B (unificacao, recomendada):** introduzir `bhistory(tickers, start, end, fields=...)`
  cobrindo close-only e OHLCV multi-dia num so ponto; manter `bclose` como atalho. Resolve a
  limitacao single-day do `bdh_ohlcv` de uma vez, ao custo de mais desenho.

Recomendacao: **Opcao B**, num release 0.7.0 dedicado, com periodo de deprecation curto (o repo
nao tem consumidores externos, entao o churn e so interno + docs + tests).

---

## Prioridade Alta (parser ja existe, so mapear campos)

Todos os endpoints abaixo usam o binary SOH ou XML — os decoders ja estao implementados em `src/py_bcast/`. O trabalho e apenas mapear os campos de resposta e expor a funcao publica.

| # | Endpoint | ID | Tipo | O que retorna | Esforco |
|---|----------|-----|------|---------------|---------|
| 1 | **EmpresasHistorico** | 154 | XML | Balanco trimestral completo (1.2MB, 80+ campos: DRE, balanco, fluxo de caixa desde 1995) | Medio — mapear 80+ campos |
| 2 | **FIIAnbimaBovespa** | 150 | XML | FII: dividend yield, ultimo dividendo, vol medio | Baixo |
| 3 | **EmpresaAcoesUnits** | 183 | Binary SOH | Acoes ON/PN, free float | Baixo |
| 4 | **CarteiraTopFundos** | 187 | Binary SOH | Quais fundos investem no ativo (top holders) | Baixo |
| 5 | **Volatilidades** | 208 | XML | Volatilidade historica por janela (1m, 3m, 6m, 1a, 2a, 3a) | Baixo |
| 6 | **HistoricoDiarioSimbolos** | 75 | XML | Multi-ticker daily alternativo ao bdh (17KB) | Baixo |

---

## Prioridade Media (renda fixa e fundos)

| # | Endpoint | ID | Tipo | O que retorna |
|---|----------|-----|------|---------------|
| 7 | **Fundos** | 76 | XML | Historico de cotas de fundos (OHLC, 24KB) |
| 8 | **TitulosPublicos** | 77 | XML | Historico de titulos do Tesouro |
| 9 | **CalculoTaxaPre** | 136 | XML | Curva de taxa pre-fixada acumulada (6.5KB) |
| 10 | **CalculoPoupanca** | 114 | XML | Rendimento poupanca diario (5.7KB) |
| 11 | **TitulosPublicosUltimos** | 141 | XML | Ultimos precos de titulos publicos |
| 12 | **FundosRentabilidade** | 82 | XML | Rentabilidade de fundo por CNPJ/codigo |

---

## Prioridade Baixa (metadados e referencia)

Endpoints de metadados que complementam funcoes ja implementadas:

| # | Endpoint | ID | Tipo | O que retorna |
|---|----------|-----|------|---------------|
| 13 | **CarteiraRecomendadaTicker** | 195 | Binary SOH | Em quais carteiras de corretoras um ticker esta presente |
| 14 | **CarteiraRecomendadaMudancas** | 197 | Binary SOH | Historico de mudancas em uma carteira de corretora |
| 15 | **UltimosIntraday** | 125 | XML | Ultimo snapshot intraday para um ticker |
| 16 | **VolumesMediosSemMesAno** | 207 | XML | Volumes medios por semana/mes/ano |
| 17 | **EmpresasHistorico (aefundamental)** | 69 | Binary SOH | Dados da empresa (complemento ao bcompany) |
| 18 | **Arquivos (aefundamental)** | 58 | Binary SOH | Lista de documentos/filings da empresa |

---

## Endpoints Possivelmente Funcionais (params desconhecidos)

Endpoints que retornam erro mas que podem funcionar com os parametros corretos:

| Endpoint | ID | Erro atual | Hipotese |
|----------|-----|-----------|---------|
| `TimesTrades` | 41 | Empty ticks | Formato de parametro diferente do HistoricoTick |
| `FundosIndicadores` | 81 | `api_error` | Precisa de ID de fundo especifico |
| `TabelaRetorno` | 138 | `api_error` | Parametros de benchmark desconhecidos |
| `TabelaRentabilidade` | 139 | `api_error` | Idem |
| `ConversorDeMoedas` | 131 | `api_error` | Par de moedas em formato diferente |

---

## Nao Implementaveis (sem perspectiva de mudanca)

| Categoria | Endpoints | Motivo |
|-----------|-----------|--------|
| `PROPRIETARY` | AEInstrumentos (~58), AEContent | Protocolo binary proprietario Java (error 88007) |
| `DEAD_BACKEND` | contentProxyOutput (~30), GraphQL indicadores | Backend offline/crashado |
| `AETP_ONLY` | HistoricoDiario, DiarioEx, UltimosPregoes | Requer pre-registro via protocolo AETP TCP:8100 |
| `BUG` | Players (id=40) | Bug SQL no servidor |

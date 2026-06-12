# Feature Compatibility — Legacy vs Plus

Mapeamento cruzado de funcionalidades entre os dois backends. Mostra o que cada terminal suporta, qual endpoint corresponde a qual funcao da lib, e o status atual de implementacao no Plus.

> Endpoints confirmados via probe HTTP sistematico com JWT valido (2026-05-25/27). Adapters verificados ao vivo em 2026-06-10.
> Catalogo detalhado por backend: [`legacy/endpoints.md`](./legacy/endpoints.md) | [`plus/endpoints.md`](./plus/endpoints.md)

---

## Renames e Removals — 0.8.0 (2026-06-12)

Esta versao e **BREAKING** sem shims ou aliases de transicao. Foco: padronizacao de outputs (nomes de coluna, dtypes de data, timezone) para integracao limpa com o ecossistema pandas / matplotlib / mplfinance.

| Antes (0.7.x) | Depois (0.8.0) | Notas |
|---|---|---|
| `bdt` coluna `close` (preco de negociacao) | `price` | Preco de trade unificado para `price` (alinha com `bticks`/`btrades`); `bdi` mantem `close` (e fechamento de barra) |
| `btrades` coluna `last` (Plus) | `price` | Mesmo nome unificado no backend Plus |
| `btrades` colunas `ask_exchange_id`/`bid_exchange_id` (string, Plus) | `ask_broker_id`/`bid_broker_id` (Int64) | O campo `exchangeId` do book e, na B3, o id da corretora de cada ponta; agora faz join com `bbrokers()` |
| `bindex_members` coluna `symbol` (Plus) | `ticker` | Padronizacao do nome de instrumento |
| `bindexes` coluna `index` (Plus) | `code` | Igual ao nome de coluna do legacy `bindices` |
| `binflation` coluna `symbol` | `ticker` | Padronizacao do nome de instrumento |
| `bdt`/`bdi` index naive | `DatetimeIndex` tz-aware `America/Sao_Paulo` | Saida tz-aware; `bdt` interpreta a janela de entrada como horario de Brasilia |
| Colunas de data como `float64`/`object` (`*_date`, `*_disclosed`, `period_*`, `expiration_date`, ...) | `datetime64[ns]` | Coercao de data centralizada em `finalize_frame` (16 funcoes) |

### Novas funcoes (aditivas)

| Funcao | Backend | Descricao |
|---|---|---|
| `bsector_members(sector_id)` | Legacy | Empresas classificadas sob um setor da B3 (EmpresasPorSetores) |
| `bstatement_dates(ticker_or_cvm)` | Legacy | Datas dos ultimos demonstrativos anual (DFP) e trimestral (ITR) |
| `bunit_price(symbol, start, end)` | Legacy | Serie de preco unitario (PU) + retorno acumulado de RF (CalculoPreco) |
| `binflation_history(symbol, start, end)` | Legacy | Serie acumulada de indice de inflacao (CalculoInflacao) |
| `bfund_list(query)` | Legacy | Universo de fundos via autocomplete, filtrado por nome (binary) |
| `bcds_indices(date=None)` | Legacy | Indices de CDS Markit na data mais recente |
| `bbrokers()` | Plus | Registro de corretoras (id, name); decodifica os broker ids de `btrades` |
| `bexchanges()` | Plus | Registro de bolsas (id, name, delay em minutos); decodifica `exchange_id` de `binfo` |
| `df.bcast.ohlc()` | accessor | View OHLCV capitalizada (Open/High/Low/Close/Volume) para mplfinance |

---

## Renames e Removals — 0.7.0 (2026-06-10)

Esta versao e **BREAKING** sem shims ou aliases de transicao:

| Antes (0.6.x) | Depois (0.7.0) | Notas |
|---|---|---|
| `bdh(tickers, start, end)` | `bhistory(tickers, start, end)` ou `bclose(tickers, start, end)` | Backend mudou: HistoricoDiarioSimbolos (1 req/ticker); valores identicos ao antigo por ticker |
| `bdh_ohlcv(ticker, date)` | `bhistory(tickers, start, end, fields="ohlcv")` | Agora multi-dia; o antigo tinha bug: lia so o primeiro tick (pregao mais recente) |
| `bdi_cdi(start, end)` | `bmacro("CDI", start, end)` | Bloco CDI agora carrega coluna `accumulated` extra |
| `bportfolios()` | `bportfolio()` (sem args) | |
| `bportfolio(broker_id)` | `bportfolio(broker_id)` | Inalterado |
| — | `bportfolio(broker_id, date=...)` | Novo: composicao historica |
| `df["dat"]` em bvolume/binflation/RANGE frames | `df["date"]` | Coluna renomeada |
| Ticker de saida `"PETR4.BVMF"` em bdh/bvolume | `"PETR4"` (bare) | `finalize_frame` remove o sufixo `.BVMF` universalmente |

---

## Mapeamento de Funcoes

| Funcao py-bcast | Endpoint Legacy | Endpoint Plus | Status Plus |
|---|---|---|---|
| `bdp()` / `BroadcastClient` | DDE `BC/COT/TICKER.FIELD` | WS `startStreamQuote` | **Implementado via `BroadcastPlusClient`** |
| `BroadcastClient.snapshot()` | DDE `BC/ATIVO/TICKER` | `POST /stock/v1/quote/symbol` | **Implementado via `binfo()`** — metadata; preco via WS |
| `bhistory()` / `bclose()` | `BaseHistoricaNumerica/HistoricoDiarioSimbolos` + `HistoricoData` | `POST /stock/v1/historical/symbol` | Bloqueado — erro bh_88063 (restricao de assinatura) |
| `bdi()` | `BaseHistoricaNumerica/HistoricoIntraday` | `POST /stock/v1/timesAndTrades` | **Implementado via `btrades()`** — 500 trades/chamada |
| `bdt()` | `BaseHistoricaNumerica/HistoricoTick` | `POST /stock/v1/historical/tickbytick/symbol` | Bloqueado — mesmo bh_88063 |
| `bticks()` | `BaseHistoricaNumerica/TimesTrades` | Sem equivalente | Sem suporte no Plus |
| `bmacro()` | `BaseHistoricaNumerica/MacroEconomicos` + `DiCetipAcumulado` (CDI) | Sem equivalente | Sem suporte no Plus |
| `bstats()` | `BaseHistoricaNumerica/FIIAnbimaBovespa` | Sem equivalente | Sem suporte no Plus |
| `bsnapshot()` | `BaseHistoricaNumerica/UltimosIntraday` | Sem equivalente | Sem suporte no Plus |
| `btreasury()` | `BaseHistoricaNumerica/TitulosPublicosUltimos` | Sem equivalente | Sem suporte no Plus |
| `btreasury_history()` | `BaseHistoricaNumerica/TitulosPublicos` | Sem equivalente | Sem suporte no Plus |
| `baccrual()` | `BaseHistoricaNumerica/CalculoTaxaPre` | Sem equivalente | Sem suporte no Plus |
| `bsavings()` | `BaseHistoricaNumerica/CalculoPoupanca` | Sem equivalente | Sem suporte no Plus |
| `bfund_history()` | `BaseHistoricaNumerica/Fundos` | Sem equivalente | Sem suporte no Plus |
| `bfund_returns()` | `BaseHistoricaNumerica/FundosRentabilidade` | Sem equivalente | Sem suporte no Plus |
| `bfx()` | `BaseHistoricaNumerica/ConversorMoedas` | Sem equivalente | Sem suporte no Plus |
| `bfirst_close()` | `aetp/output/FechamentoPrimeiro` | Sem equivalente | Sem suporte no Plus |
| `bconsensus()` | `aefundamental/consenso` | Sem equivalente | Sem suporte no Plus |
| `bcompany()` | `aetp/output/fundamental/empresa` | Sem equivalente | Sem suporte no Plus |
| `bindices()` | `aetp/output/ativos/indice` | `GET /stock/v1/indexes` | **Implementado via `bindexes()`** — lista de codigos de indices |
| `bsectors()` | `aetp/output/fundamental/setor` | `GET /stock/v1/instrumentTypes` | Confirmado — tipos de instrumento |
| `bcalendar()` | `aetp/output/fundamental/calendario` | `GET /stock/v1/calendar/tables` | **Implementado via `bholidays()`** — catalogo de tabelas; datas bloqueadas (param nao descoberto) |
| `bdividends()` | `aetp/output/fundamental/eventos/jcp-dividendos` | `POST /stock/v1/corporateevents/{symbol}` | **Implementado via `bcorpevents()`** — inclui fatores de ajuste que o legado nao tem |
| `bdy()` | `aetp/output/fundamental/eventos/dividend-yield` | incluido em `corporateevents` | A implementar |
| `bfree_float()` | `aetp/output/fundamental/EmpresaAcoesUnits` | Sem equivalente | Sem suporte no Plus |
| `bfund_holders()` | `aetp/output/fundamental/CarteiraTopFundos` | Sem equivalente | Sem suporte no Plus |
| `bshareholder_dates()` | `aetp/output/fundamental/AcionistaDatas` | Sem equivalente | Sem suporte no Plus |
| `bfilings()` | `aetp/output/fundamental/ArquivosDemonstrativos` | Sem equivalente | Sem suporte no Plus |
| `bportfolio()` | `aetp/output/fundamental/empresa/carteira-recomendada` | Sem equivalente | Sem suporte no Plus |
| `bportfolios_with()` | `aetp/output/fundamental/CarteiraRecomendadaTicker` | Sem equivalente | Sem suporte no Plus |
| `bnews()` / `bnews_recent()` | `CentralMultimidia/` (sem auth) | `POST /news/v1/headlines` + `GET /news/v1/content/{id}` | **Implementado via `bsections()`/`bheadlines()`/`bnews_content()`** — 121 secoes, tagging rico |
| `bsearch()` | `aetp_17.dat` (arquivo local) | `POST /stock/v1/quote/symbol/search` | **Implementado com routing automatico** — schema unificado em `pd.DataFrame` |

---

## Capacidades Exclusivas do Plus

Endpoints que nao tem equivalente no Terminal Antigo:

| Endpoint Plus | Funcao | Descricao |
|---|---|---|
| `GET /stock/v1/indexes/{index}` | `bindex_members(index)` | Composicao de indice com pesos de relevancia (IBOV: 79 membros, IFIX: 107) |
| `GET /stock/v1/logo/{symbol}` | `blogo(symbol)` | Logo PNG do instrumento (2-4KB) |
| `GET /stock/v1/brokerages` | `bbrokers()` | Registro de corretoras (84 corretoras); decodifica `ask_broker_id`/`bid_broker_id` de `btrades` |
| `GET /stock/v1/exchanges` | `bexchanges()` | Registro de bolsas (46 bolsas) com delay por praca; decodifica `exchange_id` de `binfo` |
| `POST /funds/v1/search` | `bfunds(query)` | Busca de fundos por nome (min. 3 chars) — rentabilidade, taxas, CNPJ, ANBIMA |
| `GET /funds/v1/{id}` | `bfund(fund_id)` | Detalhe de fundo por id numerico |
| `GET /news/v1/sections` | `bsections()` | Catalogo de 121 secoes de noticias |
| `POST /news/v1/headlines` | `bheadlines(sections, count)` | Manchetes paginadas com tagging rico |
| `GET /news/v1/content/{id}` | `bnews_content(content_id)` | Corpo HTML + tagging (autores, entidades, topicos, localizacoes) |
| WS `startStreamMarket` | `BroadcastPlusClient.subscribe_market(market_ids, callback)` | Tabelas ao vivo da Bovespa: maiores altas/baixas, volume, Ibovespa |
| WS `startStreamBook` | — | Book de ofertas — bloqueado por permissao de conta; nao implementado |
| `GET /stock/v1/fields` | — | Todos os campos com nome, tipo, descricao (83KB) |
| `POST /fit/v1/table` + `GET /fit/v1/filter/{id}` | — | Screener/triagem de acoes com filtros salvos na conta |
| `GET /marketplace/v1/products` | — | Produtos complementares do marketplace |
| `POST /news/v2/headlines` | — | Headlines v2 (100/pagina, mesmo schema) |
| `POST /authentication/v1/permissions` | — | 429 permissoes da conta por produto/servico/exchange |

Todas as funcoes Plus tem twin async com prefixo `a` (ex.: `abinfo`, `abindex_members`, `abfunds`, `abcorpevents`) disponivel em `py_bcast.async_api`.

---

## Capacidades Exclusivas do Legacy

Funcionalidades que existem apenas no Terminal Antigo e nao tem plano de suporte no Plus:

| Funcao | Endpoint Legacy | Motivo |
|--------|----------------|--------|
| `bhistory()` / `bclose()` | `HistoricoDiarioSimbolos` + `HistoricoData` | Historico bloqueado no Plus (bh_88063) |
| `bticks()` | `TimesTrades` | Sem equivalente no Plus |
| `bmacro()` (incluindo CDI) | `MacroEconomicos` + `DiCetipAcumulado` | Sem endpoint de macro series no Plus |
| `bstats()` | `FIIAnbimaBovespa` | Sem equivalente no Plus |
| `bsnapshot()` | `UltimosIntraday` | Sem equivalente no Plus |
| `btreasury()` / `btreasury_history()` | `TitulosPublicosUltimos` + `TitulosPublicos` | Sem endpoint de tesouro no Plus |
| `baccrual()` | `CalculoTaxaPre` | Sem equivalente no Plus |
| `bsavings()` | `CalculoPoupanca` | Sem equivalente no Plus |
| `bfund_history()` / `bfund_returns()` | `Fundos` + `FundosRentabilidade` | Sem equivalente no Plus |
| `bfx()` | `ConversorMoedas` | Sem equivalente no Plus |
| `bfirst_close()` | `FechamentoPrimeiro` | Sem equivalente no Plus |
| `bconsensus()` | `aefundamental/consenso` | Sem endpoint de consenso no Plus |
| `bcompany()` | `aetp/output/fundamental/empresa` | Sem endpoint de dados de empresa no Plus |
| `bfree_float()` / `bfund_holders()` | `EmpresaAcoesUnits` + `CarteiraTopFundos` | Sem equivalente no Plus |
| `bshareholder_dates()` / `bfilings()` | `AcionistaDatas` + `ArquivosDemonstrativos` | Sem equivalente no Plus |
| `bportfolio()` / `bportfolios_with()` | `aetp/output/carteira-recomendada` | Sem equivalente no Plus |
| `breturn()` | `RetornoDiario` | Sem endpoint de retorno diario no Plus |
| `bvolume()` | `VolumesMedios` | Sem endpoint de volumes medios no Plus |
| `binflation()` | `Inflacao` | Sem endpoint de indices de inflacao no Plus |
| `bindicators()` | `IndicadorHistoricoDiario` | Sem endpoint de indicadores fundamentalistas no Plus |
| `bcds()` | `MarkitOutput2/CDS` | Sem endpoint de CDS/credito no Plus |
| `InstrumentDB` / `bsearch()` (busca local) | `aetp_17.dat` | Arquivo local do bcsys32; Plus usa `quote/symbol` para lookup pontual |

---

## Comparacao Tecnica dos Backends

| Aspecto | Terminal Antigo | Terminal Novo |
|---------|----------------|---------------|
| Protocolo tempo real | DDE (DDEML, Win32) | WebSocket JSON |
| Auth tempo real | BCAA session (mem scan de bcsys32.exe) | JWT Bearer (mem scan de Broadcast+.exe) |
| Auth HTTP | Tag `10039` no query string | Header `Authorization: Bearer <JWT>` |
| Formato HTTP | XML + binary SOH | JSON |
| Paginacao | Nao | Sim (`currentPage`, `pageCount`, `remaining`) |
| Refresh de token | Manual (re-scan) | Auto-refresh via `refreshToken` |
| Ambiente headless | `BROADCAST_SESSION` env var | `BROADCAST_PLUS_TOKEN` env var |
| Configuracao headless | — | `configure(plus_login=..., plus_password=...)` |
| Dados historicos | `bhistory()`, `bdi()`, `bdt()`, `bticks()` | Historico bloqueado (bh_88063), T&T via `timesAndTrades` |
| Banco de instrumentos | `aetp_17.dat` (623K, local) | Lookup via `quote/symbol` (online) |
| Market stats streaming | Nao | `subscribe_market` em `BroadcastPlusClient` |
| Book streaming | Nao | Bloqueado (permissao de conta ausente) |

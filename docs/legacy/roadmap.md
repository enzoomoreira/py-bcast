# Roadmap — Terminal Antigo (bcsys32.exe)

Backlog de endpoints funcionais que ainda nao tem adapter na lib, mais decisoes de API
deferidas. Status de cada endpoint re-verificado ao vivo em 2026-06-02 (a varredura original
de 2025 continha erros sistematicos — ver a nota metodologica em [`endpoints.md`](./endpoints.md)).

Ver [`endpoints.md`](./endpoints.md) para o catalogo completo com status e params de cada endpoint.

---

## Reformulacao de API executada em 0.7.0 (2026-06-10)

O 0.6.0 conformou o **contrato** e a **arquitetura**. A reformulacao nominal/estrutural deferida
foi executada integralmente em 0.7.0 como **Opcao B** (unificacao via `bhistory`), sem shims ou
aliases de transicao. Resumo das decisoes tomadas:

1. `bhistory(tickers, start, end, fields="close"|"ohlcv")` substitui `bdh` e `bdh_ohlcv`;
   `bclose` e o atalho close. A perna close usa HistoricoDiarioSimbolos (1 request por ticker
   para a janela toda); a perna ohlcv usa HistoricoData, descoberto como multi-dia. Isso tambem
   corrigiu um bug latente do `bdh_ohlcv`: ele lia apenas o primeiro tick da resposta (o pregao
   mais recente), nao a data pedida.
2. `bmacro("CDI", ...)` roteia para DiCetipAcumulado; `bdi_cdi` removido.
3. `bportfolio(broker_id=None, date=None)` absorve `bportfolios` (lista quando broker omitido);
   `bportfolios` removido.
4. Colunas `dat` renomeadas para `date` onde restavam residuos (`bvolume`, `binflation`, RANGE frames).
5. Tickers de saida bare: `finalize_frame` remove o sufixo `.BVMF` que o servidor anexa.
6. `bdy` documentado com o contrato real: RangeIndex + coluna `date` (nao DatetimeIndex).
7. `@validate_params` uniforme em todas as publicas com args (tickers uppercased automaticamente).

Ver [`../compatibility.md`](../compatibility.md) para o mapeamento completo de renames.

---

## Implementado em 2026-06-10

Todos os itens das antigas listas de prioridade alta, media e baixa foram implementados:

| Endpoint | ID | Funcao py-bcast |
|----------|----|-----------------|
| FIIAnbimaBovespa | 150 | `bstats(tickers)` |
| EmpresaAcoesUnits | 183 | `bfree_float(ticker_or_cvm)` |
| CarteiraTopFundos | 187 | `bfund_holders(ticker_or_cvm)` |
| HistoricoDiarioSimbolos | 75 | `bhistory(tickers, ..., fields="close")` (perna close de `bhistory`) |
| Fundos | 76 | `bfund_history(fund, start, end)` |
| TitulosPublicos | 77 | `btreasury_history(symbol, start, end)` |
| TitulosPublicosUltimos | 141 | `btreasury(symbols)` |
| CalculoTaxaPre | 136 | `baccrual(rate, start, end)` |
| CalculoPoupanca | 114 | `bsavings(start, end)` |
| FundosRentabilidade | 82 | `bfund_returns(fund)` |
| ConversorMoedas | 131 | `bfx(from_currency, to_currency, amount)` |
| CarteiraRecomendadaTicker | 195 | `bportfolios_with(ticker)` |
| UltimosIntraday | 125 | `bsnapshot(tickers)` |
| FechamentoPrimeiro | 204 | `bfirst_close(ticker)` |
| AcionistaDatas | 193 | `bshareholder_dates(ticker_or_cvm)` |
| ArquivosDemonstrativos | 205 | `bfilings(ticker_or_cvm, start, end)` |
| TimesTrades | 41 | `bticks(ticker, start, end)` |
| CarteiraRecomendadaMudancas | 197 | `bportfolio(broker_id, date=...)` (composicao historica) |
| HistoricoData | 13 | `bhistory(tickers, ..., fields="ohlcv")` (perna ohlcv de `bhistory`) |

> `bcds` (MarkitOutput2 90-94, CDS/credito) foi IMPLEMENTADO em 2026-06-10 — modulo
> `credit/` + core nas arvores geradas (`_legacy/_async/markit.py`). Ver `api.md`.
> Pendencia anterior do `bindicators` (ProtocolError em janela vazia) NAO reproduz mais:
> a politica `empty_ok` centralizada do transporte EndpointSpec trata a resposta vazia
> (verificado live 2026-06-10 com 7 variacoes de janela/indicador).

---

## Params nao crackados (NAO sao mortos — falta descobrir o parametro)

| Endpoint | ID | Estado |
|----------|-----|--------|
| `FechamentoFormula` | 83 | Parede server-side: le `Instrumentos` (valida simbolo) mas rejeita `DataInicio` como ausente mesmo enviado em YYYYMMDD e dd/MM/yyyy |
| `TabelaRetorno` / `TabelaRentabilidade` | 138/139 | Respondem "Tipo de calculo nao enviado" a todas as chaves testadas (10029, TipoCalculo, TipoDeCalculo, Tipo, TipoRetorno, 12004, 13539) |
| `CalculoCarteira` | 144 | Mesma parede "Tipo de calculo nao enviado" com as mesmas variantes; provavel enum so no Add-In Excel |
| `FundosIndicadores` | 81 | Avancou um passo em 2026-06-10: o param `961` satisfaz a data e o servidor passa a exigir "Benchmark nao informado", mas nenhuma combinacao de nome/valor de tag testada satisfaz (Benchmark=, 13486=, variantes) |

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

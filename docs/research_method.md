# Research Method

[← Project homepage](../README.md)

<img src="../assets/readme/method-header.svg" width="100%" alt="Research method: data, timing, accounting, and evidence contract layers">

The method keeps local data, feature timing, simulated accounting, and evidence records connected from question to review.

## Workflow

<img src="../assets/readme/research-workflow.svg" width="100%" alt="Six-stage research workflow from question through deterministic evidence">

`QUESTION -> VALIDATE -> CONSTRUCT -> DIAGNOSE -> SIMULATE -> RECORD`

This is the target evidence lifecycle. Existing deterministic demos retain
their configured outputs, but the immutable all-trial ledger required for
formal campaigns is not implemented yet.

## Research contract

<img src="../assets/readme/research-contract.svg" width="100%" alt="Non-quantitative contract wheel for data, timing, accounting, and evidence">

- **Data:** local inputs with explicit schemas, provenance, validation, and date alignment.
- **Timing:** feature, signal, rebalance, and return-measurement dates remain distinct.
- **Accounting:** target weights, turnover, costs, slippage, and benchmark treatment remain visible.
- **Evidence:** configuration, assumptions, outputs, limitations, and review outcome travel together.

The wheel is qualitative; equal arcs indicate peer contract layers rather than measured proportions.

## System

<img src="../assets/readme/system-architecture.svg" width="100%" alt="Four-layer architecture from local inputs through transformations and simulated accounting to evidence">

| Layer | Repository paths | Responsibility |
| --- | --- | --- |
| Inputs | `src/data/` | Local CSV validation and aligned research panels |
| Transform | `src/features/` | Factors, preprocessing, diagnostics, and basic sample slicing |
| Account | `src/backtest/`, `src/risk/` | Current long-only selection/target construction, drift-aware holdings, signed trades, costs, metrics, and optional position caps |
| Evidence | `src/reporting/`, `research/`, `reports/` | Deterministic runs, Markdown reports, JSON logs, and registry views |

`src/strategies/` is placeholder-only; the charter requires a future strategy
layer to be evidenced separately from factors and portfolios. Tests and CI form
the software control plane. The `lean/` directory remains a metadata and
signal-contract scaffold.

## Accounting

| Contract | Current behavior |
| --- | --- |
| Signal availability | Default `signal_lag_periods=1` selects the previous available signal row |
| Return timing | Weights set on date `t` earn returns from the next available price row |
| Portfolio | Long-only equal-weight selection with an optional position cap and residual cash |
| Holdings | Post-trade weights on rebalance dates; drifted closing weights between rebalances |
| Trades | Signed target weights minus drifted pre-trade weights on rebalance dates |
| Turnover | Sum of absolute signed trades under the undivided convention |
| Costs | Fixed basis points on turnover, charged after returns and expressed on beginning-period return basis |
| Slippage | Fixed impact or reviewed exact-date precomputed impact with return-basis metadata |
| Tracking error | Annualized population volatility of aligned daily net strategy returns versus cost-free benchmark returns |
| Episode metrics | Completed positive-weight episodes with reconciled applied costs and explicit terminal-open counts |

## Controls

- Default signal lag, trailing calculations on caller-supplied data, and exact
  panel alignment. Formal point-in-time evidence remains blocked until the data
  methodology gate passes.
- Deterministic failure behavior for invalid or incomplete inputs.
- Optional long-only position caps applied before drift-aware trade calculation.
- Interpretation gates tied to provenance, universe, timing, benchmark, splits, costs, and limitations.

Active product aspiration and demo-first delivery principles are governed strictly by [North Star](north_star.md). Detailed research specifications and acceptance criteria live in [project specification](../PROJECT_SPEC.md). Program stage sequence, status, and the authoritative imperfection backlog are owned by the [canonical roadmap](current_roadmap.md). The [research program charter](research_program_charter.md) is preserved formal evidence policy (not an active product delivery blocker), and the [handoff](current_handoff.md) owns the latest recorded operational checkpoint.

## Evidence

<img src="../assets/readme/evidence-lifecycle.svg" width="100%" alt="Evidence lifecycle from hypothesis and configuration through reports, JSON logs, registry review, and retained outcomes">

Synthetic and committed-fixture evidence exercises implementation behavior and reproducibility. Real-data interpretation begins after the methodology fields and readiness gates have been reviewed.

## Verify

```bash
python -m pytest -q
python -m compileall src tests research
python -m compileall lean
git diff --check
```

## Records

[Project specification](../PROJECT_SPEC.md) · [Experiment contract](../EXPERIMENT_LOG.md) · [Risk evaluation design](risk_evaluation_metrics_design.md) · [Decision log](decision_log.md) · [Engineering log](engineering_log.md) · [Experiment registry](../reports/experiment_registry.md)

<img src="../assets/readme/method-footer.svg" width="100%" alt="Every result keeps its data, timing, accounting, and evidence assumptions">

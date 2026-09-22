# Milestone 4.5 Market Impact and Capacity Implementation

Date: 2026-09-22. Branch: `feat/m4-5-market-impact-capacity`.
Producer worktree: `/private/tmp/efr-m4-5-market-impact-capacity`.
Verified base: `fe851ba0a69be1416db265bee4375433ab45d52d`.
Accepted plan: `bd7a2c0ac8d4c3ce4d7f1bc7603b1e0da8869695`, coordinator
PASS with MATERIAL: 0. The accepted card is
[coord/card_m4_5_market_impact_capacity.md](../card_m4_5_market_impact_capacity.md).
The directive's different expanded `fe851ba` hash was corrected through live Git
verification and coordinator/owner confirmation before implementation.

## Delivered Behavior

M4.5 adds an optional daily square-root market-impact path to both portfolio
engines and a reproducible generated capacity experiment. The default path
preserves every previously exposed result field in the saved 124-book baseline.
An active model uses causal liquidity, explicit participation policies,
cash-funded buys, and dollar positions. Actual fills, deferred shares,
cancellations, slippage dollars, and forecast participation remain auditable.

`src/backtest/market_impact.py` owns the frozen model, typed refusals, complete
lagged liquidity windows, pure signed-dollar quote calculation, and shared
self-financing execution step. It uses existing NumPy, pandas, and standard
library dependencies. `portfolio.py` and `long_short.py` retain their target
construction and terminal-evidence boundaries and call that shared step only
when the optional model is supplied.

The public model defaults are eta=0.25, cap=0.10, fixed_bps=0, min_adv=100,000,
mode=`raise`, lookback=20, and penalty_bps=10. Both engines accept the model plus
explicit volume, price-basis, and volume-basis arguments. Model-free liquidity
arguments, mixed bases, simultaneous legacy slippage, and the long-only
precomputed impact overlay refuse ambiguous accounting.

For absolute dollars Q, ADV A, and daily sample volatility sigma, base dollar
cost is `Q * (fixed_bps/10000 + eta*sigma*sqrt(Q/A))`. The `raise` policy rejects
requests above cap*A before funding adjustments. `throttle` clips traded dollars
and carries signed shares. `penalize` adds the total dollar stress cost
`A*(penalty_bps/10000)*max((Q/A)/cap-1,0)^2`. Every quoted active request needs
finite ADV at least min_adv and finite nonnegative volatility. The minimum is
an admissibility cutoff. Zero requests consume zero cost and liquidity.

ADV averages matching-basis price times volume; volatility uses W complete
simple returns and ddof=1. Both windows end at the source row selected by the
positive signal lag. Full-source history supplies warm-up; post-evaluation
values remain outside estimation. Actual fills also require positive current
observed volume. Current volume provides only the declared feasibility veto.

The shared accounting step processes sells before a common cash-funded buy
scale. Sixty-four bisection iterations solve the monotone buy outlay, including
recomputed nonlinear impact and commission. Only liquidity shortfalls remain
queued. Funding shortfalls are cancelled. New targets replace old pending
shares; known ineligibility permits exposure reduction; terminal events cancel
remaining shares before a terminal quote is required. Long-only sell requests
are bounded by remaining positions, with any arithmetic excess recorded as
cancelled shares.

After returns and terminal settlement, `H_next=H+X`,
`cash_next=cash_pre-sum(X)-commission-slippage`, and
`equity_next=equity_pre-commission-slippage`. Existing return-cost fields divide
cost dollars by prior equity. Undivided turnover divides absolute executed
dollars by pretrade equity. Terminal redemption pays zero ordinary impact fee;
subsequent market reinvestment follows the impact policy. Finite cash, positive
equity, and cash-plus-position reconciliation are explicit guards.

Both result types expose `slippage_cost_series`, `realized_slippage_bps`,
`trade_participation_rates`, `executed_trade_values`, `pending_trade_shares`, and
`cancelled_trade_shares`. Active slippage dollars come directly from execution
accounting. Legacy dollar diagnostics derive from existing return-cost fields;
legacy nonzero-trade participation remains unavailable. The long-only timing
ledger identifies scheduled target attempts. The actual dollar-trade matrix
records deferred retries on all accounting rows.

## Baseline Preservation

Baseline capture ran before runtime edits against the verified M4.4 code. The
capture covers all existing dataclass fields, pandas public-cell hashes and
axes, timing metadata and ledger, assumptions, costs, holdings, cash, and
terminal evidence for 62 factors and 124 long-only/long-short books. It also
captures the trial family, PBO, weighting comparisons, M4.3 multiple-testing
summary, and M4.4 synthetic demo outputs. Only the six newly introduced fields
are excluded from the comparison.

Baseline and final-candidate JSON compare byte-for-byte equal. Their common
SHA-256 is:

```text
5a885b96e7379a83658047d4720d701f504f92838ffae10a76fa267580b61ed4
```

The preserved files are `/private/tmp/efr-m4-5-evidence/baseline.json` and
`candidate-final.json`. Capture elapsed times were 50.720 and 54.599 seconds;
the latter overlapped other validation jobs. These timings record local runs.
Hosted CI latency remains a separate measurement.

The committed replay script is
[m4_5_evidence/capture_baseline.py](m4_5_evidence/capture_baseline.py). Run it once
with `PYTHONPATH=src:.` from a detached worktree at the verified base, and once
from this feature branch, using the same interpreter and dependency versions:

```bash
PYTHONPATH=src:. python /path/to/candidate/coord/reports/m4_5_evidence/capture_baseline.py /tmp/baseline.json
PYTHONPATH=src:. python coord/reports/m4_5_evidence/capture_baseline.py /tmp/candidate.json
cmp /tmp/baseline.json /tmp/candidate.json
```

## Generated Capacity Evidence

The command `PYTHONPATH=src:. python -m research.market_impact_capacity_demo`
writes the [Markdown capacity report](../../reports/market_impact_capacity_demo.md),
JSON experiment record, and append-only attempt log. Reusable
`evaluate_capacity(...)` accepts explicitly supplied compatible cohort panels.
This delivery reads generated panels exclusively.

The declared experiment contains a 14-close/four-security hand panel and a
65-close/20-security synthetic cohort. Both engines run at $1M, $10M, $50M,
$100M, $500M, and $1B across the fixed-cost control and all three impact policies.
The 96 final scenarios retain 62 successful books and 34 typed refusals.
Thirty-eight successful books have negative net returns. Every refusal remains
an unavailable capacity endpoint.

The benchmark holds equal initial dollars across the declared roster and pays
zero benchmark cost. Net Sharpe, cumulative net and benchmark-excess returns,
weighted slippage bps, traded dollars, turnover, participation, final deferred
shares, cancellations, and realized exposure accompany per-row cash/equity
traces. All adjacent tested AUM intervals are classified in JSON. This grid has
zero positive-to-nonpositive excess-return brackets; capacity remains unresolved
by the grid. No empirical or interpolated break-even AUM is reported.

Three full runs produced 576 retained start/outcome events: 288 starts,
181 successful outcomes, 102 refusals, and five initial failures. The first run
exposed tiny negative long-only positions when floating-point deferred-share
valuation slightly exceeded a remaining long position. Bounding long-only sells
and recording excess-share cancellation closed that regression. The changing-
price cohort test and the sell-bound negative ablation preserve its evidence.
The final two full runs each retain 62 successes and 34 refusals.

## Verification

The supplied shared environment uses CPython 3.12.13, NumPy 2.5.3, pandas 3.0.6,
SciPy 1.18.1, pytest 9.1.1, pytest-xdist 3.8.0, and Ruff 0.16.8. Every test command
uses the worktree source through `PYTHONPATH=src:.`. Native thread limits are 1;
full lanes use two worksteal workers and `--max-worker-restart=0`.

| Gate | Result |
| --- | --- |
| New impact, engine, and capacity tests | 113 deterministic tests |
| Targeted impact plus project-structure suite | 179 passed in 3.17 seconds |
| Full core lane | 4,116 passed, 2 inherited platform skips in 28.02 seconds |
| Full diagnostics lane | 125 passed in 90.21 seconds |
| Combined lane coverage | 4,241 passed, 2 platform skips |
| Repository Ruff | PASS |
| compileall: src, tests, research, lean, evidence scripts | PASS |
| Distribution build | sdist and wheel built successfully |
| Package contents | impact module included; all 20 ledger JSON/hash files match source |
| Repository map | regenerated; canonical freshness test passes |
| Baseline replay | exact byte equality and matching SHA-256 |
| Isolated ablation | intact baseline passes; all 15 removals trigger failures |

The initial core run had one stale-map failure after new files were added.
Regeneration closed that failure; the complete core lane was rerun. Existing
platform longdouble precision skips and constant-input correlation warnings
remain visible. The implementation uses no test skips or dependency changes.
Hosted Python 3.11 CI and fresh independent review remain the coordinator's
next gates.

## Ablation Coverage and Outcome

The committed driver
[m4_5_evidence/ablate.py](m4_5_evidence/ablate.py) copies the backtest package into
separate directories, verifies the imported module path, applies one removal
per copy, and runs its named counterexample. Original source hashes remain
unchanged. Reproduce with a fresh output directory:

```bash
PYTHONPATH=src:. python coord/reports/m4_5_evidence/ablate.py /tmp/m4-5-ablation-replay
```

| Runtime boundary | Removal or counterexample | Outcome |
| --- | --- | --- |
| Causal liquidity | remove both estimator lags | lag/window oracle fails |
| Basis compatibility | remove matching-basis guard | invalid-basis refusal tests fail |
| ADV admissibility | remove the minimum/finite ADV guard | invalid-liquidity tests fail |
| Daily volatility | replace sample ddof=1 with ddof=0 | scalar volatility oracle fails |
| Participation refusal | remove `raise` cap | over-cap refusal test fails |
| Partial fills | remove throttle clipping | executed and deferred dollar oracle fails |
| Excess-volume policy | remove penalize branch | quadratic-cost oracle fails |
| Square-root coefficient | remove eta term | independent scalar-cost oracle fails |
| Fixed component | remove fixed-bps term | independent scalar-cost oracle fails |
| Penalty coefficient | remove penalty-bps term | excess-dollar oracle fails |
| Self-financing buys | remove cash funding | independent root/cash oracle fails |
| Cash reconciliation | remove balance guard | inconsistent input balance test fails |
| Current fill feasibility | remove observed-volume veto | zero/missing volume refusal tests fail |
| Terminal fee exemption | retain terminal positions as market legs in both engines | terminal-price/exemption integration tests fail |
| Long-only position boundary | allow deferred sell overshoot | changing-price synthetic cohort fails |

The isolated intact baseline passes 113 tests. Each negative copy exits with
pytest status 1 through a demonstrated counterexample. All 15 runtime elements
are retained. The design excludes an intraday simulator, a borrow engine,
automatic calibration, and a general event framework. The implementation uses
one shared execution step and two small result/assumption helpers. This
supported no-removal outcome covers the M4.5 additions. Earlier subsystems
receive regression coverage through both full CI lanes and the saved baseline;
this report makes no whole-project ablation-completion claim.

## Limits and Handoff

The square-root function and quadratic penalty are declared diagnostic
scenarios. Source studies identify regime dependence and different fitted
exponents; the accepted card links the primary research. Actual strategy
capacity and empirical eta remain unmeasured.

Target caps and long-short neutrality apply to frozen targets. Partial fills,
price drift, and cost-funded execution can change actual exposures. Forecast
participation uses lagged ADV. The cancellation matrix aggregates signed shares
per row/asset; opposing cancellations can offset. Final deferred shares remain
unfinished simulation state. Borrow fees, recalls, intraday fills, corporate-
action conversion of pending shares, and vendor basis verification remain open.
The complete timing/accounting supplement and roadmap record these limits.

Source hashes, artifact hashes, disjoint lane counts, environment versions, and
ablation results are recorded in
[m4_5_evidence/validation.json](m4_5_evidence/validation.json). Detailed local logs
remain in `/private/tmp/efr-m4-5-evidence`. The `.venv` symlink and untracked owner
directive are preserved outside the candidate commit. The frozen commit is
handed to coordinator `w3:pE8` for the owner-directed independent GPT-6 Astra
High Fast review on a clean detached worktree. Independent review and hosted
CI remain pending at producer delivery.

# M4.5: Causal Square-Root Impact and Capacity Diagnostics

Date: 2026-09-22. Executor: GPT-6 Astra, extra-high reasoning, Fast.
Verified base: `fe851ba0a69be1416db265bee4375433ab45d52d` (PR #253).
Branch: `feat/m4-5-market-impact-capacity`.
Worktree: `/private/tmp/efr-m4-5-market-impact-capacity`.
Report: `coord/reports/m4_5_market_impact_capacity_impl.md`.
Structural: true, `SCHEMA_PROTOCOL_CONTRACT`; lane: CRITICAL.
The owner authorizes immediate autonomous design/implementation and one fresh
independent GPT-6 Astra High Fast review after candidate delivery. The coordinator
owns acceptance, reviewer dispatch, and protected publication. This card records
the verified Git base; the directive's expanded base digest has a transcription
mismatch. The supplied `.venv` symlink and directive are preserved tooling inputs.

## Objective and preserved baseline

Deliver one generated-data thread from compatible daily price/volume panels,
through causal liquidity estimates and simulated market costs, to both portfolio
engines and an all-attempt capacity comparison. Implement `throttle`, `penalize`,
and `raise` participation policies. Keep the complete M4.4 calculation path when
`impact_model=None`, including terminal accounting and event evidence.

The current engines use post-return turnover and postcost target-weight resets.
The opt-in impact path instead retains dollar positions while paying fees from
cash. This explicit opt-in accounting extension makes partial execution and
cash debits reconcile. Existing event-free calls retain their original arithmetic.

Capture the default 62-factor/124-book diagnostic before editing runtime code,
including existing arrays, metrics, assumptions, timing metadata/ledger, M4.4 cash
and event fields, DSR/PBO, trial family, weighting comparisons, multiple-testing
summary, and the six-case PIT demo. Hash and compare the same capture afterward.
Only newly introduced M4.5 result fields fall outside the legacy comparison.

## Public model and liquidity interface

Add `src/backtest/market_impact.py`, using existing NumPy/pandas dependencies:

```python
@dataclass(frozen=True)
class SquareRootImpactModel:
    eta: float = 0.25
    max_participation_rate: float = 0.10
    fixed_bps: float = 0.0
    min_adv: float = 1e5
    mode: Literal["throttle", "penalize", "raise"] = "raise"
    lookback: int = 20
    penalty_bps: float = 10.0

def prepare_market_liquidity(
    prices: pd.DataFrame, volumes: pd.DataFrame, *,
    price_basis: str, volume_basis: str,
    model: SquareRootImpactModel, signal_lag_periods: int,
) -> MarketLiquidity: ...

def calculate_market_impact(
    trade_values: pd.Series, adv: pd.Series, daily_volatility: pd.Series, *,
    model: SquareRootImpactModel,
) -> pd.DataFrame: ...
```

`MarketLiquidity` is a small immutable container for execution-indexed dollar
ADV, daily volatility, and observed volume panels. A narrow shared execution
function consumes one row, current dollar holdings/cash, a new target or pending
share quantities, current prices, eligibility and settled IDs. Its result records
actual dollar trades, costs, cash, pending shares, and cancelled shares. These
value containers support the two engines without a schema registry or event bus.

Both engines add `impact_model=None`, `impact_volumes=None`,
`impact_price_basis=None`, and `impact_volume_basis=None`. Active impact requires
all declared liquidity inputs, strict held-price policy, zero legacy
`slippage_bps`, and no precomputed volume-impact overlay. Existing transaction
commission remains additive. Liquidity arguments without a model refuse ambiguous
ownership. Basis declarations accept matching `raw`/`raw` or
`split_adjusted`/`split_adjusted`; incompatible and total-return/volume pairs refuse.
The declarations express caller evidence and confer no vendor certification.

Require exact, unique, ordered price/volume axes and real non-Boolean cells.
Known missing or invalid cells propagate unavailable rolling estimates; a nonzero
requested trade requires a complete admissible liquidity window. Zero-volume
observations remain in the window. A zero-trade quote has zero cost and zero
participation, with no demand for unused liquidity values. Nonzero actual fills
require a finite positive execution price and positive observed execution volume.
Execution-volume feasibility supplies a refusal and supplies no target reranking.
Values after the evaluation end remain outside the estimation input slice.

For lookback `W` and execution row `a[j]`, estimates end at `a[j-L]`, using full
source history for warm-up and the engine's bounded lag for the first executable
signal. Dollar ADV is the arithmetic mean of `P*V` over `W` source rows. Daily
volatility is the sample standard deviation (`ddof=1`) of `W` simple one-row
returns, computed with `pct_change(fill_method=None)`. Volatility has daily units;
annualization enters reporting only. Every constituent price in a used return
window must be finite and positive; volume must be finite and nonnegative.

`min_adv` is a minimum admissible ADV, so values below it refuse nonzero trades.
This preserves observed liquidity instead of replacing zero/small ADV with an
artificial floor. Zero daily volatility is a valid estimate. Model coefficients
must be finite real non-Boolean values: eta/fixed/penalty >= 0, min_adv > 0,
0 < participation cap <= 1, integer lookback >= 2. Lag is a positive integer.
Overflow and non-finite costs raise typed `MarketImpactValidationError` reasons.

## Cost mathematics and participation policies

For signed requested dollars `D`, admissible ADV `A`, daily volatility `sigma`,
and cap `c`, let `Q=abs(D)` and `p=Q/A`.

Base modeled average execution-cost rate and dollar cost:

```
s = fixed_bps / 10000 + eta * sigma * sqrt(p)
C_base = Q * s
```

The coefficient eta absorbs the distinction between average execution cost and
peak price displacement. It remains a declared scenario parameter.

- `raise`: refuse a request with `p > c` before cash funding; otherwise quote
  the complete requested trade.
- `throttle`: quote signed dollars `sign(D)*min(Q,c*A)` and preserve the
  liquidity-deferred remainder. Cost uses the executed fraction's participation.
- `penalize`: preserve the full liquidity-requested trade. Add the explicit
  convex excess-volume stress cost
  `C_excess = A * (penalty_bps/10000) * max(p/c - 1, 0)**2`.
  This is a scenario penalty outside the square-root empirical approximation.

The quote frame exposes signed requested/executable/remaining trade value,
participation, and dollar slippage. Buy and sell costs are symmetric in absolute
notional. All modes apply the separate cash-funding rule below. The participation
reported is relative to lagged ADV, a daily liquidity forecast; it supplies no
claim about realized market-wide volume participation or intraday scheduling.

## Dollar accounting, funding, and residual execution

Preserve the existing order: held returns, gross solvency check, drift, evidenced
terminal cash settlement, market trades, costs, postcost solvency, holdings.
For incoming equity `E`, return multiplier `G`, post-return surviving dollar
positions `H`, and cash `K` (including terminal proceeds):

1. A scheduled target `t` requests dollar changes `D=t*(E*G)-H`. Its selection
   and weighting retain the lagged signal/membership contract. A new target
   supersedes prior pending shares and records their cancellation.
2. Off-schedule execution in throttle mode retries the remaining signed share
   quantities at the current close. Share quantities preserve an unfinished
   parent order through ordinary price changes. Current known eligibility allows
   exposure-reducing exits and cancels ineligible exposure increases. Terminal
   settlement cancels that identity's pending shares. A fresh frozen target that
   requires a settled identity retains M4.4's typed collision refusal.
3. Apply the chosen participation policy. Execute admissible sells first for
   cash accounting. Deduct their commission and modeled slippage. Insufficient
   cash to pay the sell costs refuses the row; the model supplies no borrowing.
4. Apply a single common scale in [0,1] to the quoted buys when their total price
   plus commission/slippage exceeds available cash. A bounded monotone bisection
   chooses a feasible scale. Recompute nonlinear impact for those actual buys.
   This cash-reserve policy preserves ranking and relative buy proportions.
   Cash-funding reductions are recorded cancellations; only liquidity-throttled
   shares carry to later rows. Thus full-trade policies retain their participation
   meaning while all modes share an explicit self-financing constraint.
5. With actual signed dollar trades `X`, commission `F`, and impact/slippage `C`:
   `E_next=E*G-F-C`, `K_next=K-sum(X)-F-C`, and
   `w_next=(H+X)/E_next`. Validate finite positive equity and finite feasible cash.
   Turnover is `sum(abs(X))/(E*G)`, with the existing undivided convention.
   Existing return-cost fields record `F/E` and `C/E`. Cash pays costs directly;
   surviving positions preserve their quantities between market trades.

Target position caps and long-short neutrality remain target-construction rules.
Partial fills and price drift can create different observed exposures; disclose
those exposures and pending quantities. The impact path retains no automatic
borrow/hedging engine. Terminal cash redemption pays zero market-impact fee and
contributes zero market turnover; subsequent ordinary reinvestment pays costs.
A final-row residual remains visible as pending shares with its simulated end
state. Corporate-action share conversion requires a separate contract; callers
supply consistent price/volume units within the simulated source panel.

Extend both result types with:

- `slippage_cost_series`: dollar slippage, including the impact model's fixed
  component and excess penalty; commissions remain separate.
- `realized_slippage_bps`: `10000*slippage_dollars/sum(abs(actual_trade_dollars))`,
  zero on zero-trade rows.
- `trade_participation_rates`: actual absolute dollar trades divided by lagged
  ADV; unused rows/cells are zero. Legacy nonzero trades have unavailable rates.
- `executed_trade_values`: signed market-trade dollars.
- `pending_trade_shares`: liquidity-deferred signed shares after each row.
- `cancelled_trade_shares`: signed cancellations from replacement, eligibility,
  terminal events, and cash funding.

Legacy slippage-dollar/rate diagnostics derive from existing return costs and
trade turnover. Legacy cash and all existing public fields retain exact values.

## Capacity demonstration and evidence ceiling

Add `research/market_impact_capacity_demo.py`. Supply reusable capacity evaluation
for caller-provided compatible cohort panels and run generated fixtures only in
this delivery: a small hand-checkable panel and a predeclared synthetic cohort.
Run both engines over AUM tiers 1M, 10M, 50M, 100M, 500M, and 1B. Retain every
attempt, including participation refusals, insolvent/invalid cases, and negative
returns. Include fixed-cost controls and all three participation policies.

Write Markdown and JSON with net Sharpe, net/benchmark-relative return, weighted
realized slippage bps, traded notional, participation, deferred/cancelled shares,
model assumptions, and evidence status. Report every adjacent tested AUM bracket
where benchmark-relative return changes sign. A refusal yields unavailable
capacity; an unobserved crossing remains unresolved by this grid. The report
makes no unique, interpolated, or empirical break-even-AUM claim. Sharpe uses
existing 252-day reporting; the benchmark and gross/net comparison are explicit.
No private cohort file is opened as part of this implementation.

## Acceptance and isolated ablation

Use independent scalar cost/funding oracles and deterministic engine tests for
zero/tiny/extreme trades, buy/sell symmetry, zero/invalid/low ADV, zero and extreme
volatility, coefficient validation, matching bases, warm-up, lag and future-data
prefix invariance, all three participation modes, and cost insolvency.

Test current zero-volume refusal, shared cash conservation, post-return cost
normalization, cash-funded initial investment, long-short partial exposures,
residual continuation at changing prices, target replacement, eligibility and
terminal cancellation, terminal fee exemption, final pending shares, and both
engines' exact model-absent baseline. Cover empty/duplicate/named/mixed axes at
accepted public boundaries, JSON/report parity, and all-attempt failure retention.

Run complete core/diagnostics CI lanes, Ruff, compileall, build, map freshness,
and baseline comparison. Preserve baseline and mutate isolated copies: remove
lagging, basis checks, ADV/refusal guards, each participation policy, eta/fixed/
penalty cost terms, cash funding, and terminal exclusion. Preserve counterexamples
and necessary guards. Design ablation excludes intraday fill simulation, a borrow
model, automatic calibration, private-data execution, and a general event engine.
Record justified simplifications or a supported no-change outcome.

Update the timing/accounting contract additively, roadmap limitations, engineering
log and repository map. Freeze a clean tracked candidate and evidence manifest,
then notify coordinator `w3:pE8` for the owner-directed single-seat review.

## Research grounding and limits

[Bucci et al., Crossover from linear to square-root market impact](https://arxiv.org/abs/1811.05230)
find regime-dependent impact behavior. [Almgren et al., Direct Estimation of
Equity Market Impact](https://www.cis.upenn.edu/~mkearns/finread/costestim.pdf)
fit a 3/5 temporary-impact exponent in their sample. The owner-selected square-
root function is a transparent diagnostic approximation with explicit scenario
coefficients. Calibration, intraday execution evidence, actual capacity, and
formal real-data promotion remain separate evidence gates.

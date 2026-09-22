# M4.4: Dynamic PIT Universe and Explicit Terminal Cash Settlement

Date: 2026-09-21. Author/executor: GPT-6 Astra, extra-high reasoning, Fast.
Base: `37437df765155b902566dc41e60e0d314355ec3d` (merged M4.3).
Branch: `feat/m4-4-pit-universe-delisting`.
Worktree: `/private/tmp/efr-m4-4-pit-universe-delisting`.
Report: `coord/reports/m4_4_pit_universe_delisting_impl.md`.
Lane: CRITICAL. Structural: true, reason `SCHEMA_PROTOCOL_CONTRACT`: the new
terminal-event input and cash-settlement semantics span both portfolio engines.
The owner's current directive authorizes autonomous implementation and one fresh
independent GPT-6 Astra extra-high Fast review of the frozen candidate. The
coordinator records acceptance and the explicit single-seat override.

## Objective and baseline

Deliver a synthetic end-to-end thread from an identity-backed constituent table
through causal eligibility, long-only/long-short holdings, terminal return and
cash settlement, to an auditable comparison report. Preserve legacy behavior
when the new inputs are absent. Existing ticker reuse checks, held-price
refusals, target freezing, turnover arithmetic, and insolvency guards remain
required boundaries.

The existing constituent loader validates effective intervals and permanent
IDs. Its legacy mask supplies effective-date membership; announcement
availability remains a caller responsibility. Both engines already accept an
execution-indexed `universe_mask`. Held missing prices currently refuse under
the strict policy. M4.4 adds explicit availability and terminal evidence to this
working foundation. Private-data execution, SEC collection, successor-stock
exchanges, receivable valuation, and formal universe-promotion evidence remain
separate work.

## Membership and identity contract

Add `build_pit_membership_mask(intervals, dates, assets, *,
signal_lag_periods=1) -> pd.DataFrame` in `src/data/constituent_table.py`.
Accept the existing validated wrapper or a DataFrame. Required columns:

| Field | Meaning |
| --- | --- |
| symbol | Historical display alias |
| permanent_id | Stable security identity; exact price/signal column key |
| start_date | Effective inclusive membership start |
| end_date | Effective exclusive membership end; null for open record |
| start_known_at | Conservative source-close label at which the entry was knowable |
| end_known_at | Conservative source-close label at which the closure was knowable; null only with an open end |

The daily source-close label is a declared simulation boundary. Callers assign
availability conservatively from publication, delivery, and revision evidence.
The parser preserves timestamps and refuses intraday or timezone-bearing values
for this date-label interface. It supplies no automatic timestamp truncation,
calendar repair, or formal source-availability certification. The existing CSV
loader preserves the optional two availability columns for this new boundary.

For execution row a[j], the knowledge cutoff is a[j-lag] within the bounded
accounting index. Early rows without such a cutoff are ineligible. A scheduled
entry is eligible when start_date<=a[j] and start_known_at<=cutoff. A scheduled
closure excludes the asset only when end_date<=a[j] and end_known_at<=cutoff.
This is an execution-date query of the schedule known at the frozen decision
time. Future announcements and later-known closure revisions never modify an
earlier decision. Empty eligible rows produce cash targets at scheduled resets.

Require complete nonempty string IDs, unique price axes, chronological unique
dates, valid half-open intervals, and the existing ticker/identity overlap
rules. Every supplied asset must have identity-backed interval evidence.
Ticker-only axes against permanent-ID intervals refuse. Reused tickers map to
distinct permanent-ID columns; return arithmetic remains within each column.
Membership deletion alone leaves a held position valued until its ordinary
scheduled exit or an explicit terminal settlement.

## Terminal-event contract

Both backtest APIs add optional `constituent_intervals=None` and
`terminal_events: pd.DataFrame | None = None`. An explicit constituent table and
legacy `universe_mask` together refuse ambiguous ownership. Terminal events use:

| Field | Meaning |
| --- | --- |
| event_id | Unique nonempty evidence/event identifier |
| permanent_id | Exact security column to settle |
| effective_date | Source-row close at which final cash settles |
| known_at | Source-close label by which the settlement terms are available |
| reference_date | Immediately preceding full-source accounting row |
| terminal_return | Complete return from the reference close to final cash, finite and >=-1 |
| return_basis | Literal `prior_observed_close_to_cash` |

Every supplied security has at most one terminal event. Events and assets must
match the provided source panel; duplicate IDs, unknown assets, off-calendar
effective/reference dates, missing evidence, wrong return basis, nonfinite
returns, and returns below -1 refuse. known_at<=effective_date is required.
An event on the first full-source row lacks its required reference and refuses.
The reference price for a held terminal security must remain finite and positive.
The event return uses the same units and adjustment basis as that price panel;
the literal basis is the caller's explicit complete-window declaration.

The terminal return replaces the incoming price return for that security on
the effective row. It already includes any final market move and settlement
adjustment. Combining separate market and delisting legs requires the caller
to supply (1+r_market)(1+r_delist)-1. The engine applies this complete return
once and adds no separate dividend overlay. Event-date quoted prices can remain
missing; ordinary missing-price guards continue to protect all other held legs.
PIT mode requires `missing_price_policy="raise"`.

The event's known schedule can exclude new targets when known_at<=decision
cutoff and effective_date<=execution date. Payoff magnitude supplies accounting
only. An unexpected event that collides with a nonzero frozen target refuses
execution; the engine preserves target-freezing semantics. Settled securities
remain unavailable for reopening under the same permanent ID.

## Accounting order and outputs

For previous equity E, signed held weight w_i, and terminal return r_i:

1. Resolve held returns, substituting r_i only for the explicitly evidenced
   event. Portfolio gross multiplier is G=1+sum_i(w_i*r_i).
2. Apply existing positive-equity and finite-value guards. Compute drifted
   pretrade weights w_i*(1+r_i)/G.
3. Credit signed terminal cash C_i=E*w_i*(1+r_i), then set that security's
   holding to zero. Positive long proceeds increase cash; a short settlement
   pays the liability. An explicit r_i=-1 permits zero proceeds, subject to
   the existing portfolio-insolvency refusal.
4. Apply any scheduled frozen target against the surviving pretrade holdings.
   Ordinary market trades retain existing execution-price checks and fixed-bps
   turnover/cost calculations. Terminal redemption is an exogenous cash event
   with separately reported flows and zero additional modeled settlement fees.
5. Compute net equity under the existing target-weight reset convention and
   expose cash as equity*(1-sum(signed closing holdings)). Between resets,
   surviving holdings drift and terminal cash remains cash. Long-short target
   neutrality applies at feasible scheduled resets; forced settlement can leave
   exposure between resets.

Extend both result dataclasses with `cash_balance: pd.Series`,
`terminal_cashflows: pd.DataFrame`, and `terminal_event_log: tuple[dict, ...]`.
The event log retains event identity, dates, basis, return, incoming weight,
and signed proceeds, including zero-holding events in the bounded window.
Ordinary turnover excludes terminal cash redemption. Holding-episode detection
uses the closing holding transition and receives the explicit terminal return;
episode results must reconcile without inventing a market trade.

Use narrow shared helpers in the existing portfolio module for terminal input
validation, known-schedule eligibility, and event evidence. The long-short engine
already imports shared validation/accounting helpers from that module. Preserve
the current vectorized ordinary-return path for event-free rows. Avoid a new
event-engine hierarchy, schema registry, or execution adapter.

## Walking-skeleton report

Add `research/pit_universe_delisting_demo.py` with deterministic synthetic
permanent-ID prices, display-ticker reuse, membership announcements, additions,
removals, and a cash terminal event. Write `reports/pit_universe_delisting_demo.md`
and machine-readable synthetic evidence through the existing report/log patterns.
Compare an explicitly labeled static-universe diagnostic with the PIT schedule,
using the same evidenced settlement in each valid run. Retain a missing-terminal
evidence refusal as a negative case. Show equity, cash, terminal proceeds,
holdings, timing cutoffs, and input assumptions. Every attempted case is retained.
Existing private/static-cohort reports remain historical artifacts.

## Deterministic acceptance and ablation

- PIT-005: ticker reuse without IDs refuses; old/new identities remain separate
  columns; same-ID reentry follows valid intervals; alias overlap and mismatched
  ticker/ID axes refuse.
- Membership: preannounced versus late additions/deletions, lag 1 and lag 2,
  bounded initialization, gapped observed calendar, empty eligible universe,
  duplicate/named/mixed identity axes, malformed dates and missing availability.
  Mutating records known after a decision cutoff preserves all prior targets.
- PIT-006: hand-computed long and short terminal payoffs, positive/negative
  terminal returns, explicit zero proceeds, multiple simultaneous events,
  event on final bounded row, events outside the evaluation window, one-time
  settlement, absent current quote, missing prior quote, unavailable settlement
  terms, duplicate event and mismatched reference/basis refusals.
- Accounting: cash plus signed asset value equals equity; off-rebalance terminal
  cash persists; no post-event reentry; costs and surviving holdings follow
  existing drift and reset equations; terminal payoff and ordinary price return
  avoid double counting; insolvency remains a typed refusal.
- Causality: future event amount changes preserve preceding decisions and P&L;
  late event information preserves earlier masks; unexpected frozen-target
  collisions refuse. No extrapolated terminal quote repairs the input panel.
- Baseline: capture default M4.3 synthetic portfolio outputs and compare all
  existing public values, DSR/PBO, and diagnostics with new arguments absent.
  Validate the additional zero-flow and residual-cash outputs separately.
- Run focused tests, both complete CI lanes, Ruff, compile, build, map freshness,
  and whitespace checks. Retain exact candidate/source identities and results.
- Design ablation removes a generalized corporate-action engine and payment-lag
  receivable model. The single complete-window cash event supports the requested
  minimal thread. Implementation ablation preserves baseline copies, removes
  one proposed guard/helper at a time, tests behavioral/cost effects, retains
  demonstrated simplifications, and restores any correctness regression.

Update the roadmap's relevant identity/terminal backlog entries, engineering
log, repository map, and a focused additive timing-contract note for these
optional inputs. Record current implementation evidence and outstanding limits
in the implementation report, freeze the commit, and hand it to the coordinator
for the owner's single-seat GPT review and protected same-change lifecycle.

## References and limits

- `docs/signal_execution_timing_contract.md`: bounded lagged decision and
  after-close/next-observed-close accounting; execution feasibility preserves
  frozen targets.
- `docs/point_in_time_data_methodology_contract.md`: permanent identities,
  knowability versus effective time, and explicit terminal-value evidence.
- [CRSP aggregate-return flags](https://www.crsp.org/wp-content/uploads/appendix/FlagType_AR.html)
  distinguish compounded returns incorporating appropriate delisting returns.
- [MSCI index announcements](https://app2.msci.com/webapp/index_ann/Announcement?doc_type=ANNOUNCEMENT&format=html&lang=en&prod_type=STANDARD&visibility=public)
  distinguish announcement and effective dates.

This bounded implementation records synthetic conformance for immediate cash
settlement. Multi-session unpriced receivables, future-discovered bankruptcy
recoveries, stock/mixed consideration, full revision-vintage selection, source
calendar certification, and real-data formal promotion retain separate gates.

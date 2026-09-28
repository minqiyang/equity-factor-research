# North Star

Updated: 2026-09-28 after the owner's North Star v2 decision (`docs/decision_log.md`).

Canonical responsibility: active product aspiration, core research question,
objective, decision rule, and research versus execution boundaries.

Repository authority is [AGENTS.md](../AGENTS.md), workflow behavior is owned
by the [controller](codex_long_running_controller.md), operational status is
in the [current handoff](current_handoff.md), and stage sequences are in the
[current roadmap](current_roadmap.md).

## North Star

Build an automated stock selector for US equities that aims to beat an index
fund over the long term after trading costs, with smaller drawdowns. Profit is
the aim and carries no guarantee.

This repository is the research and simulation phase. It stays simulated,
reproducible, and auditable, and it places no orders. Paper trading, broker
integrations, credentials, order routing, and live risk controls belong to a
future, separately authorized execution system (Milestone 6).

## Core Question

Which factors earn more, or lose less, in which market conditions?

A factor is a simple scoring rule for stocks, such as "recent winners" or "low
volatility". The program answers the question in three layers:

1. **Collect** as many published factors as possible from academic libraries,
   factor-sharing sites, and broker research, in one catalog.
2. **Screen** every factor with one standard backtest and keep every result.
3. **Time** factors: measure each factor's return and drawdown by market
   condition on long public histories, and turn the findings into a monthly rule
   that uses past data only.

## Objective And Benchmark

- **Objective metric:** net-of-cost return and maximum drawdown of the selected
  portfolio, compared with three baselines: SPY, the equal-weight point-in-time
  universe, and an equal-weight mix of all screened factors.
- **Expectation:** published evidence finds that simple factor timing adds about
  0 to 2 percentage points a year before costs, that holding all factors equally
  is hard to beat, and that risk is more predictable than return. The drawdown
  half of the objective is the more promising half.
- **Implementable check:** a result on public factor-return series stays a
  diagnostic until the same rule holds on the repository's own point-in-time
  S&P 500 books after costs, or on tradable factor ETFs.

## Decision Rule

- Each line of work declares, before any result, its trial family, its number of
  looks, and its decision metric (net return or drawdown difference against the
  equal-weight baseline, with a confidence interval and a Benjamini–Yekutieli
  correction across the family).
- "No detectable edge at this data size" is a valid result that closes that line
  of work. After an underpowered null, the next step may be new factors, new
  data, or a new question; history extension is one option among these.
- A frozen shortlist is confirmed on months its screen never used and then on
  forward months before any separately authorized paper or live evaluation.

## Guards Against Fake Backtest Profits

Invariants R1–R12 in [AGENTS.md](../AGENTS.md#research-safety-invariants) are the
guards: no look-ahead, point-in-time membership, no stitched identities, a
side-aware adverse rule for disappearing stocks, one total-return basis, no
silent data repair, matching price and volume bases, real costs, every trial
kept and corrected for, honest claims, private data kept private, and
simulation only. They never defer.

## Speed Rule

Work that cannot change a result or a decision in the current step waits.
Non-blocking imperfections go to the lightweight backlog in
[docs/current_roadmap.md#imperfection-policy-and-lightweight-backlog](current_roadmap.md#imperfection-policy-and-lightweight-backlog).

## Primary Milestones

The program follows six primary milestones, from the research engine to factor
timing and a separately authorized execution system. Stage sequence,
dependencies, completion criteria, and status are owned by
[docs/current_roadmap.md#primary-milestones](current_roadmap.md#primary-milestones).
Every attempted run keeps its outcome, including failures.

## Relationship to the Historical Research Charter

The historical research charter ([docs/research_program_charter.md](research_program_charter.md))
remains preserved as hash-pinned formal evidence history. Active work follows this
North Star and the invariants in `AGENTS.md`.

# North Star

Updated: 2026-09-28 after the owner's North Star v2 decision (`docs/decision_log.md`).

Canonical responsibility: active product aspiration, core research question,
objective, decision rule, and research versus execution boundaries.

Repository authority is [AGENTS.md](../AGENTS.md), workflow behavior is owned
by the [controller](codex_long_running_controller.md), operational status is
in the [current handoff](current_handoff.md), and stage sequences are in the
[current roadmap](current_roadmap.md).

## North Star

Build an automated US stock selector that learns which classes of factors, grouped
by shared traits such as theme, data source, trading speed, and risk profile, earn
more or lose less in market conditions visible at the time. Each month it decides
how much to hold of each class, using only information known then, and turns that
into a long-only portfolio of US large-cap stocks. It aims to beat an index fund
and a cheap factor-ETF blend after costs over the long term. Risk control comes
first; losing years are expected, and profit carries no guarantee.

This repository is the research and simulation phase. It stays simulated,
reproducible, and auditable, and it places no orders. Paper trading, broker
integrations, credentials, order routing, and live risk controls belong to a
future, separately authorized execution system (Milestone 6) that starts after a
forward-observation period.

## Core Question

Which classes of factors earn more, or lose less, in which market conditions
visible at the time, and does acting on that knowledge beat holding every class,
balanced by risk?

A factor is a simple scoring rule for stocks, such as "recent winners" or "low
volatility". A factor class groups factors by shared traits. A market condition is
a state known at decision time, such as the market's trailing trend, its recent
volatility, or credit stress. The system has three layers:

1. **Baseline.** Hold every factor class, sized by forecast risk. It is a working
   product on its own.
2. **Timing.** A few questions, declared before any result, test whether market
   conditions and factor traits improve on the baseline after costs.
3. **Discovery.** New factor candidates come from traits that survive. They enter
   only through a counted search that must beat random data mining on data it
   never saw.

Factors are collected broadly from academic libraries, factor-sharing sites, and
broker research into one catalog; cataloguing needs no review.

## Objective And Benchmark

- **Objective metric:** net-of-cost return and maximum drawdown of the long-only
  large-cap portfolio, compared with an index fund (SPY), a cheap factor-ETF
  blend, the equal-weight point-in-time universe, and the risk-balanced
  all-class baseline.
- **Risk first:** risk forecasts are reported before return forecasts. Published
  evidence and the 2026-09-28 public-data probe find factor risk predictable and
  stable, and conditional factor returns weak and unstable
  (`coord/reports/north_star_vision_assessment_opus.md`).
- **Expectation:** the central case is net returns close to the index with a
  smoother path; the good case is a low single-digit excess over SPY before tax.
  A long-only stock portfolio still takes the market's crashes.
- **Implementable check:** results on public long-short factor series stay
  diagnostics until the same rule holds on the repository's own point-in-time
  S&P 500 books after costs.

## Decision Rule

- Each line of work declares, before any result, its trial family, its number of
  looks, and its decision metric (net return or drawdown difference against the
  risk-balanced baseline, with a confidence interval, a Benjamini–Yekutieli
  correction across the family, and a random-date null for state effects).
- A conditional result must hold in both halves of history and after
  publication; a market state with fewer than 10 episodes supports description
  only.
- "Holding all classes, balanced by risk, is best" and "no detectable edge at this
  data size" are valid results that close a line of work. After a null, the next
  step may be new factors, new data, or a new question.
- A frozen strategy is confirmed on months its research never used and then on
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

The program follows six primary milestones, from the research engine to the
factor-class allocator and a separately authorized execution system. Stage sequence,
dependencies, completion criteria, and status are owned by
[docs/current_roadmap.md#primary-milestones](current_roadmap.md#primary-milestones).
Every attempted run keeps its outcome, including failures.

## Relationship to the Historical Research Charter

The historical research charter ([docs/research_program_charter.md](research_program_charter.md))
remains preserved as hash-pinned formal evidence history. Active work follows this
North Star and the invariants in `AGENTS.md`.

# North Star and Demo-First Delivery

Updated: 2026-09-23

Canonical responsibility: active product aspiration, delivery methodology,
and research versus execution boundaries.

Repository authority is [AGENTS.md](../AGENTS.md), workflow behavior is owned
by the [controller](codex_long_running_controller.md), operational status is
in the [current handoff](current_handoff.md), and stage sequences are in the
[current roadmap](current_roadmap.md).

## North Star

The ultimate aspiration of the project is automated stock selection and trading,
pursuing sustainable risk-controlled long-term net returns. Stable profit is an
explicit objective, not a guarantee.

This repository is the foundational research and simulation phase. It stays
strictly simulated, reproducible, auditable, and non-order-capable. Live
trading, broker integrations, credentials, order routing, pre-trade risk limits,
position and cash reconciliation, real-time health monitoring, and emergency
kill switches belong strictly to a future, separately authorized private
execution system.

## Edge Thesis

The program tests one primary source of return: diversified, low-turnover
harvesting of published risk and behavioral premia in liquid US equities,
improved by combination, cost control, and risk budgeting. Candidate premia are
momentum, short-term reversal, low risk, value, and quality. Short-horizon
price-volume alphas at end-of-day granularity sit outside the thesis; the
WorldQuant-101 library remains an exploratory control family.

## Objective And Hurdle

- **Objective metric:** net-of-cost excess return over declared benchmarks
  (SPY and the equal-weight point-in-time universe). Each pre-registration
  states a target information ratio, a tracking-error budget, and a maximum
  drawdown budget.
- **Planning prior:** a net information ratio of about 0.3–0.6 for a
  diversified premia portfolio, with material post-publication decay.
- **Hurdle:** beat the cheapest passive implementation of the same premia, an
  index fund plus factor ETFs, after costs and taxes.

## Kill Criteria

If an adequately powered, pre-registered factor family on the point-in-time
universe has no survivor under Benjamini–Yekutieli control at 5%, engine
feature work stops and the owner reviews the edge thesis. Adequate power means
a minimum detectable mean monthly Rank IC of 0.02 or better. An underpowered
null extends history or breadth before any pivot.

## Demo-First Delivery Philosophy

The engineering approach ships a small, demonstrable, presentable, and
reproducible end-to-end version first (**Demo v0**) and improves it in working
layers. Non-blocking imperfections, data caveats, and missing coverage go to a
lightweight backlog.

An initial working demonstration proceeds without an ideal pipeline, complete
SEC identity proof for every security, optional ledger/schema coverage, or a
factor zoo. Minimum research correctness at every layer is the invariant set
R1–R12 in [AGENTS.md](../AGENTS.md#research-safety-invariants).

## Relationship to the Historical Research Charter

The historical research charter ([docs/research_program_charter.md](research_program_charter.md))
remains preserved as the hash-pinned formal research evidence policy and evidentiary
ceiling definition. It governs formal claims; demo delivery proceeds under the
invariants above.

Formal promotion controls, full corporate action event reconciliation, and multiple-testing
adjustments remain prerequisites for formal academic or production claims. A
visibly limited demo proceeds without them.

## Primary Milestones

The program follows a five-milestone sequence from foundational engine to working demo and future execution. Program stage sequence, dependency order, gate and completion criteria, and coarse status are owned by [docs/current_roadmap.md#primary-milestones](current_roadmap.md#primary-milestones); detailed Demo v0 deliverable definitions and criteria are owned exclusively by [docs/current_roadmap.md#active-delivery-target-demo-v0-definition-of-done](current_roadmap.md#active-delivery-target-demo-v0-definition-of-done).

Under demo-first delivery, every actual attempted run retains its outcomes and
negative evidence. Demo v0 All-Attempt Case Logging records every attempted
case, including failures, for `python -m research.demo_v0`. Existing synthetic
sidecars are legacy diagnostics outside Demo v0 evidence. This lightweight
diagnostic run logging is distinct from the formal experiment/trial-ledger
accounting required by charter Stage 4 / Milestone 4.

## Authoritative Backlog and Imperfection Policy

The single authoritative imperfection backlog table is maintained exclusively in
[docs/current_roadmap.md#imperfection-policy-and-lightweight-backlog](current_roadmap.md#imperfection-policy-and-lightweight-backlog).
Presentation polish, additional factor families beyond demo scope, full 37-event
ledger schema breadth, and comprehensive historical SEC entity lineage proofs
are safe to defer when the claimed calculation stays valid. Invariants R1–R12
never defer.

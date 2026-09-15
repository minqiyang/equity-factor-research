# North Star and Demo-First Delivery

Updated: 2026-09-15

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

The research and simulation platform developed in this repository is the foundational
first phase—not the final execution product. The current repository remains strictly
simulated, reproducible, auditable, and non-order-capable. Live trading, broker
integrations, credentials, order routing, pre-trade risk limits, position and cash
reconciliation, real-time health monitoring, and emergency kill switches belong strictly
to a future, separately authorized private execution system.

## Demo-First Delivery Philosophy

The engineering approach prioritizes shipping a small, demonstrable, presentable,
and reproducible end-to-end version first (**Demo v0**). Non-blocking imperfections,
data caveats, and missing coverage are recorded in a lightweight backlog and improved
in working layers.

We avoid blocking an initial working demonstration on an ideal pipeline, complete
SEC identity proof for every security, optional ledger/schema coverage, or a factor
zoo. At every layer, minimum research correctness is non-negotiable:
- Strictly no lookahead or timing mismatch: enforce accepted `after_close_signal_next_observed_close_v1`
  timing contract (signals computed strictly after close, earliest target reset at next observed close;
  no same-bar or open execution without separate typed contract);
- Realistic transaction costs and turnover accounting under existing turnover conventions
  (sum of absolute signed trades under undivided convention, explicit spread and commission bps);
- Sample honesty: no historical eligibility selected by future listing continuity, future
  index membership, or survivor-cohort filters; unverified exploratory diagnostics remain
  explicitly labeled survivorship-biased; no claim of a survivorship-free universe until
  Milestone 4 formal lineage controls exist; and visible retention of all trials and negative results;
- Data honesty: no silent fill, clip, drop, or repair of missing or zero-volume bars;
- Economic correctness: no identity mis-stitching (fail closed on ticker reuse), no default
  last-price or zero-payoff disappearance (PIT-006; if accepted terminal evidence is absent, the affected window blocks), no dividend double counting (PIT-007), and
  no incompatible price/volume dollar turnover calculations;
- Strict data privacy: no raw private data, ticker lists, or secret paths in public docs;
- Pure simulation with zero live/paper trading runtime or broker connectivity.

## Relationship to the Historical Research Charter

The historical research charter ([docs/research_program_charter.md](research_program_charter.md))
remains preserved as the hash-pinned formal research evidence policy and evidentiary
ceiling definition. It is not the active product delivery queue or a blanket blocker
to delivering a bounded demo.

Formal promotion controls, full corporate action event reconciliation, and multiple-testing
adjustments remain prerequisites for formal academic or production claims, but do not
prevent shipping the initial, visibly limited Demo v0 vertical slice.

## Primary Milestones

The program follows a five-milestone sequence from foundational engine to working demo and future execution. Program stage sequence, dependency order, gate and completion criteria, coarse status, and detailed deliverable definitions are owned exclusively by the canonical roadmap in [docs/current_roadmap.md#primary-milestones](current_roadmap.md#primary-milestones).

Under demo-first delivery, All-Attempt Case Logging across all attempted cases is mandatory for every trial (including active Milestone 2 Demo v0); cherry-picking or omitting failed trials is strictly forbidden. This lightweight diagnostic run logging is explicitly distinguished from Stage 4 complete immutable ledger accounting.

## Authoritative Backlog and Imperfection Policy

The single authoritative imperfection backlog table is maintained exclusively in
[docs/current_roadmap.md#imperfection-policy-and-lightweight-backlog](current_roadmap.md#imperfection-policy-and-lightweight-backlog).
It classifies items with explicit impact, current handling, and revisit triggers:

- **Safe to Defer for Demo v0**: Presentation polish, additional factor families beyond demo scope,
  full 37-event ledger schema breadth, advanced multiple-testing statistics (deflated Sharpe/FWER),
  and comprehensive historical SEC entity lineage proofs (provided the actual claimed calculation
  remains valid without fabricating economics).
- **Non-Deferrable (Demo-Blocking Defects)**: Identity mis-stitching and ticker reuse (PIT-005),
  future-membership selection and survivor-cohort filtering (no historical eligibility selected by
  future continuity or survivor cohorts; unverified diagnostics labeled explicitly survivorship-biased;
  no claim of a survivorship-free universe until Milestone 4), silent fill/clip/drop/repair (PIT-009), default
  last-price or zero-payoff disappearance (PIT-006; if accepted terminal evidence is absent, the affected window blocks), dividend double counting (PIT-007),
  incompatible price/volume dollar turnover, lookahead leakage or timing mismatch, incorrect
  cost/return math, falsified or cherry-picked results, unhedged/leaked private data, and live
  execution or brokerage integration. A known defect is not made safe merely by adding a caveat.

Refer to [current_roadmap.md](current_roadmap.md) for the complete, authoritative table of active caveats and non-deferrable boundaries.

# North Star and Demo-First Delivery

Updated: 2026-09-15

Canonical responsibility: active product aspiration, delivery methodology,
coarse program milestones, and research versus execution boundaries.

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
- Sample honesty: no future-membership selection, no survivorship bias, and visible retention of all
  trials and negative results;
- Data honesty: no silent fill, clip, drop, or repair of missing or zero-volume bars;
- Economic correctness: no identity mis-stitching (fail closed on ticker reuse), no default
  last-price or zero-payoff disappearance (PIT-006), no dividend double counting (PIT-007), and
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

1. **Milestone 1: Core Research & Synthetic Engine (Completed Baseline)**
   Core loaders, signal execution timing, drift-aware portfolio accounting, synthetic
   demos, and SQLite ledger first checkpoints (Path A PR #199, Path B PR #200).
   The historical Track A 14-trial run is REFUSED (`ACCEPTED_IDENTITIES_ZERO_NO_LINEAGE_CONFORMANT_PANEL`,
   `DIAGNOSTIC_ONLY`) and preserved as immutable history. The 2026-09-13 local diagnostic
   confirmed exploration feasibility with documented caveats.

2. **Milestone 2: Demo v0 Working Vertical Slice (Active Delivery Target)**
   One reproducible local command/workflow using an existing price-only factor and fixed
   strategy configuration -> simulated selection/holdings -> human-readable comparison report
   with benchmark, explicit cost/timing, risk, and limitations. Demonstrable on synthetic
   fixtures without private data; separately approved local-data runs remain exploratory diagnostics.

3. **Milestone 3: Exploratory Multi-Factor & Diagnostics (Planned Follow-up)**
   Multi-factor combination (e.g., three-factor combination), broader historical windows,
   and layered handling of data caveats (date gaps, zero-volume segments, adjustment checks).

4. **Milestone 4: Formal Research & Strict Lineage Controls (Future Evidence Gate)**
   Full point-in-time corporate action reconciliation, survivorship-bias-free universe
   construction, complete all-trial append-only ledger enforcement, purged/embargoed sample splits,
   and multiple-testing inference packages. Prerequisite for formal factor promotion.

5. **Milestone 5: Automated Execution & Trading Platform (Future Separately Authorized Scope)**
   Distinct future progression: candidate comparison and freezing -> independent reproduction ->
   forward observation -> separately authorized paper trading -> separately authorized small-capital
   evaluation -> separately authorized live evaluation. Maintained in a separate execution repository
   owning pre-trade risk limits, position and cash reconciliation, real-time health monitoring,
   emergency kill switches, broker connectivity, credentials, and live order placement. Strictly
   outside the authority of the current research repository. No milestone grants authority and no
   candidate or strategy model has been validated by this documentation task.

## Authoritative Backlog and Imperfection Policy

The project maintains a single authoritative imperfection backlog table in
[PROJECT_SPEC.md](../PROJECT_SPEC.md#imperfection-policy-and-backlog) and
[current_roadmap.md](current_roadmap.md), classifying items with explicit impact, current handling,
and revisit triggers:

- **Safe to Defer for Demo v0**: Presentation polish, additional factor families beyond demo scope,
  full 37-event ledger schema breadth, advanced multiple-testing statistics (deflated Sharpe/FWER),
  and exhaustive historical entity lineage proofs (provided the actual claimed calculation remains
  valid without fabricating economics).
- **Non-Deferrable (Demo-Blocking Defects)**: Identity mis-stitching and ticker reuse,
  future-membership selection and survivorship, silent fill/clip/drop/repair, default last-price
  or zero-payoff disappearance, dividend double counting, incompatible price/volume dollar turnover,
  lookahead leakage or timing mismatch, incorrect cost/return math, falsified or cherry-picked
  results, unhedged/leaked private data, and live execution or brokerage integration. A known defect
  is not made safe merely by adding a caveat.

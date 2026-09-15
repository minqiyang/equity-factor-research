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
integrations, credentials, and order routing belong strictly to a future,
separately authorized private execution system.

## Demo-First Delivery Philosophy

The engineering approach prioritizes shipping a small, demonstrable, presentable,
and reproducible end-to-end version first (**Demo v0**). Non-blocking imperfections,
data caveats, and missing coverage are recorded in a lightweight backlog and improved
in working layers.

We avoid blocking an initial working demonstration on an ideal pipeline, complete
SEC identity proof for every security, optional ledger/schema coverage, or a factor
zoo. At every layer, minimum research correctness is non-negotiable:
- Strictly no lookahead or future information leakage (T-1 signal lag, execution at T);
- Realistic transaction costs and turnover accounting (bid-ask spread and commission bps);
- Sample honesty and visible retention of all trials and negative results;
- Strict data privacy (no raw private data, ticker lists, or secret paths in public docs);
- Pure simulation with no live/paper trading runtime or broker connectivity.

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
   Translating validated models into execution algorithms, simulated order generation, broker
   connectivity, paper trading, and eventual risk-controlled live execution in a separate execution repository.

## Lightweight Backlog of Deferred Imperfections

- **Safe to Defer for Demo v0**: Incomplete SEC entity lineage, zero-volume/flat-price segments,
  dividend/split event-level reconciliation, factor zoo expansion, 37-event ledger schema breadth,
  advanced multiple-testing statistics (deflated Sharpe/FWER), and plotting/dashboard polish.
- **Non-Deferrable (Demo-Blocking Defects)**: Lookahead leakage, transaction fee omissions,
  falsified/cherry-picked results, leaked private data, and live broker execution.

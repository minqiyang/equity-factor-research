# Local CSV Readiness Input Checkpoint

Date: 2026-06-23

This documentation-only checkpoint turns the current local CSV readiness
boundary into an explicit input package for future user-provided local data
work. It follows the post local fixture roadmap reconciliation and does not
authorize real-data interpretation by itself.

This checkpoint does not modify source code, tests, research scripts, generated
reports, strategy logic, backtester behavior, metrics, data access, execution
assumptions, or performance claims. It does not read private local data, fetch
data, download vendor data, add credentials, add live trading, add paper
trading, add brokerage integration, add order execution, or claim
profitability.

## Current Evidence

Current synced state before this checkpoint:

```text
Branch reviewed: main
HEAD reviewed: 466b115 Merge pull request #116 from minqiyang/codex/post-local-fixture-roadmap-reconcile
Latest merged staged PR reviewed: PR #116, [codex] Reconcile roadmap after local fixture outputs
Open pull requests before branch creation: none
```

Baseline validation before creating this checkpoint:

```text
.venv/bin/python -m pytest -q
503 passed

.venv/bin/python -m compileall src tests research
passed
```

## Required User-Provided Inputs

Before any future local CSV research run is interpreted as real-market
evidence, the user must provide or approve a readiness package that is separate
from private/raw data contents.

Required inputs:

1. Scope statement: intended run type, local file groups, expected schemas,
   date range, universe definition, candidate features, benchmark, cost and
   slippage assumptions, interpretation level, and whether the output is only
   a readiness review or a research experiment.
2. Metadata-only inventory: local paths or handles, source description,
   extraction/export timestamps or vendor version labels when available,
   mutability policy, hash plan if files may be re-read, and known manual
   edits or transformations.
3. Schema map: price/OHLCV fields, benchmark fields, universe or membership
   fields, optional factor or metadata fields, date columns, asset identifiers,
   adjustment fields, volume fields, and missing-value sentinels.
4. Readiness audit: completed review with no unresolved high or medium issues
   for provenance, schema, date alignment, survivorship, benchmark choice,
   train/validation/test split policy, cost/slippage assumptions, and
   privacy/secret exposure.
5. Experiment handoff draft: planned assumptions for data source, universe,
   benchmark, feature timing, execution timing, split dates, transaction costs,
   slippage, missing-data handling, caveats, and expected report/log location.
6. Explicit approval boundary: confirmation that any files considered are
   local-only user-provided files, contain no secrets or credentials, and may
   be reviewed only within the stated readiness scope.

## Stop Conditions

Stop before loading, transforming, reporting, or interpreting user-provided
local CSV data if any of these are present:

- missing or unclear data provenance.
- unknown split, adjustment, benchmark, or universe construction policy.
- point-in-time or survivorship ambiguity that affects interpretation.
- unclear feature date, signal date, execution date, or return measurement
  date alignment.
- missing transaction-cost, fixed-slippage, or volume-aware caveat policy.
- private/raw data exposure outside the approved local scope.
- credentials, tokens, account identifiers, broker files, or vendor API
  material.
- unresolved high or medium readiness-audit issue.
- wording that frames diagnostics as tradeability, execution realism, or
  profitability evidence.

## Next Stage Options

| User state | Next safe stage | Boundary |
| --- | --- | --- |
| User provides the readiness package above | Metadata-only intake and readiness review | Do not commit private/raw data contents. Stop for any high or medium readiness issue. |
| User does not provide local data but asks to keep clarifying the path | Documentation-only registry or readiness-template review | Do not imply that a real-data study can proceed without the required inputs. |
| User does not provide local data and no narrow docs/test-plan scope is requested | Pause at the readiness boundary | No real-data interpretation, fetching, vendor APIs, credentials, brokerage, order execution, or profitability claims. |

## Recommendation

The next default checkpoint after this PR merges should remain:

```text
Pause for user-provided local CSV readiness inputs before any real-data interpretation.
```

If the user asks to continue without local data, the next stage should be
documentation-only and should clarify either the readiness template or the
registry schema expectations for already committed synthetic/local-fixture
diagnostics.

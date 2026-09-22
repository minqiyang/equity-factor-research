# Milestone 4.5 Independent Remediation Re-Review

Verdict: PASS (MATERIAL: 0)

M45-R1 is resolved at `34af01417b6507725e4210e7d14de01d38b1e99a`.
Independent inspection and execution confirm correct all-buy funding, the
absolute closing-balance guard, all requested QA gates, and retained capacity
evidence. This review identifies zero new material findings.

## Identity and scope

- Review date: 2026-09-22.
- Reviewer: the owner-dispatched independent Codex re-review session.
- Candidate: `34af01417b6507725e4210e7d14de01d38b1e99a`.
- Comparison base: `fe851ba0a69be1416db265bee4375433ab45d52d`.
- Previous reviewed candidate: `fa63cfae90b6543e94b861df2277ecdfab9b9460`.
- Directive: `coord/card_m4_5_market_impact_capacity_rereview.md`.
- Clean verification root: `/private/tmp/efr-m45-rereview-34af014-verified`.
- Independent evidence: `/private/tmp/efr-m45-rereview-evidence-34af014`.
- Report delivery root: `/private/tmp/efr-m4-5-rereview-clean-34af014`.

The supplied root had the exact candidate HEAD and two untracked setup files:
`.venv` and the re-review directive. Both remain preserved. A fresh detached
worktree at the candidate supplied the clean formal inspection and execution
root; its initial and final porcelain status were empty. Imports resolved to
that root. Candidate implementation, tests, and committed evidence remained
unchanged. This report is the sole authored repository artifact.

The previous report was absent from the supplied checkout. Its preserved copy
at `/private/tmp/efr-m4-5-market-impact-capacity/coord/reports/m4_5_market_impact_capacity_review.md`
supplied the M45-R1 history and is retained as `previous_review.md` in the new
evidence directory. Inspection covered the remediation diff, shared execution
step, both engine integrations, regression tests, capacity generator and tests,
baseline/ablation drivers, implementation report, timing supplement, and
committed source/output fingerprints. Repository instructions, north star,
roadmap, accepted card, and the live coordination standard's two files informed
scope and evidence handling. The owner's explicit single-reviewer assignment
governs this re-review.

## M45-R1 — P1 MATERIAL, RESOLVED

**Resolution candidate:** `34af01417b6507725e4210e7d14de01d38b1e99a`.
**Original claim:** all-True pandas buy selections could alias the executed
Series; scaling fills then scaled the saved funding vector a second time,
understating fees and fabricating cash. Both engines consume the affected shared
execution step.

At `src/backtest/market_impact.py:420`,
`executed.loc[buys].to_numpy(dtype=float, copy=True)` gives the unscaled funding
array independent storage. Lines 424–428 quote costs from this stable array;
lines 440–445 update actual fills and compute their final outlay once.
An independent pandas 3.0.6 probe confirms that the uncopied all-True selection
shares memory with the Series and the copied selection does not. Scaling
`[50, 50]` fills by 0.5 changes the uncopied array to `[25, 25]`; the copied
array retains `[50, 50]`. `alias_check.json` preserves these observations.

The original two-security, $100 cash, 100 bps fixed-slippage reproduction now
returns:

| Quantity | Independently observed result |
| --- | ---: |
| Executed buys | 99.00990099009901 |
| Slippage | 0.9900990099009902 |
| Closing cash | 0.0 |
| Post-cost equity | 99.00990099009901 |
| Closing cash plus positions | 99.00990099009901 |

At `src/backtest/market_impact.py:482-490`, the final guard requires a finite
closing balance and enforces
`abs((cash_after + positions_after.sum()) - equity_after) <= 1e-6`.
Here `equity_after = equity_before - commission - slippage`. Excess discrepancies
raise `MarketImpactValidationError` with reason `impact_accounting_invalid`
before returning execution results. Earlier checks require finite cash,
positions, costs and equity. The pretrade reconciliation guard remains before
quotation at lines 331–341.

Independent positive and negative discrepancy probes use equity `2**30` so the
input relative tolerance admits the test values. Discrepancies of
`±1.9073486328125e-6` refuse with the required reason; discrepancies of
`±9.5367431640625e-7` and zero pass. The committed tests independently cover
these boundaries and assert pretrade validation ordering.

All eight original reviewer regressions pass: six direct-step fixed-slippage
or commission cases across all three policies and two public long-only
terminal/subsequent-row cases. The three committed impact suites pass all 133
tests. Their 20 added cases cover fixed, commission and square-root costs,
funding after participation handling, signed threshold boundaries, and
single/two-security public books. The combined focused run reports 141 passed.

The previous review's seeded independent oracle also passes on this candidate:
240 scalar quotes, 240 funding steps, 80 expected cap refusals, 266 causal
liquidity windows, and 18 long-only/long-short share-and-cash replays across
lags 1, 2 and 4. It records zero funding mismatches. The preserved runner was
copied to the new evidence directory with only its output destination changed;
the earlier evidence remains intact.

## Independently executed verification

The supplied interpreter is
`/Users/rhapsoul/Documents/Codex/Artifact/EFR/equity-factor-research-clean/.venv/bin/python`.
Observed versions are CPython 3.12.13, pandas 3.0.6, NumPy 2.5.3, SciPy 1.18.1,
pytest 9.1.1, pytest-xdist 3.8.0, and Ruff 0.16.8. Runs use `PYTHONPATH=src:.`;
the six native numerical thread limits equal 1. Full lanes use two worksteal
workers with `--max-worker-restart=0`.

| Gate | Independent result | Evidence file |
| --- | --- | --- |
| Eight reviewer cases plus three impact suites | 141 passed, 10 warnings, 4.95 s | `regressions.txt` |
| Core lane | 4,136 passed, 2 inherited skips, 30 warnings, 32.15 s | `core.txt`, `core.xml` |
| Diagnostics lane | 125 passed, 20 warnings, 94.70 s | `diagnostics.txt`, `diagnostics.xml` |
| Disjoint union | 4,261 passed, 2 skipped; 4,263 unique collected cases | `verification.json` |
| Intact ablation baseline | 133 passed | `ablation/baseline/pytest.txt` |
| Negative ablations | All 17 exit 1 through regression failures | `ablation/results.json` |
| Model-absent baseline | Exact byte equality and expected SHA-256 | `candidate.json`, `baseline.txt` |
| Full capacity replay | Exact cases, brackets, and Markdown | `capacity_check.json` |
| Repository Ruff | PASS, exit 0 | `ruff.txt` |
| `python -m compileall -q src tests research lean` | PASS, exit 0 | `compileall.txt` |
| Committed validation fingerprints | All 12 source and 3 output hashes match | `verification.json` |
| Seeded independent numerical oracles | All checks pass; zero funding mismatches | `oracle_results.json` |

JUnit case identities are unique within each full lane and have an empty
intersection across lanes. Focused, ablation and reviewer-only cases remain
outside the reported disjoint total. The two inherited skips occur at
`tests/test_backtest_timing_contract.py:1221` because this platform's longdouble
has no precision beyond float64. Warnings concern constant-input correlations.

`commands.json` records the full commands and successful process exits for the
two lanes, focused regressions, ablation and baseline replay. The reviewer
verification scripts, generated artifacts and logs are retained in the evidence
directory; `hashes.json` fingerprints the evidence bundle.

## Ablation necessity and source preservation

The committed `coord/reports/m4_5_evidence/ablate.py` ran against separate copied
packages and checked their import locations. Each negative case produced pytest
exit 1 with an exercised regression failure. Collection/import errors supplied
zero outcomes. Original source hashes remained unchanged.

| Removed element | Failing tests |
| --- | ---: |
| Estimator lag | 1 |
| Matching price/volume basis | 3 |
| ADV admissibility | 7 |
| Sample volatility ddof | 1 |
| Raise participation cap | 1 |
| Throttle clipping | 1 |
| Penalize policy | 1 |
| Eta coefficient | 4 |
| Fixed cost coefficient | 4 |
| Penalty coefficient | 1 |
| Cash funding | 1 |
| Input cash balance guard | 1 |
| Current execution volume guard | 2 |
| Terminal exemption | 3 |
| Long-only sell bound | 1 |
| Unscaled buy copy | 9 |
| Absolute post-trade balance guard | 2 |

The final two removals independently demonstrate the remediation controls'
necessity. All tested controls remain justified. This revalidation covers the
M4.5 ablation scope; earlier subsystems receive full-lane and baseline regression
coverage.

## Baseline and capacity evidence

The committed capture driver produced a fresh candidate capture in 56.70 s.
Direct byte comparison with `/private/tmp/efr-m4-5-evidence/baseline.json`
succeeds. Both files have SHA-256:

`5a885b96e7379a83658047d4720d701f504f92838ffae10a76fa267580b61ed4`.

The capture covers 62 factors and 124 books, previously exposed result fields,
diagnostic summaries and the PIT demo, with the six introduced impact fields
excluded by the established capture contract. This re-review regenerated the
candidate capture and compared the supplied hash-bound baseline.

A complete 96-scenario generated capacity run writes only to the independent
evidence directory. Its case objects and adjacent-AUM bracket objects exactly
equal the committed JSON; its Markdown is byte-identical to the committed
report. Results retain 61 successes, 35 typed refusals, 37 negative-return
books, 49 intervals without an observed crossing and 31 unavailable intervals.
The grid contains zero positive-to-nonpositive brackets.

The stricter closing-balance guard retains the documented $1B synthetic
long-short throttle refusal as an unavailable endpoint. Large-notional
floating-point discrepancies can exceed the fixed $0.000001 threshold; the
timing supplement and implementation report disclose that behavior.

The new run retains 192 events: 96 starts, 61 successes and 35 refusals. The
committed historical log retains 768 events: 384 starts, 242 successes,
137 refusals and five failures. Every attempt ID has exactly one start and one
outcome with matching case identity. Fresh outcomes and the latest historical
96 outcomes match every field in the replayed case objects. Existing tests also
exercise append behavior, typed refusals, failures, and interruption durability.

## Limits and next gate

This verdict applies to the exact candidate and the requested synthetic
simulation remediation. Empirical impact calibration, actual strategy
capacity, vendor basis certification, borrow costs, intraday execution and
corporate-action conversion of pending shares remain documented future work.
Hosted Python 3.11 CI, packaging and remote publication state were outside this
re-review's requested execution checks. The coordinator owns the remaining
delivery gates and this report's acceptance.

M45-R1 is resolved, all seven requested verification tasks are complete, and
the reviewed candidate has MATERIAL: 0.

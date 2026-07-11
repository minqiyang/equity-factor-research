# Full Repository Conformance Audit - 2026-07-11

Status: complete on merged baseline
`a3400729df675013286deab15f073c66af073d40`.

This was a read-only repository audit. It did not change research code,
strategy behavior, tests, generated evidence, or workflow controls.

## Scope

The audit compared the canonical roadmap, current handoff, README, project
specification, source, tests, synthetic reports and JSON logs, experiment
registry, package metadata, CI workflow, private-output rules, and non-executing
LEAN files.

Priority followed `AGENTS.md`: concrete timing, leakage, benchmark, portfolio,
cost, and documentation mismatches would be P1; implemented behavior missing
from current documentation or tests would be P2.

## Evidence

| Area | Evidence | Result |
| --- | --- | --- |
| Canonical status | `docs/current_roadmap.md`, `docs/current_handoff.md`, `README.md`, `PROJECT_SPEC.md` | Current claims match implemented features and explicit open gaps. |
| Timing and leakage | Feature alignment tests, signal-lag backtest tests, strict index validation, benchmark-return contract | No concrete look-ahead, same-period target-return, or benchmark-window mismatch found. |
| Portfolio accounting | Drifted holdings, signed/absolute trade identities, turnover, applied costs, position cap, episode attribution tests | Return timing and cost attribution match the documented contracts. |
| Episode metrics | Completed continuous-positive-weight episodes, deployed-weight denominator, applied-cost reconciliation, terminal-open exclusion | Design, code, tests, reports, logs, and registry agree. |
| Generated evidence | Three backtest generators plus experiment registry; SHA-256 manifest before and after regeneration | Byte-stable; no uncommitted output change. |
| Privacy and credentials | Tracked-file scan, credential-pattern scan, local-only loader boundaries | No tracked private data, credential value, downloader, or vendor client found. |
| LEAN boundary | `lean/`, LEAN scope tests, README and roadmap claims | Metadata/signal scaffold only; no brokerage, order, paper, or live path. |
| Unicode and repository hygiene | Tracked-file bidi/zero-width/non-breaking-space scan; artifact-name scan | No hidden control characters or tracked cache/private artifacts found. |
| Quality gates | 591 tests, Ruff, source/test/research/LEAN compilation, package build, JSON parsing, whitespace check | All passed on the audited baseline. |

## Findings

No actionable P1 or P2 findings.

The audit found no evidence that current documentation overstates implemented
research behavior, no implemented timing or accounting behavior missing from
the canonical status files, and no unresolved mismatch requiring remediation.

## Residual Boundaries

These are declared scope limits, not audit defects:

- Real-data interpretation remains blocked until provenance, point-in-time
  universe, survivorship, adjustment, benchmark, split, cost, and
  interpretation policies are accepted for a specific local dataset.
- Plotting remains unimplemented.
- The position cap is the only implemented portfolio constraint; broader
  exposure controls remain future work.
- Volume-aware impact remains a deterministic research estimate rather than a
  calibrated fill or market-impact model.
- LEAN execution, brokerage, paper trading, and live trading remain out of
  scope.

## Conclusion

The audited public synthetic/local research baseline is internally conformant
and reproducible at the stated scope. No remediation PR is required from this
audit. Future work must reopen conformance review when it changes timing,
portfolio accounting, costs, benchmark semantics, real-data interpretation,
private-output boundaries, or LEAN scope.

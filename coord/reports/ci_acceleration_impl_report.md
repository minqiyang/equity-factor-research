# Stage A CI Acceleration Implementation Report

Date: 2026-09-21.
Assigned branch: `feat/ci-acceleration-and-optimization`.
Design baseline / current HEAD parent: `3bb32dfd316bdd2a831fbe62ab961e62a0cf7689`.
Design card: `coord/card_ci_acceleration_and_optimization.md`.
Evidence ceiling: workflow and test-infrastructure change only. No research-result claim.

This report records producer implementation of Stage A bounded scheduling.
Independent acceptance, GitHub publication, and same-runner 5–8 minute
wall-clock measurement remain Coordinator gates.

## Design-card analysis

The architecture card measures GitHub PR #249 run 35568200842 at 2,317 s
elapsed, with 2,290 s in serial pytest (3,819 passed). Install is 18 s and
the remaining lint/compile/build surface is about four seconds. The pip
cache already restores binary wheels. The 5–8 minute objective is therefore
a test-critical-path problem.

The card's performance model for serial work `S = 2,289.27 s` gives a
two-worker floor of 1,144.64 s and a four-worker floor of 572.32 s. An
eight-minute job with 60 s reserved for setup leaves 420 s for tests, which
already exceeds the two-worker work floor. The longest recorded test
(`test_multifactor_diagnostic_official_report_table_matches_default_fixture`,
141.10 s serial / 146.55 s in this local parallel run) is an independent
lower bound. Stage A therefore ships bounded scheduling and collection
correctness. Stage B owns kernel work that can reduce `S` and `L`. Stage C
owns a measured core/diagnostics lane split.

Local design-card profiling on CPython 3.11.15 / macOS ARM64 recorded:

| Experiment | Result |
| --- | --- |
| Serial, unchanged source | 3,817 passed, 2 skipped, 23 warnings; 521.23 s |
| Two-worker worksteal, unordered `list(_SUPPORTED_MODELS)` | collection failure in 1.20 s |
| Two-worker worksteal after `sorted(_SUPPORTED_MODELS)` | 3,817 passed, 2 skipped, 23 warnings; 264.84 s; node-ID identity matches serial |

The unordered ML parametrization is a retained necessity. A fixed
`PYTHONHASHSEED` would hide the collection contract. Stage A sorts the
parameter source and leaves hash randomization enabled.

Scheduling ablation in the card rejects `--dist loadfile` as the default
because the dominant diagnostic file costs 118.733 s of modeled critical
path under file grouping. A two-lane core/diagnostics split reduces the
modeled path by only 21.524 s (8.5%) before extra setup and gate costs.
Stage A therefore keeps one job named `Python validation` with
`-n 2 --dist worksteal`.

Live GitHub protection requires the exact check context `Python validation`
(Actions app ID 15368). The workflow name remains `CI`. The job ID remains
`validation`.

## Scope completed

Stage A delivers the three executable changes plus engineering evidence:

1. `pyproject.toml` adds `pytest-xdist>=3.5.0` to the `dev` extra.
2. `tests/test_ml_combination.py` parametrizes `sorted(_SUPPORTED_MODELS)`.
3. `.github/workflows/ci.yml` is the Section 7 single-job workflow, with the
   existing campaign-safety comments retained (see Compatibility retention).
4. `docs/engineering_log.md` and `CHANGELOG.md` record the change.
5. `python scripts/repo_map.py` regenerated `docs/repo_map.md`; mapped
   counts are unchanged because no new mapped files were added.

`[tool.pytest.ini_options]` is unchanged:

```toml
testpaths = ["tests"]
pythonpath = ["src"]
addopts = "-ra"
```

Ordinary local `python -m pytest -q` remains serial. Worker count lives in
the CI command. Runtime kernels, synthetic panel sizes, factor inventory,
trial retention, timing contracts, and tolerances are unchanged.

## Files

| Path | Role |
| --- | --- |
| `pyproject.toml` | `pytest-xdist>=3.5.0` in the `dev` extra |
| `tests/test_ml_combination.py` | Deterministic xdist collection order |
| `.github/workflows/ci.yml` | Stage A two-worker workflow and evidence upload |
| `CHANGELOG.md` | Unreleased Changed notes |
| `docs/engineering_log.md` | 2026-09-21 Stage A record |
| `coord/reports/ci_acceleration_impl_report.md` | This report |

## Workflow contract implemented

| Requirement | Implementation |
| --- | --- |
| Required check name | Job `validation`, name `Python validation` |
| Native thread clamp | Job-level `OMP_NUM_THREADS`, `OPENBLAS_NUM_THREADS`, `MKL_NUM_THREADS`, `BLIS_NUM_THREADS`, `VECLIB_MAXIMUM_THREADS`, `NUMEXPR_NUM_THREADS` all `"1"` |
| Concurrency | `group: ${{ github.workflow }}-${{ github.event_name }}-${{ github.event.pull_request.number \|\| github.run_id }}`; `cancel-in-progress` only for `pull_request` |
| Triggers | `pull_request` and `push` to `main`; `merge_group` `checks_requested` |
| Permissions | `contents: read` |
| Python | `actions/setup-python@v5`, `python-version: "3.11"`, `cache: pip`, `cache-dependency-path: pyproject.toml` |
| Install | `pip install --prefer-binary -e ".[dev]"` after pip upgrade |
| Pytest | `python -m pytest -q -n 2 --dist worksteal --max-worker-restart=0 --durations=50 --durations-min=0.1` with JUnit and `tee` log |
| Fail-closed evidence | Environment, SHA, `nproc`, memory, `threadpoolctl`, `/usr/bin/time -v`, JUnit, log; `actions/upload-artifact@v4` with `if: always()` |
| Ancillary checks | Ruff, `compileall src tests research`, `compileall lean`, `python -m build`, `git diff --exit-code HEAD -- .` |
| Hang bound | `timeout-minutes: 45` |
| Shell | `defaults.run.shell: bash` (Actions fail-fast / `pipefail`) |

## Compatibility retention

`tests/test_campaign_conformance.py::test_ci_runs_only_committed_synthetic_campaign_fixtures`
requires the phrases `committed synthetic fixtures`, `not result-bearing`,
and `private panel`, and requires exactly one `python -m pytest -q`
substring. Section 7 of the design card proposed the comment
`Tests use committed or generated synthetic fixtures.` That wording drops
the two required safety phrases.

Stage A keeps the existing comments:

```yaml
    # Campaign and repository tests use committed synthetic fixtures only.
    # This job is not result-bearing and does not read a private panel.
```

The pytest invocation remains a single `python -m pytest -q -n 2 --dist worksteal`
line, so the substring count stays 1. Generated `tmp_path` Parquet fixtures
in `tests/test_real_data_multifactor_diagnostic.py` remain synthetic and
in-process; the job still reads no private panel.

## Verification

Producer interpreter: `/Users/rhapsoul/Documents/Codex/Artifact/EFR/equity-factor-research-clean/.venv/bin/python`
(CPython 3.12.13). Packages: pytest 9.1.1, pytest-xdist 3.8.0, NumPy 2.5.3,
pandas 3.0.6, SciPy 1.18.1, scikit-learn 1.9.1, PyArrow 25.0.1. Native
thread variables were set to 1 for pytest. Full pytest used
`--basetemp=/tmp/efr-pytest-ci-accel`.

This environment matches the design card on pytest/xdist/pandas/sklearn/pyarrow
and differs in CPython patch (3.12.13 vs 3.11.15), NumPy (2.5.3 vs 2.4.6),
and SciPy (1.18.1 vs 1.17.1). Local elapsed times are workload and
compatibility evidence on this machine. GitHub wall-clock acceptance remains
a same-runner measurement.

| Command | Result |
| --- | --- |
| `python -m ruff check .` | All checks passed |
| `python -m compileall -q src tests research lean` | passed |
| `python scripts/repo_map.py` | Wrote `docs/repo_map.md`; no mapped-count change |
| `git diff --check` | clean |
| actionlint 1.7.12 on `.github/workflows/ci.yml` | exit 0 |
| Three workflow `run: \|` bodies via `bash -n` | exit 0 |
| `python -m build --outdir /tmp/efr-ci-accel-dist` | sdist and wheel; 20 `ledger/schemas/*.json` and `*.sha256` files in each |
| ML collect-only under `PYTHONHASHSEED` 1, 2, 3 | identical 8 node IDs; models `gradient_boosting`, `hist_gradient_boosting`, `random_forest`, `ridge` |
| Key suites `-n 2 --dist worksteal --max-worker-restart=0` | 164 passed in 7.33 s |
| Full suite same flags | 3,817 passed, 2 skipped, 23 warnings in 268.59 s |
| JUnit | 3,819 cases, 3,819 unique node IDs, 0 duplicates; 3,817 passed, 2 skipped |
| `bash -eo pipefail` `false \| tee` | exit 1 |
| Missing pytest node piped through `tee` | exit 4 |
| Tracked `tests/fixtures`, `reports`, `src`, `research` vs HEAD | unchanged |

The two skips are the existing ARM `longdouble` cases in
`tests/test_backtest_timing_contract.py:1129`. The 23 warnings are the
existing constant-input Spearman warnings. Worker restarts were disabled;
the run completed without a crash.

Local parallel wall clock 268.59 s is 1.94x the design-card serial 521.23 s
on this machine class. The longest call in this run is 146.55 s
(`test_multifactor_diagnostic_official_report_table_matches_default_fixture`).
Controller `/usr/bin/time -l` maximum RSS is 747,618,304 bytes. That figure
is the timed parent process, not the aggregate of controller plus workers.

Local evidence files (ephemeral):

| Artifact | SHA-256 |
| --- | --- |
| `/tmp/efr-ci-accel-evidence/pytest.log` | `24c7377bd2b1fdf4bd8b9a21a89164d9ee8e71bdc8f61ad2b4620d60a869c8d0` |
| `/tmp/efr-ci-accel-evidence/pytest.xml` | `1d78c4dfa304dd1cd83781e4876ef1b2575c3da2ca6b5f6936af5874aa6023db` |

## Ablation

Stage C multi-job YAML is specified in the card and is not activated.
`addopts` stays serial. Worker count stays in the CI command.
`--dist loadfile` is unused. Four-worker `-n 4` is unused pending GitHub
CPU/RAM telemetry. A custom wheelhouse is unused; setup-python remains the
single cache owner. `PYTHONHASHSEED` is unset in CI.

The `sorted(_SUPPORTED_MODELS)` parametrization is retained because the
unordered `list(...)` collection failed under xdist. Native thread limits
are retained as the declared resource bound. Evidence upload and
`git diff --exit-code` are retained as fail-closed diagnostics. The
campaign-safety comments are retained as a required existing assertion.

## Caveats and next gate

Stage A correctness on this producer is the local serial/parallel
membership and outcome record above plus static workflow validation.
GitHub cold-cache and warm-cache wall clocks, Linux cgroup memory.peak
against the 5.5 GB budget, merge-group scheduling, and PR cancel-in-progress
behavior require an authorized published run of this workflow.

The 5–8 minute GitHub target remains open. Two workers on the measured
GitHub serial load have an ideal floor near 19 minutes. Closing that gap
is Stage B (profile-driven hot-path work on the 756×50 default diagnostic
and related accounting) and, only after a measured advantage, Stage C.

Rollback, if xdist is incompatible on the runner: keep the `dev`
dependency and set the test command to `-n 0`. Keep the check name
`Python validation`.

Push, PR creation, and merge were not performed from this producer
worktree.

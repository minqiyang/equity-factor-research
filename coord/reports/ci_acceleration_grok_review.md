# GROK_REVIEW: Stage A CI acceleration candidate `8c859ef`

**Verdict: PASS (MATERIAL: 0)**

- Reviewer seat: `GROK_REVIEW` (Grok 4.6 Extra High, Reviewer 2, independent formal review)
- Exact candidate: `8c859ef80de036f9839a72d4019d181180eca134` (`8c859ef`, `feat(ci): Stage A bounded pytest-xdist scheduling and collection fix`)
- Tree: `9cb9de95459c2af9025552a5dc9b65ab416c96dc`
- Baseline / parent: `3bb32dfd316bdd2a831fbe62ab961e62a0cf7689`
- Review root: `/private/tmp/efr-ci-review-grok-8c859ef` (detached HEAD at the exact candidate)
- Producer worktree was not used as the review root
- Design card: `coord/card_ci_acceleration_and_optimization.md`
- Producer report: `coord/reports/ci_acceleration_impl_report.md`
- Coordination standard read from `/Users/rhapsoul/Documents/Codex/Standards/herdr_pi_coordinator_v7_two_file/` (`coordinator.md`, `routing_table.json`; table status `TEMPLATE_NOT_ACTIVE`)
- Date: 2026-09-21
- Review posture: read-only on this clean root; this report is the only authored deliverable

This body reviews the exact candidate bytes named above. Coverage is Stage A bounded pytest-xdist scheduling, the ML collection-order repair, workflow fail-closed evidence, and independent local execution of the full collected suite under `-n 2 --dist worksteal`.

Evidence ceiling is workflow and test-infrastructure change. This review records no research-result, profitability, or GitHub wall-clock claim.

## Scope

Commit `8c859ef` implements Stage A of `coord/card_ci_acceleration_and_optimization.md`. Delta versus `3bb32df`: 7 files, `+804 / −8`.

| Path | Role |
| --- | --- |
| `pyproject.toml` | `pytest-xdist>=3.5.0` in the `dev` extra |
| `tests/test_ml_combination.py` | `sorted(_SUPPORTED_MODELS)` parametrization for xdist collection |
| `.github/workflows/ci.yml` | Single job `Python validation` with two-worker worksteal, thread clamps, and evidence upload |
| `CHANGELOG.md` | Unreleased Changed notes for the three executable surfaces |
| `docs/engineering_log.md` | 2026-09-21 Stage A process record |
| `coord/card_ci_acceleration_and_optimization.md` | Binding Stage A/B/C architecture |
| `coord/reports/ci_acceleration_impl_report.md` | Producer implementation evidence |

Runtime factor kernels, synthetic panel sizes, factor inventory, trial retention, timing contracts, tolerances, and the five runtime dependency declarations are unchanged. Stage B hot-path work and Stage C multi-job lanes remain specified in the card and unactivated in this candidate.

## Coverage

| Check | Result on `8c859ef` |
| --- | --- |
| Exact-head identity | HEAD `8c859ef80de036f9839a72d4019d181180eca134`. Tracked tree matches HEAD. Untracked review interpreter only: `.venv`. |
| Design Stage A files | `pyproject.toml`, `tests/test_ml_combination.py`, and `.github/workflows/ci.yml` match the Section 6/7 executable contract, with campaign-safety comments retained as required by existing tests. |
| `pytest.ini_options` | Parent and candidate both use `testpaths = ["tests"]`, `pythonpath = ["src"]`, `addopts = "-ra"`. The commit hunk adds only `pytest-xdist>=3.5.0`. |
| Required check name | Job ID `validation`, job name `Python validation`, `runs-on: ubuntu-latest`, workflow name `CI`. |
| Thread clamping | Workflow `env` sets `OMP_NUM_THREADS`, `OPENBLAS_NUM_THREADS`, `MKL_NUM_THREADS`, `BLIS_NUM_THREADS`, `VECLIB_MAXIMUM_THREADS`, and `NUMEXPR_NUM_THREADS` to `"1"`. Independent `threadpoolctl` probe: 18 OpenMP threads without the variables, 1 thread with them. |
| Pytest scheduling | `-n 2 --dist worksteal --max-worker-restart=0`, JUnit and `tee` log under `$RUNNER_TEMP/ci-evidence/`. xdist 3.8.0 help lists `worksteal` and `--max-worker-restart`. |
| Fail-closed evidence | `git diff --exit-code HEAD -- .` with `if: always()`; `actions/upload-artifact@v4` with `if: always()`, unique name per run/attempt, `if-no-files-found: warn`. Local `git diff --exit-code HEAD -- .` exited 0 after the full parallel suite. |
| Collection identity | Serial collect-only and xdist collect-only both yield 3,819 unique node IDs; the ID sets are equal; duplicate count is 0. ML model cases stay `gradient_boosting`, `hist_gradient_boosting`, `random_forest`, `ridge` under `PYTHONHASHSEED` 1, 2, and 3. |
| Deterministic QA | Ruff clean; `compileall` of `src tests research lean` passed; key suites 164 passed in 7.67 s; full two-worker suite 3,817 passed, 2 skipped, 23 warnings in 264.06 s. |

## Design fidelity

Section 6 of the design card requires this `dev` extra and an unchanged pytest INI block. The candidate matches both:

```toml
[project.optional-dependencies]
dev = [
    "build>=1.2",
    "pytest>=8.0",
    "pytest-xdist>=3.5.0",
    "ruff>=0.9",
]
```

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
addopts = "-ra"
```

Worker count lives in the CI command. Ordinary `python -m pytest -q` remains the serial local reference.

The required one-line collection repair is present at `tests/test_ml_combination.py:126`:

```python
@pytest.mark.parametrize("model_type", sorted(_SUPPORTED_MODELS))
```

Production `_SUPPORTED_MODELS` in `src/features/ml_combination.py:25-30` remains a `set` of the four model names. An AST scan of `tests/**/*.py` found zero remaining `parametrize` arguments that are set/dict literals, `list(...)` wrappers, or `.keys()/.values()/.items()` calls. There is no `pytest_generate_tests` hook.

`.github/workflows/ci.yml` matches the Section 7 single-job replacement on every executable field reviewed:

| Contract field | Candidate |
| --- | --- |
| Triggers | `pull_request`/`push` to `main`; `merge_group` `checks_requested` |
| Permissions | `contents: read` |
| Concurrency | `group: ${{ github.workflow }}-${{ github.event_name }}-${{ github.event.pull_request.number \|\| github.run_id }}`; `cancel-in-progress` only when `github.event_name == 'pull_request'` |
| Defaults | `run.shell: bash` (Actions `bash --noprofile --norc -eo pipefail`) |
| Python | `actions/setup-python@v5`, `python-version: "3.11"`, `cache: pip`, `cache-dependency-path: pyproject.toml` |
| Install | `pip install --prefer-binary -e ".[dev]"` after pip upgrade |
| Ancillary checks | `ruff check .`; `compileall src tests research`; `compileall lean`; `python -m build` |
| Hang bound | `timeout-minutes: 45` |
| Evidence | SHA, Python version, `pip freeze --all`, `nproc`, `free -m`, `threadpoolctl -i numpy scipy sklearn`, `/usr/bin/time -v`, JUnit, pytest log |

The Ubuntu 24.04 GitHub-hosted image currently aliased by `ubuntu-latest` preinstalls GNU `time` (`time 1.9-0.2build1` in the 20260907.300.1 apt list), so `/usr/bin/time -v` is available on the present runner image.

Section 7 of the card proposes the job comment `Tests use committed or generated synthetic fixtures.` Stage A keeps the existing comments at `.github/workflows/ci.yml:35-36`:

```yaml
    # Campaign and repository tests use committed synthetic fixtures only.
    # This job is not result-bearing and does not read a private panel.
```

`tests/test_campaign_conformance.py:250-258` requires those three phrases and exactly one `python -m pytest -q` substring. The pytest step remains a single `python -m pytest -q -n 2 --dist worksteal` invocation (`python -m pytest -q` count is 1). This comment retention is required for the existing campaign-safety assertion and is recorded in the producer report.

`docs/repo_map.md` states that CI commands live only in `.github/workflows/ci.yml` and that the map does not duplicate them. Regenerating the map is a no-op for this delta; the file is correctly absent from the commit.

## Concurrency and resource isolation

Job-level native-thread variables apply to the validation process and its subprocesses, including xdist workers. Independent review probe on this machine:

| Environment | `threadpoolctl` OpenMP `num_threads` for sklearn |
| --- | ---: |
| Unset | 18 |
| Six CI variables set to `1` | 1 |

`--max-worker-restart=0` keeps a worker crash or OOM visible on the first attempt. `--dist worksteal` is the card's default for the measured long-tail diagnostic distribution. `-n 2` is a fixed bound; `-n auto` and `-n 4` are unused.

xdist gives each worker its own pytest temporary root. This review executed the full suite with `--basetemp=/tmp/efr-ci-review-grok-qa/full-basetemp`. After that run, `git diff --exit-code HEAD -- .` was clean and `git status --porcelain` showed only the untracked review `.venv`. Tracked fixtures, reports, and source were unchanged.

`defaults.run.shell: bash` supplies `pipefail`, so a failing pytest still fails the step when piped through `tee`. Independent probe: `bash -eo pipefail -c 'false | tee ...'` exited 1.

The 5.5 GB aggregate memory budget and GitHub `memory.peak` measurement remain same-runner rollout evidence. This review's local controller RSS was not treated as a Linux cgroup certification.

## Research-safety

The delta does not change feature, signal, rebalance, execution, or return timing. It does not add brokerage, orders, or live-account behavior. Official diagnostic artifacts and experiment logs are untouched.

The ML change is collection order of four already-supported model cases. Test bodies and production model construction are unchanged. Full-default diagnostic regressions, the M3-10 causal oracle, and campaign isolation tests ran under two-worker worksteal in this review (see QA).

## Deterministic QA

Commands ran on exact `8c859ef80de036f9839a72d4019d181180eca134` with `/private/tmp/efr-ci-review-grok-8c859ef/.venv/bin/python` and `PYTHONPATH=src:.`. Native thread variables were set to `1` for pytest and `threadpoolctl`.

Review interpreter: CPython 3.12.13, pytest 9.1.1, pytest-xdist 3.8.0, NumPy 2.5.3, pandas 3.0.6, SciPy 1.18.1, scikit-learn 1.9.1, threadpoolctl 3.7.0. CI remains Python 3.11 on `ubuntu-latest`. Local elapsed times are compatibility evidence on this machine.

```
PYTHONPATH=src:. .venv/bin/python -m ruff check .
PYTHONPATH=src:. .venv/bin/python -m compileall -q src tests research lean
PYTHONPATH=src:. .venv/bin/python -m pytest -q -n 2 --dist worksteal --max-worker-restart=0 \
  tests/test_ml_combination.py tests/test_campaign_conformance.py tests/test_campaign_runner.py \
  tests/test_project_structure.py tests/test_real_data_multifactor_diagnostic.py \
  tests/test_cross_validation.py tests/test_lean_smoke_test_scope.py
PYTHONPATH=src:. .venv/bin/python -m pytest -q -n 2 --dist worksteal --max-worker-restart=0 --collect-only tests
PYTHONPATH=src:. .venv/bin/python -m pytest -q -n 2 --dist worksteal --max-worker-restart=0 tests
```

| Command | Result |
| --- | --- |
| `ruff check .` | All checks passed |
| `compileall -q src tests research lean` | passed (exit 0) |
| `git diff --check HEAD^..HEAD` | clean |
| Three workflow `run: \|` bodies via `bash -n` | exit 0 |
| `threadpoolctl -i numpy scipy sklearn` with CI env | OpenMP `num_threads` 1 (exit 0) |
| ML collect-only under `PYTHONHASHSEED` 1, 2, 3 | identical 4 node IDs in sorted model order |
| Key suites `-n 2 --dist worksteal --max-worker-restart=0` | 164 passed in 7.67 s |
| Full collect-only serial vs xdist | 3,819 unique IDs each; sets equal; 0 duplicates |
| Full suite same xdist flags | 3,817 passed, 2 skipped, 23 warnings in 264.06 s |
| JUnit | 3,819 cases, 3,819 unique node IDs, 0 duplicates, 0 failures |
| `git diff --exit-code HEAD -- .` after full suite | exit 0 |
| `bash -eo pipefail` `false \| tee` | exit 1 |

The two skips are the existing ARM `longdouble` / `clongdouble` cases in `tests/test_backtest_timing_contract.py:1129`. The 23 warnings are the existing constant-input Spearman warnings. Longest JUnit call in this parallel run: 144.71 s (`test_multifactor_diagnostic_official_report_table_matches_default_fixture`). Worker restarts were disabled; the run completed without a crash.

Candidate SHA-256 (review-root bytes):

| File | SHA-256 |
| --- | --- |
| `.github/workflows/ci.yml` | `10134026caa4005f8c01d6843bc3fdd65be7b98d07cc2b27eaae171ae8c114e2` |
| `pyproject.toml` | `d228ab84035b7a03d50e09669ed64ebcd311f69765b5a1e508aac482808b4358` |
| `tests/test_ml_combination.py` | `fc83af6392c9280671504a1f7ef2b5f1e2538bc859c5cd1b496eb280bba28a6c` |

## Findings

MATERIAL: none.

### ADV-CIA-1 — Campaign CI pin covers safety phrases and a single pytest substring

- Severity: `ADVISORY`
- Status: `OPEN`
- Reviewer: `GROK_REVIEW`
- Candidate: `8c859ef80de036f9839a72d4019d181180eca134`
- Claim: `tests/test_campaign_conformance.py::test_ci_runs_only_committed_synthetic_campaign_fixtures` is the executable pin of `.github/workflows/ci.yml`.
- Evidence: The test (`tests/test_campaign_conformance.py:250-267`) asserts `python -m pytest -q` occurs once, forbids a campaign-only file glob, and requires the phrases `committed synthetic fixtures`, `not result-bearing`, and `private panel`. It does not assert job name `Python validation`, the six native-thread environment keys, `-n 2`, `--dist worksteal`, `--max-worker-restart=0`, `cache-dependency-path`, or the `git diff --exit-code` / artifact-upload steps. A later edit that dropped `-n 2` while keeping one `python -m pytest -q` line would still pass this test.
- Impact: Collection identity under xdist is self-detecting if workers disagree. A silent return to serial pytest, or a drop of thread clamps, would pass this pin. Correctness of the current candidate is established by the workflow bytes and the QA table above.
- Resolution: Extend the existing workflow test to assert the required check name, the six thread-limit keys equal to `"1"`, and the scheduling flags `-n 2 --dist worksteal --max-worker-restart=0`.

## Residual rollout notes

These are open Coordinator measurements already stated by the producer. They are outside this review's local evidence and do not change the MATERIAL count.

- GitHub cold-cache and warm-cache wall clocks, Linux cgroup `memory.peak` against the 5.5 GB budget, merge-group scheduling, and PR cancel-in-progress behavior require an authorized published run of this workflow.
- The 5–8 minute GitHub target remains a Stage B/C acceptance target. Two workers on the measured GitHub serial load of 2,289 s have an ideal work floor near 19 minutes. This candidate's CHANGELOG and implementation report record that gap as open.
- `timeout-minutes: 45` is the card's hang bound. The inspected GitHub serial baseline is 38 m 37 s. First published parallel runs establish whether that bound stays comfortable on the runner.
- `ubuntu-latest` is scheduled to migrate from Ubuntu 24.04 to 26.04 between 2026-10-19 and 2026-11-19. GNU `time` is present on the current 24.04 image; reconfirm `/usr/bin/time -v`, `nproc`, and `free -m` after that migration.

## Verdict

**PASS (MATERIAL: 0)**

Stage A on `8c859ef80de036f9839a72d4019d181180eca134` matches the architecture card's executable contract: `pytest-xdist>=3.5.0` in the `dev` extra, unchanged `[tool.pytest.ini_options]`, sorted ML parametrization, required check name `Python validation` on `ubuntu-latest`, two-worker worksteal with worker-restart disabled, native-thread clamps, and fail-closed `git diff` plus artifact upload. Independent local xdist execution collected 3,819 unique cases and passed 3,817 with the two existing ARM `longdouble` skips.

OPEN advisories: ADV-CIA-1. MATERIAL count is 0.

This report records the exact-head review of `8c859ef80de036f9839a72d4019d181180eca134`.

# Stage A CI Acceleration — GPT-6 Review Report

Date: 2026-09-21 UTC.
Requested seat: Reviewer 1, GPT-6 Astra, Extra High, under `prompt_dual_review_gpt6.txt`.
Reporting session: the current Codex conversation, including its preceding CI architecture-design turn.
Candidate digest: `8c859ef80de036f9839a72d4019d181180eca134`.
Parent: `3bb32dfd316bdd2a831fbe62ab961e62a0cf7689`.
Review root: `/private/tmp/efr-ci-review-gpt6-8c859ef`.

## Verdict

**FINDINGS — formal-review seat eligibility requires a fresh reviewer.**

The technical assessment found **0 MATERIAL implementation defects** and **1 ADVISORY documentation finding**. It also records **1 MATERIAL review-process finding**, R1-G01: this session authored the design card included in the candidate. The live standard requires fresh reviewers with session and context independence. This report supplies technical evidence and the eligibility finding; it cannot count as the requested fresh independent review seat.

All completed checks and their limits are recorded below. The candidate's tracked files remained unchanged. Stage B runtime optimization and the 5–8 minute GitHub target remain open as the implementation report states.

## Findings

### R1-G01 — P1 / MATERIAL / OPEN: Replace the design-author session for the formal review seat

- **Reporting session and candidate:** current Codex conversation; `8c859ef80de036f9839a72d4019d181180eca134`.
- **Affected scope:** eligibility of this report for formal acceptance of the complete candidate, including `coord/card_ci_acceleration_and_optimization.md:1`.
- **Requirement:** the [live coordinator standard, line 66](/Users/rhapsoul/Documents/Codex/Standards/herdr_pi_coordinator_v7_two_file/coordinator.md:66) states: “Formal reviewers are visible, fresh, read-only, outside producer lineage, and mutually blind during initial review.” Line 67 requires session and context/lineage independence; line 103 requires eligible review seats for acceptance.
- **Evidence:** the preceding turn of this same conversation authored the design card. The candidate includes that complete 525-line card. Its SHA-256 is `63ff019dc8168133b496183db79db384bcde74de5ff87a529513e59236f54db1`, identical to this session's delivered design artifact. This session therefore retains producer context for bytes inside the reviewed commit. The implementation itself was produced separately; that distinction leaves the complete-candidate freshness requirement unsatisfied.
- **Impact:** counting this report as a fresh independent seat would misstate the required review coverage. Passing machine checks and a separate review worktree establish useful correctness evidence, while session independence remains a separate gate.
- **Resolution condition:** obtain the requested seat from a fresh reviewer outside the design/implementation producer context, on the exact frozen candidate or a subsequently identified replacement candidate. Preserve this report and its QA as explicitly scoped supporting evidence. This finding requires review reassignment rather than a source-code change.

### R1-A01 — P2 / ADVISORY / OPEN: Correct the reversed numerical comparisons in the implementation report

- **Reporting session and candidate:** current Codex conversation; `8c859ef80de036f9839a72d4019d181180eca134`.
- **Affected claims:** `coord/reports/ci_acceleration_impl_report.md:23` and `coord/reports/ci_acceleration_impl_report.md:163`.
- **Evidence and mismatch:** lines 23–24 say the 420-second test budget “already exceeds” the two-worker work floor, although the preceding sentence gives that floor as 1,144.64 seconds. The correct comparison is `420 < 1144.64`. Line 163 says the 268.59-second parallel wall clock “is 1.94x” the 521.23-second serial wall clock. The elapsed-time ratio is `268.59 / 521.23 = 0.5153`; the reciprocal `521.23 / 268.59 = 1.9406` describes the nominal speedup.
- **Impact:** the capacity comparison and elapsed-time wording invert the meaning of their measurements. The same report correctly retains the approximately 19-minute two-worker floor and the open GitHub target elsewhere, so this finding has advisory impact on the current Stage A implementation.
- **Recommended correction:** state that the 420-second budget falls below the 1,144.64-second floor, and that the recorded parallel run took 51.53% of the cited serial duration, corresponding to a nominal 1.94x speedup across the disclosed different environments. Preserve the existing environment and same-runner caveats.
- **Resolution condition:** correct those comparisons in a later documentation update, retaining the original measured values and provenance.

## Clean-root and environment verification

The supplied worktree was detached at the exact candidate and had no tracked changes. Initial `git status --porcelain=v1` showed one untracked environment entry: `.venv`, a symlink to the producer's environment. Candidate sources were separate from the producer worktree.

The supplied symlink was preserved at `/private/tmp/efr-ci-gpt6-review-evidence-8c859ef/original-venv-link`. A dedicated, ignored `.venv/` directory was created in the review worktree with CPython 3.11.15, and the candidate's `.[dev]` extra was installed there. This left `git status --porcelain=v1` empty before substantive QA and avoided changing the producer environment. The environment-setup record preserves the original link target. The review root retains the dedicated environment for reproducibility.

Imports resolved to the review checkout. QA used `PYTHONPATH=src:.` and the requested `.venv/bin/python` command form. The six numerical thread variables from the workflow were set to `1` before pytest startup. Review-platform details:

| Component | Version / value |
| --- | --- |
| Python / OS | CPython 3.11.15; macOS ARM64 |
| pytest / xdist | 9.1.1 / 3.8.0 |
| NumPy / pandas / SciPy | 2.4.6 / 3.0.6 / 1.17.1 |
| PyArrow / scikit-learn | 25.0.1 / 1.9.1 |
| Ruff / build | 0.16.8 / 1.6.1 |
| Reported OpenMP thread count | 1 under the workflow environment |

The interpreter minor version matches CI's configured Python 3.11. Ubuntu execution, Linux numerical backends, and aggregate runner memory remain distinct validation surfaces.

## Design fidelity and scope coverage

| Checkpoint | Candidate evidence | Assessment |
| --- | --- | --- |
| Dev dependency | `pyproject.toml:34–40` | Exactly `pytest-xdist>=3.5.0` added to dev; runtime dependencies preserved |
| Local pytest behavior | `pyproject.toml:48–51` | Parsed pytest configuration exactly matches the parent: `tests`, `src`, `-ra`; local default remains serial |
| Deterministic collection | `tests/test_ml_combination.py:126` | Uses `sorted(_SUPPORTED_MODELS)`; the production set and test bodies are unchanged |
| Stage A workflow | `.github/workflows/ci.yml:1–95` | Executable YAML matches the design's first workflow after excluding comments and blank lines |
| Required check | `.github/workflows/ci.yml:31–34` | Job ID `validation`, name `Python validation`, `ubuntu-latest`, 45-minute hang bound preserved/specified |
| Triggers and cancellation | `.github/workflows/ci.yml:3–16` | PR/main triggers, merge-group eligibility, PR-scoped cancellation; unique non-PR run groups |
| Resource controls | `.github/workflows/ci.yml:18–24,79–80` | Six native thread limits plus two xdist processes; worksteal; zero automatic worker restarts |
| Dependency cache | `.github/workflows/ci.yml:42–52` | Existing pip cache retained, explicit pyproject hash, fresh editable installation, binary preference |
| Validation coverage | `.github/workflows/ci.yml:64–82` | Ruff, source/tests/research/LEAN compilation, isolated distribution build, complete pytest discovery |
| Failure propagation | `.github/workflows/ci.yml:26–28,76–95` | Explicit bash shell, no `continue-on-error`, pytest pipeline, always-run tracked-input check and evidence upload |
| Evidence isolation | `.github/workflows/ci.yml:54–62,78–95` | Metadata, resource log, JUnit and pytest log under runner temp; unique run/attempt artifact name |
| Repository map | `scripts/repo_map.py:254`, `docs/repo_map.md` | Read-only regeneration produced byte-identical content; absence of a map diff is justified |
| Research behavior | Parent-to-candidate source diff | No changes under `src/`, `research/`, or `lean/`; only one test parametrization line changes under `tests/` |
| Deferred stages | Implementation report scope and caveats | Stage B kernels and Stage C lanes remain unactivated; target achievement remains explicitly open |

The sole intentional difference from the design's executable-workflow presentation is retention of the existing campaign-safety comments at `.github/workflows/ci.yml:35–36`. `tests/test_campaign_conformance.py:250–267` requires those phrases and one complete pytest invocation. Keeping them preserves the existing conformance test and safety statement. This is an appropriate compatibility adjustment within Stage A.

No new path filters, test selection, global xdist addopts, broad shared-output fixtures, additional cache owner, remote-data access, or runtime research changes appear in the candidate.

## Failure behavior and isolation assessment

The explicit Actions `bash` shell supplies `-e` and `-o pipefail`. A failed pytest process therefore fails the piped step even when `tee` succeeds. A local shell probe retained exit code 7 through the output pipe. The workflow has no `continue-on-error` override, and ordinary job failure remains the required check result. [GitHub workflow shell semantics](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax).

The `git diff --exit-code HEAD -- .` step runs under `always()` and checks tracked candidate changes. Its scope is tracked-file integrity; untracked output detection is a separate concern. Current report/ledger tests use their temporary destinations, and the complete test run preserved tracked content.

Artifact upload also runs under `always()`. An upload-action error fails its step. `if-no-files-found: warn` intentionally tolerates absent evidence after earlier setup failures; those earlier failures still fail the job. Artifact absence by itself is consequently a warning under this configuration. Network upload, workflow cancellation, and actual check publication were assessed from configuration and documented semantics, with no hosted workflow dispatched in this review. [upload-artifact v4 behavior](https://github.com/actions/upload-artifact/tree/v4).

Sorting the four supported model names fixes the known cross-worker collection mismatch. Collection of the eight ML cases was identical under hash seeds 1, 2, and 3. Existing explicit seeds, function-scoped temporary paths, campaign ledger redirection, and subprocess isolation were exercised through the complete suite. xdist's requirement for matching collection across workers is directly relevant to the changed line. [xdist collection limitations](https://pytest-xdist.readthedocs.io/en/stable/known-limitations.html).

Native thread limits constrain the listed BLAS/OpenMP backends; two xdist processes constrain the top-level test scheduler. They establish a configured bound for those mechanisms. Linux process-tree/cgroup peak memory and any additional library thread pools still require runner measurements. The 5.5-GB acceptance budget remains an implementation-rollout measurement.

## Deterministic verification

All commands ran from the stated review worktree at the candidate digest. Logs are under `/private/tmp/efr-ci-gpt6-review-evidence-8c859ef/`.

| Check | Result |
| --- | --- |
| `PYTHONPATH=src:. .venv/bin/python -m ruff check .` | PASS; all checks passed |
| `PYTHONPATH=src:. .venv/bin/python -m compileall src tests research lean` | PASS |
| actionlint 1.7.12 on the candidate workflow | PASS |
| Three multiline workflow shell bodies via `bash -n` | PASS |
| Parsed TOML comparison to parent and normalized workflow comparison to design | PASS |
| ML collection with hash seeds 1, 2, 3 | PASS; identical eight node IDs |
| Failure through `tee` using explicit fail-fast/pipefail bash | PASS; exit 7 retained |
| `.venv/bin/python -m build --outdir <review-evidence>/dist` | PASS; wheel and sdist produced |
| Wheel and sdist ledger package data | PASS; all 20 schema JSON/hash payloads exactly match the candidate |
| Complete two-worker suite, including all requested key tests | PASS; 3,817 passed, 2 existing skips, 23 warnings in 279.83 s |
| JUnit membership/outcome comparison and uniqueness | PASS; 3,819 unique cases, zero duplicates; identities and outcomes match both serial baseline and producer; all 164 named key cases included |
| Tracked-content integrity and final exact HEAD | PASS; empty porcelain status and unchanged exact candidate digest after QA |
| Parent-to-candidate `git diff --check` | PASS |

The two skips are the existing ARM extended-precision cases at `tests/test_backtest_timing_contract.py:1129`. The 23 warnings are constant-input Spearman warnings. The longest test call was the full-default diagnostic regression at 146.52 seconds.

The complete test command was:

```bash
PYTHONPATH=src:. \
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
BLIS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 NUMEXPR_NUM_THREADS=1 \
/usr/bin/time -l .venv/bin/python -m pytest -q \
  -n 2 --dist worksteal --max-worker-restart=0 --durations=20 \
  --junitxml=/private/tmp/efr-ci-gpt6-review-evidence-8c859ef/pytest.xml
```

Output was piped through `tee` with pipefail enabled. The macOS `time -l` wrapper records local execution; CI's GNU `time -v` wrapper requires Ubuntu validation. The complete suite covers the producer's seven named key modules, the full 756x50 synthetic diagnostic regression, and the M3-10 causal-perturbation oracle.

The producer's supplied pytest log and JUnit hashes matched its implementation report. Those historical measurements provide supporting evidence. The results above were generated again from the exact candidate with this review environment. Build and brief metadata probes overlapped the local test run; its timing is a compatibility observation rather than an isolated speedup experiment.

## Ablation and remaining gates

The candidate introduces three narrow executable changes and retains the design's existing cache owner and single-job structure. Its ablation section records retained necessities: sorted collection, thread bounds, evidence/failure handling, and campaign-safety comments. The design card contains the scheduling model and the failed unordered-collection baseline. This read-only assessment introduced no design or implementation change requiring a new removal experiment.

The hosted rollout still needs cold/warm timing, Linux memory measurements, PR supersession/cancellation behavior, merge-group behavior where used, and actual artifact/check publication. The current report correctly leaves the 5–8 minute target open. Those observations remain rollout evidence; no hosted performance or memory certification is claimed here.

The remaining formal-review gate is R1-G01. A fresh eligible reviewer must complete the requested independent seat. The advisory documentation correction is recorded separately from implementation correctness.

## Evidence identities

| Artifact | SHA-256 |
| --- | --- |
| `pytest.log` | `a98ea65171a0cfb8bfcb3c656547a6a77b3bd3f777ed37db2450830c6c07acb6` |
| `pytest.xml` | `7e6b459091bd42fdeca898856da9251dfa07673c9d052e2911bbb68b5334d261` |
| `verification.json` | `4632f9eab0c537905f2cfec6cf4fab8c890532884464ea2e4910412c1a4cea47` |
| `ruff.log` | `82b3e6a6c090a57601d22943bd23fca9218d1031dbe5a7b754092f9a156b4f18` |
| `compileall.log` | `bf3568e7daa8103b38e8a8114c6474aabe30b2f6c6e7247a06e6b4500264100d` |
| `build.log` | `e48bf691971bdc08a97deff471214c41c9a587f6139877d7aa5715fd7d7f7bbd` |

The report is written outside the frozen review candidate. Candidate code, configuration, tests, documentation, and tracked fixtures remain at `8c859ef80de036f9839a72d4019d181180eca134`.

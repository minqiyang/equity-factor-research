# Troubleshooting Log

## 2026-08-22 - Invented recognizer grammar vs real interval gap

Original failures and consequences:

- Union readjudication v1 reported C01 fail-closed for every identity. QA
  passed. Independent review found the detector used a private annotation
  language with no EDGAR referent, so the 1194 bodies were not evaluated.
- The replacement EDGAR-referential runner constructed 6024 filed-text
  records and still accepted zero identities. Almost all iXBRL durations are
  same-day contexts and do not cover the requested multi-year interval.
- Authorizing exchange listing records alone cannot cover C01 issuer and
  instrument primitives. Do not treat a second retrieval as a fix for that
  gap.

Resolution:

- Keep v1 as a frozen failed lineage. Keep v2 as the terminal fail-closed
  record under the current policy. Publish only aggregates and hashes.


## 2026-07-31 - Premature Review-Wait Completion Recovery

Original failures and consequences:

- After posting `@codex review` for `6a7445f`, the task created a bounded
  monitor and sent a final response while the review was still pending. The
  owner correctly identified that the requested terminal condition had not
  been reached and had to resume the task manually.
- The first combined reread of AGENTS, handoff, controller, and roadmap
  exceeded its output budget. No truncated portion was used as evidence.
- Invoking the thread-aware helper with `--help` unexpectedly executed its
  authentication preflight. The sandbox could not read the GitHub keyring, so
  the command failed without reading review state or changing files.
- The first two focused structure runs after editing failed only phrase
  assertions because the asserted text crossed Markdown line wraps or used a
  plural where the policy used a singular. The new three-month turnover
  mutation oracle, YAML parse, Ruff, and diff checks did not fail.
- The first focused run for the fifth-review benchmark-routing fix likewise
  failed only a structural phrase split across `primary-` and `benchmark`.
  The next two retries found the same line-wrap and capitalization issue in
  the handoff's committed-head and remaining-gate phrases. Both benchmark
  final-state behavior fixtures passed throughout.
- The sixth-round helper retrieval reported output truncation at the outer
  tool layer. The complete JSON file had been written successfully, so its
  validity and exact two new review threads were checked with bounded `jq`
  reads before it was used.
- The temporary worktree had neither a `python` alias nor pytest installed in
  Homebrew `python3`; both commands failed before collecting tests. Validation
  resumed with the repository's existing virtual-environment interpreter.
- A piped full-suite run completed without returning its final output chunk,
  so it was not counted. A direct full-suite rerun returned an exit-zero
  summary and established the test result.
- The first sixth-round Ruby safe-load omitted `Date` from the permitted class
  list and rejected existing date scalars. A corrected safe-load explicitly
  permitted `Date`, retained aliases-disabled behavior, and parsed the file.
- The first isolated build could not resolve declared build requirements in
  the network-restricted sandbox. The identical build was rerun with approved
  dependency-download access and succeeded without publishing artifacts.
- The first heartbeat-creation call used lowercase `active`, and the second
  omitted its thread destination; the app rejected both before creating
  anything. The third call used the accepted active status and thread
  destination, creating exactly one monitor. It was deleted immediately when
  the seventh-review finding arrived.
- The first ninth-round focused run failed only because a contract phrase
  assertion crossed a Markdown line wrap. The simple-return, forbidden-log,
  and invalid-anchor calculations passed. The assertion was narrowed to a
  same-line semantic fragment without weakening the protocol.
- The first tenth-round final gate failed only because the handoff split
  `exact-head` across a Markdown line. The forward-return and shared-bootstrap
  fixtures passed. The handoff was rephrased without a split token and the
  assertion retained the full CI/head meaning.
- The first eleventh-round focused run failed only because a new contract
  phrase crossed a Markdown line wrap. All MOM/REV mutation cases passed. The
  assertion was split into stable numerator/denominator and rank-exclusion
  fragments without weakening the rule.
- The first eleventh-round parallel privacy and Unicode scan call exceeded the
  outer tool output budget. No scan result from that call was accepted; each
  scan was rerun independently with bounded output before verification.
- The twelfth exact-head review found that `required_history_price_anchors`
  could imply full-window observed-price completeness even though MOM/REV use
  only two formula endpoints. The field was not retained with an explanatory
  comment; it was replaced by separate calendar-position-span, observed-anchor
  count, and interior-missing-action fields plus discriminating fixtures.
- The first twelfth-round YAML/JSON check used the repository venv, which does
  not include PyYAML, and failed before parsing. The initial Ruby fallback then
  checked `semantic_trial_count` at the document root instead of under
  `campaign` and also failed without modifying files. The corrected Ruby safe
  load permits existing `Date` scalars, disables aliases, checks the nested
  campaign count, and reconciles all 14 JSON trial records.
- The thirteenth review showed that defining endpoint-only formulas was not
  sufficient while the shared eligibility helper still tested a generic full-
  history flag. The helper, YAML inputs, and contract were changed together,
  and the regression fixture now exercises eligibility, target, and benchmark
  outputs rather than only formula values.
- The same review found the YAML prospective rule narrower than the contract.
  Both now use the latest of all three required freeze timestamps and a strict-
  after boundary, with a staggered timestamp fixture.
- The first thirteenth-round push returned without diagnostic output but left
  the remote-tracking ref unchanged. A direct retry then surfaced GitHub's
  `Recv failure: Operation timed out`; no remote commit was partially accepted.
  The unchanged local/remote SHAs were verified before retrying rather than
  assuming the silent command had succeeded.
- The first fourteenth-round focused run failed only because the structural
  assertion still named the superseded singular eligible-signal start rule.
  The new common-factor eligibility boundary and all baseline invalid-case
  fixtures passed. The assertion was updated to the exact frozen common-
  predicate start rule without weakening it.
- The post-log focused rerun then found the handoff had wrapped `current-head`
  across a line. The handoff was rephrased as exact-head CI on the current head
  followed by current-head review, and the assertion now checks those stable
  semantic fragments.
- The fourteenth review exposed two places where a locally correct rule still
  lacked campaign-level aggregation: factor-specific eligibility had no common
  prospective clock, and strategy invalid-month triggers did not reach the
  baseline outputs. The fixes therefore bind each rule across its downstream
  consumers and use integrated rather than phrase-only mutation fixtures.
- The first combined fifteenth-round patch was rejected because one expected
  bootstrap sentence did not match the current contract wording. The rejected
  patch changed no file. It was split into exact YAML, contract, and test
  patches and each applied successfully.
- The P1 showed that `min(6,n)` is not a safe short-segment rule: it collapses
  every `n<=6` start range to zero and copies the segment. The corrected fixture
  uses a full 60-record admissible sample, not a tiny smoke case, and also tests
  the explicit singleton degeneracy gate.
- The sixteenth review exposed an overgeneralization from the fourteenth-round
  fix: propagating factor invalidity to both baselines also converted the
  invested equal-weight primary benchmark to cash. The correction separates
  the benchmark/equal-weight path from the random-rank/factor path and tests
  their economic outputs together.
- The same review showed that documenting bootstrap degeneracy was insufficient
  while the executable classifier helper lacked that coverage input. The input
  and ordered boundary cases now fail closed without changing hard-validity
  precedence.
- The first sixteenth-round focused command addressed a nonexistent worktree-
  local `.venv/bin/python` and exited before collection. Validation resumed
  with the repository's existing project virtual environment; no failed or
  partial test result was counted.
- The next focused run passed all behavioral fixtures and failed only because a
  structural contract phrase crossed a Markdown line wrap. The assertion was
  narrowed to the exact invested-benchmark active-return values without
  weakening the economic mutation check. Its retry then reached a second stale
  whole-sentence assertion split by the rewritten paragraph; that assertion was
  separated into stable adjacent semantic fragments.
- The first isolated sixteenth-round build could not resolve its declared
  setuptools/wheel requirements in the network-restricted sandbox. The exact
  build was rerun with approved dependency-download access and produced both
  sdist and wheel without publishing either artifact.
- The seventeenth review confirmed that excluding an invalid factor month from
  final-state support is not a complete rule for a stateful continuous path.
  The correction keeps the row and every surrounding state transition in one
  annualization path, and the classifier fixture proves that filtering could
  reverse the final label.
- The same review found that factor-label completeness does not imply a later
  monthly strategy execution exists inside the cutoff. Continuous-schedule
  inclusion is now calendar-filtered before target freeze, so the boundary is
  structural rather than a hard-invalid missing strategy path.
- The first seventeenth-round focused run passed both new behavioral fixtures
  and failed only because one structural contract assertion crossed a Markdown
  line wrap. It was split into adjacent calendar-schedule fragments without
  weakening the boundary rule.
- The first eighteenth-round focused run passed the canonical-instant and
  threshold-maturity fixtures but reached structural assertions for the
  superseded date/phase-ambiguous prospective wording. Those assertions were
  replaced with stable UTC-close and output-maturity fragments.
- The eighteenth review showed that a strict greater-than sign is insufficient
  unless both operands use a canonical instant. The freeze and signal sides now
  fail closed to comparable UTC instants, with explicit same-day phases.
- It also separated prospective count from evidence availability. The threshold
  count remains stable, but access waits for both final factor and strategy
  outputs rather than choosing one endpoint implicitly.
- The first eighteenth-round count-update patch contained an extra hunk marker
  and was rejected without changing a file. The corrected two-file patch then
  updated the verified counts.
- The nineteenth review found that freezing runner code is not equivalent to
  completing the detached execution binding. The prospective anchor now waits
  for the full configuration/environment/data binding, and a staggered fixture
  rejects the code-only start.
- The first nineteenth-round focused run passed the staggered binding fixture
  and failed only because the expanded contract moved a line break inside one
  UTC-close phrase assertion. The assertion was split into adjacent stable
  fragments.
- The twentieth review exposed a liveness contradiction between an exact frozen
  data identity and future data arrival. The binding now fixes the immutable
  seed and succession rules, while each future batch supplies its own chained
  content address without moving the anchor.
- The twenty-first review showed that scalar-valid price endpoints plus a
  resolved signal listing still leave the lookback join ambiguous. The factor-
  anchor policy now binds every endpoint to accepted permanent-security,
  listing, and listing-episode IDs, permits only evidenced same-episode symbol
  renames, and rejects an otherwise numerically valid reused-ticker return.
- The twenty-second review exposed an unbound field in the stateful continuous
  path: factor inputs and episodic labels used adjusted close, but strategy and
  primary-benchmark held returns did not. One shared adjacent adjusted-close
  simple-return policy now controls both paths, with a split fixture proving
  raw close would change gross return, drifted turnover, cost, and active
  return.
- The twenty-third review exposed the converse path-boundary risk: a required
  21-row baseline episode could be implemented by slicing the newly frozen
  continuous path. The episode now holds its signal-time target through
  `e+21` regardless of an earlier monthly reset, and invalid constituents fail
  the whole weighted diagnostic instead of changing its universe.
- The twenty-fourth review exposed truncation bias in the long-segment
  bootstrap: non-circular starts plus a partial final block gave a seven-row
  segment expected weights `[1,1.5,1,1,1,1,0.5]`. The fix uses circular starts
  across all positions, confines wrap to the current segment, and adds a
  63-record exhaustive null-mean golden rather than relying on seeded spot
  draws alone.

Investigation:

- Deleted the bounded monitor so it could not race the resumed active task.
- Re-read every required canonical workflow source in independent bounded
  ranges.
- Re-ran the thread-aware helper with approved keyring/network access and
  separately inspected the exact-head review, inline comments, and request-
  comment reactions.
- Confirmed the review completed on exact head `6a7445f` and created two new
  current P2 threads: `PRRT_kwDOSkphKc6VluEc` and
  `PRRT_kwDOSkphKc6VluEd`.
- Continued the same active loop through `e5d72c2`; its review completed with
  benchmark-routing P2 thread `PRRT_kwDOSkphKc6Vl0hK` rather than being
  mistaken for a clean terminal result.

Correction:

- Kept the resumed task active and entered the remediation loop instead of
  returning another pending-gate final response.
- Froze the immediate scheduled decision-time predecessor for factor turnover
  and added the required outcome-invalid-middle-month mutation fixture.
- Corrected the stale handoff and changed the review wait policy so monitor
  creation or exhaustion cannot be treated as task completion.
- Replaced the brittle whole-phrase assertions with stable semantic fragments
  and matched the policy's singular wording; no protocol or workflow rule was
  weakened.
- Split the benchmark-routing assertion into stable adjacent semantic
  fragments and normalized handoff whitespace before checking its full
  semantic phrases; no protocol or handoff rule was weakened.
- Used the repository virtual environment for every evidentiary Python check,
  required an explicit final pytest summary, and reran YAML/build checks with
  the narrow environment permissions their declared dependencies required.
- Aligned both aggregate and security-level cost effects to the accepted gross
  multiplier and froze the random-rank continuous baseline at primary 10 bps
  without expanding the 14-trial inventory.
- Froze the random permutation's date token, rank direction, remainder-aware
  first-chunk selection, weights, and serialization, with a full non-divisible
  golden fixture.
- Removed Holm's index ambiguity by freezing one-based mathematical positions,
  Python `k-1` access, the sorted running maximum, and factor-order mapping.
- Froze `LOW_VOL_3M` to simple adjacent-price returns and fail-closed anchor
  validity, with a simple-versus-log and invalid-anchor mutation fixture.
- Froze diagnostic endpoint returns to fail-closed simple returns and reused
  one bootstrap index draw across uncentered and null-centered distributions.
- Applied the strict fail-closed price-anchor gate to every MOM/REV numerator
  and denominator, with per-position invalid-anchor mutations.
- Separated MOM/REV calendar-position lookback spans from observed-price
  completeness and froze unreferenced interior missing prices as irrelevant to
  the endpoint-only factor values and eligibility.
- Propagated that endpoint-only rule through the integrated decision-time
  eligibility/target path and bound prospective counting to every required
  freeze rather than protocol freeze alone.
- Froze the prospective clock to all-three-factor decision-time validity. The
  random baseline inherits the three invalid-rebalance triggers, while the
  equal-weight baseline and primary benchmark preserve their separately frozen
  invested-universe return object.
- Added genuine short-segment bootstrap draws plus a degeneracy coverage gate,
  and froze listing keys once at campaign-wide earliest any-factor eligibility.
- Bound that degeneracy gate into classification and added a tied-month fixture
  that rejects a cash substitute for the equal-weight primary benchmark.
- Replaced invalid-month economic exclusion with a single unfiltered continuous
  path and excluded no-next-execution boundary signals before continuous-target
  freeze.
- Canonicalized every prospective freeze/signal comparison to UTC and delayed
  threshold opening until both last-period output windows mature.
- Added completed detached-run-binding time to the prospective maximum anchor.
- Split prospective data binding into immutable seed and append-only batch
  succession so new observations can accumulate under the original anchor.

Verification:

- The latest corrected focused structure suite passed 67 tests and the full
  suite passed 3094 tests with two platform-conditional skips. Full Ruff,
  compileall, Skill audit, YAML and JSON parsing, deterministic repo-map
  regeneration, `git diff --check`, added-line privacy and Unicode/control
  scans, and isolated sdist/wheel build passed.

Remaining caveats:

- Historical review threads remain read only and unresolved.
- PR #177 must pass exact-new-head CI and a new current-head Codex review; any
  actionable finding restarts the loop.

Prevention:

- Check the requested outcome, not the existence of a waiting mechanism,
  before sending a final response.
- Treat an eyes/processing reaction, missing exact-head review, or pending
  review object as active work.
- After any output truncation, reread required sources independently before
  relying on them.

---

## 2026-07-31 - PR 177 Missing Worktree And Bounded-Read Recovery

Original failures and consequences:

- The former temporary worktree directory no longer existed, although Git
  still registered it as a prunable worktree at `4d832c7`. The first
  skill/handoff read therefore failed before reading or modifying any file.
- The root checkout remained stale and dirty with unrelated user files, so it
  could not safely host the remediation.
- The first `git worktree add --force` attempt could not write root Git
  metadata inside the sandbox and failed with `Operation not permitted`.
- A later combined AGENTS/handoff read exceeded the output budget. Its
  truncated handoff portion was not accepted as evidence.
- The first Ruby YAML check used a `safe_load_file` method unavailable in the
  installed Psych version. It did not modify repository files and did not
  establish a parse result.
- The first isolated sdist/wheel build could not resolve its declared build
  requirements in the network-restricted sandbox. It did not establish a
  package-build result.
- The sandboxed GitHub authentication check could not read the keyring and
  reported the active token as invalid. It did not change local or remote
  authentication state.

Investigation:

- Read `git worktree list --porcelain`, root status, the retained branch ref,
  and recent history without switching, cleaning, or editing the root.
- Confirmed the PR branch and remote head both pointed to `4d832c7` and that
  protected `origin/main` remained `6386c59`.
- Deleted the old five-minute review monitor because actionable findings had
  arrived.
- Re-read the full handoff, controller, roadmap, specification, and repo map in
  independent bounded ranges.

Correction:

- Re-ran the same worktree-add command with approved Git-metadata access and a
  new explicit temporary-worktree target.
- Used only the recreated clean worktree for the two P2 fixes.
- Switched from combined long reads to independent bounded ranges after the
  first truncation.
- Re-ran the YAML check with `YAML.safe_load(File.read(...))`, preserving the
  same safe-load and no-alias constraints supported by the installed parser.
- Re-ran the same isolated package build with approved network access only for
  the declared setuptools and wheel requirements.
- Re-ran the same read-only GitHub authentication check with approved keyring
  access; it confirmed the active `minqiyang` account and required scopes.

Verification:

- The recreated worktree started clean on
  `codex/eodhd-diagnostic-scope-reset@4d832c7` and matched the remote branch.
- Thread-aware review retrieval identified exactly the two new current P2
  findings linked by the owner.
- The corrected focused structure suite passed 48 tests; the full suite passed
  3075 tests with two platform-conditional skips. Full Ruff, compileall, Skill
  audit, YAML and JSON parsing, deterministic
  repo-map regeneration, `git diff --check`, added-line privacy and
  Unicode/control scans, and isolated sdist/wheel build passed.

Remaining caveats:

- Review threads remain read only and unresolved.
- A new review monitor will be created only after the remediation is pushed,
  exact-head CI passes, and one new `@codex review` request is posted.

Prevention:

- At every scheduled continuation, verify a temporary worktree path still
  exists before using it and recreate it from the retained branch when it is
  prunable.
- Never recover a missing isolated worktree by editing the dirty root checkout.
- After one truncation, read each required canonical source in separate bounded
  ranges rather than repeating a combined read.

---

## 2026-07-29 - PR 177 Second-Review And Local-Validation Recovery

Original failures and consequences:

- The second exact-head Codex review at `97425c0` found three P2 gaps: the
  low-volatility slice excluded `t` and contained 62 rather than 63 returns;
  `invalid_rebalance` did not enumerate its zero-target conditions; and the
  required JSON preregistration child was not bound to the frozen YAML.
- Two combined controller/roadmap reads exceeded the output budget. Their
  truncated content was not accepted as evidence.
- The review-comment helper was first invoked with `python`, which is not on
  this shell's `PATH`. Its sandboxed `python3` attempt could not see the GitHub
  keyring, and the first focused-test command incorrectly assumed the linked
  worktree contained `.venv/bin/python`.
- The first focused test run after editing failed one structural assertion
  because the asserted sentence crossed a Markdown line wrap. The behavioral
  LOW_VOL, zero-target, future-mutation, and hash oracles did not fail.
- The first isolated sdist/wheel build could not resolve the package index in
  the network-restricted sandbox, so it did not establish a build result.

Investigation:

- Re-read only the controller stop/review section and roadmap Track A/review
  section in bounded ranges.
- Verified GitHub CLI authentication outside the sandbox and used the bundled
  thread-aware GraphQL helper. It reported seven unresolved threads: two
  outdated first-round threads, two first-round threads already remediated by
  the current head, and the three current second-round P2 findings.
- Inspected the exact contract, YAML, target-construction test oracle, evidence
  artifact list, handoff, and active governance text before editing.
- Located the existing virtual environment in the preserved root checkout and
  used its absolute interpreter path from the isolated worktree.

Correction:

- Pinned `LOW_VOL_3M` to `[t-62:t+1]`, exactly 63 returns and 64 anchors.
- Enumerated the three signal-time zero-target conditions and explicitly
  prohibited post-signal missingness from changing a nonselected security's
  target, liquidation, or cash path.
- Required an exact-byte YAML bundle child with a detached-hash equality rule
  and a tampered-field hash test.
- Added automatic in-scope review remediation plus the bounded five-minute and
  thirty-minute scheduled-wait rules to `AGENTS.md` and aligned the controller,
  roadmap, and handoff.
- Replaced the brittle whole-sentence structural assertion with stable semantic
  fragments; no production or research rule was weakened.
- Re-ran the same isolated package build with approved network access only for
  its declared setuptools and wheel build requirements.

Verification:

- The corrected focused project-structure suite passed 46 tests.
- The full suite passed 3073 tests with two platform-conditional skips.
- Full Ruff, compileall, Skill audit, Ruby standard-library YAML parsing, exact
  14-trial JSON parsing, deterministic repo-map regeneration, `git diff
  --check`, added-line privacy and Unicode/control scans, and isolated sdist/
  wheel build passed.

Remaining caveats:

- GitHub review threads were read only. They were not replied to or resolved.
- Draft PR #148 still contains an older `AGENTS.md` edit and now requires a
  rebase plus semantic comparison before future use.
- The five-minute review monitor is not created while findings are being fixed.
  It is created only after the corrected exact head has stable CI and one new
  `@codex review` request.

Prevention:

- Express rolling-window bounds in the implementation language's exact slice
  convention and pair them with a hand-calculated anchor-count oracle.
- Enumerate every state transition trigger and explicitly state which later
  observations cannot rewrite a frozen decision.
- Bind the actual frozen artifact bytes into the evidence bundle; do not rely
  on an undefined format conversion.
- Use targeted reads after the first truncation, the root virtual environment's
  absolute interpreter path in linked worktrees, and short stable documentation
  assertions.

---

## 2026-07-29 - PR 177 Final-Review Protocol Remediation

Original failures and consequences:

- The first exact-head GitHub Codex review of PR #177 found two P1 and two P2
  protocol gaps after the local adversarial rereview had reported no
  actionable issue. The draft conditioned eligibility on future execution and
  endpoint availability, enumerated final states without deterministic
  assignment, left listing-key bytes implementation-dependent, and did not
  define whether fixed-bps costs were all-in.
- The first two focused-test reruns used literal assertions that crossed
  Markdown wrap boundaries. Each failed one string-presence assertion while
  the behavioral oracles passed; neither failure was accepted as validation.
- The first isolated package build could not resolve the package index inside
  the network-restricted sandbox while creating its temporary build
  environment. It changed no tracked file and did not establish a build
  result.

Correction:

- Split decision-time eligibility from outcome observation. Freeze ranks,
  deciles, targets, and matched-benchmark membership at signal close and route
  all later missingness through explicit invalidation.
- Added a versioned NFC/UTF-8/length-prefixed listing-key encoding, immutable
  first-eligibility endpoint semantics, and golden fixtures for ASCII,
  decomposed/composed Unicode, strict dates, and null ends.
- Defined every bps case as one all-in diagnostic cost with no separately
  added friction and added hand-calculated turnover fixtures.
- Added an ordered final-state decision tree plus a table-driven reference
  oracle covering hard-invalid, coverage/minimum-sample, strict-zero,
  negative, mixed, and positive boundaries.
- Shortened the two brittle phrase checks to stable same-line fragments.
- Re-ran the same isolated build with approved network access only for its
  temporary setuptools/wheel requirements.

Verification:

- Thread-aware GraphQL inspection confirmed exactly four current unresolved
  review threads before editing.
- The corrected focused suite passed 42 tests. The full suite passed 3069
  tests with two platform-conditional skips.
- Ruff, compileall, standard-library YAML parsing, exact 14-trial JSON
  validation, Skill audit, deterministic repo-map regeneration, sdist/wheel
  build, diff checks, and added-line privacy and Unicode/control scans passed.

Prevention:

- Treat future availability as an outcome state, never as a decision-time
  membership or ranking input.
- Require every preregistered result label to have an exhaustive ordered
  assignment oracle before result access.
- Freeze both serialization bytes and economic cost composition, not only
  logical field names and scalar rates.
- Keep Markdown literal assertions short enough that line wrapping cannot
  create false structural-test failures.

## 2026-07-29 - Scope-Reset Isolation And Audit Corrections

Original failures and consequences:

- The root checkout was `main@7ec6ec0`, 107 remote commits behind protected
  main, with 43 modified or untracked entries. Editing or switching it would
  have risked mixing or overwriting user work.
- The first broad combined orientation read exceeded the bounded output. The
  truncated sections were not accepted as complete evidence.
- A bare `python -m pytest -q` command failed because this shell has no
  `python` executable on `PATH`. It made no repository change and was not
  reported as a test failure.
- The first YAML parse check used `import yaml`, but PyYAML is not installed in
  the existing project environment. No dependency was installed or added.
- Initial capability/statistics audit notes accidentally relied on the stale
  dirty checkout and its one-row private diagnostic instead of protected
  `origin/main` and the owner's 21-row campaign protocol.

Correction:

- Fetched remote refs read-only, verified PR #176 through GitHub metadata, and
  created an isolated linked worktree from exact `origin/main=6386c59`.
- Re-read only targeted roadmap, handoff, controller, specification, and test
  ranges after the truncated orientation command.
- Re-ran validation with the repository's existing `.venv/bin/python`
  interpreter.
- Parsed the preregistration with Ruby's existing standard YAML library and
  kept the repository dependency set unchanged.
- Required the affected audits to restart from protected `origin/main` and the
  exact owner prompt/preregistration. Discarded the stale-tree purge/manifest
  concerns and the one-row/quintile/no-Sharpe statistical recommendation.

Verification:

- The isolated worktree started clean at `6386c59`; the root checkout remained
  untouched.
- Protected-main baseline validation passed 3064 tests with two skips, and
  compileall passed.
- The corrected YAML parse and JSON inventory validation passed; the inventory
  contains exactly 14 unique trial IDs.
- Corrected capability evidence recognizes the implemented purged/bounded split
  and next-observed-close primitives while identifying the truly missing PIT
  dataset layer, campaign orchestration, decile/statistics, baselines, and
  evidence runner.
- Corrected statistical design uses monthly 21-row episodes, ten deciles,
  retained strategy metrics, exact random/bootstrap seeds, and a six-record
  moving-block bootstrap.

Prevention:

- For a dirty or stale root checkout, explicitly anchor every read-only audit
  to `origin/main` or the isolated worktree.
- Use the exact owner artifact path when a sub-audit depends on a supplied
  protocol.
- Use the repository virtual-environment interpreter in linked worktrees.
- Prefer an already available standard-library YAML parser for this
  documentation-only artifact; do not add PyYAML solely for validation.
- Treat truncated output and nonterminal test output as unknown, never as
  evidence.

## 2026-07-29 - R1I Linked-Worktree Branch And Interpreter Recovery

Original failures and consequences:

- The first R1I branch rename could not update linked-worktree Git logs under
  the main repository's `.git/worktrees` metadata. It left the original branch
  name intact.
- A bare `python` digest-check command failed because this shell has no
  `python` executable on `PATH`. It made no repository change.
- The first hidden-Unicode scan inspected whole modified files and therefore
  flagged two pre-existing `é` negative-test literals as if they were new R1I
  additions. It made no repository change.
- The first exact 18-file `git add` could not create the linked-worktree
  `index.lock` under the main repository's Git metadata. It staged no file.
- The first post-creation `gh pr view 176` query requested broad nested PR
  metadata in one response. Its tool output exceeded the available context and
  was truncated, so the partial response was not accepted as evidence of PR
  identity, scope, head, or check state.
- The first split-query retry assembled `gh` argument arrays into unquoted
  shell strings. Spaces and jq punctuation were reinterpreted by the shell;
  three read-only metadata queries failed before reaching GitHub. The separately
  quoted CI query succeeded, but its result applied to the superseded head.
- After rebasing, three focused-test invocations used a nested execution path
  with an effective roughly 30-second lifetime. Each was terminated before its
  terminal pytest summary (at 87%, 87%, and 96% respectively), so none was
  accepted as validation evidence.

Correction:

- Retried only the exact linked-worktree branch rename with permission to
  update Git metadata; it succeeded as `codex/ledger-attempt-start-schema`.
- Re-ran the digest check with the existing project interpreter at
  `<home>/Documents/Codex/projects/equity-factor-research/.venv/bin/python`.
- Re-scoped the Unicode/control scan to added lines relative to `HEAD`, while
  scanning every line of new files.
- Retried only the exact 18-file stage with permission to update the linked
  index.
- Replaced the broad PR query with separate bounded metadata, file-scope,
  commit, and check-state queries.
- Re-issued each bounded query with explicit shell quoting instead of joining
  argument arrays.
- Re-ran the same focused suite in a reusable direct execution session and
  polled it to a terminal exit.

Verification:

- At the time of the failed local commands, the isolated worktree remained
  based on exact protected merge `b42b911`; no protected history or GitHub
  state was changed by either failure. It was later rebased normally onto
  protected `26bc9a8` after an independent README-only mainline change.
- Initial R1I-focused validation passed 225 tests.
- The corrected scan covered all 18 changed/new files and found zero new
  non-ASCII, bidi, zero-width, non-breaking-space, or control characters.
- The exact retry staged only the intended R1I files; no unrelated path was
  added.
- No PR conclusion or external mutation was based on the truncated GitHub
  response.
- No PR conclusion was based on the failed split queries or the superseded-head
  CI result.
- The terminal direct-session retry passed all 2229 focused tests; no partial
  pytest output was reported as a pass.
- No failed command installed a dependency, accessed private data, or changed
  a persistent environment.

Prevention:

- Use the exact project interpreter for repository checks in this shell.
- Distinguish pre-existing negative Unicode fixtures from newly added bytes by
  comparing added lines to the exact base.
- Expect linked-worktree branch operations to require narrowly scoped Git
  metadata permission.
- Keep post-creation GitHub verification split into bounded queries and treat
  truncated output as unknown state.
- Preserve each jq program as one quoted command argument; do not reconstruct
  shell commands by joining unescaped argument arrays.
- Use a reusable direct execution session for validation expected to exceed
  30 seconds, and require the terminal exit code and pytest summary.

## 2026-07-29 - R1H Bounded-Output And Interpreter Recovery

Original failures and consequences:

- A broad R1G registry-schema inspection expanded the 4096-value finite-count
  enum and exceeded the bounded tool output. No R1H design decision relied on
  the truncated output.
- A combined roadmap/log orientation read exceeded the bounded output. The
  partial result was not treated as complete evidence.
- A bare `python` orientation command failed because this shell has no
  `python` executable on `PATH`; it made no repository change.
- The first R1H digest probe omitted `PYTHONPATH=src` and failed with
  `ModuleNotFoundError: ledger`; it did not write the registry or sidecar.
- The `apply_patch` response for the R1H handoff next-stage update was
  truncated, so the tool response alone could not prove whether the patch had
  landed.
- The first final branch rename could not update linked-worktree Git logs
  under the main repository's `.git/worktrees` metadata. It left the original
  branch name intact.
- The first exact 19-file `git add` could not create the linked-worktree
  `index.lock` under the same Git metadata directory. No file was partially
  staged by that failed attempt.
- The first combined focused gate passed 2002 tests and found one
  documentation-structure assertion that expected a noncontiguous paraphrase
  of the `ATTEMPT_STARTED` boundary rather than the contract's exact wording.

Correction:

- Replaced broad reads with exact `rg`, bounded `sed`, and targeted JSON-path
  inspection.
- Used the existing project interpreter with `env PYTHONPATH=src`.
- Repeated the digest probe with the exact import path; it produced the
  intended canonical registry digest and sidecar.
- Re-read only the exact handoff `Next Safe Stage` range and confirmed the
  R1H text had landed exactly once before continuing.
- Retried only the exact linked-worktree branch rename with permission to
  update Git metadata; it succeeded as
  `codex/ledger-attempt-allocation-schema`.
- Retried only the exact 19-file stage with permission to update the linked
  index; it succeeded without adding unrelated files.
- Aligned the structure oracle to the contract's exact contiguous
  `ATTEMPT_STARTED` pre-execution-boundary wording without weakening the
  requirement that the event remain incomplete.

Verification:

- The isolated worktree remains based on exact protected merge `520ed65`; no
  protected history, unrelated branch, or GitHub state was changed by the
  failed reads or commands.
- Registry `0.8.0` validates under unchanged schema-language `0.2.0`, supports
  ten events, and leaves 27 events incomplete.
- Its canonical registry digest is
  `3c71399f9ee8de51b6bd401dc409865c672d12a97cc00057c6de26445c0c538f`.
- Initial R1H-focused validation passed 341 tests.
- After the exact documentation-oracle correction, final focused validation
  passed 2003 tests and the full suite passed 2838 tests with the two expected
  platform-conditional skips.
- No failed command installed a dependency, accessed private data, or changed
  a persistent environment.

Prevention:

- Avoid broad serialization of finite enumerations; inspect only required
  paths and counts.
- Use the exact project interpreter and `PYTHONPATH=src` for repository
  modules.
- Treat every truncated tool response as unknown state until the exact target
  is re-read.

## 2026-07-29 - R1G Linked-Worktree Metadata And Bounded-Output Recovery

Original failures and consequences:

- The first branch rename could not update linked-worktree Git metadata under
  the main repository's `.git/worktrees` directory because the sandbox only
  permitted content writes. The branch remained unchanged by that failed
  attempt.
- A broad controller/roadmap orientation read exceeded the available response
  context and was truncated. No design decision relied on the partial output.
- The `apply_patch` response for the new engineering-log entry was truncated,
  so the tool response alone could not prove whether the entry had landed.
- The first repo-map/focused-test command used bare `python`, which was not on
  this shell's path. Its exact retry used the existing project environment.
- The first focused-test retry named the historical R0 test file as
  `tests/test_ledger_schema_registry_r0.py`; the actual retained file is
  `tests/test_ledger_schema_registry.py`, so no tests ran in that retry.
- The first focused registry run passed 871 tests and found one expected stale
  compatibility assertion: the older R1 test still rejected newly published
  release `0.7.0`.
- The first package conformance statistics probe requested a nonexistent
  `supported_event_types` summary key after byte parity had already passed.
  The actual supported schema collection is `event_schemas`.

Correction:

- Retried only the exact branch rename with permission to update linked
  worktree metadata; it succeeded as
  `codex/ledger-campaign-inventory-seal-schema`.
- Repeated the orientation with narrow, targeted reads from the canonical
  controller, roadmap, handoff, and registry sources.
- Inspected the top of `docs/engineering_log.md`, confirmed that the R1G entry
  had landed exactly once, and did not reapply it.
- Reused the existing project interpreter, corrected the exact retained test
  filename, and reran the intended focused gate.
- Advanced the compatibility test to accept explicit published `0.7.0` while
  retaining fail-closed rejection of unknown future release `0.8.0`.
- Repeated the source/sdist/wheel conformance probe using
  `event_schemas`; all three carriers then reported the same digest,
  nine supported schemas, 28 incomplete events, and identical outcomes.

Verification:

- The isolated R1G worktree remained based on exact protected merge
  `d9ac67e`, and no protected history or unrelated branch was changed.
- The R1G registry validates as release `0.7.0` under unchanged schema-language
  `0.2.0`, supports nine events, and leaves 28 events incomplete.
- The generated R1G canonical registry digest is
  `1d85424d1ee60dcc9523a52c56b22080b47aebb4275551a7ea9ee38e8e28d710`.
- Final focused validation passed 1661 tests; the full suite passed 2496 tests
  with the two expected platform-conditional skips.
- No failed command installed a dependency, changed GitHub state, accessed
  private data, or altered protected history.

Prevention:

- Use narrowly scoped permission escalation only for linked-worktree Git
  metadata changes.
- Cap orientation reads, and treat truncated tool output as unknown state until
  the exact target is re-read.
- Keep compatibility tests explicit about the newest published release and one
  unknown future release.

## 2026-07-29 - R1D Handoff Patch Output Was Truncated

Original failure and consequence:

- A large `apply_patch` result for the R1D handoff exceeded the available tool
  response context and was truncated. The partial response could not establish
  whether the intended authority section had landed.

Correction:

- No success was inferred from the truncated result.
- Re-read only the targeted handoff ranges with bounded `sed`, confirmed that
  the R1D authority section had landed exactly once, and used small
  context-specific patches for the remaining stale PR-interaction and
  next-stage text.

Verification:

- The handoff now identifies accepted R1C, active R1D-A, registry `0.4.0`,
  exactly five supported and 32 incomplete events, and R1E as the later
  binding-event gate.
- The first combined focused gate correctly found two stale milestone
  assertions: an R1 test still treated now-published `0.4.0` as unknown, and a
  structure test still called R1C active. They were advanced without weakening
  the R0-default or unknown-future-release checks. A first corrective patch
  also introduced visible over-indentation; collection failed immediately, the
  exact lines were inspected, and the indentation was corrected.
- The first `git add` could not create the linked-worktree `index.lock` because
  the sandbox permits repository content writes but not writes under the main
  repository's `.git/worktrees` metadata. The exact same bounded 17-file stage
  was retried with the required Git metadata permission; no broader path or
  destructive Git operation was used.
- The rerun passed 569 focused registry/structure tests, Ruff, and compilation.
- The bounded follow-up reads and patches produced non-truncated terminal
  status.
- No dependency, GitHub state, private data, or protected history was changed
  by the failed-to-observe response.

Prevention:

- Keep documentation patches and verification reads narrowly targeted.
- Treat a truncated patch response as unknown state and inspect the exact
  target before retrying.

## 2026-07-28 - R1C Orientation And Documentation Commands Needed Narrow Retries

Original failures and consequences:

- The first R1C worktree creation attempt could not resolve merge
  `a6f7d43` because that protected merge object was not yet present locally.
  No worktree or branch was created by the failed attempt.
- One combined read-only orientation command exceeded the available response
  context and was truncated. No conclusion relied on the partial output.
- The first draft-registry validation used the shared project virtual
  environment without exposing this isolated worktree's `src` tree and failed
  with `ModuleNotFoundError: No module named 'ledger'`.
- An `apply_patch` result was itself truncated, leaving its success status
  uncertain. A later large handoff patch also failed atomically because one
  context paragraph did not match. Treating either as successful without
  checking could have duplicated or partially omitted authority text.
- While the first R1C pull request was being created, independent PR #168
  advanced `main` from `a6f7d43` to `4ac5adb`. The new PR snapshot therefore
  reported `mergeable=false` against a newer base even though the R1C commit
  itself had passed local gates.
- The first same-repository PR-body update passed
  `maintainer_can_modify=true`. GitHub rejected it with HTTP 422 because that
  option applies only to cross-repository fork collaboration. The R1C branch,
  PR head, title, and existing body were unchanged by the failed request.

Correction:

- Fetched `origin/main`, then created the R1C worktree from the same exact merge
  SHA and reran the clean startup baseline.
- Repeated orientation with bounded, targeted `sed` and `rg` reads.
- Repeated registry validation and every worktree-focused Python test with
  `PYTHONPATH=src`; the draft registry validated and produced canonical digest
  `d0e3c08ed5699c8fd6078afb6d7c0a513bbc20b306bad630b175abd09e695f85`.
- Inspected the exact target after the truncated patch result, confirmed the
  successor note had landed once, and split the stale handoff update into
  small context-specific patches after the large patch failed atomically.
- Fetched the new protected main, confirmed PR #168's six-file scope and the
  exact three-file R1C overlap, rebased R1C normally without conflict,
  regenerated the repo map, and reran focused/full/lint/compile/Skill/package
  gates before replacing only the R1C remote branch head.
- Repeated the PR metadata update without `maintainer_can_modify`; the body
  update then succeeded against the unchanged exact R1C head.

Verification:

- The worktree remained on exact base `a6f7d43` until intentional R1C edits.
- The first combined focused R0/R1/R1C/structure run reported 331 passing
  tests and one new structure-oracle failure. The oracle had encoded the array
  keyword from memory as `sorted_unique: true`; the frozen DSL actually uses
  `collection_semantics: "sorted_unique"`. The implementation and existing
  behavior tests were correct. The literal structure oracle was corrected to
  the exact published DSL node before rerunning the same focused gate.
- Self-adversarial review found that the first R1C contract draft had
  accidentally changed the selected currentness policy in two directions:
  `strictly monotonic` became mandatory `+1`, while `exactly one current
  accepted generation` became `at most one`. The draft had not been committed
  or published. The contract and every canonical reference/oracle were restored
  to the exact owner-selected policy before final validation.
- The same review found that the draft had copied the selected 32-campaign
  direct-scope maximum onto the separate `depends_on` graph and mentioned an
  unselected revocation mechanism. Both extrapolations were removed: the
  dependency cardinality belongs to the digest-pinned external authority
  schema, and R1C currentness uses explicit supersession only.
- The earlier focused R0/R1/R1C registry and structure run passed 302 tests.
- On the rebased PR #168 base, the final focused gate passed 336 tests and the
  full suite passed 1171 tests with two platform-conditional skips.
- No failed command installed a dependency, changed GitHub state, accessed
  private data, or altered protected history.

Prevention:

- Fetch the exact protected merge object before creating a new isolated stage
  worktree.
- Keep orientation output bounded and never use truncated output as complete
  review evidence.
- In linked worktrees that share an editable project environment, set
  `PYTHONPATH=src` so imports resolve to the active worktree.
- When tool output obscures patch status or a large patch misses context,
  inspect the exact target and retry with small, idempotent hunks.
- Copy exact schema-language nodes from the immutable artifact into literal
  structure oracles rather than reconstructing their key names from memory.
- Do not send `maintainer_can_modify` when updating metadata on a same-repo PR;
  reserve it for a cross-repository fork PR.

## 2026-07-29 - Final R1B Review Found Nullable Named-Type Cycle Recursion

Original failure and consequence:

- The final exact-head Codex review on PR #167 identified one actionable P2:
  constraint-path meta-validation reset its visited named-type state when it
  traversed `nullable` or another recursive schema branch.
- A targeted malformed-registry test reproduced the issue. A named type cycling
  through `nullable` with path components remaining raised Python
  `RecursionError` rather than the required fail-closed
  `LedgerSchemaError("INVALID_REGISTRY", ...)`.
- No accepted registry artifact contains such a cycle, so the defect did not
  change R0 or R1 event acceptance. It did violate the validator's fail-closed
  behavior for malformed caller input.

Correction:

- Threaded an immutable visited-name set through nullable, tagged-union, and
  closed-object path recursion in `_schemas_at_path`.
- Added an exact regression test that constructs the malformed nullable cycle
  through `validate_registry()` and requires `INVALID_REGISTRY`.

Verification:

- The regression failed before the fix with `RecursionError` and passed after
  the fix.
- Focused and full repository tests, Ruff, compilation, deterministic repo-map,
  Skill, package-parity, privacy/Unicode, cleanup, and diff gates passed again
  before the review-fix commit was pushed.
- No dependency was installed and no R0/R1 artifact, private data, research
  result, append/storage runtime, brokerage, order, paper, or live behavior
  changed.

Prevention:

- Recursive schema walkers must propagate cycle state through every schema
  wrapper and branch; later whole-registry cycle checks are not a substitute
  for safe earlier meta-validation.

## 2026-07-28 - R1B Full Gate Caught A Stale Contract-Phrase Oracle

Original failure and consequence:

- After the contract was reconciled from future tense to the active R1B
  release, the full suite had one failure because a structure test still
  searched for the former phrase `will add`. The run otherwise reported 1000
  passing tests and two platform-conditional skips.

Correction and verification:

- Updated the literal structure oracle to the current phrase `adds` without
  weakening its exact three-capability assertion.
- The first rerun exposed that the literal phrase was still split by a Markdown
  line break. It again failed only that structure assertion, with 165 focused
  tests or 1000 full-suite tests passing and the same two platform skips.
- Reflowed the semantically unchanged contract sentence so the exact pinned
  phrase is contiguous.
- Reran the focused structure/registry tests and the full repository suite;
  both passed. No source behavior, registry artifact, dependency, environment,
  Git, or GitHub state changed because of the failed run.

Prevention:

- When changing a canonical contract phrase that is deliberately pinned by a
  structure test, update the literal oracle in the same reviewable edit.

## 2026-07-28 - Two Read-Only Orientation Commands Used Unsafe Assumptions

Original failures and consequences:

- A double-quoted `rg` pattern contained Markdown backticks. The shell treated
  the enclosed `0.1.0` text as command substitution and printed
  `command not found`. The remaining read-only search still ran, but its output
  was not used as complete evidence.
- A one-off existing-venv Python command imported `ledger` without adding the
  source tree to its module path. It failed with
  `ModuleNotFoundError: No module named 'ledger'` before reading or changing
  registry state.
- A three-range aggregate `git diff` inspection exceeded the available model
  context and was truncated. The command was read-only and made no repository
  or environment change; no review conclusion relied on its partial output.

Investigation and correction:

- Confirmed all three commands were read-only and that none changed repository,
  environment, dependency, Git, or GitHub state.
- Repeated the documentation inspection with literal-safe targeted `sed`/`rg`
  commands.
- Repeated the registry validation with the existing project Python and an
  explicit in-process `sys.path.insert(0, "src")`. The R1 registry validated
  and produced its deterministic canonical digest.
- Resumed the independent review from `docs/current_handoff.md` and
  `docs/repo_map.md`, then inspected one bounded file range per command.

Verification:

- The focused R0/R1 registry suite passed 133 tests; Ruff and compilation
  passed.
- No dependency was installed and the worktree contained only intended R1B
  edits.

Prevention:

- Do not place Markdown backticks inside a double-quoted shell argument; use a
  literal-safe pattern or a targeted line range.
- For one-off source-tree imports, use the test runner's configured path or an
  explicit in-process source path rather than assuming the package is
  installed in the selected environment.
- Keep each independent diff-review read to one bounded file range so a
  truncated aggregate cannot hide relevant evidence.

## 2026-07-26 - Isolated Package Build Initially Lacked Network Access

Original failure and consequence:

- The default system Python did not contain the repository development tools,
  so validation reused the existing project test environment, existing Ruff
  command, and cached `build` frontend.
- The first package-build attempt ran inside the filesystem/network sandbox.
  PEP 517 correctly created a temporary isolated environment, but pip could not
  resolve the declared `setuptools>=77` and `wheel` build requirements because
  DNS/network access was unavailable.

Correction:

- Did not modify `pyproject.toml`, install a new production dependency, or
  create a persistent project environment.
- Reran the same cached `build 1.5.0` frontend with network permission. Its
  temporary isolated environment installed the already-declared
  `setuptools>=77` and `wheel` requirements and was removed after the build.
- The frontend reported the requirement names but not their resolved versions;
  because the environment was ephemeral, no persistent package state remains
  to inspect or reuse.

Verification:

- The source distribution and wheel both built successfully.
- Tests, Ruff, and compilation also passed, and `git status --porcelain`
  remained empty.

Prevention:

- Distinguish a sandbox network failure during isolated build bootstrapping
  from a package or source defect.
- Reuse declared environments when sufficient. If a future stage requires a
  persistent missing dependency, install only the minimal declared scope and
  report its package, resolved version, location, purpose, and repository-file
  impact.

## 2026-07-26 - Auto-Merge Eligibility Preceded Required Codex Review

Original policy defect and consequence:

- The controller required nontrivial PRs to request `@codex review` only after
  CI stabilized, but separately allowed auto-merge while required checks were
  still pending.
- A review-required PR could therefore merge immediately when CI passed,
  before the final-head Codex review was requested or completed.

Evidence and investigation:

- Codex review of PR #158 raised this as a P1 on
  `docs/codex_long_running_controller.md`.
- Thread-aware review inspection confirmed one unresolved, current inline
  thread and no conflicting or duplicate findings.
- The same permissive check language existed in the staged workflow Skill,
  while the roadmap stated the review timing but not its merge prerequisite.

Final fix:

- Prohibited enabling auto-merge or attempting either merge path while required
  checks or an applicable current-head Codex review is pending.
- Required the applicable review to complete with no unresolved actionable
  findings. Any actionable fix now requires stable CI and re-review on the new
  head.
- Added a cross-document contract test and aligned the roadmap, Skill, durable
  decision, engineering record, and changelog.

Verification and remaining gate:

- Focused and baseline validation, Skill audit, regenerated repo map, final CI,
  and Codex re-review are required on the changed head before merge.
- The review thread must not be resolved or replied to until the fix is pushed
  and verified; those external writes require explicit scope.

Prevention:

- Treat review ordering as a merge precondition, not merely a request-timing
  convention. Auto-merge convenience cannot bypass a current-head review gate.

## 2026-07-26 - Unbounded Ruff Upgrade Expanded The CI Lint Baseline

Original assumption and consequence:

- Local validation used Ruff 0.15.18 and passed, while the development
  requirement allowed any `ruff>=0.9` release and the repository declared no
  explicit lint rule selection.
- PR #158 installed Ruff 0.16.0. Its expanded default rules produced 95
  repository-wide findings, mostly in files untouched by the charter stage, so
  the GitHub Actions `Python validation` job failed before compilation/build.

Evidence and investigation:

- The failed run recorded Ruff 0.16.0 in the dependency-install log and
  `Found 95 errors` in the lint step.
- The charter PR changed only one Python test file; reported findings also
  covered numerous unchanged source, research, and test files.
- Ruff 0.16.0 passed the complete repository when invoked with the prior
  default baseline explicitly as `E4`, `E7`, `E9`, and `F`.

Final fix:

- Added `[tool.ruff.lint]` with an explicit `select` list for those four rule
  families.
- Added a documentation/configuration contract assertion so future edits
  cannot silently remove or broaden the baseline.
- Deferred adoption of additional Ruff rules to a separately scoped lint
  migration rather than auto-fixing unrelated files in the charter PR.

Verification:

- Ruff 0.15.18 and Ruff 0.16.0 pass the repository under the explicit baseline.
- Final pytest, compilation, build, diff, and GitHub Actions results are
  reported with PR #158.

Prevention:

- Configure intended lint semantics explicitly when development tools can
  upgrade independently. Treat adoption of new rule families as a reviewed
  migration, not an incidental dependency-resolution side effect.

## 2026-07-26 - Broad Readiness-Policy Read Exceeded The Output Cap

Original mistake and consequence:

- Requested the full active readiness Skill in one broad command after the
  independent charter review.
- The command output exceeded the context limit and was truncated, so none of
  that output was used as evidence for an edit.

Correction and final fix:

- Measured the flagged files first, then read the 234-line Skill, 211-line
  readiness audit, 151-line experiment log, and targeted controller/test
  sections in bounded ranges.
- Limited the remediation to the reviewer-identified active policy contracts
  and their cross-document tests.

Verification:

- The replacement reads reached every line of each active readiness source.
- Final focused, baseline, Skill, and documentation checks are recorded with
  this charter stage after the remediation is complete.

Prevention:

- Measure unfamiliar policy files before reading them and paginate long inputs
  with bounded output. Treat any truncated command as failed evidence and rerun
  only targeted ranges.

## 2026-07-26 - Initial Reads Used A Stale Dirty Local Main

Original mistake:

- Read the required handoff and roadmap paths before comparing the local branch
  with freshly fetched `origin/main`.

Consequence and evidence:

- Local `main` was 47 commits behind and had many unrelated modified/untracked
  files. Its handoff was stale and `docs/current_roadmap.md` appeared missing,
  although the file exists on current `origin/main`.
- Editing that checkout could have mixed the charter with user work or relied
  on obsolete governance.

Investigation:

- Fetched `origin`, compared `HEAD...origin/main`, inspected current PRs, and
  verified remote `main` at `a1486ea`.
- Confirmed the local branch was one commit ahead and 47 commits behind, with
  source, test, docs, Skill, and untracked changes outside this stage.

Correction and final fix:

- Created `codex/research-program-charter-reset` in an isolated worktree from
  exact `origin/main`.
- Re-read the complete startup control set in the new worktree before
  auditing or editing.
- Used the existing repo virtual environment for pytest/compilation and the
  available Ruff executable because the shell's missing `python` alias is
  already documented below.

Verification:

- Isolated `HEAD` matched `origin/main`; its tracked worktree was clean before
  the stage.
- The current roadmap was present, 591 tests passed, Ruff and compilation
  passed, package build passed, and the exact-head GitHub CI run was successful.

Remaining caveat:

- The original checkout remains intentionally dirty and behind; none of its
  unrelated changes were staged, rewritten, or removed.

Prevention:

- After the mandatory first handoff read, fetch and compare refs immediately.
  If the local branch diverges, create a clean worktree and reread all canonical
  control files from the verified remote baseline before drawing conclusions.

## 2026-07-26 - Charter Contract Assertions Depended On Markdown Wrapping

Original mistake and consequence:

- The first documentation-contract update asserted two multi-word phrases as
  literal single-line substrings and expected a stage label not present in the
  roadmap table.
- The focused suite failed with two assertions, then one remaining handoff
  wording assertion after the first correction.

Investigation and correction:

- Located the exact wrapped Markdown text with targeted `rg`.
- Changed the specification assertion to normalize whitespace, asserted stable
  semantic fragments for the roadmap, and retained the established
  `Active roadmap:` handoff marker.

Verification:

- `tests/test_project_structure.py` passed all 10 focused tests.

Prevention:

- Documentation contracts should enforce durable headings, policy terms, and
  links without depending on prose line wrapping or incidental table prefixes.

## 2026-07-26 - PowerShell Skill Audit Runtime Was Unavailable

Original mistake and evidence:

- Invoked `pwsh -NoProfile -File scripts/audit-skills.ps1` without first
  checking whether PowerShell was installed.
- The command failed with `zsh: command not found: pwsh`; neither `pwsh` nor
  `powershell` is available.

Correction attempts:

- An initial inline Python equivalent failed at shell parsing with
  `unmatched "` because the multi-line `-c` string was over-quoted.
- Replaced the fragile inline command with an ephemeral temporary Python script
  that implements the same frontmatter, non-empty name and description,
  top-level heading, and balanced-fence checks as the 73-line PowerShell
  script.

Final fix and verification:

- The equivalent audit passed for both repository Skill files.
- The temporary script was deleted and no dependency or runtime was added.

Remaining caveat:

- The official PowerShell entrypoint was not executable in this environment;
  CI or a PowerShell-equipped reviewer should run it if exact shell parity is
  required.

Prevention:

- Check the declared script runtime before invoking workflow audits. When a
  non-project runtime is absent, do not install it implicitly; run a documented
  read-only equivalent and report the limitation.

## 2026-07-26 - Transient Build Extra Was Not Installed In The Project Venv

Original mistake and evidence:

- Assumed the worktree `.venv` retained the `build` package after an earlier
  `uv run --with build` command.
- The final build gate failed with `No module named build`; the extra had been
  supplied only to the transient uv invocation.

Final fix and verification:

- Reran the gate with
  `uv run --no-project --with build python -m build`, avoiding a project lock
  mutation while providing the build frontend.
- The source distribution and wheel built successfully.

Prevention:

- Treat `uv --with` packages as command-scoped unless explicitly installed.
  Use `--no-project` for an ephemeral build tool when the repository does not
  track a uv lock.

## 2026-07-11 - Experiment Registry Has No Standalone Research Module

Failure:

- The position-cap generated-output stability check attempted
  `python -m research.build_experiment_registry`, but that module does not
  exist.

Recovery:

- Confirmed with `rg` that `research.synthetic_multifactor_parameter_sweep`
  already calls `write_experiment_registry_report()` and reran the existing
  generator path instead.

Prevention:

- Use the generator entrypoints named in source and tests rather than assuming
  every report helper has a same-named research module.

This log records failures, missing prerequisites, confusing environment
behavior, incorrect assumptions, failed checks, and recovery steps.

It is not an experiment log and must not be used to claim profitability or
investment performance.

## How To Update This Log

For technical, methodological, environment, testing, workflow, or reasoning
problems, include:

- original mistake or incorrect assumption.
- consequence.
- exact error or evidence.
- investigation steps.
- correction attempts.
- final fix.
- verification results.
- remaining caveats.
- prevention measures.

---

## 2026-07-11 - Generated Output Used A Stale Editable Install

Original mistake:

- Reused a shared temporary virtual environment whose editable package pointed
  at the prior worktree, then ran the tracking-error report generators without
  setting the current worktree's `src` path.

Consequence and evidence:

- The current research module imported the older `backtest` package and failed
  while rendering the new metric with `KeyError: 'tracking_error'`.

Investigation and final fix:

- Confirmed focused pytest passed because pytest adds the current repository's
  `src` directory, while direct module execution used the stale editable link.
- Reran all affected generators with `PYTHONPATH=src` so imports resolved from
  the active implementation worktree.

Verification and prevention:

- Momentum, combined-score, and parameter-sweep generators completed and
  refreshed only their expected committed synthetic reports, JSON logs, and
  registry.
- Future cross-worktree generation commands must set `PYTHONPATH=src` or install
  the active worktree before producing evidence.

---

## 2026-06-23 - Continuation Command Output And Python Path Guardrails

Original mistake:

- Reused the objective's `python -m pytest` and `python -m compileall`
  commands even though the migrated Mac shell does not provide `python`.
- Also ran one broad `rg` search across code and long docs for local-fixture
  terms.

Consequence:

- The first baseline validation attempt failed before running tests.
- The broad search output was truncated and could not be used as evidence.

Evidence:

```text
zsh:1: command not found: python
Warning: truncated output
```

Investigation:

- Verified the repo-local `.venv/bin/python` can run the same pytest and
  compileall checks.
- Switched from broad search output to targeted file ranges in the local
  fixture workflow, tests, and refresh plan.

Final fix:

- Use `.venv/bin/python` for validation on this Mac until a deliberate project
  environment adds a `python` shim.
- Cap or narrow local-fixture searches before reading long logs or docs.

Verification:

- `.venv/bin/python -m pytest -q` passed before starting the stage.
- `.venv/bin/python -m compileall src tests research` passed before starting
  the stage.
- Focused local fixture workflow tests passed after the code change.

Remaining caveats:

- The shell still has no `python` command on `PATH`; future prompts that
  specify `python ...` need the repo venv equivalent.

Prevention:

- Prefer the repo venv command in this migrated Mac workspace and keep search
  output scoped to the active files.

---

## 2026-06-22 - New Mac Python Validation Environment Missing Pytest/Pandas

Original mistake:

- Assumed the migrated Mac environment had a `python` command with the project
  test dependencies available.

Consequence:

- The focused pytest validation for `tests/test_local_csv_fixture_workflow_demo.py`
  could not run through the normal project command.

Evidence:

```text
zsh:1: command not found: python
/usr/bin/python3: No module named pytest
ModuleNotFoundError: No module named 'pandas'
ModuleNotFoundError: No module named 'scipy'
```

Investigation:

- Checked for a repo-local virtual environment; none was present.
- Checked Codex bundled Python; it has `pandas` but not `pytest`.
- Checked `<home>/.local/bin/pytest`; it runs under Python 3.9 without
  `pandas`.
- Created an ignored `.venv` from the Codex bundled Python so the environment
  could reuse bundled `pandas` and `numpy`.

Correction attempts:

- Ran a direct assertion check for the new helper with the Codex bundled Python.
- Ran compile checks with the same bundled Python.
- Installed `pytest` into the ignored `.venv`; focused pytest then reached the
  local fixture workflow tests but failed because `scipy` was missing for
  pandas Spearman correlation.
- Installed the project-declared `scipy` dependency into the ignored `.venv`.

Final fix:

- Use `.venv/bin/python -m pytest ...` for focused validation on this migrated
  Mac until a project environment is created deliberately.

Verification:

- `.venv/bin/python -m pytest tests/test_local_csv_fixture_workflow_demo.py -q`
  passed with 15 tests.

Remaining caveats:

- Full pytest has not been run in this migrated Mac environment.

Prevention:

- On this Mac, create or activate a project virtual environment before relying
  on `python -m pytest`.

---

## 2026-06-11 - PowerShell PR Body Quoting Failure

Original mistake:

- The first `gh pr create` attempt passed a multi-line Markdown PR body
  directly through a PowerShell double-quoted command string.
- The body included Markdown backticks and line breaks, which made the shell
  parse the command before `gh` received the intended text.

Consequence:

- PR creation failed after the branch had already been pushed.
- No repository files, source code, tests, reports, data, credentials, or
  remote PRs were changed by the failed command.

Evidence:

```text
The string is missing the terminator: ".
CategoryInfo          : ParserError
FullyQualifiedErrorId : TerminatorExpectedAtEndOfString
```

Investigation:

- Confirmed the failure was a PowerShell parser error, not a GitHub, network,
  permission, branch, validation, or repository-content failure.
- Identified the shell quoting shape as the only failed component.

Correction attempts:

- Stopped using the failed double-quoted multi-line command form.
- Switched to a PowerShell single-quoted here-string for the PR body so
  Markdown backticks and line breaks are passed literally to `gh`.

Final fix:

- Use a local `$body = @' ... '@` here-string and pass it to
  `gh pr create --body $body` for multi-line PR descriptions in PowerShell.

Verification:

- The corrected PR creation command is rerun after this log entry is amended
  into the workflow-control commit.

Remaining caveats:

- Shell quoting remains environment-specific. Commands that work in Bash may
  fail in PowerShell when Markdown backticks are embedded in double-quoted
  strings.

Prevention:

- Use single-quoted PowerShell strings or here-strings for Markdown containing
  backticks.
- Treat PR body quoting failures as workflow issues and log them before
  publishing the corrected PR.

---

## 2026-06-11 - Continuation Context Read Output Truncation

Original mistakes:

- During a staged workflow continuation, the first context-gathering attempt
  requested several workflow documents and memory/search output in one broad
  parallel batch.
- The read assumed that several individually capped outputs would still fit
  safely when returned together.

Consequences:

- The combined tool output exceeded the available context and was truncated.
- The continuation could not safely rely on that truncated output for stage
  selection or scope review.

Evidence:

```text
Output exceeded the available model context and was truncated
```

Investigation:

- Confirmed the truncation occurred during context gathering before the
  workflow-control policy update.
- Confirmed the issue was caused by output volume, not by project tests,
  repository data, or source-code behavior.
- Re-read current workflow state using narrower, targeted files and snippets.

Correction attempts:

- Stopped relying on the truncated output.
- Switched to targeted reads for `docs/current_handoff.md`,
  `docs/repo_map.md`, the controller, and the staged workflow Skill.
- Avoided printing full generated reports or long logs.

Final fix:

- Added a reusable "Context Budget And Retrieval Policy" to the long-running
  controller and staged workflow Skill.
- The policy limits first-pass context, defines a retrieval ladder, prohibits
  parallel broad reads of long logs/reports, and defines recovery steps when
  truncation occurs.

Verification:

- The policy update is validated in the PR checks for this workflow-control
  stage.
- No source code, tests, research scripts, generated reports, data loaders,
  backtester, metrics, alpha files, normalization, combination, diagnostics,
  real-data access, vendor API, credential, trading, order-execution, or
  profitability behavior is changed by this fix.

Remaining caveats:

- New sessions can still exceed context if they ignore the policy or read many
  long files at once.
- Full-file reads remain allowed only when absolutely required and explained.

Prevention:

- Start from `docs/current_handoff.md` and `docs/repo_map.md`.
- Use keyword search, tails, stats, and small snippets for long files.
- If truncation occurs, stop broad reading and reread only the targeted
  sections needed for the active stage.

---

## 2026-06-09 - Slippage Smoke Stage Output And Patch Recovery

Original mistakes:

- During the local fixture slippage smoke diagnostic stage, an early context
  read requested several full files and broad search output in parallel.
- The first implementation patch then attempted to edit many sections of
  `research/local_csv_fixture_workflow_demo.py` in one large patch with a
  context hunk that did not match the current file exactly.

Consequences:

- The broad read produced more output than the tool context could safely
  return, so the stage needed to recover with targeted, capped reads before
  implementation.
- The first large patch was rejected. No repository files were modified by
  that failed patch, but the implementation needed to be split into smaller
  verified patches.

Evidence:

```text
Output exceeded the available model context and was truncated
apply_patch verification failed: Failed to find expected lines in
research/local_csv_fixture_workflow_demo.py
```

Investigation:

- Confirmed the output issue was caused by the command shape rather than by a
  test, data, or repository failure.
- Re-read only the needed sections with PowerShell output caps and targeted
  `rg` patterns.
- Inspected the local fixture workflow around dataclasses, the run function,
  report/log writers, config validation, and the relevant tests before
  editing again.

Correction attempts:

- Replaced broad file reads with `Select-Object -First` / `Select-Object
  -Skip ... -First ...` and targeted `rg` commands.
- Replaced the large patch with smaller patches for imports, dataclass fields,
  run-function integration, summary helpers, report/log fields, config
  validation, and tests.

Final fix:

- The stage now uses the existing volume-aware slippage diagnostic helper from
  `src/backtest/slippage.py` in the committed synthetic local CSV fixture
  workflow, while reporting only participation and rejection/cap counts.
- The workflow does not apply candidate slippage fields to returns, does not
  run a backtest, and does not fetch or interpret real data.

Verification:

- `python -m pytest -q tests/test_local_csv_fixture_workflow_demo.py` passed
  with 14 tests.
- `python -m pytest -q tests/test_volume_aware_slippage.py` passed with 17
  tests before the full validation gate.

Remaining caveats:

- The smoke diagnostic is a wiring check on tiny committed synthetic fixtures
  only. It is not a capacity study, transaction-cost conclusion, real-market
  evidence, or profitability support.

Prevention:

- Keep unknown file reads capped by default, especially for long workflow
  scripts and tests.
- Prefer smaller patches when a file has several distant edit locations.
- Treat rejected patches and truncated command output as workflow issues that
  need a durable troubleshooting entry, even when no repository file was
  modified by the failed attempt.

---

## 2026-06-09 - PowerShell `rg` Glob Pattern Failed During Roadmap Search

Original mistake:

- During the synthetic backtest slippage report/log refresh stage, the roadmap
  search command used a Unix-style file glob directly in PowerShell:
  `rg -n -i "..." docs/*.md`.
- That form assumes shell glob expansion behavior that PowerShell did not
  provide to `rg` in this context.

Consequence:

- The first roadmap search failed before checking the documentation set.
- No repository files were modified by the failed command, but the stage
  selection evidence needed to be gathered again with a compatible command.

Evidence:

```text
rg: docs/*.md: IO error for operation on docs/*.md: The filename, directory
name, or volume label syntax is incorrect. (os error 123)
```

Investigation:

- Confirmed the failure came from the `docs/*.md` path expression rather than
  from repository content, tests, data access, or a missing documentation file.
- The earlier source-of-truth reads and baseline checks had already succeeded.

Correction attempts:

- Did not reuse the failing glob form.
- Reran the search against the `docs` directory path directly:
  `rg -n -i "recommended next|next safe|next stage|follow-up|future stage|remaining gap|slippage|cost" docs`.

Final fix:

- The corrected search completed and identified the current slippage/cost
  roadmap evidence, including the already-completed implementation stage and
  the follow-up need to refresh synthetic generated outputs.

Verification:

- The corrected search returned matches from `docs/simulated_slippage_cost_assumption_design.md`,
  `docs/post_local_csv_fixture_audit_rehearsal_checkpoint.md`,
  `docs/quantconnect_lean_plan.md`, and other roadmap/log files.
- The stage continued using the corrected search output and current repository
  state.

Remaining caveats:

- PowerShell glob behavior can differ from Unix shell behavior, especially
  when a command receives an unexpanded path pattern.

Prevention:

- Prefer directory arguments plus `rg`'s own recursive search on Windows, or
  use `rg --glob "*.md" ... docs` when a file pattern is needed.
- Treat search-command failures as failed evidence gathering and rerun them
  before selecting or committing a stage.

---

## 2026-06-08 - Local CSV Inventory Patch Context Mismatch

Original mistake:

- During the local CSV inventory dry-run validator stage, the first combined
  `apply_patch` attempted to add the new source file, tests, engineering-log
  entry, and changelog entry in one patch.
- The patch used a stale `CHANGELOG.md` context that expected
  `docs/user_provided_local_csv_research_plan.md` to be the first item under
  `### Added`.
- After PR #78 merged, `docs/local_csv_study_checklist.md` was the first item.

Consequence:

- `apply_patch` rejected the entire combined patch.
- No repository files were modified by that failed patch, but the stage needed
  to be reapplied in smaller chunks against the current main state.

Evidence:

```text
apply_patch verification failed: Failed to find expected lines in
D:\Users\MINQI\Documents\New project\CHANGELOG.md:
### Added

- Added `docs/user_provided_local_csv_research_plan.md` to define a
  documentation-only plan, scope template, validation gates, stop conditions,
  and future PR-sized stages before any user-provided local CSV result is
  interpreted.
```

Investigation:

- Checked `git status -sb --untracked-files=all` and confirmed the failed
  combined patch left no modified or untracked files.
- Read the top of `CHANGELOG.md` and confirmed PR #78 had inserted the local
  CSV study checklist entry above the user-provided local CSV research plan
  entry.
- Confirmed this was a patch-authoring/context issue only, not a source-code,
  data, CSV-loader, test, trading, credential, or profitability issue.

Correction attempts:

- Did not force the stale patch context.
- Reapplied the source module, tests, API export, engineering-log entry,
  changelog entry, and this troubleshooting note as smaller patches using the
  current file context.

Final fix:

- Added the local CSV inventory dry-run validator and focused tests in scoped
  patches.
- Updated the durable logs using the current post-PR #78 changelog and
  engineering-log context.

Verification:

- Focused and full validation are rerun before this stage is committed and
  opened as a PR.

Remaining caveats:

- This was local patch tooling friction only. It did not change project
  behavior until the corrected patches were applied.

Prevention:

- After syncing a newly merged PR, inspect the exact top-of-file changelog and
  log context before applying broad multi-file documentation patches.
- Prefer smaller patches when recent merged stages have touched the same
  durable logs.

---

## 2026-06-08 - PowerShell PR Body Quoting Error

Original mistake:

- During the local CSV fixture inventory dry-run rehearsal stage, the first
  `gh pr create` command passed a long Markdown PR body inside a PowerShell
  double-quoted argument.
- The body text contained Markdown backticks around file names and commands.
- In PowerShell, backticks are escape characters, so the shell parsed the
  command string before `gh` could receive the intended body.

Consequence:

- PR creation failed on the first attempt.
- No repository files, staged content, commits, branches, or remote PRs were
  modified by the failed command.
- The stage was not complete until the PR body was submitted with
  PowerShell-safe quoting and this recovery was logged.

Evidence:

```text
The string is missing the terminator: ".
CategoryInfo          : ParserError
FullyQualifiedErrorId : TerminatorExpectedAtEndOfString
```

Investigation:

- The failure was a shell parse error, not a GitHub, git, test, source-code,
  data, trading, credential, or profitability issue.
- The command used Markdown backticks inside a double-quoted PowerShell string.
- The repository remained clean after the existing commit, and the failed
  command did not open a PR.

Correction attempts:

- Did not retry the same double-quoted command.
- Recreated the PR body as a PowerShell single-quoted here-string assigned to
  a variable.
- Passed that variable to `gh pr create --body`, so Markdown backticks were
  treated as literal content rather than PowerShell escapes.

Final fix:

- Opened the ready-for-review PR with the here-string body command.
- The resulting PR is
  `https://github.com/minqiyang/ai-equity-factor-research/pull/80`.

Verification:

- `gh pr create` returned the PR #80 URL successfully.
- The failed command did not modify the working tree.
- This troubleshooting entry is added as a follow-up log-only update to the
  same PR branch.

Remaining caveats:

- This was command-line quoting friction only. It did not affect the local CSV
  fixture workflow implementation, generated synthetic report, JSON sidecar
  log, tests, data access, trading scope, or profitability language.

Prevention:

- Use PowerShell here-strings or `--body-file` for long Markdown PR bodies in
  this workspace.
- Avoid PowerShell double-quoted strings for Markdown text containing
  backticks.
- Treat PR creation failures as workflow problems that require durable logging
  when they occur during the staged workflow.

---

## 2026-06-07 - PowerShell Rejected Bash Here-Doc Syntax

Original mistake:

- During the local CSV fixture universe-masked signal smoke stage, a quick
  Python inspection snippet was run with Bash here-doc syntax:
  `python - <<'PY'`.
- The active shell for this workspace is Windows PowerShell, not Bash.

Consequence:

- PowerShell rejected the command before Python ran.
- No repository files were modified by the failed command, but the intended
  inspection of exact masked-signal values still had to be rerun.

Evidence:

```text
At line:2 char:11
+ python - <<'PY'
+           ~
Missing file specification after redirection operator.
The '<' operator is reserved for future use.
```

Investigation:

- The error occurred at shell-parse time, before any Python import or fixture
  workflow code executed.
- The command used a Bash redirection pattern that is not valid PowerShell
  syntax.
- The issue was an environment/command-form mistake, not a data, strategy,
  liquidity, backtest, trading, credential, or profitability issue.

Correction attempts:

- Did not change code or tests in response to the failed command.
- Replaced the Bash here-doc with a PowerShell here-string piped to Python:
  `@' ... '@ | python -`.

Final fix:

- Reran the inspection with PowerShell-compatible syntax and printed the
  `alpha_009` fixture factor, masked signal panel, masked-signal summary, and
  low-coverage dates.

Verification:

- The corrected command completed successfully.
- It confirmed the fixture universe mask keeps only `BBB` on `2024-01-04`,
  the masked `alpha_009` valid observation count is `1`, and low-coverage
  dates are `2024-01-02`, `2024-01-03`, and `2024-01-05`.

Remaining caveats:

- This was a local command syntax issue only. It did not affect repository
  behavior or generated outputs.

Prevention:

- Use PowerShell here-strings or `python -c` for ad hoc Python snippets in
  this workspace.
- Treat shell syntax failures as failed checks and rerun the intended check
  before relying on the result.

---

## 2026-06-07 - Universe-Masked Signal Duplicate-Column Validation Order

Original mistake:

- The first `apply_universe_mask_to_signals()` implementation checked
  duplicate signal columns only after passing `signals` through
  `validate_panel_data()`.
- `validate_panel_data()` is designed for normal unique-column numeric panels.
  With duplicate column labels, `data[column]` can return a DataFrame rather
  than a Series, so the validator may try to read a DataFrame `.dtype`
  attribute before the new helper reports the clearer duplicate-column
  problem.

Consequence:

- A new duplicate-column boundary test failed.
- The helper still rejected the bad input, but the failure path was an
  implementation-detail `AttributeError` rather than the intended auditable
  `ValueError`.

Evidence:

```text
tests/test_liquidity.py::test_apply_universe_mask_to_signals_rejects_duplicate_columns
AttributeError: 'DataFrame' object has no attribute 'dtype'. Did you mean: 'dtypes'?

1 failed, 57 passed
```

Investigation:

- The failure occurred before `_validate_unique_columns(signal_panel,
  "signals")` was reached.
- The root cause was validation order, not masking semantics, real-data
  handling, backtest integration, trading behavior, or profitability language.
- `universe_mask` already checked duplicate columns before dtype validation,
  so the issue was limited to the signal-panel path.

Correction attempts:

- Did not remove or weaken the duplicate-column test.
- Did not modify the shared `validate_panel_data()` helper because this stage
  is scoped to the universe-masked signal adapter.
- Moved the duplicate-column check ahead of `validate_panel_data()` only when
  `signals` is already a pandas DataFrame, preserving the existing non-DataFrame
  type error from the shared validator.

Final fix:

- `apply_universe_mask_to_signals()` now checks duplicate signal columns on
  the raw `signals` DataFrame before numeric panel validation.
- Duplicate labels now raise the intended `ValueError` with
  `columns must not contain duplicates`.

Verification:

```text
python -m pytest -q tests/test_liquidity.py
58 passed
```

Remaining caveats:

- The fix is local to the new adapter. Other helpers that rely directly on
  `validate_panel_data()` were not changed in this Stage 72 PR.

Prevention:

- For future strict panel adapters, validate duplicate labels before selecting
  columns by label or delegating to validators that assume unique columns.

---

## 2026-06-07 - Local CSV Fixture Universe-Mask Test Expectation Drift

Original mistake:

- The first partial update to the local CSV fixture workflow added a
  universe-mask count diagnostic to the report and JSON log, but the existing
  report/log test still asserted the old caveat text
  `not universe construction`.
- That old assertion was correct before the helper existed, but it became stale
  once this stage intentionally began reporting a synthetic universe-mask
  count smoke check.

Consequence:

- The first full test run on the branch failed with one test failure.
- The branch was not safe to commit because the tests no longer described the
  intended workflow boundary: there is now a universe-mask diagnostic, but
  still no tradeable universe study, backtest integration, portfolio
  construction, execution logic, or performance interpretation.

Evidence:

```text
tests/test_local_csv_fixture_workflow_demo.py::test_workflow_report_and_experiment_log_are_created_with_caveats
AssertionError: assert 'not universe construction' in '# Local CSV Fixture Workflow Demo\n...'

1 failed, 416 passed
```

Investigation:

- Inspected the working diff and confirmed the code had intentionally added
  `construct_liquidity_universe()` to the local fixture workflow.
- Checked the generated report text and confirmed it now contains a
  `Liquidity Universe Mask Smoke Check` section with count-only audit output.
- Verified the mismatch was not a real-data, trading, credential, brokerage,
  order-execution, profitability, loader, backtester, or metrics issue.
- Identified the root cause as test expectation drift: the old test was still
  checking for "no universe construction" wording instead of the new, narrower
  "universe-mask count only, no backtest/tradeability integration" boundary.

Correction attempts:

- Did not restore the old wording because that would hide the newly intended
  universe-mask smoke diagnostic.
- Did not weaken the test to ignore the liquidity section.
- Updated the test to assert the new Markdown section, expected count row,
  JSON universe-count diagnostics, low-coverage dates, caveats, and helper
  call count.
- Tightened JSON serialization so the `low_coverage` audit flag remains a
  boolean instead of being serialized as a numeric value.

Final fix:

- `research/local_csv_fixture_workflow_demo.py` now serializes universe-mask
  audit summaries with boolean `low_coverage` values and preserves caveated
  count-only wording.
- `tests/test_local_csv_fixture_workflow_demo.py` now verifies the universe
  mask, summary, low-coverage dates, generated report section, JSON
  diagnostics, caveats, helper reuse, and invalid universe-mask config.
- The default synthetic report and experiment log were regenerated from the
  committed fixture only.

Verification:

```text
python -m pytest -q tests/test_local_csv_fixture_workflow_demo.py
13 passed

python -m pytest -q
417 passed

python -m compileall src tests research
passed
```

Remaining caveats:

- This remains a committed synthetic fixture smoke check only.
- It does not integrate a liquidity universe into the backtester, produce
  weights, create trades, fetch real data, validate market tradeability, or
  support any performance interpretation.

Prevention:

- When a staged PR intentionally changes a caveat boundary from "not present"
  to "present only as a diagnostic," update tests to assert the new positive
  diagnostic contract and the negative guardrails together.
- Keep future liquidity stages split between eligibility counts, universe-mask
  diagnostics, and backtest consumption so stale wording does not blur the
  scope boundary.

---

## 2026-06-07 - Liquidity Universe Missing-Eligibility Downcast Warning

Original mistake:

- The first implementation of `construct_liquidity_universe()` cleaned a
  boolean-or-missing eligibility panel with `fillna(False).astype(bool)`.
- That worked for the current test data, but object-dtype panels containing
  booleans and `NaN` triggered pandas' future silent-downcasting warning.

Consequence:

- The focused liquidity tests passed, but the run emitted a warning that could
  become a future behavior change or hide an avoidable dtype assumption.
- The stage was not ready for commit while validation was warning-clean only by
  coincidence.

Evidence:

```text
tests/test_liquidity.py::test_construct_liquidity_universe_counts_missing_eligibility_before_excluding
FutureWarning: Downcasting object dtype arrays on .fillna, .ffill, .bfill is deprecated
and will change in a future version.
src\features\liquidity.py:314: clean_mask = eligibility_mask.fillna(False).astype(bool)
```

Investigation:

- The warning came from the missing-eligibility path, where tests intentionally
  use an object-dtype panel so `True`, `False`, and `NaN` can coexist before
  validation.
- Non-missing values were already validated to be actual booleans, so missing
  values did not need string, numeric, or sentinel coercion.

Correction attempts:

- Did not suppress the warning.
- Did not relax the missing-value test.
- Did not replace missing eligibility with forward-fill, backward-fill, zero
  defaults, or any repair policy.
- First replaced `fillna(False).astype(bool)` with `eq(True).astype(bool)`.
- A follow-up robustness check showed that pandas nullable `boolean` dtype can
  preserve `<NA>` after `eq(True)`, causing `astype(bool)` to fail.

Final fix:

- Replaced `fillna(False).astype(bool)` with
  `eq(True).fillna(False).astype(bool)`.
- This keeps only explicit `True` values eligible and maps `False`, `NaN`, or
  nullable `<NA>` values to `False` without relying on object-array
  downcasting.

Verification:

```text
python -m pytest -q tests/test_liquidity.py
44 passed
```

Remaining caveats:

- This helper still consumes synthetic/local panels only. It does not validate
  real-data provenance or make a liquidity rule tradable.

Prevention:

- For future pandas object panels that intentionally preserve missing values,
  prefer explicit boolean comparisons or typed construction over
  `fillna(...).astype(...)` when pandas warns about silent downcasting.

---

## 2026-06-07 - Alpha#012 LEAN Plan Patch Context Mismatch

Original mistake:

- During the Alpha#012 QuantConnect/LEAN plan refresh, the first attempted
  patch used an imprecise context line for the universe filter section in
  `docs/quantconnect_lean_plan.md`.
- The patch expected `Candidate filter:` without matching the exact markdown
  bullet context used in the file.

Consequence:

- `apply_patch` rejected the combined patch before any file changes from that
  patch were applied.
- The documentation stage could not proceed safely until the exact current file
  context was inspected.

Evidence:

```text
apply_patch verification failed: Failed to find expected lines in
D:\Users\MINQI\Documents\New project\docs\quantconnect_lean_plan.md:
Candidate filter:
  - price above a minimum threshold, such as `$5`.
  - positive dollar volume.
  - sufficient daily history for 252-day lookback plus 21-day skip.
  - exclude symbols with missing or stale data at rebalance.
```

Investigation:

- Checked `git status -sb --untracked-files=all` to verify that the failed
  patch did not leave partial changes.
- Used `Select-String` around `Current local status`, `Local component`,
  `Candidate filter`, `Signal Generation Timing`, and
  `Recommended Next LEAN` to inspect the exact current markdown structure.
- Confirmed the failed context was a patch-authoring issue, not a repository
  content problem or test failure.

Correction attempts:

- Did not force the combined patch.
- Reapplied the same intended documentation changes as smaller patches with
  exact nearby context.
- Kept the stage scope documentation-only and limited to the LEAN planning
  docs, durable logs, and changelog.

Final fix:

- Updated `docs/quantconnect_lean_plan.md` in smaller chunks for current
  status, local-to-LEAN mapping, universe/history assumptions, signal timing,
  diagnostic export, and next LEAN-related stage.
- Updated `docs/lean_parity_checklist.md` separately for Alpha#012 assertions
  and coverage requirements.

Verification:

- `git diff --check` passed after the corrected patches.
- Full validation is rerun before the associated PR is committed and opened.

Remaining caveats:

- The failed patch was local tooling friction only. It did not modify source
  code, tests, research scripts, generated reports, data access, execution
  behavior, credentials, brokerage behavior, or performance language.

Prevention:

- For future edits to long markdown files, inspect the exact target section
  before applying broad multi-section patches, and prefer smaller patches when
  the file has recently changed.

---

## 2026-06-07 - Alpha#012 Fixture Rank IC Exact-Float Test Expectation

Original mistake:

- During the Alpha#012 local-fixture diagnostics stage, the new JSON-log test
  asserted that the serialized Alpha#012 Rank IC value for `2024-01-03` was
  exactly `1.0`.

Consequence:

- The focused local CSV fixture workflow test failed even though the diagnostic
  calculation produced the expected perfect rank relationship within normal
  floating-point precision.

Evidence:

```text
tests/test_local_csv_fixture_workflow_demo.py::test_workflow_report_and_experiment_log_are_created_with_caveats
AssertionError: {'2024-01-03': 0.9999999999999999} != {'2024-01-03': 1.0}
```

Investigation:

- The Alpha#012 fixture values on the only valid diagnostic date have two
  overlapping assets, so the expected Rank IC is effectively 1.
- The value is computed through pandas/Spearman correlation and JSON
  serialization, which can represent the result as `0.9999999999999999`
  instead of exactly `1.0`.
- This was a test-expectation precision issue, not a workflow, alignment,
  missing-data, or guardrail failure.

Correction attempts:

- The diagnostic calculation was not changed.
- The test was not weakened to ignore the diagnostic.
- The assertion was changed to keep exact `None` checks for missing dates while
  using `pytest.approx(1.0)` for the finite Rank IC value.

Final fix:

- Updated `tests/test_local_csv_fixture_workflow_demo.py` to compare the
  finite Alpha#012 Rank IC JSON value with approximate floating-point equality.

Verification:

- The focused workflow test was rerun after the assertion fix:
  `python -m pytest -q tests/test_local_csv_fixture_workflow_demo.py`
  reported 13 passed.

Remaining caveats:

- Exact JSON equality remains useful for structural fields and missing dates,
  but floating correlation values should use tolerance-based comparisons.

Prevention:

- Future tests for Pearson, Spearman, IC, Rank IC, and other floating
  diagnostics should assert exact structure and use approximate comparisons for
  finite computed floats.

---

## 2026-06-07 - Alpha#012 Hand-Calculation Test Sign Error

Original mistake:

- During the first Alpha#012 implementation stage, the hand-calculated
  expected value for ticker `BBB` on the first valid date was written as
  `+1.0`.
- The public formula being implemented is:

```text
sign(delta(volume, 1)) * (-1 * delta(close, 1))
```

- For that test row, volume decreased from `50.0` to `40.0`, so
  `sign(delta(volume, 1))` is `-1`. Close decreased from `20.0` to `19.0`,
  so `(-1 * delta(close, 1))` is `+1`. The correct product is `-1`.

Consequence:

- The focused WorldQuant alpha test suite failed before the stage could be
  validated.
- No files were staged, committed, pushed, or merged while the failure was
  present.

Evidence:

```text
tests/test_worldquant_alphas.py::test_alpha_012_matches_public_formula_hand_calculation

E       assert np.float64(-1.0) == 1.0 +/- 1.0e-06
E         Obtained: -1.0
E         Expected: 1.0 +/- 1.0e-06
```

Investigation:

- Recomputed the formula terms for the failing row.
- Confirmed the implementation output matched the source formula.
- Confirmed only the test expectation had the wrong sign.

Correction attempts:

- Did not change the implementation because the implementation matched the
  reviewed formula.
- Corrected the expected value in
  `tests/test_worldquant_alphas.py::test_alpha_012_matches_public_formula_hand_calculation`
  from `+1.0` to `-1.0`.

Final fix:

- The test now matches the hand calculation for both falling-volume /
  falling-close and mixed-sign cases.

Verification:

- Focused and full validation are rerun in the Alpha#012 PR after this fix.

Remaining caveats:

- Alpha#012 is still a research feature only. Passing formula tests does not
  imply factor validity, strategy performance, or profitability.

Prevention:

- For future formula tests, write each hand-calculated term explicitly before
  asserting the final product, especially when nested signs are involved.
- Keep any failed formula-transcription or hand-calculation check visible in
  this log before committing.

---

## 2026-06-06 - Reversal Missing-Value Test Assumed Full Interior Window

Original mistake:

- Wrote the first short-term reversal missing-value test as if every row inside
  the lookback span had to be non-missing.
- The implemented and documented formula uses explicit current and trailing
  price anchors:

```text
-(price[t] / price[t - lookback_periods] - 1)
```

- Under that anchor-based formula, a missing non-anchor price inside the span is
  not used in the calculation and should not force the score to `NaN`.

Consequence:

- The focused reversal test suite failed even though the implementation
  matched the explicit anchor formula.
- The failure exposed that the test was enforcing an unstated rolling-window
  completeness policy rather than the chosen return-anchor policy.

Evidence:

```text
tests/test_reversal.py::test_short_term_reversal_does_not_fill_missing_values

AssertionError: assert np.False_
where np.False_ = np.isnan(np.float64(0.09999999999999998))
```

Investigation:

- Checked the failing row and confirmed `lookback_periods=2` at
  `2024-03-31` used the valid anchors `2024-01-31` and `2024-03-31`.
- Confirmed the missing value on `2024-02-29` was an interior non-anchor value.
- Compared the design to the existing momentum implementation, which also uses
  explicit anchors rather than requiring every interior row to be present.

Correction attempts:

- Did not change the implementation to require full interior windows because
  that would silently change the stated reversal formula and make it less
  consistent with the existing momentum feature style.
- Updated the test to assert the valid anchor-based score for the interior-gap
  row and retain `NaN` expectations for missing current or trailing anchors.

Final fix:

- `tests/test_reversal.py` now verifies that missing anchor values produce
  `NaN`, while a missing non-anchor row does not alter the explicit
  anchor-based return calculation.

Verification:

```text
python -m pytest -q tests/test_reversal.py
13 passed
```

Remaining caveats:

- If a future reversal definition needs a full-window cumulative-return or
  rolling-quality policy, it should be added as a separately named helper with
  its own tests rather than changing this anchor-based feature silently.

Prevention:

- When testing feature missing-data behavior, first identify exactly which
  observations the formula consumes.
- Keep formula-level tests aligned with the documented calculation instead of
  adding stricter data-quality requirements implicitly.

---

## 2026-06-06 - PowerShell Multi-Path Listing Command Failed

Original mistake:

- During the post-liquidity checkpoint review, attempted to list files across
  multiple directories with `Get-ChildItem -Path src/features tests research
  reports -File -Recurse`.
- This syntax treated later path tokens as positional arguments instead of as
  a single array passed to `-Path`.

Consequence:

- The exploratory file listing failed and did not produce evidence for the
  checkpoint report.
- No repository files were modified by the failed command.

Evidence:

```text
Get-ChildItem : A positional parameter cannot be found that accepts argument 'research'.
```

Investigation:

- Confirmed the failure was command syntax, not a repository-state issue.
- Replaced the PowerShell command with `rg --files src/features tests research
  reports`, which accepts multiple search roots and produced the intended
  evidence list.

Correction attempts:

- Did not retry with broad or destructive filesystem operations.
- Used `rg --files` for the file inventory and a focused `rg -n` search for
  implemented helper functions.

Final fix:

```text
rg --files src/features tests research reports | Sort-Object
rg -n "def factor_information_coefficient|def factor_rank_information_coefficient|def factor_quantile_spread|def make_train_validation_test_split|def average_daily_volume_eligibility|def average_dollar_volume_eligibility" src tests research
```

Verification:

- The corrected commands listed the current feature, test, research, and report
  files.
- They confirmed that diagnostics, validation split, and liquidity helper
  functions already exist.

Remaining caveats:

- This was a tooling syntax issue only; it did not affect source code,
  tests, generated reports, data access, trading behavior, or experiment
  results.

Prevention:

- Prefer `rg --files` for multi-root file inventories.
- When using PowerShell `Get-ChildItem` with multiple paths, pass an explicit
  array such as `-Path @("src/features", "tests", "research", "reports")`.

---

## 2026-06-05 - Local CSV Fixture Split Table Formatter Failure

Original mistake:

- Reused the local CSV fixture workflow's existing Markdown table formatter for
  the new split summary table.
- That formatter assumed every DataFrame index value was a date and converted
  each index through `pd.Timestamp(index)`.
- The new split summary index values are labels: `train`, `validation`, and
  `test`.

Consequence:

- The workflow could compute split diagnostics, but report generation failed
  whenever the split summary table was rendered.
- This broke focused tests that create the local CSV fixture workflow report.

Evidence:

```text
tests/test_local_csv_fixture_workflow_demo.py::test_workflow_report_and_experiment_log_are_created_with_caveats
tests/test_local_csv_fixture_workflow_demo.py::test_main_writes_report_to_requested_path
tests/test_local_csv_fixture_workflow_demo.py::test_workflow_text_contains_only_caveated_profitability_language

pandas._libs.tslibs.parsing.DateParseError:
Unknown datetime string format, unable to parse: train
```

Investigation:

- Confirmed that the factor, forward-return, IC, Rank IC, and quantile-spread
  computations completed before report writing.
- Traced the failure to `_format_markdown_table(result.split_summary)`.
- Confirmed that `_format_markdown_table()` was date-table-specific and should
  still be used for date-indexed IC and quantile-spread diagnostics.
- Confirmed that the new split summary needed a labeled-index renderer rather
  than date parsing.

Correction attempts:

- First added `_format_labeled_index_markdown_table()` and used it only for
  `result.split_summary`, leaving the existing date-indexed table formatter in
  place for diagnostic date tables.
- Reran focused tests. Report generation then succeeded, but one report-text
  assertion exposed that count-like split summary columns were formatted as
  `0.0000` because the row dtype was widened by mean columns.
- Extended `_format_table_value()` so count-like fields ending in
  `_observations` or `_valid_dates` render as integers, matching the report's
  diagnostic-count semantics.

Final fix:

- Split-summary rendering now uses a labeled-index Markdown formatter with an
  explicit `split` index label.
- Count-like split summary fields now render as integers while mean IC fields
  remain decimal values and missing means remain `NaN`.

Verification:

```text
python -m pytest -q tests/test_local_csv_fixture_workflow_demo.py
12 passed

python -m pytest -q
309 passed

python -m compileall src tests research
passed
```

Remaining caveats:

- The fixture split has only four dates, so train and validation windows are
  intentionally tiny. The report labels this as a synthetic fixture wiring
  check, not a real train/validation/test research study.

Prevention:

- Do not reuse date-specific renderers for non-date-index tables.
- When adding report tables with mixed count and mean columns, inspect the
  rendered Markdown as well as the underlying DataFrame.
- Keep focused tests that write report and JSON outputs, not only tests that
  inspect in-memory result objects.

---

## 2026-06-05 - Rebase Continue Opened Editor And Timed Out

Original mistake:

- Ran `git rebase --continue` without forcing a non-interactive editor during
  the split-aware IC / Rank IC demo branch rebase.
- In this Windows environment, Git opened Notepad++ for the commit message
  rather than completing the rebase directly.

Consequence:

- The shell command timed out while Git waited for the editor-backed commit to
  finish.
- The rebase remained in progress with all conflict resolutions staged.
- No branch was pushed and no PR was opened while the rebase was incomplete.

Evidence:

```text
command timed out after 124276 milliseconds

git status
interactive rebase in progress; onto 4884a53
all conflicts fixed: run "git rebase --continue"

Get-CimInstance Win32_Process
git.exe rebase --continue
git commit -n --no-gpg-sign -F .git/rebase-merge/message -e --allow-empty
notepad++.exe ... .git/rebase-merge/message
```

Investigation:

- Checked `git status` and confirmed the rebase was still waiting at the final
  continue step with all intended files staged.
- Inspected process command lines and confirmed the timeout was caused by the
  editor-backed commit step, not by a new merge conflict.

Correction attempts:

- Stopped only the stuck Git processes by exact PID.
- Left the user-visible Notepad++ process alone.
- Reran the continue step with a non-interactive editor override.

Final fix:

```text
git -c core.editor=true rebase --continue
```

This completed the rebase and rewrote the local split-aware demo commit onto
the latest `main`.

Verification:

```text
Successfully rebased and updated refs/heads/codex/synthetic-split-ic-rank-ic-demo.

python -m pytest -q tests/test_synthetic_split_ic_rank_ic_demo.py
11 passed

python -m pytest -q
308 passed

python -m compileall src tests research
passed

git diff --check
passed with Windows line-ending conversion warnings only
```

Remaining caveats:

- This was a Git editor configuration issue, not a source-code or test
  failure.

Prevention:

- Use `git -c core.editor=true rebase --continue` for non-interactive rebase
  continuations in this workspace.
- Avoid plain `git rebase --continue` when a previous conflict resolution has
  staged all files and only commit-message confirmation remains.

---

## 2026-06-05 - Split-Aware Demo Rebase Conflict After PR #49 Merge

Original assumption:

- The locally committed split-aware IC / Rank IC demo branch could be
  published after the prior open merge gate cleared.
- PR #49 merged while this continuation was in progress and modified
  `CHANGELOG.md` and `docs/engineering_log.md`, which were also touched by the
  local split-aware demo commit.

Consequence:

- Rebasing `codex/synthetic-split-ic-rank-ic-demo` onto the latest `main`
  stopped with content conflicts in the two overlapping documentation files.
- No branch was pushed and no PR was opened before the conflict was resolved.

Evidence:

```text
CONFLICT (content): Merge conflict in CHANGELOG.md
CONFLICT (content): Merge conflict in docs/engineering_log.md
error: could not apply 0280093... Add split-aware IC Rank IC demo
```

Investigation:

- Confirmed the conflicts were limited to adjacent top-of-file changelog and
  engineering-log entries.
- Confirmed the code and test files from the split-aware demo applied cleanly.
- Confirmed PR #49 was merged and latest `main` passed baseline validation
  before rebasing the prepared branch.

Correction attempts:

- Resolved `CHANGELOG.md` by keeping both the already-merged Apache-2.0
  metadata entries and the new split-aware diagnostic demo entry.
- Resolved `docs/engineering_log.md` by keeping the PR #49 metadata checkpoint
  and the split-aware demo checkpoint as separate durable entries.

Final fix:

- Removed conflict markers and preserved both stages' documentation.
- Kept the split-aware demo scope unchanged: synthetic panels only, no real
  data fetching, no backtest, no broker, no order execution, and no
  profitability claim.

Verification:

```text
rg -n "<<<<<<<|=======|>>>>>>>" CHANGELOG.md docs/engineering_log.md docs/troubleshooting_log.md research/synthetic_split_ic_rank_ic_demo.py tests/test_synthetic_split_ic_rank_ic_demo.py
no matches

python -m pytest -q tests/test_synthetic_split_ic_rank_ic_demo.py
11 passed

python -m pytest -q
308 passed

python -m compileall src tests research
passed

git diff --check
passed with Windows line-ending conversion warnings only
```

Remaining caveats:

- This was a documentation merge conflict only. It did not indicate a
  functional failure in the split helper, diagnostic helpers, or demo logic.

Prevention:

- When a local branch waits behind an external PR gate, expect overlapping log
  and changelog conflicts after the gate merges.
- Rebase onto the newly merged `main`, preserve both log entries, and rerun
  focused plus full validation before pushing.

---

## 2026-06-05 - Validation Split Empty-Test Expectation Mismatch

Original mistake:

- The first version of `tests/test_validation.py` included a parameterized
  empty-window test case with `validation_end="2024-01-06"` while the default
  `test_end` was also the final index date, `2024-01-06`.
- The test expected the helper to report an empty test split.

Consequence:

- The focused validation test failed even though the helper was rejecting the
  input for a stricter and earlier reason: the configured split boundaries did
  not satisfy the required chronological order.
- No files were committed, pushed, or merged before the failure was fixed.

Evidence:

```text
tests/test_validation.py::test_make_train_validation_test_split_rejects_empty_windows[2024-01-02-2024-01-06-test split]
AssertionError: Regex pattern did not match.
Expected regex: 'test split'
Actual message: 'split boundaries must satisfy train_end < validation_end < test_end'
```

Investigation:

- Reviewed the failing case against the helper contract.
- Confirmed that when `test_end` is omitted, the helper uses the final
  available date as the test boundary.
- Confirmed that `validation_end == test_end` violates the intended strict
  boundary ordering before any empty-window check should run.
- Confirmed that another test already covers this invalid boundary-order case.

Correction attempts:

- No code change was needed because the helper behavior was correct.
- Removed the contradictory duplicate parameter from the empty-window test
  case instead of weakening the boundary-order validation.

Final fix:

- Kept strict `train_end < validation_end < test_end` validation.
- Kept empty-window tests for train and validation windows where the boundary
  ordering remains meaningful.
- Left the `validation_end == test_end` case covered by the invalid-boundary
  test.

Verification:

```text
python -m pytest -q tests/test_validation.py
25 passed

python -m pytest -q
297 passed

python -m compileall src tests research
passed

git diff --check
passed with Windows line-ending conversion warnings only
```

Remaining caveats:

- The helper is intentionally limited to chronological date-window splitting.
  It does not perform model selection, calculate returns, or interpret any
  diagnostic result.

Prevention:

- For future split tests, separate invalid-boundary-order cases from
  empty-window cases.
- When a helper performs staged validation, assert the earliest intended
  validation failure rather than a later condition that cannot be reached.

---

## 2026-06-04 - README Diff Filter Regex Error

Original mistake:

- During the GitHub landing-page polish scope review, an optional
  `Select-String` diff-filter command used a regex that included an unescaped
  `[` character.

Consequence:

- The optional filtered diff display failed before printing its intended
  heading summary.
- No repository files were modified by the failed command, and the required
  validation checks had already passed, but the diff review needed to be rerun
  with a valid command before commit.

Evidence:

```text
Select-String : The string ... is not a valid regular expression:
Unterminated [] set.
```

Investigation:

- The failing pattern included alternatives such as `^\+![` without escaping
  the bracket.
- The failure was isolated to the optional presentation filter, not to
  Markdown, tests, link checking, or repository content.

Correction attempts:

- The invalid regex was not reused.
- The diff review was rerun with simpler `git diff --stat` and
  `Select-String -SimpleMatch` commands.

Final fix:

- Used fixed-string matching for README section headings and the visual asset
  reference.

Verification:

- The rerun diff review showed the intended README sections and visual asset
  reference.
- `git status --short --untracked-files=all` still showed only the intended
  documentation and asset files.

Remaining caveats:

- The failed command was an inspection aid only; it did not affect repository
  content.

Prevention:

- Prefer `Select-String -SimpleMatch` for literal diff-heading checks.
- Escape regex metacharacters when using `Select-String -Pattern`.

---

## 2026-06-04 - Parallel Pull And State Check Race

Original mistake:

- During the continuation after PR #41 was open, `git pull --ff-only origin
  main` was run in parallel with `git status` and `git log`.

Consequence:

- The `git log` output could show the pre-pull commit while the pull was
  fast-forwarding `main`.
- No files were edited, staged, committed, pushed, or merged during the
  ambiguous state check, but the state evidence needed to be refreshed before
  choosing the next stage.

Evidence:

- `git pull --ff-only origin main` fast-forwarded from the PR #40 merge to the
  PR #41 merge.
- The parallel `git log` output still showed the PR #40 merge as `HEAD`.

Investigation:

- Treated the parallel state output as potentially stale.
- Reran `git status`, `git log`, `gh pr view 41`, and `gh pr list --state
  open` after the pull completed.

Correction attempts:

- No failed correction attempt occurred. The recovery was to rerun the state
  checks after the branch-changing command completed.

Final fix:

- Used the post-pull state as authoritative.
- Confirmed `main` was at the PR #41 merge commit before selecting the next
  stage.

Verification:

- `git log --oneline --decorate -8` showed `main` at the PR #41 merge commit.
- `gh pr view 41` confirmed PR #41 was merged.
- `gh pr list --state open` returned no open pull requests.
- `python -m pytest -q` reported 264 passed.
- `python -m compileall src tests research` passed.

Remaining caveats:

- Parallel shell commands are appropriate for independent reads only when no
  command mutates the working tree, branch pointer, or index.

Prevention:

- Do not run `git pull`, `git switch`, or other branch-changing commands in
  parallel with status or log reads used as authoritative evidence.
- After any branch-changing command, rerun state checks before selecting a
  stage or editing files.

---

## 2026-06-04 - Parallel Read And Branch Switch Race

Original mistake:

- During a long-running workflow continuation after PR #40, file reads for
  roadmap documents were run in parallel with `git switch main`.

Consequence:

- Some displayed document output could have come from the pre-switch branch
  rather than the synced `main` checkout.
- No files were edited, staged, committed, pushed, or merged during this
  ambiguous read window, but the evidence used for next-stage selection needed
  to be refreshed from the authoritative current branch.

Evidence:

- The parallel output showed PR #40 scaffold content while the branch switch
  was still occurring.
- Because the file reads and branch switch were independent parallel tool
  calls, their exact ordering was not guaranteed.

Investigation:

- Treated the parallel-read output as potentially stale instead of relying on
  it for stage selection.
- Confirmed local `main` was then fast-forwarded to the PR #40 merge commit.
- Reread current scaffold and planning documents from the synced `main`
  checkout before selecting the next stage.

Correction attempts:

- No failed correction attempt occurred. The immediate recovery was to rerun
  state checks and reread the relevant current files after `main` was synced.

Final fix:

- Used the post-pull `main` state as authoritative for the next-stage decision.
- Selected a documentation-only LEAN scaffold review checklist based on the
  merged PR #40 scaffold and current planning documents.

Verification:

- `git log --oneline --decorate -8` showed `main` at the PR #40 merge commit.
- `gh pr view 40` confirmed PR #40 was merged.
- `gh pr list --state open` returned no open pull requests.
- `python -m pytest -q` reported 264 passed.
- `python -m compileall src tests research` passed.

Remaining caveats:

- Parallel file reads are safe only when the working tree reference is stable.
  They are not reliable while a branch switch or pull is changing the checkout.

Prevention:

- Do not run branch-changing commands in parallel with file reads whose content
  is used for stage selection.
- After any branch switch or pull, rerun state checks and reread relevant
  roadmap files before editing.

---

## 2026-06-04 - LEAN Scaffold README Guardrail Phrase Mismatch

Original mistake:

- The first version of `lean/README.md` described the same guardrail as
  "real data downloads" and "real market data fetching or downloads", but the
  new static guardrail test expected the exact phrase `no real market data`.

Consequence:

- The focused scaffold test failed even though the intended guardrail was
  present in less exact wording.

Evidence:

```text
tests/test_lean_smoke_test_scope.py::test_lean_scaffold_readme_preserves_guardrails
AssertionError: assert 'no real market data' in ...
```

Investigation:

- Compared the failing expected phrase with `lean/README.md`.
- Confirmed the README prohibited real data downloads but did not include the
  exact wording required by the static test.
- Confirmed this was a documentation/test wording mismatch, not an
  implementation of real data access.

Correction attempts:

- The test was not weakened and the guardrail expectation was not removed.
- First correction attempt added `no real market data path`, but the line wrap
  split the phrase as `no\nreal market data`, so the exact string check still
  failed.
- Second correction attempt placed `no real market data` on one line, but the
  focused test then exposed that other exact README phrases such as
  `no live trading` and `no brokerage` were still implied rather than written
  directly.

Final fix:

- Updated `lean/README.md` to include an `Explicit Guardrail Phrases` section
  containing the exact static-review phrases required by the test.

Verification:

- The focused test and full validation were rerun after the README fix:
  `python -m pytest -q tests/test_lean_smoke_test_scope.py` reported
  6 passed, `python -m pytest -q` reported 264 passed,
  `python -m compileall src tests research` passed,
  `python -m compileall lean` passed, and `git diff --check` passed with
  Windows line-ending conversion warnings only.

Remaining caveats:

- Exact-phrase guardrail tests can fail on equivalent wording. In this case
  the explicit wording is useful because it makes the human-facing README
  clearer.

Prevention:

- When adding static documentation guardrail tests, copy the required caveat
  phrases directly into the human-facing document during the same edit pass.

---

## 2026-06-04 - Stage Edits Started Before Branch Creation

Original mistake:

- During the synthetic IC / Rank IC diagnostics stage, implementation edits
  began after syncing `main` but before creating the dedicated stage branch.

Consequence:

- The worktree had uncommitted stage changes on local `main`.
- No files were staged, committed, pushed, or merged, and the remote `main` was
  not affected, but the local workflow temporarily violated the project rule to
  use a separate branch for each stage.

Evidence:

- The startup checks showed the repository on `main` after PR #32 was merged
  and pulled.
- After implementing the helper and tests, `git diff --name-only` showed local
  changes in `docs/engineering_log.md`, `src/features/diagnostics.py`, and
  `tests/test_diagnostics.py` before a stage branch had been created.

Investigation:

- Confirmed the issue was a workflow sequencing error, not a source-code
  correctness failure.
- Confirmed the changes were still unstaged and uncommitted, so they could be
  moved safely onto a branch without rewriting history or touching remote
  state.

Correction attempts:

- No failed correction attempt occurred. The direct recovery path was to create
  the branch from the current `main` state while preserving the unstaged
  changes.

Final fix:

- Ran `git switch -c codex/synthetic-ic-rank-ic-diagnostics`.
- The uncommitted stage changes moved onto the dedicated branch.

Verification:

- `git branch --show-current` returned
  `codex/synthetic-ic-rank-ic-diagnostics`.
- `git status -sb --untracked-files=all` showed only intended unstaged files on
  that branch before commit review.

Remaining caveats:

- The branch was created after edits instead of before edits. The final branch
  diff is still reviewable, but the sequencing mistake should remain visible in
  the durable log.

Prevention:

- After syncing `main` and passing baseline validation, create the stage branch
  before applying any patch.
- Treat the branch creation step as part of the pre-edit checklist, not as a
  pre-commit cleanup step.

---

## 2026-06-03 - PowerShell Search Pattern Quoting Error

Original mistake:

- During the WorldQuant catalog refresh scope review, a stale-text `rg` search
  used a PowerShell double-quoted string that contained Markdown backticks.

Consequence:

- The search command failed before checking the target documents.
- No repository files were modified by the failed command, and baseline tests
  had already passed, but the intended stale-text check still needed to be
  rerun.

Evidence:

```text
The string is missing the terminator: ".
CategoryInfo          : ParserError
FullyQualifiedErrorId : TerminatorExpectedAtEndOfString
```

Investigation:

- The failing pattern included `` `alpha_009` `` inside a PowerShell
  double-quoted command string.
- PowerShell treats the backtick as an escape character, so the shell parsed
  the command incorrectly before `rg` could run.

Correction attempts:

- The failed double-quoted command was not reused.
- The check was rerun with a single-quoted PowerShell pattern so Markdown
  backticks were treated as literal characters.

Final fix:

- Reran the stale-text search successfully with single quotes around the regex
  pattern.

Verification:

- The corrected search completed.
- The only remaining match was an older 2025 historical engineering-log entry,
  not the refreshed `docs/worldquant_alpha_catalog.md`.
- The catalog no longer contains the stale current-state text that said no
  alpha was implemented.

Remaining caveats:

- Historical logs can correctly preserve older milestone wording and should not
  be rewritten unless they are explicitly misleading as current guidance.

Prevention:

- Use single-quoted PowerShell strings for `rg` patterns that contain Markdown
  backticks.
- Treat shell quoting failures as failed checks and rerun the check before
  committing.

---

## 2026-06-03 - Missing Long-Running Workflow Control Files

Original assumption:

- The continuation request referenced
  `docs/codex_long_running_controller.md`, `docs/decision_log.md`,
  `docs/troubleshooting_log.md`, `CHANGELOG.md`, and
  `scripts/audit-skills.ps1` as files to read before continuing.

Consequence:

- Future Codex sessions could not rely on those files for startup order,
  durable decisions, troubleshooting history, changelog review, or Skill audit
  checks.
- The staged workflow Skill existed, but supporting controller and log
  artifacts were incomplete.

Evidence:

```text
MISSING docs\codex_long_running_controller.md
MISSING docs\decision_log.md
MISSING docs\troubleshooting_log.md
MISSING CHANGELOG.md
MISSING scripts\audit-skills.ps1
```

Investigation:

- Synced latest `main` after PR #27 was merged.
- Confirmed the repository was clean and had no open PRs.
- Read `README.md`, `AGENTS.md`,
  `.agents/skills/staged-quant-workflow/SKILL.md`,
  `docs/engineering_log.md`, and `docs/project_overview.md`.
- Listed `docs/`, `.agents/skills/`, and `scripts/` paths to confirm the
  referenced files were absent rather than overlooked.

Correction attempts:

- No failed correction attempt occurred in this stage. The missing files were a
  repository scaffolding gap, not a failing code path.

Final fix:

- Added `docs/codex_long_running_controller.md`.
- Added `docs/decision_log.md`.
- Added `docs/troubleshooting_log.md`.
- Added `CHANGELOG.md`.
- Added `scripts/audit-skills.ps1`.
- Updated `.agents/skills/staged-quant-workflow/SKILL.md` to reference the
  controller and audit script.
- Updated `docs/engineering_log.md` with the workflow-control scaffolding
  milestone.

Verification:

- `python -m pytest -q`: 209 passed.
- `python -m compileall src tests research`: passed.
- `.\scripts\audit-skills.ps1`: passed for 1 Skill file.
- `git diff --check`: passed with Windows line-ending conversion warnings only.

Remaining caveats:

- The audit script checks local Skill file structure only. It does not prove
  that a Skill is semantically complete.
- The controller should stay concise and should not become a substitute for
  current repo and PR state checks.

Prevention:

- Future long-running workflow continuations should read the controller and
  logs first.
- Missing expected controller or log files should be treated as workflow
  infrastructure gaps before new research implementation begins.

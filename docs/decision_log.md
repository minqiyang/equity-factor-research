# Decision Log

This log records durable workflow, architecture, and research-process decisions
for the simulated equity factor research project.

It is not an experiment log and must not be used to claim profitability or
investment performance.

## How To Update This Log

- Add a dated entry for decisions that future Codex sessions should preserve.
- State the context, decision, rationale, consequences, and follow-up.
- Keep entries factual and separate observed evidence from assumptions.
- Link or name the relevant files, branches, PRs, checks, or logs when useful.

---

## 2026-10-09 - Three Tiers of an R1–R12 Finding

Context:

- Under the coordinator rule of 2026-10-06, every R1–R12 violation was fixed, also at zero impact. In round 2 of
  card m55-endgap, a review seat used that rule to make two findings MATERIAL whose trigger count on the
  run-of-record data was zero. A further repair and review round would have followed for cases that the data
  cannot produce. The rule also conflicted with the rule against over-engineering.

Decision:

- Owner decision (2026-10-09): an R1–R12 finding has one of three tiers, stated in the owner process constraints
  of `AGENTS.md`.
  - Executed: a concrete trigger path exists on this project's data and stages (a named path, or a count above
    zero on the run-of-record data). It is MATERIAL and is fixed whatever its impact, zero included.
  - Latent: an actual count of zero on the run-of-record data, not an argument, shows that the violation needs
    inputs the project does not hold. It is ADVISORY but stays a defect. The backlog records the count and a
    revisit trigger (a new data vintage, reuse in a new stage, or a change to that code). Before that use, the
    code is fixed or made to refuse.
  - R11 and R12: a leak of private material or an execution path is fixed before push or publication, with no
    exception. A record or wording item that an invariant needs is fixed in the next records change, at the
    latest before publication, and never reopens a reviewed code candidate.

Consequences:

- Review seat cards quote the three tiers. The two round 2 findings of card m55-endgap are latent; their zero
  counts and revisit trigger (a new data vintage) are on the coordinator backlog.
- `tests/test_governance_constitution.py` pins the three tiers in `AGENTS.md`.

Follow-up:

- None.

---

## 2026-10-09 - Repository Rules Point at the Claude-herdr Coordination Standard

Context:

- The owner moved EFR coordination to the Claude-herdr Coordination Standard (card 0.10.0 in
  `Codex/Standards/claude-herdr-coordination-standard/`). The old `Codex/Standards/coordination-standard/` folder
  and its `routing_table.json` are no longer on the main branch of that repository. Version 0.13.0 stays on its
  `coordination-standard-0.13` branch and is not maintained.
- `AGENTS.md` and the controller still named the old folder, `routing_table.json`, and section numbers of the old
  card. The controller's seat rules of 2026-09-28 put every GPT seat in its own Herdr tab and did not let a Claude
  agent start one. Under the new card, the coordinator starts a GPT seat as a headless, read-only `codex exec`
  task.
- `AGENTS.md` capped review at two rounds per card. Under the card, two failed GENERAL_EXEC attempts go to
  EXPERT, and the repairs of EXPERT need more review rounds. The two rules did not agree after round 2.

Decision:

- `AGENTS.md` and the controller name the Claude-herdr card: `coordinator.md` and `model_bindings.json`.
- Sections 1 and 3 of the card say how seats and producers start, in a Herdr tab or headless. These owner rules
  stay: each seat runs as its bound model and writes its own report file, the coordinator reads that file
  directly, and no agent of another model wraps a seat or relays its report. The P1 process failure row now names
  a GPT seat whose report a Claude agent writes or relays.
- Section references move to the new card: the materiality test, the failure limit, and the residual-risk
  disposition are in section 5, and the seats of each lane are in section 2.
- Owner decision (2026-10-09): follow the card. The two-round cap per card is removed from `AGENTS.md` and the
  controller. Review rounds and escalation follow the failure limit in card section 5: two failed GENERAL_EXEC
  attempts, then EXPERT; after two failed EXPERT attempts, or when no new evidence or approach remains, the
  coordinator asks the owner. The other owner process constraints in `AGENTS.md` do not change.

Consequences:

- `tests/test_project_structure.py` pins the new pointers. It fails if the controller names `routing_table.json`,
  `AGENTS.md` names the old folder, or either file states the two-round cap.

Follow-up:

- None.

---

## 2026-10-09 - Trial Family v1 Amendment 4: R4 Settlement of an Index Exit on a Row Without a Close (Milestone 5.5, card m55-endgap)

Context:

- Run 3 (2026-10-08, code `b1b0517`, WRDS vintage 2025-12-31) ran the coverage, calibration, look, screen, and
  freeze stages again. The coordinator check found that they repeat run 2: the freeze digest is `62b2c8af...d59518`
  (shortlist S3 and S4), and only provenance hashes differ (the stage context, and the calibration stage file
  digest in each test B record).
- The run 3 confirm stage then refused before it wrote a file: `unresolved_disappearance`, "a held asset has no
  close at the last row" (2014-03-31), from the engine check H-5 (`_require_no_open_halt` in
  `src/backtest/portfolio.py`). No confirm or check stage file exists, and no confirm or check statistic was
  printed or read.
- Cause (coordinator, dates and counts only): one held position has no close from the row after its last close to
  the confirm end row, and its D6 event (cause unknown) falls after the confirm end row. `tilt_frames` keeps an
  event only when its last valued row and its effective row are inside the rows, so the confirm frames hold no
  event for it, and the engine holds it halt-locked to the end row. `path_break_positions` refuses the same case
  (`path_gap_at_period_end`).
- The first form of the rule (attempt a1 of this card) gave an event at the row W + 1 after a last close W only
  when no close came back from W + 1 to the segment end row. So the event depended on rows after W + 1, and R1
  failed inside the segment (review finding M55-EG-01). Before the replacement, the coordinator applied the first
  form to the real frames of the three segments with no engine run and counted its events from dates only: 2 in the
  confirm segment (1 held), 1 in the pre-seal check segment (not held), and 0 in the post-seal check segment. No
  return was read. The coordinator also saw, before the new rule was set, that the held
  position left the index on the row after its last close.

Decision:

- The owner chose option B on 2026-10-08: R4 settlement at the row after the last close. Option A would have
  extended the R6 path-break rule to the end row and blanked about 67 of the 254 confirm months in both loader runs.
- Amendment 4 changes one field and adds two. Attempt a2 edited the amendment in place, before any confirm or check
  result:
  - `status`: names amendment 4, its timing, and the changed fields.
  - `declaration_timing.amendment_4` (added): the timing facts above, the first form and why it was replaced, and
    the coordinator count of the first form. No pinned file, no code pin, and no coverage, signal, calibration,
    screen, shortlist, test, or trial-count rule changes. The confirm and check stages still give the run 2 digest
    of amendment 3 to `verify_frozen_screen`, and the next run reruns every stage from coverage into a new output
    folder.
  - `books.disappearance_r4.exit_gap` (added): in the confirm and check engine segments only, in the frames of
    each loader run, before the engine. A column gets an event at the first row W + 1 after the segment anchor and
    on or before the segment end row where all of these are true: a close on W and no close on W + 1; eligible on W
    and not eligible on W + 1 (the index spell ends on W + 1); and no D6 event of the column has `known_at` on or
    before W + 1. The event has `effective_date` = `known_at` = W + 1 (reference row W) and cause `unknown`. The
    primary run settles it by the engine default for a missing delisting return (-100 percent for a long
    position), the last_close run at the last close. A D6 event of the same column with `known_at` after W + 1
    leaves the event table of the segment. The column stays settled to the end row, also when its closes or an
    index spell come back. A gap without this index exit keeps the frozen rules (`halt_gap_return_v1`,
    `P1_path_break`, `path_gap_at_period_end`, and H-5). The screen path does not change.
- The trial file SHA-256 is `e9b2e25b...6f7081` (`m55_driver.TRIAL_SHA256`); with amendments 1 to 3 it was
  `f9122696...e4c8`.
- Driver defaults of card m55-endgap (attempt a2):
  - The rule reads rows W and W + 1 only, and "first row" reads only earlier rows. W can be the anchor row. A
    column that left the index on or before the anchor gets no event: every segment starts from cash, so no book
    holds it there.
  - Only the first such row of a column counts, because the engine settles a column once.
  - A D6 event with `known_at` on or before W + 1 keeps its row, cause, and value, and the column gets no added
    event. A later D6 event of a settled column leaves the table; the report counts it.
  - The added event has `delisting_return` NaN in the primary run and 0.0 in the last_close run, as D6 sets them.
    The engine then applies -1.0 (cause `unknown`) and 0.0. Each loader run finds its events on its own frames.
  - `path_break_positions` treats a position as settled when its event is effective on or before W + 1 (it was on
    or before W). Without this change, a column settled at W + 1 whose closes come back with a path break would
    blank months that no book holds. A D6 event is never effective on or before W + 1 when a valued break row
    follows W, so the change does not move a screen result; the run 2 driver comparison test still passes.
  - The held count uses the CW-PIT holdings of the composite set at the 1x cost case. CW-PIT is one book in every
    set and cost case (the public report checks this), and every book holds only names that CW-PIT holds. The
    report also gives the sum of these holdings.
  - The report is `exit_gap_events` under each loader run of each segment result, with no identifier and no date:
    the events and the held events by later exit class, the held CW-PIT weight sum, `priced_again`,
    `held_priced_again`, `eligible_again`, and `d6_left_out`.

Rationale:

- R4 states the rule for a held position whose price path ends: an unknown cause settles at -100 percent for a long
  position, with the last-close rerun. B blanks no month for this position. A would blank about 67 of the 254
  confirm months for it.
- R1: each fact that the event uses is known at the close of W + 1 under the frozen loader rules. The close on W and
  the missing close on W + 1 are D3 facts. The index exit is a D4 fact (`end_known_at` = `mbrenddt` = W + 1). The D6
  events with `known_at` on or before W + 1 are D6 facts (`known_at` = `effective_date`). The engine uses an event
  only on rows on or after its `effective_date`. A later D6 event leaves the table only after W + 1, when the column
  has settled already. So no row after W + 1 changes an event, a trade, a holding, or a return on or before W + 1.
- Cost of R1: whether the closes come back is known only after W + 1. So a held position whose closes come back
  later also settles at -100 percent in the primary run. The last_close run is the R4 sensitivity for this case,
  and `held_priced_again` counts it. A settled column that joins the index again stays out of both books to the
  end row; the engine allows one terminal event per column. `eligible_again` counts this.

Consequences:

- Each confirm and check stage result gains `exit_gap_events` per segment and loader run. The R4 counts
  (`r4.by_cause.unknown`) and the last_close rerun include the added events.
- The screen path does not use the rule. An index exit without a close in the screen keeps
  `halt_gap_return_v1` or the path-break months, so confirm and check numbers for such a position are not
  like-for-like with the screen numbers. No decision compares them directly.
- `blanked_windows` (an R6 report count) reads eligibility, not settlement. A settled column that joins the index
  again and has a later path break can add blanked cells that are not pool cells. `eligible_again` shows when this
  can happen.
- The run 3 confirm refusal stays visible (R9): it is in the run 3 log and goes into the attempts file of the
  public report.
- R9: each coordinator QA of this card counts the added events on real data as aggregates (dates and counts only),
  with no engine run and no return read. The a1 QA counts are above.
- Coordinator QA of the merged rule on real data before run 4, from dates and counts only (no engine run, no return
  read): the confirm segment has 1 added event in each loader run, cause unknown, held by the QA approximation. The
  check stage has 0 in each loader run. Priced again, eligible again, and D6 left out are 0. The held event is on
  the same row in both loader runs.
- `research/m55_confirm_report.py` still names run 3 (the trial with amendments 1 to 3 and the code of `b1b0517`)
  and does not publish `exit_gap_events` yet.

Follow-up:

- Coordinator QA of attempt a2: count the events of this rule on real data per segment and loader run (events,
  held, `held_priced_again`, `eligible_again`, `d6_left_out`), as dates and counts only, and confirm that the held
  confirm position gets its event on the same row in both loader runs. Add the counts to this entry.
- Run 4 from coverage on the merged main, a check that coverage to the freeze repeat run 2 (provenance hashes
  excepted), then the confirm and check stages.
- The coordinator updates the run pin of the public report and adds the `exit_gap_events` aggregates in a later
  card.

---

## 2026-10-08 - Public Report Rules of the M5.5 Confirm and Check Stages (card m55-conrep)

Context:

- Run 3 of trial family v1 (code `b1b0517`, amendments 1 to 3) runs the seven stages of `research/m55_driver.py` on
  the real data. Its confirm and check stage files hold per-position rows, per-cell trade weights, and CRSP quote
  values.
- `research/m55_confirm_report.py` makes the public report from the run 3 folder: `reports/m55_confirm_v1.md`,
  `reports/m55_confirm_v1.json`, and `reports/m55_confirm_v1_attempts.jsonl`. It reuses the checks and aggregates
  of `research/m55_screen_report.py`. No real stage file was read for this card, and no real report file exists yet.

Decision:

- Checks before any output. Each check refuses with a typed reason and writes nothing: the screen report checks
  (`check_run`, `check_freeze`), `trial_mismatch`, `data_manifest_mismatch` (the data digest of both tracked
  manifests), `code_pins_mismatch`, `code_mismatch`, `test_b_mismatch`, `test_b_open`, `run2_digest_mismatch` (the
  freeze digest, and the digest and shortlist of the confirm and check files, equal the run 2 digest of amendment
  3), `run_log_missing`, `run_log_mismatch` (the run log names each stage file once, with its digest),
  `attempts_reference_invalid`, `cw_pit_not_one_book`, and the output guard reasons.
- Default 1: code pin. The report pins run 3 to commit `b1b0517` and its code digest `59b0ba9d...707ca`
  (`m55_driver.code_digest` of `research/` and `src/` at that commit). A test computes the digest from a
  `git archive` of `b1b0517`.
- Default 2: attempts file (R9). One line per run log entry of run 3: the stage, the outcome, and the stage digest
  or the refusal reason. The detail text stays in the private run log, because it can name a date of one position
  or a private path; the provenance gives the run log SHA-256. Two reference lines come first: run 1 and run 2,
  each with the path and SHA-256 of `reports/m55_screen_v1_attempts.jsonl`.
- Default 3: CW-PIT once. The CW-PIT book is the same in every signal set, so the report gives it once per segment,
  from the composite run. It refuses when a set has another CW-PIT R4 or half-spread record.
- Default 4: the public weight rule (screen report entry, Ruling 4). R4 weight sums are given only for the CW-PIT
  group of each segment and loader run, at the `look_r4` level of the screen report (by cause, total, or none).
  Each signal set's TILT group nests in the CW-PIT group, so it gets counts only. A path-break CW weight sum is
  given only when each loader run has at least 3 positions and the two runs hold the same positions or differ by
  at least 3. A position is known by its break row, previous valid row, and later exit class. A signal set gets
  no path-break weight sum. No single maximum weight is given.
- Default 5: half-spreads. Each book and year gives the share of the traded notional by quote status, the
  CRSP-binds and BA shares, the spread cost above the schedule, and the invalid traded cells by reason and later
  exit class (nonzero counts only). No figure gives the traded notional. The largest half-spread of a traded cell
  is a band in bp (edges 5, 10, 20, 50, 100, 200), because an exact value with its book and year can single out
  one security and day in the CRSP quotes. CW-PIT and the composite TILT get all four cells. S1 to S8 and the
  Family A TILT get the decision cell only, to keep the file small (about 1.2 MB on the long synthetic chain).
- Default 6: `tilt_stats` gives per-year turnover and cost drag for the active book only (the trial's "active
  turnover and cost drag per year"), because with the per-year turnover of one book a notional share gives a weight
  sum. The full-segment figures of each book stay.
- Default 7: the "private list" of the card is the forbidden keys of the screen report, the identifier keys
  (`permno`, `permanent_id`, `gvkey`, `ticker`, `cusip`, `comnam`), and the private path patterns of the screen
  report (`PRIVATE_TEXT`).
- Default 8: claim guard. No output text contains "confirmation", "confirmed", "confirms", "profitab", "profit",
  "outperform", or "beat(s)", except in the run label of the trial file, quoted word for word, and in the phrase
  "no profitability claim".
- Default 9: the report has no run date, so its bytes depend only on the stage files and the tracked files.
- The `missing` key lists each withheld value with its reason.

Consequences:

- `research/m55_screen_report.py` changes by one move: the `keys` function inside `check_output` is now a module
  function that the confirm report shares. A test shows that the screen report output bytes equal those of the
  module at `b1b0517`.
- The confirm report gives no single-security row, identifier, private path, or single maximum weight. Each
  published weight is a sum over at least 3 positions.

Follow-up:

- After the check stage of run 3, the coordinator runs `python -m research.m55_confirm_report <run 3 folder>`,
  reads the three files, and commits them. A refusal goes to the engineering log.

---

## 2026-10-08 - Trial Family v1 Amendment 3: Confirm and Check Stages With the Half-Spread Override (Milestone 5.5, card m55-confirm)

Context:

- Run 2 (2026-10-08, code `8590b2e`, WRDS vintage 2025-12-31) ran the coverage, calibration, look, screen, and
  freeze stages on rows up to 1992-12-31 only. The freeze decision was `shortlist_frozen` with S3 and S4, digest
  `62b2c8af...d59518`. No confirm month, check month, or quote value has been read.
- The rules and code pins of amendment 3 were committed before the second pull: `56f556a` and `e186c63` at
  06:28:50 PDT and `528ac75` at 06:30:07 PDT. The owner ran the pull once, on 2026-10-08 (first quote file 07:47:54
  PDT, `VINTAGE.json` 07:50:17 PDT, vintage 2025-12-31). Later commits changed amendment 3 wording only (`452a076`
  at 07:54:21 PDT, and the commit of the tracked quote manifest). Before run 3, only the quote file bytes (for the
  SHA-256) and the Parquet row-count metadata were read; no quote value has been parsed.
- The frozen file declares the half-spread override (`books.costs.half_spread_override`), but it does not state the
  quote rule, the pull, or the run segments. The design note of card m55-confirm sets them. The engine and the
  runner change, so amendment 3 pins their new bytes before run 3 (`code_pins.statement`).

Decision:

- Amendment 3 changes three fields and adds seven:
  - `status`: names amendment 3, its timing, and the changed fields.
  - `declaration_timing.amendment_3` (added): it came after the run 2 freeze and before any confirm month, check
    month, or quote value is read. Run 3 reruns every stage from coverage into a new folder and must repeat the
    run 2 digest; a different digest, coverage count, or calibration value is a stop for the owner. No return of a
    book, SPY, or index after 1992-12-31 exists on WRDS data in the runs of this trial file (the prior exposures
    stay listed). No coverage, signal, calibration, screen, shortlist, test, or trial-count rule changes.
  - `code_pins["research/m55_index_tilt.py"]`: the new commit and SHA-256; the scope adds the quote rule
    (`half_spreads`) and the spread rate per stock (`spread_rates`).
  - `code_pins["src/backtest/portfolio.py"]` (added): the runner, with the slippage rate per asset and row
    (`asset_slippage_bps`).
  - `code_pins["coord/reports/m6_prep/wrds_pull_quotes.py"]` (added): the second pull script, SHA-256
    `1287c6a1...a419b`, commit null (the script is not tracked).
  - `data.tables_used.quotes` (added): the quote main files (`crsp_dsf_v2_quotes/<year>.parquet`, `late`,
    `nulldate`) and their columns.
  - `books.costs.half_spread_override`: a trade at row r pays scale x max(schedule spread at r, CRSP half-spread at
    r - 1); the half-spread is 10,000 x (ask - bid) / (ask + bid); an invalid cell takes the first of
    `no_quote_row`, `quote_missing`, `quote_one_sided`, `quote_nonpositive`, `quote_crossed` and pays the schedule.
    The one-pull rule: one run of the pinned script into a folder named `wrds_quotes_*`, a re-pull is a stop for the
    owner, and `reports/wrds_quotes_manifest_2025.json` is committed before run 3. It also lists the driver
    refusals and puts the quote file hashes in `data_files_sha256`.
  - `periods.confirm.segments` (added): one segment from cash, anchor 1992-12-31, first rebalance 1993-01-29, end
    row 2014-03-31, every input cut at the end row, so no value after it reaches a confirm result. The key checks
    of the quote rows (seal window, repeat, and match with the first pull) cover the whole quote copy, rows after
    2014-03-31 too, so a bad key in a check-period row stops the confirm stage.
  - `periods.check.segments` (added): pre-seal anchor 2014-02-28, first rebalance 2014-03-31, end row 2019-06-28,
    months 2014-04 to 2019-06; post-seal anchor 2021-07-30, first rebalance 2021-08-31, end row the last row of
    `check_period_end`, months 2021-09 to `check_period_end`.
  - `reports_owed.half_spread` (added): by stage, signal set, loader run, cost case, book, and year.
- The amendment pins no quote manifest. Every stage checks the quote copy from its manifest, file hashes, and
  Parquet row counts only, and compares it with the tracked quote manifest. No stage parses a quote value before
  that check and the earlier stage files pass, and the confirm and check stages parse the values only after the
  frozen digest gate. The trial file SHA-256 after amendment 3 is `f9122696...48e4c8`.
- Tracked quote manifest `reports/wrds_quotes_manifest_2025.json` (`QUOTE_MANIFEST`), SHA-256
  `cedf4cb3...8288`: vintage 2025-12-31, 36 main parts (33 files for 1993 to 2025; 2026, `late`, and `nulldate`
  with 0 rows and no file), 6,556,591 main rows. The coordinator built it from the main files, with the fields of
  `m55_wrds_loader.write_manifest` without `units`: `vintage`, `script_code_sha256`, `files` (rows, `sha256`,
  `query_sha256`), and `sealed` (`sealed_digest`: 39 files, bytes hashed, nothing parsed). The coordinator verified
  it. Change of order: the pull finished before this code merged, so the manifest is in this PR, not in a separate
  one.
- Driver defaults (producer, card m55-confirm). The note does not settle these points; each serves run 3 only:
  - The check stage reports the check means (`composite_means`) of each secondary member, with no p-value or
    q-value. Reason: the secondary family is a confirm-period family.
  - The check stage reports `tilt_stats`, `r4`, `half_spread`, `counts`, and the path_break positions per segment,
    and joins only the monthly series and the declarations. Reason: each segment starts from cash, so a turnover or
    TE across the gap has no meaning.
  - Family A: a factor value at row t is blank when its own window of `warmup_rows` rows that ends at t holds a
    `path_break` row (all six factors). Reason: P1_path_break blanks each level window across a break.
  - The confirm and check stages refuse with `test_b_open` after the calibration decision `chosen` and with
    `screen_empty_confirm` after an empty screen. Reason: run 2 gave `ratio_coverage_low` and a frozen shortlist;
    any other path needs a rule that this trial file does not state, so it is a stop for the owner.
  - The cost above the schedule in `half_spread` is the book's slippage cost minus turnover x schedule spread x
    scale x (1 + daily gross) at each rebalance row.
  - A quote row with no PERMNO or no date refuses (`quote_key_missing`). Reason: a missing key cannot be joined,
    and a drop would be silent (R6).
  - The composite's post-publication split is reported once for each publication year of its signals (S3 1996,
    S4 2013); the Family A baseline has none.
  - `me_coverage` and `bid_ask_midpoint_share` of a stage count the member-days after each segment anchor up to its
    end row.
  - The confirm stage records `composite_test` for both cost cases; the decision reads the 1x test and the 2x means
    only.
- No change loosens R1, R2, R4, R6, R8, or R9. Screen months keep `SCREEN_COST_SCHEDULE` with no rate panel.

Consequences:

- `research/m55_driver.py` runs seven stages; every stage needs the quote copy (`--quote-root`) and the tracked quote
  manifest, because their digest is part of each stage context. Without a rate panel, the runner and the engine give
  the bytes of main `8590b2e`, and on the synthetic long world the driver of `8590b2e` gives the same results from
  coverage to freeze as this driver.
- Run 3 order: coverage to freeze, the coordinator check of the freeze digest, coverage counts, and calibration
  values against run 2, then confirm and check. The second pull and its tracked manifest are done (this PR).

Follow-up:

- Run 3 after this PR merges. The second WRDS pull of CRSP closing bid and ask (OI-03) is done, and its manifest is
  in this PR.

## 2026-10-08 - Milestone 5.5 Screen of Trial Family v1: Shortlist S3 and S4

Context:

- Run 2 of trial family v1 (code `8590b2e`, amendment 2, WRDS vintage 2025-12-31) ran the five stages of
  `research/m55_driver.py` on 2026-10-08 with no refusal. Its calibration result equals run 1 on every field
  (`ratio_coverage_low`), so test B is stopped (label `stopped_coverage`, p_B = 1.0). The coordinator verified the
  stage files: hashes, stage chain, one context, trial and code digests, the recomputed shortlist digest, the test
  B record, and the run log.
- `research/m55_screen_report.py` makes the public report from the stage files of run 1 and run 2:
  `reports/m55_screen_v1.md`, `reports/m55_screen_v1.json`, and `reports/m55_screen_v1_attempts.jsonl` (one line
  per run).

Decision:

- Screen result. The freeze reads only the primary loader run with the primary cost case, with the rule IR >= 0.2
  and HAC t >= 1.0 against CW-PIT. S3 (IR 1.104, HAC t 1.850, 36 months) and S4 (IR 0.686, HAC t 1.539, 72 months)
  meet the rule. S1, S2, S6, S7, and S8 fail it. S5 has no real start, so it has the typed undefined record
  `screen_too_short`. The freeze decision is `shortlist_frozen`, the shortlist is S3 and S4, and the digest is
  `62b2c8afb379fb0322b03cbd68da47b71c68c9eb1d1172c805dcd11b00d59518`. These are `DIAGNOSTIC_ONLY` screen numbers.
  They are not a profitability claim.
- Ruling 1 (coordinator, 2026-10-08). The `path_break_held` blank set removes 215 of 354 screen months (13 held
  positions, CW-PIT weight sum 0.0034, longest span 162 months). The pull takes every `dsf_v2` row of every PERMNO
  that was ever a member, and the loader drops only off-calendar rows, so each gap is a gap in CRSP. The halt
  policy locks a held position with no close, and R6 forbids a fill, so the blank is the frozen rule applied
  correctly. Both books lose the same months, so the cut cannot favor a candidate. It lowers the power of S1 (168
  to 90 months) and S7 (348 to 133 months), and both fail. No fix and no rerun follow (R9 forking path). Backlog: a
  later trial version may treat a long coverage gap as a disappearance under R4.
- Ruling 2 (coordinator, 2026-10-08). The public report gives the path-break positions, the blanked level windows,
  and the B2 rows as aggregates only. The trial (`reports_owed.path_break`) asks for each position with its weight,
  but the owner data terms (O-22: no single-security row from stage files) take precedence. The per-position rows
  stay in the private stage files, and the report commits their SHA-256 values.
- Ruling 3 (coordinator default, 2026-10-08). The screen report has no q-values. The candidate table is in ID
  order and is not a ranking, and each decision follows the frozen thresholds. The trial puts Benjamini-Yekutieli
  q-values (family size 9) at the confirm stage (`secondary_family`). The report card found no conflict with R10:
  R10 asks for q-values beside a ranking, and R9 fixes the correction method before results, so a q-value on the
  screen p-values would use a method that the trial does not name.
- Ruling 4 (coordinator, 2026-10-08, on REVIEW M-1, R11 under O-22). Two nested public weight sums, the look
  CW-PIT group and the S7 CW-PIT group for the failure cause, differed by one event, so a subtraction gave one held
  event's weight, and the settlement counts gave its class. Public weight rule from now on: a weight is published
  only as a sum over at least 3 positions, and no two published sums may differ by fewer than 3 positions. The
  report gives R4 and path-break weight sums for the run-level look groups only. For each candidate group it gives
  counts by cause and by settlement and no weight, and it gives no single maximum weight (`incoming_weight_max`,
  B2 `max_cw_share`). The stage files hold no event identity, so they cannot show that the two loader runs hold
  the same events of a cause with equal counts (cash_merger 90 and 90, failure 17 and 17). So the look R4 weights
  are totals over causes, which differ by 5 events (316 and 321). The `missing` key of the report lists each
  withheld value, and the values stay in the private stage files.

Consequences:

- S3 meets the rule at the primary cost in both loader runs but not at 2x cost: IR 0.261 and HAC t 0.459 in the
  primary run, 0.263 and 0.462 in the last_close run. S2 and S3 have 36 screen months, the minimum. S4 meets the
  rule in all four cells (IR 0.669 to 0.686, HAC t 1.499 to 1.539). The other cells decide nothing.
- R4: no candidate and no look comparison changes sign between the primary run and the last_close rerun.
- S1 loses its 78 blank months to positions that its own books do not hold, because each declaration is the run
  blank set cut to the candidate's span (the frozen rule).
- The confirm stage runs test A on the composite of S3 and S4. With p_B = 1.0, test A needs p_A <= 0.025 for its
  Holm condition. The confirm stage also owes `check_period_end`, `check_gap_months`, and the post-seal parts of
  `s2_history_rule`.

Follow-up:

- The confirm run waits for the owner's second WRDS pull of CRSP closing bid and ask (OI-03). The confirm card
  applies p_B = 1.0 with the pinned criteria functions; a change to a pinned file needs an amendment first.

## 2026-10-08 - Trial Family v1 Amendment 2: Test B Stopped at the Coverage Stop (Milestone 5.5, owner decision)

Context:

- Run 1 (2026-10-07, code `ebc9705`, WRDS vintage 2025-12-31) ran the coverage and calibration stages of
  `research/m55_driver.py` on real data. The calibration decision was `ratio_coverage_low`. Of 354 screen
  rebalances, 131 were `defined_full`, 159 `defined_partial`, and 64 `ratio_window_short`, so the undefined share
  was 0.1808, above `LOWRISK_UNDEFINED_MAX` = 0.10. The driver gate `GO_ON = ("chosen",)` then refused the look. No
  return of any kind was computed. The trial file states the run 1 aggregates in
  `primary_family.test_B.after_coverage_stop`.
- The frozen file calls `ratio_coverage_low` "the coverage stop" (`books.low_risk.calibration.window_diagnostic`),
  but it does not say what the stop stops. The screen never uses g. The driver calls the engine with no g, and the
  engine adds the low-risk book only when g is given. `books.low_risk.role` says that no screen or confirm month
  selects the low-risk book.

Decision:

- Owner decision, 2026-10-08, option A. Test B of trial family v1 stops at the coverage stop, and the stop stays
  visible (R9). The look, the screen, and the shortlist freeze go on without the low-risk book. Any later low-risk
  rule is a separate amendment made before any low-risk return is seen. Reason: the coverage stop is about the risk
  ratio of the low-risk book, and the look, the screen, and the freeze read no g and no low-risk output.
- Amendment 2 states this in the fields that own each rule. Five fields changed and two were added:
  - `status`: names amendment 2, its timing, and the changed fields.
  - `declaration_timing.order_after_freeze`: the look, the screen, and the freeze run after the calibration
    decision `chosen` or `ratio_coverage_low`. `ratio_coverage_low` stops test B only. `refused`,
    `ratio_coverage_ambiguous`, and `no_g_reaches_target` keep their meaning in `calibration.choice` (a stop or an
    owner decision) and stop the sequence before the look.
  - `declaration_timing.amendment_2` (added): amendment 2 came after the run 1 coverage output (validity counts and
    real starts, no return) and the run 1 calibration output (ex-ante second moments only), and before any return
    of any kind. The look has not run. No coverage, signal, calibration, screen, or shortlist rule changes.
  - `books.low_risk.role`: the low-risk book gets no g, no engine call, and no return in any period, the
    last_close rerun included.
  - `screen_and_shortlist.empty_shortlist`: test B is stopped in every case. The old text said that test B may
    still run after `screen_empty`.
  - `primary_family.test_B.after_coverage_stop` (added): the run 1 facts and the SHA-256 of the run 1 calibration
    stage file (`0be87e72...a2837b`); the label `stopped_coverage`, p_B = 1.0, and a Holm family that keeps size 2,
    as test A keeps it with p_A = 1.0 after `screen_empty`; the low-risk version and its 12 grid values stay
    counted; the calibration result stays reported (`logged_per_g`, `low_risk_r6`).
  - `stop_rule.forking_paths`: a later low-risk rule is a separate amendment made before any low-risk return is
    seen, and it is a new counted trial.
- `code_pins`, `trial_count`, and every rule in `books.low_risk.calibration` stay as frozen. The trial file SHA-256
  after amendment 2 is `4f9cf222...f88a03`.
- With p_B = 1.0, test A needs a Holm-adjusted 2 x p_A <= 0.05, so p_A <= 0.025. A family of size 1 would need only
  p_A <= 0.05, so size 2 is the stricter choice. No change loosens R1, R2, R4, R6, R8, or R9.

Consequences:

- The driver binds the amended file (`TRIAL_SHA256`) and runs the look, the screen, and the freeze after `chosen`
  or `ratio_coverage_low`. After `ratio_coverage_low`, the look, screen, and freeze stage files record test B as
  stopped: the label, p_B, the calibration decision, and the calibration stage file digest. This replaces the
  calibration gate default of the 2026-10-07 entry for `ratio_coverage_low` only. `refused`,
  `ratio_coverage_ambiguous`, and `no_g_reaches_target` still stop the sequence with `calibration_stop`.
- The stage context holds the trial file and code digests, so the run 1 stage files do not chain to the amended
  driver. Run 2 starts from the coverage stage in a new output folder, and the run 1 files stay as they are (R9).
- A later confirm card applies p_B = 1.0 with the pinned criteria functions (`holm_primary(p_A, 1.0)` and
  `decide_a`). `m55_criteria.primary_decision` always computes test B from a low-risk series, so that card cannot
  call it as it is. If that card needs a change to a pinned file, an amendment that pins the new bytes comes first.

Follow-up:

- Next: run 2 from the coverage stage. Before the look, the coordinator compares the run 2 calibration result with
  run 1 (decision, ratio status counts, and grid brackets). A difference is a stop for the owner.

## 2026-10-07 - Driver Defaults From Coverage to the Shortlist Freeze (Milestone 5.5, coordinator defaults)

Context:

- `research/m55_driver.py` runs the frozen trial family v1 (PR #298) from the coverage counts to the shortlist
  freeze. The round 1 review (AUDIT Codex: MATERIAL 2; AUDIT_2 Opus: MATERIAL 0) and the producer's open questions
  found cases that the frozen file does not settle. The coordinator ruled on them in the repair card, after the
  producer's R-2 stop, and at PR time; round 2 passed with MATERIAL 0 from both seats. No real data was read.

Decision:

- Calibration gate (coordinator ruling at PR time, before any real data run). The look, the screen, and the freeze go
  on only after the calibration decision `chosen`. Every other decision stops the sequence before the look
  (`calibration_stop`, with the decision named), and the coordinator takes it to the owner. In
  `books.low_risk.calibration.choice`, a refusal below the first g that meets "stops"; `ratio_coverage_ambiguous`
  means "the owner decides"; `no_g_reaches_target` means "stop and ask the owner". `window_diagnostic` calls
  `ratio_coverage_low` "the coverage stop". On `refused`, the calibration stage itself raises and writes no file, so
  the later stages refuse with `stage_missing`. Reason: the frozen calibration rules (`choice` and
  `window_diagnostic`) name each outcome other than `chosen` a stop or an owner decision, the frozen order puts the
  calibration before the screen, and a halt never loosens R9. The owner then decides the low-risk book before any
  return is seen. This replaces the earlier default that let `ratio_coverage_low` go on; that default rested on the
  false statement that the frozen file gives no stop for it.
- Reading of "opened" (R9). `stop_rule.after_screen` says "confirm months are not opened for a tilt", and
  `screen_and_shortlist.freeze` says "the digest is saved before any confirm month is opened". The accepted loader
  builds full-history paths at load. This is its reviewed design, and it ran on this data vintage at intake. No row,
  event, or spell start dated after 1992-12-31 reaches the engine, the criteria, or the signal builder, and each
  call refuses one. The one exception is the first 1993 row of the engine frames: it keeps its date with every value
  blank, because the engine input check needs a row after the window end, and the engine check allows only that one
  blank row. An end date after 1992-12-31 on a spell or link that starts on or before that date stays, and reads as
  open on every row up to 1992-12-31. The driver cuts the signal tables at load, and it drops from the engine frames
  the events that settle after 1992-12-31, the spells that start after it, and the columns left with no spell. The
  freeze stage parses no data table. The later exit class (the frozen R6 split) is an event class, not a return.
  Reason: a row that reaches no call cannot open a confirm month for a tilt.
- Labels after the cut. The `not_yet_known` and `no_record` reasons in the screen-period stage files reflect what is
  known by 1992-12-31. On real data the cut can also change the calibration panel digest and column count and the
  S2 basis-quarter counts (round 2 AUDIT_2 ADV-1). Reason: each change removes information not known by
  1992-12-31, and no signal value, weight, screen month, record, or decision changes.
- Two refusals with no frozen rule stop the run. `path_break_adjacent`: the row before a break row has a close, so
  the engine return at the break row is a stitched value that the driver cannot blank. `path_gap_at_period_end`: a
  held position has no close on 1992-12-31 and has not settled. If one fires on real data, the owner decides.
  Reason: the frozen file has no rule for either case, and R6 permits no silent fill or drop.
- Size exposure (`reports_owed.tilt_stats`): the mean over rebalances of sum((w - b) x ln ME). Here w and b are the
  TILT and CW-PIT target weights set at rebalance r (not the drifted holdings), and ME is from the decision row
  r - 1, over the members with a CW-PIT target. Report only. Reason: the frozen file names the field but does not
  define it, and no decision reads it.
- S2 report readings, report only. `s2_short_history`: by year, the share of S2 member cells typed `short_history`,
  and the mean ME percentile (among members with ME at r - 1) of the `short_history` members and of the valid
  members. The two mean percentiles show the size mix of each group; they do not measure a change in S2 ranks.
  `s2_history_rule`: member quarters by the year of the known date, comparing the as-of `cfacshr` reads at `rdq` and
  at the known date; `unread` when either read fails. Reason: the frozen file names these reports but not their
  form, and no decision reads them.
- Short candidates. A candidate with fewer than 36 months with values in the primary run gets no engine call. Each
  run and cost case gets a typed undefined record, and its fragility is `not_evaluated`. A run with 36 months or more
  of a candidate whose primary run is short has the reason `primary_screen_too_short`. If only the last_close run is
  short, its records are typed undefined with `screen_too_short`, and the fragility is `not_evaluated`; the screen
  file states this also for a shortlisted candidate. Reason: the 36-month screen minimum leaves the record
  undefined, an engine call would compute returns that no decision uses, and the typed records keep the candidate
  visible (R9).
- Reruns. After a refusal partway through a stage, a rerun must give the same logged outputs for the earlier
  comparisons, byte for byte. Any difference is a stop. Reason: `run_log.jsonl` is append-only, so the earlier lines
  stay, and a rerun with other values would be a second, different trial of the same comparison.

Consequences:

- Backlog, each report only or before publication: the `m55_signals` label `not_yet_known` uses records known after
  t (no signal value, weight, or decision changes); an error record can hold the output path in the private run log
  (round 1 AUDIT-A3); the single-security rows in the stage files get a data-terms check before any publication
  (round 1 AUDIT_2 ADV-3); the R6 blanked-window numerator can count a settled name that is still eligible at r - 1
  (round 2 AUDIT_2 ADV-2, rare).

## 2026-10-06 - Milestone 5.5 Trial Family v1 Frozen

Context:

- R9 needs the trial family committed before any result. No real return, signal value or coverage, or low-risk
  calibration output exists on WRDS data (coordinator record). The draft passed two CRITICAL review rounds and the
  m55-checkgap review seats (OI-04).

Decision:

- `docs/preregistrations/m55_trial_family_v1.json` is frozen on 2026-10-06 by the coordinator. Its rules are those
  of the reviewed draft. Only `status`, `declared_on`, `code_pins`, and the loader commit in `declaration_timing`
  changed at commit.
- `code_pins` pins each module by its accepted commit and file SHA-256, and the untracked WRDS pull script by its
  SHA-256. If a pinned file changes before a run, an amendment that pins the new bytes comes first.
- Coordinator defaults for the open items, logged:
  - OI-01 evidence ceiling: `DIAGNOSTIC_ONLY`, with the O-17 Q3 run label in every report header.
  - OI-02 benchmark before 1993-02: `vwretd` as is, labelled gross of fund fees.
  - OI-03 half-spread override: the screen uses the dated screen cost schedule; the confirm run waits for the
    owner's second WRDS pull of CRSP closing bid and ask, and the override applies from the confirm period.
  - OI-04 post-seal check: a fixed gap `CHECK_GAP_MONTHS` 2019-07 to 2021-08 (26 months); check months restart at
    2021-09; the gap months are reported.
  - OI-05 real start: the code rule on a screen-only panel 1963-07 to 1992-12; fewer than 36 screen months gives a
    typed undefined record that fails the shortlist, stays hashed, and counts as a trial.
  - OI-06 Family A baseline: at least 4 of 6 valid signals (the M5 rule).
  - OI-07 secondary family: all eight candidates plus the Family A baseline, size 9; the baseline runs over the
    screen, confirm, and check periods, all visible.
  - OI-08 post-publication split: months whose calendar year is after the publication year (the M5 convention).
  - OI-09 look before any tilt return: CW-PIT against `vwretd` over the screen months only; CW-PIT against SPY is
    reported with the confirm run.
  - OI-10 low-risk calibration: ex-ante inputs only.
  - OI-11 bid/ask-midpoint days (`dlyprcflg = 'BA'`): valid; their share of member-days is reported.
  - OI-12 Family A on CRSP: the Gao and Ritter (2010) Nasdaq volume divisors; INDNO 1000200 as the market series in
    every month.
  - OI-13 share count for ME: loader rule D5.
  - OI-14 held member with no close on the window end row: the run refuses and the refusal is recorded; an
    amendment before any result of that run picks the fix.
  - OI-15 `real_v2` tilt diagnostic and unpriced report: left out; a later file declares them if Q5 is answered.
- None of these loosens R1, R2, R4, R6, R8, or R9.
- Amendment 1 (2026-10-06, before any real return, signal coverage, or calibration output) states the R1-R12 sweep
  repairs V1 to V6 in the fields that own them; no other rule changed, and none loosens R1, R2, R4, R6, R8, or R9:
  - V1 (R4): the last-close rerun is a second engine call on `tilt_frames(run="last_close")`; the engine flags
    `fragile_active_sign` and `fragile_lowrisk_active_sign` are never reported (`last_close_rerun`, `fragility`,
    `sensitivity_runs`).
  - V2 (R6): a traded member with a gap after its first-ever return leaves the low-risk ratio in both books and is
    counted; gap rebalances are reported (`calibration.ratio`, `window_diagnostic`, `limitations[6]`, `low_risk_r6`).
  - V3 (R1, R6): S2 also reads `cfacshr` at `rdq`; a different factor gives `split_in_basis_window`, a failed read
    its own reason, `rdq` in the seal included (`candidates.reasons`, S2 `history_rule`, `s2_history_rule`).
  - V4 (R6): the post-seal engine segment starts at the anchor 2021-07-30; signals are built once per seal segment;
    the words "first post-seal rebalance is 2020-08-31" are corrected (`check.left_out`, `limitations[9]`, OI-04).
  - V5 (R6): a share fact with no prior factor row and an unseen interval (`data_start`, `seal`) gives `unmapped` ME
    and share count; its reach and the 1963-1964 S7 coverage report are stated (`D5_market_equity`, `me_coverage`).
  - V6 (R6): each holding month that a position held across a `path_break` row touches is a declared blank month
    (`path_break_held`); one set per run and period, and each comparison declares the months inside its own span
    for every book and the benchmark (`P1_path_break`, `path_break`).
  - Records: `status` names the amendment; `declaration_timing` cites loader `312d284` (`known_at_drafting[1]`,
    `pre_freeze_requirements[0]`) and its intake rerun with the unseen-basis counts (`known_at_drafting[2]`).
  - Pins: engine `cebb487`, criteria `1a70eb7`, signals and loader `312d284`; the manifest bytes, Family A, and the
    pull script are unchanged.
- Round 1 corrections to amendment 1 (2026-10-06, from the AUDIT and AUDIT_2 seats; `status` names them; no pin or
  code change, and none loosens R1, R2, R4, R6, R8, or R9):
  - `limitations[1]` (R10): the CRSP counts are those of the intake at the pinned loader `312d284`: unmapped
    member-days are 18,519 of 423,341 for later failures and 18,776 of 2,967,375 for current members. Nearly all of
    the rise from `0c60805` (159,791 of 159,957) is the `data_start` case in 1961 to 1963, before the first screen
    rebalance; the other 166 are the `seal` case in 2020.
  - S2 `history_rule` (R1): the two factors are equal when `np.isclose(at_rdq, f, rtol=1e-9, atol=0.0)` holds, as
    the S2 code at `312d284` compares them.
  - `last_close_rerun` and `calibration.order` (R4, R9): the low-risk book is calibrated once, on
    `tilt_frames(run="primary")`; both engine calls use its chosen `g`, and the last_close call never recalibrates.
  - `limitations[0]` (R6): S7 is not affected by the late Compustat start, but it still loses coverage from the
    unseen share basis and the seal (pointers to `D5_market_equity` and `limitations[9]`).
  - `D5_market_equity` (R6): the `data_start` case can blank S7 in the return months 1962-03 to 1964-06 (was
    1963-01 to 1964-06); the 12-month anchor (the month end of R - 14) first reaches a calendar row in return month
    1962-03. No return run uses a month before 1963-07.

Follow-up:

- Next: coverage counts and real starts (before any return), then the low-risk calibration on risk data only, then
  the screen, in the order the file states.

## 2026-10-06 - Unknown Share Bases Are Typed Missing (Milestone 5.5, card m55-loader-r6)

Context:

- The R1 to R12 sweep confirmed two R6 defects before the trial freeze: a share count and ME on a share basis that
  the data cannot show (audit A-2, both forms), and an S2 quarter whose EPS and share factor can have different
  bases (review O2-A2). Each gave a value with no reason. Synthetic fixtures only; no real data was read.

Decision:

- Item 1 (D5, P-4, R6): when a PERMNO has no `dlycumfacshr` row before the share fact's `shrstartdt`, and an
  interval the data never saw lies between `shrstartdt` and the basis row, the share count and ME are `unmapped`.
  The new `market_equity` column `basis_unseen` names the case: `data_start` (`shrstartdt` before the first
  calendar row, 1961-01-03 in the 2025 vintage) or `seal` (`shrstartdt` before 2020-07-31 and the basis row on or
  after it). A PERMNO with a factor row before `shrstartdt` keeps the round 1 rule (item 1 of the loader entry).
  The new rule adds no CRSP convention, for example that CRSP adds a share row at each split. Not changed, as it is
  outside the card: a fact dated before the first row of a new listing, inside the calendar, keeps its value (the
  PERMNO has no row there, so this keeps the round 1 reading that the fact is on the first row's basis).
- Reach of item 1: a row at t is blank only while a fact dated before the unseen interval's end is in use. That
  stops when the PERMNO's first fact dated on or after 1961-01-03 (or on or after 2020-07-31) is in use, at its
  date plus 136 days, or when the old fact goes stale. There is no fixed end date.
  - Data start: blanks start on 1961-01-03 and end no earlier than 1961-05-19. ME at the rebalance rows from
    1963-06-28 is reached when that next fact is dated after 1963-02-12. The S7 share anchors from 1962-06-29 are
    reached when it is dated after 1962-02-13.
  - Seal: for each such PERMNO, every post-seal row from 2020-08-03 to at least 2020-12-11 is blank, because a fact
    dated 2020-07-31 or later is in use only from 2020-12-14. S7 reads the share count 12 months before its anchor,
    so a post-seal check month whose earlier anchor falls in that window loses S7 for these PERMNOs (members that
    list inside the seal). ME at the rebalance rows from the post-seal anchor 2021-07-30 is reached only when the
    next fact is dated after 2021-03-16.
  - So the rule can reach rows that the trial uses. The intake report gives the rows by case and year and the last
    date, for all rows and for member-days; the coordinator records the real counts.
- Item 2 (S2, R1, R6): first-reported EPS has the share basis of its own document, dated on some day from `rdq` to
  the known date. For each quarter that S2 reads (q, q - 4, and the prior quarters), S2 also reads `cfacshr` at
  `rdq` with the same as-of rule (at most one month old). When the two factors differ, the quarter gets the new
  reason `split_in_basis_window`: q or q - 4 gives that reason, and a prior quarter drops its two differences, as a
  missing prior quarter does. When the factor at `rdq` cannot be read, the quarter gets that read's own reason
  (`stale`, `no_market_data`, `missing_item`, or `invalid_value`), so each reason names what the data show. A split
  on `rdq` itself, before it, or after the known date keeps the value.
- Seal and item 2: every as-of factor read (`_Signals.factor`) now returns `no_market_data` when its row is before
  the seal start and the read date is on or after it. The one-month as-of age would otherwise carry the 2019-07-30
  factor to a date from 2019-07-31 to 2019-08-30 and hide a split in the seal. The seal dates move to
  `m55_signals.SEAL`, and the loader takes them from there. S1 reads `cfacpr` through the same function, but no
  calendar decision row can reach such a read: S1 reads statistics dates at most about five months before t.
- No rule here loosens R1, R2, R4, R6, R8, or R9.

Consequences:

- More `unmapped` ME and share-count rows from 1961 and after the seal; fewer valid S2 cells. The intake section
  "Share Basis Not Observed" and `reason_counts` give the sizes after the real rerun.
- Test fixtures whose share facts were dated before their first calendar row now start on it (they hit the
  data-start case); the S2 test with a split between a quarter's `rdq` and its EPS row now expects the new reason.

## 2026-10-06 - Gap Members Leave the Low-Risk Ratio (Milestone 5.5, card m55-ratio-gap)

Context:

- Sweep finding `review_gpt_r3:residual-complete-case`: `whole_book_ratio` measured the whole traded book on its
  complete-case rows. A missing return of a traded member after its first return removed that row for the whole
  book, so the ratio measured the member on the rows around its gap (R6 violation). The split into leading and gap
  rows used the first return inside the window, so a window that starts inside a gap was called leading.
- The loader intake counts 6 such rows inside S&P 500 member spells in 1963-1992; each touches about 12 monthly
  windows.

Decision (coordinator technical default, logged on the card):

- **Blank the member, not the rebalance.** A traded member with a missing return in the ratio window after its
  first-ever return is left out of the ratio at that rebalance, from both books, and counted (`ratio_gap_members`,
  `ratio_gap_cw_share`). It has no full window, so it is pinned at w = b and the weights do not change. The other
  members are measured at their book weights on their complete-case rows; only leading NaNs remove rows. Reason:
  blanking the whole rebalance could make about 70 of 354 calibration rebalances undefined and trip the 10 percent
  coverage stop for 6 data rows.
- **The first-ever return decides leading versus gap.** `rebalance_members` gives the flag (`short`).

Consequences:

- No value is filled, clipped, or repaired. Weights, TILT, the cap loop, and TE scaling do not change. Without a gap,
  every ratio field is bit-identical to `e50e8d6`.
- Known cost: at a gap rebalance, the ratio is that of the book without the gap member, so it moves toward the free
  sub-book ratio by an amount that grows with the member's cap weight and risk. On the synthetic GPT-R1-01 fixture
  (98 percent member) and GPT-R2-01 fixture (2 percent high-volatility member), a gap now gives `chosen` g = 0.5,
  where the old rule gave no choice. `ratio_gap_cw_share` records the share left out at each rebalance.
- Field meanings: `ratio_rows_leading` counts the rows removed (all of them leading); `ratio_rows_gap` counts the
  window rows that hold a gap, which stay unless a leading NaN also removes them; `ratio_limiting_*` count the
  measured members that remove rows. At a gap rebalance, `ex_ante_vol` and `cw_ex_ante_vol` cover the kept weights,
  which sum to 1 minus `ratio_gap_cw_share` in each book; the ratio does not depend on this scale.
- Follow-up for the coordinator: whether the real-data run needs a bound or a diagnostic on `ratio_gap_cw_share`.
  The R6 split by later exit class needs the gap members' IDs, which the record does not hold.

## 2026-10-06 - Declared Blank Months in the Criteria (Milestone 5.5, path_break, coordinator default)

Context:

- Sweep finding `tasks:driver-path_break-P-1`: CRSP has rows with a price and no return inside S&P 500 member spells
  (6 rows; 3 in the screen months). The loader types them `path_break`. A position held from the last valid row
  across the break gets only the return after the break; the return before it counts as 0. The fix types each
  holding-month return of every book that holds such a position as missing. `research/m55_criteria.py` refused any
  missing month, so a blank month needed a declared treatment before any result.

Decision:

- The criteria take `blank_months`: a mapping of each blank month to a reason in `BLANK_REASONS` (now only
  `path_break_held`). One declaration covers every series of a call (the books of a pair and SPY). A declared month
  has no row in any series. A declared month with a row (a value or a NaN) refuses with `blank_month_has_row`; a
  month left out with no declaration still refuses with `month_missing`.
- Every statistic uses the months with values, in time order: means, volatility and TE, the HAC t (n counts the
  months with values; the months on each side of a blank month become adjacent), the bootstrap (n and the 12-month
  minimum count the months with values; a block can span a blank month), the drawdowns (the path joins the months on
  each side), and the 36-month screen minimum. The period rules apply to the rows and the blank months together; a
  blank month cannot be in the check gap.
- Each record carries `blank_months` and `blank_reason_counts` when a month is declared, and the shortlist digest
  covers them. With no declared month, every output is the same as at `e8135bc`.
- Reason: R6 permits no fill. A month left out with a typed reason, listed in the hashed record, is not a silent
  drop. None of this loosens R1, R6, or R9: a declared month adds no value, and every period rule still applies.

Consequences:

- The screen driver finds the blank months at run time from the loader `path_break` panel and the engine holdings
  (no future data), leaves those months out of every book of the run, and reports the count, the months, the
  weights, and the later exit class. The trial rule `P1_path_break`, `reports_owed.path_break`, and P-1 in this log
  must state this before the freeze.

## 2026-10-06 - Check Gap Covers the Post-Seal Warm-Up (Milestone 5.5, coordinator default)

Context:

- `research/m55_criteria.py` let a check series skip only the seal months 2019-07 to 2020-07. Trial review GPT round
  2 found that the real check series cannot have those months only as its gap. The pull also seals the 2020-07-31
  row (its return starts inside the seal), so the first post-seal row is 2020-08-03 and the first post-seal
  month-end rebalance is 2020-08-31; no book has a 2020-08 return. The low-risk book refuses
  (`lowrisk_window_empty`) until a member has a full 252-row window. On the main INDNO 1000200 calendar the
  post-seal row count is 251 on 2021-07-30 and 273 on 2021-08-31 (coordinator count, aggregates only), so the first
  month end with a full window is 2021-08-31 and the first complete post-seal holding month of every book is 2021-09.

Decision:

- Coordinator default (trial open item OI-04, option 2 with a fixed gap): `CHECK_GAP_MONTHS =
  pd.period_range("2019-07", "2021-08", freq="M")` replaces `SEAL_MONTHS`. A check series has no month in the gap,
  and the gap is its only missing span. The refusal code `seal_month` is unchanged; its text names the check gap.
- Reason: every book can complete a check month only from 2021-09, so a fixed gap keeps the check months the same
  for all books and leaves no book near CW-PIT only because of the seal.
- None of this loosens R1, R6, or R9: the gap months are left out, not filled, and they are fixed before any
  check-period result.

Consequences:

- The trial file states the 26-month gap and the check start after the gap; the check months are 2014-04 to
  2019-06 and 2021-09 to the last complete month.

## 2026-10-05 - WRDS Loader Rules D1 to D9 (Milestone 5.5, coordinator defaults)

Context:

- `research/m55_wrds_loader.py` (card m55-loader) builds the engine frames, the signal inputs, and the benchmark
  returns from the main WRDS files, vintage 2025-12-31. It never opens a sealed file. The coordinator set D1 to D9;
  the producer readings P-1 to P-9 below fill the gaps the card did not cover. Each is logged before any result.

Decision:

- D1 Identity (R3): `permanent_id = str(permno)`, and the symbol is the same string. No return crosses PERMNOs.
- D2 Calendar: the trading days of INDNO 1000200 in the main file. Every member daily date must be one of them, or
  the loader refuses. A non-member row off the calendar is dropped and counted (1 row). No main row is in the seal.
- D3 Prices (R5, R6): one close index per PERMNO and seal segment from `dlyret` only (CIZ includes the delisting
  return on the `Y` row; `delret` is never added). A missing `dlyret` is NaN. A later return is the last valid value
  times (1 + `dlyret`). Each segment starts at its first priced row (index 1.0).
- D4 Membership (R2): `crsp_dsp500list_v2`, end date inclusive (500 members on 6,082 of 7,267 days in 1990-2018,
  confirmed). Engine `end_date` = `mbrenddt` + 1 day, `start_known_at = mbrstartdt`, `end_known_at = mbrenddt`.
- D5 Market equity (R1): |`dlyprc`| at t times the `shrout` with the latest `shrstartdt` on or before t - 136
  calendar days, moved to the t basis by the `dlycumfacshr` ratio. Reasons `no_share_fact`, `stale_share_fact`,
  `unmapped`. Units: `shrout` in thousands, so ME is in thousands of USD.
- D6 Disappearances (R4): a member PERMNO with a delisting record whose price path ends before the last calendar
  row. `effective_date` = the calendar row after the last valued row, or the `Y` row when it is later (item 3
  below); `known_at = effective_date`. Delisting return
  0.0 when the `Y` row is in the path; NaN when it is missing (engine default). Causes as the card lists them.
- D7 Split factors: at `dlyfacprc = 2` both cumulative factors halve (2,832 of 2,835 rows exactly; none rises),
  the median price ratio is 1.995, and the median share ratio is 2.0. The loader refuses otherwise.
- D8 Signal inputs: the sources of the card. `fund_quarterly` and `announcements` come from `comp_urq`; `comp_fundq`
  gives only `fyearq`. `known_date` = the later of `rdq` and the first of `prelimqprd`, `finalqprd`.
- D9 Seal: the loader refuses any sealed path; `tilt_frames` refuses a window across the seal.
- P-1 (D3, R6): 82 member rows (67 PERMNOs, 6 inside a member spell, all in the 1960s and 1970s) have a
  `dlyprevdt` that is a row with a price and no return (CIZ `RA` or `GP`). That return is not in the path and is
  not filled. The row without a return stays NaN, so every return window that touches it is blank. `tilt_frames`
  marks the next row in `path_break`; the driver blanks each level window (a price ratio or a maximum) that holds
  one, and reports each held position across one with its weight. The holding months across a `path_break` are
  declared blank months (`path_break_held`); the binding rule is `data.loader_rules.P1_path_break` in
  `docs/preregistrations/m55_trial_family_v1.json` (amendment 1, V6). Rejected: no price after the break (a held name
  would lock and could get a false -100 percent event), and a restart at a new base (a false return in the engine).
- P-2 (D3, D6): a delisting-row return of -100 percent (9 rows) cannot be a positive close, so that row stays NaN
  and the loader supplies the return as the delisting return.
- P-3 (D4): eligibility at the decision row t is the engine's own interval mask at r: `mbrstartdt <= t < mbrenddt`.
  A member on its last index day is not bought for the next row. This is the M5 rule
  `resolved_universe_at_next_execution_row`; the literal "in force at r - 1" would give a target the engine refuses.
- P-4 (D5): the count's basis is the first daily row on or after `shrstartdt` with a factor, on or before t. No
  valid close or factor at t, or no basis factor by t, is `unmapped`.
- P-5 (D8): rows dropped and counted, by table: no fiscal key (also a `datadate` with two `fyearq` in `comp_fundq`),
  no known date, a known date before `datadate` (Snapshot 2,478; URQ 35), and a fiscal key on two `datadate` values.
- P-6: a zero `dlyprc` is no price (1,108 rows), so it stays typed missing.
- P-7: the 21 member PERMNOs whose path ends without a delisting record all end in 2019-07, the same count as the
  sealed delisting records. A pre-seal window ends before 2019-07, so they do not reach the engine.
- P-8 (coordinator decision, card m55-loader-p9): IBES FY1 rows with a currency other than USD, or with no
  currency, are dropped before `signal_inputs` returns and counted by year (695 rows, 1978 to 2026). S1 divides the
  estimate by a USD price, so a row in another currency would give a wrong value. All IBES rows in the file are FY1.
- P-9 (D8, coordinator decision, card m55-loader-p9: option (a)): `comp_urq.ajexq` equals the current
  `comp_fundq.ajexq` on all 135,119 matched rows, and 36 of 5,431 quarters reported up to a year before a CRSP split
  have `ajexq` 1, so URQ `ajexq` is not first-reported. The loader never reads it and supplies `ajexq` 1.0 on every
  `fund_quarterly` row. S2 is unchanged: each quarter's first-reported EPS is on the share basis of its own first
  known date, and the CRSP `cfacshr` ratio moves it to the basis of q's known date. Reason: by ASC 260, reported EPS
  is restated for a split that takes effect before the statements are issued, so first-reported EPS has the share
  basis of its report date, the basis of `cfacshr` at that date. The data agree: URQ `epspxq` is as reported
  (136,579 of 136,751 equal the current value). The `ajexq_not_first_reported` refusal is removed; the 36 of 5,431
  count stays in the intake report as an aggregate.
- Round 1 review fixes (coordinator decisions, card m55-loader-fix-r1):
  - Item 1 (D5, P-4; GPT-M1, Opus M-1): the basis factor of a share fact comes from the PERMNO's full main daily
    rows, not the window. When a gap lies between `shrstartdt` and the basis row (a calendar row without a factor
    row, or the seal) and `dlycumfacshr` on the last row before `shrstartdt` differs from the basis factor, ME is
    `unmapped`. Real effect: 190 member-days in 2020, all after the seal (ME `unmapped` in 2020 rises from 9 to 199).
  - Item 2 (P-5; GPT-M2): fiscal-key conflicts are resolved by first known date. In each gvkey, a record (a
    `datadate` and its fiscal key) whose fiscal key or `datadate` an earlier-known record holds is dropped; records
    first known on the same date that share either all drop. A later row never removes an earlier known row. Each
    table uses its own clock: `fund_annual` and `fund_quarterly` their known date (after the known-date drops),
    `announcements` its `rdq` (public on `rdq`). Drops: Snapshot 340 (was 605); `fund_quarterly` 45 and
    `announcements` 48 (both were 94).
  - Item 3 (D6; GPT-M3): no settlement before the `dlydelflg = 'Y'` row. `effective_date` = `known_at` = the later
    of the row after the last valued row and the `Y` row. The engine settles from a close on the row before the
    effective row (H-8), so it cannot hold a position across rows without a value up to the `Y` row; `tilt_frames`
    refuses such a window (`terminal_gap_unsupported`). Real count: 0 events in both R4 runs.
  - Item 4 (R4; trial GPT-R1-03): `tilt_frames(..., run="last_close")` removes the return of every `Y` row from the
    price path (the path ends at the last trade close) and settles every event there (`delisting_return` 0.0),
    with the item 3 timing. ME in that run needs a close of the same path. The engine run must be `last_close`
    too, so the R4 sign comparison is between the two loader runs. The default `primary` run is unchanged.
  - Item 5 (trial OI-11, OI-12): the `daily` signal-input table carries `primaryexch` and `dlyprcflg`. Member-days
    with `dlyprcflg = 'BA'`: 38,741 of 8,062,444.
  - Item 7, D8 amendment (R1; trial Opus M3): `daily.shrout` in the signal inputs is the D5 share count on the
    row's basis (with item 1), NaN under the D5 reasons; the raw daily `shrout` is no longer an input to S7 or S8.
    The D7 check still reads the raw `shrout`. Member-days with a share count: 8,045,516 (raw 8,059,824) of
    8,060,169 with a daily row.
  - Opus A-1 (S3 across the seal) is a driver item; no change here.
- No reading loosens R1, R2, R4, R6, or R8.

Consequences:

- The first driver run uses `tilt_frames` once per seal segment, adds the six Family A signals, and applies the
  `path_break` blank (P-1). The R4 rerun uses `run="last_close"` in both `tilt_frames` and the engine.
- Real intake aggregates are in `coord/reports/m55_loader/intake_report.md` (main checkout, not tracked). The tracked
  manifest is `reports/wrds_manifest_2025.json`: names, row counts, and hashes only.

## 2026-10-05 - Signals S1 to S8 Rules (Milestone 5.5, coordinator decisions)

Context:

- `research/m55_signals.py` computes the candidate signals S1 to S8 for the O-21 screen on a normalized input
  schema. Two review rounds found timing and share-basis defects; the coordinator decided each finding. Synthetic
  fixtures only; no real data was read.

Decision:

- First-reported values: each Compustat item of a record is its first non-missing value, usable from its own
  known date plus one trading row. A later revision is a look-ahead source, so it never replaces that value.
- S2 takes `epspxq` and `ajexq` from one row (the first row with EPS) and puts each quarter on the CRSP share
  factor (`cfacshr`) basis of the latest quarter's basis date, with no factor read at t. Two rows could mix share
  bases, and `cfacpr` also moves at a spin-off; S2 is scale-free, so a read at t adds only a failure path.
- The IBES link resolves at each `statpers` with `score <= 1`, and the usable date (the first month-end row after
  `statpers`) is applied before the monthly grouping. A reused ticker then never crosses PERMNOs, and a row not
  usable at t cannot change the selected month.
- S3 uses the CRSP value-weighted market, INDNO 1000200, because INDNO 1000500 is not in the subscription.
- Price anchors (S7, S8, the S1 price) are exact rows with no as-of fill: a filled price would hide a missing row
  (R6). Only the CRSP factor reads are as-of reads, at most one month old.
- Reason order is items, then market data, then domain, so one input gap gives the same reason in every signal.
- Declared sample rule: an S2 quarter is read only when the PERMNO has a `cfacshr` row at the basis date. A
  history from before the first CRSP row is not read, so a new listing has no S2 value for about 2.5 to 3 years.
  The cells stay typed. This favors seasoned firms in the S2 ranks, and the first real run reports its size.
- None of these rules loosens R1, R2, R3, or R6.

Consequences:

- The first real run owes three loader checks: a known-split check (direction of `cfacpr` and `cfacshr`), the
  first-reported URQ `ajexq` from the same row as `epspxq` (never a current-vintage value), and the signal reason
  shares by later exit class.
- Backlog (O3-A2): the `no_record` versus `not_yet_known` label can depend on rows dated after t. Values and valid
  counts do not change; the label is a diagnostic.

## 2026-10-05 - Declared Signal Set for the Index Tilt (Milestone 5.5, card m55-signal-sets, coordinator default)

Context:

- The O-21 screen runs each candidate S1 to S8 alone as a 2 percent TE tilt, then one composite of the shortlisted
  candidates, and the six Family A price signals once as a counted baseline. `research/m55_index_tilt.py` accepted
  only the six Family A signals and a fixed minimum of 4 valid signals.

Decision (coordinator technical default):

- The caller declares the signal set (`signal_ids`) and the valid-signal minimum (`min_valid`) in `TiltInputs`.
  The defaults are the six Family A signals and 4, so every default output is bit-identical to `6395511`.
- The screen rule "c = 0 when fewer than half of the n signals are valid" is `min_valid = half_rule(n)`, with
  `half_rule(n) = ceil(n / 2)`. The driver passes it; the engine does not choose it.
- The engine applies no sign. Each signal value must already carry its declared sign (higher is better).

Consequences:

- The rank pool, the exact-fraction ranks, the full-history rule, the c = 0 counts, the weights, the cap loop, TE
  scaling, costs, B2, and the low-risk rules do not change. The engine still reads signals at row r - 1.
- The engine does not fix `min_valid` for the Family A baseline (4 of 6 by default; `half_rule(6)` is 3). The
  screen trial file must state it before results (R9; Opus advisory A-3).

## 2026-10-05 - Low-Risk Book Calibration Rules (Milestone 5.5, coordinator defaults)

Context:

- The O-20 low-risk book (`research/m55_index_tilt.py`, `lowrisk_weights` and `calibrate_lowrisk`) picks the
  volatility power `g` from ex-ante second moments only. Review round 2 left one MATERIAL finding open (GPT-R2-01:
  the ratio did not bound missing risk). After two rounds, the expert step settled the rules. The ruling is in
  `coord/reports/m55_lowrisk/expert_decision.md` (untracked).

Decision (coordinator defaults, each with one line of reason):

- **Complete-case whole-book ratio.** The ratio uses the whole traded book on the rows of the 252-row window that
  ends at r - 1 where every traded member has a return. Reason: a suffix or free-only rule drops clean rows and
  biases the estimate toward calm regimes; complete-case rows blank only the rows that touch a missing return (R6)
  and keep crash rows.
- **126-row floor.** At least `LOWRISK_RATIO_MIN_ROWS = 126` complete-case rows, else the ratio is undefined with
  status `ratio_window_short`. Reason: 126 rows give a per-rebalance standard error of about 0.02 on the ratio,
  which the median over about 350 rebalances absorbs; a shorter window is declared, not filled.
- **Two-sided median bracket and decision order.** Undefined rebalances enter the median once at +inf and once at
  -inf; each `g` meets, fails, or is ambiguous. Order: a refusal below the first `g` that meets stops; then
  `ratio_coverage_low`; then `ratio_coverage_ambiguous` (an ambiguous `g` below the first `g` that meets; the owner
  decides); then `chosen` (the first `g` that meets); else `no_g_reaches_target`. Reason: the choice holds for any
  value of the missing ratios, so missing data cannot select `g`.
- **10 percent undefined stop.** Above `LOWRISK_UNDEFINED_MAX = 0.10` undefined rebalances, nothing is chosen
  (`ratio_coverage_low`). Reason: a calibration that rests on few defined months is not a calibration.
- **`LOWRISK_PINNED_MAX` retired.** The pinned-share limit, its `pinned_share_high` status, and its test are deleted.
  Reason: the whole-book ratio counts pinned weight directly, so the limit has no job.
- **Window diagnostic (addendum).** The diagnostic treats every `defined_partial` rebalance as undefined and repeats
  the bracket classes and the choice, with no coverage stop inside it. `window_sensitive` is set only when its
  choice differs from the main decision; `window_diag_coverage_high` (diagnostic undefined share above 0.10) is
  recorded apart. Reason: with the coverage stop inside, partial windows alone set the flag almost always.

Consequences:

- None of these defaults loosens R1, R2, R4, R6, R8, or R9. Weights, the cap loop, TE scaling, and every TILT
  output are bit-identical to the round 1 code; only the ratio and the decision changed.
- The real-data driver card must copy these defaults into the trial file before any real calibration output (R9).
  The driver card also carries the 1963-1992 missingness census, the daily data span and first full 252-row
  anchor, the R6 exit-class split of undefined and partial counts, the bid/ask-midpoint day rule, and Opus ADV-05
  (cut and hash the calibration panel).
- Residual limitation: a `defined_partial` ratio cannot measure risk on rows before a member existed. Such windows
  are declared, counted (`ratio_rows_leading`, `ratio_rows_gap`), and checked by `window_sensitive`.

## 2026-10-05 - Owner Decision O-22: R11 Grant for WRDS Data

Context:

- The owner's WRDS account is approved (2026-10-05). The intake note asks for an R11 grant that names the tables,
  purpose, storage, and publication terms, and for answers to its risks 1 (purpose) and 2 (publication). It also
  leaves open whether the seal months are dropped at the pull.

Decision:

- **O-22 (owner, 2026-10-05):**
  - Scope: WRDS CRSP (CIZ stock, index, and S&P 500 constituent tables), Compustat North America and Compustat
    Snapshot, IBES, and the CRSP-Compustat and IBES-CRSP link tables, as listed in the download checklist.
  - Purpose: the owner's personal academic, non-commercial research. Only the owner logs in and downloads; agents
    read the local files. No real money uses a rule derived from these data.
  - Storage: two copies, outside every Git checkout. The working copy is `<local_data_root>/wrds_<vintage>/` on
    the local disk, in a folder that iCloud does not sync; all scripts read only this copy. The backup is one
    archive per vintage, `<private_data_root>/wrds_backup/wrds_<vintage>.tar`, next to the EODHD folders, synced
    by iCloud. No script reads the backup. It is written once after the manifest, and its SHA-256 is checked after
    the copy. To restore, the owner extracts the archive and checks the manifest hashes. This keeps iCloud
    conflict copies and cloud-only files away from the files that scripts read (A2-D-ADV-6).
  - Publication: Git holds only a manifest and hashes. No raw provider row, membership list, security code or
    ticker list, company name, credential, or private path goes into Git. Noncommercial aggregates follow the
    existing owner data terms.
  - Seal months: in each table with a price or a return, rows whose economic date interval touches
    `[2019-07-31, 2020-07-31)`, or could touch it when a date is missing, are downloaded into a separate folder
    `wrds_<vintage>/sealed/` (in the working copy; the backup archive holds it as bytes) and are never opened.
    It joins the O-18 never-opened paths. Its files are hashed as bytes only. Tables with no price or return
    (membership, links, shares, fundamentals, estimates) keep these dates in their main files (coordinator
    default). Rebalances whose windows touch the seal months stay typed missing.

Consequences:

- The coordinator may build the WRDS loader and read the local files outside `sealed/`. Every card that lets an
  agent read these files lists the never-opened paths, `wrds_<vintage>/sealed/**` included.
- Next: the owner runs the read-only subscription probe, then the reviewed pull script.

## 2026-10-04 - Signal-Screen Criteria Module: Coordinator Defaults and WRDS Source Facts

Context:

- `research/m55_criteria.py` turns monthly net return series into the O-19 and O-21 screen, shortlist, success, and
  stop decisions. It was built on synthetic series and reviewed by two seats from different model families. The
  design note left some choices to the coordinator.

Decision:

- Coordinator defaults, logged:
  1. Annual mean = 12 x the monthly mean; annual volatility or TE = the ddof-1 monthly standard deviation x sqrt(12).
     HAC t uses `newey_west_mean_tstat` with its automatic lag; one-sided p = `norm.sf(t)`. The Holm rule is read as
     an adjusted one-sided p of at most 0.05 (O-21 states it as a t of 1.65 after Holm).
  2. Test A is an intersection-union test over the active series against SPY and against CW-PIT: p_A is the larger
     one-sided p. Test B is an intersection-union test over the 0.5-point non-inferiority test and the volatility
     ratio: p_B is the larger of p_NI and p_vol.
  3. The volatility-ratio bootstrap is a paired moving-block bootstrap: 12-month blocks without wrap, 10,000 draws,
     a fixed seed. p_vol is the share of draws with a ratio of at least 1.0; the bound is the 95th percentile, and
     B also needs it below 1.0. A reviewer simulation found this percentile bound slightly liberal (about 6 to 7
     percent at a true ratio of 1.0, against 5 percent); the 0.90 point rule, the non-inferiority test, and Holm make
     B stricter overall. The trial file states it.
  4. The screen record and the shortlist are hashed (SHA-256 of canonical JSON, failed and undefined candidates
     included). Every confirm or check call takes the digest saved at the freeze as a separate input and refuses on
     any mismatch or changed rule value.
  5. A screen series covers at least 36 months and ends at 1992-12; a confirm series covers exactly 1993-02 to
     2014-03; a check series starts at 2014-04 and leaves out the months 2019-07 to 2020-07, whose returns touch the
     seal window (O-12, O-18).
  6. After `screen_empty`, test A and the composite stop rule are not run, but test B may run: the low-risk version
     uses no screened signal (O-20), and the O-21 stop rule closes the confirm months for a tilt only. The Holm
     family stays at size 2 with p_A = 1.0.
  7. The secondary family uses BY with a family size fixed by the caller (the trial file).
- None of these loosens R6, R8, R9, or R10.
- **WRDS source facts (coordinator check, two independent web checks per claim, 2026-10-04).** First-reported
  Compustat values exist only in the point-in-time product (Compustat Snapshot) from about December 1986; standard
  `funda` and `fundq` values are restated or re-standardized later, so R1 bars them. Under the locked design,
  signals S2, S4, S5, S6, and S8 therefore have about five screen years (1987 to 1992); S1 (IBES, from 1976), S3,
  and S7 are not affected, and the confirm period is fully covered. Legacy CRSP delisting code 232 is a stock merger
  into an untracked acquirer, not a cash merger; the R4 cash class uses `DelPaymentType = 'CASH'` (legacy 233). In
  the CRSP CIZ format the daily return already holds the delisting return; a missing delisting payoff still takes
  the R4 default.

## 2026-10-03 - Owner Decision O-21: Signal-Screen Thresholds and Stop Rule Locked

Context:

- O-19 asks for a declared signal screen and numeric success thresholds before any result. The screen design note
  (revision 3, after one adversarial critique) went to the owner. No data was read to write it.

Decision:

- **O-21 (owner, 2026-10-03):** the thresholds and the stop rule are locked as written:
  - Periods: screen 1963-07 to 1992-12; confirm 1993-02 to 2014-03 (254 months); check 2014-04 to the last month.
  - Shortlist: screen net information ratio at least 0.2 and HAC t at least 1.0. The primary test is one composite
    (the mean of the shortlisted scores).
  - Test A (the tilt): in the confirm period, net of dated costs, the annual active return is above zero against
    SPY and against CW-PIT, each with a one-sided HAC t of at least 1.65 after Holm; the signs hold at 2x costs;
    neither check-period estimate is negative.
  - Test B (the O-20 low-risk version): a HAC non-inferiority test that the annual net return is no more than 0.5
    point below SPY (one-sided 5 percent), and a volatility ratio to SPY of at most 0.90 with a block-bootstrap
    one-sided 95 percent upper bound below 1.0. Drawdowns are reported, not tested. In the check period the return
    gap is above -0.5 point and the volatility ratio is below 1.0.
  - Stop rule: no shortlisted candidate means stop before any confirm month is opened. A confirm-period composite
    estimate below 0.3 percent a year against SPY stops the line as a declared negative result; any later change is
    a new counted trial with no clean confirm data left.

Consequences:

- The trial file carries these numbers and is frozen by two seats before the screen runs. The candidate list
  depends on WRDS coverage (a first-reported Compustat source); a dropped candidate is recorded, not replaced.

## 2026-10-02 - Owner Decision O-20: A Separate Low-Risk Version for the Lower-Risk Criterion

Context:

- O-19 counts two kinds of success: the tilt beats SPY after costs (A), or it gives about the same return with
  materially lower drawdown and volatility (B). Under the 2 percent ex-ante TE limit and the 1-point cap, the tilt
  stays close to the index; its volatility can be at most about 2 points below SPY's. So B cannot be met by the tilt.

Decision:

- **O-20 (owner, 2026-10-02):** criterion B is judged on a separate low-risk version.
  - It is built from risk only: the 252-day volatility and covariance known at r - 1. It uses no screened return
    signal, so no screen or confirm month selects it.
  - Budget: ex-ante TE about 5 percent and at most 2 points active weight per stock. The exact numbers are set from
    1963-1992 risk data only (no returns), for an ex-ante volatility about 10 to 15 percent below the index.
  - It is judged only on B. Test A (the tilt) and test B (the low-risk version) form one primary family with a Holm
    correction at 5 percent. The power of A for an information ratio of 0.3 drops from about 39 to about 30 percent.
  - Label: factor-level in-sample, since the low-volatility effect was published in the 1970s.

Consequences:

- The signal-screen design note and the trial file carry both versions. The low-risk budget is calibrated after the
  CRSP loader and before the trial file is frozen.

## 2026-10-02 - Owner Decision O-19: Data and Success Criterion for the Index Tilt

Context:

- The index tilt removes the size bet of the Milestone 5 sleeves, but it beats SPY only if its signals carry an
  edge in large caps. The six price signals did not beat the equal-weight book in Milestone 5, and test power is
  low (about 16 to 18 percent for an information ratio of 0.3 over 1993-2014).

Decision:

- **O-19 (owner, 2026-10-02):**
  - Data: when WRDS access is approved, use CRSP, Compustat, and IBES. First confirm that the university
    subscription includes Compustat and IBES. The owner downloads; agents read local files only.
  - Success: the tilt beats SPY after costs, or it gives about the same return as SPY with materially lower
    drawdown and volatility. The numeric thresholds go into the trial file before any result.

Consequences:

- A declared signal screen comes before the test: screen on early years, confirm on later years that the screen
  never used, keep a shortlist of at most 10 (R9), and state a stop rule. Its design note goes to the owner before
  it is locked.
- If the confirmed signals do not meet the criterion, the result is reported as a pre-declared negative result.

## 2026-10-02 - Index-Tilt Engine: Coordinator Defaults and the Delisting-at-Rebalance Rule

Context:

- The engine (`research/m55_index_tilt.py`) was built on synthetic fixtures and reviewed by two seats from different
  model families. The producer picked technical defaults where the design note left a choice.

Decision:

- Coordinator defaults, logged (state after the two repairs and the expert step):
  1. Renormalization is multiplicative on the members free to tilt. The cap loop runs to max |w - b| <= cap +
     1e-12 in at most 100 passes, else it refuses.
  2. TE scaling is closed form, w = b + s (w - b) with s = min(1, 0.02 / TE); members pinned at b stay at b.
  3. Ex-ante TE = sqrt(252) x the ddof-1 standard deviation of the daily active return over the 252 rows ending at
     r - 1.
  4. A member without a complete 252-row return window ending at r - 1 gets c = 0 and stays at b.
  5. The rank pool is the book members with a valid signal value; ties take the average rank; ranks are exact
     fractions, so a true zero score is exactly zero.
  6. A disappearance event changes the target at r only when its caller-supplied `known_at` is at or before r - 1.
     An event effective at r and first known at r follows the delisting-at-rebalance rule below (it refused before
     that rule was built).
  7. The dated schedule rate (commission plus spread) is split between the engine's transaction and slippage
     columns; annual turnover and cost drag include the first purchase from cash.
  8. Monthly returns use calendar months after the first rebalance. A window needs at least two rebalances, and a
     calendar month with no row refuses.
  9. An infinite signal value refuses; a NaN is invalid for that signal only.
- None of these loosens R1, R2, R4, R6, R8, or R9.
- **Delisting at the rebalance row (Opus B2; the owner gave the choice to the expert step).** Default 6 stops a real
  run when a held target member delists on a rebalance row with no earlier notice. CRSP gives the delisting date but
  no announcement date, so an earlier `known_at` from the loader cannot remove the stop. Rule (built in
  `rebalance_targets`; two seats PASS with no MATERIAL finding):
  - The traded set at r is the target members minus the names that settle at r on an event first known at r. Their
    held positions settle under R4 in both books.
  - Scores, ranks, and the covariance stay at r - 1, and these names still count in the ranks of the others.
    CW-PIT renormalizes pro rata over the traded set. TILT runs the same tilt, cap, and TE step on the traded set.
  - The report states the count and weight share of these events at each rebalance (`unknown_event_excluded`,
    `unknown_event_cw_share`; the share is over the r - 1 ME of all target members). A rebalance with no traded
    member refuses (`traded_set_empty`).
  - An earlier `known_at` is allowed only with real evidence (for example an 8-K date); no loader invents one. If a
    reviewer asks for the strictest rule, the fallback holds that weight as cash until the next rebalance.

Consequences:

- The rule uses one execution-time fact, "no close at r", like the halt policy. All decision inputs stay at r - 1,
  and the held loss is booked under R4, so no outcome leaves the sample. `members` and the `c_zero` counts still
  include these names; the traded count is `members - unknown_event_excluded`.

## 2026-10-02 - Owner Decision O-18: Seal Kept After the Inventory Incident; Quarantine Stays Closed

Context:

- An untracked inventory script opened private files that the seal records list as never opened downstream. It
  kept date columns only, and no model saw a seal-window value (`docs/engineering_log.md`, incident entry).

Decision:

- **O-18 (owner, 2026-10-02):** the seal window stays usable as is. The new process-failure row is confirmed: a card
  that lets an agent read private data lists the seal's never-opened paths, and scripts read bars only through
  `read_discovery`. The part 2 diagnostic of unpriced members does not open `quarantine/**`; CRSP fills those days.

## 2026-10-02 - Owner Decision O-17: Index Tilt Is the Next Line of Work

Context:

- Milestone 5 left the next line of work open (O-12). The equal-weight top-20 percent sleeves trailed SPY, and the
  gap mixed the size bet, the disappearance default, and unpriced members (O-16).
- The coordinator proposed a construction that starts from point-in-time cap weights and tilts toward factor
  scores, judged against SPY. Design notes (untracked): `coord/reports/m6_prep/index_tilt_design_note.md`,
  `coord/reports/m6_prep/crsp_intake_design_note.md`, and `coord/reports/m6_prep/unpriced_inventory.md`.

Decision:

- **O-17 (owner, 2026-10-02):** the owner chose the index tilt ("a very good method") and the coordinator's plan:
  - Part 1: test factor tilts on priced, point-in-time S&P 500 members against SPY. A survivor-only cohort runs
    only as a labeled `DIAGNOSTIC_ONLY` check (R2), if at all.
  - Part 2: report the returns of the members that step 4 left unpriced, as a diagnostic.
  - Tracking error cap 2 percent a year against the cap-weight book; at most 1 percentage point active weight per
    stock (Q1).
  - CRSP results carry the label "stock-level out-of-sample, factor-level in-sample" and are not called
    confirmation (Q3).
- The owner applied for WRDS access on 2026-10-02. The approval is not yet known.

Consequences:

- The milestone is named Milestone 5.5 (coordinator default). In `docs/north_star.md`, Milestone 6 stays the future
  execution system.
- The dated R0 freeze is not scheduled; R0 is not the candidate any more.
- Coordinator defaults, logged: six price signals only on CRSP months (Q2); a SEC variant only on `real_v2`.
- Still open for the owner: the R11 grant for CRSP with its tables, storage, and publication terms, and the CRSP
  start year (Q4); and extending O-5 and O-9 to the `real_v2` tilt diagnostic (Q5).
- Next build, before any data: the cap-weight and tilt engine on synthetic fixtures, with two review seats. No tilt
  or cap-weight return exists before the trial file is frozen.

## 2026-10-02 - Owner Decision O-16: Exact Wording for the Milestone 5 Conclusion

Context:

- The owner asked how the Milestone 5 conclusion was reached. A coordinator check of the committed records found that
  the O-12 sentence "At this evidence ceiling, no rule beats an index fund" says more than the evidence:
  - No test against SPY was declared, so the gap has no p-value or q-value.
  - The quoted gaps use the -100 percent disappearance default. In the last-close rerun, R0 trails SPY by 1.60 and
    8.39 percentage points a year, not 4.61 and 9.73 (`reports/m5_step4.json`, `runs.last_close.excess`).
  - The gap mixes equal against cap weight with the disappearance default and the unpriced members; in the
    last-close rerun the equal-weight book made 9.14 and 10.68 percent a year against SPY's 10.41 and 16.41
    (`reports/m5_step4.json`, `runs.last_close.benchmarks`).
  - Rules R3 and R4 ran only on public data, and discovery never ran.
- The three step 6 review advisories (GPT-S6-R1-A1 to A3: q-values, public-factor hindsight, disappearance counts
  and weights) were not in the merged report.

Decision:

- **O-16 (owner, 2026-10-02):** correct the report. The headline becomes "No rule that we tested beat SPY after costs
  on our point-in-time S&P 500 books. Milestone 6 does not start on this allocator."

Consequences:

- `reports/m5_owner_report.md` states the new headline, four limits under it, the last-close gaps, the committed
  q-values, the public-factor hindsight caveat, and the R0 disappearance counts and weights. It still computes
  nothing new. GPT-S6-R1-A1 to A3 are closed.
- The decision does not change: Milestone 6 does not start on this allocator.

## 2026-10-02 - Owner Decision O-15: Simplified Technical English as the Writing Target

Context:

- The owner wants repository text that is easy to read and translate.

Decision:

- **O-15 (owner, 2026-10-02):** add to `AGENTS.md`: "Write at about 80% of ASD-STE100 (Simplified Technical
  English)."

Consequences:

- The rule is a target, not a test. It applies to new text in the repository, on GitHub, and in reports. Existing
  text is not rewritten for it.
- The owner also had the ablation route and rules removed from the shared coordination standards (commit `85f29f5` in
  that repository), outside this repository. That closes advisory O14-R1-A1.

## 2026-10-01 - Owner Decision O-14: AGENTS.md Simplified and the Ablation Rule Removed

Context:

- After O-13 the owner asked whether `AGENTS.md` needed all of its content. The coordinator found text that repeated
  the controller, the handoff, or the coordination standard; generic habits; and a rule (the walking skeleton) the
  project has outgrown. O-13's own evidence showed that routine ablation removed almost no code.

Decision:

- **O-14 (owner, 2026-10-01):** the owner approved both proposals: simplify `AGENTS.md` with R1–R12 and the owner process constraints
  unchanged, and delete the ablation rule entirely. The local Milestone 5 ablation worktree, branch, and patches are
  deleted.

Consequences:

- `AGENTS.md` goes from 200 to 136 lines. Its R1–R12 and Owner Process Constraints sections are unchanged word for
  word. The same-PR lifecycle authorization, the review priorities, and the process-failure procedure move to the
  controller. The startup reading list and the scope-reporting habit are removed because the controller already
  covers them. The Mermaid diagram habit and the walking skeleton rule are dropped as unneeded; no other source keeps
  them.
- The Ablation sections of `AGENTS.md` and the controller are removed, with `docs/ablation_round2.md`. One line in
  Engineering And Change Discipline replaces them: when a capability, data source, or module is retired, its code is
  deleted in the same PR. A deeper cleanup happens only when the owner asks for one.
- Tests named for past ablation passes stay; they guard computed behavior.

## 2026-10-01 - Owner Decision O-13: Triggered, Budget-Capped Ablation; Milestone 5 Ablation Patches Dropped

Context:

- The coordinator evaluated every ablation pass since PR #202 (`coord/reports/m5_ablation/ablation_value_review.md`,
  untracked). The two whole-codebase passes of 2026-09-07 and 2026-09-08 removed 18 production lines net. The
  per-delivery passes of 2026-09-16 to 2026-09-28 removed 3 lines of code already on `main`. The Milestone 5 pass,
  stopped by the owner before its combined recompute, held 24 patches with a net of 75 production lines (about
  0.16%) and was never merged. The one large cut, PR #259 (35.5% of production code), came from a strategic audit
  and an owner decision, not from the ablation rule.
- The Milestone 5 pass used about 195.6 million tokens, 96% of them cache reads: about 22 times the step 6 session
  and about 23% of all Claude tokens on this project from 2026-09-28 to 2026-10-01.

Decision:

- **O-13 (owner, 2026-10-01):**
  - Ablation runs only on a trigger: a milestone retires a whole capability or data source, a scan finds a module
    with no consumer, production code grows sharply, or the owner asks.
  - A pass starts with one agent running cheap static checks, has a hard budget of 20 million tokens, and uses at
    most two subagents.
  - A pass targets whole units only: modules, stages, rules, and unused committed evidence. Ordinary code review
    handles small surplus.
  - Removals that can change a result are verified by one combined recompute against the baseline, not one
    recompute per removal.
  - The 24 Milestone 5 ablation patches are dropped.

Consequences:

- The AGENTS.md Ablation section states the new rule; the guards R1–R12 require stay.
- No Milestone 5 ablation result is merged. The dated freeze of R0 is the next research step.

## 2026-09-30 - Owner Decision O-12: Owner Report Conclusion, No Seal Look, No Forward Observation

Context:

- The step 6 design note (`coord/reports/m5_step6/design_note.md`, untracked) found that R0, the baseline candidate,
  trails SPY and the equal-weight point-in-time book in both segments (`reports/m5_step4.md`). It also found that no
  authorized source supplies stock prices or membership after `real_v2` ends on 2026-08-07. It asked the owner four
  questions.

Decision:

- **O-12 (owner, 2026-09-30):**
  - Forward data: "Can we not use new data after August 2026, and use only the data through August 2026? I think the
    extra month of data would not help, and it would cost me a lot of money." No new price or membership source and
    no spending is authorized, and forward observation is not run.
  - Seal window `[2019-07-31, 2020-07-31)`: "Keep it reserved." It is kept for a future candidate with a real edge or
    for the later M4.8 stages. Step 6 makes no seal-window look. This replaces the O-11 reservation of the window for
    confirming the frozen allocator.
  - Report conclusion: "Yes, write it that way," for "At this evidence ceiling, no rule beats an index fund; Milestone
    6 does not start on this allocator."
  - Next line of work after Milestone 5: "Not decided yet; discuss after the report."

Consequences:

- `reports/m5_owner_report.md` states the approved conclusion. It quotes committed results only and computes
  nothing new.
- The dated freeze of R0 follows the milestone ablation and pins no seal or forward look. Forward observation needs a
  new owner decision on data and money.
- The factor-ETF blend benchmark stays absent, because no source is authorized.

## 2026-09-30 - Owner Decision O-11: Step 5 Deferred, Seal Window Kept, Step 6 Next

Context:

- Steps 1 to 4b are merged (`03e06b5`, PR #281). On point-in-time books the baseline class set is the four price
  classes (six sleeves) under R0; the SEC Value and Quality classes do not join.
- The step 5 design note (`coord/reports/m5_step5/design_note.md`, untracked) computed no result. What it records:
  - Question: does any new price-volume sleeve join R0? Search pool: 15 JKP market characteristics in the four kept
    themes. Controls: 20 random-grammar replicates of 15 signals, and the 4 OSAP placebos computable from OHLCV
    (DownsideBeta, BetaDimson, IdioVolCAPM, ReturnSkewCAPM), each a near twin of one candidate.
  - Plan: screen on the 55 pre months, freeze a shortlist of at most 10, confirm on the 44 post months.
  - Premise check: no trait region survived with evidence in steps 3 to 4b, so the search would look inside the
    region R0 already holds.
  - Power (rough): one added sleeve needs about 0.6 percent a month over R0 for p 0.05 over 44 months, and about
    0.9 percent after BY over a shortlist of 10. The expected outcome is a null.
- No step 5 trial amendment was committed and no step 5 signal, return, or statistic exists, so no trial is
  appended and the cumulative BY family stays at 481.

Decision:

- **O-11 (owner, 2026-09-30):**
  - Step 5: "Skip step 5 for now and do step 6." Step 5 is deferred for insufficient power. The reason and the design
    note are kept.
  - Seal window `[2019-07-31, 2020-07-31)`: "Keep it sealed." It is reserved for confirming the frozen allocator
    after step 6.
  - OSAP placebos, if step 5 runs later: "Keep the 4, descriptive only." The random search stays the gate.

Consequences:

- Step 6 (owner report, dated freeze, forward observation) is the next step, on the four-price-class R0 baseline.
- Step 5 reopens only by owner decision, for example when new stock-level months or a new candidate source would
  bring the minimum detectable gain of one added sleeve near a plausible size. The design note's power check is
  redone first, and a reopened step 5 freezes its own trial amendment before any result.
- The seal window stays unaccessed. Spending it on the frozen allocator leaves no unused stock-level holdout for
  M4.8 Stages E to H.

## 2026-09-30 - Milestone 5 Step 4b Trial Amendment 5 (Coordinator Technical Defaults)

Context:

- Step 4b asks one question: do SEC as-filed value and quality sleeves join the step 4 baseline class set? The
  entries below bind it: O-5 and O-9 extended to step 4b with the step 4b scope defaults, and O-10. The design note
  (`coord/reports/m5_step4b/design_note.md`, untracked) proposed the definitions.
- The SEC data build (code `7560b4a`) produced the local CIK map and the companyfacts cache. It computed no signal
  or return (`reports/m5_step4b_data.md`).

Decision:

- Amendment 5 (`docs/preregistrations/m5_trial_family_v1_amendment_5.json`) freezes step 4b. Each revision was
  committed alone, before any step 4b signal code, SEC signal value, sleeve, return, or rule result.
  - Revision 1: `acc1f5a`, SHA-256 `136fa9f7...c1dd`. It follows the data-build review round 1: both seats reported
    MATERIAL 0. OPUS-S4B-D-01 to D-03 and GPT-S4BD-A2 reading 2 are folded in; the other advisories are in the
    roadmap backlog.
  - Revision 2: `e4d73ce`, SHA-256 `a712188c...0c75c`. It repairs freeze review round 1: GPT reported MATERIAL 1
    and ADVISORY 2, and Opus reported MATERIAL 1 and ADVISORY 7. The coordinator rulings are the revision 2
    defaults below.
  - It amends amendment 4 and pins it, v1, and amendments 1 to 3 by SHA-256. The `real_v2` pins are amendment 4's,
    unchanged.
  - It pins the SEC data by the CIK-map SHA-256 `09d163b9...120a` and the per-file hash-list SHA-256
    `3c73ffe2...698a`, not by the manifest's own hash. The runner reads the cache offline only and refuses on any
    mismatch.
- Decision outcome:
  - The SEC Value and Quality classes join the baseline class set when R0 over the 6 price sleeves plus the 3 SEC
    sleeves meets all 8 step 2 conditions against the step 4 six-sleeve R0 in the primary run.
  - Otherwise they do not join, reported as a negative.
  - Fragility, the coverage-tilt label, the last-close outcome, and the S4b q-value are reported beside the outcome
    and do not change it.
- Coordinator technical defaults, one line each. None loosens R1, R2, R4, R6, R8, or R9.
  - Only IDs with rule F status `unique` (563 of 632) are rankable. Unmapped, ambiguous, and multi-class IDs are
    typed missing and stay in the price sleeves.
  - Annual 10-K and 10-KT facts only. A key's value comes from its first-filed 10-K or 10-KT fact, ties to the
    lowest accn; a key first filed in an amendment is typed missing; `frame`, `fy`, and `fp` are never read.
  - A fact is usable only if its filing date is before the date of row r - 1.
  - Every component of a signal takes the anchor concept's latest fiscal year E*, with no mixing of years.
    E* earlier than row r - 1 minus 18 months is stale. There is no older-year or quarterly fallback.
  - The share-date price is the last finite close within 10 rows on or before the cover date, inside the segment's
    loaded rows; in the post segment no seal-window price is read.
  - Revision 2 rulings, one line each:
    1. GPT-S4BF-R1-M1: every evaluation-mask member-day gets one status. A ranking-set member at signal row r - 1
       carries its rebalance-r status until the next rebalance. A between-rebalance entrant, or eligibility
       resuming after a bar gap over r - 1, is `not_ranked_at_rebalance`, first in the order and counted by later
       exit class. The reconciliation refusal stays.
    2. OPUS-S4BF-M1: preferred is the first chain concept with a key at E*, and 0 when none has one. The
       zero-by-absence cases are counted as `preferred_zero_by_absence`, not missing (the Fama-French and JKP
       convention, matching `be_me`). An amendment-first chain key at E* makes BE `amendment_first`. This replaces
       the revision 1 preferred rule.
    3. GPT-S4BF-R1-A2 and OPUS-S4BF-A4: the order is period discovery, amendment-first classification, value
       selection, staleness. E* is the latest end among anchor keys whose earliest 10-K-family fact was filed
       before row r - 1. An amendment-first E* anchor is `amendment_first`, with no fallback. In a chain, the first
       concept with a key at E* decides, with no fall-through.
    4. GPT-S4BF-R1-A1: the primary dei share count comes from the anchor accession, at its latest end on or before
       filed. The `CommonStockSharesOutstanding` fallback is restricted to end = E* before the ambiguity check.
    5. OPUS-S4BF-A2: a primary share date after filed is `shares_missing`, so p is on or before r - 1.
    6. OPUS-S4BF-A3: companyfacts carries no dimensional facts, so unlisted classes are not detected (515 filings
       without a non-dimensional dei count, 462 of them `shares_missing`).
    7. OPUS-S4BF-A1: `CostOfGoodsSold` joins the COGS chain after `CostOfRevenue`. No other tag is added, and the
       measured chain coverage is stated in the amendment's limitations.
  - The missing statuses are 15 typed reasons in a fixed order, plus the counted `preferred_zero_by_absence`. The
    member-day split by reason and exit class reconciles, or the run refuses.
  - Rule F stays as built, with no relaxation of the ticker-disagreement step (OPUS-S4B-D-03). It is fail-closed
    under R3, so the 3 affected delisting candidates stay ambiguous.
  - The foreign-form exclusion covers 20-F and 40-F filings inside the member window only. Earlier foreign
    filings do not exclude a CIK; 7 accepted IDs have them.
  - SEC facts filed inside the seal window may enter a post-segment signal. The seal governs snapshot rows and
    O-3; an SEC fact carries no snapshot row or return, and no seal-window price is read. The post comparison
    months start 2022-05, after the seal window.
  - The not-mapped share by in-segment member-days, split by exit class and identity reason, is reported beside
    the per-ID counts and gates nothing (OPUS-S4B-D-01).
  - The comparator R0 is recomputed and must equal the committed step 4 R0 metrics exactly.
  - The comparison months must equal amendment 4's 99.
  - The coverage-tilt universe is the 563 unique IDs, fixed for the run. The result is labeled coverage-tilted
    when any of the 8 margin signs changes against that comparator.
  - One test, S4b.ADD (R0 over nine sleeves minus R0 over six, primary cost, 99 pooled months, `rule_test`). BY
    family 481 = amendment 4's 480 slots at p = 1 plus the 1 observed test.
  - Rule R1 over nine sleeves, the public counterpart over the matched JKP characteristics, class returns, and
    transmission are descriptive and add no slot. R2 is not run.
  - Two review seats for the freeze and the implementation. The SEC data-build code also takes two seats, as the
    coordinator confirmed on 2026-09-30.
  - Implementation readings (code `3744acc`, `e88cea8`, and `4200cf1`), one line each. None loosens R1, R2, R4, R6, R8, or R9.
    1. OPUS-S4BF-R2-A1 (coordinator ruling): a key is amendment-first only when every earliest-filed fact is an /A
       filing. Otherwise it takes the 10-K or 10-KT value under `first_filed`, lowest accn on a tie.
    2. OPUS-S4BF-R2-A2 (coordinator ruling): the procedure computes the signal, and a non-ranked member's reason is
       the first entry of `sec_reasons.order` that applies; stale wins over `concept_missing`.
    3. GPT-S4BF-R2-A1 and OPUS-S4BF-R2-A3 (coordinator ruling): the engine's `halt_gap_return_v1` accounting is
       unchanged. `not_ranked_at_rebalance` means the member cannot be newly selected at that rebalance; a
       previously held locked position stays held, so status counts and holdings are distinct.
    4. A key's earliest fact is the minimum (filed, accn). The fiscal-year-end instant match uses the lowest accn
       among the earliest-date facts; before the run, 0 instants had a status that depends on that choice.
    5. A distinct-value tie inside one first-filed accession would take the first fact in file order; before the
       run, 0 such keys existed, and the count is reported.
    6. Staleness compares E* with the date of row r - 1 minus 18 calendar months, the day clipped to the month's
       length.
    7. The hash list is rebuilt from the cache's retrieval records, and every cached file is re-hashed against its
       record. Only the companyfacts of `unique` CIKs are parsed.
    8. For `sec_identity_pool_mismatch`, a price-sleeve asset is any asset in a segment's evaluation mask over rows
       [d0 - 1, last book row], which hold every ranking set and member-day. The eligible pool rebuilt from the
       snapshot must also equal the map's IDs.
    9. The share-date price also needs a finite, positive cumulative split factor, since the raw close is the
       split-only close times that factor.
    10. The public counterpart runs R0 over the 9 and the 6 characteristics from the first month all 9 exist and
        slices each comparison window, as step 4's public books did.
    11. A member-day's later exit class is its resolved member window's class (step 4 `classify`), else `unknown`.
    12. R0_6_mapped uses R0_6's comparison months, weights 1/6, and the drift turnover and switch cost.
    13. Two refusals were added, both stricter: `step4_regeneration_mismatch` (the recomputed step 4 results must
        equal `reports/m5_step4.json` apart from run metadata) and `sec_rebalance_rows_mismatch` (the engine's
        scheduled rebalances must equal the evaluation resets, because the SEC panels hold values only at rows
        r - 1).

## 2026-09-30 - O-5 and O-9 Extended to Milestone 5 Step 4b, and Step 4b Scope Defaults

Context:

- The step 4b design note (`coord/reports/m5_step4b/design_note.md`, untracked) proposes one decision: whether SEC
  as-filed value and quality sleeves join the step 4 baseline class set. It needs `real_v2` identity tables to map
  securities to SEC CIKs, and the same books as step 4. O-5 and O-9 were granted for step 4 only.

Decision:

- **Owner:** O-5 (local reads of `real_v1` and `real_v2`, aggregates only, nothing written inside a snapshot, the seal
  window unaccessed) and O-9 (VP-2 at `DIAGNOSTIC_ONLY`, disclosed in the report header) extend to step 4b on the same
  terms.
- **Coordinator scope defaults.** None of these loosens R1, R2, R3, R4, R6, R8, or R9.
  - Three SEC sleeves: book-to-market and earnings yield (Value) and gross profit over assets (Quality).
    Profitability and Investment wait.
  - The decision compares R0 over the six price sleeves plus the SEC sleeves with the step 4 six-sleeve R0 on the
    step 4 conditions, months, costs, R4 events, and last-close rerun. Rule R1 on the enlarged set is descriptive,
    and R2 is not run.
  - CIK mapping fails closed. A security with no unique CIK stays typed missing, with no hand override list;
    20-F and 40-F filers and predecessor CIKs are not accepted. Missing securities are counted by later exit class.
  - Annual 10-K facts only, first filed, usable from the trading day after filing, stale after 18 months. A key first
    filed in an amendment is typed missing.
  - A descriptive coverage-tilt check reruns price R0 on the mapped universe only and labels the result if any
    margin sign changes.
  - The SEC data build (CIK map, company facts, manifest) computes identity, so its code gets two review seats.

## 2026-09-30 - Owner Decision O-10: SEC EDGAR Access for Milestone 5 Step 4b

Context:

- Step 4b adds the SEC as-filed value and quality classes to the step 4 books. The O-5 entry below left SEC EDGAR
  retrieval to a separate owner decision on the R11 source list and on the User-Agent contact.
- SEC EDGAR requires every automated request to declare a name and a contact email in its `User-Agent` header,
  and limits a client to 10 requests a second.

Decision:

- **O-10 (owner):** Milestone 5 may download SEC EDGAR data, including XBRL company facts, submissions, and the
  filing index, for step 4b.
  - The `User-Agent` contact is an owner-provided research email. It is held in a local environment variable and is
    never written to the repository, a report, or an output file.
  - Retrieval stays under 10 requests a second.
- **Publication terms (owner):**
  - Downloaded SEC files stay in a gitignored local cache. The repository commits a manifest with SHA-256 hashes.
  - Per-company as-filed values stay local, because they can be joined to the private membership.
  - Aggregates (sleeve and rule returns, counts, and test statistics) may be committed at `DIAGNOSTIC_ONLY`.
  - Security codes, CIK or ticker lists tied to the membership, membership lists, and private paths are never
    committed (R11 unchanged).

Consequences:

- The step 4b trial amendment is committed before any step 4b result. Coverage counts seen while building the
  mapping are listed in its `results_seen_before_this_amendment`.
- An unresolved CIK mapping fails closed for that security (R3) and is counted in the missingness report (R6); it
  never blocks the run.

## 2026-09-29 - Milestone 5 Step 4 Trial Amendment 4 (Coordinator Technical Defaults)

Context:

- Step 4 is the first run of the price-class bridge on the point-in-time S&P 500 snapshot `real_v2`. Owner
  decisions O-5 and O-9 and the scope defaults in the entry below bind it. The design note
  (`coord/reports/m5_step4/design_note.md`, untracked) proposed the definitions.
- Revision 1 (`f2539c6`, SHA-256 `fe27d0be...cb80`) went to freeze review round 1. GPT reported MATERIAL 0 and
  ADVISORY 3; Opus reported MATERIAL 2 and ADVISORY 7. The reports are under `coord/reports/m5_step4/` in the main
  checkout, untracked.
  - OPUS-S4F-M1: the long-only Sharpe omitted the risk-free rate, which favors the lower-volatility book.
  - OPUS-S4F-M2: rule R1 used active risk, so it was not step 2's rule.
  - No step 4 code or result existed, so revision 2 repairs both in the same file.

Decision:

- Amendment 4 revision 2 (`docs/preregistrations/m5_trial_family_v1_amendment_4.json`, SHA-256
  `c2b1f8de...c617`, committed alone in `bddbf02` before any step 4 code, sleeve, return, or rule weight) freezes
  step 4.
  - It pins v1 and amendments 1 to 3 by SHA-256.
  - It pins `real_v2` by its id and the SHA-256 of its manifest, inventory, discovery inputs, seal carry, build
    manifest, interval CSV, interval results, and security master.
  - The seal guard is `_segment_calendar` (`seal_bracket_computation_forbidden`) plus the seal carry check
    (`holdout_overlap_refused`).
- Decision outcomes:
  - Rule R1 stays the point-in-time baseline only if it meets all 8 step 2 conditions against R0 on point-in-time
    books; otherwise R0 becomes the baseline.
  - R2 continues, labeled "no evidence of state timing", only if it meets all 8 against rule R1, and against R0
    too when R0 is the baseline; otherwise the timing line closes.
  - S4 q-values and the fragility label are reported beside the outcomes and do not change them.
- Coordinator technical defaults, one line each. None loosens R1, R2, R4, R6, R8, or R9.
  - `real_v2` only; the six Family A signals are the price classes, in four JKP themes (Momentum: MOM_12_1,
    HIGH_52W; Short-Term Reversal: REV_1M; Low Risk: LOW_VOL_252, LOW_BETA_252; Size: AMIHUD_ILLIQ_63).
  - The class return is rule R1 within the class, descriptive only.
  - Sleeves: top quintile, ceil(0.2 n) names, equal weight, month-end rebalance on the engine's after-close
    contract, `halt_gap_return_v1`, one engine call per segment from cash.
  - Monthly sleeve returns compound daily net returns; the first month includes the initial purchase cost; the
    partial month 2026-08 is excluded.
  - Segments load without `read_engine_events` and with empty event frames; nothing under `terminal/` is read.
  - An empty sleeve target refuses the run.
  - Unpriced member-days are counted over each segment's reset-to-last-book rows, against every interval in the
    pinned interval results. The buckets `unresolved_no_permanent_id` and `unknown` are included, and a total that
    does not reconcile refuses. The share is printed beside every excess figure.
  - Stock costs 1 + 4 bp and 2 + 8 bp; switch costs 20 and 50 bp on drift-adjusted class turnover, paired as
    (1 + 4, 20) and (2 + 8, 50); no zero-cost sleeve; no borrow cost, since nothing is shorted.
  - Rule R1 sigma is the ddof-1 standard deviation of the sleeve's own daily net return, over the 126 trading
    days ending on the last trading day of month t-2. This is step 2's rule with a daily window. No active-risk
    variant is run.
  - The long-only Sharpe is 12 x mean(r_net - RF) / (sqrt(12) x sd(r_net)), with the French FF3 monthly RF. The
    public long-short counterparts keep the v1 Sharpe.
  - The class layer starts at the first month with a full sigma window; R0, rule R1, and R2 start together from
    cash.
  - R2 uses the step 3 multipliers unchanged, from the pinned public inputs.
  - Rule comparisons end at 2025-12, the last month of the public counterpart, so every comparison and its
    counterpart use the same months. The halves are the two segments, each a separate run.
  - Survival counts the 8 conditions (1e-12 tolerance) beside the same conditions on the public jkp_factors_153
    books over the same months, with the margin ratio when the public margin is positive.
  - Transmission compares each sleeve with its matched JKP characteristic and each class with its amendment 3
    class return.
  - S4.R1 and S4.R2 use `rule_test` on the pooled comparison months at the primary cost case, in the primary run.
    The pooled HAC treats the segment boundary as adjacent.
  - The BY family is 480: 2 observed tests, 6 public rule-test slots (S2 x3, S3.R2 to S3.R4), and 472 Family A
    statistics from the committed M4.7 v1 and v2 records at p = 1, with HAC and iid counted separately. The
    static-cohort record holds no Family A test statistic.
  - No random-date null.
  - Residual held stops settle at -100 percent in every sleeve and in the equal-weight benchmark. This includes
    seal-gap stops, which are counted separately.
  - A last-close rerun is reported beside the primary run. It reports S4 means and signs, with no p-value. A sign
    change in any S4 mean, closure margin, or outcome labels the result fragile.
  - With R0 as the baseline, R2 must also meet the 8 conditions against R0.
  - Affected events are reported per book as a count and as the sum and maximum of incoming weights, taken at the
    close before the stop. At rule level, sleeve shares drift from the month's targets, and each event counts
    once, with sleeve-event incidences beside it.
  - Metrics come from the step 2 `performance` function on monthly net returns, with the long-only Sharpe in place
    of its Sharpe.

Rationale: every definition is fixed before any step 4 number exists, so the step 4 result cannot shape its own
test. Where the design note was silent, the stricter reading was chosen. The -100 percent default is a coordinator
scope default; curating the 68 terminal candidates remains an owner option.

## 2026-09-29 - Owner Decisions O-5 and O-9 for Milestone 5 Step 4, and Coordinator Scope Defaults

Context:

- Step 4 (the bridge) forms long-only top-quintile point-in-time S&P 500 books on the local snapshots. The design
  note (`coord/reports/m5_step4/design_note.md`, untracked) lists the owner decisions it needs.

Decision:

- **O-5 (owner):** step 4 may read `real_v1` and `real_v2` locally. The scope is recorded in the 2026-09-29 entry of
  `docs/engineering_log.md`.
- **O-9 (owner):** premise VP-2 is re-ratified under `DIAGNOSTIC_ONLY` for Milestone 5 step 4.
  - VP-2 is the premise that the vendor's adjusted close applies each declared distribution.
  - The M4.8 census measured `S_D > 0.05` on 22.5 percent of eligible member-days, which expired O-8.
  - The step 4 report header discloses VP-2 and the measured shares.
- **Coordinator scope defaults.** None of these loosens R1, R2, R4, R6, R8, or R9.
  - Step 4 writes nothing inside either snapshot and accepts no terminal evidence.
  - A held disappearance without accepted evidence settles at the R4 adverse default, -100 percent for a long
    position. The equal-weight benchmark gets the same events.
  - A rerun that settles every such disappearance at the last close is also reported. A sign flip between the two
    runs labels the result fragile.
  - The M4.8 seal window stays unaccessed.
  - The first run uses price classes only.
  - The factor-ETF blend and the SEC as-filed classes (step 4b) wait. SEC EDGAR retrieval needs its own owner
    decision, both on the R11 source list and on the User-Agent contact.

## 2026-09-28 - Milestone 5 Step 3 Reporting Conventions (Coordinator Technical Defaults)

Context:

- Freeze review round 2 on amendment 3 revision 2 (`f9c1152`) reported `MATERIAL: 0` from both seats. Its
  advisories GPT-R2-A2 and S3O2-A1 note that no confidence interval is specified for the decision metric that
  `docs/north_star.md` asks for. S3O2-A3 notes that the post-publication R2 is re-estimated on subset history.
  S3O2-A4 lists definitions that no required test checks.

Decision (set before any step 3 code or result; these add report outputs and tests and change no rule, test,
threshold, or decision in amendment 3):

- For S3.R2, S3.R3, and S3.R4, report a two-sided 95% pointwise interval for the mean of d_t (rule net minus R1 net
  at 20 bp, jkp_factors_153, the full evaluated window): mean ± 1.959964 × se.
  - se = sqrt(LRV / n), where LRV is `newey_west_long_run_variance(d, lags)` and `lags` is the lag that
    `return_test_statistics` uses. A test checks that mean / se equals its `hac_statistic`.
  - Units: percent per month, and that value × 12 per year.
  - The interval is typed missing when that test is not `ok`.
  - It is pointwise and not adjusted for selection or multiplicity.
- The post-publication comparison is reported as "R2 re-estimated on post-publication factor-months only, with
  history from the subset label span start". Beside it, report R2-sub's mean lambda per state and half, and the
  share of subset months in which R2-sub weights differ from R1-sub weights.
- The runner adds the S3O2-A4 tests below to amendment 3's required tests:
  - the three labels at their boundaries: a trailing market return of exactly 0 is down, the volatility median
    expands through month t-2, and the credit value at t-3 is compared with the median of months t-122 to t-3;
  - R4's rank scaling, including average ranks and 0 when n = 1, and its 83-column layout;
  - the class return as R1 within the class;
  - the subset R2's span start and its subset-only histories.
- Open advisories go to the backlog: GPT-R2-A1 (historical search completeness is not verifiable) and S3O2-A2,
  A5, and A6 (wording).

Rationale: an interval makes the size of the difference readable next to its test. The other items make the
report say what was tested and test definitions that the future-perturbation test cannot check.

## 2026-09-28 - Milestone 5 Step 3 Trial Amendment 3 (Coordinator Technical Defaults)

Context:

- v1 leaves the R2, R3, and R4 parameters and the step 3 test details to "the v2 amendment", which must be
  committed before any step 3 result. Review advisories A2-A2 (prior-exposure multiplicity) and A2R2-A1 (R4
  coverage) wait on it.
- Review round 1 of revision 1 (`cd1d578`, SHA-256 `b5c67cf1...0c62`) found one MATERIAL finding (GPT-R1-M1: the
  R2 timing claim did not need the result to hold after publication) and 12 ADVISORY findings. No step 3 code or
  result existed, so revision 2 repairs them in the same file.

Decisions:

- Amendment 3 revision 2 (`docs/preregistrations/m5_trial_family_v1_amendment_3.json`, SHA-256
  `c59f69c8...bfbb`, committed alone in `f9c1152` before any step 3 code or result) is that amendment. It pins v1
  and amendments 1 and 2 by SHA-256 and lists 26 technical defaults, one line each. The main ones:
  - R2 tilts each theme by 1 + 0.5 x the mean over the three states of sign(past cell mean) x E / (E + 10), where
    E is the cell's past episode count. R3 tilts by 1 + 0.5 x sign(trailing 12-month return). R4 fits one ridge
    per return year (alpha = training rows; 83 trait, state, and trait x state columns; no cross-sectional
    standardization), and its forecast ranks tilt R1 by factors in [0.5, 1.5]. Step 3 runs on `jkp_factors_153`
    only.
  - A2R2-A1: a factor-month without an R4 forecast keeps its exact R1 weight, including the 11 factors without a
    publication year, so every comparison uses the R1 set.
  - A2-A2: the S3 BY family counts 3 rule tests, 39 class x state tests, and 1005 prior-exposure slots at p = 1
    (family size 1047). The slots are an exact count of every test statistic on a step 3 hypothesis in the
    retained scratch scripts, full window and halves, with 32 exclusions each given a reason. A random-date null
    of 999 circular label shifts (seed 20260928) is reported beside R2 and the state tests.
  - The closure rule applies the 8 step 2 conditions to R2 against R1 on `jkp_factors_153`, with differences
    below 1e-12 counted as equal. If R2 fails any of them in either half, the return-timing line closes and R1
    alone goes to step 4.
  - A claim that states improve on the baseline needs 6 conditions: the 8 closure conditions, a positive
    full-window mean difference, S3.R2 q <= 0.05, a defined random-date p <= 0.05, R2 not losing to R1 on the
    post-publication subset at 20 and 50 bp (Sharpe, drawdown, and a positive mean difference; undefined or empty
    fails), and all three states with at least 10 episodes per cell and half. An open line without the claim
    carries R2 to step 4 as "no evidence of state timing".
- Round 1 repairs, by finding:
  - GPT-R1-M1: the post-publication condition above, with a predicate test in which every full-set condition
    passes and the post-publication condition fails.
  - GPT-R1-A1 and S3O-A7: one label span for the observed R2 and every shifted rebuild; a missing label inside
    it refuses; an undefined draw counts as an exceedance; an undefined observed statistic cannot survive; a
    lookback class-month with a missing member return is typed missing and counted; an empty class in an
    evaluated month refuses.
  - GPT-R1-A2 and S3O-A1: the exact recount above replaces the "smallest consistent count" of 617.
  - GPT-R1-A3: the 10-episode rule applies to each of R2's states; R2 credits no single state.
  - S3O-A2: the momentum-after-a-falling-market row is listed as seen; state-effect tests are re-examinations
    that support no confirmatory claim, and the report marks the six pre-seen cells.
  - S3O-A4: the 1e-12 tie tolerance; the report gives the 8 margins and the share of months where R2 differs
    from R1.
  - S3O-A5: surviving cells stay surviving descriptive cells whether the line is open or closed and may be
    named as step 5 candidates, which step 5 declares and tests on its own.
  - S3O-A6: two hindsight limitations (full-sample JKP clusters; early Compustat backfill in R2 lookback).
  - S3O-A8: the two roadmap backlog rows are updated.
  - S3O-A9: R2 and R3 no longer run on `jkp_themes_13` and `french_7`, and R3 and R4 no longer run on the
    post-publication subset; R3 stays because v1 declares it.
- Advisories kept open, one line each:
  - GPT-R1-A2 residual: 1005 counts the retained final scripts only; earlier script edits and interactive work
    left no record, so the historical search stays a stated limitation.
  - S3O-A3: with 19 down-trend episodes seen for 1972-2025, the per-half rule will very likely make the
    market_trend tests and R2's timing claim description only; a full-window 10-episode rule is an owner choice
    that must be made before any step 3 result.

Rationale:

- Counting every retained prior test keeps R9 intact without a narrower convention to defend. Keeping the R1
  weight where R4 has no forecast stops the R4 comparison from measuring the publication effect. The
  post-publication and episode conditions apply the North Star decision rule to the pooled R2 result. No choice
  used a step 3 result; the amendment lists every result seen before it.

Consequences:

- The amendment settles the backlog rows for A2-A2 and A2R2-A1. The step 3 runner must verify all four trial-file
  pins and pass the amendment's 17 required tests, including the R4 weight-level publication-year test and the
  R2 timing-claim predicate test.

## 2026-09-28 - Milestone 5 Trial Amendments 1 and 2 (Coordinator Technical Defaults)

Context:

- The v1 trial family (`docs/preregistrations/m5_trial_family_v1.json`, SHA-256 `a99a862c...417a`) lets a v2
  amendment fill only the open parameters of R2 to R4 and the step 3 test details. Both amendments below change
  other sections, so each is a coordinator technical default under the AGENTS.md Owner Process Constraints. Neither
  loosens R1, R2, R4, R6, R8, or R9. Amendment 1 said it was logged here; this entry supplies that record (review
  advisories A1-M5-04 and A2-A1).

Decisions:

1. **Amendment 1** (`m5_trial_family_v1_amendment_1.json`, SHA-256 `b3992b32...0751`, committed alone in
   `f77b4ed`): the descriptive post-publication split starts at its first evaluated month with a non-empty subset,
   because no JKP factor has a publication year before 1973 and the v1 empty-set refusal left the split without
   metrics. Leading empty months are counted; a later empty month still refuses. Results seen before it: every
   R0, R1, S2, decision, market, and volatility-forecast result of the first two step 2 attempts and the
   post-publication counts; no post-publication metric. It carries no test and no decision.
2. **Amendment 2** (`m5_trial_family_v1_amendment_2.json`, SHA-256 `59461b15...72f1`, committed alone in
   `261d84f` before any result under it) repairs review round 1 MATERIAL findings:
   - A1-M5-01 (AUDIT seat): v1 formed month t's weights from returns through month t-1 and earned month t from
     that same close. Now the signal month is t-2, the target executes at the month t-1 close, and it first earns
     month t; every v1 window ending at t-1 ends at t-2 (credit spread at t-3). This is
     `after_close_signal_next_observed_close_v1` on the monthly grid with a lag of one observed row.
   - Month-t return availability is no longer a set condition, since it is not known at the new decision time; a
     missing held return refuses instead of reallocating (advisories A1-M5-02, A2-A4). A bad-data code in the
     36-month window excludes the factor; an absent month counts only against the 24 (advisory A1-M5-03, R6).
   - A2-M1 (AUDIT_2 seat): `years_since_publication` is the signal month's year minus the publication year,
     typed missing until positive, and such factor-months leave R4's inputs. The post-publication split uses the
     same definition.
   - Results seen before it: all step 2 results of attempts 1 to 4 under the v1 timing, including the
     post-publication metrics, and both seats' round 1 diagnostics (the AUDIT seat's one-month-delay sensitivity
     and the AUDIT_2 seat's pre- versus post-publication return gap).

Rationale:

- The v1 timing let a signal known only after a close trade at that close (R1). The trait leaked which factors
  would be published later (R1). Neither repair uses any return to choose a rule.

Consequences:

- The amendment 2 rerun (attempt `20260929T003920038139Z`, outputs in `c0ce46d`) keeps the decision R1 (8 of 8);
  it equals the AUDIT seat's sensitivity. The v1-timing results stay visible as prior exposure (R9).
- Step 3 inherits the t-2 signal month and the corrected trait; R4's weight-level publication-year test becomes a
  required step 3 test.

Follow-up:

- The v2 amendment for step 3 states whether the prior-exposure variants (612 factor x state pairs, T1, T3)
  count in the step 3 BY family (review advisory A2-A2).

## 2026-09-28 - Controller Review Rules Follow The Materiality Test And The Owner's Two-Round Limit

Context:

- `docs/codex_long_running_controller.md` still carried review steps from an
  older coordination standard: stop after two P1/P2 reviews, then a
  review-loop analysis role and a fixer route. The live standard has neither
  role; it classifies each finding as `MATERIAL` or `ADVISORY`, and only
  `MATERIAL` findings block. The controller blocked merge on any actionable
  finding. PR #263 proposed the fix on 2026-09-26 and went stale.

Decision:

- Every finding is `MATERIAL` or `ADVISORY` under the materiality test in
  `coordinator.md` section 3; P1 and P2 labels only rank review attention.
- Review rounds follow the owner process constraints in `AGENTS.md` (at most
  two per card). When the last allowed round still reports `MATERIAL`
  findings, the EXPERT step and residual-risk disposition of
  `coordinator.md` section 3.3 apply.
- A PR is merge-eligible only with `MATERIAL: 0`, or an explicit merge
  disposition for each owner-accepted `MATERIAL` finding.
- The controller names the standard without a version number, so the text
  stays correct when the standard is updated.

Consequences:

- A test pins the current rules and the absence of the retired ones.

---

## 2026-09-28 - Owner Decisions: North Star v2, M4.8 Pause After Stage D, Public Factor Data, SEC Fundamentals, Process Constraints

Context:

- The owner judged progress too slow, asked for an audit of North Star drift, and asked to collect as many factors
  as possible, keep the structure simple, and define Milestone 5 as "under which conditions which factor gives
  higher returns or smaller drawdowns".
- The coordinator's progress assessment (`coord/reports/progress_assessment_opus.md`) and the six-lens audit with
  red-team and fact-check passes (`coord/reports/north_star_speed_audit_opus.md`) found: the edge thesis, the 0.02
  MDE kill criterion, the tax hurdle, and the execution-platform Milestone 5 came from the 2026-09-23 agent audit
  package; the kill criterion needs 286 to 2,508 monthly IC observations on S&P 500 data, so every null routed to
  `extend_first`; Track A used 117 of 131 calendar days with zero real-data results.

Decisions (owner, 2026-09-28, answered in session):

1. **M4.8 pauses after Stage D.** PR #275 merged at `9dee2df2267c4cfb4b587783a8447d2cbae3d88a` (squash, bound to
   the reviewed head `d1bf6a32e8c57e51e04375f58df5e0882b276d62`; Seat 1 GPT via Codex MATERIAL 0 / ADVISORY 3,
   Seat 2 Opus 5.5 MATERIAL 0 / ADVISORY 6; CI green). Stages E–H stop. Resume point: Stage E on `real_v2`. The nine
   Stage D advisories (A1-D-ADV-01..03, A2-D-ADV-1..6) and the M-2 disposition carry to the resume point.
2. **Public factor data authorized.** French, AQR, JKP, Open Source Asset Pricing, Hou–Xue–Zhang, and FRED series
   may be downloaded and interpreted. Raw third-party files stay out of the public repository; commits carry a
   manifest with URL, retrieval date, SHA-256, and row count.
3. **Fundamentals from SEC as-filed data only.** No EODHD fundamentals call. The EODHD subscription has expired
   and is not renewed now; the local snapshots `real_v1` and `real_v2` remain the stock-level data under the
   recorded written terms (`local_retention: PERMITTED`, `deletion_obligation: NONE`,
   `docs/stage1_accepted_public_record_v1.json`). A forward-price source is chosen at the forward-observation step;
   free sources are tried first.
4. **North Star v2 and process constraints adopted**, effective when the owner confirms this PR: the new
   `docs/north_star.md`, chosen by the owner after the vision assessment
   (`coord/reports/north_star_vision_assessment_opus.md`): a factor-class allocator that learns which classes of
   factors earn more or lose less in real-time market conditions, allocates monthly into a long-only large-cap
   portfolio, puts risk first, treats "all classes, balanced by risk" as a valid result, and admits new factors only
   through a counted search that beats random mining; Milestone 5 = factor-class allocator, Milestone 6 = separately
   authorized execution; AGENTS.md R1, R4, R6, R7, R8, R9, R10, R11, R12 amended; the Owner Process Constraints section (two
   cross-family seats only for real-data inference code and trial-family freezes, at most two review rounds,
   wording findings advisory, design notes instead of binding plans, logged coordinator defaults that never loosen
   R1, R2, R4, R6, R8, or R9); ablation once per milestone.
5. **English only.** Everything written to the repository, to GitHub (PR titles and bodies, comments, commit
   messages), and to any report is English; Chinese characters are prohibited there. A governance test enforces it
   for tracked files. Live chat with the owner may use the owner's language. PR titles, bodies, comments, and commit messages
   carry no AI attribution line (no "Generated with" tool line, no `Co-Authored-By` trailer naming an AI model);
   the line was removed from nine older PR bodies. Other wording, bot comments, repository files, merged commit
   history, and GitHub's contributor list stay unchanged.

Coordinator records carried by this entry:

- Coordination Standard V8.9 §3.3 acceptance of M4.8 plan Revision 4 (SHA-256
  `816a3bea1b7245accdc4b539a5c43c9558d2115e1e456366a056b89c35bbd74c`, EXPERT author Claude Code Opus 5.5 xhigh,
  history §16) and of the Stage C c4 candidate merged as PR #274 (`1c56939`); acceptor: the coordinator (Claude
  Code, Opus 5.5), recorded after the fact. Execution scope: M4.8 Stages C and D.

Consequences:

- R4 replaces "refuse the run" with the side-aware adverse default. The engines still refuse an unevidenced held
  disappearance until the default is implemented in Milestone 5; that refusal stays conservative.
- The support v2 owner risk acceptance stays in force for exploratory runs and is disclosed in their headers.
- The seal window `[2019-07-31, 2020-07-31)` stays unaccessed; spending it is an open owner item for the first
  stock-level confirmation design.

Follow-up:

- Milestone 5 step 1 (trial file and catalog) and step 2 (risk-balanced baseline on public data) start after this
  PR.

## 2026-09-28 - M4.8 Stage D: real_v2 Built Offline Under Partition Rule v2; Curated Identity Boundary Rule

Context:

- Plan `m4_8_binding_plan` Revision 4 (`816a3bea…bd74c`) section 7.3 Stage D: build `real_v2` from the local
  acquisitions, write the seal carry record and verify real_v1's prospective seal, partition under rule v2, and run
  calendar, universe build with segment-local validation, and the terminal template. Card
  `coord/v8_review_20260923/card_m4_8d_real_v2.md` (`GENERAL_EXEC`); the Stage C record (PR #274) passed G1 at
  `D0_pre` 2014-04-30.
- Stage C review finding A2-C-ADV-2 asked Stage D to give the 2017-04-03 share-exchange successor two permanent IDs
  (or a typed refusal), because its snapshot code files the predecessor's bars and no carried identity rule
  separates them.

Decision:

- `real_v2` is built offline from the same local acquisitions as real_v1; no retrieval grant beyond O48-1(a) was
  used and no network request was made. The seal carry record binds `[2019-07-31, 2020-07-31)` from the seal v1
  bytes, with all three bound hashes and real_v1's prospective seal file verified. real_v1 stays byte-identical.
- New rule `curated_identity_boundary_v1` implements the permanent-security clause of rule M-5a(c) ("so no code
  carries two permanent securities") for the successor code: a private file `membership/identity_boundaries.csv`
  (one row per boundary: code, first bar date of the later security, the M-3 source fields, and the supplement row
  it pairs with) starts a new permanent ID at that bar. An interval across the boundary refuses as
  `identity_boundary_spanned`; a member piece ending at the boundary is a disappearance that needs terminal
  evidence; an invalid row refuses the build. The file's hash enters `discovery_inputs_sha256`.
- One boundary is recorded (2017-04-03, sourced to the S&P DJI release of 2017-03-28). Two IDs result; the
  predecessor piece holds no membership interval.

Rationale:

- A typed refusal of the whole code would also drop the successor's post-segment membership. Two IDs keep each
  security's own bars and restart the successor's feature warm-up at its first bar, so no feature reads the
  predecessor's prices (R3, PIT-005).
- Treating the pieces as SL-5 siblings would attach one membership interval to both securities and end the
  predecessor piece without a terminal event, dropping the R4 obligation; the ablation keeps the refusal.

Follow-up:

- Review: the boundary file is a new private input format added on `GENERAL_EXEC`; the CRITICAL review decides
  whether plan section 2.3 should state it by revision.
- Stage E: curate the 68 in-scope terminal candidates. Stage F: census v3 on real_v2, including the pre-side panel
  shortfall (111 of 448 members at `D0_pre` without a pre-side panel) and the owner's M-2 disposition, which Stage
  D leaves open.

---

## 2026-09-27 - M4.8 Stage C: O48-1(a) Retrieval, Plan Revision 4 (Rules M-5a and M-9), and Gate G1 Record (attempt c4)

Context:

- Plan `m4_8_binding_plan` Revision 3 (`bd1bf587…bf3e`) section 7.3 gates Stage D on G1. The Stage C card
  (`coord/v8_review_20260923/card_m4_8c_membership.md`, task `m4_8c-membership-a1`) states owner directive O48-1(a):
  public-document retrieval (SEC EDGAR, S&P DJI announcements and factsheets, public changes lists with
  corroboration). O48-1(b) (EODHD retrieval) is not granted.
- Review history: Round 1 on c1 (`c150136`) found the pass rested on the unstated code convention C-1
  (AUDIT1-M48C-M01). Round 2 on c2 (`548175b`) found a 2015 S&P DJI release that c2 had missed (A2R2-M01). Round 3
  on c3 (`054ceaa`) kept A2R2-M01 open at Seat 1 (`MATERIAL: 1`): seven vendor-only placeholder events sat outside
  the change log, and typed as sourceless rows they block G1 (start 2019-03-31, 3 IC months). Seat 2
  (`MATERIAL: 0`) read the exclusion as sound and asked for the rule in the plan (A2R3-ADV-2) and for A1's adoption
  by an eligible plan author (A2R3-ADV-1). Under Coordination Standard V8.9 §3.3 the coordinator dispatched EXPERT
  (card `coord/v8_review_20260923/card_expert_m48c_c4.md`).

Decision:

- Plan Revision 4 (history §16; SHA-256 `816a3bea1b7245accdc4b539a5c43c9558d2115e1e456366a056b89c35bbd74c`), authored
  on `EXPERT` (`may_author_plan = true`), adopts amendment A1 word for word: rule M-5a (a renamed issuer keeps its
  own bars under the later snapshot code; a ticker reused by another permanent security takes `<Code>_old` and stays
  unpriced; a predecessor across a share exchange keeps its as-traded code and stays unpriced) and the change-row
  source rule. The `code` column now reads "the code rule M-5a assigns". The route deviation of c3 (A1 written on
  `GENERAL_EXEC`; the c3 card's `AUTHORITY.md` citation, which holds no plan-amendment grant) is recorded in
  history §16.1.
- Revision 4 adds rule M-9. The change log holds the index changes an independent public record establishes (an
  S&P DJI announcement, an SEC filing, or a corroborated public changes list, with dates derivable through a
  published S&P DJI policy). The census classifies every in-span endpoint of a retained dated vendor entry once:
  `change_matched`, `discrepancy` (an M-2 line), or `vendor_only`. Vendor-only endpoints stay outside R3-2a and
  M-8, their entries stay retained, the census publishes the counts, and R3-10 counts each vendor-only entry active
  in the pre segment.
- Disposition of the seven events: the 2019 spin-off addition is now sourced (the parent issuer's 2019-02-11
  announcement with the S&P DJI release and the 2015-09-14 zero-price policy) and matches its vendor date; the other
  six events (three entries) are vendor-only under M-9.
- Stage C used O48-1(a) only; no EODHD request was made. Curated files stay under `<private_data_root>`.
- Gate G1 record on `real_v1` metadata and the c4 curated files: `passed`. `coverage_start_pre` = `D0_pre` =
  2014-04-30, `r_pre_last` 2019-05-31, `pre_ic_months` 62, unresolved-change fraction 4 / 303 = 0.0132 (cap 0.02),
  R3-2c 5,738 / 650,629 = 0.0088 (cap 0.01), seven required anchors pass on the 500-line floor. Vendor endpoints in
  the span: 383 = 368 change-matched + 9 discrepancy + 6 vendor-only. Curated file SHA-256: supplement
  `37a86476…3927e5` (unchanged), changes `3fe432cf…9a799a` (402 rows), counts `bc78c556…4ffb280` (unchanged);
  public census `c40ad8aa…3f6e`.
- M-2 applied as written: 10 vendor start dates that both public lists contradict stay in force as unadjudicated
  discrepancies. All 17 published factsheet counts equal `n_cur` plus these lines. With every anchor modelled that
  way, the start moves to 2016-10-31 with 32 IC months and G1 blocks, so the pass rests on the floor-anchor slack
  plan section 10 states.

Rationale:

- R3-2a measures completeness against the independent record: its numerator counts independent-record changes the
  membership fails to match. A vendor-only endpoint is the converse relation, and M-8 would charge it as a missing
  member the universe already holds. Its risk is over-inclusion, which the anchors bound, the census counts, and
  R3-10 records as a caveat. The computed classes keep completeness machine-checked: removing the 42 sourced
  placeholder events moves the vendor-only count from 6 to 48.
- The rule was stated with its quantified contrary reading on record (R9): typed as sourceless rows, the six
  vendor-only endpoints give R3-2a 10 / 309 at 2014-04-30 and a 2018-11-30 start with 7 IC months, blocked. The
  three vendor-only entries hold 14 pre-segment membership rows and enter no book (no reset or signal row).
- The pass needs M-5a(a): with the three renamed issuers read as traded, R3-2c is 0.0104 and G1 blocks. M-5a(a)
  prices a member with its own bars; M-5a(b) and (c) fail closed where a code would join two permanent securities.

Follow-up:

- Coordinator: record the acceptance of Revision 4 and of the c4 candidate under §3.3; record the disposition of
  A2R2-M01 for the PR merge (section 8).
- Owner: the M-2 disposition (accept as the R3-10 caveat, revise M-2 by plan revision, or seek primary sources);
  the user-agent disclosure (engineering log); optionally a coverage-rule change so that more unresolved changes
  cannot shorten the evaluated segment into a pass (A2R2-ADV-2).
- Stage D: identity split at the 2017-04-03 share exchange (A2-C-ADV-2); the census v3 R3-10 input includes the
  M-9 term.

---

## 2026-09-26 - Owner Risk Acceptance: Support v2 Look-Ahead Exclusion (AUDIT1-M01, ADV-1)

Context:

- `support_exclusions` (`research/m4_7_common_support.py:81-110`) sets `X(r - 1, i)` from bar
  availability in `[r, h(r)]`; books and the equal-weight benchmark read `E = S_mask & ~X`.
  On real_v1 this affects 27 of 26,237 signal-eligible cells (26 unresolved delisting, 1 missing bar).
  Signals read `S_mask`.
- Audit Seat 1 raised AUDIT1-M01 (MATERIAL: 1) on the retrospective lookahead; Audit Seat 2 raised
  ADV-1 (ADVISORY, bounded IC impact <= 0.003, gate invariant). Independent evaluation by Claude
  Opus 5.5 High (`coord/reports/v8_review_20260923/breadth_fix/eval_option1_vs_option2_opus.md`)
  recommended Option 1: Owner risk acceptance at DIAGNOSTIC_ONLY ceiling with bounded scope and
  expiry, noting that Option 2 as worded conflicts with R4 (no default last-price or zero-payoff exit).
- ADV-2 noted that the structural contract change was directed by the owner correction card
  (`coord/v8_review_20260923/card_pit_breadth_support_fix.md`), which supersedes the M4.7 binding
  plan's v1 support sections (`coord/plans/m4_7_binding_plan.md:1956, :3069`).

Decision:

- The owner accepts this R1 deviation for candidate `4ab7d0e88a3db63384f9ba24d118b51cb94c0312` (PR #271),
  registration v2 (`4a6f8b5a0478bd70e90cd84e440a389898630f2e156eb0488c96ca0e8923e7dc`), snapshot real_v1,
  at the `DIAGNOSTIC_ONLY` ceiling.
- Accepted scope: covers IC, book, benchmark, and CPCV diagnostics of registration v2. It strictly excludes
  any ranking, selection, promotion, or profitability claim.
- Expiry: the freeze of the next registration. No later registration may bind support contract
  `asset_level_holding_period_support_exclusion_v1`.
- Revisit condition: immediately, if any rerun under this contract produces a Family A BY survivor
  (because `net_ls` then becomes a gate input), or if the excluded fraction exceeds 0.005.
- Rationale: IC labels for the 26 disappearance cells are missing under any causal design, so the gate
  inputs are unchanged; a causal book without terminal evidence either stops as Class I, refuses windows,
  or needs a default exit prohibited by R4.

---

## 2026-09-26 - M4.7 Support v2: Asset-Level Holding-Period Isolation and Registration v2 Gate Record

Context:

- The owner identified the v1 global common-support requirement as over-strict: one asset's missing bar or
  unevidenced delisting opened a market-wide gap window and dropped short segments for every asset, leaving
  32 IC months of 61 scheduled resets on real_v1 (476 excluded rows, fraction 0.3842).
- Task `v8-exec-breadth-support-fix-a1` (GENERAL_EXEC, Coordination Standard V8.7) directed asset-level
  isolation under R1-R12.

Decision:

- Support contract `asset_level_holding_period_support_exclusion_v1` replaces
  `common_support_segments_open_terminal_holdings_v3`. A missing bar or unevidenced disappearance excludes only
  the affected asset from the reset whose holding period needs that bar. Evaluation runs as one continuous
  window `[D0, D_last]`. R-CENSUS-2 reads the asset-level excluded fraction (support-excluded cells over
  signal-eligible cells, cap 0.05); the gap-window count no longer exists.
- Registration v2 (`docs/preregistrations/m4_7_sp500_pit_rerun_v2.json`, SHA-256 `4a6f8b5a…e7dc`) was frozen
  from census v2 before the rerun. Families, statistics, timing, terminal, books, benchmarks, and gate are
  unchanged; costs, objective, and the O-3 choice (`proceed_as_registered`) carry over from v1. The seal window
  is unchanged. v1 artifacts stay byte-identical as history, and the v1 result stays the M4.7 milestone record.

Registration v2 Gate Inputs:

- Snapshot `real_v1`; support SHA-256 `21731a0f…e2f9`; census v2 JSON SHA-256 `8308828f…967e`;
  seal confirmation v2 `8e9e7b02…88ae`.
- |U| = 24; exclusion cells |X| = 27 of 26,237 signal-eligible cells (fraction 0.00103; 26 unresolved
  delisting, 1 missing bar); 61 evaluation resets; 60 IC months (2021-08-31 through 2026-07-31); evaluated
  breadth 424-433 names per reset (median 430).

Family A (6 factors, primary Rank IC, BY within family of 6):

| Factor | T_f | Mean IC | HAC p | BY q | Half 1 mean | Half 2 mean | Sign stable | MDE_f | MDE_single | LS mean daily net | LS HAC p |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `MOM_12_1` | 60 | 0.018768 | 0.328505 | 1.000000 | 0.026580 | 0.010956 | true | 0.072424 | 0.053812 | 0.000176 | 0.402787 |
| `HIGH_52W` | 60 | 0.009038 | 0.647710 | 1.000000 | 0.015539 | 0.002536 | true | 0.074575 | 0.055411 | 0.000033 | 0.877417 |
| `REV_1M` | 60 | -0.017389 | 0.336964 | 1.000000 | 0.002249 | -0.037027 | false | 0.068284 | 0.050736 | -0.000194 | 0.273938 |
| `LOW_VOL_252` | 60 | -0.006301 | 0.815250 | 1.000000 | 0.015164 | -0.027765 | false | 0.101671 | 0.075543 | -0.000240 | 0.331114 |
| `LOW_BETA_252` | 60 | -0.015966 | 0.641517 | 1.000000 | 0.014032 | -0.045964 | false | 0.129300 | 0.096072 | -0.000207 | 0.462934 |
| `AMIHUD_ILLIQ_63` | 60 | -0.013076 | 0.258819 | 1.000000 | -0.023956 | -0.002196 | false | 0.043663 | 0.032442 | -0.000113 | 0.324737 |

- Family B: 63 of 63 trials evaluated (v1: 55 evaluated, 8 invalid for insufficient IC months); zero positive
  BY rejections.
- CPCV PBO over 1,239 measured rows (v1: 763): `A_long_short` 0.2143, `A_excess`
  0.1714, `B_long_short` 0.4571, `B_excess` 0.3429.
- Gate: `power_status` `inadequate` (MDE_f 0.0437-0.1293 against the 0.02 floor); zero survivors; zero
  contrary rejections; `kill_reachable_projection` false. Outcome `extend_first`.

Consequences:

- Breadth and continuity are restored. Realized MDE_f falls by 5-30 percent per factor against v1 (median
  26 percent; square-root scaling from 32 to 60 IC months predicts 27 percent, and each factor's long-run
  variance moves with its new months), and stays 2.2-6.5 times the 0.02 floor. The program decision is unchanged:
  extend breadth or history under a new registration; the holdout stays sealed.
- Owner follow-up: confirm the carried-over O-3 choice for registration v2 and scope the next extension.

## 2026-09-26 - Milestone 4.7 Point-in-Time Rerun Decision Gate Record: extend_first

Context:

- Milestone 4.7 Phase M4.7c-1 executed the pre-registered point-in-time rerun on snapshot `real_v1` bound to preregistration `docs/preregistrations/m4_7_sp500_pit_rerun_v1.json` (SHA-256 `6ea218a6…1c9f`).
- Phase M4.7c-2 records the deterministic decision gate evaluation pursuant to Binding Implementation Plan Revision 11 (§6.9, §7.3 stage c-2).

Decision:

- **Decision Gate Outcome**: `extend_first`
- **Program Decision**: "Extend breadth or history under a new registration; the holdout stays sealed."
- **Holdout Disposition**: The 1-year holdout window `[2019-07-31, 2020-07-31)` under `SPY.US_eod_dates_v1` remains completely sealed and unaccessed.

Deterministic Gate Inputs & Registered Bindings:

- **Registration SHA-256**: `6ea218a6…1c9f`
- **Result Commit**: `a9c94dca59649dcb62af9b5d9fd65bde3400af45` (PR #269 merge)
- **Snapshot Manifest SHA-256**: `ffa76053…35c7` (`real_v1`)
- **Segments SHA-256**: `6b014b13…5933`
- **Census JSON SHA-256**: `608fd1b1…1c40`
- **Universe & Support Dimensions**: `|U| = 24`, `|G| = 1`, `|W| = 20`, excluded rows: 476, excluded fraction: 0.3842 (accepted shortfall <= 0.45); eligible unpriced member-day fraction: 0.3297 (accepted shortfall <= 0.40).
- **Cost Cases**: Primary: 1.0 bp transaction cost, 4.0 bps slippage; 2x sensitivity: 2.0 bps / 8.0 bps; zero-cost diagnostic: 0.0 bps / 0.0 bps.

Family A (6 factors, primary Rank IC, BY within family of 6):

| Factor | T_f | Mean IC | HAC p | BY q | Half 1 mean | Half 2 mean | Sign stable | MDE_f | MDE_single | LS mean daily net | LS HAC p |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `MOM_12_1` | 32 | 0.013459 | 0.566874 | 1.000000 | -0.015793 | 0.042712 | false | 0.088620 | 0.065846 | -0.000012 | 0.964200 |
| `HIGH_52W` | 32 | -0.010275 | 0.706731 | 1.000000 | -0.056098 | 0.035548 | false | 0.102970 | 0.076509 | -0.000177 | 0.497036 |
| `REV_1M` | 32 | 0.027931 | 0.144407 | 1.000000 | 0.031098 | 0.024764 | true | 0.072155 | 0.053612 | 0.000010 | 0.962834 |
| `LOW_VOL_252` | 32 | -0.010835 | 0.774981 | 1.000000 | -0.090620 | 0.068950 | false | 0.142912 | 0.106186 | -0.000165 | 0.591778 |
| `LOW_BETA_252` | 32 | -0.016749 | 0.711196 | 1.000000 | -0.101960 | 0.068462 | false | 0.170566 | 0.126734 | -0.000137 | 0.708933 |
| `AMIHUD_ILLIQ_63` | 32 | -0.008513 | 0.607242 | 1.000000 | 0.018212 | -0.035237 | false | 0.062444 | 0.046397 | -0.000006 | 0.966123 |

Family B & Combinatorial Purged Cross-Validation (CPCV):

- **Family B (63 trials)**: 55 evaluated, 8 invalid (`insufficient_ic_months` reaching 27–30 vs 32 minimum). Zero BY rejections (all BY $q = 1.0$). Family B provides exploratory context and changes no decision.
- **CPCV PBO & OOS Sharpe** (763 rows, 8 blocks, 4 test blocks, 70 splits, horizon 23, embargo 5):
  - `A_excess`: PBO 0.5857, mean OOS Sharpe -0.0190
  - `A_long_short`: PBO 0.6286, mean OOS Sharpe -0.0185
  - `B_excess`: PBO 0.5000, mean OOS Sharpe -0.0121
  - `B_long_short`: PBO 0.6143, mean OOS Sharpe -0.0440

Gate Flags & Evaluation Summary:

- `power_status`: `inadequate` (realized MDEs range from 0.0624 to 0.1706, exceeding the 0.02 adequate power floor).
- `contrary_rejections`: `[]` (zero contrary rejections).
- `kill_reachable_projection`: `false`.
- Rule 1 (`evaluation_incomplete`): Not matched (all 6 factors evaluated).
- Rule 2 (`proceed`): Not matched (zero BY rejections).
- Rule 3 (`survivor_without_confirmation`): Not matched (zero survivors).
- Rule 4 (`review_thesis`): Not matched (requires every $\text{MDE}_f \le 0.02$).
- Rule 5 (`extend_first`): Matched.

Consequences:

- Milestone 4.7 closes with the deterministic outcome `extend_first`.
- The holdout window remains sealed.
- No factor is promoted; the evidence ceiling remains `DIAGNOSTIC_ONLY`.
- Follow-up research requires expanding cross-sectional breadth or historical depth under a newly versioned preregistration.

---

## 2026-09-26 - Owner Decisions O-1, O-3 (Power Projection & Contrary Rejection), And O-6 For S&P 500 PIT Registration Freeze

Context:

- Milestone 4.7 Phase M4.7b-2 requires freezing `docs/preregistrations/m4_7_sp500_pit_rerun_v1.json` before discovery-window computation (§7.3 stage b-2).
- The committed coverage census on `real_v1` yields `kill_reachable_projection = false` (32 IC months, projected MDE 0.067 at central prior 0.10 against 0.02 floor).
- Under Plan §5.5 and §7.6, `kill_reachable_projection = false` triggers Owner Decision O-3 before stage b-2 with three options: (i) proceed as registered, (ii) change the North Star definition, or (iii) extend breadth or history before rerun.
- Under Plan §6.9, the owner confirms the contrary-rejection disposition A9 (`non_survivor_confirmed_by_owner_o3`).
- Under Plan §7.3 and §7.6, Owner Decisions O-1 (cost model) and O-6 (objective budgets) are answered or their registered defaults recorded.

Decision:

- **O-3 Power Branch**: The owner explicitly directs Option (i) (`proceed_as_registered`): proceed with the point-in-time rerun as registered without delaying for data expansion or modifying North Star criteria.
- **O-3 A9 Contrary-Rejection Confirmation**: The owner confirms the reading that finding no survivor under family-partitioned BY is classified as `non_survivor_confirmed_by_owner_o3`.
- **O-1 Costs (Registered Default Standing)**: Primary case: 1.0 bp transaction cost, 4.0 bps slippage per unit turnover; 2x sensitivity case: 2.0 bps transaction cost, 8.0 bps slippage; zero-cost diagnostic case: 0.0 bps / 0.0 bps.
- **O-6 Objective Budgets (Registered Default Standing)**: Target Information Ratio 0.30; tracking-error budget 0.08; maximum drawdown budgets: 0.60 for long-only relative to equal-weight benchmark, 0.30 for long-short. Treated as descriptive flags.

Consequences:

- The frozen registration file `docs/preregistrations/m4_7_sp500_pit_rerun_v1.json` (SHA-256 `6ea218a6…1c9f`) is confirmed with zero byte changes.
- The rerun proceeds under `DIAGNOSTIC_ONLY` on snapshot `real_v1`.

## 2026-09-26 - Owner Decisions O-7 (Coverage Shortfall Accepted) And O-8 (VP-2 Re-ratified Under DIAGNOSTIC_ONLY)

Context:

- The first Option A census on `real_v1` (JSON SHA-256 `5015a1d8…5c5c`, code
  `eb8c5a5`, entry below) was `blocked` on R-CENSUS-1 (6.92 in-band years
  against 7), R-CENSUS-2 (20 gap windows and excluded fraction 0.384 against 6
  and 0.05, from peeling 24 uncurated delistings), R-CENSUS-8 (32 IC months
  against 48), and R-CENSUS-9 (unpriced fraction 0.330 against 0.02), and set
  `vp2_revisit_required` (22.5 percent of eligible member-days with
  `S_D > 0.05`).
- The owner chose Option 1 for O-7 and O-8 under Owner Directives 1 (no data
  perfectionism), 2 (no over-engineering), and 3 (break serial dependencies).

Decision:

- **O-7:** the measured coverage shortfall on the local EODHD data is
  accepted as `ready_with_caveats:coverage_shortfall_accepted`, including
  R-CENSUS-1 at 6.92 in-band years against the declared 7 (the
  identity-adjusted continuous count starts 2019-09-30). Implementation:
  `SEAL_RULES[SEAL_RULE_OPTION_A]["accepted_shortfall"]` holds the accepted
  bounds (6.9 in-band years, 32 IC months, 25 gap windows, excluded fraction
  0.45, unpriced fraction 0.40). A miss of a registered threshold inside the
  bounds reads as the caveat; each rule keeps `passed = false` against its
  registered threshold, so the census shows both the miss and the acceptance.
  A value beyond a bound stays `blocked`.
- **O-8:** premise VP-2 is re-ratified under `DIAGNOSTIC_ONLY` for the M4.7
  rerun, including the 22.5 percent of eligible member-days with
  `S_D > 0.05`. The runner registers `o8_disposition =
  re_ratified_diagnostic_only`.
- **Runner alignment for b-2 and c-1:** `MIN_IC_MONTHS = 32`,
  `MIN_HALF_MONTHS = 16` (sign stability `min_16_months_each`),
  `calendar_source = SPY.US_eod_dates_v1`, and registered support caps of 25
  gap windows and excluded fraction 0.45. `bind_snapshot` refuses
  `registration_invalid` when the registered calendar source differs from the
  snapshot seal.

Result (census JSON SHA-256 `608fd1b1…1c40`, code `9fd7734`):

- Readiness `ready_with_caveats:coverage_shortfall_accepted,holdout_breadth_after_identity`;
  every measured value equals the blocked census.
- Seal confirmed SHA-256 `b7f9380f…f506`, confirmation `caveat`; the
  prospective seal `93ce6e5a…9882` is unchanged.

Consequences and limitations:

- These bounds were set after the first census measured the shortfall; the
  blocked census stays in history at commit `cfcbb91`. Every M4.7 result on
  `real_v1` stays `DIAGNOSTIC_ONLY` and supports no ranking, selection,
  promotion, or profitability claim.
- With 32 IC months the power projection gives `kill_reachable_projection =
  false` (projected MDE 0.067 at the central prior 0.10); the gate applies
  realized power, and a `review_thesis` outcome is unlikely to be reachable.
- The 24 uncurated delistings remain in `U`, and 83,718 member-days of
  episodes refused by the in-span check remain unpriced; curation or a
  dividend source can reduce both in a later snapshot.
- M4.7b-2 (registration freeze) is the next stage.

## 2026-09-26 - Owner Decision O-3 Option A: One-Year Seal Rule For The 2019-2026 EODHD Membership History

Context:

- The M4.7a-3 local run on snapshot `real_v1` stopped at the seal with
  `holdout_overlaps_prior_exposure` (engineering log, 2026-09-26). The local
  EODHD components response holds 818 entries; 675 are retained and 143 lack
  `StartDate`. The raw month-end count enters the band `[470, 530]` at
  2019-07-31 and stays in band through 2026-07-31, about 7.0 years, while the
  v1 rule needs a 10-year holdout ending by 2014-01-01 and 16 in-band years.
- The owner reviewed the stop report and chose Option A (plan revision to the
  seal rule) under Owner Directives 1 (no data perfectionism) and 2 (no
  over-engineering), and accepted a declared calendar-source label for the
  `SPY.US` date substitution.

Decision:

- Seal rules are keyed by `rule_version` in `data.holdout_partition.SEAL_RULES`.
  The v1 decade rule stays the default. Option A,
  `earliest_available_year_from_raw_membership_counts_option_a_v1`, applies
  the unchanged tolerant `coverage_start` rule and sets:
  - holdout: one year from `coverage_start`;
  - prior-exposure cap: none; the overlap is stated (the seal record keeps its
    `prior_exposures`, and the census reports 100 percent of IC months inside
    the static 50-name cohort window);
  - census minima: 7 in-band years (1 holdout, 1 warm-up, 5 discovery) and 48
    IC months (R-CENSUS-1 and R-CENSUS-8). Every other cap is unchanged.
- The seal record declares `calendar_source`; `real_v1` declares
  `SPY.US_eod_dates_v1`. The build manifest, support record, runner support
  recomputation, and census read it from the seal.
- The parameters were fixed and committed (`eb8c5a5`) before the census ran.

Result on `real_v1` (census JSON SHA-256 `5015a1d8…5c5c`, code `eb8c5a5`):

- Seal: holdout `[2019-07-31, 2020-07-31)`, prospective SHA-256
  `93ce6e5a…9882`, confirmed SHA-256 `20e22520…125e`, confirmation `caveat`
  (identity-adjusted minimum holdout month-end count 468).
- Discovery window: `D0` 2021-08-31, `D_last` 2026-08-07.
- Readiness: `blocked`. R-CENSUS-1 in-band years 6.92 below 7 (the
  identity-adjusted count confirms coverage from 2019-09-30); R-CENSUS-2 20 gap
  windows and excluded fraction 0.384 against 6 and 0.05; R-CENSUS-8 32 IC
  months against 48; R-CENSUS-9 unpriced eligible member-day fraction 0.330
  against 0.02; R-CENSUS-7 caveat. R-CENSUS-3, 4, 5, 6, and 10 pass.
- `|U|` 24 unresolved events in the window (27 discovery candidates, none
  curated; 20 `deferred_holdout`), `|W|` 20, `|G_base|` 1 cell, `|G_term|` 0.
  Settlement lag distribution: empty (zero accepted events).
- Power projection: `T_proj` 32, `kill_reachable_projection` false.
- Premises: VP-1 `a1_volume_half = consistent` (65 rows); VP-2
  `vp2_revisit_required = true` (178,859 member-days with `S_D > 0.05`, 22.5
  percent of eligible member-days), which expires the O-8 ratification.

Consequences:

- a-3 is not closed. The plan 7.2 stop on `blocked:*` readiness applies, and
  the thresholds of R-CENSUS-2 and R-CENSUS-9 stay unchanged pending the owner.
- Open owner decisions: O-7 (coverage shortfall: curation of the 24
  unresolved delistings from public documents, a replacement dividend source
  for the in-span step refusals, and the S9 `entry_unusable_upper_bound`
  charge of 177,177 member-days from the 143 entries without `StartDate`, or
  higher registered caps with their coverage cost stated); O-8 re-decision
  (VP-2); O-3 residual (R-CENSUS-1 at 6.92 years against the declared 7).
- The runner keeps `MIN_IC_MONTHS = 60` and `calendar_source =
  GSPC.INDX_eod_dates_v1` in its registration skeleton; b-2 must align both
  with the Option A seal before the freeze.

## 2026-09-25 - Acceptance Of Milestone 4.7 Binding Implementation Plan Revision 11 And Ratification Of Premise VP-2 (Owner Item O-8)

Context:

- Under Coordination Standard V8.5 Review Iteration Limit (section 3.3) and
  Materiality Test, and following the Owner's four core directives:
  1. Eliminate data perfectionism;
  2. Eliminate over-engineering;
  3. Break strong serial dependencies via pure functions and golden fixtures;
  4. Actively prune Astra's adversarial over-engineered designs.
- The EXPERT route (Claude Opus 5.5, `card_expert_streamline_m47_plan_a11.md`)
  conducted a comprehensive streamlining and ablation pass on Revision 10,
  producing Revision 11 and report
  `coord/reports/v8_review_20260923/expert_streamline_m47_plan_opus.md`.
- Deterministic regression suite verified: 2,716 passed, 2 skipped (100% green).

Decision:

- **Formal Plan Acceptance:** Milestone 4.7 Binding Implementation Plan
  Revision 11 (`coord/plans/m4_7_binding_plan.md`, SHA-256
  `6541db93336e9181ebf3ad2f066b7b17f4550a17565036c2db5a5d82872a6407`, 3,237
  lines, 359,329 bytes) is formally accepted as the operative binding plan.
  Revision 10 is preserved byte-identical in
  `coord/plans/archive/m4_7_binding_plan_r10.md` (SHA-256 `e07989ad...9f3a`).
- **Owner Item O-8 Ratified (Premise VP-2):**
  - **Decision:** Premise VP-2 (vendor applies each declared distribution as a
    non-split adjustment by the registered prior-close formula, and no other) is
    ratified as the registered basis for rows before an in-span declared
    distribution. No per-episode withholding (M9-01's remedy) and no $B_D$ cap.
  - **Scope:** Revision 11 candidate and the M4.7 rerun.
  - **Claim limit:** Every M4.7 statement that uses dollar volume holds under
    premise VP-2; report header discloses VP-2 with measured $B_D$ and $S_D$
    exposure.
  - **Expiry and revisit trigger:** The ratification expires when the a-3
    census sets `vp2_revisit_required` (written member-days with $S_D > 0.05$
    exceed 1 percent of eligible member-days); the owner then re-decides before
    b-2 among keeping VP-2, an $S_D$ cap, or an independent event source. M9-01
    and M10-01 close under this disposition.
- **Rollout Decoupling Approved:**
  - **Phase M4.7a-0:** Pure statistical and portfolio core implemented on
    golden fixtures (dispatches immediately upon plan acceptance).
  - **Phase M4.7a-1:** Retrieval module and holdout partition.
  - **Phase M4.7a-2:** Seal script, universe build, evidence tooling, and
    census on synthetic snapshot fixtures.
  - **Phase M4.7b-1:** Runner integration on synthetic end-to-end fixture.
  - Private data dependency is deferred to Phase M4.7a-3 and M4.7b-2.

---

## 2026-09-23 - Owner Approval Of AUTHORITY.md And Four Delegated Decisions

Context:

- The owner approved the standing-authority record ("Authority is fine.",
  translated from the owner's Chinese) and delegated four open items to the producing session
  (Claude Opus 5.5): agent identity, credential location, the preservation tag,
  and the stale Standards project notes.

Decision:

- **Standing grants:** The owner approved `AUTHORITY.md` as introduced at
  PR #257 head `cb3d7e3` and confirmed that approval ("Authority is fine."); the
  approval is quoted on PR #257. The PR #257 REVIEW remediation left the grant
  substance unchanged: `7e4f5c5` rewrote each Grant field as a verbatim source
  quote, labeled Scope and Expiry as owner-approved interpretation, and
  restored the strict storage prohibition in `AGENTS.md`; `44007a0` pinned the
  quotes to their source commits in the governance tests. PR #257 merged into
  `main` as `5c5fd0c`.
- **Agent identity:** Agents keep committing under the owner's GitHub account,
  and `.github/CODEOWNERS` stays as an ownership label. Enforcement rests on
  V8.0 section 5 (repository text never expands authority by itself) and the
  CRITICAL lane for any `AUTHORITY.md` change. Revisit before any Milestone 5
  execution repository: it uses separate agent identities from its first
  commit.
- **Credentials:** The EODHD API token lives only in the
  `EFR_EODHD_API_TOKEN` environment variable, which the owner sets at run time,
  following the existing `EFR_EODHD_DATA_DIR` and `EFR_EODHD_INVENTORY_PATH`
  convention. Agents never search for, read from files, print, or store the
  token. Retrieval code refuses when the variable is absent.
- **Preservation tag:** Annotated tag `track-a-legacy-final` (object `ef13f62`)
  points to `8fa0055`, the designated preservation baseline for the Track A
  code that PR #259 removes. The immediate pre-retirement `main` commit,
  `0d96a9d`, holds identical Track A packages: `src/campaign`,
  `src/pit_manifest_validator_v1`, and `src/ledger` show no diff between the
  two commits.
- **Project notes:** The five Track A-era notes in
  `Codex/Standards/project-notes/efr/` moved, with their bytes unchanged, to
  `Codex/Standards/archive/efr_track_a_notes/`. They named the 14-trial campaign
  as the mission, an older repository path, and the retired `@codex review`
  channel. `project-notes/efr/efr_coordinator_bootstrap.md` replaces them and
  routes to the V8.0 policy and this repository's documents.

Rationale:

- A second GitHub identity requires account and credential management and adds
  little protection to a simulation-only repository. It becomes necessary where
  credentials and capital exist.
- Environment-only credentials keep secrets out of the repository and agent
  context.
- The archived notes contradicted the current North Star and would have
  misdirected a freshly bootstrapped coordinator.

Consequences:

- Every owner decision from the strategic audit, D1 through D9, now has a
  recorded disposition. Execution of D2 (the pre-flight audit) and the M4.7
  binding plan await coordinator dispatch.

---

## 2026-09-23 - Retire Track A Campaign, Validator, And Ledger Runtime Code

Context:

- `src/campaign`, `src/pit_manifest_validator_v1`, and the `src/ledger` Python
  runtime held 15,226 lines, half of `src`. No active source, research, script,
  or LEAN file imported them. They implemented the frozen Track A 14-trial
  protocol, whose run remains REFUSED.
- The owner adopted the audit's tag-and-remove disposition on 2026-09-23.

Decision:

- Remove the Python code of the three packages, the 44 test and support files
  that exist only to exercise it, and the code-bound Track A tests in
  `tests/test_project_structure.py` and `tests/test_ablation_defensive_boundaries.py`.
- Keep every artifact an accepted contract, a frozen public manifest, or an
  active test binds by path or hash, together with its static checks:
  - the 10 frozen ledger schema releases in `src/ledger/schemas/` (20 files,
    JSON plus SHA-256 sidecars) and the eight structure tests that bind them;
  - `tests/test_ledger_track_b_v7_design.py`, which checks the retained Track B
    v7 design evidence without importing retired code;
  - every file under `tests/fixtures/`;
  - all contract and protocol documents.
- Keep the CI-workflow conformance checks unchanged in `tests/test_ci_workflow.py`.
- Preservation: tag `track-a-legacy-final` points to `8fa0055`, which holds the
  removed code. The retained fixture builder
  `tests/fixtures/pit_manifest_validator_v1/_build_valid_fixtures.py` imports the
  retired validator and runs only from that checkout.

Rationale:

- The owner's anti-overengineering and walking-skeleton directives favor
  deleting unused machinery. Frozen evidence keeps its bytes and bindings.

Consequences:

- Executable verification of the removed Track A code ends: its classifier,
  deciles, listing keys, turnover, eligibility, and runner goldens. The frozen
  documents, fixtures, and schema bytes remain, and so do their static checks:
  the eight schema structure tests and the Track B v7 design test.
- The wheel ships only active packages. `src/ledger/schemas/` is repository
  data outside any package.

---

## 2026-09-23 - Adopt Strategic Audit Decisions And Governance Constitution

Context:

- An owner-commissioned strategic audit found three contradictions in
  `AGENTS.md`, a handoff 52 merged PRs stale, standing grants written in an
  agent-editable file, and a real-data design too underpowered to detect
  published-factor effect sizes. The owner adopted every decision and
  recommendation of that audit on 2026-09-23.

Decision:

- `AGENTS.md` becomes a constitution with invariants R1–R12. Procedures and the
  process-failure list move to the controller. `AUTHORITY.md` quotes each
  standing grant verbatim from its source commit (`e2476a2`, `8dbba99`) and
  adds `Scope` and `Expiry` fields as labeled interpretations that the owner
  approved on 2026-09-23. `.github/CODEOWNERS` marks owner-controlled files.
- `AGENTS.md` keeps the storage prohibition "Never store secrets or raw private
  data in the repo" for tracked, untracked, and ignored files; R11 separately
  governs publication.
- R2 permits a static survivor cohort only under `DIAGNOSTIC_ONLY` and bars it
  from ranking, selection, promotion, and profitability claims. R11 aligns
  publication with the owner's written data terms.
- The North Star gains an edge thesis, objective and hurdle, and kill criteria.
- M4.7, a survivorship-reduced S&P 500 point-in-time universe with a
  pre-registered rerun, is the next milestone. Its holdout is the earliest
  available unexamined decade. Its terminal-evidence standard covers
  documented cash consideration, stock consideration valued at the
  effective-date close, and window splitting for unresolvable events.
- Legacy Track A code retires behind a preservation tag in a separate change.
- The audit reports stay local because they contain local paths.

Recorded process deviations (sources in the engineering log and cards):

- Antigravity (Gemini) coordinated M4.0 through M4.6 while the committed v7
  standard named Pi as coordinator.
- The owner's 24-hour GPT-only mandate of 2026-09-21 routed M4.3 production and
  review to GPT-6 Astra.
- M4.4 through M4.6 used one GPT-6 Astra review seat with the Fast tier on owner
  direction; M4.4 met CRITICAL-lane criteria.
- The committed v7.30 routing table read `TEMPLATE_NOT_ACTIVE` during M4.0
  through M4.6.
- This governance change: the owner assigned the work and its prose directly to
  Claude Opus 5.5 at max effort, and the adopted audit structure served as the
  binding plan without a separate CRITICAL plan review.

Consequences:

- Authority grants have one owner-controlled record. A textual regression test
  rejects the historical grant formulations and any eight-word run of the
  current grant quotes in agent-maintained governance files; it does not
  interpret paraphrased authority.
- A test resolves the handoff's baseline commit in the base's first-parent
  history and fails when more than one merged PR follows it.
- `AGENTS.md` shrinks from 283 to under 200 lines under a tested cap.

---

## 2026-09-23 - Coordination Standard V8.0 Path

Context:

- The owner released coordination standard V8.0. It separates the portable
  rules (`coordinator.md`, `routing_table.json`) from replaceable model
  choices (`model_bindings.json`) in `Codex/Standards/coordination-standard/`.
- `Codex/Standards/herdr_pi_coordinator_v7_two_file` is a temporary link kept
  until repository references move to the new directory.

Decision:

- `AGENTS.md` and the controller reference `Codex/Standards/coordination-standard/`
  and all three policy files.
- Historical entries and review reports keep their v7 path strings unchanged.

Rationale:

- The Standards README asks for the temporary link's removal once references
  are updated. Model-binding changes then require no repository edit.

Consequences:

- After this change merges, the temporary link has no active repository
  consumer.

---

## 2026-09-18 - Walking Skeleton Uses Static 50-Stock Diagnostic Cohort

Context:

- The 14-trial run remains REFUSED for
  `ACCEPTED_IDENTITIES_ZERO_NO_LINEAGE_CONFORMANT_PANEL`.
- `PROJECT_SPEC.md` allows a static survivor cohort for diagnostics but
  not as point-in-time universe evidence.

Decision:

- Unblock the first end-to-end walking skeleton with a committed
  50-stock synthetic static cohort under `DIAGNOSTIC_ONLY`.
- Do not present that cohort as point-in-time membership, dataset
  review, or a 14-trial campaign execution.
- Reuse existing factor, backtest, and IC helpers; add only named
  operators, the cohort fixture/loader, and a thin pipeline.

Consequences:

- Evidence ceiling remains `DIAGNOSTIC_ONLY`.
- D8, A2, identity reopen, and formal interpretation stay closed.

Follow-up:

- Keep the 14-trial identity gate unchanged. Later empirical slices still
  require accepted dataset identities and separate authorization.

---

## 2026-09-15 - North Star Alignment And Demo-First Delivery Strategy

Context:

- Owner established explicit project guidance: correct the whole project's relevant docs/logs, roadmap, and North Star.
- The ultimate project aspiration is automated stock selection and trading, pursuing sustainable risk-controlled long-term net returns. Stable profit is a goal, not a guarantee. The research platform is the first simulation phase, strictly separated from any future execution repository.
- Avoid unbounded perfectionism: do not block early demonstration on an ideal pipeline, complete SEC identity proof for every security, optional ledger/schema coverage, or a factor zoo.
- Historical Track A 14-trial refusal remains preserved historical evidence, but is no longer the sole universal entry point of the project.
- A local 2026-09-13 diagnostic confirmed sufficient local data history for exploration, with documented caveats (zero-volume segments, date gaps, unverified adjustment events) deferred for layered handling.

Decision:

- Create `docs/north_star.md` as the single active product-goal document, while preserving `docs/research_program_charter.md` byte-identical to baseline as hash-pinned formal research evidence policy.
- Align project specification, roadmap, handoff, and skills around a 5-milestone progression with Demo v0 (working vertical slice) as the active delivery target.
- Establish an explicit Imperfection Policy and lightweight backlog distinguishing safe deferrals (presentation polish, extra factors, optional schemas, advanced statistics) from non-deferrable correctness/safety bugs (lookahead, cost/return errors, secrets, unsafe execution).
- Keep the current repository simulated and non-order-capable; record future execution as separately authorized scope.
- Enforce the demo-first discipline: ship a basic, presentable end-to-end version first; record imperfections and improve in working layers.
- Align active workflow and review references with live coordinator V7.23 standards (NORMAL has no mandatory formal seat; reviewer routing is table-owned in routing_table.json).
- Enforce a durable English-only documentation standard across all newly authored or edited project documentation, private addenda, handoffs, and reports.
- Enact the owner's explicit STOP boundary: stop after completing this documentation task, verification checks, and GitHub version management, leaving Demo v0 implementation and market data runs for separate future authorization.

Rationale:

- A demo-first approach enables tangible, auditable, and visible software progress without sacrificing research validity or safety invariants.
- Clear mode boundaries separate exploratory demo development from formal empirical promotion.
- Creating `docs/north_star.md` satisfies active product direction without breaking the hash-pinned charter fixture.
- Bounding this task strictly to documentation alignment prevents premature unauthorized execution.

Consequences:

- Active roadmap, handoff, and spec route to `docs/north_star.md` for active goals, while `docs/research_program_charter.md` remains preserved formal policy.
- Active roadmap and handoff target Milestone 2 Demo v0 vertical slice.
- Historical Track A refusal remains immutable evidence and does not block Demo v0.
- All non-blocking caveats are tracked in the lightweight backlog table.
- All newly authored or edited documentation is written in English.
- Development halts at the documentation boundary awaiting separate task dispatch.

---

## 2026-09-15 - Clarification Of September 13 Diagnostic Sufficiency Wording

Context:

- The earlier 2026-09-15 North Star alignment entry recorded, as of that date,
  that a local 2026-09-13 diagnostic "confirmed sufficient local data history for
  exploration, with documented caveats (zero-volume segments, date gaps,
  unverified adjustment events) deferred for layered handling." That as-of body
  is preserved unchanged below as historical text.

Decision:

- Interpret that "confirmed sufficient" wording as qualitative quantity/history
  planning context only. It is not a validation result, authorization gate,
  tradability proof, universe-completeness claim, profitability claim, or
  pristine-holdout proof. The diagnostic remains outside Demo v0 acceptance.

Rationale:

- Later public routing must not upgrade an as-of planning note into a completed
  data-sufficiency or Demo-authorization result.

Consequences:

- Active handoff, roadmap, and README September 13 statements use the qualitative
  planning-only scope with the same negative constraints. The original 2026-09-15
  decision body remains historical as-of text.

---

## 2026-09-06 - Record Merged Track B Path A And Path B First Checkpoints

Context:

- Protected `main` is at `425b7c88a6e049b63aa2ddeae8560fea08fda23e` after
  PR #199 and PR #200. No pull request was open at the verified start of
  this work.
- Path A first checkpoint merged as PR #199. Path B first checkpoint merged
  as PR #200.
- Public handoff and roadmap still said not to claim Track B runtime
  delivered.
- Research safety invariants apply: no private paths, tickers, prices, or
  performance values.

Decision:

- Record Path A first checkpoint as merged PR #199 and Path B first
  checkpoint as merged PR #200 at `425b7c8`.
- Keep evidence ceiling `DIAGNOSTIC_ONLY`.
- Record that 14-trial remains REFUSED, reason
  ACCEPTED_IDENTITIES_ZERO_NO_LINEAGE_CONFORMANT_PANEL.
- Record that terminal refusal is disposition, not Stage 4 / PR 4
  completion.
- Record that D8, A2, identity reopen, result/performance access stay
  closed.
- Record that optional 37-event completion and factor-zoo stay off the
  critical path.
- Publish no private paths, tickers, prices, or performance values.
- Do not claim ACCESS_COMPLETED, EXPOSURE_DECISION, 14-trial execution, or
  Stage 4 / PR 4 completion.

Rationale:

- A GitHub clone should see the merged Path A and Path B first checkpoints
  rather than an undelivered Track B runtime.
- First-checkpoint status is not full Track B completion and does not reopen
  closed diagnostic gates.

Consequences:

- Public resume surfaces record the merged first checkpoints.
- 14-trial remains REFUSED; Stage 4 stays incomplete; evidence ceiling
  remains `DIAGNOSTIC_ONLY`.
- D8, A2, identity reopen, result/performance access, and brokerage remain
  strictly closed.
- Optional 37-event completion and factor-zoo stay off the critical path.
- No private paths, tickers, prices, or performance values are published.

Follow-up:

- Remain at the merged Path A and Path B first-checkpoint baseline.
- Keep D8, A2, identity reopen, result/performance access closed.

---

## 2026-09-05 - Transfer Owner-Accepted Astra R1 Recommendations Into Public-Safe Roadmap And Handoff

Context:

- Protected `main` is at `027e8ae` after PR #195 and PR #196.
- The owner accepted Astra recommendations R1–R5 under `owner_astra_r1_r5_acceptance_v1`.
- Public documentation (roadmap and handoff) requires alignment with owner-accepted Astra R1 conclusions.
- Research safety invariants apply: no private paths, tickers, prices, or performance values.

Decision:

- Record that 14-trial remains REFUSED, reason ACCEPTED_IDENTITIES_ZERO_NO_LINEAGE_CONFORMANT_PANEL.
- Record that terminal refusal is disposition, not PR 4 completion; Stage 4 incomplete; DIAGNOSTIC_ONLY.
- Record that synthetic Track B is separately eligible and not blocked by success-only Track A close.
- Record that D8, A2, identity reopen, result/performance access stay closed.
- Publish no private paths, tickers, prices, or performance values.
- Do not claim v6 accepted or runtime delivered (v6 QA PASS; REVIEW FAIL; AUDIT FAIL; GROK_REVIEW FAIL; successor binding plan required; Path A is first runtime checkpoint only after accepted plan and design candidate).
- Record that optional 37-event completion and factor-zoo stay off the critical path.
- Record that first future empirical slice is later/planning; do not authorize data access here.

Rationale:

- Public roadmap and handoff documents must accurately reflect owner-accepted conclusions so reviewers and contributors understand that terminal refusal is a disposition branch and not PR 4 completion.
- Decoupling synthetic Track B allows method development to proceed independently under planning authority without compromising frozen diagnostic gates.

Consequences:

- Public documentation reflects the owner-accepted Astra R1 conclusions.
- 14-trial remains REFUSED; Stage 4 stays incomplete; evidence ceiling remains `DIAGNOSTIC_ONLY`.
- D8, A2, identity reopen, result/performance access, and brokerage remain strictly closed.
- No runtime delivery or v6 acceptance is claimed.
- No private paths, tickers, prices, or performance values are published.

Follow-up:

- Advance synthetic Track B planning and successor plan review under planning authority.
- Keep all data access and execution gates closed.

---

## 2026-09-04 - Public-Safe 14-Trial Identity Fail-Closed Stop

Context:

- Protected `main` is `24bc794d0a6cbd6502a8db088008fa74acbe8752` after
  PR #194.
- The 14-trial run is REFUSED with named reason
  `ACCEPTED_IDENTITIES_ZERO_NO_LINEAGE_CONFORMANT_PANEL`.
- Public docs still described the 14-trial run as not executed without the
  named refusal.
- The owner authorized public-safe stop status only: hashes, not bodies.

Decision:

- Record the 14-trial run as REFUSED on the public handoff, roadmap, README,
  and PR 2 status surfaces.
- Publish only the allowed hashes: owner-stop
  `163b8f31d3568e460c074592c00376cf86d4f09371a6bb6a40f8d6cdd4548f5a`,
  freeze record
  `c160a3b21f359dc96eda7f1f018e3315bae79f505078ca5199ed87a8204f0ccd`,
  and protected main `24bc794d0a6cbd6502a8db088008fa74acbe8752`.
- Keep evidence ceiling `DIAGNOSTIC_ONLY`. Keep D8, A2, and identity reopen
  closed. Publish no performance values.

Rationale:

- A GitHub clone should see the named fail-closed refusal rather than an
  open 14-trial path.
- Hash-only publication keeps private paths, ticker lists, performance
  values, and raw rows off GitHub.

Consequences:

- Public resume surfaces bind the owner-stop by hash and do not claim a
  14-trial run.
- D8, result access, A2, and identity reopen remain closed.

Follow-up:

- Keep D8, A2, and identity reopen closed.
- Do not run the 14 trials until the owner reopens a named gate.

---

## 2026-08-25 - Public-Safe Stage 4 G-2 Status

Context:

- Protected `main` is `11a9cb8849b5239faa1081eda046d2254a12febc` after
  PR #189.
- Stage 4 G-2 binding is accepted privately. Public docs still described
  detached pre-run binding as unstarted.
- The owner authorized public-safe G-4 status only: hashes, not bodies.

Decision:

- Record Stage 4 G-2 as accepted by hash on the public handoff, roadmap,
  and PR 2 status surfaces.
- Publish only the allowed hashes: G-2 acceptance file
  `84f1ce471af19b4473a2a3bfa9ffb65b08927cc0218c55bd6922a7ddc5c30de0`,
  frozen plan markdown
  `d847c6305469b050f3d2e0426ff589cf422a2fa1f54044b9dcf037963567f992`,
  EXEC-2 fileset
  `29aeec97ebc8146fccac1f575c1c098cbc9db2b106831a1b53d12e7ad2995c92`,
  and protected main `11a9cb8849b5239faa1081eda046d2254a12febc`.
- Keep Stage 4 not fully complete, the 14-trial run not executed, and the
  evidence ceiling `DIAGNOSTIC_ONLY`.

Rationale:

- A GitHub clone should see G-2 accepted rather than an unstarted Stage 4.
- Hash-only publication keeps private paths, ticker lists, performance
  values, and raw rows off GitHub.

Consequences:

- Public resume surfaces bind G-2 by hash and do not claim a 14-trial run
  or Stage 4 completion beyond that binding.
- Remaining Stage 4 detached pre-run binding still blocks the 14-trial
  run, D8, result access, and A2.

Follow-up:

- Continue remaining Stage 4 detached pre-run binding under
  `DIAGNOSTIC_ONLY`.
- Do not run the 14 trials until remaining Stage 4 binding verifies.

---

## 2026-08-24 - Public Docs Sync After PR 3 And README Merges

Context:

- Protected `main` reached `cc90b34602ee54117ac5bca2445a73b7cac7b90a` after
  PR #187 (bounded diagnostic runner) and PR #188 (README program status).
- Public handoff, roadmap, and PR 2 status still described pre-PR3 state:
  materiality awaiting approval, Stage 2 not granted, PR 3 blocked.
- The owner wants GitHub clone readers and other machines to see the newest
  public-safe program state.

Decision:

- Replace stale public handoff and roadmap checkpoints with post-#187/#188
  facts.
- Publish campaign `DIAGNOSTIC_READY` acceptance and materiality exact-SHA
  approval as hashes only, while keeping formal interpretation not granted
  and the evidence ceiling `DIAGNOSTIC_ONLY`.
- Record detached pre-run binding as the next roadmap stage.
- Do not upload private control-tree bodies; state explicitly that private
  cards still need a private-channel `private_data` transfer.

Rationale:

- Public process docs are the resume surface for another machine or reader.
- Stale "next owner gate" text would send a fresh clone to already-closed gates.
- Hash-bound acceptance facts are allowed public aggregates under Stage 1 terms.

Consequences:

- A GitHub clone can see PR 2/PR 3 public completion state and the true next
  stage (detached binding).
- Private acceptance bodies, freeze bodies, and evidence packs remain local.
- No 14-trial run, performance access, D8, or A2 is authorized by this docs
  change.

Follow-up:

- Start Stage 4 detached pre-run binding under `DIAGNOSTIC_ONLY`.
- Keep public docs updated whenever a protected merge changes stage status.

---

## 2026-08-23 - Publish Public-Safe Track A PR 2 Progress

Context:

- Local Track A PR 2 produced a validator, a private manifest bound by hash,
  a freeze record, and a `diagnostic_only` dataset-review decision.
- The owner authorized GitHub publication of everything except raw private
  data so another machine can resume from public docs.
- Terminal-event policy is explicitly deferred. Materiality numbers are
  proposed and not SHA-approved. Dataset acceptance is not granted.

Decision:

- Publish `pit_manifest_validator_v1` with synthetic fixtures.
- Publish hashes, counts, the allowlisted projection, and safe decision
  fields in `docs/track_a_pr2_public_status_v1.json` and companions.
- Keep the full private manifest, freeze-record body, evidence pack, full
  decision record, ticker lists, private paths, and raw vendor rows out of
  GitHub.

Rationale:

- Stage 1 D2–D4 already permit hashes, counts, and non-sensitive metadata.
- Another workstation can continue public work from these docs. Private
  artifact bodies remain on the originating workstation.

Consequences:

- Public main, after this PR merges, records PR 2 as in progress rather
  than unstarted.
- Stage 2 is not complete. PR 3 stays blocked.

Follow-up:

- Owner exact-SHA on the materiality proposal, then stage 2 acceptance.

---

## 2026-08-22 - Accept Stage 1 Written Terms And Capability Record

Context:

- The owner certified that private data may be retained locally and must not
  be uploaded to the public internet, then wrote that deletion is not required
  and that aggregates, charts, hashes, row counts, non-sensitive metadata,
  noncommercial aggregates, and a capability record may be public on GitHub.
- The owner then authorized the recommended package: bind the existing private
  acquisition-manifest capability conclusions (no new probe), accept Stage 1,
  accept the identity program's terminal fail-closed record, and leave
  materialization unentered.

Decision:

- Stage 1 is accepted. The public-safe record is
  `docs/stage1_accepted_public_record_v1.json`. Identity counts are in
  `docs/identity_evidence_public_aggregate_v1.json`. Both contain hashes and
  aggregates only. Raw private data, ticker lists, provider responses,
  private paths, and performance values stay out of the public repository.
- Track A PR 2 becomes eligible and is not started by this decision.
- Identity acceptance remains a separate fail-closed record and does not
  satisfy dataset acceptance or materialization.

Rationale:

- The campaign contract required written terms plus a private capability
  record. Binding an already-recorded `HistoricalTickerComponents=AVAILABLE`
  conclusion avoids a new network probe and does not purchase an entitlement.
- Closing Stage 1 without starting PR 2 keeps dataset-bound work behind its
  own review.

Consequences:

- Stage 1 is accepted and recorded in the public-safe hash file.
- The evidence ceiling remains `DIAGNOSTIC_ONLY`.

---

## 2026-08-01 - Permit Frozen Dataset-Independent Protocol Core In Parallel

Context:

- The owner accepted the completed CCA1 conclusion that the program route is
  sound but that the private EODHD gate need not idle computations that are
  already frozen, golden-backed, and independent of datasets and results.
- Track A PR 2 remains the provider-bound dataset-review stage, and Track A
  PR 3 remains the bounded diagnostic runner. Neither stage has begun.

Decision:

- `docs/current_roadmap.md` is the canonical source for a separate
  dataset-independent protocol-core lane, its eligibility boundary, the work
  that remains blocked, and the binding Track A PR 3 acceptance criteria.
- The parallel lane starts, satisfies, and unblocks neither Track A PR 2 nor PR
  3. It does not amend the campaign contract, preregistration, trial inventory,
  evidence ceiling, or owner-side private-evidence gate.
- A protocol-core implementation PR may begin only after this correction is
  merged and verified, in a fresh worktree and separately reviewed scope.

Rationale:

- Pure frozen computations can be implemented and tested against committed
  fixtures without creating provider, membership, lineage, eligibility,
  orchestration, private-data, or result-bearing behavior.
- Keeping the full boundary in one active roadmap avoids turning the handoff,
  controller, or this historical log into competing policy sources.

Consequences:

- This decision changes sequencing only. It grants no data access, result
  interpretation, campaign expansion, brokerage, paper, live, or deployment
  authority.
- The three-factor protocol, 14 semantic trials, and `DIAGNOSTIC_ONLY` ceiling
  remain frozen.

---

## 2026-08-01 - Adopt The Long-Term Factor-To-Portfolio Direction

Context:

- The owner confirmed that the project should determine what candidate factors
  are useful for, using point-in-time historical evidence rather than selecting
  only the best backtest.
- The long-term ambition includes at least ten price-derived factors,
  replication across preselected listed-equity markets, and eventual separation
  between research and any order-capable execution system.
- The current Track A campaign is already frozen at three factors and 14
  semantic trials, and its evidence ceiling remains `DIAGNOSTIC_ONLY`.

Decision:

- `docs/research_program_charter.md` is the canonical source for the long-term
  factor-to-portfolio direction and future research/execution architecture
  boundary. `PROJECT_SPEC.md` continues to own the current project contract,
  evidence-layer semantics, and factor registration requirements.
- Track A remains unchanged. A ten-factor price-derived library and cross-market
  campaigns are post-Track-A, post-required-Track-B work with separately frozen
  candidate, market, data, cost, and multiple-testing contracts.
- The research repository may eventually emit a versioned and hash-bound
  `PortfolioIntent`; only a separately authorized private execution repository
  may own broker credentials, execution-time or live-feed market-data
  credentials, broker-routable order intents and their lifecycle, pre-trade
  controls, reconciliation, monitoring, and kill switches. Separately authorized
  historical research-vendor credential use and research-only simulated order
  intents and fills remain governed by the existing research gates; this
  decision grants neither data access nor execution.

Rationale:

- Expanding the frozen pilot after observing results would change its search
  space and weaken its preregistration.
- Cross-market replication is stronger evidence when markets are selected
  before outcomes are viewed and each market has an accepted point-in-time data
  contract.
- Separating research artifacts from order capability prevents experimental
  code from gaining broker or live-execution credentials or silently changing
  live behavior.

Consequences:

- No factor, market, trial, data permission, empirical conclusion, repository
  name, paper deployment, or live capability changes through this decision.
- The active roadmap continues to own sequencing. Future implementation must
  reference the charter rather than duplicate this policy in handoff, roadmap,
  controller, or campaign documents.

---

## 2026-08-01 - Separate The Operational Checkpoint From The Program Roadmap

Context:

- The active handoff had grown to 837 lines by accumulating review chains,
  contract summaries, CI identifiers, and an obsolete PR #177 task queue.
- PR #178 temporarily made the roadmap own the latest snapshot because the
  retained handoff body was historical. That transition ended once the handoff
  could be safely compacted.
- The unchanged 20-line workflow Skill already routes `AGENTS.md`, handoff,
  controller, and roadmap in the intended permanent order.

Decision:

- `docs/current_handoff.md` owns the latest recorded operational checkpoint,
  exact last-verified repository/PR facts, immediate owner blockers, and the
  next safe action. Remote facts are cached evidence and require live verification.
- `docs/current_roadmap.md` owns the program stage sequence, dependency order,
  gate and completion criteria, and coarse stage status. It does not maintain
  branch, CI, or exact repository-state snapshots.
- `docs/codex_long_running_controller.md` continues to own execution, external
  gates, review, waiting, and stop behavior. `AGENTS.md` continues to own
  authority and research-safety invariants.
- Startup resumes through handoff, controller, and roadmap after repository
  authority is loaded. The generated repo map is orientation, not another state source.
- Historical review and contract narratives remain in canonical contracts and
  durable decision, engineering, and troubleshooting logs. Unique audit IDs
  found only in the retired handoff text are preserved in the engineering log.

Rationale:

- Separating an operational checkpoint from the research program plan prevents
  volatile GitHub facts from bloating or redefining stage dependencies.
- A bounded resume document lowers startup cost while retained logs and Git
  history preserve adverse findings, remediation evidence, and provenance.
- Relationship, ownership, length, and obsolete-state tests prevent the former
  duplication and stale-task-queue failure mode from returning.

Consequences:

- The active handoff is capped at 120 lines and contains no historical review chain.
- Roadmap status remains authoritative for research sequencing; the handoff may
  summarize it only as a routed operational checkpoint.
- The Skill and campaign contract remain unchanged, and no research or external-
  action authority is created by this documentation change.

---

## 2026-08-01 - Assign One Owner To Each Active Governance Responsibility

Context:

- `AGENTS.md`, the long-running controller, and the current roadmap repeated
  review, polling, push, and merge rules. Structure tests required the repeated
  wording, so normal documentation cleanup would fail validation.
- Repository-local process text treated technical PR eligibility as authority
  for externally visible actions, conflicting with higher-level authorization
  boundaries.
- Draft PR #148 contained useful manual-review trigger rules but overlapped the
  newer, duplicated policy.

Decision:

- `AGENTS.md` is the repository source for authority, research-safety
  invariants, alignment requirements, and review severity.
- Only `AGENTS.md` enumerates actions that require explicit authorization. The
  controller applies that boundary by reference and must not maintain a second
  action inventory.
- `docs/codex_long_running_controller.md` is the source for staged execution,
  external gates, review lifecycle, waiting, stop conditions, and completion
  reporting.
- Until the dedicated handoff compaction, `docs/current_roadmap.md` owns active
  stage status, dependencies, and the latest verified snapshot. The retained
  handoff body is historical and may not define the current task queue. Neither
  file may redefine authority or workflow policy.
- `docs/research_program_charter.md` owns research intent and evidence policy;
  it references rather than redefines external-action or GitHub review rules.
- Technical eligibility never grants permission for an external, sensitive, or
  destructive operation. Explicit current authorization must cover the action
  and scope.
- Preserve the valid PR #148 behavior in the controller: no review on Drafts,
  one explicit request on a stable current head after validation and CI, no
  duplicate request for an unchanged head, and re-review only after an
  actionable fix changes the head.
- Do not encode fixed polling or follow-up schedules in repository policy.
  Monitoring occurs only when explicitly requested through the product.

Rationale:

- One owner per responsibility prevents policy drift and lets active status
  documents remain short without weakening research or review guardrails.
- Separating eligibility from authority keeps repository rules subordinate to
  current user and higher-level instructions.
- Relationship and boundary tests are more stable than duplicated natural-
  language assertions.

Consequences:

- Governance tests validate canonical responsibilities, references, review
  triggers, and forbidden authorization-expansion wording.
- Campaign, ledger, timing, statistical, and fail-closed research tests remain
  unchanged.
- This change compresses the roadmap and corrects it to PR #177's protected
  merge. A subsequent PR will compress the handoff after preserving its review
  history in durable logs. PR #148 remains an independent Draft until separately
  dispositioned.

---

## 2026-07-31 - Use Circular Within-Segment Blocks For Uniform Null Weighting

Context:

- The twenty-fourth exact-head Codex review of PR #177 at `2c6b827` found one
  P1. For `n>6`, the prior non-circular start set `0..n-L` combined with
  `ceil(n/L)` blocks and tail truncation did not give every row equal expected
  inclusion when `n` was not divisible by `L=6`.
- With `n=7`, the expected local weights were
  `[1,1.5,1,1,1,1,0.5]`, so global null centering did not guarantee that the
  expected resampled null mean was zero.

Decision:

- For every long segment, draw starts uniformly from all `n` positions and map
  each block offset by `(start + offset) mod n`. Circular wrap is confined to
  that segment and may not cross any fold, purge, missing-month, or
  leave-one-year-out boundary.
- Continue drawing `ceil(n/L)` blocks and retain the first `n` concatenated
  rows. If `n=qL+r`, the full blocks contribute expected weight `qL/n` per row
  and the retained circular prefix contributes `r/n`, for exact total expected
  weight one.
- Preserve the previously frozen one-row resampling for segment lengths two
  through six and the fixed singleton rule.

Rationale:

- Uniform marginal row weights make the expected resampled mean of the globally
  centered table zero while retaining length-six local dependence and all
  segment boundaries.
- Re-centering each bootstrap statistic would add a different inferential rule;
  the circular construction removes the bias directly and remains auditable.

Consequences:

- The seeded shared-draw fixture now freezes circular starts, complete row
  vectors, and both uncentered and null-centered mean matrices.
- A separate 63-record fixture exhaustively enumerates all 49 ordered start
  pairs in each of nine seven-row segments, proves unit expected row weights,
  and rejects the former non-circular MOM and LOW_VOL null-mean offsets.
- No data, performance, trial execution, factor, cost case, merge, brokerage,
  paper, or live behavior is added.

---

## 2026-07-31 - Separate Baseline Episodes From Continuous Resets

Context:

- The twenty-third exact-head Codex review of PR #177 at `93adce5` found one
  P2. Both baseline trials required `episode_21_row_return`, but target,
  holding, aggregation, endpoint, and invalid-constituent semantics were not
  frozen when a later monthly reset occurred before `e+21`.

Decision:

- For each factor-valid signal month, freeze the equal-weight eligible-universe
  or random-rank top-decile target at signal close `t`, begin at execution
  close `e=t+1`, and hold the exact initial weights statically through `e+21`.
- Compute each constituent's simple adjusted-close `e` to `e+21` return and
  aggregate exactly `sum(weight_i_at_e * constituent_return_i)`. Ignore any
  intervening monthly execution for this episode; overlapping later episodes
  remain separate dependent diagnostics.
- If any targeted constituent lacks a valid accepted return, retain the whole
  episode as invalid/missing. Forbid survivor renormalization, fill, cash/zero
  substitution, alternate rows, and continuous-path reuse.

Rationale:

- A fixed-horizon factor diagnostic and a monthly-reset continuous strategy
  answer different questions and can diverge in short exchange months.
- Binding the exact episode calculation prevents implementations from
  silently choosing whichever baseline path is convenient.

Consequences:

- The short-month fixture places the next monthly execution at row 20 before
  endpoint row 21. The frozen episode returns `0.01`; a forbidden reset to a
  new target at row 20 returns `0.10`.
- Both series remain outputs of the same two baseline semantic trials; the
  immutable semantic trial count stays 14.
- No data, performance, trial execution, additional factor, merge, brokerage,
  paper, or live behavior is added.

---

## 2026-07-31 - Freeze Continuous Held Returns To Adjusted Close

Context:

- The twenty-second exact-head Codex review of PR #177 at `9bbc2c3` found one
  P2. The continuous strategy and primary-benchmark path froze timing but not
  the price field, adjacent-return formula, or held-anchor failure policy.

Decision:

- Use `adjusted_close_simple_held_return_v1` for the factor strategy, both
  long-only baselines, and factor-matched primary benchmark: each adjacent
  common-calendar held return is exactly
  `adjusted_close[d] / adjusted_close[d-1] - 1`.
- Require both anchors to be real numeric non-Boolean, present, finite,
  strictly positive, and valid under `factor_anchor_lineage_v1`. Invalid
  strategy anchors invalidate the affected trial; invalid primary-benchmark
  anchors invalidate the required comparison and route to the existing hard-
  validity state. No membership renormalization or repair is allowed.
- Forbid raw-close fallback and separately adding split or dividend cash flows
  to the adjusted-close proxy.

Rationale:

- Corporate actions can make raw-close returns economically incompatible with
  the reviewed dividend-and-split-adjusted proxy and change every downstream
  stateful calculation.
- Strategy and primary-benchmark returns must use the same field, formula,
  calendar, and missingness semantics for active-return evidence to be
  interpretable.

Consequences:

- The 2-for-1 split fixture freezes adjusted gross return `0`, equal drifted
  weights, zero turnover/cost/active return, and rejects the raw alternative's
  `-0.25` gross return, `1/3` turnover, and `0.00025` 10-bps cost impact.
- This remains an idealized diagnostic total-return proxy, not a share-level
  execution or exact total-return-index claim.
- No data, performance, trial execution, additional factor, merge, brokerage,
  paper, or live behavior is added.

---

## 2026-07-31 - Bind Factor Anchors To Resolved Listing Lineage

Context:

- The twenty-first exact-head Codex review of PR #177 at `5869193` found one
  P2. Numeric factor-anchor validity did not determine whether lookback prices
  could cross an accepted rename, a listing episode, or ticker reuse by a
  different issuer.

Decision:

- Require every factor input price anchor to carry the blinded dataset-review-
  accepted normalized permanent-security, listing, and listing-episode IDs,
  plus its source alias interval and lineage evidence. Every anchor must match
  the signal target's three resolved identity IDs exactly.
- Permit alias traversal only for a contiguous, nonoverlapping, evidenced
  symbol rename inside the same permanent security, listing, and listing
  episode. Reject ticker-text-only joins, ticker reuse, relisting, venue or
  listing moves, share-class changes, distinct successor securities, and any
  ambiguous lineage path.

Rationale:

- Ticker is an alias, so numeric adjusted-close anchors cannot establish
  longitudinal security identity by themselves.
- A verified rename can preserve one diagnostic listing episode, whereas a
  reused ticker can silently combine unrelated issuers and manufacture a
  return.

Consequences:

- An accepted old-alias/new-alias fixture retains momentum `0.25` only because
  both anchors resolve to the same security/listing episode. An equal-ticker
  different-issuer fixture shows the same ticker-only `0.25` calculation and
  rejects it before factor eligibility.
- The internal resolved IDs remain diagnostic reconstruction evidence; they do
  not assert an EODHD permanent provider ID or upgrade the evidence tier.
- No data, performance, trial execution, additional factor, merge, brokerage,
  paper, or live behavior is added.

---

## 2026-07-31 - Chain Prospective Batches Without Rebinding The Seed

Context:

- The twentieth exact-head Codex review of PR #177 at `e6c7ad5` found one P2.
  A detached binding to one latest-cutoff manifest could not accept future
  observations without rebinding and moving the start anchor.

Decision:

- Bind an immutable historical seed data record/cutoff and the append-
  succession policy before the first prospective signal. Bind future batches
  through consecutive content-addressed append records containing previous
  hash, batch manifest hash, increasing nonoverlapping session bounds, and UTC
  ingestion time. Valid appends do not reset the original anchor.
- Never overwrite prior artifacts. Provider corrections append a correction
  record, retain the affected validity state, and do not retroactively
  recompute a frozen signal.

Rationale:

- Future bytes cannot be known at initial binding, but their admissible order,
  immutability, identity, and audit treatment can be frozen in advance.
- Rebinding the root on every batch makes a strictly-post-binding prospective
  window impossible to accumulate.

Consequences:

- The fixture binds a January seed and successfully chains/counts matured
  February and March batches under the unchanged February binding anchor.
- No data, performance, trial execution, additional factor, merge, brokerage,
  paper, or live behavior is added.

---

## 2026-07-31 - Anchor Prospective Time To Completed Run Binding

Context:

- The nineteenth exact-head Codex review of PR #177 at `3aeeb5a` found one P2.
  Runner code could freeze before a signal while the detached record binding
  exact configuration and environment identity completed after it.

Decision:

- Add detached-run-binding completion to the required canonical UTC anchors.
  The binding is complete only after exact protocol, trial inventory, accepted
  data, runner code, configuration, and environment identity are bound before
  result-bearing work. An incomplete binding forbids prospective counting.

Rationale:

- Code identity alone does not freeze dependencies, configuration, dataset
  acceptance, or the executable environment needed to reproduce seeded and
  deterministic outputs.

Consequences:

- In the staggered fixture, an August signal after code freeze but before
  binding completion cannot count; the next qualifying September signal is the
  prospective start.
- No data, performance, trial execution, additional factor, merge, brokerage,
  paper, or live behavior is added.

---

## 2026-07-31 - Canonicalize Prospective Instants And Mature Threshold Outputs

Context:

- The eighteenth exact-head Codex review of PR #177 at `242f373` found two P2
  ambiguities. A timezone-aware freeze timestamp could not be ordered against
  a date-plus-`AFTER_CLOSE` signal representation, and threshold count could
  precede both final-period outputs.

Decision:

- Normalize every required timezone-aware RFC 3339 freeze timestamp to UTC and
  compare it with the official frozen-calendar XNYS session close converted to
  UTC. Reject naive and date-only freeze values. The signal close must be
  strictly later than the maximum normalized freeze instant.
- Treat the 12th/24th qualifying signal as an operational counter event only.
  Protected performance access timing first becomes eligible strictly after
  the later of that signal's `e+21` label close and following monthly execution
  close, and only after required outputs and separate access gates are ready.

Rationale:

- Same-calendar-date before-close, exact-close, and after-close freezes must
  not shift the prospective window according to an implementation's implicit
  midnight or timezone convention.
- A prospective threshold does not represent 12/24 complete observations until
  both factor-label and continuous-strategy outputs for the last signal mature.

Consequences:

- A before-close same-day freeze permits the close signal; exact-close and
  after-close freezes defer to the next qualifying month.
- Access at the threshold signal, label close, or exact following execution
  close is forbidden; the timing gate opens only after the later maturity
  instant and never bypasses authorization or Track B logging.
- No data, performance, trial execution, additional factor, merge, brokerage,
  paper, or live behavior is added.

---

## 2026-07-31 - Pre-Filter The Strategy Cutoff And Preserve One Economic Path

Context:

- The seventeenth exact-head Codex review of PR #177 at `5b08be6` found one P1
  and one P2. A factor-diagnostic label could end at the accepted cutoff even
  though the corresponding continuous target had no later monthly execution,
  and excluding invalid-month active returns did not define how to preserve a
  stateful strategy path.

Decision:

- Before continuous targets are frozen, include a signal in the continuous
  schedule only if its next monthly execution is on or before the accepted
  cutoff. A signal with a complete diagnostic label but a later execution
  beyond cutoff stays in factor diagnostics and is structurally absent from
  the continuous strategy; it is not an invalid strategy target.
- Keep every sparse/tied zero-target month in the single continuous strategy
  and primary-benchmark return path. Preserve its liquidation/redeployment
  turnover, costs, cash return, invested benchmark return, and active return in
  the full-path annualization used by economic support.

Rationale:

- A normal 22-session calendar month at a bounded cutoff must not create a hard
  campaign invalidation merely because factor-label and next-execution
  endpoints differ.
- Deleting an invalid factor month or restarting around it changes holdings,
  costs, annualization, and potentially the final diagnostic label.

Consequences:

- The July 2024 fixture retains the `2024-06-28` factor signal and its
  `2024-07-31` label but freezes no continuous target whose next execution is
  `2024-08-01`.
- A valid/tied/valid fixture retains three turnover-1 transitions and produces
  `MIXED_DIAGNOSTIC`; the forbidden filtered/direct-bridge path would produce
  `POSITIVE_DIAGNOSTIC`.
- No data, performance, trial execution, additional factor, merge, brokerage,
  paper, or live behavior is added.

---

## 2026-07-31 - Preserve The Invested Benchmark And Bind Bootstrap Coverage

Context:

- The sixteenth exact-head Codex review of PR #177 at `46679c4` found two P2
  gaps. The fourteenth-round baseline generalization incorrectly made the
  equal-weight eligible-universe benchmark reuse a factor's zero target, and
  the final-state classifier did not accept the frozen bootstrap-support gate
  as an input.

Decision:

- For sparse or tied factor months, keep the factor and random-rank targets at
  zero but keep the equal-weight baseline and primary benchmark invested in
  the nonempty unique decision-time eligible universe. Duplicate canonical
  keys or an empty universe make that benchmark unformable; cash is not a
  substitute.
- Retain invalid-factor-month active returns as descriptive evidence and
  forbid them from final-state support.
- Require nondegenerate bootstrap support for all three factors as an explicit
  realized-coverage input. Failure routes to `INCONCLUSIVE_DIAGNOSTIC` unless
  an earlier hard-validity rule produces `INVALID_DIAGNOSTIC`.

Rationale:

- The primary benchmark measures the invested eligible universe and cannot be
  silently converted into the same cash path as an invalid factor portfolio.
- A bootstrap unable to generate nondegenerate null support cannot justify a
  Holm-supported conclusion, while ordered hard-validity precedence must stay
  intact.

Consequences:

- A tied-month fixture fixes the 10/25-bps active-return contrast against an
  invested benchmark and rejects a cash-benchmark implementation.
- Classifier boundary cases cover false bootstrap support and its precedence
  interaction with hard validity.
- No data, performance, trial execution, additional factor, merge, brokerage,
  paper, or live behavior is added.

---

## 2026-07-31 - Resample Short Segments And Freeze Keys Campaign-Wide

Context:

- The fifteenth exact-head Codex review of PR #177 at `e9c2707` found one P1
  and one P2. `L=min(6,n)` copied every segment of at most six rows into every
  bootstrap replicate, and first-decision-time eligibility did not say how to
  aggregate staggered eligibility across factors for key freezing.

Decision:

- For segments longer than six, retain overlapping non-circular length-six
  blocks. For segment lengths two through six, use length-one blocks and draw
  `n` positions uniformly with replacement. A singleton necessarily stays
  fixed.
- Require at least one resampleable segment and at least two distinct null-
  bootstrap means for each factor. Degenerate support retains all evidence but
  makes primary inference invalid, grants no Holm support, and routes to the
  realized-coverage `INCONCLUSIVE_DIAGNOSTIC` rule unless an earlier rule wins.
- Freeze each listing-lineage key once, campaign-wide, at the earliest signal
  cutoff where the listing is decision-time eligible for any of the three
  factors. Later factor eligibility reuses the same bytes; per-factor key
  freezing or re-encoding is forbidden.

Rationale:

- A centered bootstrap that copies all rows can assign the minimum p-value to
  a positive mean without representing sampling uncertainty.
- One key identity must control ties, turnover, and random-baseline ordering
  across all factors even when their lookbacks become eligible on different
  dates.

Consequences:

- A 60-record fixture in ten six-row segments proves genuine within-segment
  resampling and nondegenerate null means; an all-singleton case fails support.
- A staggered-factor fixture freezes a null-ended key at reversal eligibility
  and rejects later momentum-specific endpoint bytes.
- No data, performance, trial execution, additional factor, merge, brokerage,
  paper, or live behavior is added.

---

## 2026-07-31 - Freeze Common Prospective Eligibility And Invalid Baselines

Context:

- The fourteenth exact-head Codex review of PR #177 at `fc561e4` found two P2
  ambiguities. Prospective counting did not aggregate the three factor-specific
  eligibility states, and random-rank baseline behavior was undefined for the
  three decision-time invalid-rebalance triggers.

Decision:

- A prospective signal qualifies only when all three factor rebalances are
  decision-time valid: each has at least 100 eligible listings, at least 10
  distinct finite factor values, and unique canonical keys. A subset-valid
  signal is retained operationally but neither starts nor increments the
  prospective counter.
- Both equal-weight and random-rank factor-matched baseline outputs inherit the
  same three invalid triggers. They retain an invalid output record, freeze a
  zero target and full cash, keep episodic return invalid/missing rather than
  zero, and carry the invalid flag through liquidation turnover and later cash.
  Random seeds and permutations are not consumed for invalid factor months.

Rationale:

- One common predicate prevents different implementations from opening the
  protected 12/24-rebalance windows in different months.
- Baselines must not invest a sparse or non-unique sample after the matched
  factor strategy has already failed the same decision-time gate.

Consequences:

- The prospective boundary fixture now includes a subset-valid month that does
  not count. Sparse, tied, and duplicate-key fixtures apply the retained zero-
  target behavior to both baselines and distinguish valid random draw use.
- No data, performance, trial execution, additional factor, merge, brokerage,
  paper, or live behavior is added.

---

## 2026-07-31 - Bind Eligibility And Prospective Start To Their Full Gates

Context:

- The thirteenth exact-head Codex review of PR #177 at `12cacaa` found two P2
  inconsistencies. A generic complete-history eligibility input could still
  exclude endpoint-valid MOM/REV rows with an interior missing price, and the
  machine-readable prospective start waited only for the protocol freeze.

Decision:

- Decision-time eligibility uses the factor-specific common-calendar position
  span and only the price anchors actually referenced by that factor. There is
  no independent full observed-price-history gate for MOM/REV.
- Prospective counting anchors to the maximum of the protocol-freeze, runner-
  code-freeze, and dataset-policy-freeze timestamps. The first eligible signal
  must be strictly later than that maximum; equality is not prospective and no
  earlier month may be backfilled.

Rationale:

- Factor definitions and the eligibility path must produce the same listing
  set, ranks, targets, and benchmark membership.
- A month observed before every required freeze cannot provide prospective
  confirmation merely because the protocol was already committed.

Consequences:

- An integrated 100-listing fixture retains the endpoint-valid interior-
  missing listing in each MOM/REV target and benchmark; a forbidden full-
  window exclusion leaves 99 and invalidates the rebalance.
- A staggered-freeze fixture makes a signal equal to the latest freeze
  non-prospective and starts at the following eligible monthly signal.
- No data, performance, trial execution, additional factor, merge, brokerage,
  paper, or live behavior is added.

---

## 2026-07-31 - Freeze Endpoint-Only MOM/REV Price Completeness

Context:

- The twelfth exact-head Codex review of PR #177 at `d2ac8cd` found one P2.
  The preregistration validated the two formula anchors but described 253 and
  22 required history price anchors, which could also be implemented as a
  full-window contiguous-observation requirement.

Decision:

- Treat 253 for `MOM_12_1` and 22 for `REV_1M` as inclusive common-calendar
  position spans needed to address the formulas, not counts of price values
  that must all be observed.
- Each factor consumes exactly its two referenced anchors. An interior missing
  or invalid adjusted-close value has no factor-value or eligibility effect
  when both referenced anchors pass the strict validity gate. It is not filled,
  repaired, or otherwise incorporated.

Rationale:

- The two frozen formulas are endpoint returns. Requiring unreferenced
  intermediate observations would silently introduce a different missingness
  screen and could change ranks, targets, and coverage across implementations.

Consequences:

- Separate 253-position momentum and 22-position reversal fixtures retain
  `0.25` and `0.10` with an interior missing value and explicitly distinguish
  the forbidden all-prices-contiguous interpretation.
- No data, performance, trial execution, additional factor, merge, brokerage,
  paper, or live behavior is added.

---

## 2026-07-31 - Freeze MOM_12_1 And REV_1M Anchor Validity

Context:

- The eleventh exact-head Codex review of PR #177 at `bc4c201` found one P2.
  Momentum and reversal had no strict price-anchor validity or invalid-value
  policy, so corrupt zero, negative, or Boolean numerators could still produce
  finite factor values.

Decision:

- Require every adjusted-close anchor referenced by `MOM_12_1` and `REV_1M`
  to be present, finite, strictly positive, real, and non-Boolean before any
  division. The rule applies equally to numerator and denominator anchors.
- If any anchor fails, retain the listing/signal-date factor value as invalid/
  missing, exclude the listing from factor-specific decision-time eligibility,
  and count the exact reason. No fill, interpolation, clipping, absolute-value
  repair, or alternate row is allowed.

Rationale:

- A finite formula output is not sufficient evidence that its provider price
  anchors are valid. Corrupt anchors must not enter ranks, deciles, or targets.

Consequences:

- Golden fixtures freeze momentum `80->100` as `0.25` and reversal `100->90`
  as `0.10`, then mutate each anchor position through every invalid class.
- No data, performance, trial execution, additional factor, merge, brokerage,
  paper, or live behavior is added.

---

## 2026-07-31 - Freeze Diagnostic Forward Returns And Shared Bootstrap Draws

Context:

- The tenth exact-head Codex review of PR #177 at `a5b6695` found two P2
  ambiguities: the execution-to-endpoint diagnostic return did not distinguish
  simple from log returns, and bootstrap centered/uncentered distributions did
  not state whether they shared draws or consumed two RNG passes.

Decision:

- Define diagnostic forward return as
  `adjusted_close[e+21] / adjusted_close[e] - 1`. Both anchors must be present,
  finite, strictly positive real non-Boolean scalars. Invalid anchors retain
  and invalidate the factor-month outcome with a counted reason and no repair.
- For every bootstrap replicate and chronological segment, draw block starts
  exactly once. Reuse the resulting row-index vector jointly for all factors,
  the uncentered interval table, and the globally null-centered p-value table.
- Use one RNG pass per replicate. Separate centered/uncentered passes and a
  pass-order choice are forbidden.

Rationale:

- Simple and log endpoint returns produce different decile evidence from the
  same prices.
- Two seeded bootstrap passes produce different draws depending on pass order;
  shared indices bind p-value and interval distributions to one immutable
  resampling experiment.

Consequences:

- Separate golden fixtures distinguish endpoint simple/log returns and freeze
  three segmented bootstrap replicates, row indices, uncentered means,
  null-centered means, and the rejected second-pass alternative.
- No data, performance, trial execution, additional hypothesis, merge,
  brokerage, paper, or live behavior is added.

---

## 2026-07-31 - Freeze LOW_VOL_3M Simple Returns And Anchor Validity

Context:

- The ninth exact-head Codex review of PR #177 at `86f6929` found one P2.
  `one_day_adjusted_close_returns` did not distinguish simple from log returns
  or define invalid price-anchor handling.

Decision:

- Define each `LOW_VOL_3M` observation as the adjacent-price simple return
  `adjusted_close[d] / adjusted_close[d-1] - 1` for `d=t-62..t`, inclusive.
  Log returns are forbidden.
- Require exactly 64 anchors from `t-63..t`. Every anchor must be a present,
  finite, strictly positive real numeric scalar other than a Boolean.
- If any anchor fails, retain the listing/signal-date factor value as invalid/
  missing, exclude that listing from the factor-specific decision-time
  eligible set, and count the reason. Filling, interpolation, clipping,
  absolute-value repair, alternate rows, and log fallback are forbidden.

Rationale:

- Simple and log return volatilities can rank securities differently, changing
  deciles, targets, Rank IC, and final diagnostic state.
- Invalid-anchor behavior must be decision-time deterministic and visible,
  rather than silently repaired by an implementation.

Consequences:

- The 63-return golden fixture now freezes distinct simple and forbidden-log
  sample standard deviations and mutates every invalid-anchor class.
- No data, performance, trial execution, additional factor, merge, brokerage,
  paper, or live behavior is added.

---

## 2026-07-31 - Freeze Holm Index Origin And Factor-Order Mapping

Context:

- The eighth exact-head Codex review of PR #177 at `1f6c801` found one P2.
  The code-like adjusted-p formula combined mathematical multipliers with an
  undefined `k` origin, so a zero-based implementation could use multipliers
  4, 3, and 2 instead of Holm's 3, 2, and 1.

Decision:

- Define mathematical `k` as one-based over `1..3` and access a Python sorted
  p-value sequence at `k-1`.
- For each sorted position `k`, compute
  `min(1, max((3-j+1) * sorted_raw_p[j-1] for j in 1..k))`.
- Sort raw p-values stably with frozen factor order as the tie breaker, stop
  sequential rejection at the first non-rejection, and map adjusted values
  back to the original factor order only after the sorted running maximum.

Rationale:

- Explicit index conversion prevents a runner from changing adjusted values,
  rejection decisions, or the final diagnostic state through a plausible
  Python-style interpretation of the same YAML.

Consequences:

- A three-p-value golden fixture freezes sorted order, multiplied values,
  running maxima, factor-order adjusted values, and the rejection set.
- No data, performance, trial execution, additional hypothesis, merge,
  brokerage, paper, or live behavior is added.

---

## 2026-07-31 - Freeze Random-Rank Permutation-To-Target Mapping

Context:

- The seventh exact-head Codex review of PR #177 at `b8149c2` found one P2.
  The baseline froze seed derivation and RNG but did not say which date entered
  the seed, which end of the permutation was selected, or how a non-divisible
  universe determined top-decile size.

Decision:

- Use strict signal date `t`, never execution date, in the factor/month seed
  preimage. Interpret the first 16 SHA-256 hex digits as an unsigned big-endian
  seed for NumPy `PCG64DXSM`.
- Sort canonical listing-key bytes ascending, permute integer indices once, and
  interpret the permutation as high-to-low random rank.
- Reuse the factor-decile remainder rule: select the first
  `N // 10 + (1 if N % 10 else 0)` permuted indices. The final chunk and a
  floor-only size are forbidden.
- Assign `1 / selected_count` to every selected key and serialize the target in
  ascending canonical-key order. The random baseline remains one semantic
  trial and the complete inventory remains exactly 14.

Rationale:

- Otherwise multiple reasonable implementations can produce different
  baseline holdings and returns from the same frozen seed.
- Reusing the existing high-ranked-decile size rule avoids introducing a
  second quantile convention solely for the random baseline.

Consequences:

- A 103-key golden fixture freezes the exact digest, unsigned seed, complete
  permutation, 11 selected canonical keys, equal weights, and serialization.
- No data, performance, trial execution, additional hypothesis or cost case,
  merge, brokerage, paper, or live behavior is added.

---

## 2026-07-31 - Align Diagnostic Costs And Freeze Random-Baseline Cost Basis

Context:

- The sixth exact-head Codex review of PR #177 at `0179ebb` found one P1 and
  one P2. The campaign formula omitted the accepted post-return gross
  multiplier, and the random-rank continuous baseline did not state whether
  its return was gross or net at a frozen cost rate.

Decision:

- On each rebalance row, apply held-position incoming returns first, then
  charge execution cost against post-return equity at the ending close. As a
  beginning-period return impact, cost is
  `gross_multiplier * turnover * bps / 10000` and net row return is gross row
  return minus that impact.
- Multiply every security-level cost contribution by the same gross
  multiplier so the contributions sum exactly to the portfolio cost impact.
- Keep both baselines' 21-row episodic outputs gross and cost-free. Keep the
  equal-weight continuous baseline gross and cost-free. Freeze the random-rank
  continuous baseline as net at the primary 10-bps all-in cost case, using the
  same drifted-weight turnover and execution-to-execution accounting as factor
  strategies.
- Do not emit random-baseline 0-bps or 25-bps continuous variants. The baseline
  remains one semantic trial and the complete inventory remains exactly 14.

Rationale:

- The accepted Stage 2 timing authority charges at the close after the row's
  incoming return. Omitting the gross multiplier understates a post-gain
  charge and overstates a post-loss charge relative to that contract.
- A single cost-frozen random strategy baseline is reproducible and comparable
  to the campaign's primary strategy case without creating a hidden parameter
  search.

Consequences:

- Hand-calculated fixtures cover a nonzero 10% incoming return, turnover 2.0,
  the 25-bps factor stress case, and the 10-bps random-baseline primary case.
- No data, performance, trial execution, extra semantic trial, merge,
  brokerage, paper, or live behavior is added.

---

## 2026-07-31 - Freeze Benchmark-Comparison Final-State Routing

Context:

- The fifth exact-head Codex review of PR #177 at `e5d72c2` found one P2.
  Missing factor-matched constituent returns or SPY dates invalidated their
  comparisons, but the ordered final-state tree did not state whether each gap
  was a hard failure, coverage failure, or false economic predicate.

Decision:

- Any invalid required factor-matched primary-benchmark comparison is a hard-
  validity failure for the campaign and routes to `INVALID_DIAGNOSTIC` under
  the first ordered rule. It may not be omitted, filled, or treated as merely
  economically unsupported.
- The secondary SPY comparison is descriptive only. A missing SPY date retains
  an invalid secondary output and missing count but has no final-state effect
  when every required primary comparison is valid.
- `economically_supported(f)` uses only the valid factor-matched primary-
  benchmark annualized active return at 10 and 25 bps.

Rationale:

- The primary comparison is required for the preregistered economic coherence
  predicate, so incomplete primary evidence cannot support another final state.
- SPY was frozen as a secondary proxy and should not silently become a hard
  requirement for a final state whose primary benchmark is factor-matched.

Consequences:

- Separate fixtures route a primary matched-universe gap to
  `INVALID_DIAGNOSTIC` and show that a SPY-only gap leaves an otherwise
  `POSITIVE_DIAGNOSTIC` state unchanged.
- Both invalid comparisons remain visible in the required evidence outputs.
- No data, performance, trial execution, merge, brokerage, paper, or live
  behavior is added.

---

## 2026-07-31 - Persist Through Review And Freeze Factor-Turnover Predecessors

Context:

- The fourth exact-head Codex review of PR #177 at `6a7445f` found two P2
  gaps. Factor turnover did not specify whether an outcome-invalid intervening
  month remained the next month's predecessor, and the mandatory handoff still
  called already-completed commit/push work pending.
- The owner also corrected the review-wait terminal condition: creating a
  monitor is not completion, and the task must continue through review and any
  safe remediation until the exact current head has no actionable finding.

Decision:

- Freeze factor turnover to the immediately preceding scheduled frozen
  decision-time target, including an intervening zero target and a target whose
  later outcome becomes invalid. Outcome validity is retained separately and
  cannot make turnover skip back to the last outcome-valid target.
- The first scheduled frozen target in the bounded evaluation schedule has
  `not_applicable` turnover. Every later scheduled target has exactly one
  immediate predecessor.
- Treat a pending current-head Codex review as a nonterminal task state. Keep
  the task active, use a single five-minute monitor only when needed, never
  duplicate a review request, and repeat fix, validation, push, CI, and review
  until no actionable finding remains.
- Retain the separate four-run, thirty-minute cap for a genuinely critical
  owner decision; this decision supersedes only the prior eight-run pause rule
  for a pending Codex review.

Rationale:

- Later endpoint missingness must not rewrite a previously knowable target or
  any later decision-time turnover. Skipping an outcome-invalid target would
  make a future diagnostic depend on post-signal information.
- A scheduled callback is an implementation mechanism for waiting, not proof
  that the requested review gate completed.

Consequences:

- A three-month mutation fixture distinguishes the required immediate-target
  turnover from the forbidden last-outcome-valid alternative.
- The handoff records `6a7445f` as committed, pushed, and CI-passed, names the
  fourth-review findings, and directs continuations to current-head CI/review
  state rather than redundant publication work.
- This changes protocol and workflow control only. It adds no data access,
  performance result, merge, brokerage, paper, or live behavior.

---

## 2026-07-31 - Freeze Robustness Sample And Trial Inventory Binding

Context:

- The third exact-head Codex review of PR #177 at `4d832c7` found two P2
  protocol gaps. The evidence bundle named `trial_inventory.json` without
  binding it to the frozen 14-trial JSON bytes, and the final-state robustness
  rules did not choose between factor-specific all-valid Rank IC months and the
  primary common complete-case table.
- Different valid sample choices could change yearly signs,
  leave-one-year-out means, and therefore `POSITIVE_DIAGNOSTIC` versus
  `MIXED_DIAGNOSTIC` after results were visible.

Decision:

- Require bundle `trial_inventory.json` to be an exact byte-for-byte copy of
  `docs/preregistrations/eodhd_sp500_three_factor_trial_inventory_v1.json` at
  the protocol-freeze commit. Its SHA-256 must equal the detached trial-
  inventory freeze hash; parsing, reordering, normalization, or changing one
  trial field cannot satisfy the binding.
- Use only the primary common complete-case monthly Rank IC table for yearly
  and leave-one-year-out values that enter final-state robustness. Each
  factor's all-valid-month table remains descriptive only.
- Freeze yearly grouping to signal-date calendar year. Freeze the
  outcome-independent required-year set to every year with at least one
  scheduled primary-evaluation signal whose full label is inside accepted
  bounds.
- Use every required year in the positive-year fraction denominator and omit
  every required year exactly once for leave-one-year-out. A required year with
  no common-case row, an exact-zero yearly mean, or an empty post-omission table
  fails robustness.

Rationale:

- Child hashing alone proves only that the bundle lists the bytes it contains;
  it does not prove those bytes are the preregistered trial inventory.
- One shared sample basis and an outcome-independent year denominator prevent
  result-informed switching between more favorable missingness patterns.

Consequences:

- A deterministic fixture now demonstrates that the allowed common-case basis
  yields `POSITIVE_DIAGNOSTIC` while the forbidden factor-all-valid basis would
  yield `MIXED_DIAGNOSTIC` on the same configured evidence.
- These changes freeze protocol and audit behavior only. No data, performance,
  trial execution, thread resolution, or merge is authorized.

---

## 2026-07-29 - Remediate Reviews Automatically And Bound Scheduled Waits

Context:

- The second exact-head review of PR #177 found three actionable P2 protocol
  gaps after the first remediation commit.
- The prior workflow treated each review round as a potential owner stop even
  when the finding was safe, concrete, and within the already-authorized
  stage. It also lacked exact polling bounds for a pending Codex review or a
  genuinely critical owner decision.
- Draft PR #148 already edits `AGENTS.md` from an older base, but the owner
  explicitly directed PR #177 to establish the new behavior now.

Decision:

- Fix actionable in-scope review findings immediately without waiting for a
  separate owner confirmation. Revalidate, push, and request one current-head
  rereview after each changed head.
- While only `@codex review` is pending, use one thread-scoped schedule every
  five minutes for at most eight runs. Do not post duplicate review requests;
  stop early when the review completes, the head changes, or a finding arrives.
- When a critical owner decision is genuinely required, use one thread-scoped
  follow-up every thirty minutes for at most four runs. Never make the
  decision on the owner's behalf, and remain paused after the fourth unanswered
  run.
- Freeze `LOW_VOL_3M` as the Python half-open slice `[t-62:t+1]`, exactly 63
  returns ending at `t` from 64 price anchors.
- Permit a zero strategy target only for three signal-time conditions: fewer
  than 100 eligible securities, fewer than 10 distinct finite factor values,
  or duplicate canonical listing-key bytes. Later unselected outcome
  missingness cannot change the target, liquidation, or cash path.
- Require the evidence bundle to contain an exact-byte YAML child whose
  SHA-256 equals the detached protocol-freeze hash. A derived JSON file is not
  authoritative.

Rationale:

- Safe review remediation is ordinary implementation work inside an authorized
  PR, while purchases, protected access, destructive work, external scope
  expansion, and materially different research interpretations remain owner
  decisions.
- Bounded scheduled waits prevent both silent abandonment and unbounded polling
  or reminder spam.
- Exact slices, zero-target predicates, and byte-level evidence binding remove
  implementation-dependent behavior before result access.

Consequences:

- PR #148 now overlaps `AGENTS.md`; it remains untouched but must be rebased and
  compared before future use.
- The review schedule will be created only when the new exact head is actually
  waiting for review. No schedule is needed while actionable findings are being
  fixed.
- The remediation changes protocol and governance only. It does not fetch data,
  calculate performance, resolve review threads, or authorize merge.

---

## 2026-07-29 - Freeze Decision-Time Eligibility And Diagnostic Classification

Context:

- Final review of PR #177 found that the first protocol draft allowed future
  execution/endpoint availability inside the only eligibility definition.
- The draft enumerated five final states without an exhaustive assignment
  rule, left listing-key byte serialization implementation-dependent, and did
  not say whether fixed-bps costs were all-in or composable.

Decision:

- Freeze factor ranks, deciles, long-only targets, and matched-benchmark
  membership using only information known at signal close `t`. Future
  availability or return mutations cannot change those objects.
- Treat missing future outcomes only through explicit invalidation. Do not
  drop, substitute, or renormalize over future survivors.
- Use `listing_lineage_key_bytes_v1`: NFC UTF-8 length-prefixed exchange and
  ticker, strict ASCII dates, and a tagged null/present interval end. Freeze
  the key at first decision-time eligibility so later endpoints cannot rewrite
  historical order or identity.
- Interpret 0/10/25 bps as mutually exclusive all-in diagnostic execution-cost
  cases. No separate commission, spread, slippage, fee, impact, or capacity
  charge may be added.
- Assign the five final states with the ordered decision tree in the canonical
  campaign contract and preregistration. Hard-validity failure precedes
  coverage insufficiency; positive classification requires Holm, 10/25-bps
  economic, and frozen robustness coherence.

Rationale:

- Signal targets and benchmark membership must be invariant to halts,
  delistings, missing endpoints, and provider backfills that occur after the
  signal cutoff.
- Canonical bytes, fixed cost composition, and exhaustive classification
  predicates prevent implementation- or result-dependent choices after the
  protocol freeze.

Consequences:

- Missing selected execution prices or held returns can make the diagnostic
  invalid; this is preferable to silent survivorship conditioning.
- Exact zero fails every strict-positive economic or robustness predicate.
- Economic and robustness predicates constrain the final diagnostic label but
  do not create new discovery hypotheses outside the three-factor Holm family.

---

## 2026-07-29 - Reset To A Diagnostic-First Two-Track Program

Context:

- PR #176 completed R1I on protected main at `6386c59`.
- The roadmap still required completion of the full 37-event payload registry
  before statistical or empirical research.
- The owner determined that event-schema, test, and PR counts had displaced
  empirical research progress and supplied an exact EODHD historical S&P 500
  three-factor diagnostic scope.
- EODHD entitlement, historical-membership coverage, retention after
  cancellation, and public derived-output permission remain unverified.

Decision:

- Preserve the accepted 37-event vocabulary and immutable releases as optional
  `full_ledger_profile_v1`; do not continue R1J or one-event registry PRs.
- Run Track A first: one `DIAGNOSTIC_ONLY` historical EODHD campaign containing
  exactly `MOM_12_1`, `REV_1M`, `LOW_VOL_3M`, two baselines, and nine
  factor/cost strategy trials, for 14 semantic trials total.
- Freeze research choices in a public protocol and a separate JSON inventory.
  Use detached hashes rather than a self-referential preregistration hash.
- Bind cutoff, manifest, calendar, exclusions, coverage thresholds, and dataset
  review in a blinded dataset-acceptance record. After the runner merges and
  before any expanded-data performance access, create a detached run binding
  over code, configuration, environment, protocol, inventory, and accepted
  dataset hashes.
- Require entitlement and written retention/publication permission before
  expanded retrieval, durable retention, or public derived output. Codex must
  not purchase an entitlement.
- After Track A closes, implement Track B as an 8-12-conceptual-event-family
  stateful runtime in at most one design PR and one runtime PR. More than 14
  exact wire types requires a new owner decision.

Rationale:

- A public preregistration, exact trial inventory, immutable code/data/config
  binding, all-outcome retention, content-addressed private bundle, and
  independent review can constrain cherry-picking for a diagnostic campaign
  without pretending to provide formal protected-access evidence.
- A minimal stateful runtime is still needed before prospective performance
  access or formal evidence promotion, but it need not delay the first
  falsifiable historical diagnostic.
- Separating protocol freeze, blinded data acceptance, and the final pre-run
  binding prevents data-quality decisions or runner revisions from becoming
  hidden result-dependent research choices.

Consequences:

- Track A may end only in one of the five allowed `*_DIAGNOSTIC` states.
- Track A can never produce `RESEARCH_PASS`, alpha validation, profitability,
  market-wide validity, paper readiness, or live readiness.
- Weak, negative, mixed, invalid, and cost-erased outcomes remain valid and
  must not stop or disappear from the campaign.
- Track B does not block Track A, but Track B protected-access logging blocks
  opening prospective performance.

Follow-up:

- Resolve the private EODHD entitlement/retention/publication gate.
- Add the public manifest validator and complete a blinded dataset review.
- Implement only the frozen Stage 5-MVP/6-MVP runner, then execute and
  reconcile all 14 trials.
- Report progress using accepted dataset, eligible assets/dates, trial
  reconciliation, bundle completeness, conclusion, prospective months, and
  replication status, not schema, test, or PR counts.

---

## 2026-07-29 - Select R1I-A Attempt Start Authority

Context:

- Stage 4B-R1H is accepted on protected `main` through PR #174 at `b42b911`;
  exact merge-head CI run `30489691309` passed.
- A read-only dependency/risk graph over the remaining 27 incomplete events
  selected `ATTEMPT_STARTED` as the unique smallest strict compute-path
  successor. The campaign-amendment pair remains optional, protected-access
  intent is an independent higher-risk capability root, and terminal attempt,
  trial, artifact, and closure events remain downstream.
- Existing authorities froze durable start immediately before execution but
  did not freeze exact readiness, permission, one-shot capability,
  role-independence, lost-ack, or double-execution semantics. The owner
  selected bundle `R1I-A`.

Decision:

- Promote only `ATTEMPT_STARTED`; keep every terminal, artifact, access,
  exposure, closure, review, promotion, adjudication, supersession, and
  campaign-amendment event incomplete.
- Use the existing `att_<32 lowercase hex>` attempt identity as subject and
  one campaign ID as sorted-unique scope. Bind the exact earlier
  `ATTEMPT_ALLOCATED` event ID/hash and semantic-trial ID.
- Pin one complete repository-external canonical
  `attempt_start_readiness_record_v1` through an immutable digest-pinned
  authority catalog. Require literal `READY`, exact current
  plan/executor/environment/input evidence, and distinct effective principals
  for readiness issuer/reviewer, executor, allocation actor, plan issuer, and
  plan reviewer.
- Pin a separate current `attempt_start_authority_v1` actor-authority record.
- Mint one ledger-owned `cap_<32 lowercase hex>` identity and complete private
  `attempt_execution_capability_record_v1` atomically with the start append.
  Keep redemption secret/material repository-external. Require one atomic
  consumption before execution, exactly one start per attempt, and fail-closed
  expired/revoked/wrong-executor/concurrent/double consumption.
- Exact lost-ack replay of the same operation and request returns the same
  event and capability identity. Changed requests conflict; aliases, retries,
  reruns, new campaigns, record generations, and restarts never reset start or
  consumption history.
- Publish immutable registry `0.9.0` under unchanged schema-language `0.2.0`,
  preserve R0 through R7 bytes/behavior/default selection, and leave the
  other 26 events `SCHEMA_INCOMPLETE_DIAGNOSTIC_ONLY`.

Rationale:

- Attempt start is the smallest event that advances the accepted compute path
  without inventing terminal evidence, artifact identity, protected-access
  permission, or private result fields.
- A complete readiness record makes exact validation and current executor
  inputs retrievable without leaking them into the public event.
- A ledger-owned one-shot capability plus atomic consumption separates durable
  authorization from code execution and closes lost-ack/double-start races at
  the future runtime boundary.
- Separate readiness review and start authority avoid self-certified
  execution permission.

Consequences:

- R1I may support exactly eleven events while the other 26 remain incomplete.
- Local schema acceptance remains syntax-only and cannot prove source order,
  record retrieval, readiness, independence, authority, currentness,
  idempotency, atomic mint, single consumption, durable append, execution,
  access, artifact production, or research behavior.
- Private-data access, research execution, brokerage, order, paper, and live
  trading impacts remain zero.

Follow-up:

- Add an independent positive fixture plus literal namespace, source,
  readiness, authority, capability, privacy, currentness, single-start,
  lost-ack, prior-release, package-parity, incomplete-event, and unpublished-
  promotion oracles.
- After protected R1I completion, analyze the remaining 26-event graph before
  choosing the smallest strict successor.

## 2026-07-29 - Select R1H-A Attempt Allocation Authority

Context:

- Stage 4B-R1G is accepted on protected `main` through PR #173 at `520ed65`;
  exact merge-head CI run `30485940985` passed.
- A read-only dependency/risk graph over the remaining 28 incomplete events
  selected `ATTEMPT_ALLOCATED` as the smallest strict prerequisite before
  attempt start, protected access, terminal evidence, and artifact
  disposition.
- Stage 4a and R1G deliberately did not freeze attempt identity, plan
  authority, retry relations, or actor authority. The owner selected bundle
  `R1H-A`.

Decision:

- Promote only `ATTEMPT_ALLOCATED`; keep attempt start, protected access,
  terminal, artifact, disposition, closure, review, promotion, adjudication,
  supersession, and campaign-amendment events incomplete.
- Use `att_<32 lowercase hex>` as the exact attempt namespace, `attempt` as
  subject type, and one campaign ID as the sorted-unique scope.
- Bind the exact earlier `TRIAL_ALLOCATED` and initial
  `CAMPAIGN_INVENTORY_SEALED` event ID/hash pairs.
- Pin one complete repository-external canonical `attempt_plan_record_v1`
  through an immutable digest-pinned authority catalog. Pin a separate
  immutable acceptance whose reviewer differs from the plan issuer,
  trial-definition issuer, allocation actor, and relevant private-input
  producers. Pin a separate current attempt-allocation actor authority.
- Use a closed `first_attempt`/`retry` tagged union. First attempt has literal
  ordinal 1. Retry has ordinal at least 2 and exact prior terminal attempt
  event ID/hash, requires a new attempt ID, and follows a monotonic
  policy-bounded ordinal under the same accepted trial.
- Forbid alias, clone, rerun, new-campaign, and post-result reclassification
  resets. Require source, retrieval, acceptance, role-independence,
  currentness, uniqueness, terminal-predecessor, retry-policy/budget, and
  pre-action checks to fail closed.
- Publish immutable registry `0.8.0` under unchanged schema-language `0.2.0`,
  preserve R0 through R6 bytes/behavior/default selection, and leave the
  other 27 events `SCHEMA_INCOMPLETE_DIAGNOSTIC_ONLY`.

Rationale:

- Attempt allocation is the narrowest event that advances the accepted
  partial order without granting execution or protected-access capability.
- A complete external plan keeps private operational detail out of the public
  event while retaining exact retrievability and digest authority.
- Separate acceptance and actor authority prevent plan issuance, review, and
  append permission from collapsing into self-certified evidence.
- Closed first/retry branches make ordinal and predecessor rules reviewable
  without inventing later start, terminal, or artifact wire schemas.

Consequences:

- R1H may support exactly ten events while the other 27 remain incomplete.
- Local schema acceptance remains syntax-only and cannot prove source
  existence/order, plan retrieval, independence, currentness, retry
  permission, durable append, execution, access, artifact production, or
  research behavior.
- Private-data access, research execution, brokerage, order, paper, and live
  trading impacts remain zero.

Follow-up:

- Add independent first-attempt and retry fixtures plus literal namespace,
  source, authority, acceptance, relation, ordinal, currentness, anti-reset,
  incomplete-event, prior-release, package-parity, and unpublished-promotion
  oracles.
- After protected R1H completion, analyze the remaining 27-event graph before
  choosing the next event family.

## 2026-07-29 - Select R1G-A Initial Campaign Inventory Seal Authority

Context:

- Stage 4B-R1F is accepted on protected `main` through PR #172 at `d9ac67e`;
  exact merge-head CI run `30482706983` passed.
- A read-only dependency/risk graph over the remaining 29 incomplete events
  found that `CAMPAIGN_INVENTORY_SEALED` is the unique smallest prerequisite
  after `TRIAL_ALLOCATED` and before either `ATTEMPT_ALLOCATED` or
  `ACCESS_INTENT`.
- Stage 4a deliberately did not freeze the inventory wire representation,
  exact authority/currentness model, role independence, or finite
  campaign-trial bound. The owner selected bundle `R1G-A`.

Decision:

- Promote only `CAMPAIGN_INVENTORY_SEALED`; keep amendment, attempt, access,
  disposition, artifact, closure, review, promotion, adjudication, and
  supersession events incomplete.
- Use the existing campaign as subject with singleton campaign scope and bind
  its exact earlier allocation event.
- Pin one complete repository-external canonical
  `campaign_inventory_record_v1` through an immutable digest-pinned authority
  catalog. The record binds the ordered all-and-only earlier trial allocation
  and definition evidence, experiment/family/sample relations, budgets,
  variation axes, access budget, and frozen policies.
- Pin a separate acceptance record whose reviewer differs from the inventory
  issuer, seal actor, accepted trial-definition issuers, and accepted private
  input producers. Pin the seal actor's separate current authority record.
- Bound one initial inventory to 1 through 4096 semantic trials. A larger
  campaign requires a versioned owner decision; truncation, aliasing, or
  multiple synthetic initial seals are forbidden.
- Bind the exact nested nonrecursive
  `campaign_inventory_preseal_head_v1`; locally enforce subject/scope,
  ledger, and previous-hash equality while keeping predecessor currentness,
  sequence-plus-one, uniqueness, retrieval, ordering, and atomicity as
  mandatory stateful fail-closed checks.
- Publish immutable registry `0.7.0` under unchanged schema-language `0.2.0`,
  preserve R0 through R5 bytes/behavior/default selection, and leave the other
  28 events `SCHEMA_INCOMPLETE_DIAGNOSTIC_ONLY`.

Rationale:

- Sealing the initial all-trial inventory is the narrowest event that advances
  the accepted partial order without prematurely choosing attempt or protected
  access identity/capability semantics.
- An external complete record keeps the event bounded while requiring
  retrievable all-and-only evidence rather than a hash-only assertion.
- Separate acceptance and seal authority prevent preregistration review,
  record issuance, and append permission from collapsing into one
  self-certified claim.
- The 4096 bound is finite and reviewable while remaining a schema ceiling,
  not a research budget recommendation.

Consequences:

- R1G may support exactly nine events while the other 28 remain incomplete.
- Local schema acceptance remains syntax-only and cannot be called a sealed
  campaign or append/runtime proof.
- Trial execution, attempt, protected-access, private-data, dependency, and
  trading impacts remain zero.

Follow-up:

- Add independent standard and maximum positive fixtures plus literal
  payload, scope, authority, count, pre-seal, duplicate, incomplete-event,
  prior-release, package-parity, and unpublished-promotion oracles.
- After protected R1G completion, analyze the remaining 28-event graph before
  choosing between the attempt-allocation and protected-access paths.

## 2026-07-29 - Select R1F-A Semantic Trial Allocation Authority

Context:

- Stage 4B-R1E is accepted on protected `main` through PR #171 at `814bf02`;
  exact merge-head CI run `30478870434` passed.
- The accepted Stage 4a contract defines semantic-trial allocation and exact
  parent/binding meaning, but the 0.5.0 registry deliberately leaves
  `TRIAL_ALLOCATED` incomplete.
- The owner selected bundle `R1F-A` and authorized automatic best-path analysis
  after completion.

Decision:

- The exact semantic-trial namespace is `trl_<32 lowercase hex>`.
- `TRIAL_ALLOCATED` allocates one new trial, uses a singleton campaign scope,
  and begins with literal disposition `PLANNED`.
- It pins exact earlier campaign/experiment/family source events and requires
  the complete sample set in the repository-external canonical trial
  definition to resolve through one legal current campaign path.
- The complete definition is retrieved by an exact digest-pinned authority and
  record tuple. Separate immutable records bind definition acceptance,
  allowlisted public projection approval, and allocation-actor authority.
  Acceptance review is independent of the definition issuer, allocation
  actor, and accepted private-input producers.
- The relation vocabulary is the closed union
  `original`/`child`/`clone`/`rerun`. The code-identity vocabulary is the
  closed union `clean_commit`/`dirty_tree`. Sources must be earlier, exact, and
  acyclic; dirty-tree formal interpretation remains separately review-gated.
- A semantic trial has at most 32 sample bindings. Identity-bearing defaults,
  partial records, ambiguous or stale parents, mixed paths, changed retained
  bytes, relation cycles, self-review, and post-action allocation fail closed.
- R1F may publish immutable registry `0.6.0` under unchanged schema-language
  `0.2.0`, promote only `TRIAL_ALLOCATED`, and preserve R0 through R4 bytes,
  behavior, and default selection.

Rationale:

- A trial is the first event whose immutable definition composes allocation,
  family, sample, timing, data, code, cost, selection, artifact, retry, and
  privacy authorities; a closed exact record avoids laundering narrative
  requirements into a partial wire schema.
- Closed relation and code-identity unions make lineage and dirty-source state
  explicit without implying that local shape validation verifies retained
  bytes or runtime state.
- Separate acceptance, publication, and actor-authority records keep method
  review, public disclosure, and permission from collapsing into one
  self-issued assertion.

Consequences:

- R1F's owner-methodology gate is cleared. Registry `0.6.0` may support
  exactly eight events while the other 29 remain
  `SCHEMA_INCOMPLETE_DIAGNOSTIC_ONLY`.
- Trial execution, attempt, protected-access, private-data, dependency, and
  trading impacts remain zero.

Follow-up:

- Add independent clean-original and dirty-rerun fixtures plus literal
  child/clone positives and complete namespace/parent/authority/relation/code/
  privacy/scope killing evidence.
- After protected R1F completion, analyze the remaining event dependency/risk
  graph and automatically proceed with the smallest best next slice unless a
  genuine owner-only architecture choice is encountered.

## 2026-07-29 - Select R1E-A Binding Authority

Context:

- Stage 4B-R1D is accepted on protected `main` through PR #170 at `8d02e5a`;
  exact merge-head CI run `30475306672` passed.
- R1A and R1D deliberately left campaign-entity binding, the external Stage 3
  sample-reference event, exact source references, cross-campaign
  external-origin reuse, and their stateful path/currentness rules for a
  separate owner decision.
- The owner selected bundle `R1E-A`.

Decision:

- `CAMPAIGN_ENTITY_BOUND` remains one event with a top-level closed
  `subject_type` union. The exact branches are `trial_family` with
  `fam_<32 lowercase hex>` and `sample` with
  `smp_<32 lowercase hex>`.
- Each campaign binding has singleton `campaign_scope_ids` and an exact source
  event ID and SHA-256. Trial families source only empty-scope global
  `TRIAL_FAMILY_REGISTERED`.
- The sample branch contains a nested closed `source_kind` union:
  `local_registration` sources an empty-scope global `SAMPLE_REGISTERED`;
  `external_reference` sources the exact first
  `STAGE3_SAMPLE_REFERENCE_BOUND` event.
- `STAGE3_SAMPLE_REFERENCE_BOUND` allocates one new external-origin
  `smp_<32 lowercase hex>` identity for one campaign and carries the exact R1D
  Stage 3 authority, record, acceptance, public-projection, and
  publication-approval tuple with singleton scope.
- A later campaign reuses the same external-origin identity only through the
  `external_reference` campaign-binding branch. It must not allocate another
  identity or backfill a synthetic `SAMPLE_REGISTERED`.
- Stateful use fails closed unless the campaign is already allocated; source
  bytes, digest, event ID/type/subject/scope and ordering are exact; authority
  and decisions are current; the target binding is unique; origin paths remain
  exclusive; and aliases, clones, reruns, campaigns, overlap, access, or
  reclassification cannot reset identity or exposure history.
- R1E may publish immutable registry `0.5.0` under unchanged schema-language
  `0.2.0` and promote only `CAMPAIGN_ENTITY_BOUND` and
  `STAGE3_SAMPLE_REFERENCE_BOUND`.

Rationale:

- Closed outer and nested unions prevent generic-entity and nullable-field
  ambiguity.
- Exact retained source references make campaign evidence auditable without
  copying a partial registration or external record into the binding event.
- Reusing the first external-origin identity preserves R1D-A lineage,
  dependence, and exposure history across campaigns instead of allowing a
  per-campaign reset.
- Keeping local shape validation separate from source/currentness/runtime
  enforcement prevents schema acceptance from laundering missing stateful
  evidence.

Consequences:

- R1E's owner-methodology gate is cleared. Registry `0.5.0` may support
  exactly seven events while the other 30 remain
  `SCHEMA_INCOMPLETE_DIAGNOSTIC_ONLY`.
- The R1E contract makes a bounded explicit amendment to R1A's former
  registration-only campaign source description for external-origin sample
  reuse.
- Trial, attempt, protected-access, private-data, dependency, and trading
  impacts remain zero.

Follow-up:

- Add independent fixtures for trial-family, global-local sample, first Stage
  3 external reference, and later external-origin reuse paths.
- Add literal union, source-field, namespace, singleton-scope, authority,
  privacy, incomplete-event, prior-release, package-parity, and
  unpublished-promotion oracles.
- After protected R1E completion, orient the next small registry family and
  surface any genuine owner methodology decision before mutation.

## 2026-07-29 - Select R1D-A Local Sample Registration Authority

Context:

- Stage 4B-R1C is accepted on protected `main` through PR #169 at `68a4c4f`;
  exact merge-head CI run `30471505290` passed.
- R1A and R1C deliberately deferred the exact local sample namespace, Stage 3
  sample-record authority, local/external representation boundary,
  acceptance/currentness, privacy projection, and event boundary because
  helpers, fixtures, and narrative examples are not wire-schema authorities.
- The owner selected the recommended bundle `R1D-A`.

Decision:

- The exact ledger-local `sample_id` namespace is
  `smp_<32 lowercase hex>`.
- Local registration uses an immutable versioned Stage 3 sample-authority
  catalog plus complete repository-external canonical records retrieved by one
  exact digest-pinned resolver tuple. Retrieval miss, ambiguity, schema
  mismatch, noncanonical bytes, digest mismatch, or hash-only stand-in fails
  closed.
- Acceptance and public-projection publication approval are separate complete
  immutable records. The acceptance reviewer is distinct from both the sample
  record producer and registration actor. Both authorities use strictly
  increasing, single-current generations.
- Direct local, global local with later campaign binding, and later external
  Stage 3 reference paths are mutually exclusive. One canonical lineage/path
  has one ledger-local identity per epoch; external references are not
  backfilled as synthetic local registrations.
- Aliases, clones, new campaigns, reruns, window overlap, result access, and
  reclassification do not reset identity or exposure history. Overlap cannot
  manufacture pristine holdout status.
- Complete records, private locators and digests, raw values, and performance
  remain external/private. Public projections contain only allowlisted safe IDs
  and explicitly publication-approved hashes.
- Local sample registration retains the owner-selected common maximum of 32
  direct campaign IDs.
- R1D may publish immutable registry `0.4.0` under unchanged schema-language
  `0.2.0` and promote only `SAMPLE_REGISTERED`.

Rationale:

- Complete retrievable records and independent acceptance prevent hash-only or
  self-reviewed sample registration from becoming formal authority.
- Separate publication approval treats non-reversibility as insufficient for
  public disclosure.
- Stable lineage identity and exclusive representation paths prevent exposure
  resets and duplicate local/external identities.
- Keeping both binding events for R1E avoids laundering incomplete stateful
  source, currentness, and path checks into a local shape schema.

Consequences:

- R1D's owner-methodology gate is cleared. The other 32 event types, including
  `CAMPAIGN_ENTITY_BOUND` and `STAGE3_SAMPLE_REFERENCE_BOUND`, remain
  `SCHEMA_INCOMPLETE_DIAGNOSTIC_ONLY`.
- Local schema acceptance proves event shape and pinned references only; it
  does not retrieve records, authenticate roles, determine currentness, enforce
  path exclusivity or exposure history, append events, or authorize research.
- Trial, attempt, protected-access, private-data, dependency, and trading
  impacts remain zero.

Follow-up:

- Add independent global/direct fixtures and literal namespace, authority,
  acceptance, currentness, privacy, scope, and unpublished-promotion oracles.
- Prove byte/behavior/package parity for immutable R0, R1B, and R1C releases.
- After protected R1D completion, open separate R1E design authority for both
  binding events and their stateful source/path rules.

## 2026-07-28 - Select R1C-A Trial-Family Registration Authority

Context:

- Stage 4B-R1B is accepted on protected `main` through PR #167 at `a6f7d43`;
  exact merge-head CI run `30424903896` passed.
- R1A/R1B deliberately deferred the exact family namespace, retrievable
  definition authority, acceptance/reviewer-independence model,
  anti-reset/currentness policy, relation vocabulary, and shared direct-scope
  maximum because helpers, fixtures, and narrative examples are not
  wire-schema or methodology authorities.
- The owner selected the recommended bundle `R1C-A`.

Decision:

- The exact `trial_family_id` namespace is `fam_<32 lowercase hex>`.
- Family definitions use an immutable versioned authority catalog plus complete
  repository-external canonical records retrieved by one exact
  schema/canonicalization/catalog/record digest-pinned tuple. Retrieval miss,
  ambiguity, schema mismatch, noncanonical bytes, or digest mismatch fails
  closed.
- Acceptance is a separate immutable canonical record. Its reviewer must be
  distinct from both the definition issuer and registration actor and it binds
  the exact definition tuple and global/direct campaign scope.
- Global multiplicity-family identity is stable. Acceptance generations are
  strictly monotonic, exactly one accepted generation is current, supersession
  is explicit, and currentness is required before registration, trial
  allocation, attempt execution, and protected access.
- Aliases, clones, reruns, new campaigns, result exposure, and post-result
  reclassification do not reset identity or counts. Definition generations use
  `supersedes`; distinct dependent families use `depends_on`; no record may
  self-declare `independent_of`.
- Direct family scope is limited to 32 campaign IDs. The same maximum applies
  to later local sample registration.
- R1C may publish a separate immutable registry `0.3.0` under unchanged
  schema-language `0.2.0` and promote only `TRIAL_FAMILY_REGISTERED`.

Rationale:

- Complete retrievable records prevent hash-only preregistration stand-ins.
- Separate acceptance and role independence prevent self-review from becoming
  formal authority.
- Stable identity and currentness rules prevent multiplicity resets through
  naming, cloning, reruns, campaign changes, or post-result relabeling.
- The finite shared scope bound keeps direct registration auditable while
  retaining global registration plus explicit binding for broad reuse.

Consequences:

- R1C's owner-methodology gate is cleared. The other 33 event types remain
  `SCHEMA_INCOMPLETE_DIAGNOSTIC_ONLY`.
- Local schema acceptance proves event shape and pinned references only; it
  does not retrieve records, authenticate roles, determine currentness, enforce
  anti-reset history, allocate campaigns, append events, or authorize research.
- Trial, execution-attempt, protected-access, private-data, dependency, and
  trading impacts remain zero.
- Future owner-methodology gates use at most four owner-facing reminders at
  30-minute intervals. If no owner answer follows the fourth reminder, the
  heartbeat pauses instead of emitting repeated quiet status messages.

Follow-up:

- Add independent global/direct fixtures and literal namespace, authority,
  acceptance, currentness, relation, and scope killing oracles.
- Prove byte/behavior/package parity for immutable R0 and R1 releases.
- After protected R1C completion, open a separate R1D owner gate for the exact
  sample and Stage 3 reference authority.

## 2026-07-28 - Ratify The Experiment Allocation Namespace

Context:

- Stage 4B-R1A is accepted on protected `main` through PR #166 at
  `9cf5325`; exact merge-head CI passed.
- Architecture A deliberately deferred the experiment prefix because helpers,
  narrative examples, and rejected fixtures are not wire-schema authorities.
- R1B cannot promote `EXPERIMENT_ALLOCATED` without one exact owner-ratified
  typed namespace.

Decision:

- The owner selected option `E1`.
- The exact `experiment_id` wire namespace is
  `exp_<32 lowercase hex>`.
- This owner decision, not any pre-existing helper or fixture, is the authority
  for the prefix.
- R1B may use the namespace only in its separate immutable registry `0.2.0`
  authority and exact `EXPERIMENT_ALLOCATED` schema.

Rationale:

- `exp_` is a short, type-specific namespace that remains disjoint from the
  accepted `cmp_` campaign namespace and the other frozen ledger-owned types.
- Explicit ratification prevents accidental promotion of non-authoritative
  documentation or test data into a production wire contract.

Consequences:

- R1B's final owner-methodology gate is cleared.
- The decision authorizes only typed syntax. It does not prove allocation,
  uniqueness, parent existence, authorization, append order, preregistration,
  or any research action.
- Trial-family and sample prefixes remain unresolved owner decisions for later
  releases. Their events remain `SCHEMA_INCOMPLETE_DIAGNOSTIC_ONLY`.
- Trial, execution-attempt, protected-access, private-data, and trading impacts
  remain zero.

Follow-up:

- Publish and validate the separate R1 registry/digest without changing R0
  bytes or behavior.
- Meta-test all three schema-language `0.2.0` additions and keep the other 34
  events fail closed.

## 2026-07-28 - Select Versioned Minimal Allocation/Registration Architecture

Context:

- Stage 4B-R0 is accepted on protected `main` through PR #165 at `4c874eb`;
  exact merge-head CI passed.
- Six non-overlapping read-only audits examined campaign/experiment allocation,
  family/sample registration, local/global/external binding, schema-language
  expressiveness, independent vector evidence, and adversarial scope/privacy
  risks.
- The audits agreed that promoting the six-event family from narrative fields
  or test helpers would launder incomplete semantics into false wire-schema
  coverage.
- The owner selected architecture A after reviewing the materially different
  versioned-minimal and definition-bearing alternatives.

Decision:

- Preserve the R0 registry and sidecar byte-for-byte and preserve accepted R0
  validator behavior. Add R1B as separate registry version `0.2.0` artifacts;
  every later promotion batch publishes a new immutable, monotonically
  versioned registry release rather than overwriting an accepted release.
- Retain the accepted 37-event vocabulary. Do not split
  `CAMPAIGN_ENTITY_BOUND`; use a future closed tagged union.
- Make `CAMPAIGN_ALLOCATED` and `EXPERIMENT_ALLOCATED` reservation-only.
  Complete campaign and experiment definitions belong to later exact
  campaign-inventory schemas before attempt or protected access.
- Use the allocated, registered, or bound entity as subject. Preserve the
  accepted `cmp_` campaign namespace; defer exact experiment, trial-family,
  and sample prefixes to owner decisions in R1B, R1C, and R1D.
- Place `campaign_scope_ids` explicitly in each family payload. Every campaign
  in a shared direct registration must already be allocated.
- Version the closed schema language before adding tagged unions,
  array/path membership, or `safe_public_id`; never retrofit those semantics
  into R0.
- Require future exact, immutable, schema-versioned family-definition and
  Stage 3 sample authorities with retrievable canonical records. Preserve the
  selected exact Stage 3 decision-binding/currentness rules, but defer family
  acceptance, reviewer identity/independence, decision schema, and currentness
  policy to R1C. An ID plus digest alone is not sufficient.

Rationale:

- Immutable coexistence preserves accepted R0 reproduction and prevents a
  later validator from silently reinterpreting old evidence.
- Reservation-only allocation keeps identity creation separate from the full
  research protocol and avoids partial or hash-only preregistration.
- Entity subjects and explicit scope make evidence inclusion reviewable without
  redundant scalar fields.
- Closed versioned unions and safe reference tokens prevent generic-ID,
  nullable-arm, path, URI, free-text, and private-data laundering.

Consequences:

- R1A is design-only. `LEDGER_EPOCH_CREATED` remains the sole
  `FROZEN_SUPPORTED` event and all other 36 events remain
  `SCHEMA_INCOMPLETE_DIAGNOSTIC_ONLY`.
- Trial count, execution-attempt count, and protected-sample access remain
  zero. No dependency, backend, private data, or trading behavior is added.
- The first implementable follow-up is a separate R1B batch for exact
  campaign/experiment allocation schemas only, after the owner ratifies the
  exact experiment namespace.
- Family, sample, and binding events remain blocked by their exact authority,
  anti-reset, alias/currentness, finite-bound, and privacy decisions.
- R1B must implement and meta-test all three closed schema-language `0.2.0`
  additions even though only array/path membership is consumed by its event
  schemas.

Follow-up:

- Complete R1A documentation gates without changing registry artifacts.
- In R1B, add a separate versioned R1 authority and independent allocation
  vectors, ratify the exact experiment namespace, meta-test all schema-language
  `0.2.0` additions, and prove R0 byte/hash/behavior/package parity.
- Continue with separately reviewed family, sample, and binding decisions
  before the later 37-of-37 closure and runtime architecture gates.

## 2026-07-28 - Start Stage 4B With A Fail-Closed Registry Foundation

Context:

- Stage 4a is accepted on protected `main` through PR #164 at `27f0497`; exact
  merge-head CI passed.
- The accepted contract closes the event vocabulary at 37 values but freezes
  an exact payload schema only for `LEDGER_EPOCH_CREATED`.
- Six non-overlapping read-only audits found that exact subject, campaign
  scope, fields, nullability, unions, nested objects, enums, ordering, safe
  vocabularies, and cross-field constraints remain intentionally unresolved
  for the other 36 events.
- Existing checkpoint helpers and the rejected trial-allocation stub are
  synthetic semantic evidence, not event wire schemas.

Decision:

- Begin Stage 4B with the bounded
  `experiment_trial_ledger_schema_registry_r0` contract.
- Package one self-contained ASCII canonical JSON registry in a separate
  `ledger` namespace. Use the JSON artifact, not Python constants, as the
  registry authority.
- Bind the full registry object, including vocabulary, type definitions,
  schemas, constraints, incomplete-event declarations, and vectors, into one
  canonical lowercase SHA-256 whose sidecar is outside the preimage.
- Parse raw registry and event JSON with duplicate-property detection before a
  mapping exists. Reject floating-point, non-finite, and non-I-JSON numbers.
- Freeze a small closed schema DSL sufficient for the accepted epoch schema;
  later descriptor kinds require a versioned amendment.
- Keep `LEDGER_EPOCH_CREATED` as the sole `FROZEN_SUPPORTED` event. Reject the
  other 36 known events as `SCHEMA_INCOMPLETE_DIAGNOSTIC_ONLY` and unknown
  events as `UNKNOWN_EVENT_TYPE` before append or action.
- Do not call R0 a complete registry, Stage 4B conformance, or ledger runtime.

Rationale:

- A generic object, free string, opaque metadata map, hash-only stand-in, or
  test-derived fact set would turn name coverage into false schema coverage.
- Exact subject and scope rules determine campaign evidence inclusion and
  checkpoint currentness; guessing them could conceal relevant events.
- The standard library is sufficient for the ASCII R0 registry and avoids a
  premature production-dependency decision.

Consequences:

- Trial count, execution-attempt count, and protected-sample access remain
  zero. No private data, provider, campaign, performance result, or trading
  behavior enters R0.
- The legacy reporting writers and registries remain unchanged.
- Stage 5 and formal interpretation remain blocked.
- Storage backend, private location, transaction/recovery, checkpoint
  currentness, authority/signature, capability security, and fork policy
  remain owner decisions.

Follow-up:

- Add exact schemas in separately reviewed event-family decisions, beginning
  with allocation/registration only after its subject, scope, ID namespaces,
  payload, null/union/order rules, and stateful boundary are frozen.
- Use a separate closure stage to prove 37-of-37 exact coverage with no
  incomplete, wildcard, open-object, or free-text stand-ins. Payload-registry
  acceptance will still not imply runtime completion.

## 2026-07-27 - Freeze Semantic Trials, Attempts, And Ledger Completeness

Context:

- Stage 3 is accepted on protected `main` through PR #163 at `a6c147e`, but no
  dataset is accepted for formal interpretation.
- The existing schema-v1 experiment writer creates overwrite-capable
  successful-run sidecars after computation. It cannot retain
  failed-before-write, abandoned, retried, or overwritten history and is not an
  immutable all-trial ledger.
- A record hash chain alone cannot detect deletion of a valid tail when the
  writer can also replace the retained head.

Decision:

- Propose `docs/experiment_trial_ledger_contract.md` as the Stage 4a design
  authority, subject to final current-head review, protected merge, and exact
  merge-head CI.
- Treat `trial_id` as one frozen semantic configuration and `attempt_id` as one
  invocation. Retain both semantic trial count and execution-attempt count;
  operational retries never erase failed attempts.
- Require durable allocation before validation/execution and a committed exact
  access-intent capability before protected content can be released.
- Seal the complete campaign inventory and global dependence-family lineage;
  preserve failures, invalid/aborted/excluded work, artifacts, access, review,
  and promotion decisions through append-only events and supersessions.
- Bind each initial inventory seal to one
  `campaign_inventory_preseal_head_v1` semantic anchor whose ledger ID and
  exact predecessor sequence/hash are included in the seal request/event
  preimage. Compare that anchor to the actual current stream head at the same
  serialized atomic boundary that assigns the seal sequence and
  `previous_event_sha256`; head drift conflicts rather than rebasing. This
  ordering anchor is not the independently retained closure checkpoint and
  selects no storage backend.
- Reuse `pit_canonical_json_v1` for an exact ledger-event identity projection,
  chain every event to the prior hash, and require an independently retained
  immutable head/checkpoint for formal campaign closure.
- Freeze an exact `campaign_evidence_checkpoint_v1` preimage. Reconstruct its
  all-and-only campaign-scoped evidence prefix from the retained chain; bind
  the cutoff, freeze, sealed inventory, and one ordered checkpoint reference;
  and reconcile sealed/terminal semantic-trial counts plus
  allocated/terminal attempt counts. Equal counts never replace exact set,
  membership, uniqueness, or current-disposition checks.
- Use the application-level `ledger_v1_utc_timestamp` profile for ledger event
  timestamps. It preserves proleptic-Gregorian year `0000`, ordinary UTC
  seconds, and normalized arbitrary-precision nonzero fractions, but rejects
  every `second = 60` because Stage 4a pins no immutable leap-second table.
  This narrows ledger schema acceptance without changing
  `pit_canonical_json_v1` serialization.
- Keep the independently retained evidence-closure checkpoint separate from a
  second exact `campaign_adjudication_checkpoint_v1`. The latter anchors the
  final adjudication event and therefore the complete closure, review,
  promotion/disposition, and adjudication chain. Its preallocated checkpoint
  ID avoids a digest cycle; its generation and predecessor ID/hash form a
  monotone lineage. Any later event scoped to that campaign makes the prior
  adjudication checkpoint non-current and requires a new complete cycle and
  successor checkpoint. An unrelated campaign or truly ledger-global suffix
  does not.
- Treat checkpoint latestness and anti-rollback as an external Stage 4b gate.
  Before any post-adjudication campaign action, the next generation must become
  pending under the independent `(ledger_id, campaign_id)` authority key;
  pending, missing, forked, skipped, or unverifiably current generations fail
  closed. A local old ledger plus old checkpoint cannot prove that a later
  generation was not created and then hidden.
- Allocate each ledger-owned logical typed entity ID exactly once. Later
  lifecycle, correction, supersession, review, and decision records reuse that
  ID as a typed subject or reference; only a second allocation conflicts. Event
  IDs, operation IDs, and sequences continue to identify distinct
  append/request/commit records and cannot be reused inconsistently.
- Treat event `actor_id` as an externally assigned, opaque
  claimed-attribution reference, not a ledger-owned entity allocation.
  `LEDGER_EPOCH_CREATED` atomically introduces `ledger_id`; no earlier event is
  possible. Stage 4a validates only canonical actor syntax and identity
  binding. It does not prove authenticity, control, authorization, role
  independence, currentness, or revocation, and grants no append, access,
  review, or promotion permission. Any formal behavior that depends on those
  properties remains fail closed until Stage 4b accepts an owner-approved
  external mechanism and historical activation/replacement/revocation policy.
  Stage 4a does not select that identity architecture.
- Freeze the exact common identity envelope and the synthetic
  `LEDGER_EPOCH_CREATED` payload in Stage 4a. Keep the complete
  `TRIAL_ALLOCATED` bindings and parent order as normative semantic
  requirements, but reject that event as
  `SCHEMA_INCOMPLETE_DIAGNOSTIC_ONLY` until Stage 4b accepts a complete
  machine-readable per-event payload-schema registry.
- Keep execution state separate from charter candidate evidence state.
- Keep the full ledger private and repository-external; expose only a
  deterministic allowlisted public projection without paths, credentials, raw
  values, directions, magnitudes, ranks, or private performance.

Rationale:

- Complete multiplicity and failure accounting is necessary before statistical
  evidence can be interpreted.
- Separate trials and attempts prevent infrastructure retries from either
  inflating configuration multiplicity or concealing failed executions.
- Prospective access barriers and monotone sample downgrades prevent
  after-the-fact holdout laundering.

Consequences:

- Stage 4a is a documentation/golden-contract stage only. It adds no runtime,
  database, migrated log, research trial, private access, generated performance
  evidence, dependency, or trading behavior.
- Stage 4a's epoch golden and non-append semantic fact vectors do not establish
  contract-wide payload validation or Stage 4b conformance.
- Stage 4a's adjudication-checkpoint vectors establish exact identity, lineage,
  chain anchoring, and staleness semantics only. They do not implement an
  independent currentness authority or make a campaign formally complete.
- Stage 4a's evidence-checkpoint vector uses one fixed all-excluded trial and
  zero attempts to prove exact prefix/checkpoint bytes and set/count
  relationships. General event payload, scope, inventory, and lifecycle
  extraction remains fail closed until the Stage 4b registry is accepted.
- Legacy logs remain `DIAGNOSTIC_ONLY` references and cannot prove formal
  completeness or holdout independence.
- Stage 5 remains blocked until Stage 4b implements and behaviorally verifies
  the accepted contract.

Follow-up:

- In the first separate Stage 4b slice, freeze the complete machine-readable
  event payload-schema registry, deterministic positive/negative vectors, and
  registry digest. Then choose and justify the storage, transaction/recovery,
  private-location, independent checkpoint/currentness authority, append-only
  anti-rollback, concurrency/fork, signature/authorization, and recovery
  policies in separately reviewable architecture/implementation work; add
  fault, restart, concurrency, tamper, rollback, protected-access, closure, and
  privacy tests before integrating one synthetic workflow.

## 2026-07-27 - Separate Data Methodology, Dataset, And Interpretation Gates

Context:

- Protected `main` at `8a352d3` implements the purged split and explicit
  signal/execution timing contracts, but the repository has no accepted
  provider-agnostic authority for deciding whether a historical dataset is
  point-in-time, licensed, reproducible, privacy-safe, or suitable for formal
  interpretation.
- Existing local-CSV loaders and diagnostics validate selected shapes and
  calculations only. They do not prove historical membership, permanent
  identifiers, delistings, corporate actions, field availability/revisions,
  calendar alignment, benchmark/risk-free suitability, or immutable lineage.
- Private diagnostics previously calculated and reviewed the interval
  2025-05-01 through 2026-05-31.

Decision:

- Adopt `docs/point_in_time_data_methodology_contract.md` as the proposed Stage
  3 provider-agnostic contract.
- Keep `methodology_contract_accepted`, `dataset_manifest_reviewed`, and
  `formal_interpretation_eligible` as separate review decisions. The first
  never implies the second, and the second never implies the third.
- Require immutable content and ordered-manifest hashes, evidence-backed
  license state, versioned canonicalization and environment identity,
  transformation lineage, permanent/listing identifiers, bitemporal membership
  and field availability, corporate-action and delisting treatment, compatible
  price/volume semantics, typed missingness, versioned calendars,
  benchmark/risk-free policy, private/public projections, and an immutable
  exact-version review decision from an authorized non-producing reviewer
  before a dataset-specific review can pass.
- Define `pit_canonical_json_v1` as typed NFC/timestamp/decimal preprocessing
  followed by exact RFC 8785/JCS serialization, with contract and review
  decisions bound to reproducible content/protected-merge identities.
- Classify 2025-05-01 through 2026-05-31 as
  `historical_evaluation`. It cannot later be upgraded to a pristine holdout.
- Assign append-only trial and protected-sample access enforcement to Stage 4.
  Stage 3 defines the record schema and anti-backfill rules but does not claim
  to implement them.
- Treat access to asset/benchmark paths and other inputs capable of
  reconstructing protected outcomes as exposure. Public records carry only
  allowlisted policy states, publication-approved hashes or redacted evidence
  references, and never restricted license evidence or private metric values.

Rationale:

- A general methodology can be reviewed without selecting a vendor or reading
  private values, while a concrete dataset and run still require independent
  evidence.
- Separate gates prevent a loader check, hash, license assertion, static
  cohort, or completed checklist from being mistaken for historical validity.
- Conservative sample classification preserves falsifiability after prior
  exposure.

Consequences:

- Stage 3 is documentation and workflow-control only. It adds no provider,
  downloader, credential, source-data artifact, factor, research result,
  dependency, or trading capability.
- Existing static-universe EODHD work remains `DIAGNOSTIC_ONLY`; no current
  dataset becomes `formal_ready`.
- Formal real-data interpretation remains blocked until a dataset manifest,
  Stage 4 all-trial/access ledger, Stage 5 statistical protocol, and every
  applicable downstream gate pass.

Follow-up:

- Complete Stage 4 as a small reviewable experiment/trial-ledger stage after
  the Stage 3 PR is protected-merged and its exact merge-head CI passes.

## 2026-07-27 - Require Tracked Pre-Mutation Backtest Source Provenance

Context:

- Pandas may promote an entire homogeneous real column to `complex128` after
  one complex assignment.
- Assigning `1+0j` before the evaluation window and assigning the same value
  inside it can produce byte-equivalent final frames. A post-hoc dtype or cell
  snapshot cannot identify which coordinate was written.
- Stage 2 requires both strict bounded-complex rejection and invariance to
  values that are provably outside the bounded accounting window.

Decision:

- Require `source_provenance` on every `run_long_only_backtest` call; provide no
  default or compatibility bypass.
- Treat capture as a caller-declared baseline after final panel construction.
  Enforcement begins at that call and cannot infer mutation/type history
  already erased beforehand.
- Bind each library-issued handle to its role, exact axes, original semantic
  cell/dtype state, current source identity/state, and an immutable chained
  mutation ledger.
- Require any later source write to use the controlled coordinate API.
  Untracked writes, copied/replaced source objects, stale axes, swapped roles,
  malformed records, or replay-inconsistent state fail with
  `source_provenance_invalid`.
- Recover an originally real column promoted to complex only when the ledger
  records a complex write outside the current bounds and each recovered bounded
  cell matches its original real or IEEE-NaN semantics losslessly. Native
  complex sources, bounded complex writes, and lossy conversions retain their
  signal or price domain failure.
- Emit only the allowlisted provenance policy/status strings in result
  metadata. Reject direct and nested provenance objects at the experiment-log
  serializer and scan current committed logs for private field names. Extracted
  primitive values or reconstructed plain mappings remain caller-controlled.

Rationale:

- Mutation-time coordinates are the minimum evidence that distinguishes the
  identical-frame counterexample; dtype-only or snapshot-only provenance is
  information-theoretically insufficient.
- Required provenance avoids a permissive legacy path and makes every current
  caller state its source-construction boundary.
- Internal snapshots are software-control evidence, not vendor lineage,
  point-in-time proof, or research validity.
- The contract proves controlled post-capture history only; it cannot establish
  what happened before the caller-declared baseline.

Consequences:

- The backtest API is intentionally breaking for callers that omit
  provenance.
- Arbitrary pandas mutation after capture invalidates the handle; callers that
  need a controlled test mutation must use the tracked API.
- This closes the Stage 2b provenance decision without adding a dependency,
  changing a factor, reading private results, or creating a research trial.
- The trust boundary is an in-process library-issued handle, not cryptographic
  proof against a malicious caller.

Follow-up:

- Complete the Stage 2b local gates, independent read-only review, GitHub CI,
  and final stable-head Codex review before any protected merge.

## 2026-07-26 - Freeze Signal, Execution, and Metric Timing

Context:

- Protected `main` at `202273b` contains the Stage 1 implementation and a
  637-test software baseline.
- `run_long_only_backtest()` describes every signal as available after its
  timestamp's close but accepts zero lag, silently reindexes signals, and uses
  execution-close price validity while forming target membership.
- A lag-one target set on row `t` is installed only after the return ending on
  `t`; it first earns the return ending on the next source row.
- Annualized return, volatility, Sharpe, tracking error, drawdown, benchmark,
  and warm-up handling do not yet share one declared evaluation anchor.

Decision:

- Adopt `after_close_signal_next_observed_close_v1` as the only timing policy
  for the current close-only backtester.
- Conservatively treat every generic final signal as available strictly after
  its stamped close. Require a non-boolean integer accounting-row lag of at
  least one; lag zero is not a hidden same-close or next-open model.
- Distinguish the full source index `s[0..M]` from the exact bounded accounting
  slice `a[0..N]`. For every scheduled execution `a[j]`, map lag `L` to source
  signal `a[j-L]` and freeze the target immediately after that signal becomes
  available. Pre-anchor `s` rows may support feature calculation but cannot
  satisfy execution lag. Under daily rebalancing, fixture `d0` as `a[0]` maps
  to an idealized target reset at `d1`/`a[1]` close and its first earned return
  over `(d1,d2]`.
- Require exact signal/price axes and timezone compatibility. Freeze ranking,
  selection, constraints, and intended weights from decision-time
  information; execution-close feasibility cannot rerank or redistribute, and
  available signals must be real numeric, non-Boolean, and finite, with only
  IEEE `NaN` denoting an unavailable score. Every held incoming-price endpoint
  and nonzero buy or sell execution leg requires a real numeric, non-Boolean,
  finite, strictly positive price without coercion.
- Preserve the drift-aware order: prior holdings earn the incoming return,
  drift to pre-trade weights, trade to the frozen target, incur close-time
  costs, and become post-trade holdings for the next return.
- Require explicit bounded `evaluation_start` and `evaluation_end`.
  `evaluation_start` is a zero initialization anchor; all period-return metrics
  and benchmark-relative metrics use the same later rows. Bounds must be exact
  scalar timestamps resolved to unique integer positions; partial-label
  strings, implicit rounding, timezone conversion, and non-inclusive slicing
  are invalid.
- Fix daily annualization at a non-boolean integer 252 so basic and
  benchmark-relative metrics cannot use conflicting annualizers.
- Include initial capital in drawdown, keep the benchmark cost-free on the
  identical measured window, and retain the observed-bucket terminal target,
  cost, open-holdings, and no-future-return convention.
- Compute tracking error only from strategy net and cost-free benchmark returns
  selected by exact `measured_return_dates`. Preserve the public helper's zero
  benchmark anchor; a nonzero strategy-anchor sentinel may appear only in a
  direct helper test proving that the anchor is excluded.
- Require initial capital to be a real numeric, non-Boolean, finite positive
  scalar. Validate finite gross return and a finite positive gross multiplier
  before pretrade division, drift, trades, or costs; validate finite net return,
  a finite positive net multiplier, and finite positive resulting equity after
  costs but before equity update, metrics, or a successful result. Direct
  metric helpers independently reject invalid equity curves and return series
  before annualization or drawdown. Failures retain distinct stable evidence
  reasons for the later immutable trial ledger.
- Require typed timing metadata and a Stage 2b event ledger over the sorted
  de-duplicated union of the initialization anchor and resolved rebalance dates.
  The anchor has no incoming interval; later insufficient-lag rows retain their
  measured all-cash incoming interval but have no execution or first-holding
  interval.

Rationale:

- A close-derived signal cannot use that same close as both its final input and
  its fill without a separately defined pre-close or auction information
  model.
- Close-only inputs can support a transparent next-observed-close simulation;
  next-open would require open prices and overnight/intraday decomposition.
- Separating frozen intent from execution feasibility prevents the execution
  close from silently changing portfolio membership.
- Explicit bounds and a shared anchor keep feature warm-up and synthetic
  initialization rows from contaminating strategy-versus-benchmark metrics.
- Separating pretrade gross failure, post-cost net/equity failure, and
  downstream metric-input validation prevents invalid division, complex
  annualization, and misleading successful evidence.

Consequences:

- `docs/signal_execution_timing_contract.md` is the implementation authority
  for Stage 2b.
- Stage 2a does not fix runtime behavior. Zero lag, silent alignment,
  execution-close target filtering, inconsistent metric anchors, and untyped
  metadata remain visible implementation gaps until Stage 2b. The accepted
  signal/incoming/execution-price, capital-validity, and direct metric
  equity/return failure boundaries are also pending.
- Existing Stage 1 one-row price labels and same-row synthetic responses remain
  diagnostic targets, not strategy returns under this execution policy.
- The local model remains idealized close-reset accounting, not MOC, order,
  fill, capacity, brokerage, or LEAN evidence.
- This stage creates zero research trials, changes no factor or result, opens
  no private data, and authorizes no paper or live behavior.

Follow-up:

- Implement the 14-case deterministic timing matrix test-first in Stage 2b,
  migrate every current backtest caller, regenerate only changed synthetic
  artifacts, and pass full CI and final current-head review before merge.

## 2026-07-26 - Freeze The Purged And Bounded Split Contract

Context:

- Protected `main` at `57f3db3` contains the Research Charter Reset and a
  594-test software baseline.
- `make_train_validation_test_split()` still has implicit starts, rejects a
  bounded `test_end`, and cannot retain source history outside the split axes.
- Both current price-derived diagnostic workflows calculate forward returns on
  the complete panel before slicing by signal date. The local fixture workflow
  also calculates unsplit diagnostics from those targets.

Decision:

- Require six explicit inclusive train/validation/test boundaries and allow
  recorded gaps.
- Treat `test_end` as a hard information cutoff even when later source rows
  exist. No post-test value may complete a test label.
- Define price-derived row-horizon labels by exact `signal_date`,
  `label_start`, and `label_end`; purge every label whose complete interval is
  not contained in one configured window.
- Require typed label-kind and derivation metadata. Existing synthetic split
  responses use exact same-row `[t,t]` intervals and cannot claim a price
  forward-return horizon.
- Keep raw split axes visible and mask purged or embargoed target rows to
  `NaN`. Preserve zero-eligible windows as visible `INVALID` evidence.
- Keep purge and optional row-based embargo as independent recorded flags. A
  preregistered explicit gap can satisfy embargo, with exact transition sets
  and partial-gap behavior recorded.
- Record exact feature warm-up dates, in-window purged label warm-down dates,
  ignored post-test dates, and per-candidate exclusion reasons.
- Separate structural eligibility from consumer-level valid/missing target
  cells and usable factor-label pairs; retain `no_usable_label_pairs`.
- Require post-test and cross-boundary mutation-invariance tests before Stage
  1b can be accepted, including independent raw asset and benchmark mutation.

Rationale:

- Non-overlapping signal-date rows do not isolate samples when a target still
  reads a later split's prices.
- A hard information cutoff is the narrow interpretation consistent with the
  charter rule that a complete label interval must belong to one split.
- Masking rather than dropping exclusions keeps sample failures and raw date
  counts auditable without exposing invalid label values to metrics.

Consequences:

- `docs/purged_bounded_split_contract.md` is the implementation authority for
  Stage 1b.
- The current code defects remain present until Stage 1b; this design does not
  validate or reinterpret any existing diagnostic.
- Stage 2 execution timing, nonzero-embargo selection, walk-forward folds,
  point-in-time data, and empirical thresholds remain deferred.
- This stage creates zero research trials, reads no private values, and changes
  no factor, label, strategy, portfolio, cost, benchmark, or LEAN behavior.

Follow-up:

- Implement the contract test-first in Stage 1b, migrate every current
  future-return consumer, regenerate only affected synthetic evidence, and run
  the full current-head validation and review gates.

## 2026-07-26 - Reset The Research Program Around Evidence Gates

Context:

- The verified `a1486ea` baseline is a strong deterministic simulated research
  toolkit, but its prior objective and roadmap do not cover a research-grade
  factor-to-portfolio validation program.
- Read-only audits confirmed cross-split forward labels, ambiguous zero-lag
  after-close execution, fixed-cohort data limitations, incomplete
  all-trial/statistical controls, and prior diagnostic access to the proposed
  2025-05-01 through 2026-05-31 evaluation interval.

Decision:

- Adopt `docs/research_program_charter.md` as the canonical long-term evidence
  policy and keep `docs/current_roadmap.md` as the active stage sequence.
- Separate factor, strategy, portfolio, and execution evidence.
- Require point-in-time data methodology, bounded/purged samples, immutable
  trial accounting, dependence/multiple-testing controls, frozen evaluation,
  and independent reproduction before later LEAN parity candidacy.
- Treat a static or otherwise unverified historical universe as diagnostic
  only, even when its survivorship caveat is documented.
- Keep `EXPERIMENT_LOG.md` as a diagnostic/legacy record until Stage 4 provides
  immutable pre-execution identifiers and complete all-trial retention.
- Require any applicable Codex review to complete on the current head with no
  unresolved actionable findings before auto-merge or normal protected merge;
  an actionable fix requires stable CI and re-review on the new head.
- Classify previously examined data as historical evaluation or pseudo-holdout
  unless a holdout exposure ledger proves a narrower claim.
- Keep the current phase research-only. Paper runtime, live trading, brokerage,
  credentials, and orders remain unauthorized.

Rationale:

- Software reproducibility does not by itself establish empirical validity.
- Adding factors or parameters before timing, data, trial, and inference
  controls would increase hidden research degrees of freedom.
- A precise evidence taxonomy prevents diagnostic calculations from being
  promoted as strategy, portfolio, or deployment evidence.

Consequences:

- The next stage is the purged and bounded split contract, not factor
  expansion, data interpretation, or LEAN work.
- PR #148 remains an independent Draft because it changes only `AGENTS.md`;
  this charter stage avoids that file and does not alter the PR.
- This decision creates no research trial and reads no private performance
  values.

Follow-up:

- Complete Stage 1a design for split boundaries, label ownership, purge,
  optional embargo, and warm-up/down metadata before timing implementation.

## 2026-07-11 - Attribute Episode Returns From Signed Trades

Context:

- Daily positive-return frequency cannot represent holding-episode hit rate.
- Partial resizing and applied trading costs make price-only round trips
  insufficient for average holding-period return.

Decision:

- Define one episode as an uninterrupted run of positive post-trade closing
  weight for one asset; resizing continues it and re-entry after a zero close
  starts another.
- Require signed trade weights from the backtester. Define episode return as
  net portfolio contribution divided by cumulative positive deployed weight.
- Allocate applied daily costs pro rata by absolute signed trade weight. Exclude
  terminal-open episodes rather than inventing an exit.

Rationale:

- Signed trades preserve direction and let episode costs and deployed capital
  reconcile to existing turnover and cost accounting.
- The contract handles resizing without adding tax lots, fill simulation, IRR,
  or another accounting engine.

Consequences:

- Only completed episodes contribute to hit rate and average holding-period
  return; open counts remain visible in assumptions.
- Volume-impact allocation is an accounting convention, not causal impact
  estimation.
- Implementation is deferred to a separate PR.

Follow-up:

- Expose signed trades and implement the two approved metrics with exact
  reconciliation tests.

## 2026-07-11 - Clip Position Caps Without Renormalization

Context:

- Tracking error is implemented and the next roadmap checkpoint is portfolio
  constraint design.
- The current backtester selects equal-weight long-only targets and calculates
  turnover and costs from target changes versus drifted holdings.

Decision:

- The first optional constraint is a per-position maximum applied after
  selection and before trade calculation.
- Breaching weights are clipped. Removed weight is not redistributed or
  renormalized; it remains explicit non-interest-bearing cash.
- Liquidity eligibility remains upstream, while turnover and costs use the
  constrained targets.

Rationale:

- Holding cash preserves the cap without silently changing selection or
  manufacturing exposure to other assets.
- A single narrow constraint can be tested against the existing accounting
  path without implying a general production risk engine.

Consequences:

- Infeasible fully invested targets are valid partial-cash portfolios.
- Sector, factor, beta, volatility, liquidity, and tracking-error constraints
  require separate designs.
- `src/risk/constraints.py` remains placeholder-only until the implementation
  checkpoint is accepted and started.

Follow-up:

- Implement the approved helper and backtester integration in a separate PR.

## 2026-06-29 - Keep EODHD Diagnostics Brief Neutral

Context:

- PR #126 added a private limited factor diagnostics review that may contain
  diagnostic values.
- The next checkpoint needs a brief that can describe diagnostic direction,
  magnitude, and split consistency.
- The brief must not become strategy, portfolio, investment, alpha,
  profitability, or trading-readiness interpretation.

Decision:

- Add `research/eodhd_limited_factor_diagnostics_brief.py` as a
  private-output-only neutral diagnostics brief runner.
- Read the private limited review JSON and write the real-data brief only under
  `<private_data_root>/eodhd_first_dry_run`.
- Commit synthetic tests and aggregate-count docs only; do not commit private
  logs, private market data, or private diagnostic values.

Rationale:

- Neutral direction, magnitude, and split-consistency labels make diagnostics
  easier to inspect without converting them into performance or investment
  claims.
- Keeping the brief private preserves the local-data boundary while allowing
  audited continuation.

Consequences:

- Future work must preserve the no-strategy/no-performance boundary unless a
  separate reviewed checkpoint explicitly changes scope.
- Strategy runs, backtests, portfolios, PnL, Sharpe, drawdown, trading metrics,
  investment recommendations, profitability claims, alpha claims, and
  trading-readiness language remain out of scope.

Follow-up:

- Decide whether another metadata-only methodology/data-readiness checkpoint is
  needed before any broader research interpretation.

---

## 2026-06-28 - Keep Limited Factor Diagnostics Non-Interpretive

Context:

- PR #125 added a private readiness review with
  `ready_for_limited_factor_diagnostics_review=True`.
- The next checkpoint may inspect already-computed diagnostics, but only inside
  the allowed diagnostics scope.
- The review must not become strategy, portfolio, investment, alpha,
  profitability, or trading-readiness interpretation.

Decision:

- Add `research/eodhd_limited_factor_diagnostics_review.py` as a
  private-output-only limited diagnostics review runner.
- Summarize only factor coverage, factor missingness, IC, Rank IC, quantile
  spread, and split labels.
- Write the real-data limited review only under
  `<private_data_root>/eodhd_first_dry_run`.
- Commit synthetic tests and aggregate-count docs only; do not commit private
  logs, private market data, or private diagnostic values.

Rationale:

- The readiness review proves the metadata gate is ready for a limited review.
- Keeping the review private and non-interpretive allows diagnostics to be
  inspected without converting them into performance or investment claims.

Consequences:

- Future work must preserve the no-strategy/no-performance boundary unless a
  separate reviewed checkpoint explicitly changes scope.
- Strategy runs, backtests, portfolios, PnL, Sharpe, drawdown, trading metrics,
  investment recommendations, profitability claims, alpha claims, and
  trading-readiness language remain out of scope.

Follow-up:

- Decide whether another metadata-only methodology/data-readiness checkpoint is
  needed before any broader research interpretation.

---

## 2026-06-28 - Keep EODHD Readiness Review Narrow

Context:

- PR #124 added a private experiment-log/readiness handoff for the EODHD
  factor diagnostics dry run.
- The next checkpoint needs to decide only whether the metadata is ready for a
  future limited factor-diagnostics review.
- The review must not become strategy readiness, alpha readiness, trading
  readiness, live-use readiness, or performance interpretation.

Decision:

- Add `research/eodhd_factor_diagnostics_readiness_review.py` as a
  private-output-only readiness runner.
- Name the readiness field `ready_for_limited_factor_diagnostics_review`.
- Write the real-data readiness review only under
  `<private_data_root>/eodhd_first_dry_run`.
- Commit synthetic tests and aggregate-count docs only; do not commit private
  logs, private market data, or private diagnostic values.

Rationale:

- A narrow metadata gate proves the required artifacts and guardrails exist
  before any human or future script inspects factor diagnostics.
- Avoiding broader readiness names prevents the checkpoint from being mistaken
  for strategy, alpha, trading, or live-use approval.

Consequences:

- Future work may inspect factor diagnostics only inside the explicitly limited
  no-strategy/no-performance boundary.
- Strategy runs, backtests, portfolios, PnL, Sharpe, drawdown, trading metrics,
  profitability claims, alpha claims, and trading-readiness language remain out
  of scope.

Follow-up:

- If continuing, perform a limited factor-diagnostics review that preserves the
  no-strategy/no-performance boundary.

---

## 2026-06-28 - Keep EODHD Factor Diagnostics Experiment Logs Private

Context:

- PR #123 added a private-output-only EODHD factor diagnostics dry run and
  wrote the real-data diagnostics summary under the private bundle.
- The next checkpoint needs an experiment-log/readiness handoff before anyone
  interprets the factor diagnostics.
- The handoff must record private paths, row counts, date range, allowed
  diagnostics, forbidden interpretations, `adjusted_close` policy, and
  static-universe survivorship caveats without committing private market data.

Decision:

- Add `research/eodhd_factor_diagnostics_experiment_log.py` as a
  private-output-only handoff runner.
- Write the real-data experiment log and Markdown handoff only under
  `<private_data_root>/eodhd_first_dry_run`.
- Commit synthetic tests and aggregate-count docs only; do not commit private
  logs, private market data, or private diagnostic values.

Rationale:

- A structured private handoff makes readiness fields auditable while
  preserving the no-interpretation boundary.
- Keeping the runner narrow avoids adding vendor API code, strategy code, or
  new reporting abstractions.

Consequences:

- Future work can use the private experiment log as readiness input, but must
  still complete a real-data readiness review before interpreting factor
  diagnostics.
- Strategy runs, backtests, portfolios, PnL, Sharpe, drawdown, trading metrics,
  profitability claims, alpha claims, and trading-readiness language remain out
  of scope.

Follow-up:

- Complete the real-data readiness review if continuing toward interpretation.

---

## 2026-06-28 - Keep EODHD Factor Diagnostics Private-Output Only

Context:

- PR #122 checkpointed the private EODHD data-quality diagnostics dry run.
- The next functional checkpoint adds a dry run that computes Alpha#009,
  Alpha#012, IC, Rank IC, and quantile-spread diagnostics from the private
  EODHD bundle.
- These diagnostics are allowed only as research diagnostics, not strategy or
  performance evidence.

Decision:

- Add `research/eodhd_factor_diagnostics_dry_run.py` as a private-output-only
  research script.
- Write the real-data factor diagnostics summary only under
  `<private_data_root>/eodhd_first_dry_run`.
- Commit synthetic tests and aggregate-count docs only; do not commit private
  data or private diagnostic values.

Rationale:

- Existing loaders, features, diagnostics, and split helpers are sufficient for
  the checkpoint.
- Keeping private values out of repo docs preserves the privacy and
  no-interpretation boundary while still making the workflow auditable.

Consequences:

- Future work must complete a real-data readiness review or experiment-log
  handoff before interpreting the factor diagnostic values.
- Strategy runs, backtests, portfolios, PnL, Sharpe, drawdown, trading metrics,
  profitability claims, alpha claims, and trading-readiness language remain out
  of scope.

Follow-up:

- Prepare the readiness or experiment-log handoff if continuing toward
  interpretation.

---

## 2026-06-28 - Checkpoint Private EODHD Data-Quality Diagnostics

Context:

- PR #121 documented the private-output-only diagnostics dry-run boundary.
- The private EODHD no-performance data-quality diagnostics dry run passed and
  wrote
  `<private_data_root>/eodhd_first_dry_run/DATA_QUALITY_DIAGNOSTICS_DRY_RUN_SUMMARY.md`.
- The repository needs an aggregate-only checkpoint before any factor
  diagnostics are planned.

Decision:

- Add `docs/eodhd_data_quality_diagnostics_checkpoint.md`.
- Record only aggregate data-quality evidence from the private summary.
- Route the next safe stage to a docs-only factor-diagnostics plan rather than
  factor computation or performance work.

Rationale:

- Data-quality diagnostics are useful readiness evidence but are not factor or
  performance evidence.
- A repo-reviewed checkpoint preserves auditability without committing private
  market data or changing source code.

Consequences:

- Future work may plan factor diagnostics, but it must stay separate from
  returns, IC, Rank IC, quantile spreads, strategy runs, backtests, portfolio
  metrics, profitability, alpha, and trading-readiness claims until reviewed.
- Static-universe survivorship risk and EODHD adjustment-policy ambiguity
  remain visible caveats.

Follow-up:

- Prepare a narrow docs-only factor-diagnostics plan if continuing toward
  real-data factor readiness.

---

## 2026-06-28 - Checkpoint Private EODHD Loader Smoke Before Diagnostics

Context:

- PR #120 added the reviewed plan for a private validation-only EODHD loader
  smoke test.
- The private smoke test then passed outside the repository using existing
  strict loaders and wrote
  `<private_data_root>/eodhd_first_dry_run/LOADER_SMOKE_TEST_SUMMARY.md`.
- The repository needs an aggregate-only checkpoint before any diagnostics
  dry-run work is scoped.

Decision:

- Add `docs/eodhd_loader_smoke_checkpoint_and_diagnostics_dry_run_plan.md`.
- Record only aggregate loader/schema evidence from the private summary.
- Scope the next diagnostics dry run to data-quality and readiness properties
  only: coverage, calendars, missingness, duplicates, invalid values,
  zero-volume, stale-row, adjustment-policy caveats, and survivorship caveats.

Rationale:

- Loader success is useful readiness evidence but is not research
  interpretation.
- A repo-reviewed checkpoint keeps the workflow auditable without committing
  private market data or changing code.

Consequences:

- Diagnostics may proceed only inside the no-performance boundary.
- Strategy runs, backtests, factor performance, IC, Rank IC, quantile spreads,
  returns, profitability, alpha, robustness, and trading-readiness claims remain
  out of scope.

Follow-up:

- Run or document a private-output-only diagnostics dry run if it can stay
  within this boundary. If source or report changes are needed, stop for a
  separate reviewed plan.

---

## 2026-06-28 - Plan Private EODHD Loader Smoke Test Before Execution

Context:

- PR #119 recorded the completed private EODHD validation-only handoff.
- The private bundle remains outside the repository at
  `<private_data_root>/eodhd_first_dry_run`.
- The next safe boundary is a loader smoke test, but source, tests, research
  scripts, generated reports, strategy logic, and performance interpretation
  remain out of scope.

Decision:

- Add `docs/eodhd_local_csv_loader_smoke_test_plan.md` before executing the
  loader smoke test.
- Limit the future smoke test to existing strict loaders and metadata-level
  evidence: schema, row counts, date ranges, symbol coverage, missing and
  duplicate counts, invalid-value counts, OHLC consistency, and SPY benchmark
  alignment.
- Require any smoke-test summary to be written only under the private EODHD
  bundle path, not under the repository.

Rationale:

- A short reviewed plan keeps the next private-data operation auditable without
  adding code or committing private market data.
- Loader success would only prove local ingestion readiness, not strategy,
  factor, portfolio, or performance evidence.

Consequences:

- The next stage may run the validation-only loader smoke test using existing
  loaders and private output only.
- Static-universe survivorship risk, raw OHLC versus `adjusted_close`
  adjustment semantics, sample splits, cost/slippage assumptions, execution
  timing, and experiment-log interpretation remain unresolved for research
  interpretation.

Follow-up:

- After this plan merges, execute the loader smoke test only if it can stay
  inside the private-output and no-interpretation boundary.

---

## 2026-06-27 - Record Private EODHD Validation-Only Handoff

Context:

- A private EODHD local CSV bundle exists outside the repository at
  `<private_data_root>/eodhd_first_dry_run`.
- Private readiness and validation-only summaries reported loader/schema
  validation success without copying raw CSV/JSON data into the repository.
- The repository needs a reviewable handoff before any future loader-smoke-test
  stage can be scoped.

Decision:

- Add `docs/eodhd_local_csv_validation_handoff.md` as a documentation-only
  bridge from private validation evidence to a future reviewed loader smoke
  test.
- Record only aggregate evidence: provider/source, symbol coverage, date range,
  row counts, schema result, benchmark alignment, invalid-value counts, and
  credential-marker scan result.
- Preserve explicit stop-before-strategy language and keep sample split,
  cost/slippage, universe, benchmark, and EODHD adjustment-policy gaps visible.

Rationale:

- The private bundle passed validation-only checks, but that does not make it
  research evidence.
- A repo-reviewed handoff makes the next stage auditable without committing
  private market data or changing loaders, tests, research scripts, reports, or
  strategy logic.

Consequences:

- The next safe stage is a documentation/test-plan or validation-only loader
  smoke test only.
- Strategy runs, factor-performance calculations, backtests, performance
  interpretation, profitability claims, and trading-readiness claims remain
  out of scope.
- Static-universe survivorship risk and raw OHLC versus `adjusted_close`
  adjustment semantics remain unresolved caveats for any later interpretation.

Follow-up:

- Prepare a reviewed experiment-log handoff before any future output is
  interpreted beyond loader/schema readiness.
- Keep the private bundle outside the repository and do not commit raw
  CSV/JSON files.

---

## 2026-06-23 - Require An Explicit Local CSV Readiness Input Package

Context:

- PR #116 reconciled the current roadmap after the committed local fixture
  generated-output refresh.
- The next default boundary is user-provided local CSV readiness inputs.
- The user asked to continue without starting unsafe real-data work, so the
  next safe action is to make the readiness input package explicit.

Decision:

- Require an explicit readiness package before any future local CSV research
  run is loaded, transformed, reported, or interpreted as real-market evidence.
- Treat the package as metadata and planning first: scope statement,
  metadata-only inventory, schema map, readiness audit, experiment handoff
  draft, and explicit approval boundary.
- Keep the default next checkpoint paused until those inputs exist, unless the
  user requests another narrow documentation/test-plan clarification.

Rationale:

- The project can document the gate without reading private/raw local data.
- Real-data interpretation without the package would require assumptions about
  provenance, survivorship, benchmark choice, alignment, splits, costs,
  slippage, and privacy that the project guardrails forbid.

Consequences:

- Future continuations should ask for or review the readiness package before
  touching local CSV contents.
- Documentation-only readiness-template or registry-schema work remains
  possible, but it must not imply that a real-data study can proceed without
  the package.

---

## 2026-06-23 - Pause Default Work At Local CSV Readiness Boundary

Context:

- PR #115 completed the committed synthetic local fixture configured-case
  generated-output refresh.
- The synthetic and local-fixture robustness/reporting sequence now has
  reviewed plans, implementation, tests, and committed generated artifacts.
- No user-provided local CSV bundle, completed readiness audit, or experiment
  handoff is available.

Decision:

- Treat user-provided local CSV readiness inputs as the next default boundary
  before any real-data interpretation.
- Do not add more synthetic or local-fixture generated output by default.
- If the user asks to continue without local data, choose only a
  documentation/test-plan stage that clarifies readiness gates or registry
  schema choices without implying real-data validation.

Rationale:

- More synthetic output would not answer whether stock factors are verifiable
  stock-selection signals on accepted data.
- Proceeding to real-data interpretation without scope, provenance, schema,
  survivorship, benchmark, split, cost/slippage, and readiness-audit evidence
  would violate project guardrails.

Consequences:

- Future continuations should pause at the local CSV readiness boundary unless
  the user supplies the required inputs or explicitly asks for a narrow
  documentation/test-plan clarification.

---

## 2026-06-23 - Allow Protected PR Merge For Eligible Governance Stages

Context:

- The prior workflow required Codex to pause for manual merge after each PR.
- Recent checkpoint work showed that branch protection can be verified, required
  checks can be observed, and PR author/head-owner metadata can confirm the
  branch was pushed by `minqiyang`.

Decision:

- Keep PR creation mandatory for reviewability and branch protection.
- For non-high-risk PRs, allow GitHub auto-merge or normal protected PR merge
  only when GitHub metadata verifies `minqiyang` as author/head owner, branch
  protection or rulesets are verifiable, required checks pass or auto-merge is
  used for pending checks, no required review is pending, and changed-file scope
  matches the declared stage.
- Continue to stop for human review when risk is high or unclear, author/pusher
  identity cannot be verified, protection/check/review status cannot be
  verified, CI is unstable after a bounded wait, or scope is unclear.
- Continue to forbid direct pushes or direct merges to `main`, branch
  protection bypass, ruleset/check/review/merge-queue bypass, and
  `gh pr merge --admin`.

Rationale:

- GitHub-managed auto-merge and normal protected PR merge preserve PR history
  and branch protection while avoiding unnecessary manual merge gates for
  low-risk or otherwise clearly eligible stages.
- Verifying identity from GitHub metadata is safer than trusting local git
  config.

Consequences:

- Staged continuations may proceed through multiple PR-sized stages when each
  PR is eligible and GitHub merges it during the run.
- Existing paused external PR gate behavior still applies to ineligible,
  blocked, high-risk, unclear, or unverified PRs.

---

## 2026-06-12 - Treat Unmerged PR Gates As External Wait State

Context:

- A prior workflow-control rule told Codex to report an unmerged PR gate once
  and pause.
- Active-goal automatic continuations can still resume without a user-stated
  merge, resume, or inspect instruction, which caused repeated pause output for
  the same external PR gate.

Decision:

- Treat any open, closed-unmerged, unknown, or otherwise not-verified-merged PR
  gate as a paused external wait state after one concise current-state report.
- Automatic continuations without explicit user merge/resume/inspect input must
  not query GitHub again, repeat gate reports, print repeated pause notes, mark
  the goal complete, or mark the goal blocked merely because the same external
  PR remains pending.
- If the interface forces a response while paused, use only:
  `Waiting for PR #X to merge; no checks run.`

Rationale:

- A pending PR review or merge is external state, not work Codex can advance by
  rechecking the same gate.
- Completion would be false because the staged goal still depends on the merge.
- Blocked status is also too strong when the workflow is intentionally waiting
  for human review or GitHub merge completion.

Consequences:

- Conservative auto-merge remains unchanged: direct merge is forbidden, `--admin`
  is forbidden, and medium/high/unclear-risk PRs still stop for human review.
- Future staged continuations resume only after the user says the PR merged,
  asks to resume after merge, or asks to inspect the PR.

---

## 2026-06-12 - Plan Local Fixture Robustness Before Refreshing Outputs

Context:

- PR #109 merged the post-synthetic robustness generated-output checkpoint.
- That checkpoint routed the next safe stage to a documentation-only local
  fixture robustness/report refresh plan.
- The local CSV fixture workflow already has split metadata, caveats,
  synthetic-only inventory review, liquidity diagnostics, factor diagnostics,
  and diagnostic-only volume-aware slippage smoke output.

Decision:

- Add `docs/local_fixture_robustness_report_refresh_plan.md` before changing
  fixture workflow behavior or generated artifacts.
- Require future fixture robustness output to preserve all configured cases,
  every configured split, invalid or insufficient rows, deterministic ordering,
  cost/slippage assumptions, diagnostic-only volume-aware fields, and
  guardrail caveats.
- Keep generated-output refresh as a later, separately reviewed stage unless a
  future reviewed implementation scope explicitly includes it.

Rationale:

- The reviewed synthetic all-case format should be mapped onto committed local
  fixtures before another output refresh.
- Planning first reduces the risk of cherry-picked fixture diagnostics,
  hidden invalid cases, or wording that implies real-data evidence.

Consequences:

- The next implementation PR should be test-first and should prove all-case,
  all-split, invalid-row, and guardrail behavior before writing refreshed
  reports or logs.
- Real-data interpretation remains blocked until user-provided data scope,
  provenance, readiness audit, benchmark, and experiment-handoff gates are
  available.

Follow-up:

- After this plan PR merges, add focused local fixture robustness/report
  support tests and implementation without fetching data or changing
  backtester behavior.

---

## 2026-06-12 - Add Checkpoint After Synthetic Robustness Generated Outputs

Context:

- PR #108 merged the deterministic synthetic split-aware robustness Markdown
  report, JSON experiment log, and refreshed experiment registry.
- The current handoff routes the next safe stage to a documentation or
  research-process checkpoint before any real-data interpretation.
- The older roadmap already recommends applying the reviewed robustness format
  to local fixtures only after the synthetic implementation path is complete.

Decision:

- Add `docs/post_synthetic_robustness_generated_output_checkpoint.md` as a
  documentation-only checkpoint.
- Record the completed PR #104-#108 sequence, generated-output state,
  guardrails, remaining gaps, and recommended next roadmap.
- Route the next stage toward a documentation-only local fixture
  robustness/report refresh plan before changing fixture workflows or
  generated artifacts.

Rationale:

- A checkpoint makes the post-#108 state explicit before starting another
  workflow or generated-output branch.
- The local fixture path needs a mapped plan so the all-case split summary,
  invalid rows, cost/slippage assumptions, and caveats remain visible without
  implying user-data validation.

Consequences:

- Future work should not jump directly from synthetic generated outputs to
  real-data interpretation.
- The next PR-sized stage can remain documentation-only and define fixture
  refresh requirements before any source, test, research-script, or generated
  artifact change.

Follow-up:

- After this checkpoint PR merges, create the local fixture robustness/report
  refresh plan unless current evidence or user scope changes.

---

## 2026-06-12 - Commit Synthetic Robustness Generated Outputs After Support Path

Context:

- PR #105 added the deterministic synthetic split-aware robustness demo without
  committed generated outputs.
- PR #106 added explicit report/log support with default no-output module
  execution.
- The current handoff routes the next safe stage to a scoped generated-output
  refresh if caveats, all-case fields, and invalid-case fields are verified.

Decision:

- Commit the default Markdown report and JSON experiment log for the synthetic
  robustness demo.
- Refresh the experiment registry so the new JSON log is discoverable beside
  the other synthetic demo logs.
- Keep the refresh generated-output-only and do not change implementation code
  or tests in this PR.

Rationale:

- The generated artifacts are useful review and handoff evidence only after
  the output-writing path is tested and merged.
- Committing the all-case and invalid-case output makes caveats and failure
  modes visible rather than preserving only favorable diagnostics.

Consequences:

- Reviewers can inspect the generated Markdown/JSON artifacts directly.
- These outputs remain deterministic synthetic diagnostics, not real-market
  evidence, not strategy validation, and not a profitability claim.

Follow-up:

- After this generated-output PR merges, choose the next stage from current
  evidence and avoid real-data interpretation until readiness/provenance gates
  are satisfied.

---

## 2026-06-12 - Pause After One Not-Merged PR Gate Check

Context:

- Repeated automatic continuations can keep rechecking the same previous-stage
  PR when that PR is still not merged.
- The staged workflow already requires a merge gate before starting a new
  stage and forbids Codex from merging PRs without explicit instruction.

Decision:

- Treat open, closed-unmerged, unknown, or otherwise not-verified-merged PR
  state as an immediate pause gate after one current-state status check.
- Do not repeatedly poll PR checks, reviews, branch protection, auto-merge
  eligibility, or baseline validation while that gate remains unmerged.
- Continue to sync `main` and run baseline validation only after the previous
  PR is verified merged.

Rationale:

- One authoritative status check is enough to prove the workflow cannot safely
  start the next stage.
- Repeated rechecks add noise and token cost without changing the external
  merge state.

Consequences:

- Future continuations should report the not-merged gate and pause directly.
- Explicit user requests can still inspect or update a PR, but automatic
  staged continuation should not keep reclassifying the same unmerged gate.

Follow-up:

- If a future continuation still repeats the same not-merged gate, tighten the
  controller or Skill wording further.

---

## 2026-06-12 - Add Report/Log Support Before Generated Output Refresh

Context:

- PR #105 added a deterministic synthetic split-aware robustness demo and
  focused tests, but intentionally left generated reports/logs unchanged.
- The next handoff allowed either explicit caveated report/log support or a
  generated-output refresh if deliberately scoped.

Decision:

- Add opt-in report/log support before refreshing any committed generated
  artifacts.
- Keep default module execution no-output so validation can prove support code
  exists without mutating `reports/`.
- Require the report/log path to preserve all-case diagnostics, invalid-case
  diagnostics, caveats, and separately inspectable cost/slippage assumptions.

Rationale:

- Separating output support from generated artifact refresh keeps review
  smaller and makes report/log schema and caveats testable before committing
  generated files.
- The generated-output refresh should only occur after this support path is
  reviewed.

Consequences:

- Future generated-output PRs should call the explicit output-writing path and
  review the Markdown/JSON diffs for caveats, all-case rows, invalid-case rows,
  and assumption fields.
- Real-data interpretation remains blocked by readiness, provenance,
  survivorship, benchmark/universe, and experiment-handoff gates.

Follow-up:

- After this support PR merges, consider a generated-output refresh for
  `reports/synthetic_split_robustness_demo.md`,
  `reports/experiment_logs/synthetic_split_robustness_demo.json`, and the
  experiment registry.

---

## 2026-06-12 - Implement Synthetic Robustness Demo Without Generated Outputs

Context:

- PR #104 added the plan for synthetic robustness and split-aware validation.
- The plan requires all configured cases and all configured splits to remain
  visible before any generated-output refresh.
- Generated reports and experiment logs are review-sensitive because they can
  be mistaken for stronger evidence than synthetic diagnostics support.

Decision:

- Add the first synthetic split-aware robustness implementation as a research
  helper plus focused tests only.
- Include default identity, inverse, and constant invalid signal cases so the
  all-case table includes favorable, unfavorable, and invalid diagnostics.
- Preserve missing observations across synthetic transforms and record invalid
  reasons instead of silently filling or dropping cases.
- Do not write generated reports or experiment logs in this implementation PR.

Rationale:

- Keeping implementation separate from generated-output refresh makes the PR
  small and keeps review focused on deterministic behavior and guardrails.
- The constant invalid case exercises the insufficient/undefined diagnostic
  path required by the plan without requiring real data or external inputs.

Consequences:

- Future report/log support should reuse the all-case summary rather than
  recomputing or filtering cases.
- Any generated-output PR should explicitly scope output files and verify the
  caveats, all-case table, invalid-case table, and assumption fields.

Follow-up:

- After this PR merges, consider adding caveated report/log support or a
  generated-output refresh for this synthetic robustness demo.

---

## 2026-06-12 - Plan Synthetic Robustness Before Implementation

Context:

- PR #103 refreshed the roadmap and identified robustness and split-aware
  validation policy as the next original-goal gap.
- The repository already has split helpers, synthetic diagnostics, local
  fixture workflows, fixed-bps cost/slippage accounting, and a volume-aware
  diagnostic/precomputed-impact boundary.
- No user-provided local CSV bundle or real-data readiness handoff is
  available.

Decision:

- Add `docs/synthetic_robustness_validation_plan.md` before implementing any
  new robustness summary.
- Require future implementations to report every configured parameter case
  across every configured split, including invalid or insufficient cases.
- Keep transaction costs, fixed-bps slippage, and volume-aware diagnostics or
  precomputed impacts separately inspectable in future logs and reports.

Rationale:

- A plan-first stage reduces the risk of cherry-picking, accidental
  performance framing, or hidden missing-data behavior in future synthetic
  reports.
- Chronological split policy, all-case reporting, and guardrail caveats should
  be reviewed before changing research scripts or generated outputs.

Consequences:

- The next implementation stage should add deterministic tests before or with
  any synthetic robustness code.
- Generated reports/logs should remain unchanged until an explicit
  generated-output stage or implementation PR scopes them.
- Real-data interpretation remains blocked by readiness, provenance,
  survivorship, benchmark/universe, and experiment-handoff gates.

Follow-up:

- After this plan merges, consider a synthetic split-aware robustness
  implementation PR with deterministic tests and no real-data access.

---

## 2026-06-12 - Refresh Roadmap After Volume-Aware Slippage Sequence

Context:

- PR #102 checkpointed the completed volume-aware slippage design, test-plan,
  precomputed-impact implementation, and generated-log refresh sequence.
- `docs/current_roadmap_gap_refresh.md` was written earlier and still
  recommended stages that are now implemented or superseded.
- No user-provided local CSV bundle or real-data readiness handoff is
  available.

Decision:

- Refresh `docs/current_roadmap_gap_refresh.md` from current repository
  evidence.
- Keep the next recommended stage documentation-only:
  `docs/synthetic_robustness_validation_plan.md`.
- Do not proceed directly to new source code, generated-output refresh,
  real-data interpretation, LEAN runtime work, or execution-related scope.

Rationale:

- The repository now has split helpers, synthetic diagnostics, local fixture
  demos, backtest accounting, fixed-bps cost/slippage, and a precomputed
  volume-aware slippage boundary.
- The next original-goal gap is robustness and split-aware validation policy:
  all-case reporting, split windows, benchmark assumptions, cost/slippage
  assumptions, and no-best-only filtering.
- A documentation plan is lower risk than implementation and keeps the next
  code or generated-output stage reviewable.

Consequences:

- Future continuations should route through the updated roadmap and handoff.
- User-provided local CSV interpretation remains blocked by readiness-audit,
  provenance, alignment, benchmark/universe, and experiment-handoff gates.
- GitHub auto-merge may be considered only for clearly low-risk PRs with
  verifiable protections; otherwise stop for human review.

Follow-up:

- After this roadmap refresh PR merges, add a documentation-only synthetic
  robustness and split-aware validation plan.

---

## 2026-06-11 - Checkpoint Completed Precomputed Volume-Aware Slippage Sequence

Context:

- PR #98 added the documentation-only integration design.
- PR #99 added the documentation-only integration test plan.
- PR #100 added the precomputed-impact backtester path with
  `diagnostic_only` as the default.
- PR #101 refreshed affected synthetic JSON experiment logs so full metrics
  payloads include `total_volume_aware_slippage_cost_impact: 0.0` in default
  diagnostic mode.

Decision:

- Add a documentation-only checkpoint for the completed design, test-plan,
  implementation, and generated-log sequence.
- Keep the next stage documentation-only by routing to a post-volume-aware
  roadmap gap refresh before any new code or generated-output stage.
- Preserve the current boundary: no real data, no vendor APIs, no credentials,
  no brokerage, no live or paper trading, no order execution, and no
  profitability claims.

Rationale:

- The volume-aware slippage path now has design, tests, implementation, and
  refreshed synthetic logs, so future stages need a current roadmap rather
  than another integration step by default.
- The older `docs/current_roadmap_gap_refresh.md` predates several completed
  split, liquidity, fixed-bps slippage, volume-aware diagnostic,
  precomputed-impact, and generated-log stages.
- A checkpoint keeps the audit trail explicit before selecting the next
  research-pipeline milestone.

Consequences:

- Future continuations should not treat volume-aware slippage as real-data
  capacity evidence or execution realism.
- User-provided local CSV interpretation remains blocked by readiness-audit,
  provenance, alignment, and experiment-handoff gates.
- The next recommended PR-sized stage is a documentation-only roadmap gap
  refresh.

Follow-up:

- After this checkpoint PR merges, refresh the current roadmap gap document
  from latest repository evidence before choosing additional implementation
  work.

---

## 2026-06-11 - Refresh Synthetic Logs For Default Volume-Aware Metric

Context:

- PR #100 added a precomputed volume-aware slippage boundary to the local
  backtester while keeping `volume_aware_slippage_mode="diagnostic_only"` as
  the default.
- The implementation added a separate
  `total_volume_aware_slippage_cost_impact` metric, with default diagnostic
  value `0.0` when no precomputed impact is applied.
- The current handoff recommended a synthetic generated-output review or
  refresh after PR #100 merged.

Decision:

- Refresh only committed synthetic experiment logs that serialize the full
  backtester metrics payload and therefore need the new default metric field.
- Keep unchanged generated artifacts unchanged when reruns produce no diff.
- Do not modify source code, tests, research scripts, backtester behavior,
  metrics logic, data loaders, diagnostics helper behavior, generated Markdown
  reports, the experiment registry, real-data workflows, or LEAN/runtime code
  in this generated-output PR.

Rationale:

- The committed logs should match the current deterministic synthetic
  backtester schema so downstream registry, report, and audit readers do not
  see stale metric payloads.
- A separate generated-output PR keeps schema refresh diffs from obscuring the
  PR #100 implementation review.
- A `0.0` volume-aware slippage metric in default diagnostic mode is an audit
  field, not a claim about execution realism, real-data capacity, or
  profitability.

Consequences:

- `reports/experiment_logs/synthetic_momentum_demo.json` and
  `reports/experiment_logs/synthetic_combined_score_backtest_demo.json` carry
  the new default metric.
- The synthetic parameter sweep, Markdown reports, and experiment registry do
  not change in this stage because reruns produced no committed diffs there.
- User-provided local CSV interpretation remains blocked by readiness-audit,
  provenance, alignment, and experiment-handoff gates.

Follow-up:

- After this generated-log refresh PR merges, run a documentation-only
  checkpoint for the completed precomputed volume-aware slippage implementation
  plus generated-log refresh sequence before any new code, real-data, or
  LEAN/runtime stage.

---

## 2026-06-11 - Add Precomputed Volume-Aware Slippage Backtester Boundary

Context:

- PR #99 added the documentation-only test plan for volume-aware slippage
  backtester integration.
- The reviewed design and test plan both recommend keeping helper calculation
  outside the backtester and using a precomputed impact boundary for the first
  implementation.

Decision:

- Add a narrow `apply_precomputed_impact` path to `run_long_only_backtest()`.
- Keep `volume_aware_slippage_mode="diagnostic_only"` as the default.
- Add a separate `volume_aware_slippage_costs` result series, separate metrics,
  and explicit assumption fields for applied volume-aware slippage metadata.
- Reject positive fixed-bps slippage plus positive applied volume-aware impact
  by default to avoid hidden double counting.
- Do not make the backtester compute rolling dollar volume, read OHLCV panels,
  fetch data, use vendor APIs, connect to brokers, or place orders.

Rationale:

- A precomputed series keeps date alignment, notional scale, volume policy,
  missing/zero/stale liquidity policy, and participation-cap handling in the
  diagnostic helper boundary.
- Separate result and metric fields keep fixed transaction costs, fixed-bps
  slippage, volume-aware candidate slippage, and total trading impact
  inspectable.
- The default diagnostic mode preserves existing behavior unless callers
  explicitly opt into applied precomputed impact with required metadata.

Consequences:

- Future generated reports and experiment logs may need a separate refresh or
  review stage so new metrics and audit fields are visible and caveated.
- User-provided local CSV interpretation remains blocked by readiness-audit,
  provenance, alignment, and experiment-handoff gates.

Follow-up:

- After this implementation PR merges, review and refresh affected synthetic
  generated outputs in a separate PR if the diff confirms new default fields.

---

## 2026-06-11 - Require Tests Before Volume-Aware Slippage Backtester Implementation

Context:

- PR #98 added the documentation-only backtester integration design for
  volume-aware slippage.
- The design recommends keeping `diagnostic_only` as default and using a
  precomputed-impact boundary if volume-aware slippage is later applied to
  simulated returns.
- No source code, tests, research scripts, generated reports, backtester
  behavior, metrics behavior, or diagnostics behavior changed in this stage.

Decision:

- Add `docs/volume_aware_slippage_backtester_integration_test_plan.md` as the
  acceptance checklist before any implementation.
- Require deterministic unit, integration, failure-mode, guardrail, result
  field, audit field, report-field, and experiment-log tests before or with any
  future code-changing integration PR.
- Keep generated reports unchanged until after a future implementation is
  reviewed and merged.

Rationale:

- Applying volume-aware slippage to net returns is an accounting change, not a
  documentation detail.
- Tests must prove date alignment, separate cost/slippage inspection, zero
  diagnostic behavior, invalid-liquidity failures, and no double counting
  before behavior changes.
- A test plan keeps the next implementation PR smaller and less ambiguous.

Consequences:

- The next possible implementation must keep helper calculation outside the
  backtester, keep `diagnostic_only` as default, and add deterministic tests in
  the same PR.
- Implementation must stop for missing, zero, stale, or incomplete volume
  ambiguity; invalid notional; excessive participation; ambiguous fixed-bps
  plus volume-aware slippage semantics; real-data needs; vendor APIs;
  credentials; brokerage; live or paper trading; order execution; or
  profitability language.

Follow-up:

- After this test-plan PR merges, consider a narrow code-changing
  precomputed-impact implementation PR with deterministic tests and no
  generated-output refresh.

---

## 2026-06-11 - Define Volume-Aware Slippage Backtester Integration Boundary

Context:

- PR #97 merged the post local fixture slippage output refresh checkpoint.
- The repository has a standalone volume-aware slippage diagnostic helper and
  synthetic/local-fixture outputs that report participation and rejected/cap
  counts.
- Candidate volume-aware slippage is still not applied to simulated backtester
  net returns.

Decision:

- Add `docs/volume_aware_slippage_backtester_integration_design.md` as the
  reviewed boundary before any future net-return integration.
- Keep volume-aware slippage diagnostic-only by default.
- If implemented later, prefer a precomputed-impact boundary: compute the
  diagnostic outside the backtester, pass an aligned
  `portfolio_slippage_impact` series plus audit metadata into the backtester or
  wrapper, and deduct it from net returns only under an explicit opt-in.
- Defer internal backtester calculation from price and volume panels until a
  separate design justifies making the backtester own OHLCV semantics.

Rationale:

- Applying volume-aware slippage to returns would change cost accounting and
  report interpretation.
- A precomputed-impact boundary keeps volume validation, notional scale, lagged
  dollar-volume construction, stale-volume handling, and participation caps
  auditable before net-return behavior changes.
- Fixed-bps slippage and volume-aware candidate slippage can be double-counted
  unless a reviewed rule blocks or explicitly permits combination.

Consequences:

- Source code, tests, research scripts, generated reports, loaders, backtester
  behavior, metrics behavior, diagnostics behavior, LEAN code, and real-data
  access remain unchanged in this stage.
- Any future implementation must define strict defaults and stop conditions for
  missing volume, zero volume, stale volume, invalid notional, and excessive
  participation before touching returns.
- Reports and experiment logs must distinguish transaction costs, fixed-bps
  slippage, volume-aware candidate slippage, total trading impact, diagnostic
  flags, and caveats.

Follow-up:

- After this design merges, the next safe stage is a documentation-only
  backtester integration test plan, not implementation.
- Stop if a later stage needs real data, downloads, vendor APIs, credentials,
  brokerage, live or paper trading, order execution, silent missing-data repair,
  or profitability claims.

---

## 2026-06-11 - Require Design Before Volume-Aware Slippage Net-Return Integration

Context:

- PR #90 added the volume-aware slippage design boundary.
- PR #91 added the standalone synthetic-only diagnostic helper.
- PR #92 added a committed synthetic local CSV fixture smoke diagnostic.
- PR #93 checkpointed the smoke diagnostic before generated-output refresh.
- PR #94 refreshed the committed synthetic local CSV fixture report, JSON
  experiment log, and experiment registry with the diagnostic outputs.
- None of those stages applied candidate volume-aware slippage to simulated
  portfolio returns.

Decision:

- Treat the volume-aware slippage design/helper/smoke/output-refresh sequence
  as complete at the diagnostic artifact level.
- Require a separate documentation-only integration design before any future
  stage changes `run_long_only_backtest()`, metrics, reports, or generated
  logs so volume-aware slippage affects simulated net returns.

Rationale:

- Net-return accounting needs explicit semantics for gross returns, fixed
  transaction costs, fixed-bps slippage, candidate volume-aware slippage,
  rejected/capped trades, zero-slippage diagnostics, and caveats.
- A design gate is lower risk than implementation and keeps the next PR
  reviewable.
- Synthetic/local fixture diagnostics are useful for plumbing and audit
  visibility, but they are not real-data evidence or profitability support.

Consequences:

- The next safe stage after the checkpoint can be a documentation-only
  volume-aware slippage backtester integration design.
- Source code, tests, research scripts, generated reports, and backtester
  behavior should remain unchanged until that design is reviewed.
- User-provided local CSV interpretation remains blocked by readiness-audit,
  provenance, schema, alignment, and experiment-handoff gates.

Follow-up:

- Draft `docs/volume_aware_slippage_backtester_integration_design.md` in a
  later PR after the checkpoint merges.
- Stop if the design would require real data, downloads, vendor APIs,
  credentials, live or paper trading, brokerage integration, order execution,
  silent missing-data repair, or profitability claims.

---

## 2026-06-09 - Refresh Local Fixture Outputs Before Backtester Slippage Integration

Context:

- PR #90 added the volume-aware slippage design boundary.
- PR #91 added the standalone synthetic-only diagnostic helper.
- PR #92 added a committed synthetic local CSV fixture smoke diagnostic that
  calls the helper and reports participation plus rejected/cap counts only.
- PR #92 intentionally did not refresh committed generated reports/logs and
  did not integrate volume-aware slippage into backtester net returns.

Decision:

- Treat the volume-aware design, helper, and local fixture smoke diagnostic
  sequence as complete at the code/test level.
- Before considering any backtester net-return integration, refresh the
  committed synthetic local CSV fixture generated report/log/registry in a
  separate narrow stage if the checkpoint is reviewed and merged.
- Keep any generated-output refresh synthetic-only and caveated. It may record
  participation and rejected/cap counts, but it must not treat candidate
  slippage diagnostics as real-data evidence, execution realism, or
  profitability support.

Rationale:

- The repository should not carry stale generated artifacts after a workflow
  report/log writer changes.
- Generated-output refresh is lower risk than backtester integration because
  it does not change source behavior or net returns.
- Separating artifact refresh from code changes keeps PR scope reviewable and
  prevents generated report diffs from hiding implementation changes.

Consequences:

- The next safe stage after the checkpoint can be a local fixture generated
  artifact refresh, not a new alpha, real-data study, or backtester slippage
  integration.
- Volume-aware slippage remains diagnostic-only until a later design stage
  explicitly reviews whether it should affect simulated returns.
- User-provided local CSV interpretation remains blocked by readiness-audit
  and `EXPERIMENT_LOG.md` gates.

Follow-up:

- Refresh `reports/local_csv_fixture_workflow_demo.md`,
  `reports/experiment_logs/local_csv_fixture_workflow_demo.json`, and
  `reports/experiment_registry.md` in a separate stage after this checkpoint
  merges.
- Stop if the refresh would require real data, downloads, vendor APIs,
  credentials, live or paper trading, brokerage integration, order execution,
  backtester behavior changes, or profitability claims.

---

## 2026-06-09 - Keep Volume-Aware Slippage Helper Diagnostic-Only

Context:

- PR #90 added `docs/volume_aware_slippage_design.md`.
- That design recommends a synthetic-only helper or diagnostic stage before
  any backtester net-return integration.
- The current backtester already has fixed-bps slippage, so adding a
  volume-aware path directly to `run_long_only_backtest()` would change
  strategy accounting before the new data and capacity semantics are
  independently tested.

Decision:

- Add a standalone diagnostic helper under `src/backtest/slippage.py`.
- Do not integrate the helper with `run_long_only_backtest()`,
  `calculate_basic_metrics()`, research scripts, generated reports, or local
  CSV workflows in this stage.
- Default to strict behavior: missing lagged capacity, zero or incomplete
  volume windows, zero lagged dollar volume, missing inputs, invalid notional,
  and participation above cap raise instead of being filled, clipped, or
  ignored.

Rationale:

- A standalone helper keeps the PR reviewable and makes the volume-aware
  assumptions testable before they affect simulated returns.
- Explicit `portfolio_notional` prevents normalized backtest capital from
  being mistaken for real tradable capital.
- Strict missing and zero-liquidity behavior preserves the project rule
  against silent missing-data repair.

Consequences:

- Future work can inspect participation and candidate slippage impact on
  deterministic synthetic panels without changing existing backtest output.
- Backtester integration remains a separate reviewed decision after helper
  behavior and caveats are accepted.
- User-provided local CSV interpretation remains blocked by readiness-audit
  and `EXPERIMENT_LOG.md` gates.

Follow-up:

- After this helper is reviewed and merged, consider a synthetic/local-fixture
  smoke diagnostic that reports participation and rejected/capped counts only.
- Stop if the next stage would require real data, downloads, vendor APIs,
  credentials, live or paper trading, brokerage integration, order execution,
  silent fill/clip policies, generated performance interpretation, or
  profitability claims.

---

## 2026-06-09 - Define Volume-Aware Slippage Design Boundary

Context:

- PR #85 designed fixed-bps transaction cost and slippage assumptions.
- PR #86 implemented fixed-bps slippage in the local backtester.
- PR #87 refreshed synthetic reports and logs for fixed-bps slippage fields.
- PR #88 recorded that the fixed-bps slippage path is complete and that
  volume-aware slippage requires a design gate before implementation.
- PR #89 added token-efficient workflow controls, so the current stage can use
  the handoff and repo map instead of broad repo scans.

Decision:

- Add `docs/volume_aware_slippage_design.md` as a documentation-only boundary
  before any volume-aware slippage helper, backtester integration,
  generated-output update, or local CSV interpretation.
- Treat lagged rolling dollar volume, explicit portfolio notional,
  missing/zero-volume handling, participation caps, and adjustment-policy
  compatibility as required design inputs for any future code.
- Keep same-day volume, silent missing-data repair, silent cap clipping, real
  data fetching, broker/order behavior, and execution-realism claims out of
  scope.

Rationale:

- Volume-aware slippage has higher look-ahead and interpretation risk than
  fixed-bps target-weight turnover friction.
- Current backtests are normalized research accounting; dollar-volume
  capacity requires an explicit notional scale before participation can be
  calculated.
- Zero volume, missing volume, stale volume, and incompatible price/volume
  adjustment policies can make a volume-aware estimate invalid even when the
  CSV loader accepts the rows.

Consequences:

- The next possible code stage should be a synthetic-only helper or diagnostic
  stage, not immediate backtester net-return integration.
- Any future implementation must default to strict missing/zero-liquidity and
  participation-cap behavior, with no silent fills or silent clipping.
- User-provided local CSV interpretation remains blocked until readiness audit
  and `EXPERIMENT_LOG.md` gates are complete for a specific dataset.

Follow-up:

- After this design is reviewed and merged, consider a narrow synthetic-only
  participation/slippage diagnostic helper with deterministic tests.
- Stop if implementation would require real data, downloads, vendor APIs,
  credentials, live or paper trading, brokerage integration, order execution,
  silent missing-data repair, or profitability claims.

---

## 2026-06-09 - Require Volume-Aware Slippage Design Before Implementation

Context:

- PR #85 added the simulated slippage and cost assumption design.
- PR #86 implemented the narrow fixed-bps local backtester slippage extension.
- PR #87 refreshed synthetic backtest reports, JSON logs, registry output, and
  current slippage planning docs.
- The fixed-bps path is now represented in design, code, deterministic tests,
  and synthetic generated outputs.
- Volume-aware slippage and market impact remain deferred.

Decision:

- Treat the fixed-bps slippage sequence as complete for the current synthetic
  research pipeline.
- Do not proceed directly to a volume-aware slippage helper or backtester
  extension.
- Require a documentation-only volume-aware slippage design before any
  volume-based cost/slippage implementation, generated-output update, or
  local CSV interpretation.

Rationale:

- Volume-aware slippage has higher leakage and interpretation risk than fixed
  basis-point turnover friction.
- A future model would need explicit policy for adjusted versus raw volume,
  dollar-volume alignment, lag rules, zero volume, missing volume, stale data,
  participation assumptions, liquidity caps, and benchmark/universe mismatch.
- Synthetic/local fixtures can test wiring and edge cases, but they cannot
  prove realistic execution or market impact.

Consequences:

- The next safe repository-internal stage can be a design gate for
  volume-aware slippage.
- Any future implementation must remain synthetic/local-fixture only until
  user-provided local CSV readiness gates are completed for a specific dataset.
- User-provided local CSV interpretation remains blocked by the readiness
  audit and `EXPERIMENT_LOG.md` requirements.
- No source code, tests, research scripts, reports, data access, execution
  behavior, credentials, or performance claims are changed by this decision.

Follow-up:

- Add a documentation-only volume-aware slippage design if no higher-priority
  merge gate, blocker, or stale roadmap issue appears.
- Stop before implementation if the next stage would require real data,
  downloads, vendor APIs, credentials, live or paper trading, brokerage
  integration, order execution, or profitability claims.

---

## 2026-06-09 - Require Slippage And Cost Design Before Implementation

Context:

- PR #84 merged the post-local-CSV-fixture audit rehearsal checkpoint.
- That checkpoint recommends simulated slippage and cost assumption design as
  the next repository-internal stage.
- The local backtester currently applies `transaction_cost_bps` to
  target-weight turnover, but it does not separately represent slippage or
  market impact.
- The project specification requires transaction costs, slippage, turnover,
  and execution assumptions to be explicit.

Decision:

- Add a documentation-only design before any local backtester cost/slippage
  implementation changes.
- Treat the first future implementation, if approved later, as a narrow fixed
  basis-point slippage extension on the current target-weight turnover model.
- Defer volume-aware slippage and market impact until separate policy, data,
  lag, and testing requirements are reviewed.

Rationale:

- Cost and slippage assumptions can materially affect simulated results.
- A design gate prevents a small-looking parameter addition from becoming an
  implicit execution model.
- Fixed-basis-point turnover friction is deterministic and testable, but it
  must remain caveated as simulated research accounting rather than realistic
  execution evidence.

Consequences:

- Backtester source code remains unchanged by this decision.
- Future code must keep transaction cost and slippage assumptions visible in
  outputs and logs.
- Zero-cost or no-slippage runs remain diagnostics only.
- User-provided local CSV interpretation remains blocked by the readiness
  audit and experiment-log gates.

Follow-up:

- After the design is reviewed and merged, consider a narrow synthetic-only
  implementation PR with deterministic tests for separate fixed-bps slippage.
- Stop before implementation if the next stage would require real data,
  broker fills, order execution, credential access, or performance
  interpretation.

---

## 2026-06-08 - Pause User-Provided Local CSV Work At The Readiness Gate

Context:

- PR #83 merged the committed synthetic local CSV fixture readiness audit
  rehearsal.
- The repository now has the future local CSV study plan, checklist, inventory
  validator, audit report template, and synthetic fixture rehearsal artifacts.
- No user-provided local CSV bundle, completed scope statement, completed
  checklist, completed inventory review, completed readiness audit report, or
  prepared user-data `EXPERIMENT_LOG.md` entry is available.
- Starting a user-data smoke run would require external files and human review
  decisions that are not present in the repository context.

Decision:

- Do not proceed to a user-provided local CSV smoke run by default.
- Treat local CSV user-data interpretation as blocked until the required
  bundle, checklist, inventory, readiness audit, and experiment-log gates are
  complete.
- Route the next repository-internal stage toward simulated slippage and cost
  assumption design before any cost/slippage implementation changes.

Rationale:

- The local CSV readiness artifacts are preparation gates, not evidence that a
  specific user dataset is safe to interpret.
- The original project specification requires explicit transaction costs,
  slippage, turnover, and execution assumptions.
- The current backtester has fixed basis-point transaction costs but no
  separate slippage or market-impact model; a design gate keeps that boundary
  reviewable before source code changes.

Consequences:

- Local CSV work remains synthetic, local-fixture only, or documentation-only
  until user data and completed audit artifacts are available.
- The next stage should not fetch data, add vendor APIs, add credentials, add
  live or paper trading, add brokerage/order logic, or claim profitability.
- Backtester source code remains unchanged by this decision.

Follow-up:

- Add a documentation-only simulated slippage and cost assumption design stage.
- Stop before implementation if the design would require real market data,
  broker fills, order execution, or performance interpretation.

---

## 2026-06-07 - Require Universe-Mask Backtest Integration Design Before Code

Context:

- The synthetic liquidity universe helper has merged.
- The local CSV fixture workflow now reports universe-mask counts on committed
  synthetic fixtures only.
- `run_long_only_backtest()` currently consumes prices and signals, not
  universe masks.
- Feeding a universe mask directly into a backtest without a reviewed contract
  could blur universe dates, signal dates, rebalance dates, return measurement
  dates, low-coverage handling, benchmark assumptions, and performance
  interpretation.

Decision:

- Add a documentation-only liquidity universe backtest-integration design
  before any source code consumes a liquidity universe mask in the backtester.
- Treat the likely first implementation as a narrow signal-masking adapter,
  not a broad backtester rewrite.
- Require strict signal/mask alignment, explicit timing, visible low-coverage
  and empty-rebalance summaries, and caveated synthetic-only interpretation.

Rationale:

- The project already has the lower-level universe-mask primitive.
- The next correctness risk is not mask construction; it is unsafe consumption
  of the mask in simulated portfolio research.
- A design gate keeps universe construction, signal masking, portfolio
  selection, costs, slippage, benchmark comparison, and execution timing
  reviewable as separate concerns.

Consequences:

- Backtester source code remains unchanged in this stage.
- Future code should mask signals before ranking and should not silently
  repair missing universe or signal values.
- Future synthetic backtests that consume a universe mask must record universe
  parameters, coverage, low-coverage dates, timing assumptions, and caveats.
- Real user-provided local CSV interpretation remains blocked by the
  real-data readiness audit and experiment-log requirements.

Follow-up:

- After the design is reviewed and merged, the next narrow code stage can add
  a deterministic synthetic `apply_universe_mask_to_signals()` adapter and
  tests, without running a backtest if keeping the PR narrower is safer.

---

## 2026-06-07 - Keep Liquidity Universe Construction Separate From Backtesting

Context:

- The repository has synthetic-only rolling ADV and rolling dollar-volume
  eligibility helpers.
- The committed synthetic local CSV fixture workflow reports liquidity
  eligibility counts.
- No reviewed helper yet defines a final universe mask, an audit summary, or
  how such a mask should interact with factor scores, rebalance schedules,
  costs, slippage, benchmarks, or execution assumptions.
- The active workflow still prohibits real data fetching, downloads,
  credentials, live trading, paper trading, brokerage integration, order
  execution, and profitability claims.

Decision:

- Treat liquidity eligibility, final universe mask construction, and backtest
  consumption as separate stages.
- Add a documentation-only universe construction design before any code uses
  liquidity eligibility as a final research universe mask.
- Do not wire liquidity eligibility directly into the backtester until a later
  reviewed stage defines the universe mask API, audit summary, signal timing,
  rebalance timing, execution assumptions, costs, slippage, and benchmark
  interaction.

Rationale:

- Liquidity filters are a major survivorship-bias and look-ahead-bias risk if
  they are connected directly to portfolio construction without a reviewed
  timing boundary.
- A universe mask needs its own audit summary so low coverage, missing
  eligibility, capped names, additions, removals, and caveats remain visible.
- Keeping the stages separate preserves progress while preventing a liquidity
  helper from being mistaken for a tradable universe or performance result.

Consequences:

- Future liquidity universe code should be synthetic-only and should return a
  mask plus inspectable summary before any report or backtest integration.
- Backtester integration remains blocked until a separate design defines the
  complete signal/universe/rebalance/execution contract.
- User-provided local CSV universe interpretation remains gated by the
  real-data readiness audit and experiment-log requirements.

Follow-up:

- Implement a small synthetic-only universe-mask helper and deterministic tests
  only after `docs/liquidity_universe_construction_design.md` is reviewed and
  merged.

---

## 2026-06-04 - Keep First LEAN-Adjacent Code Signal-Only

Context:

- PR #42 merged the LEAN runnable draft readiness decision.
- That decision found the repository is not ready for runnable LEAN code under
  the current guardrails.
- The active workflow still prohibits real market data fetching, downloads,
  credentials, live trading, paper trading, brokerage integration, order
  execution, and profitability claims.

Decision:

- Define the next LEAN-adjacent code boundary as signal-only and
  metadata-only.
- Do not allow the next code stage to import `AlgorithmImports`, subclass
  `QCAlgorithm`, create `config.json`, run LEAN, subscribe to platform data,
  call history APIs, create portfolio targets, place orders, model fills,
  configure brokerage, or produce backtest results.
- If this design is reviewed and merged, the next possible code PR should be a
  pure-Python `lean/signal_only_momentum_draft.py` plus static scope tests.

Rationale:

- A signal-only draft can make the factor translation boundary auditable
  without introducing runtime dependencies, account access, data-source
  semantics, order semantics, or performance interpretation.
- Keeping the first code step metadata-only preserves forward progress while
  maintaining the existing simulated-research guardrails.

Consequences:

- Runnable LEAN code remains intentionally blocked.
- The future signal-only draft must avoid order dates, target weights,
  brokerage models, fill models, live mode, paper mode, and implemented
  portfolio behavior.
- Static tests should continue to reject data downloads, credential reads,
  runtime LEAN imports, order calls, and profitability or trading-readiness
  claims.

Follow-up:

- After this design is reviewed and merged, create a small code PR for a
  pure-Python LEAN signal-only momentum draft with static guardrail tests, or
  stop if the implementation cannot satisfy the documented boundary.

---

## 2026-06-04 - Defer Runnable LEAN Draft Until Signal-Only Boundary Is Designed

Context:

- PR #41 merged the LEAN scaffold review checklist.
- The repository now has a metadata-only LEAN scaffold and static tests that
  intentionally reject runtime LEAN imports, credential/data imports,
  brokerage calls, and order calls in the scaffold.
- The current workflow guardrails still prohibit real market data fetching,
  downloads, credentials, live trading, paper trading, brokerage integration,
  order execution, and profitability claims.

Decision:

- Do not add a runnable LEAN draft in the next stage.
- Add a readiness decision documenting that runnable LEAN code is not yet
  approved under current guardrails.
- Make the next safe LEAN stage a documentation-only signal-only draft design.

Rationale:

- A normal runnable LEAN algorithm would likely use `AlgorithmImports`,
  `QCAlgorithm`, platform data subscriptions or history, scheduled events,
  portfolio targets, orders, fills, fee models, and slippage models.
- Those pieces may be appropriate in a future simulated LEAN backtest, but they
  need an explicit scope boundary before implementation so they are not
  confused with live trading, brokerage integration, real data fetching, or
  profitability evidence.
- The signal-only design stage can preserve forward progress while keeping the
  implementation bounded and reviewable.

Consequences:

- Future LEAN code remains blocked until the project defines a signal-only
  code boundary and static validation plan.
- The existing non-executing scaffold remains unchanged.
- No source code, tests, research scripts, reports, data access, execution
  behavior, credentials, or performance claims are changed by this decision.

Follow-up:

- Create a documentation-only LEAN signal-only draft design after this decision
  is reviewed and merged.
- If that design cannot avoid runtime, data, credential, order, or
  interpretation risks, stop and document the blocker before code is added.

---

## 2026-06-03 - Refresh WorldQuant Catalog Before More Alpha Work

Context:

- `docs/post_csv_checkpoint_report.md` identified stale wording in
  `docs/worldquant_alpha_catalog.md`.
- The catalog still described the repository as catalog-only even though the
  operator layer and `alpha_009` research feature now exist.
- PR #29 was merged, latest `main` was synced, baseline validation passed, and
  no open pull request gate remained.
- Assumption: refreshing the catalog is the next unblocked safe stage because
  it is documentation-only and directly addresses the latest checkpoint
  recommendation.

Decision:

- Refresh `docs/worldquant_alpha_catalog.md` before implementing another
  formula or expanding data schemas.
- Treat `alpha_009` as implemented research-feature status only, not a full
  strategy, backtest integration, trading recommendation, or profitability
  claim.
- Keep `alpha_012` blocked on volume plus close support and `alpha_101`
  blocked on OHLC support.
- Keep VWAP, market-cap, and industry-neutral categories deferred until the
  required data support and validation rules exist.

Rationale:

- Roadmap documents should not guide future stages from stale pre-`alpha_009`
  assumptions.
- Documentation cleanup is lower risk than starting another formula while the
  data prerequisites and next-stage options are still being clarified.
- The project should continue to avoid bulk WorldQuant 101 implementation.

Consequences:

- Future alpha stages should start from current implementation status rather
  than the original Stage 1 catalog-only milestone.
- Additional formula work should be PR-sized and preceded by explicit formula,
  data, operator, missing-value, and test scope.
- This decision changes documentation only. It does not modify source code,
  data access, strategy logic, backtester behavior, execution assumptions, or
  performance claims.

Follow-up:

- If the next alpha stage is code-changing, run the stricter code PR readiness
  gate: tests plus read-only review with no high or medium issues.
- Consider a future planning stage for volume + close or OHLC schema support
  before `alpha_012` or `alpha_101`.

---

## 2026-06-03 - Bounded Staged Execution Behavior

Context:

- The staged workflow now has a repository-local Skill and long-running
  controller.
- The user clarified that Codex should continue as a bounded staged execution
  agent and should not ask for a new prompt after every small step.
- Assumption: this clarification should be preserved as workflow-control
  documentation and Skill guidance, not treated as a source-code or product
  behavior change.

Decision:

- Add an explicit low-risk ambiguity policy to
  `docs/codex_long_running_controller.md`.
- Expand controller stop conditions to cover dirty working trees before new
  stages, destructive or broad architecture ambiguity, missing credentials or
  external access, new production dependencies, unsafe test failures,
  high/medium review issues, security/privacy/data-loss/irreversible risks,
  scope conflicts, and PR-ready human review gates.
- Update `.agents/skills/staged-quant-workflow/SKILL.md` so future sessions
  continue through low-risk ambiguity with logged assumptions and treat missing
  expected files as workflow scaffolding only when that is low-risk.

Rationale:

- The project needs forward motion without turning every minor ambiguity into a
  user prompt.
- The same behavior must remain bounded by safety, scope, review, and merge
  gates.
- Missing workflow files can be repaired safely in small process PRs, while
  missing product-behavior artifacts require a stop report.

Consequences:

- Future Codex sessions should continue through minor documentation/workflow
  ambiguities after recording assumptions.
- Future sessions must still stop for the defined safety, scope, review, and
  human approval conditions.
- This decision changes process guidance only. It does not modify source code,
  data access, trading behavior, strategy logic, or performance claims.

Follow-up:

- Keep each behavior update PR-sized.
- If this policy causes overreach, record the failure in
  `docs/troubleshooting_log.md` and tighten the stop conditions.

---

## 2026-06-03 - Add Long-Running Workflow Control Artifacts

Context:

- The staged workflow Skill exists at
  `.agents/skills/staged-quant-workflow/SKILL.md`.
- The user requested continuation based on `docs/codex_long_running_controller.md`,
  `docs/decision_log.md`, `docs/troubleshooting_log.md`, `CHANGELOG.md`, and
  `scripts/audit-skills.ps1`.
- On latest `main`, those controller, log, changelog, and audit script files
  were missing.

Decision:

- Add a repository-local long-running controller document.
- Add durable decision and troubleshooting logs.
- Add a changelog.
- Add a local PowerShell Skill audit script.
- Update the staged workflow Skill so future continuations read the controller
  and can run the Skill audit.

Rationale:

- The project now depends on a recurring staged workflow, not a one-off prompt.
- Missing controller and log files make future continuation ambiguous.
- A local Skill audit gives future sessions a deterministic check before
  relying on project Skills.

Consequences:

- Future Codex sessions have explicit startup, stop-condition, logging, and PR
  gate guidance.
- Workflow-control changes remain separate from factor research implementation.
- The repository gains process infrastructure but no source-code, data-access,
  strategy, backtest, or performance-claim changes.

Follow-up:

- Keep the controller concise and update it only when a reusable workflow rule
  is verified.
- Use `docs/troubleshooting_log.md` for detailed failure chains.
- Continue normal staged PR review and do not merge PRs without explicit user
  instruction.

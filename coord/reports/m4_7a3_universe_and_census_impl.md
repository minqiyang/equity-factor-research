# M4.7a-3 Implementation Report: Option A Seal Rule, Local Private Run, And Blocked Coverage Census

| Field | Value |
| --- | --- |
| Task/attempt | `m4_7a3-universe-and-census-a1` (resumed after owner decision O-3) |
| Card | `coord/v8_review_20260923/card_m4_7a3_universe_and_census.md` |
| Plan | `coord/plans/m4_7_binding_plan.md` Revision 11, SHA-256 `6541db93336e9181ebf3ad2f066b7b17f4550a17565036c2db5a5d82872a6407`, revised for the seal rule by owner decision O-3 Option A (`docs/decision_log.md`, 2026-09-26) |
| Route, lane | `GENERAL_EXEC`, CRITICAL (structural: `ARCHITECTURE`, `SCHEMA_PROTOCOL_CONTRACT`, `SECURITY_AUTHORITY`) |
| Author session | Claude Opus 5.5 (`claude-opus-5-5`) via Claude Code |
| Base | `d15ef1d` (main after PR #266), verified live against `origin/main` |
| Branch | `claude/m4_7a3-universe-census` |
| Evidence ceiling | `DIAGNOSTIC_ONLY`; count-only aggregates; no network call |
| Status | Pipeline complete; census readiness **`blocked`** (R-CENSUS-1, 2, 8, 9; R-CENSUS-7 caveat); `vp2_revisit_required = true`; owner decisions O-7 and O-8 required |

## 1. Result

The owner chose Option A for O-3. The seal rule now carries per-rule
parameters, and the full canonical sequence ran on snapshot `real_v1`: seal,
`calendar`, `splits`, `eod`, `dividends`, `verify`, the universe build, the
terminal template, validation, projection, and the census. Retrieval is
complete and snapshot integrity passes. The census readiness is `blocked`,
because four readiness rules fail by margins that no Option A parameter
addresses:

| Rule | Measured | Threshold | Main driver |
| --- | --- | --- | --- |
| R-CENSUS-1 in-band history | 6.92 years | 7 (Option A) | identity-adjusted counts confirm coverage from 2019-09-30, two months after the sealed 2019-07-31 |
| R-CENSUS-2 common support | 20 gap windows; excluded 0.384 | 6; 0.05 | 19 windows from the 24 unresolved delistings in the window (none curated) |
| R-CENSUS-8 IC supply | 32 months | 48 (Option A) | 16 IC months in dropped segments and 3 in gaps, from those windows |
| R-CENSUS-9 unpriced member-days | 0.330 | 0.02 | 177,177 `entry_unusable_upper_bound` (143 entries without `StartDate`) and 83,718 `no_discovery_panel` (80 in-span refusals) |
| R-CENSUS-7 holdout breadth | min 468 | tolerant band | caveat only |

R-CENSUS-3 (identity refusals 0.35 percent), R-CENSUS-4 (off-calendar
0.0008 percent), R-CENSUS-5, R-CENSUS-6, and R-CENSUS-10 pass. I did not raise
any cap other than the two Option A minima: reaching `ready` would need the
excluded-fraction cap above 0.384 and the unpriced cap above 0.330, which is
owner decision O-7, and the committed census states `blocked`.

The plan 7.2 stop on `blocked:*` readiness applies. The committed seal and
census are the measured record of this snapshot; a-3 closes only after the
owner acts on O-7 and O-8.

## 2. Option A implementation (`eb8c5a5`)

| File | Change |
| --- | --- |
| `src/data/holdout_partition.py` | `SEAL_RULES` keyed by `rule_version`: v1 (10-year holdout, cap 2014-01-01, 16 in-band years, 60 IC months) and Option A (1-year holdout, no cap, 7 in-band years, 48 IC months); `derive_holdout_window`, `build_prospective_seal`, and `write_prospective_seal` take the rule and `calendar_source`; `read_seal` refuses an unregistered rule; `read_holdout_end` reads through it |
| `research/m4_7_holdout_seal.py` | `--rule-version` and `--calendar-source` |
| `research/m4_7_coverage_census.py` | `derive_readiness(inputs, rule_version)` reads the minima from the seal rule and publishes `thresholds`; `calendar_source` from the seal; markdown header states the rule and calendar source |
| `research/m4_7_universe_build.py` | `Snapshot.calendar_source` from the seal; build manifest label |
| `research/m4_7_common_support.py`, `research/m4_7_sp500_pit_rerun.py` | `snapshot_support` takes `calendar_source`, so the census and the runner recompute the same `segments_sha256` |
| `tests/test_m4_7_holdout_seal.py`, `tests/test_m4_7_coverage_census.py` | Option A window and seal fields, unknown-rule refusal, Option A readiness thresholds and edges |

The default arguments keep every v1 seal and synthetic fixture unchanged
apart from the new `calendar_source` field, whose default is the former
hard-coded label. The Option A minima were fixed from dates alone before any
census ran: 7 years is 1 holdout, 1 warm-up, and 5 discovery years; a one-year
holdout on the `SPY.US` calendar allows at most 60 IC months with no gap
window, and 48 is four years.

## 3. Run on `real_v1`

| Step | Outcome |
| --- | --- |
| Seal (Option A, `SPY.US_eod_dates_v1`) | holdout `[2019-07-31, 2020-07-31)`; prospective SHA-256 `93ce6e5ad003927dbf7f1521c26aca6a17844cb3061a44f7885a5584612e9882` |
| `calendar` | 8,438 rows (1993-01-29 to 2026-08-07) |
| `splits`, `eod`, `dividends` | each 815 `retrieved`, 4 `unavailable:missing_symbol`; 2 discovery `eod` partitions quarantined; no holdout quarantine |
| `verify` | `retrieval_complete = true`; no hash mismatch, stale split evidence, or token leak |
| Universe build | 818 intervals: 663 resolved, 143 `entry_missing_field`, 12 identity refusals; 882 permanent IDs; 83 episodes refused a panel (80 `split_basis_unverified:in_span_step_mismatch`, 2 `unexplained_deviation`, 1 `split_attribution_ambiguous`) |
| Terminal evidence | 47 delisting candidates: 27 `unresolved`, 20 `deferred_holdout`; 0 engine events |
| Census | `blocked`; JSON SHA-256 `5015a1d80389c8c69019d78011943765641935211a532dbe38ac7b9061095c5c`; confirmed seal SHA-256 `20e225205d25d2402cae78f066d6dbbb3f77622f78256652a4ffdf47e095125e`, confirmation `caveat` |

Curation: no local source holds deal consideration terms. The cross-stream
integration tree holds SEC Form 25 identity targets with few retrieved
bodies, so every discovery candidate stays `unresolved` and enters `U`
(R4, R6). Curating the 24 in-window events from public documents is the
largest lever on R-CENSUS-2 and R-CENSUS-8 (O-5 curation capacity).

Other census figures: discovery window `D0` 2021-08-31 to `D_last`
2026-08-07; `max_reset_to_reset_rows` and segments in the public JSON;
power projection `T_proj = 32`, `kill_reachable_projection = false`; IC
months inside the static 50-name cohort window 100 percent and inside the
historical evaluation window 6.25 percent; VP-1 `a1_volume_half =
consistent` over 65 rows (plan stop not triggered); VP-2 exposure 178,859
member-days with `S_D > 0.05` (22.5 percent of 795,198 eligible), so
`vp2_revisit_required = true`.

The in-span refusals carry 1,548 undeclared steps among 1,598 failing pairs,
1,358 of them with residual in `(1e-3, 1e-2]`. The pattern is consistent with
dividends applied to `adjusted_close` but absent from the 217 dividend tables
that the local acquisition recorded as `EMPTY`; the pipeline reads an empty
table as valid evidence of no rows.

The census first ran on uncommitted code (`code_commit = 682e01f`). After the
code commit the build, terminal, and census reran; the public JSON differs
only in `code_commit`, now `eb8c5a5`.

## 4. Owner decisions required

1. **O-7 coverage shortfall** (R-CENSUS-2, R-CENSUS-8, R-CENSUS-9): curate the
   24 unresolved in-window delistings from public documents; replace the empty
   dividend tables with another source; decide the S9 upper-bound charge for
   the 143 entries without `StartDate` (22.3 percent of eligible member-days by
   itself); or register higher caps with their coverage cost stated.
2. **O-8 re-decision** (VP-2): the census set `vp2_revisit_required`; the
   ratification has expired, and b-2 needs a new disposition.
3. **O-3 residual** (R-CENSUS-1): 6.92 in-band years against the declared 7,
   from the identity-adjusted start 2019-09-30.
4. **b-2 alignment**: the runner registration skeleton still carries
   `MIN_IC_MONTHS = 60` and `calendar_source = GSPC.INDX_eod_dates_v1`; the
   freeze must align both with the Option A seal.

## 5. First pass: the v1 seal refusal

`components` and `symbols` first ran under the v1 rule, and the seal refused
`holdout_overlaps_prior_exposure` (holdout_end 2029-07-31 after 2014-01-01).

### 5.1 What ran before the seal refusal

```mermaid
flowchart LR
    C["components<br/>818 entries"] --> S["symbols<br/>18,184 listed / 32,555 delisted"]
    S --> SEAL["seal script<br/>REFUSED holdout_overlaps_prior_exposure"]
    SEAL -.->|holdout_seal_missing| REST["calendar, splits, eod, dividends,<br/>verify, build, terminal, census<br/>not run"]
```

| Step | Command | Outcome |
| --- | --- | --- |
| 1 | `data.eodhd_retrieval.main(["components", ...], transport=local)` | exit 0; 818 entries; `components_retrieved_utc_date = 2026-08-07` |
| 1 | `data.eodhd_retrieval.main(["symbols", ...], transport=local)` | exit 0; 18,184 listed, 32,555 delisted |
| 2 | `python -m research.m4_7_holdout_seal --snapshot-id real_v1 ...` | exit 1; `holdout_overlaps_prior_exposure` |
| 3–6 | retrieval tables, build, terminal tooling, census | not run (seal absent) |

The local transport is a private adapter (`build_local_eodhd_snapshot.py`,
SHA-256 `6b7047a5b1c0ab5320518efd9bcfc4cb5b35acff661cf33dcd296956d33d835d`)
stored beside the snapshot under `<private_data_root>`. It stays out of the
repository because T-STRUCT-1 (`tests/test_project_structure.py`) allows
`urllib.error` imports only in `src/data/eodhd_retrieval.py`, and the adapter
must raise `urllib.error.HTTPError` for the 404 path. Its mapping:

| URL path | Local source |
| --- | --- |
| `fundamentals/GSPC.INDX` | components response of acquisition `snapshot_20260807T002458Z`, wrapped as `{"HistoricalTickerComponents": ...}` |
| `exchange-symbol-list/US?delisted=0/1` | active and delisted common-stock lists of the same acquisition |
| `eod/GSPC.INDX` | `SPY.US` EOD response of acquisition `snapshot_20260808T005805Z` (no local `GSPC.INDX` bars exist) |
| `eod/`, `splits/`, `div/<CODE>` | ledger RAW artifact of acquisition `snapshot_20260808T005805Z`; `EMPTY` returns `[]`; a code absent from the ledger raises HTTP 404 |

The adapter filters dated rows to the request's `from`/`to` window, the
vendor's documented semantics, and passes `--to 2026-08-07`, the acquisition
cutoff, to every table command. The local responses were retrieved without
`from`: their `SUCCESS` files hold 237,136 EOD, 93 split, and 1,138 dividend
rows dated before the module's default `from = 1980-01-01`, and none after
the cutoff. `components` runs under the module's `clock`
seam at 2026-08-07T00:24:58Z, the local response's acquisition time, so the
open-interval rule of plan 1.4 step 1 uses the date the response was
retrieved. The manifest's `snapshot.started_utc` carries the same instant.

### 5.2 Measurements behind the v1 refusal

Entry outcomes under the shared entry rule (`classify_membership_entries`):

| Outcome | Entries |
| --- | --- |
| `retained` | 675 |
| `entry_missing_field` | 143 (every one lacks `StartDate`; none lacks `Code`) |
| `entry_unparseable_date`, `degenerate_interval`, `exact_duplicate_collapsed`, `raw_overlap` | 0 |

The 143 refused entries are all closed (`IsActiveNow = 0`; 96 carry
`IsDelisted = 1`), with `EndDate` from 2008-09-16 to 2023-12-18.

Raw month-end count `n_raw(m)` over the retained entries (count-only
aggregate, R11), with the upper bound that counts each refused entry as a
member from the earliest start through its `EndDate`:

| Month-end | `n_raw` | Upper bound |
| --- | ---: | ---: |
| 1995-12-31 | 147 | 290 |
| 2000-12-31 | 195 | 338 |
| 2005-12-31 | 236 | 379 |
| 2008-12-31 | 282 | 424 |
| 2010-12-31 | 313 | 455 |
| 2011-12-31 | 331 | 473 |
| 2013-12-31 | 366 | 479 |
| 2016-12-31 | 424 | 494 |
| 2018-12-31 | 460 | 501 |
| 2019-07-31 | 470 | 504 |
| 2019-12-31 | 476 | 504 |
| 2022-12-31 | 498 | 503 |
| 2026-07-31 | 504 | 504 |

| Quantity | Retained entries | Upper bound |
| --- | --- | --- |
| `coverage_start` (tolerant, 3 isolated exceptions) | 2019-07-31 | 2011-12-31 |
| `coverage_start_strict` | 2019-07-31 | 2011-12-31 |
| `holdout_end` (+10 years) | 2029-07-31 | 2021-12-31 |
| `holdout_end <= 2014-01-01` | fails | fails |

The local components response lists 818 entries, while the S&P 500 has had
well over a thousand distinct constituents since 1957; the counts climb
steadily from 54 in 1957 to the band in 2019, which is the signature of a
history that records current members and recent removals only. Imputing the
143 missing start dates is prohibited (R6) and would still fail the seal rule.
The shortfall is a vendor coverage limit of this membership source; the v1
design (a sealed earliest decade ending by 2014-01-01 plus at least five
discovery years) cannot be met from it, which led to owner decision O-3.

## 6. Committed files

| File | Content |
| --- | --- |
| `src/data/holdout_partition.py`, `research/m4_7_holdout_seal.py`, `research/m4_7_coverage_census.py`, `research/m4_7_universe_build.py`, `research/m4_7_common_support.py`, `research/m4_7_sp500_pit_rerun.py` | Option A seal rule and declared calendar source (`eb8c5a5`) |
| `tests/test_m4_7_holdout_seal.py`, `tests/test_m4_7_coverage_census.py` | Option A tests |
| `reports/m4_7_coverage_census.json`, `reports/m4_7_coverage_census.md` | Public census aggregates, readiness `blocked` |
| `docs/preregistrations/m4_7_holdout_seal_v1.json` | Option A seal with confirmation `caveat` |
| `docs/decision_log.md` | O-3 Option A decision, parameters, result, open decisions |
| `docs/engineering_log.md` | Run authorization and provenance; the stop; the resumed run |
| `docs/current_handoff.md` | Refreshed to base `d15ef1d` |
| `docs/repo_map.md` | Regenerated (mapped `docs/` file count) |
| `coord/reports/m4_7a3_universe_and_census_impl.md` | This report |

## 7. Privacy (R11)

The public census and seal hold counts, fractions, month-level windows,
hashes, and typed codes. A scan of the three public files finds no member
code, permanent ID, or private path; the only exchange-suffixed strings are
the benchmark calendar label `SPY.US_eod_dates_v1` and the seal's
`dates/<CODE>.US.parquet` pattern. Provider rows, membership lists, the
adapter, and the snapshot stay under `<private_data_root>`.

## 8. Verification

Run on head `cc2cd7b` (the amend that adds this table changes this report only).

| Check | Result |
| --- | --- |
| `.venv/bin/python -m pytest tests/test_governance_constitution.py tests/test_m4_7_*.py tests/test_project_structure.py tests/test_eodhd_retrieval.py` | 414 passed |
| `ruff check . --exclude .venv` | all checks passed |
| `git diff --check d15ef1d...HEAD` | clean |
| Public-file privacy scan (member codes, `#E` IDs, private paths) | no match |
| Census rerun after the code commit | public JSON identical except `code_commit` |

`docs/repo_map.md` was regenerated with `scripts/repo_map.py`, because the
committed seal adds one mapped file under `docs/`.

## 9. Ablation

- Guard-necessity check (retained): removing the unregistered-rule refusal
  from `read_seal` fails `test_a_seal_with_an_unknown_rule_version_is_refused`,
  and `derive_readiness` then raises an untyped `KeyError`.
- Simplification attempt (rejected): a `date.max` sentinel for the Option A
  cap removes the two `is None` branches with identical readiness, and fails
  only `test_option_a_readiness_thresholds_follow_the_seal_rule`, because the
  public thresholds would publish a fictitious cap `9999-12-31` instead of
  `null`.
- Private adapter (first pass): the window filter's sentinel defaults were
  removed and a clean rebuild reproduced every manifest file hash; the `from`
  filter and the non-`SUCCESS` 404 guard are retained. Its table paths have
  now executed on the full run.

## 10. Next gate

Owner decisions O-7 and O-8 (and the O-3 residual). After them, a-3 reruns
the build and census from the private manifest; M4.7b-2 stays blocked on a-3
and must align the runner registration with the Option A seal.

# Milestone 5.5 screen of trial family v1

Evidence ceiling: `DIAGNOSTIC_ONLY`. This is a simulated research diagnostic. It gives aggregates only and makes no profitability claim. The JSON file `reports/m55_screen_v1.json` holds every aggregate of this report.

- Run label: stock-level out-of-sample, factor-level in-sample; never called confirmation.
- Factor-level reuse (`reports_owed.labels`): M5 step 2: JKP and French factor returns 1926-2025, built from the same CRSP stocks (factor level).
- Benchmark note: CRSP S&P 500 value-weighted total return vwretd as is (legacy, to 2024-12-31), labelled 'gross of fund fees'; no fee is deducted.
- Low-risk label: factor-level in-sample (the low-volatility effect was published in the 1970s). Test B is stopped, so no low-risk return exists.

## Result

- Freeze decision `shortlist_frozen`. Shortlist: S3, S4. Digest `62b2c8afb379fb0322b03cbd68da47b71c68c9eb1d1172c805dcd11b00d59518`.
- The freeze reads only the primary loader run with the primary cost case. The rule is IR >= 0.2 and HAC t >= 1.0 against CW-PIT, at most 10 candidates. The other three cells are reported and decide nothing.
- Test B is stopped (label `stopped_coverage`, p_B 1.0). With p_B = 1.0, test A needs p_A <= 0.025 for its Holm condition (alpha 0.05, two tests).
- The candidate tables are in ID order and are not a ranking. The one-sided p-values have no multiple-testing correction; the trial applies Benjamini-Yekutieli q-values (family size 9) at the confirm stage.

## Limitations

- The path_break_held blank set removes 215 of 354 screen months (share 0.6073). 13 held positions cause it, with a CW-PIT weight sum of 0.0034 at their last rebalance. The longest position blanks 162 months. The blanks cut S1 from 168 to 90 months, and S7 from 348 to 133 months.
- The coordinator ruled on 2026-10-08 that the blank is the frozen rule, correctly applied. Each gap is a gap in CRSP itself: the pull takes every daily row of every PERMNO that was ever a member, and the loader drops only off-calendar rows. The halt policy locks a held position with no close, and R6 forbids a fill. Both books lose the same months, so the cut cannot favor a candidate against CW-PIT. It lowers the power of the candidates that lose months. No fix and no rerun follow, because a rule change after the result is a forking path (R9).
- S3 meets the frozen rule in the decision cell, but it fails the rule in the primary run with sensitivity_2x costs (IR 0.261, HAC t 0.459) and in the last_close run with sensitivity_2x costs (IR 0.263, HAC t 0.462). These cells decide nothing.
- S2 and S3 have 36 screen months with values, the minimum of the rule.
- The run label is 'stock-level out-of-sample, factor-level in-sample; never called confirmation'. M5 step 2: JKP and French factor returns 1926-2025, built from the same CRSP stocks (factor level).
- The sample is the point-in-time S&P 500 over the screen months 1963-07 to 1992-12. The confirm and check months are not opened.
- The screen p-values have no multiple-testing correction. The trial applies Benjamini-Yekutieli q-values (family size 9) at the confirm stage, so this report gives no q-value. The candidate table is in ID order and is not a ranking.
- No result in this report is a profitability claim. Costs follow the screen cost schedule; the books are long only, so no borrow cost applies.

## Provenance

| Item | Value |
| --- | --- |
| Trial file | `docs/preregistrations/m55_trial_family_v1.json`, SHA-256 `4f9cf222da07fc039529fcbec01b3f174275483857fd7a20a69b132d76f88a03` (run 2) |
| Data | `reports/wrds_manifest_2025.json` (vintage 2025-12-31), files SHA-256 `040b6d7693bd2d57372bf3cd824c3a8f8fc8401568e7f276660bbbe9916b94c9` (both runs) |
| Shortlist digest | `62b2c8afb379fb0322b03cbd68da47b71c68c9eb1d1172c805dcd11b00d59518` |
| Run 1 trial | trial family v1 with amendment 1, SHA-256 `ab3b4ab0bb58084aa604d78f772850641471e28cf228ab605db5cec1da16f4fe` |
| Run 1 code | commit `ebc97054301dda53e0193d59f8003d3fa904867d`, code SHA-256 `4c507f47c749e4d9f2f222dee8cbf95e9bb8e4c042650c222c333e1d87878fa6` |
| Run 1 coverage.json | `aa45d6086778bf3b762413816120bc70d161da8d182221d0306163fa12a1f048` |
| Run 1 calibration.json | `0be87e72498dc1962268ee0411fb0f7bab3cf2459c56b6928eafa142c1a2837b` |
| Run 2 trial | trial family v1 with amendments 1 and 2, SHA-256 `4f9cf222da07fc039529fcbec01b3f174275483857fd7a20a69b132d76f88a03` |
| Run 2 code | commit `8590b2e9ca11513cf9f5aa2c552e1d6a9f6d3925`, code SHA-256 `a9e2cc25a3cc698114ddaf4d48675471a257761da19f4d4882e398cbc6834a6b` |
| Run 2 coverage.json | `e46b343acb46b3560a8aa22d02fb53dd0695d20773ae4e552669e8c0b57cf29f` |
| Run 2 calibration.json | `809fbe616c150d66b2464744be80af057500e07f6d4a5f9a6018cf187ba54b82` |
| Run 2 look.json | `2890036d89c58ea9887e6d1ea0be9e5fe628b85086e6ce874804e7a4248ca4cb` |
| Run 2 screen.json | `07d660a24da069309af01b295406d2acbac65ef8fbb363f0b02d8a444b58bedb` |
| Run 2 freeze.json | `c77aa3d0158c6b496cd88ab11bbe6c3298243b8e730971dc928b4d20106e995d` |

Pinned files of run 2 (SHA-256):

| File | SHA-256 |
| --- | --- |
| `reports/wrds_manifest_2025.json` | `6dc96e69fdd6410fd5bcd41a00bddd0a2d91e54a2421e30efa06adacdf354e8f` |
| `research/m4_7_family_a.py` | `41df632629ee6f6344ba4a6b2f0158d8e031bd9a4f5c6ad499df24316d88d488` |
| `research/m55_criteria.py` | `5580b86f2037b50a864da01d6227cd9f08ddded4508577c4d7c1bd7570559623` |
| `research/m55_index_tilt.py` | `1b57c09710c6c27b2b2cdebd6e8c716cd6bafb700b1d4dd5f16240f3dc15e186` |
| `research/m55_signals.py` | `60721018e16ed09acc13087efb9cec7b72369ba3a086f8e01506df0b638693b1` |
| `research/m55_wrds_loader.py` | `8756125b237f64cfb69b09a499bea28ad24637580357b919734bae61a72f6eff` |

## Runs (R9)

Each run of the trial family is listed. `reports/m55_screen_v1_attempts.jsonl` has one line per run.

| Run | Date | Folder | Trial | Calibration decision | Stages written | Status |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 2026-10-07 | `m55_screen_v1` | trial family v1 with amendment 1 | `ratio_coverage_low` | coverage, calibration | stopped |
| 2 | 2026-10-08 | `m55_screen_v2` | trial family v1 with amendments 1 and 2 | `ratio_coverage_low` | coverage, calibration, look, screen, freeze | completed |

Run 1 stopped at the coverage stop. Reason: calibration decision ratio_coverage_low; the gate GO_ON = ("chosen",) of this code stops the sequence before the look; no return of any kind was computed. The trial file names the run 1 calibration digest in `primary_family.test_B.after_coverage_stop`: yes. Run 2 ran under amendment 2 and wrote all five stage files with no refusal.

## Calibration and test B

The run 2 calibration result equals run 1 on every field: yes. The run 2 coverage result equals run 1 on every field: yes.

| Field | Value |
| --- | --- |
| decision | `ratio_coverage_low` |
| rebalances | 354 (1963-05-31 to 1992-11-30) |
| `defined_full` | 131 |
| `defined_partial` | 159 |
| `ratio_window_short` | 64 |
| undefined share | 0.1808 (limit 0.10) |
| chosen g | none |
| target ratio | 0.87 |
| window diagnostic undefined share | 0.6299 |
| window decision | `ratio_coverage_ambiguous` |
| window diagnostic coverage high | yes |
| gap rebalances | 296 |
| ratio gap members | 3660 |
| max ratio_gap_cw_share | 0.0928 |

Grid (risk only, no return):

| g | Bracket | Bracket, full windows | Defined | Undefined | Median ratio | Median hi | Median lo | Share cap binds | Share TE-scaled |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.5 | fails | ambiguous | 290 | 64 | 0.9728 | 0.9759 | 0.9700 | 0.1695 | 0.0000 |
| 1.0 | fails | ambiguous | 290 | 64 | 0.9516 | 0.9566 | 0.9447 | 0.5565 | 0.0000 |
| 1.5 | fails | ambiguous | 290 | 64 | 0.9337 | 0.9393 | 0.9228 | 0.7345 | 0.0000 |
| 2.0 | fails | ambiguous | 290 | 64 | 0.9124 | 0.9232 | 0.9027 | 0.8277 | 0.0000 |
| 2.5 | fails | ambiguous | 290 | 64 | 0.8938 | 0.9076 | 0.8825 | 0.8701 | 0.0000 |
| 3.0 | ambiguous | ambiguous | 290 | 64 | 0.8754 | 0.8928 | 0.8632 | 0.9068 | 0.0000 |
| 3.5 | ambiguous | ambiguous | 290 | 64 | 0.8598 | 0.8772 | 0.8495 | 0.9689 | 0.0282 |
| 4.0 | meets | ambiguous | 290 | 64 | 0.8474 | 0.8630 | 0.8349 | 0.9972 | 0.0678 |
| 4.5 | meets | ambiguous | 290 | 64 | 0.8355 | 0.8528 | 0.8203 | 1.0000 | 0.0904 |
| 5.0 | meets | ambiguous | 290 | 64 | 0.8228 | 0.8409 | 0.8058 | 1.0000 | 0.1130 |
| 5.5 | meets | ambiguous | 290 | 64 | 0.8126 | 0.8315 | 0.7963 | 1.0000 | 0.1469 |
| 6.0 | meets | ambiguous | 290 | 64 | 0.8036 | 0.8214 | 0.7894 | 1.0000 | 0.1921 |

Test B record (the same in the look, screen, and freeze files): stopped yes, label `stopped_coverage`, p_B 1.0, calibration decision `ratio_coverage_low`, calibration SHA-256 `809fbe616c150d66b2464744be80af057500e07f6d4a5f9a6018cf187ba54b82`.

## Look: CW-PIT against vwretd

The look runs the engine with no signal, so TILT equals CW-PIT. Screen months: 354. Mean gap is CW-PIT minus vwretd, annual, over the months with values.

| Loader run | Cost case | Months with values | Blank months | CW-PIT annual mean | vwretd annual mean | Mean gap | TE | Correlation | CW annual turnover | CW cost drag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| primary | primary | 139 | 215 | 13.53% | 13.65% | -0.121% | 0.203% | 0.99991 | 0.2625 | 0.128% |
| primary | sensitivity_2x | 139 | 215 | 13.38% | 13.65% | -0.272% | 0.366% | 0.99970 | 0.2625 | 0.256% |
| last_close | primary | 139 | 215 | 13.53% | 13.65% | -0.122% | 0.202% | 0.99991 | 0.2625 | 0.128% |
| last_close | sensitivity_2x | 139 | 215 | 13.37% | 13.65% | -0.273% | 0.365% | 0.99970 | 0.2625 | 0.256% |

R4 fragility of the look (sign flip of the mean gap between the loader runs): primary no sign flip; sensitivity_2x no sign flip.

Blank months, all with the reason `path_break_held`. The set is the same in both loader runs: yes. Count 215, share 0.6073. By year (primary run): 1967 5, 1968 12, 1969 12, 1970 12, 1971 12, 1972 12, 1973 12, 1974 12, 1975 12, 1976 12, 1977 12, 1978 12, 1979 12, 1980 12, 1981 12, 1982 12, 1983 12, 1984 12, 1985 6. The JSON lists each blank month.

Rebalance coverage of CW-PIT in the look (`reports_owed.counts`):

| Loader run | Rebalances | Members mean | Members min | Traded mean | Traded min | Pinned mean | c = 0 few signals | c = 0 short history | c = 0 window gap | ME missing | ME missing by reason | Settled excluded | Share at stock cap | Share TE-scaled | B2 rebalances / excluded |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| primary | 355 | 498.87 | 489 | 498.87 | 489 | 498.9 | 177100 | 458 | 3651 | 332 | unmapped 126, no_share_fact 206 | 45 | 0.000 | 0.000 | 0 / 0 |
| last_close | 355 | 498.87 | 489 | 498.85 | 488 | 498.9 | 177100 | 458 | 3651 | 320 | unmapped 114, no_share_fact 206 | 57 | 0.000 | 0.000 | 9 / 9 |

## Screen

Each candidate runs alone as a 2 percent TE tilt against the CW-PIT of the same run. The decision cell is the primary loader run with the primary cost case. Annual active mean, TE, IR, and HAC t are against CW-PIT over the screen months with values. A candidate with fewer than 36 months gets a typed undefined record.

Screen cost schedule (one way, bp per traded notional): from the first row, commission 30 and spread 30; from 1975-05-01, commission 10 and spread 30. The 2x case doubles each cost.

| ID | Real start | First month | Months before blanks |
| --- | --- | --- | --- |
| S1 | 1979 | 1979-01 | 168 |
| S2 | 1990 | 1990-01 | 36 |
| S3 | 1990 | 1990-01 | 36 |
| S4 | 1987 | 1987-01 | 72 |
| S5 | none | none | 0 |
| S6 | 1987 | 1987-01 | 72 |
| S7 | 1964 | 1964-01 | 348 |
| S8 | 1987 | 1987-01 | 72 |

| ID | Loader run | Cost case | Months with values | Blank months | Record | Annual active mean | TE | IR | HAC t | p one-sided | Turnover | Decision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| S1 | primary | primary | 90 | 78 | ok | -0.14% | 0.80% | -0.173 | -0.441 | 0.670 | 1.002 | not shortlisted |
| S1 | primary | sensitivity_2x | 90 | 78 | ok | -0.43% | 0.80% | -0.537 | -1.371 | 0.915 | 1.002 | reported only |
| S1 | last_close | primary | 90 | 78 | ok | -0.13% | 0.80% | -0.169 | -0.431 | 0.667 | 1.002 | reported only |
| S1 | last_close | sensitivity_2x | 90 | 78 | ok | -0.43% | 0.80% | -0.534 | -1.362 | 0.913 | 1.002 | reported only |
| S2 | primary | primary | 36 | 0 | ok | 0.31% | 0.91% | 0.341 | 0.626 | 0.266 | 1.254 | not shortlisted |
| S2 | primary | sensitivity_2x | 36 | 0 | ok | 0.02% | 0.93% | 0.023 | 0.042 | 0.483 | 1.254 | reported only |
| S2 | last_close | primary | 36 | 0 | ok | 0.31% | 0.91% | 0.341 | 0.627 | 0.265 | 1.254 | reported only |
| S2 | last_close | sensitivity_2x | 36 | 0 | ok | 0.02% | 0.93% | 0.023 | 0.042 | 0.483 | 1.254 | reported only |
| S3 | primary | primary | 36 | 0 | ok | 0.59% | 0.54% | 1.104 | 1.850 | 0.032 | 1.627 | shortlisted |
| S3 | primary | sensitivity_2x | 36 | 0 | ok | 0.15% | 0.59% | 0.261 | 0.459 | 0.323 | 1.627 | reported only |
| S3 | last_close | primary | 36 | 0 | ok | 0.59% | 0.54% | 1.106 | 1.854 | 0.032 | 1.626 | reported only |
| S3 | last_close | sensitivity_2x | 36 | 0 | ok | 0.15% | 0.59% | 0.263 | 0.462 | 0.322 | 1.626 | reported only |
| S4 | primary | primary | 72 | 0 | ok | 0.53% | 0.77% | 0.686 | 1.539 | 0.062 | 0.434 | shortlisted |
| S4 | primary | sensitivity_2x | 72 | 0 | ok | 0.52% | 0.77% | 0.669 | 1.499 | 0.067 | 0.434 | reported only |
| S4 | last_close | primary | 72 | 0 | ok | 0.53% | 0.77% | 0.686 | 1.538 | 0.062 | 0.434 | reported only |
| S4 | last_close | sensitivity_2x | 72 | 0 | ok | 0.52% | 0.77% | 0.669 | 1.499 | 0.067 | 0.434 | reported only |
| S5 | primary | primary | 0 | 0 | undefined (`screen_too_short`) | none | none | none | none | none | none | not shortlisted |
| S5 | primary | sensitivity_2x | 0 | 0 | undefined (`screen_too_short`) | none | none | none | none | none | none | reported only |
| S5 | last_close | primary | 0 | 0 | undefined (`screen_too_short`) | none | none | none | none | none | none | reported only |
| S5 | last_close | sensitivity_2x | 0 | 0 | undefined (`screen_too_short`) | none | none | none | none | none | none | reported only |
| S6 | primary | primary | 72 | 0 | ok | 0.03% | 0.83% | 0.039 | 0.088 | 0.465 | 0.626 | not shortlisted |
| S6 | primary | sensitivity_2x | 72 | 0 | ok | -0.06% | 0.83% | -0.073 | -0.166 | 0.566 | 0.626 | reported only |
| S6 | last_close | primary | 72 | 0 | ok | 0.03% | 0.83% | 0.041 | 0.091 | 0.464 | 0.627 | reported only |
| S6 | last_close | sensitivity_2x | 72 | 0 | ok | -0.06% | 0.83% | -0.072 | -0.164 | 0.565 | 0.627 | reported only |
| S7 | primary | primary | 133 | 215 | ok | 0.02% | 0.54% | 0.043 | 0.128 | 0.449 | 0.517 | not shortlisted |
| S7 | primary | sensitivity_2x | 133 | 215 | ok | -0.09% | 0.55% | -0.168 | -0.511 | 0.695 | 0.517 | reported only |
| S7 | last_close | primary | 133 | 215 | ok | 0.02% | 0.54% | 0.039 | 0.115 | 0.454 | 0.517 | reported only |
| S7 | last_close | sensitivity_2x | 133 | 215 | ok | -0.09% | 0.55% | -0.173 | -0.526 | 0.700 | 0.517 | reported only |
| S8 | primary | primary | 72 | 0 | ok | -0.40% | 1.24% | -0.320 | -0.761 | 0.777 | 0.563 | not shortlisted |
| S8 | primary | sensitivity_2x | 72 | 0 | ok | -0.46% | 1.24% | -0.372 | -0.888 | 0.813 | 0.563 | reported only |
| S8 | last_close | primary | 72 | 0 | ok | -0.40% | 1.24% | -0.320 | -0.762 | 0.777 | 0.563 | reported only |
| S8 | last_close | sensitivity_2x | 72 | 0 | ok | -0.46% | 1.24% | -0.373 | -0.889 | 0.813 | 0.563 | reported only |

TILT and CW-PIT against vwretd, primary loader run (annual mean gap and TE):

| ID | Cost case | TILT mean gap | TILT TE | TILT correlation | CW-PIT mean gap |
| --- | --- | --- | --- | --- | --- |
| S1 | primary | -0.19% | 0.79% | 0.9989 | -0.054% |
| S1 | sensitivity_2x | -0.58% | 0.80% | 0.9989 | -0.150% |
| S2 | primary | 0.22% | 0.95% | 0.9981 | -0.086% |
| S2 | sensitivity_2x | -0.28% | 1.07% | 0.9977 | -0.299% |
| S3 | primary | 0.51% | 0.58% | 0.9993 | -0.086% |
| S3 | sensitivity_2x | -0.14% | 0.74% | 0.9988 | -0.299% |
| S4 | primary | 0.42% | 0.82% | 0.9989 | -0.107% |
| S4 | sensitivity_2x | 0.24% | 0.88% | 0.9987 | -0.278% |
| S6 | primary | -0.07% | 0.88% | 0.9990 | -0.107% |
| S6 | sensitivity_2x | -0.34% | 0.95% | 0.9989 | -0.278% |
| S7 | primary | -0.10% | 0.60% | 0.9992 | -0.128% |
| S7 | sensitivity_2x | -0.38% | 0.69% | 0.9990 | -0.283% |
| S8 | primary | -0.50% | 1.29% | 0.9976 | -0.107% |
| S8 | sensitivity_2x | -0.74% | 1.35% | 0.9974 | -0.278% |

## Freeze

- Decision `shortlist_frozen`; shortlist S3, S4.
- Rule: `ir_min` 0.2, `t_min` 1.0, `shortlist_cap` 10.
- Digest `62b2c8afb379fb0322b03cbd68da47b71c68c9eb1d1172c805dcd11b00d59518`. The script recomputed it with `m55_criteria.freeze_shortlist` from the screen records, and it equals the freeze file and `shortlist_digest.txt`.
- Test B: stopped yes, label `stopped_coverage`, p_B 1.0.

## Reports owed

Each item of `reports_owed` that the stage files hold has its own key in the JSON under `reports_owed`. The tables give the primary cost case unless they say otherwise.

### r4

Held disappearances by cause. In the primary run, `ciz_return_in_path` means CIZ put the delisting return in the path, `supplied_terminal_return` is a supplied return, and `missing_engine_default` takes the engine default. The last_close run settles every event at the last trade close. The weight at the event is the engine total book weight at the events. The weight at the last rebalance is the total post-trade weight at the last rebalance before each event.

Public weight rule (2026-10-08): the report gives weight sums only for the look groups, as totals over causes. The stage files cannot show that the two loader runs hold the same events of a cause with equal counts, so no weight by cause is given. It gives no weight for a screen candidate group and no single maximum weight.

Look, CW-PIT:

| Loader run | Cost case | Held | Weight at the event, sum | Weight at the last rebalance, sum | By cause |
| --- | --- | --- | --- | --- | --- |
| primary | primary | 316 | 0.3087 | 0.3037 | cash_merger 90 (ciz_return_in_path 90); failure 17 (ciz_return_in_path 10, missing_engine_default 6, supplied_terminal_return 1); unknown 209 (ciz_return_in_path 207, missing_engine_default 2) |
| primary | sensitivity_2x | 316 | 0.3087 | 0.3037 | cash_merger 90 (ciz_return_in_path 90); failure 17 (ciz_return_in_path 10, missing_engine_default 6, supplied_terminal_return 1); unknown 209 (ciz_return_in_path 207, missing_engine_default 2) |
| last_close | primary | 321 | 0.3090 | 0.3057 | cash_merger 90 (settled_at_last_close 90); failure 17 (settled_at_last_close 17); unknown 214 (settled_at_last_close 214) |
| last_close | sensitivity_2x | 321 | 0.3090 | 0.3057 | cash_merger 90 (settled_at_last_close 90); failure 17 (settled_at_last_close 17); unknown 214 (settled_at_last_close 214) |

Screen, primary cost (counts only):

| ID | Held CW, primary run | Held TILT, primary run | CW by cause, primary run | Held CW, last_close run |
| --- | --- | --- | --- | --- |
| S1 | 203 | 203 | cash_merger 80 (ciz_return_in_path 80); failure 2 (ciz_return_in_path 2); unknown 121 (ciz_return_in_path 121) | 205 |
| S2 | 12 | 12 | cash_merger 2 (ciz_return_in_path 2); unknown 10 (ciz_return_in_path 10) | 13 |
| S3 | 12 | 12 | cash_merger 2 (ciz_return_in_path 2); unknown 10 (ciz_return_in_path 10) | 13 |
| S4 | 55 | 55 | cash_merger 17 (ciz_return_in_path 17); unknown 38 (ciz_return_in_path 38) | 55 |
| S6 | 55 | 55 | cash_merger 17 (ciz_return_in_path 17); unknown 38 (ciz_return_in_path 38) | 55 |
| S7 | 313 | 313 | cash_merger 90 (ciz_return_in_path 90); failure 16 (ciz_return_in_path 10, missing_engine_default 5, supplied_terminal_return 1); unknown 207 (ciz_return_in_path 205, missing_engine_default 2) | 318 |
| S8 | 55 | 55 | cash_merger 17 (ciz_return_in_path 17); unknown 38 (ciz_return_in_path 38) | 55 |

### fragility

A sign flip of an active annual mean between the primary run and the last_close rerun labels a result fragile (R4).

| ID | Cost case | TILT - CW, primary run | TILT - CW, last_close run | Sign flips | Label |
| --- | --- | --- | --- | --- | --- |
| S1 | primary | -0.14% | -0.13% | none | not fragile |
| S1 | sensitivity_2x | -0.43% | -0.43% | none | not fragile |
| S2 | primary | 0.31% | 0.31% | none | not fragile |
| S2 | sensitivity_2x | 0.02% | 0.02% | none | not fragile |
| S3 | primary | 0.59% | 0.59% | none | not fragile |
| S3 | sensitivity_2x | 0.15% | 0.15% | none | not fragile |
| S4 | primary | 0.53% | 0.53% | none | not fragile |
| S4 | sensitivity_2x | 0.52% | 0.52% | none | not fragile |
| S5 | primary | not evaluated |  |  | `screen_too_short` |
| S5 | sensitivity_2x | not evaluated |  |  | `screen_too_short` |
| S6 | primary | 0.03% | 0.03% | none | not fragile |
| S6 | sensitivity_2x | -0.06% | -0.06% | none | not fragile |
| S7 | primary | 0.02% | 0.02% | none | not fragile |
| S7 | sensitivity_2x | -0.09% | -0.09% | none | not fragile |
| S8 | primary | -0.40% | -0.40% | none | not fragile |
| S8 | sensitivity_2x | -0.46% | -0.46% | none | not fragile |

### r6

Typed-missing shares by later exit class. Signal reason shares over the member cells of the return months 1963-01 to 1992-12 (coverage stage):

| ID | Reason | current | left_index | cash_merger | failure | unknown |
| --- | --- | --- | --- | --- | --- | --- |
| S1 | `fpe_changed` | 0.0033 | 0.0028 | 0.0026 | 0.0018 | 0.0026 |
| S1 | `no_link` | 0.3306 | 0.3587 | 0.5342 | 0.5242 | 0.5179 |
| S1 | `no_record` | 0.0028 | 0.0000 | 0.0033 | 0.0000 | 0.0017 |
| S1 | `not_yet_known` | 0.0028 | 0.0127 | 0.0031 | 0.0044 | 0.0028 |
| S1 | `short_history` | 0.0041 | 0.0049 | 0.0052 | 0.0053 | 0.0047 |
| S1 | `stale` | 0.0003 | 0.0016 | 0.0038 | 0.0058 | 0.0023 |
| S1 | `valid` | 0.6562 | 0.6194 | 0.4478 | 0.4586 | 0.4680 |
| S2 | `missing_item` | 0.0030 | 0.0099 | 0.0022 | 0.0058 | 0.0037 |
| S2 | `no_link` | 0.0115 | 0.0002 | 0.0281 | 0.0401 | 0.0376 |
| S2 | `no_market_data` | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0002 |
| S2 | `no_record` | 0.0000 | 0.0183 | 0.3552 | 0.1641 | 0.2252 |
| S2 | `not_yet_known` | 0.7156 | 0.7047 | 0.4682 | 0.6172 | 0.5829 |
| S2 | `short_history` | 0.1179 | 0.1179 | 0.0693 | 0.0773 | 0.0698 |
| S2 | `split_in_basis_window` | 0.0005 | 0.0004 | 0.0001 | 0.0000 | 0.0001 |
| S2 | `stale` | 0.0002 | 0.0000 | 0.0001 | 0.0002 | 0.0001 |
| S2 | `valid` | 0.1512 | 0.1486 | 0.0768 | 0.0952 | 0.0804 |
| S3 | `missing_item` | 0.0000 | 0.0000 | 0.0318 | 0.0137 | 0.0445 |
| S3 | `no_link` | 0.0115 | 0.0002 | 0.0281 | 0.0401 | 0.0376 |
| S3 | `no_market_data` | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| S3 | `no_record` | 0.0000 | 0.0000 | 0.3507 | 0.1641 | 0.2187 |
| S3 | `not_yet_known` | 0.7121 | 0.7195 | 0.4391 | 0.6014 | 0.5415 |
| S3 | `short_history` | 0.0837 | 0.0847 | 0.0523 | 0.0555 | 0.0517 |
| S3 | `stale` | 0.0004 | 0.0041 | 0.0001 | 0.0014 | 0.0003 |
| S3 | `valid` | 0.1922 | 0.1915 | 0.0979 | 0.1239 | 0.1056 |
| S4 | `missing_item` | 0.0547 | 0.0167 | 0.0073 | 0.0000 | 0.0348 |
| S4 | `no_link` | 0.0115 | 0.0002 | 0.0281 | 0.0401 | 0.0376 |
| S4 | `no_record` | 0.0000 | 0.0183 | 0.0013 | 0.0149 | 0.0333 |
| S4 | `not_yet_known` | 0.6958 | 0.6844 | 0.8098 | 0.7531 | 0.7609 |
| S4 | `short_history` | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| S4 | `stale` | 0.0002 | 0.0003 | 0.0000 | 0.0002 | 0.0001 |
| S4 | `valid` | 0.2377 | 0.2802 | 0.1535 | 0.1916 | 0.1332 |
| S5 | `missing_item` | 0.0757 | 0.0403 | 0.0130 | 0.0127 | 0.0504 |
| S5 | `no_link` | 0.0115 | 0.0002 | 0.0281 | 0.0401 | 0.0376 |
| S5 | `no_record` | 0.0000 | 0.0183 | 0.0013 | 0.0149 | 0.0333 |
| S5 | `not_yet_known` | 0.6958 | 0.6844 | 0.8098 | 0.7531 | 0.7609 |
| S5 | `short_history` | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| S5 | `stale` | 0.0002 | 0.0003 | 0.0000 | 0.0002 | 0.0001 |
| S5 | `valid` | 0.2168 | 0.2566 | 0.1478 | 0.1789 | 0.1176 |
| S6 | `missing_item` | 0.0013 | 0.0000 | 0.0009 | 0.0000 | 0.0003 |
| S6 | `no_link` | 0.0115 | 0.0002 | 0.0281 | 0.0401 | 0.0376 |
| S6 | `no_record` | 0.0000 | 0.0183 | 0.0013 | 0.0149 | 0.0333 |
| S6 | `not_yet_known` | 0.6958 | 0.6844 | 0.8098 | 0.7531 | 0.7609 |
| S6 | `short_history` | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| S6 | `stale` | 0.0002 | 0.0003 | 0.0000 | 0.0002 | 0.0001 |
| S6 | `valid` | 0.2912 | 0.2969 | 0.1599 | 0.1916 | 0.1677 |
| S7 | `missing_item` | 0.0125 | 0.0102 | 0.0160 | 0.0214 | 0.0207 |
| S7 | `no_market_data` | 0.0004 | 0.0000 | 0.0002 | 0.0001 | 0.0004 |
| S7 | `short_history` | 0.0029 | 0.0015 | 0.0033 | 0.0007 | 0.0028 |
| S7 | `valid` | 0.9842 | 0.9883 | 0.9805 | 0.9778 | 0.9761 |
| S8 | `be_nonpositive` | 0.0024 | 0.0050 | 0.0030 | 0.0116 | 0.0029 |
| S8 | `missing_item` | 0.0009 | 0.0000 | 0.0011 | 0.0000 | 0.0003 |
| S8 | `no_link` | 0.0115 | 0.0002 | 0.0281 | 0.0401 | 0.0376 |
| S8 | `no_market_data` | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| S8 | `no_record` | 0.0000 | 0.0183 | 0.0013 | 0.0149 | 0.0333 |
| S8 | `not_yet_known` | 0.6958 | 0.6844 | 0.8098 | 0.7531 | 0.7609 |
| S8 | `short_history` | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| S8 | `stale` | 0.0002 | 0.0003 | 0.0000 | 0.0002 | 0.0001 |
| S8 | `valid` | 0.2891 | 0.2919 | 0.1567 | 0.1800 | 0.1648 |

Member-day census, 1963 to 1992, by later exit class:

| Class | Member days | With daily row | With price | With return | With path value |
| --- | --- | --- | --- | --- | --- |
| current | 661975 | 661822 | 661743 | 661733 | 661742 |
| left_index | 249969 | 249969 | 249827 | 249827 | 249827 |
| cash_merger | 881589 | 881035 | 880774 | 880847 | 880853 |
| failure | 291135 | 291033 | 290039 | 290039 | 290039 |
| unknown | 1689832 | 1688827 | 1688153 | 1688295 | 1688310 |

Screen census over the rebalances of the screen window, last_close loader run (cells; share of pool cells):

| Item | current | left_index | cash_merger | failure | unknown |
| --- | --- | --- | --- | --- | --- |
| pool cells | 31275 | 11813 | 41525 | 13622 | 79185 |
| ME missing, ambiguous | 0 (0.0000) | 0 (0.0000) | 0 (0.0000) | 0 (0.0000) | 0 (0.0000) |
| ME missing, multi_class | 0 (0.0000) | 0 (0.0000) | 0 (0.0000) | 0 (0.0000) | 0 (0.0000) |
| ME missing, no_share_fact | 42 (0.0013) | 5 (0.0004) | 55 (0.0013) | 8 (0.0006) | 96 (0.0012) |
| ME missing, stale_share_fact | 0 (0.0000) | 0 (0.0000) | 0 (0.0000) | 0 (0.0000) | 0 (0.0000) |
| ME missing, unmapped | 9 (0.0003) | 7 (0.0006) | 15 (0.0004) | 46 (0.0034) | 37 (0.0005) |
| unpriced | 9 (0.0003) | 7 (0.0006) | 15 (0.0004) | 46 (0.0034) | 37 (0.0005) |
| basis unseen | 0 (0.0000) | 0 (0.0000) | 0 (0.0000) | 0 (0.0000) | 0 (0.0000) |
| blanked windows | 14 (0.0004) | 6 (0.0005) | 1 (0.0000) | 45 (0.0033) | 57 (0.0007) |

Screen census over the rebalances of the screen window, primary loader run (cells; share of pool cells):

| Item | current | left_index | cash_merger | failure | unknown |
| --- | --- | --- | --- | --- | --- |
| pool cells | 31275 | 11813 | 41528 | 13623 | 79193 |
| ME missing, ambiguous | 0 (0.0000) | 0 (0.0000) | 0 (0.0000) | 0 (0.0000) | 0 (0.0000) |
| ME missing, multi_class | 0 (0.0000) | 0 (0.0000) | 0 (0.0000) | 0 (0.0000) | 0 (0.0000) |
| ME missing, no_share_fact | 42 (0.0013) | 5 (0.0004) | 55 (0.0013) | 8 (0.0006) | 96 (0.0012) |
| ME missing, stale_share_fact | 0 (0.0000) | 0 (0.0000) | 0 (0.0000) | 0 (0.0000) | 0 (0.0000) |
| ME missing, unmapped | 9 (0.0003) | 7 (0.0006) | 18 (0.0004) | 47 (0.0035) | 45 (0.0006) |
| unpriced | 9 (0.0003) | 7 (0.0006) | 15 (0.0004) | 46 (0.0034) | 37 (0.0005) |
| basis unseen | 0 (0.0000) | 0 (0.0000) | 0 (0.0000) | 0 (0.0000) | 0 (0.0000) |
| blanked windows | 14 (0.0004) | 6 (0.0005) | 1 (0.0000) | 45 (0.0033) | 57 (0.0007) |

c = 0 cells by reason and later exit class, primary loader run:

| ID | Reason | current | left_index | cash_merger | failure | unknown |
| --- | --- | --- | --- | --- | --- | --- |
| S1 | few_signals | 365 | 210 | 982 | 311 | 2365 |
| S1 | short_history | 51 | 7 | 52 | 8 | 91 |
| S1 | window_gap | 177 | 72 | 285 | 74 | 588 |
| S2 | few_signals | 212 | 133 | 155 | 93 | 501 |
| S2 | short_history | 0 | 0 | 22 | 0 | 20 |
| S2 | window_gap | 0 | 0 | 0 | 0 | 0 |
| S3 | few_signals | 50 | 44 | 53 | 15 | 131 |
| S3 | short_history | 0 | 0 | 22 | 0 | 20 |
| S3 | window_gap | 0 | 0 | 0 | 0 | 0 |
| S4 | few_signals | 1828 | 205 | 333 | 22 | 2993 |
| S4 | short_history | 7 | 0 | 40 | 0 | 28 |
| S4 | window_gap | 24 | 0 | 0 | 7 | 3 |
| S6 | few_signals | 122 | 3 | 54 | 22 | 166 |
| S6 | short_history | 7 | 0 | 40 | 0 | 28 |
| S6 | window_gap | 24 | 0 | 0 | 7 | 3 |
| S7 | few_signals | 159 | 33 | 247 | 17 | 369 |
| S7 | short_history | 90 | 17 | 136 | 11 | 196 |
| S7 | window_gap | 347 | 161 | 833 | 288 | 1765 |
| S8 | few_signals | 183 | 63 | 183 | 185 | 397 |
| S8 | short_history | 7 | 0 | 40 | 0 | 28 |
| S8 | window_gap | 24 | 0 | 0 | 7 | 3 |

### me_coverage

ME status in member-days and in dollar volume (split-only close times split-adjusted volume), by later exit class and by year (the JSON holds the dollar volume share of each reason):

| Class | Member days | unmapped days | ambiguous days | multi_class days | no_share_fact days | stale_share_fact days | Present days | Dollar volume share present |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| current | 661975 | 233 | 0 | 0 | 861 | 0 | 660881 | 0.998931 |
| left_index | 249969 | 142 | 0 | 0 | 98 | 0 | 249729 | 0.999711 |
| cash_merger | 881589 | 815 | 0 | 0 | 1124 | 0 | 879650 | 0.998138 |
| failure | 291135 | 1105 | 0 | 0 | 171 | 0 | 289859 | 0.999781 |
| unknown | 1689832 | 1777 | 0 | 0 | 1935 | 0 | 1686120 | 0.998086 |

| Year | Member days | unmapped days | ambiguous days | multi_class days | no_share_fact days | stale_share_fact days | Present days | Dollar volume share present |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1963 | 125500 | 130 | 0 | 0 | 196 | 0 | 125174 | 0.999078 |
| 1964 | 126500 | 35 | 0 | 0 | 321 | 0 | 126144 | 0.997141 |
| 1965 | 126000 | 40 | 0 | 0 | 192 | 0 | 125768 | 0.998798 |
| 1966 | 126000 | 42 | 0 | 0 | 0 | 0 | 125958 | 1.000000 |
| 1967 | 125500 | 76 | 0 | 0 | 35 | 0 | 125389 | 0.999931 |
| 1968 | 113000 | 92 | 0 | 0 | 289 | 0 | 112619 | 0.997470 |
| 1969 | 125000 | 348 | 0 | 0 | 124 | 0 | 124528 | 0.998939 |
| 1970 | 127000 | 342 | 0 | 0 | 120 | 0 | 126538 | 0.999402 |
| 1971 | 126500 | 304 | 0 | 0 | 94 | 0 | 126102 | 0.999938 |
| 1972 | 125500 | 238 | 0 | 0 | 76 | 0 | 125186 | 0.999933 |
| 1973 | 126000 | 47 | 0 | 0 | 75 | 0 | 125878 | 0.999985 |
| 1974 | 126500 | 156 | 0 | 0 | 0 | 0 | 126344 | 0.999995 |
| 1975 | 126500 | 258 | 0 | 0 | 3 | 0 | 126239 | 0.999997 |
| 1976 | 126500 | 49 | 0 | 0 | 92 | 0 | 126359 | 0.999882 |
| 1977 | 126000 | 69 | 0 | 0 | 0 | 0 | 125931 | 1.000000 |
| 1978 | 126000 | 141 | 0 | 0 | 0 | 0 | 125859 | 1.000000 |
| 1979 | 126500 | 137 | 0 | 0 | 0 | 0 | 126363 | 1.000000 |
| 1980 | 126500 | 193 | 0 | 0 | 289 | 0 | 126018 | 0.998234 |
| 1981 | 126500 | 301 | 0 | 0 | 180 | 0 | 126019 | 0.998232 |
| 1982 | 126500 | 177 | 0 | 0 | 190 | 0 | 126133 | 0.996650 |
| 1983 | 126500 | 229 | 0 | 0 | 265 | 0 | 126006 | 0.999015 |
| 1984 | 126500 | 403 | 0 | 0 | 771 | 0 | 125326 | 0.984542 |
| 1985 | 126000 | 80 | 0 | 0 | 0 | 0 | 125920 | 1.000000 |
| 1986 | 126500 | 56 | 0 | 0 | 0 | 0 | 126444 | 1.000000 |
| 1987 | 126500 | 69 | 0 | 0 | 204 | 0 | 126227 | 0.998781 |
| 1988 | 126500 | 18 | 0 | 0 | 47 | 0 | 126435 | 0.999875 |
| 1989 | 126000 | 26 | 0 | 0 | 148 | 0 | 125826 | 0.999572 |
| 1990 | 126500 | 15 | 0 | 0 | 174 | 0 | 126311 | 0.999240 |
| 1991 | 126500 | 0 | 0 | 0 | 207 | 0 | 126293 | 0.998838 |
| 1992 | 127000 | 1 | 0 | 0 | 97 | 0 | 126902 | 0.999535 |

Unmapped member-days that the unseen-basis rule alone gives, to 1992:

| Case | By year | Last date |
| --- | --- | --- |
| data_start | 1961 119988, 1962 39911, 1963 94 | 1963-05-15 |
| seal | none | none |

S7 coverage by return month, 1963 and 1964:

| Month | Members | Valid | Valid share | Reasons | basis_unseen at anchor | basis_unseen at anchor - 12 |
| --- | --- | --- | --- | --- | --- | --- |
| 1963-01 | 500 | 48 | 0.096 | missing_item 449, short_history 3 | 1 | 445 |
| 1963-02 | 500 | 56 | 0.112 | missing_item 441, short_history 3 | 1 | 438 |
| 1963-03 | 500 | 60 | 0.120 | missing_item 437, short_history 3 | 1 | 435 |
| 1963-04 | 500 | 70 | 0.140 | missing_item 426, no_market_data 1, short_history 3 | 1 | 425 |
| 1963-05 | 500 | 84 | 0.168 | missing_item 413, short_history 3 | 1 | 411 |
| 1963-06 | 500 | 104 | 0.208 | missing_item 393, short_history 3 | 1 | 392 |
| 1963-07 | 500 | 488 | 0.976 | missing_item 11, short_history 1 | 0 | 7 |
| 1963-08 | 500 | 488 | 0.976 | missing_item 11, short_history 1 | 0 | 7 |
| 1963-09 | 500 | 488 | 0.976 | missing_item 11, short_history 1 | 0 | 7 |
| 1963-10 | 500 | 487 | 0.974 | missing_item 12, short_history 1 | 0 | 7 |
| 1963-11 | 500 | 488 | 0.976 | missing_item 11, short_history 1 | 0 | 7 |
| 1963-12 | 500 | 489 | 0.978 | missing_item 9, short_history 2 | 0 | 7 |
| 1964-01 | 500 | 495 | 0.990 | missing_item 2, no_market_data 1, short_history 2 | 0 | 1 |
| 1964-02 | 500 | 495 | 0.990 | missing_item 2, no_market_data 1, short_history 2 | 0 | 1 |
| 1964-03 | 500 | 494 | 0.988 | missing_item 3, short_history 3 | 0 | 1 |
| 1964-04 | 500 | 494 | 0.988 | missing_item 3, short_history 3 | 0 | 1 |
| 1964-05 | 500 | 493 | 0.986 | missing_item 4, no_market_data 1, short_history 2 | 0 | 1 |
| 1964-06 | 500 | 493 | 0.986 | missing_item 4, short_history 3 | 0 | 1 |
| 1964-07 | 500 | 494 | 0.988 | missing_item 3, short_history 3 | 0 | 0 |
| 1964-08 | 500 | 493 | 0.986 | missing_item 4, short_history 3 | 0 | 0 |
| 1964-09 | 500 | 493 | 0.986 | missing_item 4, short_history 3 | 0 | 0 |
| 1964-10 | 500 | 493 | 0.986 | missing_item 3, short_history 4 | 0 | 0 |
| 1964-11 | 500 | 493 | 0.986 | missing_item 3, short_history 4 | 0 | 0 |
| 1964-12 | 500 | 494 | 0.988 | missing_item 2, short_history 4 | 0 | 0 |

### s2_short_history

By year: the share of S2 member cells typed `short_history`, and the mean ME percentile of S2 `short_history` and S2 valid members (the size effect on the S2 ranks):

| Year | short_history share | Mean ME percentile, short_history | Mean ME percentile, valid |
| --- | --- | --- | --- |
| 1963 | 0.0000 | none | none |
| 1964 | 0.0000 | none | none |
| 1965 | 0.0000 | none | none |
| 1966 | 0.0000 | none | none |
| 1967 | 0.0000 | none | none |
| 1968 | 0.0000 | none | none |
| 1969 | 0.0000 | none | none |
| 1970 | 0.0000 | none | none |
| 1971 | 0.0000 | none | none |
| 1972 | 0.0000 | none | none |
| 1973 | 0.0000 | none | none |
| 1974 | 0.0000 | none | none |
| 1975 | 0.0000 | none | none |
| 1976 | 0.0000 | none | none |
| 1977 | 0.0000 | none | none |
| 1978 | 0.0000 | none | none |
| 1979 | 0.0000 | none | none |
| 1980 | 0.0000 | none | none |
| 1981 | 0.0000 | none | none |
| 1982 | 0.0000 | none | none |
| 1983 | 0.0000 | none | none |
| 1984 | 0.0000 | none | none |
| 1985 | 0.0000 | none | none |
| 1986 | 0.0000 | none | none |
| 1987 | 0.5422 | 0.5080 | none |
| 1988 | 0.9725 | 0.5012 | none |
| 1989 | 0.8567 | 0.4981 | 0.5170 |
| 1990 | 0.0383 | 0.5067 | 0.5007 |
| 1991 | 0.0243 | 0.3936 | 0.5026 |
| 1992 | 0.0215 | 0.4285 | 0.5022 |

### s2_history_rule

S2 cells typed `split_in_basis_window` by year: 1989 8, 1990 10, 1991 9, 1992 9.

Member quarters whose `cfacshr` at rdq differs from the one at the known date, by year of the known date:

| Year | Changed | Same | Unread |
| --- | --- | --- | --- |
| 1987 | 4 | 1418 | 0 |
| 1988 | 0 | 1971 | 1 |
| 1989 | 2 | 1945 | 0 |
| 1990 | 2 | 1949 | 0 |
| 1991 | 2 | 1956 | 0 |
| 1992 | 1 | 1954 | 0 |

Not in the screen stage files: The confirm stage owes the post-seal parts, because the screen stages do not open the check period. These are the member quarters with rdq before 2020-08-03 and a known date on or after it, and the S2 valid share in the post-seal check months..

### path_break

Held positions across a `path_break` row, as aggregates only. The span is the number of screen months that one position blanks. By the public weight rule (2026-10-08), only the run-level look set has a weight sum.

| Book set | Positions | Months blanked | CW weight sum | By later exit class | Span min / median / max |
| --- | --- | --- | --- | --- | --- |
| look, primary | 13 | 215 | 0.0034 | current 1, left_index 2, cash_merger 2, failure 5, unknown 3 | 2 / 16 / 162 |
| look, last_close | 13 | 215 | 0.0034 | current 1, left_index 2, cash_merger 2, failure 5, unknown 3 | 2 / 16 / 162 |
| S1, primary | 0 | 0 | not given | none | none / none / none |
| S1, last_close | 0 | 0 | not given | none | none / none / none |
| S2, primary | 0 | 0 | not given | none | none / none / none |
| S2, last_close | 0 | 0 | not given | none | none / none / none |
| S3, primary | 0 | 0 | not given | none | none / none / none |
| S3, last_close | 0 | 0 | not given | none | none / none / none |
| S4, primary | 0 | 0 | not given | none | none / none / none |
| S4, last_close | 0 | 0 | not given | none | none / none / none |
| S6, primary | 0 | 0 | not given | none | none / none / none |
| S6, last_close | 0 | 0 | not given | none | none / none / none |
| S7, primary | 13 | 215 | not given | current 1, left_index 2, cash_merger 2, failure 5, unknown 3 | 2 / 16 / 162 |
| S7, last_close | 13 | 215 | not given | current 1, left_index 2, cash_merger 2, failure 5, unknown 3 | 2 / 16 / 162 |
| S8, primary | 0 | 0 | not given | none | none / none / none |
| S8, last_close | 0 | 0 | not given | none | none / none / none |

Each candidate's declaration is the run blank set cut to its span (the frozen rule). So a candidate can lose months to positions that its own books do not hold. In the primary run, S1 loses 78 months, with no path-break position in its own books.

Blanked level windows (R6), by later exit class:

| Loader run | Windows | current | left_index | cash_merger | failure | unknown |
| --- | --- | --- | --- | --- | --- | --- |
| primary | 123 | 14 | 6 | 1 | 45 | 57 |
| last_close | 123 | 14 | 6 | 1 | 45 | 57 |

### b2

B2 exclusions as aggregates (rebalances with an exclusion and names excluded):

| Book set | Rebalances | Excluded |
| --- | --- | --- |
| look, primary | 0 | 0 |
| look, last_close | 9 | 9 |
| S1, primary | 0 | 0 |
| S1, last_close | 9 | 9 |
| S2, primary | 0 | 0 |
| S2, last_close | 0 | 0 |
| S3, primary | 0 | 0 |
| S3, last_close | 0 | 0 |
| S4, primary | 0 | 0 |
| S4, last_close | 4 | 4 |
| S6, primary | 0 | 0 |
| S6, last_close | 4 | 4 |
| S7, primary | 0 | 0 |
| S7, last_close | 9 | 9 |
| S8, primary | 0 | 0 |
| S8, last_close | 4 | 4 |

The trial asks for each held position with its weight in each book. The report gives aggregates only (owner data terms O-22). The rows stay in the private stage files. The trial asks for unknown_event_excluded and unknown_event_cw_share at each rebalance. The report gives aggregates only (owner data terms O-22). The rows stay in the private stage files.

### counts

Primary loader run, by candidate:

| ID | Rebalances | Members mean | Members min | Traded mean | Traded min | Pinned mean | c = 0 few signals | c = 0 short history | c = 0 window gap | ME missing | ME missing by reason | Settled excluded | Share at stock cap | Share TE-scaled | B2 rebalances / excluded |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| S1 | 169 | 498.82 | 489 | 498.82 | 489 | 32.3 | 4233 | 209 | 1196 | 163 | unmapped 37, no_share_fact 126 | 30 | 0.325 | 0.000 | 0 / 0 |
| S2 | 37 | 499.38 | 498 | 499.38 | 498 | 29.8 | 1094 | 42 | 0 | 21 | no_share_fact 21 | 0 | 0.297 | 0.000 | 0 / 0 |
| S3 | 37 | 499.38 | 498 | 499.38 | 498 | 8.7 | 293 | 42 | 0 | 21 | no_share_fact 21 | 0 | 0.054 | 0.000 | 0 / 0 |
| S4 | 73 | 499.33 | 497 | 499.33 | 497 | 75.3 | 5381 | 75 | 34 | 43 | unmapped 2, no_share_fact 41 | 2 | 0.041 | 0.000 | 0 / 0 |
| S6 | 73 | 499.33 | 497 | 499.33 | 497 | 6.8 | 367 | 75 | 34 | 43 | unmapped 2, no_share_fact 41 | 2 | 0.000 | 0.000 | 0 / 0 |
| S7 | 349 | 498.87 | 489 | 498.87 | 489 | 12.5 | 825 | 450 | 3394 | 326 | unmapped 126, no_share_fact 200 | 45 | 0.476 | 0.000 | 0 / 0 |
| S8 | 73 | 499.33 | 497 | 499.33 | 497 | 15.4 | 1011 | 75 | 34 | 43 | unmapped 2, no_share_fact 41 | 2 | 0.000 | 0.000 | 0 / 0 |

### tilt_stats

Primary loader run and primary cost (IR is in the screen table). Turnover and cost drag per year are in the JSON.

| ID | Realized TE (daily) | Worst relative drawdown | Size exposure mean | Turnover TILT | Turnover CW | Turnover active | Cost drag TILT | Cost drag active |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| S1 | 0.59% | -2.69% | 0.031 | 1.002 | 0.323 | 0.678 | 0.40% | 0.27% |
| S2 | 0.75% | -1.48% | 0.046 | 1.254 | 0.549 | 0.705 | 0.50% | 0.28% |
| S3 | 0.55% | -0.60% | 0.004 | 1.627 | 0.549 | 1.077 | 0.65% | 0.43% |
| S4 | 0.71% | -1.35% | 0.024 | 0.434 | 0.401 | 0.033 | 0.17% | 0.01% |
| S6 | 0.69% | -2.36% | -0.027 | 0.626 | 0.401 | 0.225 | 0.25% | 0.09% |
| S7 | 0.52% | -1.68% | 0.033 | 0.517 | 0.264 | 0.253 | 0.24% | 0.12% |
| S8 | 1.06% | -4.91% | -0.064 | 0.563 | 0.401 | 0.162 | 0.23% | 0.07% |

### post_publication_split

Active months after the signal's publication year (the M5 convention), primary loader run and primary cost:

| ID | Publication year | Months after | Months before | Annual active mean after | Annual active mean before |
| --- | --- | --- | --- | --- | --- |
| S1 | 1996 | 0 | 90 | none | -0.14% |
| S2 | 1989 | 36 | 0 | 0.31% | none |
| S3 | 1996 | 0 | 36 | none | 0.59% |
| S4 | 2013 | 0 | 72 | none | 0.53% |
| S6 | 2008 | 0 | 72 | none | 0.03% |
| S7 | 2008 | 0 | 133 | none | 0.02% |
| S8 | 1992 | 0 | 72 | none | -0.40% |

### labels

- Rule: every header states the run label of evidence_ceiling and the factor-level reuse of M5 step 2 (JKP and French factors, 1926-2025).
- Run label: stock-level out-of-sample, factor-level in-sample; never called confirmation.
- Factor-level reuse: M5 step 2: JKP and French factor returns 1926-2025, built from the same CRSP stocks (factor level).

### bid_ask_midpoint_share

Share of member-days (1963 to 1992) with `dlyprcflg` = 'BA': 0.0092.

### low_risk_r6

Ratio status counts: `defined_full` 131, `defined_partial` 159, `ratio_window_short` 64. Gap rebalances 296, ratio gap members 3660, max ratio_gap_cw_share 0.0928. Members by later exit class:

| Group | current | left_index | cash_merger | failure | unknown |
| --- | --- | --- | --- | --- | --- |
| gap_members | 347 | 178 | 906 | 336 | 1893 |
| limiting_partial | 59 | 10 | 92 | 6 | 128 |
| limiting_short | 31 | 7 | 46 | 5 | 64 |

## Owed by later stages, items given as aggregates only, and withheld weights

- `check_period_end`: the confirm stage owes it. The trial asks for the last check return month, as the driver records it.
- `check_gap_months`: the confirm stage owes it. The trial asks for the 26 check-gap months (2019-07 to 2021-08) left out of every check series, with the reason for each part (seal, sealed 2020-07-31 row, warm-up).
- `s2_history_rule`: The confirm stage owes the post-seal parts, because the screen stages do not open the check period. These are the member quarters with rdq before 2020-08-03 and a known date on or after it, and the S2 valid share in the post-seal check months.
- `path_break`: The trial asks for each held position with its weight in each book. The report gives aggregates only (owner data terms O-22). The rows stay in the private stage files.
- `b2`: The trial asks for unknown_event_excluded and unknown_event_cw_share at each rebalance. The report gives aggregates only (owner data terms O-22). The rows stay in the private stage files.
- `b2.max_cw_share`: The largest CW share excluded at one rebalance, for the look and each candidate. The report does not give it: private per O-22 (public weight rule, 2026-10-08). The value stays in the private stage files.
- `counts.b2.max_cw_share`: The same B2 maximum in the counts of the look and each candidate. The report does not give it: private per O-22 (public weight rule, 2026-10-08). The value stays in the private stage files.
- `path_break.screen.weight_sum`: The weight sum of each candidate group, CW and TILT. The run-level look sum stays. The report does not give it: private per O-22 (public weight rule, 2026-10-08). The value stays in the private stage files.
- `r4.look.by_cause.weight_at_last_rebalance_sum`: The weight share of each cause in the look groups. At least one cause does not meet the rule. Two loader runs with equal counts of a cause fail it, because the stage files hold no event identity to show that the events are the same. The report does not give it: private per O-22 (public weight rule, 2026-10-08). The value stays in the private stage files.
- `r4.look.incoming_weight_max`: The largest book weight at one event. The report does not give it: private per O-22 (public weight rule, 2026-10-08). The value stays in the private stage files.
- `r4.screen.incoming_weight_max`: The largest book weight at one event in each candidate group. The report does not give it: private per O-22 (public weight rule, 2026-10-08). The value stays in the private stage files.
- `r4.screen.incoming_weight_sum`: The engine total weight at the event of each candidate group, CW and TILT. The report does not give it: private per O-22 (public weight rule, 2026-10-08). The value stays in the private stage files.
- `r4.screen.weight_at_last_rebalance_sum`: The weight share by cause of each candidate group, CW and TILT. Each group nests in the look group, so a difference can isolate one event. The report does not give it: private per O-22 (public weight rule, 2026-10-08). The value stays in the private stage files.

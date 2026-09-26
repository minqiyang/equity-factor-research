# M4.7 Coverage Census

Evidence ceiling: `DIAGNOSTIC_ONLY`. No figure below supports a ranking, selection, promotion, or profitability claim.

- Snapshot id: `real_v1`
- Code commit: `c52baec8f67424e1d7e243f4eb730fbe219b36e1`
- Seal: prospective SHA-256 `93ce6e5ad003927dbf7f1521c26aca6a17844cb3061a44f7885a5584612e9882`; holdout end `2020-07-31`
- Seal rule: `earliest_available_year_from_raw_membership_counts_option_a_v1` (minimum in-band years 7, latest holdout end None, minimum IC months 48)
- Owner-accepted shortfall bounds: {'owner_decision': 'O-7 2026-09-26', 'min_in_band_years': 6.9, 'min_ic_months': 32, 'max_gap_windows': 25, 'max_excluded_fraction': 0.45, 'max_unpriced_fraction': 0.4}
- Calendar source: `SPY.US_eod_dates_v1`
- Readiness: `ready_with_caveats:coverage_shortfall_accepted,holdout_breadth_after_identity` (R-CENSUS-1 ready_with_caveats:coverage_shortfall_accepted, R-CENSUS-7 ready_with_caveats:holdout_breadth_after_identity, R-CENSUS-9 ready_with_caveats:coverage_shortfall_accepted)
- manifest_sha256: `ffa760532bc553a0f290c1bb04d4b1c0bd60163e6df70571737d6df3cc9335c7`
- discovery_inputs_sha256: `2395bc5af73dcffb8ab9d77acf9691ee9c83e08b03b8c107c275d08351c403e7`
- support_sha256: `21731a0f987ea498e7311c5f74eafff4e3e90ed386bd8f250cc285625379e2f9` (`asset_level_holding_period_support_exclusion_v1`)

## Premises and owner disposition

- VP-1: served volume carries the split product the prices carry; tested by volume_basis_split_diagnostic; `a1_volume_half = consistent` over 65 rows, median ell -0.08284632211045026, share above 0.5 at ratio >= 2: 0.0.
- VP-2: declared distributions are applied as non-split adjustments by the prior-close formula and no other; ratified under owner item O-8; exposure measured by B_D and S_D; written episodes with a declared-distribution pair: 452; B_D max 0.06158019855770058; S_D max 0.3690846735460174; member-days with S_D > 0.05: 178859; vp2_revisit_required: True.
- O-8: ratified; revisit when member-days with S_D > 0.05 exceed 1 percent of eligible member-days.
- Rounding: rounding refusals at low adjusted levels select on later splits; refused member-days by minimum adjusted level: {'<0.1': 0, '[0.1,1)': 0, '>=1': 56516}.
- Survivorship: members without a discovery panel are unpriced eligible member-days, capped by R-CENSUS-9.
- Discovery overlap with prior exposures: static_50_name_cohort 1.0000, historical_evaluation 0.2167

## Readiness rules

| Rule | Passed |
| --- | --- |
| R-CENSUS-1 | False |
| R-CENSUS-2 | True |
| R-CENSUS-3 | True |
| R-CENSUS-4 | True |
| R-CENSUS-5 | True |
| R-CENSUS-6 | True |
| R-CENSUS-7 | False |
| R-CENSUS-8 | True |
| R-CENSUS-9 | False |
| R-CENSUS-10 | True |

## Coverage

| Metric | Value |
| --- | --- |
| Eligible member-days | 795198 |
| Eligible unpriced member-days | 262191 |
| Eligible unpriced fraction | 0.329718 |
| Identity refusal fraction | 0.003494 |
| Unresolved events in the window | 24 |
| Support-excluded cells | 27 of 26237 |
| Support-excluded fraction | 0.001029 |
| Evaluated breadth (min, median, max) | 424, 430, 433 |
| IC month supply | 60 |
| Kill reachable (projection) | False |

## Asset-level support exclusions

A missing bar or an unevidenced disappearance excludes only the affected asset from the reset whose holding period needs that bar. Each exclusion conditions on that asset's own bar availability over one holding period.

- Excluded cells by reason: {'missing_bar': 1, 'unresolved_delisting': 26}

| Reset | Signal-eligible | Support-excluded | Evaluated |
| --- | --- | --- | --- |
| 2021-08-31 | 424 | 0 | 424 |
| 2021-09-30 | 425 | 0 | 425 |
| 2021-10-29 | 425 | 0 | 425 |
| 2021-11-30 | 425 | 1 | 424 |
| 2021-12-31 | 426 | 0 | 426 |
| 2022-01-31 | 426 | 1 | 425 |
| 2022-02-28 | 427 | 1 | 426 |
| 2022-03-31 | 427 | 0 | 427 |
| 2022-04-29 | 428 | 0 | 428 |
| 2022-05-31 | 428 | 1 | 427 |
| 2022-06-30 | 427 | 0 | 427 |
| 2022-07-29 | 427 | 0 | 427 |
| 2022-08-31 | 427 | 0 | 427 |
| 2022-09-30 | 427 | 3 | 424 |
| 2022-10-31 | 427 | 0 | 427 |
| 2022-11-30 | 428 | 1 | 427 |
| 2022-12-30 | 428 | 0 | 428 |
| 2023-01-31 | 429 | 0 | 429 |
| 2023-02-28 | 429 | 1 | 428 |
| 2023-03-31 | 430 | 1 | 429 |
| 2023-04-28 | 430 | 1 | 429 |
| 2023-05-31 | 430 | 0 | 430 |
| 2023-06-30 | 430 | 0 | 430 |
| 2023-07-31 | 430 | 0 | 430 |
| 2023-08-31 | 429 | 0 | 429 |
| 2023-09-29 | 431 | 1 | 430 |
| 2023-10-31 | 432 | 0 | 432 |
| 2023-11-30 | 432 | 0 | 432 |
| 2023-12-29 | 433 | 0 | 433 |
| 2024-01-31 | 433 | 0 | 433 |
| 2024-02-29 | 433 | 0 | 433 |
| 2024-03-28 | 433 | 0 | 433 |
| 2024-04-30 | 433 | 1 | 432 |
| 2024-05-31 | 433 | 0 | 433 |
| 2024-06-28 | 433 | 0 | 433 |
| 2024-07-31 | 433 | 0 | 433 |
| 2024-08-30 | 433 | 0 | 433 |
| 2024-09-30 | 432 | 0 | 432 |
| 2024-10-31 | 433 | 1 | 432 |
| 2024-11-29 | 433 | 1 | 432 |
| 2024-12-31 | 432 | 0 | 432 |
| 2025-01-31 | 432 | 0 | 432 |
| 2025-02-28 | 432 | 0 | 432 |
| 2025-03-31 | 433 | 0 | 433 |
| 2025-04-30 | 433 | 1 | 432 |
| 2025-05-30 | 433 | 0 | 433 |
| 2025-06-30 | 433 | 3 | 430 |
| 2025-07-31 | 433 | 1 | 432 |
| 2025-08-29 | 432 | 0 | 432 |
| 2025-09-30 | 432 | 0 | 432 |
| 2025-10-31 | 433 | 1 | 432 |
| 2025-11-28 | 432 | 2 | 430 |
| 2025-12-31 | 430 | 0 | 430 |
| 2026-01-30 | 430 | 1 | 429 |
| 2026-02-27 | 430 | 0 | 430 |
| 2026-03-31 | 430 | 1 | 429 |
| 2026-04-30 | 430 | 1 | 429 |
| 2026-05-29 | 430 | 0 | 430 |
| 2026-06-30 | 430 | 0 | 430 |
| 2026-07-31 | 429 | 1 | 428 |
| 2026-08-07 | 429 | 0 | 429 |

## Holdout integrity (metadata)

- splits_holdout_quarantined: 0
- eod_holdout_quarantined: 0
- dividends_holdout_quarantined: 0

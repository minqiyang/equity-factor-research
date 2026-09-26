# M4.7 Coverage Census

Evidence ceiling: `DIAGNOSTIC_ONLY`. No figure below supports a ranking, selection, promotion, or profitability claim.

- Snapshot id: `real_v1`
- Code commit: `9fd77349408f43ec22e564ae06c9ab8ec26fa476`
- Seal: prospective SHA-256 `93ce6e5ad003927dbf7f1521c26aca6a17844cb3061a44f7885a5584612e9882`; holdout end `2020-07-31`
- Seal rule: `earliest_available_year_from_raw_membership_counts_option_a_v1` (minimum in-band years 7, latest holdout end None, minimum IC months 48)
- Owner-accepted shortfall bounds: {'owner_decision': 'O-7 2026-09-26', 'min_in_band_years': 6.9, 'min_ic_months': 32, 'max_gap_windows': 25, 'max_excluded_fraction': 0.45, 'max_unpriced_fraction': 0.4}
- Calendar source: `SPY.US_eod_dates_v1`
- Readiness: `ready_with_caveats:coverage_shortfall_accepted,holdout_breadth_after_identity` (R-CENSUS-1 ready_with_caveats:coverage_shortfall_accepted, R-CENSUS-2 ready_with_caveats:coverage_shortfall_accepted, R-CENSUS-7 ready_with_caveats:holdout_breadth_after_identity, R-CENSUS-8 ready_with_caveats:coverage_shortfall_accepted, R-CENSUS-9 ready_with_caveats:coverage_shortfall_accepted)
- manifest_sha256: `ffa760532bc553a0f290c1bb04d4b1c0bd60163e6df70571737d6df3cc9335c7`
- discovery_inputs_sha256: `2395bc5af73dcffb8ab9d77acf9691ee9c83e08b03b8c107c275d08351c403e7`
- segments_sha256: `6b014b13a9f5017e0f5d0b383079f16b5d2915a24fe9a8862fa14e88a8ba5933`

## Premises and owner disposition

- VP-1: served volume carries the split product the prices carry; tested by volume_basis_split_diagnostic; `a1_volume_half = consistent` over 65 rows, median ell -0.08284632211045026, share above 0.5 at ratio >= 2: 0.0.
- VP-2: declared distributions are applied as non-split adjustments by the prior-close formula and no other; ratified under owner item O-8; exposure measured by B_D and S_D; written episodes with a declared-distribution pair: 452; B_D max 0.06158019855770058; S_D max 0.3690846735460174; member-days with S_D > 0.05: 178859; vp2_revisit_required: True.
- O-8: ratified; revisit when member-days with S_D > 0.05 exceed 1 percent of eligible member-days.
- Rounding: rounding refusals at low adjusted levels select on later splits; refused member-days by minimum adjusted level: {'<0.1': 0, '[0.1,1)': 0, '>=1': 56516}.
- Survivorship: members without a discovery panel are unpriced eligible member-days, capped by R-CENSUS-9.
- Discovery overlap with prior exposures: static_50_name_cohort 1.0000, historical_evaluation 0.0625

## Readiness rules

| Rule | Passed |
| --- | --- |
| R-CENSUS-1 | False |
| R-CENSUS-2 | False |
| R-CENSUS-3 | True |
| R-CENSUS-4 | True |
| R-CENSUS-5 | True |
| R-CENSUS-6 | True |
| R-CENSUS-7 | False |
| R-CENSUS-8 | False |
| R-CENSUS-9 | False |
| R-CENSUS-10 | True |

## Coverage

| Metric | Value |
| --- | --- |
| Eligible member-days | 795198 |
| Eligible unpriced member-days | 262175 |
| Eligible unpriced fraction | 0.329698 |
| Identity refusal fraction | 0.003494 |
| Gap windows | 20 |
| Excluded fraction | 0.384181 |
| IC month supply | 32 |
| Kill reachable (projection) | False |

## Gap windows (month granularity)

| Start month | End month | Reasons | Rows |
| --- | --- | --- | --- |
| 2021-12 | 2021-12 | unresolved_delisting | 11 |
| 2022-02 | 2022-03 | unresolved_delisting | 23 |
| 2022-06 | 2022-06 | unresolved_delisting | 14 |
| 2022-10 | 2022-10 | unresolved_delisting | 19 |
| 2022-12 | 2022-12 | unresolved_delisting | 3 |
| 2023-03 | 2023-03 | unresolved_delisting | 15 |
| 2023-04 | 2023-04 | missing_bar | 15 |
| 2023-05 | 2023-05 | unresolved_delisting | 19 |
| 2023-10 | 2023-10 | unresolved_delisting | 11 |
| 2024-05 | 2024-05 | unresolved_delisting | 19 |
| 2024-11 | 2024-11 | unresolved_delisting | 3 |
| 2024-12 | 2024-12 | unresolved_delisting | 8 |
| 2025-05 | 2025-05 | unresolved_delisting | 8 |
| 2025-07 | 2025-07 | unresolved_delisting | 19 |
| 2025-08 | 2025-09 | unresolved_delisting | 21 |
| 2025-11 | 2025-12 | unresolved_delisting | 22 |
| 2026-02 | 2026-02 | unresolved_delisting | 15 |
| 2026-04 | 2026-04 | unresolved_delisting | 16 |
| 2026-05 | 2026-05 | unresolved_delisting | 14 |
| 2026-08 | 2026-08 | unresolved_delisting | 1 |

## Holdout integrity (metadata)

- splits_holdout_quarantined: 0
- eod_holdout_quarantined: 0
- dividends_holdout_quarantined: 0

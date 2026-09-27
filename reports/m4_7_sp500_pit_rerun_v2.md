# M4.7 S&P 500 PIT Rerun (registration v2, asset-level support)

Evidence ceiling: `DIAGNOSTIC_ONLY`. No figure below supports a ranking, selection, promotion, or profitability claim; `formal_universe_evidence_eligible` and `formal_terminal_evidence_eligible` are false.

- Run status: `completed`
- Registration SHA-256: `4a6f8b5a0478bd70e90cd84e440a389898630f2e156eb0488c96ca0e8923e7dc`
- Code commit: `cd597363ea009f56eb42f73a1ef62cda89b61e34`
- Snapshot: `real_v1`; manifest SHA-256 `ffa760532bc553a0f290c1bb04d4b1c0bd60163e6df70571737d6df3cc9335c7`
- support_sha256: `21731a0f987ea498e7311c5f74eafff4e3e90ed386bd8f250cc285625379e2f9`; census JSON SHA-256 `8308828f3b8c2e2850bd95da9227cc21d82fee0e99133dbc58e533705039967e`
- Discovery window: holdout end `2020-07-31`, D0 `2021-08-31`, D_last `2026-08-07`, D_end `2026-07-31`
- Prior-exposure overlap fractions: historical_evaluation 0.216667, static_50_name_cohort 1
- |U| = 24; support-excluded cells |X| = 27 of 26237 signal-eligible cells (fraction 0.00102908); by reason {'missing_bar': 1, 'unresolved_delisting': 26}
- Eligible unpriced member-day fraction: 0.329718
- Census readiness: `ready_with_caveats:coverage_shortfall_accepted,holdout_breadth_after_identity`
- Holdout guard: first loaded date `2020-07-31`, overlap false

## Premises

- VP-1: volume_carries_the_split_adjustment_of_prices_tested_by_volume_basis_split_diagnostic; `a1_volume_half = consistent`
- VP-2: declared_distributions_applied_as_non_split_adjustments_by_the_registered_formula_and_no_other; in_span_distribution_support fraction 0.691043; B_D quantiles {'max': 0.06158019855770058, 'median': 0.004605331893814403, 'p90': 0.013300995098455408}; S_D quantiles {'max': 0.3690846735460174, 'median': 0.026009951257084055, 'p90': 0.12368797276555338}; vp2_revisit_required true
- O-8 disposition: re_ratified_diagnostic_only
- Rounding: rounding refusals at low adjusted levels select on later splits

## Assumptions

- timing_contract: after_close_signal_next_observed_close_v1
- label_contract: terminal_aware_reset_to_reset_forward_return_v2
- support_contract: asset_level_holding_period_support_exclusion_v1
- evaluation_window: {'anchor': '2021-08-30', 'first_measured': '2021-08-31', 'last_measured': '2026-08-07', 'evaluation_resets': 61}
- support_exclusion_lookahead: each excluded cell conditions on its own asset's bar availability over one holding period; signal inputs never read the exclusion
- initialization_anchor_policy: zero_return_zero_trade_all_cash_excluded_from_statistics
- terminal_row_policy: include_return_trade_cost_open_holdings_no_future_return
- settlement_lag_distribution: {}
- cash_availability_idealization_rows_max: 3
- consideration_valuation_rule: acquirer_close_at_completion_date_row_v1
- settlement_contract: prior_observed_close_to_consideration_at_completion_date_row_v2
- costs: {'primary': {'slippage_bps': 4.0, 'transaction_cost_bps': 1.0}, 'sensitivity_2x': {'slippage_bps': 8.0, 'transaction_cost_bps': 2.0}, 'zero_cost_diagnostic_only': {'slippage_bps': 0.0, 'transaction_cost_bps': 0.0}}
- impact_model: none
- borrow_cost: absent_from_the_long_short_engine
- first_discovery_date: 2021-08-31
- market_beta_neutral_composite_market: equal_weight_market_of_eligible_names
- engine_frame_columns: member_permanent_ids_only
- member_columns: 558

## Labels and IC months

- ic_month_supply: 60
- ic_months_horizon_unmeasured: 1
- terminal_aware_labels: 0
- missing_execution_bar: 0
- missing_horizon_end_bar: 0

## Monthly cross-sectional breadth

A missing bar or an unevidenced disappearance excludes only the affected asset from the reset whose holding period needs that bar; every other asset and month stays evaluated.

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

## Family A primary tests (monthly Rank IC, BY within family of 6)

| Factor | Status | T_f | Mean IC | HAC p | BY q | Union BY q | Half 1 mean | Half 2 mean | Sign stable | MDE_f | MDE_single | Coverage loss | Estimate | Beyond estimate | LS status | LS mean net | LS HAC p |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| MOM_12_1 | evaluated | 60 | 0.0187685 | 0.328505 | 1 | 1 | 0.0265805 | 0.0109565 | true | 0.0724237 | 0.0538122 | 64 | 64 | 0 | evaluated | 0.000175756 | 0.402787 |
| HIGH_52W | evaluated | 60 | 0.00903759 | 0.64771 | 1 | 1 | 0.015539 | 0.00253616 | true | 0.0745749 | 0.0554105 | 75 | 63 | 12 | evaluated | 3.29731e-05 | 0.877417 |
| REV_1M | evaluated | 60 | -0.0173888 | 0.336964 | 1 | 1 | 0.00224908 | -0.0370266 | false | 0.0682842 | 0.0507364 | 2 | 2 | 0 | evaluated | -0.000194395 | 0.273938 |
| LOW_VOL_252 | evaluated | 60 | -0.0063005 | 0.81525 | 1 | 1 | 0.0151636 | -0.0277646 | false | 0.101671 | 0.0755433 | 76 | 64 | 12 | evaluated | -0.000239783 | 0.331114 |
| LOW_BETA_252 | evaluated | 60 | -0.0159657 | 0.641517 | 1 | 1 | 0.0140325 | -0.0459639 | false | 0.1293 | 0.0960725 | 76 | 64 | 12 | evaluated | -0.000206765 | 0.462934 |
| AMIHUD_ILLIQ_63 | evaluated | 60 | -0.013076 | 0.258819 | 1 | 1 | -0.0239561 | -0.00219594 | false | 0.043663 | 0.0324424 | 21 | 18 | 3 | evaluated | -0.000113429 | 0.324737 |

## Family B primary tests (monthly Rank IC, BY within family of 63)

| Factor | Status | T_f | Mean IC | HAC p | BY q | Union BY q | Half 1 mean | Half 2 mean | Sign stable | MDE_f | MDE_single | Coverage loss | Estimate | Beyond estimate | LS status | LS mean net | LS HAC p |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ALPHA_001 | evaluated | 60 | -0.00229492 | 0.865624 | 1 | 1 | -0.00825525 | 0.00366542 | false | 0.0511355 | 0.0379946 | 70 | undefined | undefined | evaluated | -8.88897e-05 | 0.320504 |
| ALPHA_002 | evaluated | 60 | 0.00694318 | 0.328871 | 1 | 1 | 0.00391068 | 0.00997568 | true | 0.0268126 | 0.0199223 | 29 | undefined | undefined | evaluated | 2.22136e-05 | 0.743021 |
| ALPHA_003 | evaluated | 60 | -0.0114711 | 0.169284 | 1 | 1 | -0.0123447 | -0.0105975 | false | 0.0314674 | 0.0233809 | 250 | undefined | undefined | evaluated | -7.66349e-05 | 0.214969 |
| ALPHA_004 | evaluated | 60 | -0.0202983 | 0.206824 | 1 | 1 | -0.00408828 | -0.0365083 | false | 0.0606296 | 0.0450489 | 42 | undefined | undefined | evaluated | -0.000124385 | 0.260408 |
| ALPHA_005 | evaluated | 60 | -0.01159 | 0.38206 | 1 | 1 | -0.000543147 | -0.0226369 | false | 0.0499947 | 0.037147 | 50 | undefined | undefined | evaluated | -9.11131e-05 | 0.437296 |
| ALPHA_006 | evaluated | 60 | -0.0101262 | 0.354376 | 1 | 1 | -0.0194946 | -0.000757799 | false | 0.0412266 | 0.0306321 | 50 | undefined | undefined | evaluated | -8.62017e-05 | 0.330035 |
| ALPHA_007 | evaluated | 60 | -0.00578534 | 0.517882 | 1 | 1 | 0.00689773 | -0.0184684 | false | 0.0337355 | 0.0250661 | 117 | undefined | undefined | evaluated | -5.73604e-05 | 0.448162 |
| ALPHA_008 | evaluated | 60 | 0.00261421 | 0.848622 | 1 | 1 | 0.00796907 | -0.00274064 | false | 0.0516406 | 0.0383699 | 55 | undefined | undefined | evaluated | -5.1589e-07 | 0.996788 |
| ALPHA_009 | evaluated | 60 | 0.00364782 | 0.825899 | 1 | 1 | -0.015052 | 0.0223476 | false | 0.0625296 | 0.0464607 | 16 | undefined | undefined | evaluated | 5.71414e-05 | 0.646753 |
| ALPHA_010 | evaluated | 60 | -0.00123671 | 0.937011 | 1 | 1 | -0.0224429 | 0.0199694 | false | 0.0590056 | 0.0438422 | 7 | undefined | undefined | evaluated | 6.94956e-05 | 0.538291 |
| ALPHA_012 | evaluated | 60 | -0.00757106 | 0.353731 | 1 | 1 | -0.0100923 | -0.00504978 | false | 0.0307825 | 0.022872 | 3 | undefined | undefined | evaluated | -5.22888e-05 | 0.516679 |
| ALPHA_013 | evaluated | 60 | -0.00944198 | 0.15218 | 1 | 1 | -0.0122491 | -0.00663488 | false | 0.0248635 | 0.0184741 | 7 | undefined | undefined | evaluated | -6.36917e-05 | 0.382942 |
| ALPHA_014 | evaluated | 60 | -0.0154655 | 0.175074 | 1 | 1 | -0.0216817 | -0.00924937 | false | 0.0430016 | 0.0319509 | 50 | undefined | undefined | evaluated | -8.5746e-05 | 0.316299 |
| ALPHA_015 | evaluated | 60 | -0.0109881 | 0.18251 | 1 | 1 | -0.00533076 | -0.0166455 | false | 0.0310796 | 0.0230927 | 4435 | undefined | undefined | evaluated | -0.000222922 | 0.00243752 |
| ALPHA_016 | evaluated | 60 | -0.00911659 | 0.203216 | 1 | 1 | -0.0107602 | -0.00747297 | false | 0.0270146 | 0.0200723 | 7 | undefined | undefined | evaluated | -7.97322e-05 | 0.27794 |
| ALPHA_017 | evaluated | 60 | -0.0230793 | 0.0957992 | 1 | 1 | -0.0210044 | -0.0251541 | false | 0.0522472 | 0.0388207 | 78 | undefined | undefined | evaluated | -0.000154974 | 0.16737 |
| ALPHA_018 | evaluated | 60 | 0.00922408 | 0.578522 | 1 | 1 | -0.00285918 | 0.0213073 | false | 0.0626048 | 0.0465165 | 50 | undefined | undefined | evaluated | 0.000125303 | 0.326122 |
| ALPHA_019 | evaluated | 60 | -0.00917856 | 0.584653 | 1 | 1 | 0.00753731 | -0.0258944 | false | 0.0633153 | 0.0470444 | 847 | undefined | undefined | evaluated | -5.61503e-05 | 0.665124 |
| ALPHA_020 | evaluated | 60 | -0.018433 | 0.372522 | 1 | 1 | -0.0168553 | -0.0200107 | false | 0.0779387 | 0.0579099 | 3 | undefined | undefined | evaluated | -0.000229036 | 0.0944495 |
| ALPHA_021 | evaluated | 60 | -0.00523317 | 0.606319 | 1 | 1 | 0.0115086 | -0.0219749 | false | 0.0382895 | 0.0284498 | 64 | undefined | undefined | evaluated | -0.000102989 | 0.173223 |
| ALPHA_022 | evaluated | 60 | -0.0181109 | 0.0751764 | 1 | 1 | -0.0211176 | -0.0151042 | false | 0.0383773 | 0.028515 | 64 | undefined | undefined | evaluated | -9.89973e-05 | 0.239585 |
| ALPHA_023 | evaluated | 60 | 0.00246537 | 0.825659 | 1 | 1 | 0.0129381 | -0.00800733 | false | 0.0422013 | 0.0313563 | 64 | undefined | undefined | evaluated | 2.39165e-05 | 0.819973 |
| ALPHA_024 | evaluated | 60 | 0.0148342 | 0.151556 | 1 | 1 | 0.0201914 | 0.00947696 | true | 0.0390034 | 0.0289802 | 692 | undefined | undefined | evaluated | 7.55371e-05 | 0.480192 |
| ALPHA_025 | evaluated | 60 | -0.000726721 | 0.965246 | 1 | 1 | -0.00884106 | 0.00738762 | false | 0.0628879 | 0.0467269 | 64 | undefined | undefined | evaluated | -2.36743e-05 | 0.86508 |
| ALPHA_026 | evaluated | 60 | -0.0102145 | 0.404421 | 1 | 1 | 0.00813747 | -0.0285664 | false | 0.0461937 | 0.0343228 | 2447 | undefined | undefined | evaluated | -3.48121e-05 | 0.682501 |
| ALPHA_028 | evaluated | 60 | 0.00925388 | 0.533261 | 1 | 1 | -0.00965508 | 0.0281628 | false | 0.0560035 | 0.0416116 | 78 | undefined | undefined | evaluated | 0.000114649 | 0.345046 |
| ALPHA_030 | evaluated | 60 | 0.00255204 | 0.857279 | 1 | 1 | 0.0114137 | -0.00630963 | false | 0.0535066 | 0.0397564 | 64 | undefined | undefined | evaluated | -1.45548e-06 | 0.990249 |
| ALPHA_031 | evaluated | 60 | 0.00315581 | 0.815477 | 1 | 1 | 0.0179094 | -0.0115977 | false | 0.0509893 | 0.037886 | 122 | undefined | undefined | evaluated | -4.81331e-05 | 0.678577 |
| ALPHA_032 | evaluated | 60 | -0.00202016 | 0.89792 | 1 | 1 | 0.0166428 | -0.0206831 | false | 0.0593744 | 0.0441163 | 793 | undefined | undefined | evaluated | -7.15165e-05 | 0.567426 |
| ALPHA_033 | evaluated | 60 | 0.00136123 | 0.951584 | 1 | 1 | -0.00812927 | 0.0108517 | false | 0.0845317 | 0.0628086 | 0 | undefined | undefined | evaluated | 7.00005e-05 | 0.651749 |
| ALPHA_034 | evaluated | 60 | 0.00322339 | 0.833364 | 1 | 1 | -0.0205209 | 0.0269677 | false | 0.0577689 | 0.0429233 | 7 | undefined | undefined | evaluated | 1.79059e-05 | 0.866829 |
| ALPHA_035 | evaluated | 60 | -0.0145207 | 0.286859 | 1 | 1 | -0.00672278 | -0.0223186 | false | 0.0514074 | 0.0381967 | 126 | undefined | undefined | evaluated | -0.000117169 | 0.343118 |
| ALPHA_036 | evaluated | 60 | 0.00668316 | 0.572034 | 1 | 1 | 0.0111481 | 0.00221828 | true | 0.0445958 | 0.0331355 | 692 | undefined | undefined | evaluated | 1.25477e-05 | 0.879873 |
| ALPHA_037 | evaluated | 60 | 0.0192029 | 0.312645 | 1 | 1 | 0.00154066 | 0.0368652 | true | 0.0717108 | 0.0532824 | 694 | undefined | undefined | evaluated | 0.000105692 | 0.39657 |
| ALPHA_038 | evaluated | 60 | -0.0139688 | 0.471285 | 1 | 1 | -0.014524 | -0.0134136 | false | 0.0731133 | 0.0543245 | 50 | undefined | undefined | evaluated | -7.4802e-05 | 0.608244 |
| ALPHA_039 | evaluated | 60 | -0.02002 | 0.18745 | 1 | 1 | -0.00450903 | -0.035531 | false | 0.0572664 | 0.04255 | 847 | undefined | undefined | evaluated | -0.000206691 | 0.11494 |
| ALPHA_040 | evaluated | 60 | -0.0102161 | 0.402447 | 1 | 1 | -0.0227496 | 0.00231741 | false | 0.0460076 | 0.0341845 | 50 | undefined | undefined | evaluated | -0.0001315 | 0.199843 |
| ALPHA_041 | evaluated | 60 | 0.00456538 | 0.791989 | 1 | 1 | -0.00703183 | 0.0161626 | false | 0.0652716 | 0.048498 | 0 | undefined | undefined | evaluated | 0.000158411 | 0.199328 |
| ALPHA_042 | evaluated | 60 | 0.0147726 | 0.299155 | 1 | 1 | -0.000301983 | 0.0298472 | false | 0.0536489 | 0.0398621 | 0 | undefined | undefined | evaluated | 0.000209285 | 0.0945277 |
| ALPHA_043 | evaluated | 60 | -0.0197089 | 0.12592 | 1 | 1 | -0.0130805 | -0.0263372 | false | 0.0485583 | 0.0360797 | 136 | undefined | undefined | evaluated | -0.000127503 | 0.213976 |
| ALPHA_044 | evaluated | 60 | -0.0161384 | 0.0528209 | 1 | 1 | -0.00699026 | -0.0252865 | false | 0.0314249 | 0.0233493 | 91 | undefined | undefined | evaluated | -9.9373e-05 | 0.180906 |
| ALPHA_045 | evaluated | 60 | 0.00223723 | 0.766798 | 1 | 1 | -0.000902848 | 0.0053773 | false | 0.0284442 | 0.0211345 | 199 | undefined | undefined | evaluated | 7.19202e-05 | 0.258836 |
| ALPHA_046 | evaluated | 60 | 0.000802357 | 0.94078 | 1 | 1 | 0.0087816 | -0.00717689 | false | 0.0407236 | 0.0302584 | 69 | undefined | undefined | evaluated | 1.85549e-05 | 0.821748 |
| ALPHA_049 | evaluated | 60 | -0.0035277 | 0.759084 | 1 | 1 | -0.00952715 | 0.00247175 | false | 0.0433715 | 0.0322258 | 50 | undefined | undefined | evaluated | 2.09453e-05 | 0.852168 |
| ALPHA_050 | evaluated | 60 | -0.0075873 | 0.364251 | 1 | 1 | -0.0149346 | -0.000240004 | false | 0.0315314 | 0.0234284 | 1232 | undefined | undefined | evaluated | -5.25637e-05 | 0.38195 |
| ALPHA_051 | evaluated | 60 | -0.00477474 | 0.724576 | 1 | 1 | -0.0149788 | 0.00542935 | false | 0.0510952 | 0.0379646 | 69 | undefined | undefined | evaluated | -5.52444e-05 | 0.634052 |
| ALPHA_052 | evaluated | 60 | -0.0126373 | 0.32769 | 1 | 1 | 0.00330244 | -0.0285771 | false | 0.0486827 | 0.0361721 | 825 | undefined | undefined | evaluated | -0.000111086 | 0.334607 |
| ALPHA_053 | evaluated | 60 | 0.0138754 | 0.312374 | 1 | 1 | -0.000918185 | 0.0286689 | false | 0.0517868 | 0.0384785 | 172 | undefined | undefined | evaluated | 7.04249e-05 | 0.499937 |
| ALPHA_054 | evaluated | 60 | -0.00487125 | 0.778913 | 1 | 1 | -0.0192807 | 0.00953818 | false | 0.0654254 | 0.0486123 | 0 | undefined | undefined | evaluated | -1.42032e-05 | 0.898635 |
| ALPHA_055 | evaluated | 60 | -0.00651672 | 0.390276 | 1 | 1 | -0.00364169 | -0.00939175 | false | 0.028601 | 0.0212511 | 152 | undefined | undefined | evaluated | -0.000124493 | 0.043453 |
| ALPHA_060 | evaluated | 60 | 0.0071289 | 0.671574 | 1 | 1 | -0.0182985 | 0.0325563 | false | 0.0633975 | 0.0471055 | 50 | undefined | undefined | evaluated | 0.000113152 | 0.380079 |
| ALPHA_101 | evaluated | 60 | -0.000831095 | 0.965717 | 1 | 1 | 0.00605991 | -0.0077221 | false | 0.0729098 | 0.0541733 | 0 | undefined | undefined | evaluated | -4.73289e-05 | 0.715784 |
| EQUAL_WEIGHTED_COMPOSITE | evaluated | 60 | -0.00987149 | 0.525504 | 1 | 1 | -0.015165 | -0.00457794 | false | 0.0586263 | 0.0435604 | 0 | undefined | undefined | evaluated | -5.17225e-05 | 0.698225 |
| IC_WEIGHTED_COMPOSITE | evaluated | 58 | -0.0182366 | 0.229733 | 1 | 1 | -0.0393431 | 0.00286979 | false | 0.0572518 | 0.0425391 | 849 | undefined | undefined | evaluated | -0.000203113 | 0.0776814 |
| ICIR_WEIGHTED_COMPOSITE | evaluated | 54 | -0.014325 | 0.365709 | 1 | 1 | -0.0292446 | 0.00059468 | false | 0.0597132 | 0.044368 | 2549 | undefined | undefined | evaluated | -0.00021065 | 0.0387886 |
| CORRELATION_DISCOUNTED_COMPOSITE | evaluated | 58 | -0.0111446 | 0.339902 | 1 | 1 | -0.0328623 | 0.010573 | false | 0.0440309 | 0.0327158 | 849 | undefined | undefined | evaluated | -0.000153792 | 0.0809467 |
| ALPHA_PRODUCT_INTERACTION | evaluated | 60 | -0.0120789 | 0.125173 | 1 | 1 | -0.0127635 | -0.0113943 | false | 0.029701 | 0.0220684 | 64 | undefined | undefined | evaluated | -0.000110213 | 0.0722756 |
| CONDITIONAL_RANK_INTERACTION | evaluated | 60 | -0.0139489 | 0.230023 | 1 | 1 | -0.0159969 | -0.0119009 | false | 0.0438183 | 0.0325578 | 64 | undefined | undefined | evaluated | -8.93671e-05 | 0.306596 |
| NEUTRALIZED_IC_COMPOSITE | evaluated | 58 | -0.0103973 | 0.460968 | 1 | 1 | -0.0297551 | 0.00896057 | false | 0.053175 | 0.03951 | 855 | undefined | undefined | evaluated | -0.000151364 | 0.153257 |
| MARKET_BETA_NEUTRAL_COMPOSITE | evaluated | 58 | -0.00579838 | 0.64486 | 1 | 1 | -0.0232551 | 0.0116583 | false | 0.0474341 | 0.0352444 | 909 | undefined | undefined | evaluated | -0.000142711 | 0.162125 |
| REGIME_SWITCHING_COMPOSITE | evaluated | 58 | -0.0115353 | 0.406128 | 1 | 1 | -0.0324569 | 0.00938639 | false | 0.0523569 | 0.0389021 | 867 | undefined | undefined | evaluated | -0.000183714 | 0.103562 |
| RANDOM_FOREST_COMPOSITE | evaluated | 54 | 0.00855664 | 0.496507 | 1 | 1 | 0.0119608 | 0.00515252 | true | 0.0474462 | 0.0352534 | 9300 | undefined | undefined | evaluated | -7.03166e-05 | 0.426277 |
| GRADIENT_BOOSTING_COMPOSITE | evaluated | 54 | -0.010958 | 0.40408 | 1 | 1 | -0.0163017 | -0.00561422 | false | 0.0495203 | 0.0367945 | 9300 | undefined | undefined | evaluated | -0.000149557 | 0.120425 |

## Family A books

| Factor | Book | Cost case | Status | Mean daily net | HAC p | Turnover | Costs | Max drawdown | Within DD budget | Excess vs SPY | Excess vs EW | Tracking error | IR | IR within | TE within | Halves | Half 1 mean net | Half 2 mean net |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| MOM_12_1 | long_short | primary | evaluated | 0.000175756 | 0.402787 | 38.1242 | 0.0190678 | 0.176942 | true | undefined | undefined | undefined | undefined | undefined | undefined | evaluated | 6.61543e-05 | 0.000288406 |
| MOM_12_1 | long_only | primary | evaluated | 0.000744328 | 0.0514719 | 37.5892 | 0.0188004 | 0.227872 | true | 0.364799 | 0.634159 | 0.142322 | 0.349827 | true | false | evaluated | 0.000450508 | 0.00104632 |
| MOM_12_1 | long_short | sensitivity_2x | evaluated | 0.000160366 | 0.445509 | 38.1242 | 0.0381356 | 0.180777 | true | undefined | undefined | undefined | undefined | undefined | undefined | evaluated | 4.99074e-05 | 0.000273898 |
| MOM_12_1 | long_only | sensitivity_2x | evaluated | 0.000729154 | 0.0564143 | 37.5892 | 0.0376009 | 0.228512 | true | 0.323923 | 0.593283 | 0.142345 | 0.322908 | true | false | evaluated | 0.000434966 | 0.00103153 |
| MOM_12_1 | long_short | zero_cost_diagnostic_only | evaluated | 0.000191145 | 0.362601 | 38.1242 | 0 | 0.174452 | true | undefined | undefined | undefined | undefined | undefined | undefined | evaluated | 8.24013e-05 | 0.000302915 |
| MOM_12_1 | long_only | zero_cost_diagnostic_only | evaluated | 0.000759502 | 0.0469014 | 37.5892 | 0 | 0.227232 | true | 0.406437 | 0.675797 | 0.142307 | 0.376733 | true | false | evaluated | 0.00046605 | 0.00106112 |
| HIGH_52W | long_short | primary | evaluated | 3.29731e-05 | 0.877417 | 59.9712 | 0.0299975 | 0.184816 | true | undefined | undefined | undefined | undefined | undefined | undefined | evaluated | -2.01992e-05 | 8.76247e-05 |
| HIGH_52W | long_only | primary | evaluated | 0.000391409 | 0.117294 | 82.3453 | 0.0411943 | 0.229824 | true | -0.286548 | -0.0171881 | 0.12592 | -0.310891 | false | false | evaluated | 0.000115674 | 0.000674816 |
| HIGH_52W | long_short | sensitivity_2x | evaluated | 8.76204e-06 | 0.967316 | 59.9712 | 0.0599949 | 0.192099 | true | undefined | undefined | undefined | undefined | undefined | undefined | evaluated | -4.37416e-05 | 6.27265e-05 |
| HIGH_52W | long_only | sensitivity_2x | evaluated | 0.000358161 | 0.151452 | 82.3453 | 0.0823885 | 0.238106 | true | -0.34885 | -0.079491 | 0.125977 | -0.377258 | false | false | evaluated | 8.42444e-05 | 0.0006397 |
| HIGH_52W | long_short | zero_cost_diagnostic_only | evaluated | 5.71841e-05 | 0.789047 | 59.9712 | 0 | 0.17747 | true | undefined | undefined | undefined | undefined | undefined | undefined | evaluated | 3.34331e-06 | 0.000112523 |
| HIGH_52W | long_only | zero_cost_diagnostic_only | evaluated | 0.000424657 | 0.0896069 | 82.3453 | 0 | 0.221458 | true | -0.22167 | 0.0476894 | 0.125907 | -0.244377 | false | false | evaluated | 0.000147104 | 0.000709933 |
| REV_1M | long_short | primary | evaluated | -0.000194395 | 0.273938 | 104.545 | 0.0522881 | 0.365092 | false | undefined | undefined | undefined | undefined | undefined | undefined | evaluated | 2.30223e-05 | -0.000417861 |
| REV_1M | long_only | primary | evaluated | 0.000228903 | 0.56513 | 103.712 | 0.0518875 | 0.27435 | true | -0.674073 | -0.404713 | 0.13773 | -0.581566 | false | false | evaluated | 0.00021725 | 0.00024088 |
| REV_1M | long_short | sensitivity_2x | evaluated | -0.000236597 | 0.184301 | 104.545 | 0.104576 | 0.389357 | false | undefined | undefined | undefined | undefined | undefined | undefined | evaluated | -1.98622e-05 | -0.000459362 |
| REV_1M | long_only | sensitivity_2x | evaluated | 0.000187024 | 0.638364 | 103.712 | 0.103775 | 0.281129 | true | -0.732536 | -0.463177 | 0.137801 | -0.657849 | false | false | evaluated | 0.000174911 | 0.000199474 |
| REV_1M | long_short | zero_cost_diagnostic_only | evaluated | -0.000152193 | 0.390598 | 104.545 | 0 | 0.339886 | false | undefined | undefined | undefined | undefined | undefined | undefined | evaluated | 6.59067e-05 | -0.000376361 |
| REV_1M | long_only | zero_cost_diagnostic_only | evaluated | 0.000270781 | 0.496245 | 103.712 | 0 | 0.268005 | true | -0.612548 | -0.343188 | 0.137721 | -0.504973 | false | false | evaluated | 0.000259588 | 0.000282286 |
| LOW_VOL_252 | long_short | primary | evaluated | -0.000239783 | 0.331114 | 16.4574 | 0.00822383 | 0.401881 | false | undefined | undefined | undefined | undefined | undefined | undefined | evaluated | -6.94618e-05 | -0.000414843 |
| LOW_VOL_252 | long_only | primary | evaluated | 0.000281892 | 0.195683 | 13.7631 | 0.00688458 | 0.163648 | true | -0.465626 | -0.196266 | 0.150802 | -0.442605 | false | false | evaluated | 0.000189978 | 0.000376363 |
| LOW_VOL_252 | long_short | sensitivity_2x | evaluated | -0.00024642 | 0.317965 | 16.4574 | 0.0164477 | 0.405477 | false | undefined | undefined | undefined | undefined | undefined | undefined | evaluated | -7.61469e-05 | -0.000421431 |
| LOW_VOL_252 | long_only | sensitivity_2x | evaluated | 0.000276336 | 0.204572 | 13.7631 | 0.0137692 | 0.164035 | true | -0.474981 | -0.205622 | 0.150802 | -0.451889 | false | false | evaluated | 0.000184406 | 0.000370823 |
| LOW_VOL_252 | long_short | zero_cost_diagnostic_only | evaluated | -0.000233145 | 0.344619 | 16.4574 | 0 | 0.398264 | false | undefined | undefined | undefined | undefined | undefined | undefined | evaluated | -6.27767e-05 | -0.000408254 |
| LOW_VOL_252 | long_only | zero_cost_diagnostic_only | evaluated | 0.000287449 | 0.187087 | 13.7631 | 0 | 0.163261 | true | -0.456207 | -0.186848 | 0.150803 | -0.433317 | false | false | evaluated | 0.000195551 | 0.000381903 |
| LOW_BETA_252 | long_short | primary | evaluated | -0.000206765 | 0.462934 | 17.6888 | 0.00883264 | 0.448914 | false | undefined | undefined | undefined | undefined | undefined | undefined | evaluated | -1.38733e-05 | -0.000405023 |
| LOW_BETA_252 | long_only | primary | evaluated | 0.000319521 | 0.141397 | 14.0679 | 0.00704056 | 0.157412 | true | -0.402886 | -0.133526 | 0.175487 | -0.326309 | false | false | evaluated | 0.000213652 | 0.000428336 |
| LOW_BETA_252 | long_short | sensitivity_2x | evaluated | -0.000213893 | 0.447687 | 17.6888 | 0.0176653 | 0.452448 | false | undefined | undefined | undefined | undefined | undefined | undefined | evaluated | -2.13098e-05 | -0.000411835 |
| LOW_BETA_252 | long_only | sensitivity_2x | evaluated | 0.000313839 | 0.148507 | 14.0679 | 0.0140811 | 0.157722 | true | -0.412888 | -0.143528 | 0.175492 | -0.33446 | false | false | evaluated | 0.000208026 | 0.000422595 |
| LOW_BETA_252 | long_short | zero_cost_diagnostic_only | evaluated | -0.000199636 | 0.478473 | 17.6888 | 0 | 0.445357 | false | undefined | undefined | undefined | undefined | undefined | undefined | evaluated | -6.43676e-06 | -0.00039821 |
| LOW_BETA_252 | long_only | zero_cost_diagnostic_only | evaluated | 0.000325203 | 0.134561 | 14.0679 | 0 | 0.157101 | true | -0.392814 | -0.123455 | 0.175484 | -0.318156 | false | false | evaluated | 0.000219277 | 0.000434077 |
| AMIHUD_ILLIQ_63 | long_short | primary | evaluated | -0.000113429 | 0.324737 | 16.5695 | 0.00827894 | 0.226022 | true | undefined | undefined | undefined | undefined | undefined | undefined | evaluated | -0.000135449 | -9.07956e-05 |
| AMIHUD_ILLIQ_63 | long_only | primary | evaluated | 0.000387976 | 0.26416 | 19.3319 | 0.00966322 | 0.256824 | true | -0.372223 | -0.102864 | 0.12282 | -0.325782 | false | false | evaluated | 0.000164725 | 0.000617437 |
| AMIHUD_ILLIQ_63 | long_short | sensitivity_2x | evaluated | -0.000120111 | 0.296986 | 16.5695 | 0.0165579 | 0.230054 | true | undefined | undefined | undefined | undefined | undefined | undefined | evaluated | -0.000142358 | -9.7245e-05 |
| AMIHUD_ILLIQ_63 | long_only | sensitivity_2x | evaluated | 0.000380176 | 0.273851 | 19.3319 | 0.0193264 | 0.258055 | true | -0.386245 | -0.116886 | 0.122833 | -0.341748 | false | false | evaluated | 0.000156668 | 0.000609904 |
| AMIHUD_ILLIQ_63 | long_short | zero_cost_diagnostic_only | evaluated | -0.000106747 | 0.354137 | 16.5695 | 0 | 0.221969 | true | undefined | undefined | undefined | undefined | undefined | undefined | evaluated | -0.000128541 | -8.43463e-05 |
| AMIHUD_ILLIQ_63 | long_only | zero_cost_diagnostic_only | evaluated | 0.000395775 | 0.254714 | 19.3319 | 0 | 0.25559 | true | -0.358068 | -0.0887082 | 0.12281 | -0.309806 | false | false | evaluated | 0.000172783 | 0.000624971 |

- The zero-cost case is diagnostic only (R8). Family B books by status: {'evaluated': 126}

## Benchmarks

- Equal-weight PIT benchmark: status `evaluated`, mean daily net 0.000413946, excess total return over SPY -0.269359
- SPY.US#E1: status `evaluated`, mean daily return 0.000546756

## CPCV and PBO families

| Family | Status | Reason | PBO | Completed columns | Failed columns omitted | Holding periods |
| --- | --- | --- | --- | --- | --- | --- |
| A_long_short | available | undefined | 0.214286 | 6 | 0 | 23 |
| A_excess | available | undefined | 0.171429 | 6 | 0 | 23 |
| B_long_short | available | undefined | 0.457143 | 63 | 0 | 23 |
| B_excess | available | undefined | 0.342857 | 63 | 0 | 23 |

## Deflated Sharpe (long-short, primary costs)

- Family A: n_trials 6, trial Sharpe variance 0.000424059; values MOM_12_1 0.41679, HIGH_52W 0.212877, REV_1M 0.0236624, LOW_VOL_252 0.0309032, LOW_BETA_252 0.0530704, AMIHUD_ILLIQ_63 0.0302735
- Family B: n_trials 63, trial Sharpe variance 0.00071355; values ALPHA_001 0.001005, ALPHA_002 0.0300522, ALPHA_003 0.000407695, ALPHA_004 0.000555111, ALPHA_005 0.00140767, ALPHA_006 0.000812857, ALPHA_007 0.00170759, ALPHA_008 0.0130343, ALPHA_009 0.0368777, ALPHA_010 0.0497689, ALPHA_012 0.00201079, ALPHA_013 0.0010983, ALPHA_014 0.000648473, ALPHA_015 4.43644e-08, ALPHA_016 0.000431824, ALPHA_017 0.000169341, ALPHA_018 0.100801, ALPHA_019 0.00426335, ALPHA_020 5.49798e-05, ALPHA_021 0.000237513, ALPHA_022 0.000444832, ALPHA_023 0.0222284, ALPHA_024 0.0562672, ALPHA_025 0.00852501, ALPHA_026 0.00449598, ALPHA_028 0.092959, ALPHA_030 0.0127663, ALPHA_031 0.004031, ALPHA_032 0.00281401, ALPHA_033 0.0370778, ALPHA_034 0.0196503, ALPHA_035 0.000756616, ALPHA_036 0.0187557, ALPHA_037 0.0840033, ALPHA_038 0.00328116, ALPHA_039 0.000162118, ALPHA_040 0.000188729, ALPHA_041 0.157289, ALPHA_042 0.248234, ALPHA_043 0.000424241, ALPHA_044 0.000200769, ALPHA_045 0.124456, ALPHA_046 0.0229271, ALPHA_049 0.0206888, ALPHA_050 0.00126885, ALPHA_051 0.0035224, ALPHA_052 0.00094515, ALPHA_053 0.054746, ALPHA_054 0.00944447, ALPHA_055 1.40145e-05, ALPHA_060 0.0861813, ALPHA_101 0.00507618, EQUAL_WEIGHTED_COMPOSITE 0.00459539, IC_WEIGHTED_COMPOSITE 2.3952e-05, ICIR_WEIGHTED_COMPOSITE 6.2002e-06, CORRELATION_DISCOUNTED_COMPOSITE 6.16615e-05, ALPHA_PRODUCT_INTERACTION 4.15455e-05, CONDITIONAL_RANK_INTERACTION 0.000817498, NEUTRALIZED_IC_COMPOSITE 0.000109967, MARKET_BETA_NEUTRAL_COMPOSITE 0.000159379, REGIME_SWITCHING_COMPOSITE 4.95904e-05, RANDOM_FOREST_COMPOSITE 0.00176873, GRADIENT_BOOSTING_COMPOSITE 0.000126803
- IID Sharpe haircuts (BY, disclosed as IID) are in the sidecar.

## Decision gate

- Outcome: `extend_first`
- Program decision: Extend breadth or history under a new registration; the holdout stays sealed
- contrary_rejections: []
- power_status: `inadequate`
- kill_reachable_projection: false
- family_b_context: {'positive_by_rejections': 0, 'role': 'exploratory; changes no decision'}
- owner_decision_o3: `proceed_as_registered`

## Limitations

- Borrow cost is absent from the long-short engine; the constant spread understates costs before 2001.
- Terminal rows pay a cost for holdings that are never measured, which is conservative for the strategy.
- Family B carries no primary claim; short-horizon price-volume alphas lie outside the edge thesis.
- Each of the 27 support-excluded cells conditions on its own asset's bar availability over one holding period (a disappearance or a halt that has not yet happened at the signal row); IC pairs, books, and the equal-weight benchmark omit those cells alike, and signal inputs never read them.

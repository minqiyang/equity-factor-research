# M4.7 S&P 500 PIT Rerun

Evidence ceiling: `DIAGNOSTIC_ONLY`. No figure below supports a ranking, selection, promotion, or profitability claim; `formal_universe_evidence_eligible` and `formal_terminal_evidence_eligible` are false.

- Run status: `completed`
- Registration SHA-256: `6ea218a638dd2cba760ea22ebd4009bb184d4137233762f72a844454a10f1c9f`
- Code commit: `0d87d7ebd5d5de2bf42f264eb2e29d127c4cc64d`
- Snapshot: `real_v1`; manifest SHA-256 `ffa760532bc553a0f290c1bb04d4b1c0bd60163e6df70571737d6df3cc9335c7`
- segments_sha256: `6b014b13a9f5017e0f5d0b383079f16b5d2915a24fe9a8862fa14e88a8ba5933`; census JSON SHA-256 `608fd1b1dd633e8985ea07537f6a944777cb38d684e86e7c75ada11ddc2d1c40`
- Discovery window: holdout end `2020-07-31`, D0 `2021-08-31`, D_last `2026-08-07`, D_end `2026-06-30`
- Prior-exposure overlap fractions: historical_evaluation 0.0625, static_50_name_cohort 1
- |U| = 24, |G| = 1, |W| = 20; excluded rows 476, excluded fraction 0.384181
- Eligible unpriced member-day fraction: 0.329698
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
- window_splitting_contract: common_support_segments_open_terminal_holdings_v3
- initialization_anchor_policy: zero_return_zero_trade_all_cash_excluded_from_statistics
- terminal_row_policy: include_return_trade_cost_open_holdings_no_future_return
- segment_count: 10
- segment_terminal_reset_months: ['2021-12', '2022-06', '2022-10', '2023-03', '2023-10', '2024-05', '2024-11', '2025-05', '2025-11', '2026-08']
- terminal_reset_cells: 0
- excluded_rows: 476
- excluded_fraction: 0.384181
- settlement_lag_distribution: {}
- cash_availability_idealization_rows_max: 3
- consideration_valuation_rule: acquirer_close_at_completion_date_row_v1
- settlement_contract: prior_observed_close_to_consideration_at_completion_date_row_v2
- costs: {'primary': {'slippage_bps': 4.0, 'transaction_cost_bps': 1.0}, 'sensitivity_2x': {'slippage_bps': 8.0, 'transaction_cost_bps': 2.0}, 'zero_cost_diagnostic_only': {'slippage_bps': 0.0, 'transaction_cost_bps': 0.0}}
- impact_model: none
- borrow_cost: absent_from_the_long_short_engine
- first_discovery_date: 2021-08-31
- market_beta_neutral_composite_market: equal_weight_market_of_eligible_names
- cpcv_boundary_conservatism: segment concatenation purges labels that cannot overlap in calendar time
- engine_frame_columns: member_permanent_ids_only
- member_columns: 558

## Segments and gap windows (month granularity)

| Start month | End month | Reason types | Peeled rows |
| --- | --- | --- | --- |
| 2021-12 | 2021-12 | unresolved_delisting | 0 |
| 2022-02 | 2022-03 | unresolved_delisting | 0 |
| 2022-06 | 2022-06 | unresolved_delisting | 0 |
| 2022-10 | 2022-10 | unresolved_delisting | 0 |
| 2022-12 | 2022-12 | unresolved_delisting | 0 |
| 2023-03 | 2023-03 | unresolved_delisting | 0 |
| 2023-04 | 2023-04 | missing_bar | 0 |
| 2023-05 | 2023-05 | unresolved_delisting | 0 |
| 2023-10 | 2023-10 | unresolved_delisting | 0 |
| 2024-05 | 2024-05 | unresolved_delisting | 0 |
| 2024-11 | 2024-11 | unresolved_delisting | 0 |
| 2024-12 | 2024-12 | unresolved_delisting | 0 |
| 2025-05 | 2025-05 | unresolved_delisting | 0 |
| 2025-07 | 2025-07 | unresolved_delisting | 0 |
| 2025-08 | 2025-09 | unresolved_delisting | 0 |
| 2025-11 | 2025-12 | unresolved_delisting | 0 |
| 2026-02 | 2026-02 | unresolved_delisting | 0 |
| 2026-04 | 2026-04 | unresolved_delisting | 0 |
| 2026-05 | 2026-05 | unresolved_delisting | 0 |
| 2026-08 | 2026-08 | unresolved_delisting | 0 |

## Labels and IC months

- ic_month_supply: 32
- ic_months_in_gap: 3
- ic_months_in_dropped_segment: 16
- ic_months_horizon_unmeasured: 10
- terminal_aware_labels: 0
- missing_execution_bar: 0
- missing_horizon_end_bar: 0

## Family A primary tests (monthly Rank IC, BY within family of 6)

| Factor | Status | T_f | Mean IC | HAC p | BY q | Union BY q | Half 1 mean | Half 2 mean | Sign stable | MDE_f | MDE_single | Coverage loss | Estimate | Beyond estimate | LS status | LS mean net | LS HAC p |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| MOM_12_1 | evaluated | 32 | 0.0134593 | 0.566874 | 1 | 1 | -0.0157928 | 0.0427115 | false | 0.0886197 | 0.065846 | 38 | 38 | 0 | evaluated | -1.20221e-05 | 0.9642 |
| HIGH_52W | evaluated | 32 | -0.010275 | 0.706731 | 1 | 1 | -0.0560976 | 0.0355475 | false | 0.10297 | 0.0765086 | 47 | 37 | 10 | evaluated | -0.000177401 | 0.497036 |
| REV_1M | evaluated | 32 | 0.0279309 | 0.144407 | 1 | 1 | 0.0310982 | 0.0247637 | true | 0.0721545 | 0.0536121 | 1 | 1 | 0 | evaluated | 1.0065e-05 | 0.962834 |
| LOW_VOL_252 | evaluated | 32 | -0.010835 | 0.774981 | 1 | 1 | -0.0906195 | 0.0689496 | false | 0.142912 | 0.106186 | 48 | 38 | 10 | evaluated | -0.000164572 | 0.591778 |
| LOW_BETA_252 | evaluated | 32 | -0.0167488 | 0.711196 | 1 | 1 | -0.10196 | 0.0684624 | false | 0.170566 | 0.126734 | 48 | 38 | 10 | evaluated | -0.000136609 | 0.708933 |
| AMIHUD_ILLIQ_63 | evaluated | 32 | -0.00851259 | 0.607242 | 1 | 1 | 0.018212 | -0.0352372 | false | 0.062444 | 0.046397 | 9 | 7 | 2 | evaluated | -6.31393e-06 | 0.966123 |

## Family B primary tests (monthly Rank IC, BY within family of 63)

| Factor | Status | T_f | Mean IC | HAC p | BY q | Union BY q | Half 1 mean | Half 2 mean | Sign stable | MDE_f | MDE_single | Coverage loss | Estimate | Beyond estimate | LS status | LS mean net | LS HAC p |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ALPHA_001 | evaluated | 32 | -0.0212659 | 0.220717 | 1 | 1 | -0.00288023 | -0.0396516 | false | 0.0654764 | 0.0486502 | 39 | undefined | undefined | evaluated | -0.000159851 | 0.13282 |
| ALPHA_002 | evaluated | 32 | 0.0139627 | 0.0610095 | 1 | 1 | 0.00355784 | 0.0243675 | true | 0.0281019 | 0.0208802 | 20 | undefined | undefined | evaluated | -3.15056e-06 | 0.971534 |
| ALPHA_003 | evaluated | 32 | -0.0130879 | 0.240447 | 1 | 1 | -0.0228554 | -0.00332036 | false | 0.042039 | 0.0312358 | 137 | undefined | undefined | evaluated | -7.86142e-05 | 0.265666 |
| ALPHA_004 | evaluated | 32 | -0.00604909 | 0.727826 | 1 | 1 | -0.0132408 | 0.00114267 | false | 0.0655378 | 0.0486958 | 29 | undefined | undefined | evaluated | -0.000238405 | 0.0950654 |
| ALPHA_005 | evaluated | 32 | 0.0111752 | 0.56831 | 1 | 1 | 0.0153987 | 0.00695172 | true | 0.0738539 | 0.0548748 | 31 | undefined | undefined | evaluated | 3.03821e-05 | 0.833632 |
| ALPHA_006 | evaluated | 32 | -0.0167786 | 0.399703 | 1 | 1 | -0.0462669 | 0.0127098 | false | 0.0751223 | 0.0558173 | 31 | undefined | undefined | evaluated | -6.00045e-05 | 0.576693 |
| ALPHA_007 | evaluated | 32 | 0.00372411 | 0.729404 | 1 | 1 | 0.0112531 | -0.00380492 | false | 0.0405932 | 0.0301615 | 66 | undefined | undefined | evaluated | -8.81204e-05 | 0.331563 |
| ALPHA_008 | evaluated | 32 | -0.00868091 | 0.581332 | 1 | 1 | -0.0121397 | -0.00522213 | false | 0.0593569 | 0.0441032 | 31 | undefined | undefined | evaluated | -0.000194762 | 0.236275 |
| ALPHA_009 | evaluated | 32 | 0.0042232 | 0.849195 | 1 | 1 | -0.00992593 | 0.0183723 | false | 0.083745 | 0.0622241 | 14 | undefined | undefined | evaluated | 5.40201e-06 | 0.971265 |
| ALPHA_010 | evaluated | 32 | -0.00762281 | 0.708084 | 1 | 1 | -0.017234 | 0.00198835 | false | 0.0767624 | 0.0570358 | 5 | undefined | undefined | evaluated | -3.35818e-05 | 0.808963 |
| ALPHA_012 | evaluated | 32 | -0.0129579 | 0.257695 | 1 | 1 | -0.0140298 | -0.0118861 | false | 0.0431667 | 0.0320736 | 2 | undefined | undefined | evaluated | -0.00015943 | 0.0883405 |
| ALPHA_013 | evaluated | 32 | -0.0131333 | 0.0702181 | 1 | 1 | -0.024608 | -0.00165866 | false | 0.0273515 | 0.0203227 | 5 | undefined | undefined | evaluated | -7.05761e-05 | 0.397553 |
| ALPHA_014 | evaluated | 32 | -0.024944 | 0.179204 | 1 | 1 | -0.0477957 | -0.00209242 | false | 0.0700208 | 0.0520267 | 31 | undefined | undefined | evaluated | -0.000137858 | 0.196294 |
| ALPHA_015 | evaluated | 32 | -0.00656684 | 0.416638 | 1 | 1 | -0.0221078 | 0.00897408 | false | 0.0304832 | 0.0226496 | 2522 | undefined | undefined | evaluated | -0.000175698 | 0.0280288 |
| ALPHA_016 | evaluated | 32 | -0.00938827 | 0.257712 | 1 | 1 | -0.024837 | 0.00606045 | false | 0.0312762 | 0.0232388 | 5 | undefined | undefined | evaluated | -8.55205e-05 | 0.274413 |
| ALPHA_017 | evaluated | 32 | -0.00806427 | 0.692734 | 1 | 1 | -0.00286133 | -0.0132672 | false | 0.0769503 | 0.0571755 | 42 | undefined | undefined | evaluated | -0.000103401 | 0.45211 |
| ALPHA_018 | evaluated | 32 | 0.0139833 | 0.5248 | 1 | 1 | 0.000930132 | 0.0270366 | true | 0.0829055 | 0.0616003 | 31 | undefined | undefined | evaluated | 5.91744e-05 | 0.709116 |
| ALPHA_019 | evaluated | 32 | 0.00294315 | 0.91671 | 1 | 1 | 0.0398848 | -0.0339985 | false | 0.106114 | 0.0788445 | 450 | undefined | undefined | evaluated | -6.72347e-05 | 0.666731 |
| ALPHA_020 | evaluated | 32 | -0.0160655 | 0.577598 | 1 | 1 | -0.0581048 | 0.0259739 | false | 0.108773 | 0.0808207 | 2 | undefined | undefined | evaluated | -8.84393e-05 | 0.591924 |
| ALPHA_021 | evaluated | 32 | 0.00592772 | 0.55471 | 1 | 1 | 0.00369615 | 0.00815929 | true | 0.0378366 | 0.0281133 | 37 | undefined | undefined | evaluated | -8.44218e-05 | 0.376137 |
| ALPHA_022 | evaluated | 32 | -0.0280851 | 0.0248295 | 1 | 1 | -0.0233461 | -0.0328241 | false | 0.0471899 | 0.0350629 | 37 | undefined | undefined | evaluated | -0.000138108 | 0.214374 |
| ALPHA_023 | evaluated | 32 | 0.00140136 | 0.937417 | 1 | 1 | -0.000113699 | 0.00291641 | false | 0.0672967 | 0.0500027 | 37 | undefined | undefined | evaluated | 6.1133e-05 | 0.654043 |
| ALPHA_024 | evaluated | 32 | 0.0403701 | 0.00534078 | 1 | 1 | 0.0344537 | 0.0462865 | true | 0.0546419 | 0.0405999 | 369 | undefined | undefined | evaluated | 7.15896e-05 | 0.613374 |
| ALPHA_025 | evaluated | 32 | 0.0059024 | 0.81078 | 1 | 1 | -0.0203393 | 0.0321441 | false | 0.092955 | 0.0690673 | 37 | undefined | undefined | evaluated | -2.57469e-05 | 0.888216 |
| ALPHA_026 | evaluated | 32 | -0.00367134 | 0.827555 | 1 | 1 | 0.0208141 | -0.0281568 | false | 0.0635469 | 0.0472165 | 1174 | undefined | undefined | evaluated | -0.000119006 | 0.270751 |
| ALPHA_028 | evaluated | 32 | 0.0209405 | 0.245934 | 1 | 1 | 0.0046176 | 0.0372634 | true | 0.06805 | 0.0505624 | 42 | undefined | undefined | evaluated | 0.000173772 | 0.248736 |
| ALPHA_030 | evaluated | 32 | 0.0225334 | 0.171312 | 1 | 1 | 0.0109718 | 0.0340951 | true | 0.0621077 | 0.0461472 | 37 | undefined | undefined | evaluated | 7.87746e-05 | 0.561033 |
| ALPHA_031 | evaluated | 32 | 0.0313103 | 0.124406 | 1 | 1 | 0.0350951 | 0.0275255 | true | 0.0768331 | 0.0570884 | 60 | undefined | undefined | evaluated | 2.05874e-05 | 0.888771 |
| ALPHA_032 | evaluated | 32 | 0.0166731 | 0.472541 | 1 | 1 | 0.0111689 | 0.0221772 | true | 0.087515 | 0.0650252 | 418 | undefined | undefined | evaluated | -4.41376e-05 | 0.767306 |
| ALPHA_033 | evaluated | 32 | -0.00446718 | 0.874259 | 1 | 1 | -0.0236584 | 0.014724 | false | 0.106437 | 0.0790844 | 0 | undefined | undefined | evaluated | -3.32739e-05 | 0.86569 |
| ALPHA_034 | evaluated | 32 | -0.00306746 | 0.889704 | 1 | 1 | -0.0349392 | 0.0288043 | false | 0.0834013 | 0.0619687 | 5 | undefined | undefined | evaluated | 2.32472e-05 | 0.873378 |
| ALPHA_035 | evaluated | 32 | -0.00656765 | 0.742491 | 1 | 1 | -0.0165193 | 0.00338401 | false | 0.0753711 | 0.0560021 | 63 | undefined | undefined | evaluated | -0.000124348 | 0.404175 |
| ALPHA_036 | evaluated | 32 | 0.00609535 | 0.70189 | 1 | 1 | 0.0214989 | -0.00930817 | false | 0.0600434 | 0.0446133 | 369 | undefined | undefined | evaluated | -7.25621e-05 | 0.504072 |
| ALPHA_037 | evaluated | 32 | 0.0248896 | 0.212517 | 1 | 1 | 0.014914 | 0.0348652 | true | 0.0752782 | 0.0559331 | 370 | undefined | undefined | evaluated | 0.000183196 | 0.243805 |
| ALPHA_038 | evaluated | 32 | -0.00737097 | 0.771764 | 1 | 1 | -0.0150065 | 0.000264517 | false | 0.095814 | 0.0711916 | 31 | undefined | undefined | evaluated | -0.000156601 | 0.36926 |
| ALPHA_039 | evaluated | 32 | 0.00521514 | 0.830297 | 1 | 1 | 0.0281698 | -0.0177395 | false | 0.0917503 | 0.0681722 | 450 | undefined | undefined | evaluated | -0.000152694 | 0.330656 |
| ALPHA_040 | evaluated | 32 | -0.0198224 | 0.333167 | 1 | 1 | -0.0472599 | 0.00761514 | false | 0.0772317 | 0.0573846 | 31 | undefined | undefined | evaluated | -0.000133796 | 0.277835 |
| ALPHA_041 | evaluated | 32 | 0.0168537 | 0.482193 | 1 | 1 | 0.00110664 | 0.0326008 | true | 0.0904235 | 0.0671863 | 0 | undefined | undefined | evaluated | 0.000167247 | 0.287323 |
| ALPHA_042 | evaluated | 32 | 0.013994 | 0.406811 | 1 | 1 | 0.0115876 | 0.0164003 | true | 0.0636091 | 0.0472627 | 0 | undefined | undefined | evaluated | 6.60225e-05 | 0.685389 |
| ALPHA_043 | evaluated | 32 | -0.00404646 | 0.785997 | 1 | 1 | -0.0129782 | 0.00488529 | false | 0.0561941 | 0.0417533 | 68 | undefined | undefined | evaluated | -0.000185723 | 0.153437 |
| ALPHA_044 | evaluated | 32 | -0.0141065 | 0.120338 | 1 | 1 | -0.0160795 | -0.0121334 | false | 0.0342414 | 0.025442 | 54 | undefined | undefined | evaluated | -0.000100308 | 0.254597 |
| ALPHA_045 | evaluated | 32 | -0.00129968 | 0.90107 | 1 | 1 | -0.00282801 | 0.000228655 | false | 0.0394219 | 0.0292912 | 103 | undefined | undefined | evaluated | 6.24522e-05 | 0.453138 |
| ALPHA_046 | evaluated | 32 | 0.000908862 | 0.951193 | 1 | 1 | 0.0175522 | -0.0157345 | false | 0.0559873 | 0.0415996 | 38 | undefined | undefined | evaluated | -1.34733e-05 | 0.88449 |
| ALPHA_049 | evaluated | 32 | -0.0140683 | 0.345228 | 1 | 1 | -0.0222927 | -0.00584402 | false | 0.0561989 | 0.0417568 | 31 | undefined | undefined | evaluated | 3.26937e-05 | 0.800038 |
| ALPHA_050 | evaluated | 32 | -0.0132794 | 0.222522 | 1 | 1 | -0.0306033 | 0.00404445 | false | 0.0410467 | 0.0304984 | 696 | undefined | undefined | evaluated | -6.26023e-05 | 0.408176 |
| ALPHA_051 | evaluated | 32 | -0.0158019 | 0.293561 | 1 | 1 | -0.0279832 | -0.00362058 | false | 0.0567261 | 0.0421485 | 38 | undefined | undefined | evaluated | -5.41775e-05 | 0.678223 |
| ALPHA_052 | evaluated | 32 | -0.0068587 | 0.775134 | 1 | 1 | 0.0322655 | -0.0459829 | false | 0.0905289 | 0.0672647 | 438 | undefined | undefined | evaluated | -0.00017283 | 0.222852 |
| ALPHA_053 | evaluated | 32 | 0.00158609 | 0.933604 | 1 | 1 | -0.0120396 | 0.0152118 | false | 0.0717838 | 0.0533367 | 105 | undefined | undefined | evaluated | -3.26948e-05 | 0.806392 |
| ALPHA_054 | evaluated | 32 | -0.00486176 | 0.834236 | 1 | 1 | -0.0139936 | 0.00427007 | false | 0.0875968 | 0.065086 | 0 | undefined | undefined | evaluated | -3.06225e-05 | 0.832188 |
| ALPHA_055 | evaluated | 32 | 0.00162867 | 0.83848 | 1 | 1 | 0.00707672 | -0.00381939 | false | 0.0301266 | 0.0223846 | 89 | undefined | undefined | evaluated | -0.000109587 | 0.161755 |
| ALPHA_060 | evaluated | 32 | -0.0119817 | 0.637209 | 1 | 1 | -0.0515631 | 0.0275996 | false | 0.0957958 | 0.071178 | 31 | undefined | undefined | evaluated | 1.93491e-05 | 0.912266 |
| ALPHA_101 | evaluated | 32 | 0.00279774 | 0.906158 | 1 | 1 | 0.00646493 | -0.000869453 | false | 0.0894848 | 0.0664889 | 0 | undefined | undefined | evaluated | 1.44947e-05 | 0.929014 |
| EQUAL_WEIGHTED_COMPOSITE | evaluated | 32 | -0.00331664 | 0.884652 | 1 | 1 | -0.020238 | 0.0136048 | false | 0.0862005 | 0.0640486 | 0 | undefined | undefined | evaluated | -6.9976e-05 | 0.65873 |
| IC_WEIGHTED_COMPOSITE | invalid_insufficient_ic_months | 30 | -0.0456192 | 0.0663557 | undefined | undefined | -0.0510919 | -0.0401464 | undefined | undefined | undefined | 849 | undefined | undefined | evaluated | -0.000319611 | 0.0210365 |
| ICIR_WEIGHTED_COMPOSITE | invalid_insufficient_ic_months | 27 | -0.0222838 | 0.233882 | undefined | undefined | -0.00153399 | -0.0446297 | undefined | undefined | undefined | 2129 | undefined | undefined | evaluated | -0.000283245 | 0.0159937 |
| CORRELATION_DISCOUNTED_COMPOSITE | invalid_insufficient_ic_months | 30 | -0.0173103 | 0.283016 | undefined | undefined | 0.00200878 | -0.0366293 | undefined | undefined | undefined | 849 | undefined | undefined | evaluated | -0.00016436 | 0.127287 |
| ALPHA_PRODUCT_INTERACTION | evaluated | 32 | -0.0120022 | 0.0723376 | 1 | 1 | -0.0149106 | -0.0090939 | false | 0.0251838 | 0.018712 | 37 | undefined | undefined | evaluated | -8.16461e-05 | 0.263704 |
| CONDITIONAL_RANK_INTERACTION | evaluated | 32 | -0.0245813 | 0.112785 | 1 | 1 | -0.0144515 | -0.0347112 | false | 0.0584469 | 0.0434271 | 37 | undefined | undefined | evaluated | -0.000143583 | 0.220679 |
| NEUTRALIZED_IC_COMPOSITE | invalid_insufficient_ic_months | 30 | -0.0335119 | 0.150459 | undefined | undefined | -0.0309717 | -0.0360521 | undefined | undefined | undefined | 853 | undefined | undefined | evaluated | -0.000204708 | 0.0820738 |
| MARKET_BETA_NEUTRAL_COMPOSITE | invalid_insufficient_ic_months | 30 | -0.0213669 | 0.194491 | undefined | undefined | -0.011057 | -0.0316768 | undefined | undefined | undefined | 883 | undefined | undefined | evaluated | -0.0002106 | 0.0559457 |
| REGIME_SWITCHING_COMPOSITE | invalid_insufficient_ic_months | 30 | -0.0245533 | 0.209174 | undefined | undefined | -0.00896014 | -0.0401464 | undefined | undefined | undefined | 856 | undefined | undefined | evaluated | -0.0001906 | 0.14214 |
| RANDOM_FOREST_COMPOSITE | invalid_insufficient_ic_months | 29 | -0.0275309 | 0.0744672 | undefined | undefined | -0.037816 | -0.0165112 | undefined | undefined | undefined | 4978 | undefined | undefined | evaluated | -5.38513e-05 | 0.651995 |
| GRADIENT_BOOSTING_COMPOSITE | invalid_insufficient_ic_months | 29 | -0.0379531 | 0.0712777 | undefined | undefined | -0.0471016 | -0.0281511 | undefined | undefined | undefined | 4978 | undefined | undefined | evaluated | -0.000163564 | 0.177831 |

## Family A books

| Factor | Book | Cost case | Status | Mean daily net | HAC p | Turnover | Costs | Max drawdown | Within DD budget | Excess vs SPY | Excess vs EW | Tracking error | IR | IR within | TE within | Halves | Half 1 mean net | Half 2 mean net |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| MOM_12_1 | long_short | primary | evaluated | -1.20221e-05 | 0.9642 | 33.8346 | 0.0169294 | 0.174645 | true | undefined | undefined | undefined | undefined | undefined | undefined | evaluated | -0.000218484 | 0.000184407 |
| MOM_12_1 | long_only | primary | evaluated | 0.000605528 | 0.208549 | 33.1133 | 0.0165454 | 0.227872 | true | 0.047499 | -0.00968663 | 0.144048 | 0.175116 | false | false | evaluated | 0.000531349 | 0.000676102 |
| MOM_12_1 | long_short | sensitivity_2x | evaluated | -3.42101e-05 | 0.898506 | 33.8346 | 0.0338588 | 0.174837 | true | undefined | undefined | undefined | undefined | undefined | undefined | evaluated | -0.000243001 | 0.000164435 |
| MOM_12_1 | long_only | sensitivity_2x | evaluated | 0.000583843 | 0.225287 | 33.1133 | 0.0330909 | 0.228512 | true | 0.0236661 | -0.0335196 | 0.14404 | 0.137188 | false | false | evaluated | 0.000508041 | 0.000655962 |
| MOM_12_1 | long_short | zero_cost_diagnostic_only | evaluated | 1.01659e-05 | 0.969688 | 33.8346 | 0 | 0.174452 | true | undefined | undefined | undefined | undefined | undefined | undefined | evaluated | -0.000193968 | 0.00020438 |
| MOM_12_1 | long_only | zero_cost_diagnostic_only | evaluated | 0.000627213 | 0.192752 | 33.1133 | 0 | 0.227232 | true | 0.0717213 | 0.0145356 | 0.144069 | 0.21302 | false | false | evaluated | 0.000554657 | 0.000696242 |
| HIGH_52W | long_short | primary | evaluated | -0.000177401 | 0.497036 | 49.2036 | 0.0246179 | 0.134585 | true | undefined | undefined | undefined | undefined | undefined | undefined | evaluated | -0.000373669 | 9.33102e-06 |
| HIGH_52W | long_only | primary | evaluated | 0.000384215 | 0.181048 | 63.6695 | 0.0318067 | 0.115931 | true | -0.102394 | -0.159579 | 0.121721 | -0.250949 | false | false | evaluated | 0.000122467 | 0.000633244 |
| HIGH_52W | long_short | sensitivity_2x | evaluated | -0.000209665 | 0.422829 | 49.2036 | 0.0492359 | 0.135512 | true | undefined | undefined | undefined | undefined | undefined | undefined | evaluated | -0.000406012 | -2.28598e-05 |
| HIGH_52W | long_only | sensitivity_2x | evaluated | 0.000342528 | 0.232932 | 63.6695 | 0.0636135 | 0.116693 | true | -0.143191 | -0.200377 | 0.121772 | -0.337111 | false | false | evaluated | 8.14477e-05 | 0.000590922 |
| HIGH_52W | long_short | zero_cost_diagnostic_only | evaluated | -0.000145136 | 0.57801 | 49.2036 | 0 | 0.133657 | true | undefined | undefined | undefined | undefined | undefined | undefined | evaluated | -0.000341327 | 4.15219e-05 |
| HIGH_52W | long_only | zero_cost_diagnostic_only | evaluated | 0.000425901 | 0.138451 | 63.6695 | 0 | 0.115169 | true | -0.0603037 | -0.117489 | 0.121724 | -0.164642 | false | false | evaluated | 0.000163486 | 0.000675565 |
| REV_1M | long_short | primary | evaluated | 1.0065e-05 | 0.962834 | 76.9108 | 0.0384582 | 0.115068 | true | undefined | undefined | undefined | undefined | undefined | undefined | evaluated | 0.000132765 | -0.000106673 |
| REV_1M | long_only | primary | evaluated | 0.000528629 | 0.290262 | 76.1393 | 0.038019 | 0.223556 | true | -0.0297386 | -0.0869242 | 0.141291 | 0.04138 | false | false | evaluated | 0.000667531 | 0.000396477 |
| REV_1M | long_short | sensitivity_2x | evaluated | -4.03389e-05 | 0.852719 | 76.9108 | 0.0769165 | 0.11796 | true | undefined | undefined | undefined | undefined | undefined | undefined | evaluated | 8.02429e-05 | -0.000155061 |
| REV_1M | long_only | sensitivity_2x | evaluated | 0.000478801 | 0.338461 | 76.1393 | 0.0760379 | 0.224849 | true | -0.0811005 | -0.138286 | 0.141407 | -0.0474527 | false | false | evaluated | 0.000615298 | 0.000348936 |
| REV_1M | long_short | zero_cost_diagnostic_only | evaluated | 6.0469e-05 | 0.778407 | 76.9108 | 0 | 0.112268 | true | undefined | undefined | undefined | undefined | undefined | undefined | evaluated | 0.000185288 | -5.82842e-05 |
| REV_1M | long_only | zero_cost_diagnostic_only | evaluated | 0.000578457 | 0.246931 | 76.1393 | 0 | 0.222262 | true | 0.0235761 | -0.0336095 | 0.14124 | 0.130299 | false | false | evaluated | 0.000719763 | 0.000444018 |
| LOW_VOL_252 | long_short | primary | evaluated | -0.000164572 | 0.591778 | 19.8804 | 0.00994135 | 0.132781 | true | undefined | undefined | undefined | undefined | undefined | undefined | evaluated | -0.000558091 | 0.000209825 |
| LOW_VOL_252 | long_only | primary | evaluated | 0.000279486 | 0.280331 | 18.2978 | 0.00914465 | 0.130478 | true | -0.194827 | -0.252013 | 0.155501 | -0.366155 | false | false | evaluated | -0.000122735 | 0.000662163 |
| LOW_VOL_252 | long_short | sensitivity_2x | evaluated | -0.000177601 | 0.563101 | 19.8804 | 0.0198827 | 0.132904 | true | undefined | undefined | undefined | undefined | undefined | undefined | evaluated | -0.0005724 | 0.000198013 |
| LOW_VOL_252 | long_only | sensitivity_2x | evaluated | 0.000267501 | 0.301392 | 18.2978 | 0.0182893 | 0.130606 | true | -0.205837 | -0.263023 | 0.155492 | -0.385599 | false | false | evaluated | -0.000135658 | 0.00065107 |
| LOW_VOL_252 | long_short | zero_cost_diagnostic_only | evaluated | -0.000151543 | 0.621177 | 19.8804 | 0 | 0.132657 | true | undefined | undefined | undefined | undefined | undefined | undefined | evaluated | -0.000543782 | 0.000221636 |
| LOW_VOL_252 | long_only | zero_cost_diagnostic_only | evaluated | 0.000291472 | 0.260335 | 18.2978 | 0 | 0.13035 | true | -0.18372 | -0.240905 | 0.155515 | -0.3467 | false | false | evaluated | -0.000109813 | 0.000673256 |
| LOW_BETA_252 | long_short | primary | evaluated | -0.000136609 | 0.708933 | 20.8098 | 0.0104029 | 0.171883 | true | undefined | undefined | undefined | undefined | undefined | undefined | evaluated | -0.000638665 | 0.000341052 |
| LOW_BETA_252 | long_only | primary | evaluated | 0.000295941 | 0.245223 | 18.1914 | 0.00909229 | 0.12563 | true | -0.180128 | -0.237314 | 0.183119 | -0.288287 | false | false | evaluated | -0.000213106 | 0.000780253 |
| LOW_BETA_252 | long_short | sensitivity_2x | evaluated | -0.000150243 | 0.681526 | 20.8098 | 0.0208057 | 0.172096 | true | undefined | undefined | undefined | undefined | undefined | undefined | evaluated | -0.000653396 | 0.000328461 |
| LOW_BETA_252 | long_only | sensitivity_2x | evaluated | 0.000284025 | 0.264448 | 18.1914 | 0.0181846 | 0.125724 | true | -0.191208 | -0.248393 | 0.183111 | -0.304698 | false | false | evaluated | -0.00022538 | 0.000768676 |
| LOW_BETA_252 | long_short | zero_cost_diagnostic_only | evaluated | -0.000122974 | 0.736756 | 20.8098 | 0 | 0.171669 | true | undefined | undefined | undefined | undefined | undefined | undefined | evaluated | -0.000623935 | 0.000353643 |
| LOW_BETA_252 | long_only | zero_cost_diagnostic_only | evaluated | 0.000307858 | 0.227059 | 18.1914 | 0 | 0.125536 | true | -0.168952 | -0.226137 | 0.183132 | -0.271869 | false | false | evaluated | -0.000200832 | 0.000791829 |
| AMIHUD_ILLIQ_63 | long_short | primary | evaluated | -6.31393e-06 | 0.966123 | 19.6977 | 0.00984469 | 0.0612079 | true | undefined | undefined | undefined | undefined | undefined | undefined | evaluated | 2.25296e-05 | -3.37558e-05 |
| AMIHUD_ILLIQ_63 | long_only | primary | evaluated | 0.000528863 | 0.228279 | 21.7071 | 0.0108407 | 0.186387 | true | 0.00229244 | -0.0548932 | 0.127434 | 0.0463424 | false | false | evaluated | 0.000456427 | 0.00059778 |
| AMIHUD_ILLIQ_63 | long_short | sensitivity_2x | evaluated | -1.92165e-05 | 0.89711 | 19.6977 | 0.0196894 | 0.0616779 | true | undefined | undefined | undefined | undefined | undefined | undefined | evaluated | 8.1987e-06 | -4.52996e-05 |
| AMIHUD_ILLIQ_63 | long_only | sensitivity_2x | evaluated | 0.000514655 | 0.240839 | 21.7071 | 0.0216814 | 0.18652 | true | -0.0128863 | -0.0700719 | 0.127442 | 0.0182451 | false | false | evaluated | 0.000440773 | 0.000584947 |
| AMIHUD_ILLIQ_63 | long_short | zero_cost_diagnostic_only | evaluated | 6.58868e-06 | 0.964673 | 19.6977 | 0 | 0.0607377 | true | undefined | undefined | undefined | undefined | undefined | undefined | evaluated | 3.68605e-05 | -2.22121e-05 |
| AMIHUD_ILLIQ_63 | long_only | zero_cost_diagnostic_only | evaluated | 0.000543071 | 0.216216 | 21.7071 | 0 | 0.186253 | true | 0.017632 | -0.0395536 | 0.127435 | 0.0744382 | false | false | evaluated | 0.000472081 | 0.000610612 |

- The zero-cost case is diagnostic only (R8). Family B books by status: {'evaluated': 126}

## Benchmarks

- Equal-weight PIT benchmark: status `evaluated`, mean daily net 0.000550308, excess total return over SPY 0.0571856
- SPY.US#E1: status `evaluated`, mean daily return 0.000505428

## CPCV and PBO families

| Family | Status | Reason | PBO | Completed columns | Failed columns omitted | Holding periods |
| --- | --- | --- | --- | --- | --- | --- |
| A_long_short | available | undefined | 0.628571 | 6 | 0 | 23 |
| A_excess | available | undefined | 0.585714 | 6 | 0 | 23 |
| B_long_short | available | undefined | 0.614286 | 63 | 0 | 23 |
| B_excess | available | undefined | 0.5 | 63 | 0 | 23 |

## Deflated Sharpe (long-short, primary costs)

- Family A: n_trials 6, trial Sharpe variance 0.000102253; values MOM_12_1 0.343959, HIGH_52W 0.158541, REV_1M 0.374143, LOW_VOL_252 0.196252, LOW_BETA_252 0.241473, AMIHUD_ILLIQ_63 0.343467
- Family B: n_trials 63, trial Sharpe variance 0.000799643; values ALPHA_001 0.00145038, ALPHA_002 0.0298929, ALPHA_003 0.00236712, ALPHA_004 0.000367088, ALPHA_005 0.0497114, ALPHA_006 0.00877487, ALPHA_007 0.0034511, ALPHA_008 0.00176137, ALPHA_009 0.0349281, ALPHA_010 0.0196478, ALPHA_012 0.000262445, ALPHA_013 0.0043523, ALPHA_014 0.000826591, ALPHA_015 3.39449e-05, ALPHA_016 0.00248065, ALPHA_017 0.00525319, ALPHA_018 0.0670663, ALPHA_019 0.0124376, ALPHA_020 0.00960035, ALPHA_021 0.00406907, ALPHA_022 0.00133917, ALPHA_023 0.0760345, ALPHA_024 0.0832801, ALPHA_025 0.0238446, ALPHA_026 0.00191956, ALPHA_028 0.207891, ALPHA_030 0.0920333, ALPHA_031 0.0450059, ALPHA_032 0.0175427, ALPHA_033 0.0227072, ALPHA_034 0.0452676, ALPHA_035 0.00435059, ALPHA_036 0.00655353, ALPHA_037 0.238325, ALPHA_038 0.0040301, ALPHA_039 0.00399422, ALPHA_040 0.0014604, ALPHA_041 0.189355, ALPHA_042 0.0688174, ALPHA_043 0.00128405, ALPHA_044 0.00164864, ALPHA_045 0.132375, ALPHA_046 0.0239324, ALPHA_049 0.0528691, ALPHA_050 0.00443905, ALPHA_051 0.0132604, ALPHA_052 0.00180513, ALPHA_053 0.0188713, ALPHA_054 0.0200158, ALPHA_055 0.000705376, ALPHA_060 0.0410077, ALPHA_101 0.0389985, EQUAL_WEIGHTED_COMPOSITE 0.0122141, IC_WEIGHTED_COMPOSITE 3.48538e-05, ICIR_WEIGHTED_COMPOSITE 1.4612e-05, CORRELATION_DISCOUNTED_COMPOSITE 0.000726199, ALPHA_PRODUCT_INTERACTION 0.0020447, CONDITIONAL_RANK_INTERACTION 0.00161672, NEUTRALIZED_IC_COMPOSITE 0.00023689, MARKET_BETA_NEUTRAL_COMPOSITE 0.000171798, REGIME_SWITCHING_COMPOSITE 0.000740309, RANDOM_FOREST_COMPOSITE 0.0114217, GRADIENT_BOOSTING_COMPOSITE 0.000990887
- IID Sharpe haircuts (BY, disclosed as IID) are in the sidecar.

## Excluded event exposure

| Gap | Start month | Trial | Reason type | Side | Signed weight |
| --- | --- | --- | --- | --- | --- |
| 0 | 2021-12 | equal_weight_pit | unresolved_delisting | long | 0.00235294 |
| 0 | 2021-12 | B:ALPHA_001:long_short | unresolved_delisting | short | -0.0116279 |
| 0 | 2021-12 | B:ALPHA_009:long_short | unresolved_delisting | long | 0.0116279 |
| 0 | 2021-12 | B:ALPHA_009:long_only | unresolved_delisting | long | 0.0232558 |
| 0 | 2021-12 | B:ALPHA_010:long_short | unresolved_delisting | long | 0.0116279 |
| 0 | 2021-12 | B:ALPHA_010:long_only | unresolved_delisting | long | 0.0232558 |
| 0 | 2021-12 | B:ALPHA_012:long_short | unresolved_delisting | long | 0.0116279 |
| 0 | 2021-12 | B:ALPHA_012:long_only | unresolved_delisting | long | 0.0232558 |
| 0 | 2021-12 | B:ALPHA_019:long_short | unresolved_delisting | short | -0.0119048 |
| 0 | 2021-12 | B:ALPHA_020:long_short | unresolved_delisting | long | 0.0116279 |
| 0 | 2021-12 | B:ALPHA_020:long_only | unresolved_delisting | long | 0.0232558 |
| 0 | 2021-12 | B:ALPHA_025:long_short | unresolved_delisting | long | 0.0116279 |
| 0 | 2021-12 | B:ALPHA_025:long_only | unresolved_delisting | long | 0.0232558 |
| 0 | 2021-12 | B:ALPHA_026:long_short | unresolved_delisting | long | 0.0128205 |
| 0 | 2021-12 | B:ALPHA_026:long_only | unresolved_delisting | long | 0.025641 |
| 0 | 2021-12 | B:ALPHA_028:long_short | unresolved_delisting | short | -0.0116279 |
| 0 | 2021-12 | B:ALPHA_030:long_short | unresolved_delisting | long | 0.0116279 |
| 0 | 2021-12 | B:ALPHA_030:long_only | unresolved_delisting | long | 0.0232558 |
| 0 | 2021-12 | B:ALPHA_031:long_short | unresolved_delisting | long | 0.0116279 |
| 0 | 2021-12 | B:ALPHA_031:long_only | unresolved_delisting | long | 0.0232558 |
| 0 | 2021-12 | B:ALPHA_032:long_short | unresolved_delisting | long | 0.0119048 |
| 0 | 2021-12 | B:ALPHA_032:long_only | unresolved_delisting | long | 0.0238095 |
| 0 | 2021-12 | B:ALPHA_035:long_short | unresolved_delisting | long | 0.0116279 |
| 0 | 2021-12 | B:ALPHA_035:long_only | unresolved_delisting | long | 0.0232558 |
| 0 | 2021-12 | B:ALPHA_043:long_short | unresolved_delisting | long | 0.0116279 |
| 0 | 2021-12 | B:ALPHA_043:long_only | unresolved_delisting | long | 0.0232558 |
| 0 | 2021-12 | B:ALPHA_044:long_short | unresolved_delisting | long | 0.0116279 |
| 0 | 2021-12 | B:ALPHA_044:long_only | unresolved_delisting | long | 0.0232558 |
| 0 | 2021-12 | B:ALPHA_049:long_short | unresolved_delisting | long | 0.0116279 |
| 0 | 2021-12 | B:ALPHA_049:long_only | unresolved_delisting | long | 0.0232558 |
| 0 | 2021-12 | B:ALPHA_051:long_short | unresolved_delisting | long | 0.0116279 |
| 0 | 2021-12 | B:ALPHA_051:long_only | unresolved_delisting | long | 0.0232558 |
| 0 | 2021-12 | B:ALPHA_055:long_short | unresolved_delisting | long | 0.0116279 |
| 0 | 2021-12 | B:ALPHA_055:long_only | unresolved_delisting | long | 0.0232558 |
| 0 | 2021-12 | B:ALPHA_060:long_short | unresolved_delisting | short | -0.0116279 |
| 0 | 2021-12 | B:CORRELATION_DISCOUNTED_COMPOSITE:long_short | unresolved_delisting | long | 0.0116279 |
| 0 | 2021-12 | B:CORRELATION_DISCOUNTED_COMPOSITE:long_only | unresolved_delisting | long | 0.0232558 |
| 0 | 2021-12 | B:ALPHA_PRODUCT_INTERACTION:long_short | unresolved_delisting | short | -0.0116279 |
| 0 | 2021-12 | B:CONDITIONAL_RANK_INTERACTION:long_short | unresolved_delisting | long | 0.0116279 |
| 0 | 2021-12 | B:CONDITIONAL_RANK_INTERACTION:long_only | unresolved_delisting | long | 0.0232558 |
| 0 | 2021-12 | B:NEUTRALIZED_IC_COMPOSITE:long_short | unresolved_delisting | long | 0.0116279 |
| 0 | 2021-12 | B:NEUTRALIZED_IC_COMPOSITE:long_only | unresolved_delisting | long | 0.0232558 |
| 0 | 2021-12 | B:MARKET_BETA_NEUTRAL_COMPOSITE:long_short | unresolved_delisting | long | 0.0116279 |
| 0 | 2021-12 | B:MARKET_BETA_NEUTRAL_COMPOSITE:long_only | unresolved_delisting | long | 0.0232558 |
| 0 | 2021-12 | B:REGIME_SWITCHING_COMPOSITE:long_short | unresolved_delisting | long | 0.0116279 |
| 0 | 2021-12 | B:REGIME_SWITCHING_COMPOSITE:long_only | unresolved_delisting | long | 0.0232558 |
| 2 | 2022-06 | equal_weight_pit | unresolved_delisting | long | 0.00233645 |
| 2 | 2022-06 | A:HIGH_52W:long_short | unresolved_delisting | long | 0.0116279 |
| 2 | 2022-06 | A:HIGH_52W:long_only | unresolved_delisting | long | 0.0232558 |
| 2 | 2022-06 | A:LOW_VOL_252:long_short | unresolved_delisting | long | 0.0116279 |
| 2 | 2022-06 | A:LOW_VOL_252:long_only | unresolved_delisting | long | 0.0232558 |
| 2 | 2022-06 | A:LOW_BETA_252:long_short | unresolved_delisting | long | 0.0116279 |
| 2 | 2022-06 | A:LOW_BETA_252:long_only | unresolved_delisting | long | 0.0232558 |
| 2 | 2022-06 | A:AMIHUD_ILLIQ_63:long_short | unresolved_delisting | short | -0.0116279 |
| 2 | 2022-06 | B:ALPHA_005:long_short | unresolved_delisting | long | 0.0116279 |
| 2 | 2022-06 | B:ALPHA_005:long_only | unresolved_delisting | long | 0.0232558 |
| 2 | 2022-06 | B:ALPHA_018:long_short | unresolved_delisting | long | 0.0116279 |
| 2 | 2022-06 | B:ALPHA_018:long_only | unresolved_delisting | long | 0.0232558 |
| 2 | 2022-06 | B:ALPHA_020:long_short | unresolved_delisting | short | -0.0116279 |
| 2 | 2022-06 | B:ALPHA_021:long_only | unresolved_delisting | long | 0.0232558 |
| 2 | 2022-06 | B:ALPHA_024:long_short | unresolved_delisting | long | 0.0119048 |
| 2 | 2022-06 | B:ALPHA_024:long_only | unresolved_delisting | long | 0.0238095 |
| 2 | 2022-06 | B:ALPHA_028:long_short | unresolved_delisting | long | 0.0116279 |
| 2 | 2022-06 | B:ALPHA_028:long_only | unresolved_delisting | long | 0.0232558 |
| 2 | 2022-06 | B:ALPHA_030:long_short | unresolved_delisting | long | 0.0116279 |
| 2 | 2022-06 | B:ALPHA_030:long_only | unresolved_delisting | long | 0.0232558 |
| 2 | 2022-06 | B:ALPHA_033:long_short | unresolved_delisting | long | 0.0116279 |
| 2 | 2022-06 | B:ALPHA_033:long_only | unresolved_delisting | long | 0.0232558 |
| 2 | 2022-06 | B:ALPHA_035:long_short | unresolved_delisting | long | 0.0116279 |
| 2 | 2022-06 | B:ALPHA_035:long_only | unresolved_delisting | long | 0.0232558 |
| 2 | 2022-06 | B:ALPHA_038:long_short | unresolved_delisting | long | 0.0116279 |
| 2 | 2022-06 | B:ALPHA_038:long_only | unresolved_delisting | long | 0.0232558 |
| 2 | 2022-06 | B:ALPHA_041:long_short | unresolved_delisting | long | 0.0116279 |
| 2 | 2022-06 | B:ALPHA_041:long_only | unresolved_delisting | long | 0.0232558 |
| 2 | 2022-06 | B:ALPHA_043:long_short | unresolved_delisting | long | 0.0116279 |
| 2 | 2022-06 | B:ALPHA_043:long_only | unresolved_delisting | long | 0.0232558 |
| 2 | 2022-06 | B:ALPHA_054:long_short | unresolved_delisting | long | 0.0116279 |
| 2 | 2022-06 | B:ALPHA_054:long_only | unresolved_delisting | long | 0.0232558 |
| 2 | 2022-06 | B:ALPHA_060:long_short | unresolved_delisting | long | 0.0116279 |
| 2 | 2022-06 | B:ALPHA_060:long_only | unresolved_delisting | long | 0.0232558 |
| 2 | 2022-06 | B:ALPHA_101:long_short | unresolved_delisting | short | -0.0116279 |
| 2 | 2022-06 | B:EQUAL_WEIGHTED_COMPOSITE:long_short | unresolved_delisting | long | 0.0116279 |
| 2 | 2022-06 | B:EQUAL_WEIGHTED_COMPOSITE:long_only | unresolved_delisting | long | 0.0232558 |
| 3 | 2022-10 | equal_weight_pit | unresolved_delisting | long | 0.00234192 |
| 3 | 2022-10 | equal_weight_pit | unresolved_delisting | long | 0.00234192 |
| 3 | 2022-10 | equal_weight_pit | unresolved_delisting | long | 0.00234192 |
| 3 | 2022-10 | A:MOM_12_1:long_short | unresolved_delisting | long | 0.0116279 |
| 3 | 2022-10 | A:MOM_12_1:long_short | unresolved_delisting | short | -0.0116279 |
| 3 | 2022-10 | A:MOM_12_1:long_only | unresolved_delisting | long | 0.0232558 |
| 3 | 2022-10 | A:HIGH_52W:long_short | unresolved_delisting | long | 0.0116279 |
| 3 | 2022-10 | A:HIGH_52W:long_only | unresolved_delisting | long | 0.0232558 |
| 3 | 2022-10 | A:REV_1M:long_short | unresolved_delisting | long | 0.0116279 |
| 3 | 2022-10 | A:REV_1M:long_short | unresolved_delisting | short | -0.0116279 |
| 3 | 2022-10 | A:REV_1M:long_short | unresolved_delisting | short | -0.0116279 |
| 3 | 2022-10 | A:REV_1M:long_only | unresolved_delisting | long | 0.0232558 |
| 3 | 2022-10 | A:LOW_VOL_252:long_short | unresolved_delisting | short | -0.0116279 |
| 3 | 2022-10 | A:LOW_VOL_252:long_short | unresolved_delisting | short | -0.0116279 |
| 3 | 2022-10 | B:ALPHA_001:long_short | unresolved_delisting | long | 0.0116279 |
| 3 | 2022-10 | B:ALPHA_001:long_only | unresolved_delisting | long | 0.0232558 |
| 3 | 2022-10 | B:ALPHA_002:long_short | unresolved_delisting | long | 0.0116279 |
| 3 | 2022-10 | B:ALPHA_002:long_short | unresolved_delisting | short | -0.0116279 |
| 3 | 2022-10 | B:ALPHA_002:long_only | unresolved_delisting | long | 0.0232558 |
| 3 | 2022-10 | B:ALPHA_005:long_short | unresolved_delisting | short | -0.0116279 |
| 3 | 2022-10 | B:ALPHA_005:long_short | unresolved_delisting | short | -0.0116279 |
| 3 | 2022-10 | B:ALPHA_006:long_short | unresolved_delisting | short | -0.0116279 |
| 3 | 2022-10 | B:ALPHA_009:long_short | unresolved_delisting | short | -0.0116279 |
| 3 | 2022-10 | B:ALPHA_010:long_short | unresolved_delisting | short | -0.0116279 |
| 3 | 2022-10 | B:ALPHA_014:long_short | unresolved_delisting | long | 0.0116279 |
| 3 | 2022-10 | B:ALPHA_014:long_short | unresolved_delisting | short | -0.0116279 |
| 3 | 2022-10 | B:ALPHA_014:long_only | unresolved_delisting | long | 0.0232558 |
| 3 | 2022-10 | B:ALPHA_016:long_short | unresolved_delisting | long | 0.0116279 |
| 3 | 2022-10 | B:ALPHA_016:long_only | unresolved_delisting | long | 0.0232558 |
| 3 | 2022-10 | B:ALPHA_017:long_short | unresolved_delisting | short | -0.0116279 |
| 3 | 2022-10 | B:ALPHA_019:long_short | unresolved_delisting | long | 0.0119048 |
| 3 | 2022-10 | B:ALPHA_019:long_short | unresolved_delisting | short | -0.0119048 |
| 3 | 2022-10 | B:ALPHA_019:long_only | unresolved_delisting | long | 0.0238095 |
| 3 | 2022-10 | B:ALPHA_023:long_short | unresolved_delisting | short | -0.0116279 |
| 3 | 2022-10 | B:ALPHA_024:long_short | unresolved_delisting | long | 0.0119048 |
| 3 | 2022-10 | B:ALPHA_024:long_only | unresolved_delisting | long | 0.0238095 |
| 3 | 2022-10 | B:ALPHA_025:long_short | unresolved_delisting | short | -0.0116279 |
| 3 | 2022-10 | B:ALPHA_025:long_short | unresolved_delisting | short | -0.0116279 |
| 3 | 2022-10 | B:ALPHA_026:long_short | unresolved_delisting | short | -0.0138889 |
| 3 | 2022-10 | B:ALPHA_031:long_short | unresolved_delisting | short | -0.0116279 |
| 3 | 2022-10 | B:ALPHA_032:long_short | unresolved_delisting | short | -0.0119048 |
| 3 | 2022-10 | B:ALPHA_033:long_short | unresolved_delisting | short | -0.0116279 |
| 3 | 2022-10 | B:ALPHA_034:long_short | unresolved_delisting | short | -0.0116279 |
| 3 | 2022-10 | B:ALPHA_035:long_short | unresolved_delisting | short | -0.0116279 |
| 3 | 2022-10 | B:ALPHA_036:long_short | unresolved_delisting | short | -0.0119048 |
| 3 | 2022-10 | B:ALPHA_037:long_short | unresolved_delisting | short | -0.0119048 |
| 3 | 2022-10 | B:ALPHA_038:long_short | unresolved_delisting | short | -0.0116279 |
| 3 | 2022-10 | B:ALPHA_039:long_short | unresolved_delisting | short | -0.0119048 |
| 3 | 2022-10 | B:ALPHA_039:long_short | unresolved_delisting | short | -0.0119048 |
| 3 | 2022-10 | B:ALPHA_041:long_short | unresolved_delisting | short | -0.0116279 |
| 3 | 2022-10 | B:ALPHA_042:long_short | unresolved_delisting | short | -0.0116279 |
| 3 | 2022-10 | B:ALPHA_043:long_short | unresolved_delisting | long | 0.0116279 |
| 3 | 2022-10 | B:ALPHA_043:long_only | unresolved_delisting | long | 0.0232558 |
| 3 | 2022-10 | B:ALPHA_044:long_short | unresolved_delisting | short | -0.0116279 |
| 3 | 2022-10 | B:ALPHA_045:long_short | unresolved_delisting | long | 0.0116279 |
| 3 | 2022-10 | B:ALPHA_045:long_only | unresolved_delisting | long | 0.0232558 |
| 3 | 2022-10 | B:ALPHA_053:long_short | unresolved_delisting | short | -0.0119048 |
| 3 | 2022-10 | B:ALPHA_054:long_short | unresolved_delisting | short | -0.0116279 |
| 3 | 2022-10 | B:ALPHA_060:long_short | unresolved_delisting | long | 0.0116279 |
| 3 | 2022-10 | B:ALPHA_060:long_short | unresolved_delisting | long | 0.0116279 |
| 3 | 2022-10 | B:ALPHA_060:long_only | unresolved_delisting | long | 0.0232558 |
| 3 | 2022-10 | B:ALPHA_060:long_only | unresolved_delisting | long | 0.0232558 |
| 3 | 2022-10 | B:ALPHA_101:long_short | unresolved_delisting | long | 0.0116279 |
| 3 | 2022-10 | B:ALPHA_101:long_only | unresolved_delisting | long | 0.0232558 |
| 3 | 2022-10 | B:EQUAL_WEIGHTED_COMPOSITE:long_short | unresolved_delisting | short | -0.0116279 |
| 3 | 2022-10 | B:IC_WEIGHTED_COMPOSITE:long_short | unresolved_delisting | short | -0.0116279 |
| 3 | 2022-10 | B:ICIR_WEIGHTED_COMPOSITE:long_short | unresolved_delisting | short | -0.0116279 |
| 3 | 2022-10 | B:CORRELATION_DISCOUNTED_COMPOSITE:long_short | unresolved_delisting | short | -0.0116279 |
| 3 | 2022-10 | B:NEUTRALIZED_IC_COMPOSITE:long_short | unresolved_delisting | short | -0.0116279 |
| 3 | 2022-10 | B:MARKET_BETA_NEUTRAL_COMPOSITE:long_short | unresolved_delisting | short | -0.0116279 |
| 3 | 2022-10 | B:REGIME_SWITCHING_COMPOSITE:long_short | unresolved_delisting | short | -0.0116279 |
| 5 | 2023-03 | equal_weight_pit | unresolved_delisting | long | 0.002331 |
| 5 | 2023-03 | A:MOM_12_1:long_short | unresolved_delisting | short | -0.0116279 |
| 5 | 2023-03 | A:HIGH_52W:long_short | unresolved_delisting | short | -0.0116279 |
| 5 | 2023-03 | A:REV_1M:long_short | unresolved_delisting | long | 0.0116279 |
| 5 | 2023-03 | A:REV_1M:long_only | unresolved_delisting | long | 0.0232558 |
| 5 | 2023-03 | A:LOW_VOL_252:long_short | unresolved_delisting | short | -0.0116279 |
| 5 | 2023-03 | A:LOW_BETA_252:long_short | unresolved_delisting | short | -0.0116279 |
| 5 | 2023-03 | B:ALPHA_003:long_short | unresolved_delisting | long | 0.0116279 |
| 5 | 2023-03 | B:ALPHA_003:long_only | unresolved_delisting | long | 0.0232558 |
| 5 | 2023-03 | B:ALPHA_004:long_short | unresolved_delisting | long | 0.0116279 |
| 5 | 2023-03 | B:ALPHA_004:long_only | unresolved_delisting | long | 0.0232558 |
| 5 | 2023-03 | B:ALPHA_005:long_short | unresolved_delisting | long | 0.0116279 |
| 5 | 2023-03 | B:ALPHA_005:long_only | unresolved_delisting | long | 0.0232558 |
| 5 | 2023-03 | B:ALPHA_018:long_short | unresolved_delisting | short | -0.0116279 |
| 5 | 2023-03 | B:ALPHA_020:long_short | unresolved_delisting | long | 0.0116279 |
| 5 | 2023-03 | B:ALPHA_020:long_only | unresolved_delisting | long | 0.0232558 |
| 5 | 2023-03 | B:ALPHA_021:long_short | unresolved_delisting | long | 0.0116279 |
| 5 | 2023-03 | B:ALPHA_022:long_short | unresolved_delisting | long | 0.0116279 |
| 5 | 2023-03 | B:ALPHA_022:long_only | unresolved_delisting | long | 0.0232558 |
| 5 | 2023-03 | B:ALPHA_024:long_short | unresolved_delisting | short | -0.0119048 |
| 5 | 2023-03 | B:ALPHA_031:long_short | unresolved_delisting | long | 0.0116279 |
| 5 | 2023-03 | B:ALPHA_031:long_only | unresolved_delisting | long | 0.0232558 |
| 5 | 2023-03 | B:ALPHA_032:long_short | unresolved_delisting | long | 0.0119048 |
| 5 | 2023-03 | B:ALPHA_032:long_only | unresolved_delisting | long | 0.0238095 |
| 5 | 2023-03 | B:ALPHA_039:long_short | unresolved_delisting | long | 0.0119048 |
| 5 | 2023-03 | B:ALPHA_039:long_only | unresolved_delisting | long | 0.0238095 |
| 5 | 2023-03 | B:ALPHA_040:long_short | unresolved_delisting | long | 0.0116279 |
| 5 | 2023-03 | B:ALPHA_040:long_only | unresolved_delisting | long | 0.0232558 |
| 5 | 2023-03 | B:ALPHA_043:long_short | unresolved_delisting | long | 0.0116279 |
| 5 | 2023-03 | B:ALPHA_043:long_only | unresolved_delisting | long | 0.0232558 |
| 5 | 2023-03 | B:ALPHA_044:long_short | unresolved_delisting | long | 0.0116279 |
| 5 | 2023-03 | B:ALPHA_044:long_only | unresolved_delisting | long | 0.0232558 |
| 5 | 2023-03 | B:ALPHA_050:long_short | unresolved_delisting | long | 0.0125 |
| 5 | 2023-03 | B:ALPHA_050:long_only | unresolved_delisting | long | 0.025 |
| 5 | 2023-03 | B:CORRELATION_DISCOUNTED_COMPOSITE:long_short | unresolved_delisting | short | -0.0116279 |
| 5 | 2023-03 | B:ALPHA_PRODUCT_INTERACTION:long_short | unresolved_delisting | long | 0.0116279 |
| 5 | 2023-03 | B:ALPHA_PRODUCT_INTERACTION:long_only | unresolved_delisting | long | 0.0232558 |
| 5 | 2023-03 | B:CONDITIONAL_RANK_INTERACTION:long_short | unresolved_delisting | long | 0.0116279 |
| 5 | 2023-03 | B:CONDITIONAL_RANK_INTERACTION:long_only | unresolved_delisting | long | 0.0232558 |
| 8 | 2023-10 | equal_weight_pit | unresolved_delisting | long | 0.00232019 |
| 8 | 2023-10 | A:HIGH_52W:long_short | unresolved_delisting | long | 0.0116279 |
| 8 | 2023-10 | A:HIGH_52W:long_only | unresolved_delisting | long | 0.0232558 |
| 8 | 2023-10 | A:LOW_BETA_252:long_short | unresolved_delisting | long | 0.0116279 |
| 8 | 2023-10 | A:LOW_BETA_252:long_only | unresolved_delisting | long | 0.0232558 |
| 8 | 2023-10 | A:AMIHUD_ILLIQ_63:long_short | unresolved_delisting | short | -0.0116279 |
| 8 | 2023-10 | B:ALPHA_007:long_short | unresolved_delisting | short | -0.0116279 |
| 8 | 2023-10 | B:ALPHA_021:long_short | unresolved_delisting | short | -0.0116279 |
| 8 | 2023-10 | B:ALPHA_031:long_short | unresolved_delisting | short | -0.0116279 |
| 8 | 2023-10 | B:ALPHA_045:long_short | unresolved_delisting | long | 0.0116279 |
| 8 | 2023-10 | B:ALPHA_045:long_only | unresolved_delisting | long | 0.0232558 |
| 8 | 2023-10 | B:ALPHA_049:long_short | unresolved_delisting | short | -0.0116279 |
| 9 | 2024-05 | equal_weight_pit | unresolved_delisting | long | 0.00230947 |
| 9 | 2024-05 | B:ALPHA_019:long_short | unresolved_delisting | long | 0.0119048 |
| 9 | 2024-05 | B:ALPHA_019:long_only | unresolved_delisting | long | 0.0238095 |
| 9 | 2024-05 | B:ALPHA_024:long_short | unresolved_delisting | short | -0.0116279 |
| 9 | 2024-05 | B:ALPHA_026:long_short | unresolved_delisting | long | 0.0121951 |
| 9 | 2024-05 | B:ALPHA_026:long_only | unresolved_delisting | long | 0.0243902 |
| 9 | 2024-05 | B:ALPHA_036:long_short | unresolved_delisting | long | 0.0119048 |
| 9 | 2024-05 | B:ALPHA_036:long_only | unresolved_delisting | long | 0.0232558 |
| 9 | 2024-05 | B:ALPHA_043:long_short | unresolved_delisting | long | 0.0116279 |
| 9 | 2024-05 | B:ALPHA_043:long_only | unresolved_delisting | long | 0.0232558 |
| 9 | 2024-05 | B:ALPHA_044:long_short | unresolved_delisting | long | 0.0113636 |
| 9 | 2024-05 | B:ALPHA_044:long_only | unresolved_delisting | long | 0.0227273 |
| 9 | 2024-05 | B:ALPHA_046:long_short | unresolved_delisting | long | 0.0113636 |
| 9 | 2024-05 | B:ALPHA_046:long_only | unresolved_delisting | long | 0.0227273 |
| 9 | 2024-05 | B:ALPHA_052:long_short | unresolved_delisting | long | 0.0119048 |
| 9 | 2024-05 | B:ALPHA_052:long_only | unresolved_delisting | long | 0.0238095 |
| 9 | 2024-05 | B:IC_WEIGHTED_COMPOSITE:long_short | unresolved_delisting | short | -0.0113636 |
| 9 | 2024-05 | B:NEUTRALIZED_IC_COMPOSITE:long_short | unresolved_delisting | short | -0.0113636 |
| 9 | 2024-05 | B:MARKET_BETA_NEUTRAL_COMPOSITE:long_short | unresolved_delisting | short | -0.0113636 |
| 9 | 2024-05 | B:REGIME_SWITCHING_COMPOSITE:long_short | unresolved_delisting | short | -0.0113636 |
| 10 | 2024-11 | equal_weight_pit | unresolved_delisting | long | 0.00230947 |
| 10 | 2024-11 | B:ALPHA_003:long_short | unresolved_delisting | long | 0.0116279 |
| 10 | 2024-11 | B:ALPHA_003:long_only | unresolved_delisting | long | 0.0227273 |
| 10 | 2024-11 | B:ALPHA_018:long_short | unresolved_delisting | long | 0.0113636 |
| 10 | 2024-11 | B:ALPHA_018:long_only | unresolved_delisting | long | 0.0227273 |
| 10 | 2024-11 | B:ALPHA_025:long_short | unresolved_delisting | long | 0.0113636 |
| 10 | 2024-11 | B:ALPHA_025:long_only | unresolved_delisting | long | 0.0227273 |
| 10 | 2024-11 | B:ALPHA_026:long_short | unresolved_delisting | short | -0.0128205 |
| 10 | 2024-11 | B:ALPHA_028:long_short | unresolved_delisting | long | 0.0113636 |
| 10 | 2024-11 | B:ALPHA_028:long_only | unresolved_delisting | long | 0.0227273 |
| 10 | 2024-11 | B:ALPHA_033:long_short | unresolved_delisting | long | 0.0113636 |
| 10 | 2024-11 | B:ALPHA_033:long_only | unresolved_delisting | long | 0.0227273 |
| 10 | 2024-11 | B:ALPHA_037:long_short | unresolved_delisting | long | 0.0116279 |
| 10 | 2024-11 | B:ALPHA_037:long_only | unresolved_delisting | long | 0.0232558 |
| 10 | 2024-11 | B:ALPHA_038:long_short | unresolved_delisting | long | 0.0113636 |
| 10 | 2024-11 | B:ALPHA_038:long_only | unresolved_delisting | long | 0.0227273 |
| 10 | 2024-11 | B:ALPHA_042:long_short | unresolved_delisting | long | 0.0113636 |
| 10 | 2024-11 | B:ALPHA_042:long_only | unresolved_delisting | long | 0.0227273 |
| 10 | 2024-11 | B:ALPHA_045:long_short | unresolved_delisting | short | -0.0113636 |
| 10 | 2024-11 | B:ALPHA_053:long_short | unresolved_delisting | long | 0.0116279 |
| 10 | 2024-11 | B:ALPHA_053:long_only | unresolved_delisting | long | 0.0227273 |
| 10 | 2024-11 | B:ALPHA_054:long_short | unresolved_delisting | long | 0.0113636 |
| 10 | 2024-11 | B:ALPHA_054:long_only | unresolved_delisting | long | 0.0227273 |
| 10 | 2024-11 | B:ALPHA_060:long_short | unresolved_delisting | long | 0.0113636 |
| 10 | 2024-11 | B:ALPHA_060:long_only | unresolved_delisting | long | 0.0227273 |
| 10 | 2024-11 | B:ALPHA_101:long_short | unresolved_delisting | short | -0.0113636 |
| 12 | 2025-05 | equal_weight_pit | unresolved_delisting | long | 0.00230947 |
| 12 | 2025-05 | A:REV_1M:long_short | unresolved_delisting | short | -0.0113636 |
| 12 | 2025-05 | A:LOW_BETA_252:long_short | unresolved_delisting | short | -0.0113636 |
| 12 | 2025-05 | B:ALPHA_019:long_short | unresolved_delisting | short | -0.0116279 |
| 12 | 2025-05 | B:ALPHA_020:long_short | unresolved_delisting | long | 0.0113636 |
| 12 | 2025-05 | B:ALPHA_020:long_only | unresolved_delisting | long | 0.0227273 |
| 12 | 2025-05 | B:ALPHA_021:long_only | unresolved_delisting | long | 0.0227273 |
| 12 | 2025-05 | B:ALPHA_023:long_short | unresolved_delisting | long | 0.0113636 |
| 12 | 2025-05 | B:ALPHA_023:long_only | unresolved_delisting | long | 0.0227273 |
| 12 | 2025-05 | B:ALPHA_024:long_short | unresolved_delisting | long | 0.0116279 |
| 12 | 2025-05 | B:ALPHA_024:long_only | unresolved_delisting | long | 0.0232558 |
| 12 | 2025-05 | B:ALPHA_036:long_short | unresolved_delisting | short | -0.0116279 |
| 12 | 2025-05 | B:ALPHA_040:long_short | unresolved_delisting | short | -0.0113636 |
| 12 | 2025-05 | B:CONDITIONAL_RANK_INTERACTION:long_short | unresolved_delisting | short | -0.0113636 |
| 15 | 2025-11 | equal_weight_pit | unresolved_delisting | long | 0.00231481 |
| 15 | 2025-11 | equal_weight_pit | unresolved_delisting | long | 0.00231481 |
| 15 | 2025-11 | A:HIGH_52W:long_short | unresolved_delisting | long | 0.0116279 |
| 15 | 2025-11 | A:HIGH_52W:long_only | unresolved_delisting | long | 0.0232558 |
| 15 | 2025-11 | A:LOW_VOL_252:long_short | unresolved_delisting | long | 0.0116279 |
| 15 | 2025-11 | A:LOW_VOL_252:long_only | unresolved_delisting | long | 0.0232558 |
| 15 | 2025-11 | A:LOW_BETA_252:long_short | unresolved_delisting | long | 0.0116279 |
| 15 | 2025-11 | A:LOW_BETA_252:long_only | unresolved_delisting | long | 0.0232558 |
| 15 | 2025-11 | B:ALPHA_002:long_short | unresolved_delisting | long | 0.0113636 |
| 15 | 2025-11 | B:ALPHA_002:long_short | unresolved_delisting | long | 0.0113636 |
| 15 | 2025-11 | B:ALPHA_002:long_only | unresolved_delisting | long | 0.0227273 |
| 15 | 2025-11 | B:ALPHA_002:long_only | unresolved_delisting | long | 0.0227273 |
| 15 | 2025-11 | B:ALPHA_003:long_short | unresolved_delisting | short | -0.0116279 |
| 15 | 2025-11 | B:ALPHA_003:long_short | unresolved_delisting | short | -0.0116279 |
| 15 | 2025-11 | B:ALPHA_006:long_short | unresolved_delisting | short | -0.0113636 |
| 15 | 2025-11 | B:ALPHA_006:long_short | unresolved_delisting | short | -0.0113636 |
| 15 | 2025-11 | B:ALPHA_009:long_short | unresolved_delisting | long | 0.0113636 |
| 15 | 2025-11 | B:ALPHA_009:long_only | unresolved_delisting | long | 0.0227273 |
| 15 | 2025-11 | B:ALPHA_013:long_short | unresolved_delisting | long | 0.0113636 |
| 15 | 2025-11 | B:ALPHA_013:long_only | unresolved_delisting | long | 0.0227273 |
| 15 | 2025-11 | B:ALPHA_018:long_short | unresolved_delisting | long | 0.0113636 |
| 15 | 2025-11 | B:ALPHA_018:long_short | unresolved_delisting | long | 0.0113636 |
| 15 | 2025-11 | B:ALPHA_018:long_only | unresolved_delisting | long | 0.0227273 |
| 15 | 2025-11 | B:ALPHA_018:long_only | unresolved_delisting | long | 0.0227273 |
| 15 | 2025-11 | B:ALPHA_021:long_only | unresolved_delisting | long | 0.0232558 |
| 15 | 2025-11 | B:ALPHA_021:long_only | unresolved_delisting | long | 0.0232558 |
| 15 | 2025-11 | B:ALPHA_025:long_short | unresolved_delisting | long | 0.0116279 |
| 15 | 2025-11 | B:ALPHA_025:long_only | unresolved_delisting | long | 0.0232558 |
| 15 | 2025-11 | B:ALPHA_028:long_short | unresolved_delisting | long | 0.0116279 |
| 15 | 2025-11 | B:ALPHA_028:long_only | unresolved_delisting | long | 0.0232558 |
| 15 | 2025-11 | B:ALPHA_030:long_short | unresolved_delisting | long | 0.0116279 |
| 15 | 2025-11 | B:ALPHA_030:long_only | unresolved_delisting | long | 0.0232558 |
| 15 | 2025-11 | B:ALPHA_033:long_short | unresolved_delisting | long | 0.0113636 |
| 15 | 2025-11 | B:ALPHA_033:long_only | unresolved_delisting | long | 0.0227273 |
| 15 | 2025-11 | B:ALPHA_036:long_short | unresolved_delisting | short | -0.0119048 |
| 15 | 2025-11 | B:ALPHA_038:long_short | unresolved_delisting | long | 0.0113636 |
| 15 | 2025-11 | B:ALPHA_038:long_only | unresolved_delisting | long | 0.0227273 |
| 15 | 2025-11 | B:ALPHA_041:long_short | unresolved_delisting | long | 0.0113636 |
| 15 | 2025-11 | B:ALPHA_041:long_only | unresolved_delisting | long | 0.0227273 |
| 15 | 2025-11 | B:ALPHA_042:long_short | unresolved_delisting | long | 0.0113636 |
| 15 | 2025-11 | B:ALPHA_042:long_only | unresolved_delisting | long | 0.0227273 |
| 15 | 2025-11 | B:ALPHA_050:long_short | unresolved_delisting | short | -0.0119048 |
| 15 | 2025-11 | B:ALPHA_053:long_short | unresolved_delisting | long | 0.0116279 |
| 15 | 2025-11 | B:ALPHA_053:long_short | unresolved_delisting | long | 0.0116279 |
| 15 | 2025-11 | B:ALPHA_053:long_only | unresolved_delisting | long | 0.0232558 |
| 15 | 2025-11 | B:ALPHA_053:long_only | unresolved_delisting | long | 0.0232558 |
| 15 | 2025-11 | B:ALPHA_054:long_short | unresolved_delisting | long | 0.0113636 |
| 15 | 2025-11 | B:ALPHA_054:long_short | unresolved_delisting | long | 0.0113636 |
| 15 | 2025-11 | B:ALPHA_054:long_only | unresolved_delisting | long | 0.0227273 |
| 15 | 2025-11 | B:ALPHA_054:long_only | unresolved_delisting | long | 0.0227273 |
| 15 | 2025-11 | B:ALPHA_060:long_short | unresolved_delisting | long | 0.0113636 |
| 15 | 2025-11 | B:ALPHA_060:long_short | unresolved_delisting | long | 0.0113636 |
| 15 | 2025-11 | B:ALPHA_060:long_only | unresolved_delisting | long | 0.0227273 |
| 15 | 2025-11 | B:ALPHA_060:long_only | unresolved_delisting | long | 0.0227273 |
| 15 | 2025-11 | B:ALPHA_101:long_short | unresolved_delisting | short | -0.0113636 |
| 19 | 2026-08 | equal_weight_pit | unresolved_delisting | long | 0.002331 |
| 19 | 2026-08 | A:HIGH_52W:long_short | unresolved_delisting | long | 0.0116279 |
| 19 | 2026-08 | A:HIGH_52W:long_only | unresolved_delisting | long | 0.0232558 |
| 19 | 2026-08 | A:LOW_VOL_252:long_short | unresolved_delisting | long | 0.0116279 |
| 19 | 2026-08 | A:LOW_VOL_252:long_only | unresolved_delisting | long | 0.0232558 |
| 19 | 2026-08 | B:ALPHA_006:long_short | unresolved_delisting | short | -0.0116279 |
| 19 | 2026-08 | B:ALPHA_013:long_short | unresolved_delisting | long | 0.0116279 |
| 19 | 2026-08 | B:ALPHA_013:long_only | unresolved_delisting | long | 0.0232558 |
| 19 | 2026-08 | B:ALPHA_016:long_short | unresolved_delisting | long | 0.0116279 |
| 19 | 2026-08 | B:ALPHA_016:long_only | unresolved_delisting | long | 0.0232558 |
| 19 | 2026-08 | B:ALPHA_017:long_short | unresolved_delisting | short | -0.0116279 |
| 19 | 2026-08 | B:ALPHA_028:long_short | unresolved_delisting | long | 0.0116279 |
| 19 | 2026-08 | B:ALPHA_028:long_only | unresolved_delisting | long | 0.0232558 |
| 19 | 2026-08 | B:ALPHA_030:long_short | unresolved_delisting | long | 0.0116279 |
| 19 | 2026-08 | B:ALPHA_030:long_only | unresolved_delisting | long | 0.0232558 |
| 19 | 2026-08 | B:ALPHA_035:long_short | unresolved_delisting | short | -0.0116279 |
| 19 | 2026-08 | B:ALPHA_036:long_short | unresolved_delisting | long | 0.0119048 |
| 19 | 2026-08 | B:ALPHA_036:long_only | unresolved_delisting | long | 0.0238095 |
| 19 | 2026-08 | B:ALPHA_044:long_short | unresolved_delisting | short | -0.0116279 |
| 19 | 2026-08 | B:ALPHA_046:long_only | unresolved_delisting | long | 0.0232558 |
| 19 | 2026-08 | B:ALPHA_054:long_short | unresolved_delisting | long | 0.0116279 |
| 19 | 2026-08 | B:ALPHA_054:long_only | unresolved_delisting | long | 0.0232558 |
| 19 | 2026-08 | B:ALPHA_060:long_short | unresolved_delisting | long | 0.0116279 |
| 19 | 2026-08 | B:ALPHA_060:long_only | unresolved_delisting | long | 0.0232558 |
| 19 | 2026-08 | B:ALPHA_101:long_short | unresolved_delisting | short | -0.0116279 |

Gap windows condition on the fact that an asset disappeared, halted, or joined with a missing bar; they apply to every book and benchmark alike.

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

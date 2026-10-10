# Milestone 5.5 confirm and check stages of trial family v1

Evidence ceiling: `DIAGNOSTIC_ONLY`. This is a simulated research diagnostic. It gives aggregates only and makes no profitability claim. The JSON file `reports/m55_confirm_v1.json` holds every aggregate of this report.

- Run label: stock-level out-of-sample, factor-level in-sample; never called confirmation.
- Check period label: partly out-of-sample.
- Factor-level reuse (`reports_owed.labels`): M5 step 2: JKP and French factor returns 1926-2025, built from the same CRSP stocks (factor level).
- Sample reuse (`prior_exposures`, R10): seen before the trial declaration, counted under R9:
  - M5 step 2: JKP and French factor returns 1926-2025, built from the same CRSP stocks (factor level)
  - M5 step 4: on real_v2 point-in-time books, R0 trailed the equal-weight book by 1.55 and 2.86 percent a year and 9 of 12 sleeve results trailed it (reports/m5_step4.md)
  - the WRDS loader intake aggregates listed under declaration_timing (no return statistic)
  - the 1963-1992 synthetic-only low-risk construction experiment (no real data)
- Benchmarks: confirm months SPY total return; CW-PIT; check months SPY; CW-PIT. SPY: SPY total return from its PERMNO's dlyret, from 1993-02.
- Execution timing: `after_close_signal_next_observed_close_v1: at each month-end rebalance row r, cap weights, scores, eligibility, and the TE covariance use rows up to r - 1 only; both books trade at the close of row r and earn from row r + 1`.
- Test B: stopped at the coverage stop (label `stopped_coverage`, p_B 1.0). No low-risk book was built.

## Test A

The decision reads the primary loader run with the primary cost case. The last_close rerun is the R4 comparison and decides nothing. With p_B = 1.0, the Holm-adjusted p_A is min(1, 2 x p_A), so the Holm condition (alpha 0.05) needs p_A <= 0.025. The stop rule stops the line when the confirm annual mean against SPY is below 0.003 a year, whatever the label.

| Loader run | p_A | Holm p_A | Holm condition | Confirm vs SPY | Confirm vs CW-PIT | 2x vs SPY | 2x vs CW-PIT | Stop rule | Check vs SPY | Check vs CW-PIT | Label |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| primary | 0.6944 | 1.0000 | no | 0.298% | -0.112% | -0.053% | -0.313% | confirm_below_floor | 0.484% | 0.324% | `not_met` |
| last_close | 0.6900 | 1.0000 | no | 0.279% | -0.110% | -0.071% | -0.310% | confirm_below_floor | 0.478% | 0.324% | `not_met` |

Conditions of `decide_a`:

| Condition | primary | last_close |
| --- | --- | --- |
| check_means_not_negative | yes | yes |
| confirm_means_positive | no | no |
| cost_2x_means_positive | no | no |
| holm_p_at_most_alpha | no | no |

R4 fragility of test A (a sign flip of an active annual mean of the composite, confirm or check, against SPY or CW-PIT, either cost case): no sign flip. The label stays.

Composite test records, confirm months (annual means, HAC t, one-sided p):

| Loader run | Cost case | Months | Blank months | Mean vs SPY | t vs SPY | p vs SPY | Mean vs CW-PIT | t vs CW-PIT | p vs CW-PIT | p_A |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| primary | primary | 154 | 100 | 0.298% | 1.041 | 0.1490 | -0.112% | -0.508 | 0.6944 | 0.6944 |
| primary | sensitivity_2x | 154 | 100 | -0.053% | -0.185 | 0.5734 | -0.313% | -1.406 | 0.9202 | 0.9202 |
| last_close | primary | 154 | 100 | 0.279% | 0.978 | 0.1641 | -0.110% | -0.496 | 0.6900 | 0.6900 |
| last_close | sensitivity_2x | 154 | 100 | -0.071% | -0.247 | 0.5977 | -0.310% | -1.393 | 0.9181 | 0.9181 |

## Limitations

- The stop rule applies: the confirm annual mean of the composite against SPY is 0.298%, below the floor 0.3% a year. The line stops as a declared negative result, whatever the test A label. The check stage still ran, because declared runs stay visible (R9).
- Test A has the label `not_met` in the primary loader run. No active annual mean of the composite changes sign between the primary run and the last_close rerun (R4).
- In the confirm segment, the path_break_held blank set removes 100 months (share 0.3937) from every series of the primary loader run. 2 held positions cause it. The frozen rule blanks these months in every book, and R6 forbids a fill.
- Under amendment 4, a member that leaves the index on a row without a close gets an R4 event of cause unknown on that row, in the confirm and check segments only. In the primary loader run there are 1 such events, CW-PIT holds 1 of them, and 0 of the held ones have a close again later in the segment. The primary run settles a held event at -100 percent, because a later close is not known on that row (R1). The last_close run settles it at the last close and is the R4 sensitivity for this case.
- The check period is labelled 'partly out-of-sample'. It leaves out the 26 months 2019-07 to 2021-08 (the seal, the sealed 2020-07-31 row, and the warm-up), and each segment starts from cash.
- The run label is 'stock-level out-of-sample, factor-level in-sample; never called confirmation'. M5 step 2: JKP and French factor returns 1926-2025, built from the same CRSP stocks (factor level).
- A member without ME or without a price at r - 1 leaves both books, and SPY keeps it, so it is replication error (R2, R6). The OI-09 decomposition reports this term (CW-PIT against SPY).
- An invalid quote cell pays the schedule spread. The half-spread tables give the share of the traded notional of each quote status and the invalid cells by later exit class.
- The secondary family decides nothing. Its tables are in ID order, are not a ranking, and give the Benjamini-Yekutieli q-value beside each member.
- The trial file states the power of rule A (`limitations`): a test A label other than `met` often means 'not shown', not 'absent'.
- This report makes no profitability claim. The books are long only, so no borrow cost applies.

## Secondary family

Test A statistics of each member over the confirm months, with Benjamini-Yekutieli q-values (family size 9). The family decides nothing. The rows are in ID order and are not a ranking. A member with zero or undefined TE or t is typed undefined and keeps its place in the family size.

| Member | Loader run | Cost case | Months | Mean vs SPY | t vs SPY | Mean vs CW-PIT | t vs CW-PIT | p_A | q (BY) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| S1 | primary | primary | 154 | 0.344% | 1.054 | -0.066% | -0.266 | 0.6050 | 1.0000 |
| S2 | primary | primary | 154 | 0.608% | 1.976 | 0.199% | 0.872 | 0.1916 | 1.0000 |
| S3 | primary | primary | 154 | 0.123% | 0.496 | -0.287% | -1.637 | 0.9492 | 1.0000 |
| S4 | primary | primary | 154 | 0.441% | 1.074 | 0.031% | 0.085 | 0.4659 | 1.0000 |
| S5 | primary | primary | 154 | 0.492% | 1.699 | 0.082% | 0.350 | 0.3631 | 1.0000 |
| S6 | primary | primary | 154 | 0.619% | 1.561 | 0.209% | 0.620 | 0.2675 | 1.0000 |
| S7 | primary | primary | 154 | 0.928% | 2.607 | 0.519% | 1.791 | 0.0367 | 0.9337 |
| S8 | primary | primary | 154 | 0.464% | 0.948 | 0.054% | 0.117 | 0.4533 | 1.0000 |
| family_a_baseline | primary | primary | 154 | 0.444% | 1.297 | 0.034% | 0.126 | 0.4497 | 1.0000 |
| S1 | primary | sensitivity_2x | 154 | -0.085% | -0.258 | -0.345% | -1.365 | 0.9139 | 1.0000 |
| S2 | primary | sensitivity_2x | 154 | 0.201% | 0.643 | -0.059% | -0.256 | 0.6009 | 1.0000 |
| S3 | primary | sensitivity_2x | 154 | -0.451% | -1.831 | -0.711% | -3.909 | 1.0000 | 1.0000 |
| S4 | primary | sensitivity_2x | 154 | 0.280% | 0.674 | 0.020% | 0.055 | 0.4780 | 1.0000 |
| S5 | primary | sensitivity_2x | 154 | 0.289% | 1.027 | 0.029% | 0.123 | 0.4510 | 1.0000 |
| S6 | primary | sensitivity_2x | 154 | 0.394% | 1.004 | 0.135% | 0.396 | 0.3462 | 1.0000 |
| S7 | primary | sensitivity_2x | 154 | 0.676% | 1.902 | 0.417% | 1.443 | 0.0745 | 1.0000 |
| S8 | primary | sensitivity_2x | 154 | 0.242% | 0.503 | -0.018% | -0.039 | 0.5154 | 1.0000 |
| family_a_baseline | primary | sensitivity_2x | 154 | 0.149% | 0.439 | -0.111% | -0.412 | 0.6598 | 1.0000 |
| S1 | last_close | primary | 154 | 0.322% | 0.993 | -0.067% | -0.269 | 0.6061 | 1.0000 |
| S2 | last_close | primary | 154 | 0.587% | 1.917 | 0.198% | 0.870 | 0.1921 | 1.0000 |
| S3 | last_close | primary | 154 | 0.103% | 0.414 | -0.286% | -1.636 | 0.9491 | 1.0000 |
| S4 | last_close | primary | 154 | 0.425% | 1.035 | 0.036% | 0.098 | 0.4611 | 1.0000 |
| S5 | last_close | primary | 154 | 0.472% | 1.633 | 0.083% | 0.353 | 0.3621 | 1.0000 |
| S6 | last_close | primary | 154 | 0.594% | 1.496 | 0.205% | 0.608 | 0.2716 | 1.0000 |
| S7 | last_close | primary | 154 | 0.903% | 2.536 | 0.514% | 1.773 | 0.0381 | 0.9699 |
| S8 | last_close | primary | 154 | 0.439% | 0.895 | 0.050% | 0.109 | 0.4568 | 1.0000 |
| family_a_baseline | last_close | primary | 154 | 0.422% | 1.235 | 0.033% | 0.124 | 0.4507 | 1.0000 |
| S1 | last_close | sensitivity_2x | 154 | -0.106% | -0.323 | -0.345% | -1.370 | 0.9147 | 1.0000 |
| S2 | last_close | sensitivity_2x | 154 | 0.180% | 0.579 | -0.059% | -0.257 | 0.6015 | 1.0000 |
| S3 | last_close | sensitivity_2x | 154 | -0.471% | -1.912 | -0.710% | -3.913 | 1.0000 | 1.0000 |
| S4 | last_close | sensitivity_2x | 154 | 0.264% | 0.636 | 0.025% | 0.067 | 0.4732 | 1.0000 |
| S5 | last_close | sensitivity_2x | 154 | 0.269% | 0.959 | 0.030% | 0.127 | 0.4496 | 1.0000 |
| S6 | last_close | sensitivity_2x | 154 | 0.370% | 0.941 | 0.131% | 0.384 | 0.3506 | 1.0000 |
| S7 | last_close | sensitivity_2x | 154 | 0.652% | 1.832 | 0.412% | 1.426 | 0.0770 | 1.0000 |
| S8 | last_close | sensitivity_2x | 154 | 0.218% | 0.451 | -0.022% | -0.047 | 0.5188 | 1.0000 |
| family_a_baseline | last_close | sensitivity_2x | 154 | 0.128% | 0.378 | -0.112% | -0.415 | 0.6608 | 1.0000 |

## Family A baseline

Over the confirm months the baseline is a member of the secondary family (above). Over the screen months 1963-07 to 1992-12 it runs with the screen cost schedule and the look's blank set. It is not in the freeze. Against CW-PIT and against vwretd:

| Loader run | Cost case | Months | Record | Mean vs CW-PIT | IR | HAC t | Mean gap vs vwretd | TE vs vwretd |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| primary | primary | 139 | ok | -0.331% | -0.777 | -2.531 | -0.452% | 0.470% |
| primary | sensitivity_2x | 139 | ok | -0.531% | -1.242 | -4.012 | -0.803% | 0.554% |
| last_close | primary | 139 | ok | -0.331% | -0.777 | -2.529 | -0.453% | 0.468% |
| last_close | sensitivity_2x | 139 | ok | -0.531% | -1.242 | -4.012 | -0.804% | 0.552% |

R4 fragility over the screen months: primary no sign flip; sensitivity_2x no sign flip.

## OI-09: CW-PIT against SPY

tilt - SPY = (tilt - CW-PIT) + (CW-PIT - SPY); the second term is replication error (dropped members, full against float cap, SPY's fee); both terms are reported. Annual means over the months with values of each stage:

| Stage | Loader run | Cost case | Months | CW-PIT - SPY | TE | Correlation | TILT - SPY | TILT - CW-PIT |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| confirm | primary | primary | 154 | 0.410% | 1.158% | 0.99686 | 0.298% | -0.112% |
| confirm | primary | sensitivity_2x | 154 | 0.260% | 1.170% | 0.99680 | -0.053% | -0.313% |
| confirm | last_close | primary | 154 | 0.389% | 1.154% | 0.99688 | 0.279% | -0.110% |
| confirm | last_close | sensitivity_2x | 154 | 0.239% | 1.166% | 0.99682 | -0.071% | -0.310% |
| check | primary | primary | 114 | 0.159% | 0.354% | 0.99967 | 0.484% | 0.324% |
| check | primary | sensitivity_2x | 114 | 0.138% | 0.356% | 0.99967 | 0.435% | 0.297% |
| check | last_close | primary | 114 | 0.154% | 0.354% | 0.99967 | 0.478% | 0.324% |
| check | last_close | sensitivity_2x | 114 | 0.133% | 0.356% | 0.99967 | 0.430% | 0.297% |

## Check stage

- `check_period_end`: 2025-11.
- Series months: 2014-04 to 2025-11, 114 months, 0 of them in `CHECK_GAP_MONTHS`.
- `check_gap_months` (left out of every check series): seal 2019-07, 2019-08, 2019-09, 2019-10, 2019-11, 2019-12, 2020-01, 2020-02, 2020-03, 2020-04, 2020-05, 2020-06, 2020-07; sealed_2020_07_31_row 2020-08; warm_up 2020-09, 2020-10, 2020-11, 2020-12, 2021-01, 2021-02, 2021-03, 2021-04, 2021-05, 2021-06, 2021-07, 2021-08.

Check means of every signal set (annual means over the check months with values):

| Signal set | Loader run | Cost case | Mean vs SPY | Mean vs CW-PIT |
| --- | --- | --- | --- | --- |
| composite | primary | primary | 0.484% | 0.324% |
| composite | primary | sensitivity_2x | 0.435% | 0.297% |
| composite | last_close | primary | 0.478% | 0.324% |
| composite | last_close | sensitivity_2x | 0.430% | 0.297% |
| S1 | primary | primary | 0.275% | 0.116% |
| S1 | primary | sensitivity_2x | 0.195% | 0.057% |
| S1 | last_close | primary | 0.268% | 0.115% |
| S1 | last_close | sensitivity_2x | 0.189% | 0.056% |
| S2 | primary | primary | 0.337% | 0.177% |
| S2 | primary | sensitivity_2x | 0.277% | 0.139% |
| S2 | last_close | primary | 0.331% | 0.177% |
| S2 | last_close | sensitivity_2x | 0.272% | 0.139% |
| S3 | primary | primary | 0.197% | 0.037% |
| S3 | primary | sensitivity_2x | 0.116% | -0.022% |
| S3 | last_close | primary | 0.192% | 0.038% |
| S3 | last_close | sensitivity_2x | 0.111% | -0.022% |
| S4 | primary | primary | 0.693% | 0.534% |
| S4 | primary | sensitivity_2x | 0.670% | 0.532% |
| S4 | last_close | primary | 0.687% | 0.533% |
| S4 | last_close | sensitivity_2x | 0.664% | 0.531% |
| S5 | primary | primary | 0.297% | 0.137% |
| S5 | primary | sensitivity_2x | 0.268% | 0.129% |
| S5 | last_close | primary | 0.293% | 0.139% |
| S5 | last_close | sensitivity_2x | 0.264% | 0.131% |
| S6 | primary | primary | 0.005% | -0.155% |
| S6 | primary | sensitivity_2x | -0.028% | -0.166% |
| S6 | last_close | primary | -0.003% | -0.157% |
| S6 | last_close | sensitivity_2x | -0.035% | -0.168% |
| S7 | primary | primary | 0.195% | 0.035% |
| S7 | primary | sensitivity_2x | 0.161% | 0.022% |
| S7 | last_close | primary | 0.189% | 0.035% |
| S7 | last_close | sensitivity_2x | 0.155% | 0.022% |
| S8 | primary | primary | -0.537% | -0.696% |
| S8 | primary | sensitivity_2x | -0.563% | -0.701% |
| S8 | last_close | primary | -0.542% | -0.695% |
| S8 | last_close | sensitivity_2x | -0.568% | -0.701% |
| family_a_baseline | primary | primary | -0.253% | -0.413% |
| family_a_baseline | primary | sensitivity_2x | -0.297% | -0.436% |
| family_a_baseline | last_close | primary | -0.260% | -0.414% |
| family_a_baseline | last_close | sensitivity_2x | -0.304% | -0.437% |

## Provenance

| Item | Value |
| --- | --- |
| Trial file | `docs/preregistrations/m55_trial_family_v1.json`, SHA-256 `e9b2e25b0f43164e29f0669765b92066a5196fe26fd14909a1f1dade866f7081` |
| Data vintage | 2025-12-31 |
| Manifest, first pull | `reports/wrds_manifest_2025.json`, SHA-256 `6dc96e69fdd6410fd5bcd41a00bddd0a2d91e54a2421e30efa06adacdf354e8f`, 151 main files, 15275872 main rows |
| Manifest, second pull quotes | `reports/wrds_quotes_manifest_2025.json`, SHA-256 `cedf4cb3d6f0035474afff359cd8bf795852a7b2b3a4999e53a7751b6fba8288`, 36 main files, 6556591 main rows |
| Data files SHA-256 (both pulls) | `83020d74aba9b1f79a8f5251da92cf6460780fe176296e5aa213cae68728ddd4` |
| Run 2 freeze digest (amendment 3) | `62b2c8afb379fb0322b03cbd68da47b71c68c9eb1d1172c805dcd11b00d59518` |
| Run 4 code | commit `e5ac840e6e04406683dc93879898d272c76aaa32`, code SHA-256 `af01de3e1b399f8e2a12099e5f525b6c71ff187a9b15c4e1735a1de1c982af0d` |
| Run 4 run log SHA-256 | `f8aee0302496b7d2a16c2f85f894d7a25ca1e30826bacdb7b3f3a401d4853f08` |
| Run 4 coverage.json | `9ad6b30d800f78be5f1acee76b79cebc183f70c8a627c6e9ab23a9ed03bbed9f` |
| Run 4 calibration.json | `67a7c56cb57e441bdf028b1ea46adee5283252899d74eb83b45026a127bb37b5` |
| Run 4 look.json | `be0c53290920d2f514fc84f64afaa8b6283da02a094d76c5014498eb73663b31` |
| Run 4 screen.json | `c648b3ed6e76fdfd5a0c450bae0394f9979d340cba63b7d664a1e7e3eeac89fe` |
| Run 4 freeze.json | `98ce15ce364006ea4af5549b864c5db9d9c4d8dc29a7937a2a08635b82db4b1e` |
| Run 4 confirm.json | `5645cf4eb251d53259ed76afac50a578caaf74b09b9180db413a21b12ed853b0` |
| Run 4 check.json | `ac8052e0e2f2bfadb0679348773f60d2287b6c97802c60558443e11cdb043850` |

Pinned files of run 4 (SHA-256):

| File | SHA-256 |
| --- | --- |
| `reports/wrds_manifest_2025.json` | `6dc96e69fdd6410fd5bcd41a00bddd0a2d91e54a2421e30efa06adacdf354e8f` |
| `research/m4_7_family_a.py` | `41df632629ee6f6344ba4a6b2f0158d8e031bd9a4f5c6ad499df24316d88d488` |
| `research/m55_criteria.py` | `5580b86f2037b50a864da01d6227cd9f08ddded4508577c4d7c1bd7570559623` |
| `research/m55_index_tilt.py` | `260e5dd047c48fb1d7ca520231ca9ddc09a68b5a45ffbdaf4556c5edc741d11c` |
| `research/m55_signals.py` | `60721018e16ed09acc13087efb9cec7b72369ba3a086f8e01506df0b638693b1` |
| `research/m55_wrds_loader.py` | `8756125b237f64cfb69b09a499bea28ad24637580357b919734bae61a72f6eff` |
| `src/backtest/portfolio.py` | `b4bf05d771ff64a8ccc7f91775c33339110b8663ae2159eac623ec1d82dd28af` |

## Costs

Confirm and check runs: from the first row, commission 5 and spread 20 bp; from 2001-04-01, commission 2 and spread 8 bp; from 2007-01-01, commission 1 and spread 4 bp (one way, per traded notional, commission + spread bp, dated). Every book pays the half-spread override: Confirm and check runs only, in every book (CW-PIT too), per stock and rebalance row r: a trade at row r pays a spread of scale x max(the spread of the dated schedule at r, the CRSP closing half-spread at r - 1), so the 2x case doubles the result; the commission stays per row, and on a halt-locked row the full row cost applies (H-3c). The half-spread is 10,000 x (ask - bid) / (ask + bid) in bp, from dlybid and dlyask of the PERMNO on the calendar row r - 1: the midpoint is the basis of the close that the engine trades at, and a locked quote gives 0. A cell is invalid for the first reason that applies: no_quote_row, quote_missing (both sides missing), quote_one_sided, quote_nonpositive (a side at 0 or below), quote_crossed (ask below bid). An invalid cell keeps its reason, pays the schedule spread, and is counted (R6). Days with dlyprcflg = 'BA' are valid (OI-11). No value is clipped. One-pull rule (amendment 3): the quote files are those of one run of coord/reports/m6_prep/wrds_pull_quotes.py (code_pins) into a folder named wrds_quotes_*, under the O-22 seal rule; a re-pull is a stop for the owner. reports/wrds_quotes_manifest_2025.json (file names, rows, SHA-256, and vintage; no row) is committed before run 3. The driver reads the quote main files only after it checks each one against that manifest. It refuses when the manifest is missing, when a hash or a row count differs, when the vintage is not data.vintage, when a path is under sealed/, when a quote row is dated in the seal window [2019-07-31, 2020-07-31), when a (PERMNO, date) repeats, and when a quote row has no main daily row of the first pull on (permno, dlycaldt). The quote file hashes enter data_files_sha256 in every stage context. The confirm run does not start before that pull.

Cost cases: primary x1, sensitivity_2x x2. Borrow: long only with fixed signal weights; no switch cost; no borrow cost (no shorts). The Family A baseline over the screen months uses the screen cost schedule with no override.

## Runs and attempts (R9)

Run 4 ran every stage again from coverage, on the code of amendment 4, into a new folder, as amendment 4 states. It froze `shortlist_frozen` with the shortlist S3, S4 and the run 2 digest. Attempts in the run log: written 7. `reports/m55_confirm_v1_attempts.jsonl` has one line per attempt of run 4, after the reference lines of run 1 and run 2 (`reports/m55_screen_v1_attempts.jsonl`) and of run 3. Run 3 wrote the stages coverage, calibration, look, screen, freeze, and its confirm stage refused (`unresolved_disappearance`), so it has no confirm or check file (see `docs/decision_log.md`, entry 'Trial Family v1 Amendment 4').

## Reports owed

Each item of design note section 5 is in the JSON under `stages.<stage>.segments.<segment>`, for every signal set, both loader runs, and both cost cases. The tables give the composite run.

fragility, confirm stage (a sign flip of an active annual mean against SPY or CW-PIT between the primary run and the last_close rerun, R4): none.

### Segment confirm

Months 1993-02 to 2014-03; anchor 1992-12-31, first rebalance 1993-01-29, end row 2014-03-31.

Blank months (`path_break_held`): primary 100 (share 0.3937); last_close 100 (share 0.3937). By year (primary run): 2003 10, 2004 12, 2005 12, 2006 10, 2007 11, 2008 12, 2009 12, 2010 12, 2011 9.

r4, CW-PIT held disappearances by cause (weights: total; the public weight rule gives weight sums for the CW-PIT book only):

| Loader run | Cost case | Held | Weight at the event, sum | Weight at the last rebalance, sum | By cause |
| --- | --- | --- | --- | --- | --- |
| primary | primary | 303 | 0.4004 | 0.3931 | cash_merger 78 (ciz_return_in_path 78); failure 8 (ciz_return_in_path 7, supplied_terminal_return 1); unknown 217 (ciz_return_in_path 216, missing_engine_default 1) |
| primary | sensitivity_2x | 303 | 0.4004 | 0.3931 | cash_merger 78 (ciz_return_in_path 78); failure 8 (ciz_return_in_path 7, supplied_terminal_return 1); unknown 217 (ciz_return_in_path 216, missing_engine_default 1) |
| last_close | primary | 320 | 0.4180 | 0.4137 | cash_merger 81 (settled_at_last_close 81); failure 8 (settled_at_last_close 8); unknown 231 (settled_at_last_close 231) |
| last_close | sensitivity_2x | 320 | 0.4180 | 0.4137 | cash_merger 81 (settled_at_last_close 81); failure 8 (settled_at_last_close 8); unknown 231 (settled_at_last_close 231) |

r4, composite TILT (counts only):

| Loader run | Cost case | Held | By cause |
| --- | --- | --- | --- |
| primary | primary | 303 | cash_merger 78 (ciz_return_in_path 78); failure 8 (ciz_return_in_path 7, supplied_terminal_return 1); unknown 217 (ciz_return_in_path 216, missing_engine_default 1) |
| primary | sensitivity_2x | 303 | cash_merger 78 (ciz_return_in_path 78); failure 8 (ciz_return_in_path 7, supplied_terminal_return 1); unknown 217 (ciz_return_in_path 216, missing_engine_default 1) |
| last_close | primary | 320 | cash_merger 81 (settled_at_last_close 81); failure 8 (settled_at_last_close 8); unknown 231 (settled_at_last_close 231) |
| last_close | sensitivity_2x | 320 | cash_merger 81 (settled_at_last_close 81); failure 8 (settled_at_last_close 8); unknown 231 (settled_at_last_close 231) |

path_break (aggregates only):

| Book set | Positions | Months blanked | CW weight sum | By later exit class | Span min / median / max |
| --- | --- | --- | --- | --- | --- |
| CW-PIT, primary | 2 | 100 | not given | left_index 1, unknown 1 | 44 / 50.0 / 56 |
| CW-PIT, last_close | 2 | 100 | not given | left_index 1, unknown 1 | 44 / 50.0 / 56 |
| composite, primary | 2 | 100 | not given | left_index 1, unknown 1 | 44 / 50.0 / 56 |
| composite, last_close | 2 | 100 | not given | left_index 1, unknown 1 | 44 / 50.0 / 56 |

Blanked level windows (R6), by later exit class:

| Loader run | Windows | current | left_index | cash_merger | failure | unknown |
| --- | --- | --- | --- | --- | --- | --- |
| primary | 0 | 0 | 0 | 0 | 0 | 0 |
| last_close | 0 | 0 | 0 | 0 | 0 | 0 |

exit_gap_events, the amendment 4 events (an index exit on a row without a close). Held means that CW-PIT holds the member at the last rebalance before the event. Again means a close, or eligibility, on a later row of the segment.

| Loader run | Events | By later exit class | Held | Held, by later exit class | Held CW weight sum | Priced again | Held and priced again | Eligible again | D6 left out |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| primary | 1 | unknown 1 | 1 | unknown 1 | not given | 0 | 0 | 0 | 0 |
| last_close | 1 | unknown 1 | 1 | unknown 1 | not given | 0 | 0 | 0 | 0 |

r6, pool cells by later exit class over the rebalances (cells; share of pool cells), primary loader run:

| Item | current | left_index | cash_merger | failure | unknown |
| --- | --- | --- | --- | --- | --- |
| pool cells | 56041 | 16195 | 19349 | 4770 | 31108 |
| ME missing, ambiguous | 0 (0.0000) | 0 (0.0000) | 0 (0.0000) | 0 (0.0000) | 0 (0.0000) |
| ME missing, multi_class | 0 (0.0000) | 0 (0.0000) | 0 (0.0000) | 0 (0.0000) | 0 (0.0000) |
| ME missing, no_share_fact | 79 (0.0014) | 39 (0.0024) | 44 (0.0023) | 11 (0.0023) | 123 (0.0040) |
| ME missing, stale_share_fact | 0 (0.0000) | 0 (0.0000) | 0 (0.0000) | 0 (0.0000) | 0 (0.0000) |
| ME missing, unmapped | 0 (0.0000) | 0 (0.0000) | 0 (0.0000) | 0 (0.0000) | 0 (0.0000) |
| unpriced | 0 (0.0000) | 0 (0.0000) | 0 (0.0000) | 0 (0.0000) | 0 (0.0000) |
| basis unseen | 0 (0.0000) | 0 (0.0000) | 0 (0.0000) | 0 (0.0000) | 0 (0.0000) |
| blanked windows | 0 (0.0000) | 0 (0.0000) | 0 (0.0000) | 0 (0.0000) | 0 (0.0000) |

counts and b2, composite run:

| Loader run | Rebalances | Members mean | Members min | Traded mean | Traded min | Pinned mean | c = 0 few signals | c = 0 short history | c = 0 window gap | ME missing | ME missing by reason | Settled excluded | Share at stock cap | Share TE-scaled | B2 rebalances / excluded |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| primary | 255 | 498.69 | 495 | 498.69 | 495 | 4.3 | 375 | 628 | 84 | 296 | no_share_fact 296 | 0 | 0.047 | 0.035 | 0 / 0 |
| last_close | 255 | 498.69 | 495 | 498.69 | 495 | 4.3 | 375 | 628 | 84 | 296 | no_share_fact 296 | 0 | 0.047 | 0.035 | 2 / 2 |

tilt_stats, composite (the JSON has the active turnover and cost drag per year):

| Loader run | Cost case | Realized TE (daily) | Worst relative drawdown | Size exposure mean | Turnover TILT | Turnover active | Cost drag TILT | Cost drag active |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| primary | primary | 0.86% | -2.92% | 0.026 | 0.877 | 0.562 | 0.238% | 0.139% |
| primary | sensitivity_2x | 0.87% | -3.75% | 0.026 | 0.877 | 0.562 | 0.477% | 0.278% |
| last_close | primary | 0.86% | -2.92% | 0.026 | 0.876 | 0.562 | 0.238% | 0.139% |
| last_close | sensitivity_2x | 0.87% | -3.72% | 0.026 | 0.876 | 0.562 | 0.476% | 0.278% |

post_publication_split, composite, primary loader run and cost (active months after and before each publication year of its signals):

| Publication year | Months after | Months before | Annual active mean after | Annual active mean before |
| --- | --- | --- | --- | --- |
| 1996 | 107 | 47 | -0.002% | -0.363% |
| 2013 | 3 | 151 | -0.552% | -0.104% |

half_spread, primary loader run and primary cost (shares of the year's traded notional; the band of the largest half-spread of a valid traded cell; the spread cost above the schedule as a share of book value; invalid traded cells):

| Book | Year | Valid share | CRSP binds share | BA share | Largest half-spread, bp | Cost above schedule | Invalid cells |
| --- | --- | --- | --- | --- | --- | --- | --- |
| TILT | 1993 | 0.9948 | 0.8292 | 0.0000 | 200 or more | 0.3547% | 32 |
| TILT | 1994 | 0.9941 | 0.8371 | 0.0000 | 200 or more | 0.2088% | 37 |
| TILT | 1995 | 0.9920 | 0.7626 | 0.0000 | 200 or more | 0.1584% | 28 |
| TILT | 1996 | 0.9918 | 0.7355 | 0.0000 | 200 or more | 0.1494% | 43 |
| TILT | 1997 | 0.9884 | 0.6522 | 0.0000 | 200 or more | 0.1205% | 76 |
| TILT | 1998 | 0.9903 | 0.6782 | 0.0001 | 200 or more | 0.1719% | 97 |
| TILT | 1999 | 0.9806 | 0.6895 | 0.0000 | 200 or more | 0.2528% | 127 |
| TILT | 2000 | 0.8913 | 0.5519 | 0.0001 | 200 or more | 0.3101% | 1102 |
| TILT | 2001 | 0.8870 | 0.6745 | 0.0000 | 200 or more | 0.2367% | 1288 |
| TILT | 2002 | 0.9807 | 0.7210 | 0.0000 | 200 or more | 0.1579% | 103 |
| TILT | 2003 | 0.9340 | 0.3335 | 0.0000 | 200 or more | 0.0406% | 287 |
| TILT | 2004 | 0.8795 | 0.0466 | 0.0000 | 50 to 100 | 0.0023% | 340 |
| TILT | 2005 | 0.9481 | 0.0712 | 0.0000 | 100 to 200 | 0.0053% | 198 |
| TILT | 2006 | 0.9745 | 0.0470 | 0.0000 | 50 to 100 | 0.0023% | 152 |
| TILT | 2007 | 0.9858 | 0.2727 | 0.0000 | 200 or more | 0.0147% | 77 |
| TILT | 2008 | 0.9909 | 0.3521 | 0.0000 | 200 or more | 0.0417% | 58 |
| TILT | 2009 | 0.9471 | 0.2564 | 0.0000 | 200 or more | 0.0095% | 147 |
| TILT | 2010 | 0.9949 | 0.0908 | 0.0000 | 20 to 50 | 0.0020% | 7 |
| TILT | 2011 | 0.9996 | 0.0386 | 0.0000 | 20 to 50 | 0.0010% | 3 |
| TILT | 2012 | 0.9996 | 0.0337 | 0.0000 | 20 to 50 | 0.0005% | 2 |
| TILT | 2013 | 1.0000 | 0.0138 | 0.0000 | 20 to 50 | 0.0002% | 0 |
| TILT | 2014 | 1.0000 | 0.0219 | 0.0000 | 10 to 20 | 0.0002% | 0 |
| CW-PIT | 1993 | 0.9943 | 0.8031 | 0.0000 | 200 or more | 0.2314% | 32 |
| CW-PIT | 1994 | 0.9864 | 0.8443 | 0.0000 | 200 or more | 0.0712% | 37 |
| CW-PIT | 1995 | 0.9873 | 0.7711 | 0.0000 | 200 or more | 0.0516% | 28 |
| CW-PIT | 1996 | 0.9847 | 0.7491 | 0.0000 | 200 or more | 0.0507% | 43 |
| CW-PIT | 1997 | 0.9785 | 0.6919 | 0.0000 | 200 or more | 0.0435% | 76 |
| CW-PIT | 1998 | 0.9870 | 0.7002 | 0.0003 | 200 or more | 0.0744% | 97 |
| CW-PIT | 1999 | 0.9672 | 0.6508 | 0.0000 | 200 or more | 0.1082% | 127 |
| CW-PIT | 2000 | 0.8747 | 0.4976 | 0.0001 | 200 or more | 0.1384% | 1102 |
| CW-PIT | 2001 | 0.8873 | 0.6743 | 0.0000 | 200 or more | 0.0884% | 1288 |
| CW-PIT | 2002 | 0.9803 | 0.7237 | 0.0000 | 200 or more | 0.0591% | 103 |
| CW-PIT | 2003 | 0.9008 | 0.3171 | 0.0000 | 200 or more | 0.0111% | 287 |
| CW-PIT | 2004 | 0.9422 | 0.0482 | 0.0000 | 50 to 100 | 0.0005% | 340 |
| CW-PIT | 2005 | 0.9514 | 0.0853 | 0.0000 | 100 to 200 | 0.0030% | 198 |
| CW-PIT | 2006 | 0.9740 | 0.0432 | 0.0000 | 50 to 100 | 0.0007% | 152 |
| CW-PIT | 2007 | 0.9886 | 0.2641 | 0.0000 | 200 or more | 0.0042% | 77 |
| CW-PIT | 2008 | 0.9881 | 0.4343 | 0.0000 | 200 or more | 0.0324% | 58 |
| CW-PIT | 2009 | 0.9535 | 0.2903 | 0.0000 | 200 or more | 0.0043% | 147 |
| CW-PIT | 2010 | 0.9977 | 0.1166 | 0.0000 | 20 to 50 | 0.0013% | 7 |
| CW-PIT | 2011 | 0.9999 | 0.0430 | 0.0000 | 20 to 50 | 0.0003% | 3 |
| CW-PIT | 2012 | 0.9999 | 0.0514 | 0.0000 | 20 to 50 | 0.0002% | 2 |
| CW-PIT | 2013 | 1.0000 | 0.0149 | 0.0000 | 20 to 50 | 0.0001% | 0 |
| CW-PIT | 2014 | 1.0000 | 0.0526 | 0.0000 | 10 to 20 | 0.0001% | 0 |

s2_short_history by year (share of S2 member cells typed `short_history`; mean ME percentile of S2 `short_history` and valid members):

| Year | short_history share | Mean ME percentile, short_history | Mean ME percentile, valid |
| --- | --- | --- | --- |
| 1993 | 0.0253 | 0.4333 | 0.4999 |
| 1994 | 0.0322 | 0.5662 | 0.4948 |
| 1995 | 0.0413 | 0.5728 | 0.4965 |
| 1996 | 0.0445 | 0.5149 | 0.4978 |
| 1997 | 0.0485 | 0.5044 | 0.5006 |
| 1998 | 0.0390 | 0.5433 | 0.4992 |
| 1999 | 0.0280 | 0.5258 | 0.5003 |
| 2000 | 0.0333 | 0.4541 | 0.5016 |
| 2001 | 0.0452 | 0.4186 | 0.5047 |
| 2002 | 0.0357 | 0.3579 | 0.5060 |
| 2003 | 0.0203 | 0.4672 | 0.5009 |
| 2004 | 0.0137 | 0.5857 | 0.4995 |
| 2005 | 0.0115 | 0.5805 | 0.4992 |
| 2006 | 0.0148 | 0.5788 | 0.5008 |
| 2007 | 0.0227 | 0.5026 | 0.5019 |
| 2008 | 0.0283 | 0.4854 | 0.5020 |
| 2009 | 0.0180 | 0.5342 | 0.5004 |
| 2010 | 0.0157 | 0.5547 | 0.5004 |
| 2011 | 0.0062 | 0.4613 | 0.5016 |
| 2012 | 0.0087 | 0.4337 | 0.5020 |
| 2013 | 0.0187 | 0.4296 | 0.5010 |
| 2014 | 0.0260 | 0.4701 | 0.5010 |

Stage confirm: `bid_ask_midpoint_share` 0.0000 of the member-days of its segments.

me_coverage, confirm stage, by later exit class (the JSON has each reason, by year, and the `basis_unseen` member-days by year):

| Class | Member days | Present days | Dollar volume share present |
| --- | --- | --- | --- |
| cash_merger | 406676 | 405625 | 0.997817 |
| current | 1174032 | 1172280 | 0.999161 |
| failure | 100462 | 100204 | 0.997963 |
| left_index | 339542 | 338687 | 0.997934 |
| unknown | 654256 | 651496 | 0.996969 |

`basis_unseen` member-days by year: data_start none; seal none.

fragility, check stage (a sign flip of an active annual mean against SPY or CW-PIT between the primary run and the last_close rerun, R4): S6 primary.

### Segment check_pre_seal

Months 2014-04 to 2019-06; anchor 2014-02-28, first rebalance 2014-03-31, end row 2019-06-28.

Blank months (`path_break_held`): primary 0 (share 0.0000); last_close 0 (share 0.0000). By year (primary run): none.

r4, CW-PIT held disappearances by cause (weights: total; the public weight rule gives weight sums for the CW-PIT book only):

| Loader run | Cost case | Held | Weight at the event, sum | Weight at the last rebalance, sum | By cause |
| --- | --- | --- | --- | --- | --- |
| primary | primary | 65 | 0.0829 | 0.0817 | cash_merger 24 (ciz_return_in_path 24); unknown 41 (ciz_return_in_path 41) |
| primary | sensitivity_2x | 65 | 0.0829 | 0.0817 | cash_merger 24 (ciz_return_in_path 24); unknown 41 (ciz_return_in_path 41) |
| last_close | primary | 69 | 0.0860 | 0.0853 | cash_merger 25 (settled_at_last_close 25); unknown 44 (settled_at_last_close 44) |
| last_close | sensitivity_2x | 69 | 0.0860 | 0.0853 | cash_merger 25 (settled_at_last_close 25); unknown 44 (settled_at_last_close 44) |

r4, composite TILT (counts only):

| Loader run | Cost case | Held | By cause |
| --- | --- | --- | --- |
| primary | primary | 65 | cash_merger 24 (ciz_return_in_path 24); unknown 41 (ciz_return_in_path 41) |
| primary | sensitivity_2x | 65 | cash_merger 24 (ciz_return_in_path 24); unknown 41 (ciz_return_in_path 41) |
| last_close | primary | 69 | cash_merger 25 (settled_at_last_close 25); unknown 44 (settled_at_last_close 44) |
| last_close | sensitivity_2x | 69 | cash_merger 25 (settled_at_last_close 25); unknown 44 (settled_at_last_close 44) |

path_break (aggregates only):

| Book set | Positions | Months blanked | CW weight sum | By later exit class | Span min / median / max |
| --- | --- | --- | --- | --- | --- |
| CW-PIT, primary | 0 | 0 | not given | none | none / none / none |
| CW-PIT, last_close | 0 | 0 | not given | none | none / none / none |
| composite, primary | 0 | 0 | not given | none | none / none / none |
| composite, last_close | 0 | 0 | not given | none | none / none / none |

Blanked level windows (R6), by later exit class:

| Loader run | Windows | current | left_index | cash_merger | failure | unknown |
| --- | --- | --- | --- | --- | --- | --- |
| primary | 0 | 0 | 0 | 0 | 0 | 0 |
| last_close | 0 | 0 | 0 | 0 | 0 | 0 |

exit_gap_events, the amendment 4 events (an index exit on a row without a close). Held means that CW-PIT holds the member at the last rebalance before the event. Again means a close, or eligibility, on a later row of the segment.

| Loader run | Events | By later exit class | Held | Held, by later exit class | Held CW weight sum | Priced again | Held and priced again | Eligible again | D6 left out |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| primary | 0 | none | 0 | none | not given | 0 | 0 | 0 | 0 |
| last_close | 0 | none | 0 | none | not given | 0 | 0 | 0 | 0 |

r6, pool cells by later exit class over the rebalances (cells; share of pool cells), primary loader run:

| Item | current | left_index | cash_merger | failure | unknown |
| --- | --- | --- | --- | --- | --- |
| pool cells | 22891 | 4577 | 1512 | 166 | 3104 |
| ME missing, ambiguous | 0 (0.0000) | 0 (0.0000) | 0 (0.0000) | 0 (0.0000) | 0 (0.0000) |
| ME missing, multi_class | 0 (0.0000) | 0 (0.0000) | 0 (0.0000) | 0 (0.0000) | 0 (0.0000) |
| ME missing, no_share_fact | 43 (0.0019) | 17 (0.0037) | 8 (0.0053) | 0 (0.0000) | 4 (0.0013) |
| ME missing, stale_share_fact | 0 (0.0000) | 0 (0.0000) | 0 (0.0000) | 0 (0.0000) | 0 (0.0000) |
| ME missing, unmapped | 0 (0.0000) | 0 (0.0000) | 0 (0.0000) | 0 (0.0000) | 1 (0.0003) |
| unpriced | 0 (0.0000) | 0 (0.0000) | 0 (0.0000) | 0 (0.0000) | 0 (0.0000) |
| basis unseen | 0 (0.0000) | 0 (0.0000) | 0 (0.0000) | 0 (0.0000) | 0 (0.0000) |
| blanked windows | 0 (0.0000) | 0 (0.0000) | 0 (0.0000) | 0 (0.0000) | 0 (0.0000) |

counts and b2, composite run:

| Loader run | Rebalances | Members mean | Members min | Traded mean | Traded min | Pinned mean | c = 0 few signals | c = 0 short history | c = 0 window gap | ME missing | ME missing by reason | Settled excluded | Share at stock cap | Share TE-scaled | B2 rebalances / excluded |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| primary | 64 | 502.77 | 497 | 502.77 | 497 | 7.2 | 324 | 116 | 24 | 73 | unmapped 1, no_share_fact 72 | 1 | 0.000 | 0.000 | 0 / 0 |
| last_close | 64 | 502.77 | 497 | 502.73 | 497 | 7.2 | 324 | 116 | 24 | 72 | no_share_fact 72 | 2 | 0.000 | 0.000 | 2 / 2 |

tilt_stats, composite (the JSON has the active turnover and cost drag per year):

| Loader run | Cost case | Realized TE (daily) | Worst relative drawdown | Size exposure mean | Turnover TILT | Turnover active | Cost drag TILT | Cost drag active |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| primary | primary | 0.57% | -0.95% | 0.031 | 0.954 | 0.562 | 0.048% | 0.028% |
| primary | sensitivity_2x | 0.57% | -0.98% | 0.031 | 0.954 | 0.562 | 0.096% | 0.056% |
| last_close | primary | 0.57% | -0.95% | 0.031 | 0.953 | 0.562 | 0.048% | 0.028% |
| last_close | sensitivity_2x | 0.57% | -0.98% | 0.031 | 0.953 | 0.562 | 0.096% | 0.056% |

post_publication_split, composite, primary loader run and cost (active months after and before each publication year of its signals):

| Publication year | Months after | Months before | Annual active mean after | Annual active mean before |
| --- | --- | --- | --- | --- |
| 1996 | 63 | 0 | 0.489% | none |
| 2013 | 63 | 0 | 0.489% | none |

half_spread, primary loader run and primary cost (shares of the year's traded notional; the band of the largest half-spread of a valid traded cell; the spread cost above the schedule as a share of book value; invalid traded cells):

| Book | Year | Valid share | CRSP binds share | BA share | Largest half-spread, bp | Cost above schedule | Invalid cells |
| --- | --- | --- | --- | --- | --- | --- | --- |
| TILT | 2014 | 1.0000 | 0.0045 | 0.0000 | 10 to 20 | 0.0001% | 0 |
| TILT | 2015 | 1.0000 | 0.0088 | 0.0000 | 10 to 20 | 0.0001% | 0 |
| TILT | 2016 | 1.0000 | 0.0147 | 0.0000 | 20 to 50 | 0.0002% | 0 |
| TILT | 2017 | 1.0000 | 0.0046 | 0.0000 | 20 to 50 | 0.0001% | 0 |
| TILT | 2018 | 1.0000 | 0.0053 | 0.0000 | 20 to 50 | 0.0001% | 1 |
| TILT | 2019 | 1.0000 | 0.0131 | 0.0000 | 5 to 10 | 0.0000% | 0 |
| CW-PIT | 2014 | 1.0000 | 0.0057 | 0.0000 | 10 to 20 | 0.0001% | 0 |
| CW-PIT | 2015 | 1.0000 | 0.0146 | 0.0000 | 10 to 20 | 0.0000% | 0 |
| CW-PIT | 2016 | 1.0000 | 0.0294 | 0.0000 | 20 to 50 | 0.0001% | 0 |
| CW-PIT | 2017 | 1.0000 | 0.0104 | 0.0000 | 20 to 50 | 0.0001% | 0 |
| CW-PIT | 2018 | 0.9999 | 0.0082 | 0.0000 | 20 to 50 | 0.0001% | 1 |
| CW-PIT | 2019 | 1.0000 | 0.0195 | 0.0000 | 5 to 10 | 0.0000% | 0 |

s2_short_history by year (share of S2 member cells typed `short_history`; mean ME percentile of S2 `short_history` and valid members):

| Year | short_history share | Mean ME percentile, short_history | Mean ME percentile, valid |
| --- | --- | --- | --- |
| 2014 | 0.0219 | 0.5087 | 0.5016 |
| 2015 | 0.0151 | 0.3866 | 0.5028 |
| 2016 | 0.0084 | 0.3220 | 0.5024 |
| 2017 | 0.0099 | 0.5791 | 0.5021 |
| 2018 | 0.0114 | 0.4275 | 0.5036 |
| 2019 | 0.0139 | 0.3327 | 0.5050 |

### Segment check_post_seal

Months 2021-09 to 2025-11; anchor 2021-07-30, first rebalance 2021-08-31, end row 2025-11-28.

Blank months (`path_break_held`): primary 0 (share 0.0000); last_close 0 (share 0.0000). By year (primary run): none.

r4, CW-PIT held disappearances by cause (weights: none; the public weight rule gives weight sums for the CW-PIT book only):

| Loader run | Cost case | Held | Weight at the event, sum | Weight at the last rebalance, sum | By cause |
| --- | --- | --- | --- | --- | --- |
| primary | primary | 26 | none | none | cash_merger 7 (ciz_return_in_path 7); failure 3 (ciz_return_in_path 1, missing_engine_default 2); unknown 16 (ciz_return_in_path 16) |
| primary | sensitivity_2x | 26 | none | none | cash_merger 7 (ciz_return_in_path 7); failure 3 (ciz_return_in_path 1, missing_engine_default 2); unknown 16 (ciz_return_in_path 16) |
| last_close | primary | 27 | none | none | cash_merger 7 (settled_at_last_close 7); failure 3 (settled_at_last_close 3); unknown 17 (settled_at_last_close 17) |
| last_close | sensitivity_2x | 27 | none | none | cash_merger 7 (settled_at_last_close 7); failure 3 (settled_at_last_close 3); unknown 17 (settled_at_last_close 17) |

r4, composite TILT (counts only):

| Loader run | Cost case | Held | By cause |
| --- | --- | --- | --- |
| primary | primary | 26 | cash_merger 7 (ciz_return_in_path 7); failure 3 (ciz_return_in_path 1, missing_engine_default 2); unknown 16 (ciz_return_in_path 16) |
| primary | sensitivity_2x | 26 | cash_merger 7 (ciz_return_in_path 7); failure 3 (ciz_return_in_path 1, missing_engine_default 2); unknown 16 (ciz_return_in_path 16) |
| last_close | primary | 27 | cash_merger 7 (settled_at_last_close 7); failure 3 (settled_at_last_close 3); unknown 17 (settled_at_last_close 17) |
| last_close | sensitivity_2x | 27 | cash_merger 7 (settled_at_last_close 7); failure 3 (settled_at_last_close 3); unknown 17 (settled_at_last_close 17) |

path_break (aggregates only):

| Book set | Positions | Months blanked | CW weight sum | By later exit class | Span min / median / max |
| --- | --- | --- | --- | --- | --- |
| CW-PIT, primary | 0 | 0 | not given | none | none / none / none |
| CW-PIT, last_close | 0 | 0 | not given | none | none / none / none |
| composite, primary | 0 | 0 | not given | none | none / none / none |
| composite, last_close | 0 | 0 | not given | none | none / none / none |

Blanked level windows (R6), by later exit class:

| Loader run | Windows | current | left_index | cash_merger | failure | unknown |
| --- | --- | --- | --- | --- | --- | --- |
| primary | 0 | 0 | 0 | 0 | 0 | 0 |
| last_close | 0 | 0 | 0 | 0 | 0 | 0 |

exit_gap_events, the amendment 4 events (an index exit on a row without a close). Held means that CW-PIT holds the member at the last rebalance before the event. Again means a close, or eligibility, on a later row of the segment.

| Loader run | Events | By later exit class | Held | Held, by later exit class | Held CW weight sum | Priced again | Held and priced again | Eligible again | D6 left out |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| primary | 0 | none | 0 | none | not given | 0 | 0 | 0 | 0 |
| last_close | 0 | none | 0 | none | not given | 0 | 0 | 0 | 0 |

r6, pool cells by later exit class over the rebalances (cells; share of pool cells), primary loader run:

| Item | current | left_index | cash_merger | failure | unknown |
| --- | --- | --- | --- | --- | --- |
| pool cells | 24134 | 1276 | 218 | 55 | 490 |
| ME missing, ambiguous | 0 (0.0000) | 0 (0.0000) | 0 (0.0000) | 0 (0.0000) | 0 (0.0000) |
| ME missing, multi_class | 0 (0.0000) | 0 (0.0000) | 0 (0.0000) | 0 (0.0000) | 0 (0.0000) |
| ME missing, no_share_fact | 34 (0.0014) | 6 (0.0047) | 0 (0.0000) | 0 (0.0000) | 0 (0.0000) |
| ME missing, stale_share_fact | 0 (0.0000) | 0 (0.0000) | 0 (0.0000) | 0 (0.0000) | 0 (0.0000) |
| ME missing, unmapped | 0 (0.0000) | 0 (0.0000) | 1 (0.0046) | 0 (0.0000) | 0 (0.0000) |
| unpriced | 0 (0.0000) | 0 (0.0000) | 0 (0.0000) | 0 (0.0000) | 0 (0.0000) |
| basis unseen | 0 (0.0000) | 0 (0.0000) | 0 (0.0000) | 0 (0.0000) | 0 (0.0000) |
| blanked windows | 0 (0.0000) | 0 (0.0000) | 0 (0.0000) | 0 (0.0000) | 0 (0.0000) |

counts and b2, composite run:

| Loader run | Rebalances | Members mean | Members min | Traded mean | Traded min | Pinned mean | c = 0 few signals | c = 0 short history | c = 0 window gap | ME missing | ME missing by reason | Settled excluded | Share at stock cap | Share TE-scaled | B2 rebalances / excluded |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| primary | 52 | 502.54 | 499 | 502.54 | 499 | 7.1 | 298 | 75 | 3 | 41 | unmapped 1, no_share_fact 40 | 0 | 0.000 | 0.000 | 0 / 0 |
| last_close | 52 | 502.54 | 499 | 502.50 | 499 | 7.1 | 298 | 75 | 3 | 40 | no_share_fact 40 | 1 | 0.000 | 0.000 | 2 / 2 |

tilt_stats, composite (the JSON has the active turnover and cost drag per year):

| Loader run | Cost case | Realized TE (daily) | Worst relative drawdown | Size exposure mean | Turnover TILT | Turnover active | Cost drag TILT | Cost drag active |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| primary | primary | 0.83% | -1.57% | 0.079 | 0.959 | 0.505 | 0.048% | 0.025% |
| primary | sensitivity_2x | 0.83% | -1.60% | 0.079 | 0.959 | 0.505 | 0.097% | 0.051% |
| last_close | primary | 0.83% | -1.57% | 0.079 | 0.959 | 0.505 | 0.048% | 0.025% |
| last_close | sensitivity_2x | 0.83% | -1.60% | 0.079 | 0.959 | 0.505 | 0.097% | 0.051% |

post_publication_split, composite, primary loader run and cost (active months after and before each publication year of its signals):

| Publication year | Months after | Months before | Annual active mean after | Annual active mean before |
| --- | --- | --- | --- | --- |
| 1996 | 51 | 0 | 0.121% | none |
| 2013 | 51 | 0 | 0.121% | none |

half_spread, primary loader run and primary cost (shares of the year's traded notional; the band of the largest half-spread of a valid traded cell; the spread cost above the schedule as a share of book value; invalid traded cells):

| Book | Year | Valid share | CRSP binds share | BA share | Largest half-spread, bp | Cost above schedule | Invalid cells |
| --- | --- | --- | --- | --- | --- | --- | --- |
| TILT | 2021 | 1.0000 | 0.0233 | 0.0000 | 10 to 20 | 0.0003% | 0 |
| TILT | 2022 | 1.0000 | 0.0348 | 0.0000 | 10 to 20 | 0.0006% | 0 |
| TILT | 2023 | 1.0000 | 0.0124 | 0.0000 | 10 to 20 | 0.0001% | 0 |
| TILT | 2024 | 1.0000 | 0.0434 | 0.0000 | 10 to 20 | 0.0005% | 0 |
| TILT | 2025 | 1.0000 | 0.0343 | 0.0000 | 20 to 50 | 0.0005% | 0 |
| CW-PIT | 2021 | 1.0000 | 0.0195 | 0.0000 | 10 to 20 | 0.0002% | 0 |
| CW-PIT | 2022 | 1.0000 | 0.0501 | 0.0000 | 10 to 20 | 0.0003% | 0 |
| CW-PIT | 2023 | 1.0000 | 0.0150 | 0.0000 | 10 to 20 | 0.0000% | 0 |
| CW-PIT | 2024 | 1.0000 | 0.0577 | 0.0000 | 10 to 20 | 0.0003% | 0 |
| CW-PIT | 2025 | 1.0000 | 0.0357 | 0.0000 | 20 to 50 | 0.0002% | 0 |

s2_short_history by year (share of S2 member cells typed `short_history`; mean ME percentile of S2 `short_history` and valid members):

| Year | short_history share | Mean ME percentile, short_history | Mean ME percentile, valid |
| --- | --- | --- | --- |
| 2021 | 0.5520 | 0.4705 | none |
| 2022 | 0.9836 | 0.5040 | none |
| 2023 | 0.3267 | 0.5132 | 0.4965 |
| 2024 | 0.0073 | 0.4998 | 0.5024 |
| 2025 | 0.0081 | 0.4569 | 0.5028 |

Stage check: `bid_ask_midpoint_share` 0.0000 of the member-days of its segments.

me_coverage, check stage, by later exit class (the JSON has each reason, by year, and the `basis_unseen` member-days by year):

| Class | Member days | Present days | Dollar volume share present |
| --- | --- | --- | --- |
| cash_merger | 36565 | 36334 | 0.997665 |
| current | 983540 | 981824 | 0.998750 |
| failure | 4669 | 4662 | 1.000000 |
| left_index | 123303 | 122774 | 0.996725 |
| unknown | 75948 | 75807 | 0.998798 |

`basis_unseen` member-days by year: data_start none; seal none.

### s2_history_rule (check stage)

S2 member quarters with rdq before 2020-08-03 and a known date on or after it (no S2 value): 2020 165. S2 cells typed `split_in_basis_window` by year: 2016 4, 2017 3, 2019 5, 2023 3, 2024 6, 2025 5.

S2 valid share by post-seal check month: 2021-09 0.000, 2021-10 0.000, 2021-11 0.000, 2021-12 0.000, 2022-01 0.000, 2022-02 0.000, 2022-03 0.000, 2022-04 0.000, 2022-05 0.000, 2022-06 0.000, 2022-07 0.000, 2022-08 0.000, 2022-09 0.000, 2022-10 0.000, 2022-11 0.000, 2022-12 0.000, 2023-01 0.000, 2023-02 0.004, 2023-03 0.205, 2023-04 0.366, 2023-05 0.477, 2023-06 0.974, 2023-07 0.978, 2023-08 0.978, 2023-09 0.980, 2023-10 0.980, 2023-11 0.980, 2023-12 0.980, 2024-01 0.980, 2024-02 0.980, 2024-03 0.978, 2024-04 0.976, 2024-05 0.972, 2024-06 0.972, 2024-07 0.976, 2024-08 0.974, 2024-09 0.972, 2024-10 0.972, 2024-11 0.970, 2024-12 0.972, 2025-01 0.974, 2025-02 0.976, 2025-03 0.976, 2025-04 0.974, 2025-05 0.974, 2025-06 0.976, 2025-07 0.978, 2025-08 0.978, 2025-09 0.980, 2025-10 0.978, 2025-11 0.976.

## Withheld values

- `attempts.detail`: The detail text of each refusal or error. It can name a date of one position or a private path, so it stays in the private run log (its SHA-256 is in the provenance).
- `b2.each`: The trial asks for unknown_event_excluded and unknown_event_cw_share at each rebalance. The report gives aggregates only (owner data terms O-22).
- `b2.max_cw_share`: The largest CW share excluded at one rebalance. The report does not give it: private per O-22 (public weight rule, 2026-10-08). The value stays in the private stage files.
- `exit_gap.check.check_post_seal.held_cw_weight_sum`: The CW-PIT weight sum of the amendment 4 events that CW-PIT holds. A loader run holds fewer than 3 of them, or this sum and another published sum (of the other loader run, or an R4 sum of the segment) can differ by fewer than 3 positions. The report does not give it: private per O-22 (public weight rule, 2026-10-08). The value stays in the private stage files.
- `exit_gap.check.check_pre_seal.held_cw_weight_sum`: The CW-PIT weight sum of the amendment 4 events that CW-PIT holds. A loader run holds fewer than 3 of them, or this sum and another published sum (of the other loader run, or an R4 sum of the segment) can differ by fewer than 3 positions. The report does not give it: private per O-22 (public weight rule, 2026-10-08). The value stays in the private stage files.
- `exit_gap.confirm.confirm.held_cw_weight_sum`: The CW-PIT weight sum of the amendment 4 events that CW-PIT holds. A loader run holds fewer than 3 of them, or this sum and another published sum (of the other loader run, or an R4 sum of the segment) can differ by fewer than 3 positions. The report does not give it: private per O-22 (public weight rule, 2026-10-08). The value stays in the private stage files.
- `half_spread.max_half_spread`: The largest half-spread of a traded cell, a quote value. With its book and year, an exact value can single out one security and day in the CRSP quotes, so the report gives its band in bp (`costs.half_spread_bands_bp`).
- `half_spread.tilt.other_cells`: The half-spread tables of the S1 to S8 and Family A TILT books in the last_close run and in the 2x cost case. The report gives the decision cell of these books and every cell of the composite TILT and CW-PIT, to keep the file size small. The tables stay in the private stage files.
- `half_spread.traded_notional`: The traded notional of each book and year, and the notional by quote status. A quote status or a binding group can hold one or two traded cells. The report gives shares of the year's traded notional instead, and no figure that gives the year's traded notional. The report does not give it: private per O-22 (public weight rule, 2026-10-08). The value stays in the private stage files.
- `path_break.check.check_post_seal.weight_sum`: The CW-PIT weight sum of the path-break positions. The report does not give it: private per O-22 (public weight rule, 2026-10-08). The value stays in the private stage files.
- `path_break.check.check_pre_seal.weight_sum`: The CW-PIT weight sum of the path-break positions. The report does not give it: private per O-22 (public weight rule, 2026-10-08). The value stays in the private stage files.
- `path_break.confirm.confirm.weight_sum`: The CW-PIT weight sum of the path-break positions. The report does not give it: private per O-22 (public weight rule, 2026-10-08). The value stays in the private stage files.
- `path_break.cw_weight_by_exit_class`: The CW weight of the path-break positions by later exit class. The report does not give it: private per O-22 (public weight rule, 2026-10-08). The value stays in the private stage files.
- `path_break.positions`: The trial asks for each held position with its weight in each book. The report gives aggregates only (owner data terms O-22).
- `path_break.sets.weight_sum`: The weight sums of each signal set's books. The report does not give it: private per O-22 (public weight rule, 2026-10-08). The value stays in the private stage files.
- `r4.check.check_post_seal.by_cause.weight_at_last_rebalance_sum`: The CW-PIT weight of each cause. At least one cause does not meet the rule, or two loader runs have equal counts of a cause, which the stage files cannot show to be the same events. The report does not give it: private per O-22 (public weight rule, 2026-10-08). The value stays in the private stage files.
- `r4.check.check_post_seal.weight_at_last_rebalance_sum`: The CW-PIT total over causes. The report does not give it: private per O-22 (public weight rule, 2026-10-08). The value stays in the private stage files.
- `r4.check.check_pre_seal.by_cause.weight_at_last_rebalance_sum`: The CW-PIT weight of each cause. At least one cause does not meet the rule, or two loader runs have equal counts of a cause, which the stage files cannot show to be the same events. The report does not give it: private per O-22 (public weight rule, 2026-10-08). The value stays in the private stage files.
- `r4.confirm.confirm.by_cause.weight_at_last_rebalance_sum`: The CW-PIT weight of each cause. At least one cause does not meet the rule, or two loader runs have equal counts of a cause, which the stage files cannot show to be the same events. The report does not give it: private per O-22 (public weight rule, 2026-10-08). The value stays in the private stage files.
- `r4.incoming_weight_max`: The largest book weight at one event. The report does not give it: private per O-22 (public weight rule, 2026-10-08). The value stays in the private stage files.
- `r4.tilt.weights`: The weight sums of each signal set's TILT book. Each group nests in the CW-PIT group of its segment and loader run, so a difference can isolate one event. The report does not give it: private per O-22 (public weight rule, 2026-10-08). The value stays in the private stage files.
- `tilt_stats.turnover_by_year`: The per-year turnover and cost drag of the TILT and CW-PIT books. With them, a half-spread notional share gives a weight sum. The report gives the active book per year (the trial's 'active turnover and cost drag per year') and the full-segment figures of each book. The report does not give it: private per O-22 (public weight rule, 2026-10-08). The value stays in the private stage files.

# Milestone 5 Owner Report: What the Factor-Class Allocator Found

**Evidence ceiling: `DIAGNOSTIC_ONLY`.** Simulated research only, with no orders and no trading. This report computes
nothing new: every number is quoted from a committed report, record, or file, which is named beside it. Nothing here
is a profitability claim or investment advice.

## The Answer

**No rule that we tested beat SPY after costs on our point-in-time S&P 500 books. Milestone 6 does not start on this
allocator.**

On our own point-in-time S&P 500 books, after costs, the declared decision rules keep R0 as the baseline. R0 holds
six price-and-volume stock sleeves in equal shares. On average it trailed SPY by 4.61 percentage points a year in
2014-12 to 2019-06 and by 9.73 points a year in 2022-05 to 2025-12 (annualized mean monthly excess). It also trailed a
cost-free, equal-weight book of all priced index members, by 1.55 and 2.86 points a year (`reports/m5_step4.md`). Rule
R1 trailed SPY by 5.02 and 9.99 points a year, and the timing tilt R2 by 4.97 and 9.73 points
(`reports/m5_step4.json`, `runs.primary.excess`). With the SEC value and quality classes added, R0 over nine sleeves
came closer to SPY, at 4.43 and 8.58 points a year behind, but it did not pass the joining test (2 of 8 conditions,
BY q 1.0000; `reports/m5_step4b.md`). Timing by market conditions gave no reason to change R0. The search for new
factors (step 5) was deferred before any result (O-11).

Read this answer with four limits:

- **No test against SPY.** The trial file reports the gap to SPY but declares no test of it; the only stock-book tests
  compare one rule or book with another (S4.R1, S4.R2, and S4b.ADD). So the gap has no p-value or q-value
  (`docs/preregistrations/m5_trial_family_v1_amendment_4.json`, `benchmarks` and `step4_tests`;
  `docs/preregistrations/m5_trial_family_v1_amendment_5.json`, `step4b_tests`).
- **The size of the gap depends on the disappearance rule.** The main run settles each held stock that disappears at
  -100 percent. In the rerun that settles it at its last close, R0 trailed SPY by 1.60 and 8.39 points a year, and the
  equal-weight book by 0.33 and 2.66 points (`reports/m5_step4.json`, `runs.last_close.excess`, `R0|primary`). The
  sign does not change.
- **Most of the gap to SPY lies between the equal-weight book and SPY, and it is not only weighting.** The
  equal-weight book uses no factor and no cost. It made 7.35 and 9.53 percent a year, against 10.41 and 16.41 percent
  for SPY (`reports/m5_step4.md`). That gap mixes equal against cap weight with the -100 percent default and the
  unpriced members, which affect the equal-weight book but not SPY. In the last-close rerun the equal-weight book made
  9.14 and 10.68 percent a year against the same SPY figures (`reports/m5_step4.json`, `runs.last_close.benchmarks`,
  comparison months). Read side by side, these figures show that in 2014-2019 most of that gap moves with the
  disappearance default, and in 2022-2025 most of it remains. The gap between R0 and the equal-weight book measures
  the factor sleeves, the rule, and their costs together.
- **Not every rule was compared with SPY.** Only R0, rule R1, and R2 on the six price sleeves, and R0 and rule R1 on
  nine sleeves with the SEC classes (with the mapped-universe R0 as a diagnostic book), were compared with SPY
  (`reports/m5_step4.md`, `reports/m5_step4b.md`). The factor momentum tilt (rule R3) and the pooled ridge (rule R4)
  ran only on public data, and factor discovery (step 5) never ran. Single sleeves are not rules and carry no test.
  Their gaps to SPY are reported over sleeve months, not comparison months, and a few are above SPY in the
  last-close rerun (`reports/m5_step4.json` and `reports/m5_step4b.json`, `runs.last_close.excess`).

This wording replaces the O-12 sentence "At this evidence ceiling, no rule beats an index fund"; the owner approved
the change in O-16 (`docs/decision_log.md`).

## What We Tested, in Plain Words

0. **How the rules get their numbers.** No factor was invented or fitted. The signals are repository versions of
   published definitions (`research/factor_catalog.csv`; the SEC signals in amendment 5). R0 has no parameter. Rule R1
   uses each input's trailing volatility: 36 months on public factors, 126 trading days on stock sleeves. R2 uses past
   class returns in each market state, from history that grows each month. Rule R4 is the only fitted model: a ridge
   regression refit once a year on all months up to the prior November. Every estimate uses past data only, in one
   walk-forward pass, with two exceptions: the JKP class map comes from full-sample correlations (hindsight), and
   early R2 lookback years carry Compustat backfill bias (`reports/m5_step3.md`, Limitations). R2's multipliers come
   from public long-short data and are not re-estimated on stock books
   (`docs/preregistrations/m5_trial_family_v1.json`, `rules`;
   `docs/preregistrations/m5_trial_family_v1_amendment_3.json`, `rules`; `reports/m5_step4.md`, Limitations).
1. **Public factor data, 1972 to 2025** (`reports/m5_factor_baseline.md`). These are long-short academic factor series
   (JKP, 153 factors), gross of the factors' own trading and borrowing costs, and they include small caps.
   - Holding every factor sized by its recent risk (rule R1) met 8 of 8 declared conditions against holding them in
     equal amounts on public data. The 8 conditions decide the baseline; the q-value below does not change it.
   - R1 made 2.27 percent a year against 2.57 percent for equal amounts, but with a much smaller worst loss (-7.27
     against -13.97 percent). The difference in mean return is not significant (HAC p 0.12, BY q 0.32).
   - These figures use the full factor list, which has hindsight in it: the months before each paper was published
     were in the authors' own samples. The coordinator also saw similar comparisons before the trial file was written
     (`reports/m5_factor_baseline.md`, Read This First and Limitations). In the declared post-publication check, R1
     made 0.79 percent a year with a worst loss of -50.62 percent, and R0 1.11 percent with -50.88 percent. Both worst
     losses fall in 1972-1999, when the set of published factors was thin and changing
     (`reports/m5_factor_baseline.md`, post-publication section).
2. **Timing by market conditions** (`reports/m5_step3.md`). We tilted toward factors by market trend, market
   volatility, and credit spread, which are known at the time.
   - The tilt (R2) earned 0.23 bp a month less than R1 (HAC p 0.38, BY q 1, random-date p 0.32). It met all 8
     closure conditions against R1, so it went on to step 4 labeled "no evidence of state timing".
   - None of the 39 factor-class and market-state cells survived. There is no evidence of timing skill.
   - We also tested a factor momentum tilt (rule R3: +2.08 bp a month against R1, HAC p 0.222, BY q 1, 4 of 8
     conditions) and a pooled ridge forecast (rule R4: -0.53 bp, HAC p 0.059, BY q 1, 1 of 8). Neither qualified, and
     neither ran on stock books.
3. **Real stock books** (`reports/m5_step4.md`). We bought the top 20 percent of S&P 500 members on each price signal,
   using point-in-time membership.
   - The six sleeves are momentum, 52-week high, one-month reversal, low volatility, low beta, and illiquidity.
   - On stock books R0 is the baseline: rule R1 (here with a 126-day volatility window) met only 4 of 8 conditions
     against R0 (S4.R1, R1 minus R0: HAC p 0.193, BY q 1.000). The timing tilt was closed: it met 6 of 8 conditions
     against rule R1 and 3 of 8 against R0 (S4.R2, R2 minus R1: +0.01 percent a month, HAC p 0.352, BY q 1.000).
   - R0's annual net return was 5.80 percent in the earlier period and 6.68 percent in the later one. SPY made 10.41
     and 16.41 percent, and the equal-weight book 7.35 and 9.53 percent, over the same months.
   - R0's worst loss was -11.99 and -13.04 percent. SPY's was -13.53 and -12.95 percent.
4. **Accounting data** (`reports/m5_step4b_data.md`, `reports/m5_step4b.md`). We built value and quality classes from
   SEC filings as first filed, mapping 563 of 632 eligible securities to a company filer.
   - Adding them to R0 met 2 of 8 conditions, at +0.051 percent a month (HAC p 0.42, BY q 1.0). They do not join.
   - The nine-sleeve R0 trailed SPY by 4.43 and 8.58 points a year (`reports/m5_step4b.md`, Benchmarks).
5. **Discovery** (`docs/decision_log.md`, O-11). This step was deferred before any result. Under the step 5 plan
   (screen on 55 months, confirm on 44), a rough check put the needed gain of one new sleeve at about 0.6 percent a
   month for p 0.05, and about 0.9 percent after BY over 10 candidates.

## How the Numbers Were Made

Sources for this section: `reports/m5_step4.md` (Method and Provenance, Windows) and
`docs/preregistrations/m5_trial_family_v1_amendment_4.json`, unless another file is named.

- **Timing:** each signal uses data through the prior trading day (row r - 1). The trade executes at the close of the
  rebalance day and first earns the next day's return. Class weights for month t use inputs through month t-2 (the
  credit spread through t-3).
- **Costs:** 1 bp transaction cost plus 4 bp slippage on stock trades, and a 20 bp switch cost on moves between
  classes. A sensitivity case doubles the stock costs and uses a 50 bp switch cost. There is no market-impact model,
  and no position is short, so no borrow cost applies. The benchmarks carry no cost.
- **Benchmarks:** SPY and the equal-weight point-in-time book. A cheap factor-ETF blend is named in the North Star
  (`docs/north_star.md`), but no ETF data source is authorized (an owner item), so it is missing
  (`docs/decision_log.md`, O-12).
- **Data:** a private local EODHD snapshot (`real_v2`, last book row 2026-08-07, `research/m5_step4.py` segment dates)
  for stock books; JKP, French, and FRED public files (`reports/m5_public_data_manifest.json`); SEC EDGAR filings
  (`reports/m5_step4b_data.md`). Raw rows stay private; the repository holds aggregates and hashes.

## Limitations That Matter

- **Missing prices.** 27.83 percent of member-days in the earlier segment (2014-04 to 2019-06) and 15.72 percent in
  the later segment (2021-08 to 2026-08) have no price and are never held (`reports/m5_step4.md`; segment dates from
  `research/m5_step4.py`, `SEGMENT_DATES`). 71.8 percent of the early ones are in the exit class
  `index_removal_still_trading` (`reports/m5_step4.md`). Despite its name, this class means "still trading at the
  end of the data" and includes current members (`research/m4_7_universe_build.py`, `exit_class`). So the effect of
  these members on the reported levels is not known.
- **Missing crash.** The sealed window and its buffers remove 2019-07 to 2021-08, including the 2020 crash, from the
  stock books (`reports/m5_step4.md`). The stock-book drawdowns above are therefore too mild.
- **Delistings.** No terminal evidence is accepted, so any held stock that disappears counts as a total loss. The
  equal-weight book uses the same rule; SPY does not. Over the comparison months of the R0 book this affected 26
  unique disappearance events (61 incidences, incoming weight sum 0.1384) in the earlier segment and 14 (25
  incidences, 0.0492) in the later one. A weight sum adds across events; it is not one portfolio weight at one time
  (`reports/m5_step4.md`, R4 Affected Events, where R4 is the disappearance invariant, not rule R4). A rerun at the
  last close changes no decision, but it makes the gaps smaller (see The Answer). Step 4 is labeled fragile: three
  Sharpe margins change sign, and no decision changes (`reports/m5_step4.md`).
- **Distributions.** We accept the vendor's adjusted close as including each dividend (premise VP-2, owner decision
  O-9). The M4.7 coverage census on `real_v1` flagged 22.5 percent of eligible member-days as exposed to this premise
  (`S_D` above 0.05; `reports/m4_7_coverage_census.md`, and the O-3 Option A entry for the M4.7a-3 run in
  `docs/decision_log.md`).
- **Sample reuse.** The later stock segment re-examines Milestone 4.7 factors and months, and the earlier segment
  overlaps Milestone 4.7 checks from 2016-08; only 2014-05 to 2016-07 is unexposed
  (`docs/preregistrations/m5_trial_family_v1_amendment_4.json`, limitations). No stock-level result here is
  confirmatory (`reports/m5_step4.md`). The public-factor comparisons in steps 2 and 3 also look again at history seen
  before the trial file (`reports/m5_factor_baseline.md`, `reports/m5_step3.md`).
- **Short history.** 99 comparison months of stock data can detect only large differences (`reports/m5_step4.md`,
  Limitations).

## What Comes Next

- **Freeze.** R0 will be frozen in a dated file, so no one can tune it later. Two formal
  review seats from different model families review the freeze, the AGENTS.md gate for a trial-family freeze
  (coordinator default; `docs/current_roadmap.md`, step 6 status).
- **No seal look.** The sealed window from 2019-07-31 up to (not including) 2020-07-31 stays closed. It is kept for a
  future candidate with a real edge, or for the later M4.8 stages (O-12).
- **No forward observation.** No price or membership data after August 2026 will be bought or used. Forward
  observation needs a new owner decision on data and money (O-12).
- **Next line of work: open.** The owner will decide after this report.

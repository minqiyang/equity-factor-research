# Milestone 5 Owner Report: What the Factor-Class Allocator Found

**Evidence ceiling: `DIAGNOSTIC_ONLY`.** Simulated research only, with no orders and no trading. This report computes
nothing new: every number is quoted from a committed report, record, or file, which is named beside it. Nothing here
is a profitability claim or investment advice.

## The Answer

**No rule that we tested beat SPY after costs on our point-in-time S&P 500 books. Milestone 6 does not start on this
allocator.**

On our own point-in-time S&P 500 books, after costs, the best rule we have is R0. R0 holds six price-based stock
sleeves in equal shares. It trailed SPY by 4.61 percent a year in 2014-12 to 2019-06 and by 9.73 percent a year in
2022-05 to 2025-12. It also trailed an equal-weight book of the same stocks, by 1.55 and 2.86 percent a year
(`reports/m5_step4.md`). Rule R1 trailed SPY by 5.02 and 9.99 percent a year, and the timing tilt R2 by 4.97 and 9.73
percent (`reports/m5_step4.json`, `runs.primary.excess`). Timing by market conditions and accounting-based value and
quality classes gave no reason to change R0. The search for new factors was deferred before any result (O-11).

Read this answer with four limits:

- **No test against SPY.** The trial file declared no test against SPY, so the gap to SPY has no p-value or q-value.
  It is a reported number (`docs/preregistrations/m5_trial_family_v1_amendment_4.json`, `benchmarks`;
  `reports/m5_step4.md`, S4 Tests).
- **The size of the gap depends on the disappearance rule.** The main run settles each held stock that disappears at
  -100 percent. In the rerun that settles it at its last close, R0 trailed SPY by 1.60 and 8.39 percent a year, and the
  equal-weight book by 0.33 and 2.66 percent (`reports/m5_step4.json`, `runs.last_close.excess`, `R0|primary`). The
  sign does not change.
- **Most of the gap to SPY is equal weight against cap weight.** The equal-weight book uses no rule. It made 7.35 and
  9.53 percent a year, against 10.41 and 16.41 percent for SPY (`reports/m5_step4.md`). The gap between R0 and the
  equal-weight book measures the rules themselves, and it is smaller.
- **Not every rule met SPY.** Only R0, rule R1, and R2 on the six price sleeves, and R0 and rule R1 on nine sleeves
  with the SEC classes, were compared with SPY (`reports/m5_step4.md`, `reports/m5_step4b.md`). The factor momentum
  tilt (R3), the pooled ridge (R4), and factor discovery never ran on stock books.

This wording replaces the O-12 sentence "At this evidence ceiling, no rule beats an index fund"; the owner approved
the change in O-16 (`docs/decision_log.md`).

## What We Tested, in Plain Words

1. **Public factor data, 1972 to 2025** (`reports/m5_factor_baseline.md`). These are long-short academic factor series
   (JKP, 153 factors), gross of the factors' own trading and borrowing costs, and they include small caps.
   - Holding every factor sized by its recent risk (rule R1) met 8 of 8 declared conditions against holding them in
     equal amounts. The 8 conditions decide the baseline; the q-value below does not change it.
   - R1 made 2.27 percent a year against 2.57 percent for equal amounts, but with a much smaller worst loss (-7.27
     against -13.97 percent). The difference in mean return is not significant (HAC p 0.12, BY q 0.32).
   - These figures use the full factor list, which has hindsight in it: the months before each paper was published
     were in the authors' own samples. The coordinator also saw similar comparisons before the trial file was written
     (`reports/m5_factor_baseline.md`, Limitations). In the declared post-publication check, R1 made 0.79 percent a
     year with a worst loss of -50.62 percent, on a set of factors that is thin and changes in the early years
     (`reports/m5_factor_baseline.md`, post-publication section).
2. **Timing by market conditions** (`reports/m5_step3.md`). We tilted toward factors by market trend, market
   volatility, and credit spread, which are known at the time.
   - The tilt earned 0.23 bp a month less than R1 (HAC p 0.38, BY q 1, random-date p 0.32).
   - None of the 39 factor-class and market-state cells survived. There is no evidence of timing skill.
3. **Real stock books** (`reports/m5_step4.md`). We bought the top 20 percent of S&P 500 members on each price signal,
   using point-in-time membership.
   - The six sleeves are momentum, 52-week high, one-month reversal, low volatility, low beta, and illiquidity.
   - Equal shares (R0) stay the baseline: rule R1 met only 4 of 8 conditions against R0 (S4.R1: HAC p 0.193, BY q
     1.000). The timing tilt was closed (S4.R2: HAC p 0.352, BY q 1.000).
   - R0's annual net return was 5.80 percent in the earlier period and 6.68 percent in the later one. SPY made 10.41
     and 16.41 percent, and the equal-weight book 7.35 and 9.53 percent, over the same months.
   - R0's worst loss was -11.99 and -13.04 percent. SPY's was -13.53 and -12.95 percent.
4. **Accounting data** (`reports/m5_step4b_data.md`, `reports/m5_step4b.md`). We built value and quality classes from
   SEC filings as first filed, mapping 563 of 632 companies.
   - Adding them to R0 met 2 of 8 conditions, at +0.051 percent a month (HAC p 0.42, BY q 1.0). They do not join.
   - The nine-sleeve R0 trailed SPY by 4.43 and 8.58 percent a year (`reports/m5_step4b.md`, Benchmarks).
5. **Discovery** (`docs/decision_log.md`, O-11). This step was deferred before any result. One new sleeve would need
   to add about 0.6 to 0.9 percent a month to be detectable with the stock history we have.

## How the Numbers Were Made

Sources for this section: `reports/m5_step4.md` (Method and Provenance, Windows) and
`docs/preregistrations/m5_trial_family_v1_amendment_4.json`, unless another file is named.

- **Timing:** each signal uses data through the prior trading day (row r - 1). The trade executes at the close of the
  rebalance day and first earns the next day's return. Class weights for month t use returns through month t-2.
- **Costs:** 1 bp commission plus 4 bp spread on stock trades, and a 20 bp switch cost on moves between classes. A
  sensitivity case doubles the stock costs and uses a 50 bp switch cost. There is no market-impact model, and no
  position is short, so no borrow cost applies. The benchmarks carry no cost.
- **Benchmarks:** SPY and the equal-weight point-in-time book. A cheap factor-ETF blend is named in the North Star
  (`docs/north_star.md`), but we have no source for it, so it is missing (`docs/decision_log.md`, O-12).
- **Data:** a private local EODHD snapshot (`real_v2`, last book row 2026-08-07, `research/m5_step4.py` segment dates)
  for stock books; JKP, French, and FRED public files (`reports/m5_public_data_manifest.json`); SEC EDGAR filings
  (`reports/m5_step4b_data.md`). Raw rows stay private; the repository holds aggregates and hashes.

## Limitations That Matter

- **Missing prices.** 27.83 percent of member-days in the earlier segment (2014-04 to 2019-06) and 15.72 percent in
  the later segment (2021-08 to 2026-08) have no price and are never held (`reports/m5_step4.md`). 71.8 percent of the
  early ones belong to stocks later removed from the index, which likely flatters the reported levels
  (`docs/current_roadmap.md`, backlog).
- **Missing crash.** The sealed window and its buffers remove 2019-07 to 2021-08, including the 2020 crash, from the
  stock books (`reports/m5_step4.md`). The stock-book drawdowns above are therefore too mild.
- **Delistings.** No terminal evidence is accepted, so any held stock that disappears counts as a total loss. The
  equal-weight book uses the same rule; SPY does not. In the R0 book this affected 26 unique stocks (61 incidences,
  incoming weight sum 0.1384) in the earlier segment and 14 (25 incidences, 0.0492) in the later one. A weight sum adds
  across events; it is not one portfolio weight at one time (`reports/m5_step4.md`, R4 Affected Events). A rerun at
  the last close changes no decision, but it makes the gaps smaller (see The Answer). Step 4 is labeled fragile: three
  Sharpe margins change sign, and no decision changes (`reports/m5_step4.md`).
- **Distributions.** We accept the vendor's adjusted close as including each dividend (premise VP-2, owner decision
  O-9). The M4.7 coverage census on `real_v1` flagged 22.5 percent of eligible member-days as exposed to this
  premise (`S_D` above 0.05; `reports/m4_7_coverage_census.md`, `docs/decision_log.md`).
- **Sample reuse.** The later stock months were examined before in Milestone 4.7, and only 2014-05 to 2016-07 is
  unexposed. No stock-level result here is confirmatory (`reports/m5_step4.md`). The public-factor comparisons in
  steps 2 and 3 also look again at history seen before the trial file (`reports/m5_factor_baseline.md`,
  `reports/m5_step3.md`).
- **Short history.** 99 comparison months of stock data can detect only large differences (`reports/m5_step4.md`,
  Limitations).

## What Comes Next

- **Freeze.** R0 will be frozen in a dated file, so no one can tune it later. Two formal
  review seats from different model families review the freeze, the AGENTS.md gate for a trial-family freeze
  (`docs/current_roadmap.md`, step 6 status).
- **No seal look.** The sealed window 2019-07-31 to 2020-07-31 stays closed. It is kept for a future candidate with a
  real edge, or for the later M4.8 stages (O-12).
- **No forward observation.** No price or membership data after August 2026 will be bought or used. Forward
  observation needs a new owner decision on data and money (O-12).
- **Next line of work: open.** The owner will decide after this report.

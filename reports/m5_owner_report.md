# Milestone 5 Owner Report: What the Factor-Class Allocator Found

**Evidence ceiling: `DIAGNOSTIC_ONLY`.** Simulated research only, with no orders and no trading. This report computes
nothing new: every number is quoted from a committed report, record, or file, which is named beside it. Nothing here
is a profitability claim or investment advice.

## The Answer

**At this evidence ceiling, no rule beats an index fund. Milestone 6 does not start on this allocator.**

On our own point-in-time S&P 500 books, after costs, the best rule we have is R0. R0 holds six price-based stock
sleeves in equal shares. It trailed SPY by 4.61 percent a year in 2014-12 to 2019-06 and by 9.73 percent a year in
2022-05 to 2025-12. It also trailed an equal-weight book of the same stocks, by 1.55 and 2.86 percent a year
(`reports/m5_step4.md`). Timing by market conditions and accounting-based value and quality classes gave no reason to
change that answer. The search for new factors was deferred before any result (O-11).

## What We Tested, in Plain Words

1. **Public factor data, 1972 to 2025** (`reports/m5_factor_baseline.md`). These are long-short academic factor series
   (JKP, 153 factors), gross of the factors' own trading and borrowing costs, and they include small caps.
   - Holding every factor sized by its recent risk (rule R1) beat holding them in equal amounts: it met 8 of 8 declared
     conditions.
   - R1 made 2.27 percent a year against 2.57 percent for equal amounts, but with a much smaller worst loss (-7.27
     against -13.97 percent). The difference in mean return is not significant (HAC p 0.12).
2. **Timing by market conditions** (`reports/m5_step3.md`). We tilted toward factors by market trend, market
   volatility, and credit spread, which are known at the time.
   - The tilt earned 0.23 bp a month less than R1 (HAC p 0.38, BY q 1, random-date p 0.32).
   - None of the 39 factor-class and market-state cells survived. There is no evidence of timing skill.
3. **Real stock books** (`reports/m5_step4.md`). We bought the top 20 percent of S&P 500 members on each price signal,
   using point-in-time membership.
   - The six sleeves are momentum, 52-week high, one-month reversal, low volatility, low beta, and illiquidity.
   - Equal shares (R0) stay the baseline: rule R1 met only 4 of 8 conditions against R0. The timing tilt was closed.
   - R0's annual net return was 5.80 percent in the earlier period and 6.68 percent in the later one. SPY made 10.41
     and 16.41 percent, and the equal-weight book 7.35 and 9.53 percent, over the same months.
   - R0's worst loss was -11.99 and -13.04 percent. SPY's was -13.53 and -12.95 percent.
4. **Accounting data** (`reports/m5_step4b_data.md`, `reports/m5_step4b.md`). We built value and quality classes from
   SEC filings as first filed, mapping 563 of 632 companies.
   - Adding them to R0 met 2 of 8 conditions, at +0.051 percent a month (HAC p 0.42). They do not join.
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
- **Delistings.** No terminal evidence is accepted, so any held stock that disappears counts as a total loss. A rerun
  at the last close changes no decision. Step 4 is labeled fragile: three Sharpe margins change sign, and no
  decision changes (`reports/m5_step4.md`).
- **Distributions.** We accept the vendor's adjusted close as including each dividend (premise VP-2, owner decision
  O-9). The M4.7 coverage census on `real_v1` flagged 22.5 percent of eligible member-days as exposed to this
  premise (`S_D` above 0.05; `reports/m4_7_coverage_census.md`, `docs/decision_log.md`).
- **Sample reuse.** The later stock months were examined before in Milestone 4.7, and only 2014-05 to 2016-07 is
  unexposed. No stock-level result here is confirmatory (`reports/m5_step4.md`).
- **Short history.** 99 comparison months of stock data can detect only large differences (`reports/m5_step4.md`,
  Limitations).

## What Comes Next

- **Freeze.** R0 will be frozen in a dated file after the milestone ablation, so no one can tune it later. Two formal
  review seats from different model families review the freeze, the AGENTS.md gate for a trial-family freeze
  (`docs/current_roadmap.md`, step 6 status).
- **No seal look.** The sealed window 2019-07-31 to 2020-07-31 stays closed. It is kept for a future candidate with a
  real edge, or for the later M4.8 stages (O-12).
- **No forward observation.** No price or membership data after August 2026 will be bought or used. Forward
  observation needs a new owner decision on data and money (O-12).
- **Next line of work: open.** The owner will decide after this report.

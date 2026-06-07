# WorldQuant-Style Alpha Catalog

This catalog is a documentation-first roadmap for incorporating selected ideas from the public WorldQuant 101 Formulaic Alphas into this simulated equity factor research project.

## Purpose

The WorldQuant 101 Formulaic Alphas are public formulaic alpha references associated with WorldQuant and Kakushadze's published research. In this project, they are treated as educational and research references only.

They are not guaranteed profitable strategies, not trading recommendations, and not evidence that any strategy will work in live markets.

The purpose of this document is to classify the alpha references by data requirements, implementation complexity, and research priority before additional code is written. The project should not blindly implement all 101 alphas at once.

## Formulaic Alpha != Full Strategy

A formulaic alpha is only a signal definition. It is not a complete investment process or trading system.

Before any alpha can become part of a credible research workflow, it still needs:

- universe selection.
- data cleaning.
- explicit date alignment.
- ranking or normalization.
- portfolio construction.
- transaction costs.
- slippage assumptions.
- risk controls.
- benchmark comparison.
- out-of-sample validation.

This project should continue to treat every formula as a research feature until it has been tested for leakage, missing data behavior, stability, and implementation correctness.

## Current Implementation Status

This catalog began as a Stage 1 documentation-only milestone. The current
repository has moved beyond catalog-only status, but only in a narrow,
reviewed way.

| Area | Current status |
| --- | --- |
| Reusable operator layer | Implemented and tested for core pandas panel operators in `src/features/operators.py`. |
| `alpha_009` | Implemented and tested in `src/features/worldquant_alphas.py` as a close-only research feature. |
| Other WorldQuant-style alphas | Not implemented. |
| WorldQuant-style alpha backtest integration | Not implemented. |
| Bulk WorldQuant 101 implementation | Not implemented and still out of scope. |

`alpha_009` is not a full strategy, not a trading recommendation, not connected
to a dedicated alpha strategy backtest, and not evidence of profitability. It
only shows that one close-only formula can be represented as a tested research
feature with explicit date-alignment assumptions.

## Priority System

The current catalog is no longer catalog-only. Priority labels now distinguish
implemented research features from future candidates and deferred categories.

Priority labels:

- `Implemented research feature`: code exists with tests, but it is still not a
  complete strategy or profitability claim.
- `P1`: close-only candidate that can be considered after formula review,
  operator coverage review, and tests are planned.
- `P2`: requires volume, open, high, low, or OHLCV schema support before
  implementation.
- `P3`: deferred because it requires VWAP, market cap, industry neutralization, or higher complexity.

Important priority rules:

- `alpha_009` is implemented as a research feature only.
- Remaining close-only alphas are future `P1` candidates, not automatic
  implementation tasks.
- `alpha_012` is not an immediate implementation task; it is `P2` because it requires volume + close support.
- `alpha_101` is not an immediate implementation task; it is `P2` because it requires OHLC support.
- All VWAP, market cap, and industry-neutral categories are deferred as `P3`.
- No new formula should be implemented until its data requirements, operator
  coverage, missing-data behavior, and tests are explicitly scoped.
- Future volume or OHLC-dependent formula work should start from
  `docs/volume_ohlcv_schema_plan.md` so the local CSV schema, adjustment
  policy, missing-value behavior, and validation tests are reviewed before code
  is added.
- Future volume + close formula work should start from
  `docs/volume_close_alpha_plan.md` before any `alpha_012` or similar
  implementation PR is opened.
- Future liquidity or dollar-volume universe work should start from
  `docs/liquidity_dollar_volume_universe_plan.md` before any code filters
  assets by volume.

## Classification By Data Requirement

This classification groups the 101 alpha references by required input data
categories. It remains a roadmap aid, not a mandate to implement every formula.

```text
close only:
1, 9, 10, 19, 24, 29, 34, 46, 49, 51

low only:
4

high only:
23

open + close:
8, 18, 33, 37, 38

open + close + high + low:
20, 54, 101

volume + close:
7, 12, 13, 17, 21, 30, 39, 43, 45

volume + open + close:
2, 14

volume + open:
3, 6

volume + high:
15, 16, 26, 40, 44

volume + high + close:
22

volume + high + low + close:
28, 35, 55, 60, 68, 85

volume + close + low:
31, 52

volume + high + low:
99

volume + open + close + high + low:
88, 92, 94

volume + open + high + low:
95

vwap + close:
32, 42, 57, 84

vwap + open + close:
5

vwap + volume:
27, 50, 61, 81

vwap + volume + close:
11, 96

vwap + volume + close + high:
25, 47, 74

vwap + volume + high + low:
72, 77

vwap + volume + low:
75, 78

vwap + volume + close + high + low:
83

vwap + volume + open:
65, 98

vwap + volume + open + close:
36, 86

vwap + volume + open + high + low:
62, 64

vwap + open + high + low:
66

vwap + open + low:
73

vwap + high + low:
41

close + high + low:
53

close + industry:
48

close + market cap:
56

vwap + volume + industry:
58, 59

vwap + volume + open + close + industry:
63, 79

vwap + volume + high + industry:
67

vwap + volume + close + industry:
69, 70, 87, 91, 93

vwap + volume + low + industry:
76, 89, 97

volume + open + high + industry:
80

volume + open + industry:
82

volume + close + industry:
90

volume + close + high + low + industry:
100
```

## Data Category Priorities

| Data requirement category | Alpha references | Future priority | Notes |
| --- | --- | --- | --- |
| close only | 1, 9, 10, 19, 24, 29, 34, 46, 49, 51 | P1 | `alpha_009` is implemented as a research feature only; remaining close-only references require separate formula review and tests before implementation. |
| low only | 4 | P2 | Requires low data support. |
| high only | 23 | P2 | Requires high data support. |
| open + close | 8, 18, 33, 37, 38 | P2 | Requires open data support. |
| open + close + high + low | 20, 54, 101 | P2 | Requires OHLC support; alpha_101 is not immediate. |
| volume + close | 7, 12, 13, 17, 21, 30, 39, 43, 45 | P2 | Requires volume support; alpha_012 is not immediate. |
| volume + open + close | 2, 14 | P2 | Requires volume and open data support. |
| volume + open | 3, 6 | P2 | Requires volume and open data support. |
| volume + high | 15, 16, 26, 40, 44 | P2 | Requires volume and high data support. |
| volume + high + close | 22 | P2 | Requires volume and high data support. |
| volume + high + low + close | 28, 35, 55, 60, 68, 85 | P2 | Requires volume and OHLC-adjacent data support. |
| volume + close + low | 31, 52 | P2 | Requires volume and low data support. |
| volume + high + low | 99 | P2 | Requires volume, high, and low data support. |
| volume + open + close + high + low | 88, 92, 94 | P2 | Requires full OHLCV support. |
| volume + open + high + low | 95 | P2 | Requires OHLCV-adjacent support. |
| vwap categories | 5, 11, 25, 27, 32, 36, 41, 42, 47, 50, 57, 61, 62, 64, 65, 66, 72, 73, 74, 75, 77, 78, 81, 83, 84, 86, 96, 98 | P3 | Deferred until explicit VWAP data support exists. |
| market cap categories | 56 | P3 | Deferred until market cap data support exists. |
| industry-neutral categories | 48, 58, 59, 63, 67, 69, 70, 76, 79, 80, 82, 87, 89, 90, 91, 93, 97, 100 | P3 | Deferred until industry classification and neutralization support exist. |

## Required Operators

Reusable operator coverage before broad alpha implementation:

- `delay`
- `delta`
- `cross_sectional_rank`
- `ts_rank`
- `rolling_mean`
- `rolling_std`
- `rolling_min`
- `rolling_max`
- `rolling_corr`
- `rolling_cov`
- `signed_power`
- `scale`
- `winsorize_cross_sectional`
- `cross_sectional_zscore`
- `safe_divide`

Deferred operator:

- `neutralize_by_group`, deferred until industry group data and group-alignment tests exist.

The core operator layer now exists for the first close-only formula work, but
each additional formula still needs a formula-specific review. Missing or
ambiguous operators should be added in small tested milestones before any
dependent formula is implemented.

## Do Not Do Yet

- Do not implement all 101 alphas at once.
- Do not claim these alphas are profitable.
- Do not connect these alphas to backtesting yet.
- Do not treat `alpha_009` as a complete strategy.
- Do not fetch real data.
- Do not implement VWAP alphas before VWAP data support exists.
- Do not implement industry-neutral alphas before industry data support exists.
- Do not hide missing data with forward-fill or zero-return defaults.

## Next Milestone

The next milestone should remain small and data-prerequisite driven, not alpha
backtesting.

Reasonable next documentation or planning stages include:

- plan or implement a synthetic-only liquidity eligibility helper after
  `docs/liquidity_dollar_volume_universe_plan.md` is reviewed;
- review `docs/volume_close_alpha_plan.md` before considering `alpha_012` or
  any other volume + close alpha implementation;
- plan OHLC schema requirements before considering `alpha_101`;
- review another close-only candidate and list exact formula, operator, and test
  requirements before implementation;
- refresh roadmap documents when they still describe historical pre-`alpha_009`
  or pre-operator states.

Any future formula implementation should stay separate from backtest
integration, real-data experiments, and performance interpretation until the
project has a reviewed experiment plan.

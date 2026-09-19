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
| `alpha_001`, `alpha_002`, `alpha_003`, `alpha_004`, `alpha_006` | Implemented and tested in `src/features/alphas.py` as classical price-volume research features under `DIAGNOSTIC_ONLY`. |
| `alpha_005`, `alpha_008`, `alpha_010`, `alpha_013`, `alpha_014`, `alpha_018`, `alpha_020` | Implemented and tested in `src/features/alphas.py` as batch-2 classical price-volume research features under `DIAGNOSTIC_ONLY`. `alpha_005` uses typical-price VWAP `(high + low + close) / 3` on companion synthetic bars. |
| `alpha_007`, `alpha_009`, `alpha_017`, `alpha_019`, `alpha_023`, `alpha_028`, `alpha_033`, `alpha_038`, `alpha_054`, `alpha_101` | Implemented and tested in `src/features/alphas.py` as batch-3 classical price-volume research features under `DIAGNOSTIC_ONLY`. `alpha_009` in this module is the cross-sectional rank of the same sign-rule inner value as `src/features/worldquant_alphas.py`. |
| `alpha_009` (unranked inner) | Implemented and tested in `src/features/worldquant_alphas.py` as a close-only research feature. |
| `alpha_012` | Implemented and tested in `src/features/alphas.py` and `src/features/worldquant_alphas.py` as a volume + close research feature; covered by synthetic OHLCV fixture smoke and diagnostic runner. |
| Other WorldQuant-style alphas | Remain unimplemented. |
| WorldQuant-style alpha backtest integration | Implemented for diagnostics in `research/alphas_diagnostic_mvp.py` and `research/multifactor_diagnostic_mvp.py` using the 50-stock diagnostic cohort. |
| Bulk WorldQuant 101 implementation | Not implemented and still out of scope. |

Implemented alphas are not full strategies, not trading recommendations, and
not evidence of profitability. They show that reviewed formulas can be
represented as tested research features with explicit date-alignment and
missing-data assumptions under `DIAGNOSTIC_ONLY`.

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

- `alpha_009` and `alpha_010` are implemented as research features only.
  `features.alphas.alpha_009` applies `cs_rank` to the sign-rule inner value;
  `features.worldquant_alphas.alpha_009` returns that inner value.
- `alpha_012` is implemented as a research feature only.
- Batch-2 alphas `alpha_005`, `alpha_008`, `alpha_013`, `alpha_014`,
  `alpha_018`, and `alpha_020` are implemented as research features only.
  `alpha_005` uses typical-price VWAP on companion synthetic bars.
- Batch-3 alphas `alpha_007`, `alpha_017`, `alpha_019`, `alpha_023`,
  `alpha_028`, `alpha_033`, `alpha_038`, `alpha_054`, and `alpha_101` are
  implemented as research features only.
- Remaining close-only alphas are future `P1` candidates, not automatic
  implementation tasks.
- Remaining volume + close alphas are future `P2` candidates, not automatic
  implementation tasks.
- All VWAP, market cap, and industry-neutral categories are deferred as `P3`.
- No new formula should be implemented until its data requirements, operator
  coverage, missing-data behavior, and tests are explicitly scoped.
- Future volume or OHLC-dependent formula work should start from
  `docs/volume_ohlcv_schema_plan.md` so the local CSV schema, adjustment
  policy, missing-value behavior, and validation tests are reviewed before code
  is added.
- Future volume + close formula work for any remaining candidate should start
  from `docs/volume_close_alpha_plan.md` and use a separate formula-specific
  review before implementation.
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
| close only | 1, 9, 10, 19, 24, 29, 34, 46, 49, 51 | P1 | `alpha_001`, `alpha_009`, `alpha_010`, and `alpha_019` are implemented as research features only; remaining close-only references require separate formula review and tests before implementation. |
| low only | 4 | P2 | `alpha_004` is implemented as a research feature only. |
| high only | 23 | P2 | `alpha_023` is implemented as a research feature only. |
| open + close | 8, 18, 33, 37, 38 | P2 | `alpha_008`, `alpha_018`, `alpha_033`, and `alpha_038` are implemented as research features only; remaining open + close references require separate formula review and tests before implementation. |
| open + close + high + low | 20, 54, 101 | P2 | `alpha_020`, `alpha_054`, and `alpha_101` are implemented as research features only. |
| volume + close | 7, 12, 13, 17, 21, 30, 39, 43, 45 | P2 | `alpha_007`, `alpha_012`, `alpha_013`, and `alpha_017` are implemented as research features only; remaining volume + close references require separate formula review and tests before implementation. |
| volume + open + close | 2, 14 | P2 | `alpha_002` and `alpha_014` are implemented as research features only. |
| volume + open | 3, 6 | P2 | `alpha_003` and `alpha_006` are implemented as research features only. |
| volume + high | 15, 16, 26, 40, 44 | P2 | Requires volume and high data support. |
| volume + high + close | 22 | P2 | Requires volume and high data support. |
| volume + high + low + close | 28, 35, 55, 60, 68, 85 | P2 | `alpha_028` is implemented as a research feature only; remaining references require volume and OHLC-adjacent data support. |
| volume + close + low | 31, 52 | P2 | Requires volume and low data support. |
| volume + high + low | 99 | P2 | Requires volume, high, and low data support. |
| volume + open + close + high + low | 88, 92, 94 | P2 | Requires full OHLCV support. |
| volume + open + high + low | 95 | P2 | Requires OHLCV-adjacent support. |
| vwap categories | 5, 11, 25, 27, 32, 36, 41, 42, 47, 50, 57, 61, 62, 64, 65, 66, 72, 73, 74, 75, 77, 78, 81, 83, 84, 86, 96, 98 | P3 | `alpha_005` is implemented as a research feature using typical-price VWAP `(high + low + close) / 3` on companion synthetic bars; remaining VWAP references stay deferred until explicit VWAP data support exists. |
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
- Keep formulaic alphas as research features. Diagnostic cohort wiring lives in
  `research/alphas_diagnostic_mvp.py` and
  `research/multifactor_diagnostic_mvp.py` under `DIAGNOSTIC_ONLY`.
- Do not treat `alpha_009` as a complete strategy.
- Do not fetch real data.
- Remaining VWAP alphas stay deferred until explicit VWAP data support exists;
  `alpha_005` uses typical-price VWAP on companion synthetic bars only.
- Do not implement industry-neutral alphas before industry data support exists.
- Do not hide missing data with forward-fill or zero-return defaults.

## Next Milestone

The next milestone should remain small and data-prerequisite driven, not alpha
backtesting.

Reasonable next documentation or planning stages include:

- refresh the QuantConnect/LEAN plan for Alpha#012 signal mapping while
  keeping the LEAN path non-executing and free of data subscriptions or
  orders;
- design the first liquidity universe construction API before any backtest
  uses liquidity eligibility;
- review `docs/volume_close_alpha_plan.md` before considering any remaining
  volume + close alpha implementation;
- review another remaining close-only candidate and list exact formula, operator, and test
  requirements before implementation;
- refresh roadmap documents when they still describe historical pre-`alpha_009`
  or pre-operator states.

Any future formula implementation should stay separate from backtest
integration, real-data experiments, and performance interpretation until the
project has a reviewed experiment plan.

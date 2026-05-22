# WorldQuant-Style Alpha Catalog

This catalog is a documentation-first roadmap for incorporating selected ideas from the public WorldQuant 101 Formulaic Alphas into this simulated equity factor research project.

## Purpose

The WorldQuant 101 Formulaic Alphas are public formulaic alpha references associated with WorldQuant and Kakushadze's published research. In this project, they are treated as educational and research references only.

They are not guaranteed profitable strategies, not trading recommendations, and not evidence that any strategy will work in live markets.

The purpose of this document is to classify the alpha references by data requirements, implementation complexity, and research priority before any code is written. The project should not blindly implement all 101 alphas at once.

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

## Priority System

The current milestone is catalog-only. No alpha in this document is implemented yet.

Priority labels:

- `P0`: catalog only, not implemented.
- `P1`: can be considered once close-only operators are ready.
- `P2`: requires volume or OHLC support.
- `P3`: deferred because it requires VWAP, market cap, industry neutralization, or higher complexity.

Important priority rules:

- All alpha references are `P0` in this documentation-only milestone.
- Close-only alphas are future `P1` candidates after the operator layer exists.
- `alpha_009` is the preferred first future implementation candidate because it is close-only and narrow in data requirements.
- `alpha_012` is not an immediate implementation task; it is `P2` because it requires volume + close support.
- `alpha_101` is not an immediate implementation task; it is `P2` because it requires OHLC support.
- All VWAP, market cap, and industry-neutral categories are deferred as `P3`.

## Classification By Data Requirement

This classification is the source of truth for the Stage 1 catalog. It groups the 101 alpha references by required input data categories.

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
| close only | 1, 9, 10, 19, 24, 29, 34, 46, 49, 51 | P1 | Preferred first category after close-only operators exist; alpha_009 is the first candidate. |
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

Expected reusable operators before broad alpha implementation:

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
- `winsorize`
- `cross_sectional_zscore`
- `safe_divide`

Deferred operator:

- `neutralize_by_group`, deferred until industry group data and group-alignment tests exist.

The first operator milestone should focus on simple, testable close-only primitives before attempting VWAP, industry-neutral, or high-complexity formulas.

## Do Not Do Yet

- Do not implement all 101 alphas at once.
- Do not claim these alphas are profitable.
- Do not connect these alphas to backtesting yet.
- Do not fetch real data.
- Do not implement VWAP alphas before VWAP data support exists.
- Do not implement industry-neutral alphas before industry data support exists.
- Do not hide missing data with forward-fill or zero-return defaults.

## Next Milestone

The next milestone after this catalog is operator-layer implementation and tests, not alpha backtesting.

The operator milestone should create a small, well-tested operator layer first. Only after those operators pass deterministic, non-tautological tests should the project implement the first close-only alpha candidate, preferably `alpha_009`.

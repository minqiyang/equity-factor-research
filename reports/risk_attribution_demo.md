# Multi-Factor Risk Attribution Synthetic Diagnostic

Evidence ceiling: DIAGNOSTIC_ONLY. Seed 4606 generates 100 observed closes and 24 predeclared synthetic identities.
All inputs, market caps, and book-to-price availability are synthetic. The cohort supplies a software diagnostic; empirical validation and formal promotion remain open.

Size uses log capitalization; Value uses supplied book-to-price; Momentum uses a 20-close lookback with a 5-close skip; Volatility uses 15 sample-return observations; Liquidity uses log 10-close mean dollar volume. Price and volume use the declared raw basis. Each style uses 1%/99% winsorization and population-standard-deviation normalization. Market is a unit intercept.

Exposures, regression weights, benchmark weights, and actual portfolio weights use the immediately prior observed close. Signals execute at the next observed close under the existing engine contract; incoming returns use previous holdings. Weekly Friday resets pay 10 bps commission and 5 bps slippage under existing turnover conventions. Cash earns zero.

OLS and WLS (W = sqrt(market cap)) fit every complete 24-asset cross-section. Long-only active risk uses an equal-weight benchmark re-established at each prior close. Long-short active risk uses cash. The engine's realized benchmark metrics remain separate from this model forecast.

Risk uses the latest 20 earlier fits, with 10 observations required, sample covariance and sample residual variance. Forecasts exclude the current realized return. Diagonal specific covariance and zero factor/specific covariance are modeling assumptions. Specific return measures residual return. Economic alpha, covariance calibration, and forecast accuracy require separate evidence.

Complete finite static panels define this diagnostic. Warmup exposure gaps and collinearity produce retained refusals. Terminal-event integration and changing regression universes remain open. Every attempted case retains started and terminal records. The full synthetic interval is a diagnostic sample; holdout inference and parameter selection are outside this run.

Arithmetic contribution sums describe sums of one-period returns; compounded portfolio return has its own column. Multi-period geometric attribution remains open.

## All attempted cases

| case | status | compounded net | gross sum | specific sum | cost sum | annualized forecast TE | max identity error |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| long_only_OLS_1_valid | success | -0.06609837 | -0.03271562 | -0.00335072 | 0.03460410 | 0.08643863 | 3.47e-18 |
| long_only_OLS_-1_valid | success | -0.07150834 | -0.03974667 | -0.04235686 | 0.03312735 | 0.08937000 | 3.47e-18 |
| long_only_WLS_1_valid | success | -0.06609837 | -0.03271562 | 0.00145431 | 0.03460410 | 0.08687992 | 2.6e-18 |
| long_only_WLS_-1_valid | success | -0.07150834 | -0.03974667 | -0.04896357 | 0.03312735 | 0.09094332 | 3.47e-18 |
| long_short_OLS_1_valid | success | -0.03050576 | 0.00368372 | 0.01983023 | 0.03388684 | 0.07430988 | 2.6e-18 |
| long_short_OLS_-1_valid | success | -0.03754744 | -0.00363855 | -0.01984981 | 0.03389141 | 0.07683576 | 3.47e-18 |
| long_short_WLS_1_valid | success | -0.03050576 | 0.00368372 | 0.02562163 | 0.03388684 | 0.07502330 | 2.6e-18 |
| long_short_WLS_-1_valid | success | -0.03754744 | -0.00363855 | -0.02558695 | 0.03389141 | 0.07757343 | 3.47e-18 |
| long_only_OLS_1_collinear | refused: rank_deficient | | | | | | |
| long_only_OLS_1_warmup | refused: exposure_unavailable | | | | | | |

## Factor contribution sums

| case | Market | Size | Value | Momentum | Volatility | Liquidity |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| long_only_OLS_1_valid | -0.00387927 | 0.01566172 | -0.01027200 | -0.01431977 | -0.00575480 | -0.01080078 |
| long_only_OLS_-1_valid | -0.00387927 | 0.00657004 | -0.01939058 | 0.00287980 | -0.00116175 | 0.01759195 |
| long_only_WLS_1_valid | -0.00349218 | 0.01528415 | -0.00843716 | -0.01662340 | -0.00898465 | -0.01191670 |
| long_only_WLS_-1_valid | -0.00349218 | 0.00537857 | -0.01354981 | 0.00136931 | 0.00155050 | 0.01796051 |
| long_short_OLS_1_valid | -0.00017859 | 0.00444332 | 0.00454043 | -0.00848578 | -0.00241001 | -0.01405587 |
| long_short_OLS_-1_valid | 0.00017937 | -0.00454512 | -0.00458378 | 0.00857312 | 0.00240405 | 0.01418361 |
| long_short_WLS_1_valid | -0.00017668 | 0.00482124 | 0.00252166 | -0.00885792 | -0.00544531 | -0.01480090 |
| long_short_WLS_-1_valid | 0.00017718 | -0.00498019 | -0.00255574 | 0.00898804 | 0.00541022 | 0.01490888 |

## Latest active-risk decomposition

| case | factor variance | specific variance | total active variance | estimated intervals | warmup intervals |
| --- | ---: | ---: | ---: | ---: | ---: |
| long_only_OLS_1_valid | 0.0000080653 | 0.0000215840 | 0.0000296494 | 64 | 10 |
| long_only_OLS_-1_valid | 0.0000090197 | 0.0000226748 | 0.0000316944 | 64 | 10 |
| long_only_WLS_1_valid | 0.0000085128 | 0.0000214401 | 0.0000299529 | 64 | 10 |
| long_only_WLS_-1_valid | 0.0000095374 | 0.0000232828 | 0.0000328202 | 64 | 10 |
| long_short_OLS_1_valid | 0.0000075546 | 0.0000143579 | 0.0000219125 | 64 | 10 |
| long_short_OLS_-1_valid | 0.0000080769 | 0.0000153506 | 0.0000234275 | 64 | 10 |
| long_short_WLS_1_valid | 0.0000079410 | 0.0000143943 | 0.0000223353 | 64 | 10 |
| long_short_WLS_-1_valid | 0.0000084900 | 0.0000153895 | 0.0000238795 | 64 | 10 |

## Latest portfolio factor exposures

| case | Market | Size | Value | Momentum | Volatility | Liquidity |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| long_only_OLS_1_valid | 1.00000000 | 0.25592113 | 0.39719741 | -0.47460914 | 0.17280955 | -0.16250944 |
| long_only_OLS_-1_valid | 1.00000000 | -0.24392104 | -0.49337402 | 0.28544218 | -0.08326157 | 0.39882821 |
| long_only_WLS_1_valid | 1.00000000 | 0.25592113 | 0.39719741 | -0.47460914 | 0.17280955 | -0.16250944 |
| long_only_WLS_-1_valid | 1.00000000 | -0.24392104 | -0.49337402 | 0.28544218 | -0.08326157 | 0.39882821 |
| long_short_OLS_1_valid | 0.01643689 | 0.24594231 | 0.43723058 | -0.37538030 | 0.12668264 | -0.27414762 |
| long_short_OLS_-1_valid | -0.01699560 | -0.25430219 | -0.45209257 | 0.38813993 | -0.13098873 | 0.28346623 |
| long_short_WLS_1_valid | 0.01643689 | 0.24594231 | 0.43723058 | -0.37538030 | 0.12668264 | -0.27414762 |
| long_short_WLS_-1_valid | -0.01699560 | -0.25430219 | -0.45209257 | 0.38813993 | -0.13098873 | 0.28346623 |

Recorded cases: 10; successful books: 8; negative compounded net-return books: 8.

Reproduce: `PYTHONPATH=src:. python -m research.risk_attribution_demo`.

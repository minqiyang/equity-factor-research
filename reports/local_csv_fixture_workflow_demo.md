# Local CSV Fixture Workflow Demo

This report uses committed synthetic local CSV fixtures only. It is not real-market evidence, not financial advice, and not a profitability claim. It does not run a backtest, construct a portfolio, fetch real data, connect to a broker, place orders, or support live trading.

## Purpose

Exercise the local CSV research path with a small committed fixture:

1. Load a wide adjusted-close CSV with the strict local loader.
2. Load a benchmark CSV and verify date alignment.
3. Compute `alpha_009` as a close-only research feature.
4. Compute next-row forward returns as evaluation targets only.
5. Run IC, Rank IC, and quantile spread diagnostics.
6. Write a caveated report and JSON experiment log.

## Inputs

| Item | Value |
| --- | --- |
| Price fixture | `tests/fixtures/local_csv_loader_smoke/synthetic_adjusted_close.csv` |
| Benchmark fixture | `tests/fixtures/local_csv_loader_smoke/synthetic_benchmark.csv` |
| Price schema | `wide_price` |
| Benchmark schema | `benchmark_price` |
| Price rows | `4` |
| Asset columns | `AAA, BBB, CCC` |
| Date range | `2024-01-02` to `2024-01-05` |
| Missing price values | `0` |
| Missing benchmark values | `0` |

## Processing Summary

The workflow preserves the loader output date index and asset columns, verifies that the benchmark dates match the price panel dates, and computes `alpha_009` with `window=1`. Forward returns are aligned to the same date as the factor value for diagnostic evaluation only; they are not used as feature inputs.

No missing values were filled. No dates or assets were reindexed. No portfolio construction, execution timing, transaction cost model, slippage model, or backtest is included.

## Diagnostic Coverage

| Diagnostic | Value |
| --- | ---: |
| Factor valid observations | `9` |
| Forward-return valid observations | `9` |
| Benchmark forward-return valid observations | `3` |
| IC valid dates | `2` |
| Rank IC valid dates | `2` |
| Quantile spread valid dates | `1` |

## Information Coefficient Diagnostics

| Date | information_coefficient |
| --- | ---: |
| 2024-01-02 | NaN |
| 2024-01-03 | -0.6217 |
| 2024-01-04 | 0.9997 |
| 2024-01-05 | NaN |

## Rank Information Coefficient Diagnostics

| Date | rank_information_coefficient |
| --- | ---: |
| 2024-01-02 | NaN |
| 2024-01-03 | -0.5000 |
| 2024-01-04 | 0.8660 |
| 2024-01-05 | NaN |

## Quantile Spread Diagnostics

| Date | bottom_quantile_mean_return | top_quantile_mean_return | top_minus_bottom_spread | valid_asset_count | bottom_quantile_count | top_quantile_count |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2024-01-02 | NaN | NaN | NaN | 0 | 0 | 0 |
| 2024-01-03 | 0.0151 | 0.0074 | -0.0077 | 3 | 1 | 1 |
| 2024-01-04 | NaN | NaN | NaN | 3 | 0 | 0 |
| 2024-01-05 | NaN | NaN | NaN | 0 | 0 | 0 |

## Limitations

- The CSV files are tiny synthetic fixtures committed for workflow testing.
- The benchmark is synthetic and used only to verify local CSV date alignment.
- The diagnostic returns are synthetic fixture calculations, not market evidence.
- `alpha_009` is a research feature, not a complete strategy.
- No local CSV result here should be interpreted without the real-data readiness audit and full experiment-log requirements.
- User-provided local CSV research, validation splits, universe construction, costs, slippage, and QuantConnect/LEAN implementation remain future stages.

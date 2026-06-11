# Local CSV Fixture Workflow Demo

This report uses committed synthetic local CSV fixtures only. It is not real-market evidence, not financial advice, and not a profitability claim. It does not run a backtest, construct a strategy portfolio, fetch real data, connect to a broker, place orders, or support live trading.

## Purpose

Exercise the local CSV research path with a small committed fixture:

1. Load a wide adjusted-close CSV with the strict local loader.
2. Load a benchmark CSV and verify date alignment.
3. Load a synthetic OHLCV CSV for a liquidity eligibility count smoke check.
4. Compute lagged ADV and dollar-volume eligibility masks without filling missing volume.
5. Run a metadata-only dry-run inventory review for the declared committed fixture inputs.
6. Construct a synthetic liquidity universe mask count diagnostic from the intersection of both eligibility rules.
7. Apply the universe mask to `alpha_009` as a signal-panel smoke check only.
8. Compute `alpha_009` as a close-only research feature.
9. Compute `alpha_012` as a volume + close research feature from the OHLCV fixture.
10. Compute next-row forward returns as evaluation targets only.
11. Apply chronological train/validation/test split metadata.
12. Run IC, Rank IC, and quantile spread diagnostics.
13. Run a synthetic volume-aware slippage participation/count smoke diagnostic.
14. Write a caveated report and JSON experiment log.

## Inputs

| Item | Value |
| --- | --- |
| Price fixture | `tests/fixtures/local_csv_loader_smoke/synthetic_adjusted_close.csv` |
| Benchmark fixture | `tests/fixtures/local_csv_loader_smoke/synthetic_benchmark.csv` |
| OHLCV fixture | `tests/fixtures/local_csv_loader_smoke/synthetic_ohlcv.csv` |
| Price schema | `wide_price` |
| Benchmark schema | `benchmark_price` |
| OHLCV schema | `ohlcv_long` |
| Price rows | `4` |
| OHLCV rows | `4` |
| Asset columns | `AAA, BBB, CCC` |
| Date range | `2024-01-02` to `2024-01-05` |
| Train end | `2024-01-02` |
| Validation end | `2024-01-03` |
| Test end | `2024-01-05` |
| Missing price values | `0` |
| Missing benchmark values | `0` |
| Slippage smoke notional | `100000.0000` |
| Slippage smoke max participation | `0.1000` |

## Inventory Dry-Run Rehearsal

The workflow declares a small local CSV inventory for the committed synthetic fixtures and validates that metadata with `validate_local_csv_inventory()` before interpreting any loader output. The review is a dry-run gate only: it does not read files, check path existence, compute file hashes, store raw local paths in its result, fetch data, call vendor APIs, use credentials, or authorize real-data interpretation.

| Item | Value |
| --- | ---: |
| Declared inputs | `3` |
| High issues | `0` |
| Medium issues | `0` |
| Low issues | `0` |
| High or medium issue gate triggered | `false` |

| input_name | schema | path_declared | source_declared | version_declared | known_manual_edits_declared | mutable |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| adjusted_close_prices | wide_price | true | true | true | true | false |
| benchmark_prices | benchmark_price | true | true | true | true | false |
| ohlcv_prices_volume | ohlcv_long | true | true | true | true | false |

## Processing Summary

The workflow preserves the loader output date index and asset columns, verifies that the benchmark dates match the price panel dates, computes `alpha_009` with `window=1`, and computes `alpha_012` from the synthetic OHLCV `adjusted_close` and `volume` panels. Forward returns are aligned to the same date as the factor value for diagnostic evaluation only; they are not used as feature inputs.

The train/validation/test metadata is a chronological fixture split by factor and evaluation-target row date only. The one-row forward returns are diagnostic labels, not feature inputs, and are not used for parameter selection. This tiny fixture split is not model selection, parameter tuning, strategy validation, or real-market evidence.

No missing values were filled. No dates or assets were reindexed. No strategy portfolio construction, execution timing, transaction cost model, or backtest is included.

## Liquidity Eligibility Smoke Check

The workflow loads the committed synthetic OHLCV fixture and pivots `adjusted_close` and `volume` into panels aligned to the adjusted-close fixture's dates and assets. Missing OHLCV rows after that alignment remain missing; there is no fill, forward-fill, backward-fill, interpolation, or zero default.

Eligibility counts below are decision-date diagnostics only. They use `window=2`, `eligibility_lag=1`, `min_average_volume=100000.0000`, and `min_average_dollar_volume=11000000.0000`. They do not run a strategy, construct a portfolio, or validate market tradability.

| Date | asset_count | volume_observed_asset_count | missing_volume_count | zero_volume_count | adv_eligible_count | dollar_volume_eligible_count | both_eligible_count |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2024-01-02 | 3 | 2 | 1 | 0 | 0 | 0 | 0 |
| 2024-01-03 | 3 | 2 | 1 | 0 | 0 | 0 | 0 |
| 2024-01-04 | 3 | 0 | 3 | 0 | 2 | 1 | 1 |
| 2024-01-05 | 3 | 0 | 3 | 0 | 0 | 0 | 0 |

## Liquidity Universe Mask Smoke Check

The synthetic universe mask below is constructed from the intersection of the ADV and dollar-volume eligibility masks. It reports count and audit fields from `construct_liquidity_universe()` only. It does not create target weights, trades, positions, orders, returns, benchmark comparisons, or a tradeable universe claim.

| Date | raw_eligible_count | universe_count | missing_eligibility_count | missing_ranking_count | capped_count | added_count | removed_count | low_coverage |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2024-01-02 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | true |
| 2024-01-03 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | true |
| 2024-01-04 | 1 | 1 | 0 | 0 | 0 | 1 | 0 | false |
| 2024-01-05 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | true |

## Universe-Masked Alpha#009 Signal Smoke Check

The synthetic signal summary below applies the liquidity universe mask to the already-computed `alpha_009` factor panel. `True` mask cells preserve the original signal, `False` mask cells become missing values, and existing signal missing values remain missing. This is a signal-panel wiring check only; it does not rank assets, create weights, run a backtest, create trades, compare a benchmark, or validate performance.

| Date | raw_valid_signal_count | universe_eligible_count | valid_masked_signal_count | excluded_by_universe_count | missing_signal_count | low_coverage |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2024-01-02 | 0 | 0 | 0 | 0 | 3 | true |
| 2024-01-03 | 3 | 0 | 0 | 3 | 0 | true |
| 2024-01-04 | 3 | 1 | 1 | 2 | 0 | false |
| 2024-01-05 | 3 | 0 | 0 | 3 | 0 | true |

## Volume-Aware Slippage Smoke Diagnostic

This smoke diagnostic calls `calculate_volume_aware_slippage_diagnostics()` on a tiny synthetic target-weight panel built from complete OHLCV fixture rows only. The target weights are fixed constants for helper wiring, not factor-ranked weights, model-selected weights, strategy portfolio construction, orders, fills, or trade recommendations.

The diagnostic uses `window=1`, `volume_lag=1`, `portfolio_notional=100000.0000`, and `max_participation=0.1000`. Only participation and rejection/cap counts are reported here. Candidate slippage impact fields are not applied to returns, and this workflow still does not run a backtest.

| Date | trade_count | total_trade_weight | total_trade_notional | max_participation | missing_capacity_count | zero_capacity_count | zero_volume_window_count | rejected_capacity_count | participation_cap_breach_count |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 2024-01-02 | 0 | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 0 | 0 | 0 |
| 2024-01-03 | 2 | 0.7000 | 70000.0000 | 0.0040 | 0 | 0 | 0 | 0 | 0 |

## Split Coverage

| split | date_count | asset_count | factor_valid_observations | forward_return_valid_observations | ic_valid_dates | rank_ic_valid_dates | quantile_spread_valid_dates | mean_ic | mean_rank_ic |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| train | 1 | 3 | 0 | 3 | 0 | 0 | 0 | NaN | NaN |
| validation | 1 | 3 | 3 | 3 | 1 | 1 | 1 | -0.6217 | -0.5000 |
| test | 2 | 3 | 6 | 3 | 1 | 1 | 0 | 0.9997 | 0.8660 |

## Alpha#009 Diagnostic Coverage

| Diagnostic | Value |
| --- | ---: |
| Factor valid observations | `9` |
| Forward-return valid observations | `9` |
| Benchmark forward-return valid observations | `3` |
| IC valid dates | `2` |
| Rank IC valid dates | `2` |
| Quantile spread valid dates | `1` |

## Alpha#009 Information Coefficient Diagnostics

| Date | information_coefficient |
| --- | ---: |
| 2024-01-02 | NaN |
| 2024-01-03 | -0.6217 |
| 2024-01-04 | 0.9997 |
| 2024-01-05 | NaN |

## Alpha#009 Rank Information Coefficient Diagnostics

| Date | rank_information_coefficient |
| --- | ---: |
| 2024-01-02 | NaN |
| 2024-01-03 | -0.5000 |
| 2024-01-04 | 0.8660 |
| 2024-01-05 | NaN |

## Alpha#009 Quantile Spread Diagnostics

| Date | bottom_quantile_mean_return | top_quantile_mean_return | top_minus_bottom_spread | valid_asset_count | bottom_quantile_count | top_quantile_count |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2024-01-02 | NaN | NaN | NaN | 0 | 0 | 0 |
| 2024-01-03 | 0.0151 | 0.0074 | -0.0077 | 3 | 1 | 1 |
| 2024-01-04 | NaN | NaN | NaN | 3 | 0 | 0 |
| 2024-01-05 | NaN | NaN | NaN | 0 | 0 | 0 |

## Alpha#012 Diagnostic Coverage

`alpha_012` uses only the synthetic OHLCV dates and assets with available adjusted close and volume anchors. Missing OHLCV rows remain missing after alignment to the wider adjusted-close fixture. These diagnostics are feature-evaluation wiring checks only, not strategy validation.

| Diagnostic | Value |
| --- | ---: |
| Factor valid observations | `2` |
| Forward-return valid observations | `9` |
| IC valid dates | `1` |
| Rank IC valid dates | `1` |
| Quantile spread valid dates | `0` |

## Alpha#012 Information Coefficient Diagnostics

| Date | information_coefficient |
| --- | ---: |
| 2024-01-02 | NaN |
| 2024-01-03 | 1.0000 |
| 2024-01-04 | NaN |
| 2024-01-05 | NaN |

## Alpha#012 Rank Information Coefficient Diagnostics

| Date | rank_information_coefficient |
| --- | ---: |
| 2024-01-02 | NaN |
| 2024-01-03 | 1.0000 |
| 2024-01-04 | NaN |
| 2024-01-05 | NaN |

## Alpha#012 Quantile Spread Diagnostics

| Date | bottom_quantile_mean_return | top_quantile_mean_return | top_minus_bottom_spread | valid_asset_count | bottom_quantile_count | top_quantile_count |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2024-01-02 | NaN | NaN | NaN | 0 | 0 | 0 |
| 2024-01-03 | NaN | NaN | NaN | 2 | 0 | 0 |
| 2024-01-04 | NaN | NaN | NaN | 0 | 0 | 0 |
| 2024-01-05 | NaN | NaN | NaN | 0 | 0 | 0 |

## Limitations

- The CSV files are tiny synthetic fixtures committed for workflow testing.
- The inventory review is a metadata-only rehearsal and is not evidence that a user-provided local data bundle is research-ready.
- The benchmark is synthetic and used only to verify local CSV date alignment.
- The diagnostic returns are synthetic fixture calculations, not market evidence.
- The liquidity eligibility, universe-mask, and universe-masked signal counts are synthetic decision-date diagnostics, not tradeability evidence or backtest universe integration.
- The volume-aware slippage smoke diagnostic reports participation and capacity/cap counts only; it is not applied to returns and is not a trading-cost conclusion.
- `alpha_009` is a research feature, not a complete strategy.
- `alpha_012` is a research feature, not a complete strategy.
- The split metadata is a wiring check for the committed fixture, not a train/validation/test study on real data.
- No local CSV result here should be interpreted without the real-data readiness audit and full experiment-log requirements.
- User-provided local CSV research, universe construction, costs, slippage, and QuantConnect/LEAN implementation remain future stages.

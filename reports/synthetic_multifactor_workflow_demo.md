# Synthetic Multi-Factor Workflow Demo

This report uses synthetic data only. It is not real-market evidence, not financial advice, and not a profitability claim. It does not run a backtest, construct a portfolio, support live trading, connect to a broker, or fetch real data.

## Purpose

Demonstrate the research feature workflow on deterministic synthetic factor panels:

1. Generate synthetic factor panels.
2. Apply row-wise factor winsorization.
3. Apply cross-sectional z-score normalization.
4. Apply ordinal rank and pandas percentile-rank normalization.
5. Compute factor correlation diagnostics.
6. Combine z-scored factors with explicit weights.
7. Write a synthetic-only workflow report.

## Configuration

| Item | Value |
| --- | --- |
| Random seed | `20260528` |
| Asset count | `12` |
| Factor rows | `80` |
| Date range | `2024-01-02` to `2024-04-22` |
| Factor names | `synthetic_momentum, synthetic_quality, synthetic_reversal` |
| Winsorization quantiles | `0.05` / `0.95` |
| Combination weights | `synthetic_momentum=0.50, synthetic_quality=0.30, synthetic_reversal=0.20` |

## Processing Summary

The workflow generated synthetic factors, clipped each date's cross-section with explicit quantile bounds, transformed the clipped panels with z-score and rank-based normalization helpers, measured pairwise factor relationships, and combined the z-scored factors with explicit weights.

No missing values were filled. No dates or assets were reindexed. No strategy, return metric, order rule, or execution assumption was produced.

## Correlation Diagnostics

The matrix below is computed from flattened z-scored factor panels using the existing diagnostic helper.

| Factor | synthetic_momentum | synthetic_quality | synthetic_reversal |
| --- | ---: | ---: | ---: |
| synthetic_momentum | 1.0000 | -0.9841 | -0.9773 |
| synthetic_quality | -0.9841 | 1.0000 | 0.9771 |
| synthetic_reversal | -0.9773 | 0.9771 | 1.0000 |

## Combined Score Diagnostics

The combined score is a weighted synthetic research feature panel. It is not a portfolio, trade list, or strategy signal.

| Diagnostic | Value |
| --- | ---: |
| Rows | `80` |
| Assets | `12` |
| Mean | `0.0000` |
| Standard deviation | `0.0811` |
| Minimum | `-0.3164` |
| Maximum | `0.2658` |

## Limitations

- Synthetic factors are not calibrated to actual equities.
- The report is a workflow smoke demo only.
- No real data source, universe construction, transaction cost model, slippage model, benchmark, or validation split is used.
- No backtest integration or portfolio construction is included.
- Factor-to-backtest integration remains deferred until this synthetic workflow is reviewed.

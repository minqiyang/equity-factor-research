# Project Specification

## Objective

Build a rigorous, reproducible, auditable local Python research pipeline for a simulated cross-sectional equity factor strategy. The initial implementation should prioritize correctness, clear assumptions, and validation over performance or returns.

The project should eventually support a transparent local workflow and a platform-grade QuantConnect/LEAN implementation path.

## Initial Strategy Universe Assumptions

- Asset class: listed equities.
- Initial posture: long-only.
- Universe: liquid, tradeable equities with sufficient price and volume history.
- Liquidity filter: minimum dollar volume or average daily volume threshold.
- Data requirements: adjusted prices, volume, trading calendar, benchmark prices, and later optional fundamentals.
- Data handling: every feature must be available only after the data used to compute it would have been known.

The exact data source is intentionally not selected in this first phase.

## Initial Factor Ideas

- 12-1 month momentum: cumulative return over the prior 12 months excluding the most recent month.
- Short-term reversal: recent returns over a short lookback window, used as a contrarian signal or risk control.
- Realized volatility: trailing volatility filter to avoid extreme-risk names or scale exposure.
- Liquidity or volume: minimum tradeability screen based on volume or dollar volume.
- Optional later extensions: quality, value, profitability, leverage, or analyst revisions proxies if suitable point-in-time data is available.

## Backtesting Principles

- Use explicit rebalancing dates.
- Calculate features using only information available before portfolio formation.
- Apply trades after signals are known, not on the same close that generated them unless the execution assumption explicitly supports it.
- Include transaction costs, slippage, and turnover.
- Compare against a relevant benchmark.
- Record all parameters and assumptions for each experiment.
- Separate in-sample, validation, and test periods before evaluating strategy variations.
- Prefer simple baselines before complex models.
- Do not report only the best parameter result.

## Data Leakage Rules

- Never use future prices, future fundamentals, future membership, future corporate actions, or future benchmark data in a signal.
- Preserve date alignment between raw data, features, ranks, target returns, and portfolio weights.
- Lag features when necessary so that signal dates precede execution dates.
- Avoid survivorship bias by documenting universe construction and data limitations.
- Do not forward-fill values across dates where doing so would create information that was not actually available.
- Document every assumption about data availability, announcement timing, and execution timing.

## Evaluation Metrics

- Total return.
- Annualized return.
- Annualized volatility.
- Sharpe ratio, when appropriate and with stated assumptions.
- Maximum drawdown.
- Benchmark-relative return.
- Tracking error or active risk, if relevant.
- Hit rate and average holding-period return, if relevant.
- Turnover.
- Average number of holdings.
- Exposure concentration.
- Cost impact.

Metrics must be interpreted as simulated research output, not evidence of future performance.

## Transaction Cost and Slippage Assumptions

Initial default assumptions should be simple and explicit:

- Transaction cost: fixed basis-point cost per trade, applied to notional traded.
- Slippage: fixed basis-point estimate or volume-aware estimate once volume data is available.
- Rebalance cost: calculated from turnover at each rebalance.
- No market impact model in the first phase unless clearly justified.

Every experiment must state the cost and slippage model used. Zero-cost backtests should be treated as diagnostic only, not performance evidence.

## Development Phases

1. Create repository structure, governance documents, and minimal tests.
2. Implement 12-1 month momentum with unit tests for date alignment and missing data behavior.
3. Add additional feature modules for reversal, volatility, and liquidity.
4. Implement ranking, selection, and long-only portfolio construction.
5. Add backtest accounting, benchmark comparison, costs, slippage, turnover, and drawdown.
6. Add reporting charts and experiment export.
7. Add validation discipline with in-sample, validation, and test splits.
8. Add robustness checks and parameter sensitivity summaries.
9. Translate or mirror the core workflow in QuantConnect/LEAN.

## Explicit Non-Goals

- No live trading.
- No brokerage integration.
- No real-money execution.
- No black-box AI trading bot.
- No claims of profitability without reproducible evidence.
- No parameter mining presented as robust discovery.
- No external data fetching in the initial skeleton phase.
- No hidden manual edits to experiment results.

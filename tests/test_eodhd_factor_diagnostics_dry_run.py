from pathlib import Path

import pandas as pd

from research.eodhd_factor_diagnostics_dry_run import (
    EODHDFactorDiagnosticsConfig,
    run_eodhd_factor_diagnostics_dry_run,
)


def _write_ohlcv(path: Path, symbols: list[str], dates: pd.DatetimeIndex) -> Path:
    rows = ["date,symbol,open,high,low,close,adjusted_close,volume"]
    for date_index, date in enumerate(dates):
        for symbol_index, symbol in enumerate(symbols):
            base = 100 + symbol_index * 7 + date_index * (symbol_index + 1)
            rows.append(
                ",".join(
                    [
                        date.date().isoformat(),
                        symbol,
                        f"{base:.2f}",
                        f"{base + 1:.2f}",
                        f"{base - 1:.2f}",
                        f"{base + 0.5:.2f}",
                        f"{base + 0.5:.2f}",
                        str(1000 + 100 * symbol_index + 10 * date_index),
                    ]
                )
            )
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")
    return path


def test_eodhd_factor_diagnostics_dry_run_writes_private_summary(tmp_path: Path) -> None:
    dates = pd.date_range("2024-01-02", periods=9, freq="D")
    asset_path = _write_ohlcv(tmp_path / "asset_ohlcv.csv", ["AAA", "BBB", "CCC", "DDD"], dates)
    benchmark_path = _write_ohlcv(tmp_path / "benchmark_ohlcv.csv", ["SPY"], dates)
    output_path = tmp_path / "factor_diagnostics.md"

    result = run_eodhd_factor_diagnostics_dry_run(
        EODHDFactorDiagnosticsConfig(
            ohlcv_path=asset_path,
            benchmark_path=benchmark_path,
            output_path=output_path,
            alpha_window=1,
            quantiles=2,
            train_end="2024-01-04",
            validation_end="2024-01-06",
        )
    )

    assert output_path.is_file()
    assert result.asset_row_count == 36
    assert result.benchmark_row_count == 9
    assert result.symbol_count == 5
    assert set(result.factor_summary.index) == {"alpha_009", "alpha_012"}
    assert result.factor_summary["valid_observations"].gt(0).all()
    assert set(result.split_summary["split"]) == {"train", "validation", "test"}
    assert result.split_summary["ic_valid_dates"].ge(0).all()

    text = output_path.read_text(encoding="utf-8")
    assert "No strategy, backtest, portfolio construction, PnL, Sharpe, drawdown" in text
    assert "alpha_009" in text
    assert "alpha_012" in text

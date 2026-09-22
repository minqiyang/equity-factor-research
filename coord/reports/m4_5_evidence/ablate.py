"""Run isolated negative ablations of M4.5; production source remains unchanged."""

from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
TEST_UNIT = "tests/test_market_impact.py"
TEST_ENGINE = "tests/test_market_impact_engines.py"
TEST_DEMO = "tests/test_market_impact_capacity_demo.py"
MODEL = "market_impact.py"
# Each tuple names one removal, its independent counterexample, and exact edits.
VARIANTS = [
    (
        "lag",
        TEST_UNIT + "::test_lagged_full_windows_ddof_one_and_future_prefix",
        [(MODEL, ".shift(signal_lag_periods)", ".shift(0)")],
    ),
    (
        "basis",
        TEST_UNIT + "::test_basis_guard",
        [
            (
                MODEL,
                'if price_basis not in ("raw", "split_adjusted") or price_basis != volume_basis:',
                "if False:",
            )
        ],
    ),
    (
        "adv_minimum",
        TEST_UNIT + "::test_active_trade_adv_guard_and_zero_trade_skip",
        [(MODEL, "if not _finite_real(value) or value < model.min_adv:", "if False:")],
    ),
    (
        "volatility_ddof",
        TEST_UNIT + "::test_lagged_full_windows_ddof_one_and_future_prefix",
        [(MODEL, ".std(ddof=1)", ".std(ddof=0)")],
    ),
    (
        "raise_cap",
        TEST_UNIT + "::test_modes_and_quadratic_total_penalty",
        [(MODEL, 'if model.mode == "raise" and np.any(q > caps):', "if False:")],
    ),
    (
        "throttle_cap",
        TEST_UNIT + "::test_modes_and_quadratic_total_penalty",
        [(MODEL, 'if model.mode == "throttle":', "if False:")],
    ),
    (
        "penalize_policy",
        TEST_UNIT + "::test_modes_and_quadratic_total_penalty",
        [(MODEL, 'if model.mode == "penalize":', "if False:")],
    ),
    (
        "eta_coefficient",
        TEST_UNIT + "::test_scalar_square_root_oracle",
        [(MODEL, "model.eta * sigma * np.sqrt(participation)", "0.0 * sigma")],
    ),
    (
        "fixed_coefficient",
        TEST_UNIT + "::test_scalar_square_root_oracle",
        [(MODEL, "model.fixed_bps / 10000.0", "0.0")],
    ),
    (
        "penalty_coefficient",
        TEST_UNIT + "::test_modes_and_quadratic_total_penalty",
        [(MODEL, "model.penalty_bps / 10000.0", "0.0")],
    ),
    (
        "cash_funding",
        TEST_UNIT + "::test_initial_cash_funding_independent_root_and_cost_accounting",
        [(MODEL, "if buy_outlay(scale)[0] > available:", "if False:")],
    ),
    (
        "cash_balance_guard",
        TEST_UNIT + "::test_cash_and_position_input_balance_refused",
        [
            (
                MODEL,
                "if not math.isclose(balance, equity_before, rel_tol=1e-12, abs_tol=1e-12):",
                "if False:",
            )
        ],
    ),
    (
        "execution_volume",
        TEST_UNIT + "::test_zero_current_volume_refuses_actual_fills",
        [
            (
                MODEL,
                "if observed_volume.isna().any() or observed_volume.le(0).any():",
                "if False:",
            )
        ],
    ),
    (
        "terminal_exemption",
        TEST_ENGINE + "::test_terminal_cash_exemption_and_pending_cancellation",
        [
            (
                "portfolio.py",
                "pretrade_weights.loc[list(terminal_returns)] = 0.0",
                "pretrade_weights.loc[list(terminal_returns)] = pretrade_weights.loc[list(terminal_returns)]",
            ),
            (
                "long_short.py",
                "pretrade_net.loc[list(terminal_returns)] = 0.0",
                "pretrade_net.loc[list(terminal_returns)] = pretrade_net.loc[list(terminal_returns)]",
            ),
        ],
    ),
    (
        "long_only_sell_bound",
        TEST_DEMO + "::test_changing_price_cohort_throttle_remains_long_only",
        [("portfolio.py", "allow_short=False", "allow_short=True")],
    ),
    (
        "unscaled_buy_copy",
        TEST_UNIT + "::test_all_buy_cash_and_cost_reconciliation",
        [
            (
                MODEL,
                "executed.loc[buys].to_numpy(dtype=float, copy=True)",
                "executed.loc[buys].to_numpy(dtype=float)",
            )
        ],
    ),
    (
        "post_trade_balance_guard",
        TEST_UNIT + "::test_post_trade_balance_guard_refuses_absolute_mismatch",
        [(MODEL, "or abs(post_trade_balance - equity_after) > 1e-6", "or False")],
    ),
]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(output: Path):
    output.mkdir(parents=True, exist_ok=True)
    originals = {
        name: digest(ROOT / "src/backtest" / name)
        for name in (MODEL, "portfolio.py", "long_short.py")
    }
    cases = [("baseline", " ".join((TEST_UNIT, TEST_ENGINE, TEST_DEMO)), [])] + VARIANTS
    records = []
    for name, selection, edits in cases:
        isolated = output / name
        if isolated.exists():
            raise ValueError(f"preserve existing ablation evidence: {isolated}")
        package = isolated / "src/backtest"
        shutil.copytree(
            ROOT / "src/backtest", package, ignore=shutil.ignore_patterns("__pycache__")
        )
        for filename, old, new in edits:
            path = package / filename
            content = path.read_text()
            if old not in content:
                raise ValueError(f"missing mutation anchor: {name}/{filename}")
            path.write_text(content.replace(old, new))
        environment = dict(
            os.environ,
            PYTHONPATH=os.pathsep.join(
                (str(isolated / "src"), str(ROOT / "src"), str(ROOT))
            ),
        )
        environment.update(
            {
                key: "1"
                for key in (
                    "OMP_NUM_THREADS",
                    "OPENBLAS_NUM_THREADS",
                    "MKL_NUM_THREADS",
                    "BLIS_NUM_THREADS",
                    "VECLIB_MAXIMUM_THREADS",
                    "NUMEXPR_NUM_THREADS",
                )
            }
        )
        imported = subprocess.check_output(
            [
                sys.executable,
                "-c",
                "import backtest.market_impact as m;print(m.__file__)",
            ],
            cwd=isolated,
            env=environment,
            text=True,
        ).strip()
        if Path(imported) != package / MODEL:
            raise RuntimeError("ablation import escaped its isolated copy")
        command = [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "-o",
            "pythonpath=",
            *selection.split(),
        ]
        start = time.monotonic()
        process = subprocess.run(
            command,
            cwd=ROOT,
            env=environment,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        log = isolated / "pytest.txt"
        log.write_text(process.stdout)
        records.append(
            dict(
                name=name,
                expected_exit=0 if name == "baseline" else 1,
                observed_exit=process.returncode,
                seconds=time.monotonic() - start,
                selected_tests=selection,
                log_sha256=digest(log),
                source_sha256={file: digest(package / file) for file in originals},
                edits=[
                    dict(file=file, before=old, after=new) for file, old, new in edits
                ],
            )
        )
        print(name, process.returncode, flush=True)
    preserved = originals == {
        name: digest(ROOT / "src/backtest" / name) for name in originals
    }
    result = dict(
        production_sources_preserved=preserved,
        baseline_sources=originals,
        cases=records,
    )
    (output / "results.json").write_text(json.dumps(result, indent=2) + "\n")
    if not preserved or any(
        case["expected_exit"] != case["observed_exit"] for case in records
    ):
        raise RuntimeError("ablation has an unexpected outcome; inspect retained logs")


if __name__ == "__main__":
    main(Path(sys.argv[1]).resolve())

import dataclasses
import hashlib
import gzip
import json
import sys
import time
from pathlib import Path
import numpy as np
import pandas as pd
from research.multifactor_diagnostic_mvp import run_multifactor_diagnostic_mvp
from research.pit_universe_delisting_demo import run_pit_universe_delisting_demo

LEGACY = "--legacy" in sys.argv
NEW_FIELDS = {"risk_attribution"}
if LEGACY:
    NEW_FIELDS.update({"slippage_cost_series", "realized_slippage_bps", "trade_participation_rates",
                       "executed_trade_values", "pending_trade_shares", "cancelled_trade_shares"})


def scalar(value):
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if isinstance(value, np.generic):
        return value.item()
    if dataclasses.is_dataclass(value):
        return dataclasses.asdict(value)
    raise TypeError(type(value).__name__)


def capture(book):
    result = {}
    for field in dataclasses.fields(book):
        if field.name in NEW_FIELDS:
            continue
        value = getattr(book, field.name)
        if isinstance(value, (pd.Series, pd.DataFrame)):
            result[field.name] = {
                "hash": hashlib.sha256(
                    pd.util.hash_pandas_object(value, index=True).values.tobytes()
                ).hexdigest(),
                "shape": value.shape,
                "index_name": value.index.name,
                "columns": list(value.columns)
                if isinstance(value, pd.DataFrame)
                else value.name,
            }
            if not LEGACY:
                result[field.name].update({
                "dtypes": [str(v) for v in value.dtypes] if isinstance(value, pd.DataFrame) else str(value.dtype),
                "raw_values_sha256": hashlib.sha256(value.to_numpy().tobytes()).hexdigest(),
                "index": [scalar(v) if isinstance(v, pd.Timestamp) else v for v in value.index],
                "columns_name": value.columns.name if isinstance(value, pd.DataFrame) else None,
                })
        else:
            result[field.name] = value
    return result


start = time.monotonic()
r = run_multifactor_diagnostic_mvp(write_outputs=False)
result = {
    k: r[k]
    for k in [
        "pbo_summary",
        "trial_family",
        "weighting_comparisons",
        "multiple_testing",
    ]
}
result["factors"] = {
    factor: {
        "dsr": data["dsr"],
        "backtest": capture(data["backtest"]),
        "long_short_backtest": capture(data["long_short_backtest"]),
    }
    for factor, data in r["factors"].items()
}
result["pit_demo"] = run_pit_universe_delisting_demo(write_outputs=False)
path = Path(sys.argv[1])
payload = json.dumps(result, default=scalar, sort_keys=True, indent=2).encode()
path.write_bytes(gzip.compress(payload, mtime=0) if path.suffix == ".gz" else payload)
print(
    json.dumps(
        {
            "output": str(path),
            "seconds": time.monotonic() - start,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        }
    )
)

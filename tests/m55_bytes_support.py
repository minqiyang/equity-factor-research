"""Byte comparison against the code at main 8590b2e, before card m55-confirm (trial family v1 amendment 3).

The runner, the engine, and the driver must give the same bytes as before when the half-spread override is not
used. ``module_at`` builds a module from the file bytes at a commit (CI checks out the full history), and
``assert_same_bytes`` compares two outputs field by field.
"""

from __future__ import annotations

import dataclasses
import importlib.util
import struct
import subprocess
import sys
import types
from pathlib import Path

import numpy as np
import pandas as pd


BASE_COMMIT = "8590b2e9ca11513cf9f5aa2c552e1d6a9f6d3925"   # main before the per-asset rates


def module_at(commit: str, path: str, name: str, tmp_path) -> types.ModuleType:
    """A module built from the bytes of ``path`` at ``commit`` (CI checks out the full history)."""
    root = Path(__file__).resolve().parents[1]
    source = subprocess.run(["git", "show", f"{commit}:{path}"], cwd=root, capture_output=True, check=True).stdout
    file = tmp_path / f"{name}.py"
    file.write_bytes(source)
    spec = importlib.util.spec_from_file_location(name, file)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def assert_same_bytes(a: object, b: object, where: str = "result") -> None:
    """Equal structure and equal bytes of every float; NaN cells must hold the same bits."""
    if dataclasses.is_dataclass(a) and not isinstance(a, type):
        names = [f.name for f in dataclasses.fields(a)]
        assert names == [f.name for f in dataclasses.fields(b)], where
        for name in names:
            assert_same_bytes(getattr(a, name), getattr(b, name), f"{where}.{name}")
    elif isinstance(a, pd.DataFrame):
        assert isinstance(b, pd.DataFrame) and a.index.equals(b.index) and a.columns.equals(b.columns), where
        assert list(a.dtypes) == list(b.dtypes), where
        for column in a.columns:
            assert_same_bytes(a[column].to_numpy(), b[column].to_numpy(), f"{where}[{column}]")
    elif isinstance(a, pd.Series):
        assert isinstance(b, pd.Series) and a.index.equals(b.index) and a.name == b.name, where
        assert_same_bytes(a.to_numpy(), b.to_numpy(), where)
    elif isinstance(a, np.ndarray):
        assert isinstance(b, np.ndarray) and a.dtype == b.dtype and a.shape == b.shape, where
        if a.dtype.kind in "biufcmM":
            assert a.tobytes() == b.tobytes(), where
        else:
            for k, (x, y) in enumerate(zip(a.ravel(), b.ravel())):
                assert_same_bytes(x, y, f"{where}[{k}]")
    elif isinstance(a, dict):
        assert isinstance(b, dict) and list(a) == list(b), where
        for key in a:
            assert_same_bytes(a[key], b[key], f"{where}.{key}")
    elif isinstance(a, (list, tuple)):
        assert type(a) is type(b) and len(a) == len(b), where
        for k, (x, y) in enumerate(zip(a, b)):
            assert_same_bytes(x, y, f"{where}[{k}]")
    elif isinstance(a, float):
        assert isinstance(b, float) and struct.pack("<d", a) == struct.pack("<d", b), where
    else:
        assert type(a) is type(b) and (a == b or (a is pd.NaT and b is pd.NaT)), where

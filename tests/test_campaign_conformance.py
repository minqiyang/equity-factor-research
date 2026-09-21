"""PR 3 repo-integration conformance: T-7, no-default, fixture-JSON, CI."""

from __future__ import annotations

import ast
import dataclasses
import hashlib
import importlib
import inspect
from pathlib import Path
import pkgutil

from campaign.inference import FACTOR_ORDER
from campaign_runner_v1_support import (
    CAMPAIGN_ROOT,
    collect_disallowed_factor_id_literals,
    collect_disallowed_factor_id_literals_from_source,
    load_runner_fixture,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TEST_ROOT = PROJECT_ROOT / "tests"
CI_WORKFLOW = PROJECT_ROOT / ".github" / "workflows" / "ci.yml"

# Reviewed empty allowance. Adding a default is a reviewable diff.
NON_SEMANTIC_DEFAULT_ALLOWANCE: tuple[tuple[str, str, str], ...] = ()


def _parent_map(tree: ast.AST) -> dict[ast.AST, ast.AST]:
    parents: dict[ast.AST, ast.AST] = {}
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            parents[child] = node
    return parents


def _call_name(func: ast.AST) -> str | None:
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return None


def _is_index_or_fixture_numeric(
    node: ast.Constant,
    parents: dict[ast.AST, ast.AST],
) -> bool:
    cursor: ast.AST = node
    parent = parents.get(cursor)
    if isinstance(parent, ast.UnaryOp):
        cursor = parent
        parent = parents.get(cursor)
    if isinstance(parent, ast.Slice):
        return True
    if isinstance(parent, ast.Subscript):
        return parent.value is not cursor
    if isinstance(parent, ast.keyword) and parent.arg == "indent":
        return True
    if isinstance(parent, ast.Call):
        name = _call_name(parent.func)
        if name in {"split", "rsplit", "range", "enumerate"}:
            return True
    if isinstance(parent, ast.Compare) and node.value in {0, 0.0}:
        return True
    if (
        isinstance(parent, ast.BinOp)
        and isinstance(parent.op, ast.BitXor)
        and node.value in {0, 1}
    ):
        return True
    return False


def _runner_test_paths() -> tuple[Path, ...]:
    paths: list[Path] = []
    for path in sorted(TEST_ROOT.glob("test_campaign_*.py")):
        if path.name in {
            "test_campaign_conformance.py",
            "test_campaign_import_boundaries.py",
        }:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        imported = {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
            for alias in node.names
        }
        imported.update(
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        )
        if (
            "campaign_runner_v1_support" in imported
            or "load_runner_fixture" in imported
        ):
            paths.append(path)
    return tuple(paths)


def test_t7_owner_uniqueness_conformance_scan() -> None:
    assert collect_disallowed_factor_id_literals(FACTOR_ORDER) == ()
    owner = CAMPAIGN_ROOT / "inference.py"
    tree = ast.parse(owner.read_text(encoding="utf-8"), filename=owner.name)
    assignments = [
        node
        for node in tree.body
        if isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
        and node.targets[0].id == "FACTOR_ORDER"
    ]
    assert len(assignments) == 1


def test_t7_scan_flags_a_disallowed_literal_and_ignores_docstrings() -> None:
    factor_id = FACTOR_ORDER[0]
    disallowed = collect_disallowed_factor_id_literals_from_source(
        f"LABEL = {factor_id!r}\n",
        "registry.py",
        FACTOR_ORDER,
    )
    assert disallowed
    assert disallowed[0][1] == factor_id
    docstring_only = collect_disallowed_factor_id_literals_from_source(
        f'"""Owner prose may mention {factor_id}."""\n',
        "factors.py",
        FACTOR_ORDER,
    )
    assert docstring_only == ()
    owner_site = collect_disallowed_factor_id_literals_from_source(
        "FACTOR_ORDER = ("
        + ", ".join(repr(item) for item in FACTOR_ORDER)
        + ")\n",
        "inference.py",
        FACTOR_ORDER,
    )
    assert owner_site == ()


def test_public_campaign_api_declares_no_semantic_defaults() -> None:
    import campaign

    observed: list[tuple[str, str, str]] = []
    for info in pkgutil.iter_modules(campaign.__path__):
        module = importlib.import_module(f"campaign.{info.name}")
        for name, obj in inspect.getmembers(module):
            if name.startswith("_"):
                continue
            if inspect.isfunction(obj) and obj.__module__ == module.__name__:
                targets = ((f"{module.__name__}.{name}", obj),)
            elif inspect.isclass(obj) and obj.__module__ == module.__name__:
                targets = ((f"{module.__name__}.{name}", obj),)
                if dataclasses.is_dataclass(obj):
                    targets = targets + (
                        (f"{module.__name__}.{name}.__init__", obj),
                    )
            else:
                continue
            for label, target in targets:
                try:
                    signature = inspect.signature(target)
                except (TypeError, ValueError):
                    continue
                for parameter in signature.parameters.values():
                    if parameter.name in {"self", "cls"}:
                        continue
                    if parameter.default is inspect.Parameter.empty:
                        continue
                    key = (module.__name__, name, parameter.name)
                    if key not in NON_SEMANTIC_DEFAULT_ALLOWANCE:
                        observed.append(key)
            if inspect.isclass(obj) and obj.__module__ == module.__name__:
                for attr_name, attr in inspect.getmembers(obj):
                    if attr_name.startswith("_") or not inspect.isfunction(attr):
                        continue
                    for parameter in inspect.signature(attr).parameters.values():
                        if parameter.name in {"self", "cls"}:
                            continue
                        if parameter.default is inspect.Parameter.empty:
                            continue
                        key = (module.__name__, attr_name, parameter.name)
                        if key not in NON_SEMANTIC_DEFAULT_ALLOWANCE:
                            observed.append(key)
    assert observed == []
    assert NON_SEMANTIC_DEFAULT_ALLOWANCE == ()


def test_runner_tests_define_no_local_protocol_callables() -> None:
    hits: list[tuple[str, int, str]] = []
    for path in _runner_test_paths():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in tree.body:
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if not node.name.startswith("test_"):
                continue
            for child in ast.walk(node):
                if child is node:
                    continue
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    hits.append((path.name, child.lineno, child.name))
                elif isinstance(child, ast.Lambda):
                    hits.append((path.name, child.lineno, "<lambda>"))
    assert hits == []


def test_runner_tests_keep_numeric_literals_in_fixtures_or_index_arithmetic() -> None:
    hits: list[tuple[str, int, object]] = []
    for path in _runner_test_paths():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        parents = _parent_map(tree)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Constant):
                continue
            if not isinstance(node.value, (int, float)):
                continue
            if isinstance(node.value, bool):
                continue
            if _is_index_or_fixture_numeric(node, parents):
                continue
            hits.append((path.name, node.lineno, node.value))
    assert hits == []


def test_campaign_source_contains_no_hex_digest_literals() -> None:
    digest_width = len(hashlib.sha256(b"").hexdigest())
    hits: list[tuple[str, int]] = []
    for module_path in sorted(CAMPAIGN_ROOT.glob("*.py")):
        tree = ast.parse(
            module_path.read_text(encoding="utf-8"),
            filename=str(module_path),
        )
        for node in ast.walk(tree):
            if not isinstance(node, ast.Constant):
                continue
            if not isinstance(node.value, str):
                continue
            if len(node.value) != digest_width:
                continue
            if all(character in "0123456789abcdefABCDEF" for character in node.value):
                hits.append((module_path.name, node.lineno))
    assert hits == []


def test_ci_runs_only_committed_synthetic_campaign_fixtures() -> None:
    workflow = CI_WORKFLOW.read_text(encoding="utf-8")
    lowered = workflow.lower()
    assert "name: python validation" in lowered
    assert "python -m pytest -q" in workflow
    assert workflow.count("python -m pytest -q") == 1
    assert "-n 2 --dist worksteal" in workflow
    assert "--max-worker-restart=0" in workflow
    for env_var in (
        'OMP_NUM_THREADS: "1"',
        'OPENBLAS_NUM_THREADS: "1"',
        'MKL_NUM_THREADS: "1"',
        'BLIS_NUM_THREADS: "1"',
        'VECLIB_MAXIMUM_THREADS: "1"',
        'NUMEXPR_NUM_THREADS: "1"',
    ):
        assert env_var in workflow
    assert "python_files=test_campaign_*.py" not in workflow
    assert "committed synthetic fixtures" in lowered
    assert "not result-bearing" in lowered
    assert "private panel" in lowered
    for forbidden in (
        "private_data",
        "performance_access",
        "result_access",
        "fourteen_trial",
        "14-trial",
        "eodhd.com",
    ):
        assert forbidden not in lowered


def test_t8_owner_file_bytes_remain_frozen() -> None:
    fixture = load_runner_fixture("reuse_as_is_file_bytes.json")
    digest = hashlib.sha256(
        (PROJECT_ROOT / "src/campaign/inference.py").read_bytes()
    ).hexdigest()
    assert digest == fixture["expected"]["file_bytes"]["src/campaign/inference.py"]

"""Structural checks for the Milestone 5 factor catalog (research/factor_catalog.csv)."""

from __future__ import annotations

import csv
from pathlib import Path
import re

from research.m4_7_family_a import FAMILY_A_IDS

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CATALOG = PROJECT_ROOT / "research" / "factor_catalog.csv"
COLUMNS = ["id", "source", "formula_or_ref", "inputs", "horizon", "status"]
STATUSES = {"cataloged", "implemented"}
INPUTS = {
    "ohlcv", "price", "accounting", "analyst", "options", "holdings_13f",
    "event", "trading", "return_series", "other",
}
HORIZONS = {"daily", "weekly", "monthly", "quarterly", "annual"}
CJK_CHARACTERS = re.compile("[\u3000-\u303f\u3400-\u9fff\uf900-\ufaff\uff00-\uffef]")


def _load() -> tuple[list[str], list[dict[str, str]]]:
    with CATALOG.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or []), list(reader)


def test_catalog_has_exact_columns_and_about_one_thousand_rows() -> None:
    columns, rows = _load()
    assert columns == COLUMNS
    assert 1000 <= len(rows) <= 1300
    assert all(row[column] for row in rows for column in COLUMNS), "empty catalog cell"


def test_catalog_ids_are_unique_ascii_and_prefixed_by_source() -> None:
    _, rows = _load()
    ids = [row["id"] for row in rows]
    assert len(ids) == len(set(ids))
    assert len({identifier.lower() for identifier in ids}) == len(ids), "ids differ only by case"
    assert all(re.fullmatch(r"[a-z0-9]+\.[A-Za-z0-9_]+", identifier) for identifier in ids)
    prefixes_by_source: dict[str, set[str]] = {}
    for row in rows:
        prefixes_by_source.setdefault(row["source"], set()).add(row["id"].split(".", 1)[0])
    assert all(len(prefixes) == 1 for prefixes in prefixes_by_source.values()), prefixes_by_source


def test_catalog_values_are_in_the_allowed_sets() -> None:
    _, rows = _load()
    assert {row["status"] for row in rows} <= STATUSES
    assert {row["inputs"] for row in rows} <= INPUTS
    assert {row["horizon"] for row in rows} <= HORIZONS


def test_implemented_worldquant_rows_match_alpha_functions_exactly() -> None:
    _, rows = _load()
    source = (PROJECT_ROOT / "src" / "features" / "alphas.py").read_text(encoding="utf-8")
    functions = set(re.findall(r"^def (alpha_\d{3})\(", source, re.MULTILINE))
    implemented = {row["id"].removeprefix("wq101.") for row in rows
                   if row["id"].startswith("wq101.") and row["status"] == "implemented"}
    assert implemented == functions
    assert len(implemented) == 52
    assert {row["id"] for row in rows if row["id"].startswith("wq101.")} == {
        f"wq101.alpha_{number:03d}" for number in range(1, 102)
    }


def test_implemented_rows_are_exactly_worldquant_functions_and_family_a() -> None:
    _, rows = _load()
    family_a = {row["id"].removeprefix("repo.") for row in rows if row["source"] == "Repository Family A"}
    assert family_a == set(FAMILY_A_IDS)
    implemented_sources = {row["source"] for row in rows if row["status"] == "implemented"}
    assert implemented_sources == {"WorldQuant 101 (Kakushadze 2016)", "Repository Family A"}
    assert all(row["status"] == "implemented" for row in rows if row["source"] == "Repository Family A")


def test_catalog_text_is_ascii_without_chinese_characters() -> None:
    text = CATALOG.read_text(encoding="utf-8")
    assert not CJK_CHARACTERS.search(text)
    assert text.isascii()

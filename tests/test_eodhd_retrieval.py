"""Offline tests for ``data.eodhd_retrieval`` (M4.7 plan 1.3, 7.2 a-1: T-RET-1..17).

Every test drives the CLI through the injected transport seam; no test opens
a network connection.
"""

from __future__ import annotations

import dataclasses
import http.client
import io
import json
import traceback
import urllib.error
import urllib.parse
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import pytest

from data import eodhd_retrieval as retrieval
from data import holdout_partition
from data.eodhd_retrieval import (
    DATA_DIR_ENV,
    TOKEN_ENV,
    TOKEN_MISSING_MESSAGE,
    RetrievalTransportError,
    _request,
    main,
    split_ratio,
)
from data.holdout_partition import (
    RETRIEVAL_ORDER,
    SnapshotRefusal,
    read_authorized_bytes,
    read_authorized_parquet,
    write_prospective_seal,
)
from data.parquet_loader import (
    compute_cumulative_split_factor,
    load_eod_cohort_panels,
    load_eod_parquet,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TOKEN = "Se/cr et+tok=en&42"
TOKEN_FORMS = {
    TOKEN,
    urllib.parse.quote(TOKEN),
    urllib.parse.quote(TOKEN, safe=""),
    urllib.parse.quote_plus(TOKEN),
}
MEMBERS = ("AAA", "BBB", "CCC")
CODES = ("AAA.US", "BBB.US", "CCC.US", "SPY.US")
HOLDOUT_END = "2003-12-31"
CALENDAR = [
    day.isoformat()
    for day in (date(2003, 11, 3) + timedelta(days=offset) for offset in range(241))
    if day.weekday() < 5
]
FIRST_DISCOVERY = CALENDAR.index(HOLDOUT_END)
SATURDAY = "2004-02-07"


class Interrupt(BaseException):
    """Simulated process interruption; ``main`` catches ``Exception`` only."""


def bar(day: str, close: float = 100.0, adjusted: float | None = None, **fields) -> dict:
    row = {
        "date": day,
        "open": close,
        "high": close,
        "low": close,
        "close": close,
        "adjusted_close": close if adjusted is None else adjusted,
        "volume": 1000,
    }
    row.update(fields)
    return row


def body(payload) -> bytes:
    return json.dumps(payload).encode("utf-8")


def components_body(entries: list[dict] | None = None) -> bytes:
    if entries is None:
        entries = [
            {
                "Code": code,
                "Name": f"{code} Inc",
                "StartDate": "1993-12-15",
                "EndDate": None,
                "IsActiveNow": 1,
                "IsDelisted": 0,
            }
            for code in MEMBERS
        ]
    return body({"General": {"Code": "GSPC"}, "HistoricalTickerComponents": {str(i): e for i, e in enumerate(entries)}})


class FakeVendor:
    """Route table keyed by endpoint path; records every full URL it receives."""

    def __init__(self) -> None:
        self.urls: list[str] = []
        self.routes: dict[str, object] = {
            "fundamentals/GSPC.INDX": components_body(),
            "exchange-symbol-list/US?delisted=0": body(
                [{"Code": "AAA", "Name": "AAA Inc", "Exchange": "NYSE", "Type": "Common Stock", "Isin": "US0000000001"}]
            ),
            "exchange-symbol-list/US?delisted=1": body([]),
            "eod/GSPC.INDX": body([{"date": day, "close": 1000.0 + i} for i, day in enumerate(CALENDAR)]),
        }
        for code in CODES:
            self.routes[f"eod/{code}"] = body([bar(day) for day in CALENDAR])
            self.routes[f"splits/{code}"] = body([])
            self.routes[f"div/{code}"] = body([])

    def __call__(self, url: str) -> bytes:
        self.urls.append(url)
        parts = urllib.parse.urlsplit(url)
        key = parts.path.removeprefix("/api/")
        query = urllib.parse.parse_qs(parts.query)
        if "delisted" in query:
            key += f"?delisted={query['delisted'][0]}"
        response = self.routes.get(key, 404)
        if isinstance(response, list):
            response = response.pop(0) if len(response) > 1 else response[0]
        if callable(response):
            response = response(url)
        if isinstance(response, BaseException):
            raise response
        if isinstance(response, int):
            raise urllib.error.HTTPError(url, response, "vendor error", {}, io.BytesIO(b'{"error":"vendor"}'))
        return response

    def paths(self) -> list[str]:
        return [urllib.parse.urlsplit(url).path.removeprefix("/api/") for url in self.urls]


class Clock:
    def __init__(self) -> None:
        self.value = datetime(2026, 9, 25, 12, 0, 0, tzinfo=timezone.utc)

    def __call__(self) -> datetime:
        return self.value

    def advance(self, **delta) -> None:
        self.value += timedelta(**delta)


class Harness:
    def __init__(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, name: str = "private") -> None:
        monkeypatch.setenv(TOKEN_ENV, TOKEN)
        self.data_dir = tmp_path / name
        monkeypatch.setenv(DATA_DIR_ENV, str(self.data_dir))
        # Three synthetic members stand in for the 470..530 band of plan 1.4.
        monkeypatch.setattr(holdout_partition, "BAND", (2, 4))
        monkeypatch.setattr(holdout_partition, "HARD_BAND", (1, 5))
        self.tmp_path = tmp_path
        self.vendor = FakeVendor()
        self.clock = Clock()
        self.sleeps: list[float] = []
        self.snapshot_dir = self.data_dir / "sp500_pit_T1"

    def run(self, command: str, *extra: str) -> int:
        self.clock.advance(seconds=1)
        return main(
            [command, "--snapshot-id", "T1", "--data-dir", str(self.data_dir), "--requests-per-minute", "6000000", *extra],
            transport=self.vendor,
            clock=self.clock,
            sleep=self.sleeps.append,
        )

    def seal(self) -> None:
        write_prospective_seal(
            self.snapshot_dir,
            sealed_at="2026-09-25T12:00:00Z",
            sealing_actor="test",
            authorization_reference="test",
        )

    def prepare(self, *, calendar: bool = True) -> None:
        assert self.run("components") == 0
        assert self.run("symbols") == 0
        self.seal()
        if calendar:
            assert self.run("calendar") == 0

    def full(self) -> None:
        self.prepare()
        for command in ("splits", "eod", "dividends"):
            assert self.run(command) == 0

    def manifest(self) -> dict:
        return json.loads((self.snapshot_dir / "manifest.json").read_bytes())

    def entry(self, table: str, code: str) -> dict:
        return self.manifest()["entries"][f"{table}/{code}"]

    def frame(self, table: str, code: str, role: str) -> pd.DataFrame:
        record = self.entry(table, code)["authorized_files"][role]
        return read_authorized_parquet(self.snapshot_dir, record["path"])

    def path(self, table: str, code: str, role: str) -> Path:
        return self.snapshot_dir / self.entry(table, code)["authorized_files"][role]["path"]

    def codes_file(self, *codes: str) -> str:
        path = self.tmp_path / f"codes_{'_'.join(codes)}.txt"
        path.write_text("\n".join(codes) + "\n", encoding="utf-8")
        return str(path)

    def verify(self) -> dict:
        self.run("verify")
        return self.manifest()["verify"]


@pytest.fixture(autouse=True)
def no_live_network(monkeypatch: pytest.MonkeyPatch) -> None:
    def refuse(*args, **kwargs):
        raise AssertionError("live network access attempted in a test")

    monkeypatch.setattr(retrieval.urllib.request, "urlopen", refuse)


@pytest.fixture
def harness(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Harness:
    return Harness(tmp_path, monkeypatch)


def split_step_bars(split_day: str) -> list[dict]:
    """A 2-for-1 split: close / adjusted_close steps from 2 to 1 at ``split_day``."""

    return [
        bar(day, close=200.0, adjusted=100.0) if day < split_day else bar(day, close=100.0, adjusted=100.0)
        for day in CALENDAR
    ]


# ---------------------------------------------------------------- T-RET-1


@pytest.mark.parametrize("value", [None, "", "   "])
def test_t_ret_1_token_absent_exits_2_with_fixed_message(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], value: str | None
) -> None:
    if value is None:
        monkeypatch.delenv(TOKEN_ENV, raising=False)
    else:
        monkeypatch.setenv(TOKEN_ENV, value)
    monkeypatch.setenv(DATA_DIR_ENV, str(tmp_path / "private"))
    vendor = FakeVendor()
    assert main(["components", "--snapshot-id", "T1"], transport=vendor) == 2
    assert capsys.readouterr().err.strip() == TOKEN_MISSING_MESSAGE
    assert vendor.urls == []
    assert not (tmp_path / "private").exists()


# ---------------------------------------------------------------- T-RET-2


def _assert_token_free(text: str | bytes, where: str) -> None:
    for form in TOKEN_FORMS:
        needle = form.encode("utf-8") if isinstance(text, bytes) else form
        assert needle not in text, f"token form {form!r} leaked into {where}"


def test_t_ret_2_request_sanitizes_http_error_without_chaining() -> None:
    def transport(url: str) -> bytes:
        raise urllib.error.HTTPError(url, 500, f"boom {url}", {}, io.BytesIO(f"echo {TOKEN}".encode()))

    with pytest.raises(RetrievalTransportError) as caught:
        _request("https://eodhd.com/api/eod/AAA.US?fmt=json", TOKEN, timeout=1, transport=transport)
    error = caught.value
    assert error.status == 500 and error.typed_outcome == "provider_error"
    assert error.__cause__ is None and error.__context__ is None
    assert "<redacted>" in error.sanitized_message
    rendered = "".join(traceback.format_exception(error)) + repr(error.args) + str(error)
    _assert_token_free(rendered, "exception")
    _assert_token_free(error.body, "exception body")

    for raised in (urllib.error.URLError(f"down {TOKEN}"), TimeoutError(TOKEN), OSError(TOKEN)):
        with pytest.raises(RetrievalTransportError) as caught:
            _request("https://eodhd.com/api/x?fmt=json", TOKEN, timeout=1, transport=lambda url, e=raised: (_ for _ in ()).throw(e))
        assert caught.value.__context__ is None
        _assert_token_free("".join(traceback.format_exception(caught.value)), "exception")


def test_t_ret_2_no_written_byte_log_or_stream_holds_the_token(
    harness: Harness, capsys: pytest.CaptureFixture[str]
) -> None:
    harness.vendor.routes["splits/BBB.US"] = 500
    harness.vendor.routes["div/CCC.US"] = lambda url: urllib.error.HTTPError(
        url, 404, f"no symbol {url}", {}, io.BytesIO(f"unknown token {TOKEN}".encode())
    )
    harness.prepare()
    assert harness.run("splits", "--retries", "1") == 0
    assert harness.run("eod", "--debug") == 0
    assert harness.run("dividends") == 0
    assert harness.run("verify") == 0
    harness.vendor.routes["fundamentals/GSPC.INDX"] = 401
    other = harness.data_dir / "sp500_pit_T2"
    assert main(["components", "--snapshot-id", "T2", "--debug"], transport=harness.vendor, clock=harness.clock) == 1

    assert harness.vendor.urls and all(urllib.parse.quote(TOKEN, safe="") in url for url in harness.vendor.urls)
    streams = capsys.readouterr()
    _assert_token_free(streams.out, "stdout")
    _assert_token_free(streams.err, "stderr")
    assert "credential_refused" in streams.err and "<redacted>" in streams.err
    for root in (harness.snapshot_dir, other):
        for path in root.rglob("*"):
            if path.is_file():
                _assert_token_free(path.read_bytes(), str(path))
    assert b"<redacted>" in harness.path("dividends", "CCC.US", "raw").read_bytes()
    assert harness.manifest()["verify"]["token_leak_detected"] == []

    (harness.snapshot_dir / "raw" / "planted.json").write_text(urllib.parse.quote_plus(TOKEN))
    assert harness.run("verify") == 1
    assert harness.manifest()["verify"]["token_leak_detected"] == ["raw/planted.json"]
    assert "token_leak_detected" in capsys.readouterr().err


# ---------------------------------------------------------------- T-RET-3


def test_t_ret_3_credential_and_entitlement_stop_without_retry(
    harness: Harness, capsys: pytest.CaptureFixture[str]
) -> None:
    for status, outcome in ((401, "credential_refused"), (403, "credential_refused"), (402, "entitlement_refused")):
        harness.vendor.urls.clear()
        harness.vendor.routes["fundamentals/GSPC.INDX"] = status
        assert harness.run("components") == 1
        assert len(harness.vendor.urls) == 1
        assert outcome in capsys.readouterr().err


def test_t_ret_3_404_continues_429_backs_off_then_stops_5xx_retries(
    harness: Harness, capsys: pytest.CaptureFixture[str]
) -> None:
    harness.prepare()
    harness.vendor.routes["splits/AAA.US"] = 404
    harness.vendor.routes["splits/BBB.US"] = 503
    assert harness.run("splits", "--retries", "2") == 0
    assert harness.entry("splits", "AAA.US")["status"] == "unavailable:missing_symbol"
    assert harness.entry("splits", "BBB.US")["status"] == "provider_error"
    assert harness.entry("splits", "CCC.US")["status"] == "retrieved"
    assert harness.vendor.paths().count("splits/BBB.US") == 3

    harness.vendor.routes["div/AAA.US"] = 429
    harness.vendor.urls.clear()
    assert harness.run("dividends") == 1
    assert "rate_limited_exhausted" in capsys.readouterr().err
    assert harness.vendor.paths() == ["div/AAA.US"] * 6
    backoff = [value for value in harness.sleeps if value >= 1]
    assert [int(value) for value in backoff] == [2, 4, 8, 16, 32]
    assert all(0 <= value - int(value) < 1 for value in backoff)
    assert "dividends/AAA.US" not in harness.manifest()["entries"]


def test_t_ret_3_token_bucket_spaces_requests(harness: Harness) -> None:
    harness.prepare()
    harness.sleeps.clear()
    harness.clock.advance(seconds=1)
    assert main(
        ["splits", "--snapshot-id", "T1", "--data-dir", str(harness.data_dir), "--requests-per-minute", "60"],
        transport=harness.vendor,
        clock=harness.clock,
        sleep=harness.sleeps.append,
    ) == 0
    assert len(harness.sleeps) == len(CODES) - 1
    assert all(0.5 < value <= 1.0 for value in harness.sleeps)


# ---------------------------------------------------------------- T-RET-4


def test_t_ret_4_resume_skips_hashed_files_and_refresh_refetches(harness: Harness) -> None:
    harness.full()
    harness.vendor.urls.clear()
    for command in ("splits", "eod", "dividends"):
        assert harness.run(command) == 0
    assert harness.vendor.urls == []
    assert harness.run("eod", "--refresh") == 0
    assert sorted(harness.vendor.paths()) == sorted(f"eod/{code}" for code in CODES)


# ---------------------------------------------------------------- T-RET-5


def test_t_ret_5_data_dir_inside_repository_refuses(
    harness: Harness, capsys: pytest.CaptureFixture[str]
) -> None:
    inside = PROJECT_ROOT / "private_snapshot_should_not_exist"
    assert harness.run("components", "--data-dir", str(inside)) == 1
    assert "data_dir_inside_repository" in capsys.readouterr().err
    assert harness.vendor.urls == [] and not inside.exists()


# ---------------------------------------------------------------- T-RET-6


def test_t_ret_6_split_ratio_parsing() -> None:
    assert split_ratio("2.000000/1.000000") == 2.0
    assert split_ratio("1/4") == 0.25
    for invalid in ("0/1", "1:2", "", "1/0", "a/b", "-2/1", "2/1/1", None, 2.0, "nan/1", "inf/1"):
        assert split_ratio(invalid) is None, invalid


@pytest.mark.parametrize("value", ["0/1", "1:2", ""])
def test_t_ret_6_invalid_ratio_quarantines_only_its_partition(harness: Harness, value: str) -> None:
    harness.vendor.routes["splits/AAA.US"] = body([{"date": "2003-12-01", "split": value}, {"date": "2004-03-01", "split": "2/1"}])
    harness.vendor.routes["splits/BBB.US"] = body([{"date": "2003-12-01", "split": "2/1"}, {"date": "2004-03-01", "split": value}])
    harness.prepare()
    assert harness.run("splits") == 0
    holdout_bad = harness.entry("splits", "AAA.US")
    assert holdout_bad["status"] == "retrieved"
    assert holdout_bad["partition_statuses"] == {"discovery": "valid", "holdout": "quarantined:invalid_split_ratio"}
    assert set(holdout_bad["authorized_files"]) == {"raw", "discovery", "quarantine_holdout"}
    assert holdout_bad["authorized_files"]["quarantine_holdout"]["path"].startswith("quarantine/splits_holdout/")
    discovery_bad = harness.entry("splits", "BBB.US")
    assert discovery_bad["partition_statuses"] == {"discovery": "quarantined:invalid_split_ratio", "holdout": "valid"}
    assert harness.frame("splits", "AAA.US", "discovery")["ratio"].tolist() == [2.0]
    assert harness.manifest()["counters"]["splits_holdout_quarantined"] == 1
    assert harness.manifest()["counters"]["splits_discovery_quarantined"] == 1


# ---------------------------------------------------------------- T-RET-7


def test_t_ret_7_holdout_defect_quarantines_holdout_only_and_sidecar_is_identical(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    clean = Harness(tmp_path, monkeypatch, "clean")
    clean.full()
    defect = Harness(tmp_path, monkeypatch, "defect")
    rows = [bar(day) for day in CALENDAR]
    rows[3]["close"] = -1.0
    defect.vendor.routes["eod/AAA.US"] = body(rows)
    defect.full()

    entry = defect.entry("eod", "AAA.US")
    assert entry["status"] == "retrieved"
    assert entry["partition_statuses"] == {"discovery": "valid", "holdout": "quarantined:bar_values"}
    assert set(entry["authorized_files"]) == {"raw", "dates", "discovery", "quarantine_holdout"}
    assert defect.path("eod", "AAA.US", "dates").read_bytes() == clean.path("eod", "AAA.US", "dates").read_bytes()
    assert defect.path("eod", "AAA.US", "discovery").read_bytes() == clean.path("eod", "AAA.US", "discovery").read_bytes()
    discovery = load_eod_parquet(defect.path("eod", "AAA.US", "discovery"))
    assert discovery.index.min() == pd.Timestamp(HOLDOUT_END)
    assert len(discovery) == len(CALENDAR) - FIRST_DISCOVERY
    holdout = clean.frame("eod", "AAA.US", "holdout")
    assert pd.DatetimeIndex(holdout["date"]).max() < pd.Timestamp(HOLDOUT_END)
    assert len(holdout) == FIRST_DISCOVERY
    assert defect.frame("eod", "AAA.US", "dates")["date"].tolist() == list(pd.to_datetime(CALENDAR))


# ---------------------------------------------------------------- T-RET-8


def test_t_ret_8_components_parse_and_retrieval_date(harness: Harness) -> None:
    entries = [
        {"Code": "AAA", "Name": "A", "StartDate": "1993-12-15", "EndDate": None, "IsActiveNow": 1, "IsDelisted": 0},
        {"Code": "BBB", "Name": "B", "EndDate": "2000-01-01", "IsActiveNow": 0, "IsDelisted": 1},
    ]
    harness.vendor.routes["fundamentals/GSPC.INDX"] = components_body(entries)
    assert harness.run("components") == 0
    manifest = harness.manifest()
    assert manifest["snapshot"]["components_retrieved_utc_date"] == "2026-09-25"
    assert manifest["snapshot"]["components_response_keys"] == ["General", "HistoricalTickerComponents"]
    frame = read_authorized_parquet(harness.snapshot_dir, "membership/historical_components_raw.parquet")
    assert frame["Code"].tolist() == ["AAA", "BBB"]
    assert frame["StartDate"][0] == "1993-12-15" and pd.isna(frame["StartDate"][1])
    assert frame["raw_row"].tolist() == [0, 1]
    _, counts = holdout_partition.parse_membership_entries(frame, date(2026, 9, 25))
    assert counts["entry_missing_field"] == 1 and counts["retained"] == 1
    assert harness.run("components") == 1  # snapshot_file_exists


@pytest.mark.parametrize(
    ("payload", "code"),
    [
        ({"General": {}}, "components_malformed"),
        ({"HistoricalTickerComponents": "none"}, "components_malformed"),
        ({"HistoricalTickerComponents": [{"Code": "AAA"}, "AAA"]}, "components_malformed"),
        ([{"Code": "AAA"}], "components_malformed"),
        ({"HistoricalTickerComponents": []}, "components_empty"),
        ({"HistoricalTickerComponents": {}}, "components_empty"),
    ],
)
def test_t_ret_8_malformed_or_empty_components_refuse_and_block_the_seal(
    harness: Harness, capsys: pytest.CaptureFixture[str], payload, code: str
) -> None:
    raw = body(payload)
    harness.vendor.routes["fundamentals/GSPC.INDX"] = raw
    assert harness.run("components") == 1
    assert code in capsys.readouterr().err
    assert (harness.snapshot_dir / "raw/index/GSPC.INDX.fundamentals.json").read_bytes() == raw
    assert not (harness.snapshot_dir / "membership").exists()
    with pytest.raises(SnapshotRefusal) as refused:
        harness.seal()
    assert refused.value.code == "holdout_seal_missing"
    assert harness.run("calendar") == 1
    assert "holdout_seal_missing" in capsys.readouterr().err


# ---------------------------------------------------------------- T-RET-9


@pytest.mark.parametrize("command", ["calendar", "splits", "eod", "dividends"])
def test_t_ret_9_seal_gated_commands_refuse_before_any_request(
    harness: Harness, capsys: pytest.CaptureFixture[str], command: str
) -> None:
    assert harness.run("components") == 0
    assert harness.run("symbols") == 0
    harness.vendor.urls.clear()
    assert harness.run(command) == 1
    assert "holdout_seal_missing" in capsys.readouterr().err
    assert harness.vendor.urls == []


# ---------------------------------------------------------------- T-RET-10


def test_t_ret_10_a_split_with_scale_step_is_accepted_and_loads_with_split_factor(
    harness: Harness, tmp_path: Path
) -> None:
    split_day = "2004-03-01"
    harness.vendor.routes["splits/AAA.US"] = body([{"date": split_day, "split": "2.000000/1.000000"}])
    harness.vendor.routes["eod/AAA.US"] = body(split_step_bars(split_day))
    harness.full()
    entry = harness.entry("eod", "AAA.US")
    assert entry["partition_statuses"]["discovery"] == "valid"
    assert entry["split_evidence_basis"] == "discovery_split_table"
    assert entry["split_table_sha256_at_eod_validation"] == harness.entry("splits", "AAA.US")["authorized_files"]["discovery"]["sha256"]

    frame = load_eod_parquet(harness.path("eod", "AAA.US", "discovery"))
    frame["split_factor"] = compute_cumulative_split_factor(frame.index, harness.frame("splits", "AAA.US", "discovery"))
    panel_dir = tmp_path / "panel"
    panel_dir.mkdir()
    frame.rename_axis("date").reset_index().to_parquet(panel_dir / "AAA.US.parquet", index=False)
    panels = load_eod_cohort_panels(panel_dir, ["AAA.US"])
    assert panels["close"]["AAA.US"].loc[pd.Timestamp("2004-02-27")] == 200.0
    assert frame["split_factor"].loc[pd.Timestamp("2004-02-27")] == 2.0
    assert frame["split_factor"].loc[pd.Timestamp(split_day)] == 1.0


def test_t_ret_10_b_zero_row_split_table_quarantines_unverified_split(harness: Harness) -> None:
    harness.vendor.routes["eod/AAA.US"] = body(split_step_bars("2004-03-01"))
    harness.full()
    entry = harness.entry("eod", "AAA.US")
    assert entry["partition_statuses"] == {"discovery": "quarantined:unverified_split", "holdout": "valid"}
    assert entry["split_evidence_basis"] == "discovery_split_table"
    assert set(entry["authorized_files"]) == {"raw", "dates", "holdout", "quarantine_discovery"}


def test_t_ret_10_c_eod_before_splits_refuses_before_any_request(
    harness: Harness, capsys: pytest.CaptureFixture[str]
) -> None:
    harness.prepare()
    harness.vendor.urls.clear()
    assert harness.run("eod") == 1
    assert "splits_required_before_eod" in capsys.readouterr().err
    assert harness.vendor.urls == []


def _stage_order(paths: list[str]) -> list[str]:
    stages: list[str] = []
    for path in paths:
        stage = path.split("/")[0]
        if not stages or stages[-1] != stage:
            stages.append(stage)
    return stages


def test_t_ret_10_d_interruptions_resume_through_all_in_canonical_order(
    harness: Harness, capsys: pytest.CaptureFixture[str]
) -> None:
    assert harness.run("all") == 3
    assert "holdout_seal_required" in capsys.readouterr().err
    assert harness.vendor.paths() == ["fundamentals/GSPC.INDX", "exchange-symbol-list/US", "exchange-symbol-list/US"]
    harness.seal()
    seal = json.loads((harness.snapshot_dir / "holdout_seal_v1.json").read_bytes())
    assert seal["retrieval_order"] == list(RETRIEVAL_ORDER) == [
        "components", "symbols", "seal", "calendar", "splits", "eod", "dividends", "verify",
    ]

    # Interruption inside splits resumes at splits.
    harness.vendor.routes["splits/BBB.US"] = [Interrupt(), body([])]
    harness.vendor.urls.clear()
    with pytest.raises(Interrupt):
        harness.run("all")
    assert harness.vendor.paths() == ["eod/GSPC.INDX", "splits/AAA.US", "splits/BBB.US"]
    harness.vendor.routes["eod/CCC.US"] = [Interrupt(), body([bar(day) for day in CALENDAR])]
    harness.vendor.urls.clear()
    # Interruption inside eod after a resumed splits.
    with pytest.raises(Interrupt):
        harness.run("all")
    assert harness.vendor.paths() == [
        "splits/BBB.US", "splits/CCC.US", "splits/SPY.US", "eod/AAA.US", "eod/BBB.US", "eod/CCC.US",
    ]
    # Interruption inside eod resumes at eod.
    harness.vendor.routes["div/AAA.US"] = [Interrupt(), body([])]
    harness.vendor.urls.clear()
    with pytest.raises(Interrupt):
        harness.run("all")
    assert harness.vendor.paths() == ["eod/CCC.US", "eod/SPY.US", "div/AAA.US"]
    # Interruption after eod resumes at dividends.
    harness.vendor.urls.clear()
    assert harness.run("all") == 0
    assert _stage_order(harness.vendor.paths()) == ["div"]
    assert harness.manifest()["verify"]["retrieval_complete"] is True

    # Curated additions follow splits --codes, eod --codes, dividends --codes.
    harness.vendor.routes.update({"eod/NEW.US": body([bar(day) for day in CALENDAR]), "splits/NEW.US": body([]), "div/NEW.US": body([])})
    added = harness.codes_file("NEW.US")
    harness.vendor.urls.clear()
    assert harness.run("eod", "--codes", added) == 1
    assert "splits_required_before_eod" in capsys.readouterr().err
    assert harness.vendor.urls == []
    assert harness.run("splits", "--codes", added) == 0
    assert harness.verify()["incomplete_codes_by_table_and_status"] == {
        "eod": {"NEW.US": "absent"}, "dividends": {"NEW.US": "absent"},
    }
    for command in ("eod", "dividends"):
        assert harness.run(command, "--codes", added) == 0
    assert harness.vendor.paths() == ["splits/NEW.US", "eod/NEW.US", "div/NEW.US"]
    assert harness.verify()["retrieval_complete"] is True


def test_t_ret_10_e_discovery_split_revision_is_stale_until_eod_refresh(harness: Harness) -> None:
    harness.vendor.routes["splits/AAA.US"] = body([{"date": "2003-12-01", "split": "3/1"}, {"date": "2004-03-01", "split": "2/1"}])
    harness.vendor.routes["eod/AAA.US"] = body(split_step_bars("2004-03-01"))
    harness.full()
    assert harness.verify()["split_evidence_stale"] == []

    harness.vendor.routes["splits/AAA.US"] = body([{"date": "2003-12-01", "split": "5/1"}, {"date": "2004-03-01", "split": "2/1"}])
    assert harness.run("splits", "--refresh") == 0
    assert harness.verify()["split_evidence_stale"] == []

    harness.vendor.routes["splits/AAA.US"] = body([{"date": "2003-12-01", "split": "5/1"}, {"date": "2004-03-02", "split": "2/1"}])
    assert harness.run("splits", "--refresh") == 0
    assert harness.verify()["split_evidence_stale"] == ["AAA.US"]
    assert harness.run("eod", "--refresh", "--codes", harness.codes_file("AAA.US")) == 0
    assert harness.verify()["split_evidence_stale"] == []

    # A stale entry is open, so a plain resumed eod revalidates it (plan 1.3 caching rule).
    harness.vendor.routes["splits/AAA.US"] = body([{"date": "2004-03-01", "split": "2/1"}])
    assert harness.run("splits", "--refresh") == 0
    assert harness.verify()["split_evidence_stale"] == ["AAA.US"]
    harness.vendor.urls.clear()
    assert harness.run("eod") == 0
    assert harness.vendor.paths() == ["eod/AAA.US"]
    assert harness.verify()["split_evidence_stale"] == []


def test_t_ret_10_f_missing_split_table_uses_discontinuity_fallback(harness: Harness) -> None:
    harness.vendor.routes["splits/AAA.US"] = 404
    harness.full()
    assert harness.entry("splits", "AAA.US")["status"] == "unavailable:missing_symbol"
    entry = harness.entry("eod", "AAA.US")
    assert entry["split_evidence_basis"] == "none_discontinuity_fallback"
    assert entry["split_table_sha256_at_eod_validation"] is None
    assert set(entry["authorized_files"]) == {"raw", "dates", "discovery", "holdout"}
    frame = load_eod_parquet(harness.path("eod", "AAA.US", "discovery"))
    assert (compute_cumulative_split_factor(frame.index, None) == 1.0).all()


def test_t_ret_10_g_split_provider_error_skips_eod_until_resumed_splits(harness: Harness) -> None:
    harness.vendor.routes["splits/BBB.US"] = 500
    harness.prepare()
    assert harness.run("splits", "--retries", "0") == 0
    assert harness.entry("splits", "BBB.US")["status"] == "provider_error"
    harness.vendor.urls.clear()
    assert harness.run("eod") == 0
    assert "eod/BBB.US" not in harness.vendor.paths()
    assert harness.entry("eod", "BBB.US")["status"] == "skipped:split_table_provider_error"
    assert all(harness.entry("eod", code)["status"] == "retrieved" for code in ("AAA.US", "CCC.US", "SPY.US"))

    harness.vendor.routes["splits/BBB.US"] = body([])
    harness.vendor.urls.clear()
    assert harness.run("splits") == 0
    assert harness.run("eod") == 0
    assert harness.vendor.paths() == ["splits/BBB.US", "eod/BBB.US"]
    assert harness.entry("eod", "BBB.US")["status"] == "retrieved"


def test_t_ret_10_h_quarantined_discovery_split_evidence_fails_discovery_eod_closed(harness: Harness) -> None:
    harness.vendor.routes["splits/AAA.US"] = body([{"date": "2004-03-01", "split": "0/1"}])
    harness.full()
    assert harness.entry("splits", "AAA.US")["partition_statuses"]["discovery"] == "quarantined:invalid_split_ratio"
    entry = harness.entry("eod", "AAA.US")
    assert entry["partition_statuses"] == {"discovery": "quarantined:split_evidence_quarantined", "holdout": "valid"}
    assert entry["split_evidence_basis"] == "split_evidence_quarantined"
    assert {"dates", "holdout", "quarantine_discovery"} <= set(entry["authorized_files"])


# ---------------------------------------------------------------- T-RET-11


@pytest.mark.parametrize(
    ("mutate", "reason"),
    [
        (lambda rows: rows[5].update(date="2003/11/10"), "unparseable"),
        (lambda rows: rows[5].update(date=rows[4]["date"]), "duplicate"),
        (lambda rows: rows.insert(5, rows.pop(40)), "unsorted"),
    ],
)
def test_t_ret_11_date_structure_refuses_the_whole_code(harness: Harness, mutate, reason: str) -> None:
    rows = [bar(day) for day in CALENDAR]
    mutate(rows)
    harness.vendor.routes["eod/AAA.US"] = body(rows)
    harness.full()
    entry = harness.entry("eod", "AAA.US")
    assert entry["status"] == f"unavailable:date_structure:{reason}"
    assert set(entry["authorized_files"]) == {"raw"}
    assert not list(harness.snapshot_dir.glob("dates/AAA.US*"))
    assert not list(harness.snapshot_dir.glob("eod/*/AAA.US*"))
    assert harness.manifest()["counters"]["eod_date_structure_refusals"] == 1


def test_t_ret_11_value_defect_in_the_same_position_quarantines_one_partition(harness: Harness) -> None:
    rows = [bar(day) for day in CALENDAR]
    rows[5]["high"] = 1.0
    harness.vendor.routes["eod/AAA.US"] = body(rows)
    harness.full()
    entry = harness.entry("eod", "AAA.US")
    assert entry["partition_statuses"] == {"discovery": "valid", "holdout": "quarantined:bar_values"}
    assert "dates" in entry["authorized_files"]


# ---------------------------------------------------------------- T-RET-12


@pytest.mark.parametrize("table", ["splits", "dividends"])
def test_t_ret_12_corporate_action_date_structure_refuses_the_table_only(harness: Harness, table: str) -> None:
    endpoint = "splits" if table == "splits" else "div"
    field = {"split": "2/1"} if table == "splits" else {"value": 0.5}
    harness.vendor.routes[f"{endpoint}/AAA.US"] = body([{"date": "03-01-2003", **field}, {"date": "2004-03-01", **field}])
    harness.full()
    entry = harness.entry(table, "AAA.US")
    assert entry["status"] == "unavailable:date_structure:unparseable"
    assert set(entry["authorized_files"]) == {"raw"}
    assert harness.entry("eod", "AAA.US")["status"] == "retrieved"


def test_t_ret_12_partition_at_holdout_end_and_discovery_rows_drive_the_check(harness: Harness) -> None:
    harness.vendor.routes["div/AAA.US"] = body(
        [{"date": "2003-12-30", "value": 0.1, "unadjustedValue": 0.2}, {"date": HOLDOUT_END, "value": 0.3, "unadjustedValue": 0.4}]
    )
    # A holdout-dated split row one row before a step at the first discovery bar
    # is not discovery evidence, so the discovery partition is quarantined.
    harness.vendor.routes["splits/BBB.US"] = body([{"date": "2003-12-30", "split": "2/1"}])
    harness.vendor.routes["eod/BBB.US"] = body(
        [bar(day, close=200.0, adjusted=100.0) if day <= HOLDOUT_END else bar(day) for day in CALENDAR]
    )
    harness.full()
    discovery = harness.frame("dividends", "AAA.US", "discovery")
    holdout = harness.frame("dividends", "AAA.US", "holdout")
    assert discovery["date"].tolist() == [pd.Timestamp(HOLDOUT_END)] and discovery["value"].tolist() == [0.3]
    assert json.loads(discovery["row_json"][0])["unadjustedValue"] == 0.4
    assert holdout["date"].tolist() == [pd.Timestamp("2003-12-30")]
    assert len(harness.frame("splits", "BBB.US", "discovery")) == 0
    assert len(harness.frame("splits", "BBB.US", "holdout")) == 1
    assert harness.entry("eod", "BBB.US")["partition_statuses"]["discovery"] == "quarantined:unverified_split"


# ---------------------------------------------------------------- T-RET-13


def test_t_ret_13_row_without_date_key_is_malformed_response(harness: Harness) -> None:
    rows = [bar(day) for day in CALENDAR]
    del rows[7]["date"]
    harness.vendor.routes["eod/AAA.US"] = body(rows)
    harness.vendor.routes["eod/BBB.US"] = b"{not json"
    harness.full()
    for code in ("AAA.US", "BBB.US"):
        entry = harness.entry("eod", code)
        assert entry["status"] == "unavailable:malformed_response"
        assert set(entry["authorized_files"]) == {"raw"}


@pytest.mark.parametrize(
    "mutate",
    [
        lambda row: row.update(close="n/a"),
        lambda row: row.pop("volume"),
        lambda row: row.update(low=-1.0),
    ],
)
def test_t_ret_13_holdout_value_defect_quarantines_holdout_only(harness: Harness, mutate) -> None:
    rows = [bar(day) for day in CALENDAR]
    mutate(rows[2])
    harness.vendor.routes["eod/AAA.US"] = body(rows)
    harness.full()
    entry = harness.entry("eod", "AAA.US")
    assert entry["status"] == "retrieved"
    assert entry["partition_statuses"] == {"discovery": "valid", "holdout": "quarantined:bar_values"}
    assert len(load_eod_parquet(harness.path("eod", "AAA.US", "discovery"))) == len(CALENDAR) - FIRST_DISCOVERY
    quarantined = harness.frame("eod", "AAA.US", "quarantine_holdout")
    assert json.loads(quarantined["row_json"][2]) == rows[2]


# ---------------------------------------------------------------- T-RET-14


def test_t_ret_14_resume_and_completeness(harness: Harness, capsys: pytest.CaptureFixture[str]) -> None:
    harness.vendor.routes["eod/AAA.US"] = 500
    harness.vendor.routes["splits/BBB.US"] = 500
    harness.prepare()
    assert harness.run("splits", "--retries", "0") == 0
    assert harness.run("dividends") == 0
    assert harness.run("eod", "--retries", "0", "--max-requests", "2") == 1
    assert "budget_exhausted" in capsys.readouterr().err
    verify = harness.verify()
    assert verify["retrieval_complete"] is False
    assert verify["incomplete_codes_by_table_and_status"] == {
        "splits": {"BBB.US": "provider_error"},
        "eod": {"AAA.US": "provider_error", "BBB.US": "skipped:split_table_provider_error", "SPY.US": "absent"},
    }
    kept = harness.entry("eod", "CCC.US")

    harness.vendor.routes["eod/AAA.US"] = body([bar(day) for day in CALENDAR])
    harness.vendor.urls.clear()
    assert harness.run("eod") == 0
    assert harness.vendor.paths() == ["eod/AAA.US", "eod/SPY.US"]
    assert harness.entry("eod", "BBB.US")["status"] == "skipped:split_table_provider_error"
    harness.vendor.routes["splits/BBB.US"] = body([])
    harness.vendor.urls.clear()
    assert harness.run("splits") == 0
    assert harness.run("eod") == 0
    assert harness.vendor.paths() == ["splits/BBB.US", "eod/BBB.US"]
    assert harness.entry("eod", "CCC.US") == kept
    assert harness.verify()["retrieval_complete"] is True
    harness.vendor.urls.clear()
    assert harness.run("eod", "--refresh") == 0
    assert sorted(harness.vendor.paths()) == sorted(f"eod/{code}" for code in CODES)


# ---------------------------------------------------------------- T-RET-15


def _gap_bars(gap_rows: int, *, saturday: bool = False) -> list[dict]:
    """Discovery bars stepping 100 percent in scale across ``gap_rows`` calendar rows."""

    start = FIRST_DISCOVERY + 5
    rows = [bar(day) for day in CALENDAR[: start + 1]]
    if saturday:
        rows.append(bar(SATURDAY, close=200.0, adjusted=100.0))
    rows.extend(bar(day, close=200.0, adjusted=100.0) for day in CALENDAR[start + gap_rows + 1 :])
    return rows


def test_t_ret_15_scale_check_compares_consecutive_on_calendar_bars_only(harness: Harness) -> None:
    assert CALENDAR[FIRST_DISCOVERY + 5] < SATURDAY < CALENDAR[FIRST_DISCOVERY + 31]
    harness.vendor.routes["eod/AAA.US"] = body(_gap_bars(25))
    harness.vendor.routes["eod/BBB.US"] = body(_gap_bars(20))
    harness.vendor.routes["eod/CCC.US"] = body(_gap_bars(25, saturday=True))
    spike = [bar(day) for day in CALENDAR if day < SATURDAY]
    spike.append(bar(SATURDAY, close=200.0, adjusted=100.0))
    spike.extend(bar(day) for day in CALENDAR if day > SATURDAY)
    harness.vendor.routes["eod/SPY.US"] = body(spike)
    harness.full()
    for code in ("AAA.US", "CCC.US", "SPY.US"):
        entry = harness.entry("eod", code)
        assert entry["partition_statuses"]["discovery"] == "valid", code
        assert entry["split_evidence_basis"] == "discovery_split_table"
    assert harness.entry("eod", "BBB.US")["partition_statuses"]["discovery"] == "quarantined:unverified_split"
    assert SATURDAY in {day.date().isoformat() for day in harness.frame("eod", "CCC.US", "dates")["date"]}


def test_t_ret_15_eod_before_calendar_refuses_before_any_request(
    harness: Harness, capsys: pytest.CaptureFixture[str]
) -> None:
    harness.prepare(calendar=False)
    assert harness.run("splits") == 0
    harness.vendor.urls.clear()
    assert harness.run("eod") == 1
    assert "calendar_required_before_eod" in capsys.readouterr().err
    assert harness.vendor.urls == []


# ---------------------------------------------------------------- T-RET-16


def test_t_ret_16_third_distinct_utc_date_sets_persistent_provider_error(harness: Harness) -> None:
    harness.vendor.routes["splits/AAA.US"] = 502
    harness.prepare()
    for _ in range(3):
        assert harness.run("splits", "--retries", "0") == 0
        assert harness.entry("splits", "AAA.US")["status"] == "provider_error"
    harness.clock.advance(days=1)
    assert harness.run("splits", "--retries", "0") == 0
    assert harness.entry("splits", "AAA.US")["status"] == "provider_error"
    harness.clock.advance(days=1)
    assert harness.run("splits", "--retries", "0") == 0
    entry = harness.entry("splits", "AAA.US")
    assert entry["status"] == "unavailable:persistent_provider_error"
    assert entry["provider_error_history"] == ["2026-09-25"] * 3 + ["2026-09-26", "2026-09-27"]
    log = [json.loads(line) for line in (harness.snapshot_dir / "retrieval_log.jsonl").read_text().splitlines()]
    assert [r for r in log if r.get("status_change", {}).get("to") == "unavailable:persistent_provider_error"] == [
        next(r for r in log if r.get("status_change", {}).get("to") == "unavailable:persistent_provider_error")
    ]

    assert harness.run("eod") == 0
    assert harness.entry("eod", "AAA.US")["split_evidence_basis"] == "none_discontinuity_fallback"
    assert harness.run("dividends") == 0
    verify = harness.verify()
    assert verify["retrieval_complete"] is True
    assert verify["persistent_provider_error_by_table"] == {"splits": 1, "eod": 0, "dividends": 0}

    harness.vendor.urls.clear()
    assert harness.run("splits") == 0
    assert harness.vendor.urls == []
    before = harness.entry("splits", "AAA.US")
    assert harness.run("splits", "--refresh", "--retries", "0", "--codes", harness.codes_file("AAA.US")) == 0
    after = harness.entry("splits", "AAA.US")
    assert after["status"] == "unavailable:persistent_provider_error"
    assert after["authorized_files"] == before["authorized_files"]
    assert after["provider_error_history"] == before["provider_error_history"] + ["2026-09-27"]
    harness.vendor.routes["splits/AAA.US"] = body([])
    assert harness.run("splits", "--refresh", "--codes", harness.codes_file("AAA.US")) == 0
    assert harness.entry("splits", "AAA.US")["status"] == "retrieved"


# ---------------------------------------------------------------- T-RET-17


@pytest.mark.parametrize(
    ("response", "status", "roles"),
    [
        (404, "unavailable:missing_symbol", {"raw"}),
        (body([]), "unavailable:empty_payload", {"raw"}),
        (
            body([bar(day, close=100.0 if day != "2004-02-02" else -5.0) for day in CALENDAR]),
            "retrieved",
            {"raw", "dates", "holdout", "quarantine_discovery"},
        ),
    ],
)
def test_t_ret_17_abc_refresh_authorizes_only_the_new_outcome(harness: Harness, response, status: str, roles: set) -> None:
    harness.full()
    earlier = harness.entry("eod", "AAA.US")["authorized_files"]
    harness.vendor.routes["eod/AAA.US"] = response
    assert harness.run("eod", "--refresh", "--codes", harness.codes_file("AAA.US")) == 0
    entry = harness.entry("eod", "AAA.US")
    assert entry["status"] == status
    assert set(entry["authorized_files"]) == roles
    with pytest.raises(SnapshotRefusal) as refused:
        read_authorized_bytes(harness.snapshot_dir, earlier["discovery"]["path"])
    assert refused.value.code == "artifact_not_authorized"
    for record in earlier.values():
        assert holdout_partition.sha256_bytes((harness.snapshot_dir / record["path"]).read_bytes()) == record["sha256"]


@pytest.mark.parametrize(
    "response",
    [404, body([]), body([bar(day, close=100.0 if day != "2004-02-02" else -5.0) for day in CALENDAR])],
)
def test_t_ret_17_d_interrupted_refresh_leaves_committed_state_and_resumes_identically(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, response
) -> None:
    twins = [Harness(tmp_path, monkeypatch, name) for name in ("plain", "interrupted")]
    for twin in twins:
        twin.full()
        twin.vendor.routes["eod/AAA.US"] = response
    plain, interrupted = twins
    assert plain.run("eod", "--refresh", "--codes", plain.codes_file("AAA.US")) == 0

    committed = (interrupted.snapshot_dir / "manifest.json").read_bytes()
    original_commit = retrieval._commit
    monkeypatch.setattr(retrieval, "_commit", lambda session: (_ for _ in ()).throw(Interrupt()))
    with pytest.raises(Interrupt):
        interrupted.run("eod", "--refresh", "--codes", interrupted.codes_file("AAA.US"))
    monkeypatch.setattr(retrieval, "_commit", original_commit)
    assert (interrupted.snapshot_dir / "manifest.json").read_bytes() == committed
    assert len(list(interrupted.snapshot_dir.glob("raw/eod/AAA.US.*"))) == 2
    earlier = json.loads(committed)["entries"]["eod/AAA.US"]["authorized_files"]
    assert read_authorized_bytes(interrupted.snapshot_dir, earlier["discovery"]["path"])

    interrupted.clock.value = plain.clock.value - timedelta(seconds=1)
    assert interrupted.run("eod", "--refresh", "--codes", interrupted.codes_file("AAA.US")) == 0
    assert (interrupted.snapshot_dir / "manifest.json").read_bytes() == (plain.snapshot_dir / "manifest.json").read_bytes()
    for record in interrupted.entry("eod", "AAA.US")["authorized_files"].values():
        assert (interrupted.snapshot_dir / record["path"]).read_bytes() == (plain.snapshot_dir / record["path"]).read_bytes()


def test_t_ret_17_e_corporate_action_refreshes(harness: Harness) -> None:
    harness.vendor.routes["splits/AAA.US"] = body([{"date": "2004-03-01", "split": "2/1"}])
    harness.vendor.routes["eod/AAA.US"] = body(split_step_bars("2004-03-01"))
    harness.vendor.routes["div/AAA.US"] = body([{"date": "2004-02-02", "value": 0.2}])
    harness.full()
    assert harness.verify()["split_evidence_stale"] == []

    harness.vendor.routes["splits/AAA.US"] = 404
    harness.vendor.routes["div/AAA.US"] = 404
    only_aaa = harness.codes_file("AAA.US")
    assert harness.run("splits", "--refresh", "--codes", only_aaa) == 0
    assert harness.run("dividends", "--refresh", "--codes", only_aaa) == 0
    for table in ("splits", "dividends"):
        entry = harness.entry(table, "AAA.US")
        assert entry["status"] == "unavailable:missing_symbol"
        assert set(entry["authorized_files"]) == {"raw"}
    assert harness.verify()["split_evidence_stale"] == ["AAA.US"]

    harness.vendor.routes["splits/AAA.US"] = body([])
    harness.vendor.routes["splits/BBB.US"] = body([])
    assert harness.run("eod", "--refresh", "--codes", only_aaa) == 0
    assert harness.run("splits", "--refresh") == 0
    entry = harness.entry("splits", "AAA.US")
    assert entry["status"] == "retrieved"
    assert entry["partition_statuses"] == {"discovery": "valid", "holdout": "valid"}
    assert len(harness.frame("splits", "AAA.US", "discovery")) == 0
    # AAA's eod was validated under the fallback; BBB's zero-row table is unchanged.
    assert harness.verify()["split_evidence_stale"] == ["AAA.US"]


def test_t_ret_17_e_empty_refresh_is_stale_exactly_when_discovery_rows_existed(harness: Harness) -> None:
    harness.vendor.routes["splits/AAA.US"] = body([{"date": "2004-03-01", "split": "2/1"}])
    harness.vendor.routes["splits/BBB.US"] = body([{"date": "2003-12-01", "split": "2/1"}])
    harness.vendor.routes["eod/AAA.US"] = body(split_step_bars("2004-03-01"))
    harness.full()
    for code in ("AAA.US", "BBB.US"):
        harness.vendor.routes[f"splits/{code}"] = body([])
    assert harness.run("splits", "--refresh") == 0
    assert harness.verify()["split_evidence_stale"] == ["AAA.US"]


def test_t_ret_17_f_tampered_file_is_hash_mismatch_and_unauthorized_file_is_refused(
    harness: Harness,
) -> None:
    harness.full()
    tampered = harness.path("eod", "BBB.US", "discovery")
    tampered.write_bytes(tampered.read_bytes() + b"x")
    assert harness.run("verify") == 1
    verify = harness.manifest()["verify"]
    assert verify["artifact_hash_mismatch"] == [tampered.relative_to(harness.snapshot_dir).as_posix()]
    assert verify["retrieval_complete"] is False
    with pytest.raises(SnapshotRefusal) as refused:
        read_authorized_bytes(harness.snapshot_dir, tampered.relative_to(harness.snapshot_dir).as_posix())
    assert refused.value.code == "artifact_hash_mismatch"

    planted = harness.snapshot_dir / "eod/discovery/ZZZ.US.parquet"
    planted.write_bytes(tampered.read_bytes())
    with pytest.raises(SnapshotRefusal) as refused:
        read_authorized_bytes(harness.snapshot_dir, "eod/discovery/ZZZ.US.parquet")
    assert refused.value.code == "artifact_not_authorized"

    harness.vendor.urls.clear()
    assert harness.run("eod") == 0
    assert harness.vendor.paths() == ["eod/BBB.US"]
    assert harness.verify()["artifact_hash_mismatch"] == []


def test_t_ret_17_d_attempt_names_never_overwrite_a_committed_file(
    harness: Harness, capsys: pytest.CaptureFixture[str]
) -> None:
    harness.full()
    committed = harness.path("eod", "AAA.US", "raw").read_bytes()
    harness.vendor.routes["eod/AAA.US"] = body([])
    harness.clock.advance(seconds=-2)  # run() adds one second: this reuses the eod attempt stamp
    assert harness.run("eod", "--refresh", "--codes", harness.codes_file("AAA.US")) == 1
    assert "collides with a committed file" in capsys.readouterr().err
    assert harness.path("eod", "AAA.US", "raw").read_bytes() == committed


def test_t_ret_17_g_refresh_ending_in_5xx_writes_nothing(harness: Harness) -> None:
    harness.full()
    assert harness.verify()["retrieval_complete"] is True
    before = harness.entry("eod", "AAA.US")
    files_before = sorted(path for path in harness.snapshot_dir.rglob("*") if path.is_file())
    harness.vendor.routes["eod/AAA.US"] = 500
    assert harness.run("eod", "--refresh", "--retries", "1", "--codes", harness.codes_file("AAA.US")) == 0
    after = harness.entry("eod", "AAA.US")
    assert after == {**before, "provider_error_history": ["2026-09-25"]}
    files_after = sorted(path for path in harness.snapshot_dir.rglob("*") if path.is_file())
    assert files_after == files_before
    assert harness.verify()["retrieval_complete"] is True


# ---------------------------------------------------------------- plan


def test_plan_is_offline_and_projects_requests(harness: Harness, capsys: pytest.CaptureFixture[str]) -> None:
    harness.prepare()
    harness.vendor.urls.clear()
    capsys.readouterr()
    assert main(["plan", "--snapshot-id", "T1", "--requests-per-minute", "300"]) == 0
    lines = capsys.readouterr().out.strip().splitlines()
    summary = json.loads(lines[-1])
    assert summary == {"codes": 4, "membership_known": True, "projected_duration_minutes": 0.05, "projected_requests": 16}
    assert len(lines) == 17 and all("api_token" not in line for line in lines)
    assert harness.vendor.urls == []


# ---------------------------------------------------------------- repair a2 (candidate ed08d6c)


def _windowed_eod(harness: Harness) -> None:
    """EOD endpoints that honor ``from`` and ``to``, as the vendor does."""

    def respond(url: str) -> bytes:
        query = urllib.parse.parse_qs(urllib.parse.urlsplit(url).query)
        low = query.get("from", ["1980-01-01"])[0]
        high = query.get("to", ["9999-12-31"])[0]
        return body([bar(day) for day in CALENDAR if low <= day <= high])

    for code in CODES:
        harness.vendor.routes[f"eod/{code}"] = respond


def _last_bar(harness: Harness, code: str) -> str:
    return harness.frame("eod", code, "dates")["date"].max().date().isoformat()


def test_m47a1_a1_m1_all_refresh_retrieves_the_extended_window(harness: Harness) -> None:
    """Audit capsule: all --to <later> --refresh after a bounded retrieval."""

    _windowed_eod(harness)
    harness.prepare()
    for command in ("splits", "eod", "dividends"):
        assert harness.run(command, "--to", "2004-03-01") == 0
    assert _last_bar(harness, "AAA.US") == "2004-03-01"
    earlier = harness.entry("eod", "AAA.US")["authorized_files"]["dates"]

    harness.vendor.urls.clear()
    assert harness.run("all", "--to", "2004-06-30", "--refresh") == 0
    assert _stage_order(harness.vendor.paths()) == ["splits", "eod", "div"]
    assert len(harness.vendor.urls) == 3 * len(CODES)
    for code in CODES:
        for table in ("splits", "eod", "dividends"):
            assert harness.entry(table, code)["request_window"] == {"from": "1980-01-01", "to": "2004-06-30"}
        assert _last_bar(harness, code) == "2004-06-30"
    assert harness.entry("eod", "AAA.US")["authorized_files"]["dates"]["sha256"] != earlier["sha256"]
    verify = harness.manifest()["verify"]
    assert verify["retrieval_complete"] is True and verify["artifact_hash_mismatch"] == []

    harness.vendor.urls.clear()
    assert harness.run("all", "--to", "2004-06-30") == 0
    assert harness.vendor.urls == []

    # With the window unchanged, --refresh alone still refetches every table.
    assert harness.run("all", "--to", "2004-06-30", "--refresh") == 0
    assert _stage_order(harness.vendor.paths()) == ["splits", "eod", "div"]
    assert len(harness.vendor.urls) == 3 * len(CODES)


def test_m47a1_a1_m1_changed_window_reopens_entries_without_refresh(harness: Harness) -> None:
    _windowed_eod(harness)
    harness.prepare()
    for command in ("splits", "eod", "dividends"):
        assert harness.run(command, "--to", "2004-03-01") == 0
    assert harness.run("verify", "--to", "2004-03-01") == 0
    assert harness.manifest()["verify"]["retrieval_complete"] is True

    assert harness.run("verify", "--to", "2004-06-30") == 0
    incomplete = harness.manifest()["verify"]["incomplete_codes_by_table_and_status"]
    assert incomplete["eod"] == {code: "retrieved:request_window_mismatch" for code in CODES}
    assert harness.manifest()["verify"]["retrieval_complete"] is False

    harness.vendor.urls.clear()
    assert harness.run("all", "--to", "2004-06-30") == 0
    assert len(harness.vendor.urls) == 3 * len(CODES)
    assert _last_bar(harness, "SPY.US") == "2004-06-30"
    assert harness.manifest()["verify"]["retrieval_complete"] is True


def test_m47a1_a1_m1_eod_refuses_a_window_the_calendar_does_not_cover(
    harness: Harness, capsys: pytest.CaptureFixture[str]
) -> None:
    assert harness.run("components") == 0
    assert harness.run("symbols") == 0
    harness.seal()
    assert harness.run("calendar", "--to", "2004-03-01") == 0
    assert harness.run("splits") == 0
    harness.vendor.urls.clear()
    assert harness.run("eod") == 1
    assert "calendar_window_insufficient" in capsys.readouterr().err
    assert harness.run("eod", "--from", "1970-01-01", "--to", "2004-03-01") == 1
    assert harness.vendor.urls == []
    assert harness.run("splits", "--to", "2004-03-01") == 0
    assert harness.run("eod", "--to", "2004-03-01") == 0


def test_a1_session_holds_no_token(harness: Harness, monkeypatch: pytest.MonkeyPatch) -> None:
    harness.full()
    captured: list[retrieval.Session] = []
    monkeypatch.setitem(retrieval.COMMANDS, "verify", lambda session: captured.append(session) or 0)
    assert harness.run("verify") == 0
    (session,) = captured
    assert "token" not in {field.name for field in dataclasses.fields(retrieval.Session)}
    _assert_token_free(repr(session), "repr(Session)")
    for name, value in vars(session).items():
        _assert_token_free(repr(value), f"Session.{name}")
    assert session.contains_token(urllib.parse.quote_plus(TOKEN).encode()) is True
    assert session.contains_token(b"clean") is False


@pytest.mark.parametrize(
    "raised",
    [
        lambda url: http.client.IncompleteRead(f"partial {url}".encode()),
        lambda url: http.client.InvalidURL(f"URL can't contain control characters. {url!r}"),
        lambda url: ValueError(f"unknown url type: {url}"),
    ],
)
def test_a2_non_oserror_transport_failures_are_sanitized_without_chaining(raised) -> None:
    def transport(url: str) -> bytes:
        raise raised(url)

    with pytest.raises(RetrievalTransportError) as caught:
        _request("https://eodhd.com/api/eod/AAA.US?fmt=json", TOKEN, timeout=1, transport=transport)
    error = caught.value
    assert error.typed_outcome == "provider_error" and error.status is None
    assert error.__cause__ is None and error.__context__ is None
    _assert_token_free("".join(traceback.format_exception(error)) + repr(error.args), "exception")


def test_a2_incomplete_read_is_retried_then_provider_error(
    harness: Harness, capsys: pytest.CaptureFixture[str]
) -> None:
    harness.prepare()
    harness.vendor.routes["splits/AAA.US"] = lambda url: http.client.IncompleteRead(f"cut {url}".encode())
    assert harness.run("splits", "--retries", "1") == 0
    assert harness.vendor.paths().count("splits/AAA.US") == 2
    assert harness.entry("splits", "AAA.US")["status"] == "provider_error"
    assert harness.entry("splits", "BBB.US")["status"] == "retrieved"
    streams = capsys.readouterr()
    _assert_token_free(streams.out + streams.err, "streams")


def test_a3_invalid_vendor_codes_are_counted_and_never_reach_a_path_or_url(
    harness: Harness, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(holdout_partition, "BAND", (2, 8))
    monkeypatch.setattr(holdout_partition, "HARD_BAND", (1, 9))
    bad = ["../../../../ESCAPE", "A B", "A/B", ".HIDDEN"]
    entries = [
        {"Code": code, "Name": code, "StartDate": "1993-12-15", "EndDate": None, "IsActiveNow": 1, "IsDelisted": 0}
        for code in ["AAA", *bad]
    ]
    harness.vendor.routes["fundamentals/GSPC.INDX"] = components_body(entries)
    harness.full()
    for code in bad:
        for table in ("splits", "eod", "dividends"):
            entry = harness.entry(table, f"{code}.US")
            assert entry["status"] == "unavailable:invalid_code"
            assert entry["authorized_files"] == {}
    requested = {path.split("/", 1)[1] for path in harness.vendor.paths() if "/" in path}
    assert not requested & {f"{code}.US" for code in bad}
    assert not [path for path in harness.tmp_path.rglob("*ESCAPE*")]
    assert harness.verify()["retrieval_complete"] is True

    harness.vendor.urls.clear()
    assert harness.run("splits") == 0
    assert harness.vendor.urls == []


@pytest.mark.parametrize("code", ["../x.US", "A B.US", "A/B.US", "-X.US", "X.US\x00"])
def test_a3_invalid_curated_or_option_codes_refuse_before_any_request(
    harness: Harness, capsys: pytest.CaptureFixture[str], code: str
) -> None:
    harness.prepare()
    committed = (harness.snapshot_dir / "manifest.json").read_bytes()
    harness.vendor.urls.clear()
    curated = harness.tmp_path / "curated.txt"
    curated.write_text(f"AAA.US\n{code}\n", encoding="utf-8")
    assert harness.run("splits", "--codes", str(curated)) == 1
    assert "invalid_code" in capsys.readouterr().err
    assert harness.run("all", "--consideration-securities", str(curated)) == 1
    assert harness.run("splits", f"--benchmark={code}") == 1
    assert "invalid_code" in capsys.readouterr().err
    assert harness.vendor.urls == []
    assert (harness.snapshot_dir / "manifest.json").read_bytes() == committed

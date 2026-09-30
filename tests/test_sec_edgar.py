"""The SEC EDGAR client (owner decision O-10) on synthetic responses only.

No test opens a network connection: every request goes to an injected fake opener,
and time is a fake clock.
"""

from __future__ import annotations

import gzip
import io
import json
import logging
import urllib.error
from email.message import Message
from pathlib import Path

import pytest

import data.sec_edgar as sec
from data.sec_edgar import SecClient, SecRefusal

SENTINEL_UA = "Sentinel Research Probe sentinel.probe@example.org"
URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK0000000001.json"


class FakeClock:
    def __init__(self) -> None:
        self.now = 100.0
        self.sleeps: list[float] = []

    def __call__(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.now += seconds


class Response(io.BytesIO):
    def __init__(self, payload: bytes, headers: dict[str, str] | None = None) -> None:
        super().__init__(payload)
        self.headers = Message()
        for key, value in (headers or {}).items():
            self.headers[key] = value


class FakeOpener:
    """Serves a scripted response per URL: bytes, an HTTP status int, or a list consumed in order."""

    def __init__(self, script: dict[str, object], clock: FakeClock | None = None) -> None:
        self.script = script
        self.clock = clock
        self.calls: list[tuple[str, dict[str, str], float | None]] = []

    def __call__(self, request, timeout=None):
        url = request.full_url
        self.calls.append((url, dict(request.header_items()), self.clock.now if self.clock else None))
        step = self.script[url]
        if isinstance(step, list):
            step = step.pop(0)
        if isinstance(step, int):
            headers = Message()
            if step == 429:
                headers["Retry-After"] = "3"
            raise urllib.error.HTTPError(url, step, "scripted", headers, None)
        if isinstance(step, tuple):
            return Response(*step)
        return Response(step)


def client(tmp_path: Path, script: dict[str, object], clock: FakeClock | None = None) -> tuple[SecClient, FakeOpener]:
    clock = clock or FakeClock()
    opener = FakeOpener(script, clock)
    return SecClient(tmp_path, opener=opener, clock=clock, sleep=clock.sleep), opener


@pytest.fixture
def ua(monkeypatch: pytest.MonkeyPatch) -> str:
    monkeypatch.setenv(sec.USER_AGENT_ENV, SENTINEL_UA)
    return SENTINEL_UA


def test_unset_user_agent_refuses_online_but_not_offline(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(sec.USER_AGENT_ENV, raising=False)
    with pytest.raises(SecRefusal, match="EFR_SEC_USER_AGENT is unset"):
        SecClient(tmp_path)
    monkeypatch.setenv(sec.USER_AGENT_ENV, "   ")
    with pytest.raises(SecRefusal, match="unset"):
        sec.user_agent()
    SecClient(tmp_path, offline=True)


def test_user_agent_is_sent_but_never_written_printed_or_logged(
        tmp_path: Path, ua: str, capsys: pytest.CaptureFixture[str], caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.DEBUG)
    ok, missing = URL, URL.replace("0001", "0002")
    retried, broken = URL.replace("0001", "0003"), URL.replace("0001", "0004")
    forbidden = URL.replace("0001", "0005")
    c, opener = client(tmp_path / "cache", {ok: b"{}", missing: 404, retried: [429, 503, b"[]"],
                                            broken: [500] * sec.MAX_ATTEMPTS, forbidden: 403})
    c.get(ok, "a.json")
    c.get(missing, "b.json", allow_absent=True)
    c.get(retried, "c.json")
    messages = []
    for url, name in ((broken, "d.json"), (forbidden, "e.json"), (missing, "f.json")):
        with pytest.raises(SecRefusal) as caught:
            c.get(url, name)
        messages.append(str(caught.value) + repr(caught.value.__cause__) + repr(caught.value.__context__))
    assert {headers["User-agent"] for _, headers, _ in opener.calls} == {ua}
    captured = capsys.readouterr()
    written = "".join(p.read_text(encoding="utf-8", errors="replace") for p in tmp_path.rglob("*") if p.is_file())
    for text in (captured.out, captured.err, caplog.text, written, *messages):
        assert ua not in text and "sentinel.probe" not in text


def test_requests_are_spaced_at_most_four_a_second(tmp_path: Path, ua: str) -> None:
    urls = [URL.replace("0001", f"{i:04d}") for i in range(1, 10)]
    clock = FakeClock()
    c, opener = client(tmp_path, {u: b"{}" for u in urls}, clock)
    for i, u in enumerate(urls):
        c.get(u, f"f{i}.json")
    starts = [t for _, _, t in opener.calls]
    gaps = [b - a for a, b in zip(starts, starts[1:])]
    assert len(starts) == 9 and min(gaps) >= 1 / sec.MAX_REQUESTS_PER_SECOND - 1e-12
    assert starts[-1] - starts[0] >= 8 / sec.MAX_REQUESTS_PER_SECOND - 1e-12


def test_cached_file_makes_no_second_request(tmp_path: Path, ua: str) -> None:
    c, opener = client(tmp_path, {URL: b"{}"})
    c.get(URL, "x.json")
    c.get(URL, "x.json")
    assert len(opener.calls) == 1 and c.requests == 1


def test_retry_backs_off_on_429_and_5xx_and_honors_retry_after(tmp_path: Path, ua: str) -> None:
    clock = FakeClock()
    c, opener = client(tmp_path, {URL: [429, 502, b"{}"]}, clock)
    got = c.get(URL, "x.json")
    assert got.status == 200 and len(opener.calls) == 3 and c.retries == 2
    backoffs = [s for s in clock.sleeps if s > 1 / sec.MAX_REQUESTS_PER_SECOND]
    assert backoffs == [3.0, 4.0]  # Retry-After on the 429, then 2 ** 2 seconds


def test_retry_exhaustion_and_non_retryable_status_refuse(tmp_path: Path, ua: str) -> None:
    c, opener = client(tmp_path, {URL: [503] * sec.MAX_ATTEMPTS})
    with pytest.raises(SecRefusal, match="after 6 attempts"):
        c.get(URL, "x.json")
    assert len(opener.calls) == sec.MAX_ATTEMPTS and not (tmp_path / "x.json").exists()
    other = URL.replace("0001", "0009")
    c2, opener2 = client(tmp_path, {other: 403})
    with pytest.raises(SecRefusal, match="HTTP 403"):
        c2.get(other, "y.json")
    assert len(opener2.calls) == 1


def test_gzip_body_is_stored_decoded(tmp_path: Path, ua: str) -> None:
    body = json.dumps({"k": 1}).encode()
    c, opener = client(tmp_path, {URL: (gzip.compress(body), {"Content-Encoding": "gzip"})})
    got = c.get(URL, "x.json")
    assert (tmp_path / "x.json").read_bytes() == body and got.n_bytes == len(body)
    assert opener.calls[0][1]["Accept-encoding"] == "gzip"


def test_404_is_a_typed_absence_reproduced_offline(tmp_path: Path, ua: str) -> None:
    c, _ = client(tmp_path, {URL: 404})
    with pytest.raises(SecRefusal, match="404"):
        c.get(URL, "x.json")
    got = c.get(URL, "x.json", allow_absent=True)
    assert got.status == 404 and got.sha256 is None and not (tmp_path / "x.json").exists()
    offline = SecClient(tmp_path, offline=True, opener=_no_network)
    assert offline.get(URL, "x.json", allow_absent=True).status == 404
    with pytest.raises(SecRefusal, match="absence"):
        offline.get(URL, "x.json")


def _no_network(*args, **kwargs):
    raise AssertionError("offline mode made a request")


def test_offline_reads_cache_only_and_refuses_on_hash_mismatch(tmp_path: Path, ua: str) -> None:
    c, _ = client(tmp_path, {URL: b'{"a": 1}'})
    online = c.get(URL, "x.json")
    offline = SecClient(tmp_path, offline=True, opener=_no_network)
    assert offline.get(URL, "x.json") == online
    with pytest.raises(SecRefusal, match="not cached"):
        offline.get(URL.replace("0001", "0002"), "y.json")
    (tmp_path / "x.json").write_bytes(b'{"a": 2}')
    with pytest.raises(SecRefusal, match="does not match its recorded SHA-256"):
        offline.get(URL, "x.json")
    with pytest.raises(SecRefusal, match="does not match"):
        c.get(URL, "x.json")
    (tmp_path / "z.json").write_bytes(b"{}")
    with pytest.raises(SecRefusal, match="no retrieval record"):
        offline.get(URL.replace("0001", "0003"), "z.json")
    with pytest.raises(SecRefusal, match="another URL"):
        offline.get(URL.replace("0001", "0004"), "x.json")


@pytest.mark.parametrize("url", ["http://data.sec.gov/x.json", "https://example.com/x.json",
                                 "https://data.sec.gov.example.com/x.json", "https://sec.gov/x.json"])
def test_only_sec_hosts_over_https(tmp_path: Path, ua: str, url: str) -> None:
    c, opener = client(tmp_path, {})
    with pytest.raises(SecRefusal, match="allowlist"):
        c.get(url, "x.json")
    assert not opener.calls

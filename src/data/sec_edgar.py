"""SEC EDGAR files: the project's only network path to the SEC (owner decision O-10).

Requests go only to ``www.sec.gov`` and ``data.sec.gov``, at most four a second,
with retry and backoff on HTTP 429 and 5xx. The ``User-Agent`` is read from the
environment variable ``EFR_SEC_USER_AGENT`` at request time; it is never logged,
printed, returned, or written to any file, and an unset value refuses.

Raw files go to a gitignored cache (``data/public_cache/sec/``, R11). A sidecar
``<file>.retrieval.json`` records the URL, the retrieval time (UTC), the HTTP
status, and the SHA-256. A 404 is recorded as a typed absence (status 404, no
file), so an offline rerun reproduces it. Offline mode reads only the cache: a
file without a sidecar, or whose bytes differ from the recorded SHA-256,
refuses. No request is made in offline mode.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlsplit

from data.public_factors import sha256_file


USER_AGENT_ENV = "EFR_SEC_USER_AGENT"
ALLOWED_HOSTS = frozenset({"www.sec.gov", "data.sec.gov"})
MAX_REQUESTS_PER_SECOND = 4.0
MAX_ATTEMPTS = 6
BACKOFF_CAP_SECONDS = 60.0
TIMEOUT_SECONDS = 120

COMPANY_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
COMPANY_TICKERS_EXCHANGE_URL = "https://www.sec.gov/files/company_tickers_exchange.json"
CIK_LOOKUP_URL = "https://www.sec.gov/Archives/edgar/cik-lookup-data.txt"
SUBMISSIONS_URL = "https://data.sec.gov/submissions/{name}"
COMPANYFACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json"


class SecRefusal(ValueError):
    """An SEC request or cached SEC file fails a declared check. Messages never carry the User-Agent."""


@dataclass(frozen=True)
class SecFile:
    """One cached SEC file. ``status`` is 200, or 404 for a recorded absence (``sha256`` then ``None``)."""

    relative: str
    url: str
    retrieved_utc: str
    status: int
    sha256: str | None
    n_bytes: int

    def read_bytes(self, cache_dir: Path) -> bytes:
        if self.status != 200:
            raise SecRefusal(f"{self.relative} is a recorded absence")
        return (cache_dir / self.relative).read_bytes()


def user_agent() -> str:
    value = os.environ.get(USER_AGENT_ENV, "").strip()
    if not value:
        raise SecRefusal(f"{USER_AGENT_ENV} is unset; SEC requests need the owner's User-Agent")
    return value


def require_allowed(url: str) -> None:
    parts = urlsplit(url)
    if parts.scheme != "https" or parts.hostname not in ALLOWED_HOSTS:
        raise SecRefusal(f"URL outside the SEC allowlist: {parts.scheme}://{parts.hostname}")


def _sidecar(path: Path) -> Path:
    return path.with_name(path.name + ".retrieval.json")


class SecClient:
    """Cached SEC retrieval. ``opener``, ``clock``, and ``sleep`` exist for synthetic tests."""

    def __init__(self, cache_dir: Path, *, offline: bool = False,
                 opener: Callable[..., Any] = urllib.request.urlopen,
                 clock: Callable[[], float] = time.monotonic, sleep: Callable[[float], None] = time.sleep) -> None:
        if not offline:
            user_agent()
        self.cache_dir = Path(cache_dir)
        self.offline = offline
        self._opener, self._clock, self._sleep = opener, clock, sleep
        self._last_start: float | None = None
        self.requests = 0
        self.retries = 0

    def get(self, url: str, relative: str, *, allow_absent: bool = False) -> SecFile:
        """The cached copy of ``url`` at ``cache_dir/relative``, downloading it once when online."""

        require_allowed(url)
        path = self.cache_dir / relative
        sidecar = _sidecar(path)
        if sidecar.exists():
            return self._verified(url, relative, path, sidecar, allow_absent)
        if path.exists():
            raise SecRefusal(f"cached file {relative} has no retrieval record")
        if self.offline:
            raise SecRefusal(f"offline mode: {relative} is not cached")
        status, payload = self._download(url)
        if status == 404 and not allow_absent:
            raise SecRefusal(f"HTTP 404 for {relative}")
        retrieved = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        path.parent.mkdir(parents=True, exist_ok=True)
        digest = None
        if status == 200:
            partial = path.with_name(path.name + ".partial")
            partial.write_bytes(payload)
            partial.replace(path)
            digest = hashlib.sha256(payload).hexdigest()
        record = {"url": url, "retrieved_utc": retrieved, "status": status, "sha256": digest}
        sidecar.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
        return SecFile(relative, url, retrieved, status, digest, len(payload) if status == 200 else 0)

    def _verified(self, url: str, relative: str, path: Path, sidecar: Path, allow_absent: bool) -> SecFile:
        record = json.loads(sidecar.read_text(encoding="utf-8"))
        if record.get("url") != url:
            raise SecRefusal(f"cached file {relative} was retrieved from another URL")
        status = record.get("status")
        if status == 404:
            if not allow_absent:
                raise SecRefusal(f"cached absence for {relative} where a file is required")
            if path.exists():
                raise SecRefusal(f"cached absence for {relative} has a file beside it")
            return SecFile(relative, url, record["retrieved_utc"], 404, None, 0)
        if status != 200 or not path.exists():
            raise SecRefusal(f"cached file {relative} is missing or has an invalid status")
        digest = sha256_file(path)
        if record.get("sha256") != digest:
            raise SecRefusal(f"cached file {relative} does not match its recorded SHA-256")
        return SecFile(relative, url, record["retrieved_utc"], 200, digest, path.stat().st_size)

    def _throttle(self) -> None:
        interval = 1.0 / MAX_REQUESTS_PER_SECOND
        now = self._clock()
        if self._last_start is not None and now - self._last_start < interval:
            self._sleep(interval - (now - self._last_start))
            now = self._clock()
        self._last_start = now

    def _download(self, url: str) -> tuple[int, bytes]:
        for attempt in range(MAX_ATTEMPTS):
            self._throttle()
            self.requests += 1
            request = urllib.request.Request(url, headers={"User-Agent": user_agent(),
                                                           "Accept-Encoding": "gzip"})
            wait: float | None
            try:
                with self._opener(request, timeout=TIMEOUT_SECONDS) as response:
                    payload = response.read()
                    if (response.headers.get("Content-Encoding") or "").lower() == "gzip":
                        payload = gzip.decompress(payload)
                    return 200, payload
            except urllib.error.HTTPError as error:
                if error.code == 404:
                    return 404, b""
                if error.code != 429 and not 500 <= error.code < 600:
                    raise SecRefusal(f"HTTP {error.code} for {urlsplit(url).path}") from None
                wait = _retry_after(error.headers.get("Retry-After") if error.headers else None)
                failure = f"HTTP {error.code}"
            except (urllib.error.URLError, TimeoutError, ConnectionError) as error:
                wait, failure = None, type(error).__name__
            if attempt + 1 == MAX_ATTEMPTS:
                raise SecRefusal(f"{failure} for {urlsplit(url).path} after {MAX_ATTEMPTS} attempts")
            self.retries += 1
            self._sleep(min(BACKOFF_CAP_SECONDS, wait if wait is not None else 2.0 ** (attempt + 1)))
        raise AssertionError("unreachable")


def _retry_after(value: str | None) -> float | None:
    try:
        return max(0.0, float(value)) if value is not None else None
    except ValueError:
        return None

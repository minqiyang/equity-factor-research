# Claims Under Review: M4.7a-1 EODHD Retrieval and Holdout Partition Modules

- **Candidate Digest**: commit `ed08d6c0cd9425e9d13995596de6820bc12f1006`
- **Baseline**: `2c07ee4db70bc90cd449382c69b63765de2eab7d` (main after PR #262)
- **Branch**: `claude/m4_7a1-retrieval-and-partition`
- **Implementation Report**: `coord/reports/m4_7a1_retrieval_and_partition_impl.md`
- **Review Root**: `/Users/rhapsoul/Documents/Codex/Artifact/EFR/review-roots/m47a1-ed08d6c`
- **Operative Plan**: `coord/plans/m4_7_binding_plan.md` Revision 11 (SHA-256 `6541db93336e9181ebf3ad2f066b7b17f4550a17565036c2db5a5d82872a6407`), §1.3, §1.4, §1.5, §7.2 (a-1), Appendices A, B, D, E

---

## Falsifiable Claims

1. **Network Boundary & T-STRUCT-1 Allowlist (§1.3, Appendix D)**:
   - `src/data/eodhd_retrieval.py` is the only module under `src/`, `research/`, and `scripts/` that imports a listed network module (T-STRUCT-1); it imports exactly `urllib.request` and `urllib.error`.
   - T-STRUCT-1 scope: an AST scan of `import` and absolute `from ... import` statements in every `.py` file under `src/`, `research/`, and `scripts/`, matched on the plan §1.3 list (`urllib.request`, `urllib.error`, `http.client`, `http.server`, `socket`, `ssl`, `requests`, `httpx`, `aiohttp`, `websocket`, `websockets`, `yfinance`, `alpaca`, `alpaca_trade_api`, `ccxt`, `ib_insync`) as exact dotted names and their submodules; `pyproject.toml` declares none of them. Tests are outside the scan and import `urllib.error` and `http.client` to build fake transport failures.
   - Outside the scan's evidence: attribute access after a bare `import urllib`, `importlib.import_module`, and network-capable IO inside permitted libraries (for example `pandas.read_csv` on a URL). The claim covers listed-module imports only.
   - Verified by `tests/test_project_structure.py::test_t_struct_1_only_the_retrieval_module_imports_network_modules` (T-STRUCT-1).

2. **Token Hygiene & Exception Sanitization (§1.3, A3)**:
   - `EFR_EODHD_API_TOKEN` is read strictly once in `main` via `os.environ.get`. If absent or blank, CLI exits 2 with fixed message without touching disk.
   - `_request` sanitizes raw, `quote`, `quote(safe="")`, and `quote_plus` token representations from all error messages, HTTP bodies, logs, and stderr tracebacks.
   - `RetrievalTransportError` is raised with `__cause__ = None` and `__context__ = None` (no chained exception leaks token).
   - `verify` scans every byte of every snapshot file and exits 1 on `token_leak_detected`.
   - Verified by `tests/test_eodhd_retrieval.py` (T-RET-1, T-RET-2, and verify scan).

3. **HTTP Status Handling, Retry, & Persistent Provider Errors (§1.3, S8)**:
   - 401/402/403 stop without retry; 404 sets typed status (`unavailable:missing_symbol`) and continues.
   - 429 applies exponential backoff (2..32s + jitter); 5xx retries up to `--retries` before marking `provider_error`.
   - `provider_error_history` tracks UTC dates; a failing invocation on a 3rd distinct UTC date transitions status to terminal `unavailable:persistent_provider_error`.
   - Resumed commands skip hashed files; `--refresh` refetches.
   - Verified by `tests/test_eodhd_retrieval.py` (T-RET-3, T-RET-4, T-RET-14, T-RET-16).

4. **Date Structure, Holdout Partitioning, & Scale Checking (§1.3, §1.4, MA3-1, C45, C55)**:
   - Strict `YYYY-MM-DD` monotonic date check; unparseable/duplicate/unsorted dates refuse code with `unavailable:date_structure:<reason>`.
   - Prices, splits, and dividends are partitioned at `holdout_end` into `discovery/` and `holdout/`. Value defects in holdout partition quarantine holdout partition only, leaving discovery partition and date sidecars valid.
   - Run-local scale check compares consecutive on-calendar bars (within 20 calendar rows); scale step $>15\%$ without split within 5 rows quarantines as `validation_failed:unverified_split`.
   - `eod` requires seal, calendar, and splits status per code (`splits_required_before_eod`, `calendar_required_before_eod`).
   - Verified by `tests/test_eodhd_retrieval.py` (T-RET-6, T-RET-7, T-RET-10, T-RET-11, T-RET-12, T-RET-13, T-RET-15, T-RET-17).

5. **Holdout Seal Derivation: `src/data/holdout_partition.py` (§1.4)**:
   - Prospective seal derived purely from metadata: `membership/historical_components_raw.parquet` (hash-verified) and `snapshot.components_retrieved_utc_date`.
   - Computes monthly raw counts $n_{\text{raw}}(m)$ on calendar month-ends with band $470 \le n \le 530$.
   - Applies rule `coverage_start_tolerant_3_isolated_v1`, sets `holdout_start = coverage_start`, `holdout_end = holdout_start + 10 calendar years`, checks `holdout_end <= 2014-01-01`.
   - Writes prospective `holdout_seal_v1.json` with `status: pending` and returns SHA-256.
   - Verified by `tests/test_m4_7_holdout_seal.py` (T-SEAL-1).

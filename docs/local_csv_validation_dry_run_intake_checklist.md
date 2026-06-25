# Local CSV Validation-Only Dry Run Intake Checklist

Date: 2026-06-24

Use this checklist before asking Codex to inspect any user-provided local CSV
bundle. This is for a validation-only dry run: schema, provenance, alignment,
and readiness checks only. It does not authorize a strategy run, performance
interpretation, data fetching, vendor APIs, credentials, brokerage, live or
paper trading, order execution, or profitability claims.

## Files To Provide

Provide local files or redacted local handles for each required input:

| File | Required? | Purpose |
| --- | --- | --- |
| Adjusted close prices | yes | Close-based features, returns, and validation alignment. |
| OHLCV prices and volume | yes | Volume, liquidity, OHLC consistency, and volume-aware validation. |
| Benchmark series | yes | Date alignment and future benchmark-relative diagnostics. |
| Universe membership or eligibility | yes | Universe rule, point-in-time status, and survivorship review. |
| Metadata sidecar or notes | yes | Source, export/version, adjustment policy, calendar, and caveats. |
| Optional factor panel | optional | Only if validating user-supplied factors. |

## Required Columns

Accepted schemas and minimum columns:

| Input | Accepted schema | Required columns |
| --- | --- | --- |
| Adjusted close prices | wide price panel | `date` plus one column per symbol containing adjusted close. |
| Adjusted close prices | long price panel | `date`, `symbol`, `adjusted_close`. |
| OHLCV | long OHLCV panel | `date`, `symbol`, `open`, `high`, `low`, `close`, `volume`; include adjusted OHLC/close fields if available. |
| Benchmark | price series | `date`, benchmark adjusted close or total-return level. |
| Benchmark | return series | `date`, benchmark return; state whether returns are simple or log returns. |
| Universe | membership table | `date`, `symbol`, membership or eligibility flag. |
| Factor panel | wide factor panel | `date` plus one column per symbol. |
| Factor panel | long factor panel | `date`, `symbol`, factor value. |

Do not ask Codex to guess schemas. If column names differ, provide a column map.

## Metadata To Provide

- Date range: first date, last date, expected trading calendar, warm-up period,
  and any known gaps or partial sessions.
- Benchmark: ticker/name, source, adjustment policy, coverage dates, and why it
  matches the universe.
- Universe rule: membership source, liquidity rule, minimum history rule,
  price filter, exclusions, point-in-time status, and survivorship-bias caveat.
- Adjusted price policy: raw, split-adjusted, dividend-adjusted,
  total-return-adjusted, or unknown; include asset and benchmark policy.
- Volume/OHLCV policy: raw or adjusted volume, zero-volume meaning, stale-row
  caveats, and whether OHLC fields share the same adjustment basis.
- Train/validation/test split: warm-up exclusion, in-sample period, validation
  period, test or holdout period, and when parameters were chosen.
- Cost and slippage assumptions: transaction cost model, slippage model,
  turnover/rebalance assumptions, execution timing, and whether zero-cost or
  zero-slippage outputs are diagnostic only.
- Provenance: source name supplied by you, export timestamp or version, hash or
  hash plan for mutable files, known manual edits, and known excluded rows or
  symbols.

## GitHub And Inspection Boundary

Must not be committed to GitHub:

- private CSV data.
- raw local file contents.
- proprietary vendor exports unless explicitly approved as public.
- secrets, tokens, `.env` files, credentials, account identifiers, broker files,
  private account metadata, or private directory details.
- generated real-data reports or experiment outputs from the dry run.

Codex may inspect, after you approve the bundle:

- file names or redacted local handles.
- headers and schema maps.
- row/column counts, date ranges, duplicate counts, missing-value counts, and
  validation summaries.
- small non-sensitive snippets only if needed for schema diagnosis and approved
  by you.

Codex must not inspect:

- secrets, tokens, `.env`, credentials, SSH keys, account files, or broker
  configuration.
- unrelated local directories or files.
- full private/raw CSV contents unless you explicitly approve a narrow
  validation read.
- any file outside the declared CSV bundle.

## Ready Prompt

Once the CSV bundle and metadata are ready, use:

```text
I have a local CSV bundle ready for a validation-only dry run.
Do not fetch data, use vendor APIs, use credentials, run a strategy, or
interpret performance.

Bundle location or redacted handles:
- adjusted close:
- OHLCV:
- benchmark:
- universe:
- metadata sidecar:
- optional factor panel:

Column map:
- adjusted close:
- OHLCV:
- benchmark:
- universe:
- optional factor panel:

Metadata:
- date range and calendar:
- benchmark and adjustment policy:
- universe rule and point-in-time status:
- adjusted price and volume policy:
- train/validation/test split:
- costs, slippage, rebalance, and execution timing:
- provenance, export version/timestamp, hash plan, manual edits:

Please perform metadata-first readiness intake only and stop before any
strategy run or performance interpretation.
```

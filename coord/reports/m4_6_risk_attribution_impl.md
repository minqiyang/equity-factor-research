# M4.6 Multi-Factor Risk Attribution Implementation

The candidate adds optional five-style return attribution and causal active-risk
forecasts to both portfolio engines. The binding card is commit `738caf5`; runtime
work starts from `b60e109c6959e059dea6c19c3573dd5e861a2ac2`. Producer write
responsibility transfers to the coordinator with the frozen candidate commit.

## Implemented behavior

`src/backtest/risk_attribution.py` implements the card's public classes and
signatures. `StyleFactorExposures` builds winsorized, demeaned, population-scaled
Size, Value, Momentum, Volatility, and Liquidity exposures. Market is a constant
intercept. The market-data constructor consumes compatible price/volume panels,
positive market capitalization, and caller-declared available book-to-price.
Warmup rows retain missing values. Selected rows require complete finite values.

`CrossSectionalRiskModel.fit` reads the immediately prior observed exposure row
and optional positive WLS weights. NumPy least squares uses rcond=1e-12. More
assets than coefficients and full column rank are required; unidentified fits
raise `rank_deficient`. Each fit records rank, condition, sample size, method,
and the actual exposure date. Weighted normal-equation golden tests verify WLS.

`PortfolioRiskAttribution` records beta, factor contribution, residual specific
return, gross return, cost, net return, active beta, risk status, and Euler
variance contributions. Every gross return reconciles to factor plus specific
contributions at absolute tolerance 1e-12. Costs remain separate from residual
return. The standalone `decompose_active_risk` accepts explicit labelled
covariance and specific variances. It validates factor/asset order, covariance
symmetry and PSD, and finite nonnegative specific variance.

Risk estimation uses at most the configured number of earlier fitted intervals,
with sample covariance and sample residual variance. The current interval stays
outside the estimation sample. History below the declared minimum produces
`insufficient_history` and missing risk values. Active weights subtract supplied
prior-close benchmark weights; the default benchmark is zero-weight cash.
Variance contributions sum to factor plus specific variance. Per-period and
annualized tracking error are exposed separately. Correlated factors can produce
negative individual Euler contributions.

## Integration and baseline evidence

Both engines accept `risk_model=None` and return a default `risk_attribution=None`
sidecar. Their existing accounting and assumptions retain their exact values.
Enabled attribution consumes actual prior-close holdings, including drift and
partial-fill impact, and verifies its gross/net series against engine results.
The initialization anchor contributes zero engine return and has no attributed
interval. The integration calculates returns for every regression asset from
complete positive price endpoints; internal held-only return arrays contain
unheld-asset zeros and therefore serve a different purpose.

Enabled integration requires an absent terminal-event table and strict complete
prices. Changing regression universes and terminal-event risk attribution have
explicit refusal boundaries. Existing PIT and terminal accounting remains
available on the default engine path. The risk sidecar contains diagnostic
active-risk forecasts; existing realized benchmark metrics retain their scope.

The preserved pre-runtime capture covers 62 factor scenarios and 124 books:

| Snapshot | Existing result fields | Uncompressed SHA-256 | Replay |
| --- | ---: | --- | --- |
| Legacy M4.5 capture schema | 2,294 | `5a885b96e7379a83658047d4720d701f504f92838ffae10a76fa267580b61ed4` | exact bytes |
| Every M4.5 result field | 3,038 | `878cfc0315ac0fa64ed120205f1c73eb1572c71822c1ea8111c229ab4e17c7d1` | exact bytes |

The all-field serializer adds raw numeric-buffer hashes, dtypes, ordered indices,
and axis metadata. It includes all six impact fields omitted by the older
capture. The new sidecar lies outside the existing-field comparison. Gzip files
preserve the exact original JSON bytes. Both snapshots also retain prior
multiple-testing, weighting, family, and PIT-demo diagnostics. The directive requests
coverage of 1,674 fields. The measured legacy snapshot contains 1,798 pandas
fields and 496 additional fields; the all-field snapshot contains 2,542 pandas
fields and the same 496 other fields.

Reproduce either capture with `PYTHONPATH=src:. python
coord/reports/m4_6_evidence/capture_baseline.py /tmp/m4-6-replay.json.gz`; append
`--legacy` for the historic schema. Compare decompressed bytes to the committed
baseline. Capture wall times and the initial baseline fingerprints remain in
`coord/reports/m4_6_evidence/`.

## Reproducible diagnostic and negative evidence

Run `PYTHONPATH=src:. python -m research.risk_attribution_demo` to generate the
report and append started/final records for every case. Seed 4606 generates 100
observed closes and 24 predeclared synthetic identities. Eight combinations of
engine, OLS/WLS, and signal direction succeed; all eight produce negative
compounded net returns. Two deliberately invalid cases retain collinearity and
warmup refusals. The maximum measured reconstruction error is
`3.469446951953614e-18`. Long-only forecasts use a prior-close equal-weight
benchmark; long-short forecasts use cash. Trading costs are 10 bps commission
plus 5 bps slippage. WLS uses W=sqrt(market cap).

The report separates arithmetic contribution sums from compounded net return.
A temporary-output replay matches all returned case measurements exactly.
Failure injection verifies retention of all ten unexpected failed cases. No
private/local market data, empirical performance, or profitability claims enter
this candidate.

## Verification

Final commands, results, source hashes, and lane counts are recorded in
`coord/reports/m4_6_evidence/validation.json`.

| Gate | Result |
| --- | --- |
| M4.6 deterministic suite | 70 passed in the intact isolated package |
| Final core lane | 4,206 passed; 2 inherited platform precision skips; 29.54 seconds |
| Diagnostics lane | 125 passed; 91.83 seconds |
| Disjoint lane union | 4,331 passed; 2 skipped; 4,333 unique test IDs; zero intersection |
| Repository Ruff and compileall | PASS |
| Existing-field baseline replay | exact bytes for both snapshots |
| Isolated negative removals | all 52 trigger their expected failures |
| Standardized-volatility equivalence | one supported equivalent variant passes |
| Original production source preservation | verified by SHA-256 |
| Repo map and diff whitespace checks | PASS |

The first complete core run passed 4,205 tests and two inherited skips. Adding
the solver-output guard test and the report's risk/exposure tables produced the
final 4,206-pass run. Inherited constant-input correlation warnings remain in
the lane logs.
The environment is the provided shared CPython 3.12 environment, with native
numeric thread limits set to one and two worksteal workers for the CI lanes.

Initial tests retained two fixture failures caused by the impact constructor
argument `max_participation`; the public argument is `max_participation_rate`.
The expanded run retained two fixture failures caused by selecting a price row
before the bounded initialization anchor. Correcting the counterexample to the
actual anchor produced the intended complete-cross-section refusal. Runtime
accounting required zero changes for either fixture correction.

## Isolated ablation and scope assessment

`coord/reports/m4_6_evidence/ablate.py` copies the backtest package into separate
roots, verifies the imported path, applies one removal per root, and executes a
named independent counterexample. The intact baseline and all failed variants
retain output logs, selected tests, source hashes, runtime, and exit status.
The runner verifies that original production source hashes remain unchanged.
`ablation_initial_logs.tar.gz` and `ablation_final_logs.tar.gz` preserve exact
pytest output bytes, including diagnostic whitespace; every archived member
matches its manifest SHA-256. The initial unit failure log is likewise compressed.
Reproduce with `PYTHONPATH=src:. python coord/reports/m4_6_evidence/ablate.py
/tmp/m4-6-ablation-replay` using a fresh output directory.
The final experiment contains an intact baseline, 52 negative removals, and one
expected mathematical equivalence. Every final outcome matches its expectation.

The first run discovered that sample versus population historical volatility
produces equal standardized style exposures with complete equal-length windows:
the uniform sqrt(n/(n-1)) factor cancels in cross-sectional standardization.
Its unexpected-pass result remains in `ablation_initial.json` and the initial
logs. The final suite explicitly records this equivalence and separately removes
the volatility calculation, which fails the scalar oracle. The declared sample
volatility convention remains explicit for reproducibility. This is a supported
no-change simplification outcome with preserved negative and equivalent evidence.

| Subsystem | Removed component | Independent evidence |
| --- | --- | --- |
| Input contract | axes, dates, numeric/finite types, style set, alignment, availability, positive inputs, partial missingness | public typed-refusal counterexamples and empty/mixed/named-axis cases |
| Exposure transforms | winsorization, demeaning, population scaling, log size, value, momentum skip, sample volatility, dollar volume | scalar descriptor and cross-sectional golden values |
| Return extraction | prior exposure lag, positive WLS weights, WLS weighting, sample/rank guards, residual subtraction | orthogonal OLS, normal equations, singular and future-perturbation fixtures |
| Return attribution | signed beta, signed specific contribution, exact reconstruction guard, costs | independent weighted-return and residual oracles |
| Risk history | exclusion of current interval, rolling bound, warmup, sample ddof | independent lagged covariance oracle and prefix equality |
| Active risk | benchmark subtraction, factor covariance cross terms, squared active weights, specific-risk inclusion, square root, annualization | scalar covariance golden values and identical-benchmark zero risk |
| Risk validity | symmetric PSD covariance, nonnegative specific variance, finite calculated variance | invalid covariance and overflow counterexamples |
| Engine integration | supported scope, prior actual holdings, complete regression returns, reconciliation | both engines, fixed/impact costs, exact existing-field equality |

The experiment retains the minimal single-module implementation and its guards.
Some input-guard removals demonstrate stable typed-refusal contracts through
otherwise untyped library errors; calculation removals demonstrate incorrect
measurements, changed timing, or lost refusal. The coverage describes this M4.6
module and its two engine paths. It establishes a milestone ablation result;
whole-project ablation, realistic empirical covariance calibration, dynamic
universes, geometric linking, missing-fundamental policy, and industry factors
remain open. A solver-output fault injection independently verifies the finite-fit output
guard and its isolated removal.

## Limitations and next gate

Availability labels, price adjustment bases, fundamental release timing, and
permanent identities are caller declarations. The synthetic demo validates their
accepted contract. A diagonal specific-covariance model omits residual cross
correlations and factor/residual covariance; estimated model risk therefore
has a separate interpretation from realized active variance. Sample covariance
can be singular and noisy in short windows. Residual sample variance uses raw
fitted residuals; cross-sectional degrees-of-freedom calibration remains open.
Engine risk warmup starts with the first attributed interval in the bounded
evaluation window. Standardized exposure collinearity
refuses explicitly. Asset selection for the regression universe must be declared
causally by the caller, with complete coverage throughout the enabled window.
Observed-close labels carry the caller's frequency; periods-per-year is explicit.

Independent single-seat GPT-6 Astra High Fast review from a clean exact-head root
and hosted CI belong to the coordinator's next gate. This report records producer
implementation and local evidence; independent review remains pending.

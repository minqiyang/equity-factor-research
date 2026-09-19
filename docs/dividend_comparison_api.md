# Synthetic Dividend Comparison Callable and Evidence

Step 3 implements the synthetic-only convention accepted on design candidate
`7307a19d1a72138afd423cf5d6ece99f33970925`, merged at
`5d673f26eea0174236c601fa822916506894ef20`. The economic authority is
[the accepted design](synthetic_event_reconciliation_design.md). This note
specifies its bounded Python callable, evidence fields, and diagnostic records.
The implementation evidence and acceptance matrix are in
[the attempt report](../reports/dividend_comparison_attempt.md).

## Callable boundary

`research.dividend_comparison` defines frozen `DividendComparisonRequest` and
`DividendWindow` dataclasses. Both demo run functions accept the optional
keyword `comparison_request`. Their existing result objects and accounting
paths remain unchanged. `None` follows the existing default path, with
conceptual `NOT_REQUESTED` coverage `0/0` and zero new report/log fields.
Supplying `event_table` alone retains M3-08 date-membership semantics.

A request contains `convention`, exactly
`synthetic_ordinary_cash_dividend_gross_ex_close_v1`, and a nonempty tuple
`windows`. Each window has these fields:

| Field | Structural requirement |
| --- | --- |
| `item_id` | Nonempty string, unique within this request. |
| `security_id`, `listing_id` | Explicit nonempty synthetic identifiers beginning `SYNTH:`. Evidence still proves their mapping and effective episode. |
| `asset` | Explicit nonempty supplied-panel column name. |
| `prior`, `ex` | Exact `YYYY-MM-DD` source labels with `prior < ex`. Source membership and observed-row adjacency are evidence checks. |
| `cutoff` | Exact UTC timestamp `YYYY-MM-DDTHH:MM:SS[.fraction]Z`, with up to nine fractional digits. Its relation to evidence closes and availability is an evidence check. |
| `evidence` | A dictionary or `None`. `None` and `{}` produce D25 and D26 for the explicit scope. |

Duplicate security/listing/prior/ex scopes are refused even when item IDs
or cutoffs differ. Overlapping requested scopes that assign the same supplied
asset to different permanent security/listing identities, or the same
permanent identity to different assets, receive `identity_unresolved` and
`economic_acceptance` false for each affected item. Distinct assets and
nonoverlapping observation episodes keep their per-item diagnoses. A later
vintage/cutoff comparison uses a separate attempt, which retains the earlier
result. Malformed containers, empty requests, unknown conventions, invalid
scope/cutoff encodings, and duplicate scopes raise `TypeError` or
`ValueError`. Missing identities inside a well-formed scope, incomplete
fields, unknown bases, invalid numerics, unknown availability, and
non-string evidence keys produce the matrix's insufficient-evidence
diagnoses.

`retain_comparisons(request, prices, append_item)` is the bounded comparison
entry point. It validates request structure, evaluates items in request order,
and calls `append_item` immediately for each completed item. The runners bind
that callback to their existing attempt append function and current attempt
ID. Callback exceptions propagate before any later item or report preparation.
The callable reads the supplied panel and evidence; it leaves both intact.

## Evidence dictionary

The fixture helper in `tests/test_dividend_comparison.py` shows a complete
literal example. Every window supplies its complete scoped event evidence;
comparison retains every supplied row. Distinct securities use separate
windows and explicit mappings. Unsupported co-events on a requested window
remain visible and prevent acceptance.

| Field | Required contents |
| --- | --- |
| `vintage_id`, `provenance` | Nonempty immutable fixture/version and provenance references. |
| `sha256` | Exact lowercase digest produced by `evidence_sha256(evidence)`. |
| `as_of_cutoff` | Inclusive immutable vintage knowledge cutoff covering the requested cutoff. |
| `raw_field` | `field_id`, independent `provenance`, `basis="raw"`, `share_basis="unchanged_ordinary_share"`, `currency="USD"`, `units="USD/share"`, and availability. |
| `adjusted_field` | `field_id`, distinct supplied-level `provenance`, `basis="gross_total_return"`, `currency="USD"`, `units="index_points"`, common `scale_id`, immutable `adjustment_set_id` and `version`, and availability. |
| `policy` | `entitlement="pre_ex_holder"`, `dividend="gross"`, `withholding="zero"`, `reinvestment="ex_close"`, and availability. |
| `identity` | `mappings` list of `{asset, security_id, listing_id}` with one-to-one mapping for the requested asset/identity; effective interval fields and availability. |
| `source_times` | `rows` list of `{label, close}` with unique requested labels and expressly supplied UTC close timestamps; availability. |
| `coverage` | One declaration for each role below, plus availability of the declaration itself. |
| `raw_prior`, `raw_ex`, `adjusted_prior`, `adjusted_ex` | Anchor records defined below. |
| `events` | Complete list of event revisions for the requested security/window. An absent list is D25 and an empty list is D26. |

The content hash covers the entire dictionary except the `sha256` field.
Canonicalization uses `json_evidence`, sorted keys, compact separators, UTF-8,
and strict JSON. Caller dictionaries encode as
`{"json_evidence": "object", "items": {<caller keys>}}`, so caller keys
including nested `items` and `json_evidence` remain inside the envelope.
Integer payloads retain type and decimal-string value; finite real payloads
retain their exact numerator/denominator; Decimal, complex, nonfinite and
unsupported values retain typed representations. Tuples retain a distinct
container encoding from lists. Dictionaries with non-string keys retain a
typed item list of `{json_evidence: pair, key, value}` records. These
encodings preserve invalid evidence for diagnosis. A classification-changing
mutation of retained contents changes the digest and the snapshot even when
the declared hash is left unchanged. A hash binds the caller-declared
synthetic fixture contents; its authority is synthetic provenance rather than
independent vendor certification. Field references, actual supplied-panel
anchor values, and the root digest are checked together.

An anchor contains `value`, `status`, `label`, `field_id`, `provenance`,
`security_id`, `listing_id`, and `availability`. Its label, field, and identity
must match its role. Supplied adjusted anchors must equal the actual supplied
panel cells exactly. Raw anchor literals have independent provenance. Both
raw anchors and supplied levels require `OBSERVED` status. Other states and
missing fields remain typed in the item record. Observation states serialize
through `json_evidence`, so invalid states stay JSON-safe on the completed
item.

An event row contains `event_id`, `revision_id`, explicit `supersedes` (null
for the root revision), `event_type="ordinary_cash_dividend"`, `security_id`,
`listing_id`, `ex_date`, `amount`, `status="OBSERVED"`, `currency="USD"`,
`units="USD/share"`, `provenance`, and `availability`. Record/payment metadata
may be retained in the dictionary; those fields carry no window/availability
authority. Eligible revision history must have one current head and complete,
acyclic, stable-identity predecessors. Duplicate revision rows are refused.
Later-known revisions are retained in `excluded_revisions` at earlier cutoffs.
Multiple distinct events on a security/window remain outside the single-event
family. No row deduplication, event summation, or co-event filtering occurs.

## Time, identity, and coverage

Every availability dictionary explicitly supplies `source_published_at`,
`public_available_at`, `provider_available_at`, `revision_published_at`,
`parent_available_at`, `known_at`, and `retrieved_at_utc`. Values use the
exact UTC timestamp encoding above. `known_at` is at least every applicable
publication/public/provider/revision/parent timestamp, and retrieval is at
least `known_at`. Required records are available by the inclusive cutoff.
Anchors become known strictly after their supplied closes. Anchor field,
identity, and source-label parent declarations must be known by the anchor;
event identity declarations must be known by the event. Date-only or unknown
availability remains unproven. Calendar/session inference is outside the
callable.

Identity uses `effective_from`, always-present `effective_to`, and
`effective_to_state`. `FINITE` has an exact exclusive end covering both
anchors; `OPEN_IN_VINTAGE` has null `effective_to` and the explicit vintage
coverage limits. An exclusive end at the ex close fails. An end at the later
cutoff can cover both closes. Each requested interval consists of adjacent
observed source closes. Both existing demo source guards run first.

Coverage roles are `raw_prior`, `raw_ex`, `adjusted_prior`, `adjusted_ex`,
`events`, `identity`, `raw_field`, `adjusted_field`, `policy`, and
`source_times`. Each declaration has literal `verified=true`, `complete=true`,
`from` covering the prior close, and inclusive `through` covering the cutoff.
The vintage cutoff independently covers the request. Coverage declarations
establish only the named synthetic fixture scope.

## Numeric and diagnostic records

Admission establishes a real non-Boolean finite mathematical scalar exactly
equal to a finite binary64 encoding. The original value is represented as an
exact rational before comparing it with that encoding. Integer, NumPy integer,
Decimal, Fraction, and floating payloads obey the same value rule. Conversion
of an inadmissible value supplies typed `numeric_invalid` evidence. Admitted
values must then be strictly positive.

The comparator evaluates `(P_e + D) / P_p - 1`, `A_e / A_p - 1`, and their
difference with `Fraction`. It compares the unrounded absolute difference
against exactly `1/10^12`. Return fields and tolerance serialize as
`{numerator: decimal_string, denominator: decimal_string}`. The binary64
calculation is a separate diagnostic; infinities and NaNs have explicit typed
JSON objects. D41 retains exact delta `-1`, and D46 retains its finite rational
verdict alongside diagnostic overflow. The internal classifier covers the
D32/D47 conditional missing-classification outcomes; ordinary production
comparison always computes the rational classification. The injected-return
D04/D05/D44 fixtures test that classifier directly without adding a public
return override or precision-mode switch.

Each item record uses discriminator `record_type="dividend_comparison_item"`
and includes the runner's `attempt_id`, `item_id`, full requested `scope`,
convention, vintage/hash, evidence snapshot, selected/excluded revisions,
observation states, ordered reasons, `comparison_status`, `requested=1`,
`compared`, and `economic_acceptance`. The opt-in report JSON copies that
`attempt_id` onto each serialized item. Comparable records also retain exact
returns/delta and typed binary64 diagnostics. Multiple prerequisites retain
all applicable reasons in the design's order and suppress numeric match
classification. Adjusted-anchor panel binding runs whenever the supplied
index and column are bindable; `identity_unresolved` remains an independent
reason. `economic_acceptance` applies only to the named synthetic window.
Aggregate all-window acceptance requires every requested item to be
`MATCHED`; partial coverage and mismatches remain visible.

## Runner sequence and failures

The opt-in output preflight requires distinct report/log file identities, including
symlinks and hardlinks. An alias fails before start append because preserving
both artifacts requires separate identities. The opt-in sequence is existing attempt start, existing guards and simulation,
per-item comparison plus immediate append, same-filesystem temporary report
preparation, destination replacement, and terminal success append. The report
binds the attempt ID and displays item status, coverage, acceptance and exact
evidence. Its execution-completion statement points to the terminal log;
report bytes alone establish no terminal success. The opt-in absent-event-table
disclosure distinguishes M3-08 metadata from the explicit comparison request.
Default report text and log records retain their existing bytes/format.

Well-formed mismatched or insufficient evidence is a successful diagnostic
execution with affected economic acceptance blocked. Existing guards and
structurally malformed requests raise. Completed items survive subsequent
comparison, append, report, or terminal failures. Original exceptions and
interruptions propagate even if terminal logging fails. Preparation and
failed replacement preserve the previous report. After successful replacement,
a later error/interruption can leave the new report with an incomplete or
failed attempt. Partial append bytes remain visible; automatic repair and
cross-file rollback are absent. The contract supplies sequential local demo
retention rather than concurrent-writer, power-loss, or crash-atomic storage.

The comparator supplies no accounting, signal, benchmark, price, holdings,
cost, or execution inputs. Its formula models only the accepted one-interval
gross measurement convention. Milestone 3 remains in progress; Step 4 retains
the separate private-data owner gate and dataset-specific acceptance.

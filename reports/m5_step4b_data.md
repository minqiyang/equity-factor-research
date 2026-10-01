# Milestone 5 Step 4b SEC Data Build: CIK Map and Company-Facts Coverage

Evidence ceiling `DIAGNOSTIC_ONLY`. Identity and schema coverage only: no signal, sleeve, return, or rule result was computed. Counts are aggregates; the CIK map and per-file hashes stay local (R11, O-10).

**Conclusion.** Rule F maps 563 of 632 eligible permanent IDs to one CIK (89.1%); 7 are ambiguous, 54 unmapped, and 8 multi-class, all typed missing. Company facts exist for 563 of 563 mapped IDs.

## Provenance

- Code commit `ccca7759686a89ad92b8c4f491a6982f0bb11115`; snapshot `real_v2` bound to amendment 4 (`c2b1f8dea064ef1852d55bfda365faef8bd1c658897877037aae2fc0714ac617`).
- Sources: SEC `company_tickers.json`, `company_tickers_exchange.json`, `cik-lookup-data.txt`, submissions with history pages, and XBRL companyfacts, through `src/data/sec_edgar.py` only.
- Manifest `reports/m5_step4b_sec_manifest.json`: 2427 cached files, hash-list SHA-256 `3c73ffe2210bd87147ecc79e1963ef08a86843a937b06fe62ede372e27c6698a`, CIK-map SHA-256 `09d163b91d386064553935d0648424fa1bd1d1469fec2404a440c65c3fed120a`.

| Source | Files | Recorded 404 | Bytes |
|---|---|---|---|
| company_tickers | 1 | 0 | 798399 |
| company_tickers_exchange | 1 | 0 | 523357 |
| cik_lookup_data | 1 | 0 | 40209988 |
| submissions | 917 | 0 | 115385331 |
| submissions_history_pages | 944 | 0 | 212291728 |
| companyfacts | 563 | 0 | 2081565096 |

## Eligible pool

- 632 permanent IDs: resolved, with a side panel, and a member window overlapping the segment (by segment: post 510, pre 468).

## Mapping outcome (rule F, fail-closed)

Per permanent ID:

| unique | ambiguous | unmapped | multi_class |
|---|---|---|---|
| 563 | 7 | 54 | 8 |

By segment (one row per ID and segment):

| segment | unique | unmapped | ambiguous | multi_class | total |
|---|---|---|---|---|---|
| post | 474 | 31 | 1 | 4 | 510 |
| pre | 417 | 38 | 6 | 7 | 468 |

By later exit class (per ID):

| exit class | unique | unmapped | ambiguous | multi_class | total |
|---|---|---|---|---|---|
| delisting_candidate | 63 | 1 | 4 | 3 | 71 |
| disappearance_outside_membership | 19 | 10 | 2 | 0 | 31 |
| index_removal_still_trading | 481 | 43 | 1 | 5 | 530 |

By segment and later exit class:

| segment / exit class | unique | unmapped | ambiguous | multi_class | total |
|---|---|---|---|---|---|
| post / delisting_candidate | 25 | 1 | 0 | 1 | 27 |
| post / disappearance_outside_membership | 5 | 1 | 0 | 0 | 6 |
| post / index_removal_still_trading | 444 | 29 | 1 | 3 | 477 |
| pre / delisting_candidate | 57 | 0 | 4 | 2 | 63 |
| pre / disappearance_outside_membership | 18 | 9 | 2 | 0 | 29 |
| pre / index_removal_still_trading | 342 | 29 | 0 | 5 | 376 |

Reasons (per ID):

| status: reason | IDs |
|---|---|
| ambiguous: several_survivors | 3 |
| ambiguous: ticker_cik_disagrees | 4 |
| multi_class: shared_cik_overlapping | 8 |
| unique: accepted | 563 |
| unmapped: name_mismatch | 18 |
| unmapped: no_periodic_filing_in_window | 36 |

Multi-class: 8 IDs share an accepted CIK (8 with overlapping member windows, 0 disjoint); 563 distinct CIKs are uniquely mapped.

## Company facts for mapped IDs

An annual fact is a us-gaap fact from a 10-K or 10-KT filed inside the ID's member window. A 404 is recorded as a typed absence.

| segment | present_with_annual_fact_in_window | present_no_annual_fact_in_window | absent | total |
|---|---|---|---|---|
| post | 467 | 7 | 0 | 474 |
| pre | 415 | 2 | 0 | 417 |

| exit class | present_with_annual_fact_in_window | present_no_annual_fact_in_window | absent | total |
|---|---|---|---|---|
| delisting_candidate | 62 | 1 | 0 | 63 |
| disappearance_outside_membership | 19 | 0 | 0 | 19 |
| index_removal_still_trading | 473 | 8 | 0 | 481 |

| ended filers | present_with_annual_fact_in_window | present_no_annual_fact_in_window | absent | total |
|---|---|---|---|---|
| ended | 81 | 1 | 0 | 82 |
| not_ended | 473 | 8 | 0 | 481 |

## vendor_name and isin: current or point-in-time

- Mapped IDs whose CIK changed its SEC name inside the member window: 205. The vendor name equals the current SEC name for 188 and only a former SEC name for 17.
- ISIN is one undated value per permanent ID: blank 23, non-US prefix 36, IDs sharing an ISIN with another eligible ID 0.
- Reused vendor codes (`_old`) paired with the ID now holding the ticker: 1 pairs; same ISIN 0, same normalized name 1.
- Reading: vendor_name behaves mostly as a current (latest) value, not a point-in-time one (188 of 205 renamed IDs); isin has one undated value per ID, so it cannot be point-in-time. Neither field enters a signal; rule F uses vendor_name only with an in-window filing check.

## Limitations

- Not uniquely mapped, by later exit class: delisting_candidate 8 of 71; disappearance_outside_membership 12 of 31; index_removal_still_trading 49 of 530. Where the not-mapped share differs by exit class, the mapped sample is tilted; step 4b's coverage-tilt guard addresses this, and this build makes no claim.
- SEC's ticker files are current, not point-in-time; rule F uses them only as candidates and requires a name match and a periodic filing inside the member window.
- Multi-class and foreign-form IDs are typed missing, not repaired; there is no hand override list.

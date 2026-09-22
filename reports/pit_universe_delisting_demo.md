# PIT Universe and Terminal Cash Synthetic Diagnostic

Evidence ceiling: DIAGNOSTIC_ONLY. Twelve generated source dates and three predeclared permanent IDs.
The static roster and changing index membership are explicit synthetic controls. Historical ticker REUSED belongs to SEC_OLD and then SEC_NEW; their price columns remain separate.

Targets use lag-1 signals and the membership schedule known at that decision cutoff. The old security's -60% complete terminal return settles once on 2024-01-08. Ordinary turnover pays 10 bps commission and 5 bps slippage; terminal redemption has zero extra modeled fee.

Cash is the residual of the existing postcost target-weight convention. Signed terminal cash flows credit long proceeds and debit short liabilities. Same-close cash can fund a frozen eligible target. Unscheduled surviving long-short exposures drift until the next feasible scheduled reset.

Delayed payments, unpriced receivables, stock consideration, full revision histories, and verified source calendars remain separate work. The declared availability labels and synthetic identities supply simulation conformance evidence.

## All attempted cases

| case | status | final equity | signed terminal proceeds | refusal reason |
| --- | --- | --- | --- | --- |
| long_only_static_roster | success | 1102.965192 | 0.000000 |  |
| long_only_pit_membership | success | 423.335191 | 399.400000 |  |
| long_only_missing_terminal_evidence | refused | undefined | undefined | incoming_price_invalid |
| long_short_static_roster | success | 1205.507104 | -101.352982 |  |
| long_short_pit_membership | success | 719.378524 | 199.700000 |  |
| long_short_missing_terminal_evidence | refused | undefined | undefined | incoming_price_invalid |

## Knowledge cutoffs and eligibility

| execution close | decision cutoff | eligible permanent IDs |
| --- | --- | --- |
| 2024-01-01 | initialization |  |
| 2024-01-02 | 2024-01-01 | SEC_OLD, SEC_REF |
| 2024-01-03 | 2024-01-02 | SEC_OLD, SEC_REF |
| 2024-01-04 | 2024-01-03 | SEC_OLD, SEC_REF |
| 2024-01-05 | 2024-01-04 | SEC_OLD, SEC_REF |
| 2024-01-08 | 2024-01-05 | SEC_NEW, SEC_REF |
| 2024-01-09 | 2024-01-08 | SEC_NEW, SEC_REF |
| 2024-01-10 | 2024-01-09 | SEC_NEW, SEC_REF |
| 2024-01-11 | 2024-01-10 | SEC_NEW, SEC_REF |
| 2024-01-12 | 2024-01-11 | SEC_NEW, SEC_REF |
| 2024-01-15 | 2024-01-12 | SEC_NEW, SEC_REF |
| 2024-01-16 | 2024-01-15 | SEC_NEW, SEC_REF |

## long_only_static_roster

| close | equity | cash | terminal cash flow | signed closing holdings |
| --- | --- | --- | --- | --- |
| 2024-01-01 | 1000.000000 | 1000.000000 | 0.000000 | SEC_OLD=0.000000, SEC_NEW=0.000000, SEC_REF=0.000000 |
| 2024-01-02 | 998.500000 | 0.000000 | 0.000000 | SEC_OLD=0.000000, SEC_NEW=1.000000, SEC_REF=0.000000 |
| 2024-01-03 | 1008.485000 | 0.000000 | 0.000000 | SEC_OLD=0.000000, SEC_NEW=1.000000, SEC_REF=0.000000 |
| 2024-01-04 | 1018.569850 | 0.000000 | 0.000000 | SEC_OLD=0.000000, SEC_NEW=1.000000, SEC_REF=0.000000 |
| 2024-01-05 | 1028.755549 | 0.000000 | 0.000000 | SEC_OLD=0.000000, SEC_NEW=1.000000, SEC_REF=0.000000 |
| 2024-01-08 | 1039.043104 | 0.000000 | 0.000000 | SEC_OLD=0.000000, SEC_NEW=1.000000, SEC_REF=0.000000 |
| 2024-01-09 | 1049.433535 | 0.000000 | 0.000000 | SEC_OLD=0.000000, SEC_NEW=1.000000, SEC_REF=0.000000 |
| 2024-01-10 | 1059.927870 | 0.000000 | 0.000000 | SEC_OLD=0.000000, SEC_NEW=1.000000, SEC_REF=0.000000 |
| 2024-01-11 | 1070.527149 | 0.000000 | 0.000000 | SEC_OLD=0.000000, SEC_NEW=1.000000, SEC_REF=0.000000 |
| 2024-01-12 | 1081.232421 | 0.000000 | 0.000000 | SEC_OLD=0.000000, SEC_NEW=1.000000, SEC_REF=0.000000 |
| 2024-01-15 | 1092.044745 | 0.000000 | 0.000000 | SEC_OLD=0.000000, SEC_NEW=1.000000, SEC_REF=0.000000 |
| 2024-01-16 | 1102.965192 | 0.000000 | 0.000000 | SEC_OLD=0.000000, SEC_NEW=1.000000, SEC_REF=0.000000 |

## long_only_pit_membership

| close | equity | cash | terminal cash flow | signed closing holdings |
| --- | --- | --- | --- | --- |
| 2024-01-01 | 1000.000000 | 1000.000000 | 0.000000 | SEC_OLD=0.000000, SEC_NEW=0.000000, SEC_REF=0.000000 |
| 2024-01-02 | 998.500000 | 0.000000 | 0.000000 | SEC_OLD=1.000000, SEC_NEW=0.000000, SEC_REF=0.000000 |
| 2024-01-03 | 998.500000 | 0.000000 | 0.000000 | SEC_OLD=1.000000, SEC_NEW=0.000000, SEC_REF=0.000000 |
| 2024-01-04 | 998.500000 | 0.000000 | 0.000000 | SEC_OLD=1.000000, SEC_NEW=0.000000, SEC_REF=0.000000 |
| 2024-01-05 | 998.500000 | 0.000000 | 0.000000 | SEC_OLD=1.000000, SEC_NEW=0.000000, SEC_REF=0.000000 |
| 2024-01-08 | 398.800900 | 0.000000 | 399.400000 | SEC_OLD=0.000000, SEC_NEW=1.000000, SEC_REF=0.000000 |
| 2024-01-09 | 402.788909 | 0.000000 | 0.000000 | SEC_OLD=0.000000, SEC_NEW=1.000000, SEC_REF=0.000000 |
| 2024-01-10 | 406.816798 | 0.000000 | 0.000000 | SEC_OLD=0.000000, SEC_NEW=1.000000, SEC_REF=0.000000 |
| 2024-01-11 | 410.884966 | 0.000000 | 0.000000 | SEC_OLD=0.000000, SEC_NEW=1.000000, SEC_REF=0.000000 |
| 2024-01-12 | 414.993816 | 0.000000 | 0.000000 | SEC_OLD=0.000000, SEC_NEW=1.000000, SEC_REF=0.000000 |
| 2024-01-15 | 419.143754 | 0.000000 | 0.000000 | SEC_OLD=0.000000, SEC_NEW=1.000000, SEC_REF=0.000000 |
| 2024-01-16 | 423.335191 | 0.000000 | 0.000000 | SEC_OLD=0.000000, SEC_NEW=1.000000, SEC_REF=0.000000 |

## long_short_static_roster

| close | equity | cash | terminal cash flow | signed closing holdings |
| --- | --- | --- | --- | --- |
| 2024-01-01 | 1000.000000 | 1000.000000 | 0.000000 | SEC_OLD=0.000000, SEC_NEW=0.000000, SEC_REF=0.000000 |
| 2024-01-02 | 998.500000 | 998.500000 | 0.000000 | SEC_OLD=-0.250000, SEC_NEW=0.500000, SEC_REF=-0.250000 |
| 2024-01-03 | 1003.485011 | 1003.485011 | 0.000000 | SEC_OLD=-0.250000, SEC_NEW=0.500000, SEC_REF=-0.250000 |
| 2024-01-04 | 1008.494910 | 1008.494910 | 0.000000 | SEC_OLD=-0.250000, SEC_NEW=0.500000, SEC_REF=-0.250000 |
| 2024-01-05 | 1013.529821 | 1013.529821 | 0.000000 | SEC_OLD=-0.250000, SEC_NEW=0.500000, SEC_REF=-0.250000 |
| 2024-01-08 | 1170.018825 | 1170.018825 | -101.352982 | SEC_OLD=0.000000, SEC_NEW=0.500000, SEC_REF=-0.500000 |
| 2024-01-09 | 1175.860144 | 1175.860144 | 0.000000 | SEC_OLD=0.000000, SEC_NEW=0.500000, SEC_REF=-0.500000 |
| 2024-01-10 | 1181.730626 | 1181.730626 | 0.000000 | SEC_OLD=0.000000, SEC_NEW=0.500000, SEC_REF=-0.500000 |
| 2024-01-11 | 1187.630416 | 1187.630416 | 0.000000 | SEC_OLD=0.000000, SEC_NEW=0.500000, SEC_REF=-0.500000 |
| 2024-01-12 | 1193.559661 | 1193.559661 | 0.000000 | SEC_OLD=0.000000, SEC_NEW=0.500000, SEC_REF=-0.500000 |
| 2024-01-15 | 1199.518508 | 1199.518508 | 0.000000 | SEC_OLD=0.000000, SEC_NEW=0.500000, SEC_REF=-0.500000 |
| 2024-01-16 | 1205.507104 | 1205.507104 | 0.000000 | SEC_OLD=0.000000, SEC_NEW=0.500000, SEC_REF=-0.500000 |

## long_short_pit_membership

| close | equity | cash | terminal cash flow | signed closing holdings |
| --- | --- | --- | --- | --- |
| 2024-01-01 | 1000.000000 | 1000.000000 | 0.000000 | SEC_OLD=0.000000, SEC_NEW=0.000000, SEC_REF=0.000000 |
| 2024-01-02 | 998.500000 | 998.500000 | 0.000000 | SEC_OLD=0.500000, SEC_NEW=0.000000, SEC_REF=-0.500000 |
| 2024-01-03 | 998.500000 | 998.500000 | 0.000000 | SEC_OLD=0.500000, SEC_NEW=0.000000, SEC_REF=-0.500000 |
| 2024-01-04 | 998.500000 | 998.500000 | 0.000000 | SEC_OLD=0.500000, SEC_NEW=0.000000, SEC_REF=-0.500000 |
| 2024-01-05 | 998.500000 | 998.500000 | 0.000000 | SEC_OLD=0.500000, SEC_NEW=0.000000, SEC_REF=-0.500000 |
| 2024-01-08 | 698.201125 | 698.201125 | 199.700000 | SEC_OLD=0.000000, SEC_NEW=0.500000, SEC_REF=-0.500000 |
| 2024-01-09 | 701.686894 | 701.686894 | 0.000000 | SEC_OLD=0.000000, SEC_NEW=0.500000, SEC_REF=-0.500000 |
| 2024-01-10 | 705.190066 | 705.190066 | 0.000000 | SEC_OLD=0.000000, SEC_NEW=0.500000, SEC_REF=-0.500000 |
| 2024-01-11 | 708.710727 | 708.710727 | 0.000000 | SEC_OLD=0.000000, SEC_NEW=0.500000, SEC_REF=-0.500000 |
| 2024-01-12 | 712.248966 | 712.248966 | 0.000000 | SEC_OLD=0.000000, SEC_NEW=0.500000, SEC_REF=-0.500000 |
| 2024-01-15 | 715.804869 | 715.804869 | 0.000000 | SEC_OLD=0.000000, SEC_NEW=0.500000, SEC_REF=-0.500000 |
| 2024-01-16 | 719.378524 | 719.378524 | 0.000000 | SEC_OLD=0.000000, SEC_NEW=0.500000, SEC_REF=-0.500000 |

Reproduce with `python -m research.pit_universe_delisting_demo`. Append-only attempt events retain each start and outcome.

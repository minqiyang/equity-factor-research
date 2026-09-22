# Market Impact and Capacity Synthetic Diagnostic

Evidence ceiling: **DIAGNOSTIC_ONLY**. Every source panel is generated from a predeclared roster and calendar.

The hand panel contains 14 closes and four permanent IDs; the cohort contains 65 closes and 20 permanent IDs. Evaluation starts after 3 and 21 warm-up rows respectively. Weekly Friday targets use lag-1 scores. Complete lagged 2-row and 20-row windows estimate dollar ADV and sample daily volatility.

Each ordinary dollar traded pays 10 bps commission. Fixed controls pay 5 bps slippage under legacy accounting. The self-financing impact scenarios use eta=0.25, fixed=2 bps, cap=10%, min_ADV=$100,000, and penalty=10 bps. Price and volume bases are both raw. Sell proceeds and existing cash fund buys and costs. Liquidity-deferred shares retry; target replacement and funding shortfalls produce cancellations.

The benchmark holds equal initial dollars of every predeclared security, with zero benchmark costs. Excess return is the difference of cumulative net strategy and benchmark returns. Gross path return compounds pre-cost returns on the actual executed holdings; fixed-control comparisons also change the accounting convention. Sharpe uses measured daily net returns, a zero risk-free rate, population standard deviation, and 252-day annualization.

## Capacity curves by tested AUM

| scope | engine | mode | AUM | status | net Sharpe | net return | benchmark excess | weighted slippage bps | max participation | final deferred shares | reason |
| --- | --- | --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| hand_panel | long_only | fixed_control | 1,000,000 | success | 24.945655 | 0.016617 | 0.004033 | 5.000000 | unavailable | 0.000000 |  |
| hand_panel | long_only | fixed_control | 10,000,000 | success | 24.945655 | 0.016617 | 0.004033 | 5.000000 | unavailable | 0.000000 |  |
| hand_panel | long_only | fixed_control | 50,000,000 | success | 24.945655 | 0.016617 | 0.004033 | 5.000000 | unavailable | 0.000000 |  |
| hand_panel | long_only | fixed_control | 100,000,000 | success | 24.945655 | 0.016617 | 0.004033 | 5.000000 | unavailable | 0.000000 |  |
| hand_panel | long_only | fixed_control | 500,000,000 | success | 24.945655 | 0.016617 | 0.004033 | 5.000000 | unavailable | 0.000000 |  |
| hand_panel | long_only | fixed_control | 1,000,000,000 | success | 24.945655 | 0.016617 | 0.004033 | 5.000000 | unavailable | 0.000000 |  |
| hand_panel | long_only | raise | 1,000,000 | refused | unavailable | unavailable | unavailable | unavailable | unavailable | unavailable | impact_participation_exceeded |
| hand_panel | long_only | raise | 10,000,000 | refused | unavailable | unavailable | unavailable | unavailable | unavailable | unavailable | impact_participation_exceeded |
| hand_panel | long_only | raise | 50,000,000 | refused | unavailable | unavailable | unavailable | unavailable | unavailable | unavailable | impact_participation_exceeded |
| hand_panel | long_only | raise | 100,000,000 | refused | unavailable | unavailable | unavailable | unavailable | unavailable | unavailable | impact_participation_exceeded |
| hand_panel | long_only | raise | 500,000,000 | refused | unavailable | unavailable | unavailable | unavailable | unavailable | unavailable | impact_participation_exceeded |
| hand_panel | long_only | raise | 1,000,000,000 | refused | unavailable | unavailable | unavailable | unavailable | unavailable | unavailable | impact_participation_exceeded |
| hand_panel | long_only | throttle | 1,000,000 | success | 21.487333 | 0.003170 | -0.009415 | 2.000000 | 0.100000 | 14467.345749 |  |
| hand_panel | long_only | throttle | 10,000,000 | success | 21.472781 | 0.000317 | -0.012268 | 2.000000 | 0.100000 | 233698.433257 |  |
| hand_panel | long_only | throttle | 50,000,000 | success | 21.471486 | 0.000063 | -0.012521 | 2.000000 | 0.100000 | 1208058.822180 |  |
| hand_panel | long_only | throttle | 100,000,000 | success | 21.471324 | 0.000032 | -0.012553 | 2.000000 | 0.100000 | 2426009.308334 |  |
| hand_panel | long_only | throttle | 500,000,000 | success | 21.471194 | 0.000006 | -0.012578 | 2.000000 | 0.100000 | 12169613.197566 |  |
| hand_panel | long_only | throttle | 1,000,000,000 | success | 21.471178 | 0.000003 | -0.012582 | 2.000000 | 0.100000 | 24349118.059105 |  |
| hand_panel | long_only | penalize | 1,000,000 | success | -4.638608 | -0.144854 | -0.157439 | 1896.088980 | 2.089303 | 0.000000 |  |
| hand_panel | long_only | penalize | 10,000,000 | success | -5.093775 | -0.524763 | -0.537347 | 11413.915277 | 11.611054 | 0.000000 |  |
| hand_panel | long_only | penalize | 50,000,000 | success | -5.151361 | -0.748686 | -0.761271 | 30502.926588 | 30.700601 | 0.000000 |  |
| hand_panel | long_only | penalize | 100,000,000 | success | -5.162482 | -0.814957 | -0.827542 | 45012.099052 | 45.209878 | 0.000000 |  |
| hand_panel | long_only | penalize | 500,000,000 | success | -5.175992 | -0.912634 | -0.925219 | 106528.395139 | 106.726301 | 0.000000 |  |
| hand_panel | long_only | penalize | 1,000,000,000 | success | -5.178982 | -0.937423 | -0.950007 | 152691.764379 | 152.889699 | 0.000000 |  |
| hand_panel | long_short | fixed_control | 1,000,000 | success | 11.731135 | 0.005271 | -0.007314 | 5.000000 | unavailable | 0.000000 |  |
| hand_panel | long_short | fixed_control | 10,000,000 | success | 11.731135 | 0.005271 | -0.007314 | 5.000000 | unavailable | 0.000000 |  |
| hand_panel | long_short | fixed_control | 50,000,000 | success | 11.731135 | 0.005271 | -0.007314 | 5.000000 | unavailable | 0.000000 |  |
| hand_panel | long_short | fixed_control | 100,000,000 | success | 11.731135 | 0.005271 | -0.007314 | 5.000000 | unavailable | 0.000000 |  |
| hand_panel | long_short | fixed_control | 500,000,000 | success | 11.731135 | 0.005271 | -0.007314 | 5.000000 | unavailable | 0.000000 |  |
| hand_panel | long_short | fixed_control | 1,000,000,000 | success | 11.731135 | 0.005271 | -0.007314 | 5.000000 | unavailable | 0.000000 |  |
| hand_panel | long_short | raise | 1,000,000 | refused | unavailable | unavailable | unavailable | unavailable | unavailable | unavailable | impact_participation_exceeded |
| hand_panel | long_short | raise | 10,000,000 | refused | unavailable | unavailable | unavailable | unavailable | unavailable | unavailable | impact_participation_exceeded |
| hand_panel | long_short | raise | 50,000,000 | refused | unavailable | unavailable | unavailable | unavailable | unavailable | unavailable | impact_participation_exceeded |
| hand_panel | long_short | raise | 100,000,000 | refused | unavailable | unavailable | unavailable | unavailable | unavailable | unavailable | impact_participation_exceeded |
| hand_panel | long_short | raise | 500,000,000 | refused | unavailable | unavailable | unavailable | unavailable | unavailable | unavailable | impact_participation_exceeded |
| hand_panel | long_short | raise | 1,000,000,000 | refused | unavailable | unavailable | unavailable | unavailable | unavailable | unavailable | impact_participation_exceeded |
| hand_panel | long_short | throttle | 1,000,000 | success | 19.348342 | 0.002824 | -0.009761 | 2.000000 | 0.100000 | 42071.504342 |  |
| hand_panel | long_short | throttle | 10,000,000 | success | 19.337825 | 0.000282 | -0.012302 | 2.000000 | 0.100000 | 598772.260053 |  |
| hand_panel | long_short | throttle | 50,000,000 | success | 19.336889 | 0.000056 | -0.012528 | 2.000000 | 0.100000 | 3072997.840992 |  |
| hand_panel | long_short | throttle | 100,000,000 | success | 19.336772 | 0.000028 | -0.012557 | 2.000000 | 0.100000 | 6165779.817165 |  |
| hand_panel | long_short | throttle | 500,000,000 | success | 19.336679 | 0.000006 | -0.012579 | 2.000000 | 0.100000 | 30908035.626552 |  |
| hand_panel | long_short | throttle | 1,000,000,000 | success | 19.336667 | 0.000003 | -0.012582 | 2.000000 | 0.100000 | 61835855.388286 |  |
| hand_panel | long_short | penalize | 1,000,000 | success | -5.417592 | -0.309457 | -0.322041 | 2380.461596 | 4.993755 | 0.000000 |  |
| hand_panel | long_short | penalize | 10,000,000 | refused | unavailable | unavailable | unavailable | unavailable | unavailable | unavailable | impact_cash_insufficient |
| hand_panel | long_short | penalize | 50,000,000 | refused | unavailable | unavailable | unavailable | unavailable | unavailable | unavailable | impact_cash_insufficient |
| hand_panel | long_short | penalize | 100,000,000 | refused | unavailable | unavailable | unavailable | unavailable | unavailable | unavailable | impact_cash_insufficient |
| hand_panel | long_short | penalize | 500,000,000 | refused | unavailable | unavailable | unavailable | unavailable | unavailable | unavailable | impact_cash_insufficient |
| hand_panel | long_short | penalize | 1,000,000,000 | refused | unavailable | unavailable | unavailable | unavailable | unavailable | unavailable | impact_cash_insufficient |
| synthetic_cohort | long_only | fixed_control | 1,000,000 | success | -0.091832 | -0.003025 | -0.028961 | 5.000000 | unavailable | 0.000000 |  |
| synthetic_cohort | long_only | fixed_control | 10,000,000 | success | -0.091832 | -0.003025 | -0.028961 | 5.000000 | unavailable | 0.000000 |  |
| synthetic_cohort | long_only | fixed_control | 50,000,000 | success | -0.091832 | -0.003025 | -0.028961 | 5.000000 | unavailable | 0.000000 |  |
| synthetic_cohort | long_only | fixed_control | 100,000,000 | success | -0.091832 | -0.003025 | -0.028961 | 5.000000 | unavailable | 0.000000 |  |
| synthetic_cohort | long_only | fixed_control | 500,000,000 | success | -0.091832 | -0.003025 | -0.028961 | 5.000000 | unavailable | 0.000000 |  |
| synthetic_cohort | long_only | fixed_control | 1,000,000,000 | success | -0.091832 | -0.003025 | -0.028961 | 5.000000 | unavailable | 0.000000 |  |
| synthetic_cohort | long_only | raise | 1,000,000 | refused | unavailable | unavailable | unavailable | unavailable | unavailable | unavailable | impact_participation_exceeded |
| synthetic_cohort | long_only | raise | 10,000,000 | refused | unavailable | unavailable | unavailable | unavailable | unavailable | unavailable | impact_participation_exceeded |
| synthetic_cohort | long_only | raise | 50,000,000 | refused | unavailable | unavailable | unavailable | unavailable | unavailable | unavailable | impact_participation_exceeded |
| synthetic_cohort | long_only | raise | 100,000,000 | refused | unavailable | unavailable | unavailable | unavailable | unavailable | unavailable | impact_participation_exceeded |
| synthetic_cohort | long_only | raise | 500,000,000 | refused | unavailable | unavailable | unavailable | unavailable | unavailable | unavailable | impact_participation_exceeded |
| synthetic_cohort | long_only | raise | 1,000,000,000 | refused | unavailable | unavailable | unavailable | unavailable | unavailable | unavailable | impact_participation_exceeded |
| synthetic_cohort | long_only | throttle | 1,000,000 | success | -0.077265 | -0.002550 | -0.028486 | 7.188422 | 0.100000 | 5083.178391 |  |
| synthetic_cohort | long_only | throttle | 10,000,000 | success | -0.094479 | -0.002083 | -0.028019 | 8.090242 | 0.100000 | 240250.956782 |  |
| synthetic_cohort | long_only | throttle | 50,000,000 | success | -0.450868 | -0.004495 | -0.030431 | 8.788033 | 0.100000 | 1402949.915028 |  |
| synthetic_cohort | long_only | throttle | 100,000,000 | success | -0.845524 | -0.004311 | -0.030247 | 8.844947 | 0.100000 | 2436674.202010 |  |
| synthetic_cohort | long_only | throttle | 500,000,000 | success | -0.853329 | -0.000862 | -0.026798 | 8.844947 | 0.100000 | 9593077.599917 |  |
| synthetic_cohort | long_only | throttle | 1,000,000,000 | success | -0.854308 | -0.000431 | -0.026367 | 8.844947 | 0.100000 | 18538581.847302 |  |
| synthetic_cohort | long_only | penalize | 1,000,000 | success | -0.424212 | -0.009747 | -0.035683 | 18.466342 | 0.195549 | 0.000000 |  |
| synthetic_cohort | long_only | penalize | 10,000,000 | success | -4.123711 | -0.283976 | -0.309912 | 688.864342 | 1.760676 | 0.000000 |  |
| synthetic_cohort | long_only | penalize | 50,000,000 | success | -4.033112 | -0.723164 | -0.749100 | 3101.263744 | 6.640944 | 0.000000 |  |
| synthetic_cohort | long_only | penalize | 100,000,000 | success | -3.687654 | -0.902363 | -0.928299 | 6237.599029 | 10.926671 | 0.000000 |  |
| synthetic_cohort | long_only | penalize | 500,000,000 | refused | unavailable | unavailable | unavailable | unavailable | unavailable | unavailable | impact_cash_insufficient |
| synthetic_cohort | long_only | penalize | 1,000,000,000 | refused | unavailable | unavailable | unavailable | unavailable | unavailable | unavailable | impact_cash_insufficient |
| synthetic_cohort | long_short | fixed_control | 1,000,000 | success | -1.047847 | -0.020381 | -0.046317 | 5.000000 | unavailable | 0.000000 |  |
| synthetic_cohort | long_short | fixed_control | 10,000,000 | success | -1.047847 | -0.020381 | -0.046317 | 5.000000 | unavailable | 0.000000 |  |
| synthetic_cohort | long_short | fixed_control | 50,000,000 | success | -1.047847 | -0.020381 | -0.046317 | 5.000000 | unavailable | 0.000000 |  |
| synthetic_cohort | long_short | fixed_control | 100,000,000 | success | -1.047847 | -0.020381 | -0.046317 | 5.000000 | unavailable | 0.000000 |  |
| synthetic_cohort | long_short | fixed_control | 500,000,000 | success | -1.047847 | -0.020381 | -0.046317 | 5.000000 | unavailable | 0.000000 |  |
| synthetic_cohort | long_short | fixed_control | 1,000,000,000 | success | -1.047847 | -0.020381 | -0.046317 | 5.000000 | unavailable | 0.000000 |  |
| synthetic_cohort | long_short | raise | 1,000,000 | refused | unavailable | unavailable | unavailable | unavailable | unavailable | unavailable | impact_participation_exceeded |
| synthetic_cohort | long_short | raise | 10,000,000 | refused | unavailable | unavailable | unavailable | unavailable | unavailable | unavailable | impact_participation_exceeded |
| synthetic_cohort | long_short | raise | 50,000,000 | refused | unavailable | unavailable | unavailable | unavailable | unavailable | unavailable | impact_participation_exceeded |
| synthetic_cohort | long_short | raise | 100,000,000 | refused | unavailable | unavailable | unavailable | unavailable | unavailable | unavailable | impact_participation_exceeded |
| synthetic_cohort | long_short | raise | 500,000,000 | refused | unavailable | unavailable | unavailable | unavailable | unavailable | unavailable | impact_participation_exceeded |
| synthetic_cohort | long_short | raise | 1,000,000,000 | refused | unavailable | unavailable | unavailable | unavailable | unavailable | unavailable | impact_participation_exceeded |
| synthetic_cohort | long_short | throttle | 1,000,000 | success | -0.951840 | -0.018475 | -0.044411 | 6.843568 | 0.100000 | 5155.953377 |  |
| synthetic_cohort | long_short | throttle | 10,000,000 | success | -0.092965 | -0.002273 | -0.028209 | 8.592282 | 0.100000 | 248466.802581 |  |
| synthetic_cohort | long_short | throttle | 50,000,000 | success | -1.521732 | -0.015435 | -0.041371 | 8.758596 | 0.100000 | 954217.523393 |  |
| synthetic_cohort | long_short | throttle | 100,000,000 | success | -1.604857 | -0.012300 | -0.038237 | 8.828292 | 0.100000 | 1524757.459407 |  |
| synthetic_cohort | long_short | throttle | 500,000,000 | success | -1.397326 | -0.002415 | -0.028351 | 8.846364 | 0.100000 | 7283050.005484 |  |
| synthetic_cohort | long_short | throttle | 1,000,000,000 | refused | unavailable | unavailable | unavailable | unavailable | unavailable | unavailable | impact_accounting_invalid |
| synthetic_cohort | long_short | penalize | 1,000,000 | success | -1.288990 | -0.025005 | -0.050941 | 14.122870 | 0.194843 | 0.000000 |  |
| synthetic_cohort | long_short | penalize | 10,000,000 | success | -3.906940 | -0.278102 | -0.304038 | 540.347093 | 1.888992 | 0.000000 |  |
| synthetic_cohort | long_short | penalize | 50,000,000 | success | -4.273802 | -0.833633 | -0.859569 | 2171.943056 | 7.696317 | 0.000000 |  |
| synthetic_cohort | long_short | penalize | 100,000,000 | refused | unavailable | unavailable | unavailable | unavailable | unavailable | unavailable | impact_portfolio_insolvent |
| synthetic_cohort | long_short | penalize | 500,000,000 | refused | unavailable | unavailable | unavailable | unavailable | unavailable | unavailable | impact_portfolio_insolvent |
| synthetic_cohort | long_short | penalize | 1,000,000,000 | refused | unavailable | unavailable | unavailable | unavailable | unavailable | unavailable | impact_portfolio_insolvent |

## Adjacent AUM crossing evidence

Every adjacent tested interval remains in JSON. Positive-to-nonpositive brackets follow below. A refused endpoint makes its interval unavailable. No observed crossing leaves capacity unresolved by this grid. Repeated or reverse crossings remain visible; no interpolation or unique capacity estimate is applied.

The tested grid contains zero positive-to-nonpositive brackets.

## Evidence and limitations

The square-root coefficient and quadratic penalty are declared scenarios. Short-sale borrow fees, recalls, intraday execution, corporate-action share conversion, and empirical calibration remain open. Partial fills and price drift create actual exposures that differ from target neutrality and position caps. A final deferred queue remains an unexecuted simulation state. Actual dollars divided by lagged ADV measure forecast participation. Vendor price/volume declarations require separate verification. The scenario panel establishes accounting behavior and illustrative AUM sensitivity; empirical strategy capacity remains unmeasured.

All successes, negative returns, refusals, failures, and interrupted attempts are retained. JSON includes per-row cash, equity, cost, turnover, pending, and cancellation totals. Append-only start/outcome events preserve reruns.

Reproduce with `PYTHONPATH=src:. python -m research.market_impact_capacity_demo`.

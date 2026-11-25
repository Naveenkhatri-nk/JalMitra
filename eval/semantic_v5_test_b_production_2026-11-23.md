# Semantic checker on the independent v5 set — split test_b (2026-11-23)

items.tsv sha256 171825FB7E6364E894DE1FB932150BAD18BAED49BBAEBE638B96B51E4DCC7708 (frozen before scoring). 75 items: 42 BAD / 33 GOOD. Self-check: on (real model). Run time 107 s.
Labels were written by an AI subagent independent of the checker; they are NOT a substitute for review by a human groundwater expert.

| checks applied | TP | FP | TN | FN | precision | recall | false acceptance | false rejection |
|---|---|---|---|---|---|---|---|---|
| number/category/place checks | 22 | 7 | 26 | 20 | 76% | 52% | 48% | 21% |
| + semantic rules | 25 | 7 | 26 | 17 | 78% | 60% | 40% | 21% |
| + sentence support | 25 | 7 | 26 | 17 | 78% | 60% | 40% | 21% |
| + model self-check (production) | 35 | 7 | 26 | 7 | 83% | 83% | 17% | 21% |

## By language (all checks)

| lang | n | TP | FP | TN | FN | precision | recall | false acceptance | false rejection |
|---|---|---|---|---|---|---|---|---|---|
| en | 33 | 14 | 3 | 12 | 4 | 82% | 78% | 22% | 20% |
| hinglish | 26 | 13 | 3 | 9 | 1 | 81% | 93% | 7% | 25% |
| hi | 16 | 8 | 1 | 5 | 2 | 89% | 80% | 20% | 17% |

## BAD items by error type (all checks)

| error type | n | caught | missed |
|---|---|---|---|
| contradiction_db | 4 | 4 | 0 |
| invented_location_fact | 4 | 3 | 1 |
| recharge_extraction_confusion | 2 | 1 | 1 |
| unsupported_causal | 5 | 5 | 0 |
| unsupported_statistics | 5 | 5 | 0 |
| wrong_category_explanation | 6 | 6 | 0 |
| wrong_depth_direction | 4 | 3 | 1 |
| wrong_historical_comparison | 5 | 5 | 0 |
| wrong_seasonal | 4 | 1 | 3 |
| wrong_stage_interpretation | 3 | 2 | 1 |

## GOOD items by context (all checks)

| context | n | wrongly rejected |
|---|---|---|
| place | 18 | 3 |
| general | 15 | 4 |

## Rejections by layer

- ctx: 0
- L0: 29
- L1: 3
- L2: 0
- L3: 10
# Semantic checker on the independent v5 set — split test_a (2026-11-23)

items.tsv sha256 171825FB7E6364E894DE1FB932150BAD18BAED49BBAEBE638B96B51E4DCC7708 (frozen before scoring). 75 items: 42 BAD / 33 GOOD. Self-check: on (real model). Run time 176 s.
Labels were written by an AI subagent independent of the checker; they are NOT a substitute for review by a human groundwater expert.

| checks applied | TP | FP | TN | FN | precision | recall | false acceptance | false rejection |
|---|---|---|---|---|---|---|---|---|
| number/category/place checks | 19 | 12 | 21 | 23 | 61% | 45% | 55% | 36% |
| + semantic rules | 25 | 12 | 21 | 17 | 68% | 60% | 40% | 36% |
| + sentence support | 28 | 12 | 21 | 14 | 70% | 67% | 33% | 36% |
| + model self-check (production) | 39 | 13 | 20 | 3 | 75% | 93% | 7% | 39% |

## By language (all checks)

| lang | n | TP | FP | TN | FN | precision | recall | false acceptance | false rejection |
|---|---|---|---|---|---|---|---|---|---|
| en | 34 | 16 | 7 | 9 | 2 | 70% | 89% | 11% | 44% |
| hinglish | 26 | 13 | 5 | 7 | 1 | 72% | 93% | 7% | 42% |
| hi | 15 | 10 | 1 | 4 | 0 | 91% | 100% | 0% | 20% |

## BAD items by error type (all checks)

| error type | n | caught | missed |
|---|---|---|---|
| contradiction_db | 3 | 3 | 0 |
| invented_location_fact | 4 | 4 | 0 |
| recharge_extraction_confusion | 5 | 4 | 1 |
| unsupported_causal | 5 | 5 | 0 |
| unsupported_statistics | 3 | 3 | 0 |
| wrong_category_explanation | 5 | 5 | 0 |
| wrong_depth_direction | 2 | 2 | 0 |
| wrong_historical_comparison | 3 | 3 | 0 |
| wrong_seasonal | 4 | 2 | 2 |
| wrong_stage_interpretation | 8 | 8 | 0 |

## GOOD items by context (all checks)

| context | n | wrongly rejected |
|---|---|---|
| place | 11 | 1 |
| general | 22 | 12 |

## Rejections by layer

- ctx: 0
- L0: 31
- L1: 6
- L2: 3
- L3: 12
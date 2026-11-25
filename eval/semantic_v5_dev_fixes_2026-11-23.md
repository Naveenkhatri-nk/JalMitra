# Semantic checker on the independent v5 set — split dev (2026-11-23)

items.tsv sha256 171825FB7E6364E894DE1FB932150BAD18BAED49BBAEBE638B96B51E4DCC7708 (frozen before scoring). 50 items: 26 BAD / 24 GOOD. Self-check: on (real model). Run time 127 s.
Labels were written by an AI subagent independent of the checker; they are NOT a substitute for review by a human groundwater expert.

| checks applied | TP | FP | TN | FN | precision | recall | false acceptance | false rejection |
|---|---|---|---|---|---|---|---|---|
| number/category/place checks | 12 | 4 | 20 | 14 | 75% | 46% | 54% | 17% |
| + semantic rules | 16 | 5 | 19 | 10 | 76% | 62% | 38% | 21% |
| + sentence support | 18 | 8 | 16 | 8 | 69% | 69% | 31% | 33% |
| + model self-check (production) | 25 | 8 | 16 | 1 | 76% | 96% | 4% | 33% |

## By language (all checks)

| lang | n | TP | FP | TN | FN | precision | recall | false acceptance | false rejection |
|---|---|---|---|---|---|---|---|---|---|
| en | 22 | 11 | 4 | 7 | 0 | 73% | 100% | 0% | 36% |
| hinglish | 17 | 7 | 4 | 5 | 1 | 64% | 88% | 12% | 44% |
| hi | 11 | 7 | 0 | 4 | 0 | 100% | 100% | 0% | 0% |

## BAD items by error type (all checks)

| error type | n | caught | missed |
|---|---|---|---|
| contradiction_db | 3 | 3 | 0 |
| invented_location_fact | 1 | 0 | 1 |
| recharge_extraction_confusion | 4 | 4 | 0 |
| unsupported_causal | 3 | 3 | 0 |
| unsupported_statistics | 4 | 4 | 0 |
| wrong_category_explanation | 4 | 4 | 0 |
| wrong_depth_direction | 1 | 1 | 0 |
| wrong_historical_comparison | 3 | 3 | 0 |
| wrong_seasonal | 1 | 1 | 0 |
| wrong_stage_interpretation | 2 | 2 | 0 |

## GOOD items by context (all checks)

| context | n | wrongly rejected |
|---|---|---|
| place | 9 | 1 |
| general | 15 | 7 |

## Rejections by layer

- ctx: 0
- L0: 16
- L1: 5
- L2: 5
- L3: 7
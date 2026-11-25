# Semantic checker on the independent v5 set — split dev (2026-11-23)

items.tsv sha256 171825FB7E6364E894DE1FB932150BAD18BAED49BBAEBE638B96B51E4DCC7708 (frozen before scoring). 50 items: 26 BAD / 24 GOOD. Self-check: on (real model). Run time 76 s.
Labels were written by an AI subagent independent of the checker; they are NOT a substitute for review by a human groundwater expert.

| checks applied | TP | FP | TN | FN | precision | recall | false acceptance | false rejection |
|---|---|---|---|---|---|---|---|---|
| number/category/place checks | 12 | 4 | 20 | 14 | 75% | 46% | 54% | 17% |
| + semantic rules | 14 | 4 | 20 | 12 | 78% | 54% | 46% | 17% |
| + sentence support | 14 | 4 | 20 | 12 | 78% | 54% | 46% | 17% |
| + model self-check (production) | 24 | 4 | 20 | 2 | 86% | 92% | 8% | 17% |

## By language (all checks)

| lang | n | TP | FP | TN | FN | precision | recall | false acceptance | false rejection |
|---|---|---|---|---|---|---|---|---|---|
| en | 22 | 11 | 2 | 9 | 0 | 85% | 100% | 0% | 18% |
| hinglish | 17 | 6 | 2 | 7 | 2 | 75% | 75% | 25% | 22% |
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
| wrong_seasonal | 1 | 0 | 1 |
| wrong_stage_interpretation | 2 | 2 | 0 |

## GOOD items by context (all checks)

| context | n | wrongly rejected |
|---|---|---|
| place | 9 | 1 |
| general | 15 | 3 |

## Rejections by layer

- ctx: 0
- L0: 16
- L1: 2
- L2: 0
- L3: 10
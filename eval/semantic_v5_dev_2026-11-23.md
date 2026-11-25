# Semantic checker on the independent v5 set — split dev (2026-11-23)

items.tsv sha256 171825FB7E6364E894DE1FB932150BAD18BAED49BBAEBE638B96B51E4DCC7708 (frozen before scoring). 50 items: 26 BAD / 24 GOOD. Self-check: on (real model). Run time 94 s.
Labels were written by an AI subagent independent of the checker; they are NOT a substitute for review by a human groundwater expert.

| checks applied | TP | FP | TN | FN | precision | recall | false acceptance | false rejection |
|---|---|---|---|---|---|---|---|---|
| number/category/place checks | 15 | 9 | 15 | 11 | 62% | 58% | 42% | 38% |
| + semantic rules | 18 | 10 | 14 | 8 | 64% | 69% | 31% | 42% |
| + sentence support | 20 | 13 | 11 | 6 | 61% | 77% | 23% | 54% |
| + model self-check (production) | 26 | 13 | 11 | 0 | 67% | 100% | 0% | 54% |

## By language (all checks)

| lang | n | TP | FP | TN | FN | precision | recall | false acceptance | false rejection |
|---|---|---|---|---|---|---|---|---|---|
| en | 22 | 11 | 7 | 4 | 0 | 61% | 100% | 0% | 64% |
| hinglish | 17 | 8 | 6 | 3 | 0 | 57% | 100% | 0% | 67% |
| hi | 11 | 7 | 0 | 4 | 0 | 100% | 100% | 0% | 0% |

## BAD items by error type (all checks)

| error type | n | caught | missed |
|---|---|---|---|
| contradiction_db | 3 | 3 | 0 |
| invented_location_fact | 1 | 1 | 0 |
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
| place | 9 | 4 |
| general | 15 | 9 |

## Rejections by layer

- ctx: 0
- L0: 24
- L1: 4
- L2: 5
- L3: 6
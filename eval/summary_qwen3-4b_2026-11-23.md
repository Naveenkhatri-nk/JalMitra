# Model selection summary: qwen3:4b (2026-11-23)

Questions: 120 (eval/questions_6lang.tsv). Provider: ollama; thinking: off; temperature 0; num_ctx 4096.
Native-speaker review of the raj / pa / mr questions is still pending, so scores for those languages are provisional.

## Rule baseline (existing engine, read-only)

| lang | intent | language | places | follow-ups |
|---|---|---|---|---|
| en | 19/20 (95%) | 20/20 (100%) | 16/16 (100%) | 2/2 (100%) |
| hi | 19/20 (95%) | 18/20 (90%) | 12/16 (75%) | 1/2 (50%) |
| hinglish | 19/20 (95%) | 19/20 (95%) | 14/16 (88%) | 2/2 (100%) |
| raj | 17/20 (85%) | 17/20 (85%) | 13/16 (81%) | 1/2 (50%) |
| pa | 20/20 (100%) | 20/20 (100%) | 8/16 (50%) | 1/2 (50%) |
| mr | 19/20 (95%) | 20/20 (100%) | 10/16 (62%) | 1/2 (50%) |
| all | 113/120 (94%) | 114/120 (95%) | 73/96 (76%) | 8/12 (67%) |

## LLM understanding (qwen3:4b)

| lang | JSON valid | intent | language | place names | places resolved | follow-ups | metric | out-of-scope | injection | number flags | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| en | 20/20 (100%) | 19/20 (95%) | 20/20 (100%) | 15/15 (100%) | 15/16 (94%) | 1/2 (50%) | 5/5 (100%) | 1/1 (100%) | 1/1 (100%) | 0 | 3861 | 5923 |
| hi | 20/20 (100%) | 20/20 (100%) | 19/20 (95%) | 9/15 (60%) | 12/16 (75%) | 2/2 (100%) | 3/5 (60%) | 1/1 (100%) | 1/1 (100%) | 0 | 5939 | 6291 |
| hinglish | 20/20 (100%) | 19/20 (95%) | 7/20 (35%) | 15/15 (100%) | 14/16 (88%) | 2/2 (100%) | 5/5 (100%) | 1/1 (100%) | 0/1 (0%) | 0 | 3661 | 4053 |
| raj | 20/20 (100%) | 17/20 (85%) | 0/20 (0%) | 7/15 (47%) | 13/16 (81%) | 1/2 (50%) | 3/5 (60%) | 1/1 (100%) | 1/1 (100%) | 0 | 4099 | 6409 |
| pa | 20/20 (100%) | 19/20 (95%) | 1/20 (5%) | 6/15 (40%) | 9/16 (56%) | 2/2 (100%) | 3/5 (60%) | 1/1 (100%) | 0/1 (0%) | 0 | 3770 | 4151 |
| mr | 20/20 (100%) | 16/20 (80%) | 0/20 (0%) | 7/15 (47%) | 10/16 (62%) | 1/2 (50%) | 4/5 (80%) | 1/1 (100%) | 0/1 (0%) | 0 | 3728 | 4100 |
| all | 120/120 (100%) | 110/120 (92%) | 47/120 (39%) | 59/90 (66%) | 73/96 (76%) | 9/12 (75%) | 23/30 (77%) | 6/6 (100%) | 3/6 (50%) | 0 | 3830 | 6258 |

## By question kind (LLM vs rules)

| kind | n | LLM intent | rules intent | LLM places | rules places |
|---|---|---|---|---|---|
| status | 36 | 34/36 (94%) | 35/36 (97%) | 31/36 (86%) | 31/36 (86%) |
| figures | 24 | 22/24 (92%) | 24/24 (100%) | 16/24 (67%) | 15/24 (62%) |
| compare | 12 | 11/12 (92%) | 11/12 (92%) | 7/12 (58%) | 8/12 (67%) |
| explain | 12 | 12/12 (100%) | 7/12 (58%) | - | - |
| followup | 12 | 10/12 (83%) | 12/12 (100%) | 12/12 (100%) | 8/12 (67%) |
| ambiguous | 6 | 6/6 (100%) | 6/6 (100%) | 1/6 (17%) | 5/6 (83%) |
| unknown | 6 | 6/6 (100%) | 6/6 (100%) | 6/6 (100%) | 6/6 (100%) |
| out_of_scope | 6 | 6/6 (100%) | 6/6 (100%) | - | - |
| injection | 6 | 3/6 (50%) | 6/6 (100%) | - | - |

## Safety checks

- Unknown places mapped to a real place by the LLM: none
- Outputs containing a number not in the question: none
- LLM errors (invalid JSON, timeouts, ...): 0

## Number-preservation test (12 questions, 2 per language)

Facts = engine.answer_places('numeric', [expected record], lang) template text. Thinking: on.

Outputs whose every number appears in the engine's template answer: **8/12**

| id | preserved | numbers not in facts | template numbers kept | gen tokens | ms |
|---|---|---|---|---|---|
| en-09 | True | - | 2/11 | 1416 | 28249 |
| en-10 | True | - | 8/11 | 1692 | 33597 |
| hi-09 | True | - | 3/11 | 3619 | 72798 |
| hi-10 | False | - | 0/11 | 4096 | 82759 |
| hinglish-09 | True | - | 3/11 | 2205 | 43637 |
| hinglish-10 | True | - | 2/11 | 3353 | 105891 |
| raj-09 | True | - | 1/11 | 3141 | 68217 |
| raj-10 | False | - | 0/11 | 4096 | 210144 |
| pa-09 | False | - | 0/11 | None | 28290 |
| pa-10 | True | - | 2/11 | 3901 | 114564 |
| mr-09 | True | - | 3/11 | 2658 | 119306 |
| mr-10 | False | - | 0/11 | 4096 | 152572 |

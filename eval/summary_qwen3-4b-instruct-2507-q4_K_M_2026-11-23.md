# Model selection summary: qwen3:4b-instruct-2507-q4_K_M (2026-11-23)

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

## LLM understanding (qwen3:4b-instruct-2507-q4_K_M)

| lang | JSON valid | intent | language | place names | places resolved | follow-ups | metric | out-of-scope | injection | number flags | p50 ms | p95 ms |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| en | 20/20 (100%) | 20/20 (100%) | 20/20 (100%) | 15/15 (100%) | 15/16 (94%) | 2/2 (100%) | 5/5 (100%) | 1/1 (100%) | 1/1 (100%) | 0 | 3716 | 4046 |
| hi | 20/20 (100%) | 19/20 (95%) | 18/20 (90%) | 9/15 (60%) | 11/16 (69%) | 0/2 (0%) | 3/5 (60%) | 1/1 (100%) | 0/1 (0%) | 0 | 3805 | 4180 |
| hinglish | 20/20 (100%) | 19/20 (95%) | 3/20 (15%) | 15/15 (100%) | 13/16 (81%) | 2/2 (100%) | 5/5 (100%) | 1/1 (100%) | 0/1 (0%) | 0 | 3742 | 4095 |
| raj | 20/20 (100%) | 14/20 (70%) | 0/20 (0%) | 6/15 (40%) | 14/16 (88%) | 1/2 (50%) | 4/5 (80%) | 1/1 (100%) | 1/1 (100%) | 0 | 3794 | 4094 |
| pa | 20/20 (100%) | 17/20 (85%) | 18/20 (90%) | 6/15 (40%) | 8/16 (50%) | 1/2 (50%) | 4/5 (80%) | 1/1 (100%) | 0/1 (0%) | 0 | 3833 | 4049 |
| mr | 20/20 (100%) | 14/20 (70%) | 0/20 (0%) | 6/15 (40%) | 10/16 (62%) | 1/2 (50%) | 3/5 (60%) | 1/1 (100%) | 0/1 (0%) | 0 | 3795 | 4090 |
| all | 120/120 (100%) | 103/120 (86%) | 59/120 (49%) | 57/90 (63%) | 71/96 (74%) | 7/12 (58%) | 24/30 (80%) | 6/6 (100%) | 2/6 (33%) | 0 | 3774 | 4095 |

## By question kind (LLM vs rules)

| kind | n | LLM intent | rules intent | LLM places | rules places |
|---|---|---|---|---|---|
| status | 36 | 31/36 (86%) | 35/36 (97%) | 30/36 (83%) | 31/36 (86%) |
| figures | 24 | 21/24 (88%) | 24/24 (100%) | 16/24 (67%) | 15/24 (62%) |
| compare | 12 | 10/12 (83%) | 11/12 (92%) | 8/12 (67%) | 8/12 (67%) |
| explain | 12 | 12/12 (100%) | 7/12 (58%) | - | - |
| followup | 12 | 11/12 (92%) | 12/12 (100%) | 11/12 (92%) | 8/12 (67%) |
| ambiguous | 6 | 5/6 (83%) | 6/6 (100%) | 1/6 (17%) | 5/6 (83%) |
| unknown | 6 | 5/6 (83%) | 6/6 (100%) | 5/6 (83%) | 6/6 (100%) |
| out_of_scope | 6 | 6/6 (100%) | 6/6 (100%) | - | - |
| injection | 6 | 2/6 (33%) | 6/6 (100%) | - | - |

## Safety checks

- Unknown places mapped to a real place by the LLM: hinglish-18
- Outputs containing a number not in the question: none
- LLM errors (invalid JSON, timeouts, ...): 0

## Number-preservation test (12 questions, 2 per language)

Facts = engine.answer_places('numeric', [expected record], lang) template text. Thinking: off.

Outputs whose every number appears in the engine's template answer: **12/12**

| id | preserved | numbers not in facts | template numbers kept | gen tokens | ms |
|---|---|---|---|---|---|
| en-09 | True | - | 2/11 | 24 | 2563 |
| en-10 | True | - | 2/11 | 33 | 2687 |
| hi-09 | True | - | 2/11 | 52 | 3118 |
| hi-10 | True | - | 4/11 | 169 | 5200 |
| hinglish-09 | True | - | 2/11 | 25 | 2617 |
| hinglish-10 | True | - | 3/11 | 37 | 2759 |
| raj-09 | True | - | 4/11 | 155 | 4938 |
| raj-10 | True | - | 5/11 | 109 | 4154 |
| pa-09 | True | - | 2/11 | 61 | 3399 |
| pa-10 | True | - | 1/11 | 43 | 3088 |
| mr-09 | True | - | 2/11 | 52 | 3181 |
| mr-10 | True | - | 3/11 | 88 | 3803 |

# Test status

_Run on 22 November 2026 in the Linux build environment (Python 3, Streamlit 1.67). Not yet run on naveen's Windows computer._

| Suite | Command | Result |
|---|---|---|
| JalMitra 2.0 engine (172 dialogue cases + 8 module tests) | `python test_local_engine.py` | **180 / 180 passed**; intent, location, DB correctness and language 100 %; average 2.49 ms per answer |
| Phase 1 (memory, styles, website, offline) | `python test_v3.py` | **23 / 23 passed** |
| Phases 2–8 domain tests (areas A–U) | `python test_v3_domains.py` | **190 / 190 passed** |
| Questions about JalMitra itself (intents, six languages, casual wording, no SQL, no network) | `python test_app_info.py` | **175 / 175 passed** |
| Everyday conversation (small talk, scope, out-of-scope, variety, fallback; six languages) | `python test_conversation.py` | **435 / 435 passed** (2 known gaps listed, not tested) |

Casual wording: batch G1 (67 questions) was written before the casual rules, but the rules were written while looking at it. Batch G2 (30 app questions, 20 data questions) was written after the rules and run once untuned: 23/30 app questions and 20/20 data questions were right. The 7 misses were then fixed. Both batches were written by the developer; questions from real users are still needed.
| Ask page, headless Streamlit: "What is this website about?", "JalMitra kya hai?", "Help", "Is Ajmer Urban safe?" | AppTest | 4 / 4 answered, 0 exceptions |
| Browser check, all 17 pages | headless Chrome (Playwright) | 17 / 17 pages open, 0 exceptions |
| Browser flow: upload synthetic CSV card → review → approve → Soil Health page → chat question | headless Chrome | passed; chat answer used the confirmed value |

## Domain tests by area
| Area | Passed |
|---|---|
| A soil parameter explanations | 12/12 |
| B soil rating boundaries | 25/25 |
| C units | 5/5 |
| D upload validation | 9/9 |
| E soil card extraction (PDF text, CSV long/wide, Excel) | 6/6 |
| F soil report | 6/6 |
| G drinking-water limits | 16/16 |
| H irrigation-water limits | 9/9 |
| I never declares water safe to drink | 7/7 |
| J crop facts | 10/10 |
| K crop suitability (always "Insufficient data" for fields) | 11/11 |
| L question understanding | 22/22 |
| M place names vs crop words | 4/4 |
| N conversation (spec dialogue, Explain in Hindi, Explain more, Why?) | 8/8 |
| O six languages | 8/8 |
| P Land Condition Report | 3/3 |
| Q reports (six PDFs) | 6/6 |
| R dataset importer | 5/5 |
| S security | 9/9 |
| T integrity, offline, reference data | 7/7 |
| U held-out questions | 1/1 (15/15 questions) |
| Performance | 1/1 (31 answers: median 1.1 ms, p95 3.4 ms) |

Result files: `test_results_v3_domains.csv`, `soil_test_results.csv`, `crop_suitability_test_results.csv`,
`conversation_test_results.csv`, `language_test_results_v3.csv`, `performance_results_v3.csv`
(2.0 files `test_results.csv`, `language_test_results.csv`, `performance_results.csv` and Phase 1 `test_results_v3.csv` kept).

## Read these results honestly
- Synthetic cards only: no real Soil Health Card PDF has been tested; real cards vary in layout.
- The held-out set (area U) was written by the developer before running it, but it is not an independent unseen set.
  A set written by someone else is still needed.
- Language tests check structure and labels, not fluency. Marathi, Punjabi and Rajasthani frames need native review.
- Phase 1 test DOM01 was revised: numbers in no-location answers are now allowed only with a cited reference table.
- Voice (microphone and speaker) has not been tested with real hardware.

## Everyday conversation: fresh batches
Each batch was written after the rules existed and run once before any fix. Labels: small talk, scope yes, scope no,
out of scope, about the app, data question, fallback.

| Batch | First untuned run | Data questions kept on the data path | After fixes |
|---|---|---|---|
| 1 (159 messages) | 122 / 159 (76.7 %) | 35 / 35 | 159 / 159 |
| 2 (133 messages) | 107 / 133 (80.5 %) | 23 / 23 | 131 / 133 + 2 known gaps |
| 3 (109 messages) | 89 / 109 (81.7 %) | 20 / 20 | 108 / 109 + 1 known gap |

Most first-run misses were small talk wordings (batch 3: 24 / 41); scope, out-of-scope, app and data questions were
12/13, 10/10, 15/16, 7/7 and 20/20 on batch 3's first run. All batches were written by the developer.

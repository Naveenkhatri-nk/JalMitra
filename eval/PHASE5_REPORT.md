# JalMitra 4.0 — Phase 5 report: accuracy, safety, multilingual testing, optimisation

Date: 23 Nov 2026 · Machine: naveen's laptop (Windows 11, RTX 4050 Laptop 6 GB, 16 GB RAM)
Status: Phase 5 is finished. There was no deployment and no Phase 6 work. The AI stays disabled by default.

## 1. Summary

| area | result |
|---|---|
| Official figures (engine vs independent SQL) | **all match**: 6762/6762 units, 745/745 districts and states, 60/60 typed questions in 6 languages, 50/50 comparisons |
| Rule engine, six languages | intent 85–100 % per language; all six still work; AI policy enforced per language |
| AI-explanation checker on independent, unseen data | test_b (final configuration): **recall 83 %, false acceptance 17 %, false rejection 21 %, precision 83 %** |
| Security | blocked questions never reach the model; a planted malicious chunk leaked nothing; tampered or unlisted chunks are now dropped |
| Regression (LLM off) | 180/180 · test_v3 21/23 (the 2 known Windows harness failures, still visible) · 190/190 · 175/175 · 435/435 |
| New tests | test_llm_provider 28/28 · test_v4_llm 35/35 · test_v4_semantic 16/16 · test_v4_ui 18/18 · test_v5 15/15 |
| groundwater.db | sha256 `9eeaee1533b478c1e649b86a56b56f4415e5255e0a3311e37a466f20bdeaa46a`, the same before and after |

**Readiness for deployment:** the rule-based app (AI off) is ready to be considered for deployment. The AI
explanations are **not** ready: about 1 in 6 wrong explanations still passes the checker on unseen data. They
must stay off for the public.

## 2. Semantic checker evaluation (highest priority)

**How the set was built.** A fresh subagent wrote and labelled 200 short explanations:
- It never saw `semantic_gate.py`, `answer_verifier.py`, `llm_compose.py` or the earlier sets. It used only
  `chunks.jsonl` and read-only SQL.
- Mix: 90 GOOD / 110 BAD; 89 en, 69 Hinglish, 42 hi; 86 place items and 114 general items.
- It covers 10 error types: DB contradictions, unsupported causes, wrong season, wrong depth direction,
  recharge/extraction confusion, wrong stage interpretation, wrong category explanation, wrong historical
  comparison, unsupported statistics and invented location facts.
- Splits: dev 50 / test_a 75 / test_b 75. The file was frozen before any scoring (`eval/v5_heldout/FROZEN_SHA256.txt`,
  sha256 `171825FB…7708`).

**Blind second labelling.** A second fresh subagent relabelled the 150 test items without seeing the labels:
**150/150 agreement, Cohen's κ = 1.0**. Both labellers are AI models of the same family, so this shows the items
are unambiguous to such a reviewer. **It is not independent validation. A human groundwater expert still has to
review the labels.**

**Procedure.**
1. test_a was scored **once** with the Phase 4 checker.
2. Fixes were chosen using the **dev split only**.
3. The final configuration was scored **once** on the untouched test_b.

Positive class = BAD (should be rejected).

| split | checker | TP | FP | TN | FN | precision | recall | false acceptance | false rejection |
|---|---|---|---|---|---|---|---|---|---|
| test_a | Phase 4 (all layers) | 39 | 13 | 20 | 3 | 75 % | 93 % | 7 % | 39 % |
| dev | Phase 4 | 26 | 13 | 11 | 0 | 67 % | 100 % | 0 % | 54 % |
| dev | final (fixes, support layer off while self-check on) | 25 | 5 | 19 | 1 | 83 % | 96 % | 4 % | 21 % |
| **test_b** | **final (production)** | **35** | **7** | **26** | **7** | **83 %** | **83 %** | **17 %** | **21 %** |

Contribution of each layer on test_b:
- number/category/place checks: recall 52 %;
- \+ semantic rules: recall 60 %;
- \+ model self-check: recall 83 %.

By language, test_b:

| lang | recall | false acceptance | false rejection |
|---|---|---|---|
| en | 78 % | 22 % | 20 % |
| hinglish | 93 % | 7 % | 25 % |
| hi | 80 % | 20 % | 17 % |

**Weakest error type:** wrong seasonal interpretation, with 1/4 caught on test_b and 2/4 on test_a. It was not
tuned on the test data.

**Changes made, all chosen on dev only:**
- a negated category ("not Safe") is no longer read as a claim;
- lowercase Latin words ("agar", "gira") are no longer taken for place names;
- places named in a cited passage are allowed;
- the sentence-support layer runs only when the self-check is off (on dev it added false rejections and caught
  nothing extra);
- a self-check without a clear verdict now **rejects** (fail closed).

**Conclusions:**
- Semantic accuracy is **not guaranteed**. On unseen data, roughly 1 in 6 wrong explanations is accepted and
  1 in 5 correct ones is rejected.
- Anything the checker cannot verify falls back to the verified rule answer.
- AI explanations stay EXPERIMENTAL and off by default.

Files: `eval/v5_heldout/` (items, README, cross-check), `eval/semantic_v5.py`, and `eval/semantic_v5_*` results
(test_a, dev variants, test_b).

## 3. Six-language evaluation

Datasets: `eval/lang_en.tsv`, `lang_hi.tsv`, `lang_hinglish.tsv`, `lang_raj.tsv`, `lang_pa.tsv`, `lang_mr.tsv`,
20 questions each. Report: `eval/lang_eval_2026-11-23.md`.

| lang | intent | language label | places | AI policy | enforced |
|---|---|---|---|---|---|
| en | 95 % | 100 % | 100 % | Experimental | yes |
| hinglish | 95 % | 95 % | 88 % | Experimental | yes |
| hi | 95 % | 90 % | 75 % | Disabled (factuality validation pending) | yes |
| raj | 85 % | 85 % | 81 % | Disabled (native review pending) | yes |
| pa | 100 % | 100 % | 50 % | Disabled (native review pending) | yes |
| mr | 95 % | 100 % | 62 % | Disabled (native review pending) | yes |

- Coming Soon replies exist in all six languages.
- No native-level accuracy is claimed. The hi, raj, pa and mr wording still needs native-speaker review.
- The weakest area is Punjabi and Marathi place names, where the rules ask the user to clarify.

## 4. Groundwater accuracy (`eval/gw_accuracy.py`, `eval/gw_accuracy_2026-11-23.md`)

The SQL is independent: it does not reuse `database.py` or `retrieval.py`, and numbers are compared exactly.

- **6762/6762 assessment units.** For the 302 Rajasthan units with figures: category, stage %, recharge,
  extractable resource and extraction (ham and bcm). For category-only units: category checked, and no figure
  may be shown.
- **60/60 typed questions in six languages.** Correct place, stage shown, and no number that isn't stored.
- **745/745 districts and states**: category counts and the National Compilation stage.
- **50/50 district comparisons.**
- **History:** `groundwater.db` holds only the 2025 assessment. Earlier-year or trend questions cannot be answered
  from it, and the AI checker rejects trend claims. The monitoring data collected by the other work thread
  (`data/monitoring/`) is **not integrated and was not used**.

The first run flagged 53 mismatches. All were artefacts of my own checker, not engine errors:
- the "24" in "NORTH 24 PARGANAS";
- the conflict-source pages for Golaghat West;
- a Saline unit with no published stage.

## 5. Performance (`eval/perf_v5_2026-11-23.md`)

VALORANT was running on the GPU during the measurement (about 1.5 GB of VRAM), so speeds are lower than on an
idle laptop: Phase 2 measured about 56 tokens/s.

| item | measured |
|---|---|
| VRAM, chat + embedding model loaded | 5240 / 6141 MiB (about 3.7 GB for the models) |
| RAM, Ollama runners | about 1.7 GB in total (llama-server 996 MB + 730 MB) |
| cold load: chat model / embedding model | 4.1 s / about 6.1 s (first query) |
| time to first token, warm | about 2.1 s (prompts of 1100–1500 tokens) |
| full generation, short / medium / long | 5.3 s / 7.0 s / 6.1 s (21–28 tokens/s) |
| RAG retrieval: new query / repeated query | 2.07 s (embedding dominates) / 3.4 ms |
| full checked AI step (retrieval + generation + checks + self-check) | 7–15 s |
| repeated question (outcome cache) | below 1 ms |
| rule-only answer (AI off) | median 1.9 ms |

Optimisations (no change to safety):
- **Two-stage chat.** The verified official answer appears at once. "Writing and checking the AI explanation…"
  shows until the checked text is ready.
- **Outcome cache.** Holds only completed outcomes: verified, rejected, no answer, no passages. The key covers the
  question, language, mode, fact block, model and safety flags. Errors and timeouts are never cached.
- **Query-embedding cache.**
- **Streaming** was measured but **not** used for display, because it would show unverified text.
- No bigger or new model, and no check removed.

## 6. Security (`test_v5.py`, `eval/security_live_2026-11-23.md`)

- Blocked before any model call, in all tested forms:
  - injection in en, hi, hinglish, pa and mr, including upper case, role-play, "system prompt", SQL and `<script>`;
  - "guess / estimate / predict / make up";
  - "assume my block is Atlantis".
- False place names get no figures and no table.
- Unsupported statistics are rejected ("62 % of farmers…", "fell by 3 metres", "in 2020 it was Safe").
- Invalid RAG references are rejected: `[P9]`, `[P0]`, `[Source: … p999]`.
- Model unavailable: exact fallback to the rule answer.
- **Planted malicious chunks.** They were added to a TEMPORARY COPY of the index; `data/rag/` was never written.
  - Live run with the real model: 0 leaks of injected text, fake figures (99999, 12 %) or links across
    11 questions.
  - **Finding:** in the first live run a sanitised malicious chunk was still *cited* as a source, as fake
    "PDF page 900".
  - **Fix:** `rag.retrieve` now returns only chunks listed in the approved manifest (`data/rag/chunks.jsonl`)
    with identical text hashes. If the manifest is missing, no passages are returned. Re-run: no malicious chunk
    retrieved.
  - All 226 real chunks pass the manifest check.

## 7. UI usability findings

| finding | action |
|---|---|
| two "New conversation" buttons in the sidebar (the old one reset the 3.0 chat) | **fixed**: the old button is hidden on the chat page (screenshot 03) |
| AI step made users wait 7–15 s with nothing on screen | **improved**: two-stage answer (screenshots 01–02) |
| phone view opens scrolled down (hero hidden; Streamlit "stick to bottom") | **not fixed**: three script approaches were tried and Streamlit kept overriding them. The script was removed rather than shipped fragile. Content is still reachable by scrolling (screenshot 05) |
| sidebar caption "Offline engine: no AI model" is still shown when the dev AI toggle is on | not changed (dev mode only); listed for Phase 6 |
| desktop, mobile layout, chat history, new conversation, language selector, data cards, sources, AI labels, AI on/off, Coming Soon, loading, error handling, empty and long results | covered by test_v4_ui (18) and test_v5 UI tests; checked in the browser |

Screenshots of the improvements are in `screenshots_v5/`.

## 8. Regression

Run with the LLM off, after all changes:

| suite | passed | failed | skipped |
|---|---|---|---|
| test_local_engine | 180 | 0 | 0 |
| test_v3 | 21 | 2 (UI01_website_loads, NET01_no_network: the known Windows loopback harness issue; fix not approved) | 0 |
| test_v3_domains | 190 | 0 | 0 |
| test_app_info | 175 | 0 | 0 |
| test_conversation | 435 | 0 | 0 |
| test_llm_provider | 28 | 0 | 0 |
| test_v4_llm | 35 | 0 | 0 |
| test_v4_semantic | 16 | 0 | 0 |
| test_v4_ui | 18 | 0 | 0 |
| test_v5 (new) | 15 | 0 | 0 |

- With AI off, `engine.answer` gives byte-identical answers to before any LLM work (138/138 snapshot).
- Expected outputs of the documented suites were not changed.
- My own Phase 3/4 test fixtures were updated where Phase 5 *deliberately* changed behaviour:
  - cache off in the fixtures;
  - self-check set explicitly in the layer test;
  - a self-check with no verdict now rejects;
  - allow-lists of modules that may import the provider.

## 9. Database integrity

`groundwater.db` sha256 was `9eeaee15…aa46a` at the start of Phase 5, after every evaluation, after the
regression and at the end. Every evaluation opened it read-only (`mode=ro`).

## 10. Files

**Created**
- `test_v5.py`
- `eval/gw_accuracy.py` and its results; `eval/lang_eval.py`, `eval/lang_<6 codes>.tsv` and the report
- `eval/perf_v5.py` and its results; `eval/security_live.py` and its results
- `eval/semantic_v5.py` and its results
- `eval/v5_heldout/` (items, README, frozen hash, cross-check labels); `eval/PHASE5_REPORT.md`
- `screenshots_v5/`

**Modified**
- `app.py`: one change, hiding the old sidebar button on the chat page. Its hash was checked right before the
  edit.
- `answer_verifier.py`: negation-aware categories.
- `semantic_gate.py`: a self-check without a verdict now rejects; switch for the causal-overlap rule.
- `llm_compose.py`: outcome cache, stage timings, lowercase-word place fix, passage places, support layer only
  without the self-check.
- `rag.py`: approved-chunk manifest, embedding cache.
- `ui_chat_v4.py`: two-stage answer, AI timing (the scroll script was tried and removed).
- My test files `test_v4_llm.py`, `test_v4_semantic.py`, `test_v4_ui.py` and `test_llm_provider.py`: fixture
  changes only.
- The result CSVs that the suites rewrite.

**Not changed:** `engine.py`, `groundwater.db`, `requirements.txt`, the Coming Soon modules, and the other thread's
`ingest/`, `data/monitoring/`, `monitoring_retrieval.py` and `test_monitoring.py`. Nothing was installed or
downloaded in Phase 5.

## 11. Remaining limitations

1. The AI checker still accepts about 17 % of wrong explanations and rejects about 21 % of correct ones on unseen
   data. Seasonal errors are the weakest type.
2. All evaluation labels are AI-written. Human groundwater-expert review is still required, and native-speaker
   review for hi, raj, pa and mr.
3. AI explanations take 7–15 s (VALORANT was sharing the GPU during measurement); rule answers take about 2 ms.
4. The phone view opens scrolled towards the input (not fixed).
5. Only the 2025 assessment is in the database, so there are no historical comparisons.
6. Interface labels are in English and Hindi only.
7. The test_v3 Windows harness failures remain (fix not approved).
8. Hindi AI stays disabled. The factuality evidence for Hindi is only 42 items.

## 12. Phase 6 deployment readiness

| component | ready? | condition |
|---|---|---|
| Rule-based groundwater chat (AI off) | **Ready for a controlled deployment decision** | figures verified against SQL; all suites green except the known harness pair; Coming Soon in place |
| AI explanations (en, hinglish) | **Not ready for the public** | keep dev-only until human expert review of a larger labelled set and false acceptance clearly below the current 17 % |
| AI explanations (hi / raj / pa / mr) | **Disabled** | needs factuality and native review first |
| Hosting | not assessed | Phase 6 must decide: local Ollama on the server or a hosted provider (AI off by default either way) |

Recommended before any public AI:
1. A human-labelled set of 300 or more items, including more seasonal and direction cases.
2. Re-score the checker on it once.
3. Repeat the performance run on an idle GPU or the target server.
4. Fix the phone scroll position, possibly with a different Streamlit layout.
5. Approve the test_v3 harness fix.

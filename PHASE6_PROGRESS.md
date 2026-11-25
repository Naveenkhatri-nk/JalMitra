# Phase 6 progress

**Complete (24 Nov 2026).** The full report is in eval/PHASE6_REPORT.md.

- groundwater.db sha256 at the end: 9eeaee1533b478c1e649b86a56b56f4415e5255e0a3311e37a466f20bdeaa46a (unchanged).
- No file is left mid-edit. All evaluation and Streamlit processes I started have finished or been stopped.
- Ollama is still running, with the model kept loaded for 30 minutes after the last use.
- 24 Nov, fixes after the report (details in eval/PHASE6_REPORT.md §11a–11e):
  - small talk;
  - data-coverage questions;
  - state spellings;
  - ask-back and unclear questions;
  - borewell questions, including the "nikal" → NAYKAL misread and the sidebar location in ask-back replies.

  Files changed: jalmitra_ai.py, ui_chat_v4.py, answer_verifier.py, semantic_gate.py, entity_resolver.py (stop-words only), fake_ai_for_tests.py and test_v6.py.

  All 11 suites pass (1140/1140). DB sha256 is unchanged.
- Waiting for naveen's decision:
  - test_v3 UI01 now checks the chat start page (option (a)). Option (b), the old overview page, is available on request.
  - `ollama rm gemma3:4b` would free 3.3 GB. It is naveen's choice whether to run it.

## UI redesign (24 Nov 2026)

ChatGPT / Claude-style interface. Engine, AI pipeline and data are unchanged.

- Backup of the old UI files: backup\app_v4_ui_pre_redesign_20261124\ (BACKUP_MANIFEST.csv has the sha256 of each file).
- Sidebar: "New chat", saved chats grouped Today / Yesterday / Earlier (open, rename, delete, clear all), More pages, About, Coming soon, Settings, and a Day/Night quick toggle.
- Chat history and settings are stored only as local JSON in data\chat_history\ (chat_<id>.json, settings.json), never in groundwater.db. A reopened chat shows its official data cards again and can continue.
- Settings dialog: theme (Day / Night / System), interface and answer language, default location, answer style and length, voice, local AI status (model, GPU, server), clear history.
- Clean welcome screen with 6 of the verified example cards. Chat bubbles, restyled data cards with source and year chips, and styled notices for "could not be verified" and "AI not available". Streamlit menu, deploy button and footer are hidden. Still localhost-only.
- New files: chat_store.py, ui_settings.py, ui_theme.py. Changed: app.py, ui_chat_v4.py, ui_components.py (card chips), .streamlit/config.toml (palettes), test_v4_ui.py (+6 tests, 1 button label), test_v5.py (1 button label).
- Tests: all 11 suites pass (1146/1146; 6 are new).
- Live smoke test on port 8765 (stopped afterwards). Screenshots are in docs\screenshots\.
- groundwater.db sha256 at the end: 9eeaee1533b478c1e649b86a56b56f4415e5255e0a3311e37a466f20bdeaa46a (unchanged).

## Light theme by default (24 Nov 2026)

- naveen asked for light colours. Day (light) is now the default theme (ui_settings.DEFAULTS). Night and System are still available in Settings and through the sidebar toggle.
- The light palette is slightly softer: white main area, #F7F9FC sidebar and cards, #E3E8EF borders, light-blue user bubbles. Changed in ui_theme.py and .streamlit/config.toml.
- There was no saved settings file to switch over (data\chat_history\ does not exist yet).
- test_v4_ui now checks that the default is Day. Results: test_v4_ui 24/24, test_v5 15/15, test_v3 23/23, test_v6 25/25.
- The day screenshots in docs\screenshots\ are refreshed.
- groundwater.db sha256 is unchanged.

## Fix: concept questions answered as a place (24 Nov 2026)

- Problem (naveen's screenshot): "explain basic structure of water cycle" was answered about the block CHICHLI (Narsinghpur, MP), with a Chichli data card.
- Root cause: the place matcher (entity_resolver.py) matched words by sound. "cycle" has the same sound key as CHICHLI. The AI then correctly described CHICHLI, because the rule step had handed it that place as evidence, so the reply passed the checks. The location chosen in Settings played no part.
- Changes:
  - entity_resolver.py: a match by sound on an English-script word is kept only when the spelling is close to the place name (similarity >= 0.72), or >= 0.5 when a location cue is next to it (in/at/near, block/district, ka/ki/ke/mein). Exact names and aliases are unchanged.
  - jalmitra_ai.py: is_concept_question() covers questions like water cycle, aquifer, recharge, percolation, borewell working, जल चक्र, भूजल, पुनर्भरण, ਜਲ ਚੱਕਰ. It requires an explain cue and no place, "my area" word, "in <Name>" or mention. Such questions are classified "general": an explanation from the approved documents with no data card.
  - ui_chat_v4.py: a concept reply never shows data cards from the location chosen in Settings.
- Tests:
  - test_v6.py +3: cycle-like words never match a place; 20 concept questions in 4 languages, with and without a home location, classify as general; place regressions still resolve (Osiyan, jodpur, naykal, sikar, barmer, Shergarh, utterpradesh, "recharge of osian").
  - test_v4_ui.py +1: the chat shows no CHICHLI and no data card for the water-cycle question.
  - All 11 suites pass (1150/1150).
- Live check with the local model, 40 questions (eval/live_concept_check_20261124.csv): 39 verified, 1 honest "could not be verified" (Punjabi ਜਲ ਚੱਕਰ). No wrong place in any reply. Welcome examples and place questions behave as before.
- Weak wording seen in the live check (model quality, not a wrong place): "jal chakra kya hai" and "stages of the water cycle". The model calls these questions "not correct in this context".
- groundwater.db sha256 is unchanged (9eeaee15...aa46a).

## Block figures from the CGWB 2025 state reports in the chat (24 Nov 2026)

- naveen asked for "Data unavailable" to be filled wherever official figures exist. The data thread built data\monitoring\gwra_blocks_2025.db and gwra_blocks_retrieval.py, a read-only lookup. groundwater.db is untouched.
- New gwra_enrich.py, called at the end of jalmitra_ai.rule_for. For units outside Rajasthan it copies the usable state-report figures into the engine result:
  - into the unit record (stage, recharge, extractable, total extraction in ham; source "CGWB <State> 2025" with the pages);
  - into the table row (plus the breakdowns), into the facts text and into the sources list.
  - The data cards, the data table, the AI facts and the existing number, category and place checks therefore all use the same official figures. Nothing in the checks was loosened.
- Rajasthan still uses groundwater.db.
- Saline / zero-resource units stay "Data unavailable", with a short reason.
- Units with no figures in their state report get a one-line reason, and the chat shows the district totals (NC2025) as a clearly labelled fallback. The reasons:
  - Telangana and Mizoram: district totals only.
  - Tamil Nadu: figures per firka.
  - Punjab: no 2025 block report.
  - Odisha, Goa, Lakshadweep, Chandigarh: no usable unit table.
  - Arithmetic check failed: the unit is named as such.
- Category conflicts: in 3 units the state report's category differs from AI2025 (Golaghat West, Garhwa, Jaora). Both categories are shown with their sources, and the report's figures stay held back.
- District cards: "Units with figures" now counts the units with state-report figures, citing CGWB <State> 2025.
- Spot-check (eval/spot_check_gwra_blocks.py, eval/spot_check_gwra_blocks_20261124.csv): 10 random units in MP, UP, Gujarat, Karnataka and Maharashtra were checked against the cited PDF pages. 10/10 match. In 3 of them the PDF text layer wraps or cuts the decimals; those were confirmed by hand.
- Tests:
  - test_v6.py +4: figures for MP, UP, Gujarat and Karnataka; the verifier accepts the right number and rejects a wrong one; fallbacks for Telangana (Naykal), Tamil Nadu (taluk and firka lookup) and the Jaora conflict; Rajasthan, the Rajasthan saline unit KHAJUWALA and the Gujarat saline unit DHANDHUKA unchanged.
  - test_v4_ui.py +1: CHICHLI cards and the Naykal district fallback.
  - Results: all 11 suites pass (1157/1157); test_gwra_blocks 18/18.
- Live check with the local model, 25 questions (eval/live_state_report_check_20261124.csv): 21 verified, 4 honest "could not be verified".
  - Jaora, Dhandhuka and "Compare Chichli and Bagh" were rejected by the existing checks: a time claim, the self-check, and other category names. Olpad was model variance; it passes on a rerun.
  - No check rejected a state-report figure.
- groundwater.db sha256 is unchanged (9eeaee15...aa46a).

# Changelog

## Everyday conversation — 22 November 2026
### Fixed
- "nice", "thanks", "ok", "bye", "how are you" and similar got "Sorry, I did not understand"; some were even read as
  places ("great" as Gagret, "badhiya" as Badi, "ਧੰਨਵਾਦ" as Dhanwada, "money" as Mohania).
- "is this site about how to grow money?" got the general introduction; it now answers "No" and says what is covered.
### Added
- `conversation.py` (no LLM, no database):
  - small talk in six languages: thanks, praise, ok/yes/no, bye, greetings, how are you, who made you / are you a robot /
    is this a government site, "that's wrong", "I don't understand", laughter and emoji. Typos ("awsome"), SMS spellings
    ("thnks", "gr8", "r u"), repeated letters ("thank uuu", "hiii") are tolerated. The whole message must be small talk,
    so "thanks, is Ajmer safe?" still gets the data answer.
  - yes/no scope questions ("Is this about soil?", "Can I upload my soil card here?", "kya ye app loan deta hai?"):
    Yes / Partly (fertiliser doses) / No, then what JalMitra covers. A place, crop, parameter or category in the question
    sends it to the normal data answer.
  - out-of-scope subjects with a pointer: money, loans, schemes and insurance (bank / agriculture office), mandi prices
    (Agmarknet), weather (IMD Agromet), pests and diseases (Krishi Vigyan Kendra), animals, buying/selling, and general
    topics. Weather questions are answered even when they say "forecast" or "predict".
  - varied wording: small talk, scope, out-of-scope and fallback replies rotate between two or three wordings. The first
    reply in a conversation keeps the 2.0 text, so older tests still match.
  - smarter fallback: words that were recognised (soil, crop, water, irrigation, land ...) pick the closest real
    questions; they are shown as buttons. Every suggested question is tested to give a real answer.
- Common chat words ("bahut", "later", "sakte", "site", "rate" ...) are no longer sound-matched to place names.
- Marathi/Punjabi word gaps found on the way: पिण्याच्या (drinking), गव्हाला (wheat), धूप / ਖੋਰ (erosion).
  `data/reference/crops.csv` gained three wheat spellings and `data/knowledge.db` was rebuilt from the CSV files.
- `test_conversation.py` (435 tests) with three batches in `tests_data/`.
### Unchanged
- `data/groundwater.db` (sha256 `9eeaee1533b478c1…`), grounding, SQL safety, number lock, injection and fabrication blocks.

## Questions about JalMitra itself — 22 November 2026
### Fixed
- "What is this website about?", "JalMitra is for what?", "What does this website do?", "JalMitra kya hai?" and
  similar questions got the low-confidence "Sorry, I did not understand" reply. They are now answered.
### Added
- `app_info.py`: five intents, detected before place lookup and before the fallback, with no SQL and no groundwater
  entity resolution: `ABOUT_JALMITRA`, `WHAT_CAN_YOU_DO`, `HOW_TO_USE`, `HELP`, `FEATURE_LIST`. Handles the spellings
  JalMitra, Jalmitra, Jal Mitra, Jalmithra, जलमित्र, ਜਲਮਿੱਤਰ. Questions that also contain a data word (block,
  district, soil, crop, stage, fluoride ...) or a place go to the normal pipeline as before.
- `templates_app.py`: introduction, "what can you do", "how to use", help and feature list in English, Hindi, Hinglish,
  Marathi, Punjabi and Rajasthani. Only implemented features are listed; the text says that detailed groundwater figures
  exist for 302 Rajasthan blocks only, that coverage differs by place, and that JalMitra never certifies water as safe
  to drink. Non-English texts are pending native review.
- Casual wording without a fixed phrase ("things which you can provide me", "your services", "features?", "options",
  "who are you", "aap kya kya kar sakte ho", "ਤੁਸੀਂ ਕੀ ਕਰ ਸਕਦੇ ਹੋ"): the whole message must be made of known words
  (you/aap/tum, offer/provide/services/features/options, question words). One unknown word, such as a place, crop or
  "CGWB", sends the question to the normal pipeline. "sakti" was left out because Sakti is also a block name.
- "Explain in Hindi" / "Explain more" right after one of these answers re-shows it in the new language / as the feature list.
- `test_app_info.py` (175 tests, including 117 casual wordings in two batches) and `test_results_app_info.csv`.
### Changed
- The greeting (`help`), `rephrase` and `off_topic` texts now mention soil, water quality, crops and land and suggest
  asking "What is JalMitra?". Greetings ("hello", "namaste") still use the `help` intent; a bare "Help" now uses `HELP`.
### Unchanged
- `data/groundwater.db` (sha256 `9eeaee1533b478c1…`), grounding, SQL safety, number lock and the no-fabrication checks.

## 3.0 Phases 2–8 — 22 November 2026
### Added
- Reference database `data/knowledge.db`, built from reviewable CSV files in `data/reference/` by `build_knowledge_db.py`:
  19 catalogued sources with access class, 85 rating ranges (soil, drinking water, irrigation water), IS 11624 EC limits,
  FAO crop salt tolerance (13 crops) and water need (21 crops), SKNAU Zone II-A description and crop list,
  26 parameter explanations and 41 general guidance texts (English and Hindi, marked pending expert review).
- Empty `data/observations.db` with provenance-rich tables and `import_dataset.py` (dry run by default, original values
  kept, BDL/ND never turned into zero, duplicate files refused, every import logged).
- Soil Health Card reader (`soil_card.py`) for PDF text layer, CSV and Excel with type, size and content checks;
  review/correct/confirm workflow; private session storage with optional local save and delete.
- `soil_interpret.py`: card rating first, then each source's rating; unit mismatches are not compared; no score.
- `water_quality.py`: drinking (IS 10500:2012 and CGWB 2024, both shown when they differ) and irrigation checks.
- `knowledge_answer.py`: soil, land, crop, irrigation and water-quality answers with separated sections
  (measured facts, published category, regional description, interpretation, general suggestions, missing information).
- Conversation: "Explain in Hindi" / "Translate this", "Explain more" / "Give details", "Why?", "Show the source".
- 17-page navigation; new pages: Groundwater Quality, Soil Type and Profile, Land Degradation; rebuilt Soil Health,
  Land Intelligence, Crop Advisor, Irrigation Advisor, My Soil Report, My Reports, Learning Centre, Data Sources,
  Geographic Explorer (GeoJSON layer if supplied).
- Six report types as Markdown and English PDF (`reports_pdf.py`, `report_builders.py`).
- `test_v3_domains.py` (190 tests, areas A–U) and result files.
### Changed
- Home page texts and sample questions follow the master instruction; language, audience and detail selectors on the home page.
- Phase 1 test DOM01 now allows numbers in no-location answers only when the answer cites a reference table
  (before Phases 2–5 no reference numbers existed).
### Unchanged
- `data/groundwater.db` (sha256 `9eeaee1533b478c1…`), all original files in `data/raw`, the 2.0 answers in Standard mode.

## 3.0 Phase 1 — 22 November 2026
Website redesign, memory, answer styles and lengths (see README).

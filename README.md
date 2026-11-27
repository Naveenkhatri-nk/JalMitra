# 💧 JalMitra 4.0: multilingual groundwater assistant

Prompt Engineering project, JECRC University, Section DC (2026).
Team (7 members): Naveen Khatri, Rohit Sharma, Aryan Jangir, Himanshu Yadav, Aryan Sharma, Param Jain, Garvit Khandal. Guide: Mr. Ajay.
Who did what: [`MEMBERS.md`](MEMBERS.md) and each member's PDF in [`docs/members/`](docs/members/).

JalMitra is a chatbot (built for SIH25066, Ministry of Jal Shakti) that answers plain-language
questions about India's groundwater (CGWB GWRA 2025) in English, Hindi, Hinglish, Marathi,
Punjabi and Rajasthani.

**JalMitra 4.0 uses a local AI model.** Qwen3-4B Instruct, run by Ollama on the laptop's GPU, writes every
reply. Rules first handle safety, language, place names and the read-only database lookup. The AI gets only the
official facts and approved report passages (RAG), and every reply is checked (numbers, categories, places,
script, meaning) before it is shown. A reply that can't be verified is not shown. The official figures are always
displayed straight from the database, never from the AI. No cloud service or API key is used.

**How to run (Windows):** double-click `START_JALMITRA.bat` (needs Python, `pip install -r requirements.txt`
and `requirements-llm.txt`, and Ollama with `qwen3:4b-instruct-2507-q4_K_M` and `bge-m3`).

**Data coverage:** Category information: 6,762 assessment units. Block-level figures: 5,184 units
(Rajasthan from `data/groundwater.db`, other states from the 2025 state reports). Assessment year: 2025.

> The sections below describe earlier versions (2.0 and 3.0) and are kept for history.

> JalMitra never makes up, estimates or rounds groundwater numbers. Missing values are shown as
> "not available", never as 0. Ambiguous place names are never guessed: the user is asked.


## What is new in 3.0 (Phases 2–8)

_Understand Your Land. Improve Your Soil. Manage Your Water._ Status of every phase: `PROJECT_STATUS.md`.

- **17 pages:** Home, Ask JalMitra, Groundwater Intelligence, Groundwater Quality, Soil Health, Soil Type and Profile,
  Land Intelligence, Land Degradation, Crop Advisor, Irrigation Advisor, Geographic Explorer, Compare Areas,
  My Soil Report, My Reports, Learning Centre, Data Sources, About JalMitra.
- **My Soil Report:** upload a Soil Health Card (PDF with text, CSV or Excel, up to 5 MB) or type the values →
  check and correct every value → confirm date, depth and units → plain explanation. The card's own rating is shown
  first, then the ICAR-CRIDA and TNAU chart ratings. No overall score. Private to the session; save or delete on this
  computer (`user_data/`, never committed).
- **Groundwater Quality:** category (quantity), level, chemistry, drinking and irrigation suitability kept apart; compare
  your own water test with IS 10500:2012 and CGWB 2024 (both shown where they differ), and irrigation water with IS 11624
  (EC by clay content), SAR, RSC and %Na. JalMitra never says water is safe to drink.
- **Crop Advisor:** FAO salt tolerance and seasonal water need, the SKNAU Zone II-A crop list, comparison tables and an
  ECe check. Field suitability shows "Insufficient data" until field data exists.
- **Land Intelligence:** a 15-section Land Condition Report; missing data is written as missing.
- **Reports:** Groundwater, Soil Health, Land Condition, Crop Suitability, Irrigation and Complete reports as Markdown,
  English PDF and CSV.
- **Chat:** soil, land, crop, irrigation and water-quality questions; "Explain in Hindi", "Translate this",
  "Explain more", "Why?", "Show the source".

### Install (Windows)
```
cd E:\JalMitra
pip install -r requirements.txt
python build_knowledge_db.py        # builds data\knowledge.db from data\reference\*.csv (safe to repeat)
streamlit run app.py
```

### Import a downloaded dataset
```
python import_dataset.py groundwater_quality data\raw\groundwater_quality\FILE.csv --source CGWB_GWQ_DATA          (dry run)
python import_dataset.py groundwater_quality data\raw\groundwater_quality\FILE.csv --source CGWB_GWQ_DATA --commit
```
New sources are first added to `data\reference\source_catalog.csv`. What to download and whom to ask:
`DATA_ACCESS_REQUESTS.md`. Boundary maps: put official GeoJSON in `data\geo\` with a `.source.txt` file.

### Test
```
python test_local_engine.py   &   python test_v3.py   &   python test_v3_domains.py   &   python test_app_info.py   &   python test_conversation.py
```
Results: `TEST_STATUS.md`. Limits: `KNOWN_LIMITATIONS.md`. Sources: `DATA_SOURCES.md`.

### Deploy
It runs on one computer with `streamlit run app.py`. To share on a local network:
`streamlit run app.py --server.address 0.0.0.0`. For a public deployment (for example Streamlit Community Cloud) the
repository must not contain `.env`, `user_data/` or any farmer's report; uploads then live only in each visitor's session.

## What is new in 3.0 (Phase 1)

* **Website.** 14 pages in the sidebar: Home, Ask JalMitra, Groundwater Intelligence, Geographic
  Explorer, Compare Locations, Soil Health, Land Intelligence, Crop Suitability, Irrigation Advisor,
  My Soil Report, My Reports, Learning Centre, About JalMitra, Data Sources and Coverage.
  Logo and favicon in `assets/`, light and dark colours in `.streamlit/config.toml`
  (switch with the menu ⋮ > Settings > Theme). Interface in English or Hindi; answers in six languages.
* **Your location** is chosen by you in the sidebar or the search box on Home (no tracking).
  "my block", "my area", "mera ilaka", "here" use it; without it JalMitra asks.
* **Memory.** "What does it mean?" explains the category of the last answer; "What about Jodhpur?"
  keeps the kind of question; "Is its soil good?" / "Which crops are suitable there?" use the last place;
  "Compare both districts" compares the last two places (a block is compared through its district, and
  the answer says so); if "its" could mean two places, JalMitra asks which. "New conversation" forgets
  everything.
* **Soil, land, crop and irrigation questions** are understood, but there is no such data yet, so the
  answer is "Data unavailable" plus the verified groundwater data for that place. Nothing is estimated.
* **Answer styles** Farmer / Official / Student and **lengths** Short / Standard / Detailed (sidebar).
  Standard answers are word-for-word the 2.0 answers (tested). Detailed answers label each part:
  published classification, published assessment figures, reasoning, interpretation, general advice,
  missing information, limitations, sources.
* **Downloads:** each answer's table as CSV, the whole conversation as a Markdown report (Ask page and
  My Reports). Thumbs up/down ratings are saved only in `feedback/feedback_log.csv` on this computer.
* New files: `templates_v3.py` (new answer templates, 6 languages), `ui_text.py`, `ui_components.py`,
  `ui_pages.py`, `assets/`, `.streamlit/config.toml`, `test_v3.py`.
  The 2.0 app is kept in `backup/app_v2_offline_20261122/` (with a copy of the database).

Tests: `python test_local_engine.py` (180 tests from 2.0) and `python test_v3.py` (23 tests for 3.0:
memory, soil/crop "Data unavailable", chosen location, 6 languages x 3 styles x 3 lengths, Standard = 2.0,
website loads, no LLM/API key, no network, database unchanged).

---

## 1. Run it (Windows)

```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

No `.env` is needed. Run the tests:

```bat
python test_local_engine.py
```

This writes `test_results.csv`, `performance_results.csv` and `language_test_results.csv`.

## 2. Files

| File | What it does |
|---|---|
| `app.py` | Streamlit chat: language picker, farmer/official mode, coverage line, answers, warnings, charts, data table, source records, voice mode. |
| `engine.py` | The pipeline: clean question → language → intent + places → follow-up/clarification → database → template answer. Measures time per answer. |
| `intent_parser.py` | Rule-based intents with keyword dictionaries in six languages, regex for N, years and categories, prompt-injection and "make up a number" detection. |
| `entity_resolver.py` | Finds states, districts and blocks in the question: alias table → exact database name → phonetic key (reported to the user). Close spellings are only offered as "Did you mean…?". |
| `data/place_aliases.csv` | Separate alias table (Hindi/Marathi/Punjabi names, old names such as Poona, Gurugram). Every row is checked against the database at start-up; groundwater values are never touched. |
| `conversation_state.py` | Memory of one chat: last places, "what about X", "compare both", answers to clarification questions ("1", "district", "the West Bengal one"). |
| `retrieval.py` | Structured results from fixed, parameterised, read-only SQL (via `database.py`). |
| `response_builder.py` | Answers from fixed templates; numbers copied from database fields; citations and translated warnings. |
| `language.py` | Language detection rules, Rajasthani marker words, all answer templates in six languages, category translations, voice locales. |
| `voice.py`, `voice_component/index.html` | Browser speech recognition (Start/Stop, editable transcript) and speech synthesis (Play, Pause/Resume, Stop). |
| `database.py` | Read-only SQLite access (`mode=ro`, `query_only`, authorizer). One shared connection, cached small tables. |
| `security.py` | Cleans and length-checks the question. |
| `test_local_engine.py` | 172 dialogue tests + 8 module tests, checked against the database with independent SQL. |
| `build_dataset.py`, `extract_data.py`, `build_database.py`, `validate_database.py` | Build and validate the database from the official PDFs (unchanged). |
| `ai.py`, `test_chatbot.py` | **Legacy Gemini version, not used by 2.0.** A working copy of the Gemini version is in `backup/app_v2_gemini_20261122/`. |

## 3. Questions it understands

| Kind | Examples |
|---|---|
| Status / category | Is Ajmer Urban safe? · Jaipur ka paani kaisa hai? · जयपुर ज़िले में भूजल की स्थिति क्या है? |
| Figures | Stage of extraction of Ajmer Urban · Gadraroad ka recharge kitna hai |
| Top-N | Top 5 over-exploited blocks in Rajasthan · give me 3 worst blocks of Jodhpur district |
| Districts / states by count | Which district has the most over-exploited units? |
| Lists and counts | Safe blocks in Pune district · पुणे जिल्ह्यात किती सुरक्षित तालुके आहेत? |
| District / state search | Show all blocks in Jaipur district · Rajasthan groundwater status |
| Compare places | Compare Jaipur district and Jodhpur district · ਲੁਧਿਆਣਾ ਅਤੇ ਪਟਿਆਲਾ ਦੀ ਤੁਲਨਾ ਕਰੋ |
| Compare years | Compare 2020 and 2025 for Jaipur (answer: only 2025 is in the database) |
| Meaning of a category | What does semi-critical mean? · अतिशोषित म्हणजे काय? |
| Sources, data available, data quality | Where does this data come from? · What data do you have? · Which units have data-quality warnings? |
| Follow-ups | Is Jaipur safe? → (1) → What about Jodhpur? → Compare both |

Questions the rules cannot place confidently get "please ask another way". Requests to ignore the
rules, run SQL, or guess/estimate numbers are refused.

## 4. Voice (new in 2.0, browser only)

Turn on **Voice mode** in the sidebar. Press **Start**, speak, press **Stop** (or pause). The text appears in an
editable box; correct it and press **Ask**. Answers have **Play / Pause / Stop** buttons.

- Uses the browser's Web Speech API (Chrome or Edge). In Chrome/Edge, recognition is done by the browser
  vendor's speech service, so listening needs internet; everything else works offline.
- Locales: English en-IN and Hindi hi-IN are standard browser locales. Hinglish (en-IN recogniser), Marathi
  (mr-IN), Punjabi (pa-IN) and Rajasthani (Hindi hi-IN recogniser and voice) are **experimental**.
- Not yet tested with a real microphone or real speech. If speech fails, type in the chat box as usual.

## 5. Rules kept with the data

- 5 Rajasthan blocks where the published category differs from the stage range: published category shown,
  with a warning naming the calculated range.
- Gira and Jaisalmer Urban: published stage differs from extraction ÷ extractable; both values shown.
- 3 saline blocks published with zeros: shown as printed, with a warning that they need verification.
- Golaghat West (Assam): All India list and National Compilation disagree; both observations shown, none chosen.
- Gadra Road: name printed as "GADRARO" in the Rajasthan report; warning shown.
- National Compilation district/state totals are labelled as area totals, never mixed with unit figures.
- Units without a published stage are never ranked.

## 6. Known limits

- Understanding is rule-based: phrasings far from the keyword lists are not understood and the user is
  asked to rephrase. Rajasthani support covers tested Marwari marker words only, not the language in general.
- Place names in Devanagari/Gurmukhi are matched through the alias table and a simple transliteration;
  names outside the alias table may need the English spelling.
- Template translations (Hindi, Marathi, Punjabi, Rajasthani) need review by native speakers.
- Only assessment year 2025 is in the database, so year comparisons always say so.
- Place names are shown exactly as stored in the database (only "_" is shown as a space).
- The database has no index on `year`; adding one would change `groundwater.db`, which is not allowed.

## 7. When something goes wrong

| Message | Fix |
|---|---|
| `No official groundwater data imported yet` | `data/groundwater.db` is missing; run `build_dataset.py` and `build_database.py`. |
| `Speech recognition is not available in this browser` | Use Chrome or Edge, or type the question. |
| `Microphone permission was denied` / `No microphone was found` | Allow the microphone for the site, or plug one in. |
| `ModuleNotFoundError` | Activate `.venv` and run `pip install -r requirements.txt`. |

# JalMitra 3.0 — Project status

_Last updated: 22 November 2026 (end of the autonomous Phase 0 and 2–8 run)_

JalMitra is an offline, rule-based assistant for land, soil, groundwater and agriculture.
No AI model, no API key and no internet connection are needed to answer questions.

## Where each phase stands

| Phase | Status | What exists now |
|---|---|---|
| 0 Audit and backup | Done | `backup/app_v3_phase1_20261122/` (39 files including `groundwater.db`). Baseline: 180/180 and 23/23 tests. |
| 1 Audit and improve | Done (reviewed by naveen) | New website, memory, answer styles and lengths. |
| 2 Soil health | Done | 12 Soil Health Card parameters explained; upload (PDF text layer, CSV, Excel) → review → confirm → explanation; ratings from ICAR-CRIDA and TNAU charts; no overall score. |
| 3 Soil profile and land | Done, waiting for data | Soil Type and Profile, Land Intelligence (15-section Land Condition Report) and Land Degradation pages. Place-level soil and land values say "Not available in the current dataset" until NBSS&LUP / Bhuvan data is obtained. |
| 4 Crop and irrigation | Done, waiting for data | Crop Advisor (FAO salt tolerance and water need, SKNAU Zone II-A crop list, comparison table, ECe salinity check). Field suitability shows "Insufficient data". Irrigation Advisor (methods, irrigation-water checker, no schedules). |
| 5 Groundwater quality | Done, waiting for data | Groundwater Quality page keeps category, level, chemistry, drinking and irrigation apart; water-test checker against IS 10500:2012 and CGWB 2024; importer for CGWB station files (`import_dataset.py`). No station data is imported yet. |
| 6 Geographic explorer | Done (tables) | State → district → unit tables and charts. Draws official GeoJSON boundaries only if they are placed in `data/geo/`; none are supplied, so no map is drawn. |
| 7 Reports and voice | Done | Six report types (Groundwater, Soil Health, Land Condition, Crop Suitability, Irrigation, Complete) as Markdown and English PDF, plus CSV tables. Voice unchanged from Phase 1 (browser speech). |
| 8 QA | Done in the build environment; device checks open | 180 + 23 + 190 tests pass; database hash unchanged; all 17 pages open without errors in headless Chrome. Windows run, real microphone/speaker and native-speaker review need naveen (see `KNOWN_LIMITATIONS.md`). |

## Precise point to continue from

1. naveen downloads CGWB groundwater-quality files to `data/raw/groundwater_quality/` and runs
   `python import_dataset.py groundwater_quality <file> --source CGWB_GWQ_DATA` (dry run), then with `--commit`.
2. naveen sends the NBSS&LUP access request (`DATA_ACCESS_REQUESTS.md`). When layers arrive, add a source row to
   `data/reference/source_catalog.csv`, rebuild with `python build_knowledge_db.py`, then import with
   `import_dataset.py soil_map_units|soil_properties|land_degradation_records|slope_records`.
3. Native speakers review `templates_kn.py` (Marathi, Punjabi, Rajasthani frames) and record corrections in
   `docs/language_review_template.csv`.
4. An agronomist reviews `data/reference/guidance.csv` and `parameter_info.csv` (all rows marked "pending expert review").

## Files that hold the 3.0 work

`knowledge.py`, `knowledge_answer.py`, `templates_kn.py`, `soil_card.py`, `soil_interpret.py`, `water_quality.py`,
`report_builders.py`, `reports_pdf.py`, `import_dataset.py`, `build_knowledge_db.py`, `ui_pages_v3.py`,
`ui_text_v3.py`, `data/reference/*.csv`, `data/knowledge.db`, `data/observations.db` (empty), `test_v3_domains.py`.

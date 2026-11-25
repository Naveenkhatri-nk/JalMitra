# Groundwater accuracy: engine output vs independent SQL (2026-11-23)

Read-only SQL written in eval/gw_accuracy.py (not database.py / retrieval.py). Numbers compared exactly.

| check | passed | checked | notes |
|---|---|---|---|
| assessment units (answer_places numeric) | 6762 | 6762 | 302 units with figures (Rajasthan), the rest category-only: category checked and no figure may appear |
| typed questions, 6 languages (stage of extraction, uniquely named Rajasthan blocks) | 60 | 60 | 0 not resolved to one place (asked to clarify / not found) |
| districts + states (category counts, NC stage) | 745 | 745 | |
| district comparisons (random pairs) | 50 | 50 | |

Assessment years in groundwater.db: 2025 — historical comparisons cannot be answered from it; JalMitra says so instead of guessing. Monitoring data collected by another work thread (data/monitoring/) is not integrated and was not used.

Mismatches: 0 (eval/gw_accuracy_mismatches_2026-11-23.csv).

Run time 7 s.
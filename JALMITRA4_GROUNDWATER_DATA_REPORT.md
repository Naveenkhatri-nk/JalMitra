# JalMitra 4.0: groundwater data expansion, inventory and integration report

_Run 23–24 November 2026. Numbers below are counted by the scripts in `ingest/`. The full generated reports are in
`data/monitoring/reports/` (regenerate with `python ingest/generate_reports.py`)._

## 1. What was added

| Item | Where | Size |
|---|---|---|
| Original India-WRIS API pages (gzip JSON, unchanged) | `data/monitoring/raw/indiawris_gwl/` | 32,406 files, 127 MB |
| India-WRIS district and agency master lists | `data/monitoring/raw/indiawris_masters/` | small |
| CGWB publication pages (catalogue source) | `data/monitoring/raw/cgwb_publication_pages/` | 1,859 pages |
| CGWB publications (PDF, byte-for-byte as served) | `data/monitoring/raw/cgwb_publications/` | 149 files, about 980 MB |
| Catalogue of every CGWB publication | `data/monitoring/catalog/cgwb_publications_catalog.csv` | 1,859 rows |
| Download logs (every request, every window, SHA256) | `data/monitoring/logs/` | |
| Historical GWRA block categories | `data/monitoring/extracted/gwra_category_history.csv` | 40,996 rows |
| **Monitoring database** | `data/groundwater_monitoring.db` | about 950 MB |
| Reports | `data/monitoring/reports/` | see section 6 |
| Scripts | `ingest/` | see section 7 |
| Read-only query module | `monitoring_retrieval.py` | |
| Tests | `test_monitoring.py` | 45 tests |

`data/groundwater.db` was never opened for writing. SHA256 before and after every step:
`9eeaee1533b478c1e649b86a56b56f4415e5255e0a3311e37a466f20bdeaa46a`.

## 2. Sources and licences

| Source | Publisher | Access | Licence / terms |
|---|---|---|---|
| India-WRIS Ground Water Level API (`/Dataset/Ground Water Level`) | National Water Informatics Centre, Ministry of Jal Shakti; data by CGWB and Ground Water Department, Rajasthan | Public API, no key (https://indiawris.gov.in/swagger-ui/index.html) | India-WRIS copyright policy: free reproduction in any format, accurately, not misleading, source acknowledged |
| CGWB Publications and Media Warehouse | Central Ground Water Board | Public download, no login (https://cgwb.gov.in/cgwbpnm/public/publications) | Government publications, free download, source acknowledged. The CGWB terms page returned HTTP 500 on 23 Nov 2026; re-check when it works |

## 3. Monitoring database contents (`data/groundwater_monitoring.db`)

| Table | Rows | What it holds |
|---|---|---|
| stations | 46,371 | Well metadata (agency, code, district, block, village, coordinates, well type and depth, aquifer), coordinate flags, sign convention |
| observations | 1,874,756 (1,828,805 usable) | Manual water-level measurements; `value_raw` exactly as published, `depth_mbgl` only where the sign convention is known |
| telemetry_daily | 2,651,453 station-days | Telemetric (DWLR) readings summarised per station and day (12.0 million readings) |
| station_season | | One median depth per station, year and season (usable manual only) |
| district_season_summary | | District statistics per year and season |
| gwra_category_history | 40,996 | Block categories for GWRA 2017, 2020, 2022, 2023, 2024, 2025 |
| publications | 1,859 | CGWB catalogue, download status, SHA256 |
| raw_files, download_windows | | Provenance: every raw page with SHA256, every API window with status |
| validation_issues, duplicates, rules, sources, district_name_map, meta | | Quality and lineage |

Coverage (from `GEOGRAPHIC_COVERAGE.md` and `HISTORICAL_COVERAGE.md`):
- **Rajasthan, CGWB:** 2,418 stations, 89,976 usable manual measurements, 1970–2024 (53 years with data), 339,251 telemetry station-days.
- **Rajasthan, Ground Water Department:** 9,984 stations, 285,752 usable manual measurements, 1999–2024 (19 years), 237,840 telemetry station-days.
- **National, CGWB:** 27 states and UTs, 732 districts; most states 1970–2023/2025.
- **No CGWB level data on India-WRIS:** Manipur, Mizoram, Sikkim, Andaman & Nicobar, Dadra & Nagar Haveli and Daman & Diu. GWRA districts of Jammu & Kashmir, Andaman & Nicobar and DNH&DD are not matched to any station.

GWRA category history: every printed serial number was read for all six years (2017: 6,881; 2020: 6,965; 2022: 7,089;
2023: 6,553; 2024: 6,746; 2025: 6,762 units), with 0 problem rows. The 2025 extract agrees with `groundwater.db` for all
6,762 units. 211 rows needed a documented layout repair (district words in the state column, category fused with the
unit name); each is flagged in `quality_flag`.

## 4. Validation (rules R01–R16, listed in the `rules` table and `DATA_DICTIONARY.md`)

- Depth below ground: 1,706,955 measurements as published by CGWB (positive metres below ground); 145,147 from series
  whose sign is negative for at least 95% of readings (sign inferred, labelled `sign_inferred_negative_below_ground`);
  1,093 inferred positive; 21,561 with no usable depth.
- Not usable (kept, flagged): deeper than the well (9,981), no-data codes such as -999 (9,494), possible dry well
  (7,982), conflicting duplicates (11,439 rows), ambiguous sign, future or pre-1950 dates, implausible depth > 300 m.
- Stations with ambiguous sign conventions: CGWB 226, Rajasthan GW 1,154. They get no derived depth.
- 145,566 Rajasthan GW rows are labelled "Manual" with a GPRS data-type code; kept as usable and flagged
  `mode_label_mismatch` for transparency.
- 70,519 duplicate groups: identical copies kept once; conflicting values kept (one row per value) and excluded.
- All 10 database integrity checks pass (`DATABASE_INTEGRITY.md`).

## 5. Integration and historical comparison

`monitoring_retrieval.py` is a read-only module (query_only, SQLite authorizer, parameterised SQL) shaped like
`retrieval.execute()`:

| Function | Answer |
|---|---|
| `coverage()` | stations, usable measurements and years per state and agency |
| `district_history(state, district, season)` | year-by-year district median, P10–P90 |
| `compare_years(state, district, a, b, season)` | **paired**: same wells in both years; fewer than 3 pairs → `insufficient_data`, no number |
| `decadal_change(state, district, year, season)` | each well vs its own previous-ten-year mean (CGWB style) |
| `telemetry_summary(...)` | monthly telemetry, kept apart from manual data |
| `category_history(state, district, unit)` | block category 2017–2025, follows Rural/Urban renames only when unambiguous |
| `execute(req)` | intents `gwl_level`, `gwl_history`, `gwl_compare`, `gwl_decadal`, `gwl_stations` |

Examples on the real database:
- Jaipur, pre-monsoon 2015 vs 2024: 115 wells measured in both years; median change +1.4 m (deeper); 64 deeper,
  50 shallower.
- Jaipur 2024 vs each well's 2014–2023 mean: 123 wells, median change about 0 m.
- Jodhpur post-monsoon 2010 vs 2020: no well measured in both years → `insufficient_data` (no number given).
- Sanganer (Jaipur): Over-exploited in every assessment 2017–2025 (published as SANGANER, then Sanganer_Rural).

**Not yet wired into the chat.** The chat path (intent parser, answer checker, UI) is being changed by the AI-chat
thread, so this work stays additive: no existing file was edited. The hook is `monitoring_retrieval.execute()`; the
chat thread can route water-level and history questions to it.

## 6. Tests

| Suite | Result |
|---|---|
| test_local_engine.py | 180/180 (intent, location, DB, language 100%; groundwater.db unchanged; 0 network) |
| test_v3.py | 23/23 |
| test_v3_domains.py | 190/190 |
| test_app_info.py | 175/175 |
| test_conversation.py | 435/435 |
| **Existing total** | **1,003 / 1,003** |
| test_monitoring.py (new) | 45/45 pass on the PC against the real database: ingest rules, duplicates, coordinates, sign handling, paired comparisons, read-only, offline, extraction checks, real-DB integrity |

## 7. Reproduce

```
python ingest/download_cgwb_publications.py                      # catalogue + PDFs (minutes)
python ingest/download_indiawris_gwl.py --scope rajasthan        # about 2 hours
python ingest/download_indiawris_gwl.py --scope national         # about 16 hours
python ingest/run_pipeline.py                                    # extract, build, reports, tests (about 10 minutes)
```
`ingest/run_downloads.ps1` runs the three downloads in order; `ingest/run_pipeline_awake.py` keeps Windows awake only
while the pipeline runs. Every script resumes where it stopped and never overwrites an original file.

## 8. Could not be accessed or not used

See `data/monitoring/reports/INACCESSIBLE_DATASETS.md`: INGRES (site would not load), data.gov.in API (needs a
personal API key; optional), CGWB WIMS (authorised users only), India-WRIS groundwater quality (no public endpoint),
state ground-water agencies other than Rajasthan (not downloaded in this run). 541 CGWB publication ids returned HTTP 500
and are listed in `logs/cgwb_catalogue_errors.csv`.

## 9. Known limitations

- Telemetry sign is inferred per station; India-WRIS does not document it.
- Year-to-year district medians use different wells each year; use `compare_years` (paired) for change.
- Station district names come from India-WRIS and include post-2023 Rajasthan districts; 58 district names appear in
  Rajasthan CGWB station records against 33 GWRA districts. Unmatched names are listed in `missing_district_matches.csv`.
- Year books, aquifer-mapping (NAQUIM) reports and quality reports are downloaded and catalogued but their tables are
  not yet extracted.
- Scratch databases from interrupted builds (about 6 GB) remain in `data/monitoring/scratch/` and can be removed by hand.

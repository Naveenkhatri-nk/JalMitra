-- Final schema of data/groundwater.db as built by build_database.py

CREATE TABLE data_sources (
    source_id          TEXT PRIMARY KEY,
    file_name          TEXT NOT NULL,
    sha256             TEXT NOT NULL,
    pdf_pages          INTEGER,
    source_url         TEXT NOT NULL,
    title              TEXT NOT NULL,
    publisher          TEXT,
    publication_date   TEXT,
    publication_year   TEXT,
    assessment_year    TEXT NOT NULL,
    role               TEXT,
    original_units     TEXT,
    notes              TEXT,
    read_note          TEXT
);

CREATE TABLE groundwater_assessment (
    record_id                          TEXT PRIMARY KEY,
    state                              TEXT NOT NULL,     -- standard spelling (National Compilation)
    state_as_published                 TEXT NOT NULL,
    district                           TEXT NOT NULL,
    assessment_unit                    TEXT NOT NULL,
    assessment_unit_type               TEXT,
    assessment_unit_type_source        TEXT,
    year                               TEXT NOT NULL,     -- assessment year (GWRA)
    publication_year                   TEXT,              -- of the values source, if known
    annual_recharge_original           REAL,
    annual_recharge_original_unit      TEXT,
    annual_recharge_bcm                REAL,
    extractable_resource_original      REAL,
    extractable_resource_original_unit TEXT,
    extractable_resource_bcm           REAL,
    total_extraction_original          REAL,
    total_extraction_original_unit     TEXT,
    total_extraction_bcm               REAL,
    stage_of_extraction_pct            REAL,
    category                           TEXT NOT NULL CHECK (category IN
                                         ('Safe','Semi-critical','Critical','Over-exploited','Saline')),
    category_as_printed                TEXT NOT NULL,
    validation_category                TEXT,              -- from stage (70/90/100%), never replaces category
    category_status                    TEXT NOT NULL,     -- see build_database.py
    source_id                          TEXT NOT NULL REFERENCES data_sources(source_id),
    source_page                        INTEGER NOT NULL,
    source_serial                      TEXT,
    values_source_id                   TEXT REFERENCES data_sources(source_id),
    values_source_page                 INTEGER,
    values_source_table                TEXT,
    values_source_unit_name            TEXT,              -- name exactly as printed in the values source
    category_in_values_source          TEXT,
    quality_flag                       TEXT,
    source_note                        TEXT,
    data_completeness                  TEXT NOT NULL,
    UNIQUE (state, district, assessment_unit, year)
);

CREATE TABLE category_conflicts (
    conflict_id      TEXT NOT NULL,
    record_id        TEXT NOT NULL REFERENCES groundwater_assessment(record_id),
    state            TEXT, district TEXT, assessment_unit TEXT,
    source_id        TEXT NOT NULL REFERENCES data_sources(source_id),
    source_page      TEXT,
    observation      TEXT NOT NULL
);

CREATE TABLE national_state_summary (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    state TEXT NOT NULL, year TEXT NOT NULL, printed_serial TEXT,
    original_unit TEXT NOT NULL,
    recharge_rainfall_monsoon REAL, recharge_other_monsoon REAL,
    recharge_rainfall_nonmonsoon REAL, recharge_other_nonmonsoon REAL,
    annual_recharge REAL, natural_discharge REAL, extractable_resource REAL,
    irrigation_use REAL, industrial_use REAL, domestic_use REAL, total_extraction REAL,
    domestic_allocation_2030 REAL, net_availability_future REAL, stage_of_extraction_pct REAL,
    annual_recharge_bcm REAL, extractable_resource_bcm REAL, total_extraction_bcm REAL,
    source_id TEXT NOT NULL REFERENCES data_sources(source_id), source_page INTEGER NOT NULL,
    quality_flag TEXT
);

CREATE TABLE sqlite_sequence(name,seq);

CREATE TABLE national_district_summary (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    state TEXT NOT NULL, district TEXT NOT NULL, year TEXT NOT NULL, printed_serial TEXT,
    original_unit TEXT NOT NULL,
    recharge_rainfall_monsoon REAL, recharge_other_monsoon REAL,
    recharge_rainfall_nonmonsoon REAL, recharge_other_nonmonsoon REAL,
    annual_recharge REAL, natural_discharge REAL, extractable_resource REAL,
    irrigation_use REAL, industrial_use REAL, domestic_use REAL, total_extraction REAL,
    domestic_allocation_2030 REAL, net_availability_future REAL, stage_of_extraction_pct REAL,
    annual_recharge_bcm REAL, extractable_resource_bcm REAL, total_extraction_bcm REAL,
    source_id TEXT NOT NULL REFERENCES data_sources(source_id), source_page INTEGER NOT NULL,
    quality_flag TEXT
);

CREATE TABLE national_unit_counts (
    state TEXT PRIMARY KEY, total_units INTEGER, safe INTEGER, semi_critical INTEGER,
    critical INTEGER, over_exploited INTEGER, saline INTEGER,
    source_id TEXT NOT NULL REFERENCES data_sources(source_id), source_page INTEGER NOT NULL
);

CREATE TABLE quality_report     (check_id TEXT, scope TEXT, "check" TEXT, result TEXT, details TEXT);

CREATE TABLE duplicate_records  (duplicate_type TEXT, group_key TEXT, source_id TEXT, record_ref TEXT,
                                 page TEXT, category TEXT, resolution TEXT);

CREATE TABLE import_errors      (source_id TEXT, record_ref TEXT, page TEXT, issue TEXT, action TEXT);

CREATE INDEX idx_ga_state    ON groundwater_assessment(state);

CREATE INDEX idx_ga_district ON groundwater_assessment(district);

CREATE INDEX idx_ga_unit     ON groundwater_assessment(assessment_unit);

CREATE INDEX idx_ga_category ON groundwater_assessment(category);

-- JalMitra proposed production schema (NOT yet created)

CREATE TABLE data_sources (
    source_id          TEXT PRIMARY KEY,          -- AI2025, RJ2025, NC2025
    file_name          TEXT NOT NULL,
    sha256             TEXT NOT NULL,
    source_url         TEXT NOT NULL,
    title              TEXT NOT NULL,
    publisher          TEXT,
    publication_date   TEXT,
    publication_year   TEXT,
    assessment_year    TEXT NOT NULL,
    role               TEXT,
    original_units     TEXT,
    notes              TEXT,
    imported_at        TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE groundwater (
    record_id                     TEXT PRIMARY KEY,   -- AI2025-00001
    state                         TEXT NOT NULL,      -- as published
    state_standard                TEXT,               -- National Compilation spelling
    district                      TEXT NOT NULL,
    assessment_unit               TEXT NOT NULL,      -- block / taluk / mandal / tehsil ...
    assessment_unit_type          TEXT,               -- NULL when not stated
    assessment_unit_type_source   TEXT,
    assessment_year               TEXT NOT NULL,      -- GWRA year, e.g. 2025
    publication_year              TEXT,               -- separate from assessment year
    category                      TEXT NOT NULL CHECK (category IN
                                    ('Safe','Semi-critical','Critical','Over-exploited','Saline')),
    category_raw                  TEXT NOT NULL,      -- exactly as published
    annual_recharge_ham           REAL,               -- original value, NULL if not published
    extractable_resource_ham      REAL,
    total_extraction_ham          REAL,
    stage_of_extraction_pct       REAL,
    annual_recharge_bcm           REAL,               -- = ham / 100000
    extractable_resource_bcm      REAL,
    total_extraction_bcm          REAL,
    original_volume_unit          TEXT,
    category_source_id            TEXT NOT NULL REFERENCES data_sources(source_id),
    category_source_page          INTEGER NOT NULL,
    category_source_serial        TEXT,
    values_source_id              TEXT REFERENCES data_sources(source_id),
    values_source_page            INTEGER,
    values_source_table           TEXT,
    category_in_values_source     TEXT,
    quality_flag                  TEXT,               -- ; separated codes
    source_note                   TEXT,
    UNIQUE (state, district, assessment_unit, assessment_year)
);

-- State and district summaries from the National Compilation are kept in
-- separate tables so they can never be mixed with assessment-unit rows.
CREATE TABLE national_summary (
    id                              INTEGER PRIMARY KEY AUTOINCREMENT,
    level                           TEXT NOT NULL CHECK (level IN ('state','district')),
    state                           TEXT NOT NULL,
    district                        TEXT,             -- NULL for state rows
    assessment_year                 TEXT NOT NULL,
    original_unit                   TEXT NOT NULL,    -- 'bcm' (Annexure I) or 'ham' (Annexure II)
    annual_recharge                 REAL,             -- in original_unit
    extractable_resource            REAL,
    total_extraction                REAL,
    stage_of_extraction_pct         REAL,
    annual_recharge_bcm             REAL,
    extractable_resource_bcm        REAL,
    total_extraction_bcm            REAL,
    source_id                       TEXT NOT NULL REFERENCES data_sources(source_id),
    source_page                     INTEGER NOT NULL,
    quality_flag                    TEXT,
    source_note                     TEXT
);

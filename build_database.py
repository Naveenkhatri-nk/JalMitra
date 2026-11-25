"""
build_database.py - Create data/groundwater.db from the reviewed preview files.

Run AFTER build_dataset.py, from the JalMitra folder:
    python build_dataset.py      # PDFs -> reviewed CSV files
    python build_database.py     # CSV files -> data/groundwater.db
    python validate_database.py  # checks -> data/validation_report.csv

Rules followed here:
  * One row per assessment unit and year in groundwater_assessment.
  * National Compilation state and district summaries go in their own tables.
  * Original hectare-metre values are kept with their unit; BCM = ham / 100000.
  * Category-only units keep NULL numbers (never 0).
  * Printed values are never changed. Checks only ADD flags and validation columns.
  * If groundwater.db already exists it is kept as a dated backup, not deleted.
  * Files in data/raw are only read.
"""

import csv
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

HAM_PER_BCM = 100000
YEAR = "2025"

SCHEMA = """
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
"""

NC_FIELDS = ["recharge_rainfall_monsoon", "recharge_other_monsoon", "recharge_rainfall_nonmonsoon",
             "recharge_other_nonmonsoon", "annual_recharge", "natural_discharge", "extractable_resource",
             "irrigation_use", "industrial_use", "domestic_use", "total_extraction",
             "domestic_allocation_2030", "net_availability_future", "stage_of_extraction_pct"]


def fnum(text):
    t = (text or "").strip().replace(",", "")
    if t in ("", "-"):
        return None
    return float(t)


def read(path):
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def validation_category(stage):
    if stage is None:
        return None
    if stage <= 70:
        return "Safe"
    if stage <= 90:
        return "Semi-critical"
    if stage <= 100:
        return "Critical"
    return "Over-exploited"


def build_assessment_row(r):
    flags = [f for f in (r["quality_flag"] or "").split(";") if f]
    notes = [n for n in (r["source_note"] or "").split("; ") if n]
    has_values = bool(r["values_source_id"])

    rec = {
        "record_id": r["record_id"], "state": r["state_standard"] or r["state"],
        "state_as_published": r["state"], "district": r["district"],
        "assessment_unit": r["assessment_unit"], "assessment_unit_type": r["assessment_unit_type"] or None,
        "assessment_unit_type_source": r["assessment_unit_type_source"] or None,
        "year": r["assessment_year"] or YEAR, "publication_year": r["publication_year"] or None,
        "category": r["category"], "category_as_printed": r["category_raw"],
        "source_id": r["category_source_id"], "source_page": int(r["category_source_page"]),
        "source_serial": r["category_source_serial"],
        "values_source_id": r["values_source_id"] or None,
        "values_source_page": int(r["values_source_page"]) if r["values_source_page"] else None,
        "values_source_table": r["values_source_table"] or None,
        "values_source_unit_name": r["values_source_unit_name"] or None,
        "category_in_values_source": r["category_in_values_source"] or None,
    }
    for name in ("annual_recharge", "extractable_resource", "total_extraction"):
        ham = fnum(r[f"{name}_ham"])
        rec[f"{name}_original"] = ham
        rec[f"{name}_original_unit"] = "ham" if ham is not None else None
        rec[f"{name}_bcm"] = ham / HAM_PER_BCM if ham is not None else None
    stage = fnum(r["stage_of_extraction_pct"])
    rec["stage_of_extraction_pct"] = stage

    # validation category: only where a stage is printed and the unit is not saline
    vcat = validation_category(stage) if rec["category"] != "Saline" else None
    rec["validation_category"] = vcat
    status = "not_checked_no_stage"
    if vcat is not None:
        status = "consistent_with_stage" if vcat == rec["category"] else "differs_from_stage"
        if vcat != rec["category"]:
            flags.append("category_stage_mismatch")
            notes.append(f"printed category {rec['category']}; stage {stage:g}% gives {vcat}")
    if "category_conflict_between_sources" in flags:
        status = "conflict_between_sources"

    # stage recalculated from the printed volumes (values kept as printed)
    ext, extr = rec["extractable_resource_original"], rec["total_extraction_original"]
    if stage is not None and ext:
        calc = 100 * extr / ext
        if abs(calc - stage) > 1.5:
            flags.append("stage_calculation_mismatch")

    # saline units printed with zeros: keep zeros, ask for verification
    if has_values and rec["category"] == "Saline" and all(
            rec[f"{n}_original"] == 0 for n in ("annual_recharge", "extractable_resource", "total_extraction")):
        flags.append("measurements_require_verification")
        completeness = "printed_zero_requires_verification"
    elif has_values and all(rec[f"{n}_original"] is not None for n in
                            ("annual_recharge", "extractable_resource", "total_extraction")) and stage is not None:
        completeness = "complete"
    elif has_values:
        completeness = "partial"
    else:
        completeness = "category_only"

    if "matched_by_name_prefix" in flags:
        flags.append("truncated_name_in_values_source")

    # keep every flag from the preview, add new ones, no duplicates
    flags = list(dict.fromkeys(flags))
    rec["category_status"] = status
    rec["quality_flag"] = ";".join(flags) or None
    rec["source_note"] = "; ".join(dict.fromkeys(notes)) or None
    rec["data_completeness"] = completeness
    return rec


def build(data_dir="data"):
    data = Path(data_dir)
    proc = data / "processed"
    db_path = data / "groundwater.db"
    tmp_path = data / "groundwater.db.building"
    if tmp_path.exists():
        tmp_path.unlink()

    conn = sqlite3.connect(tmp_path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA)

    def insert(table, rows):
        if not rows:
            return
        cols = list(rows[0].keys())
        conn.executemany(
            f"INSERT INTO {table} ({', '.join(chr(34) + c + chr(34) for c in cols)}) "
            f"VALUES ({', '.join('?' for _ in cols)})",
            [[row[c] for c in cols] for row in rows])

    with conn:
        insert("data_sources", read(data / "data_sources.csv"))

        assessment = [build_assessment_row(r) for r in read(proc / "groundwater_preview.csv")]
        insert("groundwater_assessment", assessment)
        insert("category_conflicts", read(data / "category_conflicts.csv"))

        for level, fname, table in (("state", "national_state_summary_2025.csv", "national_state_summary"),
                                    ("district", "national_district_summary_2025.csv", "national_district_summary")):
            rows = []
            for r in read(proc / fname):
                flags = []
                rec = {"state": r["name"] if level == "state" else r["state"]}
                if level == "district":
                    rec["district"] = r["name"]
                    if r.get("name_was_wrapped"):
                        flags.append("name_printed_over_several_lines")
                rec.update({"year": YEAR, "printed_serial": r["serial"], "original_unit": r["unit"]})
                for f in NC_FIELDS:
                    if (r[f] or "").strip() == "-":
                        flags.append(f"{f}_printed_as_dash")
                    rec[f] = fnum(r[f])
                for f in ("annual_recharge", "extractable_resource", "total_extraction"):
                    v = rec[f]
                    rec[f + "_bcm"] = None if v is None else (v if r["unit"] == "bcm" else v / HAM_PER_BCM)
                rec.update({"source_id": "NC2025", "source_page": int(r["page"]),
                            "quality_flag": ";".join(flags) or None})
                rows.append(rec)
            insert(table, rows)

        counts = []
        for r in read(proc / "national_unit_counts_2025.csv"):
            counts.append({"state": r["state"], "total_units": int(r["total_units"]),
                           "safe": int(r["Safe"]), "semi_critical": int(r["Semi-critical"]),
                           "critical": int(r["Critical"]), "over_exploited": int(r["Over-exploited"]),
                           "saline": int(r["Saline"]), "source_id": "NC2025", "source_page": int(r["source_page"])})
        insert("national_unit_counts", counts)

        insert("quality_report", read(data / "quality_report.csv"))
        insert("duplicate_records", read(data / "duplicate_records.csv"))
        insert("import_errors", read(data / "import_errors.csv"))
    conn.close()

    if db_path.exists():
        backup = data / f"groundwater_backup_{datetime.now():%Y%m%d_%H%M%S}.db"
        shutil.move(db_path, backup)
        print("Previous database kept as:", backup)
    tmp_path.replace(db_path)

    # export the final table so the CSV matches the database exactly
    conn = sqlite3.connect(db_path)
    cur = conn.execute("SELECT * FROM groundwater_assessment ORDER BY record_id")
    cols = [d[0] for d in cur.description]
    with open(data / "groundwater.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for row in cur:
            w.writerow(["" if v is None else v for v in row])
    conn.close()
    print(f"Created {db_path} with {len(assessment)} assessment units.")
    return db_path


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else "data")

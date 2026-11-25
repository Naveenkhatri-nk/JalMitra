"""
build_knowledge_db.py - Build JalMitra's reference database from reviewed CSV files.

    python build_knowledge_db.py            # rebuild data/knowledge.db from data/reference/*.csv
    python build_knowledge_db.py --check    # only validate the CSV files

data/knowledge.db holds REFERENCE values only (rating ranges, drinking-water limits,
crop tables, zone descriptions, general text). Every row names its source, table and
page. Nothing here is a measurement of any farm, block or well.

It also creates data/observations.db (once, never overwritten) with empty tables for
measured or mapped data that naveen may import later with import_dataset.py
(groundwater quality, water levels, soil samples, land records). groundwater.db is
never opened by this script.
"""

import csv
import os
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REF = ROOT / "data" / "reference"
KNOWLEDGE_DB = ROOT / "data" / "knowledge.db"
OBSERVATIONS_DB = ROOT / "data" / "observations.db"

TABLES = {
    "source_catalog": "source_catalog.csv",
    "reference_ranges": "reference_ranges.csv",
    "irrigation_ec_limits": "irrigation_ec_limits.csv",
    "parameter_info": "parameter_info.csv",
    "guidance": "guidance.csv",
    "crops": "crops.csv",
    "crop_salt_tolerance": "crop_salt_tolerance.csv",
    "crop_water_needs": "crop_water_needs.csv",
    "agro_zones": "agro_zones.csv",
    "zone_districts": "zone_districts.csv",
    "zone_crops": "zone_crops.csv",
}
NUMERIC = {
    "reference_ranges": ["lower", "upper", "lower_inclusive", "upper_inclusive"],
    "irrigation_ec_limits": ["clay_min_pct", "clay_max_pct", "ec_upper_safe_limit_uS_cm"],
    "crop_salt_tolerance": ["ece_threshold_dS_m", "slope_pct_per_dS_m"],
    "crop_water_needs": ["water_need_min_mm", "water_need_max_mm"],
}
ACCESS_CLASSES = {"publicly_downloadable", "free_web_page", "free_web_service", "permission_required", "paid",
                  "manual_upload_required", "not_currently_accessible", "project_text"}

# Columns every observation row carries (full provenance, original and normalised value).
PROVENANCE = """
    record_id INTEGER PRIMARY KEY,
    import_id INTEGER,
    source_id TEXT NOT NULL,
    source_url TEXT,
    file_name TEXT,
    page TEXT,
    station_or_location TEXT,
    state TEXT, district TEXT, block TEXT, village TEXT,
    latitude REAL, longitude REAL,
    sample_date TEXT, measurement_date TEXT, publication_year TEXT,
    parameter TEXT NOT NULL,
    original_value TEXT, original_unit TEXT,
    normalised_value REAL, normalised_unit TEXT,
    sample_depth TEXT, resolution TEXT,
    data_origin TEXT NOT NULL CHECK (data_origin IN ('lab_tested','field_measured','survey_derived',
                                                     'map_derived','estimated_interpolated')),
    lab_reference TEXT,
    quality_flag TEXT, confidence TEXT, licence TEXT
"""
OBSERVATION_TABLES = ["groundwater_quality", "groundwater_levels", "soil_samples", "soil_test_results",
                      "soil_map_units", "soil_properties", "land_use_records", "land_capability_records",
                      "land_degradation_records", "slope_records"]


def read(name):
    with open(REF / name, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def validate():
    """Return a list of problems (empty = all good)."""
    problems = []
    data = {t: read(f) for t, f in TABLES.items()}
    ids = {r["source_id"] for r in data["source_catalog"]}
    for r in data["source_catalog"]:
        if r["access_class"] not in ACCESS_CLASSES:
            problems.append(f"source {r['source_id']}: unknown access_class {r['access_class']}")
    for table, rows in data.items():
        for i, r in enumerate(rows, 2):
            if "source_id" in r and table != "source_catalog" and r["source_id"] not in ids:
                problems.append(f"{table} line {i}: unknown source_id {r['source_id']}")
            for col in NUMERIC.get(table, []):
                if r.get(col, "") != "":
                    try:
                        float(r[col])
                    except ValueError:
                        problems.append(f"{table} line {i}: {col} is not a number: {r[col]!r}")
    for i, r in enumerate(data["reference_ranges"], 2):
        lo, hi = r["lower"], r["upper"]
        if lo == "" and hi == "":
            problems.append(f"reference_ranges line {i}: no bounds")
        if lo != "" and hi != "" and float(lo) > float(hi):
            problems.append(f"reference_ranges line {i}: lower > upper")
    salt = {r["fao_salt_label"] for r in data["crop_salt_tolerance"]}
    water = {r["fao_water_label"] for r in data["crop_water_needs"]}
    crop_ids = {r["crop_id"] for r in data["crops"]}
    for r in data["crops"]:
        if r["fao_salt_label"] and r["fao_salt_label"] not in salt:
            problems.append(f"crop {r['crop_id']}: salt label {r['fao_salt_label']} not in table")
        if r["fao_water_label"] and r["fao_water_label"] not in water:
            problems.append(f"crop {r['crop_id']}: water label {r['fao_water_label']} not in table")
    for r in data["zone_crops"]:
        if r["crop_id"] not in crop_ids:
            problems.append(f"zone_crops: unknown crop {r['crop_id']}")
    return problems


def build_knowledge():
    tmp = KNOWLEDGE_DB.with_suffix(".tmp")
    if tmp.exists():
        tmp.unlink()
    con = sqlite3.connect(tmp)
    for table, name in TABLES.items():
        rows = read(name)
        cols = list(rows[0].keys())
        num = set(NUMERIC.get(table, []))
        con.execute(f"CREATE TABLE {table} ({', '.join(c + (' REAL' if c in num else ' TEXT') for c in cols)})")
        con.executemany(f"INSERT INTO {table} VALUES ({', '.join('?' * len(cols))})",
                        [[(float(r[c]) if (c in num and r[c] != "") else (None if r[c] == "" else r[c]))
                          for c in cols] for r in rows])
    con.execute("CREATE TABLE build_info (key TEXT, value TEXT)")
    con.execute("INSERT INTO build_info VALUES ('built_from', 'data/reference/*.csv')")
    con.commit()
    con.close()
    os.replace(tmp, KNOWLEDGE_DB)


def init_observations():
    """Create the empty observation tables once. An existing file is never touched."""
    if OBSERVATIONS_DB.exists():
        return False
    con = sqlite3.connect(OBSERVATIONS_DB)
    for t in OBSERVATION_TABLES:
        con.execute(f"CREATE TABLE {t} ({PROVENANCE})")
        con.execute(f"CREATE INDEX idx_{t}_place ON {t} (state, district, block)")
    con.execute("""CREATE TABLE import_logs (import_id INTEGER PRIMARY KEY, table_name TEXT, file_name TEXT,
                   file_sha256 TEXT, source_id TEXT, rows_read INTEGER, rows_imported INTEGER,
                   rows_rejected INTEGER, imported_at TEXT, notes TEXT)""")
    con.commit()
    con.close()
    return True


def main():
    problems = validate()
    for p in problems:
        print("PROBLEM:", p)
    if problems:
        sys.exit(1)
    print("Reference CSV files: OK")
    if "--check" in sys.argv:
        return
    build_knowledge()
    print(f"Built {KNOWLEDGE_DB.relative_to(ROOT)}")
    if init_observations():
        print(f"Created empty {OBSERVATIONS_DB.relative_to(ROOT)}")


if __name__ == "__main__":
    main()

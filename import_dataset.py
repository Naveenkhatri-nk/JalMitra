"""
import_dataset.py - Import a downloaded official dataset (CSV or Excel) into data/observations.db.

    python import_dataset.py groundwater_quality data/raw/groundwater_quality/GWQ_2023.csv --source CGWB_GWQ_DATA
    python import_dataset.py groundwater_quality FILE --source CGWB_GWQ_DATA --commit

Without --commit nothing is written: the script only reports what it would import (dry run).

Rules
  * groundwater.db is never opened. Original files in data/raw are only read.
  * every row keeps the original value and unit exactly as printed; "BDL", "ND", "-" and blanks are
    stored as text with a quality flag, never as zero
  * coordinates are taken only from the file; nothing is geocoded or guessed
  * the source must already be in data/reference/source_catalog.csv
  * each import is logged in import_logs with the file's sha256

Input shapes
  long : columns parameter, value, unit (+ place / date columns)
  wide : one column per parameter, e.g. "pH", "EC (uS/cm)", "F (mg/L)" (unit read from the header)
Place and date columns are found by name (state, district, block, village, location / station / site,
latitude, longitude, date / sampling date / year). Use --map old=new to rename columns first.
"""

import argparse
import csv
import datetime as dt
import hashlib
import re
import sqlite3
import sys
from pathlib import Path

import build_knowledge_db as bk
import knowledge as kn

PLACE_COLS = {"state": ["state", "state name"], "district": ["district", "district name"],
              "block": ["block", "block name", "tehsil", "taluk", "mandal"], "village": ["village", "village name"],
              "station_or_location": ["location", "station", "site", "well", "well no", "station name", "site name"],
              "latitude": ["latitude", "lat"], "longitude": ["longitude", "long", "lon"],
              "sample_date": ["date", "sampling date", "date of sampling", "sample date"],
              "publication_year": ["year"], "lab_reference": ["lab no", "lab reference", "sample no"]}
PARAM_NAMES = {"ph": "pH", "ec": "EC", "tds": "TDS", "f": "F", "fluoride": "F", "no3": "NO3", "nitrate": "NO3",
               "as": "As", "arsenic": "As", "cl": "Cl", "chloride": "Cl", "fe": "Fe", "iron": "Fe", "th": "TH",
               "total hardness": "TH", "so4": "SO4", "sulphate": "SO4", "u": "U", "uranium": "U", "sar": "SAR",
               "rsc": "RSC", "%na": "NA_PCT", "na%": "NA_PCT", "ca": "Ca", "mg": "Mg", "na": "Na", "k": "K",
               "hco3": "HCO3", "co3": "CO3", "depth to water": "DTW", "dtw": "DTW", "water level": "DTW",
               "water level (mbgl)": "DTW"}
NOT_A_NUMBER = {"bdl": "below_detection_limit", "nd": "not_detected", "-": "blank_in_source", "": "blank_in_source",
                "na": "not_analysed", "n.a.": "not_analysed"}
TABLES = {"groundwater_quality": "lab_tested", "groundwater_levels": "field_measured", "soil_test_results": "lab_tested",
          "soil_properties": "survey_derived", "land_use_records": "map_derived", "land_degradation_records": "map_derived",
          "slope_records": "map_derived", "land_capability_records": "survey_derived", "soil_map_units": "map_derived",
          "soil_samples": "lab_tested"}


def read_rows(path):
    if path.suffix.lower() == ".csv":
        with open(path, newline="", encoding="utf-8-sig") as f:
            return list(csv.DictReader(f))
    if path.suffix.lower() == ".xlsx":
        import openpyxl
        wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
        it = wb.worksheets[0].iter_rows(values_only=True)
        header = [str(h).strip() if h is not None else "" for h in next(it)]
        rows = [{h: ("" if v is None else str(v)) for h, v in zip(header, r)} for r in it]
        wb.close()
        return rows
    raise SystemExit("Only .csv and .xlsx files can be imported. Convert PDF tables to CSV and review them first.")


def _find(cols, names):
    low = {c.lower().strip(): c for c in cols}
    return next((low[n] for n in names if n in low), None)


def _param_of(header):
    h = header.lower().strip()
    unit = re.search(r"\(([^)]+)\)", h)
    base = re.sub(r"\s*\([^)]*\)", "", h).strip()
    pid = PARAM_NAMES.get(base)
    return (pid, unit.group(1) if unit else "") if pid else (None, None)


def convert(rows, table, source_id, file_name, url=""):
    if not rows:
        return [], []
    cols = list(rows[0].keys())
    place = {k: _find(cols, v) for k, v in PLACE_COLS.items()}
    long_form = _find(cols, ["parameter"]) and _find(cols, ["value"])
    out, rejected = [], []
    for i, r in enumerate(rows, 2):
        base = {k: (r.get(c) or "").strip() if c else None for k, c in place.items()}
        for k in ("latitude", "longitude"):
            try:
                base[k] = float(base[k]) if base[k] not in (None, "") else None
            except ValueError:
                base[k] = None
        if long_form:
            items = [(r.get(long_form and _find(cols, ["parameter"])), r.get(_find(cols, ["value"])),
                      r.get(_find(cols, ["unit"]) or "", ""))]
            items = [(PARAM_NAMES.get((p or "").lower().strip(), (p or "").strip()), v, un) for p, v, un in items]
        else:
            items = []
            for c in cols:
                pid, unit = _param_of(c)
                if pid:
                    items.append((pid, r.get(c), unit))
        if not items:
            rejected.append((i, "no parameter columns"))
            continue
        for pid, raw, unit in items:
            raw = "" if raw is None else str(raw).strip()
            flag = NOT_A_NUMBER.get(raw.lower())
            norm = None
            if flag is None:
                try:
                    norm = float(raw.replace(",", ""))
                except ValueError:
                    flag = "non_numeric_value"
            out.append({**base, "source_id": source_id, "source_url": url, "file_name": file_name, "page": "",
                        "parameter": pid, "original_value": raw, "original_unit": unit, "normalised_value": norm,
                        "normalised_unit": kn.norm_unit(unit, pid) if norm is not None else None,
                        "data_origin": TABLES[table], "quality_flag": flag or "", "confidence": "as published",
                        "licence": (kn.source(source_id) or {}).get("licence", "")})
    return out, rejected


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("table", choices=sorted(TABLES))
    ap.add_argument("file")
    ap.add_argument("--source", required=True, help="source_id from data/reference/source_catalog.csv")
    ap.add_argument("--map", action="append", default=[], help="rename a column: old=new")
    ap.add_argument("--commit", action="store_true", help="write to data/observations.db (default: dry run)")
    a = ap.parse_args(argv)
    path = Path(a.file)
    if kn.source(a.source) is None:
        raise SystemExit(f"Unknown source {a.source}: add it to data/reference/source_catalog.csv and rebuild.")
    rows = read_rows(path)
    for m in a.map:
        old, new = m.split("=", 1)
        rows = [{(new if k == old else k): v for k, v in r.items()} for r in rows]
    out, rejected = convert(rows, a.table, a.source, path.name, (kn.source(a.source) or {}).get("url", ""))
    flagged = sum(1 for o in out if o["quality_flag"])
    print(f"{path.name}: {len(rows)} rows read, {len(out)} values, {flagged} flagged (kept as text), "
          f"{len(rejected)} rows rejected")
    for i, why in rejected[:10]:
        print(f"  rejected line {i}: {why}")
    if not a.commit:
        print("Dry run: nothing written. Add --commit to import.")
        return 0
    bk.init_observations()
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    con = sqlite3.connect(bk.OBSERVATIONS_DB)
    try:
        if con.execute("SELECT 1 FROM import_logs WHERE file_sha256=? AND table_name=?", (digest, a.table)).fetchone():
            raise SystemExit("This exact file was already imported into this table (same sha256).")
        cur = con.execute("INSERT INTO import_logs (table_name, file_name, file_sha256, source_id, rows_read, "
                          "rows_imported, rows_rejected, imported_at, notes) VALUES (?,?,?,?,?,?,?,?,?)",
                          (a.table, path.name, digest, a.source, len(rows), len(out), len(rejected),
                           dt.datetime.now().isoformat(timespec="seconds"), "import_dataset.py"))
        imp = cur.lastrowid
        cols = ["import_id"] + list(out[0].keys()) if out else []
        if out:
            con.executemany(f"INSERT INTO {a.table} ({', '.join(cols)}) VALUES ({', '.join('?' * len(cols))})",
                            [[imp] + list(o.values()) for o in out])
        con.commit()
    finally:
        con.close()
    print(f"Imported {len(out)} values into {a.table} (import_id {imp}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())

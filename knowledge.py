"""
knowledge.py - Read-only access to JalMitra's reference database (data/knowledge.db)
and to the (normally empty) observations database (data/observations.db).

Reference values are rating ranges, drinking-water limits, crop tables and zone
descriptions copied from named sources (see data/reference/source_catalog.csv).
They are not measurements of any place. Nothing here writes to any database.
"""

import re
import sqlite3
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parent
KNOWLEDGE_DB = ROOT / "data" / "knowledge.db"
OBSERVATIONS_DB = ROOT / "data" / "observations.db"
NOT_AVAILABLE = "Not available in the current dataset"
SOIL_HEALTH_PARAMETERS = ["N", "P", "K", "S", "Zn", "Fe", "Cu", "Mn", "B", "pH", "EC", "OC"]
DRINKING_PARAMETERS = ["pH", "TDS", "EC", "F", "NO3", "As", "Cl", "Fe", "TH", "SO4", "U"]
IRRIGATION_PARAMETERS = ["EC", "SAR", "RSC", "NA_PCT"]
DATA_ORIGINS = ["lab_tested", "field_measured", "survey_derived", "map_derived", "estimated_interpolated"]


class KnowledgeNotReady(RuntimeError):
    pass


def _ro(path):
    if not path.exists():
        raise KnowledgeNotReady(f"{path.name} is missing: run  python build_knowledge_db.py")
    con = sqlite3.connect(f"file:{path}?mode=ro", uri=True, check_same_thread=False)
    con.row_factory = sqlite3.Row
    return con


@lru_cache(maxsize=1)
def tables():
    """All reference tables in memory (they are small): {table: [dict, ...]}."""
    con = _ro(KNOWLEDGE_DB)
    names = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")]
    out = {n: [dict(r) for r in con.execute(f"SELECT * FROM {n}")] for n in names}  # names come from the DB itself
    con.close()
    return out


def ready():
    try:
        tables()
        return True
    except KnowledgeNotReady:
        return False


# ------------------------------------------------------------------ matching

def _norm(text):
    return " " + re.sub(r"\s+", " ", re.sub(r"[?!.,;:।॥\"'()\[\]{}]", " ", (text or "").lower())).strip() + " "


@lru_cache(maxsize=512)
def _pattern(words):
    alts = sorted({re.escape(w.lower()) for w in words if w}, key=len, reverse=True)
    return re.compile(r"(?<![\wऀ-੿])(?:" + "|".join(alts) + r")(?![\wऀ-੿])") if alts else None


def has_any(text, words):
    p = _pattern(tuple(words))
    return bool(p and p.search(_norm(text) if not text.startswith(" ") else text))


def _aliases(row):
    return tuple(a.strip() for a in (row.get("aliases") or "").split("|") if a.strip())


# ------------------------------------------------------------------ sources

def source(source_id):
    return next((s for s in tables()["source_catalog"] if s["source_id"] == source_id), None)


def sources():
    return list(tables()["source_catalog"])


def cite(source_id, table_ref=None, page=None):
    s = source(source_id) or {"title": source_id, "publisher": ""}
    bits = [s["title"]]
    if s.get("publisher"):
        bits.append(s["publisher"])
    if s.get("document_year"):
        bits.append(str(s["document_year"]))
    if table_ref:
        bits.append(str(table_ref))
    if page and page != "web":
        bits.append(f"p. {page}")
    return ", ".join(bits)


# ------------------------------------------------------------------ units

UNIT_SYNONYMS = {
    "kg/ha": "kg/ha", "kg ha-1": "kg/ha", "kg/hectare": "kg/ha",
    "%": "%", "percent": "%",
    "ppm": "ppm", "mg/kg": "ppm",
    "ds/m": "dS/m", "mmhos/cm": "dS/m", "mmho/cm": "dS/m", "ms/cm": "dS/m",
    "us/cm": "uS/cm", "µs/cm": "uS/cm", "μs/cm": "uS/cm", "micromhos/cm": "uS/cm", "umhos/cm": "uS/cm",
    "mg/l": "mg/L", "mg/litre": "mg/L", "mg/liter": "mg/L",
    "ug/l": "ug/L", "µg/l": "ug/L", "μg/l": "ug/L", "ppb": "ug/L",
    "ph": "pH", "": "",
    "meq/l": "meq/L", "ratio": "ratio",
}
# exact metric conversions only (never P2O5 -> P or K2O -> K)
CONVERSIONS = {("dS/m", "uS/cm"): 1000.0, ("uS/cm", "dS/m"): 0.001, ("mg/L", "ug/L"): 1000.0,
               ("ug/L", "mg/L"): 0.001}


def norm_unit(unit, parameter=None):
    u = (unit or "").strip().lower().replace(" ", "")
    if parameter == "pH" and u in ("", "ph", "-"):
        return "pH"
    if parameter in ("SAR",) and u in ("", "-"):
        return "ratio"
    return UNIT_SYNONYMS.get(u, (unit or "").strip())


# ------------------------------------------------------------------ rating ranges

def _inside(value, r):
    lo, hi = r["lower"], r["upper"]
    if lo is not None and (value < lo or (value == lo and not int(r["lower_inclusive"] or 0))):
        return False
    if hi is not None and (value > hi or (value == hi and not int(r["upper_inclusive"] or 0))):
        return False
    return True


def ranges(domain, parameter):
    return [r for r in tables()["reference_ranges"] if r["domain"] == domain and r["parameter"] == parameter]


def classify(domain, parameter, value, unit):
    """Rate one measured value against every source that has a range for it.

    Returns a list (one entry per source):
      {"source_id", "status": "rated"|"gap"|"unit_mismatch", "class_label", "range_id", "table_ref", "page",
       "note", "unit", "converted_from"}
    Nothing is rated when the unit cannot be matched exactly or by an exact metric conversion.
    """
    out = []
    unit_n = norm_unit(unit, parameter)
    by_source = {}
    for r in ranges(domain, parameter):
        by_source.setdefault(r["source_id"], []).append(r)
    for sid, rows in by_source.items():
        ref_unit = rows[0]["unit"]
        v, converted = value, None
        if unit_n != ref_unit:
            factor = CONVERSIONS.get((unit_n, ref_unit))
            if factor is None:
                out.append({"source_id": sid, "status": "unit_mismatch", "unit": ref_unit, "given_unit": unit,
                            "table_ref": rows[0]["table_ref"], "page": rows[0]["page"]})
                continue
            v, converted = value * factor, f"{value} {unit_n}"
        hit = next((r for r in rows if _inside(v, r)), None)
        if hit is None:
            out.append({"source_id": sid, "status": "gap", "unit": ref_unit, "value": v, "converted_from": converted,
                        "table_ref": rows[0]["table_ref"], "page": rows[0]["page"]})
        else:
            out.append({"source_id": sid, "status": "rated", "class_label": hit["class_label"], "range_id": hit["range_id"],
                        "table_ref": hit["table_ref"], "page": hit["page"], "note": hit["note"] or "",
                        "unit": ref_unit, "value": v, "converted_from": converted})
    return out


def range_table(domain, parameter):
    """Rows for showing a source's published classes (for the Learning Centre and detailed answers)."""
    rows = []
    for r in ranges(domain, parameter):
        lo = "" if r["lower"] is None else (">" if not int(r["lower_inclusive"] or 0) else "≥") + _fmt(r["lower"])
        hi = "" if r["upper"] is None else ("<" if not int(r["upper_inclusive"] or 0) else "≤") + _fmt(r["upper"])
        rows.append({"parameter": parameter, "class": r["class_label"], "range": " and ".join(x for x in (lo, hi) if x),
                     "unit": r["unit"], "source": r["source_id"], "table": r["table_ref"], "page": r["page"],
                     "note": r["note"] or ""})
    return rows


def _fmt(x):
    return ("%g" % x) if isinstance(x, float) else str(x)


def irrigation_ec_limits(clay_pct=None):
    rows = tables()["irrigation_ec_limits"]
    if clay_pct is None:
        return list(rows)
    out = []
    for r in rows:
        lo, hi = r["clay_min_pct"], r["clay_max_pct"]
        if (lo is None or clay_pct > lo or (hi is not None and clay_pct == lo)) and (hi is None or clay_pct <= hi):
            out.append(r)
    return out


# ------------------------------------------------------------------ parameters and guidance

def parameter(pid):
    return next((p for p in tables()["parameter_info"] if p["parameter"] == pid), None)


def find_parameters(text, domain=None):
    """Parameters named in a question, e.g. 'What is EC?' -> ['EC'] (soil and water lists kept apart)."""
    t = _norm(text)
    found = []
    for p in tables()["parameter_info"]:
        if domain and not p["domain"].startswith(domain):
            continue
        own = (p["parameter"].lower(),) if len(p["parameter"]) >= 2 else ()   # never match a bare "s", "k" or "b"
        if has_any(t, _aliases(p) + own):
            found.append(p["parameter"])
    return found


def guidance(kind):
    return [g for g in tables()["guidance"] if g["kind"] == kind]


def find_guidance(text, kind=None):
    t = _norm(text)
    return [g for g in tables()["guidance"] if (kind is None or g["kind"] == kind) and _aliases(g)
            and has_any(t, _aliases(g))]


def text_of(row, field, lang):
    """English or Hindi text of a row ('title' or 'text' / 'name' or 'what')."""
    use = "hi" if lang in ("hi", "mr", "raj") else "en"
    return row.get(f"{field}_{use}") or row.get(f"{field}_en") or ""


# ------------------------------------------------------------------ crops and zones

def crops():
    return list(tables()["crops"])


def crop(crop_id):
    return next((c for c in tables()["crops"] if c["crop_id"] == crop_id), None)


def find_crops(text):
    t = _norm(text)
    out = [c["crop_id"] for c in tables()["crops"] if has_any(t, _aliases(c))]
    # "pearl millet" also contains "millet"; "moth bean" contains "moth": keep the order of the crop table
    return out


def crop_facts(crop_id):
    c = crop(crop_id)
    if c is None:
        return None
    salt = next((r for r in tables()["crop_salt_tolerance"] if c["fao_salt_label"] and
                 r["fao_salt_label"] == c["fao_salt_label"]), None)
    water = next((r for r in tables()["crop_water_needs"] if c["fao_water_label"] and
                  r["fao_water_label"] == c["fao_water_label"]), None)
    zones = [z for z in tables()["zone_crops"] if z["crop_id"] == crop_id]
    return {"crop": c, "salt": salt, "water": water, "zones": zones}


def zone_for(state, district):
    if not state or not district:
        return None
    hit = next((z for z in tables()["zone_districts"] if z["state"].lower() == state.lower()
                and z["district"].upper() == district.upper()), None)
    if hit is None:
        return None
    zone = next(z for z in tables()["agro_zones"] if z["zone_id"] == hit["zone_id"])
    crops_listed = [z for z in tables()["zone_crops"] if z["zone_id"] == hit["zone_id"]]
    return {"zone": zone, "coverage": hit["coverage"], "crops": crops_listed}


def water_needs_sorted():
    return sorted(tables()["crop_water_needs"], key=lambda r: (r["water_need_min_mm"], r["water_need_max_mm"]))


# ------------------------------------------------------------------ observations (imported data; empty until naveen imports)

OBS_TABLES = ["groundwater_quality", "groundwater_levels", "soil_samples", "soil_test_results", "soil_map_units",
              "soil_properties", "land_use_records", "land_capability_records", "land_degradation_records",
              "slope_records"]


def observations(table, state=None, district=None, block=None, limit=500):
    """Imported rows for a place (read-only, parameterised). [] when nothing has been imported."""
    if table not in OBS_TABLES or not OBSERVATIONS_DB.exists():
        return []
    sql, args = f"SELECT * FROM {table} WHERE 1=1", []
    for col, val in (("state", state), ("district", district), ("block", block)):
        if val:
            sql += f" AND upper({col}) = upper(?)"
            args.append(val)
    sql += " LIMIT ?"
    args.append(int(limit))
    con = _ro(OBSERVATIONS_DB)
    try:
        return [dict(r) for r in con.execute(sql, args)]
    finally:
        con.close()


def observation_counts():
    if not OBSERVATIONS_DB.exists():
        return {t: 0 for t in OBS_TABLES}
    con = _ro(OBSERVATIONS_DB)
    try:
        return {t: con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in OBS_TABLES}
    finally:
        con.close()


def import_logs():
    if not OBSERVATIONS_DB.exists():
        return []
    con = _ro(OBSERVATIONS_DB)
    try:
        return [dict(r) for r in con.execute("SELECT * FROM import_logs ORDER BY import_id DESC")]
    finally:
        con.close()

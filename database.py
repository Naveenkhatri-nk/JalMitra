"""
database.py - Read-only access to data/groundwater.db for JalMitra.

The database is built by build_dataset.py + build_database.py and is NEVER
changed by the app. Every connection here is read-only:
  1. the file is opened with mode=ro,
  2. PRAGMA query_only is switched on,
  3. an SQLite authorizer allows only reading the known tables.

Every query is a fixed SQL text written in this file, with values passed as
parameters (?). No language model writes or runs SQL (JalMitra 2.0 has no
language model at all).

Speed (JalMitra 2.0): one read-only connection is opened per database file
and reused (guarded by a lock), and small tables that never change while the
app runs (sources, National Compilation totals, the name index) are cached.

Tables used (see data/processed/database_schema.sql):
  groundwater_assessment     one row per assessment unit and year
  data_sources               source files, titles, URLs
  category_conflicts         source observations that disagree
  national_state_summary     National Compilation state totals (separate)
  national_district_summary  National Compilation district totals (separate)

NULL values are returned as None and are never turned into 0.
"""

import difflib
import os
import re
import sqlite3
import threading
from functools import lru_cache
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DB_PATH = BASE_DIR / "data" / "groundwater.db"

CATEGORIES = ["Safe", "Semi-critical", "Critical", "Over-exploited", "Saline"]
METRICS = {
    "annual_recharge": "Annual groundwater recharge",
    "extractable_resource": "Annual extractable groundwater resource",
    "total_extraction": "Total groundwater extraction",
    "stage_of_extraction_pct": "Stage of groundwater extraction",
}
MAX_ROWS = 200

READABLE_TABLES = {
    "groundwater_assessment", "data_sources", "category_conflicts",
    "national_state_summary", "national_district_summary", "national_unit_counts",
}

# State names printed differently in the National Compilation tables.
STATE_ALIASES = {
    "ANDAMANNICOBARISLANDS": "Andaman And Nicobar", "ANDAMANANDNICOBARISLANDS": "Andaman And Nicobar",
    "ANDAMANANDNICOBAR": "Andaman And Nicobar",
    "CHHATISGARH": "Chhattisgarh", "JAMMUKASHMIR": "Jammu And Kashmir",
    "HAVELIANDDAMANAND": "Dadra and Nagar Haveli and Daman and Diu",
    "DADRANAGARHAVELI": "Dadra and Nagar Haveli and Daman and Diu",
    "DADRAANDNAGARHAVELI": "Dadra and Nagar Haveli and Daman and Diu",
    "TAMILNADU": "Tamil Nadu", "ORISSA": "Odisha", "NCTOFDELHI": "Delhi", "NEWDELHI": "Delhi",
}


class DatabaseNotReadyError(Exception):
    """The database file is missing or does not have the expected tables."""


def norm(text):
    """Matching key: upper case, letters and digits only ('Ajmer Urban' == 'AJMER_URBAN')."""
    return re.sub(r"[^A-Z0-9]", "", str(text or "").upper())


def get_db_path():
    custom = os.getenv("JALMITRA_DB_PATH")
    return Path(custom) if custom else DEFAULT_DB_PATH


# ------------------------------------------------------------------ connection

def _authorizer(action, arg1, arg2, db_name, trigger):
    if action in (sqlite3.SQLITE_SELECT, sqlite3.SQLITE_RECURSIVE):
        return sqlite3.SQLITE_OK
    if action == sqlite3.SQLITE_READ:
        if not arg1 or arg1 in READABLE_TABLES:
            return sqlite3.SQLITE_OK
        return sqlite3.SQLITE_DENY
    if action == sqlite3.SQLITE_FUNCTION:
        if (arg2 or "").lower() in {"load_extension", "readfile", "writefile"}:
            return sqlite3.SQLITE_DENY
        return sqlite3.SQLITE_OK
    return sqlite3.SQLITE_DENY


def connect_read_only(db_path=None):
    path = Path(db_path) if db_path else get_db_path()
    if not path.exists():
        raise DatabaseNotReadyError(f"Database not found at {path}. Build it with build_database.py.")
    conn = sqlite3.connect(f"{path.resolve().as_uri()}?mode=ro", uri=True, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA query_only = ON")
    conn.set_authorizer(_authorizer)  # from here on only reads of known tables
    return conn


_CONNECTIONS = {}
_LOCK = threading.Lock()


def _shared_connection(db_path=None):
    """One reusable read-only connection per database file (no reconnect per question)."""
    key = str(Path(db_path) if db_path else get_db_path())
    conn = _CONNECTIONS.get(key)
    if conn is None:
        conn = connect_read_only(key)
        _CONNECTIONS[key] = conn
    return conn


def close_connections():
    """Close the shared connections (used by tests)."""
    with _LOCK:
        for conn in _CONNECTIONS.values():
            conn.close()
        _CONNECTIONS.clear()


def _query(sql, params=(), db_path=None):
    """Run one fixed, parameterised SELECT and return a list of dicts."""
    with _LOCK:
        try:
            conn = _shared_connection(db_path)
            return [dict(r) for r in conn.execute(sql, list(params)).fetchall()]
        except sqlite3.DatabaseError as error:
            raise DatabaseNotReadyError(f"Database is not in the expected format: {error}") from error


def database_ready(db_path=None):
    try:
        return coverage(db_path)["total_units"] > 0
    except DatabaseNotReadyError:
        return False


# ------------------------------------------------------------------ coverage

def coverage(db_path=None):
    """Counts used for the coverage line. Raises DatabaseNotReadyError."""
    return _coverage_cached(str(db_path or get_db_path()))


@lru_cache(maxsize=4)
def _coverage_cached(db_path):
    total = _query("SELECT COUNT(*) AS n FROM groundwater_assessment", (), db_path)[0]["n"]
    numeric = _query(
        "SELECT state, assessment_unit_type, COUNT(*) AS n FROM groundwater_assessment "
        "WHERE data_completeness <> 'category_only' GROUP BY state, assessment_unit_type", (), db_path)
    yrs = [r["year"] for r in _query("SELECT DISTINCT year FROM groundwater_assessment ORDER BY year", (), db_path)]
    states = _query("SELECT COUNT(DISTINCT state) AS n FROM groundwater_assessment", (), db_path)[0]["n"]
    return {"total_units": total, "numeric_units": sum(r["n"] for r in numeric),
            "numeric_by_state": numeric, "years": yrs, "states": states}


def coverage_text(db_path=None):
    c = coverage(db_path)
    parts = []
    for r in c["numeric_by_state"]:
        kind = (r["assessment_unit_type"] or "assessment unit").lower() + "s"
        parts.append(f"{r['n']:,} {r['state']} {kind}")
    return (f"Category information: {c['total_units']:,} assessment units. "
            f"Numerical information: {', '.join(parts) if parts else 'none'}.")


# ------------------------------------------------------------------ name resolution

@lru_cache(maxsize=4)
def _name_index(db_path_key):
    rows = _query("SELECT record_id, state, district, assessment_unit, year FROM groundwater_assessment",
                  (), db_path_key)
    for r in rows:
        r["k_state"], r["k_district"], r["k_unit"] = norm(r["state"]), norm(r["district"]), norm(r["assessment_unit"])
    return rows


def _index():
    return _name_index(str(get_db_path()))


def years():
    return sorted({r["year"] for r in _index()})


def resolve_state(name):
    """Return the database spelling of a state, or None."""
    if not name:
        return None
    key = norm(STATE_ALIASES.get(norm(name), name))
    for r in _index():
        if r["k_state"] == key:
            return r["state"]
    return None


def find_units(name, state=None, district=None, year=None):
    """Assessment units whose name matches exactly (ignoring case, spaces, _ and -)."""
    key = norm(name)
    st = norm(resolve_state(state) or state) if state else None
    dk = norm(district) if district else None
    ids = [r["record_id"] for r in _index()
           if key and r["k_unit"] == key and (not st or r["k_state"] == st)
           and (not dk or r["k_district"] == dk) and (not year or r["year"] == str(year))]
    return get_units(ids)


def find_districts(name, state=None):
    """List of (state, district) whose district name matches."""
    key = norm(name)
    st = norm(resolve_state(state) or state) if state else None
    return sorted({(r["state"], r["district"]) for r in _index()
                   if key and r["k_district"] == key and (not st or r["k_state"] == st)})


def suggest_names(name, limit=5):
    """Close spellings of unit, district and state names (for 'did you mean')."""
    key = norm(name)
    if not key:
        return []
    names = {}
    for r in _index():
        names.setdefault(r["k_unit"], f"{r['assessment_unit']} ({r['district']}, {r['state']})")
        names.setdefault(r["k_district"], f"{r['district']} district ({r['state']})")
        names.setdefault(r["k_state"], r["state"])
    return [names[c] for c in difflib.get_close_matches(key, list(names), n=limit, cutoff=0.8)]


# ------------------------------------------------------------------ assessment-unit queries

def get_unit(record_id):
    rows = _query("SELECT * FROM groundwater_assessment WHERE record_id = ?", (record_id,))
    return rows[0] if rows else None


def get_units(record_ids):
    """Several units by record_id, in the order given."""
    ids = list(dict.fromkeys(record_ids))
    if not ids:
        return []
    rows = _query("SELECT * FROM groundwater_assessment WHERE record_id IN (" + ", ".join("?" for _ in ids) + ")", ids)
    by_id = {r["record_id"]: r for r in rows}
    return [by_id[i] for i in ids if i in by_id]


def _filters(state=None, district=None, category=None, year=None, numeric_only=False):
    """WHERE clause from fixed column names chosen by this code. Values go in params only."""
    where, params = [], []
    if state:
        where.append("state = ?")
        params.append(resolve_state(state) or state)
    if district:
        # exact database spellings of this district (matched in Python, passed as parameters)
        names = sorted({d for _, d in find_districts(district, state)}) or [district]
        where.append("district IN (" + ", ".join("?" for _ in names) + ")")
        params.extend(names)
    if category:
        where.append("category = ?")
        params.append(category)
    if year:
        where.append("year = ?")
        params.append(str(year))
    if numeric_only:
        where.append("stage_of_extraction_pct IS NOT NULL")
    return (" WHERE " + " AND ".join(where)) if where else "", params


def search_units(state=None, district=None, category=None, year=None, limit=50):
    where, params = _filters(state, district, category, year)
    return _query("SELECT * FROM groundwater_assessment" + where +
                  " ORDER BY state, district, assessment_unit LIMIT ?", params + [int(limit)])


def count_units(state=None, district=None, category=None, year=None):
    where, params = _filters(state, district, category, year)
    return _query("SELECT COUNT(*) AS n FROM groundwater_assessment" + where, params)[0]["n"]


def category_counts(state=None, district=None, year=None):
    """{category: count} for an area."""
    where, params = _filters(state, district, None, year)
    rows = _query("SELECT category, COUNT(*) AS n FROM groundwater_assessment" + where +
                  " GROUP BY category", params)
    counts = {c: 0 for c in CATEGORIES}
    counts.update({r["category"]: r["n"] for r in rows})
    return counts


def numeric_unit_count(state=None, district=None, year=None):
    where, params = _filters(state, district, None, year)
    extra = (" AND " if where else " WHERE ") + "data_completeness <> 'category_only'"
    return _query("SELECT COUNT(*) AS n FROM groundwater_assessment" + where + extra, params)[0]["n"]


def top_units_by_stage(n=5, state=None, district=None, category=None, year=None, highest=True):
    """Rank units by published stage of extraction. Units without a stage are left out."""
    where, params = _filters(state, district, category, year, numeric_only=True)
    order = "DESC" if highest else "ASC"
    return _query("SELECT * FROM groundwater_assessment" + where +
                  f" ORDER BY stage_of_extraction_pct {order}, assessment_unit LIMIT ?",
                  params + [max(1, min(int(n), 50))])


def top_areas_by_category(category, level="district", state=None, year=None, n=5):
    """Districts (or states) with the most units in one category."""
    group = "state, district" if level == "district" else "state"
    where, params = _filters(state, None, category, year)
    return _query(f"SELECT {group}, COUNT(*) AS units FROM groundwater_assessment" + where +
                  f" GROUP BY {group} ORDER BY units DESC, {group} LIMIT ?",
                  params + [max(1, min(int(n), 50))])


def flagged_units(flag=None, state=None, limit=50):
    """Units with quality flags (the common 'values_not_in_uploaded_sources' alone is ignored)."""
    where, params = _filters(state)
    cond = "quality_flag IS NOT NULL AND quality_flag <> 'values_not_in_uploaded_sources'"
    if flag:
        cond += " AND (';' || quality_flag || ';') LIKE ?"
        params = params + [f"%;{flag};%"]
    return _query("SELECT * FROM groundwater_assessment" + where + (" AND " if where else " WHERE ") + cond +
                  " ORDER BY state, district, assessment_unit LIMIT ?", params + [int(limit)])


# ------------------------------------------------------------------ sources and conflicts

def data_sources():
    return _data_sources_cached(str(get_db_path()))


@lru_cache(maxsize=4)
def _data_sources_cached(db_path_key):
    return {r["source_id"]: r for r in _query("SELECT * FROM data_sources ORDER BY source_id", (), db_path_key)}


def conflicts_for(record_id):
    return _query("SELECT * FROM category_conflicts WHERE record_id = ? ORDER BY source_id", (record_id,))


def sources_for(record):
    """Source references for one unit: category source, figures source, conflict sources."""
    src = data_sources()
    out = []

    def add(source_id, page, what):
        s = src.get(source_id, {})
        out.append({"used_for": what, "source_id": source_id, "title": s.get("title"),
                    "page": str(page), "url": s.get("source_url"), "file": s.get("file_name")})

    add(record["source_id"], record["source_page"], f"category (S.No {record['source_serial']})")
    if record.get("values_source_id"):
        add(record["values_source_id"], record["values_source_page"], f"figures: {record['values_source_table']}")
    for c in conflicts_for(record["record_id"]):
        if c["source_id"] != record["source_id"]:
            add(c["source_id"], c["source_page"], "different observation of the category")
    if record.get("assessment_unit_type_source"):
        m = re.search(r"p(\d+)", record["assessment_unit_type_source"])
        add("NC2025", m.group(1) if m else record["assessment_unit_type_source"], "unit type (state-wise note)")
    return out


# ------------------------------------------------------------------ National Compilation summaries

def _nc_state_key(name):
    return norm(STATE_ALIASES.get(norm(name), name))


def national_district_summary(district, state=None):
    """District totals from the National Compilation (separate from unit rows)."""
    dk = norm(district)
    sk = _nc_state_key(resolve_state(state) or state) if state else None
    rows = _nc_table("national_district_summary")
    return [r for r in rows if norm(r["district"]) == dk and (not sk or _nc_state_key(r["state"]) == sk)]


def national_state_summary(state):
    sk = _nc_state_key(resolve_state(state) or state)
    return [r for r in _nc_table("national_state_summary") if _nc_state_key(r["state"]) == sk]


def _nc_table(table):
    return _nc_cached(table, str(get_db_path()))


@lru_cache(maxsize=8)
def _nc_cached(table, db_path_key):
    # table is one of two fixed names chosen in this file, never user text
    sql = {"national_district_summary": "SELECT * FROM national_district_summary ORDER BY state, district",
           "national_state_summary": "SELECT * FROM national_state_summary ORDER BY state"}[table]
    return _query(sql, (), db_path_key)

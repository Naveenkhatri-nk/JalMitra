"""
monitoring_retrieval.py - read-only access to data/groundwater_monitoring.db (JalMitra 4.0).

Additive module: it does not change database.py, retrieval.py or data/groundwater.db. It returns STRUCTURED
results in the same spirit as retrieval.py (dicts with status, rows, sources and caveats) and writes no
sentences beyond short fixed caveat labels.

Places use the GWRA spelling already used by the rest of JalMitra (state as in groundwater.db, district in
upper case as in groundwater_assessment.district). The monitoring database maps India-WRIS district names to
these spellings in district_name_map; unmatched districts are simply not found here.

Rules:
  * only usable manual measurements (observations.usable = 1) enter levels and comparisons,
  * a year-to-year comparison uses the SAME stations in both years (paired), never two different well sets,
  * fewer than MIN_PAIRS paired stations -> status "insufficient_data" (no number is given),
  * telemetry is reported separately and never mixed with manual measurements,
  * nothing is estimated or filled in; missing stays None.
"""
from __future__ import annotations

import re
import sqlite3
import statistics
import threading
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data" / "groundwater_monitoring.db"
MIN_PAIRS = 3
MIN_DECADE_YEARS = 3
SEASONS = ("pre_monsoon", "post_monsoon", "january", "august")
SEASON_LABEL = {"pre_monsoon": "Pre-monsoon (Mar-May)", "post_monsoon": "Post-monsoon (Oct-Dec)",
                "january": "January", "august": "August"}
SOURCE_NOTE = ("India-WRIS Ground Water Level data (NWIC, Ministry of Jal Shakti); measurements by CGWB and the "
               "Ground Water Department, Rajasthan. Reproduced with acknowledgement under the India-WRIS copyright policy.")
READABLE = {"meta", "rules", "sources", "raw_files", "stations", "observations", "telemetry_daily", "station_season",
            "district_season_summary", "validation_issues", "duplicates", "district_name_map", "download_windows",
            "publications", "gwra_category_history"}

_lock = threading.Lock()
_conns: dict[str, sqlite3.Connection] = {}


def _authorizer(action, arg1, arg2, db_name, trigger):
    if action in (sqlite3.SQLITE_SELECT, sqlite3.SQLITE_FUNCTION):
        return sqlite3.SQLITE_OK
    if action == sqlite3.SQLITE_READ:
        return sqlite3.SQLITE_OK if arg1 in READABLE or arg1 == "sqlite_master" else sqlite3.SQLITE_DENY
    if action == sqlite3.SQLITE_PRAGMA and arg1 in ("query_only",):
        return sqlite3.SQLITE_OK
    return sqlite3.SQLITE_DENY


def _conn(db_path=None):
    p = str(Path(db_path or DB_PATH))
    with _lock:
        c = _conns.get(p)
        if c is None:
            c = sqlite3.connect(f"file:{Path(p).as_posix()}?mode=ro", uri=True, check_same_thread=False)
            c.row_factory = sqlite3.Row
            c.execute("PRAGMA query_only = ON")
            c.set_authorizer(_authorizer)
            _conns[p] = c
        return c


def close():
    with _lock:
        for c in _conns.values():
            c.close()
        _conns.clear()


def _q(sql, params=(), db_path=None):
    c = _conn(db_path)
    with _lock:
        return [dict(r) for r in c.execute(sql, params).fetchall()]


def available(db_path=None) -> bool:
    p = Path(db_path or DB_PATH)
    if not p.exists():
        return False
    try:
        return bool(_q("SELECT 1 FROM meta LIMIT 1", db_path=db_path))
    except sqlite3.Error:
        return False


def _norm(s):
    return "".join(ch for ch in (s or "").upper() if ch.isalnum())


def _place(state, district):
    return state, (district or "").upper() if district else None


def coverage(db_path=None):
    """Counts per state and agency (stations, usable manual measurements, years)."""
    rows = _q("""SELECT s.state, s.agency, COUNT(DISTINCT s.station_key) stations,
                        SUM(CASE WHEN o.usable=1 THEN 1 ELSE 0 END) usable_measurements,
                        MIN(o.year) first_year, MAX(o.year) last_year
                 FROM stations s LEFT JOIN observations o USING(station_key)
                 GROUP BY s.state, s.agency ORDER BY s.state, s.agency""", db_path=db_path)
    return {"status": "ok", "rows": rows, "source": SOURCE_NOTE}


def stations(state, district=None, agency=None, db_path=None, limit=500):
    state, district = _place(state, district)
    sql = ("SELECT station_key, station_code, agency, station_name, state, district, district_gwra, block, village, "
           "latitude, longitude, coord_flag, well_type, well_depth_m, aquifer_type, modes, sign_convention, "
           "first_date, last_date, n_manual, n_telemetry_days FROM stations WHERE lower(state)=lower(?)")
    p = [state]
    if district:
        sql += " AND district_gwra=?"
        p.append(district)
    if agency:
        sql += " AND agency=?"
        p.append(agency)
    sql += " ORDER BY agency, station_code LIMIT ?"
    p.append(limit)
    return _q(sql, p, db_path=db_path)


def district_history(state, district, season="pre_monsoon", agency=None, db_path=None):
    """Year-by-year district summary of usable manual measurements (all stations measured that year)."""
    state, district = _place(state, district)
    sql = ("SELECT agency, year, season, n_stations, depth_median, depth_mean, depth_p10, depth_p90, depth_min, depth_max "
           "FROM district_season_summary WHERE lower(state)=lower(?) AND district_gwra=? AND season=?")
    p = [state, district, season]
    if agency:
        sql += " AND agency=?"
        p.append(agency)
    rows = _q(sql + " ORDER BY agency, year", p, db_path=db_path)
    if not rows:
        return {"status": "no_data", "state": state, "district": district, "season": season, "rows": []}
    return {"status": "ok", "state": state, "district": district, "season": season,
            "season_label": SEASON_LABEL.get(season, season), "rows": rows, "source": SOURCE_NOTE,
            "caveat": "Each year uses the wells measured that year; the set of wells changes between years. "
                      "Use compare_years() for a like-for-like change."}


def latest_level(state, district, season="pre_monsoon", agency=None, db_path=None):
    h = district_history(state, district, season, agency, db_path)
    if h["status"] != "ok":
        return h
    by_agency = {}
    for r in h["rows"]:
        by_agency[r["agency"]] = r
    return {**h, "rows": list(by_agency.values())}


def _station_values(state, district, year, season, agency, db_path):
    sql = ("SELECT ss.station_key, ss.depth_mbgl FROM station_season ss JOIN stations s USING(station_key) "
           "WHERE lower(s.state)=lower(?) AND s.district_gwra=? AND ss.year=? AND ss.season=?")
    p = [state, district, year, season]
    if agency:
        sql += " AND s.agency=?"
        p.append(agency)
    return {r["station_key"]: r["depth_mbgl"] for r in _q(sql, p, db_path=db_path)}


def compare_years(state, district, year_a, year_b, season="pre_monsoon", agency=None, db_path=None):
    """Paired comparison: only stations with a usable measurement in both years and the same season.
    change_m > 0 means the water level is DEEPER (fell) in year_b than in year_a."""
    state, district = _place(state, district)
    a = _station_values(state, district, int(year_a), season, agency, db_path)
    b = _station_values(state, district, int(year_b), season, agency, db_path)
    keys = sorted(set(a) & set(b))
    out = {"state": state, "district": district, "season": season, "season_label": SEASON_LABEL.get(season, season),
           "year_a": int(year_a), "year_b": int(year_b), "stations_year_a": len(a), "stations_year_b": len(b),
           "paired_stations": len(keys), "min_pairs": MIN_PAIRS, "source": SOURCE_NOTE}
    if len(keys) < MIN_PAIRS:
        return {**out, "status": "insufficient_data"}
    ch = [round(b[k] - a[k], 3) for k in keys]
    return {**out, "status": "ok",
            "median_depth_a": round(statistics.median(a[k] for k in keys), 3),
            "median_depth_b": round(statistics.median(b[k] for k in keys), 3),
            "median_change_m": round(statistics.median(ch), 3),
            "stations_deeper": sum(1 for c in ch if c > 0.0), "stations_shallower": sum(1 for c in ch if c < 0.0),
            "stations_unchanged": sum(1 for c in ch if c == 0.0),
            "largest_fall_m": max(ch), "largest_rise_m": min(ch),
            "caveat": "Depth below ground level; positive change = water level fell (deeper)."}


def decadal_change(state, district, year, season="pre_monsoon", agency=None, db_path=None):
    """CGWB-style decadal comparison: each station's level in `year` minus its mean over the previous ten years
    (needs at least MIN_DECADE_YEARS of those ten years)."""
    state, district = _place(state, district)
    year = int(year)
    cur = _station_values(state, district, year, season, agency, db_path)
    sql = ("SELECT ss.station_key, ss.year, ss.depth_mbgl FROM station_season ss JOIN stations s USING(station_key) "
           "WHERE lower(s.state)=lower(?) AND s.district_gwra=? AND ss.season=? AND ss.year BETWEEN ? AND ?")
    p = [state, district, season, year - 10, year - 1]
    if agency:
        sql += " AND s.agency=?"
        p.append(agency)
    hist = {}
    for r in _q(sql, p, db_path=db_path):
        hist.setdefault(r["station_key"], []).append(r["depth_mbgl"])
    ch = [cur[k] - statistics.mean(v) for k, v in hist.items() if k in cur and len(v) >= MIN_DECADE_YEARS]
    out = {"state": state, "district": district, "season": season, "year": year,
           "baseline": f"{year-10}-{year-1}", "stations": len(ch), "min_pairs": MIN_PAIRS, "source": SOURCE_NOTE}
    if len(ch) < MIN_PAIRS:
        return {**out, "status": "insufficient_data"}
    return {**out, "status": "ok", "median_change_m": round(statistics.median(ch), 3),
            "stations_deeper": sum(1 for c in ch if c > 0), "stations_shallower": sum(1 for c in ch if c < 0),
            "caveat": "Positive = deeper than the station's own ten-year mean."}


def station_history(station_key, db_path=None):
    st = _q("SELECT * FROM stations WHERE station_key=?", (station_key,), db_path=db_path)
    if not st:
        return {"status": "not_found", "station_key": station_key}
    obs = _q("SELECT obs_date, season, value_raw, depth_mbgl, depth_basis, quality_flag, usable FROM observations "
             "WHERE station_key=? ORDER BY obs_date", (station_key,), db_path=db_path)
    return {"status": "ok", "station": st[0], "observations": obs, "source": SOURCE_NOTE}


def telemetry_summary(state, district, start=None, end=None, db_path=None):
    """Monthly median of usable telemetry station-days (kept apart from manual measurements)."""
    state, district = _place(state, district)
    sql = ("SELECT substr(t.obs_date,1,7) month, COUNT(DISTINCT t.station_key) stations, COUNT(*) station_days, "
           "AVG(t.depth_mean) mean_depth FROM telemetry_daily t JOIN stations s USING(station_key) "
           "WHERE lower(s.state)=lower(?) AND s.district_gwra=? AND t.usable=1")
    p = [state, district]
    if start:
        sql += " AND t.obs_date>=?"
        p.append(start)
    if end:
        sql += " AND t.obs_date<=?"
        p.append(end)
    rows = _q(sql + " GROUP BY 1 ORDER BY 1", p, db_path=db_path)
    if not rows:
        return {"status": "no_data", "state": state, "district": district, "rows": []}
    for r in rows:
        r["mean_depth"] = round(r["mean_depth"], 3) if r["mean_depth"] is not None else None
    return {"status": "ok", "state": state, "district": district, "rows": rows, "source": SOURCE_NOTE,
            "caveat": "Telemetric readings; sign convention inferred per station (see rules R04)."}


def _name_key(name):
    return re.sub(r"[^A-Z0-9]", "", (name or "").upper())


def _unit_key(name):
    """Name key that also drops a trailing Rural/Urban part (CGWB renamed e.g. SANGANER to Sanganer_Rural)."""
    k = _name_key(name)
    return re.sub(r"(RURAL|URBAN)$", "", k) or k


def category_history(state, district=None, assessment_unit=None, db_path=None):
    """Historical GWRA categories extracted from CGWB block-wise categorisation reports.
    For each assessment year the unit is matched on its name without case, spaces and punctuation. Only when a year
    has no such match is a renamed unit followed (same name with a Rural/Urban suffix added or dropped), and only
    if exactly one unit in that district fits, so 'X Rural' and 'X Urban' are never merged."""
    sql = "SELECT * FROM gwra_category_history WHERE lower(state)=lower(?)"
    p = [state]
    if district:
        sql += " AND upper(district)=upper(?)"
        p.append(district)
    rows = _q(sql + " ORDER BY district, assessment_unit, assessment_year", p, db_path=db_path)
    renamed = []
    if assessment_unit:
        exact, loose = _name_key(assessment_unit), _unit_key(assessment_unit)
        by_year = {}
        for r in rows:
            by_year.setdefault(r["assessment_year"], []).append(r)
        picked = []
        for y, rs in sorted(by_year.items()):
            hit = [r for r in rs if _name_key(r["assessment_unit"]) == exact]
            if not hit:
                cand = [r for r in rs if _unit_key(r["assessment_unit"]) == loose]
                if len(cand) == 1:
                    hit = cand
                    renamed.append(f"{y}: {cand[0]['assessment_unit']}")
            picked += hit
        rows = picked
    out = {"status": "ok" if rows else "no_data", "rows": rows}
    if renamed:
        out["renamed_years"] = renamed
        out["caveat"] = "The block appears under a different published name in some years (Rural/Urban suffix); " \
                        "those rows are followed only where exactly one block in the district fits."
    return out


def sources(db_path=None):
    return _q("SELECT * FROM sources ORDER BY source_id", db_path=db_path)


def execute(req, db_path=None):
    """Entry point shaped like retrieval.execute(): req = {"intent": "...", "places": [...], "years": [...],
    "season": ...}. Supported intents: gwl_level, gwl_history, gwl_compare, gwl_decadal, gwl_stations."""
    if not available(db_path):
        return {"status": "monitoring_db_missing"}
    places = req.get("places") or []
    pl = next((p for p in places if p.get("type") == "district"), None)
    if pl is None:
        return {"status": "need_district"}
    st, d = pl["state"], pl.get("district") or pl.get("name")
    season = req.get("season") or "pre_monsoon"
    years = [int(y) for y in req.get("years") or []]
    it = req.get("intent")
    if it == "gwl_level":
        return latest_level(st, d, season, db_path=db_path)
    if it == "gwl_history":
        return district_history(st, d, season, db_path=db_path)
    if it == "gwl_compare":
        if len(years) < 2:
            return {"status": "need_two_years"}
        return compare_years(st, d, min(years), max(years), season, db_path=db_path)
    if it == "gwl_decadal":
        if not years:
            return {"status": "need_year"}
        return decadal_change(st, d, years[0], season, db_path=db_path)
    if it == "gwl_stations":
        return {"status": "ok", "rows": stations(st, d, db_path=db_path)}
    return {"status": "unknown_intent"}

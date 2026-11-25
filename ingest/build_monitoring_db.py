"""
Build data/groundwater_monitoring.db from the original files kept under data/monitoring/raw/.

  * The existing data/groundwater.db is opened read-only (district name matching only) and its SHA256 is
    checked before and after the build.
  * The build writes a new scratch database first (data/monitoring/scratch/), runs the validation and
    integrity checks on it, and only then copies it to data/groundwater_monitoring.db. A previous
    groundwater_monitoring.db is moved to data/monitoring/scratch/previous/ first (never deleted).
  * Values are stored exactly as published (value_raw). Derived depth below ground level (depth_mbgl) is
    filled only where the sign convention is documented or clear for that station; every rule is listed
    in the `rules` table and in reports/DATA_DICTIONARY.md.

Usage:  python ingest/build_monitoring_db.py [--raw data/monitoring/raw] [--no-promote]
"""
from __future__ import annotations

import argparse
import json
import math
import shutil
import sqlite3
import statistics
import sys
import time
from collections import Counter, defaultdict
from datetime import date, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402

BUILD_VERSION = "4.0.0"
SENTINELS = {-999.0, -9999.0, 9999.0, 999.0, -99.0}
INDIA_BBOX = (6.0, 38.5, 68.0, 97.5)          # lat min, lat max, lon min, lon max
RAJASTHAN_BBOX = (23.0, 30.3, 69.4, 78.4)
MAX_PLAUSIBLE_DEPTH = 300.0                    # m bgl; deeper readings flagged as implausible
SEASON_OF_MONTH = {1: "january", 3: "pre_monsoon", 4: "pre_monsoon", 5: "pre_monsoon", 8: "august",
                   10: "post_monsoon", 11: "post_monsoon", 12: "post_monsoon"}

SCHEMA = """
CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE rules (rule_id TEXT PRIMARY KEY, applies_to TEXT, rule TEXT, consequence TEXT);
CREATE TABLE sources (
    source_id TEXT PRIMARY KEY, title TEXT NOT NULL, publisher TEXT, url TEXT NOT NULL, access TEXT,
    licence TEXT, licence_evidence TEXT, accessed TEXT, notes TEXT);
CREATE TABLE raw_files (
    file_id INTEGER PRIMARY KEY, source_id TEXT NOT NULL REFERENCES sources(source_id), path TEXT NOT NULL UNIQUE,
    sha256 TEXT NOT NULL, bytes INTEGER, agency TEXT, state TEXT, district TEXT, window_start TEXT,
    window_end TEXT, page INTEGER, rows INTEGER);
CREATE TABLE stations (
    station_key TEXT PRIMARY KEY,           -- agency|station_code
    station_code TEXT NOT NULL, agency TEXT NOT NULL, station_name TEXT,
    state TEXT, district TEXT, district_gwra TEXT, tehsil TEXT, block TEXT, village TEXT,
    latitude REAL, longitude REAL, coord_decimals INTEGER, coord_flag TEXT,
    well_type TEXT, well_depth_m REAL, aquifer_type TEXT, station_status TEXT,
    modes TEXT, datatype_codes TEXT, sign_convention TEXT, sign_negative_share REAL,
    first_date TEXT, last_date TEXT, n_manual INTEGER, n_telemetry_days INTEGER,
    metadata_conflicts TEXT, source_id TEXT REFERENCES sources(source_id));
CREATE TABLE observations (               -- manual (periodic) water-level measurements, one row per reading
    obs_id INTEGER PRIMARY KEY, station_key TEXT NOT NULL REFERENCES stations(station_key),
    obs_time TEXT NOT NULL, obs_date TEXT NOT NULL, year INTEGER, month INTEGER, season TEXT,
    value_raw REAL, unit TEXT, datatype_code TEXT, description TEXT, mode TEXT,
    depth_mbgl REAL, depth_basis TEXT, quality_flag TEXT NOT NULL, usable INTEGER NOT NULL,
    file_id INTEGER REFERENCES raw_files(file_id));
CREATE TABLE telemetry_daily (           -- telemetric readings summarised per station and day
    station_key TEXT NOT NULL REFERENCES stations(station_key), obs_date TEXT NOT NULL,
    n_readings INTEGER, n_used INTEGER, depth_min REAL, depth_mean REAL, depth_max REAL,
    value_raw_min REAL, value_raw_max REAL, quality_flag TEXT, usable INTEGER NOT NULL,
    PRIMARY KEY (station_key, obs_date));
CREATE TABLE station_season (            -- one usable manual depth per station, year and season (median)
    station_key TEXT NOT NULL, year INTEGER NOT NULL, season TEXT NOT NULL, depth_mbgl REAL, n INTEGER,
    PRIMARY KEY (station_key, year, season));
CREATE TABLE district_season_summary (   -- usable manual measurements only
    agency TEXT, state TEXT, district TEXT, district_gwra TEXT, year INTEGER, season TEXT,
    n_stations INTEGER, depth_median REAL, depth_mean REAL, depth_p10 REAL, depth_p90 REAL,
    depth_min REAL, depth_max REAL,
    PRIMARY KEY (agency, state, district, year, season));
CREATE TABLE validation_issues (
    issue_id INTEGER PRIMARY KEY, check_id TEXT, severity TEXT, scope TEXT, ref TEXT, detail TEXT);
CREATE TABLE duplicates (
    station_key TEXT, obs_time TEXT, n_copies INTEGER, distinct_values TEXT, resolution TEXT);
CREATE TABLE district_name_map (
    wris_state TEXT, wris_district TEXT, gwra_state TEXT, gwra_district TEXT, method TEXT,
    PRIMARY KEY (wris_state, wris_district));
CREATE TABLE download_windows (
    agency TEXT, state TEXT, district TEXT, window_start TEXT, window_end TEXT, pages INTEGER, rows INTEGER,
    status TEXT, time_utc TEXT);
CREATE TABLE publications (
    pub_id INTEGER PRIMARY KEY, title TEXT, category TEXT, state TEXT, district TEXT, year_of_issue TEXT,
    detail_url TEXT, download_url TEXT, downloaded INTEGER, file TEXT, sha256 TEXT, bytes INTEGER,
    pdf_pages INTEGER, download_status TEXT);
CREATE TABLE gwra_category_history (     -- filled by ingest/extract_gwra_history.py
    state TEXT, district TEXT, assessment_unit TEXT, assessment_year TEXT, category TEXT,
    stage_of_extraction_pct REAL, source_id TEXT, source_page INTEGER, quality_flag TEXT);
"""

INDEXES = """
CREATE INDEX IF NOT EXISTS ix_obs_station ON observations(station_key, obs_date);
CREATE INDEX ix_obs_year ON observations(year, season);
CREATE INDEX ix_st_place ON stations(state, district);
CREATE INDEX ix_st_gwra ON stations(state, district_gwra);
CREATE INDEX ix_ss_year ON station_season(year, season);
CREATE INDEX ix_dss_place ON district_season_summary(state, district_gwra, year);
CREATE INDEX ix_gch_place ON gwra_category_history(state, district, assessment_unit);
"""

RULES = [
    ("R01", "all", "value_raw keeps the published dataValue unchanged; unit kept as published", "none"),
    ("R02", "all", "values -999, -9999, 9999, 999, -99 are no-data codes", "quality_flag=sentinel, usable=0"),
    ("R03", "CGWB manual (HGZ MANUAL-Water Level)",
     "CGWB publishes manual depth to water level in metres below ground level (positive down)",
     "depth_mbgl = value_raw when value_raw >= 0; negative values flagged negative_manual_value, usable=0"),
    ("R04", "telemetric or GGZ series",
     "sign convention decided per station from its own readings: >=95% negative -> negative_below_ground "
     "(depth_mbgl = -value_raw); >=95% zero-or-positive -> positive_depth; otherwise ambiguous",
     "readings of the minority sign flagged sign_outlier and not used; ambiguous stations get no depth_mbgl"),
    ("R05", "all", "depth_mbgl greater than well depth + 0.5 m", "flag depth_exceeds_well_depth, usable=0"),
    ("R06", "manual", "depth_mbgl equal to well depth (within 0.01 m)", "flag possible_dry_well, usable=0"),
    ("R07", "all", f"depth_mbgl above {MAX_PLAUSIBLE_DEPTH} m", "flag implausible_depth, usable=0"),
    ("R08", "all", "observation date in the future or before 1950", "flag bad_date, usable=0"),
    ("R09", "stations", "coordinates outside India bounding box, or Rajasthan box for Rajasthan stations",
     "coord_flag outside_india / outside_state"),
    ("R10", "stations", "coordinates given with 2 or fewer decimals (about 1 km or coarser)", "coord_flag coarse"),
    ("R11", "stations", "station more than 1.5 degrees from the median position of its district's stations",
     "coord_flag far_from_district"),
    ("R12", "observations", "same station and time repeated with the same value", "kept once; logged in duplicates"),
    ("R13", "observations", "same station and time repeated with different values",
     "one copy of each distinct value kept, flag conflicting_duplicate, usable=0"),
    ("R14", "observations", "Rajasthan GW rows labelled Manual but with GPRS datatype GGZ",
     "kept as manual; flag mode_label_mismatch (informational, usable unchanged)"),
    ("R15", "seasons", "January=1; pre_monsoon=Mar-May; august=8; post_monsoon=Oct-Dec; other months 'other'",
     "used only for grouping; CGWB's own campaign months are Jan, Mar/Apr/May, Aug, Nov"),
    ("R16", "summaries", "district_season_summary and station_season use usable manual measurements only",
     "telemetry is summarised separately in telemetry_daily"),
]


def connect(path: Path) -> sqlite3.Connection:
    con = sqlite3.connect(path)
    con.execute("PRAGMA journal_mode=OFF")
    con.execute("PRAGMA synchronous=OFF")
    return con


def norm_name(s: str) -> str:
    return "".join(ch for ch in (s or "").upper() if ch.isalnum())


KNOWN_DISTRICT_ALIASES = {   # India-WRIS spelling -> GWRA 2025 spelling (groundwater.db)
    ("RAJASTHAN", "CHITTORGARH"): "CHITTAURGARH", ("RAJASTHAN", "JALORE"): "JALOR",
    ("RAJASTHAN", "DHOLPUR"): "DHAULPUR", ("RAJASTHAN", "SRIGANGANAGAR"): "GANGANAGAR",
    ("RAJASTHAN", "JHUNJHUNUN"): "JHUNJHUNU",
}


def gwra_districts() -> dict[str, dict[str, str]]:
    """state(norm) -> {district(norm): district as stored} from the existing database, read-only."""
    out: dict[str, dict[str, str]] = defaultdict(dict)
    if not C.EXISTING_DB.exists():
        return out
    con = sqlite3.connect(f"file:{C.EXISTING_DB.as_posix()}?mode=ro", uri=True)
    try:
        for st, d in con.execute("SELECT DISTINCT state, district FROM groundwater_assessment"):
            out[norm_name(st)][norm_name(d)] = d
            out.setdefault("_STATE_" + norm_name(st), {})["name"] = st
    finally:
        con.close()
    return out


def match_district(state: str, district: str, idx) -> tuple[str | None, str | None, str]:
    import difflib
    ns, nd = norm_name(state), norm_name(district)
    cand_states = [k for k in idx if not k.startswith("_STATE_")]
    st_key = ns if ns in idx else next((k for k in cand_states if k.startswith(ns) or ns.startswith(k)), None)
    if not st_key:
        return None, None, "state_not_in_gwra"
    gstate = idx["_STATE_" + st_key]["name"]
    d = idx[st_key]
    if nd in d:
        return gstate, d[nd], "exact"
    alias = KNOWN_DISTRICT_ALIASES.get((ns, nd))
    if alias and norm_name(alias) in d:
        return gstate, d[norm_name(alias)], "known_alias"
    close = difflib.get_close_matches(nd, list(d), n=1, cutoff=0.85)
    if close:
        return gstate, d[close[0]], f"fuzzy({difflib.SequenceMatcher(None, nd, close[0]).ratio():.2f})"
    return gstate, None, "no_match"


def parse_time(s: str):
    try:
        return datetime.fromisoformat(s.replace("Z", ""))
    except Exception:  # noqa: BLE001
        return None


def decimals(x) -> int:
    if x is None:
        return -1
    s = repr(float(x))
    return len(s.split(".")[1].rstrip("0")) if "." in s else 0


def pct(sorted_vals, q):
    if not sorted_vals:
        return None
    k = (len(sorted_vals) - 1) * q
    f, c = math.floor(k), math.ceil(k)
    return sorted_vals[f] if f == c else sorted_vals[f] + (sorted_vals[c] - sorted_vals[f]) * (k - f)


def load_sources(con):
    rows = [
        ("INDIAWRIS_GWL", "India-WRIS Ground Water Level data (API /Dataset/Ground Water Level)",
         "National Water Informatics Centre (NWIC), Ministry of Jal Shakti; data contributed by CGWB and "
         "State Ground Water Department, Rajasthan", "https://indiawris.gov.in/swagger-ui/index.html",
         "public API, no key", "India-WRIS copyright policy: material may be reproduced free of charge in any "
         "format, accurately, not misleading, source prominently acknowledged",
         "Copyright Policy text in the India-WRIS web application (read 23 Nov 2026)", "", ""),
        ("INDIAWRIS_MASTERS", "India-WRIS district and agency master lists", "NWIC",
         "https://india-water.gov.in/eswis-api/getMasterAgencyListDataViewPage/", "public", "as INDIAWRIS_GWL",
         "", "", "used only to enumerate districts"),
        ("CGWB_PUBLICATIONS", "CGWB Publications and Media Warehouse", "Central Ground Water Board",
         "https://cgwb.gov.in/cgwbpnm/public/publications", "public download, no login",
         "Government of India publication; free public download; source acknowledged",
         "CGWB terms page (https://cgwb.gov.in/en/terms-conditions) returned HTTP 500 on 23 Nov 2026; "
         "earlier JalMitra phases used the same publications", "", ""),
    ]
    con.executemany("INSERT INTO sources VALUES (?,?,?,?,?,?,?,?,?)", rows)


def iter_wris_files(raw: Path):
    base = raw / "indiawris_gwl"
    if not base.exists():
        return
    for p in sorted(base.rglob("*.json.gz")):
        yield p


def build(raw: Path, out: Path, log) -> dict:
    t0 = time.time()
    if out.exists():
        out.unlink()  # scratch file of this run only
    con = connect(out)
    con.executescript(SCHEMA)
    con.executemany("INSERT INTO rules VALUES (?,?,?,?)", RULES)
    load_sources(con)
    idx = gwra_districts()
    today = date.today().isoformat()

    # ---------- pass 1: read raw pages ----------
    station_meta: dict[str, dict] = {}
    meta_variants: dict[str, dict[str, set]] = defaultdict(lambda: defaultdict(set))
    # staging tables keep memory use flat for national-scale runs (dropped before the database is promoted)
    con.executescript("""
      CREATE TABLE stage_manual (k TEXT, t TEXT, v REAL, unit TEXT, code TEXT, descr TEXT, mode TEXT, fid INTEGER);
      CREATE TABLE stage_tele (k TEXT, d TEXT, v REAL);""")
    buf_m, buf_t = [], []
    n_manual = n_tele = 0
    n_files = 0
    for p in iter_wris_files(raw):
        rel = p.relative_to(C.ROOT).as_posix() if C.ROOT in p.parents else p.as_posix()
        body = p.read_bytes()
        import gzip
        inner = gzip.decompress(body)
        try:
            j = json.loads(inner.decode("utf-8"))
        except Exception as e:  # noqa: BLE001
            con.execute("INSERT INTO validation_issues(check_id,severity,scope,ref,detail) VALUES (?,?,?,?,?)",
                        ("V_RAW_JSON", "error", "raw_file", rel, repr(e)[:200]))
            continue
        data = j.get("data") or []
        parts = p.relative_to(raw / "indiawris_gwl").parts
        name = parts[-1].replace(".json.gz", "")
        ws, we, pg = (name.split("_") + ["", "", "p0"])[:3]
        cur = con.execute("INSERT INTO raw_files(source_id,path,sha256,bytes,agency,state,district,window_start,"
                          "window_end,page,rows) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                          ("INDIAWRIS_GWL", rel, C.sha256_bytes(inner), len(body),
                           data[0].get("agencyName") if data else parts[0], data[0].get("state") if data else parts[1],
                           data[0].get("district") if data else parts[2], ws, we, int(pg.lstrip("p") or 0), len(data)))
        fid = cur.lastrowid
        n_files += 1
        for r in data:
            code = str(r.get("stationCode") or "").strip()
            agency = (r.get("agencyName") or "").strip()
            if not code:
                con.execute("INSERT INTO validation_issues(check_id,severity,scope,ref,detail) VALUES (?,?,?,?,?)",
                            ("V_NO_STATION_CODE", "error", "row", rel, json.dumps(r)[:300]))
                continue
            key = f"{agency}|{code}"
            if key not in station_meta:
                station_meta[key] = {"code": code, "agency": agency, "first_rel": rel, "modes": set(),
                                     "codes": set(), **{k: r.get(k) for k in (
                                         "stationName", "state", "district", "tehsil", "block", "village",
                                         "latitude", "longitude", "wellType", "wellDepth", "wellAquiferType",
                                         "stationStatus")}}
            sm = station_meta[key]
            for k in ("latitude", "longitude", "district", "wellDepth", "wellType", "stationName"):
                v = r.get(k)
                if v is not None:
                    meta_variants[key][k].add(v)
            mode = r.get("dataAcquisitionMode") or ""
            sm["modes"].add(mode)
            sm["codes"].add(r.get("datatypeCode") or "")
            v = r.get("dataValue")
            t = r.get("dataTime") or ""
            if mode == "Telemetric":
                if v is not None:
                    buf_t.append((key, t[:10], float(v)))
            else:
                buf_m.append((key, t, None if v is None else float(v), r.get("unit"), r.get("datatypeCode"),
                              r.get("description"), mode, fid))
        if len(buf_m) > 50000:
            con.executemany("INSERT INTO stage_manual VALUES (?,?,?,?,?,?,?,?)", buf_m)
            n_manual += len(buf_m)
            buf_m = []
        if len(buf_t) > 50000:
            con.executemany("INSERT INTO stage_tele VALUES (?,?,?)", buf_t)
            n_tele += len(buf_t)
            buf_t = []
    con.executemany("INSERT INTO stage_manual VALUES (?,?,?,?,?,?,?,?)", buf_m)
    con.executemany("INSERT INTO stage_tele VALUES (?,?,?)", buf_t)
    n_manual += len(buf_m)
    n_tele += len(buf_t)
    del buf_m, buf_t
    sent = ",".join(str(x) for x in SENTINELS)
    manual_sign, tele_sign = defaultdict(Counter), defaultdict(Counter)
    for k, neg, n in con.execute(f"SELECT k, v<0, COUNT(*) FROM stage_manual WHERE v IS NOT NULL AND v NOT IN ({sent}) GROUP BY 1,2"):
        manual_sign[k][bool(neg)] = n
    for k, neg, n in con.execute(f"SELECT k, v<0, COUNT(*) FROM stage_tele WHERE v NOT IN ({sent}) GROUP BY 1,2"):
        tele_sign[k][bool(neg)] = n
    log(f"read {n_files} raw pages, {len(station_meta)} stations, {n_manual} manual rows, "
        f"{n_tele} telemetric readings in {time.time()-t0:.0f}s")

    # ---------- sign conventions ----------
    def convention(counter: Counter, documented_positive: bool):
        neg, pos = counter.get(True, 0), counter.get(False, 0)
        n = neg + pos
        if n == 0:
            return "no_values", None
        share = neg / n
        if documented_positive and share < 0.05:
            return "positive_depth_documented", share
        if share >= 0.95:
            return "negative_below_ground", share
        if share <= 0.05:
            return "positive_depth", share
        return "ambiguous", share

    # ---------- stations ----------
    dist_pos = defaultdict(list)
    for key, sm in station_meta.items():
        if sm["latitude"] is not None and sm["longitude"] is not None:
            dist_pos[(sm["agency"], sm["state"], sm["district"])].append((sm["latitude"], sm["longitude"]))
    dist_median = {k: (statistics.median(a for a, _ in v), statistics.median(b for _, b in v))
                   for k, v in dist_pos.items()}
    name_map = {}
    st_rows = []
    conv_manual, conv_tele = {}, {}
    for key, sm in station_meta.items():
        lat, lon = sm["latitude"], sm["longitude"]
        flags = []
        if lat is None or lon is None:
            flags.append("missing")
        else:
            if not (INDIA_BBOX[0] <= lat <= INDIA_BBOX[1] and INDIA_BBOX[2] <= lon <= INDIA_BBOX[3]):
                flags.append("outside_india")
            elif (sm["state"] or "").lower() == "rajasthan" and not (
                    RAJASTHAN_BBOX[0] <= lat <= RAJASTHAN_BBOX[1] and RAJASTHAN_BBOX[2] <= lon <= RAJASTHAN_BBOX[3]):
                flags.append("outside_state")
            if max(decimals(lat), decimals(lon)) <= 2:
                flags.append("coarse")
            med = dist_median.get((sm["agency"], sm["state"], sm["district"]))
            if med and (abs(lat - med[0]) > 1.5 or abs(lon - med[1]) > 1.5):
                flags.append("far_from_district")
        conflicts = [f"{k}:{'|'.join(map(str, sorted(map(str, v))))}" for k, v in meta_variants[key].items() if len(v) > 1]
        nk = (sm["state"] or "", sm["district"] or "")
        if nk not in name_map:
            name_map[nk] = match_district(nk[0], nk[1], idx)
        gstate, gdist, how = name_map[nk]
        cm = convention(manual_sign[key], documented_positive=(sm["agency"] == "CGWB"))
        ct = convention(tele_sign[key], documented_positive=False)
        conv_manual[key], conv_tele[key] = cm[0], ct[0]
        conv = f"manual:{cm[0]}" + (f"; telemetry:{ct[0]}" if tele_sign[key] else "")
        share = ct[1] if tele_sign[key] else cm[1]
        st_rows.append([key, sm["code"], sm["agency"], sm["stationName"], sm["state"], sm["district"], gdist,
                        sm["tehsil"], sm["block"], sm["village"], lat, lon,
                        max(decimals(lat), decimals(lon)) if lat is not None else None, ",".join(flags) or "ok",
                        sm["wellType"], sm["wellDepth"], sm["wellAquiferType"], sm["stationStatus"],
                        ",".join(sorted(sm["modes"])), ",".join(sorted(sm["codes"])), conv, share,
                        None, None, 0, 0, "; ".join(conflicts) or None, "INDIAWRIS_GWL"])
        if conflicts:
            con.execute("INSERT INTO validation_issues(check_id,severity,scope,ref,detail) VALUES (?,?,?,?,?)",
                        ("V_STATION_META_CONFLICT", "warning", "station", key, "; ".join(conflicts)[:500]))
        for f in flags:
            if f != "coarse":
                con.execute("INSERT INTO validation_issues(check_id,severity,scope,ref,detail) VALUES (?,?,?,?,?)",
                            ("V_COORD_" + f.upper(), "warning", "station", key, f"lat={lat} lon={lon}"))
    con.executemany("INSERT INTO stations VALUES (" + ",".join("?" * 28) + ")", st_rows)
    for (ws, wd), (gs, gd, how) in name_map.items():
        con.execute("INSERT OR REPLACE INTO district_name_map VALUES (?,?,?,?,?)", (ws, wd, gs, gd, how))
        if gd is None:
            con.execute("INSERT INTO validation_issues(check_id,severity,scope,ref,detail) VALUES (?,?,?,?,?)",
                        ("V_DISTRICT_UNMATCHED", "info", "district", f"{ws}/{wd}", how))
    well_depth = {r[0]: r[15] for r in st_rows}
    log(f"stations written: {len(st_rows)}")

    # ---------- manual observations ----------
    con.execute("CREATE INDEX ix_stage_m ON stage_manual(k, t)")
    def groups():
        cur_key, rows = None, []
        for row in con.cursor().execute("SELECT k,t,v,unit,code,descr,mode,fid FROM stage_manual ORDER BY k, t"):
            kt = (row[0], row[1])
            if kt != cur_key and rows:
                yield cur_key, rows
                rows = []
            cur_key = kt
            rows.append(row)
        if rows:
            yield cur_key, rows
    obs = []
    dup_rows = []
    n_obs = n_usable = 0
    ins_obs = ("INSERT INTO observations(station_key,obs_time,obs_date,year,month,season,value_raw,unit,"
               "datatype_code,description,mode,depth_mbgl,depth_basis,quality_flag,usable,file_id) "
               "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)")
    for (key, t), rows in groups():
        vals = {r[2] for r in rows}
        conflict = len(vals) > 1
        if len(rows) > 1:
            dup_rows.append((key, t, len(rows), "|".join(map(str, sorted(vals, key=lambda x: (x is None, x)))),
                             "conflicting values: all kept, not usable" if conflict else "identical: kept once"))
        if conflict:  # keep one row per distinct value (identical copies inside a conflict were exact duplicates)
            seen, use_rows = set(), []
            for r in rows:
                if r[2] not in seen:
                    seen.add(r[2])
                    use_rows.append(r)
        else:
            use_rows = rows[:1]
        for (k, tt, v, unit, code, desc, mode, fid) in use_rows:
            dt = parse_time(tt)
            flags = []
            depth, basis = None, None
            if dt is None:
                flags.append("bad_date")
            elif dt.date().isoformat() > today or dt.year < 1950:
                flags.append("bad_date")
            if v is None:
                flags.append("missing_value")
            elif v in SENTINELS:
                flags.append("sentinel")
            else:
                cm = conv_manual[k]
                if code == "HGZ" or cm == "positive_depth_documented":
                    if v >= 0:
                        depth, basis = v, "published_positive_mbgl"
                    else:
                        flags.append("negative_manual_value")
                elif cm == "negative_below_ground":
                    if v <= 0:
                        depth, basis = -v, "sign_inferred_negative_below_ground"
                    else:
                        flags.append("sign_outlier")
                elif cm == "positive_depth":
                    if v >= 0:
                        depth, basis = v, "sign_inferred_positive_depth"
                    else:
                        flags.append("sign_outlier")
                else:
                    flags.append("ambiguous_sign_convention")
            if code == "GGZ" and mode == "Manual":
                flags.append("mode_label_mismatch")
            wd = well_depth.get(k)
            if depth is not None and wd:
                try:
                    wdv = float(wd)
                    if depth > wdv + 0.5:
                        flags.append("depth_exceeds_well_depth")
                    elif abs(depth - wdv) <= 0.01:
                        flags.append("possible_dry_well")
                except (TypeError, ValueError):
                    pass
            if depth is not None and depth > MAX_PLAUSIBLE_DEPTH:
                flags.append("implausible_depth")
            if conflict:
                flags.append("conflicting_duplicate")
            blocking = [f for f in flags if f != "mode_label_mismatch"]
            usable = 1 if (depth is not None and not blocking) else 0
            y = dt.year if dt else None
            m = dt.month if dt else None
            obs.append((k, tt, tt[:10], y, m, SEASON_OF_MONTH.get(m, "other") if m else None, v, unit, code, desc,
                        mode, depth, basis, ",".join(flags) or "ok", usable, fid))
            n_usable += usable
        if len(obs) > 50000:
            con.executemany(ins_obs, obs)
            n_obs += len(obs)
            obs = []
    con.executemany(ins_obs, obs)
    n_obs += len(obs)
    con.executemany("INSERT INTO duplicates VALUES (?,?,?,?,?)", dup_rows)
    log(f"manual observations written: {n_obs} ({n_usable} usable); duplicate groups {len(dup_rows)}")

    # ---------- telemetry daily ----------
    con.execute("CREATE INDEX ix_stage_t ON stage_tele(k, d)")
    td = []
    n_td = 0
    def tgroups():
        cur_key, vals = None, []
        for k, d, v in con.cursor().execute("SELECT k, d, v FROM stage_tele ORDER BY k, d"):
            if (k, d) != cur_key and vals:
                yield cur_key, vals
                vals = []
            cur_key = (k, d)
            vals.append(v)
        if vals:
            yield cur_key, vals
    for (key, d), vals in tgroups():
        conv = conv_tele[key]
        good = [v for v in vals if v not in SENTINELS]
        flags = []
        if len(good) < len(vals):
            flags.append("sentinel_readings")
        if conv == "negative_below_ground":
            used = [-v for v in good if v <= 0]
        elif conv == "positive_depth":
            used = [v for v in good if v >= 0]
        else:
            used = []
            flags.append("ambiguous_sign_convention" if conv == "ambiguous" else "no_values")
        if good and len(used) < len(good) and conv in ("negative_below_ground", "positive_depth"):
            flags.append("sign_outliers_removed")
        wd = well_depth.get(key)
        try:
            wdv = float(wd) if wd else None
        except (TypeError, ValueError):
            wdv = None
        if wdv:
            over = [u for u in used if u > wdv + 0.5]
            if over:
                flags.append("readings_exceed_well_depth")
                used = [u for u in used if u <= wdv + 0.5]
        if used and max(used) > MAX_PLAUSIBLE_DEPTH:
            flags.append("implausible_depth")
            used = [u for u in used if u <= MAX_PLAUSIBLE_DEPTH]
        if d > today or d < "1950":
            flags.append("bad_date")
            used = []
        usable = 1 if used else 0
        td.append((key, d, len(vals), len(used), min(used) if used else None,
                   round(sum(used) / len(used), 3) if used else None, max(used) if used else None,
                   min(vals), max(vals), ",".join(flags) or "ok", usable))
        if len(td) > 50000:
            con.executemany("INSERT INTO telemetry_daily VALUES (?,?,?,?,?,?,?,?,?,?,?)", td)
            n_td += len(td)
            td = []
    con.executemany("INSERT INTO telemetry_daily VALUES (?,?,?,?,?,?,?,?,?,?,?)", td)
    n_td += len(td)
    con.executescript("DROP TABLE stage_manual; DROP TABLE stage_tele;")
    log(f"telemetry station-days written: {n_td}")

    # ---------- station stats ----------
    # index first: the correlated subqueries below would otherwise full-scan observations once per station
    con.execute("CREATE INDEX IF NOT EXISTS ix_obs_station ON observations(station_key, obs_date)")
    con.executescript("""
    UPDATE stations SET
      n_manual = (SELECT COUNT(*) FROM observations o WHERE o.station_key = stations.station_key),
      n_telemetry_days = (SELECT COUNT(*) FROM telemetry_daily t WHERE t.station_key = stations.station_key);
    UPDATE stations SET
      first_date = MIN(COALESCE((SELECT MIN(obs_date) FROM observations o WHERE o.station_key = stations.station_key), '9999'),
                       COALESCE((SELECT MIN(obs_date) FROM telemetry_daily t WHERE t.station_key = stations.station_key), '9999')),
      last_date = MAX(COALESCE((SELECT MAX(obs_date) FROM observations o WHERE o.station_key = stations.station_key), ''),
                      COALESCE((SELECT MAX(obs_date) FROM telemetry_daily t WHERE t.station_key = stations.station_key), ''));
    """)

    # ---------- station_season and district summaries (usable manual only) ----------
    per = defaultdict(list)
    for (k, depth, y, s) in con.execute("SELECT station_key, depth_mbgl, year, season FROM observations "
                                        "WHERE usable=1 AND season IS NOT NULL AND season!='other'"):
        per[(k, y, s)].append(depth)
    con.executemany("INSERT INTO station_season VALUES (?,?,?,?,?)",
                    [(k, y, s, round(statistics.median(v), 3), len(v)) for (k, y, s), v in per.items()])
    smeta = {r[0]: r[1:] for r in con.execute("SELECT station_key, agency, state, district, district_gwra FROM stations")}
    grp = defaultdict(list)
    for (k, y, s), v in per.items():
        a, st, d, dg = smeta[k]
        grp[(a, st, d, dg, y, s)].append(statistics.median(v))
    rows = []
    for (a, st, d, dg, y, s), v in grp.items():
        v = sorted(v)
        rows.append((a, st, d, dg, y, s, len(v), round(statistics.median(v), 3), round(sum(v) / len(v), 3),
                     round(pct(v, 0.1), 3), round(pct(v, 0.9), 3), v[0], v[-1]))
    con.executemany("INSERT INTO district_season_summary VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", rows)

    # ---------- download windows and publications ----------
    for r in C.read_csv(C.LOGS / "indiawris_windows_done.csv"):
        con.execute("INSERT INTO download_windows VALUES (?,?,?,?,?,?,?,?,?)",
                    (r["agency"], r["state"], r["district"], r["start"], r["end"], r["pages"], r["rows"],
                     r["status"], r["time_utc"]))
    dl = {x["pub_id"]: x for x in C.read_csv(C.CATALOG / "cgwb_downloads.csv") if x["status"] == "ok"}
    dl_any = {}
    for x in C.read_csv(C.CATALOG / "cgwb_downloads.csv"):
        dl_any[x["pub_id"]] = x
    for r in C.read_csv(C.CATALOG / "cgwb_publications_catalog.csv"):
        d = dl.get(r["pub_id"]) or {}
        pages = None
        if d.get("file"):
            pages = pdf_pages(C.ROOT / d["file"])
        con.execute("INSERT INTO publications VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (int(r["pub_id"]), r["title"], r["category"], r["state"], r["district"], r["year_of_issue"],
                     r["detail_url"], r["download_url"], 1 if d else 0, d.get("file"), d.get("sha256"),
                     int(d["bytes"]) if d.get("bytes") else None, pages,
                     (dl_any.get(r["pub_id"]) or {}).get("status")))
    gh = C.EXTRACTED / "gwra_category_history.csv"
    for r in C.read_csv(gh):
        con.execute("INSERT INTO gwra_category_history VALUES (?,?,?,?,?,?,?,?,?)",
                    (r["state"], r["district"], r["assessment_unit"], r["assessment_year"], r["category"],
                     float(r["stage_of_extraction_pct"]) if r.get("stage_of_extraction_pct") else None,
                     r["source_id"], int(r["source_page"]) if r.get("source_page") else None, r.get("quality_flag")))
    con.executescript(INDEXES)
    meta = {"build_version": BUILD_VERSION, "built_utc": C.now_utc(), "raw_pages": str(n_files),
            "existing_groundwater_db_sha256": C.sha256_file(C.EXISTING_DB) if C.EXISTING_DB.exists() else "",
            "note": "Monitoring data from official public sources. Not a substitute for site investigation."}
    con.executemany("INSERT INTO meta VALUES (?,?)", meta.items())
    con.commit()
    con.execute("VACUUM")
    con.close()
    return meta


def pdf_pages(p: Path):
    try:
        data = p.read_bytes()
    except OSError:
        return None
    import re
    m = re.findall(rb"/Type\s*/Page[^s]", data)
    return len(m) or None


def integrity(path: Path) -> list[tuple[str, str, str]]:
    con = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)
    out = []
    def chk(name, sql, ok):
        try:
            v = con.execute(sql).fetchone()[0]
            out.append((name, "pass" if ok(v) else "FAIL", str(v)))
        except Exception as e:  # noqa: BLE001
            out.append((name, "FAIL", repr(e)))
    chk("sqlite_integrity_check", "PRAGMA integrity_check", lambda v: v == "ok")
    chk("foreign_keys_obs_station", "SELECT COUNT(*) FROM observations o LEFT JOIN stations s USING(station_key) "
        "WHERE s.station_key IS NULL", lambda v: v == 0)
    chk("foreign_keys_obs_file", "SELECT COUNT(*) FROM observations o LEFT JOIN raw_files f USING(file_id) "
        "WHERE f.file_id IS NULL", lambda v: v == 0)
    chk("telemetry_station_fk", "SELECT COUNT(*) FROM telemetry_daily t LEFT JOIN stations s USING(station_key) "
        "WHERE s.station_key IS NULL", lambda v: v == 0)
    chk("usable_have_depth", "SELECT COUNT(*) FROM observations WHERE usable=1 AND depth_mbgl IS NULL", lambda v: v == 0)
    chk("usable_depth_range", "SELECT COUNT(*) FROM observations WHERE usable=1 AND (depth_mbgl<0 OR depth_mbgl>300)",
        lambda v: v == 0)
    chk("every_station_has_source", "SELECT COUNT(*) FROM stations WHERE source_id IS NULL", lambda v: v == 0)
    chk("raw_files_have_sha256", "SELECT COUNT(*) FROM raw_files WHERE length(sha256)!=64", lambda v: v == 0)
    chk("no_exact_duplicate_obs", "SELECT COUNT(*) FROM (SELECT station_key, obs_time, value_raw, COUNT(*) c FROM "
        "observations GROUP BY 1,2,3 HAVING c>1)", lambda v: v == 0)
    chk("summary_counts_positive", "SELECT COUNT(*) FROM district_season_summary WHERE n_stations<1", lambda v: v == 0)
    con.close()
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", default=str(C.RAW))
    ap.add_argument("--no-promote", action="store_true")
    args = ap.parse_args()
    C.ensure_dirs()
    before = C.assert_existing_db_untouched(C.EXPECTED_EXISTING_DB_SHA256) if C.EXISTING_DB.exists() else ""
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    scratch = C.SCRATCH / f"groundwater_monitoring_{stamp}.db"
    logf = open(C.LOGS / f"build_{stamp}.log", "w", encoding="utf-8")
    def log(m):
        print(m)
        logf.write(m + "\n")
        logf.flush()
    meta = build(Path(args.raw), scratch, log)
    checks = integrity(scratch)
    for c in checks:
        log(" ".join(c))
    import csv
    with open(C.REPORTS / "database_integrity_checks.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["check", "result", "value"])
        w.writerows(checks)
    failed = [c for c in checks if c[1] != "pass"]
    if failed:
        log(f"NOT promoted: {len(failed)} integrity checks failed; scratch kept at {scratch}")
        sys.exit(1)
    if not args.no_promote:
        if C.MONITORING_DB.exists():
            prev = C.SCRATCH / "previous"
            prev.mkdir(parents=True, exist_ok=True)
            shutil.move(str(C.MONITORING_DB), str(prev / f"groundwater_monitoring_replaced_{stamp}.db"))
        shutil.copy2(scratch, C.MONITORING_DB)
        log(f"promoted to {C.MONITORING_DB} (sha256 {C.sha256_file(C.MONITORING_DB)})")
    after = C.assert_existing_db_untouched(C.EXPECTED_EXISTING_DB_SHA256) if C.EXISTING_DB.exists() else ""
    log(f"groundwater.db sha256 before {before} after {after}")


if __name__ == "__main__":
    main()

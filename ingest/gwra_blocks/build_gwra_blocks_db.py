"""Build data/monitoring/gwra_blocks_2025.db from the matched unit rows (match_blocks.py output).
groundwater.db is opened read-only and never changed. Nothing is estimated: every number is copied from a CGWB
state report, and each row records which arithmetic checks it passed."""
import argparse, collections, csv, datetime, hashlib, json, os, re, sqlite3, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from match_blocks import rect_records, checks, key, F
from normalize import ncat

SCHEMA = """
CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE sources (pub_id TEXT PRIMARY KEY, state TEXT, title TEXT, year_of_issue TEXT, assessment_year TEXT,
  detail_url TEXT, download_url TEXT, file TEXT, bytes INTEGER, sha256 TEXT, used_for TEXT, note TEXT);
CREATE TABLE unit_resources (
  state TEXT NOT NULL, district TEXT NOT NULL, assessment_unit TEXT NOT NULL, assessment_year TEXT NOT NULL,
  status TEXT NOT NULL, usable INTEGER NOT NULL,
  recharge_ham REAL, natural_discharge_ham REAL, extractable_ham REAL,
  irrigation_ham REAL, industrial_ham REAL, domestic_ham REAL, total_extraction_ham REAL,
  allocation_domestic_ham REAL, net_availability_ham REAL, stage_pct REAL,
  category_in_report TEXT, category_official TEXT, category_agrees INTEGER,
  checks TEXT, source_pub_id TEXT REFERENCES sources(pub_id), source_page INTEGER, method TEXT,
  name_in_source TEXT, district_in_source TEXT, filled_from TEXT, other_sources_disagree TEXT, note TEXT,
  PRIMARY KEY (state, district, assessment_unit, assessment_year));
CREATE TABLE tn_firka_resources (
  district TEXT NOT NULL, firka TEXT NOT NULL, assessment_year TEXT NOT NULL, status TEXT NOT NULL, usable INTEGER NOT NULL,
  recharge_ham REAL, natural_discharge_ham REAL, extractable_ham REAL, irrigation_ham REAL, industrial_ham REAL,
  domestic_ham REAL, total_extraction_ham REAL, allocation_domestic_ham REAL, net_availability_ham REAL, stage_pct REAL,
  category_in_report TEXT, checks TEXT, source_pub_id TEXT, source_page INTEGER, PRIMARY KEY (district, firka, assessment_year));
CREATE TABLE coverage_by_state (state TEXT PRIMARY KEY, official_units INTEGER, verified INTEGER, verified_stage INTEGER,
  zero_resource INTEGER, stage_only INTEGER, partial INTEGER, checks_failed INTEGER, category_conflict INTEGER, not_found INTEGER,
  usable INTEGER, note TEXT);
CREATE TABLE district_crosscheck (state TEXT, district TEXT, official_units INTEGER, units_verified INTEGER,
  sum_recharge_ham REAL, nc2025_recharge_ham REAL, sum_extraction_ham REAL, nc2025_extraction_ham REAL, result TEXT,
  PRIMARY KEY (state, district));
CREATE TABLE status_codes (status TEXT PRIMARY KEY, usable INTEGER, meaning TEXT);
CREATE INDEX ix_unit_state_district ON unit_resources(state, district);
CREATE INDEX ix_unit_name ON unit_resources(assessment_unit);
"""
STATUS = [
    ("verified", 1, "All three GEC-2015 identities hold: extractable = recharge - natural discharge; total = irrigation + industrial + domestic; stage = total / extractable x 100."),
    ("verified_stage", 1, "Extractable resource, total extraction and stage are printed and stage = total / extractable x 100 holds; recharge components not printed in a readable table."),
    ("zero_resource", 1, "The report prints zero resource and zero extraction and no stage (typically saline units)."),
    ("stage_only", 1, "Only the stage of extraction and category are printed for this unit in the state report."),
    ("partial", 1, "Some figures printed; every check that can be made on them holds. Show only the figures present."),
    ("checks_failed", 0, "Figures were read but an arithmetic check failed; not used."),
    ("category_conflict", 0, "The state report's category differs from the national 2025 list for this unit; held back until resolved."),
    ("not_found", 0, "No unit-level figures for this unit in the downloaded 2025 state report."),
]
STATE_NOTES = {
    "Telangana": "The 2025 state report (CGWB pub 2123) has only district-level tables; no mandal-level table.",
    "Odisha": "The 2025 state report (pub 2129) has district-level tables and a table of the 10 semi-critical blocks only.",
    "Mizoram": "The 2025 state report (pub 2117) has district-level tables only.",
    "Goa": "The 2025 state report (pub 2104) has no taluk-level resource table in text form.",
    "Lakshadweep": "The 2025 state report (pub 2112) has no island-level resource table in text form.",
    "Chandigarh": "The 2025 report (pub 2100) has no readable unit table; the UT is a single unit.",
    "Punjab": "No 2025 Punjab state report with block tables is in the CGWB warehouse (pub 1843 is a 3-page summary); the 2024 report (pub 1542) is a different year and is not used.",
    "Tamil Nadu": "The 2025 state report (pub 2122) gives figures for 1,202 firkas, while the national 2025 list has 313 taluk-level units. Firka figures are kept in tn_firka_resources and are not attached to the taluk units.",
    "Uttarakhand": "The 2025 state report (pub 2126) lists stage and category per unit but no unit-level recharge table.",
}

def sha(fp):
    h = hashlib.sha256()
    with open(fp, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""): h.update(b)
    return h.hexdigest()

def fnum(x):
    return None if x in (None, "") else float(x)

def classify_status(r):
    if r["status"] == "not_found": return "not_found"
    v = {f: fnum(r[f]) for f in F}
    c = checks(v)
    if c and not all(c.values()): return "checks_failed"
    if len(c) == 3: return "verified"
    if v["extractable"] == 0 and (v["total_extraction"] in (0, None)) and v["stage_pct"] is None: return "zero_resource"
    if c.get("stage_identity"): return "verified_stage"
    if v["stage_pct"] is not None and all(v[f] is None for f in F if f != "stage_pct"): return "stage_only"
    return "partial"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--matched", required=True)
    ap.add_argument("--tables", required=True, help="directory of dump_tables.py output")
    ap.add_argument("--groundwater-db", required=True)
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--pdf-dir", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    if os.path.exists(a.out): sys.exit(f"{a.out} exists; refusing to overwrite")
    con = sqlite3.connect(a.out); con.executescript(SCHEMA)
    con.executemany("INSERT INTO status_codes VALUES (?,?,?)", STATUS)
    usable_status = {s for s, u, _ in STATUS if u}
    # sources
    cat = {r["pub_id"]: r for r in csv.DictReader(open(a.catalog, encoding="utf-8"))}
    pdfs = {f[:5].lstrip("0"): f for f in os.listdir(a.pdf_dir) if f.endswith(".pdf")}
    rows = list(csv.DictReader(open(a.matched)))
    used = collections.Counter(r["source_pub"].lstrip("0") for r in rows if r.get("source_pub"))
    for pid in sorted(set(used) | {"2122"}):
        c = cat.get(pid, {}); fp = os.path.join(a.pdf_dir, pdfs[pid]) if pid in pdfs else None
        con.execute("INSERT INTO sources VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                    (pid, c.get("state"), c.get("title"), c.get("year_of_issue"), "2025", c.get("detail_url"), c.get("download_url"),
                     os.path.join("data", "monitoring", "raw", "cgwb_publications", pdfs.get(pid, "")) if fp else None,
                     os.path.getsize(fp) if fp else None, sha(fp) if fp else None, "unit-level GWRA 2025 figures", None))
    # unit rows (Tamil Nadu and Punjab are not attached: see STATE_NOTES)
    gw = sqlite3.connect(f"file:{a.groundwater_db}?mode=ro", uri=True)
    off = {(s, d, u): cat_ for s, d, u, cat_ in gw.execute("select state, district, assessment_unit, category from groundwater_assessment")}
    cov = collections.defaultdict(collections.Counter)
    for r in rows:
        st = r["state"]
        if st in ("Tamil Nadu", "Punjab") and r["status"] != "not_found":
            r = {k: r[k] for k in ("state", "district", "assessment_unit", "official_category")} | {"status": "not_found"}
        s = classify_status(r)
        rc0 = r.get("report_category") or None
        if s != "not_found" and rc0 and rc0 != r["official_category"]:
            s = "category_conflict"
        cov[st][s] += 1
        v = {f: fnum(r.get(f)) for f in F}
        rc = r.get("report_category") or None
        agrees = None if not rc else int(rc == r["official_category"])
        note = STATE_NOTES.get(st) if s == "not_found" else None
        con.execute("INSERT INTO unit_resources VALUES (" + ",".join("?" * 28) + ")",
                    (st, r["district"], r["assessment_unit"], "2025", s, int(s in usable_status),
                     v["recharge"], v["natural_discharge"], v["extractable"], v["irrigation"], v["industrial"], v["domestic"],
                     v["total_extraction"], v["allocation_domestic"], v["net_availability"], v["stage_pct"],
                     rc, r["official_category"], agrees, r.get("checks") or None,
                     (r.get("source_pub") or "").lstrip("0") or None, int(r["source_page"]) if r.get("source_page") else None,
                     r.get("method") or None, r.get("name_in_source") or None, r.get("district_in_source") or None,
                     r.get("filled_from") or None, r.get("other_sources_disagree") or None, note))
    # Tamil Nadu firkas from the state report's unit annexure
    tn = rect_records("02122", json.load(open(os.path.join(a.tables, "02122.json"))))
    seen = set(); n_tn = collections.Counter()
    for r in tn:
        if not r.get("district_raw"): continue
        k = (r["district_raw"].upper(), r["unit_raw"].upper())
        if k in seen: continue
        seen.add(k)
        c = checks(r)
        s = "verified" if len(c) == 3 and all(c.values()) else ("checks_failed" if c and not all(c.values()) else "partial")
        if s == "partial" and r["extractable"] == 0 and r["stage_pct"] is None: s = "zero_resource"
        n_tn[s] += 1
        con.execute("INSERT INTO tn_firka_resources VALUES (" + ",".join("?" * 19) + ")",
                    (k[0], k[1], "2025", s, int(s in usable_status), r["recharge"], r["natural_discharge"], r["extractable"],
                     r["irrigation"], r["industrial"], r["domestic"], r["total_extraction"], r["allocation_domestic"],
                     r["net_availability"], r["stage_pct"], ncat(r["category_raw"]), ";".join(f"{x}={'ok' if y else 'FAIL'}" for x, y in c.items()),
                     "2122", r["page"]))
    # coverage
    for st, c in sorted(cov.items()):
        con.execute("INSERT INTO coverage_by_state VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                    (st, sum(c.values()), c["verified"], c["verified_stage"], c["zero_resource"], c["stage_only"], c["partial"],
                     c["checks_failed"], c["category_conflict"], c["not_found"], sum(c[s] for s in usable_status), STATE_NOTES.get(st)))
    # district cross-check against NC2025 Annexure II (national_district_summary in groundwater.db, ham)
    nds = {(key(s), key(d)): (r_, t_) for s, d, r_, t_ in gw.execute("select state, district, annual_recharge, total_extraction from national_district_summary")}
    groups = con.execute("""select state, district, count(*), sum(status='verified'), sum(recharge_ham), sum(total_extraction_ham)
                            from unit_resources group by state, district""").fetchall()
    for st, d, n, nv, sr, se in groups:
        nd = nds.get((key(st), key(d)))
        if nv < n: res = "not_all_units_verified"
        elif not nd: res = "district_not_in_nc2025_by_this_name"
        else:
            okr = abs(sr - nd[0]) <= max(2, 0.005 * nd[0]); oke = abs(se - nd[1]) <= max(2, 0.005 * nd[1])
            res = "match" if okr and oke else ("extraction_matches_recharge_differs" if oke else ("recharge_matches_extraction_differs" if okr else "both_differ"))
        con.execute("INSERT INTO district_crosscheck VALUES (?,?,?,?,?,?,?,?,?)",
                    (st, d, n, nv, sr, nd[0] if nd else None, se, nd[1] if nd else None, res))
    meta = {"built_utc": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "assessment_year": "2025",
            "units": "ham (hectare-metres); stage in percent", "unit_list": "groundwater.db groundwater_assessment (AI2025, 6,762 units)",
            "groundwater_db_sha256": sha(a.groundwater_db), "method": "ruled-table reading with header mapping, plus text lines whose numbers satisfy the GEC-2015 identities; matched to the official unit list by name",
            "tn_firkas": json.dumps(dict(n_tn))}
    con.executemany("INSERT INTO meta VALUES (?,?)", meta.items())
    con.commit()
    print(dict(sum(cov.values(), collections.Counter())), "TN firkas", dict(n_tn))
    print(con.execute("pragma integrity_check").fetchone(), con.execute("select result, count(*) from district_crosscheck group by 1").fetchall())

if __name__ == "__main__":
    main()

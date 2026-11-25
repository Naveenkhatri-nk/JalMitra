"""
Write the JalMitra 4.0 data reports from data/groundwater_monitoring.db and the download logs.

Output folder: data/monitoring/reports/
  SOURCE_CATALOGUE.md, DATA_DICTIONARY.md, GEOGRAPHIC_COVERAGE.md (+ geographic_coverage_*.csv),
  HISTORICAL_COVERAGE.md (+ historical_coverage_*.csv), MISSING_DATA.md (+ missing_*.csv),
  VALIDATION_REPORT.md (+ validation_summary.csv), DATABASE_INTEGRITY.md, INACCESSIBLE_DATASETS.md,
  DATASET_INVENTORY.csv (every original file with SHA256)

Every number in these reports is counted from the database or the logs; nothing is typed in by hand.
"""
from __future__ import annotations

import csv
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402

R = C.REPORTS

INACCESSIBLE = [  # (dataset, url, what happened, date, next step)
    ("INGRES (India Ground Water Resource Estimation System)", "https://ingres.iith.ac.in",
     "Site did not load from the user's computer (navigation failed) on 23 Nov 2026", "2026-11-23",
     "Retry later; GWRA reports from the CGWB warehouse are used instead"),
    ("data.gov.in OGD groundwater datasets (API)", "https://data.gov.in",
     "API needs a personal API key; not registered on the user's behalf", "2026-11-23",
     "naveen can create a key and put it in .env as DATA_GOV_IN_API_KEY (optional; India-WRIS already covers levels)"),
    ("CGWB WIMS", "-", "Authorised users only; not used", "2026-11-23", "none"),
    ("India-WRIS groundwater QUALITY", "https://indiawris.gov.in/swagger-ui/index.html",
     "No groundwater-quality endpoint in the public API (levels only)", "2026-11-23",
     "CGWB annual groundwater quality reports (PDF) are catalogued instead"),
    ("CGWB website terms page", "https://cgwb.gov.in/en/terms-conditions", "HTTP 500 on 23 Nov 2026", "2026-11-23",
     "Re-check licence text when the page works"),
    ("State ground-water agencies other than Rajasthan (India-WRIS)", "https://indiawris.gov.in",
     "Not downloaded in this run (national scope = CGWB only)", "2026-11-23",
     "Run download_indiawris_gwl.py with an added agency if wanted"),
]


def q(con, sql, p=()):
    return con.execute(sql, p).fetchall()


def write_csv(name, header, rows):
    with open(R / name, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)


def md_table(header, rows, limit=None):
    rows = list(rows)
    out = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    for r in rows[:limit] if limit else rows:
        out.append("| " + " | ".join("" if v is None else str(v) for v in r) + " |")
    if limit and len(rows) > limit:
        out.append(f"\n_{len(rows) - limit} more rows in the CSV file._")
    return "\n".join(out)


def main():
    C.ensure_dirs()
    db = C.MONITORING_DB if len(sys.argv) < 2 else Path(sys.argv[1])
    con = sqlite3.connect(f"file:{db.as_posix()}?mode=ro", uri=True)
    meta = dict(q(con, "SELECT key, value FROM meta"))
    head = f"_Built {meta.get('built_utc')} by build_monitoring_db.py {meta.get('build_version')}. " \
           f"Counts come from `data/groundwater_monitoring.db`._\n"

    # ---------- source catalogue ----------
    src = q(con, "SELECT source_id, title, publisher, url, access, licence, licence_evidence FROM sources")
    pubs = q(con, "SELECT pub_id, category, state, year_of_issue, title, downloaded, download_status, bytes, sha256, "
                  "detail_url FROM publications ORDER BY category, state, year_of_issue")
    write_csv("source_catalogue_publications.csv", ["pub_id", "category", "state", "year_of_issue", "title",
              "downloaded", "download_status", "bytes", "sha256", "detail_url"], pubs)
    cat_counts = q(con, "SELECT category, COUNT(*), SUM(downloaded) FROM publications GROUP BY 1 ORDER BY 2 DESC")
    (R / "SOURCE_CATALOGUE.md").write_text(
        "# Source catalogue\n\n" + head + "\n## Data sources\n\n" +
        md_table(["ID", "Title", "Publisher", "URL", "Access", "Licence", "Licence evidence"], src) +
        "\n\n## CGWB publications catalogued\n\nEvery publication page in the CGWB warehouse was read; the full list "
        "is `source_catalogue_publications.csv`.\n\n" + md_table(["Category", "Catalogued", "Downloaded"], cat_counts) +
        "\n", encoding="utf-8")

    # ---------- data dictionary ----------
    lines = ["# Data dictionary: groundwater_monitoring.db\n", head]
    for (name, sql) in q(con, "SELECT name, sql FROM sqlite_master WHERE type='table' ORDER BY name"):
        n = q(con, f'SELECT COUNT(*) FROM "{name}"')[0][0]
        lines.append(f"## {name} ({n:,} rows)\n\n```sql\n{sql}\n```\n")
    lines.append("## Rules applied\n\n" + md_table(["Rule", "Applies to", "Rule", "Consequence"],
                                                  q(con, "SELECT * FROM rules")))
    lines.append("\n## Quality flags\n\n" + md_table(["quality_flag (observations)", "rows", "usable"],
                 q(con, "SELECT quality_flag, COUNT(*), SUM(usable) FROM observations GROUP BY 1 ORDER BY 2 DESC")))
    (R / "DATA_DICTIONARY.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    # ---------- geographic coverage ----------
    geo_state = q(con, """SELECT s.state, s.agency, COUNT(DISTINCT s.district) districts,
        COUNT(DISTINCT s.station_key) stations, SUM(s.n_manual) manual_rows,
        (SELECT COUNT(*) FROM observations o JOIN stations s2 USING(station_key) WHERE s2.state=s.state AND s2.agency=s.agency AND o.usable=1) usable,
        SUM(s.n_telemetry_days) telemetry_days
        FROM stations s GROUP BY s.state, s.agency ORDER BY s.state, s.agency""")
    write_csv("geographic_coverage_states.csv", ["state", "agency", "districts_with_stations", "stations",
              "manual_rows", "usable_manual_rows", "telemetry_station_days"], geo_state)
    geo_dist = q(con, """SELECT s.state, s.district, s.district_gwra, s.agency, COUNT(*) stations,
        SUM(CASE WHEN s.coord_flag='ok' THEN 1 ELSE 0 END) coords_ok, SUM(s.n_manual), SUM(s.n_telemetry_days),
        MIN(s.first_date), MAX(s.last_date)
        FROM stations s GROUP BY 1,2,3,4 ORDER BY 1,2,4""")
    write_csv("geographic_coverage_districts.csv", ["state", "district_wris", "district_gwra", "agency", "stations",
              "stations_coords_ok", "manual_rows", "telemetry_station_days", "first_date", "last_date"], geo_dist)
    gw = {}
    if C.EXISTING_DB.exists():
        e = sqlite3.connect(f"file:{C.EXISTING_DB.as_posix()}?mode=ro", uri=True)
        for st, n in e.execute("SELECT state, COUNT(DISTINCT district) FROM groundwater_assessment GROUP BY 1"):
            gw[st.lower()] = n
        e.close()
    have = defaultdict(set)
    for st, dg in q(con, "SELECT DISTINCT state, district_gwra FROM stations WHERE district_gwra IS NOT NULL"):
        have[(st or "").lower()].add(dg)
    gap_rows = [(st, gw[st], len(have.get(st, ())), gw[st] - len(have.get(st, ()))) for st in sorted(gw)]
    coords = q(con, "SELECT coord_flag, COUNT(*) FROM stations GROUP BY 1 ORDER BY 2 DESC")
    (R / "GEOGRAPHIC_COVERAGE.md").write_text(
        "# Geographic coverage\n\n" + head +
        "\nCoverage means at least one station record was received; it does not mean every part of a district is "
        "monitored.\n\n## By state and agency\n\n" +
        md_table(["State", "Agency", "Districts", "Stations", "Manual rows", "Usable manual", "Telemetry days"], geo_state) +
        "\n\n## Districts of the GWRA 2025 list with at least one monitoring station\n\n" +
        md_table(["State (GWRA spelling)", "GWRA districts", "with stations", "without"], gap_rows) +
        "\n\n## Station coordinate checks\n\n" + md_table(["coord_flag", "stations"], coords) +
        "\n\nDistrict-level detail: `geographic_coverage_districts.csv`.\n", encoding="utf-8")

    # ---------- historical coverage ----------
    hist = q(con, """SELECT s.state, s.agency, o.year, COUNT(DISTINCT o.station_key), COUNT(*), SUM(o.usable)
        FROM observations o JOIN stations s USING(station_key) GROUP BY 1,2,3 ORDER BY 1,2,3""")
    write_csv("historical_coverage_state_year.csv", ["state", "agency", "year", "stations", "manual_rows",
              "usable_rows"], hist)
    tel = q(con, """SELECT s.state, s.agency, substr(t.obs_date,1,4) y, COUNT(DISTINCT t.station_key), COUNT(*), SUM(t.usable)
        FROM telemetry_daily t JOIN stations s USING(station_key) GROUP BY 1,2,3 ORDER BY 1,2,3""")
    write_csv("historical_coverage_telemetry.csv", ["state", "agency", "year", "stations", "station_days",
              "usable_station_days"], tel)
    span = q(con, """SELECT s.state, s.agency, MIN(o.year), MAX(o.year), COUNT(DISTINCT o.year)
        FROM observations o JOIN stations s USING(station_key) WHERE o.usable=1 GROUP BY 1,2 ORDER BY 1,2""")
    raj = [r for r in hist if (r[0] or "").lower() == "rajasthan"]
    long_st = q(con, """SELECT s.agency, COUNT(*) FROM (SELECT station_key, COUNT(DISTINCT year) ny FROM station_season
        WHERE season='pre_monsoon' GROUP BY 1) x JOIN stations s USING(station_key) WHERE x.ny>=10 GROUP BY 1""")
    (R / "HISTORICAL_COVERAGE.md").write_text(
        "# Historical coverage\n\n" + head + "\n## Span of usable manual measurements\n\n" +
        md_table(["State", "Agency", "First year", "Last year", "Years with data"], span) +
        "\n\n## Rajasthan by year (manual)\n\n" + md_table(["State", "Agency", "Year", "Stations", "Rows", "Usable"], raj) +
        "\n\n## Stations with 10 or more years of pre-monsoon measurements\n\n" + md_table(["Agency", "Stations"], long_st) +
        "\n\nAll states: `historical_coverage_state_year.csv`; telemetry: `historical_coverage_telemetry.csv`.\n",
        encoding="utf-8")

    # ---------- missing data ----------
    miss_fields = q(con, """SELECT 'latitude/longitude', SUM(latitude IS NULL OR longitude IS NULL) FROM stations
        UNION ALL SELECT 'well_depth_m', SUM(well_depth_m IS NULL) FROM stations
        UNION ALL SELECT 'well_type', SUM(well_type IS NULL OR well_type='') FROM stations
        UNION ALL SELECT 'aquifer_type (missing or Not Available)', SUM(aquifer_type IS NULL OR aquifer_type IN ('','Not Available')) FROM stations
        UNION ALL SELECT 'block', SUM(block IS NULL OR block='') FROM stations
        UNION ALL SELECT 'district not matched to GWRA name', SUM(district_gwra IS NULL) FROM stations""")
    nst = q(con, "SELECT COUNT(*) FROM stations")[0][0]
    empty_w = q(con, "SELECT agency, state, COUNT(*), SUM(status='empty'), SUM(status LIKE 'ok_end_on_empty%') "
                     "FROM download_windows GROUP BY 1,2 ORDER BY 1,2")
    write_csv("missing_download_windows.csv", ["agency", "state", "windows", "empty_windows", "ended_on_empty_page"], empty_w)
    unmatched = q(con, "SELECT wris_state, wris_district, method FROM district_name_map WHERE gwra_district IS NULL")
    write_csv("missing_district_matches.csv", ["wris_state", "wris_district", "reason"], unmatched)
    seasons_missing = q(con, """SELECT s.state, s.district_gwra, COUNT(DISTINCT CASE WHEN ss.season='pre_monsoon' THEN ss.year END),
        COUNT(DISTINCT CASE WHEN ss.season='post_monsoon' THEN ss.year END)
        FROM stations s LEFT JOIN station_season ss USING(station_key) WHERE s.state='Rajasthan' GROUP BY 1,2 ORDER BY 1,2""")
    gaps = [(st, gw[st] - len(have.get(st, ()))) for st in sorted(gw) if gw[st] - len(have.get(st, ())) > 0]
    (R / "MISSING_DATA.md").write_text(
        "# Missing data\n\n" + head + f"\n## Station fields missing ({nst:,} stations)\n\n" +
        md_table(["Field", "Stations missing it"], miss_fields) +
        "\n\n## GWRA districts with no monitoring station received\n\n" + md_table(["State", "Districts"], gaps) +
        "\n\n## Download windows that came back empty\n\nThe India-WRIS API sometimes answers \"No data found\" for a "
        "window that has data; each empty window was asked again before being accepted as empty.\n\n" +
        md_table(["Agency", "State", "Windows", "Empty", "Ended on empty page"], empty_w) +
        "\n\n## Rajasthan districts: years with pre- and post-monsoon measurements\n\n" +
        md_table(["State", "District", "Pre-monsoon years", "Post-monsoon years"], seasons_missing) +
        f"\n\n## India-WRIS districts not matched to a GWRA district name ({len(unmatched)})\n\n"
        "See `missing_district_matches.csv`. These stations are kept but cannot be reached by place name yet.\n",
        encoding="utf-8")

    # ---------- validation ----------
    vs = q(con, "SELECT check_id, severity, COUNT(*) FROM validation_issues GROUP BY 1,2 ORDER BY 3 DESC")
    write_csv("validation_summary.csv", ["check_id", "severity", "count"], vs)
    write_csv("validation_issues.csv", ["issue_id", "check_id", "severity", "scope", "ref", "detail"],
              q(con, "SELECT * FROM validation_issues"))
    qf = q(con, "SELECT quality_flag, COUNT(*), SUM(usable) FROM observations GROUP BY 1 ORDER BY 2 DESC")
    tf = q(con, "SELECT quality_flag, COUNT(*), SUM(usable) FROM telemetry_daily GROUP BY 1 ORDER BY 2 DESC")
    conv = q(con, "SELECT agency, sign_convention, COUNT(*) FROM stations GROUP BY 1,2 ORDER BY 1,3 DESC")
    dups = q(con, "SELECT resolution, COUNT(*), SUM(n_copies) FROM duplicates GROUP BY 1")
    basis = q(con, "SELECT depth_basis, COUNT(*), SUM(usable) FROM observations GROUP BY 1")
    tot = q(con, "SELECT COUNT(*), SUM(usable) FROM observations")[0]
    (R / "VALIDATION_REPORT.md").write_text(
        "# Validation report\n\n" + head +
        f"\nManual measurements: {tot[0]:,}; usable after checks: {tot[1] or 0:,}.\n\n"
        "## Manual measurement flags\n\n" + md_table(["quality_flag", "rows", "usable"], qf) +
        "\n\n## How depth below ground was obtained\n\n" + md_table(["depth_basis", "rows", "usable"], basis) +
        "\n\n## Sign conventions per station\n\n" + md_table(["Agency", "Convention", "Stations"], conv) +
        "\n\n## Telemetry station-day flags\n\n" + md_table(["quality_flag", "station-days", "usable"], tf) +
        "\n\n## Duplicates\n\n" + md_table(["Resolution", "Groups", "Rows"], dups) +
        "\n\n## Station and file checks\n\n" + md_table(["Check", "Severity", "Count"], vs) +
        "\n\nRow-level detail: `validation_issues.csv`; rules: DATA_DICTIONARY.md.\n", encoding="utf-8")

    # ---------- integrity ----------
    integ = C.read_csv(R / "database_integrity_checks.csv")
    (R / "DATABASE_INTEGRITY.md").write_text(
        "# Database integrity\n\n" + head +
        f"\n- groundwater_monitoring.db SHA256: `{C.sha256_file(db)}`\n"
        f"- data/groundwater.db SHA256 recorded at build: `{meta.get('existing_groundwater_db_sha256')}`\n"
        f"- data/groundwater.db SHA256 now: `{C.sha256_file(C.EXISTING_DB) if C.EXISTING_DB.exists() else 'missing'}`\n"
        f"- expected (before JalMitra 4.0 work): `{C.EXPECTED_EXISTING_DB_SHA256}`\n\n" +
        md_table(["Check", "Result", "Value"], [(r["check"], r["result"], r["value"]) for r in integ]) + "\n",
        encoding="utf-8")

    # ---------- inaccessible ----------
    failed_pubs = q(con, "SELECT pub_id, title, download_status FROM publications WHERE download_status IS NOT NULL "
                         "AND download_status!='ok'")
    (R / "INACCESSIBLE_DATASETS.md").write_text(
        "# Datasets that could not be accessed or were not downloaded\n\n" +
        md_table(["Dataset", "URL", "What happened", "Date", "Next step"], INACCESSIBLE) +
        "\n\n## CGWB publications that failed to download\n\n" +
        (md_table(["ID", "Title", "Status"], failed_pubs) if failed_pubs else "None.") + "\n", encoding="utf-8")

    # ---------- inventory ----------
    inv = []
    for root in (C.RAW / "cgwb_publications", C.RAW / "indiawris_masters"):
        if root.exists():
            for p in sorted(root.rglob("*")):
                if p.is_file():
                    inv.append((p.relative_to(C.ROOT).as_posix(), p.stat().st_size, C.sha256_file(p)))
    wris = q(con, "SELECT path, bytes, sha256 FROM raw_files")
    write_csv("DATASET_INVENTORY.csv", ["path", "bytes", "sha256 (of decompressed JSON for India-WRIS pages)"],
              inv + list(wris))
    con.close()
    print("reports written to", R)


if __name__ == "__main__":
    main()

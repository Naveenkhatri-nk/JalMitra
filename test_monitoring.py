"""
test_monitoring.py - JalMitra 4.0 groundwater monitoring tests (ingest rules, database build, read-only queries).

Uses a SYNTHETIC fixture written to a temporary folder (clearly fake station codes starting with TEST);
no network, and data/groundwater.db is only hashed. If data/groundwater_monitoring.db exists, its integrity
is checked too.

Run:  python test_monitoring.py
"""
from __future__ import annotations

import csv
import gzip
import json
import socket
import sqlite3
import sys
import tempfile
import time
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE / "ingest"))
sys.path.insert(0, str(BASE))
import common as C  # noqa: E402
import build_monitoring_db as B  # noqa: E402
import monitoring_retrieval as M  # noqa: E402

RESULTS = []


def check(name, cond, detail=""):
    RESULTS.append((name, bool(cond), detail))
    print(("PASSED " if cond else "FAILED ") + name + (f"  {detail}" if detail and not cond else ""))


def row(code, value, t, agency="CGWB", mode="Manual", dtc="HGZ", lat=26.5, lon=74.6, depth=50.0,
        state="Rajasthan", district="AJMER"):
    return {"stationCode": code, "stationName": code, "stationType": "Ground Water", "latitude": lat, "longitude": lon,
            "agencyName": agency, "state": state, "district": district, "dataAcquisitionMode": mode,
            "stationStatus": "Active", "tehsil": "T", "datatypeCode": dtc,
            "description": "MANUAL-Water Level" if dtc == "HGZ" else "GPRS-Water Level", "dataValue": value,
            "dataTime": t, "unit": "m", "block": "B", "village": "V", "wellType": "Dug Well", "wellDepth": depth,
            "wellAquiferType": "Unconfined"}


def fixture(raw: Path):
    pages = {}
    a = []
    # five stations with pre-monsoon (May) data 2010..2020: depth grows 0.5 m/yr -> paired change 2015->2020 = +2.5
    for i in range(5):
        for y in range(2010, 2021):
            a.append(row(f"TEST{i:03d}", round(5 + i + 0.5 * (y - 2010), 3), f"{y}-05-15T06:00:00"))
            a.append(row(f"TEST{i:03d}", round(3 + i + 0.5 * (y - 2010), 3), f"{y}-11-05T06:00:00"))
    a.append(row("TESTSENT", -999, "2015-05-15T06:00:00"))                       # sentinel
    a.append(row("TESTNEG", -2.0, "2015-05-15T06:00:00"))                         # negative manual HGZ
    a.append(row("TESTDRY", 12.0, "2015-05-15T06:00:00", depth=12.0))             # dry well
    a.append(row("TESTDEEP", 40.0, "2015-05-15T06:00:00", depth=20.0))            # deeper than well
    a.append(row("TESTDUP", 7.0, "2016-05-15T06:00:00"))
    a.append(row("TESTDUP", 7.0, "2016-05-15T06:00:00"))                          # identical duplicate
    a.append(row("TESTCON", 7.0, "2016-05-15T06:00:00"))
    a.append(row("TESTCON", 9.0, "2016-05-15T06:00:00"))                          # conflicting duplicate
    a.append(row("TESTFUT", 7.0, "2099-05-15T06:00:00"))                          # future date
    a.append(row("TESTOUT", 7.0, "2016-05-15T06:00:00", lat=40.0, lon=100.0))     # outside India
    a.append(row("TESTBOX", 7.0, "2016-05-15T06:00:00", lat=20.0, lon=80.0))      # outside Rajasthan
    pages[("cgwb", "rajasthan", "ajmer", "2010-01-01_2019-12-31_p000")] = a
    t = []
    for d in range(1, 11):
        for h in ("00", "06", "12", "18"):
            t.append(row("TESTTEL", -20.0 - d * 0.1, f"2024-05-{d:02d}T{h}:00:00", agency="Rajasthan GW",
                         mode="Telemetric", dtc="GGZ", depth=100.0))
    t.append(row("TESTTEL", 4.5, "2024-05-03T08:00:00", agency="Rajasthan GW", mode="Telemetric", dtc="GGZ",
                 depth=100.0))                                                     # sign outlier
    for d in range(1, 5):
        t.append(row("TESTAMB", (-1) ** d * 5.0, f"2024-05-{d:02d}T00:00:00", agency="Rajasthan GW",
                     mode="Telemetric", dtc="GGZ"))                               # ambiguous sign
    pages[("rajasthan_gw", "rajasthan", "ajmer", "2024-05-01_2024-05-31_p000")] = t
    for (ag, st, di, name), data in pages.items():
        p = raw / "indiawris_gwl" / ag / st / di
        p.mkdir(parents=True, exist_ok=True)
        (p / f"{name}.json.gz").write_bytes(gzip.compress(json.dumps(
            {"statusCode": 200, "message": "Data fetched successfully", "data": data}).encode()))


def main():
    t0 = time.time()
    sha_before = C.sha256_file(C.EXISTING_DB) if C.EXISTING_DB.exists() else None
    tmp = Path(tempfile.mkdtemp(prefix="jalmitra_mon_"))
    raw = tmp / "raw"
    fixture(raw)
    db = tmp / "mon.db"
    B.build(raw, db, lambda m: None)
    checks = B.integrity(db)
    check("BUILD01_integrity_checks_pass", all(c[1] == "pass" for c in checks), str([c for c in checks if c[1] != "pass"]))
    con = sqlite3.connect(db)
    flag = lambda code: [r[0] for r in con.execute(  # noqa: E731
        "SELECT quality_flag FROM observations o WHERE station_key=?", ("CGWB|" + code,))]
    use = lambda code: [r[0] for r in con.execute(  # noqa: E731
        "SELECT usable FROM observations WHERE station_key=?", ("CGWB|" + code,))]
    check("RULE02_sentinel_not_usable", flag("TESTSENT") == ["sentinel"] and use("TESTSENT") == [0])
    check("RULE03_negative_manual_flagged", flag("TESTNEG") == ["negative_manual_value"] and use("TESTNEG") == [0])
    check("RULE03_manual_depth_kept_as_published",
          con.execute("SELECT value_raw, depth_mbgl, depth_basis FROM observations WHERE station_key='CGWB|TEST000' "
                      "AND obs_date='2010-05-15'").fetchone() == (5.0, 5.0, "published_positive_mbgl"))
    check("RULE05_deeper_than_well_flagged", flag("TESTDEEP") == ["depth_exceeds_well_depth"])
    check("RULE06_dry_well_flagged", flag("TESTDRY") == ["possible_dry_well"] and use("TESTDRY") == [0])
    check("RULE08_future_date_flagged", "bad_date" in flag("TESTFUT")[0] and use("TESTFUT") == [0])
    check("RULE12_identical_duplicate_kept_once", len(flag("TESTDUP")) == 1 and use("TESTDUP") == [1])
    check("RULE13_conflicting_duplicate_both_kept_unusable",
          sorted(flag("TESTCON")) == ["conflicting_duplicate"] * 2 and use("TESTCON") == [0, 0])
    check("RULE12_duplicates_logged", con.execute("SELECT COUNT(*) FROM duplicates").fetchone()[0] == 2)
    cf = dict(con.execute("SELECT station_code, coord_flag FROM stations"))
    check("RULE09_outside_india", "outside_india" in cf["TESTOUT"])
    check("RULE09_outside_rajasthan", "outside_state" in cf["TESTBOX"])
    check("RULE10_coarse_coordinates", "coarse" in cf["TEST000"])
    conv = dict(con.execute("SELECT station_code, sign_convention FROM stations"))
    check("RULE04_telemetry_sign_inferred", "telemetry:negative_below_ground" in conv["TESTTEL"])
    check("RULE04_ambiguous_sign", "telemetry:ambiguous" in conv["TESTAMB"])
    d3 = con.execute("SELECT n_readings, n_used, depth_min, quality_flag FROM telemetry_daily "
                     "WHERE station_key='Rajasthan GW|TESTTEL' AND obs_date='2024-05-03'").fetchone()
    check("RULE04_sign_outlier_removed", d3[0] == 5 and d3[1] == 4 and "sign_outliers_removed" in d3[3], str(d3))
    check("RULE04_ambiguous_gets_no_depth", con.execute(
        "SELECT SUM(usable) FROM telemetry_daily WHERE station_key='Rajasthan GW|TESTAMB'").fetchone()[0] == 0)
    check("RAW01_every_obs_has_file", con.execute(
        "SELECT COUNT(*) FROM observations WHERE file_id IS NULL").fetchone()[0] == 0)
    check("RAW02_value_raw_unchanged", con.execute(
        "SELECT value_raw FROM observations WHERE station_key='CGWB|TESTSENT'").fetchone()[0] == -999)
    check("MAP01_district_matched_to_gwra", con.execute(
        "SELECT gwra_district FROM district_name_map WHERE wris_district='AJMER'").fetchone()[0] == "AJMER")
    con.close()

    # ---------- read-only query module ----------
    M.close()
    h = M.district_history("Rajasthan", "Ajmer", "pre_monsoon", db_path=db)
    check("Q01_history_years", h["status"] == "ok" and [r["year"] for r in h["rows"] if r["agency"] == "CGWB"][0] == 2010)
    c = M.compare_years("Rajasthan", "AJMER", 2015, 2020, db_path=db)
    check("Q02_paired_compare", c["status"] == "ok" and c["paired_stations"] == 5 and c["median_change_m"] == 2.5
          and c["stations_deeper"] == 5, str(c))
    c2 = M.compare_years("Rajasthan", "AJMER", 2015, 2016, db_path=db)
    check("Q03_compare_excludes_unpaired_and_unusable", c2["paired_stations"] == 5, str(c2))
    c3 = M.compare_years("Rajasthan", "AJMER", 2001, 2020, db_path=db)
    check("Q04_insufficient_data_no_number", c3["status"] == "insufficient_data" and "median_change_m" not in c3)
    dc = M.decadal_change("Rajasthan", "AJMER", 2020, db_path=db)
    check("Q05_decadal_change", dc["status"] == "ok" and dc["median_change_m"] == 2.75, str(dc))
    check("Q06_unknown_district_no_data", M.district_history("Rajasthan", "NOWHERE", db_path=db)["status"] == "no_data")
    ex = M.execute({"intent": "gwl_compare", "places": [{"type": "district", "state": "Rajasthan", "district": "AJMER"}],
                    "years": [2020, 2015]}, db_path=db)
    check("Q07_execute_compare", ex["status"] == "ok" and ex["year_a"] == 2015)
    check("Q08_execute_needs_district", M.execute({"intent": "gwl_level", "places": []}, db_path=db)["status"] == "need_district")
    ts = M.telemetry_summary("Rajasthan", "AJMER", db_path=db)
    check("Q09_telemetry_separate", ts["status"] == "ok" and ts["rows"][0]["stations"] == 1)
    try:
        M._q("DELETE FROM stations", db_path=db)
        ro = False
    except sqlite3.Error:
        ro = True
    check("Q10_read_only", ro)
    try:
        M._q("SELECT * FROM sqlite_master; DROP TABLE stations", db_path=db)
        ro2 = False
    except (sqlite3.Error, sqlite3.ProgrammingError, Exception):
        ro2 = True
    check("Q11_no_multi_statement", ro2)
    check("Q12_missing_db", M.execute({"intent": "gwl_level"}, db_path=tmp / "absent.db")["status"] == "monitoring_db_missing")

    import monitoring_retrieval as MR
    check("Q13_unit_rename_key", MR._unit_key("Sanganer_Rural") == MR._unit_key("SANGANER") == "SANGANER"
          and MR._name_key("Sanganer_Rural") != MR._name_key("SANGANER"))
    hc = sqlite3.connect(db)
    hc.executemany("INSERT INTO gwra_category_history VALUES (?,?,?,?,?,?,?,?,?)", [
        ("Testland", "TESTDIST", "SANGANER", "2020", "Over-exploited", None, "T", 1, "ok"),
        ("Testland", "TESTDIST", "Sanganer_Rural", "2022", "Over-exploited", None, "T", 1, "ok"),
        ("Testland", "TESTDIST", "KOTA", "2020", "Safe", None, "T", 1, "ok"),
        ("Testland", "TESTDIST", "Kota Rural", "2022", "Safe", None, "T", 1, "ok"),
        ("Testland", "TESTDIST", "Kota Urban", "2022", "Critical", None, "T", 1, "ok")])
    hc.commit()
    hc.close()
    MR.close()
    h1 = MR.category_history("Testland", "TESTDIST", "SANGANER", db_path=db)
    check("Q14_renamed_block_followed", [r["assessment_year"] for r in h1["rows"]] == ["2020", "2022"]
          and h1.get("renamed_years") == ["2022: Sanganer_Rural"], str(h1))
    h2 = MR.category_history("Testland", "TESTDIST", "KOTA", db_path=db)
    check("Q15_rural_urban_never_merged", [r["assessment_year"] for r in h2["rows"]] == ["2020"], str(h2))
    MR.close()

    # ---------- offline ----------
    attempts = []
    real = socket.socket.connect
    socket.socket.connect = lambda self, *a, **k: attempts.append(a) or (_ for _ in ()).throw(OSError("offline test"))
    try:
        M.close()
        M.district_history("Rajasthan", "AJMER", db_path=db)
        M.compare_years("Rajasthan", "AJMER", 2015, 2020, db_path=db)
    finally:
        socket.socket.connect = real
    check("NET01_queries_offline", not attempts)

    # ---------- GWRA history extractor helpers ----------
    import extract_gwra_history as X
    check("GWRA01_district_words_moved_back",
          X.split_state("Rajasthan Sawai", "MADHOPUR") == ("Rajasthan", "Sawai MADHOPUR", True))
    check("GWRA02_state_untouched", X.split_state("Rajasthan", "AJMER") == ("Rajasthan", "AJMER", False))
    m = X._CAT_TAIL.match("GANGAVARAM (EAST GODAsafe")
    check("GWRA03_category_split", m and m.group("cat") == "safe" and m.group("unit") == "GANGAVARAM (EAST GODA")
    check("GWRA04_category_names", [X.norm_cat(c) for c in ("over_exploited", "Semi-Critical", "salinity", "x")]
          == ["Over-exploited", "Semi-critical", "Saline", None])
    hist = C.EXTRACTED / "gwra_category_history.csv"
    if hist.exists():
        rows = C.read_csv(hist)
        y25 = {(r["district"], r["assessment_unit"].upper()): r["category"] for r in rows
               if r["assessment_year"] == "2025" and r["state"] == "Rajasthan"}
        e = sqlite3.connect(f"file:{C.EXISTING_DB.as_posix()}?mode=ro", uri=True)
        ref = {(d, u.upper()): c for d, u, c in e.execute(
            "SELECT district, assessment_unit, category FROM groundwater_assessment WHERE state='Rajasthan'")}
        e.close()
        same = sum(1 for k, v in ref.items() if y25.get(k) == v)
        check("GWRA05_2025_extract_matches_groundwater_db_rajasthan", same == len(ref) == 302, f"{same}/{len(ref)}")
    else:
        print("SKIPPED GWRA05: gwra_category_history.csv not extracted yet")

    # ---------- write protection of originals ----------
    p = tmp / "orig.bin"
    C.write_new(p, b"one")
    check("SAFE01_write_new_never_overwrites", C.write_new(p, b"two") is False and p.read_bytes() == b"one")

    # ---------- real monitoring database, if built ----------
    if C.MONITORING_DB.exists():
        res = B.integrity(C.MONITORING_DB)
        check("REAL01_monitoring_db_integrity", all(r[1] == "pass" for r in res), str([r for r in res if r[1] != "pass"]))
        M.close()
        check("REAL02_monitoring_db_has_sources", len(M.sources()) >= 1)
    else:
        print("SKIPPED REAL01/REAL02: data/groundwater_monitoring.db not built yet")

    sha_after = C.sha256_file(C.EXISTING_DB) if C.EXISTING_DB.exists() else None
    check("SAFE02_groundwater_db_unchanged", sha_before == sha_after == C.EXPECTED_EXISTING_DB_SHA256,
          f"{sha_before} {sha_after}")
    M.close()
    passed = sum(1 for r in RESULTS if r[1])
    with open(BASE / "test_results_monitoring.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["test", "passed", "detail"])
        w.writerows(RESULTS)
    print(f"\nJalMitra monitoring tests: {passed} passed, {len(RESULTS) - passed} failed of {len(RESULTS)} "
          f"({time.time() - t0:.1f}s)")
    return 0 if passed == len(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(main())

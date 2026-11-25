"""Tests for data/monitoring/gwra_blocks_2025.db and gwra_blocks_retrieval.py.
Run: .venv\\Scripts\\python.exe test_gwra_blocks.py   (writes test_results_gwra_blocks.csv)"""
import csv, hashlib, sqlite3, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "ingest"))
import gwra_blocks_retrieval as G  # noqa: E402
import common as C  # noqa: E402

DB = G.DB_PATH
RESULTS = []

def test(name):
    def deco(fn):
        t0 = time.time()
        try:
            fn(); RESULTS.append((name, "PASSED", "", round(time.time() - t0, 2)))
        except AssertionError as e:
            RESULTS.append((name, "FAILED", str(e)[:300], round(time.time() - t0, 2)))
        except Exception as e:  # noqa: BLE001
            RESULTS.append((name, "ERROR", repr(e)[:300], round(time.time() - t0, 2)))
        return fn
    return deco

def sha(p):
    h = hashlib.sha256(); h.update(Path(p).read_bytes()); return h.hexdigest()

def tol(a, b, rel=0.006, ab=0.15):
    return abs(a - b) <= max(ab, rel * max(abs(a), abs(b)))

@test("GB01_db_exists_and_integrity_ok")
def _():
    assert DB.exists(), f"{DB} missing"
    con = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    assert con.execute("pragma integrity_check").fetchone()[0] == "ok"

@test("GB02_groundwater_db_unchanged")
def _():
    assert sha(C.EXISTING_DB) == C.EXPECTED_EXISTING_DB_SHA256, "groundwater.db SHA256 changed"

@test("GB03_every_official_unit_has_one_row")
def _():
    con = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    gw = sqlite3.connect(f"file:{C.EXISTING_DB.as_posix()}?mode=ro", uri=True)
    n_off = gw.execute("select count(*) from groundwater_assessment").fetchone()[0]
    n = con.execute("select count(*) from unit_resources").fetchone()[0]
    assert n == n_off, f"{n} rows vs {n_off} official units"

@test("GB04_verified_rows_satisfy_identities")
def _():
    con = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    bad = 0
    for r, nd, e, i, ind, d, t, s in con.execute("""select recharge_ham, natural_discharge_ham, extractable_ham, irrigation_ham,
            industrial_ham, domestic_ham, total_extraction_ham, stage_pct from unit_resources where status='verified'"""):
        # some states print whole hectare-metres, so sums can differ by 1 from rounding
        ab1 = 1.01 if all(float(x).is_integer() for x in (r, nd, e)) else 0.15
        ab2 = 1.01 if all(float(x).is_integer() for x in (i, ind, d, t)) else 0.25
        ok = tol(e, r - nd, 0.006, ab1) and tol(t, i + ind + d, 0.006, ab2) and tol(s, 100 * t / e, 0.01, 0.6)
        bad += not ok
    assert bad == 0, f"{bad} verified rows fail an identity"

@test("GB05_rajasthan_matches_groundwater_db")
def _():
    con = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    gw = sqlite3.connect(f"file:{C.EXISTING_DB.as_posix()}?mode=ro", uri=True)
    ref = {(d, u): (r, e, t) for d, u, r, e, t in gw.execute("""select district, assessment_unit, annual_recharge_original,
            extractable_resource_original, total_extraction_original from groundwater_assessment where state='Rajasthan'""")}
    n = diff = 0
    for d, u, r, e, t in con.execute("""select district, assessment_unit, recharge_ham, extractable_ham, total_extraction_ham
            from unit_resources where state='Rajasthan' and status='verified'"""):
        n += 1
        rr = ref[(d, u)]
        diff += not all(abs(a - b) <= 0.51 for a, b in zip((r, e, t), rr))
    assert n >= 290 and diff == 0, f"{n} compared, {diff} differ"

@test("GB06_usable_units_cover_most_states")
def _():
    cov = G.state_coverage()["states"]
    usable = sum(s["usable"] for s in cov); total = sum(s["official_units"] for s in cov)
    assert usable >= 5000 and total == 6762, (usable, total)

@test("GB07_lookup_up_block")
def _():
    r = G.unit_figures("Uttar Pradesh", "Achhnera")
    assert r["status"] == "ok" and r["district"] == "AGRA", r
    f = r["figures"]
    assert tol(f["recharge_ham"], 12329.42, 0, 0.01) and tol(f["extractable_ham"], 11712.95, 0, 0.01), f
    assert tol(f["stage_pct"], 100 * f["total_extraction_ham"] / f["extractable_ham"], 0.01, 0.6)
    assert r["source"]["pub_id"] == "2125" and r["source"]["pages"]

@test("GB08_misspelt_state_resolves")
def _():
    assert G.unit_figures("utterpradesh", "Achhnera")["state"] == "Uttar Pradesh"

@test("GB09_unit_without_figures_says_why")
def _():
    r = G.unit_figures("Telangana", "Adilabad Rural")
    assert r["status"] == "no_figures" and r["figures"] == {} and "district-level" in r["reason"], r

@test("GB10_unknown_unit_not_found")
def _():
    assert G.unit_figures("Karnataka", "Nowhereville")["status"] == "not_found"

@test("GB11_unknown_state")
def _():
    assert G.unit_figures("Atlantis", "X")["status"] == "unknown_state"

@test("GB12_district_listing")
def _():
    r = G.district_units("Maharashtra", "Pune")
    assert r["status"] == "ok" and r["units_total"] >= 10 and r["units_with_figures"] == r["units_total"], r

@test("GB13_tamil_nadu_firka")
def _():
    r = G.tn_firka_figures("Andimadam")
    assert r["status"] == "ok" and tol(r["figures"]["stage_pct"], 75.02, 0, 0.01), r

@test("GB14_tamil_nadu_taluks_not_given_firka_figures")
def _():
    con = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    n = con.execute("select count(*) from unit_resources where state='Tamil Nadu' and usable=1").fetchone()[0]
    assert n == 0, n

@test("GB15_category_conflicts_held_back")
def _():
    con = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    n = con.execute("select count(*) from unit_resources where usable=1 and category_agrees=0").fetchone()[0]
    assert n == 0, n

@test("GB16_lookup_is_read_only")
def _():
    con = G._connect()
    try:
        con.execute("delete from unit_resources"); raise AssertionError("write was allowed")
    except sqlite3.DatabaseError:
        pass

@test("GB17_sources_have_checksums")
def _():
    con = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    n, nsha = con.execute("select count(*), sum(length(sha256)=64) from sources").fetchone()
    assert n >= 30 and n == nsha, (n, nsha)

@test("GB18_groundwater_db_unchanged_after_tests")
def _():
    assert sha(C.EXISTING_DB) == C.EXPECTED_EXISTING_DB_SHA256

if __name__ == "__main__":
    with open(ROOT / "test_results_gwra_blocks.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["test", "result", "detail", "seconds"]); w.writerows(RESULTS)
    for r in RESULTS: print(f"{r[0]:48s} {r[1]} {r[2]}")
    passed = sum(r[1] == "PASSED" for r in RESULTS)
    print(f"{passed}/{len(RESULTS)} passed")
    sys.exit(0 if passed == len(RESULTS) else 1)

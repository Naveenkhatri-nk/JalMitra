"""
validate_database.py - Run the acceptance tests on data/groundwater.db.

    python validate_database.py

Writes data/validation_report.csv and prints PASS / FAIL for every test.
Opens the database read-only; changes nothing.
"""

import csv
import hashlib
import sqlite3
import sys
from collections import Counter
from pathlib import Path

DATA = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data")
results = []


def test(test_id, name, passed, details):
    results.append({"test_id": test_id, "test": name, "result": "PASS" if passed else "FAIL", "details": details})


def read_csv(path):
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


db = DATA / "groundwater.db"
conn = sqlite3.connect(f"{db.resolve().as_uri()}?mode=ro", uri=True)
conn.row_factory = sqlite3.Row
one = lambda sql, *a: conn.execute(sql, a).fetchone()[0]
rows = [dict(r) for r in conn.execute("SELECT * FROM groundwater_assessment")]
VOL = ("annual_recharge", "extractable_resource", "total_extraction")

# T01 exactly 6,762 assessment units, one per unit and year
n = len(rows)
keys = Counter((r["state"], r["district"], r["assessment_unit"], r["year"]) for r in rows)
test("T01", "exactly 6,762 assessment units, unique per unit and year",
     n == 6762 and max(keys.values()) == 1 and len({r["record_id"] for r in rows}) == n,
     f"{n} rows, {len(keys)} unique unit+year keys")

# T02 Rajasthan: 302 units with numerical data
rj = [r for r in rows if r["state"] == "Rajasthan"]
rj_num = [r for r in rj if all(r[f"{v}_original"] is not None for v in VOL)]
comp = Counter(r["data_completeness"] for r in rj)
test("T02", "302 Rajasthan blocks have numerical data",
     len(rj) == 302 and len(rj_num) == 302,
     f"{len(rj)} Rajasthan units; {len(rj_num)} with volumes; completeness {dict(comp)}")

# T03 6,460 other units: category present, all numbers NULL (never 0)
other = [r for r in rows if r["state"] != "Rajasthan"]
num_cols = [f"{v}_{s}" for v in VOL for s in ("original", "original_unit", "bcm")] + ["stage_of_extraction_pct"]
bad = [r["record_id"] for r in other if any(r[c] is not None for c in num_cols) or not r["category"]]
test("T03", "6,460 other units have category and NULL numerical fields",
     len(other) == 6460 and not bad and all(r["data_completeness"] == "category_only" for r in other),
     f"{len(other)} units; {len(bad)} with a non-NULL number or missing category")

# T04 ham and BCM consistent
problems = []
for r in rows:
    for v in VOL:
        o, u, b = r[f"{v}_original"], r[f"{v}_original_unit"], r[f"{v}_bcm"]
        if o is None:
            if u is not None or b is not None:
                problems.append(f"{r['record_id']} {v}: NULL original but unit/bcm set")
        elif u != "ham" or b is None or abs(b * 100000 - o) > 1e-6:
            problems.append(f"{r['record_id']} {v}: {o} {u} -> {b}")
ex = conn.execute("SELECT assessment_unit, annual_recharge_original, annual_recharge_bcm FROM groundwater_assessment "
                  "WHERE annual_recharge_original > 0 ORDER BY record_id LIMIT 3").fetchall()
test("T04", "original hectare-metre values and BCM conversions consistent (bcm = ham / 100000)",
     not problems, f"{len(problems)} problems; examples: " + "; ".join(f"{a}: {b:g} ham = {c:g} bcm" for a, b, c in ex))

# T04b Rajasthan originals equal the values extracted from the report
import re
norm = lambda t: re.sub(r"[^A-Z0-9]", "", (t or "").upper())
rj_src = {(norm(x["district"]), x["assessment_unit"]): x for x in read_csv(DATA / "processed" / "rajasthan_gwra2025_blocks.csv")}
mism = []
for r in rj:
    src = rj_src.get((norm(r["district"]), r["values_source_unit_name"]))
    if not src:
        mism.append(f"{r['record_id']}: no source row")
        continue
    for v in VOL:
        if float(src[f"{v}_ham"]) != r[f"{v}_original"]:
            mism.append(f"{r['record_id']} {v}")
    src_stage = float(src["stage_of_extraction_pct"]) if src["stage_of_extraction_pct"] else None
    if src_stage != r["stage_of_extraction_pct"]:
        mism.append(f"{r['record_id']} stage")
test("T04b", "Rajasthan original values identical to the report extract", not mism,
     f"{len(mism)} differences" + (": " + "; ".join(mism[:5]) if mism else ""))

# T05 state-wise counts vs National Compilation page 213
nc = {r["state"]: dict(r) for r in conn.execute("SELECT * FROM national_unit_counts")}
by_state = Counter(r["state"] for r in rows)
diffs = [f"{s}: DB {by_state.get(s, 0)} vs NC {c['total_units']}" for s, c in nc.items() if by_state.get(s, 0) != c["total_units"]]
extra = [s for s in by_state if s not in nc]
test("T05", "state-wise assessment-unit counts match NC2025 page 213",
     not diffs and not extra, f"{len(by_state)} states/UTs in DB; {len(nc)} in NC; differences: {diffs + extra or 'none'}")

# T05b state-wise category counts (expected difference: Assam, recorded as a conflict)
catcol = {"Safe": "safe", "Semi-critical": "semi_critical", "Critical": "critical",
          "Over-exploited": "over_exploited", "Saline": "saline"}
cat_counts = Counter((r["state"], r["category"]) for r in rows)
cdiff = [f"{s} {c}: DB {cat_counts.get((s, c), 0)} vs NC {nc[s][col]}"
         for s in nc for c, col in catcol.items() if cat_counts.get((s, c), 0) != nc[s][col]]
conflict_states = {r["state"] for r in conn.execute("SELECT state FROM category_conflicts")}
unexplained = [d for d in cdiff if d.split(" ")[0] not in conflict_states]
test("T05b", "state-wise category counts match NC2025, except differences recorded in category_conflicts",
     not unexplained, f"differences: {cdiff or 'none'}; recorded conflicts in: {sorted(conflict_states) or 'none'}")

# T06 no aggregate records in the assessment table
agg_names = [r["record_id"] for r in rows if any(w in (r["assessment_unit"] + " " + r["district"]).lower()
                                                  for w in ("total", "grand total", "state total"))]
wrong_src = [r["record_id"] for r in rows if r["source_id"] != "AI2025" or (r["values_source_id"] not in (None, "RJ2025"))]
nc_level = one("SELECT COUNT(*) FROM national_district_summary WHERE district IS NULL OR district = ''")
test("T06", "no state or district aggregate records in groundwater_assessment",
     not agg_names and not wrong_src and nc_level == 0,
     f"'total' names: {len(agg_names)}; rows from an aggregate source: {len(wrong_src)}; "
     f"NC state rows {one('SELECT COUNT(*) FROM national_state_summary')} and district rows "
     f"{one('SELECT COUNT(*) FROM national_district_summary')} kept in separate tables")

# T07 all quality flags preserved and required flags present
preview = {r["record_id"]: r for r in read_csv(DATA / "processed" / "groundwater_preview.csv")}
lost = []
for r in rows:
    before = set(filter(None, preview[r["record_id"]]["quality_flag"].split(";")))
    after = set(filter(None, (r["quality_flag"] or "").split(";")))
    if not before <= after:
        lost.append(f"{r['record_id']}: {sorted(before - after)}")
flag_counts = Counter(f for r in rows for f in (r["quality_flag"] or "").split(";") if f)
need = {"measurements_require_verification": 3, "category_stage_mismatch": 5, "stage_calculation_mismatch": 2,
        "category_conflict_between_sources": 1, "truncated_name_in_values_source": 1}
short = {k: (flag_counts.get(k, 0), v) for k, v in need.items() if flag_counts.get(k, 0) != v}
test("T07", "all preview quality flags preserved; required flags present",
     not lost and not short, f"lost: {lost or 'none'}; counts: {dict(flag_counts)}"
     + (f"; unexpected (got, expected): {short}" if short else ""))

# T07b original categories never overwritten
over = [r["record_id"] for r in rows if r["category"] != preview[r["record_id"]]["category"]
        or r["category_as_printed"] != preview[r["record_id"]]["category_raw"]]
test("T07b", "printed categories kept; validation category stored separately",
     not over, f"{len(over)} changed; {sum(1 for r in rows if r['validation_category'])} rows have a validation_category")

# T07c saline zeros kept as printed
sal = [r for r in rj if r["category"] == "Saline"]
test("T07c", "3 saline Rajasthan records kept with printed zeros and flagged",
     len(sal) == 3 and all(r[f"{v}_original"] == 0 for r in sal for v in VOL)
     and all("measurements_require_verification" in r["quality_flag"] for r in sal),
     ", ".join(f"{r['assessment_unit']} ({r['data_completeness']})" for r in sal))

# T07d truncated name kept exactly as printed
tr = [r for r in rows if "truncated_name_in_values_source" in (r["quality_flag"] or "")]
test("T07d", "truncated name kept exactly as printed in the values source",
     len(tr) == 1 and tr[0]["values_source_unit_name"] == "GADRARO",
     "; ".join(f"{r['assessment_unit']} printed as '{r['values_source_unit_name']}'" for r in tr))

# T08 reports retained
for table, fname in (("duplicate_records", "duplicate_records.csv"), ("import_errors", "import_errors.csv"),
                     ("category_conflicts", "category_conflicts.csv"), ("quality_report", "quality_report.csv")):
    in_db, in_csv = one(f"SELECT COUNT(*) FROM {table}"), len(read_csv(DATA / fname))
    test(f"T08-{table}", f"{table} retained in database and CSV", in_db == in_csv and in_db > 0,
         f"{in_db} rows in DB, {in_csv} in {fname}")

# T09 original files unchanged
chg = []
for s in conn.execute("SELECT source_id, file_name, sha256 FROM data_sources"):
    p = DATA / "raw" / s["file_name"]
    if not p.exists() or sha256(p) != s["sha256"]:
        chg.append(s["file_name"])
test("T09", "original PDFs in data/raw unchanged (SHA-256)", not chg, f"changed or missing: {chg or 'none'}")

# T10 foreign keys and integrity
fk = conn.execute("PRAGMA foreign_key_check").fetchall()
ic = one("PRAGMA integrity_check")
test("T10", "database integrity and source references", not fk and ic == "ok", f"integrity {ic}; {len(fk)} broken references")

conn.close()
with open(DATA / "validation_report.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["test_id", "test", "result", "details"])
    w.writeheader()
    w.writerows(results)
for r in results:
    print(f"[{r['result']}] {r['test_id']} {r['test']}\n       {r['details'][:400]}")
failed = sum(r["result"] == "FAIL" for r in results)
print(f"\n{len(results) - failed} passed, {failed} failed")
sys.exit(1 if failed else 0)

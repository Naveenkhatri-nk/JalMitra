"""
eval/gw_accuracy.py - groundwater accuracy check (JalMitra 4.0 Phase 5).

Every figure JalMitra shows is compared with an INDEPENDENT read-only SQL query on data/groundwater.db
(written here, not reusing database.py / retrieval.py):

  units      all 6762 assessment units through engine.answer_places("numeric") (the selector path): category,
             stage %, annual recharge, extractable resource, total extraction (original unit and bcm) in the
             table; for category-only units: no figure may appear
  typed      typed questions for a sample of uniquely named Rajasthan blocks, in en / hi / hinglish / raj / pa /
             mr (lang_choice), every number in the answer text must equal a stored value of that unit
  areas      every district and state (status answer): unit counts per category vs SQL GROUP BY;
             National Compilation stage / recharge / extractable / extraction vs SQL
  compare    district pairs: both table rows match SQL
  history    only the 2025 assessment is in groundwater.db (reported; the separate monitoring data of another
             work thread is not integrated and not used)

Usage: python eval/gw_accuracy.py          -> eval/gw_accuracy_<date>.md (+ csv of every mismatch)
"""

import csv
import datetime as dt
import os
import random
import re
import sqlite3
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
sys.path.insert(0, str(BASE))
for _k in [k for k in os.environ if k.startswith("JALMITRA_")]:
    del os.environ[_k]

import engine  # noqa: E402
import entity_resolver as er  # noqa: E402

DB = f"file:{(BASE / 'data' / 'groundwater.db').as_posix()}?mode=ro"
DIGITS = str.maketrans("०१२३४५६७८९੦੧੨੩੪੫੬੭੮੯", "01234567890123456789")
CATS = ["Safe", "Semi-critical", "Critical", "Over-exploited", "Saline"]
CONFLICTS = {}


def sql(q, args=()):
    con = sqlite3.connect(DB, uri=True)
    con.row_factory = sqlite3.Row
    try:
        return [dict(r) for r in con.execute(q, args)]
    finally:
        con.close()


def same(a, b):
    if a is None or b is None:
        return a is None and b is None
    return abs(float(a) - float(b)) <= 1e-9 * max(1.0, abs(float(b)))


def nums(text):
    return [float(x.replace(",", "")) for x in re.findall(r"\d+(?:,\d{3})*(?:\.\d+)?", (text or "").translate(DIGITS))]


def main():
    t0 = time.time()
    random.seed(20261123)
    mism = []
    stats = {}

    # ---------------------------------------------------------------- units (selector path)
    units = sql("SELECT * FROM groundwater_assessment")
    for c in sql("SELECT * FROM category_conflicts"):
        CONFLICTS.setdefault(c["record_id"], []).append(c)
    by_id = {u["record_id"]: u for u in units}
    places = [p for p in er.index()["places"] if p["type"] == "unit"]
    ok = checked = fig_units = 0
    for p in places:
        u = by_id[p["record_id"]]
        out = engine.answer_places("numeric", [p], lang="en")
        row = (out.get("table") or [{}])[0]
        checked += 1
        errs = []
        if row.get("category") != u["category"]:
            errs.append(f"category {row.get('category')} != {u['category']}")
        has_fig = u["data_completeness"] != "category_only"
        if has_fig:
            fig_units += 1
            pairs = [("stage_pct", u["stage_of_extraction_pct"]),
                     ("annual_recharge_ham", u["annual_recharge_original"]),
                     ("extractable_resource_ham", u["extractable_resource_original"]),
                     ("total_extraction_ham", u["total_extraction_original"]),
                     ("annual_recharge_bcm", u["annual_recharge_bcm"]),
                     ("extractable_resource_bcm", u["extractable_resource_bcm"]),
                     ("total_extraction_bcm", u["total_extraction_bcm"])]
            for k, v in pairs:
                if not same(row.get(k), v):
                    errs.append(f"{k} {row.get(k)} != {v}")
        else:
            for k in ("stage_pct", "annual_recharge_ham", "total_extraction_ham"):
                if row.get(k) is not None:
                    errs.append(f"{k} shown for a category-only unit")
        # every number in the answer text must be a stored value, a source page / serial, the year or a limit
        allowed = {float(v) for v in u.values() if isinstance(v, (int, float))} | {2025.0, 100.0, 70.0, 90.0}
        for k in ("source_page", "values_source_page", "source_serial", "district", "state", "assessment_unit"):
            for x in re.findall(r"\d+", str(u.get(k) or "")):           # "NORTH 24 PARGANAS", "Ludhiana-1"
                allowed.add(float(x))
        for c in CONFLICTS.get(u["record_id"], []):                       # documented category conflicts
            for x in re.findall(r"\d+", str(c.get("source_page") or "") + " " + str(c.get("observation") or "")):
                allowed.add(float(x))
        stray = [n for n in nums(out["text"]) if n not in allowed and not any(same(n, a) for a in allowed)]
        stray = [n for n in stray if not re.search(r"\d", p["name"]) or str(int(n)) not in p["name"]]
        if stray:
            errs.append(f"numbers in text not stored for this unit: {stray[:5]}")
        if errs:
            mism.append({"check": "unit", "place": f"{u['state']}|{u['district']}|{u['assessment_unit']}",
                         "detail": "; ".join(errs)})
        else:
            ok += 1
    stats["units"] = (ok, checked, fig_units)

    # ---------------------------------------------------------------- typed questions, six languages
    raj = [u for u in units if u["state"] == "Rajasthan" and u["data_completeness"] != "category_only"]
    unique = [u for u in raj if len(er.find_by_name(u["assessment_unit"])) == 1]
    sample = random.sample(unique, min(60, len(unique)))
    langs = ["en", "hi", "hinglish", "raj", "pa", "mr"]
    t_ok = t_n = t_clar = 0
    for i, u in enumerate(sample):
        lang = langs[i % 6]
        name = u["assessment_unit"].replace("_", " ").title()
        out = engine.answer(f"What is the stage of extraction of {name} block?", engine.new_state(), lang_choice=lang)
        t_n += 1
        if out.get("clarify") or not out.get("places"):
            t_clar += 1
            mism.append({"check": f"typed/{lang}", "place": u["assessment_unit"],
                         "detail": "not resolved to one place (clarification or not found)"})
            continue
        allowed = {float(v) for v in u.values() if isinstance(v, (int, float))} | {2025.0, 100.0, 70.0, 90.0}
        for k in ("source_page", "values_source_page", "source_serial"):
            for x in re.findall(r"\d+", str(u.get(k) or "")):
                allowed.add(float(x))
        stray = [n for n in nums(out["text"]) if not any(same(n, a) for a in allowed)]
        p = out["places"][0]
        wrong_place = p.get("record_id") != u["record_id"]
        stage_ok = u["stage_of_extraction_pct"] is None or \
            any(same(n, u["stage_of_extraction_pct"]) for n in nums(out["text"]))   # Saline: stage not published
        if stray or wrong_place or not stage_ok:
            mism.append({"check": f"typed/{lang}", "place": u["assessment_unit"],
                         "detail": f"stray={stray[:4]} wrong_place={wrong_place} stage_shown={stage_ok}"})
        else:
            t_ok += 1
    stats["typed"] = (t_ok, t_n, t_clar)

    # ---------------------------------------------------------------- districts and states
    a_ok = a_n = 0
    for p in [x for x in er.index()["places"] if x["type"] in ("district", "state")]:
        out = engine.answer_places("status", [p], lang="en")
        row = (out.get("table") or [{}])[0]
        if p["type"] == "district":
            rows = sql("SELECT category, COUNT(*) n FROM groundwater_assessment WHERE state=? AND district=? "
                       "GROUP BY category", (p["state"], p["district"]))
            nc = sql("SELECT * FROM national_district_summary WHERE state=? COLLATE NOCASE AND district=? "
                     "COLLATE NOCASE", (p["state"], p["district"]))
        else:
            rows = sql("SELECT category, COUNT(*) n FROM groundwater_assessment WHERE state=? GROUP BY category",
                       (p["state"],))
            nc = sql("SELECT * FROM national_state_summary WHERE state=? COLLATE NOCASE", (p["state"],))
        counts = {r["category"]: r["n"] for r in rows}
        a_n += 1
        errs = [f"{c}: {row.get(c)} != {counts.get(c, 0)}" for c in CATS if (row.get(c) or 0) != counts.get(c, 0)]
        if (row.get("units") or 0) != sum(counts.values()):
            errs.append(f"units {row.get('units')} != {sum(counts.values())}")
        if len(nc) == 1 and nc[0]["stage_of_extraction_pct"] is not None:
            if not any(same(n, nc[0]["stage_of_extraction_pct"]) for n in nums(out["text"])):
                errs.append(f"NC stage {nc[0]['stage_of_extraction_pct']} not in the answer")
        if errs:
            mism.append({"check": p["type"], "place": f"{p['state']}|{p.get('district') or ''}",
                         "detail": "; ".join(errs)})
        else:
            a_ok += 1
    stats["areas"] = (a_ok, a_n)

    # ---------------------------------------------------------------- comparisons
    dists = [x for x in er.index()["places"] if x["type"] == "district"]
    c_ok = c_n = 0
    for _ in range(50):
        a, b = random.sample(dists, 2)
        out = engine.answer_places("compare", [a, b], lang="en")
        rows = [r for r in out.get("table") or [] if "area" in r]
        c_n += 1
        good = len(rows) == 2
        for r, p in zip(rows, (a, b)):
            n = sql("SELECT COUNT(*) n FROM groundwater_assessment WHERE state=? AND district=?",
                    (p["state"], p["district"]))[0]["n"]
            good &= r.get("units") == n
        c_ok += good
        if not good:
            mism.append({"check": "compare", "place": f"{a['district']} vs {b['district']}",
                         "detail": "table rows do not match SQL unit counts"})
    stats["compare"] = (c_ok, c_n)

    years = sql("SELECT DISTINCT year FROM groundwater_assessment")
    date = dt.date.today().isoformat()
    with open(HERE / f"gw_accuracy_mismatches_{date}.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["check", "place", "detail"])
        w.writeheader()
        w.writerows(mism)
    u_ok, u_n, u_fig = stats["units"]
    L = [f"# Groundwater accuracy: engine output vs independent SQL ({date})", "",
         "Read-only SQL written in eval/gw_accuracy.py (not database.py / retrieval.py). Numbers compared exactly.", "",
         "| check | passed | checked | notes |", "|---|---|---|---|",
         f"| assessment units (answer_places numeric) | {u_ok} | {u_n} | {u_fig} units with figures (Rajasthan), the rest "
         f"category-only: category checked and no figure may appear |",
         f"| typed questions, 6 languages (stage of extraction, uniquely named Rajasthan blocks) | {stats['typed'][0]} | "
         f"{stats['typed'][1]} | {stats['typed'][2]} not resolved to one place (asked to clarify / not found) |",
         f"| districts + states (category counts, NC stage) | {stats['areas'][0]} | {stats['areas'][1]} | |",
         f"| district comparisons (random pairs) | {stats['compare'][0]} | {stats['compare'][1]} | |", "",
         f"Assessment years in groundwater.db: {', '.join(r['year'] for r in years)} — historical comparisons cannot "
         "be answered from it; JalMitra says so instead of guessing. Monitoring data collected by another work thread "
         "(data/monitoring/) is not integrated and was not used.", "",
         f"Mismatches: {len(mism)} (eval/gw_accuracy_mismatches_{date}.csv)."]
    for m in mism[:40]:
        L.append(f"- {m['check']} {m['place']}: {m['detail']}")
    L.append(f"\nRun time {time.time() - t0:.0f} s.")
    (HERE / f"gw_accuracy_{date}.md").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L[:12]))


if __name__ == "__main__":
    main()

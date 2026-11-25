"""Read-only lookup of block / taluk / mandal (assessment-unit) groundwater figures for GWRA 2025.

Data: data/monitoring/gwra_blocks_2025.db, built by ingest/gwra_blocks/run_gwra_blocks.py from the CGWB
2025 state reports. Every figure is copied from a report; nothing is estimated. Only rows with usable=1 are
returned as figures. Units: ham (hectare-metres); stage in percent. 1 ham = 0.01 MCM = 0.00001 BCM.

Main calls (all return plain dicts):
    unit_figures(state, unit, district=None)   one assessment unit
    district_units(state, district)            every unit of a district
    state_coverage(state=None)                 how many units have figures, and why some do not
    tn_firka_figures(firka, district=None)     Tamil Nadu firka-level figures
"""
from __future__ import annotations

import difflib
import re
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "data" / "monitoring" / "gwra_blocks_2025.db"
FIELDS = ["recharge_ham", "natural_discharge_ham", "extractable_ham", "irrigation_ham", "industrial_ham", "domestic_ham",
          "total_extraction_ham", "allocation_domestic_ham", "net_availability_ham", "stage_pct"]
SOURCE_NOTE = "CGWB, Dynamic Ground Water Resources of {state}, 2025 (state report), p. {page}"


def _key(s: str | None) -> str:
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def _deny_writes(action, *args):
    return sqlite3.SQLITE_OK if action in (sqlite3.SQLITE_READ, sqlite3.SQLITE_SELECT, sqlite3.SQLITE_FUNCTION) else sqlite3.SQLITE_DENY


def _connect(path: Path | None = None) -> sqlite3.Connection:
    p = Path(path or DB_PATH)
    con = sqlite3.connect(f"file:{p.as_posix()}?mode=ro", uri=True)
    con.execute("PRAGMA query_only = ON")
    con.set_authorizer(_deny_writes)
    con.row_factory = sqlite3.Row
    return con


def available(path: Path | None = None) -> bool:
    try:
        with _connect(path) as con:
            return con.execute("select count(*) from unit_resources").fetchone()[0] > 0
    except sqlite3.Error:
        return False


def _resolve_state(con, state: str) -> str | None:
    states = [r[0] for r in con.execute("select state from coverage_by_state")]
    k = _key(state)
    for s in states:
        if _key(s) == k:
            return s
    best = difflib.get_close_matches(k, {_key(s): s for s in states}.keys(), n=1, cutoff=0.8)
    return {_key(s): s for s in states}[best[0]] if best else None


def _row(r: sqlite3.Row) -> dict:
    d = {"state": r["state"], "district": r["district"], "assessment_unit": r["assessment_unit"],
         "assessment_year": r["assessment_year"], "status": r["status"]}
    if r["usable"]:
        d["figures"] = {f: r[f] for f in FIELDS if r[f] is not None}
        d["category"] = r["category_in_report"] or r["category_official"]
        pages = [r["source_page"]] + [int(x.split("p")[1]) for x in (r["filled_from"] or "").split(",") if "p" in x]
        pages = sorted(set(p for p in pages if p))
        d["source"] = {"pub_id": r["source_pub_id"], "pages": pages,
                       "citation": SOURCE_NOTE.format(state=r["state"], page=", ".join(map(str, pages)))}
    else:
        d["figures"] = {}
        d["category"] = r["category_official"]
        d["reason"] = r["note"] or r["status"]
    return d


def unit_figures(state: str, unit: str, district: str | None = None, path: Path | None = None) -> dict:
    with _connect(path) as con:
        st = _resolve_state(con, state)
        if not st:
            return {"status": "unknown_state", "state": state}
        rows = con.execute("select * from unit_resources where state = ?", (st,)).fetchall()
        ku, kd = _key(unit), _key(district)
        hit = [r for r in rows if _key(r["assessment_unit"]) == ku and (not kd or _key(r["district"]) == kd)]
        if not hit:
            names = {_key(r["assessment_unit"]): r for r in rows if not kd or _key(r["district"]) == kd}
            close = difflib.get_close_matches(ku, names.keys(), n=3, cutoff=0.85)
            if len(close) == 1:
                hit = [names[close[0]]]
            elif close:
                return {"status": "ambiguous", "state": st, "candidates": [names[c]["assessment_unit"] for c in close]}
        if not hit:
            return {"status": "not_found", "state": st, "unit": unit}
        if len(hit) > 1:
            return {"status": "ambiguous", "state": st,
                    "candidates": [f"{r['assessment_unit']} ({r['district']})" for r in hit]}
        out = _row(hit[0])
        out["status"] = "ok" if hit[0]["usable"] else "no_figures"
        out["unit_status"] = hit[0]["status"]
        return out


def district_units(state: str, district: str, path: Path | None = None) -> dict:
    with _connect(path) as con:
        st = _resolve_state(con, state)
        if not st:
            return {"status": "unknown_state", "state": state}
        rows = [r for r in con.execute("select * from unit_resources where state = ? order by assessment_unit", (st,))
                if _key(r["district"]) == _key(district)]
        if not rows:
            return {"status": "not_found", "state": st, "district": district}
        units = [_row(r) for r in rows]
        return {"status": "ok", "state": st, "district": rows[0]["district"], "units": units,
                "units_total": len(rows), "units_with_figures": sum(1 for r in rows if r["usable"])}


def state_coverage(state: str | None = None, path: Path | None = None) -> dict:
    with _connect(path) as con:
        if state:
            st = _resolve_state(con, state)
            if not st:
                return {"status": "unknown_state", "state": state}
            r = con.execute("select * from coverage_by_state where state = ?", (st,)).fetchone()
            return {"status": "ok", **dict(r)}
        return {"status": "ok", "states": [dict(r) for r in con.execute("select * from coverage_by_state order by state")]}


def tn_firka_figures(firka: str, district: str | None = None, path: Path | None = None) -> dict:
    with _connect(path) as con:
        rows = [r for r in con.execute("select * from tn_firka_resources")
                if _key(r["firka"]) == _key(firka) and (not district or _key(r["district"]) == _key(district))]
        if not rows:
            return {"status": "not_found", "firka": firka}
        if len(rows) > 1:
            return {"status": "ambiguous", "candidates": [f"{r['firka']} ({r['district']})" for r in rows]}
        r = rows[0]
        return {"status": "ok" if r["usable"] else "no_figures", "state": "Tamil Nadu", "district": r["district"],
                "firka": r["firka"], "assessment_year": r["assessment_year"],
                "figures": {f: r[f] for f in FIELDS if r[f] is not None} if r["usable"] else {},
                "category": r["category_in_report"],
                "source": {"pub_id": r["source_pub_id"], "pages": [r["source_page"]],
                           "citation": SOURCE_NOTE.format(state="Tamil Nadu", page=r["source_page"])}}

"""
retrieval.py - Run a parsed request against data/groundwater.db (read only).

JalMitra 2.0: this module returns STRUCTURED results (records, counts,
rankings, National Compilation rows). It writes no sentences; that is done by
response_builder.py with fixed templates. Every value here comes straight from
database.py, which only runs fixed, parameterised SELECT statements.

Rules kept here:
  * NULL stays None (never 0); category-only units get no numbers,
  * National Compilation totals are kept separate from unit rows,
  * conflicts (Golaghat West, Assam) are attached, never resolved,
  * units without a published stage are never ranked.
"""

import database as db

PLACE_INTENTS = {"status", "numeric", "compare", "year_compare", "area_search"}


def fmt(v):
    """A stored number exactly as stored (255.0 -> '255', 0.00255 -> '0.00255')."""
    if v is None:
        return None
    if float(v).is_integer():
        return str(int(v))
    return format(v, ".10f").rstrip("0").rstrip(".")


def numbers_available(r):
    return r["data_completeness"] != "category_only"


def unit_row(r):
    row = {"state": r["state"], "district": r["district"], "assessment_unit": r["assessment_unit"],
           "type": r["assessment_unit_type"], "year": r["year"], "category": r["category"]}
    if numbers_available(r):
        for m in ("annual_recharge", "extractable_resource", "total_extraction"):
            row[f"{m}_ham"] = r[f"{m}_original"]
            row[f"{m}_bcm"] = r[f"{m}_bcm"]
        row["stage_pct"] = r["stage_of_extraction_pct"]
    row["data"] = r["data_completeness"]
    return row


def _with_conflicts(r):
    r = dict(r)
    r["_conflicts"] = db.conflicts_for(r["record_id"]) if "conflict" in (r.get("quality_flag") or "") else []
    return r


def _unit(place):
    return _with_conflicts(db.get_unit(place["record_id"]))


def _area(place, with_nc=True, year=None):
    state = place["state"]
    district = place["district"] if place["type"] == "district" else None
    counts = db.category_counts(state, district, year)
    nc = None
    if with_nc:
        nc = db.national_district_summary(district, state) if district else db.national_state_summary(state)
    return {"kind": "area", "place": place, "counts": counts, "total": sum(counts.values()),
            "numeric": db.numeric_unit_count(state, district, year), "nc": nc}


def _scope(places):
    """(state, district, place) used as the area filter for rankings and lists."""
    for p in places:
        if p["type"] == "district":
            return p["state"], p["district"], p
        if p["type"] == "state":
            return p["state"], None, p
    return None, None, None


def new_result(req):
    return {"intent": req["intent"], "status": "ok", "blocks": [], "records": [], "nc_rows": [],
            "table": [], "chart": None, "year": None, "places": req.get("places", [])}


def execute(req):
    """req: {"intent", "places": [resolved places], "category", "n", "order", "level", "years", ...}"""
    res = new_result(req)
    years = db.years()
    res["year"] = ", ".join(years)
    asked = [y for y in req.get("years") or [] if y]
    missing = [y for y in asked if y not in years]
    year = None

    if req["intent"] == "year_compare":
        for y in missing:
            res["blocks"].append({"kind": "year_missing", "year": y, "years": years})
        res["blocks"].append({"kind": "year_only", "years": years})
        _status(req, res, year)
        return _finish(res)
    if missing:
        res["status"] = "not_available"
        res["year"] = None
        res["blocks"].append({"kind": "year_missing", "year": missing[0], "years": years})
        return res
    if asked:
        year = asked[0]

    handler = {
        "status": _status, "numeric": _status, "compare": _compare, "top_n": _top_n, "top_areas": _top_areas,
        "list_category": _list_category, "area_search": _area_search, "sources": _sources,
        "data_availability": _availability, "quality": _quality, "explain_category": _explain,
        "domain": _domain,
    }[req["intent"]]
    handler(req, res, year)
    return _finish(res)


def _finish(res):
    """Remove repeated records (a unit can appear in two blocks)."""
    seen, out = set(), []
    for r in res["records"]:
        if r["record_id"] not in seen:
            seen.add(r["record_id"])
            out.append(r)
    res["records"] = out
    return res


# ------------------------------------------------------------------ handlers

def _status(req, res, year):
    numbers = req["intent"] == "numeric"
    for p in req["places"]:
        if p["type"] == "unit":
            r = _unit(p)
            res["records"].append(r)
            res["blocks"].append({"kind": "unit", "record": r, "numbers": numbers, "place": p})
            res["table"].append(unit_row(r))
        else:
            a = _area(p, with_nc=True, year=year)
            res["blocks"].append({**a, "nc_shown": True})
            res["nc_rows"].extend(a["nc"] or [])
            res["table"].append(_area_row(a))


def _area_row(a):
    p = a["place"]
    return {"area": (f"{p['district']} district ({p['state']})" if p["type"] == "district" else p["state"]),
            "units": a["total"], **a["counts"], "units_with_figures": a["numeric"]}


def _compare(req, res, year):
    places = req["places"]
    if len(places) < 2:
        res["status"] = "need_two"
        res["blocks"].append({"kind": "need_two"})
        return
    items = []
    for p in places:
        if p["type"] == "unit":
            r = _unit(p)
            res["records"].append(r)
            res["blocks"].append({"kind": "unit", "record": r, "numbers": True, "place": p})
            res["table"].append(unit_row(r))
            items.append({"place": p, "stage": r["stage_of_extraction_pct"], "counts": None, "level": "unit"})
        else:
            a = _area(p, with_nc=True, year=year)
            res["blocks"].append({**a, "nc_shown": True})
            res["nc_rows"].extend(a["nc"] or [])
            res["table"].append(_area_row(a))
            nc_stage = a["nc"][0]["stage_of_extraction_pct"] if a["nc"] and len(a["nc"]) == 1 else None
            items.append({"place": p, "stage": nc_stage, "counts": a["counts"], "level": "area"})
    same_level = len({i["level"] for i in items}) == 1
    res["blocks"].append({"kind": "compare_summary", "items": items, "comparable": same_level})
    if same_level and items[0]["level"] == "unit" and all(i["stage"] is not None for i in items):
        res["chart"] = {"type": "stage", "data": {i["place"]["name"]: i["stage"] for i in items}}
    elif same_level and items[0]["level"] == "area":
        res["chart"] = {"type": "counts", "data": {_label(i["place"]): i["counts"] for i in items}}


def _label(p):
    if p["type"] == "district":
        return f"{p['district']} ({p['state']})"
    return p["name"]


def _top_n(req, res, year):
    state, district, scope = _scope(req["places"])
    cat = req.get("category")
    n = req.get("n") or 5
    highest = req.get("order") != "lowest"
    rows = [_with_conflicts(r) for r in db.top_units_by_stage(n, state, district, cat, year, highest)]
    res["blocks"].append({"kind": "top", "area": scope, "category": cat, "order": req.get("order"), "n": n,
                          "rows": rows, "numeric_total": db.coverage()["numeric_units"]})
    if rows:
        res["records"].extend(rows)
        res["table"].extend(unit_row(r) for r in rows)
        res["chart"] = {"type": "stage", "data": {f"{r['assessment_unit']} ({r['district']})": r["stage_of_extraction_pct"]
                                                  for r in rows}}
    else:
        res["status"] = "not_available"
        if cat:
            _top_areas({**req, "level": "district"}, res, year, fallback=True)


def _top_areas(req, res, year, fallback=False):
    cat = req.get("category")
    if cat not in db.CATEGORIES:
        res["status"] = "need_category"
        res["blocks"].append({"kind": "need_category"})
        return
    level = "state" if req.get("level") == "state" else "district"
    state, _, scope = _scope([p for p in req["places"] if p["type"] == "state"])
    rows = db.top_areas_by_category(cat, level, state, year, req.get("n") or 5)
    res["blocks"].append({"kind": "top_areas", "level": level, "category": cat, "area": scope, "rows": rows,
                          "fallback": fallback})
    res["table"].extend({**r, "category": cat} for r in rows)
    if not fallback:
        res["chart"] = {"type": "units", "data": {(f"{r['district']} ({r['state']})" if level == "district" else r["state"]):
                                                  r["units"] for r in rows}}


def _list_category(req, res, year):
    cat = req.get("category")
    if cat not in db.CATEGORIES:
        res["status"] = "need_category"
        res["blocks"].append({"kind": "need_category"})
        return
    state, district, scope = _scope(req["places"])
    count = db.count_units(state, district, cat, year)
    rows = db.search_units(state, district, cat, year, limit=200)
    res["blocks"].append({"kind": "list", "area": scope, "category": cat, "count": count, "rows": rows,
                          "count_only": bool(req.get("count_only"))})
    res["table"].extend(unit_row(r) for r in rows)


def _area_search(req, res, year):
    for p in req["places"]:
        if p["type"] == "district":
            rows = db.search_units(p["state"], p["district"], None, year, limit=200)
            a = _area(p, with_nc=False, year=year)
            res["blocks"].append({**a, "nc_shown": False})
            res["blocks"].append({"kind": "area_units", "area": p, "rows": rows})
            res["table"].extend(unit_row(r) for r in rows)
            res["chart"] = {"type": "counts", "data": {_label(p): a["counts"]}}
        elif p["type"] == "state":
            a = _area(p, with_nc=False, year=year)
            res["blocks"].append({**a, "nc_shown": False})
            res["table"].append(_area_row(a))
            res["chart"] = {"type": "counts", "data": {_label(p): a["counts"]}}
        else:
            r = _unit(p)
            res["records"].append(r)
            res["blocks"].append({"kind": "unit", "record": r, "numbers": False, "place": p})
            res["table"].append(unit_row(r))


def _sources(req, res, year):
    if not req["places"]:
        res["blocks"].append({"kind": "sources_general", "sources": list(db.data_sources().values())})
        return
    for p in req["places"]:
        if p["type"] == "unit":
            r = _unit(p)
            res["records"].append(r)
            res["blocks"].append({"kind": "sources", "place": p, "refs": db.sources_for(r)})
        else:
            a = _area(p, with_nc=True, year=year)
            res["nc_rows"].extend(a["nc"] or [])
            src = db.data_sources()
            refs = [{"used_for": "category (unit list)", "source_id": "AI2025",
                     "title": src.get("AI2025", {}).get("title"), "page": "-", "url": src.get("AI2025", {}).get("source_url")}]
            for row in a["nc"] or []:
                refs.append({"used_for": "area total", "source_id": "NC2025", "title": src.get("NC2025", {}).get("title"),
                             "page": str(row["source_page"]), "url": src.get("NC2025", {}).get("source_url")})
            res["blocks"].append({"kind": "sources", "place": p, "refs": refs})


def _availability(req, res, year):
    if not req["places"]:
        res["blocks"].append({"kind": "coverage", "coverage": db.coverage()})
        return
    for p in req["places"]:
        if p["type"] == "unit":
            r = _unit(p)
            res["blocks"].append({"kind": "place_availability", "place": p, "n": 1 if numbers_available(r) else 0,
                                  "total": 1})
        else:
            a = _area(p, with_nc=False, year=year)
            res["blocks"].append({"kind": "place_availability", "place": p, "n": a["numeric"], "total": a["total"]})


def _quality(req, res, year):
    if not req["places"]:
        rows = [_with_conflicts(r) for r in db.flagged_units(limit=100)]
        res["blocks"].append({"kind": "quality_list", "rows": rows})
        res["table"].extend({**unit_row(r), "quality_flag": r["quality_flag"]} for r in rows)
        return
    for p in req["places"]:
        if p["type"] == "unit":
            r = _unit(p)
            res["records"].append(r)
            res["blocks"].append({"kind": "unit", "record": r, "numbers": True, "place": p})
            flags = set((r.get("quality_flag") or "").split(";")) - {"", "values_not_in_uploaded_sources"}
            if not flags:
                res["blocks"].append({"kind": "quality_none", "place": p})
        else:
            rows = [_with_conflicts(r) for r in db.flagged_units(state=p["state"], limit=100)
                    if p["type"] == "state" or r["district"] == p["district"]]
            res["blocks"].append({"kind": "quality_list", "rows": rows, "place": p} if rows
                                 else {"kind": "quality_none", "place": p})
            res["table"].extend({**unit_row(r), "quality_flag": r["quality_flag"]} for r in rows)


def _explain(req, res, year):
    cat = req.get("category")
    block = {"kind": "explain", "category": cat if cat in db.CATEGORIES else None, "what": req.get("what")}
    if req.get("context_categories"):
        # "What does it mean?": categories of the previous answer (JalMitra 3.0 memory)
        block["categories"] = [c for c in req["context_categories"] if c in db.CATEGORIES]
        block["prev"] = req.get("context_findings") or []
    res["blocks"].append(block)


def _domain(req, res, year):
    """Soil, crop, land or irrigation question (JalMitra 3.0). The database has no such data, so the answer
    says "Data unavailable" and, when a place is known, adds the verified groundwater data for that place."""
    places = req["places"]
    res["status"] = "data_unavailable"
    res["blocks"].append({"kind": "domain", "domain": req.get("domain"), "places": places,
                          "knowledge": req.get("knowledge"), "soil_report": req.get("soil_report")})
    if places:
        _status({**req, "intent": "status"}, res, year)

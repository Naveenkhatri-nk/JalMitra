"""
gwra_enrich.py - adds the official block / mandal / taluk figures from the CGWB 2025 STATE reports to a chat answer
(naveen, 24 Nov 2026: "Data unavailable" should be filled wherever official figures exist).

groundwater.db (the national 2025 list) has figures only for Rajasthan; the other states have a category only.
The figures read from each state's 2025 report are in a separate, read-only database
(data/monitoring/gwra_blocks_2025.db, lookup gwra_blocks_retrieval.py). This module copies those figures into the
rule-engine result of a question, so the data cards, the data table, the facts the AI receives and the checks all
use them:

  * figures found (usable rows only)   -> the unit's record and table row get stage, recharge, extractable resource,
                                          total extraction (and the breakdown) with the state-report citation + page
  * no figures in the state report      -> a short reason ("The Telangana 2025 report gives district totals only.")
                                          and the district totals (National Compilation 2025) as a clearly labelled
                                          fallback
  * category in the state report differs from the national list -> both are shown with their sources (the figures
                                          stay held back, as the data build decided)
Rajasthan keeps using groundwater.db exactly as before. Nothing is ever written to either database.
"""

import copy
import re

import language as L

try:
    import gwra_blocks_retrieval as gwra
except Exception:                       # the separate database is optional: without it nothing changes
    gwra = None

SKIP_STATES = {"Rajasthan"}             # groundwater.db already holds the Rajasthan report figures
SHORT = {  # one short line per state without unit-level figures (from the data build's notes)
    "Telangana": "The Telangana 2025 state report gives district totals only, not mandal figures.",
    "Mizoram": "The Mizoram 2025 state report gives district totals only.",
    "Odisha": "The Odisha 2025 state report gives district totals only (block figures only for 10 semi-critical "
              "blocks).",
    "Goa": "The Goa 2025 state report has no readable taluk-level table.",
    "Lakshadweep": "The Lakshadweep 2025 report has no readable island-level table.",
    "Chandigarh": "The Chandigarh 2025 report has no readable unit table.",
    "Punjab": "There is no 2025 Punjab state report with block tables (the 2024 report is a different year).",
    "Tamil Nadu": "The Tamil Nadu 2025 state report gives figures per firka, not per taluk.",
    "Uttarakhand": "The Uttarakhand 2025 state report has no unit-level recharge table for this unit.",
}
STATUS_LINE = {
    "checks_failed": "Figures for this unit were printed in the {state} 2025 state report but did not pass JalMitra's "
                     "arithmetic checks, so they are not shown.",
    "zero_resource": "The {state} 2025 state report prints no groundwater resource for this unit (saline area).",
    "not_found": "No unit-level figures for this unit were found in the {state} 2025 state report.",
}


def short_id(state):
    return f"CGWB {state} 2025"


def _reason(state, res):
    st = res.get("unit_status") or res.get("reason")
    if st in STATUS_LINE and not (st == "not_found" and state in SHORT):
        return STATUS_LINE[st].format(state=state)
    return SHORT.get(state) or STATUS_LINE["not_found"].format(state=state)


def _conflict(state, district, unit):
    """(category in the state report, page) for a held-back category conflict, read-only."""
    try:
        with gwra._connect() as con:
            for r in con.execute("select district, assessment_unit, category_in_report, source_page "
                                 "from unit_resources where state = ? and status = 'category_conflict'", (state,)):
                if gwra._key(r["assessment_unit"]) == gwra._key(unit) and \
                        (not district or gwra._key(r["district"]) == gwra._key(district)):
                    return r["category_in_report"], r["source_page"]
    except Exception:                    # noqa: BLE001
        pass
    return None, None


def _fmt(v):
    return str(int(v)) if float(v).is_integer() else f"{v:.2f}".rstrip("0").rstrip(".")


def lookup(record):
    """The state-report result for one groundwater.db record, or None (Rajasthan / no lookup available)."""
    if gwra is None or not record or record.get("state") in SKIP_STATES:
        return None
    if record.get("data_completeness") not in (None, "category_only"):
        return None
    try:
        return gwra.unit_figures(record["state"], record["assessment_unit"], record.get("district"))
    except Exception:                    # noqa: BLE001 - a missing / broken file never breaks an answer
        return None


def enrich_rule(rule):
    """Copy the state-report figures into the rule result (in place) and return it."""
    if gwra is None or not rule:
        return rule
    blocks = (rule.get("result") or {}).get("blocks") or []
    lang = rule.get("lang") or "en"
    extra = []
    for b in blocks:
        if b.get("kind") == "area":
            _enrich_area(rule, b.get("place") or {}, lang)
        if b.get("kind") != "unit":
            continue
        rec = b.get("record")
        res = lookup(rec)
        if not res or res.get("status") not in ("ok", "no_figures"):
            continue
        state, unit = rec["state"], rec["assessment_unit"]
        figs = res.get("figures") or {}
        usable = res["status"] == "ok" and (res.get("unit_status") != "zero_resource") and \
            any(k in figs for k in ("stage_pct", "recharge_ham", "extractable_ham", "total_extraction_ham"))
        row = next((r for r in rule.get("table") or [] if isinstance(r, dict) and
                    r.get("assessment_unit") == unit and r.get("district") == rec.get("district")), None)
        if usable:
            pages = ", ".join(str(p) for p in res["source"]["pages"])
            new = copy.copy(rec)
            new.update(data_completeness="state_report",
                       annual_recharge_original=figs.get("recharge_ham"), annual_recharge_original_unit="ham",
                       annual_recharge_bcm=None,
                       extractable_resource_original=figs.get("extractable_ham"),
                       extractable_resource_original_unit="ham", extractable_resource_bcm=None,
                       total_extraction_original=figs.get("total_extraction_ham"),
                       total_extraction_original_unit="ham", total_extraction_bcm=None,
                       stage_of_extraction_pct=figs.get("stage_pct"),
                       values_source_id=short_id(state), values_source_page=pages,
                       state_report_citation=res["source"]["citation"], state_report_figures=dict(figs))
            b["record"] = new
            b["numbers"] = True
            if row is not None:
                for k_src, k_dst in (("recharge_ham", "annual_recharge_ham"),
                                     ("extractable_ham", "extractable_resource_ham"),
                                     ("total_extraction_ham", "total_extraction_ham"), ("stage_pct", "stage_pct"),
                                     ("natural_discharge_ham", "natural_discharge_ham"),
                                     ("irrigation_ham", "irrigation_extraction_ham"),
                                     ("industrial_ham", "industrial_extraction_ham"),
                                     ("domestic_ham", "domestic_extraction_ham")):
                    if figs.get(k_src) is not None:
                        row[k_dst] = figs[k_src]
                row["data"] = "figures from the state report"
                row["figures_source"] = res["source"]["citation"]
            parts = []
            for k, label in (("stage_pct", "stage of extraction {v}%"), ("recharge_ham", "annual recharge {v} ham"),
                             ("extractable_ham", "annual extractable resource {v} ham"),
                             ("total_extraction_ham", "total extraction {v} ham")):
                if figs.get(k) is not None:
                    parts.append(label.format(v=_fmt(figs[k])))
            line = (f"Figures for {unit} from the {state} 2025 state report: " + ", ".join(parts) +
                    f". Source: {res['source']['citation']}.")
            text = rule.get("text") or ""
            removed = False
            for lg in {lang, "en"}:
                try:
                    s = L.t("unit_cat_only", lg)
                except Exception:        # noqa: BLE001
                    s = None
                if s and s in text:
                    text, removed = text.replace(s, line), True
            rule["text"] = text if removed else (text + "\n" + line).strip()
            rule.setdefault("sources", []).append({
                "assessment_unit": unit, "used_for": "figures (state report)", "source_id": short_id(state),
                "title": f"Dynamic Ground Water Resources of {state}, 2025 (CGWB state report)", "page": pages,
                "url": f"https://cgwb.gov.in/cgwbpnm/public/download/{res['source'].get('pub_id')}"})
        else:
            reason = _reason(state, res)
            note = {"unit": unit, "state": state, "district": rec.get("district"), "reason": reason}
            if res.get("unit_status") == "category_conflict" or res.get("reason") == "category_conflict":
                cat_r, page = _conflict(state, rec.get("district"), unit)
                if cat_r and cat_r != rec.get("category"):
                    note["conflict"] = (f"The {state} 2025 state report (p. {page}) lists {unit} as {cat_r}; the "
                                        f"national 2025 list (AI2025) gives {rec.get('category')}. Both are shown; "
                                        "the report's figures are held back until this is resolved.")
                    note["reason"] = note["conflict"]
            extra.append(note)
            rule.setdefault("warnings", []).append(note["reason"])
            if row is not None:
                row["figures_note"] = note["reason"]
    if extra:
        rule["state_report_gaps"] = extra
    return rule


def _enrich_area(rule, place, lang):
    """District answer: say how many of its units have state-report figures (instead of 'not available here')."""
    if place.get("type") != "district" or place.get("state") in SKIP_STATES:
        return
    try:
        res = gwra.district_units(place["state"], place["district"])
    except Exception:                    # noqa: BLE001
        return
    if res.get("status") != "ok":
        return
    n, total = res["units_with_figures"], res["units_total"]
    line = (f"The {place['state']} 2025 state report has unit-level figures for {n} of {total} units in "
            f"{place['district']} district; ask about a block / taluk / mandal to see its figures." if n else
            (SHORT.get(place["state"]) or f"The {place['state']} 2025 state report has no unit-level figures for "
                                          f"this district."))
    text = rule.get("text") or ""
    for lg in {lang, "en"}:
        try:
            s = L.t("area_no_numeric", lg)
        except Exception:                # noqa: BLE001
            s = None
        if s and "{" not in s and s in text:
            text = text.replace(s, line)
            break
    else:
        text = (text + "\n" + line).strip()
    rule["text"] = text
    for row in rule.get("table") or []:
        if isinstance(row, dict) and row.get("area", "").startswith(place["district"]):
            row["units_with_state_report_figures"] = n


def conflict_count():
    """Number of units whose state-report category differs from the national list (held back), read-only."""
    if gwra is None:
        return 0
    try:
        with gwra._connect() as con:
            return con.execute("select count(*) from unit_resources where status='category_conflict'").fetchone()[0]
    except Exception:                    # noqa: BLE001
        return 0

"""
response_builder.py - Turn structured retrieval results into answers.

Only fixed templates from language.py are used. Every number in an answer is
copied from a database field with retrieval.fmt(); nothing is estimated,
rounded for effect or invented. Missing values are reported as "not
available" (NULL is never shown as 0). Quality warnings and source citations
are added to every answer that uses records with flags or sources.

Styles (mode=):
  farmer   simple: category, stage if published, what it means, one tip
  official all published figures (ham and bcm), category limits, area totals
  student  (3.0) concepts: why the category follows from the stage, key term, limits
Detail (detail=, JalMitra 3.0):
  short    direct answer and key finding only
  standard the 2.0 answer (unchanged, so all 2.0 tests keep their meaning)
  detailed labelled sections: finding (published classification), data
           (published assessment figures), reasoning, interpretation, general
           advice, missing information, limitations, sources
Nothing is added to make an answer longer: every extra sentence is either a
database value, a fixed definition, or an explicit statement of what is missing.
"""

import database as db
import knowledge_answer
import language as L
from retrieval import fmt, numbers_available

CONCERN = {"Semi-critical", "Critical", "Over-exploited"}
# stage-of-extraction bands of the GWRA categories (lower bound exclusive, upper inclusive)
BANDS = {"Safe": (None, 70, "≤ 70%"), "Semi-critical": (70, 90, "70–90%"), "Critical": (90, 100, "90–100%"),
         "Over-exploited": (100, None, "> 100%")}


def bold(label):
    return f"**{label}:**"


def reason_for(r, lang):
    """'The stage (x%) lies in the band ..., classified as ...' only when the published stage really lies in
    the band of the published category (records with a category/stage mismatch get the warning instead)."""
    cat, st = r["category"], r["stage_of_extraction_pct"]
    if cat not in BANDS or st is None or "category_stage_mismatch" in (r.get("quality_flag") or ""):
        return None
    lo, hi, band = BANDS[cat]
    if (lo is not None and st <= lo) or (hi is not None and st > hi):
        return None
    return L.t("reason", lang, stage=fmt(st), band=band, cat=L.category_label(cat, lang))


def show_name(name):
    """Place name as stored in the database; only '_' is shown as a space."""
    return str(name or "").replace("_", " ")


def place_label(p, lang):
    if p["type"] == "unit":
        return show_name(p["name"])
    if p["type"] == "district":
        return L.t("district_label", lang, district=show_name(p["district"]), state=p["state"])
    return p["state"]


def option_label(p, lang):
    if p["type"] == "unit":
        return L.t("opt_unit", lang, unit=show_name(p["name"]), kind=L.unit_type_label(p.get("kind"), lang),
                   district=show_name(p["district"]), state=p["state"])
    if p["type"] == "district":
        return L.t("district_label", lang, district=show_name(p["district"]), state=p["state"])
    return L.t("opt_state", lang, state=p["state"])


def _volume(orig, unit, bcm, lang):
    if orig is None:
        return L.t("not_available", lang)
    if unit == "bcm" or bcm is None:
        return f"{fmt(orig)} {unit or ''}".strip()
    return f"{fmt(orig)} {unit} ({fmt(bcm)} bcm)"


# ------------------------------------------------------------------ warnings

def warnings_for(r, lang):
    flags = set((r.get("quality_flag") or "").split(";")) - {""}
    unit = show_name(r["assessment_unit"])
    out = []
    if "category_stage_mismatch" in flags:
        out.append(L.t("w_mismatch", lang, unit=unit, cat=L.category_label(r["category"], lang),
                       stage=fmt(r["stage_of_extraction_pct"]), vcat=L.category_label(r["validation_category"], lang)))
    if "stage_calculation_mismatch" in flags:
        ext, tot = r["extractable_resource_original"], r["total_extraction_original"]
        if ext:
            out.append(L.t("w_stagecalc", lang, unit=unit, stage=fmt(r["stage_of_extraction_pct"]),
                           calc=f"{100 * tot / ext:.1f}"))
    if "measurements_require_verification" in flags:
        out.append(L.t("w_saline_zero", lang, unit=unit))
    if "category_conflict_between_sources" in flags:
        obs = " | ".join(f"{o['source_id']} (p {o['source_page']}): {o['observation']}" for o in r.get("_conflicts") or [])
        out.append(L.t("w_conflict", lang, unit=unit, obs=obs or "-"))
    if "truncated_name_in_values_source" in flags or "matched_by_name_prefix" in flags:
        out.append(L.t("w_truncated", lang, unit=unit, printed=r.get("values_source_unit_name") or "?",
                       sid=r.get("values_source_id") or "?"))
    return out


# ------------------------------------------------------------------ citations

def citations(result, lang):
    refs = []
    for r in result["records"]:
        refs.append(L.t("page_ref", lang, sid=r["source_id"], page=r["source_page"]))
        if r.get("values_source_id"):
            refs.append(L.t("page_ref", lang, sid=r["values_source_id"], page=r["values_source_page"]))
        for c in r.get("_conflicts") or []:
            if c["source_id"] != r["source_id"]:
                refs.append(L.t("page_ref", lang, sid=c["source_id"], page=c["source_page"]))
    for row in result["nc_rows"]:
        refs.append(L.t("page_ref", lang, sid="NC2025", page=row["source_page"]))
    kinds = {b["kind"] for b in result["blocks"]}
    if kinds & {"area", "list", "top_areas", "area_units", "quality_list", "coverage"}:
        refs.append("AI2025")
    refs = list(dict.fromkeys(refs))
    if not refs:
        return None
    shown = refs[:8] + (["..."] if len(refs) > 8 else [])
    return L.t("cite", lang, refs=", ".join(shown))


def source_rows(result):
    """Source table for the app (English metadata, one row per reference)."""
    rows = []
    for r in result["records"]:
        for s in db.sources_for(r):
            rows.append({"assessment_unit": r["assessment_unit"], **s})
    src = db.data_sources().get("NC2025", {})
    for row in result["nc_rows"]:
        rows.append({"assessment_unit": f"{row['district']} (district total)" if "district" in row else f"{row['state']} (state total)",
                     "used_for": "area total (National Compilation)", "source_id": "NC2025", "title": src.get("title"),
                     "page": str(row["source_page"]), "url": src.get("source_url"), "file": src.get("file_name")})
    out, seen = [], set()
    for r in rows:
        k = tuple(sorted((k, str(v)) for k, v in r.items()))
        if k not in seen:
            seen.add(k)
            out.append(r)
    return out


# ------------------------------------------------------------------ blocks

def _unit_lines(b, lang, mode, detail="standard"):
    if detail == "detailed":
        return _unit_detailed(b, lang, mode)
    r = b["record"]
    if detail == "short":
        lines = [L.t("unit_cat", lang, unit=show_name(r["assessment_unit"]),
                     kind=L.unit_type_label(r["assessment_unit_type"], lang), district=show_name(r["district"]),
                     state=r["state"], cat=L.category_label(r["category"], lang))]
        if numbers_available(r):
            st = r["stage_of_extraction_pct"]
            lines.append(L.t("unit_stage", lang, stage=fmt(st)) if st is not None else L.t("unit_stage_null", lang))
            if b.get("numbers"):
                lines.append(_figures(r, lang))
        else:
            lines.append(L.t("unit_cat_only", lang))
        return " ".join(lines)
    lines = [L.t("unit_cat", lang, unit=show_name(r["assessment_unit"]), kind=L.unit_type_label(r["assessment_unit_type"], lang),
                 district=show_name(r["district"]), state=r["state"], cat=L.category_label(r["category"], lang))]
    if numbers_available(r):
        st = r["stage_of_extraction_pct"]
        lines.append(L.t("unit_stage", lang, stage=fmt(st)) if st is not None else L.t("unit_stage_null", lang))
        if b.get("numbers") or mode == "official":
            lines.append(L.t("figures", lang,
                             recharge=_volume(r["annual_recharge_original"], r["annual_recharge_original_unit"], r["annual_recharge_bcm"], lang),
                             extractable=_volume(r["extractable_resource_original"], r["extractable_resource_original_unit"], r["extractable_resource_bcm"], lang),
                             extraction=_volume(r["total_extraction_original"], r["total_extraction_original_unit"], r["total_extraction_bcm"], lang)))
    else:
        lines.append(L.t("unit_cat_only", lang))
    if mode == "student" and reason_for(r, lang):
        lines.append(reason_for(r, lang))
    if mode in ("farmer", "student") and f"meaning_{r['category']}" in L.TEMPLATES:
        lines.append(L.t(f"meaning_{r['category']}", lang))
    return " ".join(lines)


def _figures(r, lang):
    return L.t("figures", lang,
               recharge=_volume(r["annual_recharge_original"], r["annual_recharge_original_unit"], r["annual_recharge_bcm"], lang),
               extractable=_volume(r["extractable_resource_original"], r["extractable_resource_original_unit"], r["extractable_resource_bcm"], lang),
               extraction=_volume(r["total_extraction_original"], r["total_extraction_original_unit"], r["total_extraction_bcm"], lang))


def _unit_detailed(b, lang, mode):
    """Labelled sections: published classification / published figures / reasoning / interpretation / missing."""
    r = b["record"]
    out = [bold(L.t("lbl_finding", lang)) + " " + L.t(
        "unit_cat", lang, unit=show_name(r["assessment_unit"]), kind=L.unit_type_label(r["assessment_unit_type"], lang),
        district=show_name(r["district"]), state=r["state"], cat=L.category_label(r["category"], lang))]
    if numbers_available(r):
        st = r["stage_of_extraction_pct"]
        stage = L.t("unit_stage", lang, stage=fmt(st)) if st is not None else L.t("unit_stage_null", lang)
        out.append(bold(L.t("lbl_data", lang)) + " " + stage + " " + _figures(r, lang))
        why = reason_for(r, lang)
        if why:
            out.append(bold(L.t("lbl_reason", lang)) + " " + why)
    else:
        out.append(bold(L.t("lbl_missing", lang)) + " " + L.t("unit_cat_only", lang))
    if mode != "official" and f"meaning_{r['category']}" in L.TEMPLATES:
        out.append(bold(L.t("lbl_meaning", lang)) + " " + L.t(f"meaning_{r['category']}", lang))
    return "  \n".join(out)


def _area_lines(b, lang, mode, detail="standard"):
    p = b["place"]
    area = place_label(p, lang)
    parts = ", ".join(f"{n} {L.category_label(c, lang)}" for c, n in b["counts"].items() if n)
    lines = [L.t("area_counts", lang, area=area, total=b["total"], parts=parts or "0")]
    if detail == "short":
        return lines[0]
    lines.append(L.t("area_numeric", lang, n=b["numeric"], total=b["total"]) if b["numeric"] else L.t("area_no_numeric", lang))
    out = [" ".join(lines)]
    if b.get("nc") is not None and (b.get("nc_shown") or mode == "official" or detail == "detailed"):
        if not b["nc"]:
            out.append(L.t("nc_missing", lang, area=area))
        for row in b["nc"]:
            st = row["stage_of_extraction_pct"]
            out.append(L.t("nc_total", lang, area=area, page=row["source_page"],
                           stage=(fmt(st) + "%") if st is not None else L.t("not_available", lang),
                           recharge=_volume(row["annual_recharge"], row["original_unit"], row["annual_recharge_bcm"], lang),
                           extraction=_volume(row["total_extraction"], row["original_unit"], row["total_extraction_bcm"], lang)))
    return "\n\n".join(out)


def _names(rows, lang, limit=15):
    names = ", ".join(show_name(r["assessment_unit"]) for r in rows[:limit])
    text = L.t("list_names", lang, names=names)
    if len(rows) > limit:
        text += " " + L.t("list_more", lang, k=len(rows) - limit)
    return text


def _area_or_db(p, lang):
    return place_label(p, lang) if p else L.t("whole_db", lang)


def _numeric_scope(lang):
    c = db.coverage()
    states = {r["state"] for r in c["numeric_by_state"]}
    if states == {"Rajasthan"}:
        return L.t("numeric_scope", lang, n=c["numeric_units"])
    return ", ".join(f"{r['n']} {r['state']}" for r in c["numeric_by_state"]) or "-"


def _domain_lines(b, lang):
    domain = L.t("dom_" + (b.get("domain") or "soil"), lang)
    places = b.get("places") or []
    if not places:
        return L.t("domain_unavailable", lang, domain=domain) + "\n\n" + L.t("domain_choose_place", lang)
    names = L.t("and", lang).join(place_label(p, lang) for p in places)
    return L.t("domain_unavailable_place", lang, domain=domain, place=names) + "\n\n" + \
        L.t("domain_related", lang, place=names)


def _explain_context(b, lang):
    lines = [L.t("explain_prev", lang, place=place_label(p, lang), cat=L.category_label(c, lang)) for p, c in b["prev"]]
    lines += [L.t(f"explain_{c}", lang) for c in b["categories"]]
    return "  \n".join(lines) + "\n\n" + L.t("explain_stage", lang)


def render_block(b, lang, mode, detail="standard"):
    k = b["kind"]
    if k == "unit":
        return _unit_lines(b, lang, mode, detail)
    if k == "area":
        return _area_lines(b, lang, mode, detail)
    if k == "domain":
        if b.get("knowledge"):
            kb = b.get("_kb") or knowledge_answer.build(b["knowledge"], b.get("places") or [], lang, detail,
                                                         b.get("soil_report"))
            b["_kb"] = kb
            places = b.get("places") or []
            names = L.t("and", lang).join(place_label(p, lang) for p in places)
            head = tail = ""
            if places and not kb["has_place_data"] and b.get("domain") != "water_quality":
                head = L.t("k_place_head", lang, domain=L.t("dom_" + b["domain"], lang), place=names)
            if places:
                tail = L.t("domain_related", lang, place=names)
            return "\n\n".join(x for x in (head, knowledge_answer.render(kb), tail) if x)
        return _domain_lines(b, lang)
    if k == "list":
        area = _area_or_db(b["area"], lang)
        cat = L.category_label(b["category"], lang)
        if not b["count"]:
            return L.t("list_none", lang, area=area, cat=cat)
        text = L.t("list_cat", lang, area=area, n=b["count"], cat=cat)
        if not b["count_only"]:
            text += " " + _names(b["rows"], lang, limit=5 if detail == "short" else 15)
        return text
    if k == "area_units":
        return L.t("area_units", lang, area=place_label(b["area"], lang),
                   names=", ".join(show_name(r["assessment_unit"]) for r in b["rows"]))
    if k == "top":
        area = _area_or_db(b["area"], lang)
        cat_part = L.t("cat_part", lang, cat=L.category_label(b["category"], lang)) if b["category"] else ""
        if not b["rows"]:
            return L.t("top_none", lang, area=area + (cat_part if b["category"] else ""), numeric=_numeric_scope(lang))
        head = L.t("top_header_low" if b["order"] == "lowest" else "top_header", lang, n=len(b["rows"]), area=area, cat_part=cat_part)
        lines = [L.t("top_line", lang, i=i, unit=show_name(r["assessment_unit"]), district=show_name(r["district"]),
                     stage=fmt(r["stage_of_extraction_pct"]), cat=L.category_label(r["category"], lang))
                 for i, r in enumerate(b["rows"], 1)]
        return head + "  \n" + "  \n".join(lines) + "\n\n" + L.t("top_unranked", lang)
    if k == "top_areas":
        cat = L.category_label(b["category"], lang)
        if b["fallback"]:
            head = L.t("top_fallback", lang, cat=cat)
        elif b["level"] == "state":
            head = L.t("topareas_header_state", lang, cat=cat)
        else:
            in_part = L.t("in_part", lang, area=place_label(b["area"], lang)) if b["area"] else ""
            head = L.t("topareas_header_district", lang, cat=cat, in_part=in_part)
        lines = [L.t("topareas_line", lang, i=i, n=r["units"],
                     name=(f"{show_name(r['district'])} ({r['state']})" if "district" in r else r["state"]))
                 for i, r in enumerate(b["rows"], 1)]
        return head + "  \n" + "  \n".join(lines)
    if k == "compare_summary":
        items = b["items"]
        if not b["comparable"]:
            return ""
        with_stage = [i for i in items if i["stage"] is not None]
        missing = [place_label(i["place"], lang) for i in items if i["stage"] is None]
        if missing:
            return L.t("compare_no_numbers", lang, names=L.t("and", lang).join(missing))
        hi = max(with_stage, key=lambda i: i["stage"])
        lo = min(with_stage, key=lambda i: i["stage"])
        if hi["stage"] == lo["stage"]:
            return L.t("compare_equal", lang, sx=fmt(hi["stage"]))
        return L.t("compare_higher", lang, x=place_label(hi["place"], lang), sx=fmt(hi["stage"]),
                   y=place_label(lo["place"], lang), sy=fmt(lo["stage"]))
    if k == "need_two":
        return L.t("compare_need_two", lang)
    if k == "need_category":
        return L.t("need_category", lang)
    if k == "year_only":
        return L.t("year_only", lang, years=", ".join(b["years"]))
    if k == "year_missing":
        return L.t("year_missing", lang, year=b["year"], years=", ".join(b["years"]))
    if k == "explain":
        if b.get("categories"):
            return _explain_context(b, lang)
        if b["category"]:
            return L.t(f"explain_{b['category']}", lang) + " " + L.t("explain_stage", lang)
        if b.get("what") == "stage":
            return L.t("explain_stage", lang)
        return "  \n".join(L.t(f"explain_{c}", lang) for c in db.CATEGORIES) + "\n\n" + L.t("explain_stage", lang)
    if k == "sources":
        lines = [L.t("sources_header", lang, place=place_label(b["place"], lang))]
        for s in b["refs"]:
            u = s["used_for"]
            used = (L.t("used_category", lang) + u[len("category"):] if u.startswith("category") else
                    L.t("used_figures", lang) + u[len("figures"):] if u.startswith("figures") else
                    L.t("used_conflict", lang) if u.startswith("different") else
                    L.t("used_unit_type", lang) if u.startswith("unit type") else
                    L.t("used_area_total", lang) if u.startswith("area total") else u)
            lines.append(L.t("source_line", lang, sid=s["source_id"], title=s.get("title") or "", page=s["page"], used_for=used))
        return "  \n".join(lines)
    if k == "sources_general":
        lines = [L.t("sources_general", lang, years=", ".join(db.years()))]
        lines += [L.t("source_pub", lang, sid=s["source_id"], title=s["title"], url=s["source_url"]) for s in b["sources"]]
        return "  \n".join(lines)
    if k == "coverage":
        c = b["coverage"]
        return L.t("coverage", lang, total=f"{c['total_units']:,}", numeric=_numeric_scope(lang),
                   years=", ".join(c["years"]), states=c["states"])
    if k == "place_availability":
        if b["n"] and b["n"] == b["total"]:
            numbers = L.t("available", lang)
        elif b["n"]:
            numbers = L.t("partly_available", lang, n=b["n"], total=b["total"])
        else:
            numbers = L.t("not_available", lang)
        return L.t("place_availability", lang, place=place_label(b["place"], lang), numbers=numbers)
    if k == "quality_list":
        lines = [L.t("quality_header", lang, n=len(b["rows"]))]
        for r in b["rows"]:
            flags = ", ".join(f for f in r["quality_flag"].split(";") if f != "values_not_in_uploaded_sources")
            lines.append(L.t("quality_line", lang, unit=show_name(r["assessment_unit"]), district=show_name(r["district"]),
                             state=r["state"], flags=flags))
        return "  \n".join(lines)
    if k == "quality_none":
        return L.t("quality_none", lang, place=place_label(b["place"], lang))
    return ""


# ------------------------------------------------------------------ whole answers

def build(result, lang, mode="farmer", notes=(), history_len=0, detail="standard", pre=()):
    paragraphs = [L.t("matched_note", lang, typed=typed, name=name) for typed, name in notes] + list(pre)
    if result["intent"] == "compare" and len(result["places"]) >= 2:
        paragraphs.append(L.t("compare_header", lang, names=L.t("and", lang).join(place_label(p, lang) for p in result["places"])))
    for b in result["blocks"]:
        text = render_block(b, lang, mode, detail)
        if text:
            paragraphs.append(text)

    cats = [r["category"] for r in result["records"]]
    intent = result["intent"]
    data_intents = ("status", "numeric", "compare", "quality", "domain")
    concern = intent in ("status", "numeric", "domain") and any(c in CONCERN for c in cats)
    if detail == "standard":
        if mode == "farmer" and intent in ("status", "numeric") and concern:
            paragraphs.append(L.t("tip", lang))
        if mode == "official" and result["records"] and intent in ("status", "numeric", "compare", "quality"):
            paragraphs.append(L.t("thresholds", lang))
        if mode == "student" and result["records"] and intent in ("status", "numeric", "compare"):
            paragraphs.append(bold(L.t("lbl_term", lang)) + " " + L.t("explain_stage", lang) + "  \n" + L.t("thresholds", lang))
    elif detail == "detailed" and (result["records"] or result["nc_rows"]) and intent in data_intents:
        if mode == "official":
            paragraphs.append(bold(L.t("lbl_method", lang)) + " " + L.t("method", lang) + "  \n" + L.t("thresholds", lang))
        else:
            paragraphs.append(bold(L.t("lbl_term", lang)) + " " + L.t("explain_stage", lang) + "  \n" + L.t("thresholds", lang))
        if concern and mode != "official":
            paragraphs.append(bold(L.t("lbl_advice", lang)) + " " + L.t("tip", lang))
        if intent != "domain":
            paragraphs.append(bold(L.t("lbl_missing", lang)) + " " + L.t("missing_domains", lang))
        paragraphs.append(bold(L.t("lbl_limits", lang)) + " " + L.t("limitations", lang, year=", ".join(db.years())))

    warnings = []
    for r in result["records"]:
        for w in warnings_for(r, lang):
            if w not in warnings:
                warnings.append(w)
    for row in result["nc_rows"]:
        if row.get("quality_flag"):
            area = row.get("district") or row.get("state")
            warnings.append(L.t("w_nc_flag", lang, area=area, flags=row["quality_flag"].replace(";", ", ")))

    cite = citations(result, lang)
    if cite:
        paragraphs.append(cite)

    followups = []
    if result["intent"] in ("status", "numeric", "domain") and result["places"]:
        followups = [L.t("fu_sources", lang), L.t("fu_other", lang)]
        if history_len >= 2:
            followups.append(L.t("fu_both", lang))
        if cats:
            followups.append(L.t("fu_meaning", lang, cat=cats[0]))

    table, sources, status = result["table"], source_rows(result), result["status"]
    for b in result["blocks"]:
        kb = b.get("_kb")
        if kb:
            table = list(table or []) + kb["table"]
            sources = sources + knowledge_answer.source_rows(kb)
            if kb["has_place_data"]:
                status = "ok"
            elif not b.get("places"):
                status = "knowledge"
    return {"text": "\n\n".join(paragraphs), "warnings": warnings, "table": table,
            "sources": sources, "chart": result["chart"],
            "year": result["year"] if (result["status"] in ("ok", "not_available") or result["records"]
                                       or result["nc_rows"]) else None,
            "followups": followups, "status": status}


def build_message(key, lang, **values):
    return {"text": L.t(key, lang, **values), "warnings": [], "table": [], "sources": [], "chart": None,
            "year": None, "followups": [], "status": key}


def build_clarify(name, options, lang, not_found=False, head_key=None):
    if head_key:
        head = L.t(head_key, lang)
    else:
        head = (L.t("not_found", lang, name=name) + " " + L.t("did_you_mean", lang)) if not_found \
            else L.t("clarify", lang, name=name)
    lines = [f"{i}. {option_label(p, lang)}" for i, p in enumerate(options, 1)]
    out = build_message("clarify", lang)
    out["text"] = head + "  \n" + "  \n".join(lines)
    out["options"] = [option_label(p, lang) for p in options]
    out["status"] = "not_found" if not_found else "clarify"
    return out

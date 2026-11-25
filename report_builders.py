"""
report_builders.py - Content of the six JalMitra reports (Groundwater, Soil Health, Land Condition,
Crop Suitability, Irrigation, Complete). Each builder returns (title, sections, tables) where
sections = [(heading, markdown text)]. Only verified values, the user's own confirmed soil report,
and labelled general text are used; everything else is written as missing.
"""

import database as db
import engine
import knowledge as kn
import knowledge_answer as ka
import language as L
import response_builder as rb
import soil_interpret as si
import water_quality as wq

NA = kn.NOT_AVAILABLE
LAND_USES = ["Field crops (irrigated)", "Field crops (rainfed)", "Horticulture", "Grazing / pasture", "Agroforestry"]


def _lang(lang):
    return lang if lang in L.LANGUAGES else "en"


def place_text(place, lang="en"):
    return rb.place_label(place, _lang(lang)) if place else "No location chosen"


def groundwater_sections(place, lang="en", detail="detailed", mode="official"):
    lang = _lang(lang)
    if place is None:
        counts = db.category_counts()
        text = ", ".join(f"{L.category_label(c, lang)}: {n}" for c, n in counts.items())
        return [("National overview (AI2025)", text)], []
    r = engine.answer_places("status", [place], lang, mode, detail)
    secs = [("Groundwater status", r["text"])]
    if r["warnings"]:
        secs.append(("Data-quality warnings", "\n".join("– " + w for w in r["warnings"])))
    secs.append(("Category is not water quality", wq.category_note(lang)))
    tables = []
    if r["sources"]:
        tables.append(("Source records", [{k: s.get(k) for k in ("source_id", "title", "page", "url")} for s in r["sources"]]))
    return secs, tables


def groundwater_report(place, lang="en"):
    secs, tables = groundwater_sections(place, lang)
    return "JalMitra Groundwater Report", secs, tables


def soil_report(report, lang="en"):
    if not report or not report.get("rows"):
        return "JalMitra Soil Health Report", [("Soil Health Report", "No confirmed soil report in this session. " + NA + ".")], []
    res = si.interpret(report["rows"])
    rows = [{"parameter": it["parameter"], "value": it["value"], "unit": it["unit"], "card rating": it["card_rating"],
             "ratings": "; ".join(f"{g['source_id']}: {g.get('class_label') or g['status']}" for g in it["ratings"])}
            for it in res["items"]]
    return "JalMitra Soil Health Report", si.report_sections(res, report.get("meta", {}), lang), [("Confirmed values", rows)]


def land_condition_sections(place, lang="en"):
    """The 15 sections of the Land Condition Report named in the master instruction."""
    lang = _lang(lang)
    cl = ka.content_lang(lang)
    st, d = ka._district(place) if place else (None, None)
    zone = kn.zone_for(st, d)
    counts = {t: len(kn.observations(t, st, d)) if place else 0
              for t in ("land_use_records", "land_capability_records", "land_degradation_records", "slope_records",
                        "soil_map_units", "soil_properties")}
    gw = engine.answer_places("status", [place], lang, "farmer", "short")["text"] if place else NA
    general = "\n".join(f"– **{kn.text_of(g, 'title', cl)}.** {kn.text_of(g, 'text', cl)}" for g in kn.guidance("conservation"))
    zone_soil = (f"{zone['zone']['name']} ({zone['coverage']}): {zone['zone']['soils_text']}. "
                 f"_Published regional description, not field data ({kn.cite(zone['zone']['source_id'])})._") if zone else NA
    zone_problems = (f"{zone['zone']['problems_text']} (zone-wide, {kn.cite(zone['zone']['source_id'])})") if zone else ""
    missing = [name for name, key in (("Land use / land cover", "land_use_records"), ("Land capability", "land_capability_records"),
                                      ("Land degradation map", "land_degradation_records"), ("Slope", "slope_records"),
                                      ("Soil map units", "soil_map_units"), ("Soil properties", "soil_properties"))
               if not counts[key]]
    years = ", ".join(db.years())
    secs = [
        ("Location", place_text(place, lang)),
        ("Coverage", f"Groundwater: assessment-unit level for all of India ({years}). Soil and land layers: {NA}."),
        ("Source and year", f"Groundwater: AI2025, RJ2025, NC2025 ({years}). Land and soil maps: {NA}."),
        ("Resolution", "Groundwater: one value per assessment unit (block/taluk). No land or soil map layer is loaded."),
        ("Landform", NA),
        ("Terrain and slope", NA if not counts["slope_records"] else f"{counts['slope_records']} slope records imported"),
        ("Soil", zone_soil),
        ("Drainage", NA),
        ("Water (verified groundwater category)", gw),
        ("Degradation", (NA + (f". Regional note: {zone_problems}" if zone_problems else ""))),
        ("Potential", "Insufficient data"),
        ("Limitations", "Land limitations cannot be stated without slope, soil, drainage and degradation data. "
                        "JalMitra makes no legal or engineering claims about land."),
        ("Management (general, not a formal recommendation)", general + "\n_" + kn.cite("JALMITRA_GENERAL") + "_"),
        ("Missing information", ", ".join(missing) + ". Shown as missing, never as zero."),
        ("References", "\n".join("– " + kn.cite(s) for s in (["SKNAU_FATEHPUR"] if zone else []) + ["JALMITRA_GENERAL"])
         + "\n– Groundwater: AI2025, RJ2025, NC2025 (see Data Sources)"),
    ]
    return secs


def land_use_table():
    return [{"intended use": u, "class": "Insufficient data",
             "why": "No slope, soil, drainage or degradation data for this place in the current dataset"} for u in LAND_USES]


def land_report(place, lang="en"):
    return "JalMitra Land Condition Report", land_condition_sections(place, lang), [("Is my land good? (by use)",
                                                                                      land_use_table())]


def crop_report(place, crop_ids, lang="en"):
    crop_ids = list(crop_ids or [])
    kd = {"domain": "crop", "topic": "compare_crops" if len(crop_ids) > 1 else ("crop" if crop_ids else "crops_general"),
          "parameters": [], "crops": crop_ids}
    kb = ka.build(kd, [place] if place else [], _lang(lang), "detailed")
    return "JalMitra Crop Suitability Report", kb["sections"], [("Crop facts (published) and suitability", kb["table"])]


def irrigation_report(place, lang="en"):
    kb = ka.build({"domain": "irrigation", "topic": "irrigation", "parameters": [], "crops": []},
                  [place] if place else [], _lang(lang), "detailed")
    secs = kb["sections"]
    if place:
        secs = [("Groundwater category of the area", engine.answer_places("status", [place], _lang(lang), "farmer",
                                                                          "short")["text"])] + secs
    rows = [{"crop (FAO label)": r["fao_water_label"], "mm per season": f"{r['water_need_min_mm']:g}–{r['water_need_max_mm']:g}",
             "drought sensitivity": r["drought_sensitivity"]} for r in kn.water_needs_sorted()]
    return "JalMitra Irrigation Report", secs, [("Seasonal crop water need (FAO Table 14, rough estimates)", rows)]


def complete_report(place, soil, crop_ids, lang="en"):
    secs, tables = [], []
    for title, s, t in (groundwater_report(place, lang), soil_report(soil, lang), land_report(place, lang),
                        crop_report(place, crop_ids, lang), irrigation_report(place, lang)):
        secs.append((f"=== {title.replace('JalMitra ', '')} ===", ""))
        secs += s
        tables += t
    return "JalMitra Complete Report", secs, tables

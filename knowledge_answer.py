"""
knowledge_answer.py - Soil, land, crop, irrigation and water-quality answers (JalMitra 3.0, Phases 2-5).

detect(text)  -> what a question asks about (domain, topic, parameters, crops) or None
build(...)    -> an answer block whose sections keep apart:
                 measured facts | published category | published regional description |
                 scientific interpretation | general suggestions | missing information
Every value comes from data/knowledge.db (reference tables with source, table and page),
from data/observations.db (imported measurements, empty until naveen imports them),
or from the user's own confirmed soil report. Nothing is estimated or invented.
"""

import knowledge as kn
import language as L
import water_quality as wq

WQ_WORDS = ["drinking", "drink", "potable", "peene", "peene ka", "पीने", "पीने का", "पेयजल", "पीने योग्य",
            "water quality", "quality of water", "quality of the water", "pani ki quality", "paani ki quality",
            "पानी की गुणवत्ता", "जल गुणवत्ता", "भूजल गुणवत्ता", "groundwater quality", "ground water quality",
            "fluoride", "nitrate", "arsenic", "uranium", "tds", "hardness", "hard water", "khara pani", "khara paani",
            "खारा पानी", "contamination", "contaminated", "polluted", "pollution", "दूषित", "फ्लोराइड", "फ़्लोराइड",
            "नाइट्रेट", "आर्सेनिक", "यूरेनियम", "पिण्याचे", "पिण्याच्या", "ਪੀਣ ਵਾਲੇ", "पिण्यायोग्य", "पाण्याची गुणवत्ता", "ਪੀਣ", "ਪੀਣ ਵਾਲਾ",
            "ਪਾਣੀ ਦੀ ਗੁਣਵੱਤਾ", "पीवण", "पीवण रो"]
WATER_CTX = ["water", "pani", "paani", "पानी", "जल", "भूजल", "groundwater", "ground water", "well", "borewell",
             "tubewell", "handpump", "hand pump", "ਪਾਣੀ", "पाणी", "पाण्याचे", "पाण्याची"]
SOIL_CTX = ["soil", "soils", "mitti", "maati", "mati", "मिट्टी", "मिटटी", "माटी", "माती", "ਮਿੱਟੀ", "khet", "field",
            "खेत", "शेत", "ਖੇਤ", "land", "जमीन", "ज़मीन", "zameen", "fertility", "उर्वरता"]
WEAK_SOIL_ALIASES = {"saline", "salinity", "salt", "salty", "खारा", "खारी", "लवणता", "लवणीय", "नमक", "ਖਾਰਾ", "iron",
                     "आयरन", "लोहा", "sand", "clay", "silt", "रेत", "गाद", "चिकनी"}
LESS_WATER = ["less water", "low water", "little water", "lesser water", "minimum water", "kam pani", "kam paani",
              "कम पानी", "drought", "sookha", "sukha", "सूखा", "सूखे", "dry farming", "water saving", "save water",
              "need less", "needs less", "require less", "कमी पाणी", "ਘੱਟ ਪਾਣੀ", "कम पाणी"]
IMPROVE = ["improve", "improving", "increase", "increasing", "better", "boost", "enrich", "restore", "sudhar",
           "sudhaar", "sudharen", "badhaye", "badhayein", "badhane", "सुधार", "सुधारें", "सुधारे", "बढ़ा", "बढ़ाएं",
           "बढ़ाएँ", "बढ़ाने", "बढ़ाए", "सुधारूँ", "सुधारूं", "सुधारना", "सुधारने", "सुधरे", "बढ़ाऊँ", "बढ़ाऊं",
           "sudharun", "sudharna", "kaise sudhare", "सुधारो", "सुधारवी", "सुधारू", "वाढव", "सुधारणा", "ਸੁਧਾਰ", "ਵਧਾ"]
SOIL_TYPE = ["soil type", "type of soil", "kind of soil", "which soil", "what soil", "mitti ka prakar",
             "mitti kaun si", "kaun si mitti", "मिट्टी का प्रकार", "मिट्टी कौन सी", "कौन सी मिट्टी", "माती प्रकार",
             "मातीचा प्रकार", "ਮਿੱਟੀ ਦੀ ਕਿਸਮ", "माटी रो प्रकार", "soil profile",
             "किस प्रकार", "किस तरह की मिट्टी", "kis prakar", "kis type", "kaun si type", "कोणत्या प्रकारची",
             "ਕਿਹੜੀ ਕਿਸਮ", "किसी माटी"]
CROP_WORDS = ["crop", "crops", "fasal", "fasl", "faslen", "फसल", "फ़सल", "फसलें", "फ़सलें", "पीक", "पिके", "ਫ਼ਸਲ",
              "ਫਸਲ", "ਫ਼ਸਲਾਂ", "फसलों", "फ़सलों", "fasalon", "faslon", "पिकांना", "पिकांची", "ਫਸਲਾਂ", "what to grow", "what should i grow", "which crop", "grow", "growing", "sow", "sowing",
              "farming", "cultivation", "kheti", "खेती", "शेती", "ਖੇਤੀ", "ugaye", "उगाएं", "उगाना", "फसलां"]
COMPARE = ["compare", "comparison", " vs ", "versus", "tulna", "तुलना", "or", "ya", "या", "किंवा", "ਜਾਂ", "better"]
IRRIGATION_WORDS = ["irrigation", "irrigate", "irrigating", "sinchai", "सिंचाई", "सिंचन", "ਸਿੰਚਾਈ"]
LAND_WORDS = ["land", "lands", "zameen", "zamin", "jameen", "bhumi", "भूमि", "जमीन", "ज़मीन", "ਜ਼ਮੀਨ", "जमीन",
              "land use", "slope", "terrain", "wasteland", "landform", "degradation", "degraded"]
SOIL_PARAM_IDS = set(kn.SOIL_HEALTH_PARAMETERS) | {"TEXTURE", "AWC"}
WATER_ID = {"W_pH": "pH", "W_TDS": "TDS", "W_EC": "EC", "W_F": "F", "W_NO3": "NO3", "W_As": "As", "W_Cl": "Cl",
            "W_Fe": "Fe", "W_TH": "TH", "W_U": "U", "W_SAR": "SAR", "W_RSC": "RSC"}


def _n(text):
    return kn._norm(text)


def _strong_soil_params(t):
    """Soil parameters named in the question; salt/iron/sand words count only with a soil word."""
    out = []
    soil_ctx = kn.has_any(t, SOIL_CTX)
    for p in kn.tables()["parameter_info"]:
        if p["parameter"] not in SOIL_PARAM_IDS:
            continue
        aliases = kn._aliases(p) + ((p["parameter"].lower(),) if len(p["parameter"]) >= 2 else ())
        strong = tuple(a for a in aliases if a not in WEAK_SOIL_ALIASES)
        weak = tuple(a for a in aliases if a in WEAK_SOIL_ALIASES)
        if kn.has_any(t, strong) or (soil_ctx and kn.has_any(t, weak)):
            out.append(p["parameter"])
    return out


def detect(text):
    """What the question is about, or None (then the groundwater rules handle it)."""
    t = _n(text)
    water_params = [WATER_ID[p] for p in kn.find_parameters(t, "water") if p in WATER_ID]
    if kn.has_any(t, WQ_WORDS) or (water_params and kn.has_any(t, WATER_CTX) and not kn.has_any(t, SOIL_CTX)):
        return {"domain": "water_quality", "topic": "water_quality", "parameters": water_params, "crops": []}
    crops = kn.find_crops(t)
    if kn.has_any(t, LESS_WATER) and (crops or kn.has_any(t, CROP_WORDS)):
        return {"domain": "crop", "topic": "less_water", "parameters": [], "crops": crops}
    soil_params = _strong_soil_params(t)
    if crops:
        topic = "compare_crops" if len(crops) >= 2 else "crop"
        return {"domain": "crop", "topic": topic, "parameters": soil_params, "crops": crops}
    if kn.has_any(t, IMPROVE) and (soil_params or kn.has_any(t, SOIL_CTX)):
        return {"domain": "soil", "topic": "soil_improve", "parameters": soil_params, "crops": []}
    if kn.has_any(t, SOIL_TYPE) or kn.find_guidance(t, "soil_type"):
        named = [g["key"] for g in kn.find_guidance(t, "soil_type")]
        return {"domain": "soil", "topic": "soil_type", "parameters": [], "crops": [], "keys": named}
    if soil_params:
        return {"domain": "soil", "topic": "soil_param", "parameters": soil_params, "crops": []}
    methods = [g["key"] for g in kn.find_guidance(t, "irrigation")]
    if kn.has_any(t, IRRIGATION_WORDS) or (methods and not kn.has_any(t, LAND_WORDS + ["erosion", "कटाव", "धूप", "ਖੋਰ"])):
        return {"domain": "irrigation", "topic": "irrigation", "parameters": [], "crops": [], "keys": methods}
    degr = [g["key"] for g in kn.find_guidance(t, "degradation")]
    cons = [g["key"] for g in kn.find_guidance(t, "conservation")]
    if degr or cons or kn.has_any(t, ["erosion", "कटाव", "degradation", "degraded", "क्षरण", "धूप", "ਖੋਰ", "झीज"]):
        return {"domain": "land", "topic": "land_degradation", "parameters": [], "crops": [], "keys": degr + cons}
    if kn.has_any(t, CROP_WORDS):
        return {"domain": "crop", "topic": "crops_general", "parameters": [], "crops": []}
    if kn.has_any(t, LAND_WORDS):
        return {"domain": "land", "topic": "land_general", "parameters": [], "crops": []}
    if kn.has_any(t, SOIL_CTX[:10] + ["fertility", "fertile", "nutrient", "nutrients", "उर्वरता", "पोषक"]):
        return {"domain": "soil", "topic": "soil_general", "parameters": [], "crops": []}
    return None


# ------------------------------------------------------------------ helpers

def content_lang(lang):
    return "hi" if lang in ("hi", "mr", "raj") else "en"


def _district(p):
    if p is None:
        return None, None
    if p["type"] == "district":
        return p["state"], p.get("district") or p["name"]
    if p["type"] == "unit":
        return p["state"], p.get("district")
    return p["state"], None


def _place_label(p, lang):
    import response_builder as rb
    return rb.place_label(p, lang)


def _crop_name(c, lang):
    return c["name_hi"] if content_lang(lang) == "hi" else c["name_en"]


def _range_lines(domain, parameter):
    rows = kn.range_table(domain, parameter)
    by = {}
    for r in rows:
        by.setdefault(r["source"], []).append(f"{r['class']} {r['range']} {r['unit']}".replace(" pH", ""))
    return [f"{src}: " + "; ".join(v) for src, v in by.items()]


def _report_value(report, pid):
    if not report:
        return None
    return next((r for r in report.get("rows", []) if r.get("parameter") == pid and r.get("value") not in (None, "")),
                None)


# ------------------------------------------------------------------ main builder

def build(kd, places, lang="en", detail="standard", soil_report=None):
    """Return {"sections": [(label, text)], "table": [...], "sources": [source_id], "has_place_data": bool}."""
    cl = content_lang(lang)
    sec, table, srcs = [], [], []
    note = L.t("k_content_note", lang).strip()
    place = places[0] if places else None
    topic = kd["topic"]
    detailed = detail == "detailed"
    short = detail == "short"
    has_data = False

    def add(label_key, lines):
        lines = [x for x in lines if x]
        if lines:
            sec.append((L.t(label_key, lang), "  \n".join(lines)))

    # ---------------- soil parameter / soil type / soil general / improve
    if topic in ("soil_param", "soil_general", "soil_improve", "soil_type"):
        measured, interp, general, missing = [], [], [], []
        params = kd.get("parameters") or []
        if soil_report and soil_report.get("rows"):
            date = soil_report.get("meta", {}).get("sample_date") or "-"
            shown = params or [r["parameter"] for r in soil_report["rows"] if r.get("value") not in (None, "")]
            measured.append(L.t("k_your_report", lang, date=date))
            for pid in shown:
                r = _report_value(soil_report, pid)
                if r is None:
                    measured.append("– " + L.t("k_report_missing_param", lang, param=pid))
                    continue
                has_data = True
                ratings = kn.classify("soil", pid, float(r["value"]), r.get("unit") or "")
                rated = [f"{g['class_label']} ({g['source_id']})" for g in ratings if g["status"] == "rated"]
                card = f"; card: {r['card_rating']}" if r.get("card_rating") else ""
                measured.append(f"– {pid}: {float(r['value']):g} {r.get('unit') or ''}{card}" +
                                (f" → {', '.join(rated)}" if rated else ""))
        else:
            what = L.t("k_what_soil_type", lang) if topic == "soil_type" else L.t("k_what_soil", lang)
            measured.append(L.t("k_not_in_dataset", lang, what=what, place=_place_label(place, lang)) if place
                            else L.t("k_no_value_place", lang))
            measured.append(L.t("k_upload", lang))
        for pid in params:
            info = kn.parameter(pid)
            if info:
                interp.append(f"**{kn.text_of(info, 'name', cl)}.** {kn.text_of(info, 'what', cl)}")
                if not short:
                    rl = _range_lines("soil", pid)
                    if rl:
                        interp.append(L.t("k_ranges_head", lang) + " " + " | ".join(rl))
                        srcs += [r["source"] for r in kn.range_table("soil", pid)]
                if pid == "EC":
                    interp.append(L.t("k_ece_warn", lang))
                    sal = next((g for g in kn.guidance("degradation") if g["key"] == "salinity"), None)
                    if sal and not short:
                        interp.append(f"**{kn.text_of(sal, 'title', cl)}.** {kn.text_of(sal, 'text', cl)}")
        if topic == "soil_type":
            keys = kd.get("keys") or []
            types = kn.guidance("soil_type")
            chosen = [g for g in types if g["key"] in keys] or ([] if short else types)
            if not keys and not short:
                interp.append(L.t("k_soil_types_head", lang))
            for g in chosen:
                interp.append(f"– **{kn.text_of(g, 'title', cl)}.** {kn.text_of(g, 'text', cl)}")
        if topic in ("soil_general", "soil_type") and not has_data:
            interp.insert(0, L.t("k_cannot_judge_soil", lang))
        if topic == "soil_improve" or (topic == "soil_general" and not short):
            for g in kn.guidance("improve"):
                general.append(f"– **{kn.text_of(g, 'title', cl)}.** {kn.text_of(g, 'text', cl)}")
            srcs.append("JALMITRA_GENERAL")
        add("k_measured", measured)
        _regional(place, lang, cl, add, srcs, kind="soil")
        add("k_interpret", interp)
        if not short:
            add("k_general", general)
        if not short:
            missing.append(L.t("k_not_in_dataset_any", lang, what="NBSS&LUP soil map, AWC, depth, texture"))
            add("k_missing", missing)

    # ---------------- crops
    elif topic in ("crop", "compare_crops", "crops_general", "less_water"):
        measured, interp, general = [], [], []
        zone = _zone(place)
        if topic == "less_water":
            interp.append(L.t("k_less_water_head", lang))
            rows = kn.water_needs_sorted()
            for r in rows[: (6 if short else len(rows))]:
                note = f" ⚠️ {r['note']}" if (r["note"] and "JalMitra note" in r["note"]) else ""
                interp.append(f"– {r['fao_water_label']}: {r['water_need_min_mm']:g}–{r['water_need_max_mm']:g} mm "
                              f"({r['drought_sensitivity']}){note}")
                table.append({"crop (FAO label)": r["fao_water_label"], "water_need_min_mm": r["water_need_min_mm"],
                              "water_need_max_mm": r["water_need_max_mm"],
                              "drought_sensitivity": r["drought_sensitivity"], "source": "FAO_CROP_WATER Table 14"})
            srcs.append("FAO_CROP_WATER")
            if zone:
                listed = ", ".join(_crop_name(kn.crop(z["crop_id"]), lang) + f" ({z['season']})" for z in zone["crops"])
                measured.append(f"{zone['zone']['name']} ({zone['coverage']}): {listed}")
                srcs.append(zone["zone"]["source_id"])
            add("k_regional", measured)
            add("k_interpret", interp)
            if not short:
                add("k_missing", [L.t("k_no_schedule", lang)])
        else:
            crop_ids = kd.get("crops") or []
            if topic == "compare_crops":
                names = L.t("and", lang).join(_crop_name(kn.crop(c), lang) for c in crop_ids)
                interp.append(L.t("k_compare_crops", lang, crops=names))
            suit = []
            for cid in crop_ids:
                f = kn.crop_facts(cid)
                c = f["crop"]
                name = _crop_name(c, lang)
                suit.append(L.t("k_insufficient", lang, what=L.t("k_what_suit", lang, crop=name)))
                lines = [f"**{name}**"]
                if zone:
                    z = [x for x in f["zones"] if x["zone_id"] == zone["zone"]["zone_id"]]
                    if z:
                        season = L.t("k_season_" + z[0]["season"].lower(), lang)
                        lines.append(L.t("k_zone_listed", lang, crop=name, season=season, zone=zone["zone"]["name"],
                                         coverage=zone["coverage"]))
                    else:
                        lines.append(L.t("k_zone_not", lang, crop=name, zone=zone["zone"]["name"]))
                    srcs.append(zone["zone"]["source_id"])
                if f["salt"]:
                    s = f["salt"]
                    thr = L.t("k_salt_threshold", lang, t="%g" % s["ece_threshold_dS_m"]) if s["ece_threshold_dS_m"] else ""
                    rating = {"T": "tolerant", "MT": "moderately tolerant", "MS": "moderately sensitive",
                              "S": "sensitive"}.get(s["rating"], s["rating"])
                    lines.append(L.t("k_salt", lang, rating=f"{rating} ({s['rating']})", threshold=thr))
                    srcs.append("FAO_SALT_TOLERANCE")
                else:
                    lines.append(L.t("k_salt_none", lang))
                if f["water"]:
                    w = f["water"]
                    lines.append(L.t("k_water", lang, lo="%g" % w["water_need_min_mm"], hi="%g" % w["water_need_max_mm"],
                                     sens=w["drought_sensitivity"]) + f" [FAO: {w['fao_water_label']}]")
                    srcs.append("FAO_CROP_WATER")
                else:
                    lines.append(L.t("k_water_none", lang))
                interp.append("  \n".join(lines))
                table.append({"crop": c["name_en"],
                              "zone listing": (", ".join(f"{x['zone_id']} {x['season']}" for x in f["zones"]) or "—"),
                              "FAO salt rating": f["salt"]["rating"] if f["salt"] else "not in table",
                              "ECe threshold dS/m": (f["salt"] or {}).get("ece_threshold_dS_m"),
                              "water need mm": (f"{f['water']['water_need_min_mm']:g}–{f['water']['water_need_max_mm']:g}"
                                                if f["water"] else "not in table"),
                              "drought sensitivity": (f["water"] or {}).get("drought_sensitivity") or "not in table",
                              "suitability": "Insufficient data"})
            if topic == "crops_general":
                if zone:
                    for season in ("Kharif", "Rabi"):
                        names = [_crop_name(kn.crop(z["crop_id"]), lang) for z in zone["crops"] if z["season"] == season]
                        if names:
                            measured.append(f"{L.t('k_season_' + season.lower(), lang)}: {', '.join(names)}")
                    measured.append(f"_{zone['zone']['name']} ({zone['coverage']})_")
                    srcs.append(zone["zone"]["source_id"])
                elif place:
                    measured.append(L.t("k_no_zone", lang, place=_place_label(place, lang)))
                suit.append(L.t("k_insufficient", lang, what=L.t("k_what_crop", lang)))
            add("k_suitability", suit)
            add("k_regional", measured)
            if crop_ids and (kn.crop_facts(crop_ids[0])["salt"] is not None) and not short:
                interp.append(L.t("k_ece_warn", lang))
            add("k_interpret", interp)
            if not short:
                add("k_missing", [L.t("k_need_crop", lang)])

    # ---------------- water quality
    elif topic == "water_quality":
        measured, interp = [], []
        obs = []
        if place:
            st, d = _district(place)
            blk = place["name"] if place["type"] == "unit" else None
            obs = kn.observations("groundwater_quality", st, d, blk)
        if obs:
            has_data = True
            measured.append(L.t("k_wq_imported", lang, n=len(obs), place=_place_label(place, lang)))
            for o in obs[:10 if not detailed else 50]:
                measured.append(f"– {o['station_or_location'] or '-'} · {o['parameter']}: {o['original_value']} "
                                f"{o['original_unit'] or ''} · {o['sample_date'] or o['measurement_date'] or '-'} · "
                                f"{o['source_id']}")
                table.append({k: o[k] for k in ("station_or_location", "parameter", "original_value", "original_unit",
                                                "sample_date", "source_id", "quality_flag")})
        elif place:
            measured.append(L.t("k_not_in_dataset", lang, what=L.t("k_what_wq", lang), place=_place_label(place, lang)))
        else:
            measured.append(L.t("k_not_in_dataset_any", lang, what=L.t("k_what_wq", lang)))
        add("k_measured", measured)
        add("k_category", [L.t("k_quantity_not_quality", lang)])
        params = kd.get("parameters") or ["F", "NO3", "TDS", "As"]
        if not short:
            interp.append(L.t("k_limits_head", lang))
            for pid in params:
                info = kn.parameter("W_" + pid)
                rl = [r for r in kn.range_table("water_drinking", pid)]
                if not rl:
                    continue
                name = kn.text_of(info, "name", cl) if info else pid
                by = {}
                for r in rl:
                    by.setdefault(r["source"], []).append(f"{r['class']} {r['range']} {r['unit']}")
                interp.append(f"– **{name}**: " + " | ".join(f"{s}: " + "; ".join(v) for s, v in by.items()))
                srcs += list(by)
                if detailed and info:
                    interp.append(f"  _{kn.text_of(info, 'what', cl)}_")
        add("k_interpret", interp)
        add("k_general", [L.t("k_wq_test", lang)])

    # ---------------- irrigation
    elif topic == "irrigation":
        general = []
        keys = kd.get("keys") or []
        rows = [g for g in kn.guidance("irrigation") if (not keys or g["key"] in keys)]
        for g in rows[: (3 if short else len(rows))]:
            general.append(f"– **{kn.text_of(g, 'title', cl)}.** {kn.text_of(g, 'text', cl)}")
        srcs.append("JALMITRA_GENERAL")
        add("k_general", general)
        if not short:
            add("k_interpret", [L.t("k_quantity_not_quality", lang)])
        add("k_missing", [L.t("k_no_schedule", lang)])

    # ---------------- land
    else:
        measured, general = [], []
        if place:
            st, d = _district(place)
            recs = sum(len(kn.observations(t, st, d)) for t in ("land_use_records", "land_degradation_records",
                                                                "slope_records", "land_capability_records"))
            if recs:
                has_data = True
            measured.append(L.t("k_not_in_dataset", lang, what=L.t("k_what_land", lang), place=_place_label(place, lang))
                            if not recs else f"{recs} records")
        measured.append(L.t("k_land_cannot", lang))
        add("k_measured", measured)
        _regional(place, lang, cl, add, srcs, kind="land")
        keys = kd.get("keys") or []
        rows = [g for g in kn.guidance("degradation") + kn.guidance("conservation") if g["key"] in keys]
        if not rows and not short:
            rows = kn.guidance("conservation")[:4]
        for g in rows:
            general.append(f"– **{kn.text_of(g, 'title', cl)}.** {kn.text_of(g, 'text', cl)}")
        if rows:
            srcs.append("JALMITRA_GENERAL")
        add("k_general", general)

    if note and sec:
        sec.insert(0, ("", f"_{note}_"))
    srcs = list(dict.fromkeys(s for s in srcs if s))
    if srcs and (detailed or not short):
        sec.append((L.t("k_sources", lang), "  \n".join(f"– {kn.cite(s)}" for s in srcs)))
    return {"sections": sec, "table": table, "sources": srcs, "has_place_data": has_data}


def _zone(place):
    st, d = _district(place)
    return kn.zone_for(st, d)


def _regional(place, lang, cl, add, srcs, kind="soil"):
    zone = _zone(place)
    if not zone:
        return
    z = zone["zone"]
    lines = [f"**{z['name']}** ({zone['coverage']})"]
    if kind == "soil":
        lines += [z["soils_text"], z["fertility_text"]]
    else:
        lines += [z["soils_text"], z["problems_text"], z["rainfall_text"]]
    lines.append(f"_{z['note']}_")
    add("k_regional", lines)
    srcs.append(z["source_id"])


def render(kb):
    parts = []
    for label, text in kb["sections"]:
        parts.append((f"**{label}:**  \n" if label else "") + text)
    return "\n\n".join(parts)


def source_rows(kb):
    rows = []
    for sid in kb.get("sources") or []:
        s = kn.source(sid) or {}
        rows.append({"assessment_unit": "", "used_for": s.get("used_in_jalmitra", ""), "source_id": sid,
                     "title": s.get("title"), "page": "", "url": s.get("url"), "file": ""})
    return rows


def keyword_lists():
    """Words that must never be read as place names (crop names, soil and water terms)."""
    base = [WQ_WORDS, SOIL_CTX, LESS_WATER, IMPROVE, SOIL_TYPE, CROP_WORDS, IRRIGATION_WORDS, LAND_WORDS,
            ["erosion", "degradation", "suitable", "suitability", "उपयुक्त", "salinity", "saline"],
            ["hindi", "english", "marathi", "punjabi", "rajasthani", "marwari", "hinglish", "translate", "elaborate",
             "details"]]
    lists = [[w for w in words if not _clashes(w)] for words in base]
    try:
        t = kn.tables()
    except kn.KnowledgeNotReady:
        return lists
    for table in ("crops", "parameter_info", "guidance"):
        for row in t[table]:
            lists.append([a for a in kn._aliases(row) if not _clashes(a)])
    return lists


# Aliases that are also names of assessment units, districts or states in groundwater.db: they stay
# available as place names (checked by test KN_place_clash).
PLACE_NAME_CLASHES = {"hard", "little", "moth", "rai", "sudhar", "talai"}


def _clashes(phrase):
    return bool(set(phrase.lower().split()) & PLACE_NAME_CLASHES)


def crop_aliases(crop_id):
    c = kn.crop(crop_id)
    return [a.lower() for a in kn._aliases(c)] if c else []

"""
soil_interpret.py - Explain a CONFIRMED soil test report (Soil Health Card or lab report).

Rules (JalMitra 3.0 master instruction):
  * the card's own printed rating is shown first, then the rating from each reference source
  * a value is rated only when the unit matches the source (or by an exact metric conversion)
  * no overall soil-health score, no yield or profit prediction, no fertiliser dose
  * missing parameters are listed as missing, never treated as zero
  * soil EC (1:2 / 1:2.5 extract) is never compared with FAO ECe crop thresholds
"""

import knowledge as kn

L10N = {
    "en": {
        "summary": "Summary", "params": "Parameter-wise interpretation", "status": "Nutrient status",
        "limits": "Limitations", "crop": "Crop implications", "suggest": "General suggestions (not a formal recommendation)",
        "source": "Source and sample", "missing": "Missing information", "card": "Card rating",
        "no_range": "JalMitra has no verified rating range for this parameter yet.",
        "unit_mismatch": "{src}: not compared, the unit {given} differs from the source unit {unit}.",
        "gap": "{src}: {value} {unit} falls in a gap that the source does not classify.",
        "rated": "{src}: {cls}",
        "converted": " (converted from {orig})",
        "n_params": "{n} of 12 Soil Health Card parameters were confirmed.",
        "low_list": "Rated Low or Deficient by at least one source: {names}.",
        "none_low": "No confirmed parameter is rated Low or Deficient by the sources JalMitra holds.",
        "no_score": "JalMitra does not combine these into an overall soil-health score.",
        "limits_text": "Ratings come from general published charts (ICAR-CRIDA and TNAU), not from a crop- or state-specific "
                       "recommendation. Different labs use different methods and extraction ratios. Your card's own "
                       "rating, if printed, follows the method of your testing laboratory.",
        "ec_note": "Soil EC on a card is measured in a soil-water mix (often 1:2 or 1:2.5). FAO crop salt-tolerance "
                   "thresholds use ECe (saturation extract), so the two cannot be compared directly. Ask the lab for ECe "
                   "if salinity is a concern.",
        "crop_text": "JalMitra does not decide crop suitability from a soil card alone: climate, water, season and local "
                     "advice are also needed. See the Crop Advisor for what is known and what is missing.",
        "sample": "Sample date: {date} · Depth: {depth} · Location: {loc} · Laboratory: {lab}",
        "not_given": "not given",
        "missing_list": "Not in this report: {names}. These are shown as missing, not as zero.",
        "p_oxide": "Your report gives P as P2O5 (or K as K2O). JalMitra does not convert oxides; ratings need P or K in kg/ha.",
    },
    "hi": {
        "summary": "सारांश", "params": "पैरामीटर अनुसार व्याख्या", "status": "पोषक तत्व स्थिति",
        "limits": "सीमाएँ", "crop": "फसल पर असर", "suggest": "सामान्य सुझाव (औपचारिक सिफ़ारिश नहीं)",
        "source": "स्रोत और नमूना", "missing": "जो जानकारी नहीं है", "card": "कार्ड की रेटिंग",
        "no_range": "इस पैरामीटर की सत्यापित रेटिंग श्रेणी JalMitra में अभी नहीं है।",
        "unit_mismatch": "{src}: तुलना नहीं की, इकाई {given} स्रोत की इकाई {unit} से अलग है।",
        "gap": "{src}: {value} {unit} उस अंतराल में है जिसे स्रोत वर्गीकृत नहीं करता।",
        "rated": "{src}: {cls}",
        "converted": " ({orig} से बदला गया)",
        "n_params": "सॉयल हेल्थ कार्ड के 12 में से {n} पैरामीटर पुष्टि किए गए।",
        "low_list": "कम से कम एक स्रोत के अनुसार Low या Deficient: {names}।",
        "none_low": "JalMitra के स्रोतों के अनुसार कोई पुष्टि किया गया पैरामीटर Low या Deficient नहीं है।",
        "no_score": "JalMitra इन्हें जोड़कर कोई कुल मिट्टी-स्वास्थ्य अंक नहीं बनाता।",
        "limits_text": "रेटिंग सामान्य प्रकाशित चार्ट (ICAR-CRIDA और TNAU) से है, किसी फसल या राज्य की विशेष सिफ़ारिश से नहीं। "
                       "अलग प्रयोगशालाएँ अलग विधियाँ इस्तेमाल करती हैं। आपके कार्ड पर छपी रेटिंग आपकी प्रयोगशाला की विधि से है।",
        "ec_note": "कार्ड पर मिट्टी का EC मिट्टी-पानी के घोल (अक्सर 1:2 या 1:2.5) में मापा जाता है। FAO की फसल लवण-सहनशीलता "
                   "सीमाएँ ECe (संतृप्त अर्क) पर हैं, इसलिए दोनों की सीधी तुलना नहीं हो सकती। लवणता की चिंता हो तो प्रयोगशाला से ECe पूछें।",
        "crop_text": "JalMitra केवल मिट्टी कार्ड से फसल उपयुक्तता तय नहीं करता: जलवायु, पानी, मौसम और स्थानीय सलाह भी चाहिए। "
                     "क्या पता है और क्या नहीं, यह फसल सलाहकार में देखें।",
        "sample": "नमूना तिथि: {date} · गहराई: {depth} · स्थान: {loc} · प्रयोगशाला: {lab}",
        "not_given": "नहीं दिया",
        "missing_list": "इस रिपोर्ट में नहीं: {names}। इन्हें शून्य नहीं, अनुपलब्ध दिखाया गया है।",
        "p_oxide": "आपकी रिपोर्ट में P, P2O5 के रूप में (या K, K2O के रूप में) है। JalMitra ऑक्साइड नहीं बदलता; रेटिंग के लिए kg/ha में P या K चाहिए।",
    },
}
LOW_WORDS = ("Low", "Deficient")


def _t(key, lang, **kw):
    table = L10N["hi" if lang in ("hi", "mr", "raj") else "en"]
    return table[key].format(**kw)


def interpret(rows):
    """rows: confirmed rows {parameter, value, unit, card_rating}. Returns a structured interpretation."""
    out, given = [], set()
    for r in rows:
        if r.get("value") in (None, ""):
            continue
        pid = r["parameter"]
        given.add(pid)
        value = float(r["value"])
        ratings = kn.classify("soil", pid, value, r.get("unit") or "")
        out.append({"parameter": pid, "value": value, "unit": r.get("unit") or "",
                    "card_rating": (r.get("card_rating") or "").strip(), "ratings": ratings,
                    "info": kn.parameter(pid)})
    missing = [p for p in kn.SOIL_HEALTH_PARAMETERS if p not in given]
    low = [x["parameter"] for x in out if any(g["status"] == "rated" and g["class_label"] in LOW_WORDS
                                             for g in x["ratings"])]
    oxide = any("o5" in (x["unit"] or "").lower() or "k2o" in (x["unit"] or "").lower() for x in out)
    return {"items": out, "missing": missing, "low": low, "has_ec": "EC" in given, "oxide_units": oxide}


def rating_lines(item, lang):
    lines = []
    for g in item["ratings"]:
        src = g["source_id"]
        if g["status"] == "rated":
            line = _t("rated", lang, src=src, cls=g["class_label"])
            if g.get("converted_from"):
                line += _t("converted", lang, orig=g["converted_from"])
            line += f" ({g['table_ref']})"
        elif g["status"] == "gap":
            line = _t("gap", lang, src=src, value="%g" % g["value"], unit=g["unit"])
        else:
            line = _t("unit_mismatch", lang, src=src, given=g.get("given_unit") or "-", unit=g["unit"])
        lines.append(line)
    if not item["ratings"]:
        lines.append(_t("no_range", lang))
    return lines


def report_sections(result, meta, lang="en"):
    """[(heading, markdown)] for the Soil Health Report (on screen, Markdown and PDF)."""
    names = lambda ids: ", ".join(ids) if ids else "-"
    sec = []
    summary = [_t("n_params", lang, n=len(result["items"])),
               _t("low_list", lang, names=names(result["low"])) if result["low"] else _t("none_low", lang),
               _t("no_score", lang)]
    sec.append((_t("summary", lang), " ".join(summary)))
    lines = []
    for it in result["items"]:
        info = it["info"] or {}
        name = kn.text_of(info, "name", lang) if info else it["parameter"]
        head = f"**{name}: {it['value']:g} {it['unit']}**"
        if it["card_rating"]:
            head += f" · {_t('card', lang)}: {it['card_rating']}"
        body = "  \n".join("– " + x for x in rating_lines(it, lang))
        what = kn.text_of(info, "what", lang) if info else ""
        lines.append(head + "  \n" + body + (f"  \n_{what}_" if what else ""))
    sec.append((_t("params", lang), "\n\n".join(lines) if lines else "-"))
    status = []
    for it in result["items"]:
        if it["parameter"] in ("N", "P", "K", "S", "Zn", "Fe", "Cu", "Mn", "B"):
            rated = [f"{g['class_label']} ({g['source_id']})" for g in it["ratings"] if g["status"] == "rated"]
            status.append(f"{it['parameter']}: " + (", ".join(rated) if rated else "—"))
    sec.append((_t("status", lang), "  \n".join(status) if status else "-"))
    lim = [_t("limits_text", lang)]
    if result["has_ec"]:
        lim.append(_t("ec_note", lang))
    if result["oxide_units"]:
        lim.append(_t("p_oxide", lang))
    sec.append((_t("limits", lang), "  \n".join(lim)))
    sec.append((_t("crop", lang), _t("crop_text", lang)))
    tips = [g for g in kn.guidance("improve")]
    wanted = ["test_first", "balanced"]
    if "OC" in result["low"]:
        wanted += ["organic_matter", "cover"]
    if any(p in result["low"] for p in ("N",)):
        wanted.append("rotation")
    sug = [f"– **{kn.text_of(g, 'title', lang)}.** {kn.text_of(g, 'text', lang)}" for g in tips if g["key"] in wanted]
    sec.append((_t("suggest", lang), "  \n".join(sug) + "  \n_" + kn.cite("JALMITRA_GENERAL") + "_"))
    ng = _t("not_given", lang)
    sec.append((_t("source", lang), _t("sample", lang, date=meta.get("sample_date") or ng, depth=meta.get("depth") or ng,
                                       loc=meta.get("location") or ng, lab=meta.get("lab") or ng) + "  \n" +
                "  \n".join("– " + kn.cite(s) for s in ("CRIDA_SOIL", "TNAU_SOIL_RATING"))))
    sec.append((_t("missing", lang), _t("missing_list", lang, names=names(result["missing"])) if result["missing"] else "-"))
    return sec


def report_markdown(result, meta, lang="en", title="JalMitra Soil Health Report"):
    parts = [f"# {title}"]
    for head, body in report_sections(result, meta, lang):
        parts.append(f"## {head}\n\n{body}")
    return "\n\n".join(parts) + "\n"

"""
water_quality.py - Compare MEASURED water-test values with published limits.

  * drinking use: IS 10500:2012 and the CGWB 2024 table (both shown when they differ)
  * irrigation use: IS 11624:1986 EC limits by soil clay content and crop tolerance,
    SAR, RSC and %Na classes (CGWB 2024 Tables 2 and 3)

JalMitra never says water is "safe to drink": only the parameters that were tested
can be compared, and bacteria or untested chemicals stay unknown. The INGRES / GWRA
category (Safe, Critical ...) is about the QUANTITY of groundwater extracted, not
its quality.
"""

import knowledge as kn

ABOVE = ("Above", "Outside")


def interpret(values, use="drinking", clay_pct=None):
    """values: [{"parameter", "value", "unit"}]. Returns rows with one rating per source."""
    domain = "water_drinking" if use == "drinking" else "water_irrigation"
    rows = []
    for v in values:
        if v.get("value") in (None, ""):
            continue
        val = float(v["value"])
        pid = v["parameter"]
        if use == "irrigation" and pid == "EC":
            rows.append({"parameter": "EC", "value": val, "unit": v.get("unit") or "",
                         "ratings": _irrigation_ec(val, v.get("unit") or "", clay_pct)})
            continue
        rows.append({"parameter": pid, "value": val, "unit": v.get("unit") or "",
                     "ratings": kn.classify(domain, pid, val, v.get("unit") or "")})
    exceed = [r["parameter"] for r in rows if any(g.get("status") == "rated" and
                                                   g["class_label"].startswith(ABOVE) for g in r["ratings"])]
    return {"use": use, "rows": rows, "exceed": exceed}


def _irrigation_ec(value, unit, clay_pct):
    u = kn.norm_unit(unit)
    v = value * 1000 if u == "dS/m" else value
    if u not in ("uS/cm", "dS/m"):
        return [{"source_id": "IS11624_1986", "status": "unit_mismatch", "unit": "uS/cm", "given_unit": unit,
                 "table_ref": "CGWB_GWQ_2024 Table 2", "page": "5"}]
    if clay_pct is None:
        return [{"source_id": "IS11624_1986", "status": "needs_clay", "unit": "uS/cm", "value": v,
                 "table_ref": "CGWB_GWQ_2024 Table 2", "page": "5"}]
    limits = kn.irrigation_ec_limits(clay_pct)
    if not limits:
        return [{"source_id": "IS11624_1986", "status": "gap", "unit": "uS/cm", "value": v,
                 "table_ref": "CGWB_GWQ_2024 Table 2", "page": "5",
                 "note": "Soils with less than 10% clay are not covered by this table."}]
    out = []
    for lim in limits:
        ok = v <= lim["ec_upper_safe_limit_uS_cm"]
        out.append({"source_id": "IS11624_1986", "status": "rated", "table_ref": "CGWB_GWQ_2024 Table 2", "page": "5",
                    "class_label": ("Within" if ok else "Above") + f" the safe limit for {lim['crop_tolerance']} crops on "
                    f"{lim['soil_group'].lower()} ({lim['ec_upper_safe_limit_uS_cm']:g} uS/cm)",
                    "unit": "uS/cm", "value": v, "note": lim["note"] or ""})
    return out


CAVEAT = {
    "en": "Only the parameters you entered are compared. Bacteria and any parameter not tested remain unknown, so this "
          "is not a certificate that the water is safe to drink. Use a NABL-accredited or government laboratory.",
    "hi": "केवल आपके डाले गए पैरामीटर की तुलना हुई है। बैक्टीरिया और बिना जाँचे पैरामीटर अज्ञात हैं, इसलिए यह पानी के पीने योग्य "
          "होने का प्रमाण नहीं है। NABL-मान्यता प्राप्त या सरकारी प्रयोगशाला से जाँच कराएँ।",
}
CATEGORY_NOT_QUALITY = {
    "en": "The groundwater category (Safe, Semi-critical, Critical, Over-exploited) describes how much of the yearly "
          "recharge is extracted. It does not describe chemical quality or whether the water is fit to drink.",
    "hi": "भूजल श्रेणी (सुरक्षित, अर्ध-गंभीर, गंभीर, अति-दोहित) बताती है कि सालाना पुनर्भरण का कितना हिस्सा निकाला जा रहा है। "
          "यह पानी की रासायनिक गुणवत्ता या पीने योग्य होने के बारे में नहीं बताती।",
}


def caveat(lang):
    return CAVEAT["hi" if lang in ("hi", "mr", "raj") else "en"]


def category_note(lang):
    return CATEGORY_NOT_QUALITY["hi" if lang in ("hi", "mr", "raj") else "en"]

"""
ui_pages_v3.py - Website pages added or rebuilt in JalMitra 3.0 Phases 2-7:

  Soil Health, Soil Type and Profile, Land Intelligence, Land Degradation, Crop Advisor,
  Irrigation Advisor, Groundwater Quality, My Soil Report, My Reports, Learning Centre,
  Data Sources, Geographic Explorer (boundary layer).

Every value shown comes from groundwater.db, knowledge.db (reference tables with source,
table and page), observations.db (imported data; empty until naveen imports datasets) or the
user's own confirmed soil report. Anything else is shown as "Not available in the current dataset".
"""

import json
from pathlib import Path

import pandas as pd
import streamlit as st

import database as db
import engine
import knowledge as kn
import knowledge_answer as ka
import language as L
import report_builders as rbd
import reports_pdf as rp
import soil_card as sc
import soil_interpret as si
import ui_components as uc
import ui_pages as up
import water_quality as wq
from ui_text import u

NA_KEY = "not_in_dataset"
GEO_DIR = Path(__file__).resolve().parent / "data" / "geo"


def _lg():
    return up.ui()


def _cl():
    return ka.content_lang(_lg())


def _general_caption():
    st.caption("ℹ️ " + u("general_label", _lg()))


def _regional(place):
    st_, d = ka._district(place) if place else (None, None)
    zone = kn.zone_for(st_, d)
    if not zone:
        return None
    z = zone["zone"]
    with st.container(border=True):
        st.markdown(f"**🗺️ {z['name']}** · {zone['coverage']}")
        st.write(f"{z['soils_text']}. {z['fertility_text']}. Rainfall {z['rainfall_text']}. {z['problems_text']}.")
        st.caption(u("regional_label", _lg()) + " " + u("cited_from", _lg()) + ": " + kn.cite(z["source_id"]))
    return zone


def _home_header():
    p = up.home()
    if p is None:
        st.info(u("home_place_none", _lg()), icon="📍")
    else:
        st.markdown(f"**📍 {uc.place_title(p, up.text_lang())}**")
    return p


def soil_report():
    return st.session_state.get("soil_report")


def _ranges_df(domain, pid):
    rows = kn.range_table(domain, pid)
    return pd.DataFrame(rows)[["class", "range", "unit", "source", "table", "page", "note"]] if rows else None


def _download_report(builder, key, place=None):
    """builder(lang) -> (title, sections, tables). Markdown in the reading language, PDF always in English."""
    lg, tl = _lg(), up.text_lang()
    title, sections, tables = builder(tl)
    md = rp.markdown(title, sections, rbd.place_text(place, tl) if place is not None else "")
    c1, c2 = st.columns(2)
    c1.download_button("⬇️ " + u("download_md", lg), md.encode("utf-8"), f"{key}.md", "text/markdown", key=f"md_{key}",
                       width="stretch")
    if c2.toggle("PDF", key=f"pdfmake_{key}", help=u("pdf_english_only", lg)):
        t_en, s_en, tab_en = builder("en") if tl != "en" else (title, sections, tables)
        pdf = rp.build_pdf(t_en, s_en, rbd.place_text(place, "en") if place is not None else "", tab_en)
        c2.download_button("⬇️ " + u("download_pdf", lg), pdf, f"{key}.pdf", "application/pdf", key=f"pdf_{key}",
                           width="stretch")
    if tl != "en":
        st.caption(u("pdf_english_only", lg))
    return title, sections, tables


# ------------------------------------------------------------------ Soil Health

def page_soil():
    lg, cl = _lg(), _cl()
    st.title("🌱 " + u("nav_soil", lg))
    st.caption(u("soil_intro", lg))
    place = _home_header()
    rep = soil_report()
    st.subheader(u("your_card", lg))
    if rep:
        res = si.interpret(rep["rows"])
        cols = st.columns(4)
        given = {it["parameter"]: it for it in res["items"]}
        for i, pid in enumerate(kn.SOIL_HEALTH_PARAMETERS):
            it = given.get(pid)
            with cols[i % 4].container(border=True):
                st.markdown(f"**{pid}**")
                if it is None:
                    st.caption(u(NA_KEY, lg))
                    continue
                st.markdown(f"### {it['value']:g} {it['unit']}")
                if it["card_rating"]:
                    st.caption(f"{u('card_rating', lg)}: {it['card_rating']}")
                for line in si.rating_lines(it, lg):
                    st.caption(line)
        st.caption(si._t("no_score", lg) + " " + u("cited_from", lg) + ": " + rep.get("meta", {}).get("sample_date", "-"))
    else:
        st.info(u("upload_first", lg), icon="📄")
        st.button(u("go_soil_report", lg), on_click=up.goto, args=("soilreport",), type="primary")
    if place:
        _regional(place)
    st.subheader(u("twelve_params", lg))
    st.caption(u("soil_vs_water_ec", lg))
    for pid in kn.SOIL_HEALTH_PARAMETERS:
        info = kn.parameter(pid)
        with st.expander(kn.text_of(info, "name", cl)):
            st.write(kn.text_of(info, "what", cl))
            df = _ranges_df("soil", pid)
            if df is not None:
                st.markdown(f"**{u('published_classes', lg)}**")
                st.dataframe(df, hide_index=True, width="stretch")
                st.caption(" · ".join(kn.cite(s) for s in df["source"].unique()))
            else:
                st.caption(L.t("k_ranges_head", ka.content_lang(lg)) + " " + u(NA_KEY, lg))
            if pid == "EC":
                st.caption(L.t("k_ece_warn", lg if lg in L.LANGUAGES else "en"))
    _general_caption()


# ------------------------------------------------------------------ Soil Type and Profile

PROFILE_PROPS = ["Sand / silt / clay (%)", "Soil depth", "Available water capacity (AWC)", "Field capacity",
                 "Wilting point", "Bulk density", "Cation exchange capacity (CEC)", "Calcium carbonate (CaCO3)",
                 "Drainage class", "Soil classification"]


def page_soil_profile():
    lg, cl = _lg(), _cl()
    st.title("🧱 " + u("nav_soilprofile", lg))
    st.caption(u("profile_intro", lg))
    place = _home_header()
    st_, d = ka._district(place) if place else (None, None)
    imported = kn.observations("soil_properties", st_, d) if place else []
    st.subheader(u("profile_props", lg))
    if imported:
        st.dataframe(pd.DataFrame(imported), hide_index=True, width="stretch")
    else:
        st.dataframe(pd.DataFrame([{"property": p, "value": u(NA_KEY, lg), u("data_origin", lg): "—"}
                                   for p in PROFILE_PROPS]), hide_index=True, width="stretch")
    with st.expander(u("data_origin", lg)):
        for o in kn.DATA_ORIGINS:
            st.markdown("– " + u("origin_" + o, lg))
    if place:
        _regional(place)
    st.subheader(u("soil_types", lg))
    for g in kn.guidance("soil_type"):
        with st.expander(kn.text_of(g, "title", cl)):
            st.write(kn.text_of(g, "text", cl))
    _general_caption()


# ------------------------------------------------------------------ Land Intelligence

def page_land():
    lg = _lg()
    st.title("🏞️ " + u("nav_land", lg))
    st.caption(u("land_intro", lg))
    place = _home_header()
    secs = rbd.land_condition_sections(place, up.text_lang())
    st.subheader(u("land_report", lg))
    for head, text in secs:
        with st.container(border=True):
            st.markdown(f"**{head}**")
            st.markdown(text)
    st.subheader(u("is_land_good", lg))
    st.dataframe(pd.DataFrame(rbd.land_use_table()), hide_index=True, width="stretch")
    st.caption(u("land_eval_note", lg))
    _download_report(lambda lang: rbd.land_report(place, lang), "jalmitra_land_report", place)


def page_land_degradation():
    lg, cl = _lg(), _cl()
    st.title("🏜️ " + u("nav_landdeg", lg))
    st.caption(u("landdeg_intro", lg))
    place = _home_header()
    st.subheader(u("records_for_area", lg))
    if place:
        st_, d = ka._district(place)
        recs = kn.observations("land_degradation_records", st_, d)
        if recs:
            st.dataframe(pd.DataFrame(recs), hide_index=True, width="stretch")
        else:
            st.write(L.t("k_not_in_dataset", up.text_lang(), what=L.t("k_what_land", up.text_lang()),
                         place=uc.place_title(place, up.text_lang())))
        _regional(place)
    else:
        st.write(u(NA_KEY, lg))
    c1, c2 = st.columns(2)
    with c1:
        st.subheader(u("degradation_types", lg))
        for g in kn.guidance("degradation"):
            with st.expander(kn.text_of(g, "title", cl)):
                st.write(kn.text_of(g, "text", cl))
    with c2:
        st.subheader(u("conservation_methods", lg))
        for g in kn.guidance("conservation"):
            with st.expander(kn.text_of(g, "title", cl)):
                st.write(kn.text_of(g, "text", cl))
    _general_caption()


# ------------------------------------------------------------------ Crop Advisor

RAJ_FIRST = ["pearl_millet", "mustard", "wheat", "chickpea", "guar", "sorghum", "maize", "groundnut", "moong", "moth",
             "cotton", "barley", "taramira", "sesame", "alfalfa", "cowpea", "date_palm", "citrus"]


def page_crop():
    lg, tl = _lg(), up.text_lang()
    st.title("🌾 " + u("nav_crop", lg))
    st.caption(u("crop_intro", lg))
    place = _home_header()
    ids = [c for c in RAJ_FIRST if kn.crop(c)] + [c["crop_id"] for c in kn.crops() if c["crop_id"] not in RAJ_FIRST]
    chosen = st.multiselect(u("choose_crops", lg), ids, default=["mustard", "wheat"], key="crop_pick",
                            format_func=lambda c: ka._crop_name(kn.crop(c), lg))
    ece = st.number_input(u("ece_input", lg), min_value=0.0, max_value=100.0, value=None, step=0.1,
                          help=u("ece_help", lg), key="crop_ece")
    if place:
        zone = kn.zone_for(*ka._district(place))
        if zone:
            with st.container(border=True):
                st.markdown(f"**{u('zone_crops', lg)}** · {zone['zone']['name']} ({zone['coverage']})")
                for season in ("Kharif", "Rabi"):
                    names = [ka._crop_name(kn.crop(z["crop_id"]), lg) for z in zone["crops"] if z["season"] == season]
                    st.write(f"{L.t('k_season_' + season.lower(), tl)}: {', '.join(names)}")
                st.caption(u("regional_label", lg) + " " + kn.cite(zone["zone"]["source_id"]))
    if chosen:
        kd = {"domain": "crop", "topic": "compare_crops" if len(chosen) > 1 else "crop", "parameters": [], "crops": chosen}
        kb = ka.build(kd, [place] if place else [], tl, up.detail() if up.detail() != "short" else "standard")
        st.subheader(u("comparison_table", lg))
        st.dataframe(pd.DataFrame(kb["table"]), hide_index=True, width="stretch")
        if ece is not None:
            st.markdown(f"**{u('salinity_factor', lg)}**")
            for cid in chosen:
                salt = kn.crop_facts(cid)["salt"]
                name = ka._crop_name(kn.crop(cid), lg)
                if not salt or salt["ece_threshold_dS_m"] is None:
                    st.write(f"– {name}: {u('no_threshold', lg)}")
                elif ece <= salt["ece_threshold_dS_m"]:
                    st.write(f"– {name}: " + u("below_threshold", lg).format(ece=ece, t=salt["ece_threshold_dS_m"]))
                else:
                    st.write(f"– {name}: " + u("above_threshold", lg).format(ece=ece, t=salt["ece_threshold_dS_m"]))
            st.caption(kn.cite("FAO_SALT_TOLERANCE", "Table A1.1"))
        with st.container(border=True):
            st.markdown(ka.render(kb))
        _download_report(lambda lang: rbd.crop_report(place, chosen, lang), "jalmitra_crop_report", place)
    with st.expander(u("water_need_table", lg)):
        st.dataframe(pd.DataFrame(kn.water_needs_sorted())[["fao_water_label", "water_need_min_mm", "water_need_max_mm",
                                                              "drought_sensitivity", "note"]],
                     hide_index=True, width="stretch")
        st.caption(kn.cite("FAO_CROP_WATER", "Table 14"))


# ------------------------------------------------------------------ Irrigation Advisor

def _irrigation_checker(key):
    lg = _lg()
    st.markdown(f"**{u('irr_check', lg)}**")
    st.caption(u("wq_checker_help", lg))
    default = pd.DataFrame([{"parameter": "EC", "value": None, "unit": "uS/cm"},
                            {"parameter": "SAR", "value": None, "unit": "ratio"},
                            {"parameter": "RSC", "value": None, "unit": "meq/L"},
                            {"parameter": "NA_PCT", "value": None, "unit": "%"}])
    df = st.data_editor(default, key=key, hide_index=True, width="stretch", disabled=["parameter"],
                        column_config={"value": st.column_config.NumberColumn(min_value=0.0)})
    clay = st.number_input(u("clay_pct", lg), min_value=0.0, max_value=100.0, value=None, key=key + "_clay")
    values = [r for r in df.to_dict("records") if r["value"] is not None and not pd.isna(r["value"])]
    if values:
        res = wq.interpret(values, "irrigation", clay)
        _show_wq(res)


def _show_wq(res):
    lg = _lg()
    rows = []
    for r in res["rows"]:
        for g in r["ratings"] or [{"source_id": "-", "status": "no_range"}]:
            rows.append({"parameter": r["parameter"], "value": r["value"], "unit": r["unit"], "source": g["source_id"],
                         "result": g.get("class_label") or {"unit_mismatch": "not compared (unit differs: " + g.get("unit", "") + ")",
                                                            "gap": "not classified by the source",
                                                            "needs_clay": "needs the clay % of the soil",
                                                            "no_range": u(NA_KEY, lg)}.get(g["status"], g["status"]),
                         "table": g.get("table_ref", ""), "page": g.get("page", "")})
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
    st.warning(wq.caveat(lg), icon="⚠️")


def page_irrigation():
    lg, cl, tl = _lg(), _cl(), up.text_lang()
    st.title("🚿 " + u("nav_irrigation", lg))
    st.caption(u("irr_intro", lg))
    place = _home_header()
    if place:
        r = engine.answer_places("status", [place], tl, up.style(), "short")
        with st.container(border=True):
            st.markdown(r["text"])
            st.caption(wq.category_note(lg))
    st.info(L.t("k_no_schedule", tl), icon="ℹ️")
    st.subheader(u("irr_methods", lg))
    cols = st.columns(2)
    for i, g in enumerate(kn.guidance("irrigation")):
        with cols[i % 2].expander(kn.text_of(g, "title", cl)):
            st.write(kn.text_of(g, "text", cl))
    _general_caption()
    with st.container(border=True):
        _irrigation_checker("irr_check")
    with st.expander(u("standards", lg) + " · IS 11624 (CGWB 2024 Table 2)"):
        st.dataframe(pd.DataFrame(kn.irrigation_ec_limits()), hide_index=True, width="stretch")
        for pid in ("SAR", "RSC", "NA_PCT"):
            st.dataframe(_ranges_df("water_irrigation", pid), hide_index=True, width="stretch")
    with st.expander(u("water_need_table", lg)):
        st.dataframe(pd.DataFrame(kn.water_needs_sorted())[["fao_water_label", "water_need_min_mm", "water_need_max_mm",
                                                              "drought_sensitivity"]], hide_index=True, width="stretch")
        st.caption(kn.cite("FAO_CROP_WATER", "Table 14"))
    _download_report(lambda lang: rbd.irrigation_report(place, lang), "jalmitra_irrigation_report", place)


# ------------------------------------------------------------------ Groundwater Quality

WQ_DEFAULT_UNITS = {"pH": "pH", "TDS": "mg/L", "EC": "uS/cm", "F": "mg/L", "NO3": "mg/L", "As": "mg/L", "Cl": "mg/L",
                    "Fe": "mg/L", "TH": "mg/L", "SO4": "mg/L", "U": "ug/L"}


def page_gw_quality():
    lg, tl, cl = _lg(), up.text_lang(), _cl()
    st.title("🧪 " + u("nav_gwq", lg))
    st.caption(u("gwq_intro", lg))
    place = _home_header()
    obs = []
    rec = None
    if place:
        st_, d = ka._district(place)
        obs = kn.observations("groundwater_quality", st_, d, place["name"] if place["type"] == "unit" else None)
        levels = kn.observations("groundwater_levels", st_, d, place["name"] if place["type"] == "unit" else None)
        r = engine.answer_places("status", [place], tl, "farmer", "short")
        rec = r["text"]
    else:
        levels = []
    cols = st.columns(5)
    cards = [("gwq_category", rec or u(NA_KEY, lg)),
             ("gwq_level", f"{len(levels)} {u('rows', lg)}" if levels else u(NA_KEY, lg)),
             ("gwq_chem", f"{len(obs)} {u('rows', lg)}" if obs else u(NA_KEY, lg)),
             ("gwq_drink", u("needs_test", lg)), ("gwq_irr", u("needs_test", lg))]
    for col, (k, v) in zip(cols, cards):
        with col.container(border=True, height="stretch"):
            st.markdown(f"**{u(k, lg)}**")
            st.caption(v)
    st.warning(L.t("k_quantity_not_quality", tl), icon="⚠️")
    if obs:
        st.subheader(u("imported_records", lg))
        st.dataframe(pd.DataFrame(obs), hide_index=True, width="stretch")
    with st.container(border=True):
        st.markdown(f"**{u('wq_checker', lg)}**")
        st.caption(u("wq_checker_help", lg))
        default = pd.DataFrame([{"parameter": p, "value": None, "unit": WQ_DEFAULT_UNITS[p]} for p in kn.DRINKING_PARAMETERS])
        df = st.data_editor(default, key="wq_edit", hide_index=True, width="stretch", disabled=["parameter"],
                            column_config={"value": st.column_config.NumberColumn(min_value=0.0, format="%.4g"),
                                           "unit": st.column_config.SelectboxColumn(
                                               options=["pH", "mg/L", "ug/L", "uS/cm", "dS/m"])})
        values = [r for r in df.to_dict("records") if r["value"] is not None and not pd.isna(r["value"])]
        if values:
            _show_wq(wq.interpret(values, "drinking"))
    with st.container(border=True):
        _irrigation_checker("gwq_irr_check")
    st.subheader(u("standards", lg))
    for pid in kn.DRINKING_PARAMETERS:
        info = kn.parameter("W_" + pid)
        df = _ranges_df("water_drinking", pid)
        if df is None:
            continue
        with st.expander(kn.text_of(info, "name", cl) if info else pid):
            if info:
                st.write(kn.text_of(info, "what", cl))
            st.dataframe(df, hide_index=True, width="stretch")
            st.caption(" · ".join(kn.cite(s) for s in df["source"].unique()))


# ------------------------------------------------------------------ My Soil Report

def _set_stage(stage):
    st.session_state.sr_stage = stage


def page_soil_report():
    lg = _lg()
    st.title("📄 " + u("nav_soilreport", lg))
    st.caption(u("sr_intro", lg))
    st.caption("🔒 " + u("privacy_note", lg))
    stage = st.session_state.setdefault("sr_stage", "upload")

    if stage == "upload":
        st.subheader(u("sr_step1", lg))
        f = st.file_uploader(u("sr_upload", lg), type=["pdf", "csv", "xlsx"], key="sr_file")
        if f is not None:
            try:
                out = sc.extract(f.name, f.getvalue())
            except sc.UploadError as problem:
                st.error(str(problem))
            except Exception as problem:     # a broken file must not crash the page
                st.error(f"The file could not be read: {type(problem).__name__}")
            else:
                if out["message"] == "scanned":
                    st.warning(u("sr_scanned", lg))
                elif out["message"] == "nothing_found":
                    st.warning(u("sr_nothing", lg))
                else:
                    st.session_state.sr_rows = out["rows"]
                    st.session_state.sr_meta = {"file": f.name, "sha256": out["sha256"][:16], "kind": out["kind"]}
                    _set_stage("review")
                    st.rerun()

        def typed():
            st.session_state.sr_rows = sc.blank_rows()
            st.session_state.sr_meta = {"file": "typed by user"}
            _set_stage("review")
        st.button("⌨️ " + u("sr_type", lg), on_click=typed)

    elif stage == "review":
        st.subheader(u("sr_step2", lg))
        st.caption(u("sr_review_help", lg))
        df = pd.DataFrame(st.session_state.get("sr_rows") or sc.blank_rows())
        cols = ["parameter", "value", "unit", "card_rating", "raw_text", "extracted_by"]
        edited = st.data_editor(df[cols], key="sr_editor", num_rows="dynamic", hide_index=True, width="stretch",
                                disabled=["raw_text", "extracted_by"],
                                column_config={"parameter": st.column_config.SelectboxColumn(
                                    options=kn.SOIL_HEALTH_PARAMETERS, required=True),
                                    "value": st.column_config.NumberColumn(min_value=0.0, format="%.4g")})
        st.subheader(u("sr_step3", lg))
        c1, c2 = st.columns(2)
        date = c1.text_input(u("sample_date", lg), key="sr_date", placeholder="YYYY-MM-DD")
        depth = c2.text_input(u("sample_depth", lg), key="sr_depth", placeholder="0-15 cm")
        loc = c1.text_input(u("sample_location", lg), key="sr_loc")
        lab = c2.text_input(u("lab_name", lg), key="sr_lab")
        ok = st.checkbox(u("units_checked", lg), key="sr_ok")
        rows = [r for r in edited.to_dict("records") if r.get("parameter") and r.get("value") is not None
                and not pd.isna(r.get("value"))]

        def approve():
            meta = dict(st.session_state.get("sr_meta") or {}, sample_date=date, depth=depth, location=loc, lab=lab)
            clean = [{"parameter": r["parameter"], "value": float(r["value"]), "unit": (r.get("unit") or "").strip(),
                      "card_rating": (r.get("card_rating") or "").strip() if isinstance(r.get("card_rating"), str) else "",
                      "confirmed": True} for r in rows]
            st.session_state.soil_report = sc.new_report(clean, meta)
            st.session_state.engine_state.soil_report = st.session_state.soil_report
            _set_stage("done")
        c1, c2 = st.columns(2)
        c1.button("✅ " + u("approve", lg), on_click=approve, disabled=not (ok and rows), type="primary", width="stretch")
        c2.button("↩️ " + u("delete_report", lg), on_click=_delete_current, width="stretch")

    else:
        rep = soil_report()
        if not rep:
            _set_stage("upload")
            st.rerun()
        st.subheader(u("sr_step4", lg))
        res = si.interpret(rep["rows"])
        tl = up.text_lang()
        for head, text in si.report_sections(res, rep["meta"], tl):
            with st.container(border=True):
                st.markdown(f"**{head}**")
                st.markdown(text)
        _download_report(lambda lang: rbd.soil_report(rep, lang), "jalmitra_soil_report")
        c1, c2, c3 = st.columns(3)
        c1.button("✏️ " + u("edit_again", lg), on_click=_edit_again, width="stretch")

        def save():
            sc.save_local(rep)
            st.toast(u("saved", lg))
        c2.button("💾 " + u("save_local", lg), on_click=save, width="stretch")
        c3.button("🗑️ " + u("delete_report", lg), on_click=_delete_current, width="stretch")
    saved = sc.list_local()
    if saved:
        with st.expander(f"{u('saved_reports', lg)} ({len(saved)})"):
            for r in saved:
                c1, c2, c3 = st.columns([3, 1, 1])
                c1.write(f"{r['created']} · {r['meta'].get('sample_date') or '-'} · {len(r['rows'])} values")
                c2.button(u("load", lg), key=f"load_{r['report_id']}", on_click=_load, args=(r,))
                c3.button("🗑️", key=f"del_{r['report_id']}", on_click=sc.delete_local, args=(r["report_id"],))


def _edit_again():
    rep = soil_report()
    if rep:
        st.session_state.sr_rows = [dict(r, raw_text="", extracted_by="confirmed earlier") for r in rep["rows"]]
    _set_stage("review")


def _delete_current():
    for k in ("soil_report", "sr_rows", "sr_meta"):
        st.session_state.pop(k, None)
    st.session_state.engine_state.soil_report = None
    _set_stage("upload")


def _load(rep):
    st.session_state.soil_report = rep
    st.session_state.engine_state.soil_report = rep
    _set_stage("done")


# ------------------------------------------------------------------ My Reports

def page_reports():
    lg, tl = _lg(), up.text_lang()
    st.title("🗂️ " + u("nav_reports", lg))
    place = _home_header()
    st.subheader(u("report_types", lg))
    kinds = ["rep_groundwater", "rep_soil", "rep_land", "rep_crop", "rep_irrigation", "rep_complete"]
    kind = st.segmented_control(u("report_types", lg), kinds, default="rep_groundwater", key="rep_kind",
                                format_func=lambda k: u(k, lg), label_visibility="collapsed")
    crops = st.session_state.get("crop_pick") or ["mustard", "wheat"]
    if kind:
        builder = {"rep_groundwater": lambda lang: rbd.groundwater_report(place, lang),
                   "rep_soil": lambda lang: rbd.soil_report(soil_report(), lang),
                   "rep_land": lambda lang: rbd.land_report(place, lang),
                   "rep_crop": lambda lang: rbd.crop_report(place, crops, lang),
                   "rep_irrigation": lambda lang: rbd.irrigation_report(place, lang),
                   "rep_complete": lambda lang: rbd.complete_report(place, soil_report(), crops, lang)}[kind]
        title, secs, tabs = _download_report(builder, "jalmitra_" + kind.replace("rep_", "") + "_report", place)
        for i, (c, rows) in enumerate(tabs):
            if rows:
                st.download_button(f"⬇️ CSV · {c}", uc.csv_bytes(rows), f"{kind}_{i}.csv", "text/csv",
                                   key=f"csv_{kind}_{i}")
        with st.expander(title, expanded=True):
            for head, text in secs:
                if head:
                    st.markdown(f"**{head}**")
                if text:
                    st.markdown(text)
    st.subheader(u("chat_report", lg))
    chat = st.session_state.chat
    if not chat:
        st.info(u("no_reports", lg))
        return
    st.download_button("⬇️ " + u("download_report", lg), uc.report_markdown(chat), "jalmitra_conversation.md",
                       "text/markdown")
    tables = [dict(row, question=m.get("question", "")) for m in chat if m["role"] == "assistant"
              for row in (m.get("table") or [])]
    if tables:
        st.download_button(u("download_csv", lg), uc.csv_bytes(tables), "jalmitra_all_tables.csv", "text/csv")


# ------------------------------------------------------------------ Learning Centre (extended)

def page_learn():
    lg, cl = _lg(), _cl()
    up.page_learn()
    st.divider()
    sections = [("learn_soil", [kn.parameter(p) for p in kn.SOIL_HEALTH_PARAMETERS + ["TEXTURE", "AWC"]], "soil"),
                ("learn_water", [kn.parameter("W_" + p) for p in ["pH", "TDS", "EC", "F", "NO3", "As", "Cl", "Fe", "TH",
                                                                    "U", "SAR", "RSC"]], "water")]
    for key, rows, dom in sections:
        st.subheader(u(key, lg))
        for info in rows:
            if not info:
                continue
            with st.expander(kn.text_of(info, "name", cl)):
                st.write(kn.text_of(info, "what", cl))
                pid = info["parameter"].replace("W_", "")
                df = _ranges_df("soil" if dom == "soil" else "water_drinking", pid)
                if df is None and dom == "water":
                    df = _ranges_df("water_irrigation", pid)
                if df is not None:
                    st.dataframe(df, hide_index=True, width="stretch")
                    st.caption(u("cited_from", lg) + ": " + " · ".join(kn.cite(s) for s in df["source"].unique()))
                st.caption(u("general_label", lg))
    for key, kinds in (("soil_types", ["soil_type"]), ("learn_land", ["degradation", "conservation"]),
                       ("learn_irrigation", ["irrigation"])):
        st.subheader(u(key, lg))
        for kind in kinds:
            for g in kn.guidance(kind):
                with st.expander(kn.text_of(g, "title", cl)):
                    st.write(kn.text_of(g, "text", cl))
                    st.caption(u("cited_from", lg) + ": " + kn.cite(g["source_id"]))
    st.subheader(u("learn_crops", lg))
    rows = []
    for c in kn.crops():
        f = kn.crop_facts(c["crop_id"])
        rows.append({"crop": c["name_en"], "FAO salt rating": f["salt"]["rating"] if f["salt"] else "not in table",
                     "ECe threshold dS/m": (f["salt"] or {}).get("ece_threshold_dS_m"),
                     "water need mm": (f"{f['water']['water_need_min_mm']:g}–{f['water']['water_need_max_mm']:g}"
                                       if f["water"] else "not in table")})
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
    st.caption(kn.cite("FAO_SALT_TOLERANCE") + " · " + kn.cite("FAO_CROP_WATER") + ". " + L.t("k_ece_warn", "en"))


# ------------------------------------------------------------------ Data Sources (extended)

def page_sources():
    lg = _lg()
    up.page_sources()
    st.subheader(u("catalog", lg))
    cat = pd.DataFrame(kn.sources())
    st.dataframe(cat[["source_id", "title", "publisher", "access_class", "document_year", "data_years", "resolution",
                      "licence", "download_conditions", "used_in_jalmitra", "url", "notes"]],
                 hide_index=True, width="stretch", column_config={"url": st.column_config.LinkColumn("url")})
    st.subheader(u("access_requests", lg))
    need = cat[cat["access_class"].isin(["permission_required", "paid", "manual_upload_required",
                                         "not_currently_accessible"])]
    st.dataframe(need[["source_id", "title", "access_class", "download_conditions", "notes"]], hide_index=True,
                 width="stretch")
    st.subheader(u("observations", lg))
    counts = kn.observation_counts()
    st.dataframe(pd.DataFrame([{"table": k, u("rows", lg): v} for k, v in counts.items()]), hide_index=True)
    logs = kn.import_logs()
    if logs:
        st.dataframe(pd.DataFrame(logs), hide_index=True, width="stretch")


# ------------------------------------------------------------------ Geographic Explorer (boundary layer)

def geo_layers():
    if not GEO_DIR.exists():
        return []
    return sorted(GEO_DIR.glob("*.geojson"))


def page_geo():
    lg = _lg()
    up.page_geo()
    st.subheader("🗺️ " + u("map_layer", lg))
    layers = geo_layers()
    if not layers:
        st.info(u("no_geometry", lg), icon="ℹ️")
        return
    name = st.selectbox(u("map_layer", lg), [p.name for p in layers], key="geo_layer")
    path = GEO_DIR / name
    if path.stat().st_size > 30 * 1024 * 1024:
        st.warning("This boundary file is larger than 30 MB; please simplify it before use.")
        return
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        st.error("This GeoJSON file could not be read.")
        return
    import pydeck as pdk
    layer = pdk.Layer("GeoJsonLayer", data, stroked=True, filled=True, get_fill_color=[11, 110, 79, 40],
                      get_line_color=[11, 110, 79], line_width_min_pixels=1, pickable=True)
    st.pydeck_chart(pdk.Deck(layers=[layer], map_style=None,
                             initial_view_state=pdk.ViewState(latitude=22.5, longitude=79, zoom=3.6)))
    meta = path.with_suffix(".source.txt")
    st.caption(meta.read_text(encoding="utf-8") if meta.exists() else
               "Source, year and resolution of this boundary file are not recorded: add a .source.txt file next to it.")

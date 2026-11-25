"""
ui_pages.py - The pages of the JalMitra 3.0 website (one function per page).

app.py builds the navigation and the sidebar settings; every page reads the
settings from st.session_state. Pages for topics without data (soil, land,
crop, irrigation, soil report) say "Data unavailable" and offer only
controls that work (no decorative buttons).
"""

import pandas as pd
import streamlit as st

import database as db
import engine
import language as L
import response_builder as rb
import ui_components as uc
import voice
from ui_text import DATA_EXAMPLES, EXAMPLE_QUESTIONS, GLOSSARY, u

PAGES = {}            # filled by app.py: key -> st.Page


# ------------------------------------------------------------------ settings helpers

def ui():
    return st.session_state.get("ui_lang", "en")


def answer_lang():
    return st.session_state.get("answer_lang", L.AUTO)


def text_lang():
    """Language for category names in cards: the answer language, or the interface language on Auto."""
    a = answer_lang()
    return a if a in L.LANGUAGES else ui()


def style():
    return st.session_state.get("style", "farmer")


def detail():
    return st.session_state.get("detail", "standard")


def home():
    return st.session_state.engine_state.home


def goto(page_key, question=None):
    """Callback-safe navigation: the switch happens at the top of the next run (see app.py)."""
    if question:
        st.session_state.pending_q = question
    st.session_state.goto = page_key


def set_location_from_place(p):
    """Copy a place into the sidebar selectors (only inside callbacks)."""
    st.session_state.loc_state = p["state"] if p else ""
    st.session_state.loc_district = (p.get("district") or "") if p and p["type"] != "state" else ""
    st.session_state.loc_unit = p["name"] if p and p["type"] == "unit" else ""


def location_search(key):
    """Searchable list of every place in the database; choosing one sets 'Your location'."""
    options = uc.all_place_options()
    labels = dict(options)

    def changed():
        p = uc.place_from_key(st.session_state.get(key))
        if p:
            set_location_from_place(p)

    st.selectbox(u("location", ui()), [k for k, _ in options], index=None, key=key,
                 format_func=lambda k: labels.get(k, k), placeholder=u("type_to_search", ui()),
                 on_change=changed, help=u("location_help", ui()))


# ------------------------------------------------------------------ asking

def ask(question):
    question = (question or "").strip()
    if not question:
        return
    st.session_state.chat.append({"role": "user", "text": question})
    hist = [q for q in st.session_state.search_history if q != question]
    st.session_state.search_history = ([question] + hist)[:10]
    st.session_state.engine_state.soil_report = st.session_state.get("soil_report")
    try:
        r = engine.answer(question, st.session_state.engine_state, answer_lang(), style(), detail())
        bot = {"role": "assistant", "text": r["text"], "year": r["year"], "warnings": r["warnings"],
               "table": r["table"], "sources": r["sources"], "chart": r["chart"], "lang": r["lang"],
               "followups": r["followups"], "timing_ms": r["timing_ms"], "options": r.get("options") or [],
               "intent": r["intent"], "question": question, "style": r["style"], "detail": r["detail"]}
        if r.get("error"):
            bot["text"] = f"⚠️ {r['error']}"
    except Exception as problem:     # last safety net so the app never crashes
        bot = {"role": "assistant", "text": f"⚠️ Something went wrong: {type(problem).__name__}: {problem}",
               "question": question}
    st.session_state.chat.append(bot)


def new_conversation():
    home_place = st.session_state.engine_state.home
    st.session_state.chat = []
    st.session_state.engine_state = engine.new_state()
    st.session_state.engine_state.set_home(home_place)


def memory_line():
    m = st.session_state.engine_state.summary()
    if not m["place"] and not st.session_state.chat:
        return u("memory_empty", ui())
    parts = []
    if m["places"]:
        parts.append(" + ".join(rb.place_label(p, ui()) for p in m["places"]))
    parts.append(u("gw_preview", ui()) if m["domain"] == "groundwater" else
                 L.t("dom_" + m["domain"], ui() if ui() in L.LANGUAGES else "en"))
    parts.append(L.LANGUAGES.get(m["language"], {}).get("native_name", m["language"]))
    parts.append(u("style_" + m["style"], ui()))
    parts.append(u("detail_" + m["detail"], ui()))
    return " · ".join(parts)


def show_message(msg, index, last=False):
    with st.chat_message(msg["role"], avatar="🧑‍🌾" if msg["role"] == "user" else str(uc.ASSETS / "logo_icon.svg")):
        st.markdown(msg["text"])
        if msg["role"] != "assistant":
            return
        lg = msg.get("lang", "en")
        if msg.get("year"):
            st.caption(L.t("year_caption", lg, year=msg["year"]))
        for w in msg.get("warnings") or []:
            st.warning(w, icon="⚠️")
        if msg.get("options") and last:
            st.caption(u("choose_option", ui()))
            cols = st.columns(min(len(msg["options"]), 3))
            for i, opt in enumerate(msg["options"], 1):
                cols[(i - 1) % len(cols)].button(f"{i}. {opt}", key=f"opt_{index}_{i}", on_click=ask, args=(str(i),),
                                                 width="stretch")
        if msg.get("chart"):
            uc.show_chart(msg["chart"], ui())
        if msg.get("table"):
            with st.expander(u("data_table", ui())):
                st.dataframe(pd.DataFrame(msg["table"]), hide_index=True)
                st.caption(u("empty_cells", ui()))
                st.download_button(u("download_csv", ui()), uc.csv_bytes(msg["table"]), f"jalmitra_answer_{index}.csv",
                                   "text/csv", key=f"dl_{index}")
        if msg.get("sources"):
            with st.expander(u("source_records", ui())):
                st.dataframe(pd.DataFrame(msg["sources"]), hide_index=True,
                             column_config={"url": st.column_config.LinkColumn("url")})
        if msg.get("followups") and last:
            st.caption(u("followups", ui()))
            cols = st.columns(len(msg["followups"]))
            for i, fu in enumerate(msg["followups"]):
                cols[i].button(fu, key=f"fu_{index}_{i}", on_click=ask, args=(fu,), width="stretch")
        meta = []
        if msg.get("timing_ms") is not None:
            meta.append(u("answered_in", ui()).format(ms=msg["timing_ms"]))
        if msg.get("style"):
            meta.append(f"{u('style_' + msg['style'], ui())} · {u('detail_' + msg['detail'], ui())}")
        if meta:
            st.caption(" · ".join(meta))
        rating = st.feedback("thumbs", key=f"fb_{index}")
        if rating is not None and not st.session_state.get(f"fb_saved_{index}"):
            uc.save_feedback(msg.get("question", ""), msg.get("intent", ""), rating)
            st.session_state[f"fb_saved_{index}"] = True
            st.toast(u("feedback_thanks", ui()))
        if st.session_state.get("voice_on") and last:
            voice.speak_controls(msg["text"], lg, key=index)


# ------------------------------------------------------------------ pages

def _home_setting(key, widget, label, options, fmt):
    """A copy of a sidebar setting on the home page (same stored value, own widget key)."""
    st.session_state["h_" + key] = st.session_state.get(key)

    def changed():
        st.session_state[key] = st.session_state["h_" + key]
    if widget == "seg":
        st.segmented_control(label, options, key="h_" + key, required=True, on_change=changed, format_func=fmt)
    else:
        st.selectbox(label, options, key="h_" + key, on_change=changed, format_func=fmt)


def page_home():
    lg = ui()
    st.html(f"""<div class="jm-hero"><div class="jm-tag" style="letter-spacing:.06em;font-size:.8rem">{u('product_line', lg)}</div>
      <h1>{u('welcome', lg)}</h1>
      <div class="jm-tag">{u('tagline', lg)}</div>
      <p class="jm-sub">{u('welcome_sub', lg)}</p><p>{u('welcome_support', lg)}</p></div>""")
    with st.form("home_search", border=False, clear_on_submit=True):
        c1, c2 = st.columns([5, 1.4], vertical_alignment="bottom")
        q = c1.text_input(u("search_placeholder", lg), placeholder=u("search_placeholder", lg),
                          label_visibility="collapsed")
        if c2.form_submit_button(u("ask_button", lg), type="primary", width="stretch") and q.strip():
            goto("ask", q.strip())
            st.rerun()
    c1, c2, c3, c4 = st.columns([1.1, 1.2, 1.6, 1.6], vertical_alignment="bottom")

    def speak():
        st.session_state.voice_on = True
        goto("ask")
    c1.button("🎤 " + u("speak_button", lg), on_click=speak, width="stretch")
    lang_options = dict(L.language_options())
    with c2:
        _home_setting("answer_lang", "select", u("answer_language", lg), list(lang_options), lambda c: lang_options[c])
    with c3:
        _home_setting("style", "seg", u("style", lg), ["farmer", "official", "student"], lambda x: u("style_" + x, lg))
    with c4:
        _home_setting("detail", "seg", u("detail", lg), ["short", "standard", "detailed"], lambda x: u("detail_" + x, lg))
    location_search("home_loc")

    def example_chosen(key):
        q = st.session_state.get(key)
        if q:
            st.session_state[key] = None
            goto("ask", q)
    st.pills(u("examples", lg), EXAMPLE_QUESTIONS[lg], key="home_ex", on_change=example_chosen, args=("home_ex",))
    st.pills(u("examples_data", lg), DATA_EXAMPLES[lg], key="home_ex2", on_change=example_chosen, args=("home_ex2",))

    st.subheader(u("quick_access", lg))
    cards = [("gw", "💧", "nav_gw", "card_gw"), ("soil", "🌱", "nav_soil", "card_soil"),
             ("crop", "🌾", "nav_crop", "card_crop"), ("gwq", "🧪", "nav_gwq", "card_gwq"),
             ("soilreport", "📄", "nav_soilreport", "card_soilreport"), ("land", "🏞️", "nav_land", "card_land")]
    for row in (cards[:3], cards[3:]):
        cols = st.columns(3)
        for col, (key, icon, title, desc) in zip(cols, row):
            with col.container(border=True, height="stretch"):
                st.markdown(f"#### {icon} {u(title, lg)}")
                st.write(u(desc, lg))
                st.page_link(PAGES[key], label=u("open", lg) + " →")

    st.subheader(u("gw_preview", lg) + " · " + u("soil_preview", lg) + " · " + u("crop_preview", lg))
    c1, c2, c3 = st.columns([2, 1, 1])
    p = home()
    with c1:
        if p is None:
            st.markdown(f"**{u('national_overview', lg)}**")
            uc.category_count_cards(db.category_counts(), f"AI2025 · {u('year', lg)} {', '.join(db.years())}",
                                    text_lang(), ncols=3)
            st.caption(u("choose_location_first", lg))
        else:
            st.markdown(f"**📍 {uc.place_title(p, text_lang())}**")
            r = engine.answer_places("status", [p], text_lang(), style(), "short")
            st.markdown(r["text"])
            st.page_link(PAGES["gw"], label=u("nav_gw", lg) + " →")
    rep = st.session_state.get("soil_report")
    with c2:
        if rep:
            uc._card(u("soil_preview", lg), f"{len(rep['rows'])}/12", u("your_card", lg), "soil")
        else:
            uc._card(u("soil_preview", lg), None, u("not_in_dataset", lg), "soil")
        st.page_link(PAGES["soilreport"], label=u("nav_soilreport", lg) + " →")
    with c3:
        import knowledge as kn
        import knowledge_answer as ka
        zone = kn.zone_for(*ka._district(p)) if p else None
        if zone:
            uc._card(u("crop_preview", lg), None, zone["zone"]["name"], "crop")
        else:
            uc._card(u("crop_preview", lg), None, u("insufficient", lg), "crop")
        st.page_link(PAGES["crop"], label=u("nav_crop", lg) + " →")

    st.subheader(u("coverage_title", lg))
    coverage_table(lg)
    st.subheader(u("help_title", lg))
    cols = st.columns(3)
    for i, col in enumerate(cols, 1):
        with col.container(border=True, height="stretch"):
            st.html(f'<div class="jm-step">{i}</div>')
            st.write(u(f"help_{i}", lg))
    st.caption(u("tagline2", lg) + " · " + u("version", lg))


def coverage_table(lg):
    c = db.coverage()
    num = ", ".join(f"{r['n']} {r['state']} {(r['assessment_unit_type'] or 'unit').lower()}s" for r in c["numeric_by_state"])
    rows = [
        {"topic": "Groundwater category", "status": u("available", lg),
         "coverage": f"{c['total_units']:,} assessment units, {c['states']} states/UTs, {', '.join(c['years'])}"},
        {"topic": "Groundwater figures (stage, recharge, extraction)", "status": u("partly", lg), "coverage": num},
        {"topic": "District and state totals", "status": u("available", lg), "coverage": "National Compilation 2025"},
    ]
    rows += [
        {"topic": "Soil test interpretation", "status": u("available", lg),
         "coverage": "Your own confirmed Soil Health Card; rating charts from ICAR-CRIDA and TNAU"},
        {"topic": "Soil, land and degradation maps for places", "status": u("data_unavailable", lg),
         "coverage": "Needs NBSS&LUP / Bhuvan data (see Data Sources)"},
        {"topic": "Crop facts (salt tolerance, water need, zone listing)", "status": u("partly", lg),
         "coverage": "FAO tables; Rajasthan Zone II-A crop list (SKNAU)"},
        {"topic": "Crop suitability for a field", "status": u("insufficient", lg), "coverage": "Needs field data"},
        {"topic": "Groundwater quality (station data)", "status": u("data_unavailable", lg),
         "coverage": "Importer ready; CGWB files must be downloaded"},
        {"topic": "Drinking / irrigation water limits", "status": u("available", lg),
         "coverage": "IS 10500:2012, CGWB 2024, IS 11624 (via CGWB)"},
    ]
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")


def page_ask():
    lg = ui()
    st.title("💬 " + u("nav_ask", lg))
    st.caption(u("ask_intro", lg))
    pending = st.session_state.pop("pending_q", None)
    if pending:
        ask(pending)
    c1, c2, c3 = st.columns([4, 1.3, 1.6], vertical_alignment="center")
    c1.info(f"🧠 **{u('memory', lg)}:** {memory_line()}")
    c2.button("🔄 " + u("new_chat", lg), on_click=new_conversation, width="stretch")
    c3.download_button("⬇️ " + u("download_report", lg), uc.report_markdown(st.session_state.chat),
                       "jalmitra_report.md", "text/markdown", disabled=not st.session_state.chat,
                       width="stretch")
    if st.session_state.get("voice_on"):
        with st.container(border=True):
            heard = voice.speech_input(st.session_state.get("voice_lang", "en"))
            if heard and heard.get("id") != st.session_state.voice_seen:
                st.session_state.voice_seen = heard.get("id")
                st.session_state.voice_draft = heard.get("text", "")
            draft = st.text_area(u("transcript", lg), key="voice_draft", height=70)

            def send_draft():
                ask(st.session_state.get("voice_draft", ""))
                st.session_state.voice_draft = ""
            st.button(u("ask", lg), on_click=send_draft, disabled=not (draft or "").strip(), type="primary")
    if not st.session_state.chat:
        def chosen():
            q = st.session_state.get("ask_ex")
            if q:
                st.session_state.ask_ex = None
                ask(q)
        st.pills(u("examples", lg), DATA_EXAMPLES[lg] + EXAMPLE_QUESTIONS[lg][:3], key="ask_ex", on_change=chosen)
    question = st.chat_input(u("chat_placeholder", lg))
    if question:
        ask(question)
    for i, m in enumerate(st.session_state.chat):
        show_message(m, i, last=(i == len(st.session_state.chat) - 1))
    if st.session_state.search_history:
        with st.expander(u("recent_questions", lg)):
            for i, q in enumerate(st.session_state.search_history):
                st.button(q, key=f"hist_{i}", on_click=ask, args=(q,))


def page_groundwater():
    lg, tl = ui(), text_lang()
    st.title("💧 " + u("nav_gw", lg))
    st.caption(u("gw_intro", lg))
    location_search("gw_loc")
    p = home()
    if p is None:
        st.info(u("choose_location_first", lg))
        st.markdown(f"**{u('national_overview', lg)}**")
        uc.category_count_cards(db.category_counts(), f"AI2025 · {u('year', lg)} {', '.join(db.years())}", tl)
        return
    st.header("📍 " + uc.place_title(p, tl))
    r = engine.answer_places("status", [p], tl, style(), detail())
    if p["type"] == "unit":
        rec = r["result"]["records"][0]
        uc.unit_cards(rec, lg, tl)
    else:
        counts = uc.area_cards(p, lg, tl)
        uc.counts_chart({uc.place_title(p, tl): counts})
    with st.container(border=True):
        st.markdown(f"**{u('summary', lg)}**")
        st.markdown(r["text"])
    if r["warnings"]:
        st.markdown(f"**{u('warnings', lg)}**")
        for w in r["warnings"]:
            st.warning(w, icon="⚠️")
    if p["type"] != "unit":
        rows = db.search_units(p["state"], p["district"] if p["type"] == "district" else None, limit=2000)
        table = [{"assessment_unit": x["assessment_unit"], "type": x["assessment_unit_type"], "district": x["district"],
                  "category": x["category"], "stage_of_extraction_pct": x["stage_of_extraction_pct"],
                  "source": f"{x['source_id']} p{x['source_page']}", "year": x["year"]} for x in rows]
        with st.expander(f"{u('units_in_area', lg)} ({len(table)})"):
            st.dataframe(pd.DataFrame(table), hide_index=True, width="stretch")
            st.caption(u("empty_cells", lg))
            st.download_button(u("download_csv", lg), uc.csv_bytes(table), "jalmitra_units.csv", "text/csv")
    if r["sources"]:
        with st.expander(u("source_records", lg)):
            st.dataframe(pd.DataFrame(r["sources"]), hide_index=True,
                         column_config={"url": st.column_config.LinkColumn("url")})


SOIL_ITEMS = ["Soil pH", "Electrical conductivity (EC)", "Organic carbon (OC)", "Texture", "Soil depth",
              "Salinity / sodicity", "Erosion", "Available water capacity (AWC)"]
SOIL_ITEMS_HI = ["मिट्टी का pH", "विद्युत चालकता (EC)", "जैविक कार्बन (OC)", "बनावट", "मिट्टी की गहराई",
                 "लवणता / क्षारीयता", "कटाव", "उपलब्ध जल क्षमता (AWC)"]
LAND_ITEMS = ["Land use / land cover", "Slope", "Wasteland", "Landform", "Drainage"]
LAND_ITEMS_HI = ["भूमि उपयोग / आवरण", "ढलान", "बंजर भूमि", "भू-आकृति", "जल निकासी"]
CROP_ITEMS = ["Suitable crops", "Crop water need", "Sowing season", "Yield potential"]
CROP_ITEMS_HI = ["उपयुक्त फसलें", "फसल की पानी की ज़रूरत", "बुवाई का मौसम", "उपज क्षमता"]


def _unavailable_page(icon, title_key, intro_key, items_en, items_hi, kind, show_groundwater=False):
    lg, tl = ui(), text_lang()
    st.title(f"{icon} {u(title_key, lg)}")
    st.info(u(intro_key, lg), icon="ℹ️")
    uc.unavailable_panel(u("data_unavailable", lg), items_hi if lg == "hi" else items_en, lg, kind)
    st.caption(u("not_in_db", lg))
    p = home()
    if show_groundwater or p is not None:
        st.subheader("💧 " + u("gw_preview", lg))
        if p is None:
            st.write(u("choose_location_first", lg))
        else:
            st.markdown(f"**📍 {uc.place_title(p, tl)}**")
            r = engine.answer_places("status", [p], tl, style(), "short")
            st.markdown(r["text"])
    st.button(u("ask_groundwater", lg), on_click=goto, args=("ask",), type="primary")


def page_soil():
    _unavailable_page("🌱", "nav_soil", "soil_intro", SOIL_ITEMS, SOIL_ITEMS_HI, "soil")


def page_land():
    _unavailable_page("🏞️", "nav_land", "land_intro", LAND_ITEMS, LAND_ITEMS_HI, "soil")


def page_crop():
    _unavailable_page("🌾", "nav_crop", "crop_intro", CROP_ITEMS, CROP_ITEMS_HI, "crop")


def page_irrigation():
    _unavailable_page("🚿", "nav_irrigation", "irrigation_intro", ["Irrigation schedule", "Method advice"],
                      ["सिंचाई समय-सारणी", "विधि सलाह"], "crop", show_groundwater=True)


def page_soil_report():
    lg = ui()
    st.title("📄 " + u("nav_soilreport", lg))
    st.info(u("soilreport_intro", lg), icon="ℹ️")
    uc.unavailable_panel(u("data_unavailable", lg), SOIL_ITEMS_HI[:4] if lg == "hi" else SOIL_ITEMS[:4], lg, "soil")
    st.button(u("ask_groundwater", lg), on_click=goto, args=("ask",), type="primary")


def page_geo():
    lg, tl = ui(), text_lang()
    st.title("🗺️ " + u("nav_geo", lg))
    st.caption(u("geo_intro", lg))
    tree = uc.location_tree()
    c1, c2, c3 = st.columns([1.2, 1.2, 2])
    state = c1.selectbox(u("pick_state", lg), list(tree), index=None, key="geo_state",
                         placeholder=u("type_to_search", lg))
    district = c2.selectbox(u("pick_district", lg), list(tree.get(state, {})), index=None, key="geo_district",
                            disabled=not state, placeholder=u("type_to_search", lg))
    cats = c3.multiselect(u("filter_category", lg), db.CATEGORIES, default=db.CATEGORIES, key="geo_cats",
                          format_func=lambda c: L.category_label(c, tl))
    if not state:
        rows = []
        for s in tree:
            counts = db.category_counts(s)
            rows.append({"state": s, **counts, "units": sum(counts.values())})
        df = pd.DataFrame(rows).set_index("state")
        st.markdown(f"**{u('national_overview', lg)}**")
        st.bar_chart(df[cats], color=[uc.CAT_COLORS[c] for c in cats], horizontal=True, height=900)
        st.dataframe(df, width="stretch")
        st.download_button(u("download_csv", lg), uc.csv_bytes(df.reset_index().to_dict("records")),
                           "jalmitra_states.csv", "text/csv")
        st.caption(f"{u('source', lg)}: AI2025 · {u('year', lg)} {', '.join(db.years())}")
        return
    if not district:
        rows = []
        for d in tree[state]:
            counts = db.category_counts(state, d)
            rows.append({"district": rb.show_name(d), **counts, "units": sum(counts.values())})
        df = pd.DataFrame(rows).set_index("district")
        st.markdown(f"**{state} · {u('districts_in_state', lg)}**")
        st.bar_chart(df[cats], color=[uc.CAT_COLORS[c] for c in cats], horizontal=True,
                     height=max(300, 26 * len(df)))
        st.dataframe(df, width="stretch")
        st.download_button(u("download_csv", lg), uc.csv_bytes(df.reset_index().to_dict("records")),
                           f"jalmitra_{state}.csv", "text/csv")
    else:
        units = db.search_units(state, district, limit=2000)
        table = [{"assessment_unit": rb.show_name(x["assessment_unit"]), "type": x["assessment_unit_type"],
                  "category": x["category"], "stage_of_extraction_pct": x["stage_of_extraction_pct"],
                  "source": f"{x['source_id']} p{x['source_page']}", "year": x["year"]}
                 for x in units if x["category"] in cats]
        st.markdown(f"**{rb.show_name(district)}, {state}** · {len(table)} {u('units', lg).lower()}")
        st.dataframe(pd.DataFrame(table), hide_index=True, width="stretch")
        st.caption(u("empty_cells", lg))
        st.download_button(u("download_csv", lg), uc.csv_bytes(table), f"jalmitra_{district}.csv", "text/csv")

        def use_here():
            set_location_from_place(uc.place_for(state, district))
        st.button("📍 " + u("use_location", lg), on_click=use_here)
    st.caption(f"{u('source', lg)}: AI2025 · {u('year', lg)} {', '.join(db.years())}")


def page_compare():
    lg, tl = ui(), text_lang()
    st.title("⚖️ " + u("nav_compare", lg))
    st.caption(u("compare_intro", lg))
    options = uc.all_place_options()
    labels = dict(options)
    keys = [k for k, _ in options]
    c1, c2 = st.columns(2)
    a = c1.selectbox(u("place_a", lg), keys, index=None, key="cmp_a", format_func=lambda k: labels[k],
                     placeholder=u("type_to_search", lg))
    b = c2.selectbox(u("place_b", lg), keys, index=None, key="cmp_b", format_func=lambda k: labels[k],
                     placeholder=u("type_to_search", lg))
    if a and b and a != b:
        r = engine.answer_places("compare", [uc.place_from_key(a), uc.place_from_key(b)], tl, style(), detail())
        msg = {"role": "assistant", "text": r["text"], "year": r["year"], "warnings": r["warnings"],
               "table": r["table"], "sources": r["sources"], "chart": r["chart"], "lang": r["lang"],
               "followups": [], "timing_ms": r["timing_ms"], "style": r["style"], "detail": r["detail"],
               "question": f"compare {a} | {b}", "intent": "compare"}
        show_message(msg, 9000)


def page_reports():
    lg = ui()
    st.title("🗂️ " + u("nav_reports", lg))
    st.caption(u("reports_intro", lg))
    chat = st.session_state.chat
    if not chat:
        st.info(u("no_reports", lg))
        st.button(u("nav_ask", lg), on_click=goto, args=("ask",), type="primary")
        return
    st.download_button("⬇️ " + u("download_report", lg), uc.report_markdown(chat), "jalmitra_report.md",
                       "text/markdown", type="primary")
    tables = [dict(row, question=m.get("question", "")) for m in chat if m["role"] == "assistant"
              for row in (m.get("table") or [])]
    if tables:
        st.download_button(u("download_csv", lg), uc.csv_bytes(tables), "jalmitra_all_tables.csv", "text/csv")
    for m in chat:
        if m["role"] == "assistant":
            with st.expander("❓ " + m.get("question", "")):
                st.markdown(m["text"])


def page_learn():
    lg = ui()
    tl = lg if lg in L.LANGUAGES else "en"
    st.title("📘 " + u("nav_learn", lg))
    st.subheader(u("glossary", lg))
    for cat in db.CATEGORIES:
        with st.expander(f"{L.category_label(cat, tl)}"):
            st.write(L.t(f"explain_{cat}", tl))
            if f"meaning_{cat}" in L.TEMPLATES:
                st.write(L.t(f"meaning_{cat}", tl))
    with st.expander(u("stage", lg)):
        st.write(L.t("explain_stage", tl))
        st.write(L.t("thresholds", tl))
    for term, text in GLOSSARY.items():
        with st.expander(term):
            st.write(text.get(lg) or text["en"])
    st.subheader(u("how_to_ask", lg))
    examples = {"English": "Is Ajmer Urban safe? / Top 5 over-exploited blocks in Rajasthan",
                "हिन्दी": "अजमेर अर्बन की भूजल स्थिति क्या है?", "Hinglish": "Ajmer Urban ka paani kaisa hai?",
                "मराठी": "पुण्यात भूजल स्थिती काय आहे?", "ਪੰਜਾਬੀ": "ਲੁਧਿਆਣਾ ਜ਼ਿਲ੍ਹੇ ਵਿੱਚ ਪਾਣੀ ਦੀ ਸਥਿਤੀ ਕੀ ਹੈ?",
                "राजस्थानी": "म्हारो अजमेर जिलो रो पाणी कियां है?"}
    for name, q in examples.items():
        c1, c2 = st.columns([1, 4], vertical_alignment="center")
        c1.markdown(f"**{name}**")
        first = q.split(" / ")[0]
        c2.button(q, key=f"learn_{name}", on_click=goto, args=("ask", first))


ABOUT = {
    "en": """
**JalMitra** explains the groundwater situation of a block, district or state in simple words, in six languages,
using only published government assessments.

**How it works.** Your question is read by fixed rules (no AI model, no API key). The place is found in the
database, the answer is filled from read-only database values, and every answer shows its source page and
assessment year. If something is not in the database, JalMitra says so instead of guessing.

**What it can do now (3.0).** Groundwater category for 6,762 assessment units; figures for 302 Rajasthan blocks;
district and state totals; comparisons and follow-up questions; your own Soil Health Card explained against published
rating charts; your water test compared with IS 10500 and irrigation limits; published crop facts (FAO, SKNAU);
Land Condition, Soil, Crop, Irrigation and Complete reports.

**Not yet.** Soil, land, degradation, water-level and water-quality maps or records for places are not loaded, so those
parts say "Not available in the current dataset". Crop suitability for a field shows "Insufficient data".

**Privacy.** No sign-in, no location tracking (you choose your location). An uploaded soil report stays in your session
unless you save it on this computer, and can be deleted. Nothing is sent to any service.
""",
    "hi": """
**JalMitra** किसी ब्लॉक, ज़िले या राज्य की भूजल स्थिति आसान शब्दों में, छह भाषाओं में समझाता है, केवल प्रकाशित
सरकारी आकलन से।

**यह कैसे काम करता है।** आपका सवाल तय नियमों से पढ़ा जाता है (कोई AI मॉडल नहीं, कोई API की नहीं)। जगह डेटाबेस
में खोजी जाती है, उत्तर केवल डेटाबेस के मानों से बनता है, और हर उत्तर में स्रोत पृष्ठ और आकलन वर्ष दिखता है। जो
डेटाबेस में नहीं है, JalMitra वह साफ़ बताता है, अंदाज़ा नहीं लगाता।

**अभी क्या कर सकता है (3.0)।** 6,762 आकलन इकाइयों की भूजल श्रेणी; राजस्थान के 302 ब्लॉकों के आंकड़े; ज़िला और
राज्य कुल; तुलना और आगे के सवाल; आपके सॉयल हेल्थ कार्ड की प्रकाशित चार्ट से व्याख्या; आपकी पानी जाँच की IS 10500 और
सिंचाई सीमाओं से तुलना; फसलों के प्रकाशित तथ्य (FAO, SKNAU); भूमि, मिट्टी, फसल, सिंचाई और पूरी रिपोर्ट।

**अभी नहीं।** जगहों के मिट्टी, भूमि, क्षरण, जल-स्तर और जल-गुणवत्ता नक्शे या रिकॉर्ड नहीं हैं, वहाँ "वर्तमान डेटासेट
में उपलब्ध नहीं" दिखता है। खेत की फसल उपयुक्तता "अपर्याप्त डेटा" दिखाती है।

**गोपनीयता।** कोई साइन-इन नहीं, कोई लोकेशन ट्रैकिंग नहीं। अपलोड की गई मिट्टी रिपोर्ट आपके सत्र में रहती है जब तक आप
इसे इस कंप्यूटर पर न सहेजें, और हटाई जा सकती है। कुछ भी किसी सेवा को नहीं भेजा जाता।
""",
}


def page_about():
    lg = ui()
    st.image(str(uc.ASSETS / ("logo_dark.svg" if uc.theme_type() == "dark" else "logo.svg")), width=260)
    st.markdown(f"### {u('tagline', lg)}")
    st.markdown(ABOUT.get(lg, ABOUT["en"]))
    st.caption(u("version", lg))


def page_sources():
    lg = ui()
    st.title("📚 " + u("nav_sources", lg))
    st.caption(u("sources_intro", lg))
    src = pd.DataFrame(db.data_sources().values())
    cols = [c for c in ["source_id", "title", "publisher", "source_url", "file_name"] if c in src.columns]
    st.dataframe(src[cols], hide_index=True, width="stretch",
                 column_config={"source_url": st.column_config.LinkColumn("source_url")})
    st.subheader(u("domain_coverage", lg))
    coverage_table(lg)
    c = db.coverage()
    st.caption(db.coverage_text() + f" {u('year', lg)}: {', '.join(c['years'])}.")
    st.subheader(u("quality_title", lg))
    flagged = db.flagged_units(limit=1000)
    counts = {}
    for r in flagged:
        for f in (r["quality_flag"] or "").split(";"):
            if f and f != "values_not_in_uploaded_sources":
                counts[f] = counts.get(f, 0) + 1
    st.dataframe(pd.DataFrame([{"flag": k, "units": v} for k, v in sorted(counts.items())]), hide_index=True)
    conflicts = db.flagged_units(flag="category_conflict_between_sources", limit=100)
    for r in conflicts:
        obs = db.conflicts_for(r["record_id"])
        st.warning(f"**{rb.show_name(r['assessment_unit'])}** ({rb.show_name(r['district'])}, {r['state']}): " +
                   " | ".join(f"{o['source_id']} p{o['source_page']}: {o['observation']}" for o in obs), icon="⚠️")
    with st.expander(f"{u('warnings', lg)} ({len(flagged)})"):
        st.dataframe(pd.DataFrame([{"assessment_unit": r["assessment_unit"], "district": r["district"],
                                    "state": r["state"], "category": r["category"],
                                    "quality_flag": r["quality_flag"]} for r in flagged]),
                     hide_index=True, width="stretch")

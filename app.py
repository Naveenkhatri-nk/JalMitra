"""
app.py - JalMitra website (Streamlit). Local AI groundwater assistant (JalMitra 4.0, Phase 6), runs on this
computer only (localhost).

Run it from the JalMitra folder:
    streamlit run app.py          (or START_JALMITRA.bat)

Answers come from data/groundwater.db (read-only) and the local AI model (Ollama) through jalmitra_ai.py.

UI redesign (24 Nov 2026), ChatGPT / Claude-style:
  * sidebar: JalMitra logo, "New chat", saved conversations (Today / Yesterday / Earlier; open, rename, delete,
    clear all - stored as JSON in data/chat_history/ by chat_store.py), and at the bottom "More pages", Settings,
    a quick Day / Night toggle, About and Coming soon
  * Settings (ui_settings.py) open in a dialog: theme, interface and answer language, default location, answer
    style and length, voice, local AI status (model, GPU), clear history; saved to data/chat_history/settings.json
  * theme (ui_theme.py): Day / Night / System palettes as CSS variables, plus .streamlit/config.toml
  * Streamlit's menu, deploy button and footer are hidden
Accounts (27 Nov 2026): visitors must log in or create an account first (ui_auth.py, auth.py): Argon2id password
hashes, lockout and rate limits, password reset by email code, server-side sessions, per-user private chat history,
an Admin page for admins and a Privacy page. JALMITRA_AUTH=off turns login off for single-user use on this computer.
Unexpected errors show a short friendly message with a reference code; the details go to the server log only.
All earlier pages are kept (ui_pages.py, ui_pages_v3.py); the soil / crop / land / irrigation / water-quality pages
stay hidden (visibility=HIDDEN) and the "Coming soon" page lists them.
"""

import logging
import uuid

import streamlit as st

import database
import engine
import ui_chat_v4 as chat4          # JalMitra 4.0 (Phase 4): groundwater chat, the start page
import ui_coming_soon as soon       # JalMitra 4.0 (Phase 4): planned modules
import ui_components as uc
import ui_pages as pages
import ui_pages_v3 as pages3
import ui_settings as settings      # UI redesign: settings dialog + local settings file
import ui_theme as theme            # UI redesign: Day / Night / System
import ui_auth                      # accounts: login, sign-up, reset, admin, privacy (27 Nov 2026)
from ui_text import u

st.set_page_config(page_title="JalMitra", page_icon=str(uc.ASSETS / "favicon.png"), layout="wide",
                   initial_sidebar_state="auto")
uc.inject_css()

# ------------------------------------------------------------------ session + saved settings
settings.init_session()            # theme, languages, location, style, detail, voice (from data/chat_history/)
for k, v in {"chat": [], "voice_seen": None, "search_history": []}.items():
    st.session_state.setdefault(k, v)
st.session_state.engine_state = st.session_state.get("engine_state") or engine.new_state()

try:
    database.coverage()
    db_error = None
except database.DatabaseNotReadyError as error:
    db_error = str(error)

lg = st.session_state.ui_lang
uc.set_ui_lang(lg)
palette = theme.apply(st.session_state.theme, uc.theme_type())
st.html(settings.DIALOG_CSS)
dark = palette == "dark"

# ------------------------------------------------------------------ login (stops here with the login screen)
account = ui_auth.require_login()
st.logo(str(uc.ASSETS / ("logo_dark.svg" if dark else "logo.svg")), size="large",
        icon_image=str(uc.ASSETS / "logo_icon.svg"))

# home location chosen in Settings (never tracked)
st.session_state.engine_state.set_home(uc.place_for(st.session_state.loc_state or None,
                                                    st.session_state.loc_district or None,
                                                    st.session_state.loc_unit or None))

# ------------------------------------------------------------------ navigation
# JalMitra 4.0 (Phase 4): the groundwater chat is the start page. Soil, crop, land, irrigation and water-quality
# pages (and the 3.0 chat page) are kept but hidden from the menu (visibility="hidden"; their code is unchanged);
# the "Coming soon" page lists those modules. UI redesign: the page menu itself is hidden; the sidebar shows the
# chat history and the other pages are under "More pages".
HIDDEN = "hidden"
P = {
    "chat": st.Page(chat4.page_chat, title="JalMitra Chat" if lg != "hi" else "JalMitra चैट", icon=":material/chat:",
                    url_path="chat", default=True),
    "home": st.Page(pages.page_home, title=u("nav_home", lg), icon=":material/home:", url_path="home"),
    # Phase 6: the old rule-only chat is no longer user-facing; its URL opens the AI chat (page_ask code is kept)
    "ask": st.Page(lambda: st.switch_page(P["chat"]), title=u("nav_ask", lg), icon=":material/forum:", url_path="ask",
                   visibility=HIDDEN),
    "gw": st.Page(pages.page_groundwater, title=u("nav_gw", lg), icon=":material/water_drop:", url_path="groundwater"),
    "gwq": st.Page(pages3.page_gw_quality, title=u("nav_gwq", lg), icon=":material/science:",
                   url_path="groundwater-quality", visibility=HIDDEN),
    "soil": st.Page(pages3.page_soil, title=u("nav_soil", lg), icon=":material/grass:", url_path="soil",
                    visibility=HIDDEN),
    "soilprofile": st.Page(pages3.page_soil_profile, title=u("nav_soilprofile", lg), icon=":material/layers:",
                           url_path="soil-profile", visibility=HIDDEN),
    "land": st.Page(pages3.page_land, title=u("nav_land", lg), icon=":material/landscape:", url_path="land",
                    visibility=HIDDEN),
    "landdeg": st.Page(pages3.page_land_degradation, title=u("nav_landdeg", lg), icon=":material/terrain:",
                       url_path="land-degradation", visibility=HIDDEN),
    "crop": st.Page(pages3.page_crop, title=u("nav_crop", lg), icon=":material/agriculture:", url_path="crops",
                    visibility=HIDDEN),
    "irrigation": st.Page(pages3.page_irrigation, title=u("nav_irrigation", lg), icon=":material/shower:",
                          url_path="irrigation", visibility=HIDDEN),
    "soon": st.Page(soon.page_coming_soon, title="Coming soon" if lg != "hi" else "जल्द आ रहा है",
                    icon=":material/upcoming:", url_path="coming-soon"),
    "geo": st.Page(pages3.page_geo, title=u("nav_geo", lg), icon=":material/travel_explore:", url_path="explorer"),
    "compare": st.Page(pages.page_compare, title=u("nav_compare", lg), icon=":material/compare_arrows:",
                       url_path="compare"),
    "soilreport": st.Page(pages3.page_soil_report, title=u("nav_soilreport", lg), icon=":material/description:",
                          url_path="soil-report", visibility=HIDDEN),
    "reports": st.Page(pages3.page_reports, title=u("nav_reports", lg), icon=":material/folder_open:",
                       url_path="reports"),
    "learn": st.Page(pages3.page_learn, title=u("nav_learn", lg), icon=":material/school:", url_path="learn"),
    "sources": st.Page(pages3.page_sources, title=u("nav_sources", lg), icon=":material/verified:",
                       url_path="sources"),
    "about": st.Page(pages.page_about, title=u("nav_about", lg), icon=":material/info:", url_path="about"),
    "privacy": st.Page(ui_auth.page_privacy, title="Privacy", icon=":material/shield_lock:", url_path="privacy"),
}
if ui_auth.is_admin():              # the admin page exists only for admins (other users get "page not found")
    P["admin"] = st.Page(ui_auth.page_admin, title="Admin", icon=":material/admin_panel_settings:", url_path="admin")
pages.PAGES.update(P)
nav = st.navigation({
    u("sec_main", lg): [P["chat"], P["home"], P["ask"]],
    u("sec_water", lg): [P["gw"], P["gwq"], P["irrigation"]],
    u("sec_land", lg): [P["soil"], P["soilprofile"], P["land"], P["landdeg"], P["crop"]],
    u("sec_explore", lg): [P["geo"], P["compare"]],
    u("sec_tools", lg): [P["soilreport"], P["reports"]],
    u("sec_help", lg): [P["learn"], P["sources"], P["about"], P["soon"], P["privacy"]] + ([P["admin"]] if "admin" in P
                                                                                       else []),
}, position="hidden")
on_chat = nav.url_path == P["chat"].url_path


def open_settings():
    st.session_state["_jm_open_settings"] = True


# ------------------------------------------------------------------ sidebar: new chat, history, settings
chat4.init_history()
with st.sidebar:
    chat4.sidebar_history(on_chat_page=on_chat)
    st.divider()
    with st.container(key="jm_sidefoot"):
        with st.expander(chat4.t("explore"), icon=":material/apps:"):
            for key in ["home", "gw", "geo", "compare", "reports", "learn", "sources"]:
                st.page_link(P[key])
        st.page_link(P["about"], icon=":material/info:")
        st.page_link(P["soon"], icon=":material/upcoming:")
        st.page_link(P["privacy"], icon=":material/shield_lock:")
        if "admin" in P:
            st.page_link(P["admin"], icon=":material/admin_panel_settings:")
        ui_auth.sidebar_account()
        c1, c2 = st.columns([0.78, 0.22], vertical_alignment="center")
        c1.button(chat4.t("settings"), key="jm_settings_btn", icon=":material/settings:", on_click=open_settings,
                  width="stretch")
        with c2.container(key="jm_themeq"):
            st.button("", key="jm_theme_toggle", icon=":material/light_mode:" if dark else ":material/dark_mode:",
                      help=chat4.t("theme_day") if dark else chat4.t("theme_night"), on_click=settings.toggle_theme,
                      args=(palette,), width="stretch")
    if db_error:
        st.error(f"{u('db_problem', lg)}: {db_error}")

if st.session_state.pop("_jm_open_settings", False):
    settings.open_dialog(on_clear=chat4.clear_all)
else:
    ui_auth.maybe_open_account()
if st.session_state.get("_jm_toast"):
    st.toast(st.session_state.pop("_jm_toast"), icon=":material/check_circle:")

# page change requested by a button callback: done after the sidebar so its settings stay registered
target = st.session_state.pop("goto", None)
if target == "ask":
    target = "chat"                 # 4.0: questions from the overview page open the new chat (pending_q is kept)
if target and target in P and P[target].url_path != nav.url_path:
    st.switch_page(P[target])

if db_error:
    st.warning("**No official groundwater data imported yet.** JalMitra only answers from official data and never "
               "makes up numbers. Build the database with `python build_dataset.py` and `python build_database.py`.")
    st.stop()

try:
    nav.run()
except Exception:                   # friendly error page; the details go only to the server log (never to visitors)
    ref = uuid.uuid4().hex[:8]
    logging.getLogger("jalmitra.app").exception("page error ref=%s page=%s", ref, nav.url_path)
    st.error(f"Sorry, something went wrong on this page. Please try again, or start a new chat. "
             f"If it keeps happening, tell the JalMitra team this code: **{ref}**")

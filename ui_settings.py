"""
ui_settings.py - JalMitra settings (UI redesign, 24 Nov 2026).

Settings live in plain session keys ("theme", "ui_lang", "answer_lang", "loc_state", ...) and are saved to the local
settings file (chat_store.save_settings, data/chat_history/settings.json) whenever they change. Each widget uses a
"w_" copy of its key (Streamlit forgets widgets that were not drawn in a run, for example while the settings dialog
is closed), refilled from the plain key on every run.

The settings panel is a dialog (st.dialog) opened from the sidebar: theme, interface and answer language, default
location, answer style and length, voice, local AI status (model, GPU) and "clear all history".
"""

import streamlit as st

import chat_store
import jalmitra_ai as ja
import language
import ui_components as uc
import voice
from ui_text import u

DEFAULTS = {"theme": "day",       # naveen (24 Nov): light colours by default; Night / System in Settings
 "ui_lang": "en", "answer_lang": language.AUTO, "style": "farmer", "detail": "standard",
            "voice_on": False, "loc_state": "", "loc_district": "", "loc_unit": ""}
PERSIST = ["theme", "ui_lang", "answer_lang", "loc_state", "loc_district", "loc_unit", "style", "detail", "voice_on",
           "voice_lang"]
FULL_RERUN = {"theme", "ui_lang"}          # changes that redraw the whole page (the dialog closes)

T = {
    "en": {"title": "Settings", "appearance": "Appearance", "theme": "Theme", "day": "Day", "night": "Night",
           "system": "System", "language": "Language", "location": "Default location", "answers": "Answers",
           "ai": "Local AI", "ai_ok": "Connected", "ai_bad": "Not available", "model": "Model", "gpu": "Processor",
           "server": "Server", "not_loaded": "not loaded yet (loads on the first question)", "recheck": "Check again",
           "privacy": "Chat history", "privacy_note": "Conversations are saved only on this computer "
           "(data\\chat_history). Nothing is uploaded.",
           "privacy_note_acct": "Your conversations are saved in your own JalMitra account. Only you can see them.",
           "clear": "Clear all history",
           "clear_confirm": "Yes, delete every saved conversation", "cleared": "Deleted {n} conversations.",
           "recent": "Recent locations", "help_ai": "Start the local AI with START_JALMITRA.bat (or open the Ollama "
           "app), then reload this page."},
    "hi": {"title": "सेटिंग्स", "appearance": "रूप", "theme": "थीम", "day": "दिन", "night": "रात", "system": "सिस्टम",
           "language": "भाषा", "location": "डिफ़ॉल्ट स्थान", "answers": "उत्तर", "ai": "स्थानीय AI", "ai_ok": "जुड़ा है",
           "ai_bad": "उपलब्ध नहीं", "model": "मॉडल", "gpu": "प्रोसेसर", "server": "सर्वर",
           "not_loaded": "अभी लोड नहीं (पहले प्रश्न पर लोड होगा)", "recheck": "फिर जांचें", "privacy": "बातचीत इतिहास",
           "privacy_note": "बातचीत केवल इसी कंप्यूटर पर (data\\chat_history) सहेजी जाती है। कुछ भी अपलोड नहीं होता।",
           "privacy_note_acct": "आपकी बातचीत आपके अपने JalMitra खाते में सहेजी जाती है। केवल आप ही इसे देख सकते हैं।",
           "clear": "पूरा इतिहास मिटाएँ", "clear_confirm": "हाँ, सभी सहेजी गई बातचीत मिटाएँ",
           "cleared": "{n} बातचीत मिटाई गईं।", "recent": "हाल के स्थान",
           "help_ai": "START_JALMITRA.bat से स्थानीय AI शुरू करें (या Ollama ऐप खोलें), फिर यह पेज दोबारा लोड करें।"},
}


def lang():
    lg = st.session_state.get("ui_lang", "en")
    return lg if lg in T else "en"


def s(key):
    return T[lang()].get(key) or T["en"][key]


def init_session():
    """Fill the session from the settings file once, then from DEFAULTS; refill the widget copies."""
    if not st.session_state.get("_jm_settings_loaded"):
        st.session_state["_jm_settings_loaded"] = True
        for k, v in chat_store.load_settings().items():
            st.session_state.setdefault(k, v)
    for k, v in DEFAULTS.items():
        st.session_state.setdefault(k, v)
    for k in PERSIST:
        if k in st.session_state:
            st.session_state["w_" + k] = st.session_state[k]


def save(*keys):
    try:
        chat_store.save_settings({k: st.session_state.get(k) for k in keys})
    except OSError:
        pass                                     # a read-only folder never breaks the app


def keep(key, *reset):
    """on_change of a settings widget: copy the widget value, clear dependent keys, save to the settings file."""
    st.session_state[key] = st.session_state["w_" + key]
    for r in reset:
        st.session_state[r] = ""
    save(key, *reset)
    if key in FULL_RERUN:
        st.session_state["_jm_settings_rerun"] = True


def set_theme(choice):
    st.session_state.theme = choice
    st.session_state.w_theme = choice
    save("theme")


def toggle_theme(current_palette):
    """Sidebar quick toggle: Day <-> Night (from System it switches to the opposite of what is shown)."""
    set_theme("day" if current_palette == "dark" else "night")


def _set_location_from_place(p):
    st.session_state.loc_state = p.get("state") or ""
    st.session_state.loc_district = (p.get("district") or "") if p.get("type") in ("district", "unit") else ""
    st.session_state.loc_unit = (p.get("name") or "") if p.get("type") == "unit" else ""
    save("loc_state", "loc_district", "loc_unit")


def ai_details():
    """Rows for the Local AI section: (label, value)."""
    a = ja.ai_status()
    rows = [(s("ai"), ("🟢 " + s("ai_ok")) if a.get("ok") else ("🔴 " + s("ai_bad"))), (s("model"), a.get("model"))]
    rows.append((s("gpu"), a.get("processor") or s("not_loaded")))
    rows.append((s("server"), a.get("url") or "http://localhost:11434"))
    return a, rows


def settings_body(on_clear=None):
    """The settings controls (also usable outside the dialog)."""
    lg = lang()
    ui_lg = st.session_state.get("ui_lang", "en")

    st.markdown(f"**{s('appearance')}**")
    st.segmented_control(s("theme"), chat_store.THEMES, key="w_theme", required=True, on_change=keep,
                         args=("theme",), format_func=lambda x: {"day": "☀️ " + s("day"), "night": "🌙 " + s("night"),
                                                                  "system": "🖥️ " + s("system")}[x])

    st.markdown(f"**{s('language')}**")
    c1, c2 = st.columns(2)
    c1.segmented_control(u("ui_language", ui_lg), ["en", "hi"], key="w_ui_lang", required=True, on_change=keep,
                         args=("ui_lang",), format_func=lambda c: {"en": "English", "hi": "हिन्दी"}[c])
    opts = dict(language.language_options())
    c2.selectbox(u("answer_language", ui_lg), list(opts), key="w_answer_lang", on_change=keep, args=("answer_lang",),
                 format_func=lambda c: opts[c])

    st.markdown(f"**📍 {s('location')}**", help=u("location_help", ui_lg))
    tree = uc.location_tree()
    any_label = u("any", ui_lg)
    c1, c2, c3 = st.columns(3)
    c1.selectbox(u("state", ui_lg), [""] + list(tree), key="w_loc_state", on_change=keep,
                 args=("loc_state", "loc_district", "loc_unit"), format_func=lambda x: x or any_label)
    state = st.session_state.get("loc_state") or ""
    if state:
        c2.selectbox(u("district", ui_lg), [""] + list(tree.get(state, {})), key="w_loc_district", on_change=keep,
                     args=("loc_district", "loc_unit"), format_func=lambda d: d.replace("_", " ") if d else any_label)
    district = st.session_state.get("loc_district") or ""
    if state and district:
        c3.selectbox(u("block", ui_lg), [""] + tree.get(state, {}).get(district, []), key="w_loc_unit",
                     on_change=keep, args=("loc_unit",), format_func=lambda x: x.replace("_", " ") if x else any_label)
    es = st.session_state.get("engine_state")
    recent = list(reversed(es.history[-4:])) if es is not None else []
    if recent:
        st.caption(s("recent"))
        cols = st.columns(min(4, len(recent)))
        for i, p in enumerate(recent):
            cols[i].button("📍 " + uc.place_title(p, ui_lg), key=f"jm_recent_{i}", on_click=_set_location_from_place,
                           args=(p,), width="stretch")

    st.markdown(f"**{s('answers')}**")
    c1, c2 = st.columns(2)
    c1.segmented_control(u("style", ui_lg), ["farmer", "official", "student"], key="w_style", required=True,
                         on_change=keep, args=("style",), format_func=lambda x: u("style_" + x, ui_lg))
    c2.segmented_control(u("detail", ui_lg), ["short", "standard", "detailed"], key="w_detail", required=True,
                         on_change=keep, args=("detail",), format_func=lambda x: u("detail_" + x, ui_lg))
    st.toggle("🎤 " + u("voice_mode", ui_lg), key="w_voice_on", on_change=keep, args=("voice_on",))
    if st.session_state.get("voice_on"):
        codes = list(language.LANGUAGES)
        if st.session_state.get("voice_lang") not in codes:
            a = st.session_state.get("answer_lang")
            st.session_state.voice_lang = a if a in codes else ("hi" if ui_lg == "hi" else "en")
            st.session_state.w_voice_lang = st.session_state.voice_lang
        st.selectbox(u("voice_lang", ui_lg), codes, key="w_voice_lang", on_change=keep, args=("voice_lang",),
                     format_func=lambda c: language.LANGUAGES[c]["native_name"])
        stt, tts, level = voice.voice_info(st.session_state.voice_lang)
        st.caption(f"{stt} / {tts} · {level}. {u('voice_note', ui_lg)}")

    st.markdown(f"**🤖 {s('ai')}**")
    a, rows = ai_details()
    st.html('<div class="jm-ai-table">' + "".join(
        f'<div class="jm-ai-row"><span>{k}</span><span>{v}</span></div>' for k, v in rows) + "</div>")
    if not a.get("ok"):
        st.caption(f"{a.get('error') or ''}. {s('help_ai')}")
    if st.button(s("recheck"), key="jm_ai_recheck", icon=":material/refresh:"):
        ja.ai_status(force=True)

    st.markdown(f"**🗂️ {s('privacy')}**")
    import ui_auth
    st.caption(s("privacy_note_acct") if ui_auth.user() else s("privacy_note"))
    confirm = st.checkbox(s("clear_confirm"), key="jm_clear_confirm")
    if st.button(s("clear"), key="jm_clear_all", icon=":material/delete_sweep:", disabled=not confirm):
        n = on_clear() if on_clear else chat_store.clear_conversations()
        st.session_state["_jm_toast"] = s("cleared").format(n=n)
        st.rerun()                               # full rerun: the dialog closes, the sidebar list is emptied

    if lg and st.session_state.pop("_jm_settings_rerun", False):
        st.rerun()


def open_dialog(on_clear=None):
    @st.dialog(s("title"), width="large")
    def _dialog():
        settings_body(on_clear)
    _dialog()


DIALOG_CSS = """<style>
.jm-ai-table { border: 1px solid var(--jm-border); border-radius: 12px; overflow: hidden; font-size: .9rem; }
.jm-ai-row { display: flex; justify-content: space-between; gap: 1rem; padding: .45rem .8rem;
  border-bottom: 1px solid var(--jm-border); }
.jm-ai-row:last-child { border-bottom: none; }
.jm-ai-row span:first-child { color: var(--jm-muted); }
.jm-ai-row span:last-child { font-weight: 600; text-align: right; }
</style>"""

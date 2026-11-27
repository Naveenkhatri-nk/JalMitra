"""
ui_chat_v4.py - JalMitra chat page: "JalMitra — Your Intelligent Groundwater Assistant" (Phase 6: AI always on;
UI redesign 24 Nov 2026: ChatGPT / Claude-style layout, saved chat history).

Every reply is written by the local AI model through jalmitra_ai.respond (Ollama on this computer, no cloud):
  * the rule engine runs internally only (language, intent, place resolution, clarification options, safety,
    read-only database retrieval); its own text is never shown
  * the AI reply is checked (numbers, categories, places, citations, meaning, self-check); a reply that fails is
    regenerated, and if it still fails the user sees "could not be verified" - never a rule-written answer
  * official figures (category, stage, recharge, extractable, extraction, unit counts) are shown separately as data
    cards and a table read straight from groundwater.db, with assessment year, location and sources
  * if Ollama or the model is not available the page says so clearly and explains how to start it
  * soil, crop, land, irrigation, water quality: the AI replies that they are coming in a future update
Layout (redesign): sidebar with "New chat" and the saved conversations (Today / Yesterday / Earlier; open, rename,
delete, clear all), stored locally as JSON by chat_store.py; a clean centred welcome screen with example cards;
chat bubbles (user right, assistant left with the water-drop avatar) in a ~760 px column; a small AI status chip.
Old pages (ui_pages.py, ui_pages_v3.py) are kept.
"""

import base64
import html
import time
import uuid

import pandas as pd
import streamlit as st

import chat_store
import engine
import jalmitra_ai as ja
import language as L
import ui_components as uc

TITLE = "JalMitra — Your Intelligent Groundwater Assistant"

T = {  # interface text (en / hi; the other languages use English labels, replies come in all six)
    "en": {
        "subtitle": "Ask about groundwater status, recharge, extraction and categories for any block, district or "
                    "state in India.",
        "data_note": "Official 2025 groundwater data (CGWB / State GWRA) · replies by a local AI, checked against "
                     "the data · nothing leaves this computer",
        "examples": "Try a question", "new": "New chat", "history": "Chats",
        "placeholder": "Ask about groundwater… e.g. Is Osian block safe?",
        "thinking": "Finding the official data…", "writing": "JalMitra AI is writing and checking the reply…",
        "lang": "Answer language", "official": "Official groundwater data (from the JalMitra database)",
        "sources": "Sources", "ai_label": "AI reply · checked against official data",
        "ai_note": "Local AI reply, checked automatically. The official figures are authoritative.",
        "year": "Assessment year", "location": "Location", "table": "Data table", "followups": "You could also ask",
        "choose": "Choose one:", "error": "Sorry, something went wrong while answering. Please try again.",
        "unverified_title": "Answer could not be verified", "unavailable_title": "Local AI not available",
        "doc_src": "quoted in the reply", "answered": "Reply in {ms} s", "attempts": "after {n} attempts",
        "empty_history": "Your conversations will appear here.",
        "status_ok": "Local AI connected: {model}", "status_gpu": " · {proc}", "status_bad": "Local AI not available",
        "status_help": "Start the local AI with START_JALMITRA.bat (or open the Ollama app), then reload this page.",
        "Today": "Today", "Yesterday": "Yesterday", "Earlier": "Earlier", "rename": "Rename", "delete": "Delete chat",
        "clear_all": "Clear all history", "clear_sure": "Delete every saved conversation?", "clear_yes": "Yes, delete all",
        "settings": "Settings", "explore": "More pages", "theme_day": "Switch to Day theme",
        "theme_night": "Switch to Night theme", "cleared": "Deleted {n} conversations.",
        "fallback": "District totals instead — {district} (National Compilation 2025)",
        "units_note": "Units: ham = hectare-metre, the water that covers 1 hectare (about 2.5 acres) 1 metre deep "
                      "= 10,000 cubic metres = 1 crore litres. bcm = billion cubic metres = 1 lakh ham. "
                      "Stage of extraction = water drawn ÷ water that can be drawn × 100.",
    },
    "hi": {
        "subtitle": "भारत के किसी भी ब्लॉक, ज़िले या राज्य के भूजल की स्थिति, पुनर्भरण, दोहन और श्रेणी के बारे में पूछें।",
        "data_note": "आधिकारिक 2025 भूजल आंकड़े (CGWB / राज्य GWRA) · उत्तर स्थानीय AI लिखता है, आंकड़ों से जांचे जाते हैं · "
                     "कुछ भी इस कंप्यूटर से बाहर नहीं जाता",
        "examples": "कोई प्रश्न आज़माएँ", "new": "नई बातचीत", "history": "बातचीत",
        "placeholder": "भूजल के बारे में पूछें… जैसे: ओसियां ब्लॉक सुरक्षित है?",
        "thinking": "आधिकारिक आंकड़े खोजे जा रहे हैं…", "writing": "JalMitra AI उत्तर लिख और जांच रहा है…",
        "lang": "उत्तर की भाषा", "official": "आधिकारिक भूजल आंकड़े (JalMitra डेटाबेस से)", "sources": "स्रोत",
        "ai_label": "AI उत्तर · आधिकारिक आंकड़ों से जांचा गया",
        "ai_note": "स्थानीय AI उत्तर, स्वचालित रूप से जांचा गया। आधिकारिक आंकड़े ही प्रामाणिक हैं।",
        "year": "आकलन वर्ष", "location": "स्थान", "table": "आंकड़ा तालिका", "followups": "आप यह भी पूछ सकते हैं",
        "choose": "एक चुनें:", "error": "क्षमा करें, उत्तर देते समय कोई समस्या हुई। कृपया फिर कोशिश करें।",
        "unverified_title": "उत्तर सत्यापित नहीं हो सका", "unavailable_title": "स्थानीय AI उपलब्ध नहीं",
        "doc_src": "उत्तर में उद्धृत", "answered": "{ms} s में उत्तर", "attempts": "{n} प्रयासों के बाद",
        "empty_history": "आपकी बातचीत यहाँ दिखेगी।",
        "status_ok": "स्थानीय AI जुड़ा है: {model}", "status_gpu": " · {proc}", "status_bad": "स्थानीय AI उपलब्ध नहीं",
        "status_help": "START_JALMITRA.bat से स्थानीय AI शुरू करें (या Ollama ऐप खोलें), फिर यह पेज दोबारा लोड करें।",
        "Today": "आज", "Yesterday": "कल", "Earlier": "पहले", "rename": "नाम बदलें", "delete": "बातचीत मिटाएँ",
        "clear_all": "पूरा इतिहास मिटाएँ", "clear_sure": "सभी सहेजी गई बातचीत मिटाएँ?", "clear_yes": "हाँ, सब मिटाएँ",
        "settings": "सेटिंग्स", "explore": "अन्य पेज", "theme_day": "दिन थीम", "theme_night": "रात थीम",
        "cleared": "{n} बातचीत मिटाई गईं।",
        "fallback": "इसके बजाय ज़िले के कुल आंकड़े — {district} (राष्ट्रीय संकलन 2025)",
        "units_note": "इकाइयाँ: ham = हेक्टेयर-मीटर, यानी इतना पानी जो 1 हेक्टेयर (लगभग 2.5 एकड़) ज़मीन को 1 मीटर गहरा "
                      "ढक दे = 10,000 घन मीटर = 1 करोड़ लीटर। bcm = अरब घन मीटर = 1 लाख ham। "
                      "दोहन का स्तर = निकाला गया पानी ÷ निकाला जा सकने वाला पानी × 100।",
    },
}

EXAMPLES = {  # naveen's list (Phase 4); "my district / my block" use the location chosen in Settings or ask
    "en": ["What is the groundwater status of my district?", "Explain the assessment of my block",
           "What does Over-Exploited mean?", "What is the stage of groundwater extraction?",
           "Compare Phagi and Dudu blocks", "Explain annual groundwater recharge in Hindi",
           "मेरे जिले में भूजल की स्थिति क्या है?", "मेरे ब्लॉक को क्रिटिकल क्यों घोषित किया गया है?"],
}
EXAMPLES["hi"] = EXAMPLES["en"]
# the welcome screen shows six of the verified examples as cards (icon, question)
WELCOME = [(":material/location_on:", 1), (":material/menu_book:", 2), (":material/compare_arrows:", 4),
           (":material/water_drop:", 5), (":material/translate:", 6), (":material/help:", 7)]


def _logo_uri():
    try:
        return "data:image/svg+xml;base64," + base64.b64encode((uc.ASSETS / "logo_icon.svg").read_bytes()).decode()
    except OSError:
        return ""


LOGO = _logo_uri()

CSS = """
<style>
/* ---- chat column (~760 px) */
.stMainBlockContainer { max-width: 820px; padding-top: 2.6rem; padding-bottom: 5rem; }
[data-testid="stBottomBlockContainer"] { max-width: 820px; padding-bottom: 1.2rem; }
[data-testid="stBottom"] > div { background: var(--jm-bg); }
/* ---- top bar: small AI status chip + answer language */
.st-key-jm_topbar [data-testid="stHorizontalBlock"] { align-items: center; }
.st-key-jm_status [data-testid="stCaptionContainer"] { display: inline-flex; align-items: center; gap: .3rem;
  font-size: .78rem; padding: .18rem .7rem; border-radius: 999px; border: 1px solid var(--jm-border);
  background: var(--jm-surface); color: var(--jm-muted); width: auto; }
.st-key-jm_status [data-testid="stCaptionContainer"] p { margin: 0; font-size: .78rem; }
.st-key-jm_lang [data-baseweb="select"] > div { border-radius: 999px; min-height: 2rem; font-size: .85rem;
  background: var(--jm-surface); border-color: var(--jm-border); }
/* ---- welcome */
.jm-welcome { text-align: center; margin: 7vh auto 1.4rem; max-width: 640px; }
.jm-welcome img { width: 56px; height: 56px; margin-bottom: .6rem; }
.jm-welcome h1 { font-size: 1.85rem; line-height: 1.25; font-weight: 700; margin: 0 0 .5rem; padding: 0;
  color: var(--jm-text); letter-spacing: -.01em; }
.jm-welcome p { color: var(--jm-muted); font-size: 1.02rem; margin: 0; }
.jm-note { text-align: center; color: var(--jm-muted); font-size: .76rem; margin-top: 1rem; opacity: .9; }
.jm-ex-head { color: var(--jm-muted); font-size: .8rem; font-weight: 600; margin: 1.2rem 0 .1rem .2rem; }
.st-key-jm_examples [data-testid="stHorizontalBlock"] { gap: .6rem; }
.st-key-jm_examples button { width: 100%; min-height: 3.6rem; justify-content: flex-start; align-items: center;
  text-align: left; padding: .7rem .95rem; border-radius: 14px; border: 1px solid var(--jm-border) !important;
  background: var(--jm-bg) !important; color: var(--jm-text) !important; box-shadow: var(--jm-shadow);
  transition: border-color .15s, background .15s; }
.st-key-jm_examples button:hover { border-color: var(--jm-accent) !important; background: var(--jm-hover) !important; }
.st-key-jm_examples button p { white-space: normal; text-align: left; font-size: .92rem; line-height: 1.35; }
.st-key-jm_examples button [data-testid="stIconMaterial"] { color: var(--jm-accent); }
/* ---- chat input */
[data-testid="stChatInput"] { border-radius: 22px !important; border: 1px solid var(--jm-border) !important;
  background: var(--jm-surface) !important; box-shadow: var(--jm-shadow); }
[data-testid="stChatInput"]:focus-within { border-color: var(--jm-accent) !important; }
div[data-testid="stChatInput"] textarea { font-size: 1.02rem; }
/* ---- messages: user right (bubble), assistant left (water-drop avatar) */
[data-testid="stChatMessage"] { background: transparent !important; padding: .35rem 0; gap: .7rem; }
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) { flex-direction: row-reverse; }
[data-testid="stChatMessageAvatarUser"] { display: none; }
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) [data-testid="stChatMessageContent"] {
  flex: 0 1 auto; width: auto; max-width: 82%; margin-left: auto !important; margin-right: 0 !important;
  background: var(--jm-user-bubble);
  color: var(--jm-user-text); padding: .6rem 1rem; border-radius: 18px 18px 4px 18px; }
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) [data-testid="stChatMessageContent"] p {
  margin: 0; color: var(--jm-user-text); }
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) [data-testid="stMarkdownContainer"] {
  margin-bottom: 0; }
[data-testid="stChatMessage"] img[data-testid="stChatMessageAvatarImage"],
[data-testid="stChatMessage"] [data-testid="stChatMessageAvatarCustom"] { width: 30px; height: 30px; }
[data-testid="stChatMessageContent"] { min-width: 0; }
[data-testid="stChatMessage"] [data-testid="stCaptionContainer"] p { font-size: .78rem; color: var(--jm-muted); }
.st-key-jm_topbar { margin-bottom: .6rem; }
.jm4-ai-label { display: inline-flex; align-items: center; gap: .3rem; font-size: .72rem; font-weight: 600;
  padding: .12rem .6rem; border-radius: 999px; color: var(--jm-ok); background: var(--jm-ok-soft);
  margin-bottom: .45rem; }
.jm4-reply { font-size: 1.03rem; line-height: 1.7; color: var(--jm-text); }
.jm4-sec { font-weight: 600; font-size: .74rem; letter-spacing: .05em; margin: 1rem 0 .4rem; color: var(--jm-muted);
  text-transform: uppercase; }
.jm-src { list-style: none; margin: 0 !important; padding: 0 !important; display: flex; flex-direction: column; gap: .3rem; }
.jm-src li { font-size: .84rem; color: var(--jm-muted); padding: .35rem .6rem; border-radius: 10px;
  background: var(--jm-surface); border: 1px solid var(--jm-border); }
.jm-src b { color: var(--jm-accent); font-weight: 600; margin-right: .3rem; }
.jm-meta { display: flex; flex-wrap: wrap; gap: .3rem; margin: .3rem 0 .2rem; }
.st-key-jm_followups button, [class*="st-key-jm_opts"] button { border-radius: 999px !important; font-size: .86rem;
  border: 1px solid var(--jm-border) !important; background: var(--jm-bg) !important; color: var(--jm-text) !important; }
.st-key-jm_followups button:hover, [class*="st-key-jm_opts"] button:hover { border-color: var(--jm-accent) !important;
  color: var(--jm-accent) !important; }
/* ---- notices: could not be verified / AI not available */
[data-testid="stChatMessage"] [data-testid="stAlertContainer"] { border-radius: 12px; }
[data-testid="stChatMessage"] [data-testid="stAlertContentWarning"] p,
[data-testid="stChatMessage"] [data-testid="stAlertContentError"] p { font-size: .95rem; line-height: 1.55; }
/* ---- data cards inside the chat column */
[data-testid="stChatMessage"] .jm-card .jm-v { font-size: 1.05rem; }
[data-testid="stChatMessage"] .jm-card { padding: .6rem .7rem; }
[data-testid="stChatMessage"] [data-testid="stHorizontalBlock"] { gap: .5rem; flex-wrap: wrap; }
[data-testid="stChatMessage"] [data-testid="stColumn"] { min-width: 190px !important; }
[data-testid="stChatMessage"] .jm-chip { white-space: normal; }
@media (max-width: 640px) {
  .stMainBlockContainer { padding-top: 3rem; }
  .jm-welcome { margin-top: 2vh; } .jm-welcome h1 { font-size: 1.35rem; } .jm-welcome p { font-size: .92rem; }
  .jm4-reply { font-size: 1rem; }
  div[data-testid="stChatMessage"] { padding-left: .2rem; padding-right: .2rem; }
  [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) [data-testid="stChatMessageContent"] {
    max-width: 92%; }
}
</style>
"""


# ------------------------------------------------------------------ helpers
def ui():
    lg = st.session_state.get("ui_lang", "en")
    return lg if lg in T else "en"


def t(key):
    return ja.ui_label(T[ui()].get(key) or T["en"][key])


def status_line():
    """Ollama + model connection status (checked at start, refreshed every 15 s)."""
    s = ja.ai_status()
    if s["ok"]:
        return True, t("status_ok").format(model=s["model"]) + (t("status_gpu").format(proc=s["processor"])
                                                              if s.get("processor") else "")
    return False, f"{t('status_bad')}: {s.get('error')}. {t('status_help')}"


def _escape(s):
    return html.escape(s or "", quote=False).replace("\n", "<br>")


# ------------------------------------------------------------------ conversations (kept on disk by chat_store)
def init_history():
    """Load the saved conversations once per session; ?c=<id> in the address reopens that conversation."""
    if not st.session_state.get("_jm_history_loaded"):
        st.session_state["_jm_history_loaded"] = True
        convs = []
        try:
            stored = chat_store.load_conversations()
        except OSError:
            stored = []
        for d in stored:
            convs.append({"id": d["id"], "title": d.get("title") or "", "messages": d.get("messages") or [],
                          "state": chat_store.restore_state(d.get("state"), engine.new_state),
                          "created_ts": d.get("created"), "updated": d.get("updated") or 0})
        existing = st.session_state.setdefault("v4_convs", [])
        known = {c["id"] for c in existing}
        existing.extend(c for c in convs if c["id"] not in known)
        cid = st.query_params.get("c")
        if cid and any(c["id"] == cid for c in existing):
            st.session_state.v4_active = cid
        elif not any(c["id"] == st.session_state.get("v4_active") and not c["messages"] for c in existing):
            _new_conv()                                  # a fresh start opens a new, empty chat
    return _conversations()


def _conversations():
    st.session_state.setdefault("v4_convs", [])
    if not st.session_state.v4_convs:
        _new_conv()
    return st.session_state.v4_convs


def _new_conv():
    home = st.session_state.engine_state.home if st.session_state.get("engine_state") else None
    state = engine.new_state()
    state.set_home(home)
    now = time.time()
    st.session_state.setdefault("v4_convs", []).insert(0, {"id": uuid.uuid4().hex[:12], "title": "", "messages": [],
                                                           "state": state, "created_ts": now, "updated": now})
    st.session_state.v4_active = st.session_state.v4_convs[0]["id"]


def new_conversation(go_chat=False):
    """Start a new conversation (an empty current one is reused)."""
    if go_chat:
        st.session_state.goto = "chat"
    cur = current()
    if cur and not cur["messages"]:
        return
    _new_conv()


def current():
    convs = _conversations()
    for c in convs:
        if c["id"] == st.session_state.get("v4_active"):
            return c
    st.session_state.v4_active = convs[0]["id"]
    return convs[0]


def select_conversation(cid, go_chat=False):
    st.session_state.v4_active = cid
    if go_chat:
        st.session_state.goto = "chat"


def save(conv):
    """Write the conversation to the local history (never fails the page)."""
    conv["updated"] = time.time()
    try:
        chat_store.save_conversation(conv)
    except (OSError, ValueError, TypeError):
        pass


def delete_conversation(cid):
    chat_store.delete_conversation(cid)
    st.session_state.v4_convs = [c for c in _conversations() if c["id"] != cid]
    if st.session_state.get("v4_active") == cid or not st.session_state.v4_convs:
        empty = next((c for c in st.session_state.v4_convs if not c["messages"]), None)
        if empty:
            st.session_state.v4_active = empty["id"]
        else:
            _new_conv()


def rename_conversation(cid):
    title = (st.session_state.get(f"jm_ren_{cid}") or "").strip()
    for c in _conversations():
        if c["id"] == cid and title:
            c["title"] = title[:80]
            save(c)


def clear_all():
    """Delete every saved conversation (settings are kept). Returns the number deleted."""
    n = chat_store.clear_conversations()
    st.session_state.v4_convs = []
    _new_conv()
    st.session_state["_jm_toast"] = t("cleared").format(n=n)
    return n


def _lang_choice():
    return st.session_state.get("answer_lang", L.AUTO)


def _set_lang():
    st.session_state.answer_lang = st.session_state.v4_lang_w
    st.session_state.w_answer_lang = st.session_state.v4_lang_w      # keep the settings selector in step
    try:
        chat_store.save_settings({"answer_lang": st.session_state.answer_lang})
    except OSError:
        pass


def _history(conv, upto):
    """Conversation context for the model: user turns and VERIFIED replies only."""
    h = []
    for m in conv["messages"][:upto]:
        if m["role"] == "user":
            h.append({"role": "user", "content": m["text"]})
        elif (m.get("ai") or {}).get("status") == "verified":
            h.append({"role": "assistant", "content": m["ai"]["answer"]})
    return h


# ------------------------------------------------------------------ answering (two stages)
def stage_data(question, conv):
    """Stage 1 (fast): internal rule engine run -> official figures to show at once. No user-facing text."""
    state = conv["state"]
    home = st.session_state.engine_state.home if st.session_state.get("engine_state") else None
    state.set_home(home)
    r = ja.rule_for(ja.normalize_states(question)[0], state, _lang_choice(), st.session_state.get("style", "farmer"),
                    st.session_state.get("detail", "standard"))        # spellings + own-area questions (Phase 6 fix)
    msg = {"role": "assistant", "question": question, "lang": r.get("lang") or "en", "intent": r.get("intent"),
           "table": r.get("table") or [], "sources": r.get("sources") or [], "year": r.get("year"),
           "warnings": r.get("warnings") or [], "options": r.get("options") or [] if r.get("clarify") else [],
           "followups": r.get("followups") or [], "chart": r.get("chart"), "places": r.get("places") or [],
           "records": [], "areas": [], "ai": None, "ai_pending": True, "_rule": r}
    if r.get("intent") == "domain":                     # coming soon: no figures at all
        msg.update(table=[], sources=[], options=[], followups=[], chart=None, places=[])
    else:
        for b in (r.get("result") or {}).get("blocks") or []:
            if b.get("kind") == "unit" and len(msg["records"]) < 3:
                msg["records"].append(b["record"])
            elif b.get("kind") == "area" and len(msg["areas"]) < 2:
                msg["areas"].append(b["place"])
        # no unit figures in the state report: the district totals (National Compilation 2025) as a labelled fallback
        msg["fallback"] = []
        for g in (r.get("state_report_gaps") or [])[:1]:
            place = uc.place_for(g["state"], g["district"])
            if place and not any(a.get("type") == "district" and a.get("district") == g["district"]
                                 for a in msg["areas"]):
                msg["fallback"].append({"place": place, "unit": g["unit"], "reason": g["reason"]})
    return msg


def stage_ai(msg, conv, index):
    """Stage 2: the local AI writes and the checks verify the reply. Never raises."""
    t0 = time.perf_counter()
    try:
        out = ja.respond(msg["question"], conv["state"], _lang_choice(), st.session_state.get("style", "farmer"),
                         st.session_state.get("detail", "standard"), history=_history(conv, index),
                         rule=msg["_rule"])
        msg["ai"] = {k: out.get(k) for k in ("status", "answer", "kind", "lang", "citations", "attempts", "reasons",
                                            "error", "timings", "cache", "model")}
        # clarification buttons only when the AI step also treats the question as a place clarification
        msg["options"] = (out.get("options") or msg["options"]) if out.get("kind") == "clarify" else []
        if out.get("kind") == "general" and ja.is_concept_question(msg["question"]):
            # a concept question (water cycle, aquifer, ...) never shows a place's data cards (fix, 24 Nov)
            msg.update(table=[], records=[], areas=[], sources=[], chart=None, places=[], warnings=[], fallback=[])
        if out.get("kind") == "coverage" and not (out.get("rule") or {}).get("places"):
            msg.update(table=[], sources=[], chart=None, followups=[])   # e.g. a top-n table is not coverage data
    except Exception as e:                               # error state; the app never crashes
        msg["ai"] = {"status": "error", "answer": "", "error": f"{type(e).__name__}: {e}"}
    msg["ai_pending"] = False
    msg.pop("_rule", None)
    msg["seconds"] = round(time.perf_counter() - t0, 1)


def ask(question):
    question = (question or "").strip()
    if not question:
        return
    conv = current()
    conv["messages"].append({"role": "user", "text": question})
    if not conv["title"]:
        conv["title"] = question[:48] + ("…" if len(question) > 48 else "")
    save(conv)
    st.session_state.v4_pending = question


def _answer_pending(conv):
    q = st.session_state.pop("v4_pending", None)
    if not q:
        return
    with st.chat_message("assistant", avatar=str(uc.ASSETS / "logo_icon.svg")):
        with st.spinner(t("thinking")):
            try:
                msg = stage_data(q, conv)
            except Exception as problem:
                msg = {"role": "assistant", "question": q, "fatal": f"{type(problem).__name__}: {problem}"}
    conv["messages"].append(msg)
    if msg.get("fatal"):
        save(conv)


# ------------------------------------------------------------------ rendering
def _section(label):
    st.html(f'<div class="jm4-sec">{label}</div>')


def show_assistant(msg, index, last):
    with st.chat_message("assistant", avatar=str(uc.ASSETS / "logo_icon.svg")):
        if msg.get("fatal"):
            st.error(t("error"), icon=":material/error:")
            st.caption(msg["fatal"])
            return
        lang = msg.get("lang", "en")
        # ---- the AI reply (written by the local model, checked)
        if msg.get("ai_pending"):
            conv = current()
            with st.spinner(t("writing")):
                stage_ai(msg, conv, index)
            save(conv)
            st.rerun()
        ai = msg.get("ai") or {}
        status = ai.get("status")
        if status == "verified":
            st.html(f'<div class="jm4-ai-label">✓ {t("ai_label")}</div>')
            st.markdown(f'<div class="jm4-reply">{_escape(ai.get("answer"))}</div>', unsafe_allow_html=True)
        elif status == "unverified":
            st.warning(f"**{t('unverified_title')}** — {ai.get('answer')}", icon=":material/gpp_maybe:")
        elif status in ("ai_unavailable", "error"):
            st.error(f"**{t('unavailable_title')}** — {ai.get('answer') or ai.get('error')}",
                     icon=":material/cloud_off:")
        # ---- clarification choices: options come from the place index (entity_resolver), never from the AI
        if msg.get("options") and last:
            st.caption(t("choose"))
            with st.container(key=f"jm_opts_{index}"):
                cols = st.columns(min(len(msg["options"]), 2))
                for i, opt in enumerate(msg["options"], 1):
                    cols[(i - 1) % len(cols)].button(f"{i}. {opt}", key=f"v4opt_{index}_{i}", on_click=ask,
                                                     args=(str(i),), width="stretch")
        # ---- official data, straight from the database (never replaced by AI numbers)
        has_data = bool(msg.get("table"))
        if has_data or msg.get("records") or msg.get("areas"):
            _section(t("official"))
            for w in msg.get("warnings") or []:
                st.warning(w, icon=":material/warning:")
            for rec in msg.get("records") or []:
                uc.unit_cards(rec, ui(), lang)
            for place in msg.get("areas") or []:
                uc.area_cards(place, ui(), lang)
            for fb in msg.get("fallback") or []:
                st.html(f'<div class="jm4-sec">{_escape(t("fallback").format(district=uc.place_title(fb["place"], lang)))}'
                        "</div>")
                uc.area_cards(fb["place"], ui(), lang)
            meta = []
            if msg.get("year"):
                meta.append(f"{t('year')}: {msg['year']}")
            if msg.get("places"):
                meta.append(f"{t('location')}: " + "; ".join(uc.place_title(p, lang) for p in msg["places"][:4]))
            if meta:
                st.caption(" · ".join(meta))
            st.caption(t("units_note"))          # ham / bcm in plain words (naveen, 25 Nov)
            if has_data:
                with st.expander(t("table"), icon=":material/table_chart:", expanded=False):
                    st.dataframe(pd.DataFrame(msg["table"]), hide_index=True)
                    st.download_button("CSV", uc.csv_bytes(msg["table"]), f"jalmitra_{index}.csv", "text/csv",
                                       key=f"v4dl_{index}", icon=":material/download:")
        if msg.get("chart"):
            uc.show_chart(msg["chart"], ui())
        # ---- sources: database records + documents quoted by the reply
        cites = ai.get("citations") if status == "verified" else []
        if msg.get("sources") or cites:
            src = {}
            for s in msg.get("sources") or []:
                src.setdefault((s.get("source_id"), s.get("title")), set()).add(str(s.get("page")))
            items = [f"<li><b>{_escape(str(sid))}</b>{_escape(str(title))}, p. "
                     f"{', '.join(sorted(pages, key=lambda x: (len(x), x)))}</li>" for (sid, title), pages in src.items()]
            items += [f"<li><b>[{i}]</b>{_escape(str(c.get('title')))} ({_escape(str(c.get('source_id')))}), "
                      f"PDF page {c.get('page')} — <i>{t('doc_src')}</i></li>" for i, c in enumerate(cites or [], 1)]
            st.html(f'<div class="jm4-sec">{t("sources")}</div><ul class="jm-src">{"".join(items)}</ul>')
        # ---- follow-ups
        if msg.get("followups") and last and status == "verified":
            st.caption(t("followups"))
            with st.container(key="jm_followups"):
                cols = st.columns(min(3, len(msg["followups"])))
                for i, fu in enumerate(msg["followups"][:3]):
                    cols[i].button(fu, key=f"v4fu_{index}_{i}", on_click=ask, args=(fu,), width="stretch")
        foot = []
        if status == "verified":
            foot.append(t("ai_note"))
        if msg.get("seconds") is not None:
            cap = t("answered").format(ms=msg["seconds"])
            if (ai.get("attempts") or 1) > 1:
                cap += " · " + t("attempts").format(n=ai["attempts"])
            foot.append(cap)
        if foot:
            st.caption(" · ".join(foot))


def welcome(conv):
    st.html(f'<div class="jm-welcome">' + (f'<img src="{LOGO}" alt="">' if LOGO else "") +
            f'<h1>{TITLE}</h1><p>{t("subtitle")}</p></div>')


def welcome_examples():
    ex = EXAMPLES.get(ui(), EXAMPLES["en"])
    st.html(f'<div class="jm-ex-head">{t("examples")}</div>')
    with st.container(key="jm_examples"):
        cols = st.columns(2)
        for n, (icon, i) in enumerate(WELCOME):
            cols[n % 2].button(ex[i], key=f"v4ex_{i}", on_click=ask, args=(ex[i],), icon=icon, width="stretch")
    st.html(f'<div class="jm-note">{t("data_note")}</div>')


# ------------------------------------------------------------------ sidebar
def sidebar_history(on_chat_page=True):
    """'New chat' and the saved conversations, grouped Today / Yesterday / Earlier (most recent first)."""
    go = not on_chat_page
    with st.container(key="jm_newchat"):
        st.button(t("new"), key="v4_new_side", on_click=new_conversation, args=(go,), icon=":material/edit_square:",
                  width="stretch")
    convs = sorted([c for c in _conversations() if c["messages"]], key=lambda c: c.get("updated") or 0, reverse=True)
    if not convs:
        st.caption(t("empty_history"))
        return
    now = time.time()
    group = None
    active = st.session_state.get("v4_active")
    for c in convs[:60]:
        g = chat_store.group_label(c.get("updated") or now, now)
        if g != group:
            group = g
            st.html(f'<div class="jm-side-group">{t(g)}</div>')
        on = c["id"] == active and on_chat_page
        with st.container(key=("jm_histon_" if on else "jm_hist_") + c["id"]):
            a, b = st.columns([0.84, 0.16], vertical_alignment="center")
            a.button(c["title"] or "…", key=f"v4conv_{c['id']}", on_click=select_conversation, args=(c["id"], go),
                     width="stretch", help=c["title"] or None)
            with b.popover("", icon=":material/more_horiz:"):
                st.text_input(t("rename"), value=c["title"], key=f"jm_ren_{c['id']}", on_change=rename_conversation,
                              args=(c["id"],), max_chars=80)
                st.button(t("delete"), key=f"jm_del_{c['id']}", on_click=delete_conversation, args=(c["id"],),
                          icon=":material/delete:", width="stretch")
    with st.container(key="jm_clear"):
        with st.popover(t("clear_all"), icon=":material/delete_sweep:", width="stretch"):
            st.caption(t("clear_sure"))
            st.button(t("clear_yes"), key="jm_clear_side", on_click=clear_all, type="primary", width="stretch")


# ------------------------------------------------------------------ page
def page_chat():
    st.html(CSS)
    qp = st.query_params                                 # ?q=<question>&lang=<code> opens the chat with a question
    q_param = None
    if qp.get("q") and not st.session_state.get("v4_qp_done"):
        st.session_state.v4_qp_done = True
        if qp.get("lang") in dict(L.language_options()):
            st.session_state.answer_lang = qp.get("lang")
        q_param = qp.get("q")
    conv = current()
    if q_param:
        ask(q_param)
    pending = st.session_state.pop("pending_q", None)    # questions sent from the overview page
    if pending:
        ask(pending)
    # keep the open conversation in the address (?c=<id>) so a reload (e.g. a theme switch) reopens it
    if conv["messages"]:
        if qp.get("c") != conv["id"]:
            qp["c"] = conv["id"]
    elif "c" in qp:
        del qp["c"]
    ok, line = status_line()
    with st.container(key="jm_topbar"):
        left, right = st.columns([3.2, 1.3], vertical_alignment="center")
        with left.container(key="jm_status"):
            short = t("status_ok").format(model=ja.ai_status().get("model")) if ok else t("status_bad")
            st.caption(("🟢 " if ok else "🔴 ") + short, help=line)     # details (GPU, how to start) on hover
        opts = dict(L.language_options())
        st.session_state.v4_lang_w = _lang_choice() if _lang_choice() in opts else L.AUTO
        with right.container(key="jm_lang"):
            st.selectbox("🌐 " + t("lang"), list(opts), key="v4_lang_w", format_func=lambda c: opts[c],
                         on_change=_set_lang, label_visibility="collapsed")
    if not conv["messages"] and not st.session_state.get("v4_pending"):
        welcome(conv)
        # Phase 6 mobile fix: on the welcome screen the input sits inline below the greeting instead of the
        # bottom-pinned chat bar, so Streamlit's "stick to bottom" does not scroll the title out of view on phones.
        question = st.container().chat_input(t("placeholder"), key="v4_input_welcome")
        welcome_examples()
    else:
        question = st.chat_input(t("placeholder"), key="v4_input")
    if question:
        ask(question)
        st.rerun()
    msgs = conv["messages"]
    for i, m in enumerate(msgs):
        if m["role"] == "user":
            with st.chat_message("user"):
                st.markdown(m["text"])
        else:
            show_assistant(m, i, last=(i == len(msgs) - 1 and not st.session_state.get("v4_pending")))
    if st.session_state.get("v4_pending"):
        _answer_pending(conv)
        st.rerun()

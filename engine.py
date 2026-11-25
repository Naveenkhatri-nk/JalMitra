"""
engine.py - JalMitra 2.0 question answering pipeline (offline, no AI model).

  question
    -> security.clean_question          (length and empty checks)
    -> language.detect_language          (rules)
    -> intent_parser.parse               (keywords, regex, entity_resolver)
    -> conversation_state                (follow-ups, clarifications)
    -> retrieval.execute                 (read-only parameterised SELECTs)
    -> response_builder.build            (fixed multilingual templates)

No network call is made. Each answer carries its own measured time.

JalMitra 3.0 (Phase 1) adds:
  * answer styles  farmer | official | student      (mode=)
  * answer detail  short | standard | detailed       (detail=)
  * memory of the domain (groundwater, soil, crop, land, irrigation), the chosen
    location ("my block"), the categories of the last answer ("What does it mean?")
  * "Data unavailable" answers for soil, crop, land and irrigation questions
  * a question back when "its" could mean more than one earlier place
"""

import os
import re
import time

import app_info
import conversation
import database as db
import entity_resolver as er
import intent_parser as ip
import language as L
import response_builder as rb
import retrieval
from conversation_state import ConversationState
from security import clean_question

DEIXIS = ["its", "it's", "iska", "iski", "iske", "uska", "uski", "this block", "this unit", "this district",
          "this place", "same place", "इसका", "इसकी", "इसके", "उसका", "उसकी", "याचा", "याची", "त्याचा", "त्याची",
          "ਇਸ ਦਾ", "ਇਸਦਾ", "ਇਸ ਦੀ", "इणरो", "इणरी", "उणरो"]
CONTEXT_INTENTS = {"status", "numeric", "sources", "quality", "data_availability", "area_search", "year_compare",
                   "domain"}
THERE_WORDS = ["wahan", "wahaan", "vahan", "vahaan", "वहाँ", "वहां", "वहा", "तिथे", "तेथे", "ਉੱਥੇ", "ਉਥੇ", "उठै", "उठे"]
DISTRICT_PLURAL = ["districts", "both district", "both the district", "zilon", "jilon", "ज़िलों", "जिलों", "जिल्ह्यांची",
                   "जिल्हे", "ਜ਼ਿਲ੍ਹਿਆਂ", "जिलां"]
STYLES = ("farmer", "official", "student")
DETAILS = ("short", "standard", "detailed")
MAX_OPTIONS = 10
AREA_SCOPE_INTENTS = {"top_n", "top_areas", "list_category"}


def new_state():
    return ConversationState()


def answer(question, state, lang_choice=L.AUTO, mode="farmer", detail="standard"):
    """Answer one question. Returns a dict with text, warnings, table, sources, chart, timing_ms, ...

    mode   = answer style: farmer (simple), official (figures, limits), student (concepts, reasoning)
    detail = short, standard or detailed
    """
    t0 = time.perf_counter()
    state.style = mode if mode in STYLES else "farmer"
    state.detail = detail if detail in DETAILS else "standard"
    try:
        q = clean_question(question)
    except ValueError as problem:
        return _final(rb.build_message("rephrase", state.last_lang), state.last_lang, "invalid", [], t0, str(problem))
    lang = L.resolve_language(lang_choice, q)
    if lang_choice in (L.AUTO, None) and not re.search(r"[A-Za-zऀ-੿]{2,}", q):
        lang = state.last_lang                     # a reply like "1" keeps the conversation language
    elif lang_choice in (L.AUTO, None) and state.pending and len(q.split()) <= 2 and lang == "en":
        lang = state.last_lang
    if lang_choice in (L.AUTO, None) and lang == "en" and conversation.smalltalk(q) and conversation.is_hinglish(q):
        lang = "hinglish"                          # "shukriya", "badhiya bhai": reply in Hinglish
    elif lang_choice in (L.AUTO, None) and lang == "hi" and conversation.smalltalk(q) and conversation.lang_hint(q):
        lang = conversation.lang_hint(q)           # "छान" is Marathi, "घणो चोखो" Rajasthani
    meta = _meta_request(q, state)
    if meta:
        if meta.get("lang"):
            lang = meta["lang"]
        if meta.get("detail"):
            state.detail = meta["detail"]
    state.last_lang = lang
    try:
        if not meta:
            state.last_app = None
        out = _rerun_last(meta, state, lang, mode, t0) if meta else _answer(q, state, lang, mode, t0)
    except db.DatabaseNotReadyError:
        out = _final(rb.build_message("no_data", lang), lang, "no_data", [], t0)
    out["memory"] = state.summary()
    out["style"], out["detail"] = state.style, state.detail
    if _llm_on():
        out = _llm_enhance(question, out, state)
    return out


def _llm_on():
    """JalMitra 4.0 (Phase 3) feature flag: off unless JALMITRA_LLM_PROVIDER names a real provider."""
    return os.environ.get("JALMITRA_LLM_PROVIDER", "none").strip().lower() not in ("", "none")


def _llm_enhance(question, out, state):
    """Optional verified AI explanation (llm_compose.py). Any problem -> the rule answer unchanged."""
    try:
        import llm_compose
        return llm_compose.enhance(question, out, state)
    except Exception:
        return out


def _answer(q, state, lang, mode, t0):
    if state.pending:
        choice = state.resolve_pending(q)
        pend = state.pending
        state.pending = None
        if choice is not None:
            return _resolve_queue(pend["req"], pend["resolved"] + [choice], pend["queue"], pend["notes"],
                                  state, lang, mode, t0)

    req = ip.parse(q, context_has_places=bool(state.last_places))
    intent = req["intent"]
    if intent == "blocked":
        key = "no_estimate" if req.get("reason") == "fabricate" else "blocked"
        return _final(rb.build_message(key, lang), lang, "blocked", [], t0)
    if intent in app_info.APP_INTENTS:
        # about JalMitra itself: fixed text, no SQL, no place lookup; the last data question stays in memory
        state.last_app = intent
        state.last_intent = intent
        return _final(rb.build_message(app_info.TEMPLATE[intent], lang), lang, intent, [], t0)
    if intent in ("smalltalk", "scope", "off_topic", "unclear"):
        # everyday conversation (conversation.py): no data lookup; the wording rotates between replies
        if intent == "unclear":
            topics = conversation.topics_in(q)
            if req.get("category") and "groundwater" not in topics:
                topics.insert(0, "groundwater")
            req = {**req, "cue_topics": topics}
        seq = getattr(state, "reply_seq", 0)
        state.reply_seq = seq + 1
        out = conversation.build(req, lang, seq, L.t("rephrase", lang), L.t("off_topic", lang))
        return _final(out, lang, intent, [], t0)
    if intent == "help":
        return _final(rb.build_message(intent, lang), lang, intent, [], t0)

    mentions = req["mentions"]
    text = ip._norm_text(q)
    refers_back = _refers_back(text)

    # follow-up: "What about Jodhpur?" keeps the previous kind of question
    if mentions and req.get("followup") == "new_place" and state.last_req and \
            state.last_req["intent"] in CONTEXT_INTENTS:
        req = {**req, **{k: v for k, v in state.last_req.items()
                         if k in ("intent", "category", "n", "order", "level", "domain")}}
        intent = req["intent"]

    if not mentions:
        early = _context_answer(req, q, text, refers_back, state, lang, mode, t0)
        if early is not None:
            return early

    if not mentions:
        named = req.get("unknown") or [w for w in req["leftovers"] if w[:1].isupper() or re.search(r"[ऀ-੿]", w)]
        if named and intent in retrieval.PLACE_INTENTS | {"top_n", "list_category", "sources", "quality"}:
            return _not_found(" ".join(named[:3]), req, state, lang, t0)
        if intent == "compare":
            two = state.recent_two()
            if len(two) < 2:
                return _final(rb.build_message("compare_need_two", lang), lang, "compare", [], t0)
            pre = []
            if ip._has(text, DISTRICT_PLURAL):
                # "Compare both districts": a block in the memory is compared through its district (said in the answer)
                lifted = []
                for p in two:
                    d = er.district_of(p)
                    if d is not None and p["type"] == "unit":
                        pre.append(L.t("lifted_district", lang, unit=rb.show_name(p["name"]),
                                       district=rb.show_name(d["district"])))
                    lifted.append(d or p)
                if er.place_key(lifted[0]) != er.place_key(lifted[1]):
                    two = lifted
                else:
                    pre = []
            return _run({**req, "places": two}, [], state, lang, mode, t0, pre=pre)
        if intent in retrieval.PLACE_INTENTS or (refers_back and intent in CONTEXT_INTENTS):
            if not state.last_places:
                return _final(rb.build_message("need_place", lang), lang, intent, [], t0)
            if refers_back and len(state.last_places) > 1 and intent in ("status", "numeric"):
                return _ask_which(req, state, lang, t0)
            return _run({**req, "places": state.last_places}, [], state, lang, mode, t0)
        return _run({**req, "places": []}, [], state, lang, mode, t0)

    if intent in AREA_SCOPE_INTENTS:
        # "blocks in Barmer": the place is an area filter, so its district/state reading is used when one exists
        for m in mentions:
            areas = [c for c in m["candidates"] if c["type"] in ("district", "state")]
            if areas and m["type_hint"] != "unit":
                m["candidates"] = areas
    if intent == "compare" and len(mentions) == 1 and state.last_places:
        prev = state.last_places[-1]
        if not any(er.place_key(c) == er.place_key(prev) for c in mentions[0]["candidates"]):
            return _resolve_queue(req, [prev], mentions, [], state, lang, mode, t0)
    return _resolve_queue(req, [], mentions, [], state, lang, mode, t0)


LANG_NAMES = {"hi": ["hindi", "हिंदी", "हिन्दी", "ਹਿੰਦੀ"], "en": ["english", "अंग्रेज़ी", "अंग्रेजी", "इंग्रजी", "ਅੰਗਰੇਜ਼ੀ"],
              "mr": ["marathi", "मराठी"], "pa": ["punjabi", "पंजाबी", "ਪੰਜਾਬੀ"],
              "raj": ["rajasthani", "marwari", "राजस्थानी", "मारवाड़ी"], "hinglish": ["hinglish"]}
META_VERBS = ["explain", "translate", "tell", "say", "repeat", "answer", "give", "show", "write", "in", "into", "to",
              "mein", "me", "में", "मध्ये", "ਵਿੱਚ", "batao", "bataiye", "samjhao", "samjhaiye", "बताओ", "बताइए", "बताएं",
              "समझाओ", "समझाइए", "सांगा", "ਦੱਸੋ", "this", "it", "that", "please", "now", "again", "answer", "यह", "इसे"]
MORE_WORDS = ["explain more", "more detail", "more details", "give details", "give detail", "in detail", "tell me more",
              "elaborate", "details please", "detail me", "vistar se", "vistar mein", "aur batao", "aur bataiye",
              "विस्तार से", "विस्तार में", "और बताओ", "और बताइए", "सविस्तर", "ਵਿਸਥਾਰ", "और बतावो"]
WHY_ONLY = re.compile(r"^\s*(why|why so|why is that|kyun|kyon|kyu|क्यों|क्यूँ|का|ਕਿਉਂ|क्यूं)\s*[?!.।]*\s*$", re.I)
SOURCE_ONLY = ["show the source", "show source", "show sources", "source please", "what is the source", "sources?",
               "स्रोत दिखाओ", "स्रोत बताओ", "source batao", "source dikhao"]


def _meta_request(q, state):
    """'Explain in Hindi', 'Translate this', 'Explain more', 'Why?', 'Show the source' about the last answer."""
    text = ip._norm_text(q)
    words = text.split()
    if len(words) > 7:
        return None
    for code, names in LANG_NAMES.items():
        if ip._has(text, names) and all(w in META_VERBS or any(w == n.lower() for n in names) for w in words) \
                and len(words) >= 2:
            return {"kind": "lang", "lang": code}
    if ip._has(text, ["translate", "translate this", "अनुवाद"]) and len(words) <= 3:
        return {"kind": "lang", "lang": "hi" if state.last_lang == "en" else "en"}
    if ip._has(text, MORE_WORDS):
        return {"kind": "more", "detail": "detailed"}
    if WHY_ONLY.match(q):
        return {"kind": "why"}
    if ip._has(text, SOURCE_ONLY) and state.last_req and state.last_req.get("knowledge"):
        return {"kind": "more", "detail": "detailed"}
    return None


def _rerun_last(meta, state, lang, mode, t0):
    """Answer the previous request again in another language or in detail (nothing new is looked up)."""
    if meta["kind"] == "why":
        req = ip.parse("What does it mean?")
        out = _context_answer(req, "What does it mean?", ip._norm_text("What does it mean?"), False, state, lang, mode, t0)
        return out or _final(rb.build_message("rephrase", lang), lang, "unclear", [], t0)
    if state.pending and meta["kind"] == "lang":
        # the last answer was a question back: ask it again in the new language
        pend = state.pending
        out = rb.build_clarify(pend["name"], pend["options"], lang, head_key=None if pend["name"] else "which_place")
        return _final(out, lang, pend["req"]["intent"], [], t0, clarify=True)
    if getattr(state, "last_app", None) and meta["kind"] in ("lang", "more"):
        # "Explain in Hindi" after "What is JalMitra?": the same fixed text in the new language
        intent = state.last_app
        key = "app_features" if (meta["kind"] == "more" and intent != "FEATURE_LIST") else app_info.TEMPLATE[intent]
        out = _final(rb.build_message(key, lang), lang, intent, [], t0)
        if meta["kind"] == "lang":
            out["text"] = L.t("k_meta_lang", lang, language=L.LANGUAGES[lang]["native_name"]) + "\n\n" + out["text"]
        return out
    if not state.last_req:
        return _final(rb.build_message("k_meta_nothing", lang), lang, "meta", [], t0)
    state.pending = None
    req = {**state.last_req, "places": list(state.last_places), "mentions": []}
    out = _run(req, [], state, lang, mode, t0)
    head = L.t("k_meta_lang", lang, language=L.LANGUAGES[lang]["native_name"]) if meta["kind"] == "lang" \
        else L.t("k_meta_more", lang)
    out["text"] = head + "\n\n" + out["text"]
    return out


def _refers_back(text):
    """'its', 'this block', 'there', 'wahan' ... (but not 'is there data?')."""
    if ip._has(text, DEIXIS) or ip._has(text, THERE_WORDS):
        return True
    return bool(re.search(r"(?<![\w])there(?![\w])", text)) and \
        not re.search(r"\b(is|are|was|were)\s+there\b|\bthere\s+(is|are|was|were)\b", text)


def _context_answer(req, q, text, refers_back, state, lang, mode, t0):
    """Questions without a place name that are answered from memory (JalMitra 3.0). None = not handled here."""
    intent = req["intent"]
    if req.get("self_ref") and intent not in ("explain_category", "compare"):
        # "my block", "here", "mera ilaka": only the location chosen in the app is used, never an earlier answer
        if state.home:
            return _run({**req, "places": [state.home]}, [], state, lang, mode, t0)
        if intent == "domain":
            return _run({**req, "places": []}, [], state, lang, mode, t0)
        return _final(rb.build_message("need_home", lang), lang, intent, [], t0)
    if intent == "explain_category" and req.get("category") and refers_back and state.last_places \
            and not ip._has(text, ip.EXPLAIN_STRICT):
        # "Is groundwater safe there?" asks about the remembered place, not for a definition
        req = {**req, "intent": "status"}
        if len(state.last_places) > 1:
            return _ask_which(req, state, lang, t0)
        return _run({**req, "places": state.last_places}, [], state, lang, mode, t0)
    if intent == "explain_category" and req.get("what") == "context":
        if state.last_categories:
            return _run({**req, "places": [], "context_categories": state.last_categories,
                         "context_findings": state.last_findings}, [], state, lang, mode, t0)
        return _run({**req, "places": [], "what": None}, [], state, lang, mode, t0)
    if intent == "domain":
        follow = refers_back or ip._has(text, ip.KW["followup_new_place"] + ip.KW["both"])
        if follow and state.last_places:
            if len(state.last_places) > 1 and not ip._has(text, ip.KW["both"]):
                return _ask_which(req, state, lang, t0)
            return _run({**req, "places": state.last_places}, [], state, lang, mode, t0)
        return _run({**req, "places": []}, [], state, lang, mode, t0)
    return None


def _ask_which(req, state, lang, t0):
    """'its' after an answer about two places: ask which one (nothing is guessed)."""
    options = list(state.last_places)[:MAX_OPTIONS]
    state.set_pending(req, [], [], [], options, "")
    out = rb.build_clarify("", options, lang, head_key="which_place")
    return _final(out, lang, req["intent"], [], t0, clarify=True)


def _resolve_queue(req, resolved, queue, notes, state, lang, mode, t0):
    """Resolve place mentions one by one; ask when a mention fits several places."""
    queue = list(queue)
    while queue:
        m = queue.pop(0)
        cands = m["candidates"]
        if len(cands) == 1:
            resolved.append(cands[0])
            if m["match"] == "phonetic":
                notes = notes + [(m["text"], rb.place_label(cands[0], lang))]
            continue
        options = sorted(cands, key=lambda c: ({"state": 0, "district": 1, "unit": 2}[c["type"]], c["state"],
                                               c.get("district") or "", c["name"]))[:MAX_OPTIONS]
        state.set_pending(req, resolved, queue, notes, options, m["text"])
        return _final(rb.build_clarify(m["text"], options, lang), lang, req["intent"], [], t0, clarify=True)
    return _run({**req, "places": resolved}, notes, state, lang, mode, t0)


def _not_found(name, req, state, lang, t0):
    options = er.suggest(name)[:MAX_OPTIONS]
    if options:
        state.set_pending(req, [], [], [], options, name)
        return _final(rb.build_clarify(name, options, lang, not_found=True), lang, req["intent"], [], t0, clarify=True)
    out = rb.build_message("not_found", lang, name=name)
    out["text"] += " " + L.t("need_place", lang)
    out["status"] = "not_found"
    return _final(out, lang, req["intent"], [], t0)


def _run(req, notes, state, lang, mode, t0, pre=()):
    pre = list(pre)
    if req["intent"] == "compare" and state.domain not in (None, "groundwater"):
        pre.append(L.t("compare_domain_note", lang, domain=L.t("dom_" + state.domain, lang)))
    if req["intent"] == "domain":
        req = {**req, "soil_report": state.soil_report}
    result = retrieval.execute(req)
    state.remember(req, req["places"])
    out = rb.build(result, lang, mode, notes, history_len=len(state.history), detail=state.detail, pre=pre)
    state.note_answer(req["intent"], result, out["sources"])
    return _final(out, lang, req["intent"], req["places"], t0, result=result)


def _final(out, lang, intent, places, t0, error=None, clarify=False, result=None):
    out = dict(out)
    out.update({"lang": lang, "intent": intent, "places": places, "clarify": clarify, "error": error,
                "result": result, "timing_ms": round((time.perf_counter() - t0) * 1000, 2)})
    out.setdefault("options", [])
    return out


def answer_places(intent, places, lang="en", mode="farmer", detail="standard", state=None):
    """Answer for places chosen in the app (selectors, not typed text): 'status', 'numeric' or 'compare'.
    Same retrieval and templates as typed questions; nothing is parsed or guessed."""
    t0 = time.perf_counter()
    state = state or ConversationState()
    state.style = mode if mode in STYLES else "farmer"
    state.detail = detail if detail in DETAILS else "standard"
    state.last_lang = lang
    req = {"intent": intent, "category": None, "n": None, "order": "highest", "level": None, "years": [],
           "mentions": [], "leftovers": [], "followup": None, "places": list(places)}
    out = _run(req, [], state, lang, mode, t0)
    out["memory"] = state.summary()
    out["style"], out["detail"] = state.style, state.detail
    return out

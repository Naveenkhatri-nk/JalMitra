"""
conversation_state.py - Short memory of one chat session (no AI).

Remembers the places and the request of the last answer, so that
  "Is Jaipur safe?" -> "What about Jodhpur?" -> "Compare both."
works. It also keeps a pending clarification when a name fits several
places; the user can answer with a number ("1"), an ordinal ("first",
"पहला"), a type word ("district", "block") or a state/district name.
Nothing is ever filled in by guessing: if the context is not clear, the
engine asks.

JalMitra 3.0 adds (Phase 1):
  home          the location the user chose in the app ("my block", "here")
  domain        groundwater / soil / crop / land / irrigation of the last question
  style, detail farmer|official|student and short|standard|detailed of the last answer
  last_findings (place, category) pairs of the last answer, for "What does it mean?"
  last_sources  source rows of the last answer
  last_intent   the kind of the last question
A new chat (clear()) forgets everything except the chosen location, which
the app passes again.
"""

import re

import entity_resolver as er

ORDINALS = {
    1: ["first", "1st", "pehla", "pahla", "pehli", "पहला", "पहली", "पहिला", "पहिले", "ਪਹਿਲਾ", "ਪਹਿਲੀ", "पैलो"],
    2: ["second", "2nd", "doosra", "dusra", "doosri", "दूसरा", "दूसरी", "दुसरा", "दुसरे", "ਦੂਜਾ", "ਦੂਜੀ", "दूजो"],
    3: ["third", "3rd", "teesra", "tisra", "तीसरा", "तीसरी", "तिसरा", "ਤੀਜਾ", "तीजो"],
}
YES = {"yes", "y", "haan", "ha", "han", "ji", "हाँ", "हां", "जी", "हो", "होय", "ਹਾਂ", "ਜੀ", "हा", "ok", "okay"}


class ConversationState:
    def __init__(self):
        self.last_places = []     # places used in the last answer
        self.history = []         # distinct places, most recent last
        self.last_req = None      # the last executed request (intent, category, ...)
        self.pending = None       # {"req", "resolved", "queue", "notes", "options", "name"}
        self.last_lang = "en"
        # JalMitra 3.0
        self.home = None          # location chosen in the app (a place dict) or None
        self.domain = "groundwater"
        self.style = "farmer"
        self.detail = "standard"
        self.last_intent = None
        self.reply_seq = 0        # rotates the wording of small-talk / scope / fallback replies
        self.last_app = None      # last answer was about JalMitra itself (app_info intent), else None
        self.last_findings = []   # [(place label data, category)]
        self.last_categories = []
        self.last_sources = []
        self.soil_report = None   # the user's confirmed soil report (set by the app; private to this session)

    def clear(self):
        self.__init__()

    def set_home(self, place):
        """Location chosen in the app (None to clear). Used for "my area", "here", "mera block"."""
        self.home = place

    def note_answer(self, intent, result, sources):
        """Remember what the last answer was about (only answers with data change the memory)."""
        self.last_intent = intent
        if result is None:
            return
        findings, cats = [], []
        for b in result.get("blocks", []):
            if b.get("kind") == "unit":
                r = b["record"]
                findings.append((b.get("place") or {"type": "unit", "name": r["assessment_unit"]}, r["category"]))
                cats.append(r["category"])
            elif b.get("kind") == "area":
                cats.extend(c for c, n in (b.get("counts") or {}).items() if n)
        if findings or cats:
            self.last_findings = findings
            self.last_categories = list(dict.fromkeys(cats))
        if sources:
            self.last_sources = list(sources)

    def summary(self):
        """What the conversation currently remembers (shown in the app)."""
        place = self.last_places[-1] if self.last_places else None
        return {"place": place, "places": list(self.last_places), "domain": self.domain, "language": self.last_lang,
                "style": self.style, "detail": self.detail, "last_intent": self.last_intent, "home": self.home,
                "sources": len(self.last_sources)}

    # ---------------------------------------------------------- memory
    def remember(self, req, places):
        if places:
            self.last_places = list(places)
            for p in places:
                key = er.place_key(p)
                self.history = [h for h in self.history if er.place_key(h) != key] + [p]
            self.history = self.history[-6:]
        if req.get("intent") in ("explain_category", "help", "off_topic", "unclear", "blocked"):
            return                # explanations do not replace the last data question ("What about Jodhpur?")
        self.last_req = {k: v for k, v in req.items() if k not in ("mentions", "places", "soil_report")}
        self.domain = req.get("domain") or "groundwater"

    def recent_two(self):
        return self.history[-2:] if len(self.history) >= 2 else []

    # ---------------------------------------------------------- clarification
    def set_pending(self, req, resolved, queue, notes, options, name):
        self.pending = {"req": req, "resolved": resolved, "queue": queue, "notes": notes,
                        "options": options, "name": name}

    def resolve_pending(self, reply):
        """Return the chosen option, or None if the reply does not choose one."""
        if not self.pending:
            return None
        options = self.pending["options"]
        text = reply.strip().lower().translate(er.DEVANAGARI_DIGITS)
        words = set(re.findall(r"[\wऀ-੿]+", text))
        m = re.fullmatch(r"(?:option|number|no\.?|#|नंबर|क्रमांक|ਨੰਬਰ)?\s*(\d{1,2})\s*[.)]?", text)
        if m and 1 <= int(m.group(1)) <= len(options):
            return options[int(m.group(1)) - 1]
        for n, ws in ORDINALS.items():
            if words & set(ws) and n <= len(options) and len(words) <= 4:
                return options[n - 1]
        if len(options) == 1 and words and words <= YES:
            return options[0]
        for kind, ws in er.TYPE_WORDS.items():
            if words & ws:
                typed = [o for o in options if o["type"] == kind]
                if len(typed) == 1:
                    return typed[0]
        mentions, _ = er.extract_places(reply)
        for mention in mentions:
            for c in mention["candidates"]:
                hits = [o for o in options if er.place_key(o) == er.place_key(c)]
                if len(hits) == 1:
                    return hits[0]
            states = {c["state"] for c in mention["candidates"] if c["type"] == "state"}
            districts = {(c["state"], c["district"]) for c in mention["candidates"] if c["type"] == "district"}
            hits = [o for o in options if o["state"] in states or (o["state"], o.get("district")) in districts]
            if len(hits) == 1:
                return hits[0]
        return None

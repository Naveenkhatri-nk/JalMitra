"""
fake_ai_for_tests.py - a deterministic stand-in for the local AI model, used by the UI tests (no Ollama needed).

It reads the prompt built by jalmitra_ai.build_messages and writes a short, correct reply from the evidence in it,
in the requested language: the place's official category and stage for data replies, a clarification question,
"no data", "coming soon", a refusal, or a passage-cited explanation. Self-check prompts get "SUPPORTED".
install() swaps it in for llm_provider.LLMProvider and a fixed passage for rag.retrieve; restore() undoes it.
Test helper only - never used by the app.
"""

import re

import llm_compose as lc
import llm_provider as lp

LANG_OF = {v: k for k, v in lc.LANG_NAME.items()}
DATA = {"en": "{p} is {c}; its stage of extraction is {s}%.", "hinglish": "{p} {c} category mein hai, stage {s}% hai.",
        "hi": "{p} {c} श्रेणी में है; दोहन का स्तर {s}% है।", "raj": "{p} {c} श्रेणी में है; दोहन रो स्तर {s}% है।",
        "mr": "{p} {c} श्रेणीत आहे; उपसा टप्पा {s}% आहे.", "pa": "{p} {c} ਸ਼੍ਰੇਣੀ ਵਿੱਚ ਹੈ; ਨਿਕਾਸੀ ਪੱਧਰ {s}% ਹੈ।"}
DATA_NOSTAGE = {"en": "{p} is {c}.", "hinglish": "{p} {c} category mein hai.", "hi": "{p} {c} श्रेणी में है।",
                "raj": "{p} {c} श्रेणी में है।", "mr": "{p} {c} श्रेणीत आहे.", "pa": "{p} {c} ਸ਼੍ਰੇਣੀ ਵਿੱਚ ਹੈ।"}
LOCAL = {"hi": {"Over-exploited": "अतिदोहित (Over-exploited)", "Safe": "सुरक्षित (Safe)", "Critical": "गंभीर (Critical)",
                "Semi-critical": "अर्ध-गंभीर (Semi-critical)", "Saline": "लवणीय (Saline)"},
         "raj": {"Over-exploited": "अतिदोहित (Over-exploited)", "Safe": "सुरक्षित (Safe)", "Critical": "गंभीर (Critical)",
                 "Semi-critical": "अर्ध-गंभीर (Semi-critical)", "Saline": "लवणीय (Saline)"},
         "mr": {"Over-exploited": "अतिशोषित (Over-exploited)", "Safe": "सुरक्षित (Safe)", "Critical": "गंभीर (Critical)",
                "Semi-critical": "अर्ध-गंभीर (Semi-critical)", "Saline": "क्षारयुक्त (Saline)"},
         "pa": {"Over-exploited": "ਵੱਧ-ਸ਼ੋਸ਼ਿਤ (Over-exploited)", "Safe": "ਸੁਰੱਖਿਅਤ (Safe)", "Critical": "ਗੰਭੀਰ (Critical)",
                "Semi-critical": "ਅਰਧ-ਗੰਭੀਰ (Semi-critical)", "Saline": "ਖਾਰਾ (Saline)"}}
OTHER = {
    "clarify": {"en": "Which place do you mean? Please choose one of the options below.",
                "hinglish": "Aap kaunsi jagah poochh rahe hain? Neeche se ek option chunein.",
                "hi": "आप किस जगह के बारे में पूछ रहे हैं? कृपया नीचे से एक विकल्प चुनें।",
                "raj": "थे किण जगां री बात कर रिया हो? नीचै सूं एक चुणो।",
                "mr": "तुम्ही कोणत्या ठिकाणाबद्दल विचारत आहात? कृपया खालीलपैकी एक निवडा.",
                "pa": "ਤੁਸੀਂ ਕਿਹੜੀ ਥਾਂ ਬਾਰੇ ਪੁੱਛ ਰਹੇ ਹੋ? ਕਿਰਪਾ ਕਰਕੇ ਹੇਠਾਂ ਤੋਂ ਇੱਕ ਚੁਣੋ।"},
    "missing": {"en": "JalMitra has no official groundwater data for this place.",
                "hinglish": "JalMitra ke paas is jagah ka official groundwater data nahi hai.",
                "hi": "JalMitra के पास इस जगह का आधिकारिक भूजल डेटा नहीं है।", "raj": "JalMitra कनै इण जगां रो सरकारी भूजल डेटा कोनी।",
                "mr": "JalMitra कडे या ठिकाणाची अधिकृत भूजल माहिती नाही.", "pa": "JalMitra ਕੋਲ ਇਸ ਥਾਂ ਦਾ ਸਰਕਾਰੀ ਭੂਜਲ ਡਾਟਾ ਨਹੀਂ ਹੈ।"},
    "coming_soon": {"en": "This will come in a future JalMitra update.",
                    "hinglish": "Yeh JalMitra ke aane wale update mein aayega.",
                    "hi": "यह JalMitra के आने वाले अपडेट में आएगा।", "raj": "ओ JalMitra रै आगला अपडेट में आसी।",
                    "mr": "हे JalMitra च्या पुढील अपडेटमध्ये येईल.", "pa": "ਇਹ JalMitra ਦੇ ਅਗਲੇ ਅੱਪਡੇਟ ਵਿੱਚ ਆਵੇਗਾ।"},
    "refuse": {"en": "I can only share official recorded values.", "hinglish": "Main sirf official recorded values batata hoon.",
               "hi": "मैं केवल आधिकारिक दर्ज आंकड़े बताता हूँ।", "raj": "म्हैं सिरफ सरकारी आंकड़ा बताऊं।",
               "mr": "मी फक्त अधिकृत नोंदवलेली माहिती देतो.", "pa": "ਮੈਂ ਸਿਰਫ਼ ਸਰਕਾਰੀ ਦਰਜ ਅੰਕੜੇ ਦੱਸਦਾ ਹਾਂ।"},
    "conversation": {"en": "Hello! Ask me about groundwater.", "hinglish": "Namaste! Groundwater ke baare mein poochhiye.",
                     "hi": "नमस्ते! भूजल के बारे में पूछिए।", "raj": "राम राम! भूजल रै बारै में पूछो।",
                     "mr": "नमस्कार! भूजलाबद्दल विचारा.", "pa": "ਸਤ ਸ੍ਰੀ ਅਕਾਲ! ਭੂਜਲ ਬਾਰੇ ਪੁੱਛੋ।"},
    "general": {"en": "During the monsoon, rainfall recharges the aquifers and the water table becomes shallow{t}.",
                "hinglish": "Monsoon mein barish se aquifers recharge hote hain aur water level upar aata hai{t}.",
                "hi": "मानसून में बारिश से जलभृत भरते हैं और भूजल स्तर ऊपर आता है{t}।",
                "raj": "मानसून में मेह सूं पाणी धरती में जावै अर भूजल स्तर ऊपर आवै{t}।",
                "mr": "पावसाळ्यात पावसामुळे जलधर भरतात आणि भूजल पातळी वर येते{t}.",
                "pa": "ਮਾਨਸੂਨ ਵਿੱਚ ਮੀਂਹ ਨਾਲ ਪਾਣੀ ਧਰਤੀ ਵਿੱਚ ਜਾਂਦਾ ਹੈ ਅਤੇ ਪਾਣੀ ਦਾ ਪੱਧਰ ਉੱਪਰ ਆਉਂਦਾ ਹੈ{t}।"},
}
PASSAGE = {"text": "The water table becomes shallow during the monsoon as rainfall recharges the aquifers. Rainfall is the "
                   "main source of ground water recharge in the country.", "source_id": "NC2025",
           "title": "National Compilation on Dynamic Ground Water Resources of India, 2025", "page": 57,
           "chunk_id": "NC2025-p057-c0", "year": "2025", "distance": 0.3}


def reply(messages):
    sys_msg, user = messages[0]["content"], messages[-1]["content"]
    if "You check a short groundwater explanation" in sys_msg:
        return "SUPPORTED"
    m = re.search(r"Write the reply in (.+?)\.(\s|$)", user)
    lang = LANG_OF.get(m.group(1), "en") if m else "en"
    if user.startswith("TASK: Answer the question about this place"):
        facts = user.split("OFFICIAL DATA")[-1]          # the data block (the task line also says OFFICIAL DATA)
        rows = re.findall(r"assessment_unit: ([^;\n]+);[^\n]*?category: ([A-Za-z-]+)(?:;[^\n]*?stage_pct: ([\d.]+))?", facts)
        if rows:
            p, c, s = rows[0]
            c2 = LOCAL.get(lang, {}).get(c, c)
            return (DATA if s else DATA_NOSTAGE)[lang].format(p=p.strip(), c=c2, s=s.rstrip("0").rstrip(".") if s else "")
        return OTHER["missing"][lang]
    for kind, key in (("clarify", "TASK: The place name"), ("missing", "TASK: JalMitra has NO"),
                      ("coming_soon", "TASK: The user asked about"), ("refuse", "TASK: The user asked JalMitra to break"),
                      ("conversation", "TASK: Reply in a friendly"), ("ask_place", "TASK: The question needs a location"),
                      ("ask_place", "TASK: The user's message is short or unclear")):
        if user.startswith(key):
            return OTHER["clarify" if kind == "ask_place" else kind][lang]
    tag = " [P1]" if "[P1]" in user else ""
    return OTHER["general"][lang].format(t=tag)


class FakeProvider(lp.LLMProvider):
    def chat(self, messages, **kw):
        return lp.LLMResult(text=reply(messages), ok=True, provider="fake", model=self.model, latency_ms=1.0)


class DownProvider(lp.LLMProvider):
    def chat(self, messages, **kw):
        return lp.LLMResult(ok=False, error="connection refused (is the LLM server running?)", provider="fake",
                            model=self.model)


_SAVED = []


def install(down=False):
    import jalmitra_ai as ja
    import rag
    _SAVED.append((lp.LLMProvider, rag.retrieve, ja.ai_status))
    lp.LLMProvider = DownProvider if down else FakeProvider
    rag.retrieve = lambda *a, **k: [dict(PASSAGE)]
    ja.ai_status = (lambda force=False, timeout=3.0: {"ok": False, "model": "qwen3:4b-instruct-2507-q4_K_M",
                                                      "error": "Ollama not reachable (test)"}) if down else \
        (lambda force=False, timeout=3.0: {"ok": True, "model": "qwen3:4b-instruct-2507-q4_K_M",
                                           "processor": "100% GPU", "error": None})


def restore():
    import jalmitra_ai as ja
    import rag
    if _SAVED:
        lp.LLMProvider, rag.retrieve, ja.ai_status = _SAVED.pop()

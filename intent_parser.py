"""
intent_parser.py - Rule-based understanding of a groundwater question (no AI).

Keyword dictionaries (six languages, code-mixing allowed), regular
expressions and a fixed priority order turn a question into an intent:

  status           Is Jaipur safe? / Jaipur ka paani kaisa hai? / जयपुर में भूजल की स्थिति क्या है?
  numeric          Stage of extraction of Ajmer Urban / recharge of Gira
  top_n            Top 5 over-exploited blocks in Rajasthan / lowest stage in Jaipur district
  top_areas        Which district has the most over-exploited units?
  list_category    Safe blocks in Pune district / How many critical units in Punjab?
  area_search      Show all blocks in Jaipur district / Rajasthan summary
  compare          Compare Jaipur district and Jodhpur district / compare both
  year_compare     Compare 2020 and 2025 for Jaipur / How has Jaipur changed?
  explain_category What does semi-critical mean?
  sources          Where does this data come from? / source of Ajmer Urban
  data_availability What data do you have? / Is numerical data available for Pune?
  quality          Which units have data-quality warnings?
  help, off_topic, blocked (prompt injection / SQL / requests to invent numbers), unclear

The parser never guesses a place. Places come from entity_resolver and are
checked against the database.
"""

import re
from functools import lru_cache

import entity_resolver as er
import knowledge_answer
import app_info
import conversation

CATEGORIES = ["Safe", "Semi-critical", "Critical", "Over-exploited", "Saline"]

# ------------------------------------------------------------------ keyword dictionaries
# Latin entries are matched as whole words (lower case); entries with a space
# are phrases. Indic entries are matched as whole words or phrases too.

CATEGORY_WORDS = {
    "Semi-critical": ["semi-critical", "semi critical", "semicritical", "semi-crit", "अर्ध-गंभीर", "अर्ध गंभीर",
                      "अर्धगंभीर", "अर्ध-संकटपूर्ण", "ਅਰਧ-ਗੰਭੀਰ", "ਅਰਧ ਗੰਭੀਰ"],
    "Over-exploited": ["over-exploited", "over exploited", "overexploited", "over-exploit", "over exploit",
                       "overexploitation", "over-exploitation", "अतिदोहित", "अति-दोहित", "अति दोहित", "अतिशोषित",
                       "अति-शोषित", "अति शोषित", "ਵੱਧ-ਸ਼ੋਸ਼ਿਤ", "ਵੱਧ ਸ਼ੋਸ਼ਿਤ", "ਅਤਿ-ਸ਼ੋਸ਼ਿਤ", "ਵਧ-ਸ਼ੋਸ਼ਿਤ"],
    "Critical": ["critical", "गंभीर", "संकटपूर्ण", "ਗੰਭੀਰ"],
    "Saline": ["saline", "salty", "khara", "khaara", "खारा", "खारे", "खारो", "लवणीय", "क्षारयुक्त", "ਖਾਰਾ", "ਖਾਰੇ"],
    "Safe": ["safe", "surakshit", "सुरक्षित", "ਸੁਰੱਖਿਅਤ"],
}

KW = {
    "status": ["status", "condition", "situation", "category", "classified", "classification", "how is",
               "how's", "unsafe", "danger", "dangerous", "kaisa", "kaisi", "kaise", "haal", "halat", "sthiti",
               "theek", "thik", "accha", "achha", "kharab", "स्थिति", "हालत", "हाल", "श्रेणी", "कैसा", "कैसी",
               "कैसे", "ठीक", "स्थिती", "परिस्थिती", "कसा", "कशी", "कसे", "ਸਥਿਤੀ", "ਹਾਲਤ", "ਹਾਲ", "ਕਿਵੇਂ",
               "ਕਿਹੋ ਜਿਹਾ", "ਕਿਹੋ ਜਿਹੀ", "ਸ਼੍ਰੇਣੀ", "कियां", "कियाँ", "किसो", "किसीक", "safe", "groundwater",
               "bhujal", "भूजल", "पाणी", "पानी", "ਪਾਣੀ", "paani", "pani", "water"],
    "numeric": ["stage", "extraction", "recharge", "extractable", "how much", "figure", "figures", "numbers",
                "number", "value", "values", "percentage", "percent", "volume", "ham", "bcm", "usage", "draft",
                "withdrawal", "kitna", "kitni", "nikasi", "dohan", "दोहन", "निकासी", "पुनर्भरण", "रिचार्ज",
                "कितना", "कितनी", "प्रतिशत", "आंकड़े", "आँकड़े", "आंकड़ा", "मात्रा", "स्तर", "उपसा", "उपशाचा",
                "टक्के", "आकडे", "आकडेवारी", "टप्पा", "ਨਿਕਾਸੀ", "ਰੀਚਾਰਜ", "ਕਿੰਨਾ", "ਕਿੰਨੀ", "ਪ੍ਰਤੀਸ਼ਤ", "ਅੰਕੜੇ",
                "ਪੱਧਰ", "कित्तो", "कितरो", "कितो"],
    "top": ["top", "highest", "lowest", "most", "least", "worst", "best", "maximum", "minimum", "rank",
            "ranking", "largest", "smallest", "sabse", "sab se", "सबसे", "शीर्ष", "अधिकतम", "न्यूनतम", "सर्वाधिक",
            "सर्वात", "सगळ्यात", "ਸਭ ਤੋਂ", "ਸਿਖਰਲੇ", "ਸਿਖਰ", "सब सूं", "सगळा सूं"],
    "low": ["lowest", "least", "minimum", "best", "smallest", "safest", "kam", "कम", "न्यूनतम", "कमी", "ਘੱਟ"],
    "most_count": ["most", "maximum", "highest number", "sabse zyada", "sabse jyada", "सबसे ज़्यादा",
                   "सबसे ज्यादा", "सबसे अधिक", "सर्वाधिक", "सर्वात जास्त", "ਸਭ ਤੋਂ ਵੱਧ", "सब सूं घणा", "सब सूं घणी"],
    "list": ["list", "show", "which", "name the", "all blocks", "all units", "blocks in", "units in",
             "talukas in", "kaun se", "kaunse", "konse", "kaun kaun", "dikhao", "कौन से", "कौनसे", "कौन-से",
             "सूची", "दिखाओ", "दिखाइए", "कोणते", "कोणत्या", "यादी", "दाखवा", "ਕਿਹੜੇ", "ਕਿਹੜੀਆਂ", "ਸੂਚੀ", "ਦਿਖਾਓ",
             "कुण सा", "कुणसा", "दिखावो", "बतावो"],
    "count": ["how many", "number of", "count", "kitne", "kitni", "कितने", "कितनी", "किती", "ਕਿੰਨੇ", "ਕਿੰਨੀਆਂ",
              "कितरा", "कित्ता"],
    "units_obj": ["blocks", "units", "talukas", "taluks", "mandals", "tehsils", "assessment units", "ब्लॉकों",
                  "इकाइयाँ", "इकाइयां", "इकाइयों", "तालुके", "घटक", "ਬਲਾਕਾਂ", "ਇਕਾਈਆਂ"],
    "level_district": ["district", "districts", "zila", "zile", "jila", "jile", "ज़िले", "जिले", "ज़िला", "जिला",
                       "जिल्हे", "जिल्हा", "ਜ਼ਿਲ੍ਹੇ", "ਜ਼ਿਲ੍ਹਾ", "जिला"],
    "level_state": ["state", "states", "rajya", "राज्य", "राज्ये", "ਰਾਜ", "ਸੂਬਾ", "ਸੂਬੇ"],
    "compare": ["compare", "comparison", "versus", "vs", "difference", "differ", "better", "worse", "tulna",
                "muqabla", "farak", "fark", "तुलना", "मुकाबला", "फर्क", "फ़र्क", "अंतर", "फरक", "ਤੁਲਨਾ", "ਮੁਕਾਬਲਾ",
                "ਫਰਕ", "ਫ਼ਰਕ"],
    "both": ["both", "dono", "दोनों", "दोन्ही", "दोन्हींची", "ਦੋਵੇਂ", "ਦੋਵਾਂ", "दोनूं", "them", "these two"],
    "year_change": ["trend", "over the years", "change", "changed", "changes", "since", "previous year",
                    "last year", "earlier year", "year-wise", "yearwise", "history", "historical", "pichle saal",
                    "pichhle saal", "badla", "badlav", "पिछले साल", "पिछले वर्ष", "बदलाव", "परिवर्तन", "बदला",
                    "गेल्या वर्षी", "बदल", "ਪਿਛਲੇ ਸਾਲ", "ਬਦਲਾਅ", "ਬਦਲਿਆ", "पाछलै बरस"],
    "explain": ["mean", "means", "meaning", "define", "definition", "explain", "what is meant", "matlab",
                "kya hota", "kya hai", "मतलब", "अर्थ", "क्या होता", "क्या है", "म्हणजे", "अर्थ काय", "ਮਤਲਬ",
                "ਕੀ ਹੁੰਦਾ", "ਅਰਥ", "कांई होवै", "कांई मतलब", "रो मतलब"],
    "sources": ["source", "sources", "citation", "cite", "reference", "references", "where does", "come from",
                "comes from", "data from", "page number", "publication", "kahan se", "srot", "स्रोत", "कहाँ से",
                "कहां से", "कुठून", "ਸਰੋਤ", "ਕਿੱਥੋਂ", "कठै सूं"],
    "availability": ["what data", "which data", "available data", "data available", "coverage", "which years",
                     "what years", "which year", "kaunsa data", "kya data", "kitna data", "data hai",
                     "कौन सा डेटा", "कौनसा डेटा", "कोणता डेटा", "कोणती माहिती", "ਕਿਹੜਾ ਡਾਟਾ", "do you have",
                     "is there data", "numerical data", "numbers available", "डेटा उपलब्ध", "आंकड़े उपलब्ध",
                     "available", "उपलब्ध", "ਉਪਲਬਧ", "कोणते वर्ष", "कौन सा साल"],
    "quality": ["quality", "warning", "warnings", "flag", "flags", "flagged", "verification", "verify",
                "reliable", "error", "errors", "mismatch", "conflict", "conflicts", "inconsistent", "galti",
                "गुणवत्ता", "चेतावनी", "त्रुटि", "विरोधाभास", "इशारे", "ਗੁਣਵੱਤਾ", "ਚੇਤਾਵਨੀ"],
    "help": ["hello", "hi", "hey", "namaste", "namaskar", "help", "नमस्ते", "नमस्कार", "मदद", "ਸਤ ਸ੍ਰੀ ਅਕਾਲ",
             "ਮਦਦ", "राम राम", "खम्मा घणी", "what can you do", "how to use"],
    "off_topic": ["weather", "forecast", "cricket", "movie", "film", "song", "joke", "recipe", "politics",
                  "election", "stock", "bitcoin", "capital of", "president", "prime minister", "mausam",
                  "मौसम", "क्रिकेट", "फिल्म", "चुटकुला", "हवामान", "ਮੌਸਮ", "football", "news"],
    "followup_new_place": ["what about", "how about", "and what about", "aur", "ka kya", "ki kya", "का क्या",
                           "की क्या", "बद्दल काय", "चे काय", "चं काय", "ਦਾ ਕੀ", "ਬਾਰੇ ਕੀ", "रो कांई", "री कांई",
                           "and", "also", "bhi", "भी"],
}

# JalMitra 3.0: questions about domains that have NO data in the database yet.
# They are answered with "Data unavailable" (never guessed). Checked in this order.
DOMAIN_WORDS = {
    "soil": ["soil", "soils", "mitti", "mitty", "maati", "mati", "मिट्टी", "मिटटी", "माटी", "माती", "ਮਿੱਟੀ",
             "organic carbon", "nutrient", "nutrients", "fertility", "fertile", "fertiliser", "fertilizer",
             "fertilisers", "fertilizers", "urvarta", "उर्वरता", "पोषक", "खाद", "खत", "ਖਾਦ", "soil health"],
    "crop": ["crop", "crops", "fasal", "fasl", "faslen", "faslein", "फसल", "फ़सल", "फसलें", "फ़सलें", "फसलां",
             "पीक", "पिके", "पिकं", "ਫ਼ਸਲ", "ਫਸਲ", "ਫ਼ਸਲਾਂ", "ਫਸਲਾਂ", "what to grow", "what should i grow",
             "which crop", "sow", "sowing", "wheat", "paddy", "gehun", "गेहूं", "गेहूँ", "धान", "बुवाई", "ugaye",
             "ugayein", "उगाएं", "उगाऊं", "उगाना"],
    "land": ["land", "lands", "zameen", "zamin", "jameen", "jamin", "bhumi", "भूमि", "जमीन", "ज़मीन", "ਜ਼ਮੀਨ",
             "ਜਮੀਨ", "land use", "slope", "terrain", "wasteland"],
    "irrigation": ["irrigation", "irrigate", "irrigating", "sinchai", "सिंचाई", "सिंचन", "ਸਿੰਚਾਈ"],
}
# general farming words: crop suitability unless soil or land is named
FARMING_WORDS = ["agriculture", "agricultural", "farming", "cultivation", "kheti", "खेती", "शेती", "ਖੇਤੀ",
                 "grow", "growing"]

# words that point to the user's own area ("my block", "mera ilaka"): the location chosen in the app is used,
# otherwise JalMitra asks. Never filled from earlier answers about other places.
SELF_WORDS = ["my", "mine", "our", "near me", "here", "mera", "meri", "mere", "hamara", "hamari", "hamare",
              "yahan", "yahaan", "मेरा", "मेरी", "मेरे", "हमारा", "हमारी", "हमारे", "यहाँ", "यहां", "माझा", "माझी",
              "माझे", "माझ्या", "आमचा", "आमची", "आमच्या", "इथे", "ਮੇਰਾ", "ਮੇਰੀ", "ਮੇਰੇ", "ਸਾਡਾ", "ਸਾਡੀ", "ਸਾਡੇ",
              "ਇੱਥੇ", "म्हारो", "म्हारी", "म्हारै", "म्हारा", "अठै"]

# "What does it mean?": explain the category from the previous answer
IT_WORDS = ["it", "this", "that", "yeh", "ye", "iska", "iski", "iske", "uska", "uski", "इसका", "इसकी", "इसके", "इस",
            "यह", "ये", "उसका", "उसकी", "याचा", "याची", "त्याचा", "त्याची", "हे", "ਇਸ", "ਇਸਦਾ", "ਇਸ ਦਾ", "ਇਹ",
            "इणरो", "इणरी", "ओ"]
EXPLAIN_STRICT = ["mean", "means", "meaning", "define", "definition", "explain", "matlab", "मतलब", "अर्थ", "म्हणजे",
                  "ਮਤਲਬ", "ਅਰਥ"]


def find_domain(text):
    """'soil', 'crop', 'land' or 'irrigation' when the question is about a domain without data, else None."""
    for domain in ("soil", "crop", "land", "irrigation"):
        if _has(text, DOMAIN_WORDS[domain]):
            return domain
    if _has(text, FARMING_WORDS):
        return "crop"
    return None


# words that clearly ask for figures (even when "groundwater" or "water" is also said)
STRONG_NUMERIC = ["stage", "extraction", "extracted", "extract", "recharge", "recharged", "extractable", "how much",
                  "figures", "figure", "numbers", "percentage", "percent", "ham", "bcm", "kitna", "kitni", "दोहन",
                  "निकासी", "पुनर्भरण", "उपसा", "उपशाचा", "ਨਿਕਾਸੀ", "ਰੀਚਾਰਜ", "कितना", "कितनी", "ਕਿੰਨਾ", "ਕਿੰਨੀ",
                  "कितरो", "कित्तो", "प्रतिशत", "ਪ੍ਰਤੀਸ਼ਤ", "आंकड़े", "आकडे", "ਅੰਕੜੇ", "रिचार्ज"]

INJECTION = re.compile(
    r"ignore\s+(all\s+|the\s+|any\s+)?(previous|prior|above|earlier|your)|disregard|forget\s+(your|all|the|previous)"
    r"|system\s*prompt|you\s+are\s+now|act\s+as|pretend|jailbreak|developer\s+mode|override|bypass"
    r"|reveal\s+(your|the)\s+(prompt|instructions|rules)|new\s+instructions|naye\s+niyam"
    r"|\bdrop\s+table\b|\bdelete\s+from\b|\binsert\s+into\b|\bupdate\s+\w+\s+set\b|\balter\s+table\b"
    r"|\bunion\s+select\b|;\s*--|<\s*script|\battach\s+database\b|\bpragma\b|sqlite_master"
    r"|निर्देश(ों)?\s*(को)?\s*(भूल|अनदेखा)|नियम\s*भूल|सूचना\s*विसरा|ਹਦਾਇਤਾਂ\s*ਭੁੱਲ",
    re.IGNORECASE)
FABRICATE = re.compile(
    r"\b(make\s+up|invent|fabricate|fake|guess|estimate|predict|forecast|assume|approximate|andaza|andaaza)\b"
    r"|अंदाज़ा|अंदाजा|अनुमान|अंदाज|ਅੰਦਾਜ਼ਾ|ਅਨੁਮਾਨ", re.IGNORECASE)

WORD_NUMBERS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8,
                "nine": 9, "ten": 10, "ek": 1, "do": 2, "teen": 3, "char": 4, "paanch": 5, "panch": 5, "das": 10,
                "एक": 1, "दो": 2, "तीन": 3, "चार": 4, "पांच": 5, "पाँच": 5, "पाच": 5, "दस": 10, "ਇੱਕ": 1, "ਦੋ": 2,
                "ਤਿੰਨ": 3, "ਚਾਰ": 4, "ਪੰਜ": 5, "ਦਸ": 10}


def _norm_text(text):
    text = text.translate(er.DEVANAGARI_DIGITS)
    return " " + re.sub(r"\s+", " ", re.sub(r"[?!.,;:।॥\"'()\[\]{}]", " ", text.lower())).strip() + " "


@lru_cache(maxsize=1024)
def _pattern(words):
    """One compiled alternation per word list (3.0: avoids re-compiling hundreds of patterns per question)."""
    alts = sorted({re.escape(w.lower()) for w in words}, key=len, reverse=True)
    return re.compile(r"(?<![\wऀ-੿])(?:" + "|".join(alts) + r")(?![\wऀ-੿])")


def _has(text, words):
    """Whole-word / whole-phrase match in normalised text."""
    return bool(words) and _pattern(tuple(words)).search(text) is not None


def _found(text, words):
    return [w for w in words if re.search(r"(?<![\wऀ-੿])" + re.escape(w.lower()) + r"(?![\wऀ-੿])", text)]


def find_category(text):
    """Official category named in the question (checks 'semi-critical' before 'critical')."""
    t = text
    for cat in ["Semi-critical", "Over-exploited", "Critical", "Saline", "Safe"]:
        if _has(t, CATEGORY_WORDS[cat]):
            return cat
    return None


def _all_keyword_tokens():
    toks = set()
    for words in list(KW.values()) + list(CATEGORY_WORDS.values()) + list(DOMAIN_WORDS.values()) + \
            [FARMING_WORDS, SELF_WORDS] + knowledge_answer.keyword_lists():
        for w in words:
            toks.update(re.findall(r"[\wऀ-੿]+(?:-[\wऀ-੿]+)*", w.lower()))
    toks.update(WORD_NUMBERS)
    for _kind, _words in conversation.SMALLTALK + conversation.OUT_OF_SCOPE:
        toks.update(w for w in _words if " " not in w)
    toks.update(["site", "website", "app", "portal", "sakte", "sakta", "bata", "batao", "milega", "milegi", "bare",
                 "baare", "batate", "batata", "batati", "jankari", "jaankari", "later", "bahut", "sell",
                 "karu", "karun", "karoon", "karein", "karen", "jalmitra", "jalmithra", "jalmitr", "jalamitra", "jalmitraa", "जलमित्र", "ਜਲਮਿੱਤਰ"])
    return frozenset(toks)


KEYWORD_TOKENS = _all_keyword_tokens()


def _find_n(text):
    m = re.search(r"(?:top|first|शीर्ष|ਸਿਖਰਲੇ|sabse|सबसे)\s*(\d{1,2})\b", text) or \
        re.search(r"(?<![\d-])(\d{1,2})\s*(?:most|highest|lowest|sabse|सबसे|सर्वाधिक|blocks|units|districts|states"
                  r"|ब्लॉक|इकाइयां|इकाइयाँ|ज़िले|जिले|जिल्हे|ਬਲਾਕ|ਜ਼ਿਲ੍ਹੇ|over|critical|safe|semi)", text)
    if m:
        return max(1, min(int(m.group(1)), 50))
    if _has(text, KW["top"] + ["worst", "best"]):
        # "give me 3 worst blocks": a lone 1-2 digit number (not part of a name like Ludhiana-1, not a year)
        m = re.search(r"(?<![\w-])(\d{1,2})(?![\w-])", text)
        if m:
            return max(1, min(int(m.group(1)), 50))
    for w, n in WORD_NUMBERS.items():
        if _has(text, [w]) and _has(text, KW["top"]):
            return n
    return None


def _years(text):
    return sorted(set(re.findall(r"(?<!\d)((?:19|20)\d{2})(?!\d)", text)))


def parse(question, context_has_places=False):
    """Return a parsed request:

    {"intent", "category", "n", "order", "level", "years", "mentions", "leftovers",
     "followup", "matched": [keywords], "confidence"}
    """
    text = _norm_text(question)
    # 0. questions about JalMitra itself ("What is this website about?", "JalMitra kya hai?"): answered from
    #    fixed texts before any place lookup, so they never reach SQL or groundwater entity resolution.
    scope_x, scope_verdict = None, None
    if not INJECTION.search(question) and (not FABRICATE.search(question)
                                           or conversation.out_of_scope(question) == "weather"):
        # 0a. everyday conversation (conversation.py): small talk, out-of-scope subjects, yes/no scope questions
        early = {"category": None, "n": None, "order": "highest", "level": None, "years": [], "mentions": [],
                 "leftovers": [], "followup": None, "confidence": "high", "domain": None, "self_ref": False}
        kind = conversation.smalltalk(question)
        if kind == "greet":
            return {**early, "intent": "help", "matched": [kind]}       # the existing greeting reply
        if kind:
            return {**early, "intent": "smalltalk", "smalltalk": kind, "matched": [kind]}
        scope_x = conversation.scope_question(question)
        scope_verdict = conversation.classify_scope(scope_x) if scope_x else None
        if scope_x and scope_verdict is None and app_info.detect(question):
            scope_x = None       # "Can you show me your features?" is about the app itself
        if scope_verdict and scope_verdict[0] == "no":
            return {**early, "intent": "scope", "verdict": "no", "topic": scope_verdict[1], "matched": [scope_x]}
        oos = conversation.out_of_scope(question)
        if oos:
            return {**early, "intent": "off_topic", "oos": oos, "matched": [oos]}
    if scope_x is None and not INJECTION.search(question) and not FABRICATE.search(question):
        app = app_info.detect(question)
        if app:
            return {"intent": app, "category": None, "n": None, "order": "highest", "level": None, "years": [],
                    "mentions": [], "leftovers": [], "followup": None, "matched": [app], "confidence": "high",
                    "domain": None, "self_ref": False}
    mentions, leftovers = er.extract_places(question, KEYWORD_TOKENS)
    leftovers = [w for w in leftovers if w.lower() not in KEYWORD_TOKENS]
    category = find_category(text)
    years = _years(text)
    n = _find_n(text)
    out = {"intent": "unclear", "category": category, "n": n, "order": "highest", "level": None,
           "years": years, "mentions": mentions, "leftovers": leftovers, "followup": None, "matched": [],
           "confidence": "low", "domain": None, "self_ref": False}

    def done(intent, conf="high", **extra):
        out.update(intent=intent, confidence=conf, **extra)
        return out

    # 1. safety first
    if INJECTION.search(question):
        return done("blocked", reason="injection")
    if FABRICATE.search(question) and not _has(text, KW["explain"]):
        return done("blocked", reason="fabricate")

    has_place = bool(mentions)
    is_top = _has(text, KW["top"]) or n is not None and _has(text, KW["units_obj"] + KW["level_district"])
    if _has(text, KW["low"]) and not _has(text, ["most", "sabse zyada", "सबसे ज़्यादा", "सर्वाधिक"]):
        out["order"] = "lowest"

    # 1b. yes/no scope question ("Is this site about soil?", "Can I check my water quality here?"): answered
    #     directly unless it names a place, a crop, a parameter or a category; those go on to the data answers
    if scope_x and not has_place and not category and not _years(text):
        kd0 = knowledge_answer.detect(text)
        specific = kd0 and (kd0.get("crops") or kd0.get("parameters") or kd0.get("keys"))
        if not specific:
            if scope_verdict:
                return done("scope", verdict=scope_verdict[0], topic=scope_verdict[1])
            if kd0:
                topic = {"water_quality": "water_quality", "crop": "crops", "soil": "soil", "irrigation": "irrigation",
                         "land": "land"}.get(kd0["domain"], "farming")
                return done("scope", verdict="yes", topic=topic)
            return done("scope", verdict="unknown", topic=None)

    # 2. greetings and help (only when nothing else is asked)
    if not has_place and not category and _has(text, KW["help"]) and len(text.split()) <= 6 \
            and not scope_x and not knowledge_answer.detect(text):
        return done("help")

    # 2b. JalMitra 3.0: soil / crop / land / irrigation questions (no data yet -> "Data unavailable")
    self_ref = _has(text, SELF_WORDS) and not has_place
    out["self_ref"] = self_ref
    kd = knowledge_answer.detect(text)
    if kd and kd.get("crops") and mentions:
        # a crop word that is also a place name here ("Moth", a block) is read as the place
        said = {m["text"].lower() for m in mentions}
        longer = lambda c: any(" " in a and a in text for a in knowledge_answer.crop_aliases(c))  # "moth bean"
        kd["crops"] = [c for c in kd["crops"] if longer(c) or not said & set(knowledge_answer.crop_aliases(c))]
        mentions[:] = [m for m in mentions if not any(longer(c) and m["text"].lower() in knowledge_answer.crop_aliases(c)
                                                      for c in kd["crops"])]
        if not kd["crops"] and kd["topic"] in ("crop", "compare_crops"):
            kd = None
    if kd and not (has_place and category and kd["domain"] != "water_quality" and not kd.get("crops")
                   and not _has(text, DOMAIN_WORDS.get(kd["domain"], []))):
        return done("domain", domain=kd["domain"], knowledge=kd)
    domain = find_domain(text)
    if domain:
        return done("domain", domain=domain)

    # 2c. "What does it mean?" -> the category of the previous answer
    if not has_place and not category and _has(text, EXPLAIN_STRICT) and _has(text, IT_WORDS) \
            and not _has(text, STRONG_NUMERIC) and not is_top:
        return done("explain_category", category=None, what="context")

    # 2d. "Is groundwater safe in my area?" -> the user's chosen location (the engine asks if none is chosen)
    if self_ref and not is_top and not _has(text, EXPLAIN_STRICT + KW["list"] + KW["count"] + KW["compare"]
                                             + KW["sources"] + KW["quality"] + KW["availability"]):
        return done("numeric" if _has(text, STRONG_NUMERIC) else "status", conf="medium")

    # 3. category explanation: "What does semi-critical mean?"
    if category and not has_place and _has(text, KW["explain"]) and not is_top:
        return done("explain_category")
    if not has_place and _has(text, ["stage of extraction", "दोहन स्तर", "extraction stage"]) and _has(text, KW["explain"]):
        return done("explain_category", category=None, what="stage")

    # 4. year comparison
    if len(years) >= 2 or (_has(text, KW["year_change"]) and (has_place or context_has_places)):
        return done("year_compare")

    # 5. rankings of areas: "Which district has the most over-exploited units?"
    level = "state" if _has(text, KW["level_state"]) and not _has(text, KW["level_district"]) else \
        ("district" if _has(text, KW["level_district"]) else None)
    area_rank = level and category and (_has(text, KW["most_count"]) or (is_top and not _has(text, KW["units_obj"])))
    if area_rank and not any(c["type"] == level for m in mentions for c in m["candidates"]):
        return done("top_areas", level=level)

    # 6. rankings of units
    if is_top and not _has(text, KW["compare"]):
        return done("top_n")

    # 7. comparisons
    if _has(text, KW["compare"]) or (len(mentions) >= 2 and _has(text, [" and ", " aur ", " और ", " आणि ", " ਅਤੇ ", " अर "])
                                     and not _has(text, KW["sources"] + KW["quality"])):
        return done("compare", followup="both" if (len(mentions) < 2 and (_has(text, KW["both"]) or not mentions)) else None)
    if _has(text, KW["both"]) and context_has_places and not has_place:
        return done("compare", followup="both")

    # 8. sources, quality, coverage
    if _has(text, KW["sources"]):
        return done("sources")
    if _has(text, KW["quality"]):
        return done("quality")
    if _has(text, KW["availability"]) and not category:
        return done("data_availability")

    # 9. lists and counts
    wants_list = _has(text, KW["list"] + KW["count"])
    if category and (wants_list or _has(text, KW["units_obj"])) and not _is_status_question(text, mentions):
        return done("list_category", count_only=_has(text, KW["count"]))
    if wants_list and _has(text, KW["units_obj"] + ["blocks", "ब्लॉक", "ਬਲਾਕ"]) and has_place:
        return done("area_search")

    # 10. figures
    if _has(text, STRONG_NUMERIC) or (_has(text, KW["numeric"]) and not _has(text, KW["status"])):
        if has_place or context_has_places:
            return done("numeric")

    # 11. status
    if has_place and (_has(text, KW["status"]) or category):
        return done("status")
    if has_place and _has(text, KW["followup_new_place"]):
        return done("status", conf="medium", followup="new_place")
    if has_place and not leftovers:
        return done("status", conf="medium")
    if has_place:
        return done("status", conf="medium")

    # 12. no place found
    named = [w for w in leftovers if w[:1].isupper() or re.search(r"[\u0900-\u0A7F]", w)]
    if named and (category or _has(text, KW["status"] + KW["numeric"])):
        # the engine answers "not found" with suggestions
        return done("numeric" if _has(text, STRONG_NUMERIC) else "status", conf="low", unknown=named)
    if category and not _has(text, KW["list"] + KW["count"]):
        return done("explain_category", conf="medium")
    if _has(text, KW["off_topic"]):
        return done("off_topic")
    if category:
        return done("list_category", count_only=_has(text, KW["count"]))
    if _has(text, KW["status"] + KW["numeric"]) and context_has_places and not leftovers:
        return done("numeric" if _has(text, ["stage", "extraction", "recharge", "दोहन", "उपसा", "ਨਿਕਾਸੀ"]) else "status",
                    conf="medium", followup="same_place")
    if _has(text, KW["status"] + KW["numeric"]):
        # a place is needed; the engine asks for one
        return done("numeric" if _has(text, STRONG_NUMERIC) else "status", conf="low")
    if _has(text, KW["help"]):
        return done("help")
    return out


def _is_status_question(text, mentions):
    """'Is Jaipur safe?' names a category but asks about one place, it is not a list request."""
    if not mentions:
        return False
    if _has(text, KW["list"] + KW["count"] + KW["units_obj"]):
        return False
    return True

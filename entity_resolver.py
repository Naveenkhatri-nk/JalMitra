"""
entity_resolver.py - Find states, districts and assessment units in a question.

The database is the only list of places. Names are matched in this order:
  1. alias table data/place_aliases.csv (local-language names, old names);
     it is a separate file and never changes groundwater values,
  2. exact database spelling (ignoring case, spaces, "_" and "-"),
  3. a phonetic key, so that "Jodhapur", "जोधपुर" and "ਜੋਧਪੁਰ" all reach JODHPUR.
     A phonetic match is always reported back to the user ("I read X as Y").
  4. close spellings (difflib) are NEVER chosen automatically. They are only
     offered as "Did you mean ...?" options.

If a name fits more than one place (for example JAIPUR is a district in
Rajasthan and also a unit in Telangana and in West Bengal), every candidate
is returned and the engine asks the user which one is meant.
"""

import csv
import difflib
import re
import unicodedata
from functools import lru_cache
from pathlib import Path

import database as db

ALIAS_FILE = Path(__file__).resolve().parent / "data" / "place_aliases.csv"

# ------------------------------------------------------------------ words that are never place names

TYPE_WORDS = {
    "district": {"district", "districts", "dist", "zila", "zilla", "jila", "jilla", "zile", "jile",
                 "जिला", "ज़िला", "जिले", "ज़िले", "जिलों", "ज़िलों", "जिल्हा", "जिल्ह्यात", "जिल्ह्यातील",
                 "जिल्ह्याचा", "जिल्ह्याची", "जिल्ह्याचे", "जिल्ह्यांची", "जिल्हे", "जिलो", "जिला", "ਜ਼ਿਲ੍ਹਾ", "ਜ਼ਿਲ੍ਹੇ",
                 "ਜਿਲ੍ਹਾ", "ਜਿਲ੍ਹੇ", "ਜ਼ਿਲ੍ਹਿਆਂ"},
    "unit": {"block", "blocks", "tehsil", "tahsil", "tehsils", "taluka", "talukas", "taluk", "taluks", "mandal",
             "mandals", "unit", "units", "ब्लॉक", "ब्लाक", "ब्लॉकों", "तहसील", "तालुका", "तालुके", "तालुक", "मंडल",
             "प्रखंड", "खंड", "इकाई", "इकाइयों", "ਬਲਾਕ", "ਬਲਾਕਾਂ", "ਤਹਿਸੀਲ", "ਇਕਾਈ"},
    "state": {"state", "states", "rajya", "राज्य", "राज्यों", "राज्यात", "ਰਾਜ", "ਸੂਬਾ", "ਸੂਬੇ"},
}
ALL_TYPE_WORDS = set().union(*TYPE_WORDS.values())

# Connector words: a place after one of these is a second place, not a qualifier.
CONNECTORS = {"and", "vs", "versus", "or", "with", "aur", "ya", "against", "compare", "और", "व", "या", "आणि",
              "किंवा", "ਅਤੇ", "ਤੇ", "ਜਾਂ", "अर", "tatha", "तथा", "से", "se", "than", "ते", "सूं"}

# Common words that are also the names of some assessment units (AUR, CITY,
# NAGAR, MAN, ...). They are only read as places next to a type word
# ("Aur block"). intent_parser adds its own keywords to this list.
BASE_STOPWORDS = {
    # English
    "a", "an", "the", "is", "are", "was", "be", "of", "in", "on", "at", "to", "for", "from", "by", "it", "its",
    "this", "that", "these", "those", "what", "which", "who", "how", "why", "when", "where", "me", "my", "our",
    "we", "you", "your", "i", "do", "does", "did", "can", "could", "please", "tell", "show", "give", "list",
    "about", "and", "or", "vs", "versus", "with", "all", "any", "some", "there", "here", "has", "have", "had",
    "not", "no", "yes", "ok", "okay", "bad", "good", "fine", "poor", "high", "low", "man", "city", "town", "village", "rural", "urban", "north", "south",
    "east", "west", "central", "new", "old", "up", "down", "top", "bar", "pen", "mat", "con", "un", "par",
    "water", "ground", "groundwater", "level", "data", "status", "area", "region", "place", "india", "indian",
    "then", "than", "both", "them", "they", "each", "other", "also", "more", "most", "less", "least", "much",
    "many", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "first", "second",
    "third", "last", "next", "previous", "year", "years", "current", "now", "today", "per", "percent",
    # Hinglish
    "kya", "hai", "hain", "ka", "ki", "ke", "ko", "se", "me", "mein", "mai", "main", "aur", "ya", "bhi", "nahi",
    "na", "to", "toh", "yeh", "ye", "woh", "wo", "iska", "uska", "unka", "inka", "kaisa", "kaisi", "kaise",
    "kitna", "kitni", "kitne", "kahan", "kab", "kaun", "kaunsa", "kaunse", "konse", "konsa", "batao",
    "bataiye", "bataye", "dikhao", "paani", "pani", "jal", "bhujal", "haal", "halat", "wala", "wale", "wali",
    "sabse", "zyada", "jyada", "kam", "dono", "tulna", "karo", "kar", "kijiye", "chahiye", "mera", "meri",
    "mere", "hamara", "hamare", "apna", "abhi", "ab", "tha", "thi", "the", "hota", "hoti", "hote", "raha",
    "rahi", "rahe", "gaya", "gayi", "nagar", "pur", "ganj", "sthiti", "surakshit", "matlab", "achha",
    "accha", "theek", "thik",
    # Phase 6 fix (naveen, 24 Nov): "paani nikal sakta hu" was phonetically read as the place NAYKAL. Everyday verbs,
    # pronouns and misspelled area words must never be matched to a place name (none of them is a place in the DB).
    "nikal", "nikaal", "nikalna", "nikaalna", "nikalne", "nikaalne", "nikalta", "nikalti", "nikale", "sakta",
    "sakti", "sakte", "sakun", "sakoon", "hu", "hoon", "hun", "hoo", "jila", "jile", "jilhe", "jilha", "jilla",
    "jille", "zila", "zile", "zilla", "zille", "zilha", "distric", "distict", "disrict", "borewell", "borwell",
    "bore", "tubewell", "tubwell", "handpump", "kuan", "kuwa", "kua", "khod", "khodna", "khudai", "drill",
    "drilling", "draw", "drawing", "extract", "pump", "pumping", "khet", "kheti", "farm", "field", "sinchai", "lagwa", "lagana", "lagwana", "permission", "anumati",
    "mujhe", "hum", "aap", "tum", "kyu", "kyun", "kyon", "lena", "lene", "dena", "milega", "milta",
    "निकाल", "निकालना", "निकाले", "निकालने", "सकता", "सकती", "सकते", "हूँ", "हूं", "बोरवेल", "ट्यूबवेल", "कुआं",
    "कुआँ", "खोद", "खुदाई", "जिला", "जिले", "ज़िला", "ज़िले", "जिल्हा", "जिल्ह्यात", "अनुमति", "खेत", "मुझे",
    "ਬੋਰਵੈੱਲ", "ਕੱਢ", "ਕੱਢਣਾ", "ਸਕਦਾ", "ਸਕਦੀ", "ਜ਼ਿਲ੍ਹੇ", "ਜ਼ਿਲ੍ਹਾ",
    # Hindi / Marathi / Punjabi / Rajasthani (Devanagari, Gurmukhi)
    "का", "की", "के", "को", "में", "से", "है", "हैं", "था", "थी", "क्या", "और", "या", "भी", "नहीं", "यह", "वह",
    "इस", "उस", "कैसा", "कैसी", "कैसे", "कितना", "कितनी", "कितने", "कहाँ", "कौन", "कौनसे", "कौन-से", "बताओ",
    "बताइए", "दिखाओ", "पानी", "भूजल", "जल", "स्थिति", "हालत", "हाल", "सबसे", "ज़्यादा", "ज्यादा", "कम", "दोनों",
    "तुलना", "करो", "करें", "मेरा", "मेरे", "हमारा", "आहे", "आहेत", "काय", "कसा", "कशी", "कसे", "किती", "मध्ये",
    "मधील", "आणि", "नाही", "सांगा", "कोणते", "कोणत्या", "दाखवा", "पाणी", "पाण्याची", "भूजलाची", "स्थिती",
    "म्हणजे", "दोन्ही", "दोन्हींची", "सर्वात", "सगळ्यात", "ਦਾ", "ਦੀ", "ਦੇ", "ਨੂੰ", "ਵਿੱਚ", "ਵਿਚ", "ਤੋਂ", "ਹੈ", "ਹਨ",
    "ਕੀ", "ਅਤੇ", "ਜਾਂ", "ਵੀ", "ਨਹੀਂ", "ਇਹ", "ਉਹ", "ਕਿਵੇਂ", "ਕਿੰਨਾ", "ਕਿੰਨੀ", "ਕਿੰਨੇ", "ਕਿੱਥੇ", "ਕਿਹੜੇ", "ਦੱਸੋ",
    "ਦਿਖਾਓ", "ਪਾਣੀ", "ਸਥਿਤੀ", "ਹਾਲਤ", "ਸਭ", "ਵੱਧ", "ਘੱਟ", "ਦੋਵਾਂ", "ਦੋਵੇਂ", "ਤੁਲਨਾ", "ਕਰੋ", "ਮੇਰੇ", "ਸਾਡੇ",
    "ਧਰਤੀ", "ਹੇਠਲੇ", "म्हारो", "म्हारा", "म्हारी", "म्हारै", "थारो", "कांई", "कोनी", "सूं", "छै", "रो", "री", "रा",
    "कियां", "कियाँ", "किसो", "कठै", "कितरो", "घणो", "पाणी", "हुवै", "बताओ", "सा",
    "वाले", "वाली", "वाला", "वाळा", "वाळी", "लिए", "बारे", "अंदर", "यहां", "यहाँ", "वहां", "वहाँ", "कुछ", "सब",
    "बहुत", "अभी", "जानकारी", "डेटा", "क्षेत्र", "इलाका", "इलाके", "गांव", "गाँव", "शहर", "कृपया", "होता", "होती",
    "रहा", "रही", "स्तर", "श्रेणी", "प्रकार", "साल", "वर्ष", "हुआ", "हुई", "बदलाव", "कितरा", "बतावो",
    "ਵਾਲੇ", "ਵਾਲਾ", "ਵਾਲੀ", "ਬਾਰੇ", "ਸਾਲ", "ਪਿੰਡ", "ਸ਼ਹਿਰ", "ਜਾਣਕਾਰੀ", "ਡਾਟਾ", "ਕਿਰਪਾ", "ਕਰਕੇ",
    "वाल्या", "बद्दल", "माहिती", "गाव", "शहरात", "वर्षी", "होते",
}

DEVANAGARI_DIGITS = str.maketrans("०१२३४५६७८९੦੧੨੩੪੫੬੭੮੯", "01234567890123456789")

# ------------------------------------------------------------------ transliteration and phonetic key

_DEV = {
    "क": "k", "ख": "kh", "ग": "g", "घ": "gh", "ङ": "n", "च": "ch", "छ": "chh", "ज": "j", "झ": "jh", "ञ": "n",
    "ट": "t", "ठ": "th", "ड": "d", "ढ": "dh", "ण": "n", "त": "t", "थ": "th", "द": "d", "ध": "dh", "न": "n",
    "प": "p", "फ": "ph", "ब": "b", "भ": "bh", "म": "m", "य": "y", "र": "r", "ल": "l", "व": "v", "श": "sh",
    "ष": "sh", "स": "s", "ह": "h", "ळ": "l", "क़": "k", "ख़": "kh", "ग़": "g", "ज़": "z", "ड़": "r", "ढ़": "r",
    "फ़": "f", "य़": "y", "ऱ": "r",
    "अ": "a", "आ": "a", "इ": "i", "ई": "i", "उ": "u", "ऊ": "u", "ऋ": "ri", "ए": "e", "ऐ": "ai", "ओ": "o",
    "औ": "au", "ऑ": "o", "ा": "a", "ि": "i", "ी": "i", "ु": "u", "ू": "u", "ृ": "ri", "े": "e", "ै": "ai",
    "ो": "o", "ौ": "au", "ॉ": "o", "ं": "n", "ँ": "n", "ः": "h", "्": "", "़": "",
    # Gurmukhi
    "ਕ": "k", "ਖ": "kh", "ਗ": "g", "ਘ": "gh", "ਙ": "n", "ਚ": "ch", "ਛ": "chh", "ਜ": "j", "ਝ": "jh", "ਞ": "n",
    "ਟ": "t", "ਠ": "th", "ਡ": "d", "ਢ": "dh", "ਣ": "n", "ਤ": "t", "ਥ": "th", "ਦ": "d", "ਧ": "dh", "ਨ": "n",
    "ਪ": "p", "ਫ": "ph", "ਬ": "b", "ਭ": "bh", "ਮ": "m", "ਯ": "y", "ਰ": "r", "ਲ": "l", "ਵ": "v", "ੜ": "r",
    "ਸ": "s", "ਹ": "h", "ਸ਼": "sh", "ਖ਼": "kh", "ਗ਼": "g", "ਜ਼": "z", "ਫ਼": "f", "ਲ਼": "l",
    "ਅ": "a", "ਆ": "a", "ਇ": "i", "ਈ": "i", "ਉ": "u", "ਊ": "u", "ਏ": "e", "ਐ": "ai", "ਓ": "o", "ਔ": "au",
    "ਾ": "a", "ਿ": "i", "ੀ": "i", "ੁ": "u", "ੂ": "u", "ੇ": "e", "ੈ": "ai", "ੋ": "o", "ੌ": "au",
    "ਂ": "n", "ੰ": "n", "ੱ": "", "੍": "", "਼": "",
}
_NUKTA_PAIRS = {"ड़": "r", "ढ़": "r", "ज़": "z", "फ़": "f", "क़": "k", "ख़": "kh", "ग़": "g",
                "ਸ਼": "sh", "ਜ਼": "z", "ਫ਼": "f", "ਖ਼": "kh", "ਗ਼": "g"}


def transliterate(text):
    """Very simple Devanagari/Gurmukhi -> Latin letters (only used to build matching keys)."""
    text = unicodedata.normalize("NFC", text)
    out, i = [], 0
    while i < len(text):
        pair = text[i:i + 2]
        if pair in _NUKTA_PAIRS:
            out.append(_NUKTA_PAIRS[pair])
            i += 2
            continue
        ch = text[i]
        if ch in "ंँਂੰ" and (i + 1 == len(text) or not text[i + 1].strip()):
            i += 1  # nasal sign at the end of a word is not written in English spellings
            continue
        out.append(_DEV.get(ch, ch if ch.isascii() else ""))
        i += 1
    return "".join(out)


_DIGRAPHS = [("chh", "c"), ("ksh", "ks"), ("sh", "s"), ("ch", "c"), ("ph", "f"), ("bh", "b"), ("dh", "d"),
             ("th", "t"), ("kh", "k"), ("gh", "g"), ("jh", "j"), ("ck", "k"), ("z", "j"), ("q", "k"),
             ("w", "v"), ("x", "ks"), ("y", "i"), ("e", "i"), ("o", "u"), ("h", "")]


def phonetic(text):
    """Spelling-insensitive key: 'Jodhpur', 'Jodhapur', 'जोधपुर' -> 'judpur'."""
    s = re.sub(r"[^a-z]", "", (transliterate(text) if re.search(r"[ऀ-੿]", text) else text).lower())
    for a, b in _DIGRAPHS:
        s = s.replace(a, b)
    if not s:
        return ""
    s = s[0] + s[1:].replace("a", "")       # short/long 'a' is written very differently, drop it
    return re.sub(r"(.)\1+", r"\1", s)       # 'pp' -> 'p'


def alias_key(text):
    text = unicodedata.normalize("NFC", text.translate(DEVANAGARI_DIGITS))
    if re.search(r"[ऀ-੿]", text):
        return re.sub(r"[\s‌‍]+", "", text).replace("़", "").replace("਼", "")
    return db.norm(text)


# ------------------------------------------------------------------ index of places (built once)

def place_key(p):
    return (p["type"], p["state"], p.get("district"), p.get("record_id"))


@lru_cache(maxsize=4)
def _build_index(db_path_key):
    rows = db._query("SELECT record_id, state, district, assessment_unit, assessment_unit_type, year "
                     "FROM groundwater_assessment", (), db_path_key)
    places = []
    seen = set()
    for r in rows:
        places.append({"type": "unit", "state": r["state"], "district": r["district"],
                       "name": r["assessment_unit"], "record_id": r["record_id"], "kind": r["assessment_unit_type"]})
        if (r["state"], r["district"]) not in seen:
            seen.add((r["state"], r["district"]))
            places.append({"type": "district", "state": r["state"], "district": r["district"],
                           "name": r["district"], "record_id": None, "kind": "District"})
    for s in sorted({r["state"] for r in rows}):
        places.append({"type": "state", "state": s, "district": None, "name": s, "record_id": None, "kind": "State"})

    exact, phon = {}, {}
    for p in places:
        exact.setdefault(db.norm(p["name"]), []).append(p)
        k = phonetic(p["name"])
        if len(k) >= 3:
            phon.setdefault(k, []).append(p)
    for alias, target in db.STATE_ALIASES.items():          # NC spellings of state names
        if alias != db.norm(target):
            exact.setdefault(alias, []).extend([x for x in exact.get(db.norm(target), []) if x["type"] == "state"])

    aliases, errors = {}, []
    if ALIAS_FILE.exists():
        with open(ALIAS_FILE, encoding="utf-8") as f:
            for n, row in enumerate(csv.DictReader(f), start=2):
                targets = [p for p in exact.get(db.norm(row["canonical_name"]), [])
                           if (not row.get("target_type") or p["type"] == row["target_type"])
                           and (not row.get("target_state") or p["state"] == row["target_state"])]
                if not targets:
                    errors.append(f"line {n}: '{row['alias']}' -> '{row['canonical_name']}' is not in the database")
                    continue
                aliases.setdefault(alias_key(row["alias"]), []).extend(targets)
    return {"exact": exact, "phon": phon, "aliases": aliases, "errors": errors, "places": places}


def index():
    return _build_index(str(db.get_db_path()))


def alias_errors():
    """Alias rows whose target is not in the database (they are ignored)."""
    return list(index()["errors"])


# ------------------------------------------------------------------ tokenising

_TOKEN = re.compile(r"[A-Za-z0-9]+(?:[-_&][A-Za-z0-9]+)*|[ऀ-ॣ०-ॿ਀-੿]+(?:-[0-9]+)?")
_MR_SUFFIXES = ("मध्ये", "मधील", "ातील", "तील", "ाच्या", "ाचा", "ाची", "ाचे", "च्या", "चा", "ची", "चे", "ात", "ला", "साठी",
                "ਵਿੱਚ", "ਦਾ", "ਦੀ", "ਦੇ")


# Fix (naveen's 300-question test, 25 Nov): everyday words of the six languages that sound like a place name
# ("same" -> SAMI, "agar" (= if) -> AGAR, "कि हर" -> KHAIRA, "सोप्या" -> SUPPI, "ਵੇਲੇ" -> Velhe, "शकते" -> SAKTI).
# They are places only when a type word follows ("Agar block").
BASE_STOPWORDS |= {"ਮੁੱਲ", "ਇਕਾਈ", "म्हारे", "म्हारो", "म्हारी", "म्हारा", "म्हारै", "maine", "jin", "unka", "unki", "liya", 
    "agar", "same", "rank", "ranking", "farak", "farq", "fark", "baare", "bare", "banane", "banana", "karun", "karu",
    "karna", "karne", "karke", "samjhao", "samjhaao", "bolo", "bolti", "bolta", "kyon", "kyun", "kyu",
    # Hindi / Rajasthani
    "अगर", "कि", "हर", "भले", "जुड़े", "जुड़ा", "जुड़ी", "अनुमान", "बिना", "यही", "वही", "स्तरीय", "चिंता", "चिंताजनक",
    "बरसाती", "बरसात", "किसान", "किसानों", "आज", "इण", "घर", "गहराई", "दो", "अर", "ई", "रै", "री", "रो", "सूं",
    "नीचे", "पैला", "करै", "बढ़ै", "बार", "बातां", "पर", "तो", "भी", "ही", "नै", "कठै", "कियां", "कांई", "किण",
    # Punjabi
    "ਕਿ", "ਹਰ", "ਉੱਥੇ", "ਜੁੜਿਆ", "ਜੁੜੇ", "ਸ਼੍ਰੇਣੀ", "ਮਿਲਦੇ", "ਪੱਧਰੀ", "ਵੇਲੇ", "ਪੁਰਾਣੇ", "ਨਾ", "ਹੋਣ", "ਬਣਾ", "ਕੇ",
    "ਲਓ", "ਬਿਨਾਂ", "ਇਹੀ", "ਥਾਂ", "ਅਸਰ", "ਕਰਨ", "ਨਾਲ", "ਕਈ", "ਸਾਲਾਂ", "ਨੇ", "ਵਿੱਚ", "ਦੀ", "ਦਾ", "ਦੇ",
    # Marathi
    "सोप्या", "कोणती", "कोणता", "कोणते", "मूल्य", "करून", "करा", "वाढली", "वाढते", "शकते", "शकतो", "सांगू", "सांगा",
    "सांगत", "शेतीतील", "शेती", "लेल्या", "गृहीत", "पुरावा", "आणि", "किंवा",
}


def tokenize(text):
    text = unicodedata.normalize("NFC", text.translate(DEVANAGARI_DIGITS))
    toks = []
    for m in _TOKEN.finditer(text):
        w = m.group(0)
        toks.append({"text": w, "low": w.lower(), "start": m.start(), "end": m.end(),
                     "indic": bool(re.search(r"[ऀ-੿]", w))})
    # punctuation between tokens (commas are allowed between a place and its qualifier)
    for a, b in zip(toks, toks[1:]):
        b["gap"] = text[a["end"]:b["start"]]
    if toks:
        toks[0]["gap"] = ""
    return toks


def _uniq(places):
    out, seen = [], set()
    for p in places:
        k = place_key(p)
        if k not in seen:
            seen.add(k)
            out.append(p)
    return out


def _lookup(span_text, indic, allow_phonetic):
    """Return (match_type, candidates) for one span of words."""
    idx = index()
    hit = idx["aliases"].get(alias_key(span_text))
    if hit:
        return "alias", _uniq(hit)
    if not indic:
        hit = idx["exact"].get(db.norm(span_text))
        if hit:
            return "exact", _uniq(hit)
    if allow_phonetic:
        key = phonetic(span_text)
        if len(key) >= (4 if indic and " " not in span_text else 3):
            hit = idx["phon"].get(key)
            if hit:
                return "phonetic", _uniq(hit)
    return None, []


# Fix (naveen, 24 Nov): "explain the water cycle" was answered about the block CHICHLI because the English word
# "cycle" has the same phonetic key. A loose (phonetic) match of a Latin-script word is kept only when the spelling is
# really close to the place name, or when the words around it say it is a place ("in Osiyan", "Osiyan block",
# "Osiyan ka", "Osiyan mein"). Exact names and aliases are not affected.
LOCATION_CUES_BEFORE = {"in", "at", "near", "from", "around", "inside", "for"}
LOCATION_CUES_AFTER = {"ka", "ki", "ke", "me", "mein", "mai", "main", "se", "mei", "wala", "wale", "wali"}
PHONETIC_MIN_SIMILARITY = 0.72          # difflib ratio of the typed word and the place name (letters only)
PHONETIC_MIN_SIMILARITY_CUE = 0.5       # with a location cue next to it


def _location_cue(toks, start, end):
    prv = toks[start - 1]["low"] if start > 0 else ""
    nxt = toks[end]["low"] if end < len(toks) else ""
    return prv in LOCATION_CUES_BEFORE or prv in ALL_TYPE_WORDS or nxt in ALL_TYPE_WORDS or nxt in LOCATION_CUES_AFTER


def _close_enough(typed, cands, cue):
    a = db.norm(typed).replace(" ", "")
    need = PHONETIC_MIN_SIMILARITY_CUE if cue else PHONETIC_MIN_SIMILARITY
    return [c for c in cands if difflib.SequenceMatcher(None, a, db.norm(c["name"]).replace(" ", "")).ratio() >= need]


def extract_places(text, stopwords=frozenset()):
    """Find place mentions. Returns a list of mentions:

    {"text": typed words, "match": "alias"|"exact"|"phonetic", "candidates": [place, ...],
     "type_hint": "unit"|"district"|"state"|None, "qualifier": bool, "start": i, "end": j}
    Unmatched content words are returned separately (for "not found" answers).
    """
    stop = BASE_STOPWORDS | set(stopwords)
    toks = tokenize(text)
    mentions, used = [], set()
    i = 0
    while i < len(toks):
        if toks[i]["low"] in ALL_TYPE_WORDS or toks[i]["low"].isdigit():
            i += 1
            continue
        found = None
        # pass 1: alias and exact names only; pass 2: phonetic keys (Latin: single words only),
        # so that "Osian bad" finds OSIAN exactly instead of a phonetic match for the two words
        attempts = [(n, False) for n in (4, 3, 2, 1)] + [(n, True) for n in (4, 3, 2, 1)]
        for length, phonetic_pass in attempts:
            span = toks[i:i + length]
            if phonetic_pass and not span[0]["indic"] and length > 1:
                continue
            if len(span) < length or any(t["low"] in ALL_TYPE_WORDS for t in span):
                continue
            if len({t["indic"] for t in span}) > 1:
                continue
            indic = span[0]["indic"]
            words = [t["text"] for t in span]
            span_text = " ".join(words)
            edge_stop = span[0]["low"] in stop or span[-1]["low"] in stop
            all_stop = all(t["low"] in stop for t in span)
            next_type = (toks[i + length]["low"] if i + length < len(toks) else "") in ALL_TYPE_WORDS
            # common words ("aur", "city", "south east") are places only when a type word follows: "Aur block"
            if ((length == 1 and edge_stop) or all_stop) and not next_type:
                continue
            letters = len(re.sub(r"[^A-Za-z\u0900-\u0A7F]", "", span_text))
            allow_ph = phonetic_pass and (not edge_stop) and letters >= (3 if indic else 4)
            if allow_ph and indic and length > 1 and not next_type:
                allow_ph = False            # "रै नीचे" -> RENI, "सूं पैला" -> SUPPI (300-question test, 25 Nov)
            how, cands = _lookup(span_text, indic, allow_ph)
            if not cands and indic and allow_ph and next_type and length == 1:
                hit = index()["phon"].get(phonetic(span_text))   # short names before a type word: "ਕੋਟਾ ਜ਼ਿਲ੍ਹੇ"
                if hit and len(phonetic(span_text)) >= 3:
                    how, cands = "phonetic", _uniq(hit)
            if not cands and indic:
                for suf in _MR_SUFFIXES:                      # पुण्यात / नाशिकमध्ये / पुणे शहराचा
                    w = span_text
                    if w.endswith(suf) and len(w.split()[-1]) - len(suf) >= 2:
                        how, cands = _lookup(w[: -len(suf)], True, phonetic_pass)
                        if cands:
                            break
            if cands and how == "phonetic" and not indic:
                cands = _close_enough(span_text, cands, _location_cue(toks, i, i + length))
            if cands:
                found = {"text": span_text, "match": how, "candidates": cands, "start": i, "end": i + length,
                         "type_hint": None, "qualifier": False}
                break
        if found:
            nxt = toks[found["end"]]["low"] if found["end"] < len(toks) else ""
            prv = toks[i - 1]["low"] if i > 0 else ""
            for kind, words in TYPE_WORDS.items():
                if nxt in words or (prv in words and kind != "state"):
                    found["type_hint"] = kind
                    break
            mentions.append(found)
            used.update(range(found["start"], found["end"]))
            i = found["end"]
        else:
            i += 1

    # apply type words ("Jaipur district", "Banswara block")
    for m in mentions:
        if m["type_hint"]:
            typed = [c for c in m["candidates"] if c["type"] == m["type_hint"]]
            if typed:
                m["candidates"] = typed

    # a state or district right after a name narrows it ("Ramnagar, Nainital", "Aurangabad Maharashtra")
    for a, b in zip(mentions, mentions[1:]):
        between = [t["low"] for t in toks[a["end"]:b["start"]]]
        if any(w in CONNECTORS for w in between) or len(between) > 2:
            continue
        containers = [c for c in b["candidates"] if c["type"] in ("state", "district")]
        if len(containers) != 1 or b["type_hint"] == "unit":
            continue
        box = containers[0]
        inside = [c for c in a["candidates"] if c is not box and c["state"] == box["state"]
                  and (box["type"] == "state" or (c["type"] == "unit" and c["district"] == box["district"]))]
        if inside:
            a["candidates"] = inside
            b["qualifier"] = True

    leftovers = [t["text"] for n, t in enumerate(toks)
                 if n not in used and t["low"] not in stop and t["low"] not in ALL_TYPE_WORDS
                 and not t["low"].isdigit() and len(t["text"]) >= 3]
    return [m for m in mentions if not m["qualifier"]], leftovers


def suggest(name, limit=5):
    """Close spellings for an unknown name. Only offered, never chosen automatically."""
    idx = index()
    key = db.norm(transliterate(name) if re.search(r"[ऀ-੿]", name) else name)
    if len(key) < 3:
        return []
    names = difflib.get_close_matches(key, list(idx["exact"]), n=limit, cutoff=0.75)
    pk = phonetic(name)
    if len(pk) >= 3:
        names += [db.norm(p["name"]) for k in difflib.get_close_matches(pk, list(idx["phon"]), n=3, cutoff=0.85)
                  for p in idx["phon"][k]]
    out = []
    for n in dict.fromkeys(names):
        out.extend(idx["exact"].get(n, []))
    return _uniq(out)[: limit * 2]


def find_by_name(name, kind=None, state=None):
    """Exact lookup used by the clarification step."""
    cands = index()["exact"].get(db.norm(name), [])
    return [c for c in cands if (not kind or c["type"] == kind) and (not state or c["state"] == state)]


def district_of(place):
    """The district entry (from the database index) that contains an assessment unit, or None."""
    if place.get("type") != "unit":
        return place if place.get("type") == "district" else None
    for p in index()["places"]:
        if p["type"] == "district" and p["state"] == place["state"] and p["district"] == place["district"]:
            return p
    return None

"""
answer_verifier.py - checks an LLM-written explanation before JalMitra shows it (JalMitra 4.0 Phase 3).

The LLM may only re-word verified facts (the template answer built from groundwater.db) and quote
approved documents (retrieved RAG passages). verify() rejects the text when:

  * it contains a number, percentage or year (Latin, Devanagari or Gurmukhi digits) that is not in
    the facts or the cited passages,
  * it uses a quantity word (hundred, lakh, crore, सौ, लाख, ...) that the facts / passages do not use,
  * it names a groundwater category (in any of the six languages) that is not in the facts
    (for an answer about a place) or not in the facts / passages (for a general explanation),
  * it contains instruction-like or injected text (prompt talk, "ignore", URLs, code, <think>),
  * it is empty, too long, or mostly in the wrong script for the chosen language.

Standard library only. Nothing here changes the facts; a rejected text is simply not shown.
"""

import re
from dataclasses import dataclass, field

CATEGORIES = ["Safe", "Semi-critical", "Critical", "Over-exploited", "Saline"]

# category words, longest / most specific first ("semi-critical" before "critical")
CATEGORY_WORDS = {
    "Semi-critical": ["semi-critical", "semi critical", "semicritical", "अर्ध-गंभीर", "अर्ध गंभीर", "अर्धगंभीर",
                      "अर्ध-संकटपूर्ण", "ਅਰਧ-ਗੰਭੀਰ", "ਅਰਧ ਗੰਭੀਰ"],
    "Over-exploited": ["over-exploited", "over exploited", "overexploited", "अतिदोहित", "अति-दोहित", "अति दोहित",
                       "अतिशोषित", "अति-शोषित", "अति शोषित", "ਵੱਧ-ਸ਼ੋਸ਼ਿਤ", "ਵੱਧ ਸ਼ੋਸ਼ਿਤ", "ਅਤਿ-ਸ਼ੋਸ਼ਿਤ", "ਵਧ-ਸ਼ੋਸ਼ਿਤ"],
    "Critical": ["critical", "गंभीर", "संकटपूर्ण", "ਗੰਭੀਰ"],
    "Saline": ["saline", "लवणीय", "खारा", "खारो", "खारे", "क्षारयुक्त", "ਖਾਰਾ", "ਖਾਰੇ"],
    "Safe": ["safe", "surakshit", "सुरक्षित", "ਸੁਰੱਖਿਅਤ"],
}

QUANTITY_WORDS = ["hundred", "thousand", "lakh", "lakhs", "crore", "crores", "million", "billion", "half", "double",
                  "twice", "triple", "dozen", "सौ", "हज़ार", "हजार", "लाख", "करोड़", "करोड", "आधा", "दोगुना",
                  "दुगना", "शंभर", "हजारो", "ਸੌ", "ਹਜ਼ਾਰ", "ਲੱਖ", "ਕਰੋੜ", "ਅੱਧਾ", "ਦੁੱਗਣਾ", "सैकड़ा", "सौ गुणा",
                  # number words that are not also everyday words ("one"/"एक" = "a", "दो" = "give" are left out)
                  "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve", "fifteen",
                  "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety",
                  "तीन", "चार", "पांच", "पाँच", "छह", "सात", "आठ", "ग्यारह", "बारह", "पंद्रह", "बीस", "तीस",
                  "चालीस", "पचास", "साठ", "सत्तर", "अस्सी", "नब्बे", "एकादश", "द्वादश", "दशक", "पाच", "सहा", "नऊ",
                  "दहा", "अकरा", "बारा", "वीस", "तीस", "पन्नास", "ਤਿੰਨ", "ਚਾਰ", "ਪੰਜ", "ਛੇ", "ਸੱਤ", "ਅੱਠ", "ਨੌਂ",
                  "ਦਸ", "ਗਿਆਰਾਂ", "ਬਾਰਾਂ", "ਵੀਹ", "ਤੀਹ", "ਪੰਜਾਹ"]

INJECTION_OUT = re.compile(
    r"ignore\s+(all\s+|the\s+|any\s+|your\s+)?(previous|prior|above|earlier|instructions|rules)|disregard|"
    r"system\s*prompt|you\s+are\s+now|as\s+an\s+ai\b|jailbreak|developer\s+mode|new\s+instructions|"
    r"<\s*/?\s*(think|script|system|im_start|im_end)|https?://|www\.|```|\bselect\s+.+\bfrom\b|drop\s+table|"
    r"निर्देश(ों)?\s*(को)?\s*(भूल|अनदेखा)|नियम\s*भूल|सूचना\s*विसरा|ਹਦਾਇਤਾਂ\s*ਭੁੱਲ",
    re.IGNORECASE | re.DOTALL)

DIGITS = str.maketrans("०१२३४५६७८९੦੧੨੩੪੫੬੭੮੯", "01234567890123456789")
_NUM = re.compile(r"(?<![\w.])(\d{1,3}(?:,\d{2,3})+(?:\.\d+)?|\d+(?:\.\d+)?)")
_DEVANAGARI = re.compile(r"[ऀ-ॿ]")
_GURMUKHI = re.compile(r"[਀-੿]")
_LATIN = re.compile(r"[A-Za-z]")
SCRIPT = {"hi": "deva", "raj": "deva", "mr": "deva", "pa": "guru", "en": "latin", "hinglish": "latin"}
MAX_CHARS = 1400


@dataclass
class VerifyResult:
    ok: bool
    reasons: list = field(default_factory=list)
    numbers: list = field(default_factory=list)
    unsupported_numbers: list = field(default_factory=list)
    categories: list = field(default_factory=list)
    unsupported_categories: list = field(default_factory=list)
    key_figures_missing: list = field(default_factory=list)


def numbers_in(text):
    """Every number in the text as a float (Indian digit grouping, decimals, Devanagari/Gurmukhi digits)."""
    out = []
    for m in _NUM.finditer((text or "").translate(DIGITS)):
        try:
            out.append(float(m.group(1).replace(",", "")))
        except ValueError:
            pass
    return out


def _norm(text):
    return " " + re.sub(r"\s+", " ", (text or "").lower()) + " "


def _has_word(text, word):
    return re.search(r"(?<![\wऀ-੿-])" + re.escape(word.lower()) + r"(?![\wऀ-੿-])", text) is not None


def categories_in(text):
    """Categories named in the text (a word inside a longer category phrase is not counted twice)."""
    t = _norm(text)
    found = []
    for cat in ["Semi-critical", "Over-exploited", "Critical", "Saline", "Safe"]:
        for w in CATEGORY_WORDS[cat]:
            if _has_word(t, w):
                found.append(cat)
                t = re.sub(re.escape(w.lower()), " ", t)      # "semi-critical" must not also count as "critical"
                break
    return found


# Phase 6: "no / zero / none" added ("there are no units in the Saline category"); a negated category that the
# evidence shows as PRESENT is rejected separately (jalmitra_ai.negated_but_present).
NEGATION = re.compile(r"(?:\bnot|\bno longer|\bisn't|\bnahi|\bnahin|\bnahee|नहीं|नही|नाही|ਨਹੀਂ|कोनी|\bna|\bno|\bzero|"
                      r"\bnone)\s*(?:\S+\s+){0,3}$", re.I)


def categories_asserted(text):
    """Categories the text assigns, ignoring negated mentions ('is not Safe', 'Critical nahi hai',
    'सुरक्षित नहीं'). Phase 5: negations were wrongly rejected as foreign categories."""
    t = _norm(text)
    # "safe limit", "safely", "safe level" describe a limit, not the Safe category (Phase 6)
    t = re.sub(r"\bsafe(ly)?\s+(limit|limits|level|levels|yield|threshold|range)\b|\bsafely\b|सुरक्षित\s+(सीमा|रूप)|"
               r"surakshit\s+seema", " ", t)
    out = []
    for cat in ["Semi-critical", "Over-exploited", "Critical", "Saline", "Safe"]:
        for w in CATEGORY_WORDS[cat]:
            for m in re.finditer(r"(?<![\wऀ-੿-])" + re.escape(w.lower()) + r"(?![\wऀ-੿-])", t):
                before, after = t[max(0, m.start() - 25):m.start()], t[m.end():m.end() + 22]
                negated = NEGATION.search(before) or re.match(
                    r"\s*(?:category\s+|श्रेणी\s+|ਸ਼੍ਰੇਣੀ\s+)?(?:nahi|nahin|नहीं|नही|नाही|ਨਹੀਂ|कोनी|(?:is|was)\s+not)\b", after)
                if not negated:
                    out.append(cat)
                    break
            t = re.sub(re.escape(w.lower()), " ", t)
            if cat in out:
                break
    return out


def quantity_words_in(text):
    t = _norm(text)
    return [w for w in QUANTITY_WORDS if _has_word(t, w)]


def repetitive(text):
    """A token repeated 4+ times in a row, or one word making up over a quarter of a longer text."""
    toks = re.findall(r"[\wऀ-੿]+", (text or "").lower())
    run = 1
    for a, b in zip(toks, toks[1:]):
        run = run + 1 if a == b else 1
        if run >= 4:
            return True
    if len(toks) >= 20:
        top = max(toks.count(t) for t in set(toks) if len(t) > 2) if any(len(t) > 2 for t in toks) else 0
        return top / len(toks) > 0.25
    return False


def script_ok(text, lang):
    want = SCRIPT.get(lang)
    if not want:
        return True
    letters = {"deva": len(_DEVANAGARI.findall(text)), "guru": len(_GURMUKHI.findall(text)),
               "latin": len(_LATIN.findall(text))}
    total = sum(letters.values()) or 1
    return letters[want] / total >= 0.5


def verify(text, facts, passages=(), lang="en", fact_categories=None, key_figures=None, place_answer=True):
    """facts: verified fact text (template answer + table values). passages: list of passage texts that
    the answer may quote. fact_categories: categories of the records in the facts. key_figures: official
    numbers that should appear (only reported, because the data table is always shown next to the text).
    place_answer: False for a general explanation (then categories may come from the passages)."""
    reasons = []
    text = re.sub(r"\[\d{1,2}\]", " ", text or "")        # citation markers [1], [2] are not numbers
    if not text.strip():
        return VerifyResult(False, ["empty text"])
    if len(text) > MAX_CHARS:
        reasons.append(f"too long ({len(text)} chars)")
    if INJECTION_OUT.search(text):
        reasons.append("instruction-like or injected text in the output")
    if not script_ok(text, lang):
        reasons.append(f"wrong script for language '{lang}'")
    if repetitive(text):
        reasons.append("repetitive / degenerate text")

    passage_text = "\n".join(passages or [])
    allowed = set(numbers_in(facts)) | set(numbers_in(passage_text))
    nums = numbers_in(text)
    bad_nums = sorted({n for n in nums if n not in allowed})
    if bad_nums:
        reasons.append("numbers not in the facts or sources: " + ", ".join(f"{n:g}" for n in bad_nums))

    src_q = set(quantity_words_in(facts + "\n" + passage_text))
    bad_q = [w for w in quantity_words_in(text) if w not in src_q]
    if bad_q:
        reasons.append("quantity words not in the facts or sources: " + ", ".join(bad_q))

    cats = categories_asserted(text)
    # categories of the records when given (template wording like "सुरक्षित रूप से" = "safely" is not a category);
    # otherwise the categories named in the fact text (e.g. a category definition)
    allowed_cats = set(fact_categories) if fact_categories else set(categories_in(facts))
    if not place_answer:
        allowed_cats |= set(categories_in(passage_text))
    bad_cats = [c for c in cats if c not in allowed_cats]
    if bad_cats:
        reasons.append("categories not in the facts: " + ", ".join(bad_cats))

    missing = [k for k in (key_figures or []) if k is not None and float(k) not in set(nums)]
    return VerifyResult(not reasons, reasons, nums, bad_nums, cats, bad_cats, missing)

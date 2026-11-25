"""
semantic_gate.py - meaning checks for AI explanations (JalMitra 4.0 Phase 4).

answer_verifier.py checks numbers, categories, places and form. It cannot see that a sentence says the
opposite of its source: in Phase 3 a verified Hindi explanation said the water table becomes DEEPER in the
monsoon, while the cited passage (NC2025, PDF page 57) says it is deeper BEFORE the monsoon and shallow
during it. This module adds three layers; any one of them can reject, none can approve on its own:

  1. rules      curated groundwater direction / definition facts (en, hi, hinglish; some mr / pa words):
                monsoon recharge raises the water level (reduces depth to water); extraction above recharge
                means depletion, not a rise; stage of extraction = extraction / annual extractable resource;
                category limits (Safe <= 70 %, Semi-critical 70-90 %, Critical 90-100 %, Over-exploited > 100 %);
                recharge vs extraction comparisons against the database figures; unsupported causes
                (climate change, industries, mining, ...) that the sources do not mention.
  2. support    every sentence must be supported by the fact block or a cited passage: embedding similarity
                (bge-m3 through Ollama, cross-lingual) or key-term overlap above a threshold. If the
                embedding model cannot be reached the check FAILS CLOSED (the explanation is not shown).
  3. self-check optional (JALMITRA_SELF_CHECK=1): the LLM is asked whether the text contradicts or goes beyond
                the sources; NOT_SUPPORTED rejects, anything else changes nothing.

check(text, facts, passages, lang, table=None, embedder=None, self_checker=None) -> GateResult
"""

import json
import math
import os
import re
import urllib.request
from dataclasses import dataclass, field

import answer_verifier as av

SIM_THRESHOLD = 0.60          # tuned on eval/semantic_cases (see eval/semantic_factuality.py)
CAUSAL_OVERLAP = True         # word-overlap check for causal sentences (layer 1)
OVERLAP_THRESHOLD = 0.60

# ------------------------------------------------------------------ word lists
MONSOON = ["monsoon", "monsoons", "rainy season", "rainy-season", "during the rains", "during rains", "rains",
           "मानसून", "मॉनसून", "बरसात", "बारिश", "वर्षा ऋतु", "वर्षा काल", "बरसात के मौसम",
           "barish", "baarish", "barsaat", "barsat", "pawsala",
           "पावसाळ", "पावसाळा", "पावसाळ्यात", "मान्सून", "ਮਾਨਸੂਨ", "ਬਰਸਾਤ", "ਬਾਰਿਸ਼", "ਮੀਂਹ"]
NOT_DURING = ["pre-monsoon", "pre monsoon", "premonsoon", "before the monsoon", "before monsoon", "after the monsoon",
              "after monsoon", "post-monsoon", "post monsoon", "postmonsoon", "after the rains", "summer", "dry season",
              "के बाद", "से पहले", "पूर्व", "गर्मी", "ke baad", "se pehle", "se pahle", "garmi",
              "नंतर", "आधी", "उन्हाळ", "ਤੋਂ ਬਾਅਦ", "ਤੋਂ ਪਹਿਲਾਂ", "ਗਰਮੀ"]
LEVEL = ["water table", "water level", "water-level", "groundwater level", "ground water level", "level of groundwater",
         "level of ground water", "depth to water", "depth of water", "water depth",
         "भूजल तल", "भूजल स्तर", "भू-जल स्तर", "जल स्तर", "जलस्तर", "जल तल", "पानी का स्तर", "पानी का तल", "भूजल का स्तर",
         "jal star", "jalstar", "paani ka level", "pani ka level", "paani ka star", "pani ka star", "water ka level",
         "भूजल पातळी", "पाणी पातळी", "जलपातळी", "ਪਾਣੀ ਦਾ ਪੱਧਰ", "ਜਲ ਪੱਧਰ", "ਧਰਤੀ ਹੇਠਲੇ ਪਾਣੀ ਦਾ ਪੱਧਰ"]
DOWN = ["falls", "fall", "falling", "drops", "drop", "dropping", "declines", "decline", "declining", "goes down",
        "go down", "deeper", "deepens", "deepen", "lowers", "lowered", "decreases", "decrease", "sinks",
        "गिरता", "गिरती", "गिर", "घटता", "घटती", "घट", "नीचे", "गहरा", "गहरी", "गहरे", "कम हो",
        "girta", "girti", "gir jata", "ghat", "ghatta", "neeche", "niche", "gehra", "gahra", "kam ho",
        "खाली जाते", "खोल", "घटते", "ਡਿੱਗ", "ਘਟ", "ਡੂੰਘਾ", "ਹੇਠਾਂ",
        "ਘੱਟ", "ਡੂੰਘੀ", "ਡੂੰਘੇ", "कमी होते", "कमी होत", "खाली जाते", "गहरो", "नीचो"]     # Phase 6 (pa / mr / raj)
DEPTH_UP = [r"depth[^.।]{0,25}(increase|increases|rises|grows|goes up)", r"गहराई[^.।]{0,20}(बढ़|बढ)",
            r"gehrai[^.]{0,20}badh"]
UP = ["rises", "rise", "rising", "raises", "raise", "raising", "goes up", "go up", "increases", "increase",
      "improves", "improve", "shallower",
      "recovers", "बढ़ता", "बढ़ती", "बढ़", "बढता", "ऊपर", "सुधर", "badhta", "badhti", "badh", "upar", "sudhar",
      "वाढ", "ਵਧ", "ਉੱਪਰ"]
EXTRACTION = ["extraction", "extracted", "withdrawal", "pumping", "draft", "दोहन", "निकासी", "उपसा", "dohan", "nikasi",
              "nikala", "ਨਿਕਾਸੀ", "ਕੱਢ"]
RECHARGE = ["recharge", "recharged", "replenish", "पुनर्भरण", "रिचार्ज", "पुनर्भरित", "punarbharan", "ਰੀਚਾਰਜ",
            "ਮੁੜ ਭਰ"]
EXTRACTABLE = ["extractable", "available resource", "निकासी योग्य", "निकालने योग्य", "उपसा योग्य", "nikasi yogya",
               "ਕੱਢਣਯੋਗ", "ਕੱਢਣ ਯੋਗ"]
MORE = ["more than", "greater than", "higher than", "exceeds", "exceed", "exceeding", "above", "over",
        "से अधिक", "से ज़्यादा", "से ज्यादा", "अधिक", "se zyada", "se jyada", "zyada", "jyada", "पेक्षा जास्त",
        "ਤੋਂ ਵੱਧ", "ਵੱਧ"]
LESS = ["less than", "lower than", "below", "smaller than", "से कम", "se kam", "पेक्षा कमी", "ਤੋਂ ਘੱਟ"]
GOOD_OUTCOME = ["safe", "surplus", "rises", "rise", "rising", "goes up", "keeps rising", "improves", "improve",
                "increase in level", "sufficient",
                "सुरक्षित", "बढ़ता", "सुधर", "पर्याप्त", "surakshit", "badhta", "sudhar", "paryapt", "ਸੁਰੱਖਿਅਤ", "ਵਧਦਾ"]
DIVIDE = [r"divided by", r"÷", r"/", r"से भाग", r"का अनुपात", r"bhaag", r"ratio of"]
CAUSAL = ["because", "due to", "caused by", "as a result of", "owing to", "क्योंकि", "के कारण", "की वजह से",
          "वजह से", "कारण", "kyunki", "kyonki", "ki wajah se", "wajah se", "ke karan", "karan", "मुळे",
          "ਕਿਉਂਕਿ", "ਕਾਰਨ", "ਵਜ੍ਹਾ"]
RISKY_CAUSES = ["climate change", "global warming", "industries", "industry", "factories", "factory", "mining",
                "sand mining", "population growth", "population", "deforestation", "urbanisation", "urbanization",
                "drought", "el nino", "pollution", "जलवायु परिवर्तन", "ग्लोबल वार्मिंग", "उद्योग", "कारखान", "खनन",
                "जनसंख्या", "वनों की कटाई", "शहरीकरण", "सूखा", "प्रदूषण", "jalvayu", "factory", "fectory",
                "khanan", "aabadi", "jansankhya", "ਉਦਯੋਗ", "ਫੈਕਟਰੀ", "ਆਬਾਦੀ", "ਸੋਕਾ"]
STOP = set("""the a an is are was were be been of to in on for and or with that this it its by as at from into than
which who whom their there these those will would can could should may might has have had not no but also very
more most less such about over under per each every any all some other only then so if when while where how what
groundwater ground water block district state area year years annual means mean meaning called
है हैं था थे का की के को में से पर और या यह वह इस उस एक भी तो जो कि होता होती होते हुआ गया गई रहा रही रहे
तक लिए साथ बहुत अधिक कम भूजल पानी जल ब्लॉक जिले ज़िले राज्य
hai hain tha the ka ki ke ko mein me se par aur ya yeh woh is us ek bhi to jo hota hoti hote gaya rahi raha
liye saath bahut paani pani block jile""".split())

CAT_RANGE = {"Safe": (0, 70), "Semi-critical": (70, 90), "Critical": (90, 100), "Over-exploited": (100, 10 ** 6)}
PCT = re.compile(r"(\d+(?:\.\d+)?)\s*(%|percent|per cent|प्रतिशत|टक्के|ਪ੍ਰਤੀਸ਼ਤ|pratishat)", re.I)


@dataclass
class GateResult:
    ok: bool
    reasons: list = field(default_factory=list)
    rule_hits: list = field(default_factory=list)
    unsupported: list = field(default_factory=list)
    similarities: list = field(default_factory=list)
    self_check: str = None


# ------------------------------------------------------------------ helpers
def sentences(text):
    text = re.sub(r"\[\d{1,2}\]", " ", text or "")
    parts = re.split(r"(?<=[.!?।])\s+|\n+", text)
    return [p.strip() for p in parts if len(re.findall(r"[\wऀ-੿]+", p)) >= 3]


# Phase 6: "पर" / "par" removed - mostly the postposition "on" ("आमतौर पर", "स्तर पर"), it cut "monsoon ... level"
# apart from "... goes deeper" and hid wrong monsoon claims in Hindi / Rajasthani.
CLAUSE_SPLIT = re.compile(r",|;|:|\s(?:and|but|while|whereas|whereas|और|लेकिन|जबकि|aur|lekin|jabki|आणि|पण|"
                          r"ਅਤੇ|ਪਰ|अर)\s")


def clauses(s):
    return [c for c in CLAUSE_SPLIT.split(s) if c and c.strip()]


def _norm(s):
    return " " + re.sub(r"\s+", " ", (s or "").lower()) + " "


def _has(s, words):
    t = _norm(s)
    for w in words:
        w = w.lower()
        if re.search(r"[ऀ-੿]", w):           # Indic: substring (suffixes are common)
            if w in t:
                return True
        elif re.search(r"(?<![a-z-])" + re.escape(w) + r"(?![a-z-])", t):
            return True
    return False


def _positions(s, words):
    t = _norm(s)
    out = []
    for w in words:
        w = w.lower()
        pat = re.escape(w) if re.search(r"[ऀ-੿]", w) else r"(?<![a-z-])" + re.escape(w) + r"(?![a-z-])"
        out += [(m.start(), m.end()) for m in re.finditer(pat, t)]
    return out


def near(s, a_words, b_words, window=45):
    """Some word of A and some word of B within `window` characters of each other."""
    A, B = _positions(s, a_words), _positions(s, b_words)
    return any(abs(b0 - a1) <= window or abs(a0 - b1) <= window for a0, a1 in A for b0, b1 in B)


def _first(s, words):
    t = _norm(s)
    best = None
    for w in words:
        i = t.find(w.lower())
        if i >= 0 and (best is None or i < best):
            best = i
    return best


def _script(s):
    deva, guru = len(re.findall(r"[ऀ-ॿ]", s or "")), len(re.findall(r"[਀-੿]", s or ""))
    latin = len(re.findall(r"[A-Za-z]", s or ""))
    return max((latin, "latin"), (deva, "deva"), (guru, "guru"))[1]


def tokens(s):
    return [t for t in re.findall(r"[a-zऀ-੿]{3,}", (s or "").lower()) if t not in STOP]


USE_WORDS = ["used", "use", "using", "usage", "taken out", "drawn", "pumped", "withdrawn", "overuse", "over-use",
             "उपयोग", "इस्तेमाल", "निकाला", "निकाल", "वापर", "उपसा", "ਵਰਤੋਂ", "ਵਰਤਿਆ", "ਕੱਢਿਆ", "nikala", "istemal"]


# ------------------------------------------------------------------ layer 1: rules
def rule_check(text, facts="", passages=(), table=None):
    hits = []
    source_text = (facts or "") + "\n" + "\n".join(passages or [])
    rech_ext = _table_recharge_extraction(table)
    for s in sentences(text):
        low = _norm(s)
        # 1. monsoon: water level goes down / gets deeper / depth increases DURING the monsoon -> wrong
        # checked per clause: "deeper in the monsoon AND falls after it" has a wrong first half
        for c in clauses(s):
            if _has(c, MONSOON) and not _has(c, NOT_DURING):
                if near(c, LEVEL, DOWN) or any(re.search(p, _norm(c)) for p in DEPTH_UP):
                    hits.append(("monsoon_direction", s))
                    break
        # 2. recharge lowers the water level -> wrong ; extraction raises it -> wrong
        # Phase 6: "used faster than it can recharge, so the level may drop" blames use, not recharge
        if _has(s, RECHARGE) and near(s, LEVEL, DOWN) and not _has(s, EXTRACTION + USE_WORDS) \
                and not _has(s, ["not", "नहीं", "nahi", "ਨਹੀਂ"]):
            hits.append(("recharge_direction", s))
        if _has(s, EXTRACTION) and near(s, LEVEL, UP) and not _has(s, RECHARGE) \
                and not _has(s, ["reduce", "reduced", "less", "कम", "kam", "ਘੱਟ", "stop", "control"]):
            hits.append(("extraction_direction", s))
        # 3. extraction more than recharge -> depletion (not safe / not rising)
        e, r = _first(s, EXTRACTION), _first(s, RECHARGE)
        s_out = re.sub(r"(beyond|above|within|exceed\w*|cross\w*)\s+(the\s+)?safe\s+limits?|safe\s+limits?", " ", s,
                       flags=re.I)                                   # "beyond safe limits" is not a good outcome
        if e is not None and r is not None and _has(s, MORE) and e < r and _has(s_out, GOOD_OUTCOME) \
                and not _has(s, ["not", "नहीं", "nahi", "ਨਹੀਂ", "no longer"]):
            hits.append(("depletion_direction", s))
        # 3b. remedies that are the opposite of the reports' advice; rain "does not matter"
        if _has(s, ["reduce", "reduced", "reducing", "control", "कम", "kam", "ਘਟਾ", "रोक"]) and \
                _has(s, ["depletion", "deplet", "कमी", "गिरावट", "ghatna", "ਘਾਟ"]) and \
                re.search(r"(pump\w*|extract\w*|draw\w*)\s+more|more\s+(borewells?|tube\s*wells?|wells|pumps?)|"
                          r"(drill\w*|build\w*|dig\w*)\s+more|ज़्यादा\s+(पानी\s+)?निकाल|अधिक\s+(पानी\s+)?निकाल|"
                          r"zyada\s+(paani\s+)?nikal|ज़्यादा\s+बोरवेल|अधिक\s+बोरवेल", _norm(s)):
            hits.append(("wrong_remedy", s))
        if _has(s, MONSOON + ["rain", "rainfall", "बारिश", "वर्षा"]) and re.search(
                r"(do|does)\s*(not|n't)\s+(matter|affect|help|contribute)|no\s+(effect|role|impact)|not\s+important|"
                r"irrelevant|कोई\s+(असर|फर्क|भूमिका)\s+नहीं|फर्क\s+नहीं|koi\s+(asar|fark)\s+nahi|"
                r"असर\s+(नहीं|नहि|कोनी)|(नहीं|नहि|कोनी)\s+(कांई\s+|कोई\s+)?असर|ਅਸਰ\s+ਨਹੀਂ|ਕੋਈ\s+ਅਸਰ\s+ਨਹੀਂ|"
                r"परिणाम\s+(होत\s+)?नाही", _norm(s)):          # Phase 6: Rajasthani / Punjabi / Marathi forms
            hits.append(("rain_irrelevant", s))
        # 4. stage of extraction formula: extraction / extractable (not recharge / extraction etc.)
        for d in DIVIDE:
            m = re.search(r"([^.।]{0,60})" + d + r"([^.।]{0,60})", low)
            if m and _has(s, ["stage", "स्तर", "टप्पा", "ਪੱਧਰ"]):
                num, den = m.group(1), m.group(2)
                if (_has(den, EXTRACTION) and not _has(den, EXTRACTABLE)) and _has(num, RECHARGE + EXTRACTABLE):
                    hits.append(("stage_formula", s))
                elif _has(num, RECHARGE) and not _has(num, EXTRACTION) and _has(den, EXTRACTION + EXTRACTABLE):
                    hits.append(("stage_formula", s))
                break
        # 5. category limits
        # Phase 6: asserted categories only - "above the safe limit of 100%" / "not Safe" do not name the Safe category
        cats = [c for c in av.categories_asserted(s) if c in CAT_RANGE]
        pcts = [float(x) for x, _ in PCT.findall(s.translate(av.DIGITS))]
        if len(cats) == 1 and pcts:
            lo, hi = CAT_RANGE[cats[0]]
            if any(p < lo - 0.01 or p > hi + 0.01 for p in pcts):
                hits.append(("category_threshold", s))
        # 6. recharge vs extraction comparison against the database figures
        if rech_ext and r is not None and e is not None:
            rech, ext = rech_ext
            more, less = _has(s, MORE), _has(s, LESS)
            first_is_r = r < e
            # Indian languages put the compared-against term first: "पुनर्भरण से निकासी अधिक" = extraction > recharge.
            # The term right before the "than" marker (से / ਤੋਂ / पेक्षा / se) is the smaller one (Phase 6).
            than = re.search(r"(?<![\wऀ-੿])(से|ਤੋਂ|पेक्षा|सूं|se|son)(?![\wऀ-੿])", low)
            if than:
                before = low[:than.start()]
                pe = max((before.rfind(w.lower()) for w in EXTRACTION), default=-1)
                pr = max((before.rfind(w.lower()) for w in RECHARGE), default=-1)
                if pe >= 0 or pr >= 0:
                    smaller_is_r = pr > pe
                    first_is_r = not smaller_is_r     # reuse the English logic: "X more than Y" with X first
            claims_r_more = (first_is_r and more and not less) or (not first_is_r and less and not more)
            claims_e_more = (not first_is_r and more and not less) or (first_is_r and less and not more)
            if claims_r_more and rech < ext or claims_e_more and ext < rech:
                hits.append(("contradicts_figures", s))
        # 7. causes the sources never mention (only in sentences that state a cause)
        if _has(s, CAUSAL):
            for w in RISKY_CAUSES:
                if _has(s, [w]) and w.lower() not in source_text.lower():
                    hits.append(("unsupported_cause", s))
                    break
            # word overlap only works within one script (Marathi words vs English reports: the cross-lingual
            # embedding check in layer 2 handles that case)
            if CAUSAL_OVERLAP and _script(s) == _script(source_text):
                toks = [t for t in tokens(s) if not re.match(r"^\d", t)]
                src = set(tokens(source_text))
                if toks and sum(1 for t in toks if t in src) / len(toks) < 0.4:
                    hits.append(("unsupported_causal_claim", s))
    return hits


def _table_recharge_extraction(table):
    for row in table or []:
        if isinstance(row, dict) and row.get("annual_recharge_ham") is not None \
                and row.get("total_extraction_ham") is not None and len(table) == 1:
            return float(row["annual_recharge_ham"]), float(row["total_extraction_ham"])
    return None


# ------------------------------------------------------------------ layer 2: support
def ollama_embedder(texts):
    url = os.environ.get("JALMITRA_OLLAMA_URL", "http://localhost:11434").rstrip("/")
    model = os.environ.get("JALMITRA_EMBED_MODEL", "bge-m3")
    body = json.dumps({"model": model, "input": list(texts),
                       "keep_alive": os.environ.get("JALMITRA_KEEP_ALIVE", "30m")}).encode()
    req = urllib.request.Request(url + "/api/embed", data=body, method="POST",
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=float(os.environ.get("JALMITRA_RAG_TIMEOUT", "15"))) as r:
        return json.loads(r.read())["embeddings"]


def _cos(a, b):
    na, nb = math.sqrt(sum(x * x for x in a)), math.sqrt(sum(x * x for x in b))
    return sum(x * y for x, y in zip(a, b)) / (na * nb) if na and nb else 0.0


def support_check(text, facts, passages=(), embedder=None, sim_threshold=None, overlap_threshold=None):
    """Return (unsupported_sentences, [(sentence, best_similarity, overlap)]) ; raises when the embedder fails."""
    sim_t = SIM_THRESHOLD if sim_threshold is None else sim_threshold
    ov_t = OVERLAP_THRESHOLD if overlap_threshold is None else overlap_threshold
    sents = sentences(text)
    units = sentences(facts) + [s for p in (passages or []) for s in sentences(p)]
    if not sents:
        return [], []
    if not units:
        return sents, [(s, 0.0, 0.0) for s in sents]
    vecs = (embedder or ollama_embedder)(sents + units)
    sv, uv = vecs[:len(sents)], vecs[len(sents):]
    src_tokens = set(tokens(" ".join(units)))
    out, bad = [], []
    for s, v in zip(sents, sv):
        best = max(_cos(v, u) for u in uv)
        toks = tokens(s)
        ov = sum(1 for t in toks if t in src_tokens) / len(toks) if toks else 1.0
        out.append((s, round(best, 3), round(ov, 2)))
        if best < sim_t and ov < ov_t:
            bad.append(s)
    return bad, out


# ------------------------------------------------------------------ layer 3: self-check (reject-only)
SELF_CHECK_PROMPT = """You check a short groundwater explanation against its sources. Reply with exactly one word:
NOT_SUPPORTED if any statement contradicts the FACTS or PASSAGES or adds a claim they do not support
(for example a direction like rising/falling, a cause, or a comparison), otherwise SUPPORTED."""


def llm_self_check(text, facts, passages, provider):
    msgs = [{"role": "system", "content": SELF_CHECK_PROMPT},
            {"role": "user", "content": f"FACTS:\n<<<\n{facts}\n>>>\n\nPASSAGES:\n<<<\n" + "\n---\n".join(passages or [])
             + f"\n>>>\n\nEXPLANATION:\n<<<\n{text}\n>>>"}]
    res = provider.chat(msgs, temperature=0, max_tokens=8, timeout=float(os.environ.get("JALMITRA_LLM_TIMEOUT", "20")))
    if not res.ok:
        return None
    t = (res.text or "").strip().upper()
    return "NOT_SUPPORTED" if t.startswith("NOT") else ("SUPPORTED" if t.startswith("SUPPORTED") else None)


# ------------------------------------------------------------------ gate
def check(text, facts, passages=(), lang="en", table=None, embedder=None, self_checker=None, use_support=True):
    """Layered meaning check. ok=False on any rule hit, any unsupported sentence, a failed embedder
    (fail closed) or a self-check NOT_SUPPORTED."""
    res = GateResult(ok=True)
    res.rule_hits = rule_check(text, facts, passages, table)
    if res.rule_hits:
        res.reasons.append("semantic rule: " + ", ".join(sorted({h[0] for h in res.rule_hits})))
    if use_support:
        try:
            bad, sims = support_check(text, facts, passages, embedder)
            res.unsupported, res.similarities = bad, sims
            if bad:
                res.reasons.append(f"{len(bad)} sentence(s) not supported by the facts or cited passages")
        except Exception as e:
            res.reasons.append(f"support check could not run ({type(e).__name__}); not shown")
    if self_checker is not None and not res.reasons:
        verdict = self_checker(text, facts, passages)
        res.self_check = verdict
        if verdict == "NOT_SUPPORTED":
            res.reasons.append("model self-check: not supported")
        elif verdict is None:            # Phase 5: no clear verdict -> cannot be verified -> not shown
            res.reasons.append("model self-check gave no clear verdict; not shown")
    res.ok = not res.reasons
    return res

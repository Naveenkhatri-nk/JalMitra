"""
language.py - Languages, language detection and answer templates for JalMitra 2.0.

No language model is used. Every answer sentence is a fixed template from the
TEMPLATES table below, with database values put into the {placeholders}.

Languages: English (en), Hindi (hi), Hinglish (hinglish, Hindi in Roman
letters), Marathi (mr), Punjabi (pa, Gurmukhi) and Rajasthani (raj).

Rajasthani: JalMitra recognises a tested list of Marwari/Rajasthani marker
words and phrases (see RAJASTHANI_MARKERS and the tests). It does NOT
understand Rajasthani in general. Rajasthani answers use simple Marwari-style
templates and should be checked by a native speaker.

NOTE FOR THE TEAM: the Hindi, Marathi, Punjabi and Rajasthani templates were
written as a starting point. Please ask native speakers to review them.

Rules kept by every template:
  * place names are shown exactly as stored in the database (never translated),
  * official category values are shown in English next to any translation,
  * numbers are inserted unchanged from the database.
"""

import re

AUTO = "auto"
DEFAULT_LANGUAGE = "en"

LANGUAGES = {
    "en": {"name": "English", "native_name": "English", "script": "latin"},
    "hi": {"name": "Hindi", "native_name": "हिन्दी", "script": "devanagari"},
    "hinglish": {"name": "Hinglish", "native_name": "Hinglish", "script": "latin"},
    "mr": {"name": "Marathi", "native_name": "मराठी", "script": "devanagari"},
    "pa": {"name": "Punjabi", "native_name": "ਪੰਜਾਬੀ", "script": "gurmukhi"},
    "raj": {"name": "Rajasthani", "native_name": "राजस्थानी", "script": "devanagari"},
}

# Browser speech locales. None of these has been tested in a real browser yet.
# "experimental" = no dedicated locale or voices are often missing.
VOICE = {
    "en": {"stt": "en-IN", "tts": "en-IN", "level": "supported locale (browser-dependent)"},
    "hi": {"stt": "hi-IN", "tts": "hi-IN", "level": "supported locale (browser-dependent)"},
    "hinglish": {"stt": "en-IN", "tts": "en-IN", "level": "experimental: English recogniser, Hindi words may be misheard"},
    "mr": {"stt": "mr-IN", "tts": "mr-IN", "level": "experimental: needs a Marathi voice in the browser"},
    "pa": {"stt": "pa-IN", "tts": "pa-IN", "level": "experimental: needs a Punjabi voice in the browser"},
    "raj": {"stt": "hi-IN", "tts": "hi-IN", "level": "experimental: no Rajasthani locale, Hindi recogniser and voice are used"},
}

# ------------------------------------------------------------------ detection

DEVANAGARI = re.compile(r"[ऀ-ॿ]")
GURMUKHI = re.compile(r"[਀-੿]")
_INDIC_WORD = re.compile(r"[ऀ-ॿ਀-੿]+")

# Tested Rajasthani (Marwari) marker words. A Devanagari question with more of
# these than Marathi markers is answered in Rajasthani.
RAJASTHANI_MARKERS = {
    "म्हारो", "म्हारा", "म्हारी", "म्हारै", "म्हारे", "थारो", "थारा", "थारी", "कांई", "काईं", "कांइ",
    "कोनी", "सूं", "छै", "हुवै", "कियां", "कियाँ", "किसो", "किसीक", "कठै", "कितरो", "कितरा",
    "कित्तो", "घणो", "घणा", "रो", "री", "रा", "हुयो", "जिलो", "खम्मा", "दिखावो", "बतावो", "बताओ सा",
}
MARATHI_MARKERS = {
    "आहे", "आहेत", "काय", "कसा", "कशी", "कसे", "किती", "मध्ये", "मधील", "आणि", "नाही", "सांगा",
    "कोणते", "कोणत्या", "कोणता", "जिल्हा", "जिल्ह्यात", "जिल्ह्यातील", "तालुका", "तालुके", "स्थिती",
    "म्हणजे", "दाखवा", "यादी", "सर्वात", "सगळ्यात", "दोन्ही", "पाण्याची", "भूजलाची",
    "बद्दल", "कुठून", "गेल्या", "आमच्या", "माझ्या", "अतिशोषित", "करा",
}
HINGLISH_MARKERS = {
    "kya", "hai", "hain", "ka", "ki", "ke", "kaisa", "kaisi", "kaise", "paani", "pani", "kitna", "kitni",
    "kitne", "batao", "bataiye", "bataye", "mein", "me", "sabse", "zyada", "jyada", "kaun", "kaunsa",
    "kaunse", "konse", "dono", "aur", "nahi", "haal", "halat", "jila", "zila", "wala", "wale", "wali",
    "kahan", "kyun", "matlab", "hota", "theek", "thik", "accha", "dikhao", "tulna", "kam", "bhi", "iska",
    "uska", "unka", "yeh", "ye", "kar", "karo", "chahiye", "abhi", "sthiti", "surakshit",
}
STRONG_HINGLISH = {"kya", "kaisa", "kaisi", "kaise", "paani", "batao", "kitna", "kitne", "sabse", "hai", "hain",
                   "dikhao", "matlab", "tulna", "kaunse", "konse", "dono", "bataiye"}


def detect_language(text):
    """Guess the language of a question with simple, tested rules (no AI).

    Gurmukhi -> Punjabi. Devanagari -> Rajasthani or Marathi when their
    marker words appear, otherwise Hindi. Roman letters -> Hinglish when
    Hindi words appear, otherwise English.
    """
    if not text:
        return DEFAULT_LANGUAGE
    if GURMUKHI.search(text) and len(GURMUKHI.findall(text)) >= len(DEVANAGARI.findall(text)):
        return "pa"
    if DEVANAGARI.search(text):
        words = set(_INDIC_WORD.findall(text))
        joined = " ".join(_INDIC_WORD.findall(text))
        raj = sum(1 for w in RAJASTHANI_MARKERS if (" " in w and w in joined) or w in words)
        mr = sum(1 for w in MARATHI_MARKERS if (" " in w and w in joined) or w in words)
        # endings typical for Marathi (पुण्यात, नाशिकमध्ये, जिल्ह्याचा)
        mr += sum(1 for w in words if w.endswith(("मध्ये", "ातील", "ाची", "ाचा", "ाचे", "्यात")))
        if raj > mr:
            return "raj"
        if mr > raj:
            return "mr"
        return "hi"
    words = re.findall(r"[a-z]+", text.lower())
    hits = [w for w in words if w in HINGLISH_MARKERS]
    if len(set(hits)) >= 2 or any(w in STRONG_HINGLISH for w in hits):
        return "hinglish"
    return DEFAULT_LANGUAGE


def resolve_language(choice, question):
    if choice == AUTO or choice not in LANGUAGES:
        return detect_language(question)
    return choice


def language_options():
    options = [(AUTO, "Auto (same as my question)")]
    for code, info in LANGUAGES.items():
        label = info["name"] if info["name"] == info["native_name"] else f"{info['name']} ({info['native_name']})"
        options.append((code, label))
    return options


def get_language(code):
    return LANGUAGES.get(code, LANGUAGES[DEFAULT_LANGUAGE])


# ------------------------------------------------------------------ official terms

CATEGORY_NAMES = {
    "hi": {"Safe": "सुरक्षित", "Semi-critical": "अर्ध-गंभीर", "Critical": "गंभीर",
           "Over-exploited": "अतिदोहित", "Saline": "लवणीय (खारा)"},
    "raj": {"Safe": "सुरक्षित", "Semi-critical": "अर्ध-गंभीर", "Critical": "गंभीर",
            "Over-exploited": "अतिदोहित", "Saline": "खारो (लवणीय)"},
    "mr": {"Safe": "सुरक्षित", "Semi-critical": "अर्ध-गंभीर", "Critical": "गंभीर",
           "Over-exploited": "अतिशोषित", "Saline": "क्षारयुक्त (खारे)"},
    "pa": {"Safe": "ਸੁਰੱਖਿਅਤ", "Semi-critical": "ਅਰਧ-ਗੰਭੀਰ", "Critical": "ਗੰਭੀਰ",
           "Over-exploited": "ਵੱਧ-ਸ਼ੋਸ਼ਿਤ", "Saline": "ਖਾਰਾ"},
}

UNIT_TYPES = {
    "hi": {"Block": "ब्लॉक", "Mandal": "मंडल", "Taluk": "तालुक", "Tehsil": "तहसील", "District": "ज़िला", "UT": "केंद्र शासित प्रदेश"},
    "raj": {"Block": "ब्लॉक", "Mandal": "मंडल", "Taluk": "तालुक", "Tehsil": "तहसील", "District": "जिलो", "UT": "केंद्र शासित प्रदेश"},
    "mr": {"Block": "ब्लॉक", "Mandal": "मंडल", "Taluk": "तालुका", "Tehsil": "तहसील", "District": "जिल्हा", "UT": "केंद्रशासित प्रदेश"},
    "pa": {"Block": "ਬਲਾਕ", "Mandal": "ਮੰਡਲ", "Taluk": "ਤਾਲੁਕਾ", "Tehsil": "ਤਹਿਸੀਲ", "District": "ਜ਼ਿਲ੍ਹਾ", "UT": "ਕੇਂਦਰ ਸ਼ਾਸਿਤ ਪ੍ਰਦੇਸ਼"},
}


def category_label(category, lang):
    """Translated category with the official value kept: 'अतिदोहित (Over-exploited)'."""
    if not category:
        return category
    local = CATEGORY_NAMES.get(lang, {}).get(category)
    return f"{local} ({category})" if local else category


def unit_type_label(kind, lang):
    kind = kind or "Assessment unit"
    return UNIT_TYPES.get(lang, {}).get(kind, kind)


# ------------------------------------------------------------------ templates
# Every key must exist for every language (checked by test_local_engine.py).

TEMPLATES = {
    # ---- one assessment unit
    "unit_cat": {
        "en": "{unit} ({kind}, {district} district, {state}) is classified as {cat}.",
        "hi": "{unit} ({kind}, {district} ज़िला, {state}) को {cat} श्रेणी में रखा गया है।",
        "hinglish": "{unit} ({kind}, {district} district, {state}) ko {cat} category mein rakha gaya hai.",
        "mr": "{unit} ({kind}, {district} जिल्हा, {state}) {cat} श्रेणीत आहे.",
        "pa": "{unit} ({kind}, {district} ਜ਼ਿਲ੍ਹਾ, {state}) ਨੂੰ {cat} ਸ਼੍ਰੇਣੀ ਵਿੱਚ ਰੱਖਿਆ ਗਿਆ ਹੈ।",
        "raj": "{unit} ({kind}, {district} जिलो, {state}) नै {cat} श्रेणी में राख्यो है।",
    },
    "unit_stage": {
        "en": "Its recorded stage of extraction is {stage}%.",
        "hi": "उपलब्ध रिकॉर्ड में भूजल दोहन का स्तर {stage}% है।",
        "hinglish": "Available data ke according extraction stage {stage}% hai.",
        "mr": "उपलब्ध नोंदीनुसार भूजल उपशाचा टप्पा {stage}% आहे.",
        "pa": "ਉਪਲਬਧ ਰਿਕਾਰਡ ਅਨੁਸਾਰ ਧਰਤੀ ਹੇਠਲੇ ਪਾਣੀ ਦੀ ਨਿਕਾਸੀ ਦਾ ਪੱਧਰ {stage}% ਹੈ।",
        "raj": "उपलब्ध रिकॉर्ड में भूजल दोहन रो स्तर {stage}% है।",
    },
    "unit_stage_null": {
        "en": "No stage of extraction is published for this unit.",
        "hi": "इस इकाई के लिए भूजल दोहन का स्तर प्रकाशित नहीं है।",
        "hinglish": "Is unit ke liye extraction stage published nahi hai.",
        "mr": "या घटकासाठी भूजल उपशाचा टप्पा प्रकाशित केलेला नाही.",
        "pa": "ਇਸ ਇਕਾਈ ਲਈ ਨਿਕਾਸੀ ਦਾ ਪੱਧਰ ਪ੍ਰਕਾਸ਼ਿਤ ਨਹੀਂ ਹੈ।",
        "raj": "इण इकाई रो भूजल दोहन स्तर छप्यो कोनी।",
    },
    "unit_cat_only": {
        "en": "Numerical figures are not available for this unit in the database; only the category is recorded.",
        "hi": "डेटाबेस में इस इकाई के आंकड़े उपलब्ध नहीं हैं; केवल श्रेणी दर्ज है।",
        "hinglish": "Database mein is unit ke numbers available nahi hain; sirf category recorded hai.",
        "mr": "डेटाबेसमध्ये या घटकाचे आकडे उपलब्ध नाहीत; फक्त श्रेणी नोंदलेली आहे.",
        "pa": "ਡਾਟਾਬੇਸ ਵਿੱਚ ਇਸ ਇਕਾਈ ਦੇ ਅੰਕੜੇ ਉਪਲਬਧ ਨਹੀਂ ਹਨ; ਸਿਰਫ਼ ਸ਼੍ਰੇਣੀ ਦਰਜ ਹੈ।",
        "raj": "डेटाबेस में इण इकाई रा आंकड़ा कोनी; फगत श्रेणी दर्ज है।",
    },
    "figures": {
        "en": "Annual recharge: {recharge}. Extractable resource: {extractable}. Total extraction: {extraction}.",
        "hi": "वार्षिक पुनर्भरण: {recharge}। निकालने योग्य संसाधन: {extractable}। कुल निकासी: {extraction}।",
        "hinglish": "Annual recharge: {recharge}. Extractable resource: {extractable}. Total extraction: {extraction}.",
        "mr": "वार्षिक पुनर्भरण: {recharge}. उपसा करण्यायोग्य साठा: {extractable}. एकूण उपसा: {extraction}.",
        "pa": "ਸਾਲਾਨਾ ਰੀਚਾਰਜ: {recharge}। ਕੱਢਣਯੋਗ ਸਰੋਤ: {extractable}। ਕੁੱਲ ਨਿਕਾਸੀ: {extraction}।",
        "raj": "सालाना पुनर्भरण: {recharge}। काढ़बा जोग संसाधन: {extractable}। कुल निकासी: {extraction}।",
    },
    "not_available": {
        "en": "not available", "hi": "उपलब्ध नहीं", "hinglish": "available nahi",
        "mr": "उपलब्ध नाही", "pa": "ਉਪਲਬਧ ਨਹੀਂ", "raj": "उपलब्ध कोनी",
    },
    "matched_note": {
        "en": "(I read '{typed}' as {name}.)",
        "hi": "('{typed}' को {name} माना गया है।)",
        "hinglish": "('{typed}' ko {name} samjha gaya hai.)",
        "mr": "('{typed}' म्हणजे {name} असे घेतले आहे.)",
        "pa": "('{typed}' ਨੂੰ {name} ਮੰਨਿਆ ਗਿਆ ਹੈ।)",
        "raj": "('{typed}' नै {name} मान्यो है।)",
    },
    # ---- farmer-mode meaning of a category
    "meaning_Safe": {
        "en": "This means groundwater use here is within the safe limit (up to 70% of the water that can be taken out).",
        "hi": "इसका मतलब है कि यहाँ भूजल का उपयोग सुरक्षित सीमा में है (निकालने योग्य पानी का 70% तक)।",
        "hinglish": "Matlab yahan groundwater ka use safe limit mein hai (nikalne layak paani ka 70% tak).",
        "mr": "याचा अर्थ येथे भूजलाचा वापर सुरक्षित मर्यादेत आहे (उपसा करण्यायोग्य पाण्याच्या 70% पर्यंत).",
        "pa": "ਇਸ ਦਾ ਮਤਲਬ ਹੈ ਕਿ ਇੱਥੇ ਧਰਤੀ ਹੇਠਲੇ ਪਾਣੀ ਦੀ ਵਰਤੋਂ ਸੁਰੱਖਿਅਤ ਹੱਦ ਵਿੱਚ ਹੈ (ਕੱਢਣਯੋਗ ਪਾਣੀ ਦਾ 70% ਤੱਕ)।",
        "raj": "इणरो मतलब है कै अठै भूजल रो उपयोग सुरक्षित सीमा में है (काढ़बा जोग पाणी रो 70% तांई)।",
    },
    "meaning_Semi-critical": {
        "en": "This means 70% to 90% of the water that can be taken out is being used. Use water carefully.",
        "hi": "इसका मतलब है कि निकालने योग्य पानी का 70% से 90% उपयोग हो रहा है। पानी सोच-समझकर इस्तेमाल करें।",
        "hinglish": "Matlab nikalne layak paani ka 70% se 90% use ho raha hai. Paani soch-samajh kar use karein.",
        "mr": "याचा अर्थ उपसा करण्यायोग्य पाण्याच्या 70% ते 90% पाणी वापरले जात आहे. पाणी जपून वापरा.",
        "pa": "ਇਸ ਦਾ ਮਤਲਬ ਹੈ ਕਿ ਕੱਢਣਯੋਗ ਪਾਣੀ ਦਾ 70% ਤੋਂ 90% ਵਰਤਿਆ ਜਾ ਰਿਹਾ ਹੈ। ਪਾਣੀ ਸੋਚ-ਸਮਝ ਕੇ ਵਰਤੋ।",
        "raj": "इणरो मतलब है कै काढ़बा जोग पाणी रो 70% सूं 90% काम में आ रियो है। पाणी सोच-समझ नै बरतो।",
    },
    "meaning_Critical": {
        "en": "This means 90% to 100% of the water that can be taken out is being used. The situation is serious.",
        "hi": "इसका मतलब है कि निकालने योग्य पानी का 90% से 100% उपयोग हो रहा है। स्थिति गंभीर है।",
        "hinglish": "Matlab nikalne layak paani ka 90% se 100% use ho raha hai. Situation serious hai.",
        "mr": "याचा अर्थ उपसा करण्यायोग्य पाण्याच्या 90% ते 100% पाणी वापरले जात आहे. परिस्थिती गंभीर आहे.",
        "pa": "ਇਸ ਦਾ ਮਤਲਬ ਹੈ ਕਿ ਕੱਢਣਯੋਗ ਪਾਣੀ ਦਾ 90% ਤੋਂ 100% ਵਰਤਿਆ ਜਾ ਰਿਹਾ ਹੈ। ਹਾਲਤ ਗੰਭੀਰ ਹੈ।",
        "raj": "इणरो मतलब है कै काढ़बा जोग पाणी रो 90% सूं 100% काम में आ रियो है। हालत गंभीर है।",
    },
    "meaning_Over-exploited": {
        "en": "This means more groundwater is taken out than can be safely replaced (above 100%).",
        "hi": "इसका मतलब है कि जितना भूजल सुरक्षित रूप से भर सकता है, उससे ज़्यादा निकाला जा रहा है (100% से ऊपर)।",
        "hinglish": "Matlab jitna groundwater wapas bhar sakta hai, usse zyada nikala ja raha hai (100% se upar).",
        "mr": "याचा अर्थ जितके भूजल पुन्हा भरू शकते त्यापेक्षा जास्त उपसा होत आहे (100% पेक्षा जास्त).",
        "pa": "ਇਸ ਦਾ ਮਤਲਬ ਹੈ ਕਿ ਜਿੰਨਾ ਪਾਣੀ ਮੁੜ ਭਰ ਸਕਦਾ ਹੈ, ਉਸ ਤੋਂ ਵੱਧ ਕੱਢਿਆ ਜਾ ਰਿਹਾ ਹੈ (100% ਤੋਂ ਉੱਪਰ)।",
        "raj": "इणरो मतलब है कै जितो भूजल पाछो भर सकै, उणसूं घणो काढ्यो जा रियो है (100% सूं ऊपर)।",
    },
    "meaning_Saline": {
        "en": "This means the groundwater here is salty (saline), so the usual extraction limits are not applied.",
        "hi": "इसका मतलब है कि यहाँ का भूजल खारा (लवणीय) है, इसलिए सामान्य दोहन सीमाएँ लागू नहीं की जातीं।",
        "hinglish": "Matlab yahan ka groundwater khaara (saline) hai, isliye normal extraction limits apply nahi hoti.",
        "mr": "याचा अर्थ येथील भूजल खारे (क्षारयुक्त) आहे, त्यामुळे नेहमीच्या उपसा मर्यादा लागू होत नाहीत.",
        "pa": "ਇਸ ਦਾ ਮਤਲਬ ਹੈ ਕਿ ਇੱਥੇ ਦਾ ਪਾਣੀ ਖਾਰਾ ਹੈ, ਇਸ ਲਈ ਆਮ ਨਿਕਾਸੀ ਹੱਦਾਂ ਲਾਗੂ ਨਹੀਂ ਹੁੰਦੀਆਂ।",
        "raj": "इणरो मतलब है कै अठै रो भूजल खारो है, इण वास्तै सामान्य दोहन सीमा लागू कोनी होवै।",
    },
    "tip": {
        "en": "Tip: drip or sprinkler irrigation and crops that need less water help save groundwater.",
        "hi": "सुझाव: ड्रिप या स्प्रिंकलर सिंचाई और कम पानी वाली फसलें भूजल बचाने में मदद करती हैं।",
        "hinglish": "Tip: drip ya sprinkler irrigation aur kam paani wali faslein groundwater bachane mein madad karti hain.",
        "mr": "सूचना: ठिबक किंवा तुषार सिंचन आणि कमी पाण्याची पिके भूजल वाचवण्यास मदत करतात.",
        "pa": "ਸੁਝਾਅ: ਤੁਪਕਾ ਜਾਂ ਫੁਹਾਰਾ ਸਿੰਚਾਈ ਅਤੇ ਘੱਟ ਪਾਣੀ ਵਾਲੀਆਂ ਫ਼ਸਲਾਂ ਪਾਣੀ ਬਚਾਉਣ ਵਿੱਚ ਮਦਦ ਕਰਦੀਆਂ ਹਨ।",
        "raj": "सुझाव: ड्रिप या फव्वारा सिंचाई अर कम पाणी वाळी फसलां भूजल बचावण में मदद करै।",
    },
    "thresholds": {
        "en": "Category limits (stage of extraction): Safe up to 70%, Semi-critical 70-90%, Critical 90-100%, Over-exploited above 100%.",
        "hi": "श्रेणी सीमाएँ (दोहन स्तर): Safe 70% तक, Semi-critical 70-90%, Critical 90-100%, Over-exploited 100% से ऊपर।",
        "hinglish": "Category limits (extraction stage): Safe 70% tak, Semi-critical 70-90%, Critical 90-100%, Over-exploited 100% se upar.",
        "mr": "श्रेणी मर्यादा (उपसा टप्पा): Safe 70% पर्यंत, Semi-critical 70-90%, Critical 90-100%, Over-exploited 100% पेक्षा जास्त.",
        "pa": "ਸ਼੍ਰੇਣੀ ਹੱਦਾਂ (ਨਿਕਾਸੀ ਪੱਧਰ): Safe 70% ਤੱਕ, Semi-critical 70-90%, Critical 90-100%, Over-exploited 100% ਤੋਂ ਉੱਪਰ।",
        "raj": "श्रेणी सीमा (दोहन स्तर): Safe 70% तांई, Semi-critical 70-90%, Critical 90-100%, Over-exploited 100% सूं ऊपर।",
    },
    # ---- districts and states
    "district_label": {
        "en": "{district} district ({state})", "hi": "{district} ज़िला ({state})",
        "hinglish": "{district} district ({state})", "mr": "{district} जिल्हा ({state})",
        "pa": "{district} ਜ਼ਿਲ੍ਹਾ ({state})", "raj": "{district} जिलो ({state})",
    },
    "whole_db": {
        "en": "the whole database", "hi": "पूरे डेटाबेस", "hinglish": "poore database",
        "mr": "संपूर्ण डेटाबेस", "pa": "ਪੂਰੇ ਡਾਟਾਬੇਸ", "raj": "पूरा डेटाबेस",
    },
    "area_counts": {
        "en": "{area} has {total} assessment units: {parts}.",
        "hi": "{area} में {total} आकलन इकाइयाँ हैं: {parts}।",
        "hinglish": "{area} mein {total} assessment units hain: {parts}.",
        "mr": "{area} मध्ये {total} मूल्यांकन घटक आहेत: {parts}.",
        "pa": "{area} ਵਿੱਚ {total} ਮੁਲਾਂਕਣ ਇਕਾਈਆਂ ਹਨ: {parts}।",
        "raj": "{area} में {total} आकलन इकाइयां है: {parts}।",
    },
    "area_numeric": {
        "en": "Unit-level figures are available for {n} of these {total} units.",
        "hi": "इनमें से {total} में से {n} इकाइयों के आंकड़े उपलब्ध हैं।",
        "hinglish": "In {total} units mein se {n} units ke numbers available hain.",
        "mr": "या {total} पैकी {n} घटकांचे आकडे उपलब्ध आहेत.",
        "pa": "ਇਨ੍ਹਾਂ {total} ਵਿੱਚੋਂ {n} ਇਕਾਈਆਂ ਦੇ ਅੰਕੜੇ ਉਪਲਬਧ ਹਨ।",
        "raj": "आं {total} में सूं {n} इकाइयां रा आंकड़ा उपलब्ध है।",
    },
    "area_no_numeric": {
        "en": "Unit-level figures are not available here; only categories are recorded.",
        "hi": "यहाँ इकाई-स्तर के आंकड़े उपलब्ध नहीं हैं; केवल श्रेणियाँ दर्ज हैं।",
        "hinglish": "Yahan unit-level numbers available nahi hain; sirf categories recorded hain.",
        "mr": "येथे घटक-स्तरावरील आकडे उपलब्ध नाहीत; फक्त श्रेणी नोंदलेल्या आहेत.",
        "pa": "ਇੱਥੇ ਇਕਾਈ-ਪੱਧਰ ਦੇ ਅੰਕੜੇ ਉਪਲਬਧ ਨਹੀਂ ਹਨ; ਸਿਰਫ਼ ਸ਼੍ਰੇਣੀਆਂ ਦਰਜ ਹਨ।",
        "raj": "अठै इकाई रा आंकड़ा कोनी; फगत श्रेणियां दर्ज है।",
    },
    "nc_total": {
        "en": "National Compilation 2025 total for {area} (page {page}; an area total, not a unit figure): stage of extraction {stage}, annual recharge {recharge}, total extraction {extraction}.",
        "hi": "{area} के लिए राष्ट्रीय संकलन 2025 का कुल (पृष्ठ {page}; यह क्षेत्र का कुल है, इकाई का आंकड़ा नहीं): दोहन स्तर {stage}, वार्षिक पुनर्भरण {recharge}, कुल निकासी {extraction}।",
        "hinglish": "{area} ka National Compilation 2025 total (page {page}; yeh area total hai, unit figure nahi): extraction stage {stage}, annual recharge {recharge}, total extraction {extraction}.",
        "mr": "{area} साठी राष्ट्रीय संकलन 2025 मधील एकूण (पान {page}; हे क्षेत्राचे एकूण आहे, घटकाचा आकडा नाही): उपसा टप्पा {stage}, वार्षिक पुनर्भरण {recharge}, एकूण उपसा {extraction}.",
        "pa": "{area} ਲਈ ਰਾਸ਼ਟਰੀ ਸੰਕਲਨ 2025 ਦਾ ਕੁੱਲ (ਪੰਨਾ {page}; ਇਹ ਖੇਤਰ ਦਾ ਕੁੱਲ ਹੈ, ਇਕਾਈ ਦਾ ਅੰਕੜਾ ਨਹੀਂ): ਨਿਕਾਸੀ ਪੱਧਰ {stage}, ਸਾਲਾਨਾ ਰੀਚਾਰਜ {recharge}, ਕੁੱਲ ਨਿਕਾਸੀ {extraction}।",
        "raj": "{area} रो राष्ट्रीय संकलन 2025 रो कुल (पानो {page}; ओ इलाका रो कुल है, इकाई रो आंकड़ो कोनी): दोहन स्तर {stage}, सालाना पुनर्भरण {recharge}, कुल निकासी {extraction}।",
    },
    "nc_missing": {
        "en": "No National Compilation total was found for {area}.",
        "hi": "{area} के लिए राष्ट्रीय संकलन का कुल नहीं मिला।",
        "hinglish": "{area} ka National Compilation total nahi mila.",
        "mr": "{area} साठी राष्ट्रीय संकलनातील एकूण सापडले नाही.",
        "pa": "{area} ਲਈ ਰਾਸ਼ਟਰੀ ਸੰਕਲਨ ਦਾ ਕੁੱਲ ਨਹੀਂ ਮਿਲਿਆ।",
        "raj": "{area} रो राष्ट्रीय संकलन रो कुल कोनी मिल्यो।",
    },
    # ---- lists
    "list_cat": {
        "en": "{area}: {n} assessment units are {cat}.",
        "hi": "{area}: {n} आकलन इकाइयाँ {cat} हैं।",
        "hinglish": "{area}: {n} assessment units {cat} hain.",
        "mr": "{area}: {n} मूल्यांकन घटक {cat} आहेत.",
        "pa": "{area}: {n} ਮੁਲਾਂਕਣ ਇਕਾਈਆਂ {cat} ਹਨ।",
        "raj": "{area}: {n} आकलन इकाइयां {cat} है।",
    },
    "list_none": {
        "en": "{area}: no assessment unit is {cat}.",
        "hi": "{area}: कोई भी आकलन इकाई {cat} नहीं है।",
        "hinglish": "{area}: koi bhi assessment unit {cat} nahi hai.",
        "mr": "{area}: कोणताही मूल्यांकन घटक {cat} नाही.",
        "pa": "{area}: ਕੋਈ ਵੀ ਮੁਲਾਂਕਣ ਇਕਾਈ {cat} ਨਹੀਂ ਹੈ।",
        "raj": "{area}: कोई भी आकलन इकाई {cat} कोनी।",
    },
    "list_names": {
        "en": "They are: {names}.", "hi": "ये हैं: {names}।", "hinglish": "Yeh hain: {names}.",
        "mr": "ते आहेत: {names}.", "pa": "ਇਹ ਹਨ: {names}।", "raj": "ऐ है: {names}।",
    },
    "list_more": {
        "en": "...and {k} more (see the table).", "hi": "...और {k} अन्य (तालिका देखें)।",
        "hinglish": "...aur {k} aur (table dekhiye).", "mr": "...आणि आणखी {k} (तक्ता पहा).",
        "pa": "...ਅਤੇ {k} ਹੋਰ (ਸਾਰਣੀ ਵੇਖੋ)।", "raj": "...अर {k} दूजा (तालिका देखो)।",
    },
    "area_units": {
        "en": "Assessment units in {area}: {names}.", "hi": "{area} की आकलन इकाइयाँ: {names}।",
        "hinglish": "{area} ki assessment units: {names}.", "mr": "{area} मधील मूल्यांकन घटक: {names}.",
        "pa": "{area} ਦੀਆਂ ਮੁਲਾਂਕਣ ਇਕਾਈਆਂ: {names}।", "raj": "{area} री आकलन इकाइयां: {names}।",
    },
    # ---- rankings
    "top_header": {
        "en": "Highest {n} recorded stages of extraction in {area}{cat_part}:",
        "hi": "{area} में{cat_part} भूजल दोहन के {n} सबसे ऊँचे दर्ज स्तर:",
        "hinglish": "{area} mein{cat_part} sabse zyada {n} recorded extraction stages:",
        "mr": "{area} मधील{cat_part} सर्वाधिक {n} नोंदलेले उपसा टप्पे:",
        "pa": "{area} ਵਿੱਚ{cat_part} ਸਭ ਤੋਂ ਵੱਧ {n} ਦਰਜ ਨਿਕਾਸੀ ਪੱਧਰ:",
        "raj": "{area} में{cat_part} सब सूं ऊंचा {n} दर्ज दोहन स्तर:",
    },
    "top_header_low": {
        "en": "Lowest {n} recorded stages of extraction in {area}{cat_part}:",
        "hi": "{area} में{cat_part} भूजल दोहन के {n} सबसे कम दर्ज स्तर:",
        "hinglish": "{area} mein{cat_part} sabse kam {n} recorded extraction stages:",
        "mr": "{area} मधील{cat_part} सर्वात कमी {n} नोंदलेले उपसा टप्पे:",
        "pa": "{area} ਵਿੱਚ{cat_part} ਸਭ ਤੋਂ ਘੱਟ {n} ਦਰਜ ਨਿਕਾਸੀ ਪੱਧਰ:",
        "raj": "{area} में{cat_part} सब सूं कम {n} दर्ज दोहन स्तर:",
    },
    "cat_part": {
        "en": " among {cat} units", "hi": " {cat} इकाइयों में", "hinglish": " {cat} units mein",
        "mr": " {cat} घटकांपैकी", "pa": " {cat} ਇਕਾਈਆਂ ਵਿੱਚ", "raj": " {cat} इकाइयां में",
    },
    "top_line": {
        "en": "{i}. {unit} ({district}): {stage}%, {cat}", "hi": "{i}. {unit} ({district}): {stage}%, {cat}",
        "hinglish": "{i}. {unit} ({district}): {stage}%, {cat}", "mr": "{i}. {unit} ({district}): {stage}%, {cat}",
        "pa": "{i}. {unit} ({district}): {stage}%, {cat}", "raj": "{i}. {unit} ({district}): {stage}%, {cat}",
    },
    "top_unranked": {
        "en": "Units without a published stage of extraction are not ranked.",
        "hi": "जिन इकाइयों का दोहन स्तर प्रकाशित नहीं है, उन्हें रैंक नहीं किया गया।",
        "hinglish": "Jin units ka extraction stage published nahi hai, unhe rank nahi kiya gaya.",
        "mr": "ज्या घटकांचा उपसा टप्पा प्रकाशित नाही त्यांना क्रम दिलेला नाही.",
        "pa": "ਜਿਨ੍ਹਾਂ ਇਕਾਈਆਂ ਦਾ ਨਿਕਾਸੀ ਪੱਧਰ ਪ੍ਰਕਾਸ਼ਿਤ ਨਹੀਂ, ਉਨ੍ਹਾਂ ਨੂੰ ਦਰਜਾ ਨਹੀਂ ਦਿੱਤਾ ਗਿਆ।",
        "raj": "जिण इकाइयां रो दोहन स्तर छप्यो कोनी, वां नै रैंक कोनी करी।",
    },
    "top_none": {
        "en": "Stage-of-extraction figures are not available for {area}. Numbers exist only for {numeric}.",
        "hi": "{area} के लिए दोहन स्तर के आंकड़े उपलब्ध नहीं हैं। आंकड़े केवल {numeric} के लिए हैं।",
        "hinglish": "{area} ke liye extraction stage ke numbers available nahi hain. Numbers sirf {numeric} ke liye hain.",
        "mr": "{area} साठी उपसा टप्प्याचे आकडे उपलब्ध नाहीत. आकडे फक्त {numeric} साठी आहेत.",
        "pa": "{area} ਲਈ ਨਿਕਾਸੀ ਪੱਧਰ ਦੇ ਅੰਕੜੇ ਉਪਲਬਧ ਨਹੀਂ ਹਨ। ਅੰਕੜੇ ਸਿਰਫ਼ {numeric} ਲਈ ਹਨ।",
        "raj": "{area} सारू दोहन स्तर रा आंकड़ा कोनी। आंकड़ा फगत {numeric} सारू है।",
    },
    "numeric_scope": {
        "en": "{n} Rajasthan blocks", "hi": "राजस्थान के {n} ब्लॉकों", "hinglish": "Rajasthan ke {n} blocks",
        "mr": "राजस्थानमधील {n} ब्लॉक", "pa": "ਰਾਜਸਥਾਨ ਦੇ {n} ਬਲਾਕਾਂ", "raj": "राजस्थान रा {n} ब्लॉक",
    },
    "top_fallback": {
        "en": "Instead, here are the districts with the most {cat} units:",
        "hi": "इसके बजाय, सबसे अधिक {cat} इकाइयों वाले ज़िले ये हैं:",
        "hinglish": "Iske badle, sabse zyada {cat} units wale districts yeh hain:",
        "mr": "त्याऐवजी, सर्वाधिक {cat} घटक असलेले जिल्हे हे आहेत:",
        "pa": "ਇਸ ਦੀ ਬਜਾਏ, ਸਭ ਤੋਂ ਵੱਧ {cat} ਇਕਾਈਆਂ ਵਾਲੇ ਜ਼ਿਲ੍ਹੇ ਇਹ ਹਨ:",
        "raj": "इणरी जगां, सब सूं घणी {cat} इकाइयां वाळा जिला ऐ है:",
    },
    "topareas_header_district": {
        "en": "Districts with the most {cat} assessment units{in_part}:",
        "hi": "सबसे अधिक {cat} आकलन इकाइयों वाले ज़िले{in_part}:",
        "hinglish": "Sabse zyada {cat} assessment units wale districts{in_part}:",
        "mr": "सर्वाधिक {cat} मूल्यांकन घटक असलेले जिल्हे{in_part}:",
        "pa": "ਸਭ ਤੋਂ ਵੱਧ {cat} ਮੁਲਾਂਕਣ ਇਕਾਈਆਂ ਵਾਲੇ ਜ਼ਿਲ੍ਹੇ{in_part}:",
        "raj": "सब सूं घणी {cat} आकलन इकाइयां वाळा जिला{in_part}:",
    },
    "topareas_header_state": {
        "en": "States/UTs with the most {cat} assessment units:",
        "hi": "सबसे अधिक {cat} आकलन इकाइयों वाले राज्य/केंद्र शासित प्रदेश:",
        "hinglish": "Sabse zyada {cat} assessment units wale states/UTs:",
        "mr": "सर्वाधिक {cat} मूल्यांकन घटक असलेली राज्ये/केंद्रशासित प्रदेश:",
        "pa": "ਸਭ ਤੋਂ ਵੱਧ {cat} ਮੁਲਾਂਕਣ ਇਕਾਈਆਂ ਵਾਲੇ ਰਾਜ/ਕੇਂਦਰ ਸ਼ਾਸਿਤ ਪ੍ਰਦੇਸ਼:",
        "raj": "सब सूं घणी {cat} आकलन इकाइयां वाळा राज्य:",
    },
    "in_part": {
        "en": " in {area}", "hi": " ({area} में)", "hinglish": " ({area} mein)",
        "mr": " ({area} मध्ये)", "pa": " ({area} ਵਿੱਚ)", "raj": " ({area} में)",
    },
    "topareas_line": {
        "en": "{i}. {name}: {n} units", "hi": "{i}. {name}: {n} इकाइयाँ", "hinglish": "{i}. {name}: {n} units",
        "mr": "{i}. {name}: {n} घटक", "pa": "{i}. {name}: {n} ਇਕਾਈਆਂ", "raj": "{i}. {name}: {n} इकाइयां",
    },
    # ---- comparisons
    "compare_header": {
        "en": "Comparison of {names}:", "hi": "{names} की तुलना:", "hinglish": "{names} ki tulna:",
        "mr": "{names} यांची तुलना:", "pa": "{names} ਦੀ ਤੁਲਨਾ:", "raj": "{names} री तुलना:",
    },
    "and": {"en": " and ", "hi": " और ", "hinglish": " aur ", "mr": " आणि ", "pa": " ਅਤੇ ", "raj": " अर "},
    "compare_higher": {
        "en": "{x} has the higher recorded stage of extraction ({sx}% against {sy}% for {y}).",
        "hi": "{x} का दर्ज दोहन स्तर अधिक है ({x}: {sx}%, {y}: {sy}%)।",
        "hinglish": "{x} ka recorded extraction stage zyada hai ({x}: {sx}%, {y}: {sy}%).",
        "mr": "{x} चा नोंदलेला उपसा टप्पा जास्त आहे ({x}: {sx}%, {y}: {sy}%).",
        "pa": "{x} ਦਾ ਦਰਜ ਨਿਕਾਸੀ ਪੱਧਰ ਵੱਧ ਹੈ ({x}: {sx}%, {y}: {sy}%)।",
        "raj": "{x} रो दर्ज दोहन स्तर घणो है ({x}: {sx}%, {y}: {sy}%)।",
    },
    "compare_equal": {
        "en": "Both have the same recorded stage of extraction ({sx}%).",
        "hi": "दोनों का दर्ज दोहन स्तर बराबर है ({sx}%)।",
        "hinglish": "Dono ka recorded extraction stage barabar hai ({sx}%).",
        "mr": "दोघांचा नोंदलेला उपसा टप्पा सारखाच आहे ({sx}%).",
        "pa": "ਦੋਵਾਂ ਦਾ ਦਰਜ ਨਿਕਾਸੀ ਪੱਧਰ ਬਰਾਬਰ ਹੈ ({sx}%)।",
        "raj": "दोनूं रो दर्ज दोहन स्तर बराबर है ({sx}%)।",
    },
    "compare_no_numbers": {
        "en": "A numerical comparison is not possible because figures are missing for {names}.",
        "hi": "{names} के आंकड़े नहीं हैं, इसलिए संख्याओं की तुलना संभव नहीं है।",
        "hinglish": "{names} ke numbers nahi hain, isliye numbers ki tulna possible nahi hai.",
        "mr": "{names} चे आकडे नाहीत, त्यामुळे आकड्यांची तुलना शक्य नाही.",
        "pa": "{names} ਦੇ ਅੰਕੜੇ ਨਹੀਂ ਹਨ, ਇਸ ਲਈ ਅੰਕੜਿਆਂ ਦੀ ਤੁਲਨਾ ਸੰਭਵ ਨਹੀਂ।",
        "raj": "{names} रा आंकड़ा कोनी, इण वास्तै आंकड़ां री तुलना कोनी हो सकै।",
    },
    "compare_need_two": {
        "en": "Please name two places to compare, for example: Compare Jaipur district and Jodhpur district.",
        "hi": "तुलना के लिए दो जगहों के नाम बताइए, जैसे: जयपुर ज़िला और जोधपुर ज़िला की तुलना करें।",
        "hinglish": "Tulna ke liye do jagah ke naam batayein, jaise: Jaipur district aur Jodhpur district compare karo.",
        "mr": "तुलनेसाठी दोन ठिकाणांची नावे सांगा, उदा.: पुणे आणि नाशिक जिल्ह्यांची तुलना करा.",
        "pa": "ਤੁਲਨਾ ਲਈ ਦੋ ਥਾਵਾਂ ਦੇ ਨਾਂ ਦੱਸੋ, ਜਿਵੇਂ: ਲੁਧਿਆਣਾ ਅਤੇ ਪਟਿਆਲਾ ਦੀ ਤੁਲਨਾ ਕਰੋ।",
        "raj": "तुलना सारू दो जगां रा नाम बताओ, जियां: जयपुर अर जोधपुर री तुलना करो।",
    },
    # ---- years
    "year_only": {
        "en": "The database has only assessment year {years}, so a comparison between years is not possible. Here is the {years} data:",
        "hi": "डेटाबेस में केवल आकलन वर्ष {years} है, इसलिए वर्षों की तुलना संभव नहीं है। {years} का डेटा यह है:",
        "hinglish": "Database mein sirf assessment year {years} hai, isliye saalon ki tulna possible nahi hai. {years} ka data yeh hai:",
        "mr": "डेटाबेसमध्ये फक्त मूल्यांकन वर्ष {years} आहे, त्यामुळे वर्षांची तुलना शक्य नाही. {years} चा डेटा हा आहे:",
        "pa": "ਡਾਟਾਬੇਸ ਵਿੱਚ ਸਿਰਫ਼ ਮੁਲਾਂਕਣ ਸਾਲ {years} ਹੈ, ਇਸ ਲਈ ਸਾਲਾਂ ਦੀ ਤੁਲਨਾ ਸੰਭਵ ਨਹੀਂ। {years} ਦਾ ਡਾਟਾ ਇਹ ਹੈ:",
        "raj": "डेटाबेस में फगत आकलन बरस {years} है, इण वास्तै बरसां री तुलना कोनी हो सकै। {years} रो डेटा ओ है:",
    },
    "year_missing": {
        "en": "Assessment year {year} is not in the database. Available year(s): {years}.",
        "hi": "आकलन वर्ष {year} डेटाबेस में नहीं है। उपलब्ध वर्ष: {years}।",
        "hinglish": "Assessment year {year} database mein nahi hai. Available year: {years}.",
        "mr": "मूल्यांकन वर्ष {year} डेटाबेसमध्ये नाही. उपलब्ध वर्ष: {years}.",
        "pa": "ਮੁਲਾਂਕਣ ਸਾਲ {year} ਡਾਟਾਬੇਸ ਵਿੱਚ ਨਹੀਂ ਹੈ। ਉਪਲਬਧ ਸਾਲ: {years}।",
        "raj": "आकलन बरस {year} डेटाबेस में कोनी। उपलब्ध बरस: {years}।",
    },
    "year_caption": {
        "en": "Assessment year: {year}", "hi": "आकलन वर्ष: {year}", "hinglish": "Assessment year: {year}",
        "mr": "मूल्यांकन वर्ष: {year}", "pa": "ਮੁਲਾਂਕਣ ਸਾਲ: {year}", "raj": "आकलन बरस: {year}",
    },
    # ---- explanations
    "explain_Safe": {
        "en": "Safe: the stage of groundwater extraction is up to 70%. Less water is taken out than the limit.",
        "hi": "Safe (सुरक्षित): भूजल दोहन का स्तर 70% तक है। सीमा से कम पानी निकाला जाता है।",
        "hinglish": "Safe: groundwater extraction stage 70% tak hai. Limit se kam paani nikala jaata hai.",
        "mr": "Safe (सुरक्षित): भूजल उपशाचा टप्पा 70% पर्यंत आहे. मर्यादेपेक्षा कमी पाणी उपसले जाते.",
        "pa": "Safe (ਸੁਰੱਖਿਅਤ): ਨਿਕਾਸੀ ਦਾ ਪੱਧਰ 70% ਤੱਕ ਹੈ। ਹੱਦ ਤੋਂ ਘੱਟ ਪਾਣੀ ਕੱਢਿਆ ਜਾਂਦਾ ਹੈ।",
        "raj": "Safe (सुरक्षित): भूजल दोहन रो स्तर 70% तांई है। सीमा सूं कम पाणी काढ्यो जावै।",
    },
    "explain_Semi-critical": {
        "en": "Semi-critical: the stage of groundwater extraction is more than 70% and up to 90%.",
        "hi": "Semi-critical (अर्ध-गंभीर): भूजल दोहन का स्तर 70% से अधिक और 90% तक है।",
        "hinglish": "Semi-critical: groundwater extraction stage 70% se zyada aur 90% tak hai.",
        "mr": "Semi-critical (अर्ध-गंभीर): भूजल उपशाचा टप्पा 70% पेक्षा जास्त आणि 90% पर्यंत आहे.",
        "pa": "Semi-critical (ਅਰਧ-ਗੰਭੀਰ): ਨਿਕਾਸੀ ਦਾ ਪੱਧਰ 70% ਤੋਂ ਵੱਧ ਅਤੇ 90% ਤੱਕ ਹੈ।",
        "raj": "Semi-critical (अर्ध-गंभीर): भूजल दोहन रो स्तर 70% सूं घणो अर 90% तांई है।",
    },
    "explain_Critical": {
        "en": "Critical: the stage of groundwater extraction is more than 90% and up to 100%.",
        "hi": "Critical (गंभीर): भूजल दोहन का स्तर 90% से अधिक और 100% तक है।",
        "hinglish": "Critical: groundwater extraction stage 90% se zyada aur 100% tak hai.",
        "mr": "Critical (गंभीर): भूजल उपशाचा टप्पा 90% पेक्षा जास्त आणि 100% पर्यंत आहे.",
        "pa": "Critical (ਗੰਭੀਰ): ਨਿਕਾਸੀ ਦਾ ਪੱਧਰ 90% ਤੋਂ ਵੱਧ ਅਤੇ 100% ਤੱਕ ਹੈ।",
        "raj": "Critical (गंभीर): भूजल दोहन रो स्तर 90% सूं घणो अर 100% तांई है।",
    },
    "explain_Over-exploited": {
        "en": "Over-exploited: the stage of groundwater extraction is more than 100%. More water is taken out each year than is recharged and can be extracted.",
        "hi": "Over-exploited (अतिदोहित): भूजल दोहन का स्तर 100% से अधिक है। हर साल पुनर्भरण से ज़्यादा पानी निकाला जाता है।",
        "hinglish": "Over-exploited: groundwater extraction stage 100% se zyada hai. Har saal recharge se zyada paani nikala jaata hai.",
        "mr": "Over-exploited (अतिशोषित): भूजल उपशाचा टप्पा 100% पेक्षा जास्त आहे. दरवर्षी पुनर्भरणापेक्षा जास्त पाणी उपसले जाते.",
        "pa": "Over-exploited (ਵੱਧ-ਸ਼ੋਸ਼ਿਤ): ਨਿਕਾਸੀ ਦਾ ਪੱਧਰ 100% ਤੋਂ ਵੱਧ ਹੈ। ਹਰ ਸਾਲ ਰੀਚਾਰਜ ਤੋਂ ਵੱਧ ਪਾਣੀ ਕੱਢਿਆ ਜਾਂਦਾ ਹੈ।",
        "raj": "Over-exploited (अतिदोहित): भूजल दोहन रो स्तर 100% सूं घणो है। हर बरस पुनर्भरण सूं घणो पाणी काढ्यो जावै।",
    },
    "explain_Saline": {
        "en": "Saline: the groundwater in the unit is salty, so it is reported separately and the usual extraction limits are not applied.",
        "hi": "Saline (लवणीय): इकाई का भूजल खारा है, इसलिए इसे अलग दिखाया जाता है और सामान्य दोहन सीमाएँ लागू नहीं होतीं।",
        "hinglish": "Saline: unit ka groundwater khaara hai, isliye ise alag dikhaya jaata hai aur normal extraction limits apply nahi hoti.",
        "mr": "Saline (क्षारयुक्त): घटकातील भूजल खारे आहे, म्हणून ते वेगळे दाखवले जाते आणि नेहमीच्या उपसा मर्यादा लागू होत नाहीत.",
        "pa": "Saline (ਖਾਰਾ): ਇਕਾਈ ਦਾ ਪਾਣੀ ਖਾਰਾ ਹੈ, ਇਸ ਲਈ ਇਸ ਨੂੰ ਵੱਖਰਾ ਦਿਖਾਇਆ ਜਾਂਦਾ ਹੈ ਅਤੇ ਆਮ ਨਿਕਾਸੀ ਹੱਦਾਂ ਲਾਗੂ ਨਹੀਂ ਹੁੰਦੀਆਂ।",
        "raj": "Saline (खारो): इकाई रो भूजल खारो है, इण वास्तै इणनै न्यारो दिखावै अर सामान्य दोहन सीमा लागू कोनी होवै।",
    },
    "explain_stage": {
        "en": "Stage of extraction = total groundwater extraction divided by the annual extractable groundwater resource, in percent.",
        "hi": "दोहन स्तर = कुल भूजल निकासी ÷ वार्षिक निकालने योग्य भूजल संसाधन, प्रतिशत में।",
        "hinglish": "Extraction stage = total groundwater extraction ÷ annual extractable resource, percent mein.",
        "mr": "उपसा टप्पा = एकूण भूजल उपसा ÷ वार्षिक उपसा करण्यायोग्य भूजल साठा, टक्क्यांमध्ये.",
        "pa": "ਨਿਕਾਸੀ ਪੱਧਰ = ਕੁੱਲ ਨਿਕਾਸੀ ÷ ਸਾਲਾਨਾ ਕੱਢਣਯੋਗ ਸਰੋਤ, ਪ੍ਰਤੀਸ਼ਤ ਵਿੱਚ।",
        "raj": "दोहन स्तर = कुल भूजल निकासी ÷ सालाना काढ़बा जोग संसाधन, प्रतिसत में।",
    },
    # ---- sources and data coverage
    "sources_header": {
        "en": "Sources for {place}:", "hi": "{place} के स्रोत:", "hinglish": "{place} ke sources:",
        "mr": "{place} चे स्रोत:", "pa": "{place} ਦੇ ਸਰੋਤ:", "raj": "{place} रा स्रोत:",
    },
    "sources_general": {
        "en": "JalMitra answers only from these official publications (assessment year {years}):",
        "hi": "JalMitra केवल इन आधिकारिक प्रकाशनों से जवाब देता है (आकलन वर्ष {years}):",
        "hinglish": "JalMitra sirf in official publications se jawab deta hai (assessment year {years}):",
        "mr": "JalMitra फक्त या अधिकृत प्रकाशनांमधून उत्तर देते (मूल्यांकन वर्ष {years}):",
        "pa": "JalMitra ਸਿਰਫ਼ ਇਨ੍ਹਾਂ ਸਰਕਾਰੀ ਪ੍ਰਕਾਸ਼ਨਾਂ ਤੋਂ ਜਵਾਬ ਦਿੰਦਾ ਹੈ (ਮੁਲਾਂਕਣ ਸਾਲ {years}):",
        "raj": "JalMitra फगत आं सरकारी प्रकासनां सूं जवाब देवै (आकलन बरस {years}):",
    },
    "source_line": {
        "en": "- {sid}: {title}, page {page} ({used_for})", "hi": "- {sid}: {title}, पृष्ठ {page} ({used_for})",
        "hinglish": "- {sid}: {title}, page {page} ({used_for})", "mr": "- {sid}: {title}, पान {page} ({used_for})",
        "pa": "- {sid}: {title}, ਪੰਨਾ {page} ({used_for})", "raj": "- {sid}: {title}, पानो {page} ({used_for})",
    },
    "source_pub": {
        "en": "- {sid}: {title} ({url})", "hi": "- {sid}: {title} ({url})", "hinglish": "- {sid}: {title} ({url})",
        "mr": "- {sid}: {title} ({url})", "pa": "- {sid}: {title} ({url})", "raj": "- {sid}: {title} ({url})",
    },
    "cite": {
        "en": "Source: {refs}.", "hi": "स्रोत: {refs}।", "hinglish": "Source: {refs}.",
        "mr": "स्रोत: {refs}.", "pa": "ਸਰੋਤ: {refs}।", "raj": "स्रोत: {refs}।",
    },
    "page_ref": {
        "en": "{sid} p{page}", "hi": "{sid} पृ.{page}", "hinglish": "{sid} p{page}",
        "mr": "{sid} पान {page}", "pa": "{sid} ਪੰਨਾ {page}", "raj": "{sid} पानो {page}",
    },
    "used_category": {
        "en": "category", "hi": "श्रेणी", "hinglish": "category", "mr": "श्रेणी", "pa": "ਸ਼੍ਰੇਣੀ", "raj": "श्रेणी",
    },
    "used_figures": {
        "en": "figures", "hi": "आंकड़े", "hinglish": "figures", "mr": "आकडे", "pa": "ਅੰਕੜੇ", "raj": "आंकड़ा",
    },
    "used_conflict": {
        "en": "different observation of the category", "hi": "श्रेणी का अलग अवलोकन",
        "hinglish": "category ka alag observation", "mr": "श्रेणीचे वेगळे निरीक्षण",
        "pa": "ਸ਼੍ਰੇਣੀ ਦਾ ਵੱਖਰਾ ਨਿਰੀਖਣ", "raj": "श्रेणी रो न्यारो अवलोकन",
    },
    "used_unit_type": {
        "en": "unit type", "hi": "इकाई का प्रकार", "hinglish": "unit type", "mr": "घटकाचा प्रकार",
        "pa": "ਇਕਾਈ ਦੀ ਕਿਸਮ", "raj": "इकाई रो प्रकार",
    },
    "used_area_total": {
        "en": "area total", "hi": "क्षेत्र का कुल", "hinglish": "area total", "mr": "क्षेत्राचे एकूण",
        "pa": "ਖੇਤਰ ਦਾ ਕੁੱਲ", "raj": "इलाका रो कुल",
    },
    "coverage": {
        "en": "Category information: {total} assessment units. Numerical information: {numeric}. Assessment year: {years}. States/UTs: {states}.",
        "hi": "श्रेणी की जानकारी: {total} आकलन इकाइयाँ। संख्यात्मक जानकारी: {numeric}। आकलन वर्ष: {years}। राज्य/केंद्र शासित प्रदेश: {states}।",
        "hinglish": "Category information: {total} assessment units. Numerical information: {numeric}. Assessment year: {years}. States/UTs: {states}.",
        "mr": "श्रेणी माहिती: {total} मूल्यांकन घटक. आकडेवारी: {numeric}. मूल्यांकन वर्ष: {years}. राज्ये/केंद्रशासित प्रदेश: {states}.",
        "pa": "ਸ਼੍ਰੇਣੀ ਜਾਣਕਾਰੀ: {total} ਮੁਲਾਂਕਣ ਇਕਾਈਆਂ। ਅੰਕੜਾ ਜਾਣਕਾਰੀ: {numeric}। ਮੁਲਾਂਕਣ ਸਾਲ: {years}। ਰਾਜ/ਕੇਂਦਰ ਸ਼ਾਸਿਤ ਪ੍ਰਦੇਸ਼: {states}।",
        "raj": "श्रेणी री जाणकारी: {total} आकलन इकाइयां। आंकड़ा री जाणकारी: {numeric}। आकलन बरस: {years}। राज्य: {states}।",
    },
    "place_availability": {
        "en": "For {place}: category is available; numerical figures are {numbers}.",
        "hi": "{place} के लिए: श्रेणी उपलब्ध है; आंकड़े {numbers}।",
        "hinglish": "{place} ke liye: category available hai; numbers {numbers}.",
        "mr": "{place} साठी: श्रेणी उपलब्ध आहे; आकडे {numbers}.",
        "pa": "{place} ਲਈ: ਸ਼੍ਰੇਣੀ ਉਪਲਬਧ ਹੈ; ਅੰਕੜੇ {numbers}।",
        "raj": "{place} सारू: श्रेणी उपलब्ध है; आंकड़ा {numbers}।",
    },
    "available": {
        "en": "available", "hi": "उपलब्ध हैं", "hinglish": "available hain", "mr": "उपलब्ध आहेत",
        "pa": "ਉਪਲਬਧ ਹਨ", "raj": "उपलब्ध है",
    },
    "partly_available": {
        "en": "available for {n} of {total} units", "hi": "{total} में से {n} इकाइयों के उपलब्ध हैं",
        "hinglish": "{total} mein se {n} units ke available hain", "mr": "{total} पैकी {n} घटकांचे उपलब्ध आहेत",
        "pa": "{total} ਵਿੱਚੋਂ {n} ਇਕਾਈਆਂ ਦੇ ਉਪਲਬਧ ਹਨ", "raj": "{total} में सूं {n} इकाइयां रा उपलब्ध है",
    },
    # ---- quality
    "quality_header": {
        "en": "{n} assessment units have data-quality warnings:",
        "hi": "{n} आकलन इकाइयों पर डेटा-गुणवत्ता चेतावनियाँ हैं:",
        "hinglish": "{n} assessment units par data-quality warnings hain:",
        "mr": "{n} मूल्यांकन घटकांवर डेटा-गुणवत्ता इशारे आहेत:",
        "pa": "{n} ਮੁਲਾਂਕਣ ਇਕਾਈਆਂ ਉੱਤੇ ਡਾਟਾ-ਗੁਣਵੱਤਾ ਚੇਤਾਵਨੀਆਂ ਹਨ:",
        "raj": "{n} आकलन इकाइयां माथै डेटा-गुणवत्ता चेतावणी है:",
    },
    "quality_line": {
        "en": "- {unit} ({district}, {state}): {flags}", "hi": "- {unit} ({district}, {state}): {flags}",
        "hinglish": "- {unit} ({district}, {state}): {flags}", "mr": "- {unit} ({district}, {state}): {flags}",
        "pa": "- {unit} ({district}, {state}): {flags}", "raj": "- {unit} ({district}, {state}): {flags}",
    },
    "quality_none": {
        "en": "No data-quality warnings are recorded for {place}.",
        "hi": "{place} के लिए कोई डेटा-गुणवत्ता चेतावनी दर्ज नहीं है।",
        "hinglish": "{place} ke liye koi data-quality warning recorded nahi hai.",
        "mr": "{place} साठी कोणताही डेटा-गुणवत्ता इशारा नोंदलेला नाही.",
        "pa": "{place} ਲਈ ਕੋਈ ਡਾਟਾ-ਗੁਣਵੱਤਾ ਚੇਤਾਵਨੀ ਦਰਜ ਨਹੀਂ ਹੈ।",
        "raj": "{place} सारू कोई डेटा-गुणवत्ता चेतावणी दर्ज कोनी।",
    },
    # ---- warnings (built only from stored flags and values)
    "w_mismatch": {
        "en": "{unit}: the published category is {cat}, but the published stage of extraction ({stage}%) falls in the {vcat} range. The published category is shown unchanged.",
        "hi": "{unit}: प्रकाशित श्रेणी {cat} है, लेकिन प्रकाशित दोहन स्तर ({stage}%) {vcat} की सीमा में आता है। प्रकाशित श्रेणी बिना बदले दिखाई गई है।",
        "hinglish": "{unit}: published category {cat} hai, lekin published extraction stage ({stage}%) {vcat} range mein aata hai. Published category bina badle dikhayi gayi hai.",
        "mr": "{unit}: प्रकाशित श्रेणी {cat} आहे, पण प्रकाशित उपसा टप्पा ({stage}%) {vcat} मर्यादेत येतो. प्रकाशित श्रेणी न बदलता दाखवली आहे.",
        "pa": "{unit}: ਪ੍ਰਕਾਸ਼ਿਤ ਸ਼੍ਰੇਣੀ {cat} ਹੈ, ਪਰ ਪ੍ਰਕਾਸ਼ਿਤ ਨਿਕਾਸੀ ਪੱਧਰ ({stage}%) {vcat} ਦੀ ਹੱਦ ਵਿੱਚ ਆਉਂਦਾ ਹੈ। ਪ੍ਰਕਾਸ਼ਿਤ ਸ਼੍ਰੇਣੀ ਬਿਨਾਂ ਬਦਲੇ ਦਿਖਾਈ ਗਈ ਹੈ।",
        "raj": "{unit}: छपी श्रेणी {cat} है, पण छप्यो दोहन स्तर ({stage}%) {vcat} री सीमा में आवै। छपी श्रेणी बिना बदळ्यां दिखाई है।",
    },
    "w_stagecalc": {
        "en": "{unit}: the published stage of extraction is {stage}%, but total extraction divided by extractable resource from the published volumes gives {calc}%. The published stage is shown unchanged.",
        "hi": "{unit}: प्रकाशित दोहन स्तर {stage}% है, लेकिन प्रकाशित मात्राओं से कुल निकासी ÷ निकालने योग्य संसाधन {calc}% आता है। प्रकाशित स्तर बिना बदले दिखाया गया है।",
        "hinglish": "{unit}: published extraction stage {stage}% hai, lekin published volumes se total extraction ÷ extractable resource {calc}% aata hai. Published stage bina badle dikhaya gaya hai.",
        "mr": "{unit}: प्रकाशित उपसा टप्पा {stage}% आहे, पण प्रकाशित आकड्यांवरून एकूण उपसा ÷ उपसा करण्यायोग्य साठा {calc}% येतो. प्रकाशित टप्पा न बदलता दाखवला आहे.",
        "pa": "{unit}: ਪ੍ਰਕਾਸ਼ਿਤ ਨਿਕਾਸੀ ਪੱਧਰ {stage}% ਹੈ, ਪਰ ਪ੍ਰਕਾਸ਼ਿਤ ਮਾਤਰਾਵਾਂ ਤੋਂ ਕੁੱਲ ਨਿਕਾਸੀ ÷ ਕੱਢਣਯੋਗ ਸਰੋਤ {calc}% ਬਣਦਾ ਹੈ। ਪ੍ਰਕਾਸ਼ਿਤ ਪੱਧਰ ਬਿਨਾਂ ਬਦਲੇ ਦਿਖਾਇਆ ਗਿਆ ਹੈ।",
        "raj": "{unit}: छप्यो दोहन स्तर {stage}% है, पण छपी मात्रा सूं कुल निकासी ÷ काढ़बा जोग संसाधन {calc}% आवै। छप्यो स्तर बिना बदळ्यां दिखायो है।",
    },
    "w_saline_zero": {
        "en": "{unit}: this saline unit is published with 0 for recharge, extractable resource and extraction, and no stage of extraction. These zeros are shown as printed and must not be read as a confirmed zero; they need verification.",
        "hi": "{unit}: यह लवणीय इकाई पुनर्भरण, निकालने योग्य संसाधन और निकासी के लिए 0 के साथ प्रकाशित है और इसका दोहन स्तर नहीं है। ये शून्य जैसे छपे हैं वैसे दिखाए गए हैं; इन्हें पक्का शून्य न मानें, इनकी जाँच ज़रूरी है।",
        "hinglish": "{unit}: yeh saline unit recharge, extractable resource aur extraction ke liye 0 ke saath published hai, aur iska extraction stage nahi hai. Yeh zero jaise chhape hain waise dikhaye gaye hain; inhe pakka zero na maanein, verification zaroori hai.",
        "mr": "{unit}: हा क्षारयुक्त घटक पुनर्भरण, उपसा करण्यायोग्य साठा आणि उपसा यासाठी 0 सह प्रकाशित आहे आणि त्याचा उपसा टप्पा नाही. हे शून्य जसे छापले तसे दाखवले आहेत; त्यांना निश्चित शून्य मानू नका, पडताळणी आवश्यक आहे.",
        "pa": "{unit}: ਇਹ ਖਾਰੀ ਇਕਾਈ ਰੀਚਾਰਜ, ਕੱਢਣਯੋਗ ਸਰੋਤ ਅਤੇ ਨਿਕਾਸੀ ਲਈ 0 ਨਾਲ ਪ੍ਰਕਾਸ਼ਿਤ ਹੈ ਅਤੇ ਇਸ ਦਾ ਨਿਕਾਸੀ ਪੱਧਰ ਨਹੀਂ ਹੈ। ਇਹ ਸਿਫ਼ਰ ਜਿਵੇਂ ਛਪੇ ਉਵੇਂ ਦਿਖਾਏ ਗਏ ਹਨ; ਇਨ੍ਹਾਂ ਨੂੰ ਪੱਕਾ ਸਿਫ਼ਰ ਨਾ ਮੰਨੋ, ਜਾਂਚ ਜ਼ਰੂਰੀ ਹੈ।",
        "raj": "{unit}: आ खारी इकाई पुनर्भरण, काढ़बा जोग संसाधन अर निकासी सारू 0 साथै छपी है अर इणरो दोहन स्तर कोनी। ऐ शून्य जियां छप्या वियां दिखाया है; इणनै पक्को शून्य मत मानो, जांच जरूरी है।",
    },
    "w_conflict": {
        "en": "{unit}: the sources disagree about this unit's category: {obs}. JalMitra does not choose one source as correct.",
        "hi": "{unit}: इस इकाई की श्रेणी पर स्रोत अलग-अलग हैं: {obs}। JalMitra किसी एक स्रोत को सही नहीं चुनता।",
        "hinglish": "{unit}: is unit ki category par sources alag-alag hain: {obs}. JalMitra kisi ek source ko sahi nahi chunta.",
        "mr": "{unit}: या घटकाच्या श्रेणीबद्दल स्रोतांमध्ये मतभेद आहेत: {obs}. JalMitra कोणताही एक स्रोत बरोबर म्हणून निवडत नाही.",
        "pa": "{unit}: ਇਸ ਇਕਾਈ ਦੀ ਸ਼੍ਰੇਣੀ ਬਾਰੇ ਸਰੋਤ ਵੱਖ-ਵੱਖ ਹਨ: {obs}। JalMitra ਕਿਸੇ ਇੱਕ ਸਰੋਤ ਨੂੰ ਸਹੀ ਨਹੀਂ ਚੁਣਦਾ।",
        "raj": "{unit}: इण इकाई री श्रेणी माथै स्रोत न्यारा-न्यारा है: {obs}। JalMitra किणी एक स्रोत नै सही कोनी चुणै।",
    },
    "w_truncated": {
        "en": "{unit}: the name is printed as '{printed}' (cut off) in the {sid} report that the figures come from.",
        "hi": "{unit}: जिस {sid} रिपोर्ट से आंकड़े लिए गए, उसमें नाम '{printed}' (अधूरा) छपा है।",
        "hinglish": "{unit}: jis {sid} report se numbers liye gaye, usme naam '{printed}' (adhoora) chhapa hai.",
        "mr": "{unit}: ज्या {sid} अहवालातून आकडे घेतले, त्यात नाव '{printed}' (अपूर्ण) छापले आहे.",
        "pa": "{unit}: ਜਿਸ {sid} ਰਿਪੋਰਟ ਤੋਂ ਅੰਕੜੇ ਲਏ ਗਏ, ਉਸ ਵਿੱਚ ਨਾਂ '{printed}' (ਅਧੂਰਾ) ਛਪਿਆ ਹੈ।",
        "raj": "{unit}: जिण {sid} रिपोर्ट सूं आंकड़ा लिया, उणमें नाम '{printed}' (अधूरो) छप्यो है।",
    },
    "w_nc_flag": {
        "en": "{area} (National Compilation): {flags}.", "hi": "{area} (राष्ट्रीय संकलन): {flags}।",
        "hinglish": "{area} (National Compilation): {flags}.", "mr": "{area} (राष्ट्रीय संकलन): {flags}.",
        "pa": "{area} (ਰਾਸ਼ਟਰੀ ਸੰਕਲਨ): {flags}।", "raj": "{area} (राष्ट्रीय संकलन): {flags}।",
    },
    # ---- dialogue
    "not_found": {
        "en": "I could not find '{name}' in the JalMitra database.",
        "hi": "JalMitra डेटाबेस में '{name}' नहीं मिला।",
        "hinglish": "JalMitra database mein '{name}' nahi mila.",
        "mr": "JalMitra डेटाबेसमध्ये '{name}' सापडले नाही.",
        "pa": "JalMitra ਡਾਟਾਬੇਸ ਵਿੱਚ '{name}' ਨਹੀਂ ਮਿਲਿਆ।",
        "raj": "JalMitra डेटाबेस में '{name}' कोनी मिल्यो।",
    },
    "unknown_place": {
        "en": "I could not find a block, district or state from the database in your question.",
        "hi": "आपके सवाल में डेटाबेस का कोई ब्लॉक, ज़िला या राज्य नहीं मिला।",
        "hinglish": "Aapke sawal mein database ka koi block, district ya state nahi mila.",
        "mr": "तुमच्या प्रश्नात डेटाबेसमधील कोणताही ब्लॉक, जिल्हा किंवा राज्य सापडले नाही.",
        "pa": "ਤੁਹਾਡੇ ਸਵਾਲ ਵਿੱਚ ਡਾਟਾਬੇਸ ਦਾ ਕੋਈ ਬਲਾਕ, ਜ਼ਿਲ੍ਹਾ ਜਾਂ ਰਾਜ ਨਹੀਂ ਮਿਲਿਆ।",
        "raj": "थारै सवाल में डेटाबेस रो कोई ब्लॉक, जिलो या राज्य कोनी मिल्यो।",
    },
    "did_you_mean": {
        "en": "Did you mean one of these? Reply with the number or the name:",
        "hi": "क्या आपका मतलब इनमें से कोई है? नंबर या नाम लिखकर जवाब दें:",
        "hinglish": "Kya aapka matlab inme se koi hai? Number ya naam likh kar reply karein:",
        "mr": "तुम्हाला यांपैकी एखादे म्हणायचे आहे का? क्रमांक किंवा नाव लिहून उत्तर द्या:",
        "pa": "ਕੀ ਤੁਹਾਡਾ ਮਤਲਬ ਇਨ੍ਹਾਂ ਵਿੱਚੋਂ ਕੋਈ ਹੈ? ਨੰਬਰ ਜਾਂ ਨਾਂ ਲਿਖ ਕੇ ਜਵਾਬ ਦਿਓ:",
        "raj": "कांई थारो मतलब आं में सूं कोई है? नंबर या नाम लिख नै जवाब देवो:",
    },
    "clarify": {
        "en": "'{name}' matches more than one place in the database. Which one do you mean? Reply with the number:",
        "hi": "'{name}' नाम से डेटाबेस में एक से ज़्यादा जगहें हैं। आप कौन-सी जगह पूछ रहे हैं? नंबर लिखकर जवाब दें:",
        "hinglish": "'{name}' naam se database mein ek se zyada jagah hain. Aap kaunsi jagah pooch rahe hain? Number likh kar reply karein:",
        "mr": "'{name}' या नावाची डेटाबेसमध्ये एकापेक्षा जास्त ठिकाणे आहेत. तुम्ही कोणते विचारत आहात? क्रमांक लिहून उत्तर द्या:",
        "pa": "'{name}' ਨਾਂ ਨਾਲ ਡਾਟਾਬੇਸ ਵਿੱਚ ਇੱਕ ਤੋਂ ਵੱਧ ਥਾਵਾਂ ਹਨ। ਤੁਸੀਂ ਕਿਹੜੀ ਪੁੱਛ ਰਹੇ ਹੋ? ਨੰਬਰ ਲਿਖ ਕੇ ਜਵਾਬ ਦਿਓ:",
        "raj": "'{name}' नाम सूं डेटाबेस में एक सूं घणी जगां है। थे किसी जगां पूछ रिया हो? नंबर लिख नै जवाब देवो:",
    },
    "opt_unit": {
        "en": "{unit} ({kind} in {district} district, {state})", "hi": "{unit} ({kind}, {district} ज़िला, {state})",
        "hinglish": "{unit} ({kind}, {district} district, {state})", "mr": "{unit} ({kind}, {district} जिल्हा, {state})",
        "pa": "{unit} ({kind}, {district} ਜ਼ਿਲ੍ਹਾ, {state})", "raj": "{unit} ({kind}, {district} जिलो, {state})",
    },
    "opt_state": {
        "en": "{state} (state/UT)", "hi": "{state} (राज्य)", "hinglish": "{state} (state)",
        "mr": "{state} (राज्य)", "pa": "{state} (ਰਾਜ)", "raj": "{state} (राज्य)",
    },
    "need_place": {
        "en": "Please name a block, district or state, for example: Is Ajmer Urban safe?",
        "hi": "कृपया किसी ब्लॉक, ज़िले या राज्य का नाम बताइए, जैसे: अजमेर ज़िले की भूजल स्थिति क्या है?",
        "hinglish": "Kripya kisi block, district ya state ka naam batayein, jaise: Ajmer Urban ka paani kaisa hai?",
        "mr": "कृपया ब्लॉक, जिल्हा किंवा राज्याचे नाव सांगा, उदा.: पुणे जिल्ह्यातील भूजल स्थिती काय आहे?",
        "pa": "ਕਿਰਪਾ ਕਰਕੇ ਕਿਸੇ ਬਲਾਕ, ਜ਼ਿਲ੍ਹੇ ਜਾਂ ਰਾਜ ਦਾ ਨਾਂ ਦੱਸੋ, ਜਿਵੇਂ: ਲੁਧਿਆਣਾ ਵਿੱਚ ਪਾਣੀ ਦੀ ਸਥਿਤੀ ਕੀ ਹੈ?",
        "raj": "किणी ब्लॉक, जिला या राज्य रो नाम बताओ, जियां: म्हारो अजमेर जिलो रो पाणी कियां है?",
    },
    "need_category": {
        "en": "Please name a category: Safe, Semi-critical, Critical, Over-exploited or Saline.",
        "hi": "कृपया एक श्रेणी बताइए: Safe, Semi-critical, Critical, Over-exploited या Saline।",
        "hinglish": "Kripya ek category batayein: Safe, Semi-critical, Critical, Over-exploited ya Saline.",
        "mr": "कृपया एक श्रेणी सांगा: Safe, Semi-critical, Critical, Over-exploited किंवा Saline.",
        "pa": "ਕਿਰਪਾ ਕਰਕੇ ਇੱਕ ਸ਼੍ਰੇਣੀ ਦੱਸੋ: Safe, Semi-critical, Critical, Over-exploited ਜਾਂ Saline।",
        "raj": "एक श्रेणी बताओ: Safe, Semi-critical, Critical, Over-exploited या Saline।",
    },
    "off_topic": {
        "en": "I can only answer questions about groundwater, soil, water quality, crops, irrigation and land, from the datasets loaded in JalMitra. Ask *What is JalMitra?* to see what is covered.",
        "hi": "मैं केवल JalMitra में लोड किए गए डेटासेट से भूजल, मिट्टी, पानी की गुणवत्ता, फसल, सिंचाई और भूमि से जुड़े सवालों के जवाब दे सकता हूँ। क्या-क्या शामिल है, यह जानने के लिए पूछें: *JalMitra क्या है?*",
        "hinglish": "Main sirf JalMitra mein load kiye gaye datasets se groundwater, mitti, paani ki quality, fasal, sinchai aur zameen ke sawalon ka jawab de sakta hoon. Kya-kya shamil hai, jaanne ke liye poochiye: *JalMitra kya hai?*",
        "mr": "मी फक्त JalMitra मध्ये लोड केलेल्या डेटासेटमधून भूजल, माती, पाण्याची गुणवत्ता, पिके, सिंचन आणि जमीन याबद्दलच्या प्रश्नांची उत्तरे देऊ शकतो. काय समाविष्ट आहे हे पाहण्यासाठी विचारा: *JalMitra काय आहे?*",
        "pa": "ਮੈਂ ਸਿਰਫ਼ JalMitra ਵਿੱਚ ਲੋਡ ਕੀਤੇ ਡਾਟਾਸੈੱਟਾਂ ਤੋਂ ਧਰਤੀ ਹੇਠਲੇ ਪਾਣੀ, ਮਿੱਟੀ, ਪਾਣੀ ਦੀ ਗੁਣਵੱਤਾ, ਫ਼ਸਲਾਂ, ਸਿੰਚਾਈ ਅਤੇ ਜ਼ਮੀਨ ਬਾਰੇ ਸਵਾਲਾਂ ਦੇ ਜਵਾਬ ਦੇ ਸਕਦਾ ਹਾਂ। ਕੀ-ਕੀ ਸ਼ਾਮਲ ਹੈ, ਇਹ ਜਾਣਨ ਲਈ ਪੁੱਛੋ: *JalMitra ਕੀ ਹੈ?*",
        "raj": "म्हैं फगत JalMitra में लोड करियोड़ा डेटासेट सूं भूजल, माटी, पाणी री गुणवत्ता, फसल, सिंचाई अर जमीन रा सवालां रो जवाब दे सकूं। कांई-कांई सामिल है, ओ जाणण सारू पूछो: *JalMitra कांई है?*",
    },
    "blocked": {
        "en": "Sorry, I can't follow that request. I only read the official groundwater database and never change its data or rules.",
        "hi": "क्षमा करें, मैं यह अनुरोध नहीं मान सकता। मैं केवल आधिकारिक भूजल डेटाबेस पढ़ता हूँ और उसके डेटा या नियम कभी नहीं बदलता।",
        "hinglish": "Sorry, main yeh request nahi maan sakta. Main sirf official groundwater database padhta hoon aur uska data ya rules kabhi nahi badalta.",
        "mr": "माफ करा, मी ही विनंती पाळू शकत नाही. मी फक्त अधिकृत भूजल डेटाबेस वाचतो आणि त्याचा डेटा किंवा नियम कधीही बदलत नाही.",
        "pa": "ਮਾਫ਼ ਕਰਨਾ, ਮੈਂ ਇਹ ਬੇਨਤੀ ਨਹੀਂ ਮੰਨ ਸਕਦਾ। ਮੈਂ ਸਿਰਫ਼ ਸਰਕਾਰੀ ਡਾਟਾਬੇਸ ਪੜ੍ਹਦਾ ਹਾਂ ਅਤੇ ਉਸ ਦਾ ਡਾਟਾ ਜਾਂ ਨਿਯਮ ਕਦੇ ਨਹੀਂ ਬਦਲਦਾ।",
        "raj": "माफ करजो, म्हैं आ अरज कोनी मान सकूं। म्हैं फगत सरकारी भूजल डेटाबेस बांचूं अर उणरो डेटा या नियम कदेई कोनी बदळूं।",
    },
    "no_estimate": {
        "en": "I don't estimate, guess or make up groundwater figures. I only show values recorded in the official database.",
        "hi": "मैं भूजल के आंकड़ों का अनुमान नहीं लगाता और न ही उन्हें गढ़ता हूँ। मैं केवल आधिकारिक डेटाबेस में दर्ज मान दिखाता हूँ।",
        "hinglish": "Main groundwater figures ka andaza nahi lagata aur na hi banata hoon. Main sirf official database mein recorded values dikhata hoon.",
        "mr": "मी भूजल आकड्यांचा अंदाज लावत नाही किंवा ते तयार करत नाही. मी फक्त अधिकृत डेटाबेसमध्ये नोंदलेली मूल्ये दाखवतो.",
        "pa": "ਮੈਂ ਪਾਣੀ ਦੇ ਅੰਕੜਿਆਂ ਦਾ ਅੰਦਾਜ਼ਾ ਨਹੀਂ ਲਗਾਉਂਦਾ ਅਤੇ ਨਾ ਹੀ ਬਣਾਉਂਦਾ ਹਾਂ। ਮੈਂ ਸਿਰਫ਼ ਸਰਕਾਰੀ ਡਾਟਾਬੇਸ ਵਿੱਚ ਦਰਜ ਮੁੱਲ ਦਿਖਾਉਂਦਾ ਹਾਂ।",
        "raj": "म्हैं भूजल रा आंकड़ां रो अंदाजो कोनी लगाऊं अर ना ही घड़ूं। म्हैं फगत सरकारी डेटाबेस में दर्ज मान दिखाऊं।",
    },
    "rephrase": {
        "en": "Sorry, I did not understand the question confidently. Please ask it another way, for example: Is Ajmer Urban safe? / Top 5 over-exploited blocks in Rajasthan. You can also ask *What is JalMitra?*",
        "hi": "क्षमा करें, मैं सवाल ठीक से नहीं समझ पाया। कृपया दूसरे तरीके से पूछें, जैसे: जयपुर ज़िले में भूजल की स्थिति क्या है? आप *JalMitra क्या है?* भी पूछ सकते हैं।",
        "hinglish": "Sorry, main sawal theek se nahi samajh paaya. Kripya doosre tareeke se poochiye, jaise: Ajmer Urban ka paani kaisa hai? Aap *JalMitra kya hai?* bhi pooch sakte hain.",
        "mr": "माफ करा, मला प्रश्न नीट समजला नाही. कृपया वेगळ्या प्रकारे विचारा, उदा.: पुणे जिल्ह्यातील भूजल स्थिती काय आहे? तुम्ही *JalMitra काय आहे?* असेही विचारू शकता.",
        "pa": "ਮਾਫ਼ ਕਰਨਾ, ਮੈਂ ਸਵਾਲ ਠੀਕ ਤਰ੍ਹਾਂ ਨਹੀਂ ਸਮਝ ਸਕਿਆ। ਕਿਰਪਾ ਕਰਕੇ ਹੋਰ ਤਰੀਕੇ ਨਾਲ ਪੁੱਛੋ, ਜਿਵੇਂ: ਲੁਧਿਆਣਾ ਜ਼ਿਲ੍ਹੇ ਵਿੱਚ ਪਾਣੀ ਦੀ ਸਥਿਤੀ ਕੀ ਹੈ? ਤੁਸੀਂ *JalMitra ਕੀ ਹੈ?* ਵੀ ਪੁੱਛ ਸਕਦੇ ਹੋ।",
        "raj": "माफ करजो, म्हैं सवाल ठीक सूं कोनी समझ्यो। दूजे ढंग सूं पूछो, जियां: म्हारो अजमेर जिलो रो पाणी कियां है? थे *JalMitra कांई है?* भी पूछ सको।",
    },
    "help": {
        "en": "Hello! I answer from the official groundwater assessment database. Try: Is Ajmer Urban safe? / Top 5 over-exploited blocks in Rajasthan / Compare Jaipur district and Jodhpur district / What does semi-critical mean? Ask *What is JalMitra?* to see everything I can do.",
        "hi": "नमस्ते! मैं आधिकारिक भूजल आकलन डेटाबेस से जवाब देता हूँ। पूछकर देखें: जयपुर ज़िले में भूजल की स्थिति क्या है? / राजस्थान के 5 सबसे ज़्यादा दोहन वाले ब्लॉक / अतिदोहित का मतलब क्या है? मैं क्या-क्या कर सकता हूँ, यह जानने के लिए पूछें: *JalMitra क्या है?*",
        "hinglish": "Namaste! Main official groundwater assessment database se jawab deta hoon. Poochiye: Ajmer Urban ka paani kaisa hai? / Rajasthan ke top 5 over-exploited block / Semi-critical ka matlab kya hai? Main kya-kya kar sakta hoon, yeh jaanne ke liye poochiye: *JalMitra kya hai?*",
        "mr": "नमस्कार! मी अधिकृत भूजल मूल्यांकन डेटाबेसमधून उत्तर देतो. विचारून पहा: पुणे जिल्ह्यातील भूजल स्थिती काय आहे? / अतिशोषित म्हणजे काय? मी काय काय करू शकतो हे पाहण्यासाठी विचारा: *JalMitra काय आहे?*",
        "pa": "ਸਤ ਸ੍ਰੀ ਅਕਾਲ! ਮੈਂ ਸਰਕਾਰੀ ਭੂਜਲ ਮੁਲਾਂਕਣ ਡਾਟਾਬੇਸ ਤੋਂ ਜਵਾਬ ਦਿੰਦਾ ਹਾਂ। ਪੁੱਛ ਕੇ ਵੇਖੋ: ਲੁਧਿਆਣਾ ਜ਼ਿਲ੍ਹੇ ਵਿੱਚ ਪਾਣੀ ਦੀ ਸਥਿਤੀ ਕੀ ਹੈ? / ਵੱਧ-ਸ਼ੋਸ਼ਿਤ ਦਾ ਮਤਲਬ ਕੀ ਹੈ? ਮੈਂ ਕੀ-ਕੀ ਕਰ ਸਕਦਾ ਹਾਂ, ਇਹ ਜਾਣਨ ਲਈ ਪੁੱਛੋ: *JalMitra ਕੀ ਹੈ?*",
        "raj": "खम्मा घणी! म्हैं सरकारी भूजल आकलन डेटाबेस सूं जवाब देऊं। पूछ नै देखो: म्हारो अजमेर जिलो रो पाणी कियां है? / अतिदोहित रो कांई मतलब है? म्हैं कांई-कांई कर सकूं, ओ जाणण सारू पूछो: *JalMitra कांई है?*",
    },
    "no_data": {
        "en": "No official groundwater data imported yet. Build the database with build_dataset.py and build_database.py.",
        "hi": "अभी तक कोई आधिकारिक भूजल डेटा आयात नहीं हुआ है। build_dataset.py और build_database.py से डेटाबेस बनाइए।",
        "hinglish": "Abhi tak koi official groundwater data import nahi hua hai. build_dataset.py aur build_database.py se database banaiye.",
        "mr": "अजून कोणताही अधिकृत भूजल डेटा आयात झालेला नाही. build_dataset.py आणि build_database.py वापरून डेटाबेस तयार करा.",
        "pa": "ਹਾਲੇ ਤੱਕ ਕੋਈ ਸਰਕਾਰੀ ਡਾਟਾ ਇੰਪੋਰਟ ਨਹੀਂ ਹੋਇਆ। build_dataset.py ਅਤੇ build_database.py ਨਾਲ ਡਾਟਾਬੇਸ ਬਣਾਓ।",
        "raj": "अबार तांई कोई सरकारी भूजल डेटा कोनी आयो। build_dataset.py अर build_database.py सूं डेटाबेस बणावो।",
    },
    "followups": {
        "en": "You can also ask: {items}", "hi": "आप यह भी पूछ सकते हैं: {items}", "hinglish": "Aap yeh bhi pooch sakte hain: {items}",
        "mr": "तुम्ही हेही विचारू शकता: {items}", "pa": "ਤੁਸੀਂ ਇਹ ਵੀ ਪੁੱਛ ਸਕਦੇ ਹੋ: {items}", "raj": "थे ओ भी पूछ सको: {items}",
    },
    "fu_sources": {
        "en": "Show the sources", "hi": "स्रोत दिखाओ", "hinglish": "Sources dikhao", "mr": "स्रोत दाखवा",
        "pa": "ਸਰੋਤ ਦਿਖਾਓ", "raj": "स्रोत दिखावो",
    },
    "fu_other": {
        "en": "What about another place?", "hi": "किसी दूसरी जगह का क्या?", "hinglish": "Doosri jagah ka kya?",
        "mr": "दुसऱ्या ठिकाणाचे काय?", "pa": "ਕਿਸੇ ਹੋਰ ਥਾਂ ਦਾ ਕੀ?", "raj": "दूजी जगां रो कांई?",
    },
    "fu_both": {
        "en": "Compare both", "hi": "दोनों की तुलना करो", "hinglish": "Dono ki tulna karo", "mr": "दोन्हींची तुलना करा",
        "pa": "ਦੋਵਾਂ ਦੀ ਤੁਲਨਾ ਕਰੋ", "raj": "दोनूं री तुलना करो",
    },
    "fu_meaning": {
        "en": "What does {cat} mean?", "hi": "{cat} का मतलब क्या है?", "hinglish": "{cat} ka matlab kya hai?",
        "mr": "{cat} म्हणजे काय?", "pa": "{cat} ਦਾ ਮਤਲਬ ਕੀ ਹੈ?", "raj": "{cat} रो कांई मतलब है?",
    },
}

# JalMitra 3.0 templates (domains without data, memory messages, answer-mode labels)
from templates_v3 import TEMPLATES_V3  # noqa: E402

TEMPLATES.update(TEMPLATES_V3)
from templates_kn import TEMPLATES_KN  # noqa: E402  (JalMitra 3.0 Phases 2-5)
TEMPLATES.update(TEMPLATES_KN)
from templates_app import TEMPLATES_APP  # noqa: E402  (questions about JalMitra itself)
TEMPLATES.update(TEMPLATES_APP)


def t(key, lang, **values):
    """Fill one template. Falls back to English only if a translation is missing."""
    entry = TEMPLATES[key]
    text = entry.get(lang) or entry["en"]
    return text.format(**values) if values else text


def missing_translations():
    """(key, language) pairs without a template; used by the tests."""
    return [(k, code) for k, entry in TEMPLATES.items() for code in LANGUAGES if not entry.get(code)]


def message(code, key):
    """Fixed app message in a language (kept for older callers)."""
    return t(key if key in TEMPLATES else "rephrase", code)

"""
app_info.py - Questions about JalMitra itself ("What is this website about?", "JalMitra kya hai?").

Five intents, answered from fixed multilingual texts (templates_app.py). They are detected
before place lookup, so they never reach SQL, groundwater entity resolution or the
low-confidence fallback. Greetings ("hello", "namaste") keep the older "help" intent.

  ABOUT_JALMITRA   what JalMitra / this website is, what it is for
  WHAT_CAN_YOU_DO  what it can do, services, how it helps farmers, what its use is
  HOW_TO_USE       how to use it, how it works, getting started
  HELP             "help", "help me", "madad"
  FEATURE_LIST     which features / sections / pages exist
"""

import re

APP_INTENTS = ("ABOUT_JALMITRA", "WHAT_CAN_YOU_DO", "HOW_TO_USE", "HELP", "FEATURE_LIST")
TEMPLATE = {"ABOUT_JALMITRA": "app_about", "WHAT_CAN_YOU_DO": "app_can_do", "HOW_TO_USE": "app_how_to",
            "HELP": "app_help", "FEATURE_LIST": "app_features"}

# "JalMitra" and common misspellings: jalmitra, jal mitra, jal-mitra, jalmithra, jalmitr, jalamitra, jalmitraa
BRAND = re.compile(r"(?<![\w])(jal[\s\-]?a?[\s\-]?mi(?:t|tt|th)h?r(?:a|aa)?|जल\s?मित्र|ਜਲ\s?ਮਿੱਤਰ|ਜਲ\s?ਮਿਤਰ)(?![\w])")
SELF = re.compile(r"(?<![\w])((this|your) (website|web site|site|app|application|platform|project|tool|portal|chatbot|bot)"
                  r"|the (website|app|application|platform|portal|chatbot)"
                  r"|(ye|yeh|is|iss) (website|site|app|application)"
                  r"|(यह|ये|इस|इसका) (वेबसाइट|साइट|ऐप|एप्लिकेशन|प्रोजेक्ट|परियोजना)"
                  r"|(ही|या|हे) (वेबसाइट|साइट|ॲप|अ‍ॅप)|(ਇਹ|ਇਸ) (ਵੈੱਬਸਾਈਟ|ਵੈਬਸਾਈਟ|ਸਾਈਟ|ਐਪ)"
                  r"|(आ|इण) (वेबसाइट|साइट))(?![\w])")
DATA_WORDS = re.compile(r"(?<![\w])(stage|extraction|recharge|over-exploited|semi-critical|critical|saline|block|blocks|"
                        r"district|districts|tehsil|taluk|safe|top \d+|compare|soil|crop|crops|fluoride|nitrate|"
                        r"ब्लॉक|ज़िला|जिला|ज़िले|जिले|मिट्टी|फसल)(?![\w])")

FEATURES = re.compile(r"(?<![\w])(features?|feature list|sections|pages|menu|modules|services available|"
                      r"सुविधाएँ|सुविधाएं|सुविधा|फ़ीचर|फीचर|विभाग|ਸਹੂਲਤਾਂ|ਫੀਚਰ|सुविधा कोणत्या|वैशिष्ट्ये)(?![\w])")
HOW = re.compile(r"(?<![\w])(how (can|do|should|to) (i |we )?(use|start)|how (does|do) (it|this|jalmitra|you) work|"
                 r"get(ting)? started|how to ask|kaise (use|istemal|istemaal|chalaye|chalayen|upyog)|"
                 r"(use|istemal|upyog) kaise|कैसे (इस्तेमाल|उपयोग|चलाएँ|चलाएं|शुरू)|(इस्तेमाल|उपयोग) कैसे|"
                 r"कसे (वापरायचे|वापरावे)|ਕਿਵੇਂ (ਵਰਤ|ਵਰਤੀਏ|ਵਰਤਾਂ)|कियां (वापरां|काम में लेवां))(?![\w])")
CAN_DO = re.compile(r"(?<![\w])(what (can|do|will) (you|it|i|we) (do|offer|provide)|what can i do here|what services|"
                    r"which services|services do you|what do you do|what does (this|jalmitra) do|what (does|do|can) (this |the |your )?(website|site|app|application|platform|portal|project|chatbot|jal ?mitra) (do|offer|provide)|"
                    r"how (does|can|will|would) (it|this|you|jalmitra) help|help (farmers|kisan|me with)|"
                    r"kya kar sakte|kya kar sakta|kya kar sakti|kya karta|kya karti|kya karegi|kya karega|"
                    r"(ka|ki|ke) (use|upyog|fayda|faayda|labh) kya|use kya hai|kya use|kya upyog|kya fayda|kya faayda|kis kaam|kis kam|"
                    r"क्या कर सकते|क्या कर सकता|क्या करता|क्या करती|किस काम|(का|की) (उपयोग|फ़ायदा|फायदा|लाभ) क्या|"
                    r"काय करू शकतो|काय करते|काय उपयोग|कशासाठी|ਕੀ ਕਰ ਸਕਦ|ਕਿਸ ਕੰਮ|ਕੀ ਫ਼ਾਇਦਾ|ਕੀ ਫਾਇਦਾ|"
                    r"कांई कर सकै|किण काम)(?![\w])")
ABOUT = re.compile(r"(?<![\w])(what is|what's|whats|who is|tell me about|about|explain|introduce|introduction|"
                   r"is for what|for what|used for|purpose|meant for|kya hai|kya he|kya h|kis liye|kisliye|"
                   r"kiske liye|ke bare|ke baare|kya cheez|क्या है|किस लिए|किसलिए|के बारे|परिचय|काय आहे|"
                   r"कशासाठी आहे|बद्दल|ਕੀ ਹੈ|ਕਿਸ ਲਈ|ਬਾਰੇ|कांई है|कांई हुवै|किण सारू)(?![\w])")
HELP_ONLY = re.compile(r"^\s*(help|help me|help please|please help|i need help|need help|madad|madad karo|madad kijiye|"
                       r"मदद|मदद करो|मदद करें|मदद कीजिए|सहायता|मदत|मदत करा|ਮਦਦ|ਮਦਦ ਕਰੋ|मदद करो सा)\s*[?!.।]*\s*$")
HELP_ANY = re.compile(r"(?<![\w])(help|madad|मदद|सहायता|मदत|ਮਦਦ)(?![\w])")


def _norm(text):
    return re.sub(r"\s+", " ", re.sub(r"[?!.,;:।॥\"'()\[\]{}]", " ", (text or "").lower())).strip()


# ---------------------------------------------------------------- casual wording (no fixed phrase)
# "things which you can provide me", "your services", "features?", "aap kya kya kar sakte ho".
# Every word must come from these small lists; one unknown word (a place, a crop, "fluoride", "CGWB")
# and the question is left to the normal pipeline. So this never guesses about a place or a data question.
def _words(*groups):
    return frozenset(w for g in groups for w in g.split())


ADDRESS = _words("you your yours yourself u ur this isme ismein here yahan yaha ye yeh",
                 "aap aapka aapki aapke apka apki apke tum tumhara tumhari tumhare tu tera teri tere",
                 "आप आपका आपकी आपके तुम तुम्हारा तुम्हारी तू तेरा इसमें इसमे इसमें यहाँ यहां यह ये",
                 "ਤੁਸੀਂ ਤੁਸੀ ਤੁਹਾਡੀ ਤੁਹਾਡਾ ਤੁਹਾਡੇ ਇਸ ਵਿੱਚ ਇੱਥੇ",
                 "तुम्ही तुमच्या तुमची तुमचे इथे यात",
                 "थे थारी थारो थारा अठै इण")
# nouns that mean "what the app offers" even without "you": "services?", "options", "kya features hai"
OFFER_NOUNS = _words("service services feature features option options capability capabilities facility facilities",
                     "offer function functions functionality offerings menu modules sections tools available",
                     "suvidha suvidhaen suvidhayen suvidhaye",
                     "सुविधा सुविधाएं सुविधाएँ सेवा सेवाएं सेवाएँ फीचर फ़ीचर विकल्प",
                     "ਸਹੂਲਤ ਸਹੂਲਤਾਂ ਸੇਵਾਵਾਂ ਫੀਚਰ ਵਿਕਲਪ", "सुविधा वैशिष्ट्ये सेवा पर्याय", "सुविधावां")
LIST_NOUNS = _words("feature features option options menu modules sections facility facilities suvidha suvidhaen",
                    "suvidhayen suvidhaye सुविधा सुविधाएं सुविधाएँ फीचर फ़ीचर विकल्प ਸਹੂਲਤ ਸਹੂਲਤਾਂ ਫੀਚਰ ਵਿਕਲਪ",
                    "वैशिष्ट्ये पर्याय सुविधावां")
# verbs and words of offering / doing / helping (need "you" / "this" / "aap" with them)
OFFER_WORDS = _words("provide provides providing offer offers offering ways way do does doing help helps support give gives",
                     "get got have has tell capable able info information things thing stuff else",
                     "kar karte karti karta karoge karogi sakte sakta de dete deti doge dogi milega milta mil",
                     "provide offer help",
                     "कर करते करती सकते सकता सकती देते देती दे मिलेगा मिलता मिल",
                     "ਕਰ ਕਰਦੇ ਸਕਦੇ ਸਕਦਾ ਦਿੰਦੇ ਦੇ ਮਿਲਦਾ", "करू करता करते शकता शकतो देता देते मिळेल",
                     "कर सको सकै देवो मिलै")
HOW_WORDS = _words("guide guidance start started begin beginning steps tutorial use using work works",
                   "kaise कैसे ਕਿਵੇਂ कसे कियां शुरू ਸ਼ੁਰੂ सुरू")
FILLER_WORDS = _words("what whats what's which who how why kind kinds type sort of the a an are is am be me i my mine",
                      "we us our can could would will shall should to for with from there all any some other more",
                      "show list tell please kindly pls plz just exactly s ve re ll d in on so",
                      "kya kyaa kaun kaunsa kaunsi kaunse se si sa hai hain he h ho hoon hu ka ki ke ko mujhe mere",
                      "mera meri liye sab aur bhi bata batao batayein yeh ye",
                      "क्या कौन कौनसी कौन-सी सी से सा है हैं हो हूँ का की के को मुझे मेरे मेरा लिए सब और भी बताओ बताइए",
                      "ये यह",
                      "ਕੀ ਕੌਣ ਕਿਹੜੀਆਂ ਕਿਹੜੇ ਹੈ ਹਨ ਹੋ ਦਾ ਦੀ ਦੇ ਨੂੰ ਮੈਨੂੰ ਮੇਰੇ ਲਈ ਸਭ ਅਤੇ ਵੀ ਦੱਸੋ",
                      "काय कोण कोणत्या कोणते आहे आहेत आहात मला माझ्या साठी सर्व आणि पण सांगा",
                      "कांई कुण कोई म्हनै म्हारै सारू सगळा अर भी बतावो")


def _casual(t):
    """Classify a short casual message made only of known words; None when any other word appears."""
    words = re.sub(r"[-–—/]", " ", t).split()
    if not words or len(words) > 12:
        return None
    known = ADDRESS | OFFER_NOUNS | OFFER_WORDS | HOW_WORDS | FILLER_WORDS
    if any(w not in known for w in words):
        return None
    ws = set(words)
    addressed = bool(ws & ADDRESS) or bool(ws & {"ho", "हो", "ਹੋ", "सको"} and ws & OFFER_WORDS) or bool(ws & {"mujhe", "मुझे", "ਮੈਨੂੰ", "मला", "म्हनै"} and ws & {"mil", "मिल", "milega", "मिलेगा", "ਮਿਲਦਾ", "मिळेल", "मिलै"})
    if ws & LIST_NOUNS:
        return "FEATURE_LIST"
    if ws & HOW_WORDS and (addressed or ws & {"guide", "guidance", "tutorial", "steps", "start", "started", "begin", "शुरू", "ਸ਼ੁਰੂ", "सुरू"} or len(words) <= 4):
        return "HOW_TO_USE" if not ws & {"work", "works"} or addressed else None
    if ws & OFFER_NOUNS or (addressed and ws & OFFER_WORDS):
        return "WHAT_CAN_YOU_DO"
    if addressed and ws & {"what", "whats", "who", "kya", "kaun", "क्या", "कौन", "ਕੀ", "ਕੌਣ", "काय", "कोण", "कांई", "कुण"}:
        return "ABOUT_JALMITRA"
    return None


# Words allowed around a "what can you do" / "how do I use" phrase when JalMitra is not named.
# Anything else (a place, a topic) means the person is asking about that thing, not about the app.
FILLER = set("""here you it i we me this the a an do does can could will would please provide offer services service
for to with farmers farmer kisan kisano kisanon people users user use using help helps start started getting get
work works hain hai ho hoon sakte sakta main aap hum yahan yaha kya karta karti kar mere liye ke ki ka
आप मैं हम यहाँ यहां क्या कर सकते सकता सकती हैं है हो मेरे लिए के की का किसान किसानों
ਤੁਸੀਂ ਮੈਂ ਇੱਥੇ ਕੀ ਕਰ ਸਕਦੇ ਸਕਦਾ ਹੋ ਹੈ ਹਾਂ ਲਈ ਕਿਸਾਨ
तुम्ही मी इथे काय करू शकता शकतो आहे साठी शेतकरी
थे म्हैं अठै कांई कर सको सकूं है सारू करसाण""".split())


def _only_filler(t, pattern):
    rest = pattern.sub(" ", t).split()
    return all(w in FILLER for w in rest)


def detect(question):
    """Return one of APP_INTENTS, or None when the question is not about JalMitra itself."""
    t = _norm(question)
    if not t:
        return None
    if HELP_ONLY.match(t):
        return "HELP"
    if DATA_WORDS.search(t):
        return None          # a data question that happens to mention the app goes to the normal pipeline
    brand = bool(BRAND.search(t))
    selfref = bool(SELF.search(t))
    named = brand or selfref
    if FEATURES.search(t) and (named or re.search(r"(what|which) features|(कौन सी|कौन-सी|kaun se|kaun si) "
                                                   r"(सुविधा|features?)", t)):
        return "FEATURE_LIST"
    if HOW.search(t) and (named or _only_filler(t, HOW)):
        return "HOW_TO_USE"
    if CAN_DO.search(t) and (named or _only_filler(t, CAN_DO)):
        return "WHAT_CAN_YOU_DO"
    if named:
        if HELP_ANY.search(t) and not ABOUT.search(t):
            return "HELP"
        return "ABOUT_JALMITRA" if (ABOUT.search(t) or len(t.split()) <= 4) else None
    if re.search(r"(?<![\w])(explain|describe) (this|the|your) (project|website|app|application)(?![\w])", t):
        return "ABOUT_JALMITRA"
    return _casual(t)

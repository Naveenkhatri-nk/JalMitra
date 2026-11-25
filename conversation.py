"""
conversation.py - Everyday conversation around the data questions, without any LLM.

  * small talk        "nice", "thanks", "ok", "bye", "how are you", "are you a robot", "galat hai" ...
  * scope questions   "Is this site about money?" -> "No ...", "Is this about groundwater?" -> "Yes ..."
  * out of scope      money, loans, schemes, prices, weather, pests, animals -> polite answer + where to look
  * fallback          when nothing is understood, the words that WERE recognised pick the closest real questions

Rules: whole-message matching for small talk (one unknown word and it is not small talk), out-of-scope words are
specific phrases, a place name always keeps the question in the data pipeline (except money/price/weather words,
which JalMitra has no data for anyway). Replies rotate through a few wordings so the same sentence is not repeated.
Nothing here reads a database. Texts in six languages; non-English texts are pending native review.
"""

import re

LANGS = ("en", "hi", "hinglish", "mr", "pa", "raj")


SMS = {"u": "you", "r": "are", "ur": "your", "urs": "yours", "gr8": "great", "gud": "good", "gd": "good",
       "nyc": "nice", "nic": "nice", "thnks": "thanks", "thnx": "thanks", "thanx": "thanks", "tnks": "thanks",
       "tks": "thanks", "thks": "thanks", "thankx": "thanks", "plz": "please", "pls": "please", "plss": "please",
       "nhi": "nahi", "tq": "thanks", "tqsm": "thanks", "tysm": "thanks", "nite": "night", "hlo": "hello", "helo": "hello", "hloo": "hello", "hellow": "hello", "ohk": "ok", "okh": "ok", "nai": "nahi", "nahin": "nahi", "h": "hai", "hn": "haan", "wat": "what", "wht": "what",
       "hw": "how", "abt": "about", "dis": "this", "gn": "good night", "gm": "good morning",
       "tc": "take care", "bbye": "bye", "okey": "ok", "okie": "ok", "kk": "ok", "oky": "ok",
       "acha": "accha", "achha": "accha", "thik": "theek", "didnt": "did not", "dont": "do not", "cant": "cannot",
       "whats": "what is", "wats": "what is", "tmrw": "tomorrow", "tmr": "tomorrow", "2day": "today", "2morrow": "tomorrow"}
KEEP_DOUBLE = set("good cool see too free feel need seed weed food book look soon moon well all till still small "
                  "really sorry hello bless happy accha".split())


def _norm(text):
    t = (text or "").lower()
    t = re.sub(r"[\U0001F300-\U0001FAFF☀-➿]", lambda m: " " + EMOJI.get(m.group(0), "") + " ", t)
    t = re.sub(r"[?!.,;:।॥\"()\[\]{}*~_]+", " ", t)
    t = re.sub(r"(?<=\w)'(?=\w)", "", t).replace("'", " ")          # don't -> dont, tomorrow's -> tomorrows
    t = re.sub(r"(?<=\w)-(?=\w)", " ", t)
    t = re.sub(r"([a-z])\1{2,}", r"\1\1", t)                          # "thank uuu", "hiii", "okkkk"
    words = []
    for w in t.split():
        w = SMS.get(w, w)
        if re.fullmatch(r"[a-z]+", w) and w not in KEEP_DOUBLE:
            w2 = re.sub(r"([a-z])\1", r"\1", w)
            if w2 != w and (w2 in SMS or w2 in _single_words() or w2 in ST_FILLER or w2 in ("you", "so")):
                w = SMS.get(w2, w2)                                    # "hii" -> "hi", "okk" -> "ok"
        words.append(w)
    return re.sub(r"\s+", " ", " ".join(words)).strip()


def _single_words():
    return ST_SINGLE if "ST_SINGLE" in globals() else set()


EMOJI = {"👍": "ok", "👌": "ok", "🙏": "thanks", "😊": "nice", "🙂": "nice", "😀": "nice", "😃": "nice", "😄": "lol",
         "😂": "lol", "🤣": "lol", "❤": "nice", "❤️": "nice", "👏": "nice", "👋": "bye", "😞": "", "😕": ""}


def _rx(phrases):
    alts = sorted({p.strip() for p in phrases if p.strip()}, key=len, reverse=True)
    return re.compile(r"(?<![\wऀ-੿])(" + "|".join(re.escape(p) for p in alts) + r")(?![\wऀ-੿])")


def _split(*groups):
    return [p.strip() for g in groups for p in g.split("|") if p.strip()]


# ================================================================== small talk
# order = priority when several kinds appear ("not good" is feedback, not praise)
SMALLTALK = [
    ("identity", _split(
        "who made you|who built you|who created you|who developed you|who designed you|who are your makers|"
        "what is your name|whats your name|your name|tumhara naam|aapka naam|tera naam|naam kya hai|"
        "are you a robot|are you robot|are you a bot|are you bot|are you human|are you a human|are you real|"
        "are you a person|are you ai|are you an ai|are you chatgpt|are you gemini|you are a robot|you are a bot|"
        "kya tum robot ho|kya aap robot ho|robot ho|insaan ho|kisne banaya|tumhe kisne banaya|aapko kisne banaya|"
        "who built this|who made this|who created this|who made this app|who developed this|who owns this|naam batao|"
        "is this a government site|is this a government website|is it a government site|is this official|is it official|"
        "is this a govt site|is it govt|sarkari site hai|sarkari website hai|kya ye sarkari hai|is this government|"
        "your developers|your developer|your creator|your creators|your team|who developed|who is your developer|"
        "real person|are you real person|are you a real person|human or robot|robot or human|are you a machine|"
        "your name please|name please|what should i call you|what do i call you|what can i call you|call you|"
        "who created this|who created this app|",
        "आपका नाम|तुम्हारा नाम|नाम क्या है|आपको किसने बनाया|तुम्हें किसने बनाया|किसने बनाया|क्या आप रोबोट हैं|रोबोट हो|",
        "ਤੁਹਾਡਾ ਨਾਮ|ਤੁਹਾਨੂੰ ਕਿਸ ਨੇ ਬਣਾਇਆ|ਕਿਸ ਨੇ ਬਣਾਇਆ|ਰੋਬੋਟ ਹੋ|",
        "तुमचे नाव|तुम्हाला कोणी बनवले|कोणी बनवले|रोबोट आहात|",
        "थारो नाम|थानै कुण बणायो|कुण बणायो")),
    ("negative", _split(
        "not good|not helpful|not useful|not working|not correct|not right|no use|useless|wrong|incorrect|"
        "bad answer|bad|worst|stupid|rubbish|nonsense|you are wrong|this is wrong|that is wrong|wrong answer|"
        "galat|galat hai|galat jawab|bakwas|bekar|bekaar|kuch nahi aaya|kaam ka nahi|wrong info|wrong information|"
        "not satisfied|unsatisfied|disappointed|poor answer|not what i asked|confusing answer|answer is useless|"
        "bekar jawab|faltu|faltu jawab|gave wrong answer|wrong answer given|not right|this is not right|"
        "answer galat hai|answer is wrong|",
        "गलत|ग़लत|गलत है|बेकार|बकवास|ठीक नहीं|काम का नहीं|",
        "ਗਲਤ|ਬੇਕਾਰ|ਠੀਕ ਨਹੀਂ|", "चूक|चुकीचे|चुकीचं|बेकार|", "गलत है सा|बेकार है|कोनी ठीक")),
    ("confused", _split(
        "i dont understand|i don t understand|i did not understand|didnt understand|didn t understand|"
        "dont understand|not clear|confusing|confused|what do you mean|what does that mean|i am confused|"
        "did not get|did not get it|i did not get it|not getting it|do not get it|do not understand|i do not understand|"
        "cannot understand|can not understand|unable to understand|kuch samajh nahi aaya|not understanding|"
        "am not understanding|i am not understanding|"
        "samajh nahi aaya|samajh nahi aya|samjha nahi|samjhi nahi|samajh nahi|kuch samajh nahi|",
        "समझ नहीं आया|समझ नहीं|समझा नहीं|कुछ समझ नहीं आया|", "ਸਮਝ ਨਹੀਂ ਆਇਆ|ਸਮਝ ਨਹੀਂ|",
        "समजले नाही|समजलं नाही|कळले नाही|", "समझ कोनी आयो|कोनी समझ्यो")),
    ("how_are_you", _split(
        "how are you|how are you doing|how r u|how are u|how do you do|hows it going|how is it going|whats up|what is up|"
        "wassup|sup|how is your day|haal chaal|kya haal chaal|kaise ho aap|how are things|how is everything|"
        "how have you been|how are you today|how is it going today|"
        "how is the day|how was the day|how was your day|hows your day|how s your day|how is your day going|"
        "how is the day going|how is your day today|how was your day today|how is today|how is life|hows life|"
        "how is your life|how are you doing today|i ask how is your day|i asked how is your day|"
        "i am asking how is your day|i ask how are you|i asked how are you|i am asking how are you|"
        "din kaisa hai|din kaisa raha|aapka din kaisa hai|aapka din kaisa raha|"
        "kaise ho|kaise hain|kaise hai|kaisa hai|kaisi ho|kya haal hai|kya haal|kya hal hai|sab theek|sab badhiya|",
        "कैसे हो|कैसे हैं|क्या हाल है|क्या हाल|सब ठीक|दिन कैसा है|दिन कैसा रहा|आपका दिन कैसा रहा|", "ਕਿਵੇਂ ਹੋ|ਕੀ ਹਾਲ ਹੈ|ਕੀ ਹਾਲ|",
        "कसे आहात|कसा आहेस|काय म्हणता|", "कांई हाल है|कियां हो|कांई हाल")),
    ("thanks", _split(
        "thanks|thank you|thankyou|thank u|thanx|thnx|thx|tnx|ty|many thanks|thanks a lot|much appreciated|tysm|"
        "thank you very much|thanks so much|no thanks|thanku|thank you so much|"
        "shukriya|shukria|dhanyavad|dhanyavaad|dhanyawad|dhanyabad|aabhar|abhar|meherbani|",
        "धन्यवाद|शुक्रिया|आभार|बहुत धन्यवाद|मेहरबानी|", "ਧੰਨਵਾਦ|ਸ਼ੁਕਰੀਆ|ਸ਼ੁਕਰੀਆ|ਮਿਹਰਬਾਨੀ|",
        "आभारी आहे|आभार|धन्यवाद|", "घणो आभार|घणा आभार|आभार सा")),
    ("bye", _split(
        "bye|bye bye|byee|goodbye|good bye|see you|see you later|see ya|take care|good night|gn|tata|cya|"
        "ok bye|talk later|talk to you later|bye for now|catch you later|later|see you soon|see you tomorrow|"
        "good nite|nite|goodnight|"
        "alvida|chalta hoon|chalti hoon|chalo bye|phir milenge|fir milenge|shubh ratri|",
        "अलविदा|फिर मिलेंगे|शुभ रात्रि|चलता हूँ|", "ਅਲਵਿਦਾ|ਫਿਰ ਮਿਲਾਂਗੇ|ਸ਼ੁਭ ਰਾਤ|",
        "पुन्हा भेटू|निरोप|शुभ रात्री|", "फेर मिलांला|राम राम सा")),
    ("greet_time", _split(
        "good morning|good afternoon|good evening|gm|morning|suprabhat|shubh prabhat|",
        "सुप्रभात|शुभ प्रभात|नमस्कार जी|", "ਸ਼ੁਭ ਸਵੇਰ|", "शुभ सकाळ|", "खम्मा घणी सा")),
    ("greet", _split("hi|hello|hey|hey there|hello there|hi there|hola|namaste|namaskar|ram ram|salaam|sat sri akal|"
                     "नमस्ते|नमस्कार|राम राम|ਸਤ ਸ੍ਰੀ ਅਕਾਲ|खम्मा घणी")),
    ("praise", _split(
        "nice|very nice|good|very good|great|awesome|amazing|excellent|superb|super|perfect|wonderful|fantastic|"
        "brilliant|wow|cool|good job|well done|helpful|very helpful|useful|love it|i like it|i love it|like it|"
        "nice one|good one|great job|great work|nice work|good work|impressive|interesting|kya baat hai|kya baat|"
        "maza aa gaya|mazaa aa gaya|lovely|beautiful|outstanding|terrific|fabulous|marvellous|"
        "marvelous|splendid|incredible|neat|sweet|informative|very informative|great help|nice info|too good|"
        "very useful|ekdum badhiya|bohot accha|bohot badhiya|"
        "badhiya|badiya|bdiya|mast|zabardast|shandar|shaandar|wah|waah|kamaal|kamal|bahut accha|bahut acha|sahi hai|",
        "बढ़िया|बहुत बढ़िया|बहुत अच्छा|शानदार|वाह|कमाल|ज़बरदस्त|जबरदस्त|सही है|",
        "ਵਧੀਆ|ਬਹੁਤ ਵਧੀਆ|ਸ਼ਾਨਦਾਰ|ਵਾਹ|ਕਮਾਲ|", "छान|खूप छान|मस्त|भारी|सुंदर|", "चोखो|घणो चोखो|जोरदार|फूटरो")),
    ("laugh", _split("lol|haha|hahaha|hehe|lmao|😂")),
    ("ack", _split(
        "ok|okay|okk|okey|k|kk|fine|alright|all right|sure|got it|understood|noted|hmm|hm|hmmm|yes|yeah|yep|ya|"
        "no|nope|nah|achha|accha|acha|theek hai|thik hai|theek|thik|haan|han|haa|ji|ji haan|ok ji|yes please|"
        "ok thanks|okay thanks|ok fine|alright then|sure thing|nahi|nahin|na|ohk|okh|"
        "fine thanks|ok cool|okay cool|right|correct|exactly|true|agreed|done|ok ok|okay okay|",
        "ठीक है|ठीक|अच्छा|हाँ|हां|जी|जी हाँ|नहीं|", "ਠੀਕ ਹੈ|ਠੀਕ|ਹਾਂ|ਜੀ|ਨਹੀਂ|",
        "ठीक आहे|बरं|हो|हो ना|नाही|", "ठीक है सा|हां सा|ना")),
]
SMALLTALK_RX = [(kind, _rx(words)) for kind, words in SMALLTALK]
ST_SINGLE = {w for _k, ws in SMALLTALK for w in ws if " " not in w and re.fullmatch(r"[a-z]+", w)}


def _edit1(a, b):
    """True when a and b differ by at most one insertion, deletion or substitution."""
    if abs(len(a) - len(b)) > 1:
        return False
    if len(a) > len(b):
        a, b = b, a
    i = j = diff = 0
    while i < len(a) and j < len(b):
        if a[i] != b[j]:
            diff += 1
            if diff > 1:
                return False
            if len(a) == len(b):
                i += 1
            j += 1
        else:
            i += 1
            j += 1
    return diff + (len(b) - j) <= 1


def _repair(t):
    """'awsome' -> 'awesome', 'thnaks' -> 'thanks' (Latin words of 5+ letters, one typo, one candidate)."""
    out = []
    for w in t.split():
        if len(w) >= 5 and re.fullmatch(r"[a-z]+", w) and w not in ST_SINGLE and w not in ST_FILLER:
            near = [v for v in ST_SINGLE if len(v) >= 5 and _edit1(w, v)]
            if len(near) == 1:
                w = near[0]
        out.append(w)
    return " ".join(out)
# words that may surround small talk: "thanks a lot jalmitra", "nice bro", "bahut bahut dhanyavaad ji"
ST_FILLER = set(("very so much too really a lot lots alot bro brother bhai bhaiya dost yaar friend sir madam mam "
                 "aap tum tu you kya hai hain ho is what please info information jawab answer reply then there "
                 "app website site bot chatbot tool stuff kaam ekdum today now tonight tomorrow again gave give "
                 "giving me am i one काम बहुत "
                 "who are ton tons for now job work kuch bhi jankari jaankari jaankaari details guidance thing jee "
                 "जानकारी जवाब "
                 "ji sa jalmitra jal mitra buddy dear man again for the help your answer that this it is was you "
                 "bahut bohot bahot hi bilkul aapka aapko tumhara and also too sab kuch ji "
                 "बहुत बहुत जी भाई दोस्त आपका आपको सर ਬਹੁਤ ਜੀ ਭਾਈ ਵੀਰ खूप जी सा घणो").split())


HINGLISH_WORDS = set(("shukriya shukria dhanyavad dhanyavaad dhanyawad dhanyabad accha acha achha badhiya badiya bdiya "
                      "alvida theek thik haan kaise kaisa kaisi haal mast zabardast shandar shaandar wah waah kamaal "
                      "bakwas bekar bekaar galat samajh samjha samjhi milenge chalta chalti bhai yaar kisne banaya naam "
                      "tumhara aapka bahut bohot nahi aaya ho hai").split())


LANG_HINTS = {"mr": set("छान खूप मस्त भारी बरं आभारी आहे नाही निरोप भेटू पुन्हा काय कसे सकाळ रात्री".split()),
              "raj": set("घणो घणा चोखो जोरदार फूटरो सा थारो थे म्हैं कोनी कांई कियां खम्मा".split())}


def lang_hint(question):
    """Marathi or Rajasthani small talk written in Devanagari ("छान", "घणो चोखो") -> that language, else None."""
    words = set(_norm(question).split())
    for code in ("raj", "mr"):
        if words & LANG_HINTS[code]:
            return code
    return None


def is_hinglish(question):
    """Latin-script small talk with Hindi words ("shukriya", "badhiya bhai") -> answer in Hinglish."""
    return any(w in HINGLISH_WORDS for w in _norm(question).split())


def smalltalk(question):
    """Kind of small talk, or None. The whole message must be small talk (plus filler words)."""
    t = _repair(_norm(question))
    if not t or len(t.split()) > 9:
        return None
    if t in ("what", "huh", "eh", "kya", "matlab", "kya matlab", "क्या", "मतलब", "ਕੀ"):
        return "confused"
    t = " ".join("thanks" if re.match(r"(thank|appreciat|grateful|shukri|dhanyav|dhanyaw|dhanyab)", w) else w
                 for w in t.split())
    found, rest = [], t
    for kind, rx in SMALLTALK_RX:
        if rx.search(rest):
            found.append(kind)
            rest = rx.sub(" ", rest)
    if not found:
        return None
    if any(w not in ST_FILLER for w in rest.split()):
        return None
    if found[0] in ("ack", "praise") and set(rest.split()) & {"what", "who", "how", "why", "which", "kya", "kaun",
                                                          "kaise", "क्या", "कौन", "कैसे", "ਕੀ", "काय", "कांई"}:
        return None          # "what is jalmitra exactly" is a question, not "exactly"
    return found[0]


# ================================================================== topics (scope questions and fallback cues)
TOPICS = [   # in scope
    ("water_quality", _split(
        "water quality|drinking water|water test|water testing|test my water|tds|fluoride|nitrate|arsenic|"
        "hardness|salty water|khara pani|khara paani|peene ka paani|peene ka pani|pine ka pani|paani ki quality|"
        "pani ki quality|paani ki jaanch|pani ki jaanch|water report|water sample|",
        "पानी की गुणवत्ता|पीने का पानी|पानी की जांच|पानी की जाँच|फ्लोराइड|खारा पानी|",
        "ਪਾਣੀ ਦੀ ਗੁਣਵੱਤਾ|ਪੀਣ ਵਾਲਾ ਪਾਣੀ|", "पाण्याची गुणवत्ता|पिण्याचे पाणी|", "पाणी री गुणवत्ता|पीवण रो पाणी")),
    ("fertilizer", _split("fertilizer|fertiliser|fertilizers|khad|khaad|urea|dap|npk|manure|",
                          "खाद|उर्वरक|यूरिया|", "ਖਾਦ|ਯੂਰੀਆ|", "खत|", "खाद")),
    ("soil", _split(
        "soil|soil test|soil testing|soil health|soil health card|soil card|soil report|mitti|mitti ki jaanch|",
        "मिट्टी|मृदा|मृदा स्वास्थ्य कार्ड|", "ਮਿੱਟੀ|", "माती|मृदा|", "माटी")),
    ("irrigation", _split(
        "irrigation|drip|sprinkler|watering|water saving|save water|saving water|rainwater|rain water harvesting|"
        "rainwater harvesting|farm pond|recharge pit|sinchai|sichai|paani bachaye|pani bachaye|paani bachana|"
        "pani bachana|paani ki bachat|",
        "सिंचाई|ड्रिप|पानी बचाना|पानी की बचत|वर्षा जल|", "ਸਿੰਚਾਈ|ਪਾਣੀ ਦੀ ਬੱਚਤ|", "सिंचन|पाणी बचत|", "सिंचाई|पाणी बचावणो")),
    ("groundwater", _split(
        "groundwater|ground water|water level|water table|borewell|bore well|tubewell|tube well|well|wells|aquifer|"
        "bhujal|jal star|paani ka star|pani ka star|water|paani|pani|",
        "भूजल|भू जल|जल स्तर|जलस्तर|बोरवेल|कुआं|कुआँ|पानी|", "ਧਰਤੀ ਹੇਠਲਾ ਪਾਣੀ|ਪਾਣੀ ਦਾ ਪੱਧਰ|ਪਾਣੀ|ਬੋਰ|",
        "भूजल|पाणी पातळी|पाणी|विहीर|", "भूजल|पाणी|कुओ")),
    ("crops", _split(
        "crop|crops|which crop|what to grow|grow|growing|sowing|cultivation|harvest|fasal|fasal kaun si|kheti|",
        "फसल|फसलें|खेती|बुवाई|", "ਫ਼ਸਲ|ਫਸਲ|ਖੇਤੀ|", "पीक|पिके|शेती|", "फसल|खेती")),
    ("farming", _split("farming|agriculture|farmer|farmers|kisan|kisaan|kisano|kisaano|kisanon|krishi|"
                       "students|student|officials|officers|researchers|teachers|everyone|public|common people|", "किसान|कृषि|किसानों|",
                       "ਕਿਸਾਨ|ਖੇਤੀਬਾੜੀ|", "शेतकरी|कृषी|", "करसाण")),
    ("land", _split("land|land record|land condition|land degradation|erosion|wasteland|zameen|jameen|bhoomi|",
                    "भूमि|ज़मीन|जमीन|भूमि क्षरण|", "ਜ਼ਮੀਨ|", "जमीन|", "जमीन")),
    ("reports", _split("report|reports|pdf|download|", "रिपोर्ट|", "ਰਿਪੋਰਟ|", "अहवाल|", "रिपोर्ट")),
    ("languages", _split("hindi|english|punjabi|marathi|rajasthani|hinglish|language|languages|bhasha|",
                         "भाषा|हिंदी|", "ਭਾਸ਼ਾ|ਪੰਜਾਬੀ|", "भाषा|मराठी|", "भासा")),
]
OUT_OF_SCOPE = [
    ("prices", _split(
        "price|prices|mandi rate|mandi rates|mandi bhav|mandi price|market rate|market rates|market price|bhav|"
        "bhaav|daam|kimat|keemat|msp|selling price|rate of|rates of|ka rate|ka bhav|ka daam|rate|rates|rate today|"
        "today rate|aaj ka rate|aaj ka bhav|",
        "भाव|दाम|कीमत|मंडी भाव|मंडी रेट|बाजार भाव|", "ਭਾਅ|ਕੀਮਤ|ਮੰਡੀ|", "भाव|किंमत|बाजारभाव|", "भाव|मोल")),
    ("money", _split(
        "money|paisa|paise|earn|earning|earnings|income|make money|grow money|profit|profits|loan|loans|"
        "become rich|get rich|be rich|ameer|amir banna|"
        "karz|karza|kcc|kisan credit card|credit card|bank loan|bank account|insurance|bima|fasal bima|subsidy|subsidies|scheme|"
        "schemes|yojana|yojna|pm kisan|kisan samman|samman nidhi|installment|instalment|kist|kisht|"
        "invest|investment|share market|stock market|stocks|shares|bitcoin|crypto|lottery|salary|job|jobs|naukri|",
        "पैसा|पैसे|कमाई|आमदनी|मुनाफा|लोन|कर्ज|कर्ज़|बैंक|बीमा|सब्सिडी|योजना|किस्त|नौकरी|",
        "ਪੈਸਾ|ਪੈਸੇ|ਕਮਾਈ|ਕਰਜ਼ਾ|ਬੈਂਕ|ਬੀਮਾ|ਸਬਸਿਡੀ|ਯੋਜਨਾ|", "पैसा|पैसे|कर्ज|बँक|विमा|अनुदान|योजना|",
        "पइसा|रिपिया|करजो|बैंक|योजना")),
    ("weather", _split(
        "weather|forecast|weather forecast|temperature|will it rain|is it going to rain|rain tomorrow|rain today|"
        "rain forecast|when will it rain|monsoon forecast|storm|cyclone|hailstorm|heatwave|heat wave|cold wave|"
        "mausam|mosam|barish kab|baarish kab|kal barish|barish hogi|baarish hogi|aaj barish|barish|baarish|rain|rains|"
        "raining|rainfall forecast|be rain|monsoon kab|monsoon when|when will monsoon|monsoon arrive|monsoon aayega|",
        "मौसम|बारिश कब|बारिश होगी|आज बारिश|कल बारिश|तापमान|", "ਮੌਸਮ|ਮੀਂਹ ਕਦੋਂ|ਮੀਂਹ ਪਵੇਗਾ|",
        "हवामान|पाऊस कधी|पाऊस येईल|", "मौसम|मेह कद|बिरखा कद")),
    ("shop", _split(
        "sell|sells|selling|buy|buying|purchase|order|orders|shop|shopping|online shopping|delivery|book|booking|"
        "rent|hire|kharidna|kharide|bechna|beche|kiraye|",
        "खरीद|बेच|किराये|बुकिंग|", "ਖਰੀਦ|ਵੇਚ|", "खरेदी|विक्री|", "खरीद|बेच")),
    ("pests", _split(
        "pest|pests|insect|insects|keeda|keede|keet|disease|diseases|plant disease|crop disease|fungus|"
        "pesticide|pesticides|insecticide|locust|termite|deemak|",
        "कीड़ा|कीड़े|कीट|रोग|बीमारी|कीटनाशक|दीमक|टिड्डी|", "ਕੀੜੇ|ਕੀੜਾ|ਬਿਮਾਰੀ|ਸਪਰੇ|",
        "कीड|रोग|कीटकनाशक|", "कीड़ा|रोग")),
    ("livestock", _split(
        "cow|cows|buffalo|buffaloes|cattle|goat|goats|sheep|camel|poultry|chicken|dairy|milk|fishery|fish farming|"
        "gaay|gai|bhains|bakri|pashu|",
        "गाय|भैंस|बकरी|पशु|दूध|डेयरी|मुर्गी|", "ਗਾਂ|ਮੱਝ|ਪਸ਼ੂ|ਦੁੱਧ|", "गाय|म्हैस|पशु|दूध|", "गाय|भैंस|ऊंट")),
    ("general", _split(
        "cricket|football|ipl|cricket match|movie|movies|film|films|song|songs|music|joke|jokes|recipe|recipes|cook|cooking|"
        "tea|coffee|politics|election|elections|news|capital of|president|prime minister|chief minister|"
        "girlfriend|boyfriend|love story|horoscope|astrology|game|games|exam result|",
        "क्रिकेट|फिल्म|गाना|चुटकुला|राजनीति|चुनाव|खबर|", "ਕ੍ਰਿਕਟ|ਫ਼ਿਲਮ|ਗੀਤ|ਚੁਟਕਲਾ|",
        "क्रिकेट|चित्रपट|गाणे|विनोद|", "क्रिकेट|फिलम|गीत")),
]
TOPIC_RX = [(k, _rx(w)) for k, w in TOPICS]
OOS_RX = [(k, _rx(w)) for k, w in OUT_OF_SCOPE]
# data words that keep a question in the pipeline even next to an out-of-scope word ("rainfall recharge")
DATA_RX = _rx(_split("stage of extraction|extraction|recharge|over exploited|over-exploited|semi critical|"
                     "critical|safe|saline|category|block|blocks|district|tehsil|ec|ph|"
                     "दोहन|पुनर्भरण|अतिदोहित|ब्लॉक|जिला|ज़िला"))


TOPIC_SINGLE = [(k, w) for k, ws in TOPICS for w in ws if " " not in w and re.fullmatch(r"[a-z]{4,}", w)]


def topics_in(text):
    t = _norm(text)
    found = [k for k, rx in TOPIC_RX if rx.search(t)]
    for tok in t.split():                       # "kisano" -> kisan, "irrigations" -> irrigation
        if len(tok) >= 5 and re.fullmatch(r"[a-z]+", tok):
            for k, w in TOPIC_SINGLE:
                if k not in found and tok != w and tok.startswith(w) and len(tok) - len(w) <= 3:
                    found.append(k)
    order = [k for k, _ in TOPICS]
    return sorted(found, key=order.index)


OOS_SINGLE = {k: [w for w in ws if " " not in w and re.fullmatch(r"[a-z]{4,}", w)] for k, ws in OUT_OF_SCOPE}


def _prefix_hit(t, kind):
    """'termites' -> termite, 'loaners' -> loan (Latin words, up to 3 extra letters)."""
    for tok in t.split():
        if len(tok) >= 5 and re.fullmatch(r"[a-z]+", tok):
            for w in OOS_SINGLE.get(kind, ()):
                if tok != w and tok.startswith(w) and len(tok) - len(w) <= 3 and w not in ("rate", "bank", "book"):
                    return True
    return False


def out_of_scope(text):
    """Out-of-scope subject (money, prices, weather, pests, livestock, general) or None."""
    t = _norm(text)
    tops = None
    for kind, rx in OOS_RX:
        if rx.search(t) or _prefix_hit(t, kind):
            tops = topics_in(t) if tops is None else tops
            if DATA_RX.search(t):
                if kind != "money" or "groundwater" in tops:
                    return None      # "rainfall recharge", "rate of extraction" stay data questions
            if kind == "general" and tops:
                return None          # "news about groundwater"
            if kind == "pests" and "water_quality" in tops:
                return None          # "does fluoride cause disease"
            if kind == "weather" and set(tops) & {"irrigation", "groundwater", "water_quality", "soil"}:
                return None          # "rain water harvesting", "barish ka paani recharge"
            if kind == "prices" and set(tops) & {"irrigation", "groundwater", "water_quality", "soil"} \
                    and not re.search(r"price|bhav|bhaav|daam|kimat|keemat|mandi|msp|भाव|दाम|कीमत", t):
                return None          # "application rate of drip", "infiltration rate of soil"
            return kind
    return None


# ================================================================== yes/no scope questions
# "is this site about X", "does it cover X", "do you give X", "can I check X here", "kya isme X milega"
ADDR = r"(this|it|jalmitra|jal mitra|you|u|this site|this website|this app|this application|the app|the site|" \
       r"the website|this portal|this platform|this chatbot|this bot|this tool|this project)"
SCOPE_RX = [re.compile(p) for p in (
    r"^(is|are|was) " + ADDR + r" (is |are )?(only |just |also |really |mainly )?(about|for|related to|meant for|"
    r"used for|useful for|made for|a site for|an app for|a website for|helpful for|good for|able to|going to)\b(?P<x>.*)",
    r"^(does|do|will|can|could) " + ADDR + r" (also |really )?(cover|covers|tell|give|show|have|has|support|provide|"
    r"offer|include|know|know about|deal with|handle|help with|help me with|help in|help|explain|predict|"
    r"calculate|answer|check|do|talk about|work for|work with|tell me about|give me|show me)\b(?P<x>.*)",
    r"^(can|could|may) (i|we) (check|get|see|find|know|learn|ask|ask about|use (it|this|jalmitra) for|"
    r"find out|look up|upload|download|enter|compare|test|save|print|read|share)\b(?P<x>.*?)"
    r"( here| on this| on this site| in this app| from you| with this| on jalmitra)?$",
    r"^(kya )?(ye|yeh|is|isme|ismein|iss|aap|tum|jalmitra) (site |app |website )?(se |par |mein |me )?"
    r"(?P<x>.*?) (ke bare|ke baare|ke liye|bata|batata|batati|batate|milega|milegi|milta|milti|dikhata|"
    r"deta|deti|dete|hai kya|ho sakta|jankari|jaankari|jaankaari|info|information)(?=\s|$).*",
    r"^(क्या )?(यह|ये|इस|इसमें|आप|तुम|जलमित्र) (वेबसाइट |साइट |ऐप )?(से |पर |में )?(?P<x>.*?) "
    r"(के बारे|के लिए|बता|बताता|बताती|बताते|मिलेगा|मिलेगी|मिलता|देता|देती|देते)(?=\s|$).*",
    r"^(is|are|can i use) (?P<x>(hindi|english|punjabi|marathi|rajasthani|hinglish|gujarati|tamil|telugu|bengali|"
    r"kannada|malayalam|odia|urdu|bhojpuri)( language)?) (available|supported|there|possible|allowed)(?P<y>.*)$",
    r"^(is|are) (this|it|jalmitra|jal mitra) (a|an|some|some kind of|kind of) (?P<x>.+?)"
    r"( site| website| app| application| portal| platform| tool| chatbot| bot)?$",
    r"^(ਕੀ )?(ਇਹ|ਇਸ|ਤੁਸੀਂ) (ਵੈੱਬਸਾਈਟ |ਸਾਈਟ |ਐਪ )?(?P<x>.*?) (ਬਾਰੇ|ਲਈ|ਦੱਸ\S*|ਮਿਲ\S*)(?=\s|$).*",
    r"^(ही|हे|या|तुम्ही) (वेबसाइट |साइट |ॲप )?(?P<x>.*?) (बद्दल|साठी|सांग\S*|मिळ\S*)(?=\s|$).*",
    r"^(कांई )?(आ|इण|थे) (वेबसाइट |साइट )?(?P<x>.*?) (रै बारै|सारू|बता\S*|मिलै)(?=\s|$).*",
)]


def scope_question(question):
    """For a yes/no question about what JalMitra covers, return the asked-about text X; else None."""
    t = _norm(question)
    for rx in SCOPE_RX:
        m = rx.match(t)
        if m:
            x = (m.group("x") or "").strip()
            x = re.sub(r"^(how to|how do i|how can i|the|a|an|my|any|info on|information on|information about|"
                       r"data on|data about|about|on|with|for|me|to)\s+", "", x).strip()
            x = re.sub(r"^(how to|the|a|an|my|any|about)\s+", "", x).strip()
            if not x or all(w in QWORDS for w in x.split()):
                return None          # "is this for what?" is a question about the app, not a yes/no scope question
            return x
    return None


QWORDS = set("what which who whom how why kya kaun kaunsa kis kiske kya kya kuch something anything this that it "
             "here there all everything क्या कौन किस कुछ ਕੀ ਕਿਸ काय कोण कांई कुण".split())


def classify_scope(x):
    """('no', oos) / ('yes', topic) / ('partly', 'fertilizer') / None (unknown -> decided by the parser)."""
    oos = out_of_scope(x)
    if oos:
        return ("no", oos)
    if re.search(r"(gujarati|tamil|telugu|bengali|bangla|kannada|malayalam|odia|oriya|urdu|bhojpuri|assamese)", x):
        return ("no", "languages")
    tops = topics_in(x)
    if "fertilizer" in tops:
        return ("partly", "fertilizer")
    if tops:
        return ("yes", tops[0])
    return None


# ================================================================== reply texts
def V(**langs):
    """One reply key: {lang: [variants]}"""
    return {k: (v if isinstance(v, list) else [v]) for k, v in langs.items()}


COVERS = V(
    en="JalMitra covers groundwater, soil, water quality, crops, irrigation and land information.",
    hi="JalMitra भूजल, मिट्टी, पानी की गुणवत्ता, फसल, सिंचाई और भूमि की जानकारी देता है।",
    hinglish="JalMitra groundwater, mitti, paani ki quality, fasal, sinchai aur zameen ki jaankari deta hai.",
    mr="JalMitra भूजल, माती, पाण्याची गुणवत्ता, पिके, सिंचन आणि जमिनीची माहिती देतो.",
    pa="JalMitra ਧਰਤੀ ਹੇਠਲੇ ਪਾਣੀ, ਮਿੱਟੀ, ਪਾਣੀ ਦੀ ਗੁਣਵੱਤਾ, ਫ਼ਸਲਾਂ, ਸਿੰਚਾਈ ਅਤੇ ਜ਼ਮੀਨ ਦੀ ਜਾਣਕਾਰੀ ਦਿੰਦਾ ਹੈ।",
    raj="JalMitra भूजल, माटी, पाणी री गुणवत्ता, फसल, सिंचाई अर जमीन री जाणकारी देवै।",
)

TEXT = {
    # ------------------------------------------------------------ small talk
    "st_thanks": V(
        en=["You're welcome! Ask me anything else about water, soil, crops or land.",
            "Glad I could help. Is there anything else you'd like to check?",
            "Happy to help! You can ask another question whenever you like."],
        hi=["आपका स्वागत है! पानी, मिट्टी, फसल या ज़मीन के बारे में और कुछ पूछिए।",
            "मदद करके खुशी हुई। क्या आप कुछ और देखना चाहेंगे?",
            "खुशी हुई! जब चाहें, अगला सवाल पूछिए।"],
        hinglish=["Aapka swagat hai! Paani, mitti, fasal ya zameen ke baare mein aur kuch poochiye.",
                  "Madad karke khushi hui. Kuch aur dekhna chahenge?",
                  "Khushi hui! Jab chahein, agla sawal poochiye."],
        mr=["तुमचे स्वागत आहे! पाणी, माती, पिके किंवा जमिनीबद्दल आणखी काही विचारा.",
            "मदत करून आनंद झाला. आणखी काही पाहायचे आहे का?"],
        pa=["ਤੁਹਾਡਾ ਸਵਾਗਤ ਹੈ! ਪਾਣੀ, ਮਿੱਟੀ, ਫ਼ਸਲ ਜਾਂ ਜ਼ਮੀਨ ਬਾਰੇ ਹੋਰ ਕੁਝ ਪੁੱਛੋ।",
            "ਮਦਦ ਕਰਕੇ ਖੁਸ਼ੀ ਹੋਈ। ਕੀ ਤੁਸੀਂ ਹੋਰ ਕੁਝ ਵੇਖਣਾ ਚਾਹੋਗੇ?"],
        raj=["पधारो सा! पाणी, माटी, फसल या जमीन रै बारै में और कीं पूछो।",
             "मदद कर नै घणी खुसी होई। और कीं देखणो है कांई?"]),
    "st_praise": V(
        en=["Thank you! What would you like to look at next?",
            "Glad it was useful. Ask me another question any time.",
            "Thanks! I can also explain soil reports, water tests and crop water needs."],
        hi=["धन्यवाद! अब आप क्या देखना चाहेंगे?", "खुशी है कि यह काम आया। कभी भी अगला सवाल पूछिए।",
            "धन्यवाद! मैं मिट्टी की रिपोर्ट, पानी की जाँच और फसलों की पानी की ज़रूरत भी समझा सकता हूँ।"],
        hinglish=["Dhanyavaad! Ab aap kya dekhna chahenge?", "Khushi hai ki yeh kaam aaya. Kabhi bhi agla sawal poochiye.",
                  "Shukriya! Main soil report, paani ki jaanch aur fasal ki paani ki zaroorat bhi samjha sakta hoon."],
        mr=["धन्यवाद! पुढे काय पाहायचे आहे?", "उपयोगी पडले याचा आनंद आहे. कधीही पुढचा प्रश्न विचारा."],
        pa=["ਧੰਨਵਾਦ! ਹੁਣ ਤੁਸੀਂ ਕੀ ਵੇਖਣਾ ਚਾਹੋਗੇ?", "ਖੁਸ਼ੀ ਹੈ ਕਿ ਇਹ ਕੰਮ ਆਇਆ। ਕਦੇ ਵੀ ਅਗਲਾ ਸਵਾਲ ਪੁੱਛੋ।"],
        raj=["घणो आभार सा! अबै कांई देखणो है?", "खुसी है कै ओ काम आयो। कदेई भी अगलो सवाल पूछो।"]),
    "st_ack": V(
        en=["Okay. What would you like to know?", "Alright. Ask me about groundwater, soil, water quality, crops or land.",
            "Sure. I'm ready for your next question."],
        hi=["ठीक है। आप क्या जानना चाहेंगे?", "अच्छा। भूजल, मिट्टी, पानी की गुणवत्ता, फसल या ज़मीन के बारे में पूछिए।",
            "ज़रूर। अगला सवाल पूछिए।"],
        hinglish=["Theek hai. Aap kya jaanna chahenge?",
                  "Achha. Groundwater, mitti, paani ki quality, fasal ya zameen ke baare mein poochiye.",
                  "Zaroor. Agla sawal poochiye."],
        mr=["ठीक आहे. तुम्हाला काय जाणून घ्यायचे आहे?", "बरं. भूजल, माती, पाणी, पिके किंवा जमिनीबद्दल विचारा."],
        pa=["ਠੀਕ ਹੈ। ਤੁਸੀਂ ਕੀ ਜਾਣਨਾ ਚਾਹੋਗੇ?", "ਅੱਛਾ। ਪਾਣੀ, ਮਿੱਟੀ, ਫ਼ਸਲ ਜਾਂ ਜ਼ਮੀਨ ਬਾਰੇ ਪੁੱਛੋ।"],
        raj=["ठीक है सा। थे कांई जाणणो चावो?", "आछो। भूजल, माटी, फसल या जमीन रै बारै में पूछो।"]),
    "st_bye": V(
        en=["Goodbye! Come back any time you have a question about water, soil or crops.",
            "Take care! JalMitra will be here when you need it.", "Bye! Wishing you a good season."],
        hi=["अलविदा! पानी, मिट्टी या फसल के बारे में सवाल हो तो फिर आइए।", "अपना ध्यान रखिए! ज़रूरत हो तो JalMitra यहीं है।",
            "नमस्ते! आपका मौसम अच्छा रहे।"],
        hinglish=["Alvida! Paani, mitti ya fasal ke baare mein sawal ho to phir aaiye.",
                  "Apna dhyan rakhiye! Zaroorat ho to JalMitra yahin hai.", "Bye! Aapki fasal achhi ho."],
        mr=["निरोप! पाणी, माती किंवा पिकांबद्दल प्रश्न असल्यास पुन्हा या.", "काळजी घ्या! गरज असेल तेव्हा JalMitra इथेच आहे."],
        pa=["ਅਲਵਿਦਾ! ਪਾਣੀ, ਮਿੱਟੀ ਜਾਂ ਫ਼ਸਲ ਬਾਰੇ ਸਵਾਲ ਹੋਵੇ ਤਾਂ ਫਿਰ ਆਓ।", "ਆਪਣਾ ਧਿਆਨ ਰੱਖੋ! ਲੋੜ ਹੋਵੇ ਤਾਂ JalMitra ਇੱਥੇ ਹੀ ਹੈ।"],
        raj=["राम राम सा! पाणी, माटी या फसल रो सवाल हुवै तो फेर पधारजो।", "ध्यान राखजो सा! जरूरत हुवै तो JalMitra अठै ही है।"]),
    "st_greet_time": V(
        en=["Good day to you too! Ask me about groundwater, soil, water quality, crops or land.",
            "Hello! What would you like to check today?"],
        hi=["आपको भी नमस्कार! भूजल, मिट्टी, पानी की गुणवत्ता, फसल या ज़मीन के बारे में पूछिए।", "नमस्ते! आज आप क्या देखना चाहेंगे?"],
        hinglish=["Aapko bhi namaskar! Groundwater, mitti, paani ki quality, fasal ya zameen ke baare mein poochiye.",
                  "Namaste! Aaj aap kya dekhna chahenge?"],
        mr=["तुम्हालाही नमस्कार! भूजल, माती, पाणी, पिके किंवा जमिनीबद्दल विचारा.", "नमस्कार! आज काय पाहायचे आहे?"],
        pa=["ਤੁਹਾਨੂੰ ਵੀ ਸਤ ਸ੍ਰੀ ਅਕਾਲ! ਪਾਣੀ, ਮਿੱਟੀ, ਫ਼ਸਲ ਜਾਂ ਜ਼ਮੀਨ ਬਾਰੇ ਪੁੱਛੋ।", "ਸਤ ਸ੍ਰੀ ਅਕਾਲ! ਅੱਜ ਕੀ ਵੇਖਣਾ ਹੈ?"],
        raj=["खम्मा घणी सा! भूजल, माटी, फसल या जमीन रै बारै में पूछो।", "राम राम सा! आज कांई देखणो है?"]),
    "st_how_are_you": V(
        en=["I'm a computer program, so I'm always ready! How can I help you today?",
            "All good here, thank you. What would you like to check?"],
        hi=["मैं एक कंप्यूटर प्रोग्राम हूँ, इसलिए हमेशा तैयार हूँ! आज मैं आपकी क्या मदद करूँ?", "सब ठीक है, धन्यवाद। आप क्या देखना चाहेंगे?"],
        hinglish=["Main ek computer program hoon, isliye hamesha taiyaar hoon! Aaj main aapki kya madad karoon?",
                  "Sab theek hai, shukriya. Aap kya dekhna chahenge?"],
        mr=["मी एक संगणक प्रोग्राम आहे, त्यामुळे नेहमी तयार आहे! आज काय मदत करू?", "सगळं ठीक आहे, धन्यवाद. काय पाहायचे आहे?"],
        pa=["ਮੈਂ ਇੱਕ ਕੰਪਿਊਟਰ ਪ੍ਰੋਗਰਾਮ ਹਾਂ, ਇਸ ਲਈ ਹਮੇਸ਼ਾ ਤਿਆਰ ਹਾਂ! ਅੱਜ ਕੀ ਮਦਦ ਕਰਾਂ?", "ਸਭ ਠੀਕ ਹੈ, ਧੰਨਵਾਦ। ਕੀ ਵੇਖਣਾ ਹੈ?"],
        raj=["म्हैं एक कंप्यूटर प्रोग्राम हूं, सो सदा तैयार हूं! आज कांई मदद करूं?", "सब ठीक है सा, आभार। कांई देखणो है?"]),
    "st_identity": V(
        en="I'm JalMitra, a computer program, not a person. I work from fixed rules and the official datasets stored "
           "with this app, on this computer. I don't use ChatGPT, Gemini or any online AI. JalMitra was built for "
           "Smart India Hackathon problem statement SIH25066 (Ministry of Jal Shakti). It is not an official government "
           "website; it uses published government data.",
        hi="मैं JalMitra हूँ, एक कंप्यूटर प्रोग्राम, कोई इंसान नहीं। मैं तय नियमों और इस ऐप में रखे आधिकारिक डेटासेट से, इसी "
           "कंप्यूटर पर काम करता हूँ। मैं ChatGPT, Gemini या कोई ऑनलाइन AI इस्तेमाल नहीं करता। JalMitra को स्मार्ट इंडिया "
           "हैकथॉन की समस्या SIH25066 (जल शक्ति मंत्रालय) के लिए बनाया गया है। यह कोई आधिकारिक सरकारी वेबसाइट नहीं है; यह प्रकाशित "
           "सरकारी डेटा का उपयोग करता है।",
        hinglish="Main JalMitra hoon, ek computer program, koi insaan nahi. Main fixed rules aur is app mein rakhe "
                 "official datasets se, isi computer par kaam karta hoon. Main ChatGPT, Gemini ya koi online AI use nahi "
                 "karta. JalMitra Smart India Hackathon problem SIH25066 (Jal Shakti Mantralaya) ke liye banaya gaya hai. Yeh koi "
                 "official sarkari website nahi hai; yeh published sarkari data use karta hai.",
        mr="मी JalMitra आहे, एक संगणक प्रोग्राम, माणूस नाही. मी ठरलेल्या नियमांवर आणि या ॲपमधील अधिकृत डेटासेटवर, याच संगणकावर "
           "काम करतो. मी ChatGPT, Gemini किंवा कोणतीही ऑनलाइन AI वापरत नाही. JalMitra स्मार्ट इंडिया हॅकॅथॉनच्या SIH25066 "
           "(जलशक्ती मंत्रालय) समस्येसाठी बनवले आहे. ही अधिकृत सरकारी वेबसाइट नाही; ती प्रकाशित सरकारी डेटा वापरते.",
        pa="ਮੈਂ JalMitra ਹਾਂ, ਇੱਕ ਕੰਪਿਊਟਰ ਪ੍ਰੋਗਰਾਮ, ਕੋਈ ਇਨਸਾਨ ਨਹੀਂ। ਮੈਂ ਤੈਅ ਨਿਯਮਾਂ ਅਤੇ ਇਸ ਐਪ ਦੇ ਸਰਕਾਰੀ ਡਾਟਾਸੈੱਟਾਂ ਨਾਲ, "
           "ਇਸੇ ਕੰਪਿਊਟਰ 'ਤੇ ਕੰਮ ਕਰਦਾ ਹਾਂ। ਮੈਂ ChatGPT, Gemini ਜਾਂ ਕੋਈ ਔਨਲਾਈਨ AI ਨਹੀਂ ਵਰਤਦਾ। JalMitra ਸਮਾਰਟ ਇੰਡੀਆ "
           "ਹੈਕਾਥਨ ਦੀ ਸਮੱਸਿਆ SIH25066 (ਜਲ ਸ਼ਕਤੀ ਮੰਤਰਾਲਾ) ਲਈ ਬਣਾਇਆ ਗਿਆ ਹੈ। ਇਹ ਸਰਕਾਰੀ ਵੈੱਬਸਾਈਟ ਨਹੀਂ ਹੈ; ਇਹ ਪ੍ਰਕਾਸ਼ਿਤ ਸਰਕਾਰੀ ਡਾਟਾ ਵਰਤਦਾ ਹੈ।",
        raj="म्हैं JalMitra हूं, एक कंप्यूटर प्रोग्राम, कोई मिनख कोनी। म्हैं तय नियमां अर इण ऐप रा सरकारी डेटासेट सूं, इणी "
            "कंप्यूटर माथै काम करूं। म्हैं ChatGPT, Gemini या कोई ऑनलाइन AI काम में कोनी लेऊं। JalMitra स्मार्ट इंडिया "
            "हैकाथॉन री समस्या SIH25066 (जल शक्ति मंत्रालय) सारू बणायो गयो है। आ सरकारी वेबसाइट कोनी; आ छप्योड़ो सरकारी डेटा काम में लेवै।"),
    "st_negative": V(
        en=["Sorry about that. Could you tell me the place and what you want to know? For example: Is Ajmer Urban safe? "
            "You can also press 👎 under an answer so the problem is noted.",
            "I'm sorry the answer didn't help. Try naming the block or district, or pick one of the questions below."],
        hi=["माफ़ कीजिए। कृपया जगह और आप क्या जानना चाहते हैं, बताइए। जैसे: जयपुर ज़िले में भूजल की स्थिति क्या है? "
            "जवाब के नीचे 👎 दबाकर भी बता सकते हैं।",
            "माफ़ कीजिए, जवाब काम नहीं आया। ब्लॉक या ज़िले का नाम लिखिए, या नीचे दिया कोई सवाल चुनिए।"],
        hinglish=["Maaf kijiye. Jagah ka naam aur aap kya jaanna chahte hain, bataiye. Jaise: Ajmer Urban ka paani kaisa hai? "
                  "Jawab ke neeche 👎 dabakar bhi bata sakte hain.",
                  "Maaf kijiye, jawab kaam nahi aaya. Block ya district ka naam likhiye, ya neeche diya koi sawal chuniye."],
        mr=["माफ करा. ठिकाण आणि तुम्हाला काय जाणून घ्यायचे आहे ते सांगा. उत्तराखाली 👎 दाबूनही सांगू शकता.",
            "माफ करा, उत्तर उपयोगी पडले नाही. ब्लॉक किंवा जिल्ह्याचे नाव लिहा, किंवा खालील प्रश्न निवडा."],
        pa=["ਮਾਫ਼ ਕਰਨਾ। ਥਾਂ ਦਾ ਨਾਮ ਅਤੇ ਤੁਸੀਂ ਕੀ ਜਾਣਨਾ ਚਾਹੁੰਦੇ ਹੋ, ਦੱਸੋ। ਜਵਾਬ ਹੇਠਾਂ 👎 ਦਬਾ ਕੇ ਵੀ ਦੱਸ ਸਕਦੇ ਹੋ।",
            "ਮਾਫ਼ ਕਰਨਾ, ਜਵਾਬ ਕੰਮ ਨਹੀਂ ਆਇਆ। ਬਲਾਕ ਜਾਂ ਜ਼ਿਲ੍ਹੇ ਦਾ ਨਾਮ ਲਿਖੋ, ਜਾਂ ਹੇਠਾਂ ਦਿੱਤਾ ਸਵਾਲ ਚੁਣੋ।"],
        raj=["माफ करजो सा। जगां रो नाम अर थे कांई जाणणो चावो, बतावो। जवाब रै नीचै 👎 दबा नै भी बता सको।",
             "माफ करजो, जवाब काम कोनी आयो। ब्लॉक या जिलै रो नाम लिखो, या नीचै दियो सवाल चुणो।"]),
    "st_confused": V(
        en=["Let me make it simpler. Set the answer style to Farmer and the detail to Short in the sidebar, or ask one of "
            "the questions below.", "No problem. Ask me one short question, for example: Is Ajmer Urban safe?"],
        hi=["मैं आसान कर देता हूँ। साइडबार में जवाब की शैली Farmer और विवरण Short चुनिए, या नीचे दिया कोई सवाल पूछिए।",
            "कोई बात नहीं। एक छोटा सवाल पूछिए, जैसे: जयपुर ज़िले में भूजल की स्थिति क्या है?"],
        hinglish=["Main aasaan kar deta hoon. Sidebar mein answer style Farmer aur detail Short chuniye, ya neeche diya koi "
                  "sawal poochiye.", "Koi baat nahi. Ek chhota sawal poochiye, jaise: Ajmer Urban ka paani kaisa hai?"],
        mr=["मी सोपे करतो. साइडबारमध्ये उत्तर शैली Farmer आणि तपशील Short निवडा, किंवा खालील प्रश्न विचारा.",
            "हरकत नाही. एक छोटा प्रश्न विचारा."],
        pa=["ਮੈਂ ਸੌਖਾ ਕਰ ਦਿੰਦਾ ਹਾਂ। ਸਾਈਡਬਾਰ ਵਿੱਚ ਜਵਾਬ ਸ਼ੈਲੀ Farmer ਅਤੇ ਵੇਰਵਾ Short ਚੁਣੋ, ਜਾਂ ਹੇਠਾਂ ਦਿੱਤਾ ਸਵਾਲ ਪੁੱਛੋ।",
            "ਕੋਈ ਗੱਲ ਨਹੀਂ। ਇੱਕ ਛੋਟਾ ਸਵਾਲ ਪੁੱਛੋ।"],
        raj=["म्हैं सोरो कर देऊं। साइडबार में जवाब री सैली Farmer अर विवरण Short चुणो, या नीचै दियो सवाल पूछो।",
             "कोई बात कोनी। एक छोटो सवाल पूछो।"]),
    "st_laugh": V(
        en=["😊 Glad you're enjoying it. Ask me anything about water, soil or crops.", "😄 What would you like to check next?"],
        hi=["😊 खुशी हुई। पानी, मिट्टी या फसल के बारे में कुछ भी पूछिए।", "😄 अब क्या देखना चाहेंगे?"],
        hinglish=["😊 Khushi hui. Paani, mitti ya fasal ke baare mein kuch bhi poochiye.", "😄 Ab kya dekhna chahenge?"],
        mr=["😊 आनंद झाला. पाणी, माती किंवा पिकांबद्दल काहीही विचारा.", "😄 पुढे काय पाहायचे?"],
        pa=["😊 ਖੁਸ਼ੀ ਹੋਈ। ਪਾਣੀ, ਮਿੱਟੀ ਜਾਂ ਫ਼ਸਲ ਬਾਰੇ ਕੁਝ ਵੀ ਪੁੱਛੋ।", "😄 ਹੁਣ ਕੀ ਵੇਖਣਾ ਹੈ?"],
        raj=["😊 खुसी होई। पाणी, माटी या फसल रै बारै में कीं भी पूछो।", "😄 अबै कांई देखणो है?"]),

    # ------------------------------------------------------------ yes / no / partly openers
    "sc_yes": V(en=["Yes.", "Yes, that is covered.", "Yes, it is."], hi=["हाँ।", "हाँ, यह शामिल है।"],
                hinglish=["Haan.", "Haan, yeh shamil hai."], mr=["हो.", "हो, हे समाविष्ट आहे."],
                pa=["ਹਾਂ।", "ਹਾਂ, ਇਹ ਸ਼ਾਮਲ ਹੈ।"], raj=["हां सा।", "हां, ओ सामिल है।"]),
    "sc_no": V(en=["No.", "No, that is not covered.", "No, JalMitra does not cover that."],
               hi=["नहीं।", "नहीं, यह शामिल नहीं है।"], hinglish=["Nahi.", "Nahi, yeh shamil nahi hai."],
               mr=["नाही.", "नाही, हे समाविष्ट नाही."], pa=["ਨਹੀਂ।", "ਨਹੀਂ, ਇਹ ਸ਼ਾਮਲ ਨਹੀਂ ਹੈ।"],
               raj=["कोनी सा।", "ना, ओ सामिल कोनी।"]),
    "sc_partly": V(en="Partly.", hi="कुछ हद तक।", hinglish="Kuch had tak.", mr="काही प्रमाणात.", pa="ਕੁਝ ਹੱਦ ਤੱਕ।",
                   raj="थोड़ो-घणो।"),
    "sc_unknown": V(
        en=["I don't think JalMitra covers that.", "That doesn't look like something JalMitra covers."],
        hi=["मुझे नहीं लगता कि JalMitra में यह शामिल है।", "यह JalMitra के दायरे में नहीं लगता।"],
        hinglish=["Mujhe nahi lagta ki JalMitra mein yeh shamil hai.", "Yeh JalMitra ke daayre mein nahi lagta."],
        mr=["JalMitra मध्ये हे समाविष्ट असल्याचे वाटत नाही."], pa=["ਮੈਨੂੰ ਨਹੀਂ ਲੱਗਦਾ ਕਿ JalMitra ਵਿੱਚ ਇਹ ਸ਼ਾਮਲ ਹੈ।"],
        raj=["म्हनै कोनी लागै कै JalMitra में ओ सामिल है।"]),
    "oos_open": V(
        en=["That is outside what JalMitra covers.", "Sorry, JalMitra can't help with that.",
            "JalMitra doesn't have that information."],
        hi=["यह JalMitra के दायरे से बाहर है।", "माफ़ कीजिए, JalMitra इसमें मदद नहीं कर सकता।"],
        hinglish=["Yeh JalMitra ke daayre se bahar hai.", "Maaf kijiye, JalMitra ismein madad nahi kar sakta."],
        mr=["हे JalMitra च्या कक्षेबाहेर आहे.", "माफ करा, JalMitra यात मदत करू शकत नाही."],
        pa=["ਇਹ JalMitra ਦੇ ਦਾਇਰੇ ਤੋਂ ਬਾਹਰ ਹੈ।", "ਮਾਫ਼ ਕਰਨਾ, JalMitra ਇਸ ਵਿੱਚ ਮਦਦ ਨਹੀਂ ਕਰ ਸਕਦਾ।"],
        raj=["ओ JalMitra रै दायरै सूं बारै है।", "माफ करजो, JalMitra इण में मदद कोनी कर सकै।"]),

    # ------------------------------------------------------------ topic bodies (what is / is not covered)
    "tp_groundwater": V(
        en="JalMitra shows the official 2025 groundwater category for 6,762 assessment units across India, with "
           "detailed figures (recharge, extraction, stage of extraction) for 302 Rajasthan blocks.",
        hi="JalMitra पूरे भारत की 6,762 आकलन इकाइयों की 2025 की आधिकारिक भूजल श्रेणी दिखाता है, और राजस्थान के 302 ब्लॉकों "
           "के विस्तृत आंकड़े (पुनर्भरण, दोहन, दोहन का स्तर)।",
        hinglish="JalMitra poore Bharat ki 6,762 assessment units ki 2025 ki official groundwater category dikhata hai, aur "
                 "Rajasthan ke 302 blocks ke detailed figures (recharge, extraction, stage of extraction).",
        mr="JalMitra संपूर्ण भारतातील 6,762 मूल्यांकन घटकांची 2025 ची अधिकृत भूजल श्रेणी दाखवतो, आणि राजस्थानमधील 302 ब्लॉकचे "
           "तपशीलवार आकडे.",
        pa="JalMitra ਪੂਰੇ ਭਾਰਤ ਦੀਆਂ 6,762 ਮੁਲਾਂਕਣ ਇਕਾਈਆਂ ਦੀ 2025 ਦੀ ਸਰਕਾਰੀ ਸ਼੍ਰੇਣੀ ਦਿਖਾਉਂਦਾ ਹੈ, ਅਤੇ ਰਾਜਸਥਾਨ ਦੇ 302 "
           "ਬਲਾਕਾਂ ਦੇ ਵਿਸਤ੍ਰਿਤ ਅੰਕੜੇ।",
        raj="JalMitra पूरै भारत री 6,762 आकलन इकाइयां री 2025 री सरकारी भूजल श्रेणी दिखावै, अर राजस्थान रा 302 ब्लॉकां रा "
            "पूरा आंकड़ा।"),
    "tp_water_quality": V(
        en="You can enter your own water-test results on the Groundwater Quality page and compare them with BIS IS 10500 "
           "drinking-water limits and IS 11624 irrigation guidelines. JalMitra has no measured water-quality data for "
           "places yet, and it never certifies water as safe to drink.",
        hi="आप भूजल गुणवत्ता पेज पर अपनी पानी जाँच के नतीजे डालकर उनकी तुलना BIS IS 10500 पेयजल सीमाओं और IS 11624 सिंचाई "
           "दिशानिर्देशों से कर सकते हैं। JalMitra के पास अभी जगहों का मापा हुआ पानी गुणवत्ता डेटा नहीं है, और यह पानी को कभी "
           "पीने के लिए सुरक्षित घोषित नहीं करता।",
        hinglish="Groundwater Quality page par apni paani jaanch ke results daal kar unki tulna BIS IS 10500 peene ke paani "
                 "ki limits aur IS 11624 sinchai guidelines se kar sakte hain. JalMitra ke paas abhi jagahon ka measured "
                 "water quality data nahi hai, aur yeh paani ko kabhi peene ke liye safe declare nahi karta.",
        mr="Groundwater Quality पानावर तुमच्या पाणी तपासणीचे निकाल टाकून त्यांची तुलना BIS IS 10500 आणि IS 11624 शी करता "
           "येते. JalMitra कडे ठिकाणांचा मोजलेला पाणी गुणवत्ता डेटा अजून नाही, आणि तो पाणी पिण्यास सुरक्षित असल्याचे कधीच जाहीर करत नाही.",
        pa="Groundwater Quality ਪੰਨੇ 'ਤੇ ਆਪਣੀ ਪਾਣੀ ਜਾਂਚ ਦੇ ਨਤੀਜੇ ਪਾ ਕੇ BIS IS 10500 ਅਤੇ IS 11624 ਨਾਲ ਤੁਲਨਾ ਕਰ ਸਕਦੇ ਹੋ। "
           "JalMitra ਕੋਲ ਹਾਲੇ ਥਾਵਾਂ ਦਾ ਮਾਪਿਆ ਪਾਣੀ ਗੁਣਵੱਤਾ ਡਾਟਾ ਨਹੀਂ ਹੈ, ਅਤੇ ਇਹ ਪਾਣੀ ਨੂੰ ਕਦੇ ਪੀਣ ਲਈ ਸੁਰੱਖਿਅਤ ਨਹੀਂ ਐਲਾਨਦਾ।",
        raj="Groundwater Quality पानै माथै आपरी पाणी जांच रा नतीजा भर नै BIS IS 10500 अर IS 11624 सूं मिला सको। JalMitra "
            "कनै हाल जगां रो मापियोड़ो पाणी गुणवत्ता डेटा कोनी, अर ओ पाणी नै कदेई पीवण सारू सुरक्षित कोनी बतावै।"),
    "tp_soil": V(
        en="Upload your Soil Health Card or lab report on My Soil Report (PDF, CSV or Excel) and JalMitra explains each "
           "value against published reference ranges. It is not a soil-testing lab, and it has no measured soil data for "
           "places.",
        hi="My Soil Report पर अपना मृदा स्वास्थ्य कार्ड या लैब रिपोर्ट (PDF, CSV या Excel) अपलोड कीजिए, JalMitra हर मान को "
           "प्रकाशित संदर्भ सीमाओं के साथ समझाता है। यह मिट्टी जाँच की लैब नहीं है, और इसके पास जगहों का मापा हुआ मिट्टी डेटा नहीं है।",
        hinglish="My Soil Report par apna Soil Health Card ya lab report (PDF, CSV ya Excel) upload kijiye, JalMitra har "
                 "value ko published reference ranges ke saath samjhata hai. Yeh soil testing lab nahi hai, aur iske paas "
                 "jagahon ka measured soil data nahi hai.",
        mr="My Soil Report वर तुमची मृदा आरोग्य पत्रिका किंवा प्रयोगशाळा अहवाल अपलोड करा; JalMitra प्रत्येक मूल्य प्रकाशित "
           "मर्यादांनुसार समजावतो. ही माती तपासणी प्रयोगशाळा नाही.",
        pa="My Soil Report 'ਤੇ ਆਪਣਾ ਸੋਇਲ ਹੈਲਥ ਕਾਰਡ ਜਾਂ ਲੈਬ ਰਿਪੋਰਟ ਅੱਪਲੋਡ ਕਰੋ; JalMitra ਹਰ ਮੁੱਲ ਨੂੰ ਪ੍ਰਕਾਸ਼ਿਤ ਸੀਮਾਵਾਂ ਨਾਲ "
           "ਸਮਝਾਉਂਦਾ ਹੈ। ਇਹ ਮਿੱਟੀ ਜਾਂਚ ਲੈਬ ਨਹੀਂ ਹੈ।",
        raj="My Soil Report माथै आपरो मृदा स्वास्थ्य कार्ड या लैब रिपोर्ट अपलोड करो; JalMitra हर मान नै छपी सीमावां सागै "
            "समझावै। ओ माटी जांचण री लैब कोनी।"),
    "tp_fertilizer": V(
        en="JalMitra explains the nutrient values on your Soil Health Card, but it does not calculate fertiliser doses. "
           "Follow the recommendation printed on your card, or ask your local agriculture officer or Krishi Vigyan Kendra.",
        hi="JalMitra आपके मृदा स्वास्थ्य कार्ड के पोषक तत्वों के मान समझाता है, पर खाद की मात्रा नहीं निकालता। कार्ड पर छपी "
           "सिफारिश मानिए, या अपने कृषि अधिकारी या कृषि विज्ञान केंद्र से पूछिए।",
        hinglish="JalMitra aapke Soil Health Card ke nutrient values samjhata hai, par khaad ki matra nahi nikalta. Card par "
                 "chhapi sifarish maaniye, ya apne krishi adhikari ya Krishi Vigyan Kendra se poochiye.",
        mr="JalMitra तुमच्या मृदा आरोग्य पत्रिकेतील पोषक मूल्ये समजावतो, पण खताची मात्रा काढत नाही. पत्रिकेवरील शिफारस पाळा "
           "किंवा कृषी अधिकारी / कृषी विज्ञान केंद्राला विचारा.",
        pa="JalMitra ਤੁਹਾਡੇ ਸੋਇਲ ਹੈਲਥ ਕਾਰਡ ਦੇ ਪੋਸ਼ਕ ਮੁੱਲ ਸਮਝਾਉਂਦਾ ਹੈ, ਪਰ ਖਾਦ ਦੀ ਮਾਤਰਾ ਨਹੀਂ ਕੱਢਦਾ। ਕਾਰਡ 'ਤੇ ਲਿਖੀ ਸਿਫ਼ਾਰਸ਼ "
           "ਮੰਨੋ ਜਾਂ ਖੇਤੀਬਾੜੀ ਅਫ਼ਸਰ / ਕ੍ਰਿਸ਼ੀ ਵਿਗਿਆਨ ਕੇਂਦਰ ਨੂੰ ਪੁੱਛੋ।",
        raj="JalMitra आपरै मृदा स्वास्थ्य कार्ड रा पोसक तत्वां रा मान समझावै, पण खाद री मात्रा कोनी काढै। कार्ड माथै छपी "
            "सिफारिस मानो, या कृषि अधिकारी या कृषि विज्ञान केंद्र सूं पूछो।"),
    "tp_crops": V(
        en="JalMitra gives crop facts such as water need and salt tolerance (FAO) and the crop list for SKNAU Zone II-A. "
           "It does not predict yield or profit.",
        hi="JalMitra फसलों की पानी की ज़रूरत और लवण सहनशीलता (FAO) जैसी जानकारी और SKNAU ज़ोन II-A की फसल सूची देता है। "
           "यह पैदावार या मुनाफ़े का अनुमान नहीं लगाता।",
        hinglish="JalMitra fasal ki paani ki zaroorat aur salt tolerance (FAO) jaisi jaankari aur SKNAU Zone II-A ki fasal "
                 "list deta hai. Yeh paidavaar ya munafe ka andaza nahi lagata.",
        mr="JalMitra पिकांची पाण्याची गरज आणि क्षार सहनशीलता (FAO) आणि SKNAU झोन II-A ची पीक यादी देतो. तो उत्पादन किंवा "
           "नफ्याचा अंदाज देत नाही.",
        pa="JalMitra ਫ਼ਸਲਾਂ ਦੀ ਪਾਣੀ ਦੀ ਲੋੜ ਅਤੇ ਲੂਣ ਸਹਿਣਸ਼ੀਲਤਾ (FAO) ਅਤੇ SKNAU ਜ਼ੋਨ II-A ਦੀ ਫ਼ਸਲ ਸੂਚੀ ਦਿੰਦਾ ਹੈ। ਇਹ ਝਾੜ "
           "ਜਾਂ ਮੁਨਾਫ਼ੇ ਦਾ ਅੰਦਾਜ਼ਾ ਨਹੀਂ ਲਗਾਉਂਦਾ।",
        raj="JalMitra फसलां री पाणी री जरूरत अर खारेपण सहण (FAO) री जाणकारी अर SKNAU जोन II-A री फसल सूची देवै। ओ "
            "उपज या नफै रो अंदाजो कोनी लगावै।"),
    "tp_farming": V(
        en="JalMitra is made for farmers and anyone who needs water and land information: groundwater status, soil "
           "report explanations, water-test checks, crop water needs and irrigation methods.",
        hi="JalMitra किसानों और पानी व ज़मीन की जानकारी चाहने वालों के लिए है: भूजल की स्थिति, मिट्टी रिपोर्ट की व्याख्या, पानी "
           "जाँच, फसलों की पानी की ज़रूरत और सिंचाई के तरीके।",
        hinglish="JalMitra kisanon aur paani-zameen ki jaankari chahne walon ke liye hai: groundwater status, soil report "
                 "ki vyakhya, paani ki jaanch, fasal ki paani ki zaroorat aur sinchai ke tareeke.",
        mr="JalMitra शेतकऱ्यांसाठी आहे: भूजल स्थिती, माती अहवालाचे स्पष्टीकरण, पाणी तपासणी, पिकांची पाण्याची गरज आणि सिंचन पद्धती.",
        pa="JalMitra ਕਿਸਾਨਾਂ ਲਈ ਹੈ: ਧਰਤੀ ਹੇਠਲੇ ਪਾਣੀ ਦੀ ਹਾਲਤ, ਮਿੱਟੀ ਰਿਪੋਰਟ ਦੀ ਵਿਆਖਿਆ, ਪਾਣੀ ਜਾਂਚ, ਫ਼ਸਲਾਂ ਦੀ ਪਾਣੀ ਦੀ ਲੋੜ ਅਤੇ "
           "ਸਿੰਚਾਈ ਦੇ ਤਰੀਕੇ।",
        raj="JalMitra करसाणां सारू है: भूजल री हालत, माटी री रिपोर्ट री समझ, पाणी री जांच, फसलां री पाणी री जरूरत अर सिंचाई "
            "रा तरीका।"),
    "tp_irrigation": V(
        en="The Irrigation Advisor explains drip, sprinkler and other methods, farm ponds, rainwater harvesting and "
           "recharge structures, and checks irrigation-water salinity (EC) against IS 11624.",
        hi="सिंचाई सलाहकार ड्रिप, स्प्रिंकलर और दूसरे तरीके, खेत तलाई, वर्षा जल संचयन और पुनर्भरण संरचनाएँ समझाता है, और "
           "सिंचाई के पानी की लवणता (EC) को IS 11624 से जाँचता है।",
        hinglish="Irrigation Advisor drip, sprinkler aur doosre tareeke, khet talai, rainwater harvesting aur recharge "
                 "structures samjhata hai, aur sinchai ke paani ki salinity (EC) ko IS 11624 se jaanchta hai.",
        mr="Irrigation Advisor ठिबक, तुषार आणि इतर पद्धती, शेततळे, पावसाचे पाणी साठवण आणि पुनर्भरण समजावतो, आणि सिंचनाच्या "
           "पाण्याची क्षारता (EC) IS 11624 नुसार तपासतो.",
        pa="Irrigation Advisor ਤੁਪਕਾ, ਫੁਹਾਰਾ ਅਤੇ ਹੋਰ ਤਰੀਕੇ, ਖੇਤ ਤਲਾਬ, ਮੀਂਹ ਦੇ ਪਾਣੀ ਦੀ ਸੰਭਾਲ ਅਤੇ ਰੀਚਾਰਜ ਸਮਝਾਉਂਦਾ ਹੈ, ਅਤੇ "
           "ਸਿੰਚਾਈ ਪਾਣੀ ਦੀ ਖਾਰਾਪਣ (EC) IS 11624 ਨਾਲ ਜਾਂਚਦਾ ਹੈ।",
        raj="Irrigation Advisor ड्रिप, फव्वारो अर दूजा तरीका, खेत तलाई, बिरखा रो पाणी भेळो करणो अर पुनर्भरण समझावै, अर "
            "सिंचाई रै पाणी रो खारोपण (EC) IS 11624 सूं जांचै।"),
    "tp_land": V(
        en="The Land Condition Report brings together the data available for a place, and the Land Degradation page "
           "explains erosion, salinity, waterlogging and conservation practices. Measured data for your own field is not "
           "available.",
        hi="भूमि स्थिति रिपोर्ट किसी जगह का उपलब्ध डेटा एक साथ दिखाती है, और भूमि क्षरण पेज कटाव, लवणता, जलभराव और संरक्षण के "
           "तरीके समझाता है। आपके अपने खेत का मापा हुआ डेटा उपलब्ध नहीं है।",
        hinglish="Land Condition Report kisi jagah ka uplabdh data ek saath dikhati hai, aur Land Degradation page katav, "
                 "salinity, waterlogging aur sanrakshan ke tareeke samjhata hai. Aapke apne khet ka measured data nahi hai.",
        mr="जमीन स्थिती अहवाल एखाद्या ठिकाणाचा उपलब्ध डेटा एकत्र दाखवतो, आणि Land Degradation पान धूप, क्षारता, पाणथळ आणि "
           "संवर्धन समजावते.",
        pa="ਜ਼ਮੀਨ ਦੀ ਹਾਲਤ ਰਿਪੋਰਟ ਕਿਸੇ ਥਾਂ ਦਾ ਉਪਲਬਧ ਡਾਟਾ ਇਕੱਠਾ ਦਿਖਾਉਂਦੀ ਹੈ, ਅਤੇ Land Degradation ਪੰਨਾ ਖੋਰ, ਖਾਰਾਪਣ ਅਤੇ "
           "ਸੰਭਾਲ ਸਮਝਾਉਂਦਾ ਹੈ।",
        raj="जमीन री हालत री रिपोर्ट किणी जगां रो मिलतो डेटा एक सागै दिखावै, अर Land Degradation पानो कटाव, खारोपण अर बचाव "
            "समझावै।"),
    "tp_reports": V(
        en="Six reports can be downloaded from My Reports: groundwater, soil, land, crop, irrigation and a complete report.",
        hi="My Reports से छह रिपोर्ट डाउनलोड हो सकती हैं: भूजल, मिट्टी, भूमि, फसल, सिंचाई और पूरी रिपोर्ट।",
        hinglish="My Reports se 6 reports download ho sakti hain: groundwater, soil, land, crop, irrigation aur complete report.",
        mr="My Reports मधून सहा अहवाल डाउनलोड करता येतात: भूजल, माती, जमीन, पीक, सिंचन आणि संपूर्ण अहवाल.",
        pa="My Reports ਤੋਂ ਛੇ ਰਿਪੋਰਟਾਂ ਡਾਊਨਲੋਡ ਹੋ ਸਕਦੀਆਂ ਹਨ: ਪਾਣੀ, ਮਿੱਟੀ, ਜ਼ਮੀਨ, ਫ਼ਸਲ, ਸਿੰਚਾਈ ਅਤੇ ਪੂਰੀ ਰਿਪੋਰਟ।",
        raj="My Reports सूं छह रिपोर्टां डाउनलोड हो सकै: भूजल, माटी, जमीन, फसल, सिंचाई अर पूरी रिपोर्ट।"),
    "tp_languages": V(
        en="Answers are available in English, Hindi, Hinglish, Rajasthani, Punjabi and Marathi. Pick one in the sidebar "
           "or just type in your language.",
        hi="जवाब English, हिंदी, Hinglish, राजस्थानी, ਪੰਜਾਬੀ और मराठी में मिलते हैं। साइडबार में भाषा चुनिए या सीधे अपनी भाषा में लिखिए।",
        hinglish="Jawab English, Hindi, Hinglish, Rajasthani, Punjabi aur Marathi mein milte hain. Sidebar mein bhasha "
                 "chuniye ya seedhe apni bhasha mein likhiye.",
        mr="उत्तरे English, हिंदी, Hinglish, राजस्थानी, ਪੰਜਾਬੀ आणि मराठी मध्ये मिळतात.",
        pa="ਜਵਾਬ English, हिंदी, Hinglish, राजस्थानी, ਪੰਜਾਬੀ ਅਤੇ मराठी ਵਿੱਚ ਮਿਲਦੇ ਹਨ।",
        raj="जवाब English, हिंदी, Hinglish, राजस्थानी, ਪੰਜਾਬੀ अर मराठी में मिलै।"),
    # out of scope
    "tp_money": V(
        en="JalMitra has no information on money, income, loans, subsidies or government schemes, and it does not "
           "predict yield or profit. For loans and schemes, please ask your bank or your local agriculture office.",
        hi="JalMitra के पास पैसे, आमदनी, लोन, सब्सिडी या सरकारी योजनाओं की जानकारी नहीं है, और यह पैदावार या मुनाफ़े का अनुमान "
           "नहीं लगाता। लोन और योजनाओं के लिए अपने बैंक या स्थानीय कृषि कार्यालय से पूछिए।",
        hinglish="JalMitra ke paas paise, aamdani, loan, subsidy ya sarkari yojanaon ki jaankari nahi hai, aur yeh "
                 "paidavaar ya munafe ka andaza nahi lagata. Loan aur yojanaon ke liye apne bank ya krishi karyalay se poochiye.",
        mr="JalMitra कडे पैसा, उत्पन्न, कर्ज, अनुदान किंवा सरकारी योजनांची माहिती नाही, आणि तो उत्पादन किंवा नफ्याचा अंदाज देत "
           "नाही. कर्ज व योजनांसाठी तुमच्या बँकेला किंवा कृषी कार्यालयाला विचारा.",
        pa="JalMitra ਕੋਲ ਪੈਸੇ, ਕਮਾਈ, ਕਰਜ਼ੇ, ਸਬਸਿਡੀ ਜਾਂ ਸਰਕਾਰੀ ਯੋਜਨਾਵਾਂ ਦੀ ਜਾਣਕਾਰੀ ਨਹੀਂ ਹੈ, ਅਤੇ ਇਹ ਝਾੜ ਜਾਂ ਮੁਨਾਫ਼ੇ ਦਾ "
           "ਅੰਦਾਜ਼ਾ ਨਹੀਂ ਲਗਾਉਂਦਾ। ਕਰਜ਼ੇ ਅਤੇ ਯੋਜਨਾਵਾਂ ਲਈ ਆਪਣੇ ਬੈਂਕ ਜਾਂ ਖੇਤੀਬਾੜੀ ਦਫ਼ਤਰ ਨੂੰ ਪੁੱਛੋ।",
        raj="JalMitra कनै पइसा, कमाई, करजो, सब्सिडी या सरकारी योजनावां री जाणकारी कोनी, अर ओ उपज या नफै रो अंदाजो कोनी "
            "लगावै। करजै अर योजनावां सारू आपरै बैंक या कृषि दफ्तर सूं पूछो।"),
    "tp_prices": V(
        en="JalMitra has no market or mandi prices. Government mandi prices are published on the Agmarknet portal.",
        hi="JalMitra के पास बाज़ार या मंडी भाव नहीं हैं। सरकारी मंडी भाव Agmarknet पोर्टल पर प्रकाशित होते हैं।",
        hinglish="JalMitra ke paas market ya mandi bhav nahi hain. Sarkari mandi bhav Agmarknet portal par milte hain.",
        mr="JalMitra कडे बाजारभाव नाहीत. सरकारी बाजारभाव Agmarknet पोर्टलवर प्रकाशित होतात.",
        pa="JalMitra ਕੋਲ ਮੰਡੀ ਦੇ ਭਾਅ ਨਹੀਂ ਹਨ। ਸਰਕਾਰੀ ਮੰਡੀ ਭਾਅ Agmarknet ਪੋਰਟਲ 'ਤੇ ਮਿਲਦੇ ਹਨ।",
        raj="JalMitra कनै मंडी रा भाव कोनी। सरकारी मंडी भाव Agmarknet पोर्टल माथै मिलै।"),
    "tp_weather": V(
        en="JalMitra has no weather data or forecasts. For forecasts and farm weather advice, see the India "
           "Meteorological Department (IMD) and its Agromet advisories.",
        hi="JalMitra के पास मौसम का डेटा या पूर्वानुमान नहीं है। पूर्वानुमान और खेती की मौसम सलाह के लिए भारत मौसम विज्ञान विभाग "
           "(IMD) और उसकी एग्रोमेट सलाह देखिए।",
        hinglish="JalMitra ke paas mausam ka data ya forecast nahi hai. Forecast aur kheti ki mausam salah ke liye India "
                 "Meteorological Department (IMD) aur uski Agromet advisory dekhiye.",
        mr="JalMitra कडे हवामानाचा डेटा किंवा अंदाज नाही. अंदाज आणि शेती हवामान सल्ल्यासाठी भारतीय हवामान विभाग (IMD) आणि "
           "त्याचे ॲग्रोमेट सल्ले पहा.",
        pa="JalMitra ਕੋਲ ਮੌਸਮ ਦਾ ਡਾਟਾ ਜਾਂ ਭਵਿੱਖਬਾਣੀ ਨਹੀਂ ਹੈ। ਇਸ ਲਈ ਭਾਰਤ ਮੌਸਮ ਵਿਭਾਗ (IMD) ਅਤੇ ਉਸ ਦੀਆਂ ਐਗਰੋਮੈਟ "
           "ਸਲਾਹਾਂ ਵੇਖੋ।",
        raj="JalMitra कनै मौसम रो डेटा या अंदाजो कोनी। इण सारू भारत मौसम विज्ञान विभाग (IMD) अर उणरी एग्रोमेट सलाह देखो।"),
    "tp_shop": V(
        en="JalMitra does not sell, buy, rent or book anything. It only gives information.",
        hi="JalMitra कुछ भी बेचता, खरीदता, किराये पर देता या बुक नहीं करता। यह केवल जानकारी देता है।",
        hinglish="JalMitra kuch bhi bechta, khareedta, kiraye par deta ya book nahi karta. Yeh sirf jaankari deta hai.",
        mr="JalMitra काहीही विकत नाही, खरेदी करत नाही किंवा बुक करत नाही. तो फक्त माहिती देतो.",
        pa="JalMitra ਕੁਝ ਵੀ ਵੇਚਦਾ, ਖਰੀਦਦਾ ਜਾਂ ਬੁੱਕ ਨਹੀਂ ਕਰਦਾ। ਇਹ ਸਿਰਫ਼ ਜਾਣਕਾਰੀ ਦਿੰਦਾ ਹੈ।",
        raj="JalMitra कीं भी कोनी बेचै, खरीदै या बुक करै। ओ फगत जाणकारी देवै।"),
    "tp_pests": V(
        en="JalMitra does not cover pests or crop diseases. Please contact your nearest Krishi Vigyan Kendra or "
           "agriculture officer.",
        hi="JalMitra कीट या फसल रोगों की जानकारी नहीं देता। कृपया नज़दीकी कृषि विज्ञान केंद्र या कृषि अधिकारी से संपर्क कीजिए।",
        hinglish="JalMitra keet ya fasal rogon ki jaankari nahi deta. Kripya nazdeeki Krishi Vigyan Kendra ya krishi "
                 "adhikari se sampark kijiye.",
        mr="JalMitra कीड किंवा पीक रोगांची माहिती देत नाही. जवळच्या कृषी विज्ञान केंद्राशी किंवा कृषी अधिकाऱ्याशी संपर्क करा.",
        pa="JalMitra ਕੀੜਿਆਂ ਜਾਂ ਫ਼ਸਲ ਬਿਮਾਰੀਆਂ ਬਾਰੇ ਜਾਣਕਾਰੀ ਨਹੀਂ ਦਿੰਦਾ। ਨੇੜਲੇ ਕ੍ਰਿਸ਼ੀ ਵਿਗਿਆਨ ਕੇਂਦਰ ਜਾਂ ਖੇਤੀਬਾੜੀ ਅਫ਼ਸਰ ਨਾਲ ਸੰਪਰਕ ਕਰੋ।",
        raj="JalMitra कीड़ा या फसल रा रोगां री जाणकारी कोनी देवै। नैड़ै कृषि विज्ञान केंद्र या कृषि अधिकारी सूं मिलो।"),
    "tp_livestock": V(
        en="JalMitra does not cover animals, dairy or poultry.",
        hi="JalMitra पशु, डेयरी या मुर्गी पालन की जानकारी नहीं देता।",
        hinglish="JalMitra pashu, dairy ya murgi paalan ki jaankari nahi deta.",
        mr="JalMitra पशू, दुग्ध व्यवसाय किंवा कुक्कुटपालनाची माहिती देत नाही.",
        pa="JalMitra ਪਸ਼ੂਆਂ, ਡੇਅਰੀ ਜਾਂ ਮੁਰਗੀ ਪਾਲਣ ਬਾਰੇ ਜਾਣਕਾਰੀ ਨਹੀਂ ਦਿੰਦਾ।",
        raj="JalMitra पसुवां, डेयरी या मुरगी पालण री जाणकारी कोनी देवै।"),
    "tp_general": V(en="", hi="", hinglish="", mr="", pa="", raj=""),

    # ------------------------------------------------------------ fallback
    "fb_cue": V(
        en=["I'm not sure what you meant. Did you mean one of these?",
            "I didn't fully understand. These are the closest questions I can answer:",
            "Could you say that another way? These questions are close to what you asked:"],
        hi=["मैं ठीक से नहीं समझ पाया। क्या आप इनमें से कुछ पूछना चाहते हैं?", "मैं पूरा नहीं समझ पाया। ये सबसे मिलते-जुलते सवाल हैं:",
            "कृपया दूसरे शब्दों में पूछिए। ये सवाल आपके सवाल के करीब हैं:"],
        hinglish=["Main theek se nahi samajh paaya. Kya aap inmein se kuch poochna chahte hain?",
                  "Main poora nahi samajh paaya. Yeh sabse milte-julte sawal hain:",
                  "Kripya doosre shabdon mein poochiye. Yeh sawal aapke sawal ke kareeb hain:"],
        mr=["मला नीट समजले नाही. तुम्हाला यापैकी काही विचारायचे आहे का?", "मला पूर्ण समजले नाही. हे सर्वात जवळचे प्रश्न आहेत:"],
        pa=["ਮੈਂ ਠੀਕ ਤਰ੍ਹਾਂ ਨਹੀਂ ਸਮਝ ਸਕਿਆ। ਕੀ ਤੁਸੀਂ ਇਹਨਾਂ ਵਿੱਚੋਂ ਕੁਝ ਪੁੱਛਣਾ ਚਾਹੁੰਦੇ ਹੋ?", "ਮੈਂ ਪੂਰਾ ਨਹੀਂ ਸਮਝ ਸਕਿਆ। ਇਹ ਸਭ ਤੋਂ ਨੇੜਲੇ ਸਵਾਲ ਹਨ:"],
        raj=["म्हैं ठीक सूं कोनी समझ्यो। कांई थे इणां में सूं कीं पूछणो चावो?", "म्हैं पूरो कोनी समझ्यो। ए सगळां सूं मिलता सवाल है:"]),
    "fb_none": V(   # variant 0 is replaced by the existing "rephrase" template (kept for the 2.0 tests)
        en=["", "I couldn't match that to anything I know. You could try one of these:",
            "That one is new to me. Here are some questions I can answer:"],
        hi=["", "मैं इसे किसी जानकारी से नहीं जोड़ पाया। इनमें से कोई सवाल पूछकर देखिए:"],
        hinglish=["", "Main ise kisi jaankari se nahi jod paaya. Inmein se koi sawal poochkar dekhiye:"],
        mr=["", "मला हे कोणत्याही माहितीशी जोडता आले नाही. यापैकी एखादा प्रश्न विचारून पहा:"],
        pa=["", "ਮੈਂ ਇਸ ਨੂੰ ਕਿਸੇ ਜਾਣਕਾਰੀ ਨਾਲ ਨਹੀਂ ਜੋੜ ਸਕਿਆ। ਇਹਨਾਂ ਵਿੱਚੋਂ ਕੋਈ ਸਵਾਲ ਪੁੱਛ ਕੇ ਵੇਖੋ:"],
        raj=["", "म्हैं इणनै किणी जाणकारी सूं कोनी जोड़ सक्यो। इणां में सूं कोई सवाल पूछ नै देखो:"]),
}

# questions to suggest, per topic and language; every one is checked by test_conversation.py to give a real answer
SUGGEST = {
    "groundwater": {"en": ["Is Ajmer Urban safe?", "Top 5 over-exploited blocks in Rajasthan", "What does semi-critical mean?"],
                    "hi": ["जयपुर ज़िले में भूजल की स्थिति क्या है?", "अतिदोहित का मतलब क्या है?"],
                    "hinglish": ["Ajmer Urban ka paani kaisa hai?", "Semi-critical ka matlab kya hai?"],
                    "mr": ["पुणे जिल्ह्यातील भूजल स्थिती काय आहे?", "Semi-critical म्हणजे काय?"],
                    "pa": ["ਲੁਧਿਆਣਾ ਜ਼ਿਲ੍ਹੇ ਵਿੱਚ ਪਾਣੀ ਦੀ ਹਾਲਤ ਕੀ ਹੈ?", "Semi-critical ਦਾ ਮਤਲਬ ਕੀ ਹੈ?"],
                    "raj": ["म्हारो अजमेर जिलो रो पाणी कियां है?", "Semi-critical रो मतलब कांई है?"]},
    "water_quality": {"en": ["What is the drinking-water limit for fluoride?"],
                      "hi": ["फ्लोराइड की पेयजल सीमा क्या है?"], "hinglish": ["Fluoride ki peene ke paani ki limit kya hai?"],
                      "mr": ["फ्लोराइडची पिण्याच्या पाण्याची मर्यादा काय आहे?"],
                      "pa": ["ਫਲੋਰਾਈਡ ਦੀ ਪੀਣ ਵਾਲੇ ਪਾਣੀ ਦੀ ਸੀਮਾ ਕੀ ਹੈ?"],
                      "raj": ["फ्लोराइड री पीवण रा पाणी री सीमा कांई है?"]},
    "soil": {"en": ["What does pH mean in a soil report?"], "hi": ["मिट्टी में pH का मतलब क्या है?"],
             "hinglish": ["Mitti mein pH ka matlab kya hai?"], "mr": ["मातीत pH म्हणजे काय?"],
             "pa": ["ਮਿੱਟੀ ਵਿੱਚ pH ਦਾ ਮਤਲਬ ਕੀ ਹੈ?"], "raj": ["माटी में pH रो मतलब कांई है?"]},
    "crops": {"en": ["How much water does wheat need?"], "hi": ["गेहूं को कितना पानी चाहिए?"],
              "hinglish": ["Gehun ko kitna paani chahiye?"], "mr": ["गव्हाला किती पाणी लागते?"],
              "pa": ["ਕਣਕ ਨੂੰ ਕਿੰਨਾ ਪਾਣੀ ਚਾਹੀਦਾ ਹੈ?"], "raj": ["गेहूं नै कित्तो पाणी चाहीजै?"]},
    "irrigation": {"en": ["Which irrigation method saves water?"], "hi": ["कौन सी सिंचाई विधि पानी बचाती है?"],
                   "hinglish": ["Kaun si sinchai vidhi paani bachati hai?"], "mr": ["कोणती सिंचन पद्धत पाणी वाचवते?"],
                   "pa": ["ਕਿਹੜੀ ਸਿੰਚਾਈ ਵਿਧੀ ਪਾਣੀ ਬਚਾਉਂਦੀ ਹੈ?"], "raj": ["कौन सी सिंचाई विधि पानी बचाती है?"]},
    "land": {"en": ["What is land degradation?"], "hi": ["भूमि क्षरण क्या है?"], "hinglish": ["Land degradation kya hai?"],
             "mr": ["जमिनीची धूप म्हणजे काय?"], "pa": ["ਜ਼ਮੀਨ ਦਾ ਖੋਰ ਕੀ ਹੈ?"], "raj": ["भूमि क्षरण कांई है?"]},
    "app": {"en": ["What can you do?"], "hi": ["आप क्या कर सकते हैं?"], "hinglish": ["Aap kya kar sakte ho?"],
            "mr": ["तुम्ही काय करू शकता?"], "pa": ["ਤੁਸੀਂ ਕੀ ਕਰ ਸਕਦੇ ਹੋ?"], "raj": ["थे कांई कर सको?"]},
}
TOPIC_SUGGEST = {"groundwater": "groundwater", "water_quality": "water_quality", "soil": "soil", "fertilizer": "soil",
                 "crops": "crops", "farming": "crops", "irrigation": "irrigation", "land": "land",
                 "reports": "app", "languages": "app"}
SMALLTALK_SUGGEST = {"ack": True, "greet_time": True, "confused": True, "negative": True, "how_are_you": True,
                     "praise": False, "thanks": False, "bye": False, "identity": False, "laugh": False}


# ================================================================== building replies
def pick(key, lang, seq):
    variants = TEXT[key].get(lang) or TEXT[key]["en"]
    return variants[seq % len(variants)]


def suggestions(topics, lang, limit=3):
    out = []
    for tp in topics:
        group = SUGGEST.get(TOPIC_SUGGEST.get(tp, tp))
        if group:
            for q in group.get(lang) or group["en"]:
                if q not in out:
                    out.append(q)
    if not out:
        g = SUGGEST["groundwater"]
        out = (g.get(lang) or g["en"])[:2]
    app = SUGGEST["app"].get(lang) or SUGGEST["app"]["en"]
    out = out[:limit - 1] + [q for q in app if q not in out]
    return out[:limit]


def _cover(lang):
    return COVERS[lang][0] if lang in COVERS else COVERS["en"][0]


def build(req, lang, seq, rephrase_text, off_topic_text):
    """Reply dict (text, followups, status) for intents smalltalk / scope / off_topic / unclear."""
    intent = req["intent"]
    followups = []
    if intent == "smalltalk":
        kind = req["smalltalk"]
        text = pick("st_" + kind, lang, seq)
        if SMALLTALK_SUGGEST.get(kind):
            followups = suggestions([], lang)
        status = "smalltalk"
    elif intent == "scope":
        verdict, topic = req["verdict"], req.get("topic")
        if verdict == "unknown":
            text = pick("sc_unknown", lang, seq) + " " + _cover(lang)
            followups = suggestions([], lang)
        elif verdict == "no":
            body = pick("tp_" + topic, lang, 0) if topic != "general" else ""
            text = " ".join(x for x in (pick("sc_no", lang, seq), body, _cover(lang)) if x)
            followups = suggestions([], lang)
        else:
            text = pick("sc_partly" if verdict == "partly" else "sc_yes", lang, seq) + " " + pick("tp_" + topic, lang, 0)
            followups = suggestions([topic], lang)
        status = "scope"
    elif intent == "off_topic":
        topic = req.get("oos") or "general"
        if topic == "general":
            text = off_topic_text if seq % 3 == 0 else pick("oos_open", lang, seq) + " " + _cover(lang)
        else:
            text = pick("oos_open", lang, seq) + " " + pick("tp_" + topic, lang, 0) + " " + _cover(lang)
        followups = suggestions([], lang)
        status = "off_topic"
    else:   # unclear
        topics = req.get("cue_topics") or []
        followups = suggestions(topics, lang)
        if topics:
            text = pick("fb_cue", lang, seq)
        else:
            head = pick("fb_none", lang, seq)
            text = head or rephrase_text
        if text != rephrase_text:
            text += "\n" + "\n".join(f"- {q}" for q in followups)
        status = "rephrase"
    return {"text": text, "warnings": [], "table": [], "sources": [], "chart": None, "year": None,
            "followups": followups, "status": status}

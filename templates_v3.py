"""
templates_v3.py - Answer templates added in JalMitra 3.0 (Phase 1).

Every key has all six languages (en, hi, hinglish, mr, pa, raj); the test
suite checks this. Values in {braces} are filled from the database only.
language.py merges this table into TEMPLATES.

Groups:
  dom_*                     names of the domains that have no data yet
  domain_*                  "data unavailable" answers for soil, crop, land, irrigation
  need_home, explain_prev,  conversation memory messages
  lifted_district, which_place, compare_domain_note
  lbl_*                     section labels used by the Detailed answer mode
  limitations, method, reason, missing_domains
"""

TEMPLATES_V3 = {
    # ---------------------------------------------------------------- domains without data
    "dom_soil": {
        "en": "Soil", "hi": "मिट्टी", "hinglish": "Mitti (soil)", "mr": "माती", "pa": "ਮਿੱਟੀ", "raj": "माटी",
    },
    "dom_crop": {
        "en": "Crop suitability", "hi": "फसल उपयुक्तता", "hinglish": "Fasal suitability", "mr": "पीक योग्यता",
        "pa": "ਫ਼ਸਲ ਅਨੁਕੂਲਤਾ", "raj": "फसल जोगता",
    },
    "dom_land": {
        "en": "Land", "hi": "भूमि", "hinglish": "Zameen (land)", "mr": "जमीन", "pa": "ਜ਼ਮੀਨ", "raj": "जमीन",
    },
    "dom_irrigation": {
        "en": "Irrigation advice", "hi": "सिंचाई सलाह", "hinglish": "Sinchai advice", "mr": "सिंचन सल्ला",
        "pa": "ਸਿੰਚਾਈ ਸਲਾਹ", "raj": "सिंचाई सलाह",
    },
    "domain_unavailable": {
        "en": "{domain} data: Data unavailable. JalMitra does not have any such measurements, maps or survey "
              "records yet, so it will not guess. This will be added in a later phase, and only from verified sources.",
        "hi": "{domain} डेटा: डेटा उपलब्ध नहीं है। JalMitra के पास अभी इसका कोई माप, नक्शा या सर्वे रिकॉर्ड "
              "नहीं है, इसलिए वह अंदाज़ा नहीं लगाएगा। यह बाद के चरण में, केवल सत्यापित स्रोतों से जोड़ा जाएगा।",
        "hinglish": "{domain} data: Data available nahi hai. JalMitra ke paas abhi iska koi measurement, map "
                    "ya survey record nahi hai, isliye woh guess nahi karega. Yeh agle phase mein, sirf verified "
                    "sources se joda jayega.",
        "mr": "{domain} डेटा: डेटा उपलब्ध नाही. JalMitra कडे अजून याचे कोणतेही मोजमाप, नकाशा किंवा "
              "सर्वेक्षण नोंद नाही, त्यामुळे तो अंदाज लावणार नाही. हे पुढील टप्प्यात, फक्त सत्यापित स्रोतांमधून जोडले जाईल.",
        "pa": "{domain} ਡਾਟਾ: ਡਾਟਾ ਉਪਲਬਧ ਨਹੀਂ ਹੈ। JalMitra ਕੋਲ ਅਜੇ ਇਸ ਦਾ ਕੋਈ ਮਾਪ, ਨਕਸ਼ਾ ਜਾਂ ਸਰਵੇਖਣ ਰਿਕਾਰਡ "
              "ਨਹੀਂ ਹੈ, ਇਸ ਲਈ ਇਹ ਅੰਦਾਜ਼ਾ ਨਹੀਂ ਲਗਾਏਗਾ। ਇਹ ਅਗਲੇ ਪੜਾਅ ਵਿੱਚ, ਸਿਰਫ਼ ਪ੍ਰਮਾਣਿਤ ਸਰੋਤਾਂ ਤੋਂ ਜੋੜਿਆ ਜਾਵੇਗਾ।",
        "raj": "{domain} डेटा: डेटा उपलब्ध कोनी। JalMitra कनै हाल इणरो कोई माप, नक्शो या सर्वे रिकॉर्ड "
               "कोनी, इण वास्तै बो अंदाजो कोनी लगावैलो। ओ आगला चरण में, फगत सत्यापित स्रोतां सूं जोड़्यो जावैलो।",
    },
    "domain_unavailable_place": {
        "en": "{domain} data for {place}: Data unavailable. JalMitra does not have any such measurements, maps or "
              "survey records yet, so it will not guess. This will be added in a later phase, and only from verified sources.",
        "hi": "{place} के लिए {domain} डेटा: डेटा उपलब्ध नहीं है। JalMitra के पास अभी इसका कोई माप, नक्शा या "
              "सर्वे रिकॉर्ड नहीं है, इसलिए वह अंदाज़ा नहीं लगाएगा। यह बाद के चरण में, केवल सत्यापित स्रोतों से जोड़ा जाएगा।",
        "hinglish": "{place} ke liye {domain} data: Data available nahi hai. JalMitra ke paas abhi iska koi "
                    "measurement, map ya survey record nahi hai, isliye woh guess nahi karega. Yeh agle phase mein, "
                    "sirf verified sources se joda jayega.",
        "mr": "{place} साठी {domain} डेटा: डेटा उपलब्ध नाही. JalMitra कडे अजून याचे कोणतेही मोजमाप, नकाशा "
              "किंवा सर्वेक्षण नोंद नाही, त्यामुळे तो अंदाज लावणार नाही. हे पुढील टप्प्यात, फक्त सत्यापित स्रोतांमधून जोडले जाईल.",
        "pa": "{place} ਲਈ {domain} ਡਾਟਾ: ਡਾਟਾ ਉਪਲਬਧ ਨਹੀਂ ਹੈ। JalMitra ਕੋਲ ਅਜੇ ਇਸ ਦਾ ਕੋਈ ਮਾਪ, ਨਕਸ਼ਾ ਜਾਂ "
              "ਸਰਵੇਖਣ ਰਿਕਾਰਡ ਨਹੀਂ ਹੈ, ਇਸ ਲਈ ਇਹ ਅੰਦਾਜ਼ਾ ਨਹੀਂ ਲਗਾਏਗਾ। ਇਹ ਅਗਲੇ ਪੜਾਅ ਵਿੱਚ, ਸਿਰਫ਼ ਪ੍ਰਮਾਣਿਤ ਸਰੋਤਾਂ ਤੋਂ ਜੋੜਿਆ ਜਾਵੇਗਾ।",
        "raj": "{place} सारू {domain} डेटा: डेटा उपलब्ध कोनी। JalMitra कनै हाल इणरो कोई माप, नक्शो या सर्वे "
               "रिकॉर्ड कोनी, इण वास्तै बो अंदाजो कोनी लगावैलो। ओ आगला चरण में, फगत सत्यापित स्रोतां सूं जोड़्यो जावैलो।",
    },
    "domain_related": {
        "en": "What JalMitra does have for {place} is verified groundwater information:",
        "hi": "{place} के लिए JalMitra के पास सत्यापित भूजल जानकारी है:",
        "hinglish": "{place} ke liye JalMitra ke paas verified groundwater jaankari hai:",
        "mr": "{place} साठी JalMitra कडे सत्यापित भूजल माहिती आहे:",
        "pa": "{place} ਲਈ JalMitra ਕੋਲ ਪ੍ਰਮਾਣਿਤ ਧਰਤੀ ਹੇਠਲੇ ਪਾਣੀ ਦੀ ਜਾਣਕਾਰੀ ਹੈ:",
        "raj": "{place} सारू JalMitra कनै सत्यापित भूजल जाणकारी है:",
    },
    "domain_choose_place": {
        "en": "To see the verified groundwater information for your area, name your block or district, or choose your location in the settings (📍).",
        "hi": "अपने क्षेत्र की सत्यापित भूजल जानकारी देखने के लिए अपने ब्लॉक या ज़िले का नाम बताइए, या सेटिंग में अपना स्थान (📍) चुनिए।",
        "hinglish": "Apne area ki verified groundwater jaankari dekhne ke liye apne block ya district ka naam batayein, ya settings mein apni location (📍) chunein.",
        "mr": "तुमच्या भागाची सत्यापित भूजल माहिती पाहण्यासाठी तुमच्या ब्लॉक किंवा जिल्ह्याचे नाव सांगा, किंवा सेटिंगमध्ये तुमचे ठिकाण (📍) निवडा.",
        "pa": "ਆਪਣੇ ਇਲਾਕੇ ਦੀ ਪ੍ਰਮਾਣਿਤ ਪਾਣੀ ਜਾਣਕਾਰੀ ਵੇਖਣ ਲਈ ਆਪਣੇ ਬਲਾਕ ਜਾਂ ਜ਼ਿਲ੍ਹੇ ਦਾ ਨਾਂ ਦੱਸੋ, ਜਾਂ ਸੈਟਿੰਗ ਵਿੱਚ ਆਪਣੀ ਥਾਂ (📍) ਚੁਣੋ।",
        "raj": "आपरा इलाका री सत्यापित भूजल जाणकारी देखण सारू आपरा ब्लॉक या जिला रो नाम बताओ, या सेटिंग में आपरी जगां (📍) चुणो।",
    },
    # ---------------------------------------------------------------- conversation memory
    "need_home": {
        "en": "Which area do you mean? Please choose your location in the settings (📍), or name your block or district, for example: Is groundwater safe in Ajmer Urban?",
        "hi": "आप कौन-सा क्षेत्र पूछ रहे हैं? कृपया सेटिंग में अपना स्थान (📍) चुनिए, या अपने ब्लॉक या ज़िले का नाम बताइए, जैसे: अजमेर अर्बन में भूजल सुरक्षित है?",
        "hinglish": "Aap kaunsa area pooch rahe hain? Kripya settings mein apni location (📍) chunein, ya apne block ya district ka naam batayein, jaise: Ajmer Urban mein paani safe hai?",
        "mr": "तुम्ही कोणत्या भागाबद्दल विचारत आहात? कृपया सेटिंगमध्ये तुमचे ठिकाण (📍) निवडा, किंवा तुमच्या ब्लॉक किंवा जिल्ह्याचे नाव सांगा, उदा.: पुणे जिल्ह्यातील भूजल सुरक्षित आहे का?",
        "pa": "ਤੁਸੀਂ ਕਿਹੜੇ ਇਲਾਕੇ ਬਾਰੇ ਪੁੱਛ ਰਹੇ ਹੋ? ਕਿਰਪਾ ਕਰਕੇ ਸੈਟਿੰਗ ਵਿੱਚ ਆਪਣੀ ਥਾਂ (📍) ਚੁਣੋ, ਜਾਂ ਆਪਣੇ ਬਲਾਕ ਜਾਂ ਜ਼ਿਲ੍ਹੇ ਦਾ ਨਾਂ ਦੱਸੋ, ਜਿਵੇਂ: ਲੁਧਿਆਣਾ ਵਿੱਚ ਪਾਣੀ ਸੁਰੱਖਿਅਤ ਹੈ?",
        "raj": "थे कुणसो इलाको पूछ रिया हो? सेटिंग में आपरी जगां (📍) चुणो, या आपरा ब्लॉक या जिला रो नाम बताओ, जियां: अजमेर अर्बन में भूजल सुरक्षित है?",
    },
    "explain_prev": {
        "en": "In the previous answer, {place} was {cat}.",
        "hi": "पिछले उत्तर में {place} {cat} था।",
        "hinglish": "Pichhle jawab mein {place} {cat} tha.",
        "mr": "मागील उत्तरात {place} {cat} होते.",
        "pa": "ਪਿਛਲੇ ਜਵਾਬ ਵਿੱਚ {place} {cat} ਸੀ।",
        "raj": "पाछला जवाब में {place} {cat} हो।",
    },
    "lifted_district": {
        "en": "{unit} is an assessment unit (block), so its district {district} is used for this district comparison.",
        "hi": "{unit} एक आकलन इकाई (ब्लॉक) है, इसलिए ज़िलों की इस तुलना में उसका ज़िला {district} लिया गया है।",
        "hinglish": "{unit} ek assessment unit (block) hai, isliye district comparison mein uska district {district} liya gaya hai.",
        "mr": "{unit} हा एक मूल्यांकन घटक (ब्लॉक) आहे, म्हणून या जिल्हा तुलनेत त्याचा जिल्हा {district} घेतला आहे.",
        "pa": "{unit} ਇੱਕ ਮੁਲਾਂਕਣ ਇਕਾਈ (ਬਲਾਕ) ਹੈ, ਇਸ ਲਈ ਜ਼ਿਲ੍ਹਿਆਂ ਦੀ ਇਸ ਤੁਲਨਾ ਵਿੱਚ ਉਸ ਦਾ ਜ਼ਿਲ੍ਹਾ {district} ਲਿਆ ਗਿਆ ਹੈ।",
        "raj": "{unit} एक आकलन इकाई (ब्लॉक) है, इण वास्तै जिलां री इण तुलना में उणरो जिलो {district} लियो है।",
    },
    "which_place": {
        "en": "The last answer was about more than one place. Which one do you mean? Reply with the number:",
        "hi": "पिछला उत्तर एक से अधिक जगहों के बारे में था। आप किसकी बात कर रहे हैं? नंबर लिखकर बताइए:",
        "hinglish": "Pichhla jawab ek se zyada jagah ke baare mein tha. Aap kiski baat kar rahe hain? Number likh kar batayein:",
        "mr": "मागील उत्तर एकापेक्षा जास्त ठिकाणांबद्दल होते. तुम्हाला कोणते म्हणायचे आहे? क्रमांक लिहून सांगा:",
        "pa": "ਪਿਛਲਾ ਜਵਾਬ ਇੱਕ ਤੋਂ ਵੱਧ ਥਾਵਾਂ ਬਾਰੇ ਸੀ। ਤੁਸੀਂ ਕਿਸ ਦੀ ਗੱਲ ਕਰ ਰਹੇ ਹੋ? ਨੰਬਰ ਲਿਖ ਕੇ ਦੱਸੋ:",
        "raj": "पाछलो जवाब एक सूं घणी जगां रै बारै में हो। थे किणरी बात कर रिया हो? नंबर लिख नै बताओ:",
    },
    "compare_domain_note": {
        "en": "{domain} data is not available, so this comparison uses groundwater data.",
        "hi": "{domain} डेटा उपलब्ध नहीं है, इसलिए यह तुलना भूजल डेटा से की गई है।",
        "hinglish": "{domain} data available nahi hai, isliye yeh comparison groundwater data se kiya gaya hai.",
        "mr": "{domain} डेटा उपलब्ध नाही, म्हणून ही तुलना भूजल डेटावर आधारित आहे.",
        "pa": "{domain} ਡਾਟਾ ਉਪਲਬਧ ਨਹੀਂ ਹੈ, ਇਸ ਲਈ ਇਹ ਤੁਲਨਾ ਧਰਤੀ ਹੇਠਲੇ ਪਾਣੀ ਦੇ ਡਾਟੇ ਨਾਲ ਕੀਤੀ ਗਈ ਹੈ।",
        "raj": "{domain} डेटा उपलब्ध कोनी, इण वास्तै आ तुलना भूजल डेटा सूं करी है।",
    },
    # ---------------------------------------------------------------- Detailed mode labels
    "lbl_finding": {
        "en": "Finding (published classification)", "hi": "निष्कर्ष (प्रकाशित वर्गीकरण)",
        "hinglish": "Finding (published classification)", "mr": "निष्कर्ष (प्रकाशित वर्गीकरण)",
        "pa": "ਨਤੀਜਾ (ਪ੍ਰਕਾਸ਼ਿਤ ਵਰਗੀਕਰਨ)", "raj": "नतीजो (प्रकाशित वर्गीकरण)",
    },
    "lbl_data": {
        "en": "Data (published assessment figures)", "hi": "आंकड़े (प्रकाशित आकलन आंकड़े)",
        "hinglish": "Data (published assessment figures)", "mr": "आकडेवारी (प्रकाशित मूल्यांकन आकडे)",
        "pa": "ਅੰਕੜੇ (ਪ੍ਰਕਾਸ਼ਿਤ ਮੁਲਾਂਕਣ ਅੰਕੜੇ)", "raj": "आंकड़ा (प्रकाशित आकलन आंकड़ा)",
    },
    "lbl_meaning": {
        "en": "What it means (interpretation)", "hi": "इसका मतलब (व्याख्या)", "hinglish": "Iska matlab (interpretation)",
        "mr": "याचा अर्थ (विवेचन)", "pa": "ਇਸ ਦਾ ਮਤਲਬ (ਵਿਆਖਿਆ)", "raj": "इणरो मतलब (व्याख्या)",
    },
    "lbl_reason": {
        "en": "Why this category (reasoning)", "hi": "यह श्रेणी क्यों (तर्क)", "hinglish": "Yeh category kyon (reasoning)",
        "mr": "ही श्रेणी का (कारणमीमांसा)", "pa": "ਇਹ ਸ਼੍ਰੇਣੀ ਕਿਉਂ (ਤਰਕ)", "raj": "आ श्रेणी क्यूं (तर्क)",
    },
    "lbl_term": {
        "en": "Key term", "hi": "मुख्य शब्द", "hinglish": "Key term", "mr": "महत्त्वाची संज्ञा", "pa": "ਮੁੱਖ ਸ਼ਬਦ",
        "raj": "मुख्य सबद",
    },
    "lbl_advice": {
        "en": "General advice (not specific to this place)", "hi": "सामान्य सलाह (इस जगह के लिए विशेष नहीं)",
        "hinglish": "General advice (is jagah ke liye specific nahi)", "mr": "सर्वसाधारण सल्ला (या ठिकाणासाठी विशिष्ट नाही)",
        "pa": "ਆਮ ਸਲਾਹ (ਇਸ ਥਾਂ ਲਈ ਖ਼ਾਸ ਨਹੀਂ)", "raj": "सामान्य सलाह (इण जगां सारू खास कोनी)",
    },
    "lbl_missing": {
        "en": "Missing information", "hi": "अनुपलब्ध जानकारी", "hinglish": "Missing information",
        "mr": "उपलब्ध नसलेली माहिती", "pa": "ਗੁੰਮ ਜਾਣਕਾਰੀ", "raj": "जकी जाणकारी कोनी",
    },
    "lbl_limits": {
        "en": "Limitations", "hi": "सीमाएँ", "hinglish": "Limitations", "mr": "मर्यादा", "pa": "ਸੀਮਾਵਾਂ", "raj": "सीमावां",
    },
    "lbl_method": {
        "en": "Method", "hi": "पद्धति", "hinglish": "Method", "mr": "पद्धत", "pa": "ਵਿਧੀ", "raj": "तरीको",
    },
    "lbl_sources": {
        "en": "Sources", "hi": "स्रोत", "hinglish": "Sources", "mr": "स्रोत", "pa": "ਸਰੋਤ", "raj": "स्रोत",
    },
    # ---------------------------------------------------------------- Detailed / Student / Official content
    "limitations": {
        "en": "These are published groundwater resource assessment (GWRA {year}) estimates for a whole assessment unit. "
              "They are not live well readings, and conditions in a single village or farm can differ.",
        "hi": "ये पूरी आकलन इकाई के लिए प्रकाशित भूजल संसाधन आकलन (GWRA {year}) के अनुमान हैं। ये किसी कुएँ की "
              "ताज़ा माप नहीं हैं, और किसी एक गाँव या खेत की स्थिति अलग हो सकती है।",
        "hinglish": "Yeh poori assessment unit ke liye published groundwater resource assessment (GWRA {year}) ke "
                    "estimates hain. Yeh kisi kuen ki live reading nahi hain, aur ek gaon ya khet ki sthiti alag ho sakti hai.",
        "mr": "हे संपूर्ण मूल्यांकन घटकासाठी प्रकाशित भूजल संसाधन मूल्यांकन (GWRA {year}) अंदाज आहेत. ही विहिरीची "
              "थेट मोजणी नाही, आणि एखाद्या गावाची किंवा शेताची स्थिती वेगळी असू शकते.",
        "pa": "ਇਹ ਪੂਰੀ ਮੁਲਾਂਕਣ ਇਕਾਈ ਲਈ ਪ੍ਰਕਾਸ਼ਿਤ ਧਰਤੀ ਹੇਠਲੇ ਪਾਣੀ ਦੇ ਸਰੋਤ ਮੁਲਾਂਕਣ (GWRA {year}) ਦੇ ਅਨੁਮਾਨ ਹਨ। "
              "ਇਹ ਕਿਸੇ ਖੂਹ ਦੀ ਤਾਜ਼ਾ ਮਾਪ ਨਹੀਂ ਹਨ, ਅਤੇ ਕਿਸੇ ਇੱਕ ਪਿੰਡ ਜਾਂ ਖੇਤ ਦੀ ਸਥਿਤੀ ਵੱਖਰੀ ਹੋ ਸਕਦੀ ਹੈ।",
        "raj": "ऐ पूरी आकलन इकाई सारू प्रकाशित भूजल संसाधन आकलन (GWRA {year}) रा अनुमान है। ऐ किणी कुआ री "
               "ताजा माप कोनी, अर किणी एक गांव या खेत री हालत न्यारी हो सकै।",
    },
    "method": {
        "en": "Stage of extraction = annual groundwater extraction ÷ annual extractable groundwater resource × 100. "
              "Units are grouped by this percentage; Saline is a separate class for units where the groundwater is saline.",
        "hi": "दोहन स्तर = वार्षिक भूजल निकासी ÷ वार्षिक निकालने योग्य भूजल संसाधन × 100। इकाइयों को इसी प्रतिशत से "
              "श्रेणियों में रखा जाता है; Saline उन इकाइयों की अलग श्रेणी है जहाँ भूजल खारा है।",
        "hinglish": "Extraction stage = annual groundwater extraction ÷ annual extractable resource × 100. Units isi "
                    "percent se categories mein rakhi jaati hain; Saline un units ki alag category hai jahan groundwater khara hai.",
        "mr": "उपसा टप्पा = वार्षिक भूजल उपसा ÷ वार्षिक उपसा करण्यायोग्य भूजल साठा × 100. घटकांची श्रेणी याच टक्केवारीवरून "
              "ठरते; Saline ही खारे भूजल असलेल्या घटकांसाठी वेगळी श्रेणी आहे.",
        "pa": "ਨਿਕਾਸੀ ਪੱਧਰ = ਸਾਲਾਨਾ ਨਿਕਾਸੀ ÷ ਸਾਲਾਨਾ ਕੱਢਣਯੋਗ ਸਰੋਤ × 100। ਇਕਾਈਆਂ ਨੂੰ ਇਸੇ ਪ੍ਰਤੀਸ਼ਤ ਨਾਲ ਸ਼੍ਰੇਣੀਆਂ ਵਿੱਚ "
              "ਰੱਖਿਆ ਜਾਂਦਾ ਹੈ; Saline ਉਹਨਾਂ ਇਕਾਈਆਂ ਦੀ ਵੱਖਰੀ ਸ਼੍ਰੇਣੀ ਹੈ ਜਿੱਥੇ ਪਾਣੀ ਖਾਰਾ ਹੈ।",
        "raj": "दोहन स्तर = सालाना भूजल निकासी ÷ सालाना काढ़बा जोग संसाधन × 100। इकाइयां नै इणी प्रतिसत सूं श्रेणियां "
               "में राखै; Saline उण इकाइयां री न्यारी श्रेणी है जठै भूजल खारो है।",
    },
    "reason": {
        "en": "The recorded stage of extraction ({stage}%) lies in the band {band}, which the assessment classifies as {cat}.",
        "hi": "दर्ज दोहन स्तर ({stage}%) {band} की सीमा में है, जिसे आकलन में {cat} माना जाता है।",
        "hinglish": "Recorded extraction stage ({stage}%) {band} ki range mein hai, jise assessment mein {cat} mana jata hai.",
        "mr": "नोंदलेला उपसा टप्पा ({stage}%) {band} या मर्यादेत आहे, ज्याला मूल्यांकनात {cat} मानले जाते.",
        "pa": "ਦਰਜ ਨਿਕਾਸੀ ਪੱਧਰ ({stage}%) {band} ਦੀ ਹੱਦ ਵਿੱਚ ਹੈ, ਜਿਸ ਨੂੰ ਮੁਲਾਂਕਣ ਵਿੱਚ {cat} ਮੰਨਿਆ ਜਾਂਦਾ ਹੈ।",
        "raj": "दर्ज दोहन स्तर ({stage}%) {band} री सीमा में है, जिणनै आकलन में {cat} मानै।",
    },
    "missing_domains": {
        "en": "Soil, land and crop-suitability data are not in JalMitra yet (Data unavailable).",
        "hi": "मिट्टी, भूमि और फसल उपयुक्तता का डेटा अभी JalMitra में नहीं है (डेटा उपलब्ध नहीं)।",
        "hinglish": "Mitti, zameen aur fasal suitability ka data abhi JalMitra mein nahi hai (Data available nahi).",
        "mr": "माती, जमीन आणि पीक योग्यतेचा डेटा अजून JalMitra मध्ये नाही (डेटा उपलब्ध नाही).",
        "pa": "ਮਿੱਟੀ, ਜ਼ਮੀਨ ਅਤੇ ਫ਼ਸਲ ਅਨੁਕੂਲਤਾ ਦਾ ਡਾਟਾ ਅਜੇ JalMitra ਵਿੱਚ ਨਹੀਂ ਹੈ (ਡਾਟਾ ਉਪਲਬਧ ਨਹੀਂ)।",
        "raj": "माटी, जमीन अर फसल जोगता रो डेटा हाल JalMitra में कोनी (डेटा उपलब्ध कोनी)।",
    },
}

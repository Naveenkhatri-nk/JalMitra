"""
templates_app.py - Answers to questions about JalMitra itself (intents in app_info.py).

Rules followed in every language:
  * Only features that exist in this build are listed (checked against app.py pages,
    report_builders.py and data/reference/source_catalog.csv).
  * Coverage is stated honestly: detailed groundwater figures exist only for 302 Rajasthan
    blocks; soil, water-quality and crop answers depend on what the user uploads or enters
    and on the reference tables that are loaded.
  * Water is never called "safe to drink"; a water test is compared with published limits only.
  * No yield, profit or overall soil score is promised.
Non-English texts are plain translations of the English text and are listed for native review
in docs/language_review_template.csv.
"""

_FEATURES_EN = (
    "\n- **Groundwater:** the 2025 official category (Safe, Semi-critical, Critical, Over-exploited, Saline) "
    "for 6,762 assessment units across India, with detailed figures (recharge, extraction, stage of extraction) "
    "for 302 Rajasthan blocks. You can also compare places and see district and state summaries."
    "\n- **Soil Health:** upload your Soil Health Card or lab report (PDF, CSV or Excel), check the values, "
    "and get each parameter explained against published reference ranges."
    "\n- **Water Quality:** compare your own water-test results with BIS IS 10500 drinking-water limits and "
    "IS 11624 irrigation guidelines. JalMitra does not certify water as safe to drink; only an accredited "
    "laboratory can do that."
    "\n- **Crops and Irrigation:** crop facts such as water need and salt tolerance (FAO, SKNAU Zone II-A) "
    "and guidance on irrigation methods."
    "\n- **Land Information:** a Land Condition Report that brings together the data available for a place."
    "\n- **Reports:** six downloadable reports: groundwater, soil, land, crop, irrigation and a complete report."
    "\n- **Languages:** English, Hindi, Hinglish, Rajasthani, Punjabi and Marathi."
)
_NOTE_EN = ("\n\n**Important:** answers depend on the datasets loaded in this app. Coverage is not the same for every "
            "place. When a value is missing, JalMitra says \"Not available in the current dataset\" instead of guessing.")

_FEATURES_HI = (
    "\n- **भूजल:** पूरे भारत की 6,762 आकलन इकाइयों की 2025 की आधिकारिक श्रेणी (Safe, Semi-critical, Critical, "
    "Over-exploited, Saline), और राजस्थान के 302 ब्लॉकों के विस्तृत आंकड़े (पुनर्भरण, दोहन, दोहन का स्तर)। "
    "आप जगहों की तुलना और ज़िला व राज्य का सारांश भी देख सकते हैं।"
    "\n- **मिट्टी स्वास्थ्य:** अपना मृदा स्वास्थ्य कार्ड या लैब रिपोर्ट (PDF, CSV या Excel) अपलोड करें, मान जाँचें, "
    "और हर पैरामीटर की प्रकाशित संदर्भ सीमाओं के साथ व्याख्या पाएँ।"
    "\n- **पानी की गुणवत्ता:** अपनी पानी जाँच के नतीजों की तुलना BIS IS 10500 पेयजल सीमाओं और IS 11624 सिंचाई "
    "दिशानिर्देशों से करें। JalMitra पानी को पीने के लिए सुरक्षित घोषित नहीं करता; यह केवल मान्यता प्राप्त प्रयोगशाला कर सकती है।"
    "\n- **फसल और सिंचाई:** फसलों की पानी की ज़रूरत और लवण सहनशीलता जैसी जानकारी (FAO, SKNAU ज़ोन II-A) और "
    "सिंचाई के तरीकों पर मार्गदर्शन।"
    "\n- **भूमि जानकारी:** भूमि स्थिति रिपोर्ट, जिसमें किसी जगह के लिए उपलब्ध डेटा एक साथ मिलता है।"
    "\n- **रिपोर्ट:** छह डाउनलोड करने योग्य रिपोर्ट: भूजल, मिट्टी, भूमि, फसल, सिंचाई और पूरी रिपोर्ट।"
    "\n- **भाषाएँ:** English, हिंदी, Hinglish, राजस्थानी, ਪੰਜਾਬੀ और मराठी।"
)
_NOTE_HI = ("\n\n**ज़रूरी:** जवाब इस ऐप में लोड किए गए डेटासेट पर निर्भर करते हैं। हर जगह का कवरेज एक जैसा नहीं है। "
            "जब कोई मान नहीं होता, तो JalMitra अनुमान लगाने के बजाय \"वर्तमान डेटासेट में उपलब्ध नहीं\" बताता है।")

_FEATURES_HL = (
    "\n- **Groundwater:** poore Bharat ki 6,762 assessment units ki 2025 ki official category (Safe, Semi-critical, "
    "Critical, Over-exploited, Saline), aur Rajasthan ke 302 blocks ke detailed figures (recharge, extraction, "
    "stage of extraction). Jagahon ki tulna aur district/state summary bhi dekh sakte hain."
    "\n- **Soil Health:** apna Soil Health Card ya lab report (PDF, CSV ya Excel) upload kijiye, values check kijiye, "
    "aur har parameter ka matlab published reference ranges ke saath samajhiye."
    "\n- **Water Quality:** apne paani ki jaanch ke results ko BIS IS 10500 peene ke paani ki limits aur IS 11624 "
    "sinchai guidelines se milaiye. JalMitra paani ko peene ke liye safe declare nahi karta; yeh sirf accredited lab kar sakti hai."
    "\n- **Crops aur Irrigation:** fasal ki paani ki zaroorat aur salt tolerance jaisi jaankari (FAO, SKNAU Zone II-A) "
    "aur sinchai ke tareekon par guidance."
    "\n- **Land Information:** Land Condition Report, jismein kisi jagah ka uplabdh data ek saath milta hai."
    "\n- **Reports:** 6 download hone wali reports: groundwater, soil, land, crop, irrigation aur complete report."
    "\n- **Languages:** English, Hindi, Hinglish, Rajasthani, Punjabi aur Marathi."
)
_NOTE_HL = ("\n\n**Zaroori:** jawab is app mein load kiye gaye datasets par depend karte hain. Har jagah ka coverage ek "
            "jaisa nahi hai. Jab koi value nahi hoti, JalMitra andaza lagane ke bajay \"Not available in the current dataset\" batata hai.")

_FEATURES_MR = (
    "\n- **भूजल:** संपूर्ण भारतातील 6,762 मूल्यांकन घटकांची 2025 ची अधिकृत श्रेणी (Safe, Semi-critical, Critical, "
    "Over-exploited, Saline), आणि राजस्थानमधील 302 ब्लॉकचे तपशीलवार आकडे (पुनर्भरण, उपसा, उपशाची पातळी). "
    "ठिकाणांची तुलना आणि जिल्हा व राज्य सारांशही पाहता येतो."
    "\n- **मृदा आरोग्य:** तुमचे मृदा आरोग्य पत्रिका किंवा प्रयोगशाळा अहवाल (PDF, CSV किंवा Excel) अपलोड करा, मूल्ये तपासा, "
    "आणि प्रत्येक घटकाचे प्रकाशित संदर्भ मर्यादांनुसार स्पष्टीकरण मिळवा."
    "\n- **पाण्याची गुणवत्ता:** तुमच्या पाणी तपासणीचे निकाल BIS IS 10500 पिण्याच्या पाण्याच्या मर्यादा आणि IS 11624 "
    "सिंचन मार्गदर्शक तत्त्वांशी तुलना करा. JalMitra पाणी पिण्यास सुरक्षित असल्याचे जाहीर करत नाही; ते फक्त मान्यताप्राप्त प्रयोगशाळा करू शकते."
    "\n- **पिके आणि सिंचन:** पिकांची पाण्याची गरज आणि क्षार सहनशीलता यांसारखी माहिती (FAO, SKNAU झोन II-A) आणि "
    "सिंचन पद्धतींवर मार्गदर्शन."
    "\n- **जमीन माहिती:** जमीन स्थिती अहवाल, ज्यात एखाद्या ठिकाणाचा उपलब्ध डेटा एकत्र मिळतो."
    "\n- **अहवाल:** सहा डाउनलोड करता येणारे अहवाल: भूजल, माती, जमीन, पीक, सिंचन आणि संपूर्ण अहवाल."
    "\n- **भाषा:** English, हिंदी, Hinglish, राजस्थानी, ਪੰਜਾਬੀ आणि मराठी."
)
_NOTE_MR = ("\n\n**महत्त्वाचे:** उत्तरे या ॲपमध्ये लोड केलेल्या डेटासेटवर अवलंबून आहेत. प्रत्येक ठिकाणाचे कव्हरेज सारखे नाही. "
            "एखादे मूल्य नसल्यास JalMitra अंदाज न लावता \"सध्याच्या डेटासेटमध्ये उपलब्ध नाही\" असे सांगते.")

_FEATURES_PA = (
    "\n- **ਧਰਤੀ ਹੇਠਲਾ ਪਾਣੀ:** ਪੂਰੇ ਭਾਰਤ ਦੀਆਂ 6,762 ਮੁਲਾਂਕਣ ਇਕਾਈਆਂ ਦੀ 2025 ਦੀ ਸਰਕਾਰੀ ਸ਼੍ਰੇਣੀ (Safe, Semi-critical, "
    "Critical, Over-exploited, Saline), ਅਤੇ ਰਾਜਸਥਾਨ ਦੇ 302 ਬਲਾਕਾਂ ਦੇ ਵਿਸਤ੍ਰਿਤ ਅੰਕੜੇ (ਰੀਚਾਰਜ, ਕੱਢਿਆ ਪਾਣੀ, ਕੱਢਣ ਦਾ ਪੱਧਰ)। "
    "ਤੁਸੀਂ ਥਾਵਾਂ ਦੀ ਤੁਲਨਾ ਅਤੇ ਜ਼ਿਲ੍ਹਾ ਤੇ ਰਾਜ ਦਾ ਸਾਰ ਵੀ ਵੇਖ ਸਕਦੇ ਹੋ।"
    "\n- **ਮਿੱਟੀ ਦੀ ਸਿਹਤ:** ਆਪਣਾ ਸੋਇਲ ਹੈਲਥ ਕਾਰਡ ਜਾਂ ਲੈਬ ਰਿਪੋਰਟ (PDF, CSV ਜਾਂ Excel) ਅੱਪਲੋਡ ਕਰੋ, ਮੁੱਲ ਜਾਂਚੋ, "
    "ਅਤੇ ਹਰ ਪੈਰਾਮੀਟਰ ਦੀ ਪ੍ਰਕਾਸ਼ਿਤ ਹਵਾਲਾ ਸੀਮਾਵਾਂ ਨਾਲ ਵਿਆਖਿਆ ਪਾਓ।"
    "\n- **ਪਾਣੀ ਦੀ ਗੁਣਵੱਤਾ:** ਆਪਣੀ ਪਾਣੀ ਜਾਂਚ ਦੇ ਨਤੀਜਿਆਂ ਦੀ ਤੁਲਨਾ BIS IS 10500 ਪੀਣ ਵਾਲੇ ਪਾਣੀ ਦੀਆਂ ਸੀਮਾਵਾਂ ਅਤੇ IS 11624 "
    "ਸਿੰਚਾਈ ਹਦਾਇਤਾਂ ਨਾਲ ਕਰੋ। JalMitra ਪਾਣੀ ਨੂੰ ਪੀਣ ਲਈ ਸੁਰੱਖਿਅਤ ਨਹੀਂ ਐਲਾਨਦਾ; ਇਹ ਸਿਰਫ਼ ਮਾਨਤਾ ਪ੍ਰਾਪਤ ਲੈਬ ਕਰ ਸਕਦੀ ਹੈ।"
    "\n- **ਫ਼ਸਲਾਂ ਅਤੇ ਸਿੰਚਾਈ:** ਫ਼ਸਲਾਂ ਦੀ ਪਾਣੀ ਦੀ ਲੋੜ ਅਤੇ ਲੂਣ ਸਹਿਣਸ਼ੀਲਤਾ ਵਰਗੀ ਜਾਣਕਾਰੀ (FAO, SKNAU ਜ਼ੋਨ II-A) ਅਤੇ "
    "ਸਿੰਚਾਈ ਦੇ ਤਰੀਕਿਆਂ ਬਾਰੇ ਸੇਧ।"
    "\n- **ਜ਼ਮੀਨ ਦੀ ਜਾਣਕਾਰੀ:** ਜ਼ਮੀਨ ਦੀ ਹਾਲਤ ਰਿਪੋਰਟ, ਜਿਸ ਵਿੱਚ ਕਿਸੇ ਥਾਂ ਦਾ ਉਪਲਬਧ ਡਾਟਾ ਇਕੱਠਾ ਮਿਲਦਾ ਹੈ।"
    "\n- **ਰਿਪੋਰਟਾਂ:** ਛੇ ਡਾਊਨਲੋਡ ਹੋਣ ਵਾਲੀਆਂ ਰਿਪੋਰਟਾਂ: ਪਾਣੀ, ਮਿੱਟੀ, ਜ਼ਮੀਨ, ਫ਼ਸਲ, ਸਿੰਚਾਈ ਅਤੇ ਪੂਰੀ ਰਿਪੋਰਟ।"
    "\n- **ਭਾਸ਼ਾਵਾਂ:** English, हिंदी, Hinglish, राजस्थानी, ਪੰਜਾਬੀ ਅਤੇ मराठी।"
)
_NOTE_PA = ("\n\n**ਜ਼ਰੂਰੀ:** ਜਵਾਬ ਇਸ ਐਪ ਵਿੱਚ ਲੋਡ ਕੀਤੇ ਡਾਟਾਸੈੱਟਾਂ 'ਤੇ ਨਿਰਭਰ ਕਰਦੇ ਹਨ। ਹਰ ਥਾਂ ਦੀ ਕਵਰੇਜ ਇੱਕੋ ਜਿਹੀ ਨਹੀਂ ਹੈ। "
            "ਜਦੋਂ ਕੋਈ ਮੁੱਲ ਨਹੀਂ ਹੁੰਦਾ, JalMitra ਅੰਦਾਜ਼ਾ ਲਗਾਉਣ ਦੀ ਬਜਾਏ \"ਮੌਜੂਦਾ ਡਾਟਾਸੈੱਟ ਵਿੱਚ ਉਪਲਬਧ ਨਹੀਂ\" ਦੱਸਦਾ ਹੈ।")

_FEATURES_RAJ = (
    "\n- **भूजल:** पूरै भारत री 6,762 आकलन इकाइयां री 2025 री सरकारी श्रेणी (Safe, Semi-critical, Critical, "
    "Over-exploited, Saline), अर राजस्थान रा 302 ब्लॉकां रा पूरा आंकड़ा (पुनर्भरण, दोहन, दोहन रो स्तर)। "
    "थे जगां री तुलना अर जिलै व राज्य रो सार भी देख सको।"
    "\n- **माटी री सेहत:** आपरो मृदा स्वास्थ्य कार्ड या लैब रिपोर्ट (PDF, CSV या Excel) अपलोड करो, मान जांचो, "
    "अर हर पैरामीटर री छपी संदर्भ सीमावां सागै समझ पावो।"
    "\n- **पाणी री गुणवत्ता:** आपरी पाणी जांच रा नतीजा BIS IS 10500 पीवण रा पाणी री सीमावां अर IS 11624 सिंचाई "
    "दिशानिर्देशां सूं मिलावो। JalMitra पाणी नै पीवण सारू सुरक्षित कोनी बतावै; ओ फगत मान्यता वाळी लैब कर सकै।"
    "\n- **फसल अर सिंचाई:** फसलां री पाणी री जरूरत अर खारेपण सहण री जाणकारी (FAO, SKNAU जोन II-A) अर "
    "सिंचाई रा तरीकां माथै मारग दरसण।"
    "\n- **जमीन री जाणकारी:** जमीन री हालत री रिपोर्ट, जिण में किणी जगां रो मिलतो डेटा एक सागै मिलै।"
    "\n- **रिपोर्ट:** छह डाउनलोड होवण वाळी रिपोर्टां: भूजल, माटी, जमीन, फसल, सिंचाई अर पूरी रिपोर्ट।"
    "\n- **भासावां:** English, हिंदी, Hinglish, राजस्थानी, ਪੰਜਾਬੀ अर मराठी।"
)
_NOTE_RAJ = ("\n\n**जरूरी:** जवाब इण ऐप में लोड करियोड़ा डेटासेट माथै टिक्योड़ा है। हर जगां रो कवरेज एक जैड़ो कोनी। "
             "जद कोई मान कोनी हुवै, तो JalMitra अंदाजो लगावण री ठौड़ \"हाल रा डेटासेट में उपलब्ध कोनी\" बतावै।")

TEMPLATES_APP = {
    "app_about": {
        "en": "**JalMitra** is a local, multilingual information assistant for groundwater, soil, water quality, crops "
              "and land. It reads official and published datasets stored with this app and explains them in simple "
              "language. It runs on this computer and does not use any online AI service.\n\n**What you can do here:**"
              + _FEATURES_EN + _NOTE_EN +
              "\n\nTry asking: *Is Ajmer Urban safe?* or *What does semi-critical mean?*",
        "hi": "**JalMitra** भूजल, मिट्टी, पानी की गुणवत्ता, फसल और भूमि के लिए एक स्थानीय, बहुभाषी जानकारी सहायक है। "
              "यह इस ऐप में रखे आधिकारिक और प्रकाशित डेटासेट पढ़ता है और उन्हें आसान भाषा में समझाता है। यह इसी कंप्यूटर पर "
              "चलता है और किसी ऑनलाइन AI सेवा का उपयोग नहीं करता।\n\n**आप यहाँ क्या कर सकते हैं:**"
              + _FEATURES_HI + _NOTE_HI +
              "\n\nपूछकर देखें: *जयपुर ज़िले में भूजल की स्थिति क्या है?* या *Semi-critical का मतलब क्या है?*",
        "hinglish": "**JalMitra** groundwater, mitti, paani ki quality, fasal aur zameen ke liye ek local, multilingual "
                    "jaankari sahayak hai. Yeh is app mein rakhe official aur published datasets padhta hai aur unhe "
                    "aasaan bhasha mein samjhata hai. Yeh isi computer par chalta hai aur kisi online AI service ka use "
                    "nahi karta.\n\n**Aap yahan kya kar sakte hain:**" + _FEATURES_HL + _NOTE_HL +
                    "\n\nPoochkar dekhiye: *Ajmer Urban ka paani kaisa hai?* ya *Semi-critical ka matlab kya hai?*",
        "mr": "**JalMitra** हा भूजल, माती, पाण्याची गुणवत्ता, पिके आणि जमीन यांसाठी स्थानिक, बहुभाषिक माहिती सहाय्यक आहे. "
              "तो या ॲपमध्ये ठेवलेले अधिकृत आणि प्रकाशित डेटासेट वाचतो आणि सोप्या भाषेत समजावतो. तो याच संगणकावर चालतो "
              "आणि कोणतीही ऑनलाइन AI सेवा वापरत नाही.\n\n**तुम्ही इथे काय करू शकता:**" + _FEATURES_MR + _NOTE_MR +
              "\n\nविचारून पहा: *पुणे जिल्ह्यातील भूजल स्थिती काय आहे?*",
        "pa": "**JalMitra** ਧਰਤੀ ਹੇਠਲੇ ਪਾਣੀ, ਮਿੱਟੀ, ਪਾਣੀ ਦੀ ਗੁਣਵੱਤਾ, ਫ਼ਸਲਾਂ ਅਤੇ ਜ਼ਮੀਨ ਲਈ ਇੱਕ ਸਥਾਨਕ, ਬਹੁ-ਭਾਸ਼ੀ ਜਾਣਕਾਰੀ "
              "ਸਹਾਇਕ ਹੈ। ਇਹ ਇਸ ਐਪ ਵਿੱਚ ਰੱਖੇ ਸਰਕਾਰੀ ਅਤੇ ਪ੍ਰਕਾਸ਼ਿਤ ਡਾਟਾਸੈੱਟ ਪੜ੍ਹਦਾ ਹੈ ਅਤੇ ਸੌਖੀ ਭਾਸ਼ਾ ਵਿੱਚ ਸਮਝਾਉਂਦਾ ਹੈ। "
              "ਇਹ ਇਸੇ ਕੰਪਿਊਟਰ 'ਤੇ ਚੱਲਦਾ ਹੈ ਅਤੇ ਕਿਸੇ ਔਨਲਾਈਨ AI ਸੇਵਾ ਦੀ ਵਰਤੋਂ ਨਹੀਂ ਕਰਦਾ।\n\n**ਤੁਸੀਂ ਇੱਥੇ ਕੀ ਕਰ ਸਕਦੇ ਹੋ:**"
              + _FEATURES_PA + _NOTE_PA + "\n\nਪੁੱਛ ਕੇ ਵੇਖੋ: *ਲੁਧਿਆਣਾ ਜ਼ਿਲ੍ਹੇ ਵਿੱਚ ਪਾਣੀ ਦੀ ਹਾਲਤ ਕੀ ਹੈ?*",
        "raj": "**JalMitra** भूजल, माटी, पाणी री गुणवत्ता, फसल अर जमीन सारू एक लोकल, घणी भासावां वाळो जाणकारी सहायक है। "
               "ओ इण ऐप में राख्योड़ा सरकारी अर छप्योड़ा डेटासेट बांचै अर सीधी भासा में समझावै। ओ इणी कंप्यूटर माथै चालै "
               "अर किणी ऑनलाइन AI सेवा रो उपयोग कोनी करै।\n\n**थे अठै कांई कर सको:**" + _FEATURES_RAJ + _NOTE_RAJ +
               "\n\nपूछ नै देखो: *म्हारो अजमेर जिलो रो पाणी कियां है?*",
    },
    "app_can_do": {
        "en": "Here is what JalMitra can do for farmers, students and officials:" + _FEATURES_EN + _NOTE_EN +
              "\n\nTo begin, open **Ask JalMitra** and type a question such as *Is Ajmer Urban safe?*",
        "hi": "JalMitra किसानों, विद्यार्थियों और अधिकारियों के लिए ये काम कर सकता है:" + _FEATURES_HI + _NOTE_HI +
              "\n\nशुरू करने के लिए **JalMitra से पूछें** खोलें और सवाल लिखें, जैसे *जयपुर ज़िले में भूजल की स्थिति क्या है?*",
        "hinglish": "JalMitra kisanon, students aur officials ke liye yeh kaam kar sakta hai:" + _FEATURES_HL + _NOTE_HL +
                    "\n\nShuru karne ke liye **Ask JalMitra** kholiye aur sawal likhiye, jaise *Ajmer Urban ka paani kaisa hai?*",
        "mr": "JalMitra शेतकरी, विद्यार्थी आणि अधिकाऱ्यांसाठी हे करू शकतो:" + _FEATURES_MR + _NOTE_MR +
              "\n\nसुरुवात करण्यासाठी **Ask JalMitra** (JalMitra ला विचारा) उघडा आणि प्रश्न लिहा.",
        "pa": "JalMitra ਕਿਸਾਨਾਂ, ਵਿਦਿਆਰਥੀਆਂ ਅਤੇ ਅਧਿਕਾਰੀਆਂ ਲਈ ਇਹ ਕੰਮ ਕਰ ਸਕਦਾ ਹੈ:" + _FEATURES_PA + _NOTE_PA +
              "\n\nਸ਼ੁਰੂ ਕਰਨ ਲਈ **Ask JalMitra** (JalMitra ਨੂੰ ਪੁੱਛੋ) ਖੋਲ੍ਹੋ ਅਤੇ ਸਵਾਲ ਲਿਖੋ।",
        "raj": "JalMitra करसाणां, विद्यार्थियां अर अधिकारियां सारू ए काम कर सकै:" + _FEATURES_RAJ + _NOTE_RAJ +
               "\n\nसरू करण सारू **Ask JalMitra** (JalMitra सूं पूछो) खोलो अर सवाल लिखो।",
    },
    "app_how_to": {
        "en": "**How to use JalMitra:**"
              "\n1. Pick your language from the sidebar (or leave it on automatic)."
              "\n2. Open **Ask JalMitra** and type or speak a question, for example *Is Ajmer Urban safe?*, "
              "*Top 5 over-exploited blocks in Rajasthan* or *What does semi-critical mean?*"
              "\n3. Use the pages in the sidebar for a guided view: Groundwater Intelligence, Groundwater Quality, Soil "
              "Health, Land Intelligence, Crop Advisor, Irrigation Advisor, Compare Areas."
              "\n4. To check your own soil, open **My Soil Report** and upload your Soil Health Card (PDF, CSV or Excel). "
              "Review the values before they are explained."
              "\n5. Open **My Reports** to download a report."
              "\n6. Open **Data Sources** to see where every figure comes from and which places are covered."
              + _NOTE_EN,
        "hi": "**JalMitra का उपयोग कैसे करें:**"
              "\n1. साइडबार से अपनी भाषा चुनें (या स्वचालित रहने दें)।"
              "\n2. **JalMitra से पूछें** (Ask JalMitra) खोलें और सवाल लिखें या बोलें, जैसे *जयपुर ज़िले में भूजल की स्थिति क्या है?* "
              "या *Semi-critical का मतलब क्या है?*"
              "\n3. साइडबार के पेजों से विषय के अनुसार जानकारी देखें: भूजल, भूजल गुणवत्ता, मिट्टी स्वास्थ्य, भूमि, फसल, सिंचाई, तुलना।"
              "\n4. अपनी मिट्टी जाँचने के लिए **मेरी मिट्टी रिपोर्ट** (My Soil Report) खोलें और मृदा स्वास्थ्य कार्ड (PDF, CSV या Excel) अपलोड करें। "
              "व्याख्या से पहले मान जाँच लें।"
              "\n5. रिपोर्ट डाउनलोड करने के लिए **मेरी रिपोर्टें** (My Reports) खोलें।"
              "\n6. हर आंकड़े का स्रोत और कवरेज देखने के लिए **डेटा स्रोत** (Data Sources) खोलें।" + _NOTE_HI,
        "hinglish": "**JalMitra kaise use karein:**"
                    "\n1. Sidebar se apni bhasha chuniye (ya automatic rehne dijiye)."
                    "\n2. **Ask JalMitra** kholiye aur sawal likhiye ya boliye, jaise *Ajmer Urban ka paani kaisa hai?* "
                    "ya *Semi-critical ka matlab kya hai?*"
                    "\n3. Sidebar ke pages se topic ke hisaab se dekhiye: Groundwater, Groundwater Quality, Soil Health, "
                    "Land, Crop Advisor, Irrigation Advisor, Compare Areas."
                    "\n4. Apni mitti check karne ke liye **My Soil Report** kholiye aur Soil Health Card (PDF, CSV ya Excel) "
                    "upload kijiye. Explanation se pehle values check kar lijiye."
                    "\n5. Report download karne ke liye **My Reports** kholiye."
                    "\n6. Har figure ka source aur coverage dekhne ke liye **Data Sources** kholiye." + _NOTE_HL,
        "mr": "**JalMitra कसे वापरावे:**"
              "\n1. साइडबारमधून तुमची भाषा निवडा (किंवा स्वयंचलित राहू द्या)."
              "\n2. **Ask JalMitra** (JalMitra ला विचारा) उघडा आणि प्रश्न लिहा किंवा बोला."
              "\n3. साइडबारमधील पानांवर विषयानुसार माहिती पहा: भूजल, भूजल गुणवत्ता, मृदा आरोग्य, जमीन, पीक, सिंचन, तुलना."
              "\n4. तुमची माती तपासण्यासाठी **My Soil Report** (माझा माती अहवाल) उघडा आणि मृदा आरोग्य पत्रिका (PDF, CSV किंवा Excel) अपलोड करा. "
              "स्पष्टीकरणापूर्वी मूल्ये तपासा."
              "\n5. अहवाल डाउनलोड करण्यासाठी **My Reports** (माझे अहवाल) उघडा."
              "\n6. प्रत्येक आकड्याचा स्रोत आणि कव्हरेज पाहण्यासाठी **Data Sources** (डेटा स्रोत) उघडा." + _NOTE_MR,
        "pa": "**JalMitra ਕਿਵੇਂ ਵਰਤੀਏ:**"
              "\n1. ਸਾਈਡਬਾਰ ਤੋਂ ਆਪਣੀ ਭਾਸ਼ਾ ਚੁਣੋ (ਜਾਂ ਆਟੋਮੈਟਿਕ ਰਹਿਣ ਦਿਓ)।"
              "\n2. **Ask JalMitra** (JalMitra ਨੂੰ ਪੁੱਛੋ) ਖੋਲ੍ਹੋ ਅਤੇ ਸਵਾਲ ਲਿਖੋ ਜਾਂ ਬੋਲੋ।"
              "\n3. ਸਾਈਡਬਾਰ ਦੇ ਪੰਨਿਆਂ ਤੋਂ ਵਿਸ਼ੇ ਮੁਤਾਬਕ ਵੇਖੋ: ਪਾਣੀ, ਪਾਣੀ ਦੀ ਗੁਣਵੱਤਾ, ਮਿੱਟੀ, ਜ਼ਮੀਨ, ਫ਼ਸਲ, ਸਿੰਚਾਈ, ਤੁਲਨਾ।"
              "\n4. ਆਪਣੀ ਮਿੱਟੀ ਜਾਂਚਣ ਲਈ **My Soil Report** (ਮੇਰੀ ਮਿੱਟੀ ਰਿਪੋਰਟ) ਖੋਲ੍ਹੋ ਅਤੇ ਸੋਇਲ ਹੈਲਥ ਕਾਰਡ (PDF, CSV ਜਾਂ Excel) ਅੱਪਲੋਡ ਕਰੋ। "
              "ਵਿਆਖਿਆ ਤੋਂ ਪਹਿਲਾਂ ਮੁੱਲ ਜਾਂਚ ਲਓ।"
              "\n5. ਰਿਪੋਰਟ ਡਾਊਨਲੋਡ ਕਰਨ ਲਈ **My Reports** (ਮੇਰੀਆਂ ਰਿਪੋਰਟਾਂ) ਖੋਲ੍ਹੋ।"
              "\n6. ਹਰ ਅੰਕੜੇ ਦਾ ਸਰੋਤ ਅਤੇ ਕਵਰੇਜ ਵੇਖਣ ਲਈ **Data Sources** (ਡਾਟਾ ਸਰੋਤ) ਖੋਲ੍ਹੋ।" + _NOTE_PA,
        "raj": "**JalMitra कियां काम में लेवां:**"
               "\n1. साइडबार सूं आपरी भासा चुणो (या अपणै आप रैवण दो)।"
               "\n2. **Ask JalMitra** (JalMitra सूं पूछो) खोलो अर सवाल लिखो या बोलो।"
               "\n3. साइडबार रा पानां सूं विसय रै हिसाब सूं देखो: भूजल, पाणी री गुणवत्ता, माटी, जमीन, फसल, सिंचाई, तुलना।"
               "\n4. आपरी माटी जांचण सारू **My Soil Report** (म्हारी माटी रिपोर्ट) खोलो अर मृदा स्वास्थ्य कार्ड (PDF, CSV या Excel) अपलोड करो। "
               "समझावण सूं पैलां मान जांच लो।"
               "\n5. रिपोर्ट डाउनलोड करण सारू **My Reports** (म्हारी रिपोर्टां) खोलो।"
               "\n6. हर आंकड़ै रो स्रोत अर कवरेज देखण सारू **Data Sources** (डेटा स्रोत) खोलो।" + _NOTE_RAJ,
    },
    "app_help": {
        "en": "I can help with groundwater, soil, water quality, crops, irrigation and land information. "
              "Here are some questions to start with:"
              "\n- *Is Ajmer Urban safe?*"
              "\n- *Top 5 over-exploited blocks in Rajasthan*"
              "\n- *Compare Jaipur district and Jodhpur district*"
              "\n- *What does semi-critical mean?*"
              "\n- *What is the drinking-water limit for fluoride?*"
              "\n- *Which irrigation method saves water?*"
              "\n\nYou can also ask *What is JalMitra?*, *What features are available?* or *How can I use this website?*",
        "hi": "मैं भूजल, मिट्टी, पानी की गुणवत्ता, फसल, सिंचाई और भूमि की जानकारी में मदद कर सकता हूँ। शुरुआत के लिए कुछ सवाल:"
              "\n- *जयपुर ज़िले में भूजल की स्थिति क्या है?*"
              "\n- *राजस्थान के 5 सबसे अतिदोहित ब्लॉक*"
              "\n- *Semi-critical का मतलब क्या है?*"
              "\n- *फ्लोराइड की पेयजल सीमा क्या है?*"
              "\n- *कौन सी सिंचाई विधि पानी बचाती है?*"
              "\n\nआप यह भी पूछ सकते हैं: *JalMitra क्या है?*, *कौन सी सुविधाएँ हैं?* या *इस वेबसाइट का उपयोग कैसे करें?*",
        "hinglish": "Main groundwater, mitti, paani ki quality, fasal, sinchai aur zameen ki jaankari mein madad kar sakta hoon. "
                    "Shuru karne ke liye kuch sawal:"
                    "\n- *Ajmer Urban ka paani kaisa hai?*"
                    "\n- *Rajasthan ke top 5 over-exploited block*"
                    "\n- *Semi-critical ka matlab kya hai?*"
                    "\n- *Fluoride ki peene ke paani ki limit kya hai?*"
                    "\n- *Kaun si sinchai vidhi paani bachati hai?*"
                    "\n\nAap yeh bhi pooch sakte hain: *JalMitra kya hai?*, *Kaun se features hain?* ya *Is website ko kaise use karein?*",
        "mr": "मी भूजल, माती, पाण्याची गुणवत्ता, पिके, सिंचन आणि जमिनीच्या माहितीसाठी मदत करू शकतो. सुरुवातीसाठी काही प्रश्न:"
              "\n- *पुणे जिल्ह्यातील भूजल स्थिती काय आहे?*"
              "\n- *Semi-critical म्हणजे काय?*"
              "\n- *फ्लोराईडची पिण्याच्या पाण्याची मर्यादा काय आहे?*"
              "\n\nतुम्ही हेही विचारू शकता: *JalMitra काय आहे?* किंवा *ही वेबसाइट कशी वापरावी?*",
        "pa": "ਮੈਂ ਧਰਤੀ ਹੇਠਲੇ ਪਾਣੀ, ਮਿੱਟੀ, ਪਾਣੀ ਦੀ ਗੁਣਵੱਤਾ, ਫ਼ਸਲਾਂ, ਸਿੰਚਾਈ ਅਤੇ ਜ਼ਮੀਨ ਦੀ ਜਾਣਕਾਰੀ ਵਿੱਚ ਮਦਦ ਕਰ ਸਕਦਾ ਹਾਂ। "
              "ਸ਼ੁਰੂ ਕਰਨ ਲਈ ਕੁਝ ਸਵਾਲ:"
              "\n- *ਲੁਧਿਆਣਾ ਜ਼ਿਲ੍ਹੇ ਵਿੱਚ ਪਾਣੀ ਦੀ ਹਾਲਤ ਕੀ ਹੈ?*"
              "\n- *Semi-critical ਦਾ ਕੀ ਮਤਲਬ ਹੈ?*"
              "\n- *ਫਲੋਰਾਈਡ ਦੀ ਪੀਣ ਵਾਲੇ ਪਾਣੀ ਦੀ ਸੀਮਾ ਕੀ ਹੈ?*"
              "\n\nਤੁਸੀਂ ਇਹ ਵੀ ਪੁੱਛ ਸਕਦੇ ਹੋ: *JalMitra ਕੀ ਹੈ?* ਜਾਂ *ਇਹ ਵੈੱਬਸਾਈਟ ਕਿਵੇਂ ਵਰਤੀਏ?*",
        "raj": "म्हैं भूजल, माटी, पाणी री गुणवत्ता, फसल, सिंचाई अर जमीन री जाणकारी में मदद कर सकूं। सरू करण सारू थोड़ा सवाल:"
               "\n- *म्हारो अजमेर जिलो रो पाणी कियां है?*"
               "\n- *Semi-critical रो मतलब कांई है?*"
               "\n- *फ्लोराइड री पीवण रा पाणी री सीमा कांई है?*"
               "\n\nथे ओ भी पूछ सको: *JalMitra कांई है?* या *इण वेबसाइट नै कियां काम में लेवां?*",
    },
    "app_features": {
        "en": "**Features available in JalMitra:**" + _FEATURES_EN +
              "\n\n**Pages:** Home, Ask JalMitra, Groundwater Intelligence, Groundwater Quality, Soil Health, Soil Type and "
              "Profile, Land Intelligence, Land Degradation, Crop Advisor, Irrigation Advisor, Geographic Explorer, Compare "
              "Areas, My Soil Report, My Reports, Learning Centre, Data Sources, About JalMitra." + _NOTE_EN,
        "hi": "**JalMitra में उपलब्ध सुविधाएँ:**" + _FEATURES_HI +
              "\n\n**पेज:** होम, JalMitra से पूछें, भूजल जानकारी, भूजल गुणवत्ता, मिट्टी स्वास्थ्य, मिट्टी का प्रकार और प्रोफ़ाइल, "
              "भूमि जानकारी, भूमि क्षरण, फसल सलाहकार, सिंचाई सलाहकार, भौगोलिक एक्सप्लोरर, क्षेत्रों की तुलना, मेरी मिट्टी रिपोर्ट, "
              "मेरी रिपोर्टें, सीखने का केंद्र, डेटा स्रोत, JalMitra के बारे में।" + _NOTE_HI,
        "hinglish": "**JalMitra ke features:**" + _FEATURES_HL +
                    "\n\n**Pages:** Home, Ask JalMitra, Groundwater Intelligence, Groundwater Quality, Soil Health, Soil Type "
                    "and Profile, Land Intelligence, Land Degradation, Crop Advisor, Irrigation Advisor, Geographic Explorer, "
                    "Compare Areas, My Soil Report, My Reports, Learning Centre, Data Sources, About JalMitra." + _NOTE_HL,
        "mr": "**JalMitra मधील सुविधा:**" + _FEATURES_MR + _NOTE_MR,
        "pa": "**JalMitra ਵਿੱਚ ਉਪਲਬਧ ਸਹੂਲਤਾਂ:**" + _FEATURES_PA + _NOTE_PA,
        "raj": "**JalMitra में मिलण वाळी सुविधावां:**" + _FEATURES_RAJ + _NOTE_RAJ,
    },
}

"""
templates_kn.py - Sentence frames for soil, land, crop, irrigation and water-quality answers
(JalMitra 3.0, Phases 2-5), in the six answer languages.

The explanatory CONTENT (parameter meanings, methods, soil types) comes from
data/reference/*.csv and exists in English and Hindi; Marathi and Rajasthani answers
show the Hindi text, Hinglish and Punjabi answers the English text, with a note.
Marathi, Punjabi and Rajasthani frames still need review by native speakers.
"""

TEMPLATES_KN = {
    "k_measured": {"en": "Measured facts", "hi": "मापे गए तथ्य", "hinglish": "Measured facts (naape gaye tathya)",
                   "mr": "मोजलेली तथ्ये", "pa": "ਮਾਪੇ ਗਏ ਤੱਥ", "raj": "मापियोड़ा तथ्य"},
    "k_category": {"en": "Published category", "hi": "प्रकाशित श्रेणी", "hinglish": "Published category",
                   "mr": "प्रकाशित वर्ग", "pa": "ਪ੍ਰਕਾਸ਼ਿਤ ਸ਼੍ਰੇਣੀ", "raj": "छपियोड़ी श्रेणी"},
    "k_regional": {"en": "Published regional description (not field data)", "hi": "प्रकाशित क्षेत्रीय विवरण (खेत का डेटा नहीं)",
                   "hinglish": "Published regional description (khet ka data nahi)",
                   "mr": "प्रकाशित प्रादेशिक वर्णन (शेतातील माहिती नाही)", "pa": "ਪ੍ਰਕਾਸ਼ਿਤ ਖੇਤਰੀ ਵੇਰਵਾ (ਖੇਤ ਦਾ ਡੇਟਾ ਨਹੀਂ)",
                   "raj": "छपियोड़ो क्षेत्र रो विवरण (खेत रो डेटा कोनी)"},
    "k_interpret": {"en": "Scientific interpretation", "hi": "वैज्ञानिक व्याख्या", "hinglish": "Scientific interpretation",
                    "mr": "वैज्ञानिक अर्थ", "pa": "ਵਿਗਿਆਨਕ ਵਿਆਖਿਆ", "raj": "वैज्ञानिक व्याख्या"},
    "k_general": {"en": "General suggestions (educational, not a formal government recommendation)",
                  "hi": "सामान्य सुझाव (शैक्षिक, औपचारिक सरकारी सिफ़ारिश नहीं)",
                  "hinglish": "General suggestions (educational, sarkari sifarish nahi)",
                  "mr": "सामान्य सूचना (शैक्षणिक, अधिकृत सरकारी शिफारस नाही)",
                  "pa": "ਆਮ ਸੁਝਾਅ (ਸਿੱਖਿਆਤਮਕ, ਸਰਕਾਰੀ ਸਿਫ਼ਾਰਸ਼ ਨਹੀਂ)", "raj": "सामान्य सुझाव (सीखण सारू, सरकारी सिफारिस कोनी)"},
    "k_missing": {"en": "Missing information", "hi": "जो जानकारी उपलब्ध नहीं है", "hinglish": "Missing information",
                  "mr": "उपलब्ध नसलेली माहिती", "pa": "ਗੁੰਮ ਜਾਣਕਾਰੀ", "raj": "जकी जाणकारी कोनी"},
    "k_sources": {"en": "Sources", "hi": "स्रोत", "hinglish": "Sources", "mr": "स्रोत", "pa": "ਸਰੋਤ", "raj": "स्रोत"},
    "k_suitability": {"en": "Suitability", "hi": "उपयुक्तता", "hinglish": "Suitability", "mr": "योग्यता", "pa": "ਯੋਗਤਾ",
                      "raj": "उपयुक्तता"},
    "k_content_note": {"en": " ", "hi": " ",
                       "hinglish": "(Yeh vyakhya abhi sirf English aur Hindi mein hai, isliye English mein dikhayi gayi hai.)",
                       "mr": "(हे स्पष्टीकरण सध्या फक्त इंग्रजी आणि हिंदीत आहे, म्हणून हिंदीत दाखवले आहे.)",
                       "pa": "(ਇਹ ਵਿਆਖਿਆ ਹਾਲੇ ਸਿਰਫ਼ ਅੰਗਰੇਜ਼ੀ ਅਤੇ ਹਿੰਦੀ ਵਿੱਚ ਹੈ, ਇਸ ਲਈ ਅੰਗਰੇਜ਼ੀ ਵਿੱਚ ਦਿਖਾਈ ਗਈ ਹੈ।)",
                       "raj": "(आ व्याख्या अबार फगत अंग्रेजी अर हिंदी में है, इण सारू हिंदी में दिखाई है।)"},
    "k_not_in_dataset": {"en": "{what} for {place}: Not available in the current dataset.",
                         "hi": "{place} के लिए {what}: वर्तमान डेटासेट में उपलब्ध नहीं।",
                         "hinglish": "{place} ke liye {what}: current dataset mein available nahi.",
                         "mr": "{place} साठी {what}: सध्याच्या डेटासेटमध्ये उपलब्ध नाही.",
                         "pa": "{place} ਲਈ {what}: ਮੌਜੂਦਾ ਡੇਟਾਸੈੱਟ ਵਿੱਚ ਉਪਲਬਧ ਨਹੀਂ।",
                         "raj": "{place} सारू {what}: अबार रा डेटासेट में कोनी।"},
    "k_not_in_dataset_any": {"en": "{what}: Not available in the current dataset.",
                             "hi": "{what}: वर्तमान डेटासेट में उपलब्ध नहीं।",
                             "hinglish": "{what}: current dataset mein available nahi.",
                             "mr": "{what}: सध्याच्या डेटासेटमध्ये उपलब्ध नाही.",
                             "pa": "{what}: ਮੌਜੂਦਾ ਡੇਟਾਸੈੱਟ ਵਿੱਚ ਉਪਲਬਧ ਨਹੀਂ।",
                             "raj": "{what}: अबार रा डेटासेट में कोनी।"},
    "k_upload": {"en": "Upload your Soil Health Card in “My Soil Report” and JalMitra will explain its values.",
                 "hi": "अपना सॉयल हेल्थ कार्ड “मेरी मिट्टी रिपोर्ट” में अपलोड करें, JalMitra उसके मान समझाएगा।",
                 "hinglish": "Apna Soil Health Card “My Soil Report” mein upload karein, JalMitra uske values samjhayega.",
                 "mr": "तुमचे मृदा आरोग्य पत्रिका “माझा माती अहवाल” मध्ये अपलोड करा, JalMitra त्यातील मूल्ये समजावेल.",
                 "pa": "ਆਪਣਾ ਸੌਇਲ ਹੈਲਥ ਕਾਰਡ “My Soil Report” ਵਿੱਚ ਅਪਲੋਡ ਕਰੋ, JalMitra ਉਸਦੇ ਮੁੱਲ ਸਮਝਾਏਗਾ।",
                 "raj": "थारो सॉयल हेल्थ कार्ड “म्हारी माटी रिपोर्ट” में अपलोड करो, JalMitra उणरा मान समझावैलो।"},
    "k_your_report": {"en": "From your confirmed soil report (sample date: {date}):",
                      "hi": "आपकी पुष्टि की गई मिट्टी रिपोर्ट से (नमूना तिथि: {date}):",
                      "hinglish": "Aapki confirm ki gayi soil report se (sample date: {date}):",
                      "mr": "तुमच्या पुष्टी केलेल्या माती अहवालातून (नमुना दिनांक: {date}):",
                      "pa": "ਤੁਹਾਡੀ ਪੁਸ਼ਟੀ ਕੀਤੀ ਮਿੱਟੀ ਰਿਪੋਰਟ ਤੋਂ (ਨਮੂਨਾ ਮਿਤੀ: {date}):",
                      "raj": "थारी पक्की करियोड़ी माटी रिपोर्ट सूं (नमूना तारीख: {date}):"},
    "k_report_missing_param": {"en": "{param} is not in your confirmed soil report.",
                               "hi": "{param} आपकी पुष्टि की गई मिट्टी रिपोर्ट में नहीं है।",
                               "hinglish": "{param} aapki confirm ki gayi soil report mein nahi hai.",
                               "mr": "{param} तुमच्या पुष्टी केलेल्या माती अहवालात नाही.",
                               "pa": "{param} ਤੁਹਾਡੀ ਪੁਸ਼ਟੀ ਕੀਤੀ ਮਿੱਟੀ ਰਿਪੋਰਟ ਵਿੱਚ ਨਹੀਂ ਹੈ।",
                               "raj": "{param} थारी माटी रिपोर्ट में कोनी।"},
    "k_insufficient": {"en": "{what}: Insufficient data.", "hi": "{what}: अपर्याप्त डेटा।",
                       "hinglish": "{what}: Insufficient data (data kaafi nahi).", "mr": "{what}: अपुरी माहिती.",
                       "pa": "{what}: ਨਾਕਾਫ਼ੀ ਡੇਟਾ।", "raj": "{what}: डेटा पूरो कोनी।"},
    "k_need_crop": {"en": "A suitability class needs a soil test of the field, soil salinity as ECe, irrigation water "
                          "quality, rainfall and temperature, the season and local KVK or agriculture-university advice. "
                          "JalMitra does not rate suitability from a district name alone.",
                    "hi": "उपयुक्तता श्रेणी के लिए खेत की मिट्टी जाँच, ECe के रूप में मिट्टी की लवणता, सिंचाई पानी की गुणवत्ता, "
                          "वर्षा और तापमान, मौसम और स्थानीय KVK या कृषि विश्वविद्यालय की सलाह चाहिए। JalMitra केवल ज़िले के "
                          "नाम से उपयुक्तता तय नहीं करता।",
                    "hinglish": "Suitability class ke liye khet ki soil test, ECe (mitti ki lavanta), sinchai pani ki "
                                "quality, barish aur taapmaan, season aur local KVK ki salah chahiye. JalMitra sirf "
                                "zile ke naam se suitability tay nahi karta.",
                    "mr": "योग्यता वर्गासाठी शेतातील माती चाचणी, ECe स्वरूपात मातीची क्षारता, सिंचनाच्या पाण्याची गुणवत्ता, "
                          "पाऊस आणि तापमान, हंगाम आणि स्थानिक KVK किंवा कृषी विद्यापीठाचा सल्ला लागतो. JalMitra फक्त "
                          "जिल्ह्याच्या नावावरून योग्यता ठरवत नाही.",
                    "pa": "ਯੋਗਤਾ ਸ਼੍ਰੇਣੀ ਲਈ ਖੇਤ ਦੀ ਮਿੱਟੀ ਜਾਂਚ, ECe ਵਜੋਂ ਮਿੱਟੀ ਦੀ ਖਾਰਾਪਣ, ਸਿੰਚਾਈ ਪਾਣੀ ਦੀ ਗੁਣਵੱਤਾ, ਮੀਂਹ ਅਤੇ "
                          "ਤਾਪਮਾਨ, ਮੌਸਮ ਅਤੇ ਸਥਾਨਕ KVK ਦੀ ਸਲਾਹ ਚਾਹੀਦੀ ਹੈ। JalMitra ਸਿਰਫ਼ ਜ਼ਿਲ੍ਹੇ ਦੇ ਨਾਮ ਤੋਂ ਯੋਗਤਾ ਤੈਅ ਨਹੀਂ ਕਰਦਾ।",
                    "raj": "उपयुक्तता सारू खेत री माटी जांच, ECe में माटी रो खारोपण, सिंचाई रै पाणी री गुणवत्ता, बरसात अर "
                           "तापमान, मौसम अर स्थानीय KVK री सलाह चाइजै। JalMitra फगत जिलै रै नाम सूं उपयुक्तता तय कोनी करै।"},
    "k_zone_listed": {"en": "{crop} is named for the {season} season in the published profile of {zone} ({coverage}). "
                            "This is a regional listing, not a rating of your field.",
                      "hi": "{zone} ({coverage}) के प्रकाशित विवरण में {crop} {season} मौसम के लिए लिखी है। यह क्षेत्रीय सूची है, "
                            "आपके खेत की रेटिंग नहीं।",
                      "hinglish": "{zone} ({coverage}) ke published profile mein {crop} {season} season ke liye likhi hai. "
                                  "Yeh regional list hai, aapke khet ki rating nahi.",
                      "mr": "{zone} ({coverage}) च्या प्रकाशित वर्णनात {crop} {season} हंगामासाठी नमूद आहे. ही प्रादेशिक यादी "
                            "आहे, तुमच्या शेताचे मूल्यांकन नाही.",
                      "pa": "{zone} ({coverage}) ਦੇ ਪ੍ਰਕਾਸ਼ਿਤ ਵੇਰਵੇ ਵਿੱਚ {crop} {season} ਮੌਸਮ ਲਈ ਲਿਖੀ ਹੈ। ਇਹ ਖੇਤਰੀ ਸੂਚੀ ਹੈ, "
                            "ਤੁਹਾਡੇ ਖੇਤ ਦੀ ਰੇਟਿੰਗ ਨਹੀਂ।",
                      "raj": "{zone} ({coverage}) रै छपियोड़ा विवरण में {crop} {season} मौसम सारू लिखियोड़ी है। आ क्षेत्र री "
                             "सूची है, थारै खेत री रेटिंग कोनी।"},
    "k_zone_not": {"en": "{crop} is not in the crop list JalMitra holds for {zone}.",
                   "hi": "{zone} की JalMitra वाली फसल सूची में {crop} नहीं है।",
                   "hinglish": "{zone} ki JalMitra wali crop list mein {crop} nahi hai.",
                   "mr": "{zone} साठी JalMitra कडील पीक यादीत {crop} नाही.",
                   "pa": "{zone} ਲਈ JalMitra ਦੀ ਫ਼ਸਲ ਸੂਚੀ ਵਿੱਚ {crop} ਨਹੀਂ ਹੈ।",
                   "raj": "{zone} री JalMitra आळी फसल सूची में {crop} कोनी।"},
    "k_no_zone": {"en": "JalMitra holds no published agro-climatic zone description for {place} yet.",
                  "hi": "{place} के लिए प्रकाशित कृषि-जलवायु क्षेत्र विवरण JalMitra में अभी नहीं है।",
                  "hinglish": "{place} ke liye published agro-climatic zone description JalMitra mein abhi nahi hai.",
                  "mr": "{place} साठी प्रकाशित कृषी-हवामान विभाग वर्णन JalMitra कडे अजून नाही.",
                  "pa": "{place} ਲਈ ਪ੍ਰਕਾਸ਼ਿਤ ਖੇਤੀ-ਜਲਵਾਯੂ ਖੇਤਰ ਵੇਰਵਾ JalMitra ਕੋਲ ਹਾਲੇ ਨਹੀਂ ਹੈ।",
                  "raj": "{place} सारू छपियोड़ो कृषि-जलवायु क्षेत्र विवरण JalMitra कनै अबार कोनी।"},
    "k_salt": {"en": "Salt tolerance (FAO table, soil ECe): {rating}{threshold}.",
               "hi": "लवण सहनशीलता (FAO तालिका, मिट्टी ECe): {rating}{threshold}।",
               "hinglish": "Salt tolerance (FAO table, mitti ECe): {rating}{threshold}.",
               "mr": "क्षार सहनशीलता (FAO तक्ता, माती ECe): {rating}{threshold}.",
               "pa": "ਲੂਣ ਸਹਿਣਸ਼ੀਲਤਾ (FAO ਸਾਰਣੀ, ਮਿੱਟੀ ECe): {rating}{threshold}।",
               "raj": "खारो सहन करण री ताकत (FAO तालिका, माटी ECe): {rating}{threshold}।"},
    "k_salt_threshold": {"en": ", yield starts to fall above {t} dS/m", "hi": ", {t} dS/m से ऊपर उपज घटने लगती है",
                         "hinglish": ", {t} dS/m se upar upaj ghatne lagti hai", "mr": ", {t} dS/m वर उत्पादन घटू लागते",
                         "pa": ", {t} dS/m ਤੋਂ ਉੱਪਰ ਝਾੜ ਘਟਣ ਲੱਗਦਾ ਹੈ", "raj": ", {t} dS/m सूं ऊपर उपज घटण लागै"},
    "k_salt_none": {"en": "Salt tolerance: not in the FAO table JalMitra holds (no substitute crop is used).",
                    "hi": "लवण सहनशीलता: JalMitra की FAO तालिका में नहीं (किसी दूसरी फसल का मान नहीं लिया गया)।",
                    "hinglish": "Salt tolerance: JalMitra ki FAO table mein nahi (kisi doosri fasal ka maan nahi liya).",
                    "mr": "क्षार सहनशीलता: JalMitra कडील FAO तक्त्यात नाही (दुसऱ्या पिकाचे मूल्य वापरलेले नाही).",
                    "pa": "ਲੂਣ ਸਹਿਣਸ਼ੀਲਤਾ: JalMitra ਦੀ FAO ਸਾਰਣੀ ਵਿੱਚ ਨਹੀਂ (ਕਿਸੇ ਹੋਰ ਫ਼ਸਲ ਦਾ ਮੁੱਲ ਨਹੀਂ ਲਿਆ)।",
                    "raj": "खारो सहन करण री ताकत: JalMitra री FAO तालिका में कोनी (दूजी फसल रो मान कोनी लियो)।"},
    "k_water": {"en": "Seasonal water need (FAO rough estimate): {lo}–{hi} mm; drought sensitivity: {sens}.",
                "hi": "पूरे मौसम की पानी की ज़रूरत (FAO मोटा अनुमान): {lo}–{hi} mm; सूखे के प्रति संवेदनशीलता: {sens}।",
                "hinglish": "Poore season ki pani ki zarurat (FAO rough estimate): {lo}–{hi} mm; sookhe ke prati sensitivity: {sens}.",
                "mr": "हंगामातील पाण्याची गरज (FAO ढोबळ अंदाज): {lo}–{hi} mm; दुष्काळ संवेदनशीलता: {sens}.",
                "pa": "ਪੂਰੇ ਮੌਸਮ ਦੀ ਪਾਣੀ ਦੀ ਲੋੜ (FAO ਮੋਟਾ ਅੰਦਾਜ਼ਾ): {lo}–{hi} mm; ਸੋਕੇ ਪ੍ਰਤੀ ਸੰਵੇਦਨਸ਼ੀਲਤਾ: {sens}।",
                "raj": "पूरै मौसम री पाणी री जरूरत (FAO मोटो अंदाजो): {lo}–{hi} mm; सूखै सूं असर: {sens}।"},
    "k_water_none": {"en": "Seasonal water need: not in the FAO table JalMitra holds.",
                     "hi": "मौसम भर की पानी की ज़रूरत: JalMitra की FAO तालिका में नहीं।",
                     "hinglish": "Season bhar ki pani ki zarurat: JalMitra ki FAO table mein nahi.",
                     "mr": "हंगामातील पाण्याची गरज: JalMitra कडील FAO तक्त्यात नाही.",
                     "pa": "ਮੌਸਮ ਦੀ ਪਾਣੀ ਦੀ ਲੋੜ: JalMitra ਦੀ FAO ਸਾਰਣੀ ਵਿੱਚ ਨਹੀਂ।",
                     "raj": "मौसम री पाणी री जरूरत: JalMitra री FAO तालिका में कोनी।"},
    "k_ece_warn": {"en": "FAO thresholds use ECe (saturation extract). A Soil Health Card EC (1:2 or 1:2.5 extract) cannot be "
                         "compared with them directly.",
                   "hi": "FAO सीमाएँ ECe (संतृप्त अर्क) पर हैं। सॉयल हेल्थ कार्ड का EC (1:2 या 1:2.5 घोल) इनसे सीधे नहीं मिलाया जा सकता।",
                   "hinglish": "FAO limits ECe (saturation extract) par hain. Soil Health Card ka EC (1:2 ya 1:2.5) inse seedha "
                               "compare nahi ho sakta.",
                   "mr": "FAO मर्यादा ECe (संपृक्त अर्क) वर आहेत. मृदा आरोग्य पत्रिकेतील EC (1:2 किंवा 1:2.5) थेट तुलना करता येत नाही.",
                   "pa": "FAO ਹੱਦਾਂ ECe (ਸੰਤ੍ਰਿਪਤ ਅਰਕ) ਉੱਤੇ ਹਨ। ਸੌਇਲ ਹੈਲਥ ਕਾਰਡ ਦਾ EC (1:2 ਜਾਂ 1:2.5) ਸਿੱਧਾ ਨਹੀਂ ਮਿਲਾਇਆ ਜਾ ਸਕਦਾ।",
                   "raj": "FAO री सीमा ECe (संतृप्त अर्क) माथै है। सॉयल हेल्थ कार्ड रो EC (1:2 का 1:2.5) सीधो कोनी मिलायो जा सकै।"},
    "k_quantity_not_quality": {
        "en": "The groundwater category (Safe, Semi-critical, Critical, Over-exploited) is about how much water is extracted, "
              "not about chemical quality. A Safe category does not mean the water is safe to drink.",
        "hi": "भूजल श्रेणी (सुरक्षित, अर्ध-गंभीर, गंभीर, अति-दोहित) इस बारे में है कि कितना पानी निकाला जाता है, रासायनिक "
              "गुणवत्ता के बारे में नहीं। “सुरक्षित” श्रेणी का मतलब यह नहीं कि पानी पीने के लिए सुरक्षित है।",
        "hinglish": "Groundwater category (Safe, Semi-critical, Critical, Over-exploited) batati hai ki kitna pani nikala "
                    "ja raha hai, quality nahi. Safe category ka matlab yeh nahi ki pani peene ke liye safe hai.",
        "mr": "भूजल वर्ग (सुरक्षित, अर्ध-गंभीर, गंभीर, अतिशोषित) किती पाणी उपसले जाते याबद्दल आहे, रासायनिक गुणवत्तेबद्दल नाही. "
              "“सुरक्षित” वर्ग म्हणजे पाणी पिण्यास सुरक्षित असे नाही.",
        "pa": "ਭੂਜਲ ਸ਼੍ਰੇਣੀ (ਸੁਰੱਖਿਅਤ, ਅਰਧ-ਗੰਭੀਰ, ਗੰਭੀਰ, ਵੱਧ-ਸ਼ੋਸ਼ਿਤ) ਇਸ ਬਾਰੇ ਹੈ ਕਿ ਕਿੰਨਾ ਪਾਣੀ ਕੱਢਿਆ ਜਾਂਦਾ ਹੈ, ਰਸਾਇਣਕ "
              "ਗੁਣਵੱਤਾ ਬਾਰੇ ਨਹੀਂ। “ਸੁਰੱਖਿਅਤ” ਸ਼੍ਰੇਣੀ ਦਾ ਮਤਲਬ ਇਹ ਨਹੀਂ ਕਿ ਪਾਣੀ ਪੀਣ ਲਈ ਸੁਰੱਖਿਅਤ ਹੈ।",
        "raj": "भूजल श्रेणी (सुरक्षित, अर्ध-गंभीर, गंभीर, अति-दोहित) इण बारै में है कै कितरो पाणी काढ़ीजै, रासायनिक "
               "गुणवत्ता बारै में कोनी। “सुरक्षित” श्रेणी रो मतलब औ कोनी कै पाणी पीवण सारू सुरक्षित है।"},
    "k_wq_test": {"en": "Have the water tested at a NABL-accredited or government laboratory, then enter the results in "
                        "“Groundwater Quality” to compare them with IS 10500.",
                  "hi": "पानी की जाँच NABL-मान्यता प्राप्त या सरकारी प्रयोगशाला में कराएँ, फिर नतीजे “भूजल गुणवत्ता” में डालकर IS 10500 से तुलना करें।",
                  "hinglish": "Pani ki jaanch NABL ya sarkari lab mein karayein, phir results “Groundwater Quality” mein daal kar "
                              "IS 10500 se compare karein.",
                  "mr": "पाण्याची तपासणी NABL मान्यताप्राप्त किंवा सरकारी प्रयोगशाळेत करा, मग निकाल “भूजल गुणवत्ता” मध्ये भरून IS 10500 शी तुलना करा.",
                  "pa": "ਪਾਣੀ ਦੀ ਜਾਂਚ NABL ਜਾਂ ਸਰਕਾਰੀ ਲੈਬ ਵਿੱਚ ਕਰਵਾਓ, ਫਿਰ ਨਤੀਜੇ “Groundwater Quality” ਵਿੱਚ ਪਾ ਕੇ IS 10500 ਨਾਲ ਮਿਲਾਓ।",
                  "raj": "पाणी री जांच NABL का सरकारी प्रयोगशाला में करावो, पछै नतीजा “भूजल गुणवत्ता” में भर'र IS 10500 सूं मिलावो।"},
    "k_limits_head": {"en": "Drinking-water limits (IS 10500:2012):", "hi": "पीने के पानी की सीमाएँ (IS 10500:2012):",
                      "hinglish": "Peene ke pani ki limits (IS 10500:2012):", "mr": "पिण्याच्या पाण्याच्या मर्यादा (IS 10500:2012):",
                      "pa": "ਪੀਣ ਵਾਲੇ ਪਾਣੀ ਦੀਆਂ ਹੱਦਾਂ (IS 10500:2012):", "raj": "पीवण रै पाणी री सीमा (IS 10500:2012):"},
    "k_no_schedule": {"en": "JalMitra does not calculate an irrigation schedule: that needs crop stage, weather, soil and water "
                            "data for your field.",
                      "hi": "JalMitra सिंचाई समय-सारणी नहीं बनाता: इसके लिए आपके खेत की फसल अवस्था, मौसम, मिट्टी और पानी का डेटा चाहिए।",
                      "hinglish": "JalMitra irrigation schedule nahi banata: iske liye aapke khet ki fasal avastha, mausam, "
                                  "mitti aur pani ka data chahiye.",
                      "mr": "JalMitra सिंचन वेळापत्रक काढत नाही: त्यासाठी तुमच्या शेताची पीक अवस्था, हवामान, माती आणि पाणी माहिती लागते.",
                      "pa": "JalMitra ਸਿੰਚਾਈ ਸਮਾਂ-ਸਾਰਣੀ ਨਹੀਂ ਬਣਾਉਂਦਾ: ਇਸ ਲਈ ਤੁਹਾਡੇ ਖੇਤ ਦੀ ਫ਼ਸਲ ਅਵਸਥਾ, ਮੌਸਮ, ਮਿੱਟੀ ਅਤੇ ਪਾਣੀ ਦਾ ਡੇਟਾ ਚਾਹੀਦਾ ਹੈ।",
                      "raj": "JalMitra सिंचाई री समय-सारणी कोनी बणावै: इण सारू थारै खेत री फसल, मौसम, माटी अर पाणी रो डेटा चाइजै।"},
    "k_less_water_head": {"en": "Seasonal crop water need in the FAO table, lowest first (rough estimates for the whole growing "
                                "period; not a recommendation):",
                          "hi": "FAO तालिका में फसलों की मौसमी पानी की ज़रूरत, सबसे कम पहले (पूरे मौसम का मोटा अनुमान; सिफ़ारिश नहीं):",
                          "hinglish": "FAO table mein fasalon ki season bhar ki pani ki zarurat, sabse kam pehle (rough "
                                      "estimate; sifarish nahi):",
                          "mr": "FAO तक्त्यातील पिकांची हंगामी पाण्याची गरज, सर्वात कमी आधी (ढोबळ अंदाज; शिफारस नाही):",
                          "pa": "FAO ਸਾਰਣੀ ਵਿੱਚ ਫ਼ਸਲਾਂ ਦੀ ਮੌਸਮੀ ਪਾਣੀ ਦੀ ਲੋੜ, ਸਭ ਤੋਂ ਘੱਟ ਪਹਿਲਾਂ (ਮੋਟਾ ਅੰਦਾਜ਼ਾ; ਸਿਫ਼ਾਰਸ਼ ਨਹੀਂ):",
                          "raj": "FAO तालिका में फसलां री मौसमी पाणी री जरूरत, सगळां सूं कम पैली (मोटो अंदाजो; सिफारिस कोनी):"},
    "k_cannot_judge_soil": {"en": "JalMitra cannot call a soil good or poor without a soil test of that field.",
                            "hi": "खेत की मिट्टी जाँच के बिना JalMitra मिट्टी को अच्छी या खराब नहीं कह सकता।",
                            "hinglish": "Khet ki soil test ke bina JalMitra mitti ko achhi ya kharab nahi keh sakta.",
                            "mr": "शेताच्या माती चाचणीशिवाय JalMitra माती चांगली किंवा वाईट म्हणू शकत नाही.",
                            "pa": "ਖੇਤ ਦੀ ਮਿੱਟੀ ਜਾਂਚ ਤੋਂ ਬਿਨਾਂ JalMitra ਮਿੱਟੀ ਨੂੰ ਚੰਗੀ ਜਾਂ ਮਾੜੀ ਨਹੀਂ ਕਹਿ ਸਕਦਾ।",
                            "raj": "खेत री माटी जांच बिना JalMitra माटी नै चोखी का माड़ी कोनी कै सकै।"},
    "k_land_cannot": {"en": "JalMitra has no slope, landform, drainage or degradation records for this place yet, so land "
                            "condition cannot be rated.",
                      "hi": "इस जगह के ढलान, भू-आकृति, जल निकासी या भूमि क्षरण के रिकॉर्ड JalMitra में अभी नहीं हैं, इसलिए भूमि की स्थिति की रेटिंग नहीं हो सकती।",
                      "hinglish": "Is jagah ke slope, landform, drainage ya degradation records JalMitra mein abhi nahi hain, "
                                  "isliye land condition ki rating nahi ho sakti.",
                      "mr": "या ठिकाणचे उतार, भूरूप, निचरा किंवा जमीन ऱ्हास नोंदी JalMitra कडे अजून नाहीत, म्हणून जमिनीच्या स्थितीचे मूल्यांकन करता येत नाही.",
                      "pa": "ਇਸ ਥਾਂ ਦੇ ਢਲਾਣ, ਭੂ-ਆਕਾਰ, ਨਿਕਾਸੀ ਜਾਂ ਨਿਘਾਰ ਦੇ ਰਿਕਾਰਡ JalMitra ਕੋਲ ਹਾਲੇ ਨਹੀਂ ਹਨ, ਇਸ ਲਈ ਜ਼ਮੀਨ ਦੀ ਹਾਲਤ ਦੀ ਰੇਟਿੰਗ ਨਹੀਂ ਹੋ ਸਕਦੀ।",
                      "raj": "इण जगां रा ढलान, भू-आकृति, निकासी का भूमि क्षरण रा रिकॉर्ड JalMitra कनै अबार कोनी, इण सारू जमीन री रेटिंग कोनी हो सकै।"},
    "k_no_value_place": {"en": "Values for your own field are not available until you upload a soil test.",
                         "hi": "आपके खेत के मान तब तक उपलब्ध नहीं जब तक आप मिट्टी जाँच अपलोड न करें।",
                         "hinglish": "Aapke khet ke values tab tak available nahi jab tak aap soil test upload na karein.",
                         "mr": "तुम्ही माती चाचणी अपलोड करेपर्यंत तुमच्या शेताची मूल्ये उपलब्ध नाहीत.",
                         "pa": "ਜਦ ਤੱਕ ਤੁਸੀਂ ਮਿੱਟੀ ਜਾਂਚ ਅਪਲੋਡ ਨਹੀਂ ਕਰਦੇ, ਤੁਹਾਡੇ ਖੇਤ ਦੇ ਮੁੱਲ ਉਪਲਬਧ ਨਹੀਂ।",
                         "raj": "जद तांई थे माटी जांच अपलोड नीं करो, थारै खेत रा मान कोनी।"},
    "k_ranges_head": {"en": "Published rating classes:", "hi": "प्रकाशित रेटिंग श्रेणियाँ:", "hinglish": "Published rating classes:",
                      "mr": "प्रकाशित वर्गवारी:", "pa": "ਪ੍ਰਕਾਸ਼ਿਤ ਰੇਟਿੰਗ ਸ਼੍ਰੇਣੀਆਂ:", "raj": "छपियोड़ी रेटिंग श्रेणियां:"},
    "k_soil_types_head": {"en": "Main soil types explained in JalMitra:", "hi": "JalMitra में समझाए गए मुख्य मिट्टी प्रकार:",
                          "hinglish": "JalMitra mein samjhaye gaye mukhya mitti prakar:", "mr": "JalMitra मध्ये समजावलेले मुख्य माती प्रकार:",
                          "pa": "JalMitra ਵਿੱਚ ਸਮਝਾਈਆਂ ਮੁੱਖ ਮਿੱਟੀ ਕਿਸਮਾਂ:", "raj": "JalMitra में समझायोड़ी मुख्य माटी री किस्मां:"},
    "k_what_soil": {"en": "Soil test values", "hi": "मिट्टी जाँच के मान", "hinglish": "Soil test values", "mr": "माती चाचणी मूल्ये",
                    "pa": "ਮਿੱਟੀ ਜਾਂਚ ਮੁੱਲ", "raj": "माटी जांच रा मान"},
    "k_what_soil_type": {"en": "Mapped soil type", "hi": "मानचित्रित मिट्टी प्रकार", "hinglish": "Mapped soil type",
                         "mr": "नकाशावरील माती प्रकार", "pa": "ਨਕਸ਼ੇ ਮੁਤਾਬਕ ਮਿੱਟੀ ਕਿਸਮ", "raj": "नक्सै रो माटी प्रकार"},
    "k_what_wq": {"en": "Measured groundwater quality", "hi": "मापी गई भूजल गुणवत्ता", "hinglish": "Measured groundwater quality",
                  "mr": "मोजलेली भूजल गुणवत्ता", "pa": "ਮਾਪੀ ਗਈ ਭੂਜਲ ਗੁਣਵੱਤਾ", "raj": "मापियोड़ी भूजल गुणवत्ता"},
    "k_what_land": {"en": "Land condition records", "hi": "भूमि स्थिति रिकॉर्ड", "hinglish": "Land condition records",
                    "mr": "जमीन स्थिती नोंदी", "pa": "ਜ਼ਮੀਨੀ ਹਾਲਤ ਰਿਕਾਰਡ", "raj": "जमीन री हालत रा रिकॉर्ड"},
    "k_what_crop": {"en": "Crop suitability for your field", "hi": "आपके खेत के लिए फसल उपयुक्तता",
                    "hinglish": "Aapke khet ke liye crop suitability", "mr": "तुमच्या शेतासाठी पीक योग्यता",
                    "pa": "ਤੁਹਾਡੇ ਖੇਤ ਲਈ ਫ਼ਸਲ ਯੋਗਤਾ", "raj": "थारै खेत सारू फसल उपयुक्तता"},
    "k_what_suit": {"en": "Suitability of {crop}", "hi": "{crop} की उपयुक्तता", "hinglish": "{crop} ki suitability",
                    "mr": "{crop} ची योग्यता", "pa": "{crop} ਦੀ ਯੋਗਤਾ", "raj": "{crop} री उपयुक्तता"},
    "k_season_kharif": {"en": "Kharif", "hi": "खरीफ़", "hinglish": "Kharif", "mr": "खरीप", "pa": "ਸਾਉਣੀ", "raj": "खरीफ"},
    "k_season_rabi": {"en": "Rabi", "hi": "रबी", "hinglish": "Rabi", "mr": "रब्बी", "pa": "ਹਾੜ੍ਹੀ", "raj": "रबी"},
    "k_compare_crops": {"en": "Comparison of {crops} (published facts only):", "hi": "{crops} की तुलना (केवल प्रकाशित तथ्य):",
                        "hinglish": "{crops} ki tulna (sirf published facts):", "mr": "{crops} यांची तुलना (फक्त प्रकाशित तथ्ये):",
                        "pa": "{crops} ਦੀ ਤੁਲਨਾ (ਸਿਰਫ਼ ਪ੍ਰਕਾਸ਼ਿਤ ਤੱਥ):", "raj": "{crops} री तुलना (फगत छपियोड़ा तथ्य):"},
    "k_wq_imported": {"en": "{n} measured quality records for {place} (imported dataset):",
                      "hi": "{place} के {n} मापे गए गुणवत्ता रिकॉर्ड (आयात किया गया डेटासेट):",
                      "hinglish": "{place} ke {n} measured quality records (imported dataset):",
                      "mr": "{place} च्या {n} मोजलेल्या गुणवत्ता नोंदी (आयात केलेला डेटासेट):",
                      "pa": "{place} ਦੇ {n} ਮਾਪੇ ਗੁਣਵੱਤਾ ਰਿਕਾਰਡ (ਆਯਾਤ ਡੇਟਾਸੈੱਟ):",
                      "raj": "{place} रा {n} मापियोड़ा गुणवत्ता रिकॉर्ड (आयात करियोड़ो डेटासेट):"},
    "dom_water_quality": {"en": "Groundwater quality", "hi": "भूजल गुणवत्ता", "hinglish": "Groundwater quality",
                          "mr": "भूजल गुणवत्ता", "pa": "ਭੂਜਲ ਗੁਣਵੱਤਾ", "raj": "भूजल गुणवत्ता"},
    "k_meta_lang": {"en": "Same answer in {language}:", "hi": "वही उत्तर {language} में:", "hinglish": "Wahi jawab {language} mein:",
                    "mr": "तेच उत्तर {language} मध्ये:", "pa": "ਉਹੀ ਜਵਾਬ {language} ਵਿੱਚ:", "raj": "वो ही जवाब {language} में:"},
    "k_meta_more": {"en": "More detail on the previous answer:", "hi": "पिछले उत्तर का विस्तार:",
                    "hinglish": "Pichhle jawab ki zyada detail:", "mr": "मागील उत्तराचा तपशील:", "pa": "ਪਿਛਲੇ ਜਵਾਬ ਦਾ ਵੇਰਵਾ:",
                    "raj": "पैलड़ै जवाब रो विस्तार:"},
    "k_meta_nothing": {"en": "There is no earlier answer in this conversation to repeat. Please ask a question first.",
                       "hi": "इस बातचीत में दोहराने के लिए कोई पिछला उत्तर नहीं है। पहले एक सवाल पूछें।",
                       "hinglish": "Is baatcheet mein dohrane ke liye koi pichhla jawab nahi hai. Pehle ek sawal poochhein.",
                       "mr": "या संभाषणात पुन्हा सांगण्यासाठी आधीचे उत्तर नाही. आधी एक प्रश्न विचारा.",
                       "pa": "ਇਸ ਗੱਲਬਾਤ ਵਿੱਚ ਦੁਹਰਾਉਣ ਲਈ ਕੋਈ ਪਿਛਲਾ ਜਵਾਬ ਨਹੀਂ। ਪਹਿਲਾਂ ਇੱਕ ਸਵਾਲ ਪੁੱਛੋ।",
                       "raj": "इण बातचीत में दोहरावण सारू कोई पैलड़ो जवाब कोनी। पैली एक सवाल पूछो।"},
    "k_place_head": {
        "en": "{domain} data for {place}: Data unavailable. No measurements, maps or survey records for this place are in the "
              "current dataset, so JalMitra will not guess. What it can say from verified reference sources:",
        "hi": "{place} के लिए {domain} डेटा: डेटा उपलब्ध नहीं है। इस जगह का कोई माप, नक्शा या सर्वे रिकॉर्ड वर्तमान डेटासेट में "
              "नहीं है, इसलिए JalMitra अंदाज़ा नहीं लगाएगा। सत्यापित संदर्भ स्रोतों से जो बताया जा सकता है:",
        "hinglish": "{place} ke liye {domain} data: Data available nahi hai. Is jagah ka koi measurement, map ya survey record "
                    "current dataset mein nahi hai, isliye JalMitra guess nahi karega. Verified reference sources se jo bataya "
                    "ja sakta hai:",
        "mr": "{place} साठी {domain} डेटा: डेटा उपलब्ध नाही. या ठिकाणचे कोणतेही मोजमाप, नकाशा किंवा सर्वेक्षण नोंद सध्याच्या "
              "डेटासेटमध्ये नाही, म्हणून JalMitra अंदाज करणार नाही. सत्यापित संदर्भ स्रोतांवरून जे सांगता येते:",
        "pa": "{place} ਲਈ {domain} ਡੇਟਾ: ਡੇਟਾ ਉਪਲਬਧ ਨਹੀਂ ਹੈ। ਇਸ ਥਾਂ ਦਾ ਕੋਈ ਮਾਪ, ਨਕਸ਼ਾ ਜਾਂ ਸਰਵੇ ਰਿਕਾਰਡ ਮੌਜੂਦਾ ਡੇਟਾਸੈੱਟ ਵਿੱਚ "
              "ਨਹੀਂ ਹੈ, ਇਸ ਲਈ JalMitra ਅੰਦਾਜ਼ਾ ਨਹੀਂ ਲਗਾਏਗਾ। ਪ੍ਰਮਾਣਿਤ ਹਵਾਲਾ ਸਰੋਤਾਂ ਤੋਂ ਜੋ ਦੱਸਿਆ ਜਾ ਸਕਦਾ ਹੈ:",
        "raj": "{place} सारू {domain} डेटा: डेटा उपलब्ध कोनी। इण जगां रो कोई माप, नक्सो का सर्वे रिकॉर्ड अबार रा डेटासेट में "
               "कोनी, इण सारू JalMitra अंदाजो कोनी लगावैलो। पक्का संदर्भ स्रोतां सूं जको बतायो जा सकै:"},
}

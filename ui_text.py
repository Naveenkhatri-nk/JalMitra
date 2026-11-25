"""
ui_text.py - Interface text of the JalMitra 3.0 website in English and Hindi.

Answers are produced in six languages by the engine (language.py). The
interface itself (menus, buttons, headings) is available in English and
Hindi. Missing Hindi entries fall back to English (checked by the tests).
"""

UI = {
    # brand
    "tagline": {"en": "Understand Your Land. Improve Your Soil. Manage Your Water.",
                "hi": "अपनी ज़मीन को समझें। अपनी मिट्टी सुधारें। अपने पानी का प्रबंधन करें।"},
    "tagline2": {"en": "Your Land, Your Soil, Your Water — Explained in Your Language.",
                 "hi": "आपकी ज़मीन, आपकी मिट्टी, आपका पानी — आपकी भाषा में।"},
    "welcome": {"en": "Welcome to JalMitra", "hi": "JalMitra में आपका स्वागत है"},
    "welcome_sub": {"en": "Your intelligent assistant for groundwater, soil, land and agriculture.",
                    "hi": "भूजल, मिट्टी, भूमि और खेती के लिए आपका समझदार सहायक।"},
    "welcome_support": {"en": "Ask questions in your own language and understand the condition, potential and "
                              "limitations of your land through verified information.",
                        "hi": "अपनी भाषा में सवाल पूछें और सत्यापित जानकारी से अपनी ज़मीन की स्थिति, संभावना और "
                              "सीमाएँ समझें।"},
    "search_placeholder": {"en": "Ask about your groundwater, soil, land or crops...",
                           "hi": "अपने भूजल, मिट्टी, ज़मीन या फसल के बारे में पूछें..."},
    "ask_button": {"en": "Ask JalMitra", "hi": "JalMitra से पूछें"},
    "speak_button": {"en": "Speak your question", "hi": "बोलकर पूछें"},
    "examples": {"en": "Try a question", "hi": "ये सवाल आज़माएँ"},
    "examples_data": {"en": "Questions JalMitra can answer with data today",
                      "hi": "जिन सवालों के उत्तर आज डेटा से मिलते हैं"},
    # navigation
    "nav_home": {"en": "Home", "hi": "होम"},
    "nav_ask": {"en": "Ask JalMitra", "hi": "JalMitra से पूछें"},
    "nav_gw": {"en": "Groundwater Intelligence", "hi": "भूजल जानकारी"},
    "nav_soil": {"en": "Soil Health", "hi": "मिट्टी स्वास्थ्य"},
    "nav_land": {"en": "Land Intelligence", "hi": "भूमि जानकारी"},
    "nav_crop": {"en": "Crop Suitability", "hi": "फसल उपयुक्तता"},
    "nav_irrigation": {"en": "Irrigation Advisor", "hi": "सिंचाई सलाहकार"},
    "nav_geo": {"en": "Geographic Explorer", "hi": "भौगोलिक एक्सप्लोरर"},
    "nav_compare": {"en": "Compare Locations", "hi": "स्थानों की तुलना"},
    "nav_soilreport": {"en": "My Soil Report", "hi": "मेरी मिट्टी रिपोर्ट"},
    "nav_reports": {"en": "My Reports", "hi": "मेरी रिपोर्टें"},
    "nav_learn": {"en": "Learning Centre", "hi": "सीखने का केंद्र"},
    "nav_about": {"en": "About JalMitra", "hi": "JalMitra के बारे में"},
    "nav_sources": {"en": "Data Sources and Coverage", "hi": "डेटा स्रोत और कवरेज"},
    "sec_main": {"en": "JalMitra", "hi": "JalMitra"},
    "sec_explore": {"en": "Explore", "hi": "जानकारी"},
    "sec_land": {"en": "Your land (coming later)", "hi": "आपकी ज़मीन (बाद में)"},
    "sec_tools": {"en": "Tools", "hi": "साधन"},
    "sec_help": {"en": "Help and data", "hi": "मदद और डेटा"},
    # settings
    "settings": {"en": "Your settings", "hi": "आपकी सेटिंग"},
    "ui_language": {"en": "Interface", "hi": "इंटरफ़ेस"},
    "answer_language": {"en": "Answer language", "hi": "उत्तर की भाषा"},
    "location": {"en": "Your location", "hi": "आपका स्थान"},
    "location_help": {"en": "Chosen by you (no location tracking). Used for questions like 'my block'.",
                      "hi": "आप स्वयं चुनें (कोई लोकेशन ट्रैकिंग नहीं)। 'मेरा ब्लॉक' जैसे सवालों के लिए।"},
    "state": {"en": "State", "hi": "राज्य"},
    "district": {"en": "District", "hi": "ज़िला"},
    "block": {"en": "Block / assessment unit", "hi": "ब्लॉक / आकलन इकाई"},
    "any": {"en": "— not chosen —", "hi": "— नहीं चुना —"},
    "style": {"en": "Explain for", "hi": "किसके लिए समझाएँ"},
    "style_farmer": {"en": "Farmer", "hi": "किसान"},
    "style_official": {"en": "Official", "hi": "अधिकारी"},
    "style_student": {"en": "Student", "hi": "विद्यार्थी"},
    "detail": {"en": "Answer length", "hi": "उत्तर की लंबाई"},
    "detail_short": {"en": "Short", "hi": "छोटा"},
    "detail_standard": {"en": "Standard", "hi": "सामान्य"},
    "detail_detailed": {"en": "Detailed", "hi": "विस्तृत"},
    "voice_mode": {"en": "Voice mode", "hi": "आवाज़ मोड"},
    "voice_lang": {"en": "Voice language", "hi": "आवाज़ की भाषा"},
    "voice_note": {"en": "Uses your browser's speech service (Chrome/Edge). Not yet tested with a real "
                         "microphone. Typing always works.",
                   "hi": "आपके ब्राउज़र की आवाज़ सेवा (Chrome/Edge) का उपयोग। असली माइक्रोफ़ोन से अभी जाँचा नहीं गया। "
                         "टाइप करना हमेशा काम करता है।"},
    "new_chat": {"en": "New conversation", "hi": "नई बातचीत"},
    "engine_status": {"en": "Offline engine: no AI model, no API key, no internet needed for text.",
                      "hi": "ऑफ़लाइन इंजन: कोई AI मॉडल नहीं, कोई API की नहीं, टेक्स्ट के लिए इंटरनेट ज़रूरी नहीं।"},
    # home sections
    "quick_access": {"en": "What would you like to know?", "hi": "आप क्या जानना चाहते हैं?"},
    "open": {"en": "Open", "hi": "खोलें"},
    "card_gw": {"en": "Category, stage of extraction, recharge and sources for your block or district.",
                "hi": "आपके ब्लॉक या ज़िले की श्रेणी, दोहन स्तर, पुनर्भरण और स्रोत।"},
    "card_ask": {"en": "Ask in English, Hindi, Hinglish, Marathi, Punjabi or Rajasthani.",
                 "hi": "अंग्रेज़ी, हिंदी, हिंग्लिश, मराठी, पंजाबी या राजस्थानी में पूछें।"},
    "card_compare": {"en": "Put two blocks, districts or states side by side.",
                     "hi": "दो ब्लॉक, ज़िले या राज्य साथ-साथ देखें।"},
    "card_geo": {"en": "Browse every state and district in the assessment.",
                 "hi": "आकलन के हर राज्य और ज़िले को देखें।"},
    "card_soil": {"en": "Soil data is not in JalMitra yet. See what is planned.",
                  "hi": "मिट्टी का डेटा अभी JalMitra में नहीं है। देखें क्या योजना है।"},
    "card_learn": {"en": "What 'Over-exploited' or 'stage of extraction' means, in simple words.",
                   "hi": "'अतिदोहित' या 'दोहन स्तर' का मतलब, आसान शब्दों में।"},
    "gw_preview": {"en": "Groundwater", "hi": "भूजल"},
    "soil_preview": {"en": "Soil health", "hi": "मिट्टी स्वास्थ्य"},
    "crop_preview": {"en": "Crop suitability", "hi": "फसल उपयुक्तता"},
    "coverage_title": {"en": "What data JalMitra has", "hi": "JalMitra के पास कौन-सा डेटा है"},
    "sources_title": {"en": "Verified sources", "hi": "सत्यापित स्रोत"},
    "help_title": {"en": "How to use JalMitra", "hi": "JalMitra का उपयोग कैसे करें"},
    "help_1": {"en": "Choose your state and district in the sidebar (optional).",
               "hi": "साइडबार में अपना राज्य और ज़िला चुनें (वैकल्पिक)।"},
    "help_2": {"en": "Type or speak your question in your language.",
               "hi": "अपनी भाषा में सवाल लिखें या बोलें।"},
    "help_3": {"en": "Read the answer with its source and year. Ask a follow-up like 'What does it mean?'.",
               "hi": "स्रोत और वर्ष के साथ उत्तर पढ़ें। आगे पूछें, जैसे 'इसका मतलब क्या है?'।"},
    "choose_location_first": {"en": "Choose a location in the sidebar to see its groundwater cards.",
                              "hi": "भूजल कार्ड देखने के लिए साइडबार में स्थान चुनें।"},
    "national_overview": {"en": "All India, assessment units by category", "hi": "पूरे भारत की आकलन इकाइयाँ, श्रेणी अनुसार"},
    # cards and states
    "data_unavailable": {"en": "Data unavailable", "hi": "डेटा उपलब्ध नहीं"},
    "not_in_db": {"en": "No verified data has been added for this yet. JalMitra does not estimate it.",
                  "hi": "इसके लिए अभी कोई सत्यापित डेटा नहीं जोड़ा गया है। JalMitra इसका अनुमान नहीं लगाता।"},
    "coming_phase": {"en": "Planned for a later phase, only from verified sources.",
                     "hi": "बाद के चरण में, केवल सत्यापित स्रोतों से।"},
    "available": {"en": "Available", "hi": "उपलब्ध"},
    "partly": {"en": "Partly available", "hi": "आंशिक रूप से उपलब्ध"},
    "source": {"en": "Source", "hi": "स्रोत"},
    "year": {"en": "Assessment year", "hi": "आकलन वर्ष"},
    "category": {"en": "Category", "hi": "श्रेणी"},
    "stage": {"en": "Stage of extraction", "hi": "दोहन स्तर"},
    "recharge": {"en": "Annual recharge", "hi": "वार्षिक पुनर्भरण"},
    "extractable": {"en": "Extractable resource", "hi": "निकालने योग्य संसाधन"},
    "extraction": {"en": "Total extraction", "hi": "कुल निकासी"},
    "units": {"en": "Assessment units", "hi": "आकलन इकाइयाँ"},
    "units_with_figures": {"en": "Units with figures", "hi": "आंकड़ों वाली इकाइयाँ"},
    "area_total_note": {"en": "Area total from the National Compilation, not a unit figure.",
                        "hi": "राष्ट्रीय संकलन का क्षेत्रीय कुल, इकाई का आंकड़ा नहीं।"},
    "download_csv": {"en": "Download table (CSV)", "hi": "तालिका डाउनलोड करें (CSV)"},
    "download_report": {"en": "Download conversation report", "hi": "बातचीत की रिपोर्ट डाउनलोड करें"},
    "data_table": {"en": "Data from the database", "hi": "डेटाबेस से डेटा"},
    "source_records": {"en": "Source records", "hi": "स्रोत रिकॉर्ड"},
    "empty_cells": {"en": "Empty cells mean the value is not available (never zero).",
                    "hi": "खाली खाने का मतलब है कि मान उपलब्ध नहीं है (शून्य नहीं)।"},
    "chart_note": {"en": "Chart drawn from the published values in the table.",
                   "hi": "चार्ट तालिका के प्रकाशित मानों से बना है।"},
    "answered_in": {"en": "Answered in {ms} ms on this computer", "hi": "इस कंप्यूटर पर {ms} ms में उत्तर"},
    "memory": {"en": "Remembering", "hi": "याद है"},
    "memory_empty": {"en": "Nothing yet. Ask about a block, district or state.",
                     "hi": "अभी कुछ नहीं। किसी ब्लॉक, ज़िले या राज्य के बारे में पूछें।"},
    "followups": {"en": "You can also ask", "hi": "आप यह भी पूछ सकते हैं"},
    "choose_option": {"en": "Choose one", "hi": "एक चुनें"},
    "recent_questions": {"en": "Recent questions", "hi": "हाल के सवाल"},
    "recent_locations": {"en": "Recent places", "hi": "हाल की जगहें"},
    "use_location": {"en": "Use as my location", "hi": "मेरा स्थान बनाएँ"},
    "feedback_thanks": {"en": "Thank you. Your rating was saved on this computer only.",
                        "hi": "धन्यवाद। आपकी रेटिंग केवल इस कंप्यूटर पर सहेजी गई।"},
    "transcript": {"en": "Transcript (you can edit it)", "hi": "लिखा हुआ सवाल (आप बदल सकते हैं)"},
    "ask": {"en": "Ask", "hi": "पूछें"},
    "chat_placeholder": {"en": "Example: Is Ajmer Urban safe? / Ludhiana ka paani kaisa hai?",
                         "hi": "उदाहरण: अजमेर अर्बन में भूजल सुरक्षित है? / जोधपुर ज़िले की स्थिति"},
    "ask_intro": {"en": "Answers come only from the official groundwater assessment database, with source and year.",
                  "hi": "उत्तर केवल आधिकारिक भूजल आकलन डेटाबेस से आते हैं, स्रोत और वर्ष के साथ।"},
    "db_problem": {"en": "Database problem", "hi": "डेटाबेस समस्या"},
    # pages
    "gw_intro": {"en": "Published groundwater assessment for the location chosen in the sidebar.",
                 "hi": "साइडबार में चुने गए स्थान का प्रकाशित भूजल आकलन।"},
    "warnings": {"en": "Data-quality notes", "hi": "डेटा गुणवत्ता नोट"},
    "units_in_area": {"en": "Assessment units in this area", "hi": "इस क्षेत्र की आकलन इकाइयाँ"},
    "summary": {"en": "Summary", "hi": "सारांश"},
    "soil_intro": {"en": "These are the soil properties JalMitra is planned to show. None of them is in the "
                         "database yet, so every card says 'Data unavailable'.",
                   "hi": "ये मिट्टी के गुण JalMitra में दिखाने की योजना है। इनमें से कोई भी अभी डेटाबेस में नहीं है, "
                         "इसलिए हर कार्ड पर 'डेटा उपलब्ध नहीं' लिखा है।"},
    "land_intro": {"en": "Land information (land use, slope, wasteland, terrain) is not in the database yet.",
                   "hi": "भूमि जानकारी (भूमि उपयोग, ढलान, बंजर भूमि, भू-आकृति) अभी डेटाबेस में नहीं है।"},
    "crop_intro": {"en": "Crop suitability needs verified soil, climate and water data. Only groundwater data is "
                         "in JalMitra now, so crop advice is not given.",
                   "hi": "फसल उपयुक्तता के लिए सत्यापित मिट्टी, जलवायु और पानी का डेटा चाहिए। अभी JalMitra में केवल "
                         "भूजल डेटा है, इसलिए फसल सलाह नहीं दी जाती।"},
    "irrigation_intro": {"en": "Irrigation advice is not available yet. The groundwater status of your location, "
                               "which is one input for it, is shown below.",
                         "hi": "सिंचाई सलाह अभी उपलब्ध नहीं है। इसके लिए एक ज़रूरी जानकारी, आपके स्थान की भूजल "
                               "स्थिति, नीचे दिखाई गई है।"},
    "soilreport_intro": {"en": "Entering your Soil Health Card values is planned for Phase 2. Nothing can be "
                               "entered or stored here yet.",
                         "hi": "अपने मृदा स्वास्थ्य कार्ड के मान दर्ज करना चरण 2 में आएगा। अभी यहाँ कुछ दर्ज या सहेजा "
                               "नहीं जा सकता।"},
    "ask_groundwater": {"en": "Ask about groundwater instead", "hi": "इसके बजाय भूजल के बारे में पूछें"},
    "geo_intro": {"en": "Browse the assessment by state and district. A map needs boundary data, which is not in "
                        "the database yet (map: Data unavailable).",
                  "hi": "राज्य और ज़िले के अनुसार आकलन देखें। नक्शे के लिए सीमा डेटा चाहिए, जो अभी डेटाबेस में नहीं है "
                        "(नक्शा: डेटा उपलब्ध नहीं)।"},
    "pick_state": {"en": "Choose a state", "hi": "राज्य चुनें"},
    "pick_district": {"en": "Choose a district (optional)", "hi": "ज़िला चुनें (वैकल्पिक)"},
    "filter_category": {"en": "Show categories", "hi": "श्रेणियाँ दिखाएँ"},
    "districts_in_state": {"en": "Districts by category", "hi": "श्रेणी अनुसार ज़िले"},
    "compare_intro": {"en": "Choose two places. Units are compared with units, areas with areas.",
                      "hi": "दो जगहें चुनें। इकाई की तुलना इकाई से, क्षेत्र की क्षेत्र से होती है।"},
    "place_a": {"en": "First place", "hi": "पहली जगह"},
    "place_b": {"en": "Second place", "hi": "दूसरी जगह"},
    "compare_button": {"en": "Compare", "hi": "तुलना करें"},
    "type_to_search": {"en": "Type to search", "hi": "खोजने के लिए लिखें"},
    "reports_intro": {"en": "Everything asked in this session. Nothing is uploaded; downloads are created in your "
                            "browser from this session.",
                      "hi": "इस सत्र में पूछा गया सब कुछ। कुछ भी अपलोड नहीं होता; डाउनलोड इसी सत्र से बनते हैं।"},
    "no_reports": {"en": "No questions asked yet in this session.", "hi": "इस सत्र में अभी कोई सवाल नहीं पूछा गया।"},
    "glossary": {"en": "Glossary", "hi": "शब्दावली"},
    "how_to_ask": {"en": "Questions you can ask", "hi": "आप ये सवाल पूछ सकते हैं"},
    "about_title": {"en": "About JalMitra", "hi": "JalMitra के बारे में"},
    "sources_intro": {"en": "Every answer is built from these published documents. Pages are cited in each answer.",
                      "hi": "हर उत्तर इन प्रकाशित दस्तावेज़ों से बनता है। हर उत्तर में पृष्ठ दिए जाते हैं।"},
    "domain_coverage": {"en": "Coverage by topic", "hi": "विषय अनुसार कवरेज"},
    "quality_title": {"en": "Data-quality flags and source conflicts (kept, not hidden)",
                      "hi": "डेटा गुणवत्ता फ़्लैग और स्रोतों का विरोधाभास (रखे गए, छिपाए नहीं)"},
    "version": {"en": "JalMitra 3.0 · Phase 1", "hi": "JalMitra 3.0 · चरण 1"},
}

GLOSSARY = {
    "Assessment unit": {
        "en": "The area for which the groundwater assessment is published: a block, taluka, mandal, firka or "
              "watershed, depending on the state.",
        "hi": "वह क्षेत्र जिसके लिए भूजल आकलन प्रकाशित होता है: राज्य के अनुसार ब्लॉक, तालुका, मंडल, फ़िरका या जलग्रहण क्षेत्र।"},
    "Annual recharge": {
        "en": "Water added to groundwater in a year, mostly from rain, canals, tanks and return flow from irrigation.",
        "hi": "एक साल में भूजल में जुड़ने वाला पानी, ज़्यादातर बारिश, नहरों, तालाबों और सिंचाई के लौटते पानी से।"},
    "Extractable resource": {
        "en": "Annual recharge minus the natural discharge that must stay in the ground: the water that can be "
              "taken out in a year.",
        "hi": "वार्षिक पुनर्भरण में से ज़मीन में रहने वाला प्राकृतिक बहाव घटाकर: एक साल में निकाला जा सकने वाला पानी।"},
    "Total extraction": {
        "en": "Groundwater taken out in a year for irrigation, industry and domestic use.",
        "hi": "एक साल में सिंचाई, उद्योग और घरेलू उपयोग के लिए निकाला गया भूजल।"},
    "ham and bcm": {
        "en": "Units of volume. ham = hectare-metre (10,000 cubic metres). bcm = billion cubic metres. "
              "1 bcm = 100,000 ham.",
        "hi": "आयतन की इकाइयाँ। ham = हेक्टेयर-मीटर (10,000 घन मीटर)। bcm = अरब घन मीटर। 1 bcm = 1,00,000 ham।"},
    "GWRA": {
        "en": "Ground Water Resource Assessment, published jointly by the Central Ground Water Board and the "
              "state groundwater departments.",
        "hi": "भूजल संसाधन आकलन, जिसे केंद्रीय भूजल बोर्ड और राज्य भूजल विभाग मिलकर प्रकाशित करते हैं।"},
}

EXAMPLE_QUESTIONS = {
    "en": ["Is groundwater safe in my block?", "What is my soil type?", "Is my land suitable for mustard farming?",
           "Which crops need less water?", "Why is my soil saline?", "How can I improve my soil fertility?"],
    "hi": ["क्या मेरे ब्लॉक में भूजल सुरक्षित है?", "मेरी मिट्टी किस प्रकार की है?",
           "क्या मेरी ज़मीन सरसों की खेती के लिए उपयुक्त है?", "किन फसलों को कम पानी चाहिए?",
           "मेरी मिट्टी खारी क्यों है?", "मैं अपनी मिट्टी की उर्वरता कैसे सुधारूँ?"],
}

DATA_EXAMPLES = {
    "en": ["Is Ajmer Urban safe?", "Top 5 over-exploited blocks in Rajasthan", "Compare Jaipur district and Jodhpur district",
           "What does semi-critical mean?", "Which district has the most over-exploited units?"],
    "hi": ["अजमेर अर्बन की भूजल स्थिति क्या है?", "राजस्थान के 5 सबसे ज़्यादा दोहन वाले ब्लॉक",
           "जयपुर ज़िला और जोधपुर ज़िला की तुलना करें", "अर्ध-गंभीर का मतलब क्या है?", "Ludhiana ka paani kaisa hai?"],
}


def u(key, lang):
    entry = UI[key]
    return entry.get(lang) or entry["en"]


def missing_ui():
    return [(k, "hi") for k, v in UI.items() if not v.get("hi")] + \
        [(k, "hi") for k, v in GLOSSARY.items() if not v.get("hi")]


from ui_text_v3 import UI_V3  # noqa: E402  (JalMitra 3.0 Phases 2-8)

UI.update(UI_V3)

"""
ui_text_v3.py - Interface texts added or changed in JalMitra 3.0 Phases 2-8 (English and Hindi).
Merged into ui_text.UI (entries here replace older ones with the same key).
"""

UI_V3 = {
    # identity (master instruction)
    "product_line": {"en": "YOUR INTELLIGENT LAND, SOIL, WATER AND AGRICULTURE ASSISTANT",
                     "hi": "ज़मीन, मिट्टी, पानी और खेती के लिए आपका समझदार सहायक"},
    "welcome_sub": {"en": "Your intelligent assistant for land, soil, groundwater and agriculture.",
                    "hi": "ज़मीन, मिट्टी, भूजल और खेती के लिए आपका समझदार सहायक।"},
    "welcome_support": {"en": "Explore your natural resources, understand your land and make better-informed agricultural "
                              "decisions using verified data and scientific guidance.",
                        "hi": "अपने प्राकृतिक संसाधनों को जानें, अपनी ज़मीन को समझें और सत्यापित डेटा व वैज्ञानिक "
                              "मार्गदर्शन से खेती के बेहतर निर्णय लें।"},
    "search_placeholder": {"en": "Ask JalMitra about your soil, water, land or crops...",
                           "hi": "अपनी मिट्टी, पानी, ज़मीन या फसल के बारे में JalMitra से पूछें..."},
    "version": {"en": "JalMitra 3.0", "hi": "JalMitra 3.0"},
    # navigation (17 sections)
    "nav_gw": {"en": "Groundwater Intelligence", "hi": "भूजल जानकारी"},
    "nav_gwq": {"en": "Groundwater Quality", "hi": "भूजल गुणवत्ता"},
    "nav_soil": {"en": "Soil Health", "hi": "मिट्टी स्वास्थ्य"},
    "nav_soilprofile": {"en": "Soil Type and Profile", "hi": "मिट्टी का प्रकार और प्रोफ़ाइल"},
    "nav_land": {"en": "Land Intelligence", "hi": "भूमि जानकारी"},
    "nav_landdeg": {"en": "Land Degradation", "hi": "भूमि क्षरण"},
    "nav_crop": {"en": "Crop Advisor", "hi": "फसल सलाहकार"},
    "nav_irrigation": {"en": "Irrigation Advisor", "hi": "सिंचाई सलाहकार"},
    "nav_compare": {"en": "Compare Areas", "hi": "क्षेत्रों की तुलना"},
    "nav_sources": {"en": "Data Sources", "hi": "डेटा स्रोत"},
    "sec_water": {"en": "Water", "hi": "पानी"},
    "sec_land": {"en": "Soil, land and crops", "hi": "मिट्टी, ज़मीन और फसल"},
    "sec_explore": {"en": "Explore", "hi": "खोजें"},
    "sec_tools": {"en": "Your reports", "hi": "आपकी रिपोर्टें"},
    "sec_help": {"en": "Learn and data", "hi": "सीखें और डेटा"},
    # common
    "not_in_dataset": {"en": "Not available in the current dataset", "hi": "वर्तमान डेटासेट में उपलब्ध नहीं"},
    "insufficient": {"en": "Insufficient data", "hi": "अपर्याप्त डेटा"},
    "general_label": {"en": "General educational information, not a formal government recommendation. Pending expert review.",
                      "hi": "सामान्य शैक्षिक जानकारी, औपचारिक सरकारी सिफ़ारिश नहीं। विशेषज्ञ समीक्षा बाकी।"},
    "regional_label": {"en": "Published regional description of the whole zone, not field data.",
                       "hi": "पूरे क्षेत्र का प्रकाशित विवरण, खेत का डेटा नहीं।"},
    "published_classes": {"en": "Published rating classes", "hi": "प्रकाशित रेटिंग श्रेणियाँ"},
    "what_it_means": {"en": "What it means", "hi": "इसका मतलब"},
    "your_value": {"en": "Your value", "hi": "आपका मान"},
    "card_rating": {"en": "Card rating", "hi": "कार्ड की रेटिंग"},
    "source_ratings": {"en": "Rating by source", "hi": "स्रोत अनुसार रेटिंग"},
    "upload_first": {"en": "No confirmed soil report yet. Upload or type your Soil Health Card in “My Soil Report”.",
                     "hi": "अभी कोई पुष्टि की गई मिट्टी रिपोर्ट नहीं है। “मेरी मिट्टी रिपोर्ट” में अपना सॉयल हेल्थ कार्ड अपलोड करें या मान भरें।"},
    "go_soil_report": {"en": "Open My Soil Report", "hi": "मेरी मिट्टी रिपोर्ट खोलें"},
    "home_place_none": {"en": "Choose your location in the settings (📍) to see what is known for your area.",
                        "hi": "अपने क्षेत्र की जानकारी देखने के लिए सेटिंग (📍) में स्थान चुनें।"},
    "download_md": {"en": "Download (Markdown)", "hi": "डाउनलोड (Markdown)"},
    "download_pdf": {"en": "Download PDF (English)", "hi": "PDF डाउनलोड (अंग्रेज़ी)"},
    "pdf_english_only": {"en": "PDF reports are in English (Hindi letters are not shaped correctly by the PDF library); "
                               "use the Markdown download for Hindi.",
                         "hi": "PDF रिपोर्ट अंग्रेज़ी में है (PDF लाइब्रेरी हिंदी अक्षर सही नहीं जोड़ती); हिंदी के लिए Markdown डाउनलोड करें।"},
    # soil health page
    "soil_intro": {"en": "The 12 Soil Health Card parameters explained, and your own card's values rated against published "
                         "charts. JalMitra never gives an overall soil score and never invents values for your field.",
                   "hi": "सॉयल हेल्थ कार्ड के 12 पैरामीटर की व्याख्या, और आपके कार्ड के मान प्रकाशित चार्ट से तुलना। JalMitra कोई "
                         "कुल मिट्टी अंक नहीं देता और आपके खेत के मान कभी नहीं गढ़ता।"},
    "twelve_params": {"en": "The 12 Soil Health Card parameters", "hi": "सॉयल हेल्थ कार्ड के 12 पैरामीटर"},
    "soil_vs_water_ec": {"en": "Soil EC (from a soil-water mix) and groundwater EC (from water) are different measurements "
                               "and are never mixed in JalMitra.",
                         "hi": "मिट्टी का EC (मिट्टी-पानी घोल से) और भूजल का EC (पानी से) अलग माप हैं, JalMitra इन्हें कभी नहीं मिलाता।"},
    "your_card": {"en": "Your confirmed soil report", "hi": "आपकी पुष्टि की गई मिट्टी रिपोर्ट"},
    # soil profile
    "profile_intro": {"en": "Soil type and profile properties of your area. Each value must show where it comes from "
                            "(lab-tested, field-measured, survey-derived, map-derived or estimated).",
                      "hi": "आपके क्षेत्र की मिट्टी का प्रकार और प्रोफ़ाइल गुण। हर मान का स्रोत दिखना चाहिए (प्रयोगशाला, खेत "
                            "माप, सर्वे, मानचित्र या अनुमान)।"},
    "profile_props": {"en": "Measured soil properties", "hi": "मापे गए मिट्टी गुण"},
    "data_origin": {"en": "Data origin", "hi": "डेटा का स्रोत प्रकार"},
    "soil_types": {"en": "Soil types explained", "hi": "मिट्टी के प्रकार"},
    "origin_lab_tested": {"en": "Lab-tested: measured in a laboratory from a sample of the field.",
                          "hi": "प्रयोगशाला जाँच: खेत के नमूने से प्रयोगशाला में मापा गया।"},
    "origin_field_measured": {"en": "Field-measured: measured on site.", "hi": "खेत में माप: मौके पर मापा गया।"},
    "origin_survey_derived": {"en": "Survey-derived: from a soil survey of the area (for example NBSS&LUP).",
                              "hi": "सर्वे आधारित: क्षेत्र के मिट्टी सर्वे से (जैसे NBSS&LUP)।"},
    "origin_map_derived": {"en": "Map-derived: read from a map at a stated scale; not your exact field.",
                           "hi": "मानचित्र आधारित: तय पैमाने के नक्शे से; आपका सटीक खेत नहीं।"},
    "origin_estimated_interpolated": {"en": "Estimated or interpolated: calculated from nearby points; least certain.",
                                      "hi": "अनुमानित: आसपास के बिंदुओं से गणना; सबसे कम निश्चित।"},
    # land
    "land_intro": {"en": "A Land Condition Report for your chosen location. Each section shows verified data or says "
                         "plainly that it is not available. JalMitra makes no legal or engineering claims about land.",
                   "hi": "आपके चुने स्थान की भूमि स्थिति रिपोर्ट। हर भाग में सत्यापित डेटा है या साफ़ लिखा है कि उपलब्ध नहीं। "
                         "JalMitra ज़मीन के बारे में कोई कानूनी या इंजीनियरिंग दावा नहीं करता।"},
    "land_report": {"en": "Land Condition Report", "hi": "भूमि स्थिति रिपोर्ट"},
    "is_land_good": {"en": "Is my land good? (by intended use)", "hi": "क्या मेरी ज़मीन अच्छी है? (उपयोग अनुसार)"},
    "intended_use": {"en": "Intended use", "hi": "इच्छित उपयोग"},
    "land_eval_note": {"en": "A class (Highly suitable … Not suitable) is given only when slope, soil, drainage, water and "
                             "degradation data exist for the place and a documented method applies. None of these are in the "
                             "current dataset, so every use shows “Insufficient data”.",
                       "hi": "श्रेणी (अत्यधिक उपयुक्त … उपयुक्त नहीं) तभी दी जाती है जब जगह का ढलान, मिट्टी, जल निकासी, पानी और "
                             "क्षरण डेटा हो और कोई प्रलेखित विधि लागू हो। वर्तमान डेटासेट में इनमें से कुछ नहीं है, इसलिए हर "
                             "उपयोग पर “अपर्याप्त डेटा” दिखता है।"},
    "landdeg_intro": {"en": "Kinds of land degradation and conservation methods, and what is recorded for your area.",
                      "hi": "भूमि क्षरण के प्रकार, संरक्षण के तरीके, और आपके क्षेत्र के बारे में दर्ज जानकारी।"},
    "degradation_types": {"en": "Kinds of degradation", "hi": "क्षरण के प्रकार"},
    "conservation_methods": {"en": "Conservation methods", "hi": "संरक्षण के तरीके"},
    "records_for_area": {"en": "Records for your area", "hi": "आपके क्षेत्र के रिकॉर्ड"},
    # crop
    "crop_intro": {"en": "Published facts about each crop (zone listing, salt tolerance, water need). A suitability class "
                         "for your field needs field data, so it shows “Insufficient data” until that data exists.",
                   "hi": "हर फसल के प्रकाशित तथ्य (क्षेत्र सूची, लवण सहनशीलता, पानी की ज़रूरत)। आपके खेत की उपयुक्तता के लिए "
                         "खेत का डेटा चाहिए, तब तक “अपर्याप्त डेटा” दिखता है।"},
    "choose_crops": {"en": "Crops to look at", "hi": "कौन-सी फसलें देखें"},
    "ece_input": {"en": "Soil ECe from a lab (saturation extract, dS/m) — optional",
                  "hi": "प्रयोगशाला से मिट्टी का ECe (संतृप्त अर्क, dS/m) — वैकल्पिक"},
    "ece_help": {"en": "Only ECe can be compared with FAO thresholds. Do not enter the 1:2 EC from a Soil Health Card here.",
                 "hi": "केवल ECe की तुलना FAO सीमा से हो सकती है। यहाँ सॉयल हेल्थ कार्ड का 1:2 EC न डालें।"},
    "salinity_factor": {"en": "Salinity factor only (FAO threshold)", "hi": "केवल लवणता कारक (FAO सीमा)"},
    "below_threshold": {"en": "ECe {ece} dS/m is at or below the FAO threshold {t} dS/m for this crop (salinity alone; other "
                              "factors unknown).",
                        "hi": "ECe {ece} dS/m इस फसल की FAO सीमा {t} dS/m तक या उससे कम है (केवल लवणता; बाकी कारक अज्ञात)।"},
    "above_threshold": {"en": "ECe {ece} dS/m is above the FAO threshold {t} dS/m for this crop: FAO expects yield to start "
                              "falling from salinity.",
                        "hi": "ECe {ece} dS/m इस फसल की FAO सीमा {t} dS/m से ज़्यादा है: FAO के अनुसार लवणता से उपज घटने लगती है।"},
    "no_threshold": {"en": "FAO gives no threshold for this crop.", "hi": "FAO इस फसल की सीमा नहीं देता।"},
    "comparison_table": {"en": "Comparison table", "hi": "तुलना तालिका"},
    "zone_crops": {"en": "Crops named in the published zone profile", "hi": "प्रकाशित क्षेत्र विवरण में लिखी फसलें"},
    "water_need_table": {"en": "Seasonal crop water need (FAO rough estimates)", "hi": "फसलों की मौसमी पानी की ज़रूरत (FAO मोटा अनुमान)"},
    # irrigation
    "irr_intro": {"en": "Irrigation methods explained, your area's groundwater category, and a checker for your irrigation "
                        "water test. JalMitra does not calculate an irrigation schedule.",
                  "hi": "सिंचाई के तरीके, आपके क्षेत्र की भूजल श्रेणी, और आपके सिंचाई पानी की जाँच का मिलान। JalMitra सिंचाई "
                        "समय-सारणी नहीं बनाता।"},
    "irr_methods": {"en": "Irrigation and water-saving methods", "hi": "सिंचाई और पानी बचाने के तरीके"},
    "irr_check": {"en": "Check my irrigation water test", "hi": "मेरी सिंचाई पानी जाँच मिलाएँ"},
    "clay_pct": {"en": "Clay in your soil (%) — from a soil test, needed for the EC limit",
                 "hi": "आपकी मिट्टी में चिकनी मिट्टी (%) — मिट्टी जाँच से, EC सीमा के लिए ज़रूरी"},
    "check": {"en": "Check", "hi": "मिलाएँ"},
    # groundwater quality
    "gwq_intro": {"en": "Five different questions about groundwater, kept apart: how much is extracted (category), how deep "
                        "the water is (level), what is dissolved in it (chemical quality), and whether it suits drinking or "
                        "irrigation.",
                  "hi": "भूजल के पाँच अलग सवाल, अलग-अलग: कितना निकाला जाता है (श्रेणी), पानी कितना गहरा है (स्तर), उसमें क्या "
                        "घुला है (रासायनिक गुणवत्ता), और पीने या सिंचाई के लिए उपयुक्त है या नहीं।"},
    "gwq_category": {"en": "Extraction category", "hi": "दोहन श्रेणी"},
    "gwq_level": {"en": "Groundwater level", "hi": "भूजल स्तर"},
    "gwq_chem": {"en": "Chemical quality", "hi": "रासायनिक गुणवत्ता"},
    "gwq_drink": {"en": "Drinking suitability", "hi": "पीने के लिए उपयुक्तता"},
    "gwq_irr": {"en": "Irrigation suitability", "hi": "सिंचाई के लिए उपयुक्तता"},
    "needs_test": {"en": "Needs a laboratory water test", "hi": "प्रयोगशाला जल जाँच चाहिए"},
    "wq_checker": {"en": "Compare my water test with IS 10500", "hi": "मेरी पानी जाँच की IS 10500 से तुलना"},
    "wq_checker_help": {"en": "Type only the values printed on your laboratory report, with their units. Leave others empty.",
                        "hi": "केवल प्रयोगशाला रिपोर्ट पर छपे मान उनकी इकाई के साथ भरें। बाकी खाली छोड़ें।"},
    "standards": {"en": "Published limits", "hi": "प्रकाशित सीमाएँ"},
    "imported_records": {"en": "Imported monitoring records", "hi": "आयात किए गए निगरानी रिकॉर्ड"},
    # soil report
    "sr_intro": {"en": "Upload your Soil Health Card or lab report (PDF, CSV or Excel, up to 5 MB), or type the values. "
                       "You review and correct every value before JalMitra explains it. Your report stays private in this "
                       "session; nothing is sent anywhere.",
                 "hi": "अपना सॉयल हेल्थ कार्ड या प्रयोगशाला रिपोर्ट (PDF, CSV या Excel, 5 MB तक) अपलोड करें, या मान भरें। JalMitra "
                       "के समझाने से पहले आप हर मान जाँचें और सुधारें। आपकी रिपोर्ट इसी सत्र में निजी रहती है; कहीं नहीं भेजी जाती।"},
    "sr_step1": {"en": "1. Upload or type", "hi": "1. अपलोड करें या भरें"},
    "sr_step2": {"en": "2. Review and correct", "hi": "2. जाँचें और सुधारें"},
    "sr_step3": {"en": "3. Confirm details", "hi": "3. विवरण की पुष्टि"},
    "sr_step4": {"en": "4. Your explained report", "hi": "4. आपकी समझाई गई रिपोर्ट"},
    "sr_upload": {"en": "Soil Health Card or lab report", "hi": "सॉयल हेल्थ कार्ड या प्रयोगशाला रिपोर्ट"},
    "sr_type": {"en": "Type the values instead", "hi": "मान स्वयं भरें"},
    "sr_scanned": {"en": "This PDF has no text layer (it is a scanned image). JalMitra does not run OCR, so please type the "
                         "values from the card.",
                   "hi": "इस PDF में टेक्स्ट नहीं है (यह स्कैन की गई छवि है)। JalMitra OCR नहीं करता, कृपया कार्ड से मान स्वयं भरें।"},
    "sr_nothing": {"en": "No soil parameters were recognised in this file. Please type the values.",
                   "hi": "इस फ़ाइल में कोई मिट्टी पैरामीटर नहीं पहचाना गया। कृपया मान स्वयं भरें।"},
    "sr_review_help": {"en": "Check every number and unit against your card. Fix mistakes, delete wrong rows and add missing "
                             "ones. Units must match the card exactly (P or P2O5, K or K2O).",
                       "hi": "हर संख्या और इकाई कार्ड से मिलाएँ। गलती सुधारें, गलत पंक्ति हटाएँ, छूटी जोड़ें। इकाई कार्ड जैसी ही हो "
                             "(P या P2O5, K या K2O)।"},
    "sample_date": {"en": "Sample date", "hi": "नमूना तिथि"},
    "sample_depth": {"en": "Sample depth", "hi": "नमूना गहराई"},
    "sample_location": {"en": "Village / survey number (optional, stays private)",
                        "hi": "गाँव / खसरा नंबर (वैकल्पिक, निजी रहता है)"},
    "lab_name": {"en": "Laboratory (optional)", "hi": "प्रयोगशाला (वैकल्पिक)"},
    "units_checked": {"en": "I have checked the values and units against my card", "hi": "मैंने मान और इकाइयाँ कार्ड से मिला ली हैं"},
    "approve": {"en": "Approve and explain", "hi": "स्वीकार करें और समझाएँ"},
    "edit_again": {"en": "Edit values again", "hi": "मान फिर से बदलें"},
    "delete_report": {"en": "Delete this report", "hi": "यह रिपोर्ट हटाएँ"},
    "save_local": {"en": "Save on this computer", "hi": "इस कंप्यूटर पर सहेजें"},
    "saved_reports": {"en": "Reports saved on this computer", "hi": "इस कंप्यूटर पर सहेजी रिपोर्टें"},
    "load": {"en": "Open", "hi": "खोलें"},
    "deleted": {"en": "Deleted.", "hi": "हटा दी गई।"},
    "saved": {"en": "Saved in user_data/ on this computer only.", "hi": "केवल इसी कंप्यूटर के user_data/ में सहेजी गई।"},
    "privacy_note": {"en": "Private: kept only in this browser session unless you save it on this computer. Never shared "
                           "with other users or sent to any service.",
                     "hi": "निजी: केवल इसी ब्राउज़र सत्र में रहती है जब तक आप इसे इस कंप्यूटर पर न सहेजें। किसी और उपयोगकर्ता या "
                           "सेवा को नहीं भेजी जाती।"},
    # reports
    "report_types": {"en": "Create a report", "hi": "रिपोर्ट बनाएँ"},
    "rep_groundwater": {"en": "Groundwater report", "hi": "भूजल रिपोर्ट"},
    "rep_soil": {"en": "Soil Health report", "hi": "मिट्टी स्वास्थ्य रिपोर्ट"},
    "rep_land": {"en": "Land Condition report", "hi": "भूमि स्थिति रिपोर्ट"},
    "rep_crop": {"en": "Crop Suitability report", "hi": "फसल उपयुक्तता रिपोर्ट"},
    "rep_irrigation": {"en": "Irrigation report", "hi": "सिंचाई रिपोर्ट"},
    "rep_complete": {"en": "Complete report", "hi": "पूरी रिपोर्ट"},
    "chat_report": {"en": "This conversation", "hi": "यह बातचीत"},
    # explorer
    "no_geometry": {"en": "No boundary maps have been added, so areas are shown as tables. JalMitra never invents "
                          "coordinates. Official boundary files (GeoJSON) placed in data/geo/ are drawn here.",
                    "hi": "कोई सीमा नक्शा नहीं जोड़ा गया है, इसलिए क्षेत्र तालिका में दिखते हैं। JalMitra कभी निर्देशांक नहीं गढ़ता। "
                          "data/geo/ में रखी आधिकारिक सीमा फ़ाइलें (GeoJSON) यहाँ दिखेंगी।"},
    "map_layer": {"en": "Boundary layer", "hi": "सीमा परत"},
    # sources
    "catalog": {"en": "Source catalogue and access status", "hi": "स्रोत सूची और पहुँच स्थिति"},
    "access_requests": {"en": "Datasets that need naveen's action (download, permission or upload)",
                        "hi": "जिन डेटासेट के लिए कार्रवाई चाहिए (डाउनलोड, अनुमति या अपलोड)"},
    "observations": {"en": "Imported measurement tables", "hi": "आयात की गई माप तालिकाएँ"},
    "rows": {"en": "rows", "hi": "पंक्तियाँ"},
    # learning centre
    "learn_soil": {"en": "Soil parameters", "hi": "मिट्टी के पैरामीटर"},
    "learn_water": {"en": "Water quality parameters", "hi": "पानी की गुणवत्ता के पैरामीटर"},
    "learn_land": {"en": "Land degradation and conservation", "hi": "भूमि क्षरण और संरक्षण"},
    "learn_irrigation": {"en": "Irrigation methods", "hi": "सिंचाई के तरीके"},
    "learn_crops": {"en": "Crops: water need and salt tolerance", "hi": "फसलें: पानी की ज़रूरत और लवण सहनशीलता"},
    "learn_gw": {"en": "Groundwater categories", "hi": "भूजल श्रेणियाँ"},
    "cited_from": {"en": "Source", "hi": "स्रोत"},
    # home cards
    "card_soil": {"en": "The 12 Soil Health Card parameters explained, and your own card rated against published charts.",
                  "hi": "सॉयल हेल्थ कार्ड के 12 पैरामीटर, और आपका कार्ड प्रकाशित चार्ट से मिलाकर।"},
    "card_crop": {"en": "Published facts per crop: zone listing, salt tolerance and water need. No guessing.",
                  "hi": "हर फसल के प्रकाशित तथ्य: क्षेत्र सूची, लवण सहनशीलता, पानी की ज़रूरत। कोई अंदाज़ा नहीं।"},
    "card_gwq": {"en": "Compare your water test with IS 10500 and irrigation limits; quantity and quality kept apart.",
                 "hi": "अपनी पानी जाँच की IS 10500 और सिंचाई सीमाओं से तुलना; मात्रा और गुणवत्ता अलग-अलग।"},
    "card_soilreport": {"en": "Upload your Soil Health Card, check the values, and get a plain explanation.",
                        "hi": "अपना सॉयल हेल्थ कार्ड अपलोड करें, मान जाँचें, और आसान व्याख्या पाएँ।"},
    "card_land": {"en": "Land Condition Report: what is known for your area and what is still missing.",
                  "hi": "भूमि स्थिति रिपोर्ट: आपके क्षेत्र के बारे में क्या पता है और क्या बाकी है।"},
}

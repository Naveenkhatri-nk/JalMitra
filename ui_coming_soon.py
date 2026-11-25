"""
ui_coming_soon.py - "Coming soon" page (JalMitra 4.0 Phase 4).

Lists the modules that are planned but not part of JalMitra 4.0. Groundwater is the only primary domain;
the older soil / crop / land / irrigation / water-quality pages are kept in the code (ui_pages_v3.py) but
hidden from the navigation, and chat questions about them get a "coming in a future update" reply.
"""

import streamlit as st

FEATURES = [
    ("🌱", {"en": "Soil Health Analysis", "hi": "मृदा स्वास्थ्य विश्लेषण"},
     {"en": "Reading Soil Health Cards and explaining nutrients.", "hi": "मृदा स्वास्थ्य कार्ड पढ़ना और पोषक तत्व समझाना।"}),
    ("🌾", {"en": "Crop Advisory", "hi": "फसल सलाह"},
     {"en": "Crop suggestions linked to water availability.", "hi": "पानी की उपलब्धता के अनुसार फसल सुझाव।"}),
    ("🧪", {"en": "Water Quality Analysis", "hi": "जल गुणवत्ता विश्लेषण"},
     {"en": "Groundwater quality parameters and drinking / irrigation suitability.",
      "hi": "भूजल गुणवत्ता और पीने / सिंचाई के लिए उपयुक्तता।"}),
    ("🚿", {"en": "Irrigation Intelligence", "hi": "सिंचाई जानकारी"},
     {"en": "Irrigation planning based on groundwater status.", "hi": "भूजल स्थिति के आधार पर सिंचाई योजना।"}),
    ("🗺️", {"en": "Land Intelligence", "hi": "भूमि जानकारी"},
     {"en": "Land use, slope and land degradation information.", "hi": "भूमि उपयोग, ढलान और भूमि क्षरण की जानकारी।"}),
    ("🎙️", {"en": "Advanced Voice Assistant", "hi": "उन्नत वॉयस सहायक"},
     {"en": "Full spoken conversations in all six languages.", "hi": "सभी छह भाषाओं में पूरी बोलचाल वाली बातचीत।"}),
]
TEXT = {
    "en": {"title": "Coming soon", "intro": "JalMitra 4.0 focuses on groundwater. These modules are planned for future "
           "updates. Until then JalMitra does not answer these topics with data, and never guesses.",
           "badge": "Coming soon"},
    "hi": {"title": "जल्द आ रहा है", "intro": "JalMitra 4.0 भूजल पर केंद्रित है। ये मॉड्यूल आने वाले अपडेट में आएंगे। तब तक "
           "JalMitra इन विषयों पर आंकड़े नहीं देता और कभी अनुमान नहीं लगाता।", "badge": "जल्द आ रहा है"},
}


def page_coming_soon():
    lg = st.session_state.get("ui_lang", "en")
    lg = lg if lg in TEXT else "en"
    st.title("🚧 " + TEXT[lg]["title"])
    st.caption(TEXT[lg]["intro"])
    cols = st.columns(2)
    for i, (icon, name, desc) in enumerate(FEATURES):
        with cols[i % 2]:
            with st.container(border=True):
                st.markdown(f"### {icon} {name.get(lg, name['en'])}")
                st.markdown(desc.get(lg, desc["en"]))
                st.caption("⏳ " + TEXT[lg]["badge"])

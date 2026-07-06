import streamlit as st
from config.languages import t, init_session_state
from utils.constants import LANGUAGE_CODES

def get_lang() -> str:
    """Get current language code from session state."""
    return st.session_state.get("lang_code", "en")

def render_sidebar():
    """Render the multilingual sidebar for all pages."""
    init_session_state()
    
    with st.sidebar:
        st.markdown("## 🌾 SCAS")
        st.markdown({
            "en": "*Smart Crop Advisory*",
            "ta": "*ஸ்மார்ட் பயிர் ஆலோசனை*",
            "hi": "*स्मार्ट फसल सलाह*",
            "te": "*స్మార్ట్ పంట సలహా*",
            "ml": "*സ്മാർട്ട് വിള உபദേശം*",
        }.get(get_lang(), "*Smart Crop Advisory*"))
        st.markdown("---")

        # Language Selector
        lang_options = list(LANGUAGE_CODES.keys())
        current_lang = st.session_state.get("language", "English")
        if current_lang not in lang_options:
            current_lang = "English"

        selected_lang = st.selectbox(
            t("select_language", get_lang()),
            options=lang_options,
            index=lang_options.index(current_lang),
            key="lang_selector_sidebar",
        )

        if selected_lang != st.session_state.language:
            st.session_state.language = selected_lang
            st.session_state.lang_code = LANGUAGE_CODES[selected_lang]
            st.rerun()

        st.markdown("---")

        # ── Custom Translated Navigation ────────────────────────────────────
        lang = get_lang()
        st.markdown(f"### {t('navigation', lang)}")

        # Each nav item: (page_path, translation_key)
        nav_pages = [
            ("app.py",                        "page_home"),
            ("pages/01_🌍_Location.py",      "page_location"),
            ("pages/02_🌤_Weather.py",        "page_weather"),
            ("pages/03_🧪_Soil_Analysis.py",  "page_soil"),
            ("pages/04_🌾_Crop_Advisor.py",   "page_crop"),
            ("pages/05_💧_Irrigation.py",     "page_irrigation"),
            ("pages/06_🧫_Fertilizer.py",     "page_fertilizer"),
            ("pages/07_📊_Market.py",         "page_market"),
            ("pages/08_🏪_Buy_Sell.py",       "page_buy_sell"),
            ("pages/09_🔬_Disease.py",        "page_disease"),
            ("pages/10_🎙_Voice.py",          "page_voice"),
            ("pages/11_💬_Chatbot.py",        "page_chatbot"),
        ]

        for page_path, key in nav_pages:
            label = t(key, lang)
            st.page_link(page_path, label=label, use_container_width=True)

        st.markdown("---")

        # Status indicators
        if st.session_state.get("latitude"):
            district = st.session_state.location_data.get("district", "Located") if st.session_state.location_data else "Located"
            st.success(f"📍 {district}")
        else:
            st.warning(f"📍 {t('no_location', lang)}")

        if st.session_state.get("weather_data"):
            temp = st.session_state.weather_data.get("temperature", "--")
            st.info(f"🌡️ {temp}°C")
        else:
            st.info(f"🌤 {t('no_weather', lang)}")

        if st.session_state.get("selected_crop"):
            st.success(f"🌾 {st.session_state.selected_crop}")

        st.markdown("---")
        st.markdown(
            f"""
            <div style='text-align: center; color: #78909C; font-size: 0.75rem; padding: 1rem 0;'>
                <p>{'இந்திய விவசாயிகளுக்காக ❤️ உடன் கட்டப்பட்டது' if lang == 'ta'
                   else 'भारतीय किसानों के लिए ❤️ से बना' if lang == 'hi'
                   else 'భారత రైతుల కోసం ❤️ తో నిర్మించబడింది' if lang == 'te'
                   else 'ഇന്ത്യൻ കർഷകർക്കായി ❤️ കൊണ്ട് നിർമ്മിച്ചത്' if lang == 'ml'
                   else 'Built with ❤️ for Indian Farmers'}</p>
                <p>v1.0.0 | AI-Powered</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

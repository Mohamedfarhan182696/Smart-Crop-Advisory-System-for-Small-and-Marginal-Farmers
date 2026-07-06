"""
Smart Crop Advisory System — Main Application
===============================================
AI-powered agriculture platform for Indian farmers.
Entry point for the Streamlit multi-page application.
"""

import streamlit as st
import os
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from config.settings import get_settings
from config.languages import t, TRANSLATIONS
from database.database import init_database
from utils.constants import LANGUAGE_CODES

# ── Page Configuration ───────────────────────────────────────────────────
st.set_page_config(
    page_title="Smart Crop Advisory System",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get help": "https://github.com/smart-crop-advisor",
        "Report a Bug": "https://github.com/smart-crop-advisor/issues",
        "About": "Smart Crop Advisory System v1.0 — AI-powered farming assistant for Indian farmers.",
    },
)

# ── Load Custom CSS ──────────────────────────────────────────────────────
css_path = PROJECT_ROOT / "frontend" / "styles" / "custom.css"
if css_path.exists():
    with open(css_path, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# ── Initialize Database (once) ───────────────────────────────────────────
if "db_initialized" not in st.session_state:
    try:
        init_database()
        st.session_state.db_initialized = True
    except Exception as e:
        st.error(f"Database initialization failed: {e}")
        st.session_state.db_initialized = False

# ── Session State Initialization ─────────────────────────────────────────
defaults = {
    "language": "English",
    "lang_code": "en",
    "latitude": None,
    "longitude": None,
    "location_data": None,
    "weather_data": None,
    "soil_data": None,
    "crop_recommendations": None,
    "selected_crop": None,
    "chat_history": [],
    "user_id": None,
}
for key, default_value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = default_value


def get_lang() -> str:
    """Get current language code from session state."""
    return st.session_state.get("lang_code", "en")


from utils.sidebar import render_sidebar
render_sidebar()

lang = get_lang()
# ── Main Home Page Content ───────────────────────────────────────────────
lang = get_lang()

st.markdown(f"# {t('app_title', lang)}")
st.markdown(f"#### {t('welcome_message', lang)}")

st.markdown("---")

# ── Quick Stats / Dashboard Cards ────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)

# Translated labels for dashboard
_loc_label    = {"en": "🌍 Location", "ta": "🌍 இருப்பிடம்", "hi": "🌍 स्थान", "te": "🌍 స్థానం", "ml": "🌍 സ്ഥാനം"}.get(lang, "🌍 Location")
_not_set      = {"en": "Not Set", "ta": "அமைக்கப்படவில்லை", "hi": "सेट नहीं", "te": "సెట్ చేయలేదు", "ml": "സജ്ജമല്ല"}.get(lang, "Not Set")
_set_loc      = {"en": "📍 Set Location", "ta": "📍 இருப்பிடம் அமை", "hi": "📍 स्थान सेट करें", "te": "📍 స్థానం సెట్ చేయి", "ml": "📍 സ്ഥാനം സജ്ജമാക്കുക"}.get(lang, "📍 Set Location")
_chg_loc      = {"en": "⚙️ Change Location", "ta": "⚙️ இருப்பிடம் மாற்று", "hi": "⚙️ स्थान बदलें", "te": "⚙️ స్థానం మార్చు", "ml": "⚙️ സ്ഥാനം മാറ്റുക"}.get(lang, "⚙️ Change Location")
_temp_label   = {"en": "🌡️ Temperature", "ta": "🌡️ வெப்பநிலை", "hi": "🌡️ तापमान", "te": "🌡️ ఉష్ణోగ్రత", "ml": "🌡️ താപനില"}.get(lang, "🌡️ Temperature")
_hum_label    = {"en": "Humidity", "ta": "ஈரப்பதம்", "hi": "आर्द्रता", "te": "తేమ", "ml": "ഈർപ്പം"}.get(lang, "Humidity")
_view_weather = {"en": "🌤 View Weather", "ta": "🌤 வானிலை காண்க", "hi": "🌤 मौसम देखें", "te": "🌤 వాతావరణం చూడండి", "ml": "🌤 കാലാവസ്ഥ കാണുക"}.get(lang, "🌤 View Weather")
_crop_label   = {"en": "🌾 Selected Crop", "ta": "🌾 தேர்ந்தெடுத்த பயிர்", "hi": "🌾 चयनित फसल", "te": "🌾 ఎంచుకున్న పంట", "ml": "🌾 തിരഞ്ഞെടുത്ത വിള"}.get(lang, "🌾 Selected Crop")
_crop_na      = {"en": "Not Selected", "ta": "தேர்ந்தெடுக்கப்படவில்லை", "hi": "चयनित नहीं", "te": "ఎంచుకోలేదు", "ml": "തിരഞ്ഞെടുത്തിട്ടില്ല"}.get(lang, "Not Selected")
_crop_adv     = {"en": "🌾 Crop Advisor", "ta": "🌾 பயிர் ஆலோசகர்", "hi": "🌾 फसल सलाहकार", "te": "🌾 పంట సలహాదారు", "ml": "🌾 വിള ഉപദേഷ്ടാവ്"}.get(lang, "🌾 Crop Advisor")
_lang_label   = {"en": "🗣️ Language", "ta": "🗣️ மொழி", "hi": "🗣️ भाषा", "te": "🗣️ భాష", "ml": "🗣️ ഭാഷ"}.get(lang, "🗣️ Language")

with col1:
    st.metric(
        label=_loc_label,
        value=st.session_state.location_data.get("district", _not_set) if st.session_state.location_data else _not_set,
        delta=st.session_state.location_data.get("state", "") if st.session_state.location_data else None,
    )
    st.page_link("pages/01_🌍_Location.py", label=_set_loc if not st.session_state.location_data else _chg_loc, use_container_width=True)

with col2:
    weather = st.session_state.get("weather_data")
    if isinstance(weather, dict):
        st.metric(
            label=_temp_label,
            value=f"{weather.get('temperature', '--')}°C",
            delta=f"{_hum_label}: {weather.get('humidity', '--')}%",
        )
    else:
        st.metric(label=_temp_label, value="--°C")
    st.page_link("pages/02_🌤_Weather.py", label=_view_weather, use_container_width=True)

with col3:
    if st.session_state.selected_crop:
        st.metric(label=_crop_label, value=st.session_state.selected_crop)
    else:
        st.metric(label=_crop_label, value=_crop_na)
    st.page_link("pages/04_🌾_Crop_Advisor.py", label=_crop_adv, use_container_width=True)

with col4:
    st.metric(
        label=_lang_label,
        value=st.session_state.language,
    )

st.markdown("---")

# ── Getting Started Guide ────────────────────────────────────────────────
_getting_started = {
    "en": "🚀 Getting Started",
    "ta": "🚀 தொடங்குவது எப்படி",
    "hi": "🚀 शुरुआत कैसे करें",
    "te": "🚀 ప్రారంభించడం",
    "ml": "🚀 ആരംഭിക്കുക",
}.get(lang, "🚀 Getting Started")
st.markdown(f"## {_getting_started}")

steps_data = {
    "en": [
        ("1️⃣", "Set Location", "Go to the **Location** page to detect your GPS or enter your district manually."),
        ("2️⃣", "Check Weather", "View real-time weather data, soil temperature, and 7-day forecast."),
        ("3️⃣", "Analyze Soil", "Enter your soil values: Nitrogen, Phosphorus, Potassium, pH, moisture."),
        ("4️⃣", "Get Crop Advice", "AI recommends the top 5 crops based on your location, weather, and soil."),
        ("5️⃣", "Plan Irrigation", "Calculate daily, weekly, and seasonal water requirements."),
        ("6️⃣", "Choose Fertilizer", "Get organic, chemical, and bio-fertilizer recommendations."),
        ("7️⃣", "Market Analysis", "View current prices, predictions, and profit estimates."),
        ("8️⃣", "Detect Diseases", "Upload a crop image to identify diseases and get treatment."),
    ],
    "ta": [
        ("1️⃣", "இருப்பிடம் அமை", "உங்கள் GPS கண்டறிய அல்லது மாவட்டம் உள்ளிட **இருப்பிடம்** பக்கத்திற்கு செல்லவும்."),
        ("2️⃣", "வானிலை சரிபார்க்கவும்", "நிகழ்நேர வானிலை, மண் வெப்பநிலை மற்றும் 7 நாள் முன்னறிவிப்பு."),
        ("3️⃣", "மண் பகுப்பாய்வு", "நைட்ரஜன், பாஸ்பரஸ், பொட்டாசியம், pH, ஈரப்பதம் உள்ளிடவும்."),
        ("4️⃣", "பயிர் ஆலோசனை பெறுங்கள்", "AI உங்கள் இருப்பிடம், வானிலை, மண் அடிப்படையில் சிறந்த 5 பயிர்களை பரிந்துரைக்கும்."),
        ("5️⃣", "நீர்ப்பாசன திட்டம்", "தினசரி, வாராந்திர, பருவகால நீர் தேவையை கணக்கிடுங்கள்."),
        ("6️⃣", "உர தேர்வு", "கரிம, இரசாயன மற்றும் உயிரி உர பரிந்துரைகள் பெறுங்கள்."),
        ("7️⃣", "சந்தை பகுப்பாய்வு", "தற்போதைய விலைகள், கணிப்புகள் மற்றும் லாப மதிப்பீடுகள்."),
        ("8️⃣", "நோய் கண்டறிதல்", "நோய்களை கண்டறிய மற்றும் சிகிச்சை பெற பயிர் படத்தை பதிவேற்றுங்கள்."),
    ],
    "hi": [
        ("1️⃣", "स्थान सेट करें", "GPS द्वारा स्थान पहचानने या जिला दर्ज करने के लिए **स्थान** पेज पर जाएं।"),
        ("2️⃣", "मौसम जांचें", "रीयल-टाइम मौसम, मिट्टी का तापमान और 7-दिवसीय पूर्वानुमान देखें।"),
        ("3️⃣", "मिट्टी विश्लेषण", "नाइट्रोजन, फॉस्फोरस, पोटैशियम, pH, नमी मान दर्ज करें।"),
        ("4️⃣", "फसल सलाह पाएं", "AI आपके स्थान, मौसम और मिट्टी के आधार पर शीर्ष 5 फसलें सुझाता है।"),
        ("5️⃣", "सिंचाई योजना", "दैनिक, साप्ताहिक और मौसमी जल आवश्यकताओं की गणना करें।"),
        ("6️⃣", "उर्वरक चुनें", "जैविक, रासायनिक और जैव-उर्वरक सिफारिशें पाएं।"),
        ("7️⃣", "बाजार विश्लेषण", "वर्तमान कीमतें, पूर्वानुमान और लाभ अनुमान देखें।"),
        ("8️⃣", "रोग पहचानें", "रोगों की पहचान और उपचार के लिए फसल की तस्वीर अपलोड करें।"),
    ],
    "te": [
        ("1️⃣", "స్థానం సెట్ చేయండి", "GPS ద్వారా స్థానం గుర్తించడానికి లేదా జిల్లా నమోదు చేయడానికి **స్థానం** పేజీకి వెళ్ళండి।"),
        ("2️⃣", "వాతావరణం తనిఖీ", "రియల్-టైమ్ వాతావరణం, నేల ఉష్ణోగ్రత మరియు 7 రోజుల అంచనా చూడండి."),
        ("3️⃣", "నేల విశ్లేషణ", "నత్రజని, భాస్వరం, పొటాషియం, pH, తేమ విలువలు నమోదు చేయండి."),
        ("4️⃣", "పంట సలహా పొందండి", "AI మీ స్థానం, వాతావరణం, నేల ఆధారంగా అగ్ర 5 పంటలను సిఫారసు చేస్తుంది."),
        ("5️⃣", "నీటిపారుదల ప్రణాళిక", "రోజువారీ, వారపు, సీజన్ నీటి అవసరాలను లెక్కించండి."),
        ("6️⃣", "ఎరువు ఎంపిక", "సేంద్రీయ, రసాయనిక మరియు జీవ ఎరువు సిఫారసులు పొందండి."),
        ("7️⃣", "మార్కెట్ విశ్లేషణ", "ప్రస్తుత ధరలు, అంచనాలు మరియు లాభ మదింపులు చూడండి."),
        ("8️⃣", "వ్యాధులు గుర్తించండి", "వ్యాధులను గుర్తించడానికి పంట చిత్రాన్ని అప్‌లోడ్ చేయండి."),
    ],
    "ml": [
        ("1️⃣", "സ്ഥാനം സജ്ജമാക്കുക", "GPS ഉപയോഗിച്ച് സ്ഥാനം കണ്ടെത്താൻ അല്ലെങ്കിൽ ജില്ല നൽകാൻ **സ്ഥാനം** പേജ് സന്ദർശിക്കുക."),
        ("2️⃣", "കാലാവസ്ഥ പരിശോധിക്കുക", "തത്സമയ കാലാവസ്ഥ, മണ്ണ് ഊഷ്മാവ്, 7 ദിവസത്തെ പ്രവചനം."),
        ("3️⃣", "മണ്ണ് വിശകലനം", "നൈട്രജൻ, ഫോസ്ഫറസ്, പൊട്ടാസ്യം, pH, ഈർപ്പം മൂല്യങ്ങൾ നൽകുക."),
        ("4️⃣", "വിള ഉപദേശം നേടുക", "AI നിങ്ങളുടെ സ്ഥാനം, കാലാവസ്ഥ, മണ്ണ് അടിസ്ഥാനത്തിൽ മികച്ച 5 വിളകൾ ശുപാർശ ചെയ്യുന്നു."),
        ("5️⃣", "ജലസേചന പദ്ധതി", "ദൈനിക, ആഴ്ചതോറും, സീസൺ ജല ആവശ്യകതകൾ കണക്കാക്കുക."),
        ("6️⃣", "വളം തിരഞ്ഞെടുക്കുക", "ജൈവ, രാസ, ജൈവ-വള ശുപാർശകൾ നേടുക."),
        ("7️⃣", "വിപണി വിശകലനം", "നിലവിലെ വില, പ്രവചനങ്ങൾ, ലാഭ കണക്കുകൾ."),
        ("8️⃣", "രോഗം കണ്ടെത്തുക", "രോഗങ്ങൾ തിരിച്ചറിയാൻ വിള ഫോട്ടോ അപ്‌ലോഡ് ചെയ്യുക."),
    ],
}

steps = steps_data.get(lang, steps_data["en"])
cols = st.columns(4)
for idx, (emoji, title, desc) in enumerate(steps):
    with cols[idx % 4]:
        st.markdown(
            f"""
            <div style='
                background: rgba(17, 29, 51, 0.85);
                border: 1px solid rgba(76, 175, 80, 0.2);
                border-radius: 16px;
                padding: 1.2rem;
                margin-bottom: 1rem;
                min-height: 160px;
                transition: all 0.3s ease;
            '>
                <h3 style='margin: 0 0 0.5rem; color: #81C784;'>{emoji} {title}</h3>
                <p style='color: #A5D6A7; font-size: 0.85rem; margin: 0;'>{desc}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.markdown("---")

# ── Feature Highlights ───────────────────────────────────────────────────
_features_title = {
    "en": "✨ Features", "ta": "✨ அம்சங்கள்", "hi": "✨ विशेषताएं",
    "te": "✨ లక్షణాలు", "ml": "✨ സവിശേഷതകൾ",
}.get(lang, "✨ Features")
st.markdown(f"## {_features_title}")

feature_cols = st.columns(3)
features_data = {
    "en": [
        ("🤖 AI-Powered", "Machine learning models trained on real agricultural data for accurate crop, fertilizer, and disease recommendations."),
        ("🌐 Multilingual", "Full support for English, Tamil, Hindi, Telugu, and Malayalam — including voice assistant and chatbot."),
        ("📱 Farmer-Friendly", "Simple, intuitive interface designed for farmers with little or no technical knowledge."),
        ("🎙️ Voice Assistant", "Ask questions by speaking naturally in your language. The AI understands and responds with voice."),
        ("🔬 Disease Detection", "Upload a photo of your crop to instantly detect diseases and get treatment recommendations."),
        ("📊 Market Intelligence", "Real-time market prices, historical trends, profit predictions, and nearby market locations."),
    ],
    "ta": [
        ("🤖 AI-சக்தி", "உண்மையான விவசாய தரவில் பயிற்றுவிக்கப்பட்ட ML மாதிரிகள் துல்லியமான பயிர், உர மற்றும் நோய் பரிந்துரைகளை வழங்குகின்றன."),
        ("🌐 பன்மொழி", "ஆங்கிலம், தமிழ், இந்தி, தெலுங்கு மற்றும் மலையாளம் — குரல் உதவியாளர் மற்றும் சாட்போட் உட்பட."),
        ("📱 விவசாயி நட்பு", "குறைந்த அல்லது தொழில்நுட்ப அறிவு இல்லாத விவசாயிகளுக்காக வடிவமைக்கப்பட்ட எளிய இடைமுகம்."),
        ("🎙️ குரல் உதவியாளர்", "உங்கள் மொழியில் இயற்கையாக பேசி கேளுங்கள். AI புரிந்து குரலில் பதில் சொல்லும்."),
        ("🔬 நோய் கண்டறிதல்", "நோய்களை கண்டறிந்து சிகிச்சை பரிந்துரை பெற பயிர் புகைப்படம் பதிவேற்றவும்."),
        ("📊 சந்தை அறிவு", "நிகழ்நேர விலைகள், வரலாற்று போக்குகள், லாப கணிப்புகள் மற்றும் அருகில் உள்ள சந்தை இடங்கள்."),
    ],
    "hi": [
        ("🤖 AI-संचालित", "वास्तविक कृषि डेटा पर प्रशिक्षित ML मॉडल सटीक फसल, उर्वरक और रोग सिफारिशें प्रदान करते हैं।"),
        ("🌐 बहुभाषी", "अंग्रेजी, तमिल, हिंदी, तेलुगु और मलयालम — वॉइस असिस्टेंट और चैटबॉट सहित।"),
        ("📱 किसान-अनुकूल", "कम या बिना तकनीकी ज्ञान वाले किसानों के लिए सरल, सहज इंटरफेस।"),
        ("🎙️ वॉइस असिस्टेंट", "अपनी भाषा में स्वाभाविक रूप से बोलकर पूछें। AI समझता और आवाज में जवाब देता है।"),
        ("🔬 रोग पहचान", "रोगों की पहचान और उपचार सिफारिशें पाने के लिए फसल की तस्वीर अपलोड करें।"),
        ("📊 बाजार खुफिया", "रीयल-टाइम कीमतें, ऐतिहासिक रुझान, लाभ पूर्वानुमान और पास के बाजार।"),
    ],
    "te": [
        ("🤖 AI-ఆధారిత", "నిజమైన వ్యవసాయ డేటాపై శిక్షణ పొందిన ML మోడళ్ళు ఖచ్చితమైన పంట, ఎరువు మరియు వ్యాధి సిఫారసులు అందిస్తాయి."),
        ("🌐 బహుభాషా", "ఇంగ్లీషు, తమిళం, హిందీ, తెలుగు మరియు మలయాళం — వాయిస్ అసిస్టెంట్ మరియు చాట్‌బాట్ సహా."),
        ("📱 రైతు-స్నేహపూర్వక", "తక్కువ లేదా సాంకేతిక జ్ఞానం లేని రైతులకు సులభంగా ఉపయోగించగలిగే ఇంటర్‌ఫేస్."),
        ("🎙️ వాయిస్ అసిస్టెంట్", "మీ భాషలో సహజంగా మాట్లాడండి. AI అర్థం చేసుకుని వాయిస్‌లో సమాధానం ఇస్తుంది."),
        ("🔬 వ్యాధి గుర్తింపు", "వ్యాధులను గుర్తించి చికిత్స సిఫారసులు పొందడానికి పంట ఫోటో అప్‌లోడ్ చేయండి."),
        ("📊 మార్కెట్ ఇంటెలిజెన్స్", "తక్షణ ధరలు, చారిత్రక ట్రెండ్‌లు, లాభ అంచనాలు మరియు సమీప మార్కెట్‌లు."),
    ],
    "ml": [
        ("🤖 AI-ശക്തി", "യഥാർഥ കൃഷി ഡേറ്റയിൽ പരിശീലിച്ച ML മോഡലുകൾ കൃത്യമായ വിള, വള, രോഗ ശുപാർശകൾ നൽകുന്നു."),
        ("🌐 ബഹുഭാഷ", "ഇംഗ്ലീഷ്, തമിഴ്, ഹിന്ദി, തെലുഗ്, മലയാളം — വോയ്സ് അസിസ്റ്റന്റ്, ചാറ്റ്ബോട്ട് സഹിതം."),
        ("📱 കർഷക-സൗഹൃദം", "കുറഞ്ഞ അല്ലെങ്കിൽ സാങ്കേതിക അറിവ് ഇല്ലാത്ത കർഷകർക്ക് ലളിതവും അനുഭവജ്ഞ്യമുള്ളതുമായ ഇന്റർഫേസ്."),
        ("🎙️ വോയ്സ് അസിസ്റ്റന്റ്", "നിങ്ങളുടെ ഭാഷയിൽ സ്വാഭാവികമായി സംസാരിക്കൂ. AI മനസ്സിലാക്കി ശബ്ദത്തിൽ മറുപടി നൽകും."),
        ("🔬 രോഗ നിർണ്ണയം", "രോഗങ്ങൾ കണ്ടെത്തി ചികിത്സ ശുപാർശ നേടാൻ വിള ഫോട്ടോ അപ്‌ലോഡ് ചെയ്യുക."),
        ("📊 വിപണി വിവരം", "തത്സമയ വില, ചരിത്ര ട്രെൻഡ്, ലാഭ പ്രവചനങ്ങൾ, സമീപ വിപണി സ്ഥാനങ്ങൾ."),
    ],
}

features = features_data.get(lang, features_data["en"])
for idx, (title, desc) in enumerate(features):
    with feature_cols[idx % 3]:
        st.markdown(
            f"""
            <div style='
                background: linear-gradient(135deg, rgba(76, 175, 80, 0.08) 0%, rgba(255, 152, 0, 0.05) 100%);
                border: 1px solid rgba(76, 175, 80, 0.15);
                border-radius: 16px;
                padding: 1.5rem;
                margin-bottom: 1rem;
                min-height: 140px;
            '>
                <h3 style='margin: 0 0 0.5rem; color: #FFB74D; font-size: 1.1rem;'>{title}</h3>
                <p style='color: #A5D6A7; font-size: 0.85rem; margin: 0;'>{desc}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

# ── Government Schemes Quick Access ──────────────────────────────────────
from utils.constants import GOVERNMENT_SCHEMES

_schemes_title = {
    "en": "🏛️ Government Schemes for Farmers",
    "ta": "🏛️ விவசாயிகளுக்கான அரசு திட்டங்கள்",
    "hi": "🏛️ किसानों के लिए सरकारी योजनाएं",
    "te": "🏛️ రైతులకు ప్రభుత్వ పథకాలు",
    "ml": "🏛️ കർഷകർക്കുള്ള സർക്കാർ പദ്ധതികൾ",
}.get(lang, "🏛️ Government Schemes for Farmers")

st.markdown("---")
st.markdown(f"## {_schemes_title}")

scheme_cols = st.columns(3)
for idx, scheme in enumerate(GOVERNMENT_SCHEMES):
    with scheme_cols[idx % 3]:
        st.markdown(
            f"""
            <div style='
                background: rgba(17, 29, 51, 0.85);
                border: 1px solid rgba(2, 119, 189, 0.3);
                border-radius: 12px;
                padding: 1rem;
                margin-bottom: 0.8rem;
            '>
                <h4 style='color: #4FC3F7; margin: 0 0 0.3rem;'>{scheme['name']}</h4>
                <p style='color: #B0BEC5; font-size: 0.8rem; margin: 0 0 0.3rem;'>{scheme['full_name']}</p>
                <p style='color: #81C784; font-size: 0.85rem; margin: 0;'>💰 {scheme['benefit']}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

# ── Footer ───────────────────────────────────────────────────────────────
_footer = {
    "en": "Designed for Small and Marginal Farmers of India",
    "ta": "இந்தியாவின் சிறு மற்றும் குறு விவசாயிகளுக்காக வடிவமைக்கப்பட்டது",
    "hi": "भारत के छोटे और सीमांत किसानों के लिए डिज़ाइन किया गया",
    "te": "భారత చిన్న మరియు సన్నకారు రైతుల కోసం రూపొందించబడింది",
    "ml": "ഇന്ത്യയിലെ ചെറുകിട, നാമമാത്ര കർഷകർക്ക് വേണ്ടി രൂപകൽപ്പന ചെയ്തത്",
}.get(lang, "Designed for Small and Marginal Farmers of India")

st.markdown(
    f"""
    <div class='footer-text'>
        <p>🌾 Smart Crop Advisory System v1.0.0 | Built with Streamlit + FastAPI + TensorFlow + Google Gemini</p>
        <p>{_footer}</p>
    </div>
    """,
    unsafe_allow_html=True,
)


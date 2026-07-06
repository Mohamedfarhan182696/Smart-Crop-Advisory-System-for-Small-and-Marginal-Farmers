"""
📍 Location Page
==================
GPS detection + manual location entry.
All UI strings translated via config/languages.py t() function.
"""

import streamlit as st
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.sidebar import render_sidebar
render_sidebar()

from config.languages import t, get_soil_types
from backend.services.location_service import (
    reverse_geocode, search_location, get_states_list,
    get_districts_for_state, get_all_districts,
)

def set_new_location(latitude, longitude, location_data):
    """Set new location and clear all dependent data from session state to avoid stales."""
    st.session_state.latitude = latitude
    st.session_state.longitude = longitude
    st.session_state.location_data = location_data
    
    # Clear stale dependencies
    keys_to_clear = [
        "weather_data", "crop_recommendations", "soil_data",
        "soil_n", "soil_p", "soil_k", "soil_ph", "soil_moisture",
        "soil_water", "soil_type_selected"
    ]
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]

# Page config
lang = st.session_state.get("lang_code", "en")
st.markdown(f"# {t('page_location', lang)}")
st.markdown("---")

# ── Tab Layout: GPS vs Manual ────────────────────────────────────────────
tab_gps, tab_manual = st.tabs([t("loc_gps_tab", lang), t("loc_manual_tab", lang)])

# ── GPS Tab ──────────────────────────────────────────────────────────────
with tab_gps:
    st.markdown(f"### {t('loc_gps_tab', lang)}")
    st.info({"en": "Click the button below to detect your location using your device's GPS.",
             "ta": "உங்கள் சாதனத்தின் GPS மூலம் உங்கள் இருப்பிடத்தை கண்டறிய கீழே உள்ள பொத்தானை கிளிக் செய்யவும்.",
             "hi": "अपने डिवाइस के GPS का उपयोग करके अपना स्थान पता लगाने के लिए नीचे बटन दबाएं।",
             "te": "మీ పరికరం GPS ఉపయోగించి మీ స్థానాన్ని గుర్తించడానికి దిగువ బటన్ నొక్కండి.",
             "ml": "നിങ്ങളുടെ ഉപകരണത്തിന്റെ GPS ഉപയോഗിച്ച് സ്ഥാനം കണ്ടെത്താൻ ചുവടെ ക്ലിക്ക് ചെയ്യുക.",
             }.get(lang, "Click the button below to detect your location using your device's GPS."))

    if st.button(t("btn_detect_location", lang), key="gps_btn", type="primary"):
        try:
            from streamlit_js_eval import get_geolocation
            loc = get_geolocation()

            if loc and "coords" in loc:
                lat = loc["coords"]["latitude"]
                lon = loc["coords"]["longitude"]

                with st.spinner("🔍 " + {"en": "Looking up your location...", "ta": "உங்கள் இருப்பிடத்தை கண்டறிகிறது...",
                    "hi": "आपका स्थान ढूंढ रहे हैं...", "te": "మీ స్థానాన్ని వెతుకుతోంది...",
                    "ml": "നിങ്ങളുടെ സ്ഥാനം കണ്ടെത്തുന്നു..."}.get(lang, "Looking up your location...")):
                    location_data = reverse_geocode(lat, lon)

                if location_data:
                    set_new_location(lat, lon, location_data)
                    st.success(f"✅ {location_data.get('district', '')}, {location_data.get('state', '')}")
                else:
                    set_new_location(lat, lon, {
                        "latitude": lat, "longitude": lon,
                        "district": "Unknown", "state": "Unknown",
                        "country": "Unknown", "village": "", "taluk": "",
                    })
                    st.warning({"en": "Location coordinates detected but address lookup failed.",
                        "ta": "இருப்பிட ஒருங்கிணைப்புகள் கண்டறியப்பட்டன, ஆனால் முகவரி தேடல் தோல்வியடைந்தது.",
                        "hi": "स्थान निर्देशांक मिले लेकिन पता खोज विफल रही।",
                        "te": "స్థానం సమన్వయాలు గుర్తించబడ్డాయి కానీ చిరునామా శోధన విఫలమైంది.",
                        "ml": "സ്ഥানം കണ്ടെത്തി, പക്ഷേ വിലാസം ലഭ്യമല്ല."}.get(lang, "Location detected but address lookup failed."))
            elif loc and "error" in loc:
                st.error(t("gps_denied", lang))
            else:
                st.warning({"en": "Waiting for GPS response... Please allow location access in your browser.",
                    "ta": "GPS பதிலுக்கு காத்திருக்கிறது... உங்கள் உலாவியில் இருப்பிட அணுகலை அனுமதிக்கவும்.",
                    "hi": "GPS प्रतिक्रिया की प्रतीक्षा... कृपया ब्राउज़र में स्थान एक्सेस की अनुमति दें।",
                    "te": "GPS స్పందన కోసం వేచి ఉంది... దయచేసి బ్రౌజర్‌లో స్థాన ప్రాప్తిని అనుమతించండి.",
                    "ml": "GPS പ്രതികരണത്തിനായി കാത്തിരിക്കുന്നു... ബ്രൗസറിൽ ലൊക്കേഷൻ ആക്സസ് അനുവദിക്കുക."}.get(lang, "Waiting for GPS..."))
        except ImportError:
            st.error("GPS component not available. Please install: `pip install streamlit-js-eval`")
        except Exception as e:
            st.error(f"GPS error: {str(e)}. Please use manual entry.")

# ── Manual Entry Tab ─────────────────────────────────────────────────────
with tab_manual:
    st.markdown(f"### {t('loc_manual_tab', lang)}")

    # Method radio labels
    method_labels = {
        "en": ["Search by City/District", "Select State & District", "Enter Coordinates"],
        "ta": ["நகரம்/மாவட்டம் மூலம் தேடு", "மாநிலம் & மாவட்டம் தேர்ந்தெடு", "ஆயத்தொலைவுகளை உள்ளிடு"],
        "hi": ["शहर/जिले से खोजें", "राज्य और जिला चुनें", "निर्देशांक दर्ज करें"],
        "te": ["నగరం/జిల్లాతో వెతకండి", "రాష్ట్రం & జిల్లా ఎంచుకోండి", "కోఆర్డినేట్లు నమోదు చేయండి"],
        "ml": ["നഗരം/ജില്ല തിരയുക", "സംസ്ഥാനം & ജില്ല തിരഞ്ഞെടുക്കുക", "കോർഡിനേറ്റുകൾ നൽകുക"],
    }
    labels = method_labels.get(lang, method_labels["en"])

    method_choice = st.radio(
        {"en": "Choose input method:", "ta": "உள்ளீட்டு முறையை தேர்ந்தெடுக்கவும்:",
         "hi": "इनपुट विधि चुनें:", "te": "ఇన్పుట్ పద్ధతి ఎంచుకోండి:",
         "ml": "ഇൻപുട്ട് രീതി തിരഞ്ഞെടുക്കുക:"}.get(lang, "Choose input method:"),
        labels,
        horizontal=True,
    )

    if method_choice == labels[0]:  # Search by City/District
        search_query = st.text_input(
            t("loc_search_city", lang),
            placeholder={"en": "e.g., Coimbatore, Guntur, Indore...",
                "ta": "எ.கா., கோயம்புத்தூர், குந்தூர், இண்டோர்...",
                "hi": "जैसे कोयंबटूर, गुंटूर, इंदौर...",
                "te": "ఉదా., కోయంబత్తూర్, గుంటూర్, ఇండోర్...",
                "ml": "ഉദാ., കോയമ്പത്തൂർ, ഗുണ്ടൂർ, ഇൻഡോർ..."}.get(lang, "e.g., Coimbatore..."),
        )
        if st.button(t("loc_search_btn", lang), key="search_btn") and search_query:
            with st.spinner({"en": "Searching...", "ta": "தேடுகிறது...", "hi": "खोज रहे हैं...",
                "te": "వెతుకుతోంది...", "ml": "തിരയുന്നു..."}.get(lang, "Searching...")):
                location_data = search_location(search_query)
            if location_data:
                set_new_location(location_data["latitude"], location_data["longitude"], location_data)
                st.success(f"{t('loc_location_set', lang)} — {location_data.get('district', '')}, {location_data.get('state', '')}")
            else:
                st.error({"en": "Location not found. Please try a different search term.",
                    "ta": "இருப்பிடம் கிடைக்கவில்லை. வேறு வார்த்தையில் தேடவும்.",
                    "hi": "स्थान नहीं मिला। कृपया भिन्न खोज शब्द आज़माएं।",
                    "te": "స్థానం కనుగొనబడలేదు. వేరే పదంతో ప్రయత్నించండి.",
                    "ml": "സ്ഥാനം കണ്ടെത്തിയില്ല. മറ്റൊരു പദം ഉപയോഗിക്കുക."}.get(lang, "Location not found."))

    elif method_choice == labels[1]:  # Select State & District
        col1, col2 = st.columns(2)
        with col1:
            state_label = {"en": "Select State:", "ta": "மாநிலம் தேர்ந்தெடு:", "hi": "राज्य चुनें:",
                "te": "రాష్ట్రం ఎంచుకోండి:", "ml": "സംസ്ഥാനം തിരഞ്ഞെടുക്കുക:"}.get(lang, "Select State:")
            state = st.selectbox(state_label, [""] + get_states_list())
        with col2:
            district_label = {"en": "Select District:", "ta": "மாவட்டம் தேர்ந்தெடு:", "hi": "जिला चुनें:",
                "te": "జిల్లా ఎంచుకోండి:", "ml": "ജില്ല തിരഞ്ഞെടുക്കുക:"}.get(lang, "Select District:")
            districts = get_districts_for_state(state) if state else []
            district = st.selectbox(district_label, [""] + districts)

        set_location_label = {"en": "📍 Set Location", "ta": "📍 இருப்பிடம் அமை",
            "hi": "📍 स्थान सेट करें", "te": "📍 స్థానం సెట్ చేయి",
            "ml": "📍 സ്ഥാനം സജ്ജമാക്കുക"}.get(lang, "📍 Set Location")
        if st.button(set_location_label, key="state_district_btn") and state and district:
            with st.spinner({"en": "Looking up location...", "ta": "இருப்பிடத்தை தேடுகிறது...",
                "hi": "स्थान खोज रहे हैं...", "te": "స్థానాన్ని వెతుకుతోంది...",
                "ml": "സ്ഥാനം തിരയുന്നു..."}.get(lang, "Looking up location...")):
                location_data = search_location(f"{district}, {state}")
            if location_data:
                set_new_location(location_data["latitude"], location_data["longitude"], location_data)
                st.success(f"{t('loc_location_set', lang)} — {district}, {state}")
            else:
                st.error({"en": "Could not find coordinates for this location.",
                    "ta": "இந்த இருப்பிடத்திற்கான ஆயத்தொலைவுகள் கிடைக்கவில்லை.",
                    "hi": "इस स्थान के निर्देशांक नहीं मिले।",
                    "te": "ఈ స్థానానికి కోఆర్డినేట్లు దొరకలేదు.",
                    "ml": "ഈ സ്ഥാനത്തിന് കോർഡിനേറ്റുകൾ കണ്ടെത്തിയില്ല."}.get(lang, "Could not find coordinates."))

    elif method_choice == labels[2]:  # Enter Coordinates
        col1, col2 = st.columns(2)
        with col1:
            lat_label = {"en": "Latitude:", "ta": "அட்சரேகை:", "hi": "अक्षांश:",
                "te": "అక్షాంశం:", "ml": "അക്ഷാംശം:"}.get(lang, "Latitude:")
            lat = st.number_input(lat_label, min_value=6.0, max_value=37.0, value=13.0, step=0.01)
        with col2:
            lon_label = {"en": "Longitude:", "ta": "தீர்க்கரேகை:", "hi": "देशांतर:",
                "te": "రేఖాంశం:", "ml": "രേഖാംശം:"}.get(lang, "Longitude:")
            lon = st.number_input(lon_label, min_value=68.0, max_value=98.0, value=80.0, step=0.01)

        set_coords_label = {"en": "📍 Set Coordinates", "ta": "📍 ஆயத்தொலைவுகளை அமை",
            "hi": "📍 निर्देशांक सेट करें", "te": "📍 కోఆర్డినేట్లు సెట్ చేయి",
            "ml": "📍 കോർഡിനേറ്റ് സജ്ജമാക്കുക"}.get(lang, "📍 Set Coordinates")
        if st.button(set_coords_label, key="coords_btn"):
            with st.spinner({"en": "Looking up address...", "ta": "முகவரி தேடுகிறது...",
                "hi": "पता खोज रहे हैं...", "te": "చిరునామా శోధిస్తోంది...",
                "ml": "വിലാസം തിരയുന്നു..."}.get(lang, "Looking up address...")):
                location_data = reverse_geocode(lat, lon)
            if location_data:
                set_new_location(lat, lon, location_data)
                st.success(f"{t('loc_location_set', lang)} — {location_data.get('district', '')}, {location_data.get('state', '')}")
            else:
                set_new_location(lat, lon, {
                    "latitude": lat, "longitude": lon,
                    "district": "Unknown", "state": "Unknown",
                    "country": "India", "village": "", "taluk": "",
                })
                st.warning({"en": "Coordinates set but address lookup failed.",
                    "ta": "ஆயத்தொலைவுகள் அமைக்கப்பட்டன, ஆனால் முகவரி தேடல் தோல்வியடைந்தது.",
                    "hi": "निर्देशांक सेट लेकिन पता खोज विफल।",
                    "te": "కోఆర్డినేట్లు సెట్ అయ్యాయి కానీ చిరునామా శోధన విఫలమైంది.",
                    "ml": "കോർഡിനേറ്റ് സജ്ജമാക്കി, പക്ഷേ വിലാസം ലഭ്യമല്ല."}.get(lang, "Coordinates set but address lookup failed."))

# ── Display Current Location ─────────────────────────────────────────────
st.markdown("---")

if st.session_state.location_data:
    loc = st.session_state.location_data
    st.markdown(f"## {t('loc_current_location', lang)}")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(t("loc_latitude", lang), f"{st.session_state.latitude:.4f}")
        st.metric(t("loc_village", lang), loc.get("village", "N/A") or "N/A")
    with col2:
        st.metric(t("loc_longitude", lang), f"{st.session_state.longitude:.4f}")
        st.metric(t("loc_taluk", lang), loc.get("taluk", "N/A") or "N/A")
    with col3:
        st.metric(t("loc_district", lang), loc.get("district", "N/A"))
        st.metric(t("loc_state", lang), loc.get("state", "N/A"))

    # Map display
    try:
        import folium
        from streamlit_folium import st_folium

        map_title = {"en": "🗺️ Location Map", "ta": "🗺️ இருப்பிட வரைபடம்",
            "hi": "🗺️ स्थान मानचित्र", "te": "🗺️ స్థాన మ్యాప్",
            "ml": "🗺️ ലൊക്കേഷൻ മാപ്പ്"}.get(lang, "🗺️ Location Map")
        st.markdown(f"### {map_title}")
        m = folium.Map(
            location=[st.session_state.latitude, st.session_state.longitude],
            zoom_start=12,
            tiles="OpenStreetMap",
        )
        folium.Marker(
            [st.session_state.latitude, st.session_state.longitude],
            popup=f"{loc.get('district', '')}, {loc.get('state', '')}",
            tooltip={"en": "Your Location", "ta": "உங்கள் இருப்பிடம்", "hi": "आपका स्थान",
                "te": "మీ స్థానం", "ml": "നിങ്ങളുടെ സ്ഥാനം"}.get(lang, "Your Location"),
            icon=folium.Icon(color="green", icon="leaf", prefix="fa"),
        ).add_to(m)

        st_folium(m, width=700, height=400)
    except ImportError:
        st.info("Install `folium` and `streamlit-folium` for map display.")
        st.map(data={"lat": [st.session_state.latitude], "lon": [st.session_state.longitude]})
else:
    st.info({"en": "👆 Please detect or enter your location above to get started.",
        "ta": "👆 தொடங்க மேலே உங்கள் இருப்பிடத்தை கண்டறியவும் அல்லது உள்ளிடவும்.",
        "hi": "👆 शुरू करने के लिए ऊपर अपना स्थान पता लगाएं या दर्ज करें।",
        "te": "👆 ప్రారంభించడానికి పై పట్టిక స్థానాన్ని గుర్తించండి లేదా నమోదు చేయండి.",
        "ml": "👆 ആരംഭിക്കാൻ മുകളിൽ സ്ഥാനം കണ്ടെത്തുക അല്ലെങ്കിൽ നൽകുക."}.get(lang, "Please set your location above."))

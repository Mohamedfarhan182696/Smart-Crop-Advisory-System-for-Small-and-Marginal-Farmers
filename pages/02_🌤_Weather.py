"""
🌤 Weather Dashboard Page
===========================
Real-time weather, soil data, and 7-day forecast — fully multilingual.
"""

import streamlit as st
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.sidebar import render_sidebar
render_sidebar()

import plotly.graph_objects as go
from config.languages import t
from backend.services.weather_service import get_current_weather
from utils.helpers import get_wind_direction_name, get_uv_level

lang = st.session_state.get("lang_code", "en")
st.markdown(f"# {t('page_weather', lang)}")
st.markdown("---")

# ── Translate helper (inline dict shorthand) ─────────────────────────────
def tr(d): return d.get(lang, d.get("en", ""))

# ── Check Location ───────────────────────────────────────────────────────
if not st.session_state.get("latitude"):
    st.warning(t("no_location", lang))
    st.info(tr({"en": "👈 Please go to the **Location** page first.",
                "ta": "👈 முதலில் **இருப்பிடம்** பக்கத்திற்கு செல்லவும்.",
                "hi": "👈 पहले **स्थान** पेज पर जाएं।",
                "te": "👈 ముందు **స్థానం** పేజీకి వెళ్ళండి.",
                "ml": "👈 ആദ്യം **സ്ഥാനം** പേജ് സന്ദർശിക്കുക."}))
    st.stop()

lat = st.session_state.latitude
lon = st.session_state.longitude
location_name = ""
if st.session_state.location_data:
    location_name = f"{st.session_state.location_data.get('district', '')}, {st.session_state.location_data.get('state', '')}"

_loc_label = tr({"en": "📍 Location", "ta": "📍 இருப்பிடம்", "hi": "📍 स्थान", "te": "📍 స్థానం", "ml": "📍 സ്ഥാനം"})
st.markdown(f"**{_loc_label}:** {location_name} ({lat:.2f}°N, {lon:.2f}°E)")

col_btn, _ = st.columns([1, 3])
with col_btn:
    fetch = st.button(t("btn_get_weather", lang), type="primary")

if fetch:
    with st.spinner(tr({"en": "🌤 Fetching weather data...", "ta": "🌤 வானிலை தரவை பெறுகிறது...",
                        "hi": "🌤 मौसम डेटा प्राप्त हो रहा है...", "te": "🌤 వాతావరణ డేటా పొందుతోంది...",
                        "ml": "🌤 കാലാവസ്ഥ ഡേറ്റ ലഭ്യമാക്കുന്നു..."})):
        weather = get_current_weather(lat, lon)

    if weather:
        st.session_state.weather_data = weather
        st.success(tr({"en": "✅ Weather data updated!", "ta": "✅ வானிலை தரவு புதுப்பிக்கப்பட்டது!",
                       "hi": "✅ मौसम डेटा अपडेट हुआ!", "te": "✅ వాతావరణ డేటా నవీకరించబడింది!",
                       "ml": "✅ കാലാവസ്ഥ ഡേറ്റ അപ്‌ഡേറ്റ് ആയി!"}))
    else:
        st.error(tr({"en": "❌ Failed to fetch weather data.", "ta": "❌ வானிலை தரவு பெற தோல்வி.",
                     "hi": "❌ मौसम डेटा नहीं मिला।", "te": "❌ వాతావరణ డేటా పొందడం విఫలమైంది.",
                     "ml": "❌ കാലാവസ്ഥ ഡേറ്റ ലഭ്യമല്ല."}))
        st.stop()

weather = st.session_state.get("weather_data")
if not weather:
    st.info(tr({"en": "Click **Get Weather** to fetch current weather data.",
                "ta": "தற்போதைய வானிலை தரவை பெற **வானிலை பெறு** கிளிக் செய்யவும்.",
                "hi": "वर्तमान मौसम डेटा के लिए **मौसम प्राप्त करें** दबाएं।",
                "te": "ప్రస్తుత వాతావరణ డేటా కోసం **వాతావరణం పొందు** నొక్కండి.",
                "ml": "നിലവിലെ കാലാവസ్ഥ ഡേറ്റ നേടാൻ **കാലാവస്ഥ നേടുക** ക്ലിക്ക് ചെയ്യൂ."}))
    st.stop()

# ── Current Conditions ───────────────────────────────────────────────────
_cur_cond = tr({"en": "☀️ Current Conditions", "ta": "☀️ தற்போதைய நிலைகள்",
                "hi": "☀️ वर्तमान स्थिति", "te": "☀️ ప్రస్తుత పరిస్థితులు", "ml": "☀️ നിലവിലെ അവസ്ഥ"})
st.markdown(f"## {_cur_cond}")

icon = weather.get("weather_icon", "🌤")
desc = weather.get("weather_description", "")
st.markdown(f"### {icon} {desc}")

row1 = st.columns(4)
with row1[0]:
    st.metric(
        tr({"en": "🌡️ Temperature", "ta": "🌡️ வெப்பநிலை", "hi": "🌡️ तापमान", "te": "🌡️ ఉష్ణోగ్రత", "ml": "🌡️ താപനില"}),
        f"{weather['temperature']}°C",
        f"{tr({'en':'Feels like','ta':'உணர்வு','hi':'महसूस','te':'అనిపిస్తుంది','ml':'అనுഭვം'})} {weather.get('feels_like','--')}°C",
    )
with row1[1]:
    st.metric(tr({"en": "💧 Humidity", "ta": "💧 ஈரப்பதம்", "hi": "💧 आर्द्रता", "te": "💧 తేమ", "ml": "💧 ഈർപ്പം"}), f"{weather['humidity']}%")
with row1[2]:
    st.metric(tr({"en": "🌧️ Rainfall", "ta": "🌧️ மழைப்பொழிவு", "hi": "🌧️ वर्षा", "te": "🌧️ వర్షపాతం", "ml": "🌧️ മഴ"}), f"{weather['rainfall']} mm")
with row1[3]:
    wind_dir = get_wind_direction_name(weather.get("wind_direction", 0))
    st.metric(
        tr({"en": "💨 Wind Speed", "ta": "💨 காற்று வேகம்", "hi": "💨 हवा गति", "te": "💨 గాలి వేగం", "ml": "💨 കാറ്റ് വേഗം"}),
        f"{weather['wind_speed']} km/h",
        f"{tr({'en':'Direction','ta':'திசை','hi':'दिशा','te':'దిశ','ml':'ദിശ'})}: {wind_dir}",
    )

row2 = st.columns(4)
with row2[0]:
    st.metric(tr({"en": "🔵 Pressure", "ta": "🔵 அழுத்தம்", "hi": "🔵 दबाव", "te": "🔵 పీడనం", "ml": "🔵 മർദ്ദം"}), f"{weather.get('pressure','--')} hPa")
with row2[1]:
    uv = weather.get("uv_index", 0)
    uv_level, _ = get_uv_level(uv)
    st.metric(tr({"en": "☀️ UV Index", "ta": "☀️ UV குறியீடு", "hi": "☀️ UV सूचकांक", "te": "☀️ UV సూచిక", "ml": "☀️ UV സൂചിക"}),
              f"{uv}", f"{tr({'en':'Level','ta':'நிலை','hi':'स्तर','te':'స్థాయి','ml':'നില'})}: {uv_level}")
with row2[2]:
    st.metric(tr({"en": "☁️ Cloud Cover", "ta": "☁️ மேகமூட்டம்", "hi": "☁️ बादल आवरण", "te": "☁️ మేఘావరణం", "ml": "☁️ മേഘം"}), f"{weather.get('cloud_cover','--')}%")
with row2[3]:
    st.metric(tr({"en": "🌬️ Wind Gusts", "ta": "🌬️ காற்று சீற்றம்", "hi": "🌬️ हवा के झोंके", "te": "🌬️ గాలి ఉంట్లు", "ml": "🌬️ കാറ്റ് ചുഴലി"}), f"{weather.get('wind_gusts','--')} km/h")

# ── Soil Conditions ──────────────────────────────────────────────────────
st.markdown("---")
_soil_cond = tr({"en": "🌱 Soil Conditions", "ta": "🌱 மண் நிலைகள்", "hi": "🌱 मिट्टी की स्थिति", "te": "🌱 నేల పరిస్థితులు", "ml": "🌱 മണ്ണ് അവസ്ഥ"})
st.markdown(f"## {_soil_cond}")

soil_cols = st.columns(2)
with soil_cols[0]:
    st.metric(tr({"en": "🌡️ Soil Temperature", "ta": "🌡️ மண் வெப்பநிலை", "hi": "🌡️ मिट्टी तापमान", "te": "🌡️ నేల ఉష్ణోగ్రత", "ml": "🌡️ മണ്ണ് ഊഷ്മാവ്"}),
              f"{weather.get('soil_temperature','--')}°C")
with soil_cols[1]:
    st.metric(tr({"en": "💧 Soil Moisture", "ta": "💧 மண் ஈரப்பதம்", "hi": "💧 मिट्टी नमी", "te": "💧 నేల తేమ", "ml": "💧 മണ്ണ് ഈർപ്പം"}),
              f"{weather.get('soil_moisture','--')}%")

# ── 7-Day Forecast ───────────────────────────────────────────────────────
st.markdown("---")
_forecast_title = tr({"en": "📅 7-Day Weather Forecast", "ta": "📅 7-நாள் வானிலை முன்னறிவிப்பு",
                       "hi": "📅 7-दिवसीय मौसम पूर्वानुमान", "te": "📅 7-రోజుల వాతావరణ అంచనా",
                       "ml": "📅 7-ദിവസ കാലാവസ്ഥ പ്രവചനം"})
st.markdown(f"## {_forecast_title}")

forecast = weather.get("forecast", [])
if forecast:
    forecast_cols = st.columns(min(7, len(forecast)))
    for idx, day in enumerate(forecast):
        if idx < 7:
            with forecast_cols[idx]:
                temp_max = day.get("temp_max", 0)
                temp_color = "#FF5722" if temp_max > 35 else ("#FF9800" if temp_max > 28 else "#4CAF50")
                rain = day.get("rain", 0) or 0
                rain_icon = "🌧️" if rain > 5 else ("🌦️" if rain > 0 else "☀️")
                st.markdown(f"""
                <div style='background:rgba(17,29,51,0.85);border:1px solid rgba(76,175,80,0.2);
                border-radius:12px;padding:0.8rem;text-align:center;min-height:200px;'>
                    <p style='color:#81C784;font-weight:600;margin:0 0 4px;'>{day.get('day_name','')}</p>
                    <p style='font-size:1.5rem;margin:4px 0;'>{rain_icon}</p>
                    <p style='color:{temp_color};font-weight:700;font-size:1.2rem;margin:4px 0;'>{day.get('temp_max','--')}°</p>
                    <p style='color:#78909C;font-size:0.85rem;margin:2px 0;'>↓ {day.get('temp_min','--')}°</p>
                    <p style='color:#4FC3F7;font-size:0.75rem;margin:4px 0;'>🌧 {rain:.1f}mm</p>
                    <p style='color:#78909C;font-size:0.7rem;margin:2px 0;'>💨 {day.get('wind_speed_max','--')} km/h</p>
                </div>""", unsafe_allow_html=True)

    # ── Charts ───────────────────────────────────────────────────────────
    st.markdown("---")
    _charts_title = tr({"en": "📈 Weather Charts", "ta": "📈 வானிலை விளக்கப்படங்கள்",
                         "hi": "📈 मौसम चार्ट", "te": "📈 వాతావరణ చార్ట్‌లు", "ml": "📈 കാലാவസ്ഥ ചാർട്ടുകൾ"})
    st.markdown(f"## {_charts_title}")

    tab_labels = [
        tr({"en": "🌡 Temperature", "ta": "🌡 வெப்பநிலை", "hi": "🌡 तापमान", "te": "🌡 ఉష్ణోగ్రత", "ml": "🌡 താപനില"}),
        tr({"en": "🌧 Precipitation", "ta": "🌧 மழைப்பொழிவு", "hi": "🌧 वर्षा", "te": "🌧 వర్షపాతం", "ml": "🌧 മഴ"}),
        tr({"en": "📊 Hourly Today", "ta": "📊 இன்றைய மணி", "hi": "📊 आज का घंटेवार", "te": "📊 ఈరోజు గంటవారీ", "ml": "📊 ഇന്നത്തെ മണിക്കൂർ"}),
    ]
    chart_tab1, chart_tab2, chart_tab3 = st.tabs(tab_labels)

    dates = [d["date"] for d in forecast]

    with chart_tab1:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=dates, y=[d["temp_max"] for d in forecast], mode="lines+markers",
            name=tr({"en":"Max Temp","ta":"அதிகபட்ச வெப்பம்","hi":"अधिकतम तापमान","te":"గరిష్ట ఉష్ణోగ్రత","ml":"പരമാവധി ഉഷ്ണം"}),
            line=dict(color="#FF5722", width=3), marker=dict(size=8)))
        fig.add_trace(go.Scatter(x=dates, y=[d["temp_min"] for d in forecast], mode="lines+markers",
            name=tr({"en":"Min Temp","ta":"குறைந்தபட்ச வெப்பம்","hi":"न्यूनतम तापमान","te":"కనిష్ట ఉష్ణోగ్రత","ml":"കുറഞ്ഞ ഉഷ്ണം"}),
            line=dict(color="#2196F3", width=3), marker=dict(size=8)))
        fig.update_layout(
            title=tr({"en":"7-Day Temperature Forecast","ta":"7-நாள் வெப்பநிலை முன்னறிவிப்பு","hi":"7-दिवसीय तापमान पूर्वानुमान","te":"7-రోజుల ఉష్ణోగ్రత అంచనా","ml":"7-ദിവസ ഊഷ്മാവ് പ്രവചനം"}),
            yaxis_title=tr({"en":"Temperature (°C)","ta":"வெப்பநிலை (°C)","hi":"तापमान (°C)","te":"ఉష్ణోగ్రత (°C)","ml":"ഊഷ്മാവ് (°C)"}),
            template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=400)
        st.plotly_chart(fig, use_container_width=True)

    with chart_tab2:
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(x=dates, y=[d.get("rain", 0) or 0 for d in forecast],
            name=tr({"en":"Rainfall","ta":"மழைப்பொழிவு","hi":"वर्षा","te":"వర్షపాతం","ml":"മഴ"}),
            marker_color="#2196F3"))
        fig2.update_layout(
            title=tr({"en":"7-Day Rainfall Forecast","ta":"7-நாள் மழை முன்னறிவிப்பு","hi":"7-दिवसीय वर्षा पूर्वानुमान","te":"7-రోజుల వర్షపాత అంచనా","ml":"7-ദിവസ മഴ പ്രവചനം"}),
            yaxis_title=tr({"en":"Rainfall (mm)","ta":"மழை (மி.மீ.)","hi":"वर्षा (मिमी)","te":"వర్షపాతం (మి.మీ.)","ml":"മഴ (mm)"}),
            template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=400)
        st.plotly_chart(fig2, use_container_width=True)

    with chart_tab3:
        hourly_temp = weather.get("hourly_temperature", [])
        hourly_humidity = weather.get("hourly_humidity", [])
        if hourly_temp:
            hours = list(range(len(hourly_temp)))
            fig3 = go.Figure()
            fig3.add_trace(go.Scatter(x=hours, y=hourly_temp, mode="lines",
                name=tr({"en":"Temperature (°C)","ta":"வெப்பநிலை (°C)","hi":"तापमान (°C)","te":"ఉష్ణోగ్రత (°C)","ml":"ഊഷ്മാവ് (°C)"}),
                line=dict(color="#FF9800", width=2)))
            fig3.add_trace(go.Scatter(x=hours, y=hourly_humidity, mode="lines",
                name=tr({"en":"Humidity (%)","ta":"ஈரப்பதம் (%)","hi":"आर्द्रता (%)","te":"తేమ (%)","ml":"ഈർപ്പം (%)"}),
                line=dict(color="#2196F3", width=2), yaxis="y2"))
            fig3.update_layout(
                title=tr({"en":"Today's Hourly Temp & Humidity","ta":"இன்றைய மணிக்கணக்கான வெப்பம் & ஈரப்பதம்","hi":"आज का घंटेवार तापमान & आर्द्रता","te":"ఈరోజు గంటవారీ ఉష్ణోగ్రత & తేమ","ml":"ഇന്ന് മണിക്കൂർ ഊഷ്മാവ് & ഈർപ്പം"}),
                xaxis_title=tr({"en":"Hour","ta":"மணி","hi":"घंटा","te":"గంట","ml":"മണിക്കൂർ"}),
                yaxis=dict(title=tr({"en":"Temperature (°C)","ta":"வெப்பநிலை","hi":"तापमान","te":"ఉష్ణోగ్రత","ml":"ഊഷ്മാവ്"}), side="left"),
                yaxis2=dict(title=tr({"en":"Humidity (%)","ta":"ஈரப்பதம்","hi":"आर्द्रता","te":"తేమ","ml":"ഈർപ്പം"}), side="right", overlaying="y"),
                template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=400)
            st.plotly_chart(fig3, use_container_width=True)

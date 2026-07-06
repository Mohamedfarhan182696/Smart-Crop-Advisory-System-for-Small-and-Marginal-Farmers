"""
🌾 Crop Advisor Page
======================
AI-powered crop recommendations — fully multilingual.
"""

import streamlit as st
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.sidebar import render_sidebar
render_sidebar()

import plotly.graph_objects as go
from config.languages import t
from backend.services.crop_service import recommend_crops
from utils.helpers import format_currency

lang = st.session_state.get("lang_code", "en")
def tr(d): return d.get(lang, d.get("en", ""))

st.markdown(f"# {t('page_crop', lang)}")
st.markdown("---")

# ── Check Prerequisites ──────────────────────────────────────────────────
if not st.session_state.get("soil_data"):
    st.warning(tr({"en": "⚠️ Please complete the **Soil Analysis** page first.",
                   "ta": "⚠️ முதலில் **மண் பகுப்பாய்வு** பக்கத்தை முடிக்கவும்.",
                   "hi": "⚠️ कृपया पहले **मृदा विश्लेषण** पेज पूरा करें।",
                   "te": "⚠️ దయచేసి ముందుగా **నేల విశ్లేషణ** పేజీ పూర్తి చేయండి.",
                   "ml": "⚠️ ആദ്യം **മണ്ണ് വിശകലനം** പേജ് പൂർത്തിയാക്കുക."}))
    st.stop()

soil = st.session_state.soil_data
weather = st.session_state.get("weather_data")
if not isinstance(weather, dict):
    weather = {}
temperature = weather.get("temperature", 28.0)
if temperature is None:
    temperature = 28.0
humidity = weather.get("humidity", 65.0)
if humidity is None:
    humidity = 65.0
raw_rainfall = weather.get("rainfall")
rainfall = raw_rainfall if raw_rainfall is not None and raw_rainfall > 0 else 150.0

# ── Input Summary ────────────────────────────────────────────────────────
with st.expander(t("crop_input_params", lang), expanded=False):
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("N", f"{soil['nitrogen']} kg/ha")
    c2.metric("P", f"{soil['phosphorus']} kg/ha")
    c3.metric("K", f"{soil['potassium']} kg/ha")
    c4.metric("pH", f"{soil['ph']}")

    c5, c6, c7, c8 = st.columns(4)
    c5.metric(tr({"en":"🌡️ Temp","ta":"🌡️ வெப்பம்","hi":"🌡️ तापमान","te":"🌡️ ఉష్ణోగ్రత","ml":"🌡️ ഊഷ്മാവ്"}), f"{temperature}°C")
    c6.metric(tr({"en":"💧 Humidity","ta":"💧 ஈரப்பதம்","hi":"💧 आर्द्रता","te":"💧 తేమ","ml":"💧 ഈർപ്പം"}), f"{humidity}%")
    c7.metric(tr({"en":"🌧️ Rainfall","ta":"🌧️ மழை","hi":"🌧️ वर्षा","te":"🌧️ వర్షపాతం","ml":"🌧️ മഴ"}), f"{rainfall} mm")
    c8.metric(tr({"en":"🌍 Soil","ta":"🌍 மண்","hi":"🌍 मिट्टी","te":"🌍 నేల","ml":"🌍 മണ്ണ്"}), soil["soil_type"])

# ── Get Recommendations ──────────────────────────────────────────────────
if st.button(t("btn_get_recommendations", lang), type="primary"):
    with st.spinner(tr({"en":"🤖 AI is analyzing your conditions...","ta":"🤖 AI உங்கள் நிலைகளை பகுப்பாய்கிறது...",
                        "hi":"🤖 AI आपकी स्थितियों का विश्लेषण कर रहा है...","te":"🤖 AI మీ పరిస్థితులు విశ్లేషిస్తోంది...",
                        "ml":"🤖 AI നിങ്ങളുടെ അവസ്ഥകൾ വിശകലനം ചെയ്യുന്നു..."})):
        loc = st.session_state.get("location_data", {})
        recommendations = recommend_crops(
            nitrogen=soil["nitrogen"], phosphorus=soil["phosphorus"],
            potassium=soil["potassium"], temperature=temperature,
            humidity=humidity, ph=soil["ph"], rainfall=rainfall,
            soil_type=soil["soil_type"], water_availability=soil["water_availability"],
            top_n=5, state=loc.get("state"), district=loc.get("district"),
        )

    if recommendations:
        st.session_state.crop_recommendations = recommendations
        found_msg = tr({"en": f"✅ Found {len(recommendations)} crop recommendations!",
                        "ta": f"✅ {len(recommendations)} பயிர் பரிந்துரைகள் கிடைத்தன!",
                        "hi": f"✅ {len(recommendations)} फसल सिफारिशें मिलीं!",
                        "te": f"✅ {len(recommendations)} పంట సిఫారసులు లభించాయి!",
                        "ml": f"✅ {len(recommendations)} വിള ശുപാർശകൾ കിട്ടി!"})
        st.success(found_msg)
    else:
        st.error(tr({"en":"❌ Could not generate recommendations.","ta":"❌ பரிந்துரைகளை உருவாக்க முடியவில்லை.",
                     "hi":"❌ सिफारिशें नहीं मिलीं।","te":"❌ సిఫారసులు రాలేదు.","ml":"❌ ശുപാർശകൾ ലഭ്യമല്ല."}))

# ── Display Recommendations ──────────────────────────────────────────────
recommendations = st.session_state.get("crop_recommendations")

if recommendations:
    st.markdown("---")
    st.markdown(f"## {t('crop_top_recommendations', lang)}")

    _match_lbl = t("crop_match", lang)
    _why_lbl   = tr({"en":"🔍 Why this crop:","ta":"🔍 ஏன் இந்த பயிர்:","hi":"🔍 यह फसल क्यों:","te":"🔍 ఈ పంట ఎందుకు:","ml":"🔍 ഈ വിള ഏക്കം:"})
    _irr_lbl   = tr({"en":"💧 Irrigation:","ta":"💧 நீர்ப்பாசனம்:","hi":"💧 सिंचाई:","te":"💧 నీటిపారుదల:","ml":"💧 ജലസേചനം:"})
    _days_lbl  = tr({"en":"days","ta":"நாட்கள்","hi":"दिन","te":"రోజులు","ml":"ദിവസങ്ങൾ"})
    _sel_lbl   = t("btn_select_crop", lang)
    _sel_ok    = tr({"en":"✅ selected! Go to Irrigation or Fertilizer page.","ta":"✅ தேர்ந்தெடுக்கப்பட்டது! நீர்ப்பாசன அல்லது உர பக்கத்திற்கு செல்லவும்.",
                     "hi":"✅ चयनित! सिंचाई या उर्वरक पेज पर जाएं।","te":"✅ ఎంచుకున్నారు! నీటిపారుదల లేదా ఎరువు పేజీకి వెళ్ళండి.",
                     "ml":"✅ തിരഞ്ഞെടുത്തു! ജലസേചന അല്ലെങ്കിൽ വള പേജിലേക്ക് പോകൂ."})

    for idx, crop in enumerate(recommendations):
        score = crop["suitability_score"]
        border_color = "rgba(76,175,80,0.4)" if score >= 70 else ("rgba(255,152,0,0.4)" if score >= 40 else "rgba(244,67,54,0.4)")
        gradient = "#1B5E20, #4CAF50" if score >= 70 else ("#E65100, #FF9800" if score >= 40 else "#B71C1C, #F44336")
        rank_emoji = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"][idx]

        st.markdown(f"""
        <div style='background:rgba(17,29,51,0.85);border:1px solid {border_color};
        border-left:4px solid {border_color.replace("0.4","1")};border-radius:16px;padding:1.5rem;margin-bottom:1rem;'>
            <div style='display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;'>
                <h3 style='color:#E8F5E9;margin:0;'>{rank_emoji} {crop['crop_name']}</h3>
                <span style='background:linear-gradient(135deg,{gradient});color:white;padding:0.3rem 1rem;border-radius:20px;font-weight:700;'>
                    {score}{_match_lbl}
                </span>
            </div>
        </div>""", unsafe_allow_html=True)

        details_lbl = tr({"en":f"📋 Details — {crop['crop_name']}","ta":f"📋 விவரங்கள் — {crop['crop_name']}",
                          "hi":f"📋 विवरण — {crop['crop_name']}","te":f"📋 వివరాలు — {crop['crop_name']}",
                          "ml":f"📋 വിശദാംശം — {crop['crop_name']}"})
        with st.expander(details_lbl, expanded=(idx == 0)):
            d1, d2, d3, d4 = st.columns(4)
            d1.metric(t("confidence", lang), f"{crop['confidence']}%")
            d2.metric(t("crop_duration", lang), f"{crop['duration_days']} {_days_lbl}")
            d3.metric(t("season", lang), crop["season"])
            d4.metric(t("market_demand", lang), crop["market_demand"])

            d5, d6, d7, d8 = st.columns(4)
            d5.metric(t("water_requirement", lang), f"{crop['water_requirement_mm']} mm")
            d6.metric(t("expected_yield", lang), crop["estimated_yield"])
            d7.metric(t("estimated_profit", lang), format_currency(crop["estimated_profit"]))
            d8.metric(t("roi", lang), f"{crop['roi_percentage']}%")

            if crop.get("reasons"):
                st.markdown(f"**{_why_lbl}**")
                for reason in crop["reasons"]:
                    st.markdown(f"  ✅ {reason}")

            st.markdown(f"**{_irr_lbl}** {crop['irrigation_method']} — {crop['irrigation_frequency']}")

            if st.button(_sel_lbl, key=f"select_{idx}", type="primary"):
                st.session_state.selected_crop = crop["crop_name"]
                st.session_state.selected_crop_data = crop
                st.success(f"✅ **{crop['crop_name']}** {_sel_ok}")

    # ── Comparison Radar Chart ────────────────────────────────────────────
    st.markdown("---")
    st.markdown(f"## {t('crop_comparison', lang)}")

    cat_labels = [
        tr({"en":"Suitability","ta":"பொருத்தம்","hi":"उपयुक्तता","te":"అనుకూలత","ml":"അനുകൂലത"}),
        tr({"en":"Yield","ta":"மகசூல்","hi":"उपज","te":"దిగుబడి","ml":"വിളവ്"}),
        tr({"en":"Profit","ta":"லாபம்","hi":"लाभ","te":"లాభం","ml":"ലാഭം"}),
        tr({"en":"Water Eff.","ta":"நீர் திறன்","hi":"जल दक्षता","te":"నీటి సామర్ధ్యం","ml":"ജല ക്ഷമത"}),
        tr({"en":"Demand","ta":"தேவை","hi":"मांग","te":"డిమాండ్","ml":"ഡിമാൻഡ്"}),
    ]
    fig = go.Figure()
    for crop in recommendations[:5]:
        demand_score = {"High": 90, "Medium": 60, "Low": 30}.get(crop["market_demand"], 50)
        water_eff = max(0, 100 - (crop["water_requirement_mm"] / 20))
        yield_score = min(100, float(crop["estimated_yield"].split()[0]) * 5)
        profit_score = min(100, max(0, crop["roi_percentage"]))
        values = [crop["suitability_score"], yield_score, profit_score, water_eff, demand_score]
        values.append(values[0])
        fig.add_trace(go.Scatterpolar(r=values, theta=cat_labels + [cat_labels[0]], fill="toself",
                                      name=crop["crop_name"], opacity=0.6))
    fig.update_layout(
        polar=dict(bgcolor="rgba(0,0,0,0)", radialaxis=dict(visible=True, range=[0, 100], showticklabels=False)),
        showlegend=True, template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", height=500,
        title=tr({"en":"Crop Comparison Radar","ta":"பயிர் ஒப்பீடு ரேடார்","hi":"फसल तुलना रडार","te":"పంట పోలిక రాడార్","ml":"വിള താരതമ്യ റഡാർ"}),
    )
    st.plotly_chart(fig, use_container_width=True)

else:
    st.info(tr({"en":"👆 Click **Get Crop Recommendations** to receive AI-powered crop suggestions.",
                "ta":"👆 AI-ஆல் இயக்கப்படும் பயிர் பரிந்துரைகளைப் பெற **பயிர் பரிந்துரைகளை பெறு** கிளிக் செய்யவும்.",
                "hi":"👆 AI-संचालित फसल सुझाव के लिए **फसल सिफारिशें प्राप्त करें** दबाएं।",
                "te":"👆 AI-ఆధారిత పంట సూచనలు పొందడానికి **పంట సిఫారసులు పొందు** నొక్కండి.",
                "ml":"👆 AI-ഓണ്‍ ഓടിക്കുന്ന വിള നിർദേശങ്ങൾ ലഭ്യമാക്കാൻ **വിള ശുപാർശകൾ നേടുക** ക്ലിക്ക് ചെയ്യൂ."}))

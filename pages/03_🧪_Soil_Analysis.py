"""
🧪 Soil Analysis Page
========================
Input form for soil nutrients with validation.
"""

import streamlit as st
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.sidebar import render_sidebar
render_sidebar()

from config.languages import t, get_soil_types, SOIL_TYPE_MAP
from utils.validators import validate_soil_inputs
from backend.services.soil_service import get_location_soil_data

lang = st.session_state.get("lang_code", "en")
st.markdown(f"# {t('page_soil', lang)}")
st.markdown("---")

st.markdown("""
Enter your soil test values below. If you don't have a soil test report, 
you can get one from the nearest **Soil Health Card center** or estimate values based on your soil type.
""")

# Initialize form defaults from saved soil_data or standard defaults
if "soil_n" not in st.session_state:
    if st.session_state.get("soil_data"):
        sd = st.session_state.soil_data
        st.session_state.soil_n = sd["nitrogen"]
        st.session_state.soil_p = sd["phosphorus"]
        st.session_state.soil_k = sd["potassium"]
        st.session_state.soil_ph = sd["ph"]
        st.session_state.soil_moisture = sd["moisture"]
        st.session_state.soil_water = sd["water_availability"]
        st.session_state.soil_type_selected = sd["soil_type"]
    else:
        st.session_state.soil_n = 50.0
        st.session_state.soil_p = 40.0
        st.session_state.soil_k = 40.0
        st.session_state.soil_ph = 6.5
        st.session_state.soil_moisture = 50.0
        st.session_state.soil_water = 500.0
        st.session_state.soil_type_selected = "Loamy Soil"

# ── Smart Soil Autofill Card ─────────────────────────────────────────────
if st.session_state.get("location_data"):
    loc = st.session_state.location_data
    district = loc.get("district", "Unknown")
    state_name = loc.get("state", "Unknown")
    
    st.markdown(
        f"""
        <div style='
            background: rgba(76, 175, 80, 0.1);
            border: 1px solid rgba(76, 175, 80, 0.3);
            border-radius: 12px;
            padding: 1.2rem;
            margin-bottom: 1.5rem;
        '>
            <h4 style='color: #81C784; margin: 0 0 0.5rem;'>📡 Location-Wise Soil Autofill Available</h4>
            <p style='color: #A5D6A7; font-size: 0.85rem; margin: 0 0 0.75rem;'>
                We detected your location as <b>{district}, {state_name}</b>. 
                You can auto-load typical local soil nutrient profiles and global satellite estimates for this area.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    if st.button("🪄 Autofill Location Soil Data", key="autofill_soil_btn", type="secondary"):
        with st.spinner("🤖 Retrieving location soil properties..."):
            soil_data = get_location_soil_data(
                latitude=st.session_state.get("latitude"),
                longitude=st.session_state.get("longitude"),
                state=state_name
            )
            
            if soil_data:
                st.session_state.soil_n = soil_data["nitrogen"]
                st.session_state.soil_p = soil_data["phosphorus"]
                st.session_state.soil_k = soil_data["potassium"]
                st.session_state.soil_ph = soil_data["ph"]
                st.session_state.soil_moisture = soil_data["moisture"]
                st.session_state.soil_water = soil_data["water_availability"]
                st.session_state.soil_type_selected = soil_data["soil_type"]
                
                # Also save directly to soil_data
                st.session_state.soil_data = soil_data
                
                st.success("✅ Soil values loaded successfully! Review the values below and click Analyze.")
                st.rerun()
            else:
                st.error("❌ Failed to fetch soil properties for this location.")

# ── Soil Input Form ──────────────────────────────────────────────────────
with st.form("soil_form", clear_on_submit=False):
    st.markdown("### 🧪 Soil Nutrient Values")

    col1, col2, col3 = st.columns(3)

    with col1:
        nitrogen = st.number_input(
            t("label_nitrogen", lang),
            min_value=0.0, max_value=200.0,
            value=st.session_state.soil_n,
            step=1.0,
            help="Typical range: 0-140 kg/ha. Get from soil test report.",
        )
        ph = st.number_input(
            t("label_ph", lang),
            min_value=0.0, max_value=14.0,
            value=st.session_state.soil_ph,
            step=0.1,
            help="Neutral pH is 7.0. Most crops prefer 5.5-7.5.",
        )

    with col2:
        phosphorus = st.number_input(
            t("label_phosphorus", lang),
            min_value=0.0, max_value=200.0,
            value=st.session_state.soil_p,
            step=1.0,
            help="Typical range: 0-145 kg/ha.",
        )
        moisture = st.number_input(
            t("label_moisture", lang),
            min_value=0.0, max_value=100.0,
            value=st.session_state.soil_moisture,
            step=1.0,
            help="Soil moisture percentage (0-100%).",
        )

    with col3:
        potassium = st.number_input(
            t("label_potassium", lang),
            min_value=0.0, max_value=250.0,
            value=st.session_state.soil_k,
            step=1.0,
            help="Typical range: 0-205 kg/ha.",
        )
        water_availability = st.number_input(
            t("label_water_availability", lang),
            min_value=0.0, max_value=5000.0,
            value=st.session_state.soil_water,
            step=10.0,
            help="Total water availability for the season (mm).",
        )

    st.markdown("### 🌍 Soil Type")
    soil_types_localized = get_soil_types(lang)
    
    # Map back to find the localized name index of the preset soil type
    default_soil_type_localized = t("soil_loamy", lang)
    for st_local in soil_types_localized:
        if SOIL_TYPE_MAP.get(st_local) == st.session_state.soil_type_selected:
            default_soil_type_localized = st_local
            break

    soil_type_selected = st.selectbox(
        t("label_soil_type", lang),
        options=soil_types_localized,
        index=soil_types_localized.index(default_soil_type_localized),
        help="Select the predominant soil type in your field.",
    )

    # Map localized name back to English
    soil_type_english = SOIL_TYPE_MAP.get(soil_type_selected, "Loamy Soil")

    submitted = st.form_submit_button(t("btn_analyze", lang), type="primary")

if submitted:
    # Validate inputs
    is_valid, errors = validate_soil_inputs(
        nitrogen, phosphorus, potassium, ph, moisture,
        water_availability, soil_type_english,
    )

    if not is_valid:
        for error in errors:
            st.error(f"❌ {error}")
    else:
        # Store soil data in session state
        st.session_state.soil_data = {
            "nitrogen": nitrogen,
            "phosphorus": phosphorus,
            "potassium": potassium,
            "ph": ph,
            "moisture": moisture,
            "water_availability": water_availability,
            "soil_type": soil_type_english,
        }
        # Update inputs defaults as well
        st.session_state.soil_n = nitrogen
        st.session_state.soil_p = phosphorus
        st.session_state.soil_k = potassium
        st.session_state.soil_ph = ph
        st.session_state.soil_moisture = moisture
        st.session_state.soil_water = water_availability
        st.session_state.soil_type_selected = soil_type_english

        st.success("✅ Soil data saved! Go to **Crop Advisor** page for AI recommendations.")

        # Display soil health summary
        st.markdown("---")
        st.markdown("## 🧪 Soil Health Summary")

        health_cols = st.columns(4)
        with health_cols[0]:
            n_status = "🟢 Good" if 40 <= nitrogen <= 120 else ("🟡 Low" if nitrogen < 40 else "🔴 High")
            st.metric("Nitrogen (N)", f"{nitrogen} kg/ha", n_status)
        with health_cols[1]:
            p_status = "🟢 Good" if 25 <= phosphorus <= 100 else ("🟡 Low" if phosphorus < 25 else "🔴 High")
            st.metric("Phosphorus (P)", f"{phosphorus} kg/ha", p_status)
        with health_cols[2]:
            k_status = "🟢 Good" if 20 <= potassium <= 150 else ("🟡 Low" if potassium < 20 else "🔴 High")
            st.metric("Potassium (K)", f"{potassium} kg/ha", k_status)
        with health_cols[3]:
            ph_status = "🟢 Neutral" if 6.0 <= ph <= 7.5 else ("🟡 Acidic" if ph < 6.0 else "🔴 Alkaline")
            st.metric("Soil pH", f"{ph}", ph_status)

        # Soil type info
        st.info(f"🌍 **Soil Type:** {soil_type_english} | 💧 **Moisture:** {moisture}% | 💦 **Water:** {water_availability} mm/season")

# ── Quick Presets ────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### 📋 Quick Presets (Common Soil Profiles)")

preset_cols = st.columns(3)
presets = {
    "Rice Paddy": {"N": 80, "P": 50, "K": 40, "ph": 6.0, "moisture": 80, "water": 1200, "soil": "Clay Soil"},
    "Wheat Field": {"N": 90, "P": 65, "K": 60, "ph": 7.0, "moisture": 40, "water": 400, "soil": "Loamy Soil"},
    "Cotton Field": {"N": 110, "P": 50, "K": 20, "ph": 7.5, "moisture": 35, "water": 600, "soil": "Black Soil"},
}

for idx, (name, vals) in enumerate(presets.items()):
    with preset_cols[idx]:
        st.markdown(
            f"""
            <div style='
                background: rgba(17, 29, 51, 0.85);
                border: 1px solid rgba(76, 175, 80, 0.2);
                border-radius: 12px;
                padding: 1rem;
            '>
                <h4 style='color: #81C784; margin: 0 0 0.5rem;'>🌱 {name}</h4>
                <p style='color: #A5D6A7; font-size: 0.8rem; margin: 0;'>
                    N:{vals['N']} P:{vals['P']} K:{vals['K']} pH:{vals['ph']}<br/>
                    {vals['soil']} | Water: {vals['water']}mm
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button(f"Use {name}", key=f"preset_{idx}"):
            st.session_state.soil_n = vals["N"]
            st.session_state.soil_p = vals["P"]
            st.session_state.soil_k = vals["K"]
            st.session_state.soil_ph = vals["ph"]
            st.session_state.soil_moisture = vals["moisture"]
            st.session_state.soil_water = vals["water"]
            st.session_state.soil_type_selected = vals["soil"]
            st.session_state.soil_data = {
                "nitrogen": vals["N"], "phosphorus": vals["P"],
                "potassium": vals["K"], "ph": vals["ph"],
                "moisture": vals["moisture"],
                "water_availability": vals["water"],
                "soil_type": vals["soil"],
            }
            st.rerun()

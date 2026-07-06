"""
🧫 Fertilizer Recommendation Page
====================================
Organic, chemical, and bio-fertilizer recommendations with costs and schedule.
"""

import streamlit as st
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.sidebar import render_sidebar
render_sidebar()

import plotly.graph_objects as go
from config.languages import t
from backend.services.fertilizer_service import recommend_fertilizers
from utils.helpers import format_currency
from utils.constants import CROP_DATABASE

lang = st.session_state.get("lang_code", "en")
st.markdown(f"# {t('page_fertilizer', lang)}")
st.markdown("---")

# ── Check Prerequisites ──────────────────────────────────────────────────
soil = st.session_state.get("soil_data")
selected_crop = st.session_state.get("selected_crop")

if not soil:
    st.warning("⚠️ Please complete the **Soil Analysis** page first.")
    st.stop()

# ── Crop Selection ──────────────────────────────────────────────────────
crop_names = [v["name"] for v in CROP_DATABASE.values()]
default_idx = crop_names.index(selected_crop) if selected_crop in crop_names else 0
crop_choice = st.selectbox("Select Crop:", crop_names, index=default_idx)

area = st.number_input("Farm Area (hectares):", min_value=0.1, max_value=100.0, value=1.0, step=0.1)

if st.button("🧫 Get Fertilizer Recommendations", type="primary"):
    with st.spinner("🤖 Analyzing soil nutrients..."):
        result = recommend_fertilizers(
            crop_name=crop_choice,
            nitrogen=soil["nitrogen"],
            phosphorus=soil["phosphorus"],
            potassium=soil["potassium"],
            ph=soil["ph"],
            soil_type=soil["soil_type"],
            area_hectares=area,
        )

    if result:
        st.session_state.fertilizer_data = result
        st.success("✅ Fertilizer recommendations ready!")

# ── Display Results ─────────────────────────────────────────────────────
fert_data = st.session_state.get("fertilizer_data")

if fert_data:
    st.markdown("---")

    # ── Nutrient Analysis ────────────────────────────────────────────────
    st.markdown("## 🧪 Soil Nutrient Analysis")
    analysis = fert_data.get("nutrient_analysis", {})

    na1, na2, na3 = st.columns(3)
    for col, (nutrient, data) in zip([na1, na2, na3], analysis.items()):
        with col:
            status_emoji = "🟢" if data["status"] == "Adequate" else ("🟡" if data["status"] == "Low" else "🔴")
            st.metric(
                f"{nutrient.title()} ({status_emoji} {data['status']})",
                f"{data['current']} kg/ha",
                f"Ideal: {data['ideal']} | Gap: {data['deficit']:.0f}",
            )

    st.markdown(f"**📈 Expected Improvement:** {fert_data.get('expected_improvement', 'N/A')}")
    st.markdown(f"**💰 Total Estimated Cost:** {fert_data.get('total_cost_formatted', 'N/A')}")

    # ── Fertilizer Recommendations by Type ───────────────────────────────
    st.markdown("---")
    tab_org, tab_chem, tab_bio = st.tabs(["🌿 Organic", "⚗️ Chemical", "🦠 Bio-Fertilizer"])

    with tab_org:
        st.markdown("### 🌿 Organic Fertilizer Recommendations")
        for fert in fert_data.get("organic", []):
            with st.expander(f"🌿 {fert['name']} — {fert['quantity_per_ha_kg']} kg/ha"):
                c1, c2, c3 = st.columns(3)
                c1.metric("📦 Total Quantity", f"{fert['total_quantity_kg']} kg")
                c2.metric("💰 Cost/kg", f"₹{fert['cost_per_kg']}")
                c3.metric("💰 Total Cost", format_currency(fert['total_cost']))

                st.markdown(f"**📋 Method:** {fert['application_method']}")
                st.markdown(f"**⏰ Timing:** {fert['application_timing']}")
                st.markdown(f"**✅ Benefit:** {fert['benefit']}")
                st.markdown(f"**🎯 Relevance:** {fert['relevance']}")

    with tab_chem:
        st.markdown("### ⚗️ Chemical Fertilizer Recommendations")
        if not fert_data.get("chemical"):
            st.info("No chemical fertilizer needed — soil nutrients are adequate!")
        for fert in fert_data.get("chemical", []):
            with st.expander(f"⚗️ {fert['name']} — {fert['quantity_per_ha_kg']} kg/ha"):
                c1, c2, c3 = st.columns(3)
                c1.metric("📦 Total Quantity", f"{fert['total_quantity_kg']} kg")
                c2.metric("💰 Cost/kg", f"₹{fert['cost_per_kg']}")
                c3.metric("💰 Total Cost", format_currency(fert['total_cost']))

                st.markdown(f"**📋 Method:** {fert['application_method']}")
                st.markdown(f"**⏰ Timing:** {fert['application_timing']}")
                st.markdown(f"**🎯 Why:** {fert['relevance']}")

    with tab_bio:
        st.markdown("### 🦠 Bio-Fertilizer Recommendations")
        for fert in fert_data.get("bio", []):
            with st.expander(f"🦠 {fert['name']} — {fert['quantity_per_ha_kg']} kg/ha"):
                c1, c2, c3 = st.columns(3)
                c1.metric("📦 Total Quantity", f"{fert['total_quantity_kg']} kg")
                c2.metric("💰 Cost/kg", f"₹{fert['cost_per_kg']}")
                c3.metric("💰 Total Cost", format_currency(fert['total_cost']))

                st.markdown(f"**📋 Method:** {fert['application_method']}")
                st.markdown(f"**✅ Benefit:** {fert['benefit']}")
                st.markdown(f"**🎯 Relevance:** {fert['relevance']}")

    # ── Application Schedule ─────────────────────────────────────────────
    st.markdown("---")
    st.markdown("## 📅 Application Schedule")

    schedule = fert_data.get("schedule", [])
    if schedule:
        for step in schedule:
            st.markdown(
                f"""
                <div style='
                    background: rgba(17, 29, 51, 0.85);
                    border-left: 3px solid #4CAF50;
                    border-radius: 8px;
                    padding: 0.8rem 1rem;
                    margin-bottom: 0.5rem;
                '>
                    <span style='color: #81C784; font-weight: 600;'>Day {step['day']}</span>
                    <span style='color: #FFB74D; margin-left: 1rem;'>{step['stage']}</span>
                    <p style='color: #A5D6A7; margin: 0.3rem 0 0; font-size: 0.9rem;'>{step['action']}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # ── Cost Breakdown Chart ─────────────────────────────────────────────
    st.markdown("---")
    st.markdown("## 💰 Cost Breakdown")

    all_ferts = fert_data.get("organic", []) + fert_data.get("chemical", []) + fert_data.get("bio", [])
    if all_ferts:
        names = [f["name"] for f in all_ferts]
        costs = [f["total_cost"] for f in all_ferts]
        types = [f["type"] for f in all_ferts]

        color_map = {"Organic": "#4CAF50", "Chemical": "#FF9800", "Bio-Fertilizer": "#2196F3"}
        colors = [color_map.get(t, "#9E9E9E") for t in types]

        fig = go.Figure(data=[go.Bar(x=names, y=costs, marker_color=colors, text=[format_currency(c) for c in costs], textposition="auto")])
        fig.update_layout(
            title="Fertilizer Cost Breakdown",
            yaxis_title="Cost (₹)",
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            height=400,
        )
        st.plotly_chart(fig, use_container_width=True)

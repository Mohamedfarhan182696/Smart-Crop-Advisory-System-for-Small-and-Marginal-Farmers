"""
💧 Irrigation Calculator Page
================================
Water requirement calculation and irrigation method comparison.
All UI strings translated via config/languages.py t() function.
"""

import streamlit as st
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.sidebar import render_sidebar
render_sidebar()

import plotly.graph_objects as go
from config.languages import t
from backend.services.irrigation_service import calculate_water_requirement
from utils.helpers import format_volume

lang = st.session_state.get("lang_code", "en")
st.markdown(f"# {t('page_irrigation', lang)}")
st.markdown("---")

# ── Check Prerequisites ──────────────────────────────────────────────────
selected_crop = st.session_state.get("selected_crop")
if not selected_crop:
    st.warning(t("irr_warning_no_crop", lang))
    st.info(t("irr_alt_select", lang))

# ── Crop Selection ──────────────────────────────────────────────────────
from utils.constants import CROP_DATABASE
crop_names = [v["name"] for v in CROP_DATABASE.values()]
default_idx = crop_names.index(selected_crop) if selected_crop in crop_names else 0

crop_choice = st.selectbox(t("irr_select_crop", lang), crop_names, index=default_idx)

col1, col2 = st.columns(2)
with col1:
    area = st.number_input(t("irr_farm_area", lang), min_value=0.1, max_value=100.0, value=1.0, step=0.1)
with col2:
    soil_type = st.session_state.get("soil_data", {}).get("soil_type", "Loamy Soil")
    st.info(f"{t('irr_soil_type', lang)} **{soil_type}**")

# Weather conditions
weather = st.session_state.get("weather_data", {})
temp = weather.get("temperature", 28.0)
hum = weather.get("humidity", 65.0)

if st.button(t("btn_calculate", lang), type="primary"):
    with st.spinner(t("irr_calculating", lang)):
        result = calculate_water_requirement(
            crop_name=crop_choice,
            area_hectares=area,
            soil_type=soil_type,
            temperature=temp,
            humidity=hum,
        )

    if result:
        st.session_state.irrigation_data = result
        st.success(t("irr_calculated_ok", lang))

# ── Display Results ─────────────────────────────────────────────────────
irrigation = st.session_state.get("irrigation_data")

if irrigation:
    st.markdown("---")
    st.markdown(f"## {t('irr_water_requirements', lang)} — {irrigation['crop_name']}")
    st.markdown(
        f"**{t('irr_area_label', lang)}:** {irrigation['area_hectares']} {t('irr_hectares', lang)} | "
        f"**{t('irr_duration_label', lang)}:** {irrigation['duration_days']} {t('irr_days', lang)}"
    )

    # Water requirement cards
    w1, w2, w3, w4 = st.columns(4)
    with w1:
        st.metric(t("irr_daily", lang), format_volume(irrigation["daily_water_litres"]))
    with w2:
        st.metric(t("irr_weekly", lang), format_volume(irrigation["weekly_water_litres"]))
    with w3:
        st.metric(t("irr_monthly", lang), format_volume(irrigation["monthly_water_litres"]))
    with w4:
        st.metric(t("irr_seasonal", lang), format_volume(irrigation["seasonal_water_litres"]))

    st.markdown(
        f"**{t('irr_daily_per_ha', lang)}:** {irrigation['daily_water_mm']} mm/day | "
        f"**{t('irr_total', lang)}:** {irrigation['total_water_mm']} mm/season"
    )

    # ── Irrigation Frequency ─────────────────────────────────────────────
    st.markdown("---")
    st.markdown(f"## {t('irr_schedule_title', lang)}")

    freq = irrigation.get("irrigation_frequency", {})
    f1, f2, f3 = st.columns(3)
    with f1:
        st.metric(t("irr_frequency", lang), freq.get("schedule", "Every 3-5 days"))
    with f2:
        st.metric(t("irr_best_time", lang), freq.get("best_time", "Morning"))
    with f3:
        st.metric(t("irr_base_schedule", lang), freq.get("base_frequency", ""))

    if freq.get("note"):
        st.info(f"💡 {freq['note']}")

    # ── Irrigation Methods Comparison ────────────────────────────────────
    st.markdown("---")
    st.markdown(f"## {t('irr_methods_title', lang)}")

    methods = irrigation.get("irrigation_methods", [])
    for method in methods:
        score = method.get("suitability", 50)

        with st.expander(
            f"{method['icon']} {method['method']} — {score}% {t('irr_suitable', lang)}",
            expanded=(score >= 70)
        ):
            mc1, mc2 = st.columns(2)
            with mc1:
                st.markdown(f"**{t('irr_water_savings', lang)}:** {method.get('water_savings', '0%')}")
                st.markdown(f"**{t('irr_cost', lang)}:** {method.get('cost_estimate', 'N/A')}")
                st.markdown(f"**{t('irr_best_for', lang)}:** {method.get('best_for', '')}")
            with mc2:
                st.markdown(f"**{t('irr_pros', lang)}:** {method.get('pros', '')}")
                st.markdown(f"**{t('irr_cons', lang)}:** {method.get('cons', '')}")

            # Suitability bar
            st.progress(score / 100)

    # ── Water Requirement Chart ──────────────────────────────────────────
    st.markdown("---")
    st.markdown(f"## {t('irr_chart_title', lang)}")

    fig = go.Figure(data=[
        go.Bar(
            x=[
                t("irr_chart_daily", lang),
                t("irr_chart_weekly", lang),
                t("irr_chart_monthly", lang),
            ],
            y=[
                irrigation["daily_water_litres"],
                irrigation["weekly_water_litres"],
                irrigation["monthly_water_litres"],
            ],
            marker_color=["#2196F3", "#1565C0", "#0D47A1"],
            text=[
                format_volume(irrigation["daily_water_litres"]),
                format_volume(irrigation["weekly_water_litres"]),
                format_volume(irrigation["monthly_water_litres"]),
            ],
            textposition="auto",
        ),
    ])
    fig.update_layout(
        title=f"{t('irr_chart_for', lang)} {irrigation['crop_name']}",
        yaxis_title=t("irr_chart_y_axis", lang),
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=400,
    )
    st.plotly_chart(fig, use_container_width=True)

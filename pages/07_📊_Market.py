"""
📊 Market Prices Page
========================
Market price analysis, predictions, profit calculator, and nearby markets.
"""

import streamlit as st
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.sidebar import render_sidebar
render_sidebar()

import plotly.graph_objects as go
from config.languages import t
from backend.services.market_service import get_market_analysis
from utils.helpers import format_currency
from utils.constants import CROP_DATABASE

lang = st.session_state.get("lang_code", "en")
st.markdown(f"# {t('page_market', lang)}")
st.markdown("---")

# ── Crop Selection ──────────────────────────────────────────────────────
crop_names = [v["name"] for v in CROP_DATABASE.values()]
selected = st.session_state.get("selected_crop")
default_idx = crop_names.index(selected) if selected in crop_names else 0

col1, col2 = st.columns([2, 1])
with col1:
    crop_choice = st.selectbox("Select Crop:", crop_names, index=default_idx)
with col2:
    area = st.number_input("Area (hectares):", min_value=0.1, max_value=100.0, value=1.0, step=0.1)

if st.button("📊 Get Market Analysis", type="primary"):
    with st.spinner("📈 Analyzing market data..."):
        result = get_market_analysis(crop_choice, area)
    if result:
        st.session_state.market_data = result
        st.success("✅ Market analysis complete!")

market = st.session_state.get("market_data")

if market:
    st.markdown("---")

    # ── Price Cards ──────────────────────────────────────────────────────
    st.markdown(f"## 💰 Market Prices — {market['crop_name']}")

    p1, p2, p3, p4 = st.columns(4)
    with p1:
        st.metric(t("current_price", lang), f"₹{market['current_price']:.0f}/q")
    with p2:
        trend = f"+{market['trend_percentage']}%" if market['trend_percentage'] > 0 else f"{market['trend_percentage']}%"
        st.metric(t("predicted_price", lang), f"₹{market['predicted_price']:.0f}/q", trend)
    with p3:
        st.metric("📉 Min Price", f"₹{market['min_price']:.0f}/q")
    with p4:
        st.metric("📈 Max Price", f"₹{market['max_price']:.0f}/q")

    # ── Historical Price Chart ───────────────────────────────────────────
    st.markdown("---")
    st.markdown("## 📈 Price Trend (90 Days)")

    hist = market.get("historical_prices", [])
    if hist:
        dates = [h["date"] for h in hist]
        prices = [h["price"] for h in hist]

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=dates, y=prices, mode="lines", name="Market Price",
            line=dict(color="#4CAF50", width=2),
            fill="tozeroy", fillcolor="rgba(76, 175, 80, 0.1)",
        ))
        fig.add_hline(y=market["current_price"], line_dash="dash", line_color="#FF9800",
                      annotation_text="Current Price")
        fig.add_hline(y=market["predicted_price"], line_dash="dot", line_color="#2196F3",
                      annotation_text="Predicted Price")
        fig.update_layout(
            yaxis_title="Price (₹/quintal)", template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=400,
        )
        st.plotly_chart(fig, use_container_width=True)

    # ── Profit Analysis ──────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("## 💰 Profit Analysis")

    tab_current, tab_predicted = st.tabs(["📊 At Current Price", "🔮 At Predicted Price"])

    for tab, data, label in [
        (tab_current, market.get("current_profit", {}), "Current"),
        (tab_predicted, market.get("predicted_profit", {}), "Predicted"),
    ]:
        with tab:
            pr1, pr2, pr3 = st.columns(3)
            with pr1:
                st.metric("📦 Yield", f"{data.get('yield_tonnes', 0):.1f} tonnes ({data.get('yield_quintals', 0):.0f} q)")
            with pr2:
                st.metric("💵 Revenue", format_currency(data.get("total_revenue", 0)))
            with pr3:
                st.metric("🏭 Production Cost", format_currency(data.get("production_cost", 0)))

            pr4, pr5 = st.columns(2)
            with pr4:
                profit = data.get("net_profit", 0)
                color = "normal" if profit >= 0 else "inverse"
                st.metric(
                    t("profit", lang) if profit >= 0 else t("loss", lang),
                    format_currency(abs(profit)),
                    f"{'Profit' if profit >= 0 else 'Loss'}",
                    delta_color=color,
                )
            with pr5:
                st.metric(t("roi", lang), f"{data.get('roi_percentage', 0)}%")

    # ── Profit Comparison Chart ──────────────────────────────────────────
    current_p = market.get("current_profit", {})
    predicted_p = market.get("predicted_profit", {})

    fig2 = go.Figure(data=[
        go.Bar(name="Current", x=["Revenue", "Cost", "Profit"],
               y=[current_p.get("total_revenue", 0), current_p.get("production_cost", 0), current_p.get("net_profit", 0)],
               marker_color=["#4CAF50", "#FF5722", "#2196F3"]),
        go.Bar(name="Predicted", x=["Revenue", "Cost", "Profit"],
               y=[predicted_p.get("total_revenue", 0), predicted_p.get("production_cost", 0), predicted_p.get("net_profit", 0)],
               marker_color=["#81C784", "#FF8A65", "#64B5F6"]),
    ])
    fig2.update_layout(
        barmode="group", title="Current vs Predicted Profit Analysis",
        yaxis_title="Amount (₹)", template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=400,
    )
    st.plotly_chart(fig2, use_container_width=True)

    # ── Nearby Markets ───────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("## 🏪 Nearby Markets & Services")

    markets_list = market.get("nearby_markets", [])
    for m in markets_list:
        st.markdown(
            f"""
            <div style='
                background: rgba(17, 29, 51, 0.85);
                border: 1px solid rgba(76, 175, 80, 0.2);
                border-radius: 12px;
                padding: 1rem;
                margin-bottom: 0.5rem;
            '>
                <div style='display: flex; justify-content: space-between; flex-wrap: wrap;'>
                    <span style='color: #E8F5E9; font-weight: 600;'>{m['icon']} {m['name']}</span>
                    <span style='color: #FFB74D;'>📍 {m['distance']}</span>
                </div>
                <p style='color: #78909C; font-size: 0.8rem; margin: 0.3rem 0;'>{m['type']} | ⏰ {m['timing']}</p>
                <p style='color: #A5D6A7; font-size: 0.85rem; margin: 0;'>🛒 {m['services']}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

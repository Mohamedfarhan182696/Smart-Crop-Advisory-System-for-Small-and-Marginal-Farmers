"""
🏪 Buy & Sell Page
====================
Find nearby markets, seed shops, fertilizer stores, and selling points.
"""

import streamlit as st
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.sidebar import render_sidebar
render_sidebar()

from config.languages import t
from backend.services.market_service import _get_nearby_markets

lang = st.session_state.get("lang_code", "en")
st.markdown(f"# {t('page_buy_sell', lang)}")
st.markdown("---")

# ── Buy Section ──────────────────────────────────────────────────────────
st.markdown("## 🛒 Where to Buy")

tab_seeds, tab_fert, tab_pest, tab_equip = st.tabs(["🌱 Seeds", "🧫 Fertilizers", "🐛 Pesticides", "🔧 Equipment"])

buy_sources = [
    {"name": "Krishi Vigyan Kendra (KVK)", "icon": "🌾", "type": "Government", "items": "Certified seeds, Soil test kits", "tip": "Best for certified seeds and free training"},
    {"name": "Primary Agricultural Cooperative", "icon": "🤝", "type": "Cooperative", "items": "Seeds, Fertilizers, Credit", "tip": "Members get subsidized rates"},
    {"name": "State Seed Corporation", "icon": "🏛️", "type": "Government", "items": "Foundation & certified seeds", "tip": "Quality assured seeds at fair prices"},
    {"name": "Local Agricultural Input Dealer", "icon": "🏪", "type": "Private", "items": "Seeds, Fertilizers, Pesticides, Tools", "tip": "Convenient but verify product authenticity"},
    {"name": "IFFCO / KRIBHCO Outlets", "icon": "🏭", "type": "Cooperative", "items": "Fertilizers, Seeds", "tip": "Quality fertilizers at cooperative rates"},
    {"name": "Online: BigHaat / DeHaat / AgroStar", "icon": "📱", "type": "Online", "items": "Full range with delivery", "tip": "Compare prices, read reviews, doorstep delivery"},
]

for tab, category in [(tab_seeds, "Seeds"), (tab_fert, "Fertilizers"), (tab_pest, "Pesticides"), (tab_equip, "Equipment")]:
    with tab:
        for source in buy_sources:
            st.markdown(
                f"""
                <div style='
                    background: rgba(17, 29, 51, 0.85);
                    border: 1px solid rgba(76, 175, 80, 0.2);
                    border-radius: 12px;
                    padding: 1rem;
                    margin-bottom: 0.5rem;
                '>
                    <div style='display: flex; justify-content: space-between;'>
                        <span style='color: #E8F5E9; font-weight: 600;'>{source['icon']} {source['name']}</span>
                        <span style='color: #78909C; font-size: 0.8rem;'>{source['type']}</span>
                    </div>
                    <p style='color: #A5D6A7; font-size: 0.85rem; margin: 0.3rem 0;'>📦 {source['items']}</p>
                    <p style='color: #FFB74D; font-size: 0.8rem; margin: 0;'>💡 {source['tip']}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

# ── Sell Section ─────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("## 💰 Where to Sell")

sell_options = [
    {"name": "APMC / Government Mandi", "icon": "🏛️", "desc": "Regulated market with transparent pricing. MSP guaranteed for select crops.", "link": "Visit nearest APMC yard"},
    {"name": "e-NAM (National Agriculture Market)", "icon": "📱", "desc": "Online platform for direct selling. Register at enam.gov.in for pan-India market access.", "link": "https://enam.gov.in"},
    {"name": "Direct to Industry / FPO", "icon": "🏭", "desc": "Sell directly to food processors, mills, or through Farmer Producer Organizations for better prices.", "link": "Contact your nearest FPO"},
    {"name": "Contract Farming", "icon": "📝", "desc": "Pre-agreed price with buyer companies. Provides price security and sometimes inputs.", "link": "Check with agriculture department"},
    {"name": "Local Retail / Weekly Market", "icon": "🛍️", "desc": "Direct to consumer sales for vegetables, fruits. Higher margins but requires effort.", "link": "Local weekly haat/market"},
    {"name": "Government Procurement (MSP)", "icon": "🏛️", "desc": "Government buys at Minimum Support Price during procurement season. Best for wheat, rice, pulses.", "link": "Register with Food Corporation"},
]

for opt in sell_options:
    st.markdown(
        f"""
        <div style='
            background: rgba(17, 29, 51, 0.85);
            border: 1px solid rgba(255, 152, 0, 0.2);
            border-left: 3px solid #FF9800;
            border-radius: 12px;
            padding: 1rem;
            margin-bottom: 0.5rem;
        '>
            <h4 style='color: #FFB74D; margin: 0 0 0.3rem;'>{opt['icon']} {opt['name']}</h4>
            <p style='color: #A5D6A7; font-size: 0.85rem; margin: 0 0 0.3rem;'>{opt['desc']}</p>
            <p style='color: #4FC3F7; font-size: 0.8rem; margin: 0;'>🔗 {opt['link']}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ── Nearby Services Map ─────────────────────────────────────────────────
st.markdown("---")
st.markdown("## 📍 Nearby Agricultural Services")

markets = _get_nearby_markets()
for m in markets:
    with st.expander(f"{m['icon']} {m['name']} — 📍 {m['distance']}"):
        st.markdown(f"**Type:** {m['type']}")
        st.markdown(f"**Services:** {m['services']}")
        st.markdown(f"**Timing:** {m['timing']}")
        if m.get("website"):
            st.markdown(f"**Website:** [{m['website']}]({m['website']})")

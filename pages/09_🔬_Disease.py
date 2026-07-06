"""
🔬 Disease Detection Page
============================
Upload crop images for AI-powered disease detection.
"""

import streamlit as st
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.sidebar import render_sidebar
render_sidebar()

from PIL import Image
from config.languages import t
from backend.services.disease_service import detect_disease

lang = st.session_state.get("lang_code", "en")
st.markdown(f"# {t('page_disease', lang)}")
st.markdown("---")

st.markdown("""
Upload a photo of your crop's leaves to detect diseases using AI. 
The system supports: **Rice, Tomato, Potato, Cotton, Corn, Wheat, Banana, and more.**
""")

# ── Image Upload ─────────────────────────────────────────────────────────
uploaded_file = st.file_uploader(
    t("btn_upload_image", lang),
    type=["jpg", "jpeg", "png", "webp"],
    help="Upload a clear photo of the affected leaf. Best results with close-up images.",
)

if uploaded_file:
    image = Image.open(uploaded_file)

    col_img, col_result = st.columns([1, 1])
    with col_img:
        st.markdown("### 📷 Uploaded Image")
        st.image(image, caption="Uploaded crop image", use_container_width=True)

    with col_result:
        if st.button(t("btn_detect_disease", lang), type="primary"):
            with st.spinner("🔬 Analyzing image with AI..."):
                result = detect_disease(image)

            if result:
                st.session_state.disease_result = result

    # ── Display Results ──────────────────────────────────────────────────
    disease_result = st.session_state.get("disease_result")

    if disease_result:
        st.markdown("---")

        if disease_result.get("is_healthy"):
            st.success("### ✅ Your crop appears healthy!")
            st.balloons()
            st.markdown(f"**Confidence:** {disease_result['confidence']}%")
            st.info("Continue good agricultural practices. Regular monitoring is recommended.")
        else:
            # Disease detected
            severity_color = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}.get(disease_result["severity"], "🟡")

            st.error(f"### ⚠️ Disease Detected: {disease_result['disease_name']}")

            # Key metrics
            r1, r2, r3, r4 = st.columns(4)
            with r1:
                st.metric(t("disease_name", lang), disease_result["disease_name"])
            with r2:
                st.metric(t("confidence", lang), f"{disease_result['confidence']}%")
            with r3:
                st.metric(t("severity", lang), f"{severity_color} {disease_result['severity']}")
            with r4:
                st.metric("🌾 Crop", disease_result.get("crop", "Unknown"))

            # Detailed info
            st.markdown("---")

            st.markdown(f"### {t('cause', lang)}")
            st.markdown(f"_{disease_result.get('cause', 'Unknown')}_")

            tab_organic, tab_chemical, tab_prevent = st.tabs([
                "🌿 Organic Treatment",
                "⚗️ Chemical Treatment",
                "🛡️ Prevention",
            ])

            with tab_organic:
                st.markdown(f"**{t('treatment', lang)} (Organic):**")
                st.markdown(disease_result.get("organic_treatment", "N/A"))

            with tab_chemical:
                st.markdown(f"**{t('treatment', lang)} (Chemical):**")
                st.markdown(disease_result.get("chemical_treatment", "N/A"))

                # Recommended sprays
                sprays = disease_result.get("recommended_sprays", [])
                if sprays:
                    st.markdown("**🧴 Recommended Sprays:**")
                    for spray in sprays:
                        st.markdown(f"  • {spray}")

            with tab_prevent:
                st.markdown(f"**{t('prevention', lang)}:**")
                st.markdown(disease_result.get("prevention", "N/A"))

            st.markdown("---")
            st.metric(t("recovery_time", lang), disease_result.get("recovery_time", "Unknown"))

            # Severity description
            if disease_result.get("severity_description"):
                st.info(f"**Severity Note:** {disease_result['severity_description']}")

# ── Disease Reference Gallery ────────────────────────────────────────────
st.markdown("---")
st.markdown("## 📚 Common Crop Diseases Reference")

from utils.constants import DISEASE_DATABASE

disease_items = [(k, v) for k, v in DISEASE_DATABASE.items() if k != "Healthy"]
cols = st.columns(3)

for idx, (key, disease) in enumerate(disease_items[:9]):
    with cols[idx % 3]:
        st.markdown(
            f"""
            <div style='
                background: rgba(17, 29, 51, 0.85);
                border: 1px solid rgba(244, 67, 54, 0.2);
                border-radius: 12px;
                padding: 0.8rem;
                margin-bottom: 0.5rem;
                min-height: 100px;
            '>
                <h4 style='color: #FF8A65; margin: 0 0 0.3rem; font-size: 0.9rem;'>🦠 {disease['disease']}</h4>
                <p style='color: #78909C; font-size: 0.75rem; margin: 0;'>Crop: {disease['crop']}</p>
                <p style='color: #A5D6A7; font-size: 0.8rem; margin: 0.3rem 0 0;'>{disease['cause'][:80]}...</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

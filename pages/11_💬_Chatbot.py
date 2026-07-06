"""
💬 AI Chatbot Page — Fully multilingual
"""
import streamlit as st
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.sidebar import render_sidebar
render_sidebar()

from config.languages import t
from backend.services.chat_service import chat

lang = st.session_state.get("lang_code", "en")
def tr(d): return d.get(lang, d.get("en", ""))

st.markdown(f"# {t('page_chatbot', lang)}")
st.markdown("---")

st.markdown(tr({
    "en": "Ask me anything about farming! I can help with crop selection, fertilizers, irrigation, pest management, diseases, market prices, and government schemes.",
    "ta": "விவசாயம் பற்றி எதையும் கேளுங்கள்! பயிர் தேர்வு, உரங்கள், நீர்ப்பாசனம், நோய் மேலாண்மை, சந்தை விலைகள், அரசு திட்டங்கள் பற்றி உதவுவேன்.",
    "hi": "खेती के बारे में कुछ भी पूछें! फसल चयन, उर्वरक, सिंचाई, कीट प्रबंधन, रोग, बाजार मूल्य और सरकारी योजनाओं में मदद करूंगा।",
    "te": "వ్యవసాయం గురించి ఏదైనా అడగండి! పంట ఎంపిక, ఎరువులు, నీటిపారుదల, వ్యాధి నిర్వహణ, మార్కెట్ ధరలు, ప్రభుత్వ పథకాలలో సహాయం చేస్తాను.",
    "ml": "കൃഷിയെക്കുറിച്ച് എന്തും ചോദിക്കൂ! വിള ഇനം, വളങ്ങൾ, ജലസേചനം, രോഗ നിർവഹണം, വിപണി വില, സർക്കാർ പദ്ധതികൾ — എല്ലാ കാര്യങ്ങളും.",
}))

# ── Initialize Chat History ──────────────────────────────────────────────
welcome = tr({
    "en": "🙏 Namaste! I am **Krishi Mitra** — your AI farming assistant. How can I help you today?",
    "ta": "🙏 வணக்கம்! நான் **கிருஷி மிட்ரா** — உங்கள் AI விவசாய உதவியாளர். இன்று உங்களுக்கு எவ்வாறு உதவலாம்?",
    "hi": "🙏 नमस्ते! मैं **कृषि मित्र** हूं — आपका AI कृषि सहायक। आज मैं आपकी कैसे मदद कर सकता हूं?",
    "te": "🙏 నమస్కారం! నేను **కృషి మిత్ర** — మీ AI వ్యవసాయ సహాయకుడు. నేడు మీకు ఎలా సహాయపడగలను?",
    "ml": "🙏 നമസ്തേ! ഞാൻ **കൃഷി മിത്ര** — നിങ്ങളുടെ AI കൃഷി സഹായി. ഇന്ന് ഞാൻ എങ്ങനെ സഹായിക്കാം?",
})

if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = [{"role": "assistant", "content": welcome}]

# ── Quick Action Buttons ─────────────────────────────────────────────────
_quick_title = tr({"en":"💡 Quick Questions","ta":"💡 விரைவு கேள்விகள்","hi":"💡 त्वरित प्रश्न","te":"💡 త్వరిత ప్రశ్నలు","ml":"💡 ദ്രുത ചോദ്യങ്ങൾ"})
st.markdown(f"### {_quick_title}")

quick_questions_data = {
    "en": ["What crop should I grow?", "How much water does rice need?", "Tell me about PM-KISAN scheme", "My tomato has yellow leaves"],
    "ta": ["நான் என்ன பயிர் பயிரிக்க வேண்டும்?", "நெல்லுக்கு எவ்வளவு தண்ணீர்?", "PM-KISAN திட்டம் என்ன?", "என் தக்காளி இலைகள் மஞ்சளாக உள்ளன"],
    "hi": ["मुझे कौन सी फसल उगानी चाहिए?", "चावल को कितना पानी चाहिए?", "PM-KISAN योजना क्या है?", "मेरे टमाटर की पत्तियां पीली हैं"],
    "te": ["నేను ఏ పంట వేయాలి?", "వరికి ఎంత నీరు కావాలి?", "PM-KISAN పథకం ఏమిటి?", "నా టమాటా ఆకులు పసుపు రంగులో ఉన్నాయి"],
    "ml": ["ഞാൻ ഏത് വിള കൃഷി ചെയ്യണം?", "നെല്ലിന് എത്ര വെള്ളം?", "PM-KISAN പദ്ധതി എന്ത്?", "എന്റെ തക്കാളി ഇലകൾ മഞ്ഞ"],
}
quick_questions = quick_questions_data.get(lang, quick_questions_data["en"])
quick_cols = st.columns(4)
for idx, question in enumerate(quick_questions):
    with quick_cols[idx]:
        if st.button(f"💬 {question[:22]}…", key=f"quick_{idx}", use_container_width=True):
            st.session_state.chat_messages.append({"role": "user", "content": question})
            with st.spinner(tr({"en":"🤖 Thinking...","ta":"🤖 யோசிக்கிறது...","hi":"🤖 सोच रहे हैं...","te":"🤖 ఆలోచిస్తోంది...","ml":"🤖 ചിന്തിക്കുന്നു..."})):
                response = chat(question, st.session_state.chat_messages, lang)
            st.session_state.chat_messages.append({"role": "assistant", "content": response})
            st.rerun()

st.markdown("---")

# ── Chat Display ─────────────────────────────────────────────────────────
for message in st.session_state.chat_messages:
    avatar = "🧑‍🌾" if message["role"] == "user" else "🤖"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

# ── Chat Input ───────────────────────────────────────────────────────────
user_input = st.chat_input(t("chat_placeholder", lang))

if user_input:
    st.session_state.chat_messages.append({"role": "user", "content": user_input})
    with st.chat_message("user", avatar="🧑‍🌾"):
        st.markdown(user_input)
    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner(tr({"en":"🤖 Thinking...","ta":"🤖 யோசிக்கிறது...","hi":"🤖 सोच रहे हैं...","te":"🤖 ఆలోచిస్తోంది...","ml":"🤖 ചിന്തിക്കുന്നു..."})):
            response = chat(user_input, st.session_state.chat_messages, lang)
        st.markdown(response)
    st.session_state.chat_messages.append({"role": "assistant", "content": response})

# ── Clear Chat ───────────────────────────────────────────────────────────
st.markdown("---")
_clear_btn = tr({"en":"🗑️ Clear Chat History","ta":"🗑️ அரட்டை வரலாற்றை அழி","hi":"🗑️ चैट इतिहास साफ़ करें","te":"🗑️ చాట్ చరిత్ర క్లియర్ చేయండి","ml":"🗑️ ചാറ്റ് ചരിത്രം മായ്ക്കൂ"})
if st.button(_clear_btn):
    st.session_state.chat_messages = [{"role": "assistant", "content": welcome}]
    st.rerun()

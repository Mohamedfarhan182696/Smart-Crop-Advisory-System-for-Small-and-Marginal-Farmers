"""
🎙 Voice Assistant Page
=========================
Full end-to-end voice pipeline:
  1. st.audio_input()  → captures mic audio directly in Python
  2. Faster-Whisper    → transcribes audio to text
  3. chat()            → generates AI farming advice
  4. gTTS              → converts answer back to speech
All UI strings are fully multilingual.
"""

import streamlit as st
import streamlit.components.v1 as components
import sys
import os
import tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.sidebar import render_sidebar
render_sidebar()

from config.languages import t
from backend.services.voice_service import speech_to_text, text_to_speech
from backend.services.chat_service import chat
from translation.translator import translate_text

lang = st.session_state.get("lang_code", "en")

# ── Page header ───────────────────────────────────────────────────────────
st.markdown(f"# {t('page_voice', lang)}")
st.markdown("---")

# ── Language selection ────────────────────────────────────────────────────
_lang_label = {
    "en": "🌐 Voice Language:", "ta": "🌐 குரல் மொழி:",
    "hi": "🌐 वॉइस भाषा:",      "te": "🌐 వాయిస్ భాష:", "ml": "🌐 ശബ്ദ ഭാഷ:"
}.get(lang, "🌐 Voice Language:")

voice_lang_options = {"English": "en", "Tamil": "ta", "Hindi": "hi", "Telugu": "te", "Malayalam": "ml"}
voice_lang_name = st.selectbox(
    _lang_label,
    list(voice_lang_options.keys()),
    index=list(voice_lang_options.values()).index(lang) if lang in voice_lang_options.values() else 0,
)
voice_lang = voice_lang_options[voice_lang_name]

# ── Translated UI strings ─────────────────────────────────────────────────
_mic_heading = {
    "en": "🎤 Speak Your Question",
    "ta": "🎤 உங்கள் கேள்வியை பேசுங்கள்",
    "hi": "🎤 अपना प्रश्न बोलें",
    "te": "🎤 మీ ప్రశ్న చెప్పండి",
    "ml": "🎤 നിങ്ങളുടെ ചോദ്യം സംസാരിക്കൂ",
}.get(lang, "🎤 Speak Your Question")

_mic_instruction = {
    "en": "Click the microphone button below, speak your question, then click **Stop** to send.",
    "ta": "கீழே உள்ள மைக்ரோஃபோன் பொத்தானை கிளிக் செய்யுங்கள், கேள்வியை பேசுங்கள், பிறகு **நிறுத்து** கிளிக் செய்யுங்கள்.",
    "hi": "नीचे माइक्रोफ़ोन बटन क्लिक करें, प्रश्न बोलें, फिर **रोकें** क्लिक करें।",
    "te": "క్రింద మైక్రోఫోన్ బటన్ నొక్కండి, మీ ప్రశ్న చెప్పండి, తర్వాత **ఆపు** నొక్కండి.",
    "ml": "താഴെ മൈക്ക് ബട്ടൺ അമർത്തുക, ചോദ്യം സംസാരിക്കുക, തുടർന്ന് **നിർത്തുക** അമർത്തുക.",
}.get(lang, "Click the microphone below, speak, then click Stop.")

_transcribing = {
    "en": "📝 Transcribing your voice...",
    "ta": "📝 குரலை உரையாக மாற்றுகிறது...",
    "hi": "📝 आवाज़ को टेक्स्ट में बदल रहे हैं...",
    "te": "📝 వాయిస్ అనువదిస్తోంది...",
    "ml": "📝 ശബ്ദം ടെക്സ്റ്റ് ആക്കി മാറ്റുന്നു...",
}.get(lang, "📝 Transcribing your voice...")

_thinking = {
    "en": "🤖 AI is thinking...",
    "ta": "🤖 AI யோசிக்கிறது...",
    "hi": "🤖 AI सोच रहा है...",
    "te": "🤖 AI ఆలోచిస్తోంది...",
    "ml": "🤖 AI ചിന്തിക്കുന്നു...",
}.get(lang, "🤖 AI is thinking...")

_speaking = {
    "en": "🔊 Converting to speech...",
    "ta": "🔊 குரலாக மாற்றுகிறது...",
    "hi": "🔊 आवाज़ में बदल रहे हैं...",
    "te": "🔊 వాయిస్‌గా మారుస్తోంది...",
    "ml": "🔊 ശബ്ദമായി മാറ്റുന്നു...",
}.get(lang, "🔊 Converting to speech...")

_you_said     = {"en": "📝 You said:",      "ta": "📝 நீங்கள் சொன்னது:",   "hi": "📝 आपने कहा:",    "te": "📝 మీరు చెప్పింది:",  "ml": "📝 നിങ്ങൾ പറഞ്ഞത്:"}.get(lang, "📝 You said:")
_ai_response  = {"en": "🤖 AI Response",    "ta": "🤖 AI பதில்",           "hi": "🤖 AI उत्तर",     "te": "🤖 AI సమాధానం",      "ml": "🤖 AI മറുപടി"}.get(lang, "🤖 AI Response")
_listen_resp  = {"en": "🔊 Listen",         "ta": "🔊 கேளுங்கள்",          "hi": "🔊 सुनें",        "te": "🔊 వినండి",          "ml": "🔊 കേൾക്കുക"}.get(lang, "🔊 Listen")
_or_type      = {"en": "📝 Or Type Your Question", "ta": "📝 அல்லது தட்டச்சு செய்யுங்கள்", "hi": "📝 या टाइप करें", "te": "📝 లేదా టైప్ చేయండి", "ml": "📝 അല്ലെങ്കിൽ ടൈപ്പ് ചെയ്യുക"}.get(lang, "📝 Or Type Your Question")
_send_btn     = {"en": "🔊 Get Answer",     "ta": "🔊 பதில் பெறுங்கள்",    "hi": "🔊 उत्तर पाएं",  "te": "🔊 సమాధానం పొందండి", "ml": "🔊 ഉത്തരം നേടുക"}.get(lang, "🔊 Get Answer")
_examples_lbl = {"en": "💡 Example Questions", "ta": "💡 உதாரண கேள்விகள்", "hi": "💡 उदाहरण प्रश्न", "te": "💡 ఉదాహరణ ప్రశ్నలు", "ml": "💡 ഉദാഹരണ ചോദ്യങ്ങൾ"}.get(lang, "💡 Example Questions")

# ════════════════════════════════════════════════════════════════════════════
#  SECTION 1 — WhatsApp-style Voice Input  (st.audio_input)
# ════════════════════════════════════════════════════════════════════════════
st.markdown(f"## {_mic_heading}")
st.info(_mic_instruction)

# Style the audio_input widget to look premium
st.markdown("""
<style>
/* Make audio input look like a WhatsApp mic button */
div[data-testid="stAudioInput"] {
    background: linear-gradient(135deg, rgba(17,29,51,0.95), rgba(27,40,63,0.9)) !important;
    border: 1px solid rgba(76,175,80,0.3) !important;
    border-radius: 20px !important;
    padding: 20px !important;
    box-shadow: 0 4px 24px rgba(0,0,0,0.25) !important;
}
div[data-testid="stAudioInput"] button {
    background: linear-gradient(135deg, #1B5E20, #43A047) !important;
    border-radius: 50% !important;
    width: 72px !important;
    height: 72px !important;
    font-size: 1.8rem !important;
    box-shadow: 0 4px 20px rgba(76,175,80,0.5) !important;
    border: 3px solid rgba(76,175,80,0.4) !important;
    transition: all 0.2s !important;
}
div[data-testid="stAudioInput"] button:hover {
    transform: scale(1.08) !important;
    box-shadow: 0 6px 30px rgba(76,175,80,0.7) !important;
}
div[data-testid="stAudioInput"] button[aria-label*="Stop"],
div[data-testid="stAudioInput"] button[aria-label*="Recording"] {
    background: linear-gradient(135deg, #B71C1C, #EF5350) !important;
    box-shadow: 0 0 0 0 rgba(244,67,54,0.6) !important;
    animation: mic-pulse 1.1s ease-out infinite !important;
}
@keyframes mic-pulse {
    0%   { box-shadow: 0 0 0 0 rgba(244,67,54,0.6); }
    70%  { box-shadow: 0 0 0 18px rgba(244,67,54,0); }
    100% { box-shadow: 0 0 0 0 rgba(244,67,54,0); }
}
</style>
""", unsafe_allow_html=True)

audio_bytes = st.audio_input(
    label="🎤 " + {"en": "Hold to speak", "ta": "பேச பிடிக்கவும்", "hi": "बोलने के लिए पकड़ें",
                    "te": "మాట్లాడటానికి పట్టుకోండి", "ml": "സംസാരിക്കാൻ അമർത്തുക"}.get(lang, "Hold to speak"),
    key="voice_mic_input",
)

# ── Process the recorded audio ────────────────────────────────────────────
if audio_bytes is not None:
    # Save to temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        tmp.write(audio_bytes.getvalue())
        tmp_path = tmp.name

    # Step 1: Transcribe
    with st.spinner(_transcribing):
        stt_result = speech_to_text(tmp_path, language=voice_lang)

    # Clean up temp file
    try:
        os.unlink(tmp_path)
    except Exception:
        pass

    if stt_result and stt_result.get("text", "").strip():
        transcript = stt_result["text"].strip()

        # Show what was heard
        st.markdown(f"**{_you_said}**")
        st.markdown(
            f"""<div style='background:rgba(76,175,80,0.12);border-left:4px solid #4CAF50;
            border-radius:10px;padding:12px 16px;color:#E8F5E9;font-size:1rem;
            margin-bottom:12px;'>"{transcript}"</div>""",
            unsafe_allow_html=True,
        )

        # Step 2: Get AI response
        with st.spinner(_thinking):
            response = chat(transcript, language=voice_lang)

        # Translate response to user's language if needed
        if voice_lang != "en":
            try:
                response = translate_text(response, "en", voice_lang)
            except Exception:
                pass  # Fall back to English response

        # Show AI response
        st.markdown(f"### {_ai_response}")
        st.markdown(
            f"""<div style='background:rgba(17,29,51,0.92);border:1px solid rgba(76,175,80,0.3);
            border-radius:14px;padding:1.4rem 1.6rem;color:#E8F5E9;font-size:1rem;
            line-height:1.7;margin-bottom:8px;'>
            {response}</div>""",
            unsafe_allow_html=True,
        )

        # Step 3: Text-to-speech playback
        with st.spinner(_speaking):
            try:
                audio_path = text_to_speech(response, language=voice_lang)
                if audio_path and os.path.exists(audio_path):
                    st.markdown(f"#### {_listen_resp}")
                    st.audio(audio_path, format="audio/mp3", autoplay=True)
                    os.unlink(audio_path)
            except Exception:
                pass  # TTS is best-effort

    else:
        err = stt_result.get("error", "") if stt_result else ""
        st.warning({
            "en": f"⚠️ Could not transcribe audio. Please speak clearly and try again. {('(' + err + ')') if err else ''}",
            "ta": "⚠️ குரலை உரையாக மாற்ற முடியவில்லை. தெளிவாக பேசி மீண்டும் முயற்சிக்கவும்.",
            "hi": "⚠️ आवाज़ समझ में नहीं आई। स्पष्ट बोलकर फिर कोशिश करें।",
            "te": "⚠️ ఆడియో అర్థం కాలేదు. స్పష్టంగా మాట్లాడి మళ్ళీ ప్రయత్నించండి.",
            "ml": "⚠️ ശബ്ദം മനസ്സിലായില്ല. വ്യക്തമായി സംസാരിച്ച് വീണ്ടും ശ്രമിക്കൂ.",
        }.get(lang, "⚠️ Could not transcribe. Please speak clearly and try again."))

# ════════════════════════════════════════════════════════════════════════════
#  SECTION 2 — Manual Text Input (fallback / supplement)
# ════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown(f"## {_or_type}")

placeholder = {
    "en": "What crop should I grow in summer?",
    "ta": "கோடையில் என்ன பயிர் பயிரிட வேண்டும்?",
    "hi": "गर्मी में मुझे कौन सी फसल उगानी चाहिए?",
    "te": "వేసవిలో ఏ పంట వేయాలి?",
    "ml": "വേനൽക്കാലത്ത് ഏത് വിള കൃഷി ചെയ്യണം?",
}.get(lang, "What crop should I grow in summer?")

text_input = st.text_area(
    {"en": "Your question:", "ta": "உங்கள் கேள்வி:", "hi": "आपका प्रश्न:",
     "te": "మీ ప్రశ్న:", "ml": "നിങ്ങളുടെ ചോദ്യം:"}.get(lang, "Your question:"),
    value=st.session_state.get("voice_prefill", ""),
    placeholder=placeholder,
    height=100,
    key="voice_text_input",
)
# Clear prefill after one use
if "voice_prefill" in st.session_state:
    del st.session_state["voice_prefill"]

if st.button(_send_btn, type="primary", key="voice_send_btn"):
    query = text_input.strip()
    if query:
        with st.spinner(_thinking):
            response = chat(query, language=voice_lang)

        if voice_lang != "en":
            try:
                response = translate_text(response, "en", voice_lang)
            except Exception:
                pass

        st.markdown(f"### {_ai_response}")
        st.markdown(
            f"""<div style='background:rgba(17,29,51,0.92);border:1px solid rgba(76,175,80,0.3);
            border-radius:14px;padding:1.4rem 1.6rem;color:#E8F5E9;font-size:1rem;line-height:1.7;'>
            {response}</div>""",
            unsafe_allow_html=True,
        )

        with st.spinner(_speaking):
            try:
                audio_path = text_to_speech(response, language=voice_lang)
                if audio_path and os.path.exists(audio_path):
                    st.markdown(f"#### {_listen_resp}")
                    st.audio(audio_path, format="audio/mp3", autoplay=True)
                    os.unlink(audio_path)
            except Exception:
                pass
    else:
        st.warning({"en": "Please enter a question.", "ta": "கேள்வியை உள்ளிடுங்கள்.",
                    "hi": "कृपया प्रश्न दर्ज करें।", "te": "దయచేసి ప్రశ్న నమోదు చేయండి.",
                    "ml": "ദയവായി ചോദ്യം നൽകുക."}.get(lang, "Please enter a question."))

# ════════════════════════════════════════════════════════════════════════════
#  SECTION 3 — Example Questions
# ════════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown(f"### {_examples_lbl}")

examples_data = {
    "en": ["What crop should I grow?", "How much water does rice need?",
           "What fertilizer for wheat?", "My crop has yellow leaves — what to do?",
           "What is the market price of cotton?", "Tell me about PM-KISAN scheme"],
    "ta": ["நான் என்ன பயிர் பயிரிக்க வேண்டும்?", "நெல்லுக்கு எவ்வளவு தண்ணீர் தேவை?",
           "கோதுமைக்கு என்ன உரம்?", "என் பயிரின் இலைகள் மஞ்சளாக உள்ளன — என்ன செய்வது?",
           "பருத்தியின் சந்தை விலை என்ன?", "PM-KISAN திட்டம் பற்றி சொல்லுங்கள்"],
    "hi": ["मुझे कौन सी फसल उगानी चाहिए?", "चावल को कितना पानी चाहिए?",
           "गेहूं के लिए कौन सी खाद?", "मेरी फसल की पत्तियाँ पीली हैं — क्या करें?",
           "कपास का बाजार मूल्य क्या है?", "PM-KISAN योजना के बारे में बताएं"],
    "te": ["నేను ఏ పంట వేయాలి?", "వరికి ఎంత నీరు కావాలి?",
           "గోధుమకు ఏ ఎరువు?", "నా పంట ఆకులు పసుపు రంగులో ఉన్నాయి — ఏమి చేయాలి?",
           "పత్తి మార్కెట్ ధర ఎంత?", "PM-KISAN పథకం గురించి చెప్పండి"],
    "ml": ["ഞാൻ ഏത് വിള കൃഷി ചെയ്യണം?", "നെല്ലിന് എത്ര വെള്ളം വേണം?",
           "ഗോതമ്പിന് ഏത് വളം?", "എന്റെ വിള ഇലകൾ മഞ്ഞ — എന്ത് ചെയ്യണം?",
           "പരുത്തിയുടെ വിപണി വില എന്ത്?", "PM-KISAN പദ്ധതിയെക്കുറിച്ച് പറയൂ"],
}

examples = examples_data.get(lang, examples_data["en"])
ex_cols = st.columns(2)
for i, ex in enumerate(examples):
    with ex_cols[i % 2]:
        if st.button(f"🎤 {ex}", key=f"ex_{i}", use_container_width=True):
            st.session_state["voice_prefill"] = ex
            st.rerun()

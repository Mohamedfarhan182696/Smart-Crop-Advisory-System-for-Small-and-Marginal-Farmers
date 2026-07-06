"""
Chat Service
=============
AI chatbot using Google Gemini with RAG from agricultural knowledge base.
Falls back to rule-based responses when no API key is available.
"""

import os
import json
from typing import Optional
from pathlib import Path
from utils.logger import get_logger
from utils.constants import CROP_DATABASE, GOVERNMENT_SCHEMES, DISEASE_DATABASE, FERTILIZER_DATABASE
from config.settings import get_settings

logger = get_logger("chatbot")

_client = None
_chat_session = None

KNOWLEDGE_DIR = Path(__file__).resolve().parent.parent.parent / "chatbot" / "knowledge_base"

# System prompt for agricultural assistant
SYSTEM_PROMPT = """You are an expert Agricultural Advisor AI for Indian farmers. Your name is "Krishi Mitra" (Farming Friend).

ROLE:
- Help farmers with crop selection, irrigation, fertilizers, pest management, disease identification, market prices, and government schemes.
- Give practical, actionable advice suitable for small and marginal farmers in India.
- Be encouraging, simple, and use examples when possible.

GUIDELINES:
- Always recommend consulting local Krishi Vigyan Kendra (KVK) for specific local advice.
- When recommending chemicals/pesticides, also suggest organic alternatives.
- Mention relevant government schemes when applicable.
- Keep answers concise but informative (2-4 paragraphs max).
- If you're unsure, say so honestly and suggest where to get help.

CONTEXT: You have access to data about 22+ Indian crops, fertilizer recommendations, disease treatments, and government schemes.
"""


def _init_gemini():
    """Initialize Google Gemini client."""
    global _client
    if _client is not None:
        return True

    settings = get_settings()
    api_key = settings.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY", "")
    if not api_key or api_key == "your_gemini_api_key_here":
        logger.info("No Gemini API key found. Using offline mode.")
        return False

    try:
        from google import genai
        _client = genai.Client(api_key=api_key)
        logger.info("Gemini client initialized successfully.")
        return True
    except Exception as e:
        logger.error(f"Gemini initialization error: {e}")
        return False


def chat(user_message: str, chat_history: list = None, language: str = "en") -> str:
    """
    Process a chat message and return AI response.

    Args:
        user_message: User's question
        chat_history: Previous conversation messages
        language: Language code for response

    Returns:
        AI response text
    """
    if not user_message.strip():
        return "Please ask a question about farming."

    # Try Gemini first
    if _init_gemini():
        return _gemini_chat(user_message, chat_history, language)
    else:
        return _offline_chat(user_message, language)


def _gemini_chat(user_message: str, chat_history: list, language: str) -> str:
    """Chat using Google Gemini API."""
    try:
        # Retrieve relevant knowledge
        context = _retrieve_knowledge(user_message)

        # Build prompt with context
        lang_instruction = ""
        if language != "en":
            lang_map = {"ta": "Tamil", "hi": "Hindi", "te": "Telugu", "ml": "Malayalam"}
            lang_instruction = f"\n\nIMPORTANT: Respond in {lang_map.get(language, 'English')} language."

        full_prompt = f"""{SYSTEM_PROMPT}

RELEVANT KNOWLEDGE:
{context}
{lang_instruction}

User Question: {user_message}"""

        response = _client.models.generate_content(
            model="gemini-2.0-flash",
            contents=full_prompt,
        )

        return response.text if response.text else "I couldn't generate a response. Please try again."

    except Exception as e:
        logger.error(f"Gemini chat error: {e}")
        return _offline_chat(user_message, language)


def _offline_chat(user_message: str, language: str) -> str:
    """Rule-based fallback when no LLM is available."""
    msg = user_message.lower()

    # Pattern matching for common questions
    if any(word in msg for word in ["crop", "grow", "plant", "sow", "recommend"]):
        return (
            "🌾 For crop recommendations, please go to the **Crop Advisor** page. "
            "Enter your soil values (N, P, K, pH) and the AI will suggest the best crops "
            "for your conditions. The system considers your location, weather, and soil type.\n\n"
            "💡 Tip: Get a soil test from your nearest Soil Health Card center for accurate values."
        )

    elif any(word in msg for word in ["water", "irrigation", "irrigat"]):
        return (
            "💧 For irrigation requirements, go to the **Irrigation** page after selecting a crop. "
            "The system calculates daily, weekly, and seasonal water needs.\n\n"
            "💡 Tip: Drip irrigation saves 30-40% water compared to flood irrigation. "
            "Check PM-KUSUM scheme for solar pump subsidy."
        )

    elif any(word in msg for word in ["fertilizer", "fertiliser", "manure", "urea", "dap"]):
        return (
            "🧫 For fertilizer recommendations, go to the **Fertilizer** page. "
            "Based on your soil nutrients and crop, the AI recommends organic, chemical, and bio-fertilizers "
            "with exact quantities, timing, and costs.\n\n"
            "💡 Tip: Always apply FYM or vermicompost as base manure before chemical fertilizers."
        )

    elif any(word in msg for word in ["disease", "pest", "yellow", "spot", "wilt", "rot", "blight"]):
        return (
            "🔬 For disease detection, go to the **Disease Detection** page and upload a photo of "
            "the affected leaf. The AI will identify the disease and suggest treatment.\n\n"
            "🌿 Quick tips:\n"
            "- Yellow leaves: Could be nitrogen deficiency or overwatering\n"
            "- Brown spots: Fungal infection likely - apply Mancozeb\n"
            "- Wilting: Check for root rot or water stress\n\n"
            "💡 Always try organic remedies (neem oil, Trichoderma) before chemicals."
        )

    elif any(word in msg for word in ["price", "market", "sell", "mandi", "rate"]):
        return (
            "📊 For market prices and profit analysis, go to the **Market** page. "
            "You can see current prices, historical trends, and profit predictions.\n\n"
            "💡 Tips:\n"
            "- Register on e-NAM (enam.gov.in) for online trading\n"
            "- Check APMC mandi rates daily before selling\n"
            "- Consider storing crops if prices are low — use warehouse receipt financing"
        )

    elif any(word in msg for word in ["scheme", "government", "subsidy", "loan", "kisan"]):
        schemes_text = "\n".join(
            [f"• **{s['name']}** ({s['full_name']}): {s['benefit']}" for s in GOVERNMENT_SCHEMES[:4]]
        )
        return f"🏛️ Key Government Schemes for Farmers:\n\n{schemes_text}\n\n💡 Visit your nearest bank or agriculture office for registration."

    elif any(word in msg for word in ["weather", "rain", "temperature", "forecast"]):
        return (
            "🌤 For weather data, go to the **Weather** page. It shows:\n"
            "- Current temperature, humidity, rainfall\n"
            "- Soil temperature and moisture\n"
            "- 7-day forecast with charts\n\n"
            "💡 The system uses Open-Meteo API for accurate, location-based weather data."
        )

    elif any(word in msg for word in ["hello", "hi", "hey", "namaste"]):
        return (
            "🙏 Namaste! I am **Krishi Mitra** — your AI farming assistant.\n\n"
            "I can help you with:\n"
            "🌾 Crop selection\n"
            "💧 Irrigation planning\n"
            "🧫 Fertilizer recommendations\n"
            "🔬 Disease detection\n"
            "📊 Market prices\n"
            "🏛️ Government schemes\n\n"
            "Ask me anything about farming!"
        )

    else:
        return (
            "🤔 I understand you're asking about farming. Here's what I can help with:\n\n"
            "🌾 **Crops**: 'What crop should I grow?'\n"
            "💧 **Water**: 'How much water does rice need?'\n"
            "🧫 **Fertilizer**: 'What fertilizer for wheat?'\n"
            "🔬 **Disease**: 'My tomato has yellow leaves'\n"
            "📊 **Prices**: 'What is the rice market price?'\n"
            "🏛️ **Schemes**: 'Tell me about PM-KISAN'\n\n"
            "Try asking one of these questions!"
        )


def _retrieve_knowledge(query: str) -> str:
    """Simple keyword-based knowledge retrieval (RAG lite)."""
    query_lower = query.lower()
    context_parts = []

    # Search crop database
    for crop_key, crop_data in CROP_DATABASE.items():
        if crop_key in query_lower or crop_data["name"].lower() in query_lower:
            context_parts.append(
                f"Crop: {crop_data['name']}, Season: {crop_data['season']}, "
                f"Duration: {crop_data['duration_days']} days, "
                f"Water: {crop_data['water_req_mm']}mm, "
                f"NPK: {crop_data['fertilizer_n']}-{crop_data['fertilizer_p']}-{crop_data['fertilizer_k']}, "
                f"Yield: {crop_data['yield_tonnes_per_ha']} t/ha, "
                f"Price: ₹{crop_data['market_price_per_quintal']}/q"
            )

    # Search disease database
    for disease_key, disease_data in DISEASE_DATABASE.items():
        if any(word in query_lower for word in disease_data.get("disease", "").lower().split()):
            context_parts.append(
                f"Disease: {disease_data['disease']} in {disease_data['crop']}, "
                f"Cause: {disease_data['cause']}, "
                f"Treatment: {disease_data.get('chemical_treatment', '')}"
            )

    # Search government schemes
    for scheme in GOVERNMENT_SCHEMES:
        if any(word in query_lower for word in scheme["name"].lower().split()):
            context_parts.append(
                f"Scheme: {scheme['full_name']}, Benefit: {scheme['benefit']}, "
                f"Eligibility: {scheme['eligibility']}"
            )

    return "\n".join(context_parts[:5]) if context_parts else "No specific knowledge found for this query."

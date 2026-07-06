# 🌾 Smart Crop Advisory System

**AI-Powered Agriculture Platform for Small and Marginal Farmers of India**

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.38+-red.svg)](https://streamlit.io)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com)
[![TensorFlow](https://img.shields.io/badge/TensorFlow-2.16+-orange.svg)](https://tensorflow.org)

---

## 🌟 Features

| Module | Description |
|--------|-------------|
| 📍 GPS Location | Auto-detect or manual district/city entry |
| 🌤 Weather | Real-time weather, soil data, 7-day forecast |
| 🧪 Soil Analysis | NPK, pH, moisture, soil type input |
| 🌾 AI Crop Advisor | ML-powered top 5 crop recommendations |
| 💧 Irrigation | Daily/weekly/seasonal water calculator |
| 🧫 Fertilizer | Organic, chemical, bio-fertilizer recommendations |
| 📊 Market Prices | Price trends, predictions, profit analysis |
| 🏪 Buy & Sell | Nearby markets, shops, e-NAM integration |
| 🔬 Disease Detection | Upload crop image → AI diagnosis + treatment |
| 🎙 Voice Assistant | Speak questions in 5 languages |
| 💬 AI Chatbot | Gemini-powered agriculture expert |
| 🌐 Multilingual | English, Tamil, Hindi, Telugu, Malayalam |

## 🚀 Quick Start

### 1. Clone & Install

```bash
git clone <repository-url>
cd SmartCropAdvisor
cl
# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure

```bash
# Copy environment template
copy .env.example .env

# Edit .env and add your API keys:
# - GEMINI_API_KEY (get from https://aistudio.google.com)
```

### 3. Train ML Model (Optional - has built-in fallback)

```bash
python models/crop_recommendation/train.py
```

### 4. Run Application

```bash
# Streamlit Frontend (main app)
streamlit run app.py

# FastAPI Backend (optional, for API access)
python -m backend.main
```

### 5. Open in Browser

- **Streamlit App:** http://localhost:8501
- **API Docs:** http://localhost:8000/docs

## 🐳 Docker

```bash
docker build -t smart-crop-advisor .
docker run -p 8501:8501 -p 8000:8000 smart-crop-advisor
```

## 📁 Project Structure

```
SmartCropAdvisor/
├── app.py                    # Main Streamlit app
├── requirements.txt          # Dependencies
├── Dockerfile               # Docker config
├── .env.example             # Environment template
│
├── frontend/pages/          # 11 Streamlit pages
├── frontend/styles/         # Custom CSS
├── backend/services/        # Business logic
├── backend/api/             # FastAPI routes
├── backend/main.py          # FastAPI app
│
├── models/                  # ML model training & artifacts
├── datasets/                # Data download & preprocessing
├── chatbot/                 # Knowledge base & prompts
├── voice_assistant/         # STT + TTS
├── translation/             # Deep Translator
├── database/                # SQLAlchemy ORM
├── utils/                   # Constants, validators, helpers
├── config/                  # Settings & translations
└── tests/                   # Test suite
```

## 🛠 Technology Stack

- **Frontend:** Streamlit, Plotly, Folium
- **Backend:** FastAPI, SQLAlchemy
- **ML:** Scikit-learn, TensorFlow, XGBoost
- **LLM:** Google Gemini API
- **Voice:** Faster Whisper, gTTS
- **Translation:** Deep Translator
- **Weather:** Open-Meteo (free, no key)
- **Maps:** OpenStreetMap, Nominatim

## 🌐 Supported Languages

| Language | Code | Voice | Chat | UI |
|----------|------|-------|------|----|
| English | en | ✅ | ✅ | ✅ |
| Tamil | ta | ✅ | ✅ | ✅ |
| Hindi | hi | ✅ | ✅ | ✅ |
| Telugu | te | ✅ | ✅ | ✅ |
| Malayalam | ml | ✅ | ✅ | ✅ |

## 📝 License

MIT License — Built for Indian Farmers 🇮🇳

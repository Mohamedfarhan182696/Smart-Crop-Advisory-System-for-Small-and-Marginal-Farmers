"""
Application Configuration
=========================
Central configuration using pydantic-settings for type-safe environment variable loading.
All secrets are loaded from .env file or environment variables.
"""

import os
from pathlib import Path
from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import Field


# Project root directory
BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # ── App ──────────────────────────────────────────────────────────────
    APP_NAME: str = "Smart Crop Advisory System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    SECRET_KEY: str = "change-me-in-production-use-strong-key"

    # ── API Keys ─────────────────────────────────────────────────────────
    GEMINI_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    GROQ_API_KEY: str = ""

    # ── LLM Configuration ───────────────────────────────────────────────
    LLM_PROVIDER: str = "gemini"  # gemini, openai, groq, offline
    GEMINI_MODEL: str = "gemini-2.0-flash"
    OPENAI_MODEL: str = "gpt-4o-mini"
    GROQ_MODEL: str = "llama-3.1-70b-versatile"

    # ── Database ─────────────────────────────────────────────────────────
    DATABASE_URL: str = f"sqlite:///{BASE_DIR / 'database' / 'scas.db'}"
    DATABASE_ECHO: bool = False

    # ── Model Paths ──────────────────────────────────────────────────────
    CROP_MODEL_PATH: str = str(BASE_DIR / "models" / "crop_recommendation" / "model.pkl")
    CROP_SCALER_PATH: str = str(BASE_DIR / "models" / "crop_recommendation" / "scaler.pkl")
    CROP_ENCODER_PATH: str = str(BASE_DIR / "models" / "crop_recommendation" / "label_encoder.pkl")
    DISEASE_MODEL_PATH: str = str(BASE_DIR / "models" / "disease_detection" / "model.h5")
    DISEASE_LABELS_PATH: str = str(BASE_DIR / "models" / "disease_detection" / "class_labels.json")
    FERTILIZER_MODEL_PATH: str = str(BASE_DIR / "models" / "fertilizer_prediction" / "model.pkl")
    IRRIGATION_MODEL_PATH: str = str(BASE_DIR / "models" / "irrigation_prediction" / "model.pkl")
    MARKET_MODEL_PATH: str = str(BASE_DIR / "models" / "market_prediction" / "model.pt")

    # ── Dataset Paths ────────────────────────────────────────────────────
    CROP_DATASET_PATH: str = str(BASE_DIR / "datasets" / "crop" / "crop_data.csv")
    FERTILIZER_DATASET_PATH: str = str(BASE_DIR / "datasets" / "fertilizer" / "fertilizer_data.csv")
    IRRIGATION_DATASET_PATH: str = str(BASE_DIR / "datasets" / "irrigation" / "irrigation_data.csv")
    MARKET_DATASET_PATH: str = str(BASE_DIR / "datasets" / "market" / "market_data.csv")

    # ── Weather API ──────────────────────────────────────────────────────
    WEATHER_API_BASE: str = "https://api.open-meteo.com/v1"
    WEATHER_CACHE_TTL: int = 3600  # 1 hour in seconds

    # ── Voice Configuration ──────────────────────────────────────────────
    WHISPER_MODEL_SIZE: str = "small"  # tiny, base, small, medium, large-v3
    WHISPER_DEVICE: str = "cpu"  # cpu or cuda
    WHISPER_COMPUTE_TYPE: str = "int8"  # int8, float16, float32
    TTS_SLOW: bool = False

    # ── Backend API ──────────────────────────────────────────────────────
    BACKEND_HOST: str = "127.0.0.1"
    BACKEND_PORT: int = 8000
    BACKEND_URL: str = "http://127.0.0.1:8000"
    CORS_ORIGINS: list = ["*"]

    # ── Geocoding ────────────────────────────────────────────────────────
    NOMINATIM_USER_AGENT: str = "smart-crop-advisor-v1"
    NOMINATIM_TIMEOUT: int = 10

    # ── Feature Flags ────────────────────────────────────────────────────
    ENABLE_VOICE: bool = True
    ENABLE_CHATBOT: bool = True
    ENABLE_DISEASE_DETECTION: bool = True
    ENABLE_MARKET_PREDICTION: bool = True
    ENABLE_GPS: bool = True

    # ── Supported Languages ──────────────────────────────────────────────
    SUPPORTED_LANGUAGES: dict = {
        "English": "en",
        "தமிழ்": "ta",
        "हिन्दी": "hi",
        "తెలుగు": "te",
        "മലയാളം": "ml",
    }
    DEFAULT_LANGUAGE: str = "English"

    class Config:
        env_file = str(BASE_DIR / ".env")
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

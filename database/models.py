"""
Database ORM Models
====================
SQLAlchemy models for all application tables.
Designed for SQLite (dev) with easy PostgreSQL upgrade path.
"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Text, Boolean, DateTime,
    JSON, ForeignKey, Index, create_engine,
)
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


class User(Base):
    """Farmer/user profile."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=True)
    phone = Column(String(15), nullable=True, unique=True)
    district = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    language = Column(String(20), default="en")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    soil_reports = relationship("SoilReport", back_populates="user", cascade="all, delete-orphan")
    crop_recommendations = relationship("CropRecommendation", back_populates="user", cascade="all, delete-orphan")
    disease_reports = relationship("DiseaseReport", back_populates="user", cascade="all, delete-orphan")
    chat_history = relationship("ChatMessage", back_populates="user", cascade="all, delete-orphan")
    voice_conversations = relationship("VoiceConversation", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, name='{self.name}', district='{self.district}')>"


class SoilReport(Base):
    """Soil analysis input records."""
    __tablename__ = "soil_reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    nitrogen = Column(Float, nullable=False)
    phosphorus = Column(Float, nullable=False)
    potassium = Column(Float, nullable=False)
    ph = Column(Float, nullable=False)
    moisture = Column(Float, nullable=False)
    water_availability = Column(Float, nullable=False)
    soil_type = Column(String(50), nullable=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="soil_reports")
    crop_recommendations = relationship("CropRecommendation", back_populates="soil_report", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_soil_user", "user_id"),
        Index("idx_soil_date", "created_at"),
    )


class WeatherRecord(Base):
    """Cached weather data."""
    __tablename__ = "weather_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    temperature = Column(Float, nullable=True)
    humidity = Column(Float, nullable=True)
    rainfall = Column(Float, nullable=True)
    wind_speed = Column(Float, nullable=True)
    wind_direction = Column(Float, nullable=True)
    pressure = Column(Float, nullable=True)
    uv_index = Column(Float, nullable=True)
    cloud_cover = Column(Float, nullable=True)
    soil_temperature = Column(Float, nullable=True)
    soil_moisture = Column(Float, nullable=True)
    full_data = Column(JSON, nullable=True)
    fetched_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_weather_coords", "latitude", "longitude"),
        Index("idx_weather_date", "fetched_at"),
    )


class CropRecommendation(Base):
    """Stored crop recommendation results."""
    __tablename__ = "crop_recommendations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    soil_report_id = Column(Integer, ForeignKey("soil_reports.id"), nullable=True)
    recommendations = Column(JSON, nullable=False)  # List of top 5 crops with scores
    selected_crop = Column(String(50), nullable=True)
    temperature = Column(Float, nullable=True)
    humidity = Column(Float, nullable=True)
    rainfall = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="crop_recommendations")
    soil_report = relationship("SoilReport", back_populates="crop_recommendations")
    water_calculations = relationship("WaterCalculation", back_populates="crop_recommendation", cascade="all, delete-orphan")
    fertilizer_recommendations = relationship("FertilizerRecommendation", back_populates="crop_recommendation", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_crop_rec_user", "user_id"),
    )


class WaterCalculation(Base):
    """Irrigation requirement calculations."""
    __tablename__ = "water_calculations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    crop_recommendation_id = Column(Integer, ForeignKey("crop_recommendations.id"), nullable=True)
    crop_name = Column(String(50), nullable=False)
    daily_water_litres = Column(Float, nullable=False)
    weekly_water_litres = Column(Float, nullable=False)
    monthly_water_litres = Column(Float, nullable=False)
    seasonal_water_litres = Column(Float, nullable=False)
    irrigation_method = Column(String(50), nullable=True)
    irrigation_frequency = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    crop_recommendation = relationship("CropRecommendation", back_populates="water_calculations")


class FertilizerRecommendation(Base):
    """Fertilizer recommendation records."""
    __tablename__ = "fertilizer_recommendations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    crop_recommendation_id = Column(Integer, ForeignKey("crop_recommendations.id"), nullable=True)
    crop_name = Column(String(50), nullable=False)
    recommendations = Column(JSON, nullable=False)  # Organic, chemical, bio recommendations
    created_at = Column(DateTime, default=datetime.utcnow)

    crop_recommendation = relationship("CropRecommendation", back_populates="fertilizer_recommendations")


class DiseaseReport(Base):
    """Crop disease detection results."""
    __tablename__ = "disease_reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    image_path = Column(String(500), nullable=True)
    disease_name = Column(String(100), nullable=False)
    confidence = Column(Float, nullable=False)
    severity = Column(String(20), nullable=True)
    crop_name = Column(String(50), nullable=True)
    treatment = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="disease_reports")

    __table_args__ = (
        Index("idx_disease_user", "user_id"),
    )


class MarketPrice(Base):
    """Market price records and predictions."""
    __tablename__ = "market_prices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    crop_name = Column(String(50), nullable=False)
    current_price = Column(Float, nullable=True)
    predicted_price = Column(Float, nullable=True)
    min_price = Column(Float, nullable=True)
    max_price = Column(Float, nullable=True)
    market_name = Column(String(200), nullable=True)
    state = Column(String(100), nullable=True)
    data_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_market_crop", "crop_name"),
        Index("idx_market_date", "data_date"),
    )


class ChatMessage(Base):
    """AI chatbot conversation history."""
    __tablename__ = "chat_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    session_id = Column(String(100), nullable=True)
    role = Column(String(20), nullable=False)  # user, assistant, system
    message = Column(Text, nullable=False)
    language = Column(String(10), default="en")
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="chat_history")

    __table_args__ = (
        Index("idx_chat_session", "session_id"),
        Index("idx_chat_user", "user_id"),
    )


class VoiceConversation(Base):
    """Voice assistant interaction logs."""
    __tablename__ = "voice_conversations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    audio_path = Column(String(500), nullable=True)
    transcription = Column(Text, nullable=True)
    response_text = Column(Text, nullable=True)
    response_audio_path = Column(String(500), nullable=True)
    language = Column(String(10), default="en")
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="voice_conversations")


class UploadedImage(Base):
    """Record of uploaded crop images."""
    __tablename__ = "uploaded_images"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    file_path = Column(String(500), nullable=False)
    file_name = Column(String(200), nullable=True)
    file_size = Column(Integer, nullable=True)
    purpose = Column(String(50), default="disease_detection")
    created_at = Column(DateTime, default=datetime.utcnow)


class AppLog(Base):
    """Application event logs."""
    __tablename__ = "app_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    level = Column(String(20), nullable=False)
    module = Column(String(100), nullable=True)
    message = Column(Text, nullable=False)
    extra_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_log_level", "level"),
        Index("idx_log_date", "created_at"),
    )

"""
FastAPI Backend
================
REST API for all Smart Crop Advisory System services.
"""

import os
import sys
from pathlib import Path
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
import tempfile

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.services.location_service import reverse_geocode, search_location
from backend.services.weather_service import get_current_weather
from backend.services.crop_service import recommend_crops
from backend.services.irrigation_service import calculate_water_requirement
from backend.services.fertilizer_service import recommend_fertilizers
from backend.services.market_service import get_market_analysis
from backend.services.disease_service import detect_disease
from backend.services.chat_service import chat
from backend.services.voice_service import speech_to_text, text_to_speech
from translation.translator import translate_text

# ── App Setup ────────────────────────────────────────────────────────────
app = FastAPI(
    title="Smart Crop Advisory System API",
    description="AI-powered agriculture advisory REST API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request/Response Models ──────────────────────────────────────────────
class LocationRequest(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)

class LocationSearchRequest(BaseModel):
    query: str

class WeatherRequest(BaseModel):
    latitude: float
    longitude: float

class CropRequest(BaseModel):
    nitrogen: float = Field(..., ge=0, le=200)
    phosphorus: float = Field(..., ge=0, le=200)
    potassium: float = Field(..., ge=0, le=250)
    temperature: float = Field(default=28.0)
    humidity: float = Field(default=65.0)
    ph: float = Field(..., ge=0, le=14)
    rainfall: float = Field(default=150.0)
    soil_type: str = "Loamy Soil"
    water_availability: float = 500.0
    state: Optional[str] = None
    district: Optional[str] = None

class IrrigationRequest(BaseModel):
    crop_name: str
    area_hectares: float = 1.0
    soil_type: str = "Loamy Soil"
    temperature: float = 28.0
    humidity: float = 65.0

class FertilizerRequest(BaseModel):
    crop_name: str
    nitrogen: float
    phosphorus: float
    potassium: float
    ph: float
    soil_type: str = "Loamy Soil"
    area_hectares: float = 1.0

class MarketRequest(BaseModel):
    crop_name: str
    area_hectares: float = 1.0

class ChatRequest(BaseModel):
    message: str
    language: str = "en"

class TranslateRequest(BaseModel):
    text: str
    target_lang: str
    source_lang: str = "en"


# ── Endpoints ────────────────────────────────────────────────────────────
@app.get("/")
def root():
    return {"message": "Smart Crop Advisory System API", "version": "1.0.0", "docs": "/docs"}

@app.post("/api/location/reverse")
def api_reverse_geocode(req: LocationRequest):
    result = reverse_geocode(req.latitude, req.longitude)
    if not result:
        raise HTTPException(404, "Location not found")
    return result

@app.post("/api/location/search")
def api_search_location(req: LocationSearchRequest):
    result = search_location(req.query)
    if not result:
        raise HTTPException(404, "Location not found")
    return result

@app.post("/api/weather")
def api_weather(req: WeatherRequest):
    result = get_current_weather(req.latitude, req.longitude)
    if not result:
        raise HTTPException(502, "Weather service unavailable")
    return result

@app.post("/api/crop/recommend")
def api_crop_recommend(req: CropRequest):
    result = recommend_crops(
        nitrogen=req.nitrogen, phosphorus=req.phosphorus,
        potassium=req.potassium, temperature=req.temperature,
        humidity=req.humidity, ph=req.ph, rainfall=req.rainfall,
        soil_type=req.soil_type, water_availability=req.water_availability,
        state=req.state, district=req.district,
    )
    return {"recommendations": result}

@app.post("/api/irrigation")
def api_irrigation(req: IrrigationRequest):
    return calculate_water_requirement(
        crop_name=req.crop_name, area_hectares=req.area_hectares,
        soil_type=req.soil_type, temperature=req.temperature, humidity=req.humidity,
    )

@app.post("/api/fertilizer")
def api_fertilizer(req: FertilizerRequest):
    return recommend_fertilizers(
        crop_name=req.crop_name, nitrogen=req.nitrogen,
        phosphorus=req.phosphorus, potassium=req.potassium,
        ph=req.ph, soil_type=req.soil_type, area_hectares=req.area_hectares,
    )

@app.post("/api/market")
def api_market(req: MarketRequest):
    return get_market_analysis(req.crop_name, req.area_hectares)

@app.post("/api/disease/detect")
async def api_disease_detect(file: UploadFile = File(...)):
    from PIL import Image
    import io
    contents = await file.read()
    image = Image.open(io.BytesIO(contents))
    return detect_disease(image)

@app.post("/api/chat")
def api_chat(req: ChatRequest):
    response = chat(req.message, language=req.language)
    return {"response": response}

@app.post("/api/translate")
def api_translate(req: TranslateRequest):
    result = translate_text(req.text, req.target_lang, req.source_lang)
    return {"translated": result}

@app.get("/api/health")
def health_check():
    return {"status": "healthy", "version": "1.0.0"}


# ── Run ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=os.environ.get("BACKEND_HOST", "127.0.0.1"),
        port=int(os.environ.get("BACKEND_PORT", 8000)),
        reload=True,
    )

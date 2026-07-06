"""
Crop Recommendation Service
=============================
ML-based crop recommendation using trained model + crop metadata enrichment.
"""

import os
import json
import numpy as np
import pandas as pd
from typing import Optional
from pathlib import Path
from utils.logger import get_logger
from utils.constants import CROP_DATABASE
from utils.helpers import calculate_profit

logger = get_logger("crop_service")

# Module-level model cache
_model = None
_scaler = None
_label_encoder = None

MODEL_DIR = Path(__file__).resolve().parent.parent.parent / "models" / "crop_recommendation"


def _load_model():
    """Load trained crop recommendation model, scaler, and label encoder."""
    global _model, _scaler, _label_encoder

    if _model is not None:
        return True

    try:
        import joblib

        model_path = MODEL_DIR / "model.pkl"
        scaler_path = MODEL_DIR / "scaler.pkl"
        encoder_path = MODEL_DIR / "label_encoder.pkl"

        if not model_path.exists():
            logger.warning(f"Model not found at {model_path}. Using rule-based fallback.")
            return False

        _model = joblib.load(str(model_path))
        _scaler = joblib.load(str(scaler_path)) if scaler_path.exists() else None
        _label_encoder = joblib.load(str(encoder_path)) if encoder_path.exists() else None

        logger.info("Crop recommendation model loaded successfully.")
        return True

    except Exception as e:
        logger.error(f"Error loading crop model: {e}")
        return False


# Geographic and climatological constraints for crops in India
CROP_GEOGRAPHIC_RESTRICTIONS = {
    "apple": {
        "allowed_states": ["jammu & kashmir", "himachal pradesh", "uttarakhand"],
        "message": "Apples require cool temperate climates found in northern hilly regions."
    },
    "coffee": {
        "allowed_states": ["karnataka", "kerala", "tamil nadu", "andhra pradesh", "odisha"],
        # Hilly coffee-growing districts in India
        "allowed_districts": [
            "kodagu", "coorg", "chikkamagaluru", "hassan", # Karnataka
            "wayanad", "idukki", "palakkad", "travancore", # Kerala
            "nilgiris", "salem", "dindigul", "theni", "coimbatore", # Tamil Nadu (Salem=Yercaud, Dindigul=Kodaikanal, Coimbatore=Valparai)
            "visakhapatnam", "arauku" # Andhra Pradesh
        ],
        "message": "Coffee requires high altitude, shade, and cool temperatures typical of hill stations."
    },
    "coconut": {
        "allowed_states": ["kerala", "tamil nadu", "karnataka", "andhra pradesh", "goa", "maharashtra", "odisha", "west bengal", "telangana", "pondicherry", "gujarat"],
        "message": "Coconut requires humid tropical coastal/sub-coastal climates."
    },
    "jute": {
        "allowed_states": ["west bengal", "bihar", "assam", "odisha", "uttar pradesh", "meghalaya", "tripura"],
        "message": "Jute requires hot and humid alluvial plains with high water availability."
    },
    "wheat": {
        "prohibited_states": ["kerala", "tamil nadu", "telangana", "andhra pradesh", "karnataka"],
        "message": "Wheat is a cool-season Rabi crop and is not suited for hot humid South Indian plains."
    },
    "grapes": {
        "allowed_states": ["maharashtra", "karnataka", "andhra pradesh", "tamil nadu", "telangana"],
        "allowed_districts": [
            "nashik", "sangli", "pune", "solapur",  # Maharashtra
            "bijapur", "vijayapura", "bagalkot", "kolar", "bangalore",  # Karnataka
            "theni", "dindigul", "coimbatore",  # Tamil Nadu (Cumbum Valley)
            "rangareddy", "medchal"  # Telangana
        ],
        "message": "Grapes require specific warm dry climates with trellis infrastructure."
    },
    "mothbeans": {
        # Moth beans are highly drought-tolerant, grown only in arid/semi-arid zones
        "allowed_states": ["rajasthan", "gujarat", "haryana", "maharashtra", "madhya pradesh", "uttar pradesh"],
        "message": "Moth beans are arid-zone crops suited for Rajasthan, Gujarat, and dry plains only."
    },
    "lentil": {
        # Lentils are Rabi (winter) crops requiring cool, dry weather - not suited for South India
        "prohibited_states": ["kerala", "tamil nadu", "andhra pradesh", "telangana", "karnataka"],
        "message": "Lentils are cool-season Rabi crops not suited for hot humid South Indian states."
    },
    "kidneybeans": {
        # Kidney beans prefer cool moderate temperatures - not suited for hot humid plains
        "prohibited_states": ["kerala", "tamil nadu"],
        "message": "Kidney beans prefer cool moderate temperatures and are not suited for Tamil Nadu's hot humid plains."
    },
    "chickpea": {
        "prohibited_states": ["kerala", "tamil nadu", "telangana", "andhra pradesh", "puducherry"],
        "message": "Chickpeas require cool, dry winters and are not suited for hot tropical South Indian plains."
    },
    "orange": {
        "prohibited_states": ["kerala", "tamil nadu", "andhra pradesh", "telangana", "puducherry"],
        "message": "Oranges require sub-tropical climates or cool hilly terrains, and are not suited for hot tropical plains."
    },
    "mungbean": {
        # Mung beans can grow in South India but prefer drier, warmer conditions
        "prohibited_states": [],  # No blanket restriction — suitable widely but watch temperature
        "message": "Mung beans grow well in many regions."
    },
    "blackgram": {
        # Black gram (urad) grows widely in South India
        "prohibited_states": [],
        "message": "Black gram grows well across South India."
    }
}

# Optimal and tolerable agronomic ranges for the 22 crops
CROP_AGRONOMIC_RANGES = {
    "rice": {
        "optimal_temp": (20.0, 35.0), "optimal_ph": (5.5, 7.2),
        "min_water_mm": 800, "optimal_soils": ["Clay Soil", "Loamy Soil", "Black Soil"],
        "min_n": 50, "min_p": 25, "min_k": 30
    },
    "maize": {
        "optimal_temp": (18.0, 32.0), "optimal_ph": (5.5, 7.5),
        "min_water_mm": 400, "optimal_soils": ["Loamy Soil", "Clay Soil", "Red Soil", "Black Soil"],
        "min_n": 40, "min_p": 20, "min_k": 20
    },
    "chickpea": {
        "optimal_temp": (15.0, 28.0), "optimal_ph": (6.0, 8.0),
        "min_water_mm": 350, "optimal_soils": ["Loamy Soil", "Red Soil", "Black Soil"],
        "min_n": 20, "min_p": 30, "min_k": 35
    },
    "kidneybeans": {
        "optimal_temp": (15.0, 25.0), "optimal_ph": (5.5, 7.0),
        "min_water_mm": 400, "optimal_soils": ["Loamy Soil", "Red Soil"],
        "min_n": 15, "min_p": 30, "min_k": 15
    },
    "pigeonpeas": {
        "optimal_temp": (18.0, 35.0), "optimal_ph": (5.5, 7.5),
        "min_water_mm": 500, "optimal_soils": ["Red Soil", "Loamy Soil", "Black Soil"],
        "min_n": 20, "min_p": 30, "min_k": 20
    },
    "mothbeans": {
        "optimal_temp": (25.0, 35.0), "optimal_ph": (6.5, 8.0),
        "min_water_mm": 250, "optimal_soils": ["Sandy Soil", "Red Soil", "Loamy Soil"],
        "min_n": 15, "min_p": 20, "min_k": 15
    },
    "mungbean": {
        "optimal_temp": (25.0, 35.0), "optimal_ph": (6.0, 7.5),
        "min_water_mm": 300, "optimal_soils": ["Loamy Soil", "Red Soil", "Sandy Soil"],
        "min_n": 15, "min_p": 20, "min_k": 15
    },
    "blackgram": {
        "optimal_temp": (25.0, 35.0), "optimal_ph": (6.0, 7.5),
        "min_water_mm": 400, "optimal_soils": ["Loamy Soil", "Black Soil", "Red Soil"],
        "min_n": 20, "min_p": 25, "min_k": 15
    },
    "lentil": {
        "optimal_temp": (10.0, 28.0), "optimal_ph": (5.5, 8.0),
        "min_water_mm": 300, "optimal_soils": ["Loamy Soil", "Red Soil", "Black Soil"],
        "min_n": 15, "min_p": 30, "min_k": 20
    },
    "pomegranate": {
        "optimal_temp": (18.0, 35.0), "optimal_ph": (5.5, 7.5),
        "min_water_mm": 400, "optimal_soils": ["Loamy Soil", "Red Soil", "Black Soil"],
        "min_n": 25, "min_p": 15, "min_k": 30
    },
    "banana": {
        "optimal_temp": (22.0, 35.0), "optimal_ph": (5.5, 7.5),
        "min_water_mm": 1000, "optimal_soils": ["Loamy Soil", "Clay Soil", "Red Soil", "Black Soil"],
        "min_n": 60, "min_p": 30, "min_k": 40
    },
    "mango": {
        "optimal_temp": (22.0, 38.0), "optimal_ph": (5.5, 7.5),
        "min_water_mm": 600, "optimal_soils": ["Loamy Soil", "Red Soil", "Laterite Soil"],
        "min_n": 20, "min_p": 15, "min_k": 20
    },
    "grapes": {
        "optimal_temp": (15.0, 32.0), "optimal_ph": (5.5, 7.0),
        "min_water_mm": 500, "optimal_soils": ["Loamy Soil", "Red Soil"],
        "min_n": 25, "min_p": 40, "min_k": 50
    },
    "watermelon": {
        "optimal_temp": (22.0, 35.0), "optimal_ph": (6.0, 7.2),
        "min_water_mm": 400, "optimal_soils": ["Sandy Soil", "Loamy Soil", "Red Soil"],
        "min_n": 40, "min_p": 20, "min_k": 30
    },
    "muskmelon": {
        "optimal_temp": (24.0, 38.0), "optimal_ph": (6.0, 7.5),
        "min_water_mm": 350, "optimal_soils": ["Sandy Soil", "Loamy Soil", "Red Soil"],
        "min_n": 40, "min_p": 20, "min_k": 30
    },
    "apple": {
        "optimal_temp": (10.0, 24.0), "optimal_ph": (5.5, 6.8),
        "min_water_mm": 800, "optimal_soils": ["Loamy Soil", "Red Soil"],
        "min_n": 30, "min_p": 40, "min_k": 50
    },
    "orange": {
        "optimal_temp": (18.0, 32.0), "optimal_ph": (6.0, 7.5),
        "min_water_mm": 700, "optimal_soils": ["Loamy Soil", "Red Soil", "Laterite Soil"],
        "min_n": 30, "min_p": 20, "min_k": 15
    },
    "papaya": {
        "optimal_temp": (22.0, 35.0), "optimal_ph": (6.0, 7.0),
        "min_water_mm": 600, "optimal_soils": ["Loamy Soil", "Sandy Soil", "Red Soil"],
        "min_n": 40, "min_p": 30, "min_k": 30
    },
    "coconut": {
        "optimal_temp": (22.0, 35.0), "optimal_ph": (5.2, 7.5),
        "min_water_mm": 1000, "optimal_soils": ["Sandy Soil", "Loamy Soil", "Red Soil"],
        "min_n": 30, "min_p": 15, "min_k": 25
    },
    "cotton": {
        "optimal_temp": (22.0, 35.0), "optimal_ph": (6.0, 7.8),
        "min_water_mm": 500, "optimal_soils": ["Black Soil", "Loamy Soil", "Red Soil"],
        "min_n": 60, "min_p": 30, "min_k": 20
    },
    "jute": {
        "optimal_temp": (24.0, 35.0), "optimal_ph": (6.0, 7.5),
        "min_water_mm": 1200, "optimal_soils": ["Clay Soil", "Loamy Soil"],
        "min_n": 50, "min_p": 30, "min_k": 30
    },
    "coffee": {
        "optimal_temp": (15.0, 26.0), "optimal_ph": (5.0, 6.5),
        "min_water_mm": 1200, "optimal_soils": ["Laterite Soil", "Loamy Soil", "Red Soil"],
        "min_n": 50, "min_p": 25, "min_k": 40
    }
}


def _calculate_agronomic_score(
    crop_key: str,
    nitrogen: float,
    phosphorus: float,
    potassium: float,
    temperature: float,
    humidity: float,
    ph: float,
    rainfall: float,
    soil_type: str,
    water_availability: float,
) -> tuple[float, list[str]]:
    """
    Calculate an accurate agronomic suitability score (0-100) and compile justification reasons.
    """
    limits = CROP_AGRONOMIC_RANGES.get(crop_key)
    crop_info = CROP_DATABASE.get(crop_key, {})
    if not limits or not crop_info:
        return 50.0, ["Default profile matching"]

    score = 0.0
    reasons = []

    # 1. Soil Type compatibility (30 points)
    optimal_soils = limits.get("optimal_soils", [])
    if soil_type in optimal_soils:
        score += 30.0
        reasons.append(f"Highly compatible soil type ({soil_type})")
    elif soil_type in crop_info.get("suitable_soil", []):
        score += 20.0
        reasons.append(f"Tolerable soil type ({soil_type})")
    else:
        score += 5.0

    # 2. pH suitability (20 points)
    opt_ph = limits["optimal_ph"]
    if opt_ph[0] <= ph <= opt_ph[1]:
        score += 20.0
        reasons.append("Optimal soil pH")
    elif opt_ph[0] - 0.6 <= ph <= opt_ph[1] + 0.6:
        score += 12.0
        reasons.append("Tolerable soil pH range")
    else:
        score += 2.0

    # 3. Temperature suitability (20 points)
    opt_temp = limits["optimal_temp"]
    if opt_temp[0] <= temperature <= opt_temp[1]:
        score += 20.0
        reasons.append("Ideal growing temperature")
    elif opt_temp[0] - 4.0 <= temperature <= opt_temp[1] + 4.0:
        score += 10.0
        reasons.append("Tolerable temperature range")
    else:
        score += 2.0

    # 4. Water suitability (20 points)
    # Total available water = rainfall (if any) or seasonal water availability
    total_water = max(rainfall, water_availability)
    min_water = limits["min_water_mm"]
    if total_water >= min_water:
        score += 20.0
        reasons.append("Sufficient moisture & water resources")
    elif total_water >= min_water * 0.7:
        score += 12.0
        reasons.append("Moderate water availability")
    else:
        score += 4.0

    # 5. Nutrient sufficiency (10 points)
    n_suff = nitrogen >= limits["min_n"]
    p_suff = phosphorus >= limits["min_p"]
    k_suff = potassium >= limits["min_k"]
    
    nut_score = 0
    if n_suff: 
        nut_score += 4
    if p_suff: 
        nut_score += 3
    if k_suff: 
        nut_score += 3
        
    score += nut_score
    if nut_score >= 8:
        reasons.append("Rich soil nutrient profile")

    # 6. Market demand bonus (10 points)
    demand = crop_info.get("market_demand", "Medium")
    if demand == "High":
        score += 10.0
        reasons.append("High market demand")
    elif demand == "Medium":
        score += 6.0

    # Cap to max 100
    final_score = min(score, 100.0)
    return round(final_score, 1), reasons


# District-level crop preferences to prioritize locally successful crops
DISTRICT_CROP_BOOSTS = {
    # Tamil Nadu
    ("karur", "tamil nadu"): ["banana", "coconut", "cotton", "maize", "rice", "blackgram", "mungbean", "papaya", "pomegranate"],
    ("coimbatore", "tamil nadu"): ["maize", "cotton", "coconut", "banana", "blackgram", "mungbean", "grapes", "pomegranate"],
    ("thanjavur", "tamil nadu"): ["rice", "coconut", "banana", "blackgram", "mungbean", "maize"],
    ("trichy", "tamil nadu"): ["rice", "banana", "coconut", "cotton", "maize", "blackgram"],
    ("madurai", "tamil nadu"): ["rice", "cotton", "coconut", "banana", "blackgram", "mungbean", "watermelon", "muskmelon"],
    # Andhra Pradesh
    ("guntur", "andhra pradesh"): ["cotton", "maize", "rice", "pigeonpeas", "blackgram"],
    ("anantapur", "andhra pradesh"): ["pomegranate", "watermelon", "muskmelon", "maize", "pigeonpeas"],
    # Rajasthan
    ("jaipur", "rajasthan"): ["maize", "watermelon", "muskmelon", "pomegranate"],
    ("jodhpur", "rajasthan"): ["mothbeans", "mungbean", "muskmelon", "watermelon"],
}


def recommend_crops(
    nitrogen: float,
    phosphorus: float,
    potassium: float,
    temperature: float,
    humidity: float,
    ph: float,
    rainfall: float,
    soil_type: str = "Loamy Soil",
    water_availability: float = 500.0,
    top_n: int = 5,
    state: Optional[str] = None,
    district: Optional[str] = None,
) -> list[dict]:
    """
    Recommend top N crops based on soil, weather, and geographical conditions.

    Args:
        nitrogen: Soil nitrogen content (kg/ha)
        phosphorus: Soil phosphorus content (kg/ha)
        potassium: Soil potassium content (kg/ha)
        temperature: Temperature (°C)
        humidity: Relative humidity (%)
        ph: Soil pH
        rainfall: Rainfall (mm)
        soil_type: Type of soil
        water_availability: Water availability (mm/season)
        top_n: Number of recommendations to return
        state: State name for geographical validation
        district: District name for detailed district-level checks (e.g., hill stations)

    Returns:
        List of crop recommendation dicts with all metadata
    """
    model_loaded = _load_model()

    if model_loaded and _model is not None:
        return _ml_recommend(
            nitrogen, phosphorus, potassium,
            temperature, humidity, ph, rainfall,
            soil_type, water_availability, top_n,
            state, district,
        )
    else:
        return _rule_based_recommend(
            nitrogen, phosphorus, potassium,
            temperature, humidity, ph, rainfall,
            soil_type, water_availability, top_n,
            state, district,
        )


def _ml_recommend(
    nitrogen, phosphorus, potassium,
    temperature, humidity, ph, rainfall,
    soil_type, water_availability, top_n,
    state=None, district=None,
) -> list[dict]:
    """ML model-based recommendation with geographic post-filtering and hybrid agronomic scoring."""
    try:
        # Prepare features (same order as training: N, P, K, temperature, humidity, ph, rainfall)
        features = np.array([[nitrogen, phosphorus, potassium, temperature, humidity, ph, rainfall]])

        if _scaler is not None:
            features = _scaler.transform(features)

        # Get probabilities for all crops
        if hasattr(_model, "predict_proba"):
            probabilities = _model.predict_proba(features)[0]
        else:
            prediction = _model.predict(features)[0]
            probabilities = np.zeros(len(_label_encoder.classes_) if _label_encoder else 22)
            probabilities[prediction if isinstance(prediction, int) else 0] = 1.0

        # Get class labels
        if _label_encoder is not None:
            classes = _label_encoder.classes_
        else:
            classes = list(CROP_DATABASE.keys())

        # Sort by probability
        sorted_indices = np.argsort(probabilities)[::-1]
        max_ml_prob = max(probabilities) if len(probabilities) > 0 else 0.0

        recommendations = []
        for idx in sorted_indices:
            crop_name = classes[idx] if idx < len(classes) else "unknown"
            ml_prob = float(probabilities[idx])
            crop_key = crop_name.lower().replace(" ", "")

            # Apply geographic restrictions
            if state or district:
                state_clean = state.lower().strip() if state else ""
                district_clean = district.lower().strip() if district else ""
                
                restriction = CROP_GEOGRAPHIC_RESTRICTIONS.get(crop_key)
                if restriction:
                    # Validate allowed states
                    if "allowed_states" in restriction:
                        if not any(s in state_clean for s in restriction["allowed_states"]):
                            logger.info(f"Filtering out {crop_name} for state '{state}': not in allowed states")
                            continue
                            
                    # Validate prohibited states
                    if "prohibited_states" in restriction:
                        if any(s in state_clean for s in restriction["prohibited_states"]):
                            logger.info(f"Filtering out {crop_name} for state '{state}': prohibited state")
                            continue
                            
                    # Validate allowed districts (specifically for hill station crops like coffee/grapes)
                    if "allowed_districts" in restriction:
                        if district_clean:
                            if not any(d in district_clean for d in restriction["allowed_districts"]):
                                logger.info(f"Filtering out {crop_name} for district '{district}': not a suitable hill district")
                                continue

            # Calculate agronomic suitability score and reasons
            rule_score, reasons = _calculate_agronomic_score(
                crop_key, nitrogen, phosphorus, potassium,
                temperature, humidity, ph, rainfall,
                soil_type, water_availability
            )
            
            # Hybrid Blending Logic:
            if max_ml_prob < 0.25:
                suitability_confidence = rule_score / 100.0
            else:
                suitability_confidence = (0.6 * (rule_score / 100.0)) + (0.4 * ml_prob)

            # Apply district boost
            if state and district:
                state_clean = state.lower().strip()
                district_clean = district.lower().strip()
                if district_clean == "tiruchirappalli":
                    district_clean = "trichy"
                boost_crops = DISTRICT_CROP_BOOSTS.get((district_clean, state_clean), [])
                if crop_key in boost_crops:
                    suitability_confidence = min(suitability_confidence * 1.15, 1.0)
                    if "Highly successful crop in this district" not in reasons:
                        reasons.append("Highly successful crop in this district")

            crop_data = _enrich_crop_data(
                crop_name, suitability_confidence, soil_type, water_availability,
                temperature, humidity, rainfall, reasons
            )
            if crop_data:
                recommendations.append(crop_data)
                if len(recommendations) >= top_n:
                    break

        # Ensure we have at least some recommendations
        if not recommendations:
            recommendations = _rule_based_recommend(
                nitrogen, phosphorus, potassium,
                temperature, humidity, ph, rainfall,
                soil_type, water_availability, top_n,
                state, district,
            )

        return recommendations

    except Exception as e:
        logger.error(f"ML recommendation error: {e}")
        return _rule_based_recommend(
            nitrogen, phosphorus, potassium,
            temperature, humidity, ph, rainfall,
            soil_type, water_availability, top_n,
            state, district,
        )


def _rule_based_recommend(
    nitrogen, phosphorus, potassium,
    temperature, humidity, ph, rainfall,
    soil_type, water_availability, top_n,
    state=None, district=None,
) -> list[dict]:
    """Rule-based fallback when ML model is unavailable."""
    logger.info("Using rule-based crop recommendation (model not loaded)")

    scores = {}

    for crop_key, crop in CROP_DATABASE.items():
        # Apply geographic restrictions first
        if state or district:
            state_clean = state.lower().strip() if state else ""
            district_clean = district.lower().strip() if district else ""
            
            restriction = CROP_GEOGRAPHIC_RESTRICTIONS.get(crop_key)
            if restriction:
                if "allowed_states" in restriction:
                    if not any(s in state_clean for s in restriction["allowed_states"]):
                        continue
                if "prohibited_states" in restriction:
                    if any(s in state_clean for s in restriction["prohibited_states"]):
                        continue
                if "allowed_districts" in restriction:
                    if district_clean:
                        if not any(d in district_clean for d in restriction["allowed_districts"]):
                            continue

        # Apply district boost
        if state and district:
            state_clean = state.lower().strip()
            district_clean = district.lower().strip()
            if district_clean == "tiruchirappalli":
                district_clean = "trichy"
            boost_crops = DISTRICT_CROP_BOOSTS.get((district_clean, state_clean), [])
            if crop_key in boost_crops:
                rule_score = min(rule_score * 1.15, 100.0)
                reasons.append("Highly successful crop in this district")

        scores[crop_key] = {"score": rule_score, "reasons": reasons}

    # Sort by score and take top N
    sorted_crops = sorted(scores.items(), key=lambda x: x[1]["score"], reverse=True)

    recommendations = []
    for crop_key, data in sorted_crops[:top_n]:
        confidence = data["score"] / 100.0
        crop_data = _enrich_crop_data(
            crop_key, confidence, soil_type, water_availability,
            temperature, humidity, rainfall, data["reasons"],
        )
        if crop_data:
            recommendations.append(crop_data)

    return recommendations


def _enrich_crop_data(
    crop_name: str,
    confidence: float,
    soil_type: str,
    water_availability: float,
    temperature: float,
    humidity: float,
    rainfall: float,
    reasons: list[str] = None,
) -> Optional[dict]:
    """Enrich crop recommendation with metadata from CROP_DATABASE."""
    crop_key = crop_name.lower().replace(" ", "")
    crop_info = CROP_DATABASE.get(crop_key)

    if crop_info is None:
        # Try fuzzy match
        for key in CROP_DATABASE:
            if key in crop_key or crop_key in key:
                crop_info = CROP_DATABASE[key]
                break

    if crop_info is None:
        return None

    # Calculate profit
    profit_data = calculate_profit(
        yield_tonnes=crop_info.get("yield_tonnes_per_ha", 3),
        price_per_quintal=crop_info.get("market_price_per_quintal", 2000),
        production_cost=crop_info.get("production_cost_per_ha", 40000),
    )

    # Calculate suitability score
    suitability = round(confidence * 100, 1)
    if soil_type in crop_info.get("suitable_soil", []):
        suitability = min(suitability + 5, 100)

    if reasons is None:
        reasons = []
        if soil_type in crop_info.get("suitable_soil", []):
            reasons.append(f"Suitable for {soil_type}")
        if crop_info.get("market_demand") == "High":
            reasons.append("High market demand")

    return {
        "crop_name": crop_info["name"],
        "crop_key": crop_key,
        "suitability_score": suitability,
        "confidence": round(confidence * 100, 1),
        "duration_days": crop_info.get("duration_days", 120),
        "season": crop_info.get("season", "Kharif"),
        "water_requirement_mm": crop_info.get("water_req_mm", 500),
        "irrigation_method": crop_info.get("irrigation_method", "Drip"),
        "irrigation_frequency": crop_info.get("irrigation_freq", "Every 5-7 days"),
        "fertilizer_n": crop_info.get("fertilizer_n", 100),
        "fertilizer_p": crop_info.get("fertilizer_p", 50),
        "fertilizer_k": crop_info.get("fertilizer_k", 50),
        "estimated_yield": f"{crop_info.get('yield_tonnes_per_ha', 3)} tonnes/ha",
        "market_demand": crop_info.get("market_demand", "Medium"),
        "estimated_profit": profit_data["net_profit"],
        "roi_percentage": profit_data["roi_percentage"],
        "production_cost": profit_data["production_cost"],
        "total_revenue": profit_data["total_revenue"],
        "price_per_quintal": crop_info.get("market_price_per_quintal", 2000),
        "suitable_soil": crop_info.get("suitable_soil", []),
        "reasons": reasons,
    }

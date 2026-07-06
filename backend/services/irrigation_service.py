"""
Irrigation Service
===================
Water requirement calculation and irrigation method recommendation.
"""

from utils.constants import CROP_DATABASE
from utils.logger import get_logger

logger = get_logger("irrigation")


def calculate_water_requirement(
    crop_name: str,
    area_hectares: float = 1.0,
    soil_type: str = "Loamy Soil",
    temperature: float = 28.0,
    humidity: float = 65.0,
    season_days: int = None,
) -> dict:
    """
    Calculate detailed irrigation requirements for a crop.

    Returns daily, weekly, monthly, seasonal water needs in litres,
    plus irrigation method and frequency recommendations.
    """
    crop_key = crop_name.lower().replace(" ", "")
    crop_info = CROP_DATABASE.get(crop_key)

    if crop_info is None:
        for key in CROP_DATABASE:
            if key in crop_key or crop_key in key:
                crop_info = CROP_DATABASE[key]
                break

    if crop_info is None:
        crop_info = {
            "water_req_mm": 500, "duration_days": 120,
            "irrigation_method": "Drip / Sprinkler",
            "irrigation_freq": "Every 5-7 days",
        }

    # Base water requirement
    total_water_mm = crop_info.get("water_req_mm", 500)
    duration = season_days or crop_info.get("duration_days", 120)

    # Adjustments based on conditions
    # Higher temperature = more water needed
    temp_factor = 1.0
    if temperature > 35:
        temp_factor = 1.25
    elif temperature > 30:
        temp_factor = 1.15
    elif temperature < 15:
        temp_factor = 0.8

    # Lower humidity = more evaporation = more water
    humidity_factor = 1.0
    if humidity < 40:
        humidity_factor = 1.2
    elif humidity < 60:
        humidity_factor = 1.1
    elif humidity > 80:
        humidity_factor = 0.9

    # Soil type factor (sandy drains faster, clay retains more)
    soil_factors = {
        "Sandy Soil": 1.3,
        "Red Soil": 1.15,
        "Loamy Soil": 1.0,
        "Black Soil": 0.9,
        "Clay Soil": 0.85,
        "Laterite Soil": 1.2,
    }
    soil_factor = soil_factors.get(soil_type, 1.0)

    # Adjusted total water
    adjusted_total_mm = total_water_mm * temp_factor * humidity_factor * soil_factor

    # Convert mm to litres (1 mm over 1 hectare = 10,000 litres)
    litres_per_mm_per_ha = 10000
    total_litres = adjusted_total_mm * litres_per_mm_per_ha * area_hectares

    daily_litres = total_litres / duration
    weekly_litres = daily_litres * 7
    monthly_litres = daily_litres * 30

    # Irrigation method recommendation
    methods = _recommend_irrigation_methods(crop_key, soil_type, total_water_mm)

    # Irrigation frequency
    frequency = _recommend_frequency(crop_key, soil_type, temperature)

    result = {
        "crop_name": crop_name,
        "area_hectares": area_hectares,
        "duration_days": duration,

        # Water requirements
        "daily_water_litres": round(daily_litres, 0),
        "weekly_water_litres": round(weekly_litres, 0),
        "monthly_water_litres": round(monthly_litres, 0),
        "seasonal_water_litres": round(total_litres, 0),

        "daily_water_mm": round(adjusted_total_mm / duration, 1),
        "total_water_mm": round(adjusted_total_mm, 0),

        # Adjustment factors
        "temperature_factor": temp_factor,
        "humidity_factor": humidity_factor,
        "soil_factor": soil_factor,

        # Recommendations
        "irrigation_methods": methods,
        "recommended_method": methods[0] if methods else {},
        "irrigation_frequency": frequency,

        # Original crop info
        "base_water_mm": total_water_mm,
        "crop_irrigation_method": crop_info.get("irrigation_method", "Drip"),
        "crop_irrigation_freq": crop_info.get("irrigation_freq", "Every 5-7 days"),
    }

    logger.info(f"Water calc: {crop_name} = {daily_litres:.0f} L/day for {area_hectares} ha")
    return result


def _recommend_irrigation_methods(crop_key: str, soil_type: str, water_mm: float) -> list[dict]:
    """Recommend irrigation methods ranked by suitability."""
    methods = []

    # Drip irrigation
    drip_score = 70
    drip_savings = 40  # % water savings
    if water_mm > 800:
        drip_score += 15
    if soil_type in ["Sandy Soil", "Red Soil", "Laterite Soil"]:
        drip_score += 10
    methods.append({
        "method": "Drip Irrigation",
        "icon": "💧",
        "suitability": min(drip_score, 100),
        "water_savings": f"{drip_savings}%",
        "pros": "Highest water efficiency, reduces weed growth, uniform water distribution",
        "cons": "Higher initial cost, requires filtration, may clog",
        "best_for": "Vegetables, fruits, orchards, row crops",
        "cost_estimate": "₹25,000 - ₹45,000 per hectare",
    })

    # Sprinkler
    sprinkler_score = 60
    if soil_type in ["Loamy Soil", "Sandy Soil"]:
        sprinkler_score += 15
    if water_mm < 600:
        sprinkler_score += 10
    methods.append({
        "method": "Sprinkler Irrigation",
        "icon": "🌧️",
        "suitability": min(sprinkler_score, 100),
        "water_savings": "25%",
        "pros": "Good coverage, suitable for uneven terrain, simulates rainfall",
        "cons": "Wind drift losses, higher energy cost, not suitable for heavy soils",
        "best_for": "Cereals, pulses, oilseeds",
        "cost_estimate": "₹15,000 - ₹30,000 per hectare",
    })

    # Flood / Furrow
    flood_score = 40
    if crop_key in ["rice", "jute"]:
        flood_score = 90  # Rice needs standing water
    if soil_type in ["Clay Soil", "Black Soil"]:
        flood_score += 15
    methods.append({
        "method": "Flood / Surface Irrigation",
        "icon": "🌊",
        "suitability": min(flood_score, 100),
        "water_savings": "0%",
        "pros": "Low cost, simple to implement, good for paddy",
        "cons": "High water wastage, uneven distribution, promotes waterlogging",
        "best_for": "Rice, sugarcane, field crops in clayey soils",
        "cost_estimate": "₹2,000 - ₹5,000 per hectare",
    })

    # Sort by suitability
    methods.sort(key=lambda x: x["suitability"], reverse=True)
    return methods


def _recommend_frequency(crop_key: str, soil_type: str, temperature: float) -> dict:
    """Recommend irrigation frequency."""
    # Base frequency from crop database
    crop_info = CROP_DATABASE.get(crop_key, {})
    base_freq = crop_info.get("irrigation_freq", "Every 5-7 days")

    # Adjust for temperature
    if temperature > 35:
        freq_note = "Increase frequency due to high temperature"
        interval_days = 2
    elif temperature > 30:
        freq_note = "Standard frequency"
        interval_days = 3
    elif temperature < 15:
        freq_note = "Reduce frequency in cool weather"
        interval_days = 7
    else:
        freq_note = "Normal irrigation schedule"
        interval_days = 4

    # Adjust for soil type
    if soil_type == "Sandy Soil":
        interval_days = max(1, interval_days - 1)
        freq_note += ". Sandy soil drains fast — irrigate more frequently."
    elif soil_type in ["Clay Soil", "Black Soil"]:
        interval_days += 1
        freq_note += ". Clay soil retains water — irrigate less frequently."

    return {
        "base_frequency": base_freq,
        "recommended_interval_days": interval_days,
        "schedule": f"Every {interval_days} days" if interval_days > 1 else "Daily",
        "note": freq_note,
        "best_time": "Early morning (6-8 AM) or evening (5-7 PM)",
    }

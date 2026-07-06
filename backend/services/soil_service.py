"""
Soil Service
=============
Provides location-based soil data (N, P, K, pH, moisture, soil type) 
using ISRIC SoilGrids point query API and local state-level agricultural profiles.
"""

import requests
from typing import Optional
from utils.logger import get_logger

logger = get_logger("soil")

# Baseline agricultural soil statistics for Indian states (N, P, K in kg/ha)
# Derived from standard regional Soil Health Card statistics.
STATE_SOIL_PROFILES = {
    "andhra pradesh": {
        "nitrogen": 78.0, "phosphorus": 38.0, "potassium": 165.0,
        "ph": 7.2, "moisture": 45.0, "water_availability": 600.0,
        "soil_type": "Red Soil"
    },
    "tamil nadu": {
        "nitrogen": 72.0, "phosphorus": 35.0, "potassium": 175.0,
        "ph": 6.6, "moisture": 40.0, "water_availability": 550.0,
        "soil_type": "Red Soil"
    },
    "karnataka": {
        "nitrogen": 74.0, "phosphorus": 32.0, "potassium": 155.0,
        "ph": 6.8, "moisture": 42.0, "water_availability": 500.0,
        "soil_type": "Red Soil"
    },
    "kerala": {
        "nitrogen": 88.0, "phosphorus": 26.0, "potassium": 125.0,
        "ph": 5.6, "moisture": 65.0, "water_availability": 1100.0,
        "soil_type": "Laterite Soil"
    },
    "telangana": {
        "nitrogen": 70.0, "phosphorus": 33.0, "potassium": 145.0,
        "ph": 7.0, "moisture": 40.0, "water_availability": 500.0,
        "soil_type": "Red Soil"
    },
    "maharashtra": {
        "nitrogen": 82.0, "phosphorus": 28.0, "potassium": 210.0,
        "ph": 7.7, "moisture": 38.0, "water_availability": 600.0,
        "soil_type": "Black Soil"
    },
    "madhya pradesh": {
        "nitrogen": 76.0, "phosphorus": 30.0, "potassium": 195.0,
        "ph": 7.4, "moisture": 35.0, "water_availability": 500.0,
        "soil_type": "Black Soil"
    },
    "uttar pradesh": {
        "nitrogen": 112.0, "phosphorus": 46.0, "potassium": 185.0,
        "ph": 7.2, "moisture": 50.0, "water_availability": 700.0,
        "soil_type": "Loamy Soil"
    },
    "rajasthan": {
        "nitrogen": 42.0, "phosphorus": 22.0, "potassium": 135.0,
        "ph": 8.1, "moisture": 20.0, "water_availability": 300.0,
        "soil_type": "Sandy Soil"
    },
    "gujarat": {
        "nitrogen": 78.0, "phosphorus": 34.0, "potassium": 170.0,
        "ph": 7.5, "moisture": 35.0, "water_availability": 450.0,
        "soil_type": "Black Soil"
    },
    "punjab": {
        "nitrogen": 118.0, "phosphorus": 48.0, "potassium": 205.0,
        "ph": 7.5, "moisture": 55.0, "water_availability": 800.0,
        "soil_type": "Loamy Soil"
    },
    "haryana": {
        "nitrogen": 114.0, "phosphorus": 45.0, "potassium": 195.0,
        "ph": 7.6, "moisture": 52.0, "water_availability": 750.0,
        "soil_type": "Loamy Soil"
    },
    "west bengal": {
        "nitrogen": 92.0, "phosphorus": 36.0, "potassium": 145.0,
        "ph": 6.3, "moisture": 58.0, "water_availability": 950.0,
        "soil_type": "Loamy Soil"
    },
    "bihar": {
        "nitrogen": 88.0, "phosphorus": 34.0, "potassium": 155.0,
        "ph": 6.8, "moisture": 48.0, "water_availability": 650.0,
        "soil_type": "Loamy Soil"
    },
    "odisha": {
        "nitrogen": 74.0, "phosphorus": 29.0, "potassium": 135.0,
        "ph": 6.1, "moisture": 50.0, "water_availability": 800.0,
        "soil_type": "Red Soil"
    }
}

# General fallback for any other location
DEFAULT_SOIL_PROFILE = {
    "nitrogen": 75.0, "phosphorus": 35.0, "potassium": 150.0,
    "ph": 6.5, "moisture": 45.0, "water_availability": 500.0,
    "soil_type": "Loamy Soil"
}


def get_location_soil_data(
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    state: Optional[str] = None
) -> dict:
    """
    Fetch/calculate point-based soil parameters (N, P, K, pH, Soil Type) 
    using GPS coordinates (via ISRIC SoilGrids API) and state baseline averages.
    
    Args:
        latitude: GPS latitude of target farm
        longitude: GPS longitude of target farm
        state: State name to load baseline profiles
        
    Returns:
        Dict with nitrogen, phosphorus, potassium, ph, moisture, water_availability, soil_type
    """
    # 1. Start with baseline profile based on State
    state_key = state.lower().strip() if state else ""
    baseline = STATE_SOIL_PROFILES.get(state_key, DEFAULT_SOIL_PROFILE).copy()
    
    # If no coordinates are provided, return the baseline profile immediately
    if latitude is None or longitude is None:
        logger.info(f"Returning baseline soil data for state: {state or 'Default'}")
        return baseline
        
    # 2. Query ISRIC SoilGrids API to refine values for Nitrogen, pH, and Soil Type
    url = "https://rest.isric.org/soilgrids/v2.0/properties/query"
    params = {
        "lat": latitude,
        "lon": longitude,
        "property": ["nitrogen", "phh2o", "clay", "sand", "silt"],
        "depth": "0-5cm",
        "value": "mean"
    }
    
    try:
        logger.info(f"Querying SoilGrids API for soil parameters at ({latitude}, {longitude})")
        response = requests.get(url, params=params, timeout=8)
        
        if response.status_code == 200:
            data = response.json()
            layers = data.get("properties", {}).get("layers", [])
            
            soil_props = {}
            for layer in layers:
                name = layer.get("name")
                depths = layer.get("depths", [])
                if depths:
                    val = depths[0].get("values", {}).get("mean")
                    if val is not None:
                        soil_props[name] = float(val)
            
            # Update Nitrogen if returned (cg/kg to kg/ha conversion, approx. scale * 0.8)
            if "nitrogen" in soil_props:
                raw_n = soil_props["nitrogen"]
                # Mapping typical SoilGrids N (100-300 cg/kg) to realistic agricultural kg/ha (80-240)
                baseline["nitrogen"] = round(raw_n * 0.8, 1)
                
            # Update pH if returned (pH is scaled by 10 in SoilGrids, e.g. 65 -> 6.5)
            if "phh2o" in soil_props:
                raw_ph = soil_props["phh2o"]
                baseline["ph"] = round(raw_ph / 10.0, 1)
                
            # Classify soil type based on Clay/Sand/Silt fractions (returned in g/kg)
            if "clay" in soil_props and "sand" in soil_props:
                clay_pct = soil_props["clay"] / 10.0
                sand_pct = soil_props["sand"] / 10.0
                
                if clay_pct > 35.0:
                    soil_type = "Clay Soil"
                elif sand_pct > 65.0:
                    soil_type = "Sandy Soil"
                else:
                    soil_type = "Loamy Soil"
                    
                # State-specific soil classification override
                if state_key in ["maharashtra", "madhya pradesh", "gujarat"]:
                    if soil_type in ["Clay Soil", "Loamy Soil"]:
                        soil_type = "Black Soil"
                elif state_key in ["kerala"]:
                    soil_type = "Laterite Soil"
                elif state_key in ["andhra pradesh", "tamil nadu", "karnataka", "telangana", "odisha"]:
                    if soil_type in ["Loamy Soil", "Sandy Soil"]:
                        soil_type = "Red Soil"
                        
                baseline["soil_type"] = soil_type
                
            logger.info(f"Successfully auto-filled soil values from SoilGrids API: N={baseline['nitrogen']}, pH={baseline['ph']}, Type={baseline['soil_type']}")
            return baseline
            
        else:
            logger.warning(f"SoilGrids API returned status {response.status_code}. Using state baseline averages.")
            return baseline
            
    except requests.RequestException as e:
        logger.error(f"SoilGrids API request failed: {e}. Using state baseline averages.")
        return baseline
    except Exception as e:
        logger.error(f"Unexpected error parsing SoilGrids data: {e}. Using state baseline averages.")
        return baseline

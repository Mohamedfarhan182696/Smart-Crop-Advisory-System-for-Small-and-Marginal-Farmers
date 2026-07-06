"""
Market Price Service
=====================
Market price analysis, predictions, profit calculations, and nearby market finder.
"""

import random
from datetime import datetime, timedelta
from typing import Optional
from utils.constants import CROP_DATABASE
from utils.helpers import calculate_profit, format_currency
from utils.logger import get_logger

logger = get_logger("market")


def get_market_analysis(crop_name: str, area_hectares: float = 1.0) -> dict:
    """
    Get comprehensive market analysis for a crop.

    Returns current price, historical trend, predictions, profit analysis.
    """
    crop_key = crop_name.lower().replace(" ", "")
    crop_info = CROP_DATABASE.get(crop_key, {})

    base_price = crop_info.get("market_price_per_quintal", 2000)
    production_cost = crop_info.get("production_cost_per_ha", 40000) * area_hectares
    yield_tonnes = crop_info.get("yield_tonnes_per_ha", 3) * area_hectares

    # Generate realistic price data
    current_price = base_price * random.uniform(0.92, 1.08)
    predicted_price = current_price * random.uniform(1.02, 1.15)
    min_price = base_price * 0.75
    max_price = base_price * 1.35

    # Historical prices (90 days)
    historical = _generate_historical_prices(base_price, days=90)

    # Profit analysis
    profit_data = calculate_profit(yield_tonnes, current_price, production_cost)
    predicted_profit = calculate_profit(yield_tonnes, predicted_price, production_cost)

    result = {
        "crop_name": crop_name,
        "area_hectares": area_hectares,

        # Price info
        "current_price": round(current_price, 2),
        "predicted_price": round(predicted_price, 2),
        "min_price": round(min_price, 2),
        "max_price": round(max_price, 2),
        "price_unit": "₹/quintal",

        # Historical data for charts
        "historical_prices": historical,

        # Profit analysis - current
        "current_profit": {
            **profit_data,
            "price_scenario": "Current Market Price",
        },

        # Profit analysis - predicted
        "predicted_profit": {
            **predicted_profit,
            "price_scenario": "Predicted Future Price",
        },

        # Market trend
        "trend": "Upward" if predicted_price > current_price else "Stable",
        "trend_percentage": round(((predicted_price - current_price) / current_price) * 100, 1),

        # Nearby markets (simulated)
        "nearby_markets": _get_nearby_markets(),
    }

    logger.info(f"Market analysis for {crop_name}: ₹{current_price:.0f}/q, Profit: ₹{profit_data['net_profit']:.0f}")
    return result


def _generate_historical_prices(base_price: float, days: int = 90) -> list[dict]:
    """Generate realistic historical price data."""
    prices = []
    current = base_price * 0.9

    for i in range(days):
        date = datetime.now() - timedelta(days=days - i)
        # Random walk with slight upward trend
        change = random.gauss(0.001, 0.02)
        current = current * (1 + change)
        current = max(base_price * 0.6, min(base_price * 1.5, current))

        prices.append({
            "date": date.strftime("%Y-%m-%d"),
            "price": round(current, 2),
        })

    return prices


def _get_nearby_markets() -> list[dict]:
    """Get list of nearby agricultural markets."""
    markets = [
        {
            "name": "Agricultural Produce Market Committee (APMC)",
            "type": "Government Mandi",
            "icon": "🏛️",
            "distance": f"{random.uniform(2, 15):.1f} km",
            "services": "Crop selling, Price discovery, Weighing",
            "timing": "6:00 AM - 2:00 PM",
        },
        {
            "name": "Krishi Vigyan Kendra (KVK)",
            "type": "Government Agricultural Center",
            "icon": "🌾",
            "distance": f"{random.uniform(5, 25):.1f} km",
            "services": "Seeds, Training, Soil testing",
            "timing": "9:00 AM - 5:00 PM",
        },
        {
            "name": "Primary Agricultural Cooperative Society",
            "type": "Cooperative",
            "icon": "🤝",
            "distance": f"{random.uniform(1, 8):.1f} km",
            "services": "Seeds, Fertilizers, Credit, Crop procurement",
            "timing": "8:00 AM - 4:00 PM",
        },
        {
            "name": "Seed & Fertilizer Shop",
            "type": "Private Retailer",
            "icon": "🏪",
            "distance": f"{random.uniform(0.5, 5):.1f} km",
            "services": "Seeds, Fertilizers, Pesticides, Equipment",
            "timing": "8:00 AM - 8:00 PM",
        },
        {
            "name": "e-NAM Online Trading",
            "type": "Online Marketplace",
            "icon": "📱",
            "distance": "Online",
            "services": "Online crop trading, Price discovery, Direct selling",
            "timing": "24/7",
            "website": "https://enam.gov.in",
        },
        {
            "name": "Government Procurement Center",
            "type": "MSP Procurement",
            "icon": "🏛️",
            "distance": f"{random.uniform(5, 30):.1f} km",
            "services": "Minimum Support Price procurement",
            "timing": "During procurement season",
        },
    ]
    return markets

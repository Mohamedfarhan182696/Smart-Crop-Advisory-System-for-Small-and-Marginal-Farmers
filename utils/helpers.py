"""
Utility Helpers
===============
Common utility functions used across the application.
"""

import os
import json
from datetime import datetime, timedelta
from typing import Any, Optional
from pathlib import Path


def format_currency(amount: float, currency: str = "₹") -> str:
    """Format a number as Indian currency."""
    if amount >= 10000000:  # 1 crore
        return f"{currency}{amount / 10000000:.2f} Cr"
    elif amount >= 100000:  # 1 lakh
        return f"{currency}{amount / 100000:.2f} L"
    elif amount >= 1000:
        return f"{currency}{amount:,.0f}"
    else:
        return f"{currency}{amount:.2f}"


def format_weight(kg: float) -> str:
    """Format weight with appropriate unit."""
    if kg >= 1000:
        return f"{kg / 1000:.1f} tonnes"
    elif kg >= 100:
        return f"{kg:.0f} kg"
    elif kg >= 1:
        return f"{kg:.1f} kg"
    else:
        return f"{kg * 1000:.0f} g"


def format_volume(litres: float) -> str:
    """Format volume with appropriate unit."""
    if litres >= 1000000:
        return f"{litres / 1000000:.2f} ML (Million Litres)"
    elif litres >= 1000:
        return f"{litres / 1000:.1f} KL"
    elif litres >= 1:
        return f"{litres:.0f} L"
    else:
        return f"{litres * 1000:.0f} mL"


def celsius_to_fahrenheit(celsius: float) -> float:
    """Convert Celsius to Fahrenheit."""
    return (celsius * 9 / 5) + 32


def mm_to_inches(mm: float) -> float:
    """Convert millimeters to inches."""
    return mm / 25.4


def hectare_to_acre(ha: float) -> float:
    """Convert hectares to acres."""
    return ha * 2.47105


def acre_to_hectare(acre: float) -> float:
    """Convert acres to hectares."""
    return acre / 2.47105


def litres_per_hectare_to_per_acre(lpf: float) -> float:
    """Convert litres/hectare to litres/acre."""
    return lpf / 2.47105


def kg_per_hectare_to_per_acre(kph: float) -> float:
    """Convert kg/hectare to kg/acre."""
    return kph / 2.47105


def get_season_from_month(month: int) -> str:
    """Get Indian agricultural season from month number."""
    if month in [6, 7, 8, 9, 10]:
        return "Kharif"
    elif month in [11, 12, 1, 2, 3]:
        return "Rabi"
    else:
        return "Zaid (Summer)"


def get_current_season() -> str:
    """Get the current agricultural season."""
    return get_season_from_month(datetime.now().month)


def safe_json_load(filepath: str) -> Optional[dict]:
    """Safely load a JSON file, returning None on error."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, Exception):
        return None


def safe_json_save(data: Any, filepath: str) -> bool:
    """Safely save data to a JSON file."""
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception:
        return False


def ensure_dir(path: str) -> str:
    """Ensure a directory exists, create if needed."""
    os.makedirs(path, exist_ok=True)
    return path


def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp a value between min and max."""
    return max(min_val, min(max_val, value))


def calculate_profit(
    yield_tonnes: float,
    price_per_quintal: float,
    production_cost: float,
) -> dict:
    """
    Calculate profit/loss analysis.

    Args:
        yield_tonnes: Expected yield in tonnes per hectare
        price_per_quintal: Market price per quintal (100 kg)
        production_cost: Total production cost per hectare

    Returns:
        Dict with revenue, profit, ROI, etc.
    """
    yield_quintals = yield_tonnes * 10  # 1 tonne = 10 quintals
    revenue = yield_quintals * price_per_quintal
    profit = revenue - production_cost
    roi = (profit / production_cost * 100) if production_cost > 0 else 0

    return {
        "yield_tonnes": yield_tonnes,
        "yield_quintals": yield_quintals,
        "price_per_quintal": price_per_quintal,
        "total_revenue": revenue,
        "production_cost": production_cost,
        "net_profit": profit,
        "roi_percentage": round(roi, 1),
        "is_profitable": profit > 0,
    }


def get_wind_direction_name(degrees: float) -> str:
    """Convert wind direction degrees to compass name."""
    directions = [
        "N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
        "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW",
    ]
    idx = round(degrees / 22.5) % 16
    return directions[idx]


def get_uv_level(uv_index: float) -> tuple[str, str]:
    """
    Get UV level description and color.

    Returns:
        (level_name, hex_color)
    """
    if uv_index <= 2:
        return "Low", "#4CAF50"
    elif uv_index <= 5:
        return "Moderate", "#FF9800"
    elif uv_index <= 7:
        return "High", "#FF5722"
    elif uv_index <= 10:
        return "Very High", "#F44336"
    else:
        return "Extreme", "#9C27B0"


def time_ago(dt: datetime) -> str:
    """Get human-readable time ago string."""
    now = datetime.now()
    diff = now - dt

    if diff.days > 365:
        years = diff.days // 365
        return f"{years} year{'s' if years > 1 else ''} ago"
    elif diff.days > 30:
        months = diff.days // 30
        return f"{months} month{'s' if months > 1 else ''} ago"
    elif diff.days > 0:
        return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    else:
        return "Just now"

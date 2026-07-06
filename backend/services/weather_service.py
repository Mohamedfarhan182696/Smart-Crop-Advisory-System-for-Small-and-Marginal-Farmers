"""
Weather Service
================
Open-Meteo API integration for real-time weather, soil data, and 7-day forecasts.
Free API — no key required.
"""

import requests
from datetime import datetime, timedelta
from typing import Optional
from utils.logger import get_logger
from cachetools import TTLCache

logger = get_logger("weather")

# Cache weather responses (1 hour TTL, max 100 entries)
_weather_cache = TTLCache(maxsize=100, ttl=3600)

OPEN_METEO_BASE = "https://api.open-meteo.com/v1"


def get_current_weather(latitude: float, longitude: float) -> Optional[dict]:
    """
    Fetch current weather + soil data from Open-Meteo.

    Args:
        latitude: GPS latitude
        longitude: GPS longitude

    Returns:
        Dict with temperature, humidity, rainfall, wind, pressure, UV,
        cloud cover, soil temperature, soil moisture
    """
    cache_key = f"current_{round(latitude, 2)}_{round(longitude, 2)}"
    if cache_key in _weather_cache:
        logger.info("Returning cached weather data")
        return _weather_cache[cache_key]

    try:
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": ",".join([
                "temperature_2m",
                "relative_humidity_2m",
                "apparent_temperature",
                "precipitation",
                "rain",
                "weather_code",
                "cloud_cover",
                "pressure_msl",
                "surface_pressure",
                "wind_speed_10m",
                "wind_direction_10m",
                "wind_gusts_10m",
            ]),
            "hourly": ",".join([
                "temperature_2m",
                "relative_humidity_2m",
                "precipitation",
                "uv_index",
                "soil_temperature_0cm",
                "soil_moisture_0_to_1cm",
            ]),
            "daily": ",".join([
                "temperature_2m_max",
                "temperature_2m_min",
                "precipitation_sum",
                "rain_sum",
                "wind_speed_10m_max",
                "uv_index_max",
                "sunrise",
                "sunset",
            ]),
            "timezone": "auto",
            "forecast_days": 7,
        }

        response = requests.get(f"{OPEN_METEO_BASE}/forecast", params=params, timeout=15)
        response.raise_for_status()
        data = response.json()

        current = data.get("current", {})
        hourly = data.get("hourly", {})
        daily = data.get("daily", {})

        # Get current hour index for hourly data
        current_hour = datetime.now().hour

        # Extract UV index from hourly (not available in current)
        uv_index = 0
        if hourly.get("uv_index") and len(hourly["uv_index"]) > current_hour:
            uv_index = hourly["uv_index"][current_hour] or 0

        # Extract soil data from hourly
        soil_temp = 0
        if hourly.get("soil_temperature_0cm") and len(hourly["soil_temperature_0cm"]) > current_hour:
            soil_temp = hourly["soil_temperature_0cm"][current_hour] or 0

        soil_moisture = 0
        if hourly.get("soil_moisture_0_to_1cm") and len(hourly["soil_moisture_0_to_1cm"]) > current_hour:
            soil_moisture = hourly["soil_moisture_0_to_1cm"][current_hour] or 0

        result = {
            # Current conditions
            "temperature": current.get("temperature_2m", 0),
            "feels_like": current.get("apparent_temperature", 0),
            "humidity": current.get("relative_humidity_2m", 0),
            "precipitation": current.get("precipitation", 0),
            "rainfall": current.get("rain", 0),
            "weather_code": current.get("weather_code", 0),
            "cloud_cover": current.get("cloud_cover", 0),
            "pressure": current.get("pressure_msl", 0),
            "surface_pressure": current.get("surface_pressure", 0),
            "wind_speed": current.get("wind_speed_10m", 0),
            "wind_direction": current.get("wind_direction_10m", 0),
            "wind_gusts": current.get("wind_gusts_10m", 0),

            # Hourly-derived
            "uv_index": uv_index,
            "soil_temperature": soil_temp,
            "soil_moisture": round(soil_moisture * 100, 1),  # Convert to percentage

            # 7-day forecast
            "forecast": _format_forecast(daily),

            # Hourly data for charts
            "hourly_temperature": hourly.get("temperature_2m", [])[:24],
            "hourly_humidity": hourly.get("relative_humidity_2m", [])[:24],
            "hourly_precipitation": hourly.get("precipitation", [])[:24],

            # Metadata
            "latitude": latitude,
            "longitude": longitude,
            "timezone": data.get("timezone", ""),
            "fetched_at": datetime.now().isoformat(),
        }

        # Interpret weather code
        result["weather_description"] = _get_weather_description(result["weather_code"])
        result["weather_icon"] = _get_weather_icon(result["weather_code"])

        # Cache the result
        _weather_cache[cache_key] = result
        logger.info(f"Weather fetched: {result['temperature']}°C, {result['humidity']}% humidity at {latitude},{longitude}")
        return result

    except requests.exceptions.RequestException as e:
        logger.error(f"Weather API request failed: {e}")
        return None
    except Exception as e:
        logger.error(f"Weather data processing error: {e}")
        return None


def _format_forecast(daily: dict) -> list[dict]:
    """Format daily forecast data into a list of day forecasts."""
    dates = daily.get("time", [])
    forecast = []

    for i, date_str in enumerate(dates):
        day = {
            "date": date_str,
            "day_name": _get_day_name(date_str),
            "temp_max": daily.get("temperature_2m_max", [0])[i] if i < len(daily.get("temperature_2m_max", [])) else 0,
            "temp_min": daily.get("temperature_2m_min", [0])[i] if i < len(daily.get("temperature_2m_min", [])) else 0,
            "precipitation": daily.get("precipitation_sum", [0])[i] if i < len(daily.get("precipitation_sum", [])) else 0,
            "rain": daily.get("rain_sum", [0])[i] if i < len(daily.get("rain_sum", [])) else 0,
            "wind_speed_max": daily.get("wind_speed_10m_max", [0])[i] if i < len(daily.get("wind_speed_10m_max", [])) else 0,
            "uv_index_max": daily.get("uv_index_max", [0])[i] if i < len(daily.get("uv_index_max", [])) else 0,
            "sunrise": daily.get("sunrise", [""])[i] if i < len(daily.get("sunrise", [])) else "",
            "sunset": daily.get("sunset", [""])[i] if i < len(daily.get("sunset", [])) else "",
        }
        forecast.append(day)

    return forecast


def _get_day_name(date_str: str) -> str:
    """Get day name from date string."""
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        if dt.date() == datetime.now().date():
            return "Today"
        elif dt.date() == (datetime.now() + timedelta(days=1)).date():
            return "Tomorrow"
        return dt.strftime("%A")
    except ValueError:
        return date_str


def _get_weather_description(code: int) -> str:
    """Convert WMO weather code to description."""
    descriptions = {
        0: "Clear sky",
        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Overcast",
        45: "Foggy",
        48: "Rime fog",
        51: "Light drizzle",
        53: "Moderate drizzle",
        55: "Dense drizzle",
        56: "Light freezing drizzle",
        57: "Dense freezing drizzle",
        61: "Slight rain",
        63: "Moderate rain",
        65: "Heavy rain",
        66: "Light freezing rain",
        67: "Heavy freezing rain",
        71: "Slight snowfall",
        73: "Moderate snowfall",
        75: "Heavy snowfall",
        77: "Snow grains",
        80: "Slight rain showers",
        81: "Moderate rain showers",
        82: "Violent rain showers",
        85: "Slight snow showers",
        86: "Heavy snow showers",
        95: "Thunderstorm",
        96: "Thunderstorm with hail",
        99: "Thunderstorm with heavy hail",
    }
    return descriptions.get(code, "Unknown")


def _get_weather_icon(code: int) -> str:
    """Get weather emoji icon from WMO code."""
    if code == 0:
        return "☀️"
    elif code in [1, 2]:
        return "⛅"
    elif code == 3:
        return "☁️"
    elif code in [45, 48]:
        return "🌫️"
    elif code in [51, 53, 55, 56, 57]:
        return "🌧️"
    elif code in [61, 63, 65, 66, 67, 80, 81, 82]:
        return "🌧️"
    elif code in [71, 73, 75, 77, 85, 86]:
        return "🌨️"
    elif code in [95, 96, 99]:
        return "⛈️"
    return "🌤️"

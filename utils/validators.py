"""
Input Validators
================
Validation functions for all user inputs with descriptive error messages.
"""

from typing import Optional


def validate_nitrogen(value: float) -> tuple[bool, str]:
    """Validate nitrogen input (0-140 kg/ha typical range)."""
    if value < 0:
        return False, "Nitrogen value cannot be negative."
    if value > 200:
        return False, "Nitrogen value seems too high. Typical range: 0-140 kg/ha."
    return True, ""


def validate_phosphorus(value: float) -> tuple[bool, str]:
    """Validate phosphorus input (0-145 kg/ha typical range)."""
    if value < 0:
        return False, "Phosphorus value cannot be negative."
    if value > 200:
        return False, "Phosphorus value seems too high. Typical range: 0-145 kg/ha."
    return True, ""


def validate_potassium(value: float) -> tuple[bool, str]:
    """Validate potassium input (0-205 kg/ha typical range)."""
    if value < 0:
        return False, "Potassium value cannot be negative."
    if value > 250:
        return False, "Potassium value seems too high. Typical range: 0-205 kg/ha."
    return True, ""


def validate_ph(value: float) -> tuple[bool, str]:
    """Validate soil pH (0-14 scale, agricultural range 3.5-10)."""
    if value < 0 or value > 14:
        return False, "Soil pH must be between 0 and 14."
    if value < 3.5 or value > 10:
        return False, "Soil pH for agriculture typically ranges from 3.5 to 10."
    return True, ""


def validate_moisture(value: float) -> tuple[bool, str]:
    """Validate soil moisture percentage (0-100%)."""
    if value < 0 or value > 100:
        return False, "Soil moisture must be between 0% and 100%."
    return True, ""


def validate_temperature(value: float) -> tuple[bool, str]:
    """Validate temperature in Celsius (-10 to 55°C for India)."""
    if value < -20 or value > 60:
        return False, "Temperature must be between -20°C and 60°C."
    return True, ""


def validate_humidity(value: float) -> tuple[bool, str]:
    """Validate humidity percentage (0-100%)."""
    if value < 0 or value > 100:
        return False, "Humidity must be between 0% and 100%."
    return True, ""


def validate_rainfall(value: float) -> tuple[bool, str]:
    """Validate rainfall in mm (0-5000mm)."""
    if value < 0:
        return False, "Rainfall cannot be negative."
    if value > 5000:
        return False, "Rainfall value seems too high. Maximum expected: 5000 mm."
    return True, ""


def validate_water_availability(value: float) -> tuple[bool, str]:
    """Validate water availability in mm/season."""
    if value < 0:
        return False, "Water availability cannot be negative."
    if value > 5000:
        return False, "Water availability seems too high."
    return True, ""


def validate_coordinates(lat: float, lon: float) -> tuple[bool, str]:
    """Validate GPS coordinates."""
    if lat < -90 or lat > 90:
        return False, "Latitude must be between -90 and 90."
    if lon < -180 or lon > 180:
        return False, "Longitude must be between -180 and 180."
    return True, ""


def validate_indian_coordinates(lat: float, lon: float) -> tuple[bool, str]:
    """Validate that coordinates are within India's approximate boundaries."""
    valid, msg = validate_coordinates(lat, lon)
    if not valid:
        return valid, msg
    # India approximate bounds: 6°N-37°N, 68°E-98°E
    if lat < 6 or lat > 37 or lon < 68 or lon > 98:
        return False, "Coordinates appear to be outside India. The system is optimized for Indian agriculture."
    return True, ""


def validate_soil_inputs(
    nitrogen: float,
    phosphorus: float,
    potassium: float,
    ph: float,
    moisture: float,
    water_availability: float,
    soil_type: str,
) -> tuple[bool, list[str]]:
    """
    Validate all soil analysis inputs at once.

    Returns:
        (is_valid, list_of_error_messages)
    """
    errors = []
    valid_soil_types = [
        "Black Soil", "Red Soil", "Sandy Soil",
        "Clay Soil", "Loamy Soil", "Laterite Soil",
    ]

    validators = [
        (validate_nitrogen, nitrogen, "Nitrogen"),
        (validate_phosphorus, phosphorus, "Phosphorus"),
        (validate_potassium, potassium, "Potassium"),
        (validate_ph, ph, "pH"),
        (validate_moisture, moisture, "Moisture"),
        (validate_water_availability, water_availability, "Water Availability"),
    ]

    for validator_fn, value, name in validators:
        is_valid, msg = validator_fn(value)
        if not is_valid:
            errors.append(f"{name}: {msg}")

    if soil_type not in valid_soil_types:
        errors.append(f"Invalid soil type: {soil_type}. Must be one of: {', '.join(valid_soil_types)}")

    return len(errors) == 0, errors

"""
Tests for Backend Services
============================
Unit tests for crop, weather, irrigation, fertilizer, and market services.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest


class TestValidators:
    """Test input validation functions."""

    def test_validate_nitrogen_valid(self):
        from utils.validators import validate_nitrogen
        valid, msg = validate_nitrogen(80)
        assert valid is True

    def test_validate_nitrogen_negative(self):
        from utils.validators import validate_nitrogen
        valid, msg = validate_nitrogen(-10)
        assert valid is False

    def test_validate_ph_valid(self):
        from utils.validators import validate_ph
        valid, msg = validate_ph(6.5)
        assert valid is True

    def test_validate_ph_out_of_range(self):
        from utils.validators import validate_ph
        valid, msg = validate_ph(15)
        assert valid is False

    def test_validate_soil_inputs_valid(self):
        from utils.validators import validate_soil_inputs
        valid, errors = validate_soil_inputs(80, 50, 40, 6.5, 50, 500, "Loamy Soil")
        assert valid is True
        assert len(errors) == 0

    def test_validate_soil_inputs_invalid_soil_type(self):
        from utils.validators import validate_soil_inputs
        valid, errors = validate_soil_inputs(80, 50, 40, 6.5, 50, 500, "Moon Soil")
        assert valid is False


class TestHelpers:
    """Test utility helper functions."""

    def test_format_currency(self):
        from utils.helpers import format_currency
        assert "₹" in format_currency(1000)
        assert "L" in format_currency(150000)
        assert "Cr" in format_currency(15000000)

    def test_calculate_profit(self):
        from utils.helpers import calculate_profit
        result = calculate_profit(4.5, 2040, 45000)
        assert result["net_profit"] > 0
        assert result["is_profitable"] is True
        assert "roi_percentage" in result

    def test_get_current_season(self):
        from utils.helpers import get_current_season
        season = get_current_season()
        assert season in ["Kharif", "Rabi", "Zaid (Summer)"]

    def test_wind_direction(self):
        from utils.helpers import get_wind_direction_name
        assert get_wind_direction_name(0) == "N"
        assert get_wind_direction_name(90) == "E"
        assert get_wind_direction_name(180) == "S"
        assert get_wind_direction_name(270) == "W"


class TestCropService:
    """Test crop recommendation service."""

    def test_recommend_crops_returns_list(self):
        from backend.services.crop_service import recommend_crops
        result = recommend_crops(
            nitrogen=80, phosphorus=50, potassium=40,
            temperature=28, humidity=65, ph=6.5, rainfall=150,
        )
        assert isinstance(result, list)
        assert len(result) <= 5
        assert len(result) > 0

    def test_recommend_crops_has_required_fields(self):
        from backend.services.crop_service import recommend_crops
        result = recommend_crops(80, 50, 40, 28, 65, 6.5, 150)
        if result:
            crop = result[0]
            assert "crop_name" in crop
            assert "suitability_score" in crop
            assert "confidence" in crop
            assert "season" in crop
            assert "estimated_profit" in crop


class TestIrrigationService:
    """Test irrigation calculation service."""

    def test_calculate_water_requirement(self):
        from backend.services.irrigation_service import calculate_water_requirement
        result = calculate_water_requirement("Rice", area_hectares=1.0)
        assert result["daily_water_litres"] > 0
        assert result["weekly_water_litres"] > result["daily_water_litres"]
        assert result["seasonal_water_litres"] > result["monthly_water_litres"]
        assert len(result["irrigation_methods"]) > 0

    def test_water_increases_with_area(self):
        from backend.services.irrigation_service import calculate_water_requirement
        r1 = calculate_water_requirement("Rice", area_hectares=1.0)
        r2 = calculate_water_requirement("Rice", area_hectares=2.0)
        assert r2["seasonal_water_litres"] > r1["seasonal_water_litres"]


class TestFertilizerService:
    """Test fertilizer recommendation service."""

    def test_recommend_fertilizers(self):
        from backend.services.fertilizer_service import recommend_fertilizers
        result = recommend_fertilizers("Rice", 40, 20, 15, 6.5)
        assert "organic" in result
        assert "chemical" in result
        assert "bio" in result
        assert "nutrient_analysis" in result
        assert result["total_estimated_cost"] >= 0


class TestMarketService:
    """Test market analysis service."""

    def test_get_market_analysis(self):
        from backend.services.market_service import get_market_analysis
        result = get_market_analysis("Rice")
        assert result["current_price"] > 0
        assert result["predicted_price"] > 0
        assert len(result["historical_prices"]) > 0
        assert len(result["nearby_markets"]) > 0


class TestDiseaseService:
    """Test disease detection service."""

    def test_demo_detect(self):
        from backend.services.disease_service import detect_disease
        from PIL import Image
        import numpy as np

        # Create a green test image (should detect as healthy)
        img_array = np.zeros((224, 224, 3), dtype=np.uint8)
        img_array[:, :, 1] = 150  # Green channel
        img = Image.fromarray(img_array)

        result = detect_disease(img)
        assert "disease_name" in result
        assert "confidence" in result
        assert "severity" in result


class TestChatService:
    """Test chatbot service."""

    def test_offline_chat_crop(self):
        from backend.services.chat_service import chat
        response = chat("What crop should I grow?")
        assert len(response) > 0
        assert "crop" in response.lower() or "Crop" in response

    def test_offline_chat_greeting(self):
        from backend.services.chat_service import chat
        response = chat("Hello")
        assert len(response) > 0
        assert "Krishi" in response or "farming" in response.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

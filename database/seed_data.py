"""
Seed Data
==========
Insert initial reference data into the database.
"""

from database.database import get_db_session
from database.models import MarketPrice
from datetime import datetime, timedelta
import random


def seed_initial_data():
    """Seed market prices and other reference data."""
    seed_market_prices()


def seed_market_prices():
    """Insert sample market price data for major crops."""
    crop_prices = {
        "rice": {"base": 2040, "min": 1800, "max": 2400},
        "wheat": {"base": 2125, "min": 1900, "max": 2500},
        "maize": {"base": 1962, "min": 1700, "max": 2300},
        "cotton": {"base": 6620, "min": 5800, "max": 7500},
        "jute": {"base": 4750, "min": 4200, "max": 5300},
        "chickpea": {"base": 5230, "min": 4500, "max": 6000},
        "lentil": {"base": 5500, "min": 4800, "max": 6200},
        "mungbean": {"base": 7275, "min": 6500, "max": 8000},
        "banana": {"base": 1200, "min": 800, "max": 1800},
        "mango": {"base": 4500, "min": 3000, "max": 6000},
        "coffee": {"base": 25000, "min": 20000, "max": 30000},
        "coconut": {"base": 2500, "min": 2000, "max": 3200},
        "apple": {"base": 5000, "min": 3500, "max": 7000},
        "grapes": {"base": 4000, "min": 2500, "max": 6000},
        "pomegranate": {"base": 5000, "min": 3500, "max": 7000},
        "orange": {"base": 3000, "min": 2000, "max": 4500},
        "papaya": {"base": 1200, "min": 800, "max": 1800},
        "watermelon": {"base": 800, "min": 400, "max": 1200},
        "pigeonpeas": {"base": 6600, "min": 5800, "max": 7500},
        "blackgram": {"base": 6000, "min": 5200, "max": 7000},
        "kidneybeans": {"base": 8000, "min": 6500, "max": 9500},
        "mothbeans": {"base": 5800, "min": 5000, "max": 6800},
    }

    markets = [
        ("Delhi Mandi", "Delhi"),
        ("Azadpur Mandi", "Delhi"),
        ("Vashi Market", "Maharashtra"),
        ("Koyambedu Market", "Tamil Nadu"),
        ("Yeshwanthpur Market", "Karnataka"),
        ("Bowenpally Market", "Telangana"),
    ]

    with get_db_session() as db:
        # Check if data already exists
        existing = db.query(MarketPrice).first()
        if existing:
            return  # Already seeded

        records = []
        for crop_name, prices in crop_prices.items():
            for days_ago in range(90):
                date = datetime.utcnow() - timedelta(days=days_ago)
                # Simulate price variation
                variation = random.uniform(-0.08, 0.08)
                trend = (90 - days_ago) / 90 * random.uniform(-0.05, 0.05)
                price = prices["base"] * (1 + variation + trend)

                market_name, state = random.choice(markets)

                record = MarketPrice(
                    crop_name=crop_name,
                    current_price=round(price, 2),
                    predicted_price=round(price * random.uniform(1.0, 1.1), 2),
                    min_price=prices["min"],
                    max_price=prices["max"],
                    market_name=market_name,
                    state=state,
                    data_date=date,
                )
                records.append(record)

        db.add_all(records)
        db.commit()


if __name__ == "__main__":
    seed_initial_data()

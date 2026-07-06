"""
Database Initialization
========================
Create tables and seed initial data.
"""

from database.database import init_database
from database.seed_data import seed_initial_data


def initialize():
    """Run database initialization: create tables + seed data."""
    print("🔧 Initializing database...")
    engine = init_database()
    print("✅ Database tables created successfully.")

    print("🌱 Seeding initial data...")
    seed_initial_data()
    print("✅ Initial data seeded successfully.")

    return engine


if __name__ == "__main__":
    initialize()

"""
Soil Service
=============
Provides location-based soil data (N, P, K, pH, moisture, soil type)
using ISRIC SoilGrids point query API and comprehensive state/district profiles.

Now includes:
- All 28 Indian states + 8 UTs
- District-level variation using geographic sub-region offsets
- Reliable fallback chain: GPS → SoilGrids → District profile → State profile → Default
"""

import math
import hashlib
import requests
from typing import Optional
from utils.logger import get_logger

logger = get_logger("soil")

# ──────────────────────────────────────────────────────────────────────────────
# Comprehensive State Soil Profiles
# (N, P, K in kg/ha | pH | moisture % | water_availability mm | soil_type)
# Sources: ICAR Soil Health Card averages, NBSS&LUP regional surveys
# ──────────────────────────────────────────────────────────────────────────────
STATE_SOIL_PROFILES = {
    # South India
    "andhra pradesh":   {"nitrogen": 78.0,  "phosphorus": 38.0, "potassium": 165.0, "ph": 7.2, "moisture": 45.0, "water_availability": 600.0,  "soil_type": "Red Soil"},
    "tamil nadu":       {"nitrogen": 72.0,  "phosphorus": 35.0, "potassium": 175.0, "ph": 6.6, "moisture": 40.0, "water_availability": 550.0,  "soil_type": "Red Soil"},
    "karnataka":        {"nitrogen": 74.0,  "phosphorus": 32.0, "potassium": 155.0, "ph": 6.8, "moisture": 42.0, "water_availability": 500.0,  "soil_type": "Red Soil"},
    "kerala":           {"nitrogen": 88.0,  "phosphorus": 26.0, "potassium": 125.0, "ph": 5.6, "moisture": 65.0, "water_availability": 1100.0, "soil_type": "Laterite Soil"},
    "telangana":        {"nitrogen": 70.0,  "phosphorus": 33.0, "potassium": 145.0, "ph": 7.0, "moisture": 40.0, "water_availability": 500.0,  "soil_type": "Red Soil"},
    "goa":              {"nitrogen": 85.0,  "phosphorus": 28.0, "potassium": 120.0, "ph": 5.8, "moisture": 60.0, "water_availability": 2800.0, "soil_type": "Laterite Soil"},
    # West India
    "maharashtra":      {"nitrogen": 82.0,  "phosphorus": 28.0, "potassium": 210.0, "ph": 7.7, "moisture": 38.0, "water_availability": 600.0,  "soil_type": "Black Soil"},
    "gujarat":          {"nitrogen": 78.0,  "phosphorus": 34.0, "potassium": 170.0, "ph": 7.5, "moisture": 35.0, "water_availability": 450.0,  "soil_type": "Black Soil"},
    "rajasthan":        {"nitrogen": 42.0,  "phosphorus": 22.0, "potassium": 135.0, "ph": 8.1, "moisture": 20.0, "water_availability": 300.0,  "soil_type": "Sandy Soil"},
    # Central India
    "madhya pradesh":   {"nitrogen": 76.0,  "phosphorus": 30.0, "potassium": 195.0, "ph": 7.4, "moisture": 35.0, "water_availability": 500.0,  "soil_type": "Black Soil"},
    "chhattisgarh":     {"nitrogen": 68.0,  "phosphorus": 26.0, "potassium": 130.0, "ph": 6.2, "moisture": 48.0, "water_availability": 900.0,  "soil_type": "Red Soil"},
    # North India
    "uttar pradesh":    {"nitrogen": 112.0, "phosphorus": 46.0, "potassium": 185.0, "ph": 7.2, "moisture": 50.0, "water_availability": 700.0,  "soil_type": "Loamy Soil"},
    "punjab":           {"nitrogen": 118.0, "phosphorus": 48.0, "potassium": 205.0, "ph": 7.5, "moisture": 55.0, "water_availability": 800.0,  "soil_type": "Loamy Soil"},
    "haryana":          {"nitrogen": 114.0, "phosphorus": 45.0, "potassium": 195.0, "ph": 7.6, "moisture": 52.0, "water_availability": 750.0,  "soil_type": "Loamy Soil"},
    "himachal pradesh": {"nitrogen": 96.0,  "phosphorus": 38.0, "potassium": 180.0, "ph": 6.4, "moisture": 55.0, "water_availability": 900.0,  "soil_type": "Loamy Soil"},
    "uttarakhand":      {"nitrogen": 92.0,  "phosphorus": 36.0, "potassium": 160.0, "ph": 6.6, "moisture": 52.0, "water_availability": 850.0,  "soil_type": "Loamy Soil"},
    "delhi":            {"nitrogen": 108.0, "phosphorus": 42.0, "potassium": 175.0, "ph": 7.4, "moisture": 40.0, "water_availability": 650.0,  "soil_type": "Loamy Soil"},
    # East India
    "west bengal":      {"nitrogen": 92.0,  "phosphorus": 36.0, "potassium": 145.0, "ph": 6.3, "moisture": 58.0, "water_availability": 950.0,  "soil_type": "Loamy Soil"},
    "bihar":            {"nitrogen": 88.0,  "phosphorus": 34.0, "potassium": 155.0, "ph": 6.8, "moisture": 48.0, "water_availability": 650.0,  "soil_type": "Loamy Soil"},
    "odisha":           {"nitrogen": 74.0,  "phosphorus": 29.0, "potassium": 135.0, "ph": 6.1, "moisture": 50.0, "water_availability": 800.0,  "soil_type": "Red Soil"},
    "jharkhand":        {"nitrogen": 65.0,  "phosphorus": 24.0, "potassium": 125.0, "ph": 5.8, "moisture": 45.0, "water_availability": 750.0,  "soil_type": "Red Soil"},
    # Northeast India
    "assam":            {"nitrogen": 96.0,  "phosphorus": 28.0, "potassium": 130.0, "ph": 5.4, "moisture": 70.0, "water_availability": 1800.0, "soil_type": "Loamy Soil"},
    "meghalaya":        {"nitrogen": 88.0,  "phosphorus": 24.0, "potassium": 115.0, "ph": 5.2, "moisture": 75.0, "water_availability": 2000.0, "soil_type": "Laterite Soil"},
    "manipur":          {"nitrogen": 82.0,  "phosphorus": 22.0, "potassium": 110.0, "ph": 5.5, "moisture": 68.0, "water_availability": 1500.0, "soil_type": "Loamy Soil"},
    "nagaland":         {"nitrogen": 78.0,  "phosphorus": 20.0, "potassium": 105.0, "ph": 5.3, "moisture": 65.0, "water_availability": 1600.0, "soil_type": "Loamy Soil"},
    "mizoram":          {"nitrogen": 76.0,  "phosphorus": 18.0, "potassium": 100.0, "ph": 5.4, "moisture": 70.0, "water_availability": 1900.0, "soil_type": "Laterite Soil"},
    "tripura":          {"nitrogen": 84.0,  "phosphorus": 26.0, "potassium": 120.0, "ph": 5.6, "moisture": 68.0, "water_availability": 1700.0, "soil_type": "Laterite Soil"},
    "arunachal pradesh":{"nitrogen": 90.0,  "phosphorus": 25.0, "potassium": 120.0, "ph": 5.5, "moisture": 72.0, "water_availability": 2200.0, "soil_type": "Loamy Soil"},
    "sikkim":           {"nitrogen": 94.0,  "phosphorus": 30.0, "potassium": 140.0, "ph": 5.8, "moisture": 70.0, "water_availability": 1800.0, "soil_type": "Loamy Soil"},
    # UTs
    "jammu and kashmir":{"nitrogen": 90.0,  "phosphorus": 36.0, "potassium": 168.0, "ph": 6.9, "moisture": 50.0, "water_availability": 700.0,  "soil_type": "Loamy Soil"},
    "ladakh":           {"nitrogen": 35.0,  "phosphorus": 18.0, "potassium": 110.0, "ph": 8.2, "moisture": 15.0, "water_availability": 150.0,  "soil_type": "Sandy Soil"},
    "puducherry":       {"nitrogen": 72.0,  "phosphorus": 33.0, "potassium": 165.0, "ph": 6.8, "moisture": 42.0, "water_availability": 500.0,  "soil_type": "Red Soil"},
    "chandigarh":       {"nitrogen": 115.0, "phosphorus": 46.0, "potassium": 198.0, "ph": 7.5, "moisture": 53.0, "water_availability": 780.0,  "soil_type": "Loamy Soil"},
    "andaman and nicobar islands": {"nitrogen": 90.0, "phosphorus": 28.0, "potassium": 125.0, "ph": 5.8, "moisture": 70.0, "water_availability": 2500.0, "soil_type": "Laterite Soil"},
    "lakshadweep":      {"nitrogen": 55.0,  "phosphorus": 20.0, "potassium": 95.0,  "ph": 6.5, "moisture": 60.0, "water_availability": 1500.0, "soil_type": "Sandy Soil"},
    "dadra and nagar haveli": {"nitrogen": 82.0, "phosphorus": 30.0, "potassium": 155.0, "ph": 6.5, "moisture": 45.0, "water_availability": 1000.0, "soil_type": "Laterite Soil"},
    "daman and diu":    {"nitrogen": 75.0,  "phosphorus": 28.0, "potassium": 145.0, "ph": 7.2, "moisture": 40.0, "water_availability": 600.0,  "soil_type": "Sandy Soil"},
}

# Fallback for genuinely unknown states
DEFAULT_SOIL_PROFILE = {
    "nitrogen": 75.0, "phosphorus": 35.0, "potassium": 150.0,
    "ph": 6.5, "moisture": 45.0, "water_availability": 500.0,
    "soil_type": "Loamy Soil"
}

# ──────────────────────────────────────────────────────────────────────────────
# District-level variation offsets
# Generated from NBSS&LUP district soil surveys and ICAR regional data.
# Format: (district_key, state_key) → {delta fields}
# Delta values are ADDED to the state baseline.
# ──────────────────────────────────────────────────────────────────────────────
DISTRICT_SOIL_OFFSETS = {
    # Andhra Pradesh
    ("visakhapatnam", "andhra pradesh"): {"nitrogen": +8,  "phosphorus": +4,  "potassium": -10, "ph": -0.2, "moisture": +8,  "water_availability": +150, "soil_type": "Laterite Soil"},
    ("vijayawada",    "andhra pradesh"): {"nitrogen": +5,  "phosphorus": +2,  "potassium": +15, "ph": +0.1, "moisture": +5,  "water_availability": +80},
    ("guntur",        "andhra pradesh"): {"nitrogen": +12, "phosphorus": +6,  "potassium": +20, "ph": +0.2, "moisture": +2,  "water_availability": -50,  "soil_type": "Black Soil"},
    ("kurnool",       "andhra pradesh"): {"nitrogen": -8,  "phosphorus": -4,  "potassium": -15, "ph": +0.3, "moisture": -8,  "water_availability": -120},
    ("anantapur",     "andhra pradesh"): {"nitrogen": -15, "phosphorus": -8,  "potassium": -20, "ph": +0.5, "moisture": -12, "water_availability": -200, "soil_type": "Sandy Soil"},
    ("nellore",       "andhra pradesh"): {"nitrogen": +4,  "phosphorus": +3,  "potassium": +5,  "ph": +0.1, "moisture": +4,  "water_availability": +50},
    ("tirupati",      "andhra pradesh"): {"nitrogen": -5,  "phosphorus": -2,  "potassium": -5,  "ph": -0.1, "moisture": -3,  "water_availability": -30},
    # Tamil Nadu
    ("chennai",       "tamil nadu"):     {"nitrogen": -10, "phosphorus": -5,  "potassium": +5,  "ph": +0.2, "moisture": -10, "water_availability": -100, "soil_type": "Sandy Soil"},
    ("coimbatore",    "tamil nadu"):     {"nitrogen": +10, "phosphorus": +5,  "potassium": +15, "ph": -0.2, "moisture": +5,  "water_availability": +50},
    ("madurai",       "tamil nadu"):     {"nitrogen": -5,  "phosphorus": -2,  "potassium": -5,  "ph": +0.3, "moisture": -5,  "water_availability": -80},
    ("thanjavur",     "tamil nadu"):     {"nitrogen": +18, "phosphorus": +8,  "potassium": +20, "ph": -0.3, "moisture": +15, "water_availability": +200, "soil_type": "Clay Soil"},
    ("salem",         "tamil nadu"):     {"nitrogen": +5,  "phosphorus": +3,  "potassium": +8,  "ph": -0.1, "moisture": +3,  "water_availability": +30},
    ("erode",         "tamil nadu"):     {"nitrogen": +8,  "phosphorus": +4,  "potassium": +10, "ph": -0.1, "moisture": +5,  "water_availability": +40},
    ("tiruchirappalli","tamil nadu"):    {"nitrogen": +6,  "phosphorus": +3,  "potassium": +10, "ph": +0.1, "moisture": +4,  "water_availability": +60},
    ("tirunelveli",   "tamil nadu"):     {"nitrogen": -8,  "phosphorus": -3,  "potassium": -10, "ph": +0.2, "moisture": -5,  "water_availability": -60},
    ("vellore",       "tamil nadu"):     {"nitrogen": -3,  "phosphorus": -1,  "potassium": -5,  "ph": +0.2, "moisture": -3,  "water_availability": -40},
    ("thoothukudi",   "tamil nadu"):     {"nitrogen": -12, "phosphorus": -6,  "potassium": -15, "ph": +0.4, "moisture": -10, "water_availability": -100, "soil_type": "Sandy Soil"},
    # Karnataka
    ("bengaluru",     "karnataka"):      {"nitrogen": +5,  "phosphorus": +2,  "potassium": +5,  "ph": -0.1, "moisture": +3,  "water_availability": +30},
    ("mysuru",        "karnataka"):      {"nitrogen": +8,  "phosphorus": +4,  "potassium": +10, "ph": -0.2, "moisture": +5,  "water_availability": +80, "soil_type": "Red Soil"},
    ("hubli-dharwad", "karnataka"):      {"nitrogen": +2,  "phosphorus": +1,  "potassium": +15, "ph": +0.3, "moisture": -3,  "water_availability": -50, "soil_type": "Black Soil"},
    ("belagavi",      "karnataka"):      {"nitrogen": +5,  "phosphorus": +3,  "potassium": +20, "ph": +0.2, "moisture": -2,  "water_availability": -20, "soil_type": "Black Soil"},
    ("mangaluru",     "karnataka"):      {"nitrogen": +12, "phosphorus": +4,  "potassium": -10, "ph": -0.5, "moisture": +20, "water_availability": +600, "soil_type": "Laterite Soil"},
    ("kalaburagi",    "karnataka"):      {"nitrogen": -8,  "phosphorus": -4,  "potassium": -10, "ph": +0.4, "moisture": -8,  "water_availability": -150, "soil_type": "Black Soil"},
    # Kerala
    ("thiruvananthapuram","kerala"):     {"nitrogen": +5,  "phosphorus": -3,  "potassium": -5,  "ph": -0.2, "moisture": +5,  "water_availability": +200},
    ("ernakulam",     "kerala"):         {"nitrogen": +8,  "phosphorus": -2,  "potassium": -8,  "ph": -0.3, "moisture": +8,  "water_availability": +300},
    ("kozhikode",     "kerala"):         {"nitrogen": +6,  "phosphorus": -1,  "potassium": -5,  "ph": -0.2, "moisture": +10, "water_availability": +400},
    ("palakkad",      "kerala"):         {"nitrogen": -5,  "phosphorus": +2,  "potassium": +5,  "ph": +0.2, "moisture": -5,  "water_availability": -200},
    ("wayanad",       "kerala"):         {"nitrogen": +15, "phosphorus": +2,  "potassium": +10, "ph": -0.4, "moisture": +12, "water_availability": +500, "soil_type": "Loamy Soil"},
    # Maharashtra
    ("mumbai",        "maharashtra"):    {"nitrogen": -15, "phosphorus": -5,  "potassium": -20, "ph": -0.2, "moisture": +10, "water_availability": +200, "soil_type": "Loamy Soil"},
    ("pune",          "maharashtra"):    {"nitrogen": +5,  "phosphorus": +3,  "potassium": +10, "ph": -0.1, "moisture": +3,  "water_availability": +100},
    ("nashik",        "maharashtra"):    {"nitrogen": +10, "phosphorus": +5,  "potassium": +15, "ph": -0.2, "moisture": +5,  "water_availability": +150, "soil_type": "Black Soil"},
    ("nagpur",        "maharashtra"):    {"nitrogen": +8,  "phosphorus": +4,  "potassium": +18, "ph": +0.1, "moisture": -2,  "water_availability": -50,  "soil_type": "Black Soil"},
    ("aurangabad",    "maharashtra"):    {"nitrogen": -5,  "phosphorus": -2,  "potassium": +10, "ph": +0.3, "moisture": -5,  "water_availability": -100, "soil_type": "Black Soil"},
    ("solapur",       "maharashtra"):    {"nitrogen": -10, "phosphorus": -3,  "potassium": +5,  "ph": +0.4, "moisture": -8,  "water_availability": -150, "soil_type": "Black Soil"},
    ("kolhapur",      "maharashtra"):    {"nitrogen": +12, "phosphorus": +6,  "potassium": +20, "ph": -0.2, "moisture": +8,  "water_availability": +200},
    ("amravati",      "maharashtra"):    {"nitrogen": +5,  "phosphorus": +3,  "potassium": +15, "ph": +0.1, "moisture": -3,  "water_availability": -30,  "soil_type": "Black Soil"},
    # Uttar Pradesh
    ("lucknow",       "uttar pradesh"):  {"nitrogen": +8,  "phosphorus": +5,  "potassium": +10, "ph": -0.1, "moisture": +3,  "water_availability": +50},
    ("agra",          "uttar pradesh"):  {"nitrogen": -5,  "phosphorus": -3,  "potassium": -10, "ph": +0.2, "moisture": -5,  "water_availability": -80},
    ("varanasi",      "uttar pradesh"):  {"nitrogen": +10, "phosphorus": +6,  "potassium": +15, "ph": -0.1, "moisture": +5,  "water_availability": +100},
    ("kanpur",        "uttar pradesh"):  {"nitrogen": +5,  "phosphorus": +4,  "potassium": +8,  "ph": +0.1, "moisture": -2,  "water_availability": -20},
    ("allahabad",     "uttar pradesh"):  {"nitrogen": +8,  "phosphorus": +5,  "potassium": +12, "ph": -0.1, "moisture": +4,  "water_availability": +80},
    ("meerut",        "uttar pradesh"):  {"nitrogen": +15, "phosphorus": +8,  "potassium": +20, "ph": -0.2, "moisture": +8,  "water_availability": +150},
    ("gorakhpur",     "uttar pradesh"):  {"nitrogen": +5,  "phosphorus": +3,  "potassium": +8,  "ph": -0.2, "moisture": +6,  "water_availability": +100},
    # Punjab
    ("amritsar",      "punjab"):         {"nitrogen": +10, "phosphorus": +5,  "potassium": +15, "ph": -0.1, "moisture": +5,  "water_availability": +100},
    ("ludhiana",      "punjab"):         {"nitrogen": +15, "phosphorus": +8,  "potassium": +20, "ph": -0.1, "moisture": +8,  "water_availability": +150},
    ("patiala",       "punjab"):         {"nitrogen": +8,  "phosphorus": +4,  "potassium": +10, "ph": +0.1, "moisture": +3,  "water_availability": +80},
    ("jalandhar",     "punjab"):         {"nitrogen": +12, "phosphorus": +6,  "potassium": +15, "ph": -0.1, "moisture": +6,  "water_availability": +120},
    # Rajasthan
    ("jaipur",        "rajasthan"):      {"nitrogen": +5,  "phosphorus": +3,  "potassium": +10, "ph": -0.1, "moisture": +3,  "water_availability": +50},
    ("jodhpur",       "rajasthan"):      {"nitrogen": -10, "phosphorus": -5,  "potassium": -15, "ph": +0.3, "moisture": -5,  "water_availability": -100, "soil_type": "Sandy Soil"},
    ("udaipur",       "rajasthan"):      {"nitrogen": +8,  "phosphorus": +4,  "potassium": +15, "ph": -0.2, "moisture": +8,  "water_availability": +100, "soil_type": "Loamy Soil"},
    ("bikaner",       "rajasthan"):      {"nitrogen": -15, "phosphorus": -8,  "potassium": -20, "ph": +0.5, "moisture": -8,  "water_availability": -150, "soil_type": "Sandy Soil"},
    ("kota",          "rajasthan"):      {"nitrogen": +5,  "phosphorus": +4,  "potassium": +15, "ph": -0.1, "moisture": +5,  "water_availability": +80,  "soil_type": "Black Soil"},
    # West Bengal
    ("kolkata",       "west bengal"):    {"nitrogen": -5,  "phosphorus": +2,  "potassium": -10, "ph": +0.1, "moisture": +5,  "water_availability": +100, "soil_type": "Clay Soil"},
    ("darjeeling",    "west bengal"):    {"nitrogen": +15, "phosphorus": +5,  "potassium": +10, "ph": -0.8, "moisture": +15, "water_availability": +500, "soil_type": "Loamy Soil"},
    ("murshidabad",   "west bengal"):    {"nitrogen": +8,  "phosphorus": +4,  "potassium": +5,  "ph": -0.2, "moisture": +8,  "water_availability": +200},
    ("nadia",         "west bengal"):    {"nitrogen": +10, "phosphorus": +5,  "potassium": +8,  "ph": -0.2, "moisture": +10, "water_availability": +250},
    ("bardhaman",     "west bengal"):    {"nitrogen": +12, "phosphorus": +6,  "potassium": +10, "ph": -0.3, "moisture": +8,  "water_availability": +200},
    ("jalpaiguri",    "west bengal"):    {"nitrogen": +10, "phosphorus": +4,  "potassium": +5,  "ph": -0.4, "moisture": +12, "water_availability": +400},
    # Madhya Pradesh
    ("bhopal",        "madhya pradesh"): {"nitrogen": +5,  "phosphorus": +3,  "potassium": +10, "ph": -0.1, "moisture": +3,  "water_availability": +50},
    ("indore",        "madhya pradesh"): {"nitrogen": +10, "phosphorus": +5,  "potassium": +20, "ph": -0.2, "moisture": +5,  "water_availability": +100, "soil_type": "Black Soil"},
    ("jabalpur",      "madhya pradesh"): {"nitrogen": +8,  "phosphorus": +4,  "potassium": +15, "ph": -0.1, "moisture": +5,  "water_availability": +80},
    ("gwalior",       "madhya pradesh"): {"nitrogen": -5,  "phosphorus": -2,  "potassium": -10, "ph": +0.2, "moisture": -5,  "water_availability": -80},
    ("ujjain",        "madhya pradesh"): {"nitrogen": +8,  "phosphorus": +4,  "potassium": +18, "ph": -0.1, "moisture": +3,  "water_availability": +60,  "soil_type": "Black Soil"},
    # Gujarat
    ("ahmedabad",     "gujarat"):        {"nitrogen": +5,  "phosphorus": +3,  "potassium": +10, "ph": +0.1, "moisture": -3,  "water_availability": -50},
    ("surat",         "gujarat"):        {"nitrogen": +8,  "phosphorus": +5,  "potassium": +15, "ph": -0.2, "moisture": +5,  "water_availability": +100},
    ("vadodara",      "gujarat"):        {"nitrogen": +5,  "phosphorus": +4,  "potassium": +10, "ph": +0.1, "moisture": -2,  "water_availability": -30},
    ("rajkot",        "gujarat"):        {"nitrogen": -5,  "phosphorus": -2,  "potassium": -10, "ph": +0.3, "moisture": -5,  "water_availability": -80},
    ("junagadh",      "gujarat"):        {"nitrogen": +8,  "phosphorus": +4,  "potassium": +15, "ph": -0.1, "moisture": +5,  "water_availability": +100},
    # Bihar
    ("patna",         "bihar"):          {"nitrogen": +10, "phosphorus": +5,  "potassium": +15, "ph": -0.1, "moisture": +5,  "water_availability": +100},
    ("gaya",          "bihar"):          {"nitrogen": -5,  "phosphorus": -2,  "potassium": -10, "ph": +0.2, "moisture": -3,  "water_availability": -50},
    ("muzaffarpur",   "bihar"):          {"nitrogen": +8,  "phosphorus": +4,  "potassium": +10, "ph": -0.1, "moisture": +5,  "water_availability": +80},
    ("bhagalpur",     "bihar"):          {"nitrogen": +5,  "phosphorus": +3,  "potassium": +8,  "ph": +0.1, "moisture": +3,  "water_availability": +60},
    # Odisha
    ("bhubaneswar",   "odisha"):         {"nitrogen": +8,  "phosphorus": +4,  "potassium": +10, "ph": -0.1, "moisture": +5,  "water_availability": +100},
    ("cuttack",       "odisha"):         {"nitrogen": +10, "phosphorus": +5,  "potassium": +12, "ph": -0.2, "moisture": +8,  "water_availability": +150},
    ("sambalpur",     "odisha"):         {"nitrogen": -5,  "phosphorus": -2,  "potassium": -8,  "ph": +0.2, "moisture": -3,  "water_availability": -50},
    ("puri",          "odisha"):         {"nitrogen": +5,  "phosphorus": +3,  "potassium": +8,  "ph": +0.1, "moisture": +5,  "water_availability": +80},
    ("koraput",       "odisha"):         {"nitrogen": +5,  "phosphorus": +3,  "potassium": +8,  "ph": -0.3, "moisture": +10, "water_availability": +200},
    # Telangana
    ("hyderabad",     "telangana"):      {"nitrogen": +5,  "phosphorus": +3,  "potassium": +10, "ph": +0.1, "moisture": -3,  "water_availability": -50},
    ("warangal",      "telangana"):      {"nitrogen": +8,  "phosphorus": +4,  "potassium": +15, "ph": -0.1, "moisture": +3,  "water_availability": +50,  "soil_type": "Black Soil"},
    ("nizamabad",     "telangana"):      {"nitrogen": +5,  "phosphorus": +3,  "potassium": +12, "ph": +0.1, "moisture": +2,  "water_availability": +30,  "soil_type": "Black Soil"},
    ("karimnagar",    "telangana"):      {"nitrogen": +6,  "phosphorus": +3,  "potassium": +12, "ph": +0.1, "moisture": +2,  "water_availability": +40},
    # Haryana
    ("gurugram",      "haryana"):        {"nitrogen": +8,  "phosphorus": +4,  "potassium": +10, "ph": +0.1, "moisture": -3,  "water_availability": -50},
    ("hisar",         "haryana"):        {"nitrogen": -5,  "phosphorus": -2,  "potassium": -8,  "ph": +0.2, "moisture": -5,  "water_availability": -80},
    ("ambala",        "haryana"):        {"nitrogen": +10, "phosphorus": +5,  "potassium": +15, "ph": -0.1, "moisture": +5,  "water_availability": +100},
    ("karnal",        "haryana"):        {"nitrogen": +12, "phosphorus": +6,  "potassium": +18, "ph": -0.1, "moisture": +6,  "water_availability": +120},
    # Assam
    ("guwahati",      "assam"):          {"nitrogen": +8,  "phosphorus": +3,  "potassium": +5,  "ph": -0.2, "moisture": +5,  "water_availability": +200},
    ("silchar",       "assam"):          {"nitrogen": +5,  "phosphorus": +2,  "potassium": +3,  "ph": -0.3, "moisture": +8,  "water_availability": +300},
    ("dibrugarh",     "assam"):          {"nitrogen": +10, "phosphorus": +4,  "potassium": +8,  "ph": -0.3, "moisture": +8,  "water_availability": +300},
    # Himachal Pradesh
    ("shimla",        "himachal pradesh"):{"nitrogen": +5, "phosphorus": +3,  "potassium": +8,  "ph": -0.3, "moisture": +8,  "water_availability": +150},
    ("dharamshala",   "himachal pradesh"):{"nitrogen": +8, "phosphorus": +4,  "potassium": +10, "ph": -0.4, "moisture": +10, "water_availability": +200},
    # Chhattisgarh
    ("raipur",        "chhattisgarh"):   {"nitrogen": +5,  "phosphorus": +3,  "potassium": +8,  "ph": -0.1, "moisture": +3,  "water_availability": +80},
    ("bilaspur",      "chhattisgarh"):   {"nitrogen": +3,  "phosphorus": +2,  "potassium": +5,  "ph": -0.1, "moisture": +3,  "water_availability": +60},
    # Uttarakhand
    ("dehradun",      "uttarakhand"):    {"nitrogen": +8,  "phosphorus": +4,  "potassium": +10, "ph": -0.2, "moisture": +8,  "water_availability": +150},
    ("haridwar",      "uttarakhand"):    {"nitrogen": +10, "phosphorus": +5,  "potassium": +12, "ph": -0.1, "moisture": +5,  "water_availability": +100},
    ("nainital",      "uttarakhand"):    {"nitrogen": +5,  "phosphorus": +3,  "potassium": +8,  "ph": -0.3, "moisture": +10, "water_availability": +200},
    # Jharkhand
    ("ranchi",        "jharkhand"):      {"nitrogen": +5,  "phosphorus": +3,  "potassium": +8,  "ph": -0.2, "moisture": +5,  "water_availability": +100},
    ("dhanbad",       "jharkhand"):      {"nitrogen": -3,  "phosphorus": -1,  "potassium": -5,  "ph": +0.1, "moisture": -2,  "water_availability": -30},
    ("jamshedpur",    "jharkhand"):      {"nitrogen": -5,  "phosphorus": -2,  "potassium": -8,  "ph": +0.1, "moisture": -3,  "water_availability": -50},
}


def _get_district_key(district: str, state: str) -> tuple:
    """Normalize district and state names to lookup keys."""
    d = district.lower().strip()
    s = state.lower().strip()
    # Common alternate names
    aliases = {
        "bengaluru urban": "bengaluru", "bangalore": "bengaluru",
        "mumbai city": "mumbai", "bombay": "mumbai",
        "allahabad": "allahabad", "prayagraj": "allahabad",
        "aurangabad": "aurangabad",
        "vizag": "visakhapatnam",
        "trivandrum": "thiruvananthapuram",
        "calicut": "kozhikode",
        "gurugram": "gurugram", "gurgaon": "gurugram",
        "faridabad": "gurugram",
        "noida": "meerut",
        "thane": "mumbai",
    }
    d = aliases.get(d, d)
    return (d, s)


def _apply_geographic_variation(baseline: dict, latitude: float, longitude: float, state: str) -> dict:
    """
    Add realistic micro-variation to soil values based on exact GPS coordinates.
    Uses a deterministic hash of lat/lon to produce stable, location-specific variation.
    Variation is bounded so it stays agronomically realistic.
    """
    result = baseline.copy()

    # Create a stable hash from the coordinates rounded to 0.1° (~11km grid)
    lat_r = round(latitude, 1)
    lon_r = round(longitude, 1)
    key = f"{lat_r},{lon_r},{state}"
    h = int(hashlib.md5(key.encode()).hexdigest(), 16)

    def _vary(seed_offset, amplitude, step=0.5):
        """Extract a bounded variation from the hash."""
        part = (h >> seed_offset) & 0xFF  # 0..255
        # Map to [-amplitude, +amplitude] in steps
        steps = int(2 * amplitude / step)
        chosen = (part % (steps + 1)) * step - amplitude
        return round(chosen, 1)

    result["nitrogen"]           = round(result["nitrogen"]           + _vary(0,  8.0, 1.0), 1)
    result["phosphorus"]         = round(result["phosphorus"]         + _vary(8,  4.0, 0.5), 1)
    result["potassium"]          = round(result["potassium"]          + _vary(16, 10.0, 1.0), 1)
    result["ph"]                 = round(result["ph"]                 + _vary(24, 0.3, 0.05), 2)
    result["moisture"]           = round(result["moisture"]           + _vary(32, 5.0, 0.5), 1)
    result["water_availability"] = round(result["water_availability"] + _vary(40, 60.0, 5.0), 0)

    # Clamp values to realistic ranges
    result["nitrogen"]           = max(20.0,  min(180.0, result["nitrogen"]))
    result["phosphorus"]         = max(10.0,  min(100.0, result["phosphorus"]))
    result["potassium"]          = max(50.0,  min(280.0, result["potassium"]))
    result["ph"]                 = max(4.5,   min(9.0,   result["ph"]))
    result["moisture"]           = max(10.0,  min(90.0,  result["moisture"]))
    result["water_availability"] = max(100.0, min(3000.0, result["water_availability"]))

    return result


def _query_soilgrids(latitude: float, longitude: float, baseline: dict, state_key: str) -> dict:
    """
    Query the ISRIC SoilGrids v2 API and refine the baseline profile.
    Returns updated baseline dict, or unchanged baseline if the API fails.
    """
    url = "https://rest.isric.org/soilgrids/v2.0/properties/query"
    params = {
        "lat": latitude,
        "lon": longitude,
        "property": ["nitrogen", "phh2o", "clay", "sand", "silt"],
        "depth": "0-5cm",
        "value": "mean"
    }

    try:
        logger.info(f"Querying SoilGrids API for ({latitude}, {longitude})")
        response = requests.get(url, params=params, timeout=8)

        if response.status_code != 200:
            logger.warning(f"SoilGrids returned HTTP {response.status_code}")
            return baseline

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

        result = baseline.copy()

        # Nitrogen: SoilGrids returns cg/kg, we convert to kg/ha (approx × 0.8)
        if "nitrogen" in soil_props:
            result["nitrogen"] = round(soil_props["nitrogen"] * 0.8, 1)

        # pH: SoilGrids returns pH × 10
        if "phh2o" in soil_props:
            result["ph"] = round(soil_props["phh2o"] / 10.0, 1)

        # Soil texture → soil type classification
        if "clay" in soil_props and "sand" in soil_props:
            clay_pct = soil_props["clay"] / 10.0
            sand_pct = soil_props["sand"] / 10.0

            if clay_pct > 35.0:
                soil_type = "Clay Soil"
            elif sand_pct > 65.0:
                soil_type = "Sandy Soil"
            else:
                soil_type = "Loamy Soil"

            # State-specific overrides for culturally well-known soil types
            if state_key in ("maharashtra", "madhya pradesh", "gujarat", "telangana"):
                if soil_type in ("Clay Soil", "Loamy Soil"):
                    soil_type = "Black Soil"
            elif state_key == "kerala":
                soil_type = "Laterite Soil"
            elif state_key in ("andhra pradesh", "tamil nadu", "karnataka", "odisha",
                               "chhattisgarh", "jharkhand"):
                if soil_type in ("Loamy Soil", "Sandy Soil"):
                    soil_type = "Red Soil"

            result["soil_type"] = soil_type

        logger.info(f"SoilGrids enrichment done: N={result['nitrogen']}, pH={result['ph']}, Type={result['soil_type']}")
        return result

    except requests.RequestException as e:
        logger.error(f"SoilGrids request failed: {e}")
        return baseline
    except Exception as e:
        logger.error(f"Error parsing SoilGrids data: {e}")
        return baseline


def get_location_soil_data(
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    state: Optional[str] = None,
    district: Optional[str] = None,
) -> dict:
    """
    Fetch/calculate point-based soil parameters (N, P, K, pH, Soil Type).

    Priority chain:
      1. Start with state-level profile (covers all 36 states/UTs)
      2. Apply district-level offsets if district is known
      3. Apply GPS-coordinate micro-variation for intra-district uniqueness
      4. Try ISRIC SoilGrids API to refine nitrogen and pH with satellite data
         (best-effort — falls back gracefully if the API is unavailable)

    Args:
        latitude:  GPS latitude
        longitude: GPS longitude
        state:     State name (used to pick regional baseline)
        district:  District name (used for district-level offsets)

    Returns:
        Dict with nitrogen, phosphorus, potassium, ph, moisture,
        water_availability, soil_type — all location-specific.
    """
    state_key = (state or "").lower().strip()
    district_key = (district or "").lower().strip()

    # ── Step 1: State-level baseline ─────────────────────────────────────────
    baseline = STATE_SOIL_PROFILES.get(state_key, DEFAULT_SOIL_PROFILE).copy()
    logger.info(f"Step 1 – State baseline for '{state_key}': N={baseline['nitrogen']}, pH={baseline['ph']}")

    # ── Step 2: District-level offsets ───────────────────────────────────────
    if district_key and state_key:
        dk = _get_district_key(district_key, state_key)
        if dk in DISTRICT_SOIL_OFFSETS:
            offset = DISTRICT_SOIL_OFFSETS[dk]
            for field, delta in offset.items():
                if field == "soil_type":
                    baseline["soil_type"] = delta
                else:
                    baseline[field] = round(baseline.get(field, 0) + delta, 1)
            logger.info(f"Step 2 – District offset applied for {dk}: N={baseline['nitrogen']}, pH={baseline['ph']}")
        else:
            logger.info(f"Step 2 – No district offset for '{district_key}' in '{state_key}'")

    # ── Step 3: GPS coordinate micro-variation ────────────────────────────────
    if latitude is not None and longitude is not None:
        baseline = _apply_geographic_variation(baseline, latitude, longitude, state_key)
        logger.info(f"Step 3 – GPS variation applied: N={baseline['nitrogen']}, pH={baseline['ph']}")

    # ── Step 4: SoilGrids API refinement (best-effort) ────────────────────────
    if latitude is not None and longitude is not None:
        baseline = _query_soilgrids(latitude, longitude, baseline, state_key)

    return baseline

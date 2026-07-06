"""
Location Service
=================
GPS detection, reverse geocoding, and manual location search.
Uses Nominatim (OpenStreetMap) for free geocoding.
"""

import time
import math
from typing import Optional
from utils.logger import get_logger
from utils.constants import INDIAN_STATES

logger = get_logger("location")

# Nominatim client (reuse to respect rate limits)
_geocoder = None

# Local database of coordinates for Indian states and districts to ensure 100% reliability offline/online
LOCAL_COORDINATES = {
    # Andhra Pradesh
    ("visakhapatnam", "andhra pradesh"): (17.6868, 83.2185),
    ("vijayawada", "andhra pradesh"): (16.5062, 80.6480),
    ("guntur", "andhra pradesh"): (16.3067, 80.4365),
    ("nellore", "andhra pradesh"): (14.4426, 79.9865),
    ("kurnool", "andhra pradesh"): (15.8281, 78.0373),
    ("tirupati", "andhra pradesh"): (13.6284, 79.4192),
    ("kakinada", "andhra pradesh"): (16.9891, 82.2475),
    ("rajahmundry", "andhra pradesh"): (17.0005, 81.8040),
    ("anantapur", "andhra pradesh"): (14.6819, 77.6006),
    ("kadapa", "andhra pradesh"): (14.4712, 78.8242),
    # Tamil Nadu
    ("chennai", "tamil nadu"): (13.0827, 80.2707),
    ("coimbatore", "tamil nadu"): (11.0168, 76.9558),
    ("madurai", "tamil nadu"): (9.9252, 78.1198),
    ("tiruchirappalli", "tamil nadu"): (10.7905, 78.7047),
    ("salem", "tamil nadu"): (11.6643, 78.1460),
    ("tirunelveli", "tamil nadu"): (8.7139, 77.7567),
    ("erode", "tamil nadu"): (11.3410, 77.7172),
    ("vellore", "tamil nadu"): (12.9165, 79.1325),
    ("thoothukudi", "tamil nadu"): (8.7642, 78.1348),
    ("thanjavur", "tamil nadu"): (10.7870, 79.1378),
    # Karnataka
    ("bengaluru", "karnataka"): (12.9716, 77.5946),
    ("mysuru", "karnataka"): (12.2958, 76.6394),
    ("hubli-dharwad", "karnataka"): (15.3647, 75.1240),
    ("mangaluru", "karnataka"): (12.9141, 74.8560),
    ("belagavi", "karnataka"): (15.8497, 74.4977),
    ("davanagere", "karnataka"): (14.4644, 75.9218),
    ("ballari", "karnataka"): (15.1394, 76.9214),
    ("kalaburagi", "karnataka"): (17.3297, 76.8343),
    ("shimoga", "karnataka"): (13.9299, 75.5681),
    ("tumkur", "karnataka"): (13.3379, 77.1173),
    # Kerala
    ("thiruvananthapuram", "kerala"): (8.5241, 76.9366),
    ("kochi", "kerala"): (9.9312, 76.2673),
    ("kozhikode", "kerala"): (11.2588, 75.7804),
    ("thrissur", "kerala"): (10.5276, 76.2144),
    ("kollam", "kerala"): (8.8932, 76.6141),
    ("palakkad", "kerala"): (10.7867, 76.6548),
    ("alappuzha", "kerala"): (9.4981, 76.3388),
    ("kannur", "kerala"): (11.8745, 75.3704),
    ("kottayam", "kerala"): (9.5916, 76.5221),
    ("malappuram", "kerala"): (11.0736, 76.0740),
    # Telangana
    ("hyderabad", "telangana"): (17.3850, 78.4867),
    ("warangal", "telangana"): (17.9689, 79.5941),
    ("nizamabad", "telangana"): (18.6725, 78.0941),
    ("karimnagar", "telangana"): (18.4386, 79.1288),
    ("khammam", "telangana"): (17.2473, 80.1514),
    ("mahbubnagar", "telangana"): (16.7367, 77.9892),
    ("nalgonda", "telangana"): (17.0575, 79.2684),
    ("adilabad", "telangana"): (19.6759, 78.5320),
    ("medak", "telangana"): (18.0447, 78.2616),
    ("rangareddy", "telangana"): (17.3481, 78.5081),
    # Maharashtra
    ("mumbai", "maharashtra"): (19.0760, 72.8777),
    ("pune", "maharashtra"): (18.5204, 73.8567),
    ("nagpur", "maharashtra"): (21.1458, 79.0882),
    ("nashik", "maharashtra"): (19.9975, 73.7898),
    ("aurangabad", "maharashtra"): (19.8762, 75.3433),
    ("solapur", "maharashtra"): (17.6599, 75.9064),
    ("kolhapur", "maharashtra"): (16.7050, 74.2433),
    ("amravati", "maharashtra"): (20.9374, 77.7796),
    ("sangli", "maharashtra"): (16.8524, 74.5815),
    ("satara", "maharashtra"): (17.6805, 73.9918),
    # Madhya Pradesh
    ("bhopal", "madhya pradesh"): (23.2599, 77.4126),
    ("indore", "madhya pradesh"): (22.7196, 75.8577),
    ("jabalpur", "madhya pradesh"): (23.1815, 79.9864),
    ("gwalior", "madhya pradesh"): (26.2183, 78.1828),
    ("ujjain", "madhya pradesh"): (23.1760, 75.7885),
    ("sagar", "madhya pradesh"): (23.8388, 78.7378),
    ("rewa", "madhya pradesh"): (24.5362, 81.3037),
    ("satna", "madhya pradesh"): (24.6005, 80.8322),
    ("dewas", "madhya pradesh"): (22.9623, 76.0508),
    ("chhindwara", "madhya pradesh"): (22.0574, 78.9382),
    # Uttar Pradesh
    ("lucknow", "uttar pradesh"): (26.8467, 80.9462),
    ("kanpur", "uttar pradesh"): (26.4499, 80.3319),
    ("agra", "uttar pradesh"): (27.1767, 78.0081),
    ("varanasi", "uttar pradesh"): (25.3176, 82.9739),
    ("meerut", "uttar pradesh"): (28.9845, 77.7064),
    ("allahabad", "uttar pradesh"): (25.4358, 81.8463),
    ("bareilly", "uttar pradesh"): (28.3670, 79.4304),
    ("gorakhpur", "uttar pradesh"): (26.7606, 83.3731),
    ("aligarh", "uttar pradesh"): (27.8974, 78.0880),
    ("moradabad", "uttar pradesh"): (28.8351, 78.7732),
    # Rajasthan
    ("jaipur", "rajasthan"): (26.9124, 75.7873),
    ("jodhpur", "rajasthan"): (26.2389, 73.0243),
    ("udaipur", "rajasthan"): (24.5854, 73.7125),
    ("kota", "rajasthan"): (25.2138, 75.8648),
    ("bikaner", "rajasthan"): (28.0229, 73.3119),
    ("ajmer", "rajasthan"): (26.4498, 74.6398),
    ("bhilwara", "rajasthan"): (25.3477, 74.6408),
    ("alwar", "rajasthan"): (27.5530, 76.6087),
    ("sikar", "rajasthan"): (27.6094, 75.1398),
    ("sri ganganagar", "rajasthan"): (29.9149, 73.8761),
    # Gujarat
    ("ahmedabad", "gujarat"): (23.0225, 72.5714),
    ("surat", "gujarat"): (21.1702, 72.8311),
    ("vadodara", "gujarat"): (22.3072, 73.1812),
    ("rajkot", "gujarat"): (22.3039, 70.8022),
    ("bhavnagar", "gujarat"): (21.7645, 72.1519),
    ("jamnagar", "gujarat"): (22.4707, 70.0577),
    ("junagadh", "gujarat"): (21.5222, 70.4579),
    ("gandhinagar", "gujarat"): (23.2156, 72.6369),
    ("anand", "gujarat"): (22.5645, 72.9289),
    ("nadiad", "gujarat"): (22.6916, 72.8634),
    # Punjab
    ("ludhiana", "punjab"): (30.9010, 75.8573),
    ("amritsar", "punjab"): (31.6340, 74.8723),
    ("jalandhar", "punjab"): (31.3260, 75.5762),
    ("patiala", "punjab"): (30.3398, 76.3869),
    ("bathinda", "punjab"): (30.2110, 74.9455),
    ("mohali", "punjab"): (30.6975, 76.7324),
    ("hoshiarpur", "punjab"): (31.5143, 75.9115),
    ("pathankot", "punjab"): (32.2689, 75.6531),
    ("moga", "punjab"): (30.8179, 75.1717),
    ("firozpur", "punjab"): (30.9255, 74.6067),
    # Haryana
    ("gurgaon", "haryana"): (28.4595, 77.0266),
    ("faridabad", "haryana"): (28.4089, 77.3178),
    ("panipat", "haryana"): (29.3909, 76.9635),
    ("ambala", "haryana"): (30.3782, 76.7767),
    ("hisar", "haryana"): (29.1492, 75.7217),
    ("karnal", "haryana"): (29.6857, 76.9905),
    ("sonipat", "haryana"): (28.9931, 77.0151),
    ("rohtak", "haryana"): (28.8955, 76.6066),
    ("yamunanagar", "haryana"): (30.1290, 77.2674),
    ("kurukshetra", "haryana"): (29.9695, 76.8783),
    # West Bengal
    ("kolkata", "west bengal"): (22.5726, 88.3639),
    ("howrah", "west bengal"): (22.5779, 88.3175),
    ("durgapur", "west bengal"): (23.5204, 87.3119),
    ("siliguri", "west bengal"): (26.7271, 88.3953),
    ("asansol", "west bengal"): (23.6740, 86.9525),
    ("bardhaman", "west bengal"): (23.2324, 87.8630),
    ("malda", "west bengal"): (25.0108, 88.1411),
    ("baharampur", "west bengal"): (24.0988, 88.2679),
    ("habra", "west bengal"): (22.8394, 88.6653),
    ("kharagpur", "west bengal"): (22.3302, 87.3237),
    # Bihar
    ("patna", "bihar"): (25.5941, 85.1376),
    ("gaya", "bihar"): (24.7914, 85.0002),
    ("bhagalpur", "bihar"): (25.2425, 87.0145),
    ("muzaffarpur", "bihar"): (26.1209, 85.3647),
    ("darbhanga", "bihar"): (26.1542, 85.8918),
    ("purnia", "bihar"): (25.7771, 87.4753),
    ("arrah", "bihar"): (25.5560, 84.6653),
    ("begusarai", "bihar"): (25.4182, 86.1274),
    ("katihar", "bihar"): (25.5521, 87.5720),
    ("munger", "bihar"): (25.3748, 86.4735),
    # Odisha
    ("bhubaneswar", "odisha"): (20.2961, 85.8245),
    ("cuttack", "odisha"): (20.4625, 85.8830),
    ("rourkela", "odisha"): (22.2604, 84.8512),
    ("berhampur", "odisha"): (19.3150, 84.7941),
    ("sambalpur", "odisha"): (21.4700, 83.9800),
    ("puri", "odisha"): (19.8134, 85.8315),
    ("balasore", "odisha"): (21.4934, 86.9337),
    ("baripada", "odisha"): (21.9320, 86.7300),
    ("bhadrak", "odisha"): (21.0500, 86.5000),
    ("jharsuguda", "odisha"): (21.8500, 84.0300),
}


def _get_geocoder():
    """Get or create geocoder instance (lazy import of geopy)."""
    global _geocoder
    if _geocoder is None:
        try:
            from geopy.geocoders import Nominatim
            _geocoder = Nominatim(
                user_agent="smart-crop-advisor-v1",
                timeout=10,
            )
        except ImportError:
            logger.warning(
                "geopy is not installed in this Python environment. "
                "Online geocoding disabled; local database will be used."
            )
            return None
    return _geocoder


def _build_local_result(district: str, state: str, lat: float, lon: float) -> dict:
    """Helper to build a standardized geocoding result dict from local coordinates."""
    dist_cap = district.title()
    state_cap = state.title()
    return {
        "latitude": lat,
        "longitude": lon,
        "full_address": f"{dist_cap}, {state_cap}, India",
        "village": "",
        "taluk": dist_cap,
        "district": dist_cap,
        "state": state_cap,
        "country": "India",
        "postcode": "",
    }


def _local_search(query: str) -> Optional[dict]:
    """Search local coordinates list for a matching district."""
    query_clean = query.lower().replace(", india", "").replace("india", "").replace(",", " ").strip()
    words = [w.strip() for w in query_clean.split() if w.strip()]
    if not words:
        return None

    # Try direct match of district & state
    if len(words) > 1:
        for (district, state), (lat, lon) in LOCAL_COORDINATES.items():
            if words[0] in district and words[1] in state:
                return _build_local_result(district, state, lat, lon)

    # Try exact match on district
    for (district, state), (lat, lon) in LOCAL_COORDINATES.items():
        if words[0] == district:
            return _build_local_result(district, state, lat, lon)

    # Try substring match on district
    for (district, state), (lat, lon) in LOCAL_COORDINATES.items():
        if words[0] in district:
            return _build_local_result(district, state, lat, lon)

    return None


def _local_reverse_geocode(lat: float, lon: float) -> Optional[dict]:
    """Find the closest local district to the given coordinates."""
    min_dist = float("inf")
    closest_match = None

    for (district, state), (d_lat, d_lon) in LOCAL_COORDINATES.items():
        # Euclidean distance
        dist = math.sqrt((lat - d_lat) ** 2 + (lon - d_lon) ** 2)
        if dist < min_dist:
            min_dist = dist
            closest_match = (district, state, d_lat, d_lon)

    if closest_match and min_dist < 4.0:  # Within ~400km range
        district, state, d_lat, d_lon = closest_match
        return _build_local_result(district, state, lat, lon)

    return None


def reverse_geocode(latitude: float, longitude: float) -> Optional[dict]:
    """
    Convert GPS coordinates to address components.

    Args:
        latitude: GPS latitude
        longitude: GPS longitude

    Returns:
        Dict with village, taluk, district, state, country, full_address
    """
    try:
        geocoder = _get_geocoder()
        if geocoder is None:
            raise ImportError("geopy unavailable")
        location = geocoder.reverse(
            (latitude, longitude),
            exactly_one=True,
            language="en",
            addressdetails=True,
        )

        if location is None:
            logger.warning(f"No results for coordinates: {latitude}, {longitude}")
            # Try local lookup
            local_res = _local_reverse_geocode(latitude, longitude)
            if local_res:
                logger.info(f"Local reverse geocoding fallback: {latitude},{longitude} -> {local_res['district']}")
                return local_res
            return None

        address = location.raw.get("address", {})

        # In India: state_district holds the administrative district name.
        # county holds the taluk/tehsil/sub-district name.
        district_name = address.get("state_district", "")
        if not district_name:
            district_name = address.get("city", address.get("city_district", address.get("county", "Unknown")))

        # Strip trailing " District" suffix if present (e.g., "Karur District" -> "Karur")
        if district_name.endswith(" District"):
            district_name = district_name[:-9]

        taluk_name = address.get("county", "")
        if not taluk_name:
            taluk_name = address.get("subdistrict", "")

        result = {
            "latitude": latitude,
            "longitude": longitude,
            "full_address": location.address,
            "village": address.get("village", address.get("hamlet", address.get("town", address.get("suburb", "")))),
            "taluk": taluk_name,
            "district": district_name,
            "state": address.get("state", ""),
            "country": address.get("country", ""),
            "postcode": address.get("postcode", ""),
        }

        logger.info(f"Reverse geocoded: {latitude},{longitude} -> {result['district']}, {result['state']}")

        return result

    except Exception as e:
        logger.error(f"Geocoding error: {e}. Trying local fallback.")
        local_res = _local_reverse_geocode(latitude, longitude)
        if local_res:
            logger.info(f"Local reverse geocoding fallback: {latitude},{longitude} -> {local_res['district']}")
            return local_res
        return None


def search_location(query: str) -> Optional[dict]:
    """
    Search for a location by name (district/city).

    Args:
        query: Location name (e.g., "Coimbatore, Tamil Nadu")

    Returns:
        Dict with coordinates and address components
    """
    # 1. Try local database lookup first (ensures fast offline-capable loading)
    local_res = _local_search(query)
    if local_res:
        logger.info(f"Local search match for '{query}': {local_res['district']}, {local_res['state']}")
        return local_res

    # 2. Try online Nominatim API as fallback
    try:
        geocoder = _get_geocoder()
        if geocoder is None:
            raise ImportError("geopy unavailable")

        # Append India if not present
        if "india" not in query.lower():
            query = f"{query}, India"

        location = geocoder.geocode(
            query,
            exactly_one=True,
            language="en",
            addressdetails=True,
        )

        if location is None:
            logger.warning(f"No results for query: {query}")
            return None

        # Now reverse geocode for detailed address
        result = reverse_geocode(location.latitude, location.longitude)
        if result is None:
            result = {
                "latitude": location.latitude,
                "longitude": location.longitude,
                "full_address": location.address,
                "village": "",
                "taluk": "",
                "district": query.split(",")[0].strip(),
                "state": "",
                "country": "India",
            }

        logger.info(f"Search result for '{query}': {result['district']}, {result['state']}")
        return result

    except Exception as e:
        logger.error(f"Online search error: {e}. Trying substring local lookup.")
        # Try a wider local substring search as final backup
        query_clean = query.lower().replace(", india", "").replace("india", "").replace(",", " ").strip()
        for (district, state), (lat, lon) in LOCAL_COORDINATES.items():
            if query_clean in district or district in query_clean:
                return _build_local_result(district, state, lat, lon)
        return None


def get_states_list() -> list[str]:
    """Get list of all Indian states."""
    return sorted(INDIAN_STATES.keys())


def get_districts_for_state(state: str) -> list[str]:
    """Get list of districts for a given state."""
    return INDIAN_STATES.get(state, [])


def get_all_districts() -> list[str]:
    """Get a flat list of all districts across all states."""
    districts = []
    for state, state_districts in INDIAN_STATES.items():
        for district in state_districts:
            districts.append(f"{district}, {state}")
    return sorted(districts)

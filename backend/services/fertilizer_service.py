"""
Fertilizer Recommendation Service
===================================
Recommend organic, chemical, and bio fertilizers based on crop + soil analysis.
"""

from utils.constants import CROP_DATABASE, FERTILIZER_DATABASE
from utils.logger import get_logger
from utils.helpers import format_currency

logger = get_logger("fertilizer")


def recommend_fertilizers(
    crop_name: str,
    nitrogen: float,
    phosphorus: float,
    potassium: float,
    ph: float,
    soil_type: str = "Loamy Soil",
    area_hectares: float = 1.0,
) -> dict:
    """
    Generate comprehensive fertilizer recommendations.

    Returns organic, chemical, and bio-fertilizer recommendations
    with quantities, timing, and cost estimates.
    """
    crop_key = crop_name.lower().replace(" ", "")
    crop_info = CROP_DATABASE.get(crop_key, {})

    # Ideal NPK for this crop
    ideal_n = crop_info.get("fertilizer_n", 100)
    ideal_p = crop_info.get("fertilizer_p", 50)
    ideal_k = crop_info.get("fertilizer_k", 50)

    # Calculate deficiencies
    n_deficit = max(0, ideal_n - nitrogen)
    p_deficit = max(0, ideal_p - phosphorus)
    k_deficit = max(0, ideal_k - potassium)

    n_status = "Deficient" if n_deficit > 20 else ("Adequate" if n_deficit < 5 else "Low")
    p_status = "Deficient" if p_deficit > 15 else ("Adequate" if p_deficit < 5 else "Low")
    k_status = "Deficient" if k_deficit > 15 else ("Adequate" if k_deficit < 5 else "Low")

    # Generate recommendations
    organic_recs = _recommend_organic(n_deficit, p_deficit, k_deficit, crop_key, area_hectares)
    chemical_recs = _recommend_chemical(n_deficit, p_deficit, k_deficit, crop_key, area_hectares)
    bio_recs = _recommend_bio(crop_key, ph, soil_type, area_hectares)

    total_cost = (
        sum(r.get("total_cost", 0) for r in organic_recs) +
        sum(r.get("total_cost", 0) for r in chemical_recs) +
        sum(r.get("total_cost", 0) for r in bio_recs)
    )

    result = {
        "crop_name": crop_name,
        "area_hectares": area_hectares,

        # Nutrient analysis
        "nutrient_analysis": {
            "nitrogen": {"current": nitrogen, "ideal": ideal_n, "deficit": n_deficit, "status": n_status},
            "phosphorus": {"current": phosphorus, "ideal": ideal_p, "deficit": p_deficit, "status": p_status},
            "potassium": {"current": potassium, "ideal": ideal_k, "deficit": k_deficit, "status": k_status},
        },

        # Recommendations
        "organic": organic_recs,
        "chemical": chemical_recs,
        "bio": bio_recs,

        # Summary
        "total_estimated_cost": total_cost,
        "total_cost_formatted": format_currency(total_cost),
        "expected_improvement": _calculate_improvement(n_deficit, p_deficit, k_deficit),

        # Application schedule
        "schedule": _generate_schedule(crop_key, crop_info.get("duration_days", 120)),
    }

    logger.info(f"Fertilizer rec for {crop_name}: N-def={n_deficit}, P-def={p_deficit}, K-def={k_deficit}")
    return result


def _recommend_organic(n_deficit, p_deficit, k_deficit, crop_key, area_ha) -> list[dict]:
    """Recommend organic fertilizers."""
    recs = []
    organic_db = FERTILIZER_DATABASE.get("organic", [])

    for fert in organic_db:
        qty_per_ha = 0
        relevance = ""

        if fert["name"] == "Farm Yard Manure (FYM)":
            qty_per_ha = 5000 + (n_deficit * 20)  # Base + deficit adjustment
            relevance = "Essential for soil health and organic matter"
        elif fert["name"] == "Vermicompost":
            qty_per_ha = 2000 + (n_deficit * 10)
            relevance = "Rich in nutrients, improves soil structure"
        elif fert["name"] == "Neem Cake":
            qty_per_ha = 200 + (n_deficit * 2)
            relevance = "Natural pest repellent + nitrogen source"
        elif fert["name"] == "Green Manure (Dhaincha/Sesbania)":
            if n_deficit > 30:
                qty_per_ha = 0  # Grown, not applied by weight
                relevance = "Grow and plow in for nitrogen fixing"
            else:
                continue

        total_qty = qty_per_ha * area_ha
        total_cost = total_qty * fert.get("cost_per_kg", 5)

        recs.append({
            "name": fert["name"],
            "type": "Organic",
            "quantity_per_ha_kg": round(qty_per_ha),
            "total_quantity_kg": round(total_qty),
            "application_method": fert.get("application_method", ""),
            "application_timing": "Before sowing (15-20 days)",
            "cost_per_kg": fert.get("cost_per_kg", 5),
            "total_cost": round(total_cost),
            "benefit": fert.get("benefit", ""),
            "relevance": relevance,
            "expected_improvement": "10-15% yield improvement",
        })

    return recs


def _recommend_chemical(n_deficit, p_deficit, k_deficit, crop_key, area_ha) -> list[dict]:
    """Recommend chemical fertilizers based on nutrient deficits."""
    recs = []
    chemical_db = FERTILIZER_DATABASE.get("chemical", [])

    for fert in chemical_db:
        qty_per_ha = 0
        timing = ""
        relevance = ""

        if fert["name"] == "Urea (46-0-0)" and n_deficit > 5:
            # Urea is 46% N → need qty = deficit / 0.46
            qty_per_ha = round(n_deficit / 0.46, 1)
            timing = "Split: 50% at sowing, 25% at 30 days, 25% at 60 days"
            relevance = f"To fill nitrogen deficit of {n_deficit:.0f} kg/ha"

        elif fert["name"] == "DAP (18-46-0)" and p_deficit > 5:
            qty_per_ha = round(p_deficit / 0.46, 1)
            timing = "Full dose at sowing (basal)"
            relevance = f"To fill phosphorus deficit of {p_deficit:.0f} kg/ha"

        elif fert["name"] == "MOP (0-0-60)" and k_deficit > 5:
            qty_per_ha = round(k_deficit / 0.60, 1)
            timing = "50% at sowing, 50% at 30-45 days"
            relevance = f"To fill potassium deficit of {k_deficit:.0f} kg/ha"

        elif fert["name"] == "NPK Complex (10-26-26)" and (p_deficit > 10 and k_deficit > 10):
            qty_per_ha = round(max(p_deficit / 0.26, k_deficit / 0.26), 1)
            timing = "Full dose at sowing (basal)"
            relevance = "Balanced NPK for overall growth"

        elif fert["name"] == "SSP (0-16-0)" and p_deficit > 5:
            qty_per_ha = round(p_deficit / 0.16, 1)
            timing = "Full dose at sowing"
            relevance = "Phosphorus with added calcium and sulphur"

        else:
            continue

        if qty_per_ha <= 0:
            continue

        total_qty = qty_per_ha * area_ha
        total_cost = total_qty * fert.get("cost_per_kg", 10)

        recs.append({
            "name": fert["name"],
            "type": "Chemical",
            "quantity_per_ha_kg": round(qty_per_ha, 1),
            "total_quantity_kg": round(total_qty, 1),
            "application_method": fert.get("application_method", ""),
            "application_timing": timing,
            "cost_per_kg": fert.get("cost_per_kg", 10),
            "total_cost": round(total_cost),
            "benefit": fert.get("benefit", ""),
            "relevance": relevance,
            "expected_improvement": "15-25% yield improvement",
        })

    return recs


def _recommend_bio(crop_key, ph, soil_type, area_ha) -> list[dict]:
    """Recommend bio-fertilizers."""
    recs = []
    bio_db = FERTILIZER_DATABASE.get("bio", [])

    # Legume crops benefit from Rhizobium
    legumes = ["chickpea", "lentil", "mungbean", "blackgram", "pigeonpeas", "kidneybeans", "mothbeans"]

    for fert in bio_db:
        include = False
        qty_per_ha = 2  # Standard bio-fert dose: 2 kg/ha
        relevance = ""

        if fert["name"] == "Rhizobium" and crop_key in legumes:
            include = True
            relevance = "Essential for nitrogen fixation in legumes"
        elif fert["name"] == "Azospirillum" and crop_key not in legumes:
            include = True
            relevance = "Nitrogen fixation for non-legume crops"
        elif fert["name"] == "PSB (Phosphorus Solubilizing Bacteria)":
            include = True
            relevance = "Makes soil phosphorus available to plants"
        elif fert["name"] == "Trichoderma":
            if ph < 6.5 or soil_type in ["Clay Soil", "Black Soil"]:
                include = True
                relevance = "Prevents soil-borne diseases in acidic/heavy soils"

        if include:
            total_qty = qty_per_ha * area_ha
            total_cost = total_qty * fert.get("cost_per_kg", 50)

            recs.append({
                "name": fert["name"],
                "type": "Bio-Fertilizer",
                "quantity_per_ha_kg": qty_per_ha,
                "total_quantity_kg": round(total_qty, 1),
                "application_method": fert.get("application_method", ""),
                "application_timing": "At sowing / transplanting",
                "cost_per_kg": fert.get("cost_per_kg", 50),
                "total_cost": round(total_cost),
                "benefit": fert.get("benefit", ""),
                "relevance": relevance,
                "expected_improvement": "5-10% yield improvement",
            })

    return recs


def _calculate_improvement(n_def, p_def, k_def) -> str:
    """Estimate yield improvement from fertilizer application."""
    if n_def > 50 or p_def > 40 or k_def > 40:
        return "25-40% yield improvement expected"
    elif n_def > 20 or p_def > 15 or k_def > 15:
        return "15-25% yield improvement expected"
    else:
        return "5-15% yield improvement expected"


def _generate_schedule(crop_key: str, duration_days: int) -> list[dict]:
    """Generate fertilizer application schedule."""
    schedule = [
        {"day": 0, "stage": "Land Preparation", "action": "Apply FYM/Vermicompost + Basal dose of DAP/NPK complex"},
        {"day": 1, "stage": "Sowing/Transplanting", "action": "Seed treatment with Rhizobium/Trichoderma + PSB soil application"},
        {"day": 21, "stage": "Early Growth", "action": "First top dressing of Urea (25% dose)"},
        {"day": 45, "stage": "Vegetative Growth", "action": "Second top dressing of Urea (25% dose) + MOP (50%)"},
        {"day": int(duration_days * 0.5), "stage": "Flowering", "action": "Foliar spray of micronutrients if deficiency symptoms appear"},
        {"day": int(duration_days * 0.7), "stage": "Grain/Fruit Formation", "action": "Final potassium application if needed"},
    ]
    return schedule

"""
Disease Detection Service
===========================
Image-based plant disease detection using MobileNetV2 deep learning model.
"""

import os
import json
import numpy as np
from typing import Optional
from pathlib import Path
from PIL import Image
from utils.constants import DISEASE_DATABASE
from utils.logger import get_logger

logger = get_logger("disease")

_model = None
_class_labels = None

MODEL_DIR = Path(__file__).resolve().parent.parent.parent / "models" / "disease_detection"


def _load_model():
    """Load trained disease detection model."""
    global _model, _class_labels

    if _model is not None:
        return True

    try:
        model_path = MODEL_DIR / "model.h5"
        labels_path = MODEL_DIR / "class_labels.json"

        if not model_path.exists():
            logger.warning("Disease model not found. Using knowledge-base fallback.")
            _class_labels = list(DISEASE_DATABASE.keys())
            return False

        import tensorflow as tf
        _model = tf.keras.models.load_model(str(model_path))

        if labels_path.exists():
            with open(labels_path, "r", encoding="utf-8") as f:
                _class_labels = json.load(f)
        else:
            _class_labels = list(DISEASE_DATABASE.keys())

        logger.info("Disease detection model loaded successfully.")
        return True

    except Exception as e:
        logger.error(f"Error loading disease model: {e}")
        _class_labels = list(DISEASE_DATABASE.keys())
        return False


def detect_disease(image: Image.Image) -> dict:
    """
    Detect disease from a crop leaf image.

    Args:
        image: PIL Image object

    Returns:
        Dict with disease name, confidence, severity, treatments
    """
    model_loaded = _load_model()

    if model_loaded and _model is not None:
        return _ml_detect(image)
    else:
        return _demo_detect(image)


def _ml_detect(image: Image.Image) -> dict:
    """ML model-based disease detection."""
    try:
        import tensorflow as tf

        # Preprocess image
        img = image.resize((224, 224))
        img_array = np.array(img) / 255.0

        if len(img_array.shape) == 2:  # Grayscale
            img_array = np.stack([img_array] * 3, axis=-1)
        elif img_array.shape[2] == 4:  # RGBA
            img_array = img_array[:, :, :3]

        img_array = np.expand_dims(img_array, axis=0)

        # Predict
        predictions = _model.predict(img_array, verbose=0)[0]
        top_idx = np.argmax(predictions)
        confidence = float(predictions[top_idx])

        class_name = _class_labels[top_idx] if top_idx < len(_class_labels) else "Unknown"

        return _build_result(class_name, confidence)

    except Exception as e:
        logger.error(f"ML detection error: {e}")
        return _demo_detect(image)


def _demo_detect(image: Image.Image) -> dict:
    """Demo mode detection when model isn't available."""
    logger.info("Using demo mode for disease detection")

    # Analyze image color properties for basic heuristic
    img_array = np.array(image.resize((100, 100)))

    if len(img_array.shape) == 3:
        avg_green = np.mean(img_array[:, :, 1])
        avg_red = np.mean(img_array[:, :, 0])

        # Very green = likely healthy
        if avg_green > avg_red * 1.3 and avg_green > 100:
            return _build_result("Healthy", 0.75)
        elif avg_red > avg_green * 1.2:
            # Reddish/brownish could indicate disease
            return _build_result("Tomato___Early_blight", 0.65)
        else:
            return _build_result("Tomato___Late_blight", 0.55)
    else:
        return _build_result("Healthy", 0.50)


def _build_result(class_name: str, confidence: float) -> dict:
    """Build comprehensive disease detection result."""
    disease_info = DISEASE_DATABASE.get(class_name, DISEASE_DATABASE.get("Healthy"))

    if disease_info is None:
        disease_info = DISEASE_DATABASE["Healthy"]

    # Determine severity based on confidence
    if confidence > 0.85:
        severity = "High"
    elif confidence > 0.6:
        severity = "Medium"
    else:
        severity = "Low"

    severity_desc = disease_info.get("severity_levels", {}).get(severity, "")

    # Recommended sprays based on disease
    sprays = []
    if "Mancozeb" in disease_info.get("chemical_treatment", ""):
        sprays.append("Mancozeb 75% WP (2.5g/L)")
    if "Copper" in disease_info.get("chemical_treatment", "") or "Copper" in disease_info.get("organic_treatment", ""):
        sprays.append("Copper Oxychloride 50% WP (3g/L)")
    if "Carbendazim" in disease_info.get("chemical_treatment", ""):
        sprays.append("Carbendazim 50% WP (1g/L)")
    if "Tricyclazole" in disease_info.get("chemical_treatment", ""):
        sprays.append("Tricyclazole 75% WP (0.6g/L)")
    if not sprays and class_name != "Healthy":
        sprays.append("Contact your local agricultural officer for specific spray recommendations")

    return {
        "disease_name": disease_info.get("disease", class_name),
        "class_name": class_name,
        "crop": disease_info.get("crop", "Unknown"),
        "confidence": round(confidence * 100, 1),
        "severity": severity,
        "severity_description": severity_desc,
        "cause": disease_info.get("cause", "Unknown"),
        "organic_treatment": disease_info.get("organic_treatment", ""),
        "chemical_treatment": disease_info.get("chemical_treatment", ""),
        "prevention": disease_info.get("prevention", ""),
        "recovery_time": disease_info.get("recovery_time", "Unknown"),
        "recommended_sprays": sprays,
        "is_healthy": class_name == "Healthy",
    }

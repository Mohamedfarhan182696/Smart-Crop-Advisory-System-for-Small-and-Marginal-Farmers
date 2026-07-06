"""
Crop Recommendation Model Training
=====================================
Trains and compares multiple ML models on crop recommendation dataset.
Uses: Random Forest, XGBoost, KNN, SVM, Gradient Boosting.
Saves the best-performing model.
"""

import os
import sys
import json
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import joblib

# Project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

DATASET_PATH = PROJECT_ROOT / "datasets" / "crop" / "crop_data.csv"
MODEL_DIR = PROJECT_ROOT / "models" / "crop_recommendation"
REPORTS_DIR = PROJECT_ROOT / "training" / "reports"


def load_dataset():
    """Load and validate the crop recommendation dataset."""
    if not DATASET_PATH.exists():
        print(f"❌ Dataset not found at {DATASET_PATH}")
        print("   Generating synthetic dataset...")
        generate_synthetic_dataset()

    df = pd.read_csv(DATASET_PATH)
    print(f"✅ Dataset loaded: {df.shape[0]} rows, {df.shape[1]} columns")
    print(f"   Crops: {df['label'].nunique()} unique crops")
    print(f"   Features: {list(df.columns)}")
    return df


def generate_synthetic_dataset():
    """Generate a realistic synthetic crop recommendation dataset."""
    np.random.seed(42)

    crop_params = {
        "rice":        {"N": (60, 100), "P": (35, 65), "K": (35, 55), "temp": (20, 35), "hum": (75, 95), "ph": (5.0, 7.5), "rain": (150, 300)},
        "wheat":       {"N": (70, 120), "P": (55, 85), "K": (55, 80), "temp": (10, 25), "hum": (40, 70), "ph": (6.0, 7.5), "rain": (50, 120)},
        "maize":       {"N": (60, 100), "P": (35, 65), "K": (25, 55), "temp": (18, 32), "hum": (55, 80), "ph": (5.5, 7.0), "rain": (60, 120)},
        "chickpea":    {"N": (30, 60),  "P": (55, 85), "K": (70, 90), "temp": (15, 28), "hum": (15, 40), "ph": (6.0, 8.0), "rain": (50, 100)},
        "kidneybeans": {"N": (10, 40),  "P": (55, 85), "K": (15, 35), "temp": (15, 25), "hum": (20, 45), "ph": (5.5, 7.0), "rain": (60, 120)},
        "pigeonpeas":  {"N": (15, 35),  "P": (55, 80), "K": (15, 35), "temp": (18, 35), "hum": (30, 65), "ph": (5.0, 7.5), "rain": (80, 180)},
        "mothbeans":   {"N": (15, 35),  "P": (40, 65), "K": (15, 35), "temp": (25, 35), "hum": (30, 60), "ph": (6.5, 8.0), "rain": (30, 70)},
        "mungbean":    {"N": (10, 30),  "P": (40, 70), "K": (15, 35), "temp": (25, 35), "hum": (75, 95), "ph": (6.0, 7.5), "rain": (30, 60)},
        "blackgram":   {"N": (30, 50),  "P": (55, 75), "K": (15, 30), "temp": (25, 35), "hum": (55, 75), "ph": (6.0, 7.5), "rain": (50, 100)},
        "lentil":      {"N": (10, 30),  "P": (55, 85), "K": (15, 35), "temp": (10, 28), "hum": (20, 50), "ph": (5.5, 8.0), "rain": (30, 60)},
        "pomegranate": {"N": (10, 30),  "P": (10, 30), "K": (35, 55), "temp": (18, 35), "hum": (80, 95), "ph": (5.5, 7.5), "rain": (30, 50)},
        "banana":      {"N": (80, 120), "P": (70, 100),"K": (45, 60), "temp": (25, 35), "hum": (75, 95), "ph": (5.5, 7.0), "rain": (80, 120)},
        "mango":       {"N": (15, 35),  "P": (15, 35), "K": (25, 45), "temp": (25, 38), "hum": (45, 70), "ph": (5.5, 7.0), "rain": (40, 100)},
        "grapes":      {"N": (15, 35),  "P": (120,150),"K": (190,210),"temp": (15, 30), "hum": (75, 90), "ph": (5.5, 7.0), "rain": (60, 80)},
        "watermelon":  {"N": (80, 110), "P": (15, 35), "K": (45, 60), "temp": (22, 35), "hum": (80, 95), "ph": (6.0, 7.0), "rain": (40, 60)},
        "muskmelon":   {"N": (80, 110), "P": (15, 35), "K": (45, 60), "temp": (25, 38), "hum": (85, 95), "ph": (6.0, 7.5), "rain": (20, 40)},
        "apple":       {"N": (15, 35),  "P": (120,140),"K": (190,210),"temp": (10, 25), "hum": (85, 95), "ph": (5.5, 6.5), "rain": (100, 140)},
        "orange":      {"N": (15, 30),  "P": (10, 30), "K": (5, 15),  "temp": (20, 32), "hum": (85, 95), "ph": (6.0, 8.0), "rain": (90, 120)},
        "papaya":      {"N": (35, 65),  "P": (45, 70), "K": (45, 60), "temp": (25, 38), "hum": (85, 95), "ph": (6.0, 7.0), "rain": (100, 180)},
        "coconut":     {"N": (15, 35),  "P": (5, 20),  "K": (25, 40), "temp": (25, 35), "hum": (85, 99), "ph": (5.5, 7.0), "rain": (120, 180)},
        "cotton":      {"N": (100,140), "P": (40, 65), "K": (15, 30), "temp": (22, 35), "hum": (60, 85), "ph": (6.0, 8.0), "rain": (60, 110)},
        "coffee":      {"N": (80, 120), "P": (15, 35), "K": (25, 45), "temp": (18, 28), "hum": (50, 75), "ph": (5.0, 6.5), "rain": (120, 200)},
        "jute":        {"N": (60, 100), "P": (35, 55), "K": (35, 55), "temp": (22, 35), "hum": (70, 95), "ph": (6.0, 7.5), "rain": (150, 250)},
    }

    records = []
    samples_per_crop = 100

    for crop, params in crop_params.items():
        for _ in range(samples_per_crop):
            record = {
                "N": np.random.uniform(*params["N"]),
                "P": np.random.uniform(*params["P"]),
                "K": np.random.uniform(*params["K"]),
                "temperature": np.random.uniform(*params["temp"]),
                "humidity": np.random.uniform(*params["hum"]),
                "ph": np.random.uniform(*params["ph"]),
                "rainfall": np.random.uniform(*params["rain"]),
                "label": crop,
            }
            records.append(record)

    df = pd.DataFrame(records)
    df = df.sample(frac=1, random_state=42).reset_index(drop=True)

    os.makedirs(DATASET_PATH.parent, exist_ok=True)
    df.to_csv(DATASET_PATH, index=False)
    print(f"✅ Synthetic dataset generated: {df.shape[0]} samples, {df['label'].nunique()} crops")
    return df


def train_and_compare():
    """Train multiple models and select the best one."""
    df = load_dataset()

    # Features and target
    feature_cols = ["N", "P", "K", "temperature", "humidity", "ph", "rainfall"]
    X = df[feature_cols].values
    y = df["label"].values

    # Encode labels
    le = LabelEncoder()
    y_encoded = le.fit_transform(y)

    # Scale features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Train/test split
    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded,
    )

    print(f"\n📊 Training set: {X_train.shape[0]} samples")
    print(f"📊 Test set: {X_test.shape[0]} samples")
    print(f"📊 Classes: {len(le.classes_)}")

    # Models to compare
    models = {
        "Random Forest": RandomForestClassifier(
            n_estimators=200, max_depth=20, random_state=42, n_jobs=-1,
        ),
        "Gradient Boosting": GradientBoostingClassifier(
            n_estimators=150, max_depth=8, learning_rate=0.1, random_state=42,
        ),
        "KNN": KNeighborsClassifier(n_neighbors=5, n_jobs=-1),
        "SVM": SVC(kernel="rbf", probability=True, random_state=42),
    }

    # Try XGBoost if available
    try:
        from xgboost import XGBClassifier
        models["XGBoost"] = XGBClassifier(
            n_estimators=200, max_depth=10, learning_rate=0.1,
            random_state=42, n_jobs=-1, use_label_encoder=False,
            eval_metric="mlogloss",
        )
    except ImportError:
        print("⚠️ XGBoost not installed, skipping...")

    results = {}
    best_accuracy = 0
    best_model_name = None
    best_model = None

    print("\n" + "=" * 60)
    print("MODEL COMPARISON")
    print("=" * 60)

    for name, model in models.items():
        print(f"\n🔄 Training {name}...")

        # Train
        model.fit(X_train, y_train)

        # Evaluate
        y_pred = model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)

        # Cross-validation
        cv_scores = cross_val_score(model, X_scaled, y_encoded, cv=5, n_jobs=-1)

        results[name] = {
            "accuracy": round(accuracy * 100, 2),
            "cv_mean": round(cv_scores.mean() * 100, 2),
            "cv_std": round(cv_scores.std() * 100, 2),
        }

        print(f"   ✅ Test Accuracy: {accuracy * 100:.2f}%")
        print(f"   📊 CV Score: {cv_scores.mean() * 100:.2f}% ± {cv_scores.std() * 100:.2f}%")

        if accuracy > best_accuracy:
            best_accuracy = accuracy
            best_model_name = name
            best_model = model

    print(f"\n🏆 Best Model: {best_model_name} ({best_accuracy * 100:.2f}%)")

    # Save best model
    os.makedirs(MODEL_DIR, exist_ok=True)
    joblib.dump(best_model, str(MODEL_DIR / "model.pkl"))
    joblib.dump(scaler, str(MODEL_DIR / "scaler.pkl"))
    joblib.dump(le, str(MODEL_DIR / "label_encoder.pkl"))

    print(f"\n💾 Model saved to {MODEL_DIR}")

    # Save comparison report
    os.makedirs(REPORTS_DIR, exist_ok=True)
    report_path = REPORTS_DIR / "crop_model_comparison.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump({
            "best_model": best_model_name,
            "best_accuracy": best_accuracy,
            "results": results,
            "classes": list(le.classes_),
            "features": feature_cols,
        }, f, indent=2, ensure_ascii=False)

    print(f"📄 Report saved to {report_path}")

    # Print classification report for best model
    y_pred_best = best_model.predict(X_test)
    print(f"\n📋 Classification Report ({best_model_name}):")
    print(classification_report(y_test, y_pred_best, target_names=le.classes_))

    return best_model, scaler, le, results


if __name__ == "__main__":
    train_and_compare()

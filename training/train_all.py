"""
Master Training Script
=======================
Train all ML models for the Smart Crop Advisory System.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def train_all():
    """Train all models sequentially."""
    print("=" * 60)
    print("  SMART CROP ADVISORY SYSTEM — MODEL TRAINING")
    print("=" * 60)

    # 1. Crop Recommendation Model
    print("\n\n🌾 [1/2] Training Crop Recommendation Model...")
    print("-" * 50)
    try:
        from models.crop_recommendation.train import train_and_compare
        train_and_compare()
        print("✅ Crop model training complete!\n")
    except Exception as e:
        print(f"❌ Crop model training failed: {e}\n")

    # 2. Disease Detection Model (requires large dataset)
    print("\n🔬 [2/2] Disease Detection Model...")
    print("-" * 50)
    print("⚠️ Disease detection model requires PlantVillage dataset (54K images).")
    print("   Run separately: python models/disease_detection/train.py")
    print("   Or use Google Colab for GPU-accelerated training.")
    print("   The system works without it using a knowledge-base fallback.")

    print("\n" + "=" * 60)
    print("  TRAINING COMPLETE")
    print("=" * 60)
    print("\nNext steps:")
    print("  1. Run the app: streamlit run app.py")
    print("  2. API server: python -m backend.main")
    print("  3. Open: http://localhost:8501")


if __name__ == "__main__":
    train_all()

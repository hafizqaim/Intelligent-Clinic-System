"""
Training script for telemetry anomaly detection model.
Generates realistic synthetic patient vital signs data and trains an Isolation Forest model.

Run:  python ml_models/train_model.py
"""
import os
import pickle

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.metrics import classification_report

np.random.seed(42)

MODEL_PATH = os.path.join(os.path.dirname(__file__), "telemetry_anomaly_model.pkl")
CSV_PATH = os.path.join(os.path.dirname(__file__), "synthetic_vitals.csv")

COLUMNS = [
    "heart_rate",
    "blood_pressure_systolic",
    "blood_pressure_diastolic",
    "oxygen_saturation",
    "temperature",
]


# ── Synthetic data generation ────────────────────────────────────────────────

def _normal_vitals(n: int) -> np.ndarray:
    """Healthy adult resting vitals."""
    return np.column_stack([
        np.random.normal(75, 8, n).clip(55, 100),
        np.random.normal(118, 10, n).clip(90, 135),
        np.random.normal(76, 7, n).clip(60, 88),
        np.random.normal(97.5, 1.2, n).clip(94, 100),
        np.random.normal(36.8, 0.3, n).clip(36.1, 37.5),
    ])


def _elderly_vitals(n: int) -> np.ndarray:
    """Older adults — slightly higher BP, lower O2."""
    return np.column_stack([
        np.random.normal(70, 10, n).clip(50, 95),
        np.random.normal(132, 12, n).clip(100, 155),
        np.random.normal(82, 8, n).clip(62, 95),
        np.random.normal(95.5, 1.8, n).clip(91, 100),
        np.random.normal(36.6, 0.35, n).clip(35.8, 37.4),
    ])


def _pediatric_vitals(n: int) -> np.ndarray:
    """Children — higher heart rate, lower BP."""
    return np.column_stack([
        np.random.normal(100, 12, n).clip(75, 130),
        np.random.normal(100, 8, n).clip(80, 120),
        np.random.normal(65, 6, n).clip(50, 80),
        np.random.normal(98, 1.0, n).clip(95, 100),
        np.random.normal(36.9, 0.3, n).clip(36.2, 37.6),
    ])


def _athlete_vitals(n: int) -> np.ndarray:
    """Athletes — lower resting HR."""
    return np.column_stack([
        np.random.normal(55, 6, n).clip(40, 70),
        np.random.normal(115, 8, n).clip(95, 130),
        np.random.normal(72, 6, n).clip(58, 85),
        np.random.normal(98.5, 0.8, n).clip(96, 100),
        np.random.normal(36.7, 0.25, n).clip(36.2, 37.3),
    ])


def _anomalous_vitals(n: int) -> np.ndarray:
    """Clearly dangerous vitals — used ONLY for evaluation, not training."""
    return np.column_stack([
        np.where(
            np.random.rand(n) > 0.5,
            np.random.uniform(150, 220, n),
            np.random.uniform(25, 45, n),
        ),
        np.random.uniform(160, 250, n),
        np.random.uniform(100, 160, n),
        np.random.uniform(60, 88, n),
        np.where(
            np.random.rand(n) > 0.5,
            np.random.uniform(33.0, 35.0, n),
            np.random.uniform(39.5, 42.0, n),
        ),
    ])


def generate_training_data() -> pd.DataFrame:
    """Create a multi-profile normal dataset for Isolation Forest training."""
    parts = [
        _normal_vitals(3000),
        _elderly_vitals(1000),
        _pediatric_vitals(500),
        _athlete_vitals(500),
    ]
    X = np.vstack(parts)
    np.random.shuffle(X)
    return pd.DataFrame(X, columns=COLUMNS)


def generate_eval_data() -> tuple[pd.DataFrame, np.ndarray]:
    """Create a labelled evaluation set: 0 = normal, 1 = anomaly."""
    normal = _normal_vitals(500)
    anomalous = _anomalous_vitals(100)
    X = np.vstack([normal, anomalous])
    y = np.array([0] * len(normal) + [1] * len(anomalous))
    idx = np.random.permutation(len(X))
    df = pd.DataFrame(X[idx], columns=COLUMNS)
    return df, y[idx]


# ── Training + evaluation ────────────────────────────────────────────────────

def train_anomaly_detector() -> None:
    print("=" * 60)
    print("  Intelligent Clinic - Anomaly Detection Model Training")
    print("=" * 60)

    # 1. Generate data
    df_train = generate_training_data()
    print(f"\n[+] Generated {len(df_train)} training samples across 4 patient profiles")
    print(f"  Feature statistics:\n{df_train.describe().round(1).to_string()}\n")

    # 2. Save CSV for reference
    df_train.to_csv(CSV_PATH, index=False)
    print(f"[+] Training data exported to {CSV_PATH}")

    # 3. Train
    model = IsolationForest(
        n_estimators=200,
        contamination=0.05,
        max_samples="auto",
        random_state=42,
        n_jobs=-1,
    )
    model.fit(df_train.values)
    print("[+] Isolation Forest trained (n_estimators=200, contamination=0.05)")

    # 4. Save
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(model, f)
    print(f"[+] Model saved to {MODEL_PATH}")

    # 5. Evaluate
    df_eval, y_true = generate_eval_data()
    preds_raw = model.predict(df_eval.values)
    y_pred = (preds_raw == -1).astype(int)

    print("\n-- Evaluation on held-out synthetic data --")
    print(classification_report(
        y_true, y_pred, target_names=["Normal", "Anomaly"], digits=3,
    ))

    # 6. Sanity checks
    print("-- Sanity checks --")
    cases = {
        "Healthy adult":            [75, 120, 78, 98, 36.8],
        "Elderly patient":          [68, 140, 88, 94, 36.5],
        "Tachycardia + fever":      [180, 200, 120, 85, 40.5],
        "Bradycardia + hypothermia": [35, 85, 55, 88, 34.0],
    }
    for label, vitals in cases.items():
        pred = model.predict(np.array(vitals).reshape(1, -1))[0]
        status = "ANOMALY" if pred == -1 else "NORMAL"
        print(f"  {label:30s} {vitals} -> {status}")

    print("\n[+] Done.")


if __name__ == "__main__":
    train_anomaly_detector()

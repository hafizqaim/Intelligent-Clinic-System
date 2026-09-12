"""ML model for anomaly detection in patient telemetry."""

import os
import pickle
import numpy as np
from sklearn.ensemble import IsolationForest
from typing import Optional, List


class AnomalyDetector:
    """Isolation Forest-based anomaly detector for patient vital signs."""

    def __init__(self, model_path: str = "ml_models/telemetry_anomaly_model.pkl"):
        self.model_path = model_path
        self.model: Optional[IsolationForest] = None

    def train(self, X: np.ndarray) -> None:
        """Train the Isolation Forest model on normal (non-anomalous) vital signs data."""
        self.model = IsolationForest(
            n_estimators=200, contamination=0.05, random_state=42, n_jobs=-1
        )
        self.model.fit(X)
        self.save()

    def save(self) -> None:
        """Persist model to disk."""
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        with open(self.model_path, "wb") as f:
            pickle.dump(self.model, f)

    def load(self) -> None:
        """Load model from disk."""
        if os.path.exists(self.model_path):
            with open(self.model_path, "rb") as f:
                self.model = pickle.load(f)
        else:
            raise FileNotFoundError(f"Model not found at {self.model_path}")

    def predict(self, vital_signs: List[Optional[float]]) -> bool:
        """
        Predict if a reading is anomalous.

        Args:
            vital_signs: List of [heart_rate, bp_systolic, bp_diastolic, o2_sat, temperature]
                        Use 0.0 for missing values

        Returns:
            True if anomalous, False if normal
        """
        if self.model is None:
            raise RuntimeError("Model not loaded. Call load() first.")

        # Ensure we have exactly 5 features
        if len(vital_signs) != 5:
            raise ValueError(f"Expected 5 vital signs, got {len(vital_signs)}")

        # Replace None with 0.0
        vital_signs = [v if v is not None else 0.0 for v in vital_signs]

        # Reshape for sklearn (1 sample, 5 features)
        X = np.array(vital_signs).reshape(1, -1)

        # Isolation Forest returns -1 for anomalies, 1 for normal
        prediction = self.model.predict(X)[0]
        return prediction == -1  # Return True if anomaly


# Global detector instance
detector = AnomalyDetector()

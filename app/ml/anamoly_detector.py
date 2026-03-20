from sklearn.ensemble import IsolationForest
import pandas as pd
import joblib

class AnomalyDetector:
    def __init__(self, contamination=0.1):
        self.contamination = contamination
        self.model = IsolationForest(contamination=self.contamination, n_estimators=100, random_state=42)

    def get_feature_columns(self, df: pd.DataFrame) -> list[str]:
        return [col for col in df.columns if col != 'timestamp' and col != 'patient_id' and col != 'is_anomaly']
        
    def train(self, df: pd.DataFrame):
        feature_columns = self.get_feature_columns(df)
        self.model.fit(df[feature_columns])

    def predict(self, df: pd.DataFrame) -> pd.DataFrame:
        feature_columns = self.get_feature_columns(df)
        predictions = self.model.predict(df[feature_columns])
        df['predicted_anomaly'] = predictions
        df['predicted_anomaly'] = df['predicted_anomaly'].apply(lambda x: 1 if x == -1 else 0)
        df['anomaly_score'] = self.model.decision_function(df[feature_columns])
        return df
    
    def save_model(self, file_path: str):
        joblib.dump(self.model, file_path)

    def load_model(self, file_path: str):
        self.model = joblib.load(file_path)
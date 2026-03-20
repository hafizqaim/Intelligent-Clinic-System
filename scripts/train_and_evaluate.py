from app.ml import preprocessing, anamoly_detector
from sklearn.metrics import classification_report, confusion_matrix

def main():
    # Load and preprocess data
    df = preprocessing.load_telemetry('data/telemetry_data.csv')

    df = preprocessing.clean_telemetry(df)
    
    df = preprocessing.engineer_features(df)

    anamoly_detector = anamoly_detector.AnomalyDetector(contamination=0.1)
    anamoly_detector.train(df)
    predictions_df = anamoly_detector.predict(df)

    print(classification_report(df['is_anomaly'], predictions_df['predicted_anomaly']))
    print(confusion_matrix(df['is_anomaly'], predictions_df['predicted_anomaly']))

    anamoly_detector.save_model('./ml_models/isolation_forest.joblib')

if __name__ == "__main__":
    main()
    
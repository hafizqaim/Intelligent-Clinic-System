import pandas as pd
from app.ml import preprocessing, anamoly_detector
from app.models.telemetry_readings import TelemetryReadings

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import UUID

async def ingest_telemetry(db: AsyncSession, clinic_id: UUID, patient_id: UUID, readings: list[dict]) -> list[dict]:
    """Ingest telemetry data into the database."""
    df = pd.DataFrame(readings)
    df = preprocessing.clean_telemetry(df)
    df = preprocessing.engineer_features(df)

    model = anamoly_detector.AnomalyDetector.load_model('./ml_models/isolation_forest.joblib')
    predictions_df = model.predict(df)

    # Convert predictions back to list of dicts for database insertion
    results = []
    for _, row in predictions_df.iterrows():
        result = {
            'clinic_id': clinic_id,
            'patient_id': patient_id,
            'timestamp': row['timestamp'],
            'heart_rate': row.get('heart_rate'),
            'blood_pressure_systolic': row.get('blood_pressure_systolic'),
            'blood_pressure_diastolic': row.get('blood_pressure_diastolic'),
            'oxygen_saturation': row.get('oxygen_saturation'),
            'temperature': row.get('temperature'),
            'is_anomaly': bool(row['predicted_anomaly'])
        }
        results.append(result)

    # Here you would insert results into the database using db session

    for result in results:
        telemetry_record = TelemetryReadings(**result)
        db.add(telemetry_record)
    await db.commit()


async def get_anamolies(db: AsyncSession, patient_id: UUID) -> list[dict]:
    """Retrieve anamolies for a given patient."""
    Query = (select(TelemetryReadings).
             where(TelemetryReadings.patient_id == patient_id).
             where(TelemetryReadings.is_anomaly == True))

    result = await db.execute(Query)
    rows = result.scalars().all()

    return [row.__dict__ for row in rows]

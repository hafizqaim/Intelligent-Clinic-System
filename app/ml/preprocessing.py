import pandas as pd

def load_telemetry(file_path) -> pd.DataFrame:
    """Load telemetry data from a CSV file."""

    df = pd.read_csv(file_path, parse_dates=['timestamp'])
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df.set_index('timestamp', inplace=True)
    
    return df

def clean_telemetry(df: pd.DataFrame) -> pd.DataFrame:
    """Clean telemetry data by handling missing values and outliers."""

    # Handle missing values
    df = df.fillna(method='ffill')

    if "patient_id" in df.columns:
        df = df.drop_duplicates(subset=["timestamp", "patient_id"])
    else:
        df = df.drop_duplicates()

    if "heart_rate" in df.columns:
            df["heart_rate"] = df["heart_rate"].clip(lower=0, upper=350)
    if "spo2" in df.columns:
            df["spo2"] = df["spo2"].clip(lower=0, upper=100)

        # Ensure chronological order
    df = df.sort_index()

    return df

def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Engineer features from telemetry data."""

    if "heart_rate" in df.columns:
        df['hr_rolling_mean'] = df['heart_rate'].rolling(window=5).mean()
        df['hr_rolling_std'] = df['heart_rate'].rolling(window=5).std()
        df['hr_rate_of_change'] = df['heart_rate'].diff()
    
    if "spo2" in df.columns:
        df['spo2_rolling_mean'] = df['spo2'].rolling(window=5).mean()
        df['spo2_rolling_std'] = df['spo2'].rolling(window=5).std()

    if "temperature" in df.columns:
        df['temp_rolling_mean'] = df['temperature'].rolling(window=5).mean()
        df['temp_rolling_std'] = df['temperature'].rolling(window=5).std()
        df['temp_rate_of_change'] = df['temperature'].diff()

    if "bp_systolic" in df.columns and "bp_diastolic" in df.columns:
        df['pulse_pressure'] = df['bp_systolic'] - df['bp_diastolic']
    
    if "heart_rate" in df.columns and "hr_rolling_mean" in df.columns and "hr_rolling_std" in df.columns:
        df['hr_z_score'] = (df['heart_rate'] - df['hr_rolling_mean']) / df['hr_rolling_std']

    if "spo2" in df.columns and "spo2_rolling_mean" in df.columns and "spo2_rolling_std" in df.columns:
        df['spo2_z_score'] = (df['spo2'] - df['spo2_rolling_mean']) / df['spo2_rolling_mean'].std()

    if "temperature" in df.columns and "temp_rolling_mean" in df.columns and "temp_rolling_std" in df.columns:
        df['temp_z_score'] = (df['temperature'] - df['temp_rolling_mean']) / df['temp_rolling_std']

    return df
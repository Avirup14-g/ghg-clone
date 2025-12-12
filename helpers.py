import requests
import pandas as pd
from datetime import datetime
import sqlite3
from config import DATABASE_NAME

def load_db_table():
    conn = sqlite3.connect(DATABASE_NAME)
    df = pd.read_sql("SELECT * FROM ghg_data ORDER BY timestamp ASC", conn)
    conn.close()
    return df

def save_dataframe_to_db(df, table="ghg_data"):
    conn = sqlite3.connect(DATABASE_NAME)
    df.to_sql(table, conn, if_exists="append", index=False)
    conn.close()

def fetch_location_air_quality(lat, lon, hourly_vars=None):
    """
    Fetch hourly air-quality data for given lat/lon from Open-Meteo Air Quality API.
    Returns a DataFrame with timestamp and requested pollutant columns.
    """
    if hourly_vars is None:
        hourly_vars = [
            "pm10","pm2_5","carbon_monoxide","nitrogen_dioxide",
            "sulphur_dioxide","ozone","temperature_2m",
            "relative_humidity_2m","wind_speed_10m"
        ]

    hourly_param = ",".join(hourly_vars)
    url = (
        f"https://air-quality-api.open-meteo.com/v1/air-quality?"
        f"latitude={lat}&longitude={lon}&hourly={hourly_param}"
    )

    r = requests.get(url, timeout=20)
    r.raise_for_status()
    payload = r.json()

    hourly = payload.get("hourly", {})
    # Build DataFrame only from keys that exist
    data = {"timestamp": hourly.get("time", [])}
    for var in hourly_vars:
        # Map API names to safer column names (carbon_monoxide -> co)
        col_name = var
        if var == "carbon_monoxide":
            col_name = "co"
        elif var == "nitrogen_dioxide":
            col_name = "no2"
        elif var == "sulphur_dioxide":
            col_name = "so2"
        elif var == "pm2_5":
            col_name = "pm2_5"
        elif var == "temperature_2m":
            col_name = "temp"
        elif var == "relative_humidity_2m":
            col_name = "humidity"
        elif var == "wind_speed_10m":
            col_name = "wind_speed"
        elif var == "ozone":
            col_name = "o3"

        # Only add if present in payload
        if hourly.get(var) is not None:
            data[col_name] = hourly[var]

    df = pd.DataFrame(data)
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df

def extract_latest_pollutant(df, pollutant_col):
    """
    Return the most recent non-null value for pollutant_col and its timestamp.
    """
    if pollutant_col not in df.columns:
        return None, None
    s = df.dropna(subset=[pollutant_col]).sort_values("timestamp")
    if s.empty:
        return None, None
    last = s.iloc[-1]
    return float(last[pollutant_col]), last["timestamp"]

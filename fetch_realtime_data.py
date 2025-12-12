import requests
import sqlite3
import pandas as pd
from config import LATITUDE, LONGITUDE, DATABASE_NAME

API_URL = (
    f"https://air-quality-api.open-meteo.com/v1/air-quality?"
    f"latitude={LATITUDE}&longitude={LONGITUDE}&hourly="
    "pm10,pm2_5,carbon_monoxide,nitrogen_dioxide,"
    "sulphur_dioxide,ozone,temperature_2m,"
    "relative_humidity_2m,wind_speed_10m"
)

# --------------------------------------
# CREATE DATABASE TABLE
# --------------------------------------
def create_table():
    conn = sqlite3.connect(DATABASE_NAME)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS ghg_data (
            timestamp TEXT,
            pm10 REAL,
            pm2_5 REAL,
            co REAL,
            no2 REAL,
            so2 REAL,
            o3 REAL,
            temp REAL,
            humidity REAL,
            wind_speed REAL
        )
    """)

    conn.commit()
    conn.close()


# --------------------------------------
# FETCH REAL-TIME DATA
# --------------------------------------
def fetch_data():
    response = requests.get(API_URL)
    hourly = response.json()["hourly"]

    df = pd.DataFrame({
        "timestamp": hourly["time"],
        "pm10": hourly["pm10"],
        "pm2_5": hourly["pm2_5"],
        "co": hourly["carbon_monoxide"],
        "no2": hourly["nitrogen_dioxide"],
        "so2": hourly["sulphur_dioxide"],
        "o3": hourly["ozone"],
        "temp": hourly["temperature_2m"],
        "humidity": hourly["relative_humidity_2m"],
        "wind_speed": hourly["wind_speed_10m"]
    })

    return df


# --------------------------------------
# INSERT INTO DATABASE
# --------------------------------------
def save_to_db(df):
    conn = sqlite3.connect(DATABASE_NAME)
    df.to_sql("ghg_data", conn, if_exists="append", index=False)
    conn.close()


if __name__ == "__main__":
    create_table()
    df = fetch_data()
    save_to_db(df)
    print("Real-time GHG data saved successfully!")

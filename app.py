# -------------------------------
# app.py (FINAL PATCHED VERSION)
# -------------------------------

import streamlit as st
import pandas as pd
import numpy as np
import tensorflow as tf
tf.get_logger().setLevel('ERROR')
from sklearn.preprocessing import MinMaxScaler
from helpers import fetch_location_air_quality, extract_latest_pollutant
from config import LSTM_MODEL_PATH

# NEW: geocoding
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

# NEW: HTML Leaflet map
import streamlit.components.v1 as components

st.set_page_config(page_title="GHG Monitor (Location-based)", layout="wide")
st.title("🌍 Real-Time GHG Monitoring — Location Based")

# --------------------------------------
# 1) FORWARD GEOCODING FUNCTION
# --------------------------------------
geolocator = Nominatim(user_agent="ghg_location_app")
geocode_safe = RateLimiter(geolocator.geocode, min_delay_seconds=1)

def forward_geocode(place):
    """Return lat, lon or None."""
    try:
        loc = geocode_safe(place)
        if loc:
            return loc.latitude, loc.longitude, loc.address
    except:
        pass
    return None, None, None

# --------------------------------------
# 2) SIDEBAR SEARCH
# --------------------------------------
st.sidebar.header("🔍 Location Search")

place_name = st.sidebar.text_input("Enter location name:")
search_btn = st.sidebar.button("Search")

st.sidebar.markdown("---")
lat_manual = st.sidebar.text_input("Latitude (optional override)")
lon_manual = st.sidebar.text_input("Longitude (optional override)")

lat = None
lon = None
display_name = None

# --------------------------------------
# 3) GEOCODING
# --------------------------------------
if search_btn and place_name.strip():
    lat, lon, display_name = forward_geocode(place_name)
    if lat is None:
        st.sidebar.error("❌ Location not found.")
    else:
        st.sidebar.success(f"Found: {display_name}")

# Manual override
if lat_manual.strip() and lon_manual.strip():
    try:
        lat = float(lat_manual)
        lon = float(lon_manual)
        display_name = f"Manual: {lat}, {lon}"
        st.sidebar.success("Using manually entered coordinates.")
    except:
        st.sidebar.error("Invalid manual coordinates.")

# --------------------------------------
# 4) LEAFLET MAP
# --------------------------------------
st.subheader("🗺️ Select / view location on map")

if lat is None:
    lat = 22.5726
    lon = 88.3639

leaflet_map = f"""
<div id="map" style="height: 480px; border-radius: 10px;"></div>
<script>
var map = L.map('map').setView([{lat}, {lon}], 13);
L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png').addTo(map);

var marker = L.marker([{lat}, {lon}]).addTo(map);

map.on('click', function(e) {{
    var lat = e.latlng.lat;
    var lon = e.latlng.lng;
    marker.setLatLng([lat, lon]);
    window.parent.postMessage({{"lat": lat, "lon": lon}}, "*");
}});
</script>
"""

leaflet_header = """
<link rel="stylesheet" href="https://unpkg.com/leaflet/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet/dist/leaflet.js"></script>
"""

components.html(leaflet_header + leaflet_map, height=500)

# --------------------------------------
# 5) FETCH BUTTON
# --------------------------------------
st.markdown("---")
fetch_btn = st.button("📡 Fetch air quality for this location")

# --------------------------------------
# 6) AIR QUALITY FETCH + UNIT PATCH
# --------------------------------------
if fetch_btn and lat is not None and lon is not None:
    st.success(f"Fetching AQ data for {lat:.6f}, {lon:.6f}...")

    try:
        hourly_vars = [
            "pm10","pm2_5","carbon_monoxide","nitrogen_dioxide",
            "sulphur_dioxide","ozone","temperature_2m",
            "relative_humidity_2m","wind_speed_10m"
        ]

        df_local = fetch_location_air_quality(lat, lon, hourly_vars=hourly_vars)

        # 🔥 PATCH: UNIT CONVERSION (µg/m³ → mg/m³)
        if "co" in df_local.columns:
            df_local["co_mg"] = df_local["co"] / 1000.0
        if "o3" in df_local.columns:
            df_local["o3_mg"] = df_local["o3"] / 1000.0

        st.subheader("📡 Raw AQ Data")
        st.write(df_local.tail(6))

        # ----------------------
        # TREND CHARTS (PATCHED)
        # ----------------------
        st.subheader("📈 Trends — CO (mg/m³), NO₂ (µg/m³), O₃ (mg/m³)")

        chart_cols = []
        if "co_mg" in df_local.columns:
            chart_cols.append("co_mg")
        if "no2" in df_local.columns:
            chart_cols.append("no2")
        if "o3_mg" in df_local.columns:
            chart_cols.append("o3_mg")

        st.line_chart(df_local.set_index("timestamp")[chart_cols])

        colA, colB = st.columns([2, 1])

        # --------------------------
        # O₃ SECTION (PATCHED UNITS)
        # --------------------------
        with colB:
            st.subheader("🧪 Environment pollutant — O₃ (mg/m³)")
            o3_val, o3_time = extract_latest_pollutant(df_local, "o3_mg" if "o3_mg" in df_local else "o3")

            if o3_val is None:
                st.write("No O₃ data.")
            else:
                st.metric("Latest O₃", f"{o3_val:.4f} mg/m³")
                st.line_chart(df_local.set_index("timestamp")[["o3_mg"]])

    except Exception as e:
        st.error(f"Error while fetching data: {e}")

# --------------------------------------
# 7) LSTM CO PREDICTION (PATCHED)
# --------------------------------------
if fetch_btn and "co" in df_local.columns:
    st.markdown("---")
    st.subheader("🔮 CO Prediction (next hour)")

    co_series = df_local["co"].dropna().values.reshape(-1, 1)

    if len(co_series) < 30:
        st.warning("Need at least 30 points.")
    else:
        scaler = MinMaxScaler()
        scaled = scaler.fit_transform(co_series)

        window = 24
        if len(scaled) <= window:
            st.warning("Not enough data for window.")
        else:
            inp = scaled[-window:].reshape(1, window, 1)
            try:
                model = tf.keras.models.load_model(LSTM_MODEL_PATH, compile=False)
                pred_scaled = model.predict(inp)
                pred_ug = float(scaler.inverse_transform(pred_scaled)[0][0])
                pred_mg = pred_ug / 1000.0   # 🔥 PATCH

                st.metric("Forecasted CO (mg/m³)", f"{pred_mg:.4f}")

            except Exception as e:

                st.error("Prediction failed: " + str(e))



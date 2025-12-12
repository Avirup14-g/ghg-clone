import streamlit as st
import streamlit.components.v1 as components

def get_user_location():
    location_html = """
    <script>
    navigator.geolocation.getCurrentPosition(
        (pos) => {
            document.cookie = "lat=" + pos.coords.latitude;
            document.cookie = "lon=" + pos.coords.longitude;
        }, 
        (err) => {
            document.cookie = "lat=0";
            document.cookie = "lon=0";
        }
    );
    </script>
    """

    components.html(location_html)

    # Read cookies
    lat = st.session_state.get("lat", None)
    lon = st.session_state.get("lon", None)

    return lat, lon

import streamlit as st
import requests
import pandas as pd
import pydeck as pdk
from streamlit_autorefresh import st_autorefresh
from datetime import datetime, timedelta

# ----------------------------
# Page config
# ----------------------------
st.set_page_config(page_title="SafeWaters - Fishermen GPS Risk Monitor", layout="wide")

# ----------------------------
# Config
# ----------------------------
interval_ms = 60000  # 1 minute auto-refresh

# ----------------------------
# Initialize session state
# ----------------------------
if "last_refreshed" not in st.session_state:
    st.session_state.last_refreshed = datetime.now()

# ----------------------------
# Auto-refresh
# ----------------------------
st_autorefresh(interval=interval_ms, key="data_refresh")

# ----------------------------
# Manual refresh button
# ----------------------------
if st.button("🔄 Refresh Now"):
    st.session_state.last_refreshed = datetime.now()
    st.rerun()

# ----------------------------
# Fetch NOAA Kp Index
# ----------------------------
url = "https://services.swpc.noaa.gov/json/planetary_k_index_1m.json"
df = pd.read_json(url)
latest = df.tail(1).iloc[0]
kp_index = latest["kp_index"]
time_tag = latest["time_tag"]

# ----------------------------
# Fetch NOAA Alerts/Warnings/Forecasts
# ----------------------------
alerts_url = "https://services.swpc.noaa.gov/json/alerts.json"
try:
    alerts_data = requests.get(alerts_url, timeout=10).json()
except Exception:
    alerts_data = []

# Extract active geomagnetic alerts/watches
active_alerts = [
    a for a in alerts_data
    if "WATA" in a.get("message", "") or "ALTK" in a.get("message", "")
]

# ----------------------------
# Risk function (G-scale based)
# ----------------------------
def gps_risk_from_gscale(kp):
    if kp <= 4:
        return "🟢 Safe"
    elif kp == 5:
        return "🟡 Caution (G1 Minor Storm)"
    elif kp == 6:
        return "🟠 High Risk (G2 Moderate Storm)"
    elif kp == 7:
        return "🔴 High Risk (G3 Strong Storm)"
    elif kp == 8:
        return "⛔ Severe Risk (G4 Severe Storm)"
    else:
        return "🚨 Extreme Risk (G5 Extreme Storm)"

# ----------------------------
# Fishing Regions - Kenya & India
# ----------------------------
regions = {
    # --- Kenya (Coastal + Lakes) ---
    "Mombasa (Indian Ocean)": (-4.0435, 39.6682),
    "Malindi (Indian Ocean)": (-3.2174, 40.1169),
    "Lamu (Indian Ocean)": (-2.2717, 40.9020),
    "Kilifi (Indian Ocean)": (-3.6308, 39.8496),
    "Watamu (Indian Ocean)": (-3.3520, 40.0284),
    "Kisumu (Lake Victoria)": (-0.0917, 34.7680),
    "Homa Bay (Lake Victoria)": (-0.5273, 34.4571),
    "Mbita Point (Lake Victoria)": (-0.4210, 34.2034),
    "Bondo (Lake Victoria)": (-0.1066, 34.2502),
    "Kalokol (Lake Turkana)": (3.4871, 35.8721),
    "Lodwar (Lake Turkana)": (3.1155, 35.6007),
    "Naivasha (Lake Naivasha)": (-0.7167, 36.4333),
    "Marigat (Lake Baringo)": (0.4667, 36.1000),

    # --- India (Coastal Fishing Hubs) ---
    "Kochi (Arabian Sea)": (9.9312, 76.2673),
    "Mangalore (Arabian Sea)": (12.9141, 74.8560),
    "Veraval (Arabian Sea)": (20.9077, 70.3679),
    "Mumbai (Arabian Sea)": (19.0760, 72.8777),
    "Kakinada (Bay of Bengal)": (16.9891, 82.2475),
    "Chennai (Bay of Bengal)": (13.0827, 80.2707),
    "Visakhapatnam (Bay of Bengal)": (17.6868, 83.2185),
    "Puri (Bay of Bengal)": (19.8135, 85.8312),
    "Paradip (Bay of Bengal)": (20.3167, 86.6167),
    "Tuticorin (Bay of Bengal)": (8.7642, 78.1348),
    "Kollam (Arabian Sea)": (8.8932, 76.6141),
    "Nagapattinam (Bay of Bengal)": (10.7630, 79.8449),
}

# Build DataFrame
data = []
for city, (lat, lon) in regions.items():
    risk = gps_risk_from_gscale(kp_index)
    data.append({"City": city, "Latitude": lat, "Longitude": lon, "Risk": risk})
risk_df = pd.DataFrame(data)

# Map + Table Colors
color_map = {
    "🟢 Safe": [0, 180, 0],
    "🟡 Caution (G1 Minor Storm)": [255, 200, 0],
    "🟠 High Risk (G2 Moderate Storm)": [255, 140, 0],
    "🔴 High Risk (G3 Strong Storm)": [220, 80, 0],
    "⛔ Severe Risk (G4 Severe Storm)": [200, 0, 0],
    "🚨 Extreme Risk (G5 Extreme Storm)": [120, 0, 0],
}
risk_df["Color"] = risk_df["Risk"].map(color_map)

# For table styling
def highlight_risk(val):
    if "Safe" in val:
        color = "lightgreen"
    elif "Caution" in val:
        color = "khaki"
    elif "High Risk" in val:
        color = "salmon"
    elif "Severe" in val:
        color = "red"
    else:
        color = "darkred; color: white"
    return f"background-color: {color}; font-weight: bold;"

# ----------------------------
# Streamlit Layout
# ----------------------------
st.title("🌊 SafeWaters - Fishermen GPS Risk Monitor")
st.caption("Helping fishermen in Kenya & India stay safe from GPS disruptions caused by solar storms.")

# Last refresh info
st.caption(f"⏱️ Last refreshed: {st.session_state.last_refreshed.strftime('%Y-%m-%d %H:%M:%S')}")

# Countdown
next_refresh_time = st.session_state.last_refreshed + timedelta(milliseconds=interval_ms)
seconds_remaining = int((next_refresh_time - datetime.now()).total_seconds())
seconds_remaining = max(0, seconds_remaining)
mins, secs = divmod(seconds_remaining, 60)
st.markdown(f"⌛ Next auto-refresh in: **{mins}m {secs:02d}s**")

# ----------------------------
# NOAA Alert Banner
# ----------------------------
if active_alerts:
    st.error("⚠️ ACTIVE NOAA ALERTS/WATCHES")
    for a in active_alerts:
        st.markdown(f"- {a.get('message')}")
else:
    st.success("✅ No active NOAA geomagnetic storm alerts at the moment.")

# ----------------------------
# Filters: Dropdown + Search
# ----------------------------
col_filter1, col_filter2 = st.columns([1,2])
with col_filter1:
    city_filter = st.selectbox("📍 Select a Location", ["All"] + list(risk_df["City"]))
with col_filter2:
    search_query = st.text_input("🔎 Search Location")

filtered_df = risk_df.copy()
if city_filter != "All":
    filtered_df = filtered_df[filtered_df["City"] == city_filter]
if search_query:
    filtered_df = filtered_df[filtered_df["City"].str.contains(search_query, case=False)]

# ----------------------------
# Fishermen Quick Status
# ----------------------------
if city_filter != "All" and not filtered_df.empty:
    current_status = filtered_df.iloc[0]["Risk"]
    if "Safe" in current_status:
        st.success(f"{current_status} today in {city_filter} – GPS stable.")
    elif "Caution" in current_status:
        st.warning(f"{current_status} in {city_filter} – Minor GPS disruptions possible.")
    else:
        st.error(f"{current_status} in {city_filter} – GPS may be unreliable.")

# ----------------------------
# Fishermen Toolbox (simple demo version)
# ----------------------------
st.markdown("### 🧰 Fishermen Toolbox")
col1, col2, col3 = st.columns(3)
col1.metric("🌤 Weather", "Clear", "24°C")   # Placeholder
col2.metric("🌊 Wave Height", "2 ft", "Stable")  # Placeholder
col3.metric("📡 Kp Index", f"{kp_index}", "Latest")

# ----------------------------
# Tabs for Table and Map
# ----------------------------
tab1, tab2 = st.tabs(["📍 Location Risks (Table)", "🌍 Regional Risk Map"])

with tab1:
    st.subheader("📍 Location-specific Risks")
    st.dataframe(filtered_df.style.applymap(highlight_risk, subset=["Risk"]))

with tab2:
    st.subheader("🌍 Risk Map")
    layer = pdk.Layer(
        "ScatterplotLayer",
        data=filtered_df,
        get_position=["Longitude", "Latitude"],
        get_color="Color",
        get_radius=200000,
        pickable=True,
    )
    view_state = pdk.ViewState(latitude=10, longitude=75, zoom=3, pitch=0)  # focus on Kenya & India
    st.pydeck_chart(
        pdk.Deck(
            layers=[layer],
            initial_view_state=view_state,
            tooltip={"text": "📍 {City}\n⚠️ Risk: {Risk}"}
        )
    )

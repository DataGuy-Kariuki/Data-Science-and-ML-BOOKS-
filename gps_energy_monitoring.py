import streamlit as st
import requests
import pandas as pd
import pydeck as pdk
from datetime import datetime

# ----------------------------
# Page config
# ----------------------------
st.set_page_config(page_title="SafeWaters - Fishermen GPS Risk Monitor", layout="wide")

# ----------------------------
# Background Styling (Ocean Blue Theme)
# ----------------------------
page_bg = """
<style>
    .stApp {
        background-color: #f0f8ff;
        background-image: linear-gradient(to bottom right, #f0f8ff, #e6f7ff);
    }
    .stDataFrame, .stMarkdown, .stDownloadButton {
        font-family: "Arial", sans-serif;
    }
    h1, h2, h3, h4 {
        color: #003366; /* Deep ocean blue for titles */
    }
</style>
"""
st.markdown(page_bg, unsafe_allow_html=True)

# ----------------------------
# Data Sources
# ----------------------------
url = "https://services.swpc.noaa.gov/json/planetary_k_index_1m.json"
alerts_url = "https://services.swpc.noaa.gov/json/alerts.json"

# ----------------------------
# Refresh Data Button
# ----------------------------
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def fetch_data():
    df = pd.read_json(url)
    latest = df.tail(1).iloc[0]
    kp = latest["kp_index"]
    time_tag = latest["time_tag"]

    try:
        alerts_data = requests.get(alerts_url, timeout=10).json()
    except Exception:
        alerts_data = []

    return kp, time_tag, alerts_data

if st.button("🔄 Refresh Data"):
    kp_index, time_tag, alerts_data = fetch_data()
    st.session_state.kp_index = kp_index
    st.session_state.time_tag = time_tag
    st.session_state.alerts_data = alerts_data
    st.session_state.last_refresh = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# If first run and no refresh yet, fetch once
if "kp_index" not in st.session_state:
    kp_index, time_tag, alerts_data = fetch_data()
    st.session_state.kp_index = kp_index
    st.session_state.time_tag = time_tag
    st.session_state.alerts_data = alerts_data

st.caption(f"🕒 Last refresh: {st.session_state.last_refresh}")

kp_index = st.session_state.kp_index
time_tag = st.session_state.time_tag
alerts_data = st.session_state.alerts_data

# ----------------------------
# Extract active alerts
# ----------------------------
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

# ----------------------------
# Risk Colors for Map
# ----------------------------
color_map = {
    "🟢 Safe": [0, 180, 0],
    "🟡 Caution (G1 Minor Storm)": [255, 200, 0],
    "🟠 High Risk (G2 Moderate Storm)": [255, 140, 0],
    "🔴 High Risk (G3 Strong Storm)": [220, 80, 0],
    "⛔ Severe Risk (G4 Severe Storm)": [200, 0, 0],
    "🚨 Extreme Risk (G5 Extreme Storm)": [120, 0, 0],
}

# Build DataFrame
data = []
for city, (lat, lon) in regions.items():
    risk = gps_risk_from_gscale(kp_index)
    color = color_map[risk]
    data.append({"City": city, "Latitude": lat, "Longitude": lon, "Risk": risk, "Color": color})
risk_df = pd.DataFrame(data)

# ----------------------------
# Streamlit Layout
# ----------------------------
st.title("🌊 SafeWaters - Fishermen GPS Risk Monitor")
st.caption("Helping fishermen in Kenya & India stay safe from GPS disruptions caused by solar storms.")

# NOAA Alert Banner
if active_alerts:
    st.error("⚠️ ACTIVE NOAA ALERTS/WATCHES")
    for a in active_alerts:
        st.markdown(f"- {a.get('message')}")
else:
    st.success("✅ No active NOAA geomagnetic storm alerts at the moment.")

# Filters
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

# Fishermen Quick Status
if city_filter != "All" and not filtered_df.empty:
    current_status = filtered_df.iloc[0]["Risk"]
    if "Safe" in current_status:
        st.success(f"{current_status} today in {city_filter} – GPS stable.")
    elif "Caution" in current_status:
        st.warning(f"{current_status} in {city_filter} – Minor GPS disruptions possible.")
    else:
        st.error(f"{current_status} in {city_filter} – GPS may be unreliable.")

# Table + Map
col1, col2 = st.columns([1.2, 2])

with col1:
    st.subheader(" Location-specific Risks")
    display_df = filtered_df[["City", "Risk"]]
    st.dataframe(display_df)

    # Download CSV
    csv = risk_df.to_csv(index=False).encode("utf-8")
    st.download_button("📥 Download Full Data (CSV)", data=csv, file_name="gps_risk_data.csv", mime="text/csv")

    # Legend
    st.markdown("### Risk Legend")
    legend_items = [
        ("🟢 Safe", "GPS is stable, good to go fishing."),
        ("🟡 Caution (G1 Minor Storm)", "Small GPS disruptions possible — stay alert but still safe."),
        ("🟠 High Risk (G2 Moderate Storm)", "GPS may mislead boats — use extra caution."),
        ("🔴 High Risk (G3 Strong Storm)", "Dangerous GPS errors likely — avoid fishing today."),
        ("⛔ Severe Risk (G4 Severe Storm)", "GPS very unreliable — don’t go out."),
        ("🚨 Extreme Risk (G5 Extreme Storm)", "Severe storm — stay on land for safety."),
    ]
    for status, explanation in legend_items:
        st.markdown(
            f"<div style='margin-bottom:12px;'>"
            f"<div style='font-size:16px; font-weight:bold;'>{status}</div>"
            f"<div style='margin-left:20px; color:#555;'>{explanation}</div>"
            f"</div>",
            unsafe_allow_html=True
        )

with col2:
    st.subheader(" Risk Map")
    layer = pdk.Layer(
        "ScatterplotLayer",
        data=filtered_df,
        get_position=["Longitude", "Latitude"],
        get_color="Color",
        get_radius=200000,
        pickable=True,
    )
    view_state = pdk.ViewState(latitude=10, longitude=75, zoom=3, pitch=0)
    st.pydeck_chart(
        pdk.Deck(
            layers=[layer],
            initial_view_state=view_state,
            tooltip={"text": "📍 {City}\n⚠️ Risk: {Risk}"}
        )
    )

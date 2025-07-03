import streamlit as st
import pandas as pd
import numpy as np
from scipy.spatial import cKDTree
import requests

# --- API Function (embedded locally) ---
def get_price_estimates(zip_code="85004", limit=50):
    url = "https://realty-in-us.p.rapidapi.com/properties/v3/list"
    headers = {
        "content-type": "application/json",
        "X-RapidAPI-Key": "33f7baa8aemshb3380eca00fc1c0p16a229jsn6f972fd9d47e",
        "X-RapidAPI-Host": "realty-in-us.p.rapidapi.com"
    }
    payload = {
        "limit": limit,
        "offset": 0,
        "postal_code": zip_code,
        "status": ["for_sale"],
        "sort": {"direction": "desc", "field": "list_date"}
    }

    response = requests.post(url, json=payload, headers=headers)
    if response.status_code != 200:
        raise Exception(f"API error {response.status_code}: {response.text}")

    listings = response.json().get("data", {}).get("home_search", {}).get("results", [])
    records = []

    for i, home in enumerate(listings):
        try:
            location = home.get("location")
            address = location.get("address") if location else None
            coord = address.get("coordinate") if address else None

            if not location or not address or not coord:
                continue

            lat = coord.get("lat")
            lon = coord.get("lon")
            if lat is None or lon is None:
                continue

            desc = home.get("description", {}) or {}

            records.append({
                "address": address.get("line", "N/A"),
                "city": address.get("city", "N/A"),
                "zipcode": address.get("postal_code", "N/A"),
                "base_price": home.get("list_price", None),
                "nearest_lat": lat,
                "nearest_lon": lon,
                "beds": desc.get("beds", None),
                "baths": desc.get("baths", None),
                "lot_sqft": desc.get("lot_sqft", None),
                "type": desc.get("type", None),
                "url": home.get("href", None)
            })
        except Exception as e:
            print(f"❌ Skipped listing {i+1}: {e}")

    return pd.DataFrame(records)

# --- Streamlit UI ---
st.title("🏠 Risk-Adjusted Housing Prices")

# Sidebar for city selection (Phoenix only for now)
city = st.sidebar.selectbox("Select a City", ["Phoenix"])

@st.cache_data
def load_scores():
    return pd.read_csv("C:/Users/tomas/Capstone/phoenix_scores.csv")

@st.cache_data
def load_housing():
    return get_price_estimates(zip_code="85004")

if city == "Phoenix":
    st.subheader("Phoenix Housing Risk-Adjusted Pricing")

    df_scores = load_scores()
    df_houses = load_housing()

    df_houses = df_houses.dropna(subset=['nearest_lat', 'nearest_lon'])
    if df_houses.empty:
        st.warning("No valid listings found.")
        st.stop()

    tree = cKDTree(df_scores[['lat', 'lon']].values)
    house_coords = df_houses[['nearest_lat', 'nearest_lon']].values
    _, indices = tree.query(house_coords, k=1)
    df_houses['std_score'] = df_scores.iloc[indices]['std_score'].values
    df_houses = df_houses.dropna(subset=['std_score'])

    risk_scaled = (df_houses['std_score'] - df_houses['std_score'].min()) / (
        df_houses['std_score'].max() - df_houses['std_score'].min()
    )
    df_houses['risk_adjusted_price'] = df_houses['base_price'] * (1 - 0.2 * risk_scaled)

    # --- Selection/Input ---
    st.markdown("### 📍 Choose or Input a House")
    option = st.radio("Select input method", ["Choose from list", "Manual input"])

    if option == "Choose from list":
        selected = st.selectbox("Select a house", df_houses['address'])
        row = df_houses[df_houses['address'] == selected].iloc[0]
        st.write(f"**Base Price:** ${row['base_price']:,}")
        st.write(f"**Adjusted Price:** ${row['risk_adjusted_price']:.2f}")
        st.write(f"**Lat/Lon:** ({row['nearest_lat']}, {row['nearest_lon']})")
        st.write(f"[View Listing](https://www.realtor.com{row['url']})")
    else:
        lat = st.number_input("Latitude", format="%.6f")
        lon = st.number_input("Longitude", format="%.6f")
        price = st.number_input("Base Price (USD)", format="%.2f")

        _, idx = tree.query([[lat, lon]], k=1)
        std_score = df_scores.iloc[idx[0]]['std_score']
        risk_scaled = (std_score - df_scores['std_score'].min()) / (
            df_scores['std_score'].max() - df_scores['std_score'].min()
        )
        adjusted_price = price * (1 - 0.2 * risk_scaled)

        st.write(f"**Nearest Score:** {std_score:.4f}")
        st.write(f"**Risk-Adjusted Price:** ${adjusted_price:,.2f}")

    # --- Optional Visualization ---
    if st.checkbox("Show Risk Adjusted Price Map"):
        st.map(df_houses.rename(columns={"nearest_lat": "lat", "nearest_lon": "lon"}))

    if st.checkbox("Show Price Distribution", value=True):
        st.bar_chart(df_houses['risk_adjusted_price'])
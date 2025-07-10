import streamlit as st
import pandas as pd
import numpy as np
from scipy.spatial import cKDTree
import requests
import pydeck as pdk
import matplotlib.pyplot as plt

# --- API Key Input ---
st.title("🔐 Risk-Adjusted Housing Prices")
api_key = st.text_input("Enter your RapidAPI key to begin:", type="password")

if not api_key:
    st.warning("Please enter your API key to continue.")
    st.stop()

# --- API Function ---
def get_price_estimates(zip_code="85004", limit=200):
    url = "https://realty-in-us.p.rapidapi.com/properties/v3/list"
    headers = {
        "content-type": "application/json",
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": "realty-in-us.p.rapidapi.com"
    }
    payload = {
        "limit": limit,
        "offset": 0,
        "postal_code": zip_code,
        "status": ["for_sale"],
        "sort": {"direction": "desc", "field": "list_date"}
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        listings = data.get("data", {}).get("home_search", {}).get("results", [])
    except Exception as e:
        st.warning(f"Failed to fetch ZIP {zip_code}: {e}")
        return pd.DataFrame()

    records = []
    for home in listings:
        try:
            location = home.get("location", {}).get("address", {})
            coord = location.get("coordinate", {})
            if not coord.get("lat") or not coord.get("lon"):
                continue
            desc = home.get("description", {}) or {}
            records.append({
                "address": location.get("line", "N/A"),
                "city": location.get("city", "N/A"),
                "zipcode": location.get("postal_code", "N/A"),
                "base_price": home.get("list_price", None),
                "nearest_lat": coord.get("lat"),
                "nearest_lon": coord.get("lon"),
                "beds": desc.get("beds", None),
                "baths": desc.get("baths", None),
                "lot_sqft": desc.get("lot_sqft", None),
                "type": desc.get("type", None),
                "url": home.get("href", None)
            })
        except:
            continue

    return pd.DataFrame(records)

# --- Load Data ---
@st.cache_data
def load_scores():
    return pd.read_csv("../Dataset/phoenix_scores.csv")

@st.cache_data
def load_housing(zips):
    dfs = [get_price_estimates(zip_code=z) for z in zips]
    return pd.concat(dfs, ignore_index=True)

PHOENIX_ZIPS = [
    "85003", "85004", "85006", "85007", "85008", "85009", "85012",
    "85013", "85014", "85015", "85016", "85017", "85018", "85020",
    "85021", "85022", "85023", "85024", "85027", "85028", "85029",
    "85031", "85032", "85033", "85034", "85035", "85037", "85040",
    "85041", "85042", "85043", "85044", "85045", "85048", "85050",
    "85051", "85053", "85054", "85083", "85085", "85086", "85087"
]

df_scores = load_scores()
df_houses = load_housing(PHOENIX_ZIPS)
df_houses = df_houses.dropna(subset=['nearest_lat', 'nearest_lon'])

# Match risk scores
tree = cKDTree(df_scores[['lat', 'lon']].values)
house_coords = df_houses[['nearest_lat', 'nearest_lon']].values
_, indices = tree.query(house_coords, k=1)
df_houses['std_score'] = df_scores.iloc[indices]['std_score'].values
df_houses = df_houses.dropna(subset=['std_score'])

# Adjust prices
risk_scaled = (df_houses['std_score'] - df_houses['std_score'].min()) / (
    df_houses['std_score'].max() - df_houses['std_score'].min()
)
df_houses['risk_adjusted_price'] = df_houses['base_price'] * (1 - 0.2 * risk_scaled)
df_houses['adjustment_pct'] = ((df_houses['risk_adjusted_price'] - df_houses['base_price']) / df_houses['base_price']) * 100

# --- UI ---
st.subheader("🏡 Property Lookup")
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

# --- Insights ---
st.divider()
st.subheader("📊 Data Insights")

if st.checkbox("Top 5 Most Under/Over-Priced Homes"):
    top_up = df_houses.sort_values("adjustment_pct", ascending=False).head(5)
    top_down = df_houses.sort_values("adjustment_pct").head(5)
    st.markdown("#### Most Underpriced")
    st.dataframe(top_up[['address', 'base_price', 'risk_adjusted_price', 'adjustment_pct']])
    st.markdown("#### Most Overpriced")
    st.dataframe(top_down[['address', 'base_price', 'risk_adjusted_price', 'adjustment_pct']])

if st.checkbox("Cumulative Market Impact of Risk"):
    total_market_value = df_houses['base_price'].sum()
    total_adjusted_value = df_houses['risk_adjusted_price'].sum()
    delta = total_adjusted_value - total_market_value
    st.metric("Total Market Value", f"${total_market_value:,.0f}")
    st.metric("Total Adjusted Value", f"${total_adjusted_value:,.0f}",
              delta=f"${abs(delta):,.0f}", delta_color="inverse" if delta < 0 else "normal")

if st.checkbox("Adjusted Price per Square Foot"):
    df_houses['adjusted_ppsqft'] = df_houses['risk_adjusted_price'] / df_houses['lot_sqft']
    top_ppsqft = df_houses[['address', 'type', 'adjusted_ppsqft']].dropna().sort_values('adjusted_ppsqft', ascending=False)
    st.dataframe(top_ppsqft.head(10))

if st.checkbox("Show Map of All Homes by Risk"):
    df_houses['lat'] = df_houses['nearest_lat']
    df_houses['lon'] = df_houses['nearest_lon']
    layer = pdk.Layer(
        'ScatterplotLayer',
        data=df_houses,
        get_position='[lon, lat]',
        get_color='[255 * std_score, 50, 150]',
        get_radius=100,
        pickable=True
    )
    st.pydeck_chart(pdk.Deck(
        initial_view_state=pdk.ViewState(
            latitude=df_houses['lat'].mean(),
            longitude=df_houses['lon'].mean(),
            zoom=12
        ),
        layers=[layer],
        tooltip={"text": "{address}\\nPrice: ${base_price}\\nRisk: {std_score}"}
    ))

if st.checkbox("Simulate Risk Sensitivity"):
    penalty_slider = st.slider("Risk Penalty Weight", 0.0, 1.0, 0.4)
    df_houses['simulated_price'] = df_houses['base_price'] * (1 - penalty_slider * risk_scaled)
    st.markdown("#### Simulated Adjusted Price (with Risk Penalty Weight)")
    chart_data = pd.DataFrame({
        'Original Price': df_houses['base_price'],
        'Simulated Price': df_houses['simulated_price']
    })
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(chart_data['Original Price'].values, label='Original Price')
    ax.plot(chart_data['Simulated Price'].values, label='Simulated Price', linestyle='--')
    ax.set_title("Price Adjustment under Varying Risk Penalty")
    ax.set_ylabel("Price ($)")
    ax.set_xlabel("Property Index")
    ax.legend()
    st.pyplot(fig)

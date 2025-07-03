import requests
import pandas as pd

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
import os
import time
import urllib.parse
from pathlib import Path

import folium
import pandas as pd
import requests


access_token = os.getenv("MAPBOX_TOKEN", "YOUR_MAPBOX_TOKEN")
base_dir = Path(__file__).resolve().parent
csv_file = base_dir / "hometown_locations.csv"
output_file = base_dir / "austin_hometown_map.html"
required_columns = {"Name", "Address", "Type", "Description", "Image_URL"}


def style_by_type(place_type):
    place_type = str(place_type).strip().lower()
    if place_type == "park":
        return "green", "tree"
    if place_type == "recreation":
        return "cadetblue", "info-sign"
    if place_type == "restaurant":
        return "red", "cutlery"
    if place_type == "cafe":
        return "orange", "coffee"
    if place_type == "shopping":
        return "purple", "shopping-cart"
    if place_type == "dessert":
        return "pink", "heart"
    return "blue", "info-sign"


def geocode_address(address):
    encoded_address = urllib.parse.quote(address)
    geocode_url = (
        f"https://api.mapbox.com/search/geocode/v6/forward"
        f"?q={encoded_address}&access_token={access_token}"
    )
    response = requests.get(geocode_url, timeout=30)
    response.raise_for_status()
    data = response.json()
    if data.get("features"):
        lon, lat = data["features"][0]["geometry"]["coordinates"]
        return lat, lon
    return None, None


def fallback_data():
    return pd.DataFrame(
        [
            {
                "Name": "Zilker Park",
                "Type": "park",
                "Description": "A favorite Austin green space.",
                "Image_URL": "",
                "Latitude": 30.266962,
                "Longitude": -97.772859,
            },
            {
                "Name": "South Congress",
                "Type": "shopping",
                "Description": "Iconic Austin street with local shops.",
                "Image_URL": "",
                "Latitude": 30.250276,
                "Longitude": -97.749405,
            },
            {
                "Name": "Lady Bird Lake",
                "Type": "recreation",
                "Description": "Popular trail and water recreation area.",
                "Image_URL": "",
                "Latitude": 30.260704,
                "Longitude": -97.744433,
            },
        ]
    )


def load_or_build_data():
    if not csv_file.exists():
        print(f"CSV not found at {csv_file}. Using fallback Austin locations.")
        return fallback_data(), False

    df = pd.read_csv(csv_file)
    missing_columns = required_columns - set(df.columns)
    if missing_columns:
        raise ValueError(f"CSV is missing required columns: {sorted(missing_columns)}")

    if {"Latitude", "Longitude"}.issubset(df.columns):
        df = df.dropna(subset=["Latitude", "Longitude"]).copy()
        if not df.empty:
            return df, True

    if access_token == "YOUR_MAPBOX_TOKEN":
        print("Mapbox token not set. Using fallback Austin locations.")
        return fallback_data(), False

    latitudes = []
    longitudes = []
    for address in df["Address"]:
        try:
            lat, lon = geocode_address(address)
            latitudes.append(lat)
            longitudes.append(lon)
        except Exception as e:
            print(f"Could not geocode {address}: {e}")
            latitudes.append(None)
            longitudes.append(None)
        time.sleep(0.2)

    df["Latitude"] = latitudes
    df["Longitude"] = longitudes
    df = df.dropna(subset=["Latitude", "Longitude"]).copy()
    if df.empty:
        print("No valid geocoded rows. Using fallback Austin locations.")
        return fallback_data(), False
    return df, True


def build_map(df, use_mapbox):
    center_lat = df["Latitude"].mean()
    center_lon = df["Longitude"].mean()
    m = folium.Map(location=[center_lat, center_lon], zoom_start=11, tiles=None)

    if use_mapbox and access_token != "YOUR_MAPBOX_TOKEN":
        folium.TileLayer(
            tiles=(
                "https://api.mapbox.com/styles/v1/summerregan/"
                "cmm82ywzg000201qo7jeof7uk/tiles/256/{z}/{x}/{y}@2x"
                f"?access_token={access_token}"
            ),
            attr="Mapbox",
            name="Custom Mapbox Style",
        ).add_to(m)
    else:
        folium.TileLayer("OpenStreetMap", name="OpenStreetMap").add_to(m)

    for _, row in df.iterrows():
        color, icon_name = style_by_type(row.get("Type", ""))
        image_url = str(row.get("Image_URL", "")).strip()
        image_html = f'<img src="{image_url}" width="220">' if image_url else ""
        popup_html = f"""
        <div style="width:260px;">
            <h4>{row.get('Name', 'Location')}</h4>
            <p>{row.get('Description', '')}</p>
            {image_html}
        </div>
        """
        folium.Marker(
            location=[row["Latitude"], row["Longitude"]],
            popup=folium.Popup(popup_html, max_width=280),
            icon=folium.Icon(color=color, icon=icon_name, prefix="glyphicon"),
            tooltip=str(row.get("Name", "Location")),
        ).add_to(m)

    return m


def main():
    df, use_mapbox = load_or_build_data()
    m = build_map(df, use_mapbox)
    m.save(str(output_file))
    print(f"Map saved as {output_file}")


if __name__ == "__main__":
    main()

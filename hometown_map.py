import os
import time
import urllib.parse
from pathlib import Path

import folium
import pandas as pd
import requests

# ---------------------------
# MAPBOX SETTINGS
# ---------------------------
access_token = os.getenv("MAPBOX_TOKEN", "YOUR_MAPBOX_TOKEN")

# Your custom Mapbox style
tiles = "https://api.mapbox.com/styles/v1/summerregan/cmm82ywzg000201qo7jeof7uk/tiles/256/{z}/{x}/{y}@2x?access_token=" + access_token

base_dir = Path(__file__).resolve().parent
csv_file = base_dir / "hometown_locations.csv"
output_file = base_dir / "austin_hometown_map.html"
required_columns = {"Name", "Address", "Type", "Description", "Image_URL"}

# ---------------------------
# READ CSV
# ---------------------------
if not csv_file.exists():
    raise FileNotFoundError(f"Missing input file: {csv_file}")

if access_token == "YOUR_MAPBOX_TOKEN":
    raise ValueError("Set your Mapbox token in `access_token` before running this script.")

df = pd.read_csv(csv_file)
missing_columns = required_columns - set(df.columns)
if missing_columns:
    raise ValueError(f"CSV is missing required columns: {sorted(missing_columns)}")

# ---------------------------
# GEOCODE FUNCTION
# ---------------------------
def geocode_address(address):
    encoded_address = urllib.parse.quote(address)
    geocode_url = f"https://api.mapbox.com/search/geocode/v6/forward?q={encoded_address}&access_token={access_token}"

    response = requests.get(geocode_url, timeout=30)
    response.raise_for_status()
    data = response.json()

    if "features" in data and len(data["features"]) > 0:
        lon, lat = data["features"][0]["geometry"]["coordinates"]
        return lat, lon
    else:
        return None, None

# ---------------------------
# GEOCODE ALL ADDRESSES
# ---------------------------
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

# Remove rows that failed
df = df.dropna(subset=["Latitude", "Longitude"])
if df.empty:
    raise ValueError("No valid locations were geocoded. Check addresses and token permissions.")

# ---------------------------
# CENTER THE MAP
# ---------------------------
center_lat = df["Latitude"].mean()
center_lon = df["Longitude"].mean()

m = folium.Map(
    location=[center_lat, center_lon],
    zoom_start=11,
    tiles=None
)

# Add your custom basemap
folium.TileLayer(
    tiles=tiles,
    attr="Mapbox",
    name="Custom Mapbox Style"
).add_to(m)

# ---------------------------
# STYLE MARKERS BY TYPE
# ---------------------------
def style_by_type(place_type):
    place_type = str(place_type).strip().lower()

    if place_type == "park":
        return "green", "tree"
    elif place_type == "recreation":
        return "cadetblue", "info-sign"
    elif place_type == "restaurant":
        return "red", "cutlery"
    elif place_type == "cafe":
        return "orange", "coffee"
    elif place_type == "shopping":
        return "purple", "shopping-cart"
    elif place_type == "dessert":
        return "pink", "heart"
    else:
        return "blue", "info-sign"

# ---------------------------
# ADD MARKERS + POPUPS
# ---------------------------
for _, row in df.iterrows():
    color, icon_name = style_by_type(row["Type"])

    popup_html = f"""
    <div style="width:260px;">
        <h4>{row['Name']}</h4>
        <p>{row['Description']}</p>
        <img src="{row['Image_URL']}" width="220">
    </div>
    """

    folium.Marker(
        location=[row["Latitude"], row["Longitude"]],
        popup=folium.Popup(popup_html, max_width=280),
        icon=folium.Icon(color=color, icon=icon_name, prefix="glyphicon"),
        tooltip=row["Name"]
    ).add_to(m)

# ---------------------------
# SAVE MAP
# ---------------------------
m.save(str(output_file))
print(f"Map saved as {output_file}")

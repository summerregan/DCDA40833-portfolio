import os
import pandas as pd
import requests
import folium
import urllib.parse
import time
from pathlib import Path

# ---------------------------
# MAPBOX SETTINGS
# ---------------------------
access_token = os.getenv("MAPBOX_TOKEN", "").strip()

# Your custom Mapbox style tiles
tiles = "https://api.mapbox.com/styles/v1/summerregan/cmm82ywzg000201qo7jeof7uk/tiles/256/{z}/{x}/{y}@2x?access_token=" + access_token

base_dir = Path(__file__).resolve().parent
csv_candidates = [
    base_dir / "hometown_locations.csv",
    base_dir / "js" / "hometown_locations.csv",
]
csv_file = next((p for p in csv_candidates if p.exists()), None)
output_file = base_dir / "austin_hometown_map.html"

# ---------------------------
# READ CSV
# ---------------------------
if not access_token:
    raise ValueError("Set MAPBOX_TOKEN in your environment before running this script.")

if csv_file is None:
    raise FileNotFoundError("Could not find hometown_locations.csv in project root or js/ folder.")

df = pd.read_csv(csv_file)

print("CSV loaded successfully")
print(df.head())
print("Number of rows in CSV:", len(df))

# ---------------------------
# GEOCODE FUNCTION
# ---------------------------
def geocode_address(address):
    encoded_address = urllib.parse.quote(str(address))
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
        print(f"{address} -> {lat}, {lon}")
        latitudes.append(lat)
        longitudes.append(lon)
    except Exception as e:
        print(f"Could not geocode {address}: {e}")
        latitudes.append(None)
        longitudes.append(None)
    time.sleep(0.2)

df["Latitude"] = latitudes
df["Longitude"] = longitudes

# Remove rows that failed to geocode
df = df.dropna(subset=["Latitude", "Longitude"])

print("Rows after geocoding:", len(df))

# ---------------------------
# CENTER MAP
# ---------------------------
center_lat = df["Latitude"].mean()
center_lon = df["Longitude"].mean()

m = folium.Map(
    location=[center_lat, center_lon],
    zoom_start=11,
    tiles=None
)

# Add custom Mapbox basemap
folium.TileLayer(
    tiles=tiles,
    attr="Mapbox",
    name="Custom Mapbox Style",
    overlay=False,
    control=False
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
    image_url = str(row.get("Image_URL", "")).strip()
    if image_url.startswith("https://example.com/"):
        image_url = ""

    image_html = f'<img src="{image_url}" width="220">' if image_url else ""

    popup_html = f"""
    <div style="width:260px;">
        <h4>{row['Name']}</h4>
        <p>{row['Description']}</p>
        {image_html}
    </div>
    """

    folium.Marker(
        location=[row["Latitude"], row["Longitude"]],
        tooltip=row["Name"],
        popup=folium.Popup(popup_html, max_width=300),
        icon=folium.Icon(color=color, icon=icon_name)
    ).add_to(m)

# ---------------------------
# SAVE MAP
# ---------------------------
m.save(str(output_file))
print(f"Map saved as {output_file}")

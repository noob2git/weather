import json
import math
from pathlib import Path
from datetime import datetime
import pytz
import requests
import geopandas as gpd
import matplotlib.pyplot as plt
from adjustText import adjust_text
import matplotlib.patheffects as path_effects
import pandas as pd

# ==========================
# CONFIG
# ==========================
OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

# Approximate centroids for each state/UT
STATE_CENTROIDS = {
    "Andhra Pradesh": (15.9129, 79.74),
    "Arunachal Pradesh": (28.2180, 94.7278),
    "Assam": (26.2006, 92.9376),
    "Bihar": (25.0961, 85.3131),
    "Chhattisgarh": (21.2787, 81.8661),
    "Delhi": (28.7041, 77.1025),
    "Goa": (15.2993, 74.1240),
    "Gujarat": (22.2587, 71.1924),
    "Haryana": (29.0588, 76.0856),
    "Himachal Pradesh": (31.1048, 77.1734),
    "Jharkhand": (23.6102, 85.2799),
    "Karnataka": (15.3173, 75.7139),
    "Kerala": (10.8505, 76.2711),
    "Madhya Pradesh": (22.9734, 78.6569),
    "Maharashtra": (19.7515, 75.7139),
    "Manipur": (24.6637, 93.9063),
    "Meghalaya": (25.4670, 91.3662),
    "Mizoram": (23.1645, 92.9376),
    "Nagaland": (26.1584, 94.5624),
    "Odisha": (20.9517, 85.0985),
    "Punjab": (31.1471, 75.3412),
    "Rajasthan": (27.0238, 74.2179),
    "Sikkim": (27.5330, 88.5122),
    "Tamil Nadu": (11.1271, 78.6569),
    "Telangana": (18.1124, 79.0193),
    "Tripura": (23.9408, 91.9882),
    "Uttar Pradesh": (26.8467, 80.9462),
    "Uttarakhand": (30.0668, 79.0193),
    "West Bengal": (22.9868, 87.8550),
    # Union Territories
    "Andaman and Nicobar Islands": (11.7401, 92.6586),
    "Chandigarh": (30.7333, 76.7794),
    "D&D": (20.1809, 73.0169),
    "Jammu and Kashmir": (33.7782, 76.5762),
    "Ladakh": (34.1526, 77.5770),
    "Lakshadweep": (10.5667, 72.6417),
    "Puducherry": (11.9416, 79.8083),
}

# ==========================
# FUNCTIONS
# ==========================

def get_current_temp(lat: float, lon: float):
    """Fetch current temperature for given lat/lon using Open-Meteo."""
    params = {
        "latitude": lat,
        "longitude": lon,
        "current_weather": "true",
        "timezone": "auto",
    }
    r = requests.get(OPEN_METEO_URL, params=params, timeout=15)
    r.raise_for_status()
    data = r.json()
    return data.get("current_weather", {}).get("temperature")


def plot_heatmap(temp_data: dict, geojson_path: str, out_path: str, timestamp: str):
    """Plot a heatmap of India states using GeoPandas + Matplotlib, with adjusted labels."""
    india = gpd.read_file(geojson_path)

    # Standardize state name column
    if "name" in india.columns:
        india["state_name"] = india["name"]
    elif "st_nm" in india.columns:
        india["state_name"] = india["st_nm"]
    else:
        raise ValueError(f"Could not find state name column. Available: {india.columns}")

    # 🔑 Fix: normalize "Dadra and Nagar Haveli and Daman and Diu" → "D&D"
    india["state_name"] = india["state_name"].replace({
        "Dadra and Nagar Haveli and Daman and Diu": "D&D"
    })

    # Dissolve polygons by state_name (to merge sub-polygons into one)
    india = india.dissolve(by="state_name", as_index=False)

    # Attach temperatures
    india["temperature"] = india["state_name"].map(temp_data)

    # Plot
    fig, ax = plt.subplots(1, 1, figsize=(12, 14))
    india.plot(
        column="temperature",
        cmap="YlOrRd",   # Yellow → Orange → Red
        linewidth=0.5,
        ax=ax,
        edgecolor="black",
        legend=True,
        legend_kwds={
            "label": "Temperature (°C)",
            "orientation": "horizontal",
            "shrink": 0.5,
            "pad": 0.02,
            "aspect": 30
        },
        missing_kwds={"color": "lightgrey", "label": "No data"}
    )

    # Add labels (full names, small font)
    texts = []
    for idx, row in india.iterrows():
        if row["temperature"] is not None:
            centroid = row["geometry"].centroid
            label = f"{row['state_name']} {row['temperature']}°C"
            txt = ax.text(
                centroid.x,
                centroid.y,
                label,
                ha="center",
                fontsize=5,
                color="black",
                zorder=10
            )
            txt.set_path_effects([path_effects.withStroke(linewidth=1.5, foreground="white")])
            texts.append(txt)

    # Adjust to avoid overlaps
    adjust_text(
        texts,
        ax=ax,
        arrowprops=dict(arrowstyle="-", color="gray", lw=0.3),
        only_move={'points': 'y', 'text': 'y'},
        autoalign=False,
        force_text=0.3
    )

    # Title + timestamp
    plt.title("Average Temperature by State (India)", fontsize=18, fontweight="bold")
    plt.figtext(
        0.5, 0.01, f"Data extracted: {timestamp}", ha="center", fontsize=9, style="italic"
    )
    plt.axis("off")

    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    print(f"Heatmap saved → {out_path}")
    plt.close(fig)

# ==========================
# MAIN
# ==========================

def main():
    results = {}
    print("Fetching current temperatures...\n")
    for state, (lat, lon) in STATE_CENTROIDS.items():
        try:
            temp = get_current_temp(lat, lon)
            results[state] = temp
            print(f"{state:<35} {temp:>6} °C")
        except Exception as e:
            print(f"{state:<35} ERROR: {e}")
            results[state] = math.nan   # ensure state is logged even on failure

    out_dir = Path(__file__).resolve().parent.parent / "data"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Save raw JSON (latest snapshot)
    out_file = out_dir / "current_temps.json"
    out_file.write_text(json.dumps(results, indent=2))
    print(f"\nSaved JSON → {out_file}")

    # Append to CSV history
    csv_file = out_dir / "weather_history.csv"
    ist = pytz.timezone("Asia/Kolkata")
    timestamp = datetime.now(ist).strftime("%Y-%m-%d %H:%M:%S")

    row_df = pd.DataFrame([{"timestamp": timestamp, **results}])

    if csv_file.exists():
        row_df.to_csv(csv_file, mode="a", index=False, header=False)
    else:
        row_df.to_csv(csv_file, mode="w", index=False, header=True)

    print(f"Appended weather data → {csv_file}")

    # Use uploaded India GeoJSON
    geojson_file = out_dir / "india.geojson"
    if not geojson_file.exists():
        raise FileNotFoundError("india.geojson not found in data/. Please place it there.")

    # Plot heatmap
    heatmap_file = out_dir / "india_heatmap.png"
    ist = pytz.timezone("Asia/Kolkata")
    timestamp_full = datetime.now(ist).strftime("%Y-%m-%d %H:%M:%S %Z")
    plot_heatmap(results, str(geojson_file), str(heatmap_file), timestamp_full)

if __name__ == "__main__":
    main()

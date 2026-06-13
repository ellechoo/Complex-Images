"""
Submarine Cable Data Scraper
-----------------------------
Downloads cable data from submarinecablemap.com's public JSON API
and saves it into CSV files you can use for visualization.

How to run:
    python scrape_cables.py

Output files (created in the same folder):
    cables_summary.csv      -> one row per cable (name, length, owners, dates, etc.)
    landing_points.csv      -> one row per landing point (city/country + coordinates)
"""

import requests
import pandas as pd
import time
import json

# -----------------------------
# STEP 1: Set up basics
# -----------------------------
BASE_URL = "https://www.submarinecablemap.com/api/v3"
HEADERS = {
    # Pretending to be a normal browser helps avoid being blocked
    "User-Agent": "Mozilla/5.0 (compatible; research-script/1.0)"
}

def get_json(url):
    """Download a URL and return it as Python data (dict/list)."""
    response = requests.get(url, headers=HEADERS, timeout=20)
    response.raise_for_status()  # stops the script if something went wrong
    return response.json()


# -----------------------------
# STEP 2: Get the master list of all cables
# -----------------------------
print("Fetching list of all cables...")
cable_geo = get_json(f"{BASE_URL}/cable/cable-geo.json")

# cable_geo is GeoJSON: a "features" list, one per cable
cable_ids = []
for feature in cable_geo["features"]:
    props = feature["properties"]
    cable_ids.append({
        "id": props.get("id"),
        "name": props.get("name"),
        "slug": props.get("slug")  # used to build the detail URL
    })

print(f"Found {len(cable_ids)} cables.")


# -----------------------------
# STEP 3: Fetch details for EACH cable
# -----------------------------
all_cable_data = []

for i, cable in enumerate(cable_ids, start=1):
    cable_id = cable["id"]
    name = cable["name"]
    print(f"[{i}/{len(cable_ids)}] Fetching details for: {name}")

    try:
        detail = get_json(f"{BASE_URL}/cable/{cable_id}.json")
    except Exception as e:
        print(f"   -> Failed: {e}")
        continue

    # Pull out the fields we care about (use .get() so missing fields don't crash)
    all_cable_data.append({
        "id": cable_id,
        "name": detail.get("name"),
        "owners": detail.get("owners"),
        "length": detail.get("length"),
        "rfs_date": detail.get("rfs"),          # "ready for service" date
        "is_planned": detail.get("is_planned"),
        "notes": detail.get("notes"),
        "url": detail.get("url"),
        "landing_points": ", ".join(
            lp.get("name", "") for lp in detail.get("landing_points", [])
        ),
    })

    # Be polite: pause briefly so we don't hammer their server
    time.sleep(1)


# -----------------------------
# STEP 4: Save cable data to CSV
# -----------------------------
cables_df = pd.DataFrame(all_cable_data)
cables_df.to_csv("cables_summary.csv", index=False)
print(f"\nSaved {len(cables_df)} cables to cables_summary.csv")


# -----------------------------
# STEP 5: Get landing points (locations) separately
# -----------------------------
print("\nFetching landing points...")
landing_geo = get_json(f"{BASE_URL}/landing-point/landing-point-geo.json")

landing_rows = []
for feature in landing_geo["features"]:
    props = feature["properties"]
    coords = feature["geometry"]["coordinates"]  # [longitude, latitude]
    landing_rows.append({
        "id": props.get("id"),
        "name": props.get("name"),
        "longitude": coords[0],
        "latitude": coords[1],
    })

landing_df = pd.DataFrame(landing_rows)
landing_df.to_csv("landing_points.csv", index=False)
print(f"Saved {len(landing_df)} landing points to landing_points.csv")

print("\nDone! Open the CSV files in Excel or load them into your visualization tool.")

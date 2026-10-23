"""
Step 1a - Download Chicago crime records from the City of Chicago open data portal.

Dataset: "Crimes - 2001 to Present" (Socrata resource id: ijzp-q8t2)
Output : data/raw/chicago_crimes.csv  (date, primary_type, latitude, longitude)

Usage:
    python backend/ml/download_chicago.py            # last 2 years
    python backend/ml/download_chicago.py --years 3

Optional: set SOCRATA_APP_TOKEN in your environment for higher rate limits
(free: https://data.cityofchicago.org/profile/edit/developer_settings).
"""
import argparse
import csv
import os
import time
from datetime import datetime, timedelta
from pathlib import Path

import requests

URL = "https://data.cityofchicago.org/resource/ijzp-q8t2.json"
FIELDS = ["date", "primary_type", "latitude", "longitude"]
PAGE_SIZE = 50_000
OUT = Path(__file__).resolve().parents[2] / "data" / "raw" / "chicago_crimes.csv"


def fetch_page(params, headers, retries=5):
    for attempt in range(retries):
        try:
            r = requests.get(URL, params=params, headers=headers, timeout=120)
            r.raise_for_status()
            return r.json()
        except requests.RequestException as e:
            wait = 2 ** attempt
            print(f"  request failed ({e}); retrying in {wait}s")
            time.sleep(wait)
    raise RuntimeError("Chicago API kept failing. Check your internet and try again.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--years", type=float, default=2.0, help="how many years back to fetch")
    args = ap.parse_args()

    since = (datetime.now() - timedelta(days=int(365 * args.years))).strftime("%Y-%m-%dT00:00:00")
    headers = {}
    token = os.getenv("SOCRATA_APP_TOKEN")
    if token:
        headers["X-App-Token"] = token

    OUT.parent.mkdir(parents=True, exist_ok=True)
    print(f"Downloading Chicago crimes since {since[:10]} ...")

    total, offset = 0, 0
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        while True:
            params = {
                "$select": ",".join(FIELDS),
                "$where": f"date >= '{since}' AND latitude IS NOT NULL AND longitude IS NOT NULL",
                "$order": ":id",
                "$limit": PAGE_SIZE,
                "$offset": offset,
            }
            rows = fetch_page(params, headers)
            if not rows:
                break
            for row in rows:
                writer.writerow({k: row.get(k, "") for k in FIELDS})
            total += len(rows)
            offset += PAGE_SIZE
            print(f"  {total:,} rows")
            if len(rows) < PAGE_SIZE:
                break

    print(f"\nDone. Saved {total:,} rows to {OUT}")


if __name__ == "__main__":
    main()
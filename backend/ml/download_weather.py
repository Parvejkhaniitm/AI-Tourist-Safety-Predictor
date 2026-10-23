"""
Step 2a - Download hourly Chicago weather history from Open-Meteo (free, no key needed).

Output: data/raw/chicago_weather.csv
Usage : python backend/ml/download_weather.py
"""
from datetime import date, timedelta

import pandas as pd
import requests

from common import RAW

URL = "https://archive-api.open-meteo.com/v1/archive"
HOURLY = "temperature_2m,precipitation,snowfall,wind_speed_10m,cloud_cover"


def main():
    start = date(2024, 10, 1)
    end = date.today() - timedelta(days=6)  # the archive lags a few days
    print(f"Downloading hourly weather {start} -> {end} ...")
    r = requests.get(URL, timeout=120, params={
        "latitude": 41.8781, "longitude": -87.6298,
        "start_date": start.isoformat(), "end_date": end.isoformat(),
        "hourly": HOURLY, "timezone": "America/Chicago",
    })
    r.raise_for_status()
    h = r.json()["hourly"]
    df = pd.DataFrame({
        "time": h["time"],
        "temp_c": h["temperature_2m"],
        "precip_mm": h["precipitation"],
        "snowfall_cm": h["snowfall"],
        "wind_kmh": h["wind_speed_10m"],
        "cloud_pct": h["cloud_cover"],
    })
    RAW.mkdir(parents=True, exist_ok=True)
    out = RAW / "chicago_weather.csv"
    df.to_csv(out, index=False)
    print(f"Saved {len(df):,} hourly rows to {out}")
    print(df.describe().round(1).to_string())
    print(f"\nMissing values per column:\n{df.isna().sum().to_string()}")


if __name__ == "__main__":
    main()
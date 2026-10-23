"""
Step 2b - Build the hourly dataset for the "WHEN" model.

One row per hour of the last ~2 years: how much severity-weighted crime happened in
Chicago that hour, plus what the hour looked like (time, holiday, weather, sun height).

Output: data/processed/temporal.parquet
Usage : python backend/ml/build_temporal.py
"""
import pandas as pd
from pandas.tseries.holiday import USFederalHolidayCalendar

from common import RAW, TEMPORAL_FEATURES, load_crimes, solar_elevation, table_path, write_table

LAT, LNG = 41.8781, -87.6298
TZ = "America/Chicago"


def main():
    print("Loading crimes ...")
    df = load_crimes()

    # The newest records are still being reported, so ignore the final 7 days.
    cut = df["date"].max().normalize() - pd.Timedelta(days=7)
    df = df[df["date"] < cut]

    hourly = df.groupby(df["date"].dt.floor("h"))["w"].agg(["sum", "count"])
    hourly.columns = ["severity", "n_crimes"]
    idx = pd.date_range(df["date"].min().floor("D"), cut - pd.Timedelta(hours=1), freq="h")
    hourly = hourly.reindex(idx, fill_value=0)
    hourly.index.name = "time"
    print(f"  {len(hourly):,} hourly rows, avg {hourly['n_crimes'].mean():.1f} crimes/hour")

    # weather
    wx = pd.read_csv(RAW / "chicago_weather.csv", parse_dates=["time"]).set_index("time")
    hourly = hourly.join(wx, how="left")
    before = len(hourly)
    hourly = hourly.dropna(subset=["temp_c", "precip_mm", "wind_kmh"])
    print(f"  dropped {before - len(hourly)} hours with no weather data")
    hourly[["snowfall_cm", "cloud_pct"]] = hourly[["snowfall_cm", "cloud_pct"]].fillna(0)

    # calendar features
    t = hourly.index
    hourly["hour"] = t.hour
    hourly["dow"] = t.day_of_week
    hourly["month"] = t.month
    hourly["is_weekend"] = (t.day_of_week >= 5).astype(int)
    holidays = USFederalHolidayCalendar().holidays(start=t.min(), end=t.max())
    hourly["is_holiday"] = t.normalize().isin(holidays).astype(int)

    # sun height (needs UTC time; the 2 ambiguous daylight-saving hours a year are dropped)
    local = t.tz_localize(TZ, ambiguous="NaT", nonexistent="NaT")
    ok = ~local.isna()
    hourly = hourly[ok]
    hourly["sun_elevation"] = solar_elevation(LAT, LNG, local[ok].tz_convert("UTC")).round(2)

    out = hourly.reset_index()[["time", "severity", "n_crimes"] + TEMPORAL_FEATURES]
    path = table_path("temporal")
    write_table(out, path)
    print(f"\nSaved {len(out):,} rows to {path}")
    print(out.describe().round(1).T.to_string())


if __name__ == "__main__":
    main()
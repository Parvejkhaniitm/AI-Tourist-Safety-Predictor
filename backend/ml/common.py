"""Shared helpers for the SafeRoute AI training pipeline (paths, crime loading, sun position)."""
import os
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
PROC = ROOT / "data" / "processed"
MODELS = Path(__file__).resolve().parent / "models"
EXT = os.getenv("SAFEROUTE_EXT", "parquet")  # set to "csv" only for offline testing

# ~500 m grid cells at Chicago's latitude
LAT_STEP = 0.0045
LNG_STEP = 0.0060
LAT_MIN, LAT_MAX = 41.60, 42.05
LNG_MIN, LNG_MAX = -87.95, -87.50

SEVERITY = {
    "HOMICIDE": 10, "CRIMINAL SEXUAL ASSAULT": 9, "KIDNAPPING": 8, "HUMAN TRAFFICKING": 8,
    "ROBBERY": 7, "WEAPONS VIOLATION": 6, "OFFENSE INVOLVING CHILDREN": 6, "ASSAULT": 5,
    "BATTERY": 5, "ARSON": 5, "SEX OFFENSE": 5, "BURGLARY": 4, "INTIMIDATION": 4,
    "STALKING": 4, "THEFT": 3, "MOTOR VEHICLE THEFT": 3, "CRIMINAL DAMAGE": 2,
    "CRIMINAL TRESPASS": 2, "NARCOTICS": 2, "PUBLIC PEACE VIOLATION": 2, "DECEPTIVE PRACTICE": 1,
}
DEFAULT_WEIGHT = 1

# Inputs of the "when" model. The live API must produce exactly these.
TEMPORAL_FEATURES = [
    "hour", "dow", "is_weekend", "is_holiday",
    "temp_c", "precip_mm", "snowfall_cm", "wind_kmh", "cloud_pct", "sun_elevation",
]


def table_path(name):
    return PROC / f"{name}.{EXT}"


def write_table(df, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix == ".csv":
        df.to_csv(path, index=False)
    else:
        df.to_parquet(path, index=False)


def read_table(path):
    return pd.read_csv(path) if path.suffix == ".csv" else pd.read_parquet(path)


def load_crimes(path=None, verbose=True):
    """Load and clean the raw Chicago crimes. Adds a severity weight column 'w'."""
    path = path or (RAW / "chicago_crimes.csv")
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date", "latitude", "longitude"])
    df = df[df["latitude"].between(LAT_MIN, LAT_MAX) & df["longitude"].between(LNG_MIN, LNG_MAX)]
    if verbose:
        print(f"  {len(df):,} usable rows, {df['date'].min().date()} -> {df['date'].max().date()}")

    # Chicago stamps records with an unknown time as exactly 00:00:00 or 12:00:00.
    # Keeping them would create fake spikes at those hours, so drop them.
    secs = df["date"].dt.hour * 3600 + df["date"].dt.minute * 60 + df["date"].dt.second
    placeholder = (secs == 0) | (secs == 12 * 3600)
    if verbose:
        print(f"  dropping {placeholder.mean():.1%} of rows with placeholder times (00:00:00 / 12:00:00)")
    df = df[~placeholder].copy()
    df["w"] = df["primary_type"].str.upper().map(SEVERITY).fillna(DEFAULT_WEIGHT)
    return df


def solar_elevation(lat, lng, times_utc):
    """Sun height above the horizon in degrees (NOAA formula). Works for any place on Earth.
    times_utc: pandas DatetimeIndex in UTC (tz-aware or naive-UTC). Negative = night."""
    t = pd.DatetimeIndex(times_utc)
    hours = t.hour.to_numpy() + t.minute.to_numpy() / 60.0
    g = 2 * np.pi / 365 * (t.dayofyear.to_numpy() - 1 + (hours - 12) / 24)
    eqtime = 229.18 * (0.000075 + 0.001868 * np.cos(g) - 0.032077 * np.sin(g)
                       - 0.014615 * np.cos(2 * g) - 0.040849 * np.sin(2 * g))
    decl = (0.006918 - 0.399912 * np.cos(g) + 0.070257 * np.sin(g) - 0.006758 * np.cos(2 * g)
            + 0.000907 * np.sin(2 * g) - 0.002697 * np.cos(3 * g) + 0.00148 * np.sin(3 * g))
    tst = hours * 60 + eqtime + 4 * lng          # true solar time in minutes
    ha = np.radians(tst / 4 - 180)
    lat_r = np.radians(lat)
    sin_el = np.sin(lat_r) * np.sin(decl) + np.cos(lat_r) * np.cos(decl) * np.cos(ha)
    return np.degrees(np.arcsin(np.clip(sin_el, -1, 1)))


def to_baseline_score(bundle, raw_pred):
    """Convert the spatial model's raw output into a 0-100 baseline score.
    The raw output is bunched near the average, so we rank it against the model's honest
    (never-seen-neighbourhood) predictions on Chicago cells: top 30% of Chicago -> 70-100."""
    ref = bundle["oof_sorted"]
    x = np.asarray(raw_pred, dtype=float)
    # average of "how many below" and "how many at or below" so tied values land mid-rank
    pos = (np.searchsorted(ref, x, side="left") + np.searchsorted(ref, x, side="right")) / 2
    return np.clip(pos / len(ref) * 100.0, 0, 100)
"""
Step 1b - Turn raw Chicago crimes into risk labels (0-100) per map cell and hour-of-week.

Score = percentile of severity-weighted incidents per week, so a 70 means
"riskier than ~70% of Chicago cell-hours" (a RELATIVE score).

Output: data/processed/chicago_labels.parquet
Usage : python backend/ml/build_labels.py [--min-crimes 25]
"""
import argparse

import numpy as np
import pandas as pd

from common import LAT_STEP, LNG_STEP, load_crimes, table_path, write_table


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-crimes", type=int, default=25,
                    help="drop cells with fewer total crimes than this")
    args = ap.parse_args()

    print("Loading crimes ...")
    df = load_crimes()

    df["ci"] = np.floor(df["latitude"] / LAT_STEP).astype(int)
    df["cj"] = np.floor(df["longitude"] / LNG_STEP).astype(int)
    df["how"] = df["date"].dt.day_of_week * 24 + df["date"].dt.hour  # 0..167

    cell_key = df["ci"].astype(str) + "_" + df["cj"].astype(str)
    cell_codes, cell_names = pd.factorize(cell_key)
    n_cells = len(cell_names)

    sums = np.zeros((n_cells, 168))
    np.add.at(sums, (cell_codes, df["how"].to_numpy()), df["w"].to_numpy())
    counts = np.bincount(cell_codes, minlength=n_cells)

    n_weeks = max((df["date"].max() - df["date"].min()).days / 7, 1.0)
    rate = sums / n_weeks
    rate = (np.roll(rate, 1, axis=1) + rate + np.roll(rate, -1, axis=1)) / 3  # smooth +/- 1 hour

    keep = counts >= args.min_crimes
    print(f"  {n_cells:,} cells found, keeping {keep.sum():,} with >= {args.min_crimes} crimes")
    if keep.sum() == 0:
        raise SystemExit("No cells left. Lower --min-crimes or download more data.")
    rate, kept_names, kept_counts = rate[keep], np.asarray(cell_names)[keep], counts[keep]

    flat = np.log1p(rate).ravel()
    score = (flat.argsort().argsort() / (len(flat) - 1) * 100).reshape(rate.shape)

    ci = np.array([int(n.split("_")[0]) for n in kept_names])
    cj = np.array([int(n.split("_")[1]) for n in kept_names])
    out = pd.DataFrame({
        "cell_id": np.repeat(kept_names, 168),
        "lat": np.repeat((ci + 0.5) * LAT_STEP, 168),
        "lng": np.repeat((cj + 0.5) * LNG_STEP, 168),
        "total_crimes": np.repeat(kept_counts, 168),
        "dow": np.tile(np.repeat(np.arange(7), 24), len(kept_names)),
        "hour": np.tile(np.tile(np.arange(24), 7), len(kept_names)),
        "raw_rate": rate.ravel(),
        "risk_label": score.ravel(),
    })
    out["is_weekend"] = (out["dow"] >= 5).astype(int)

    path = table_path("chicago_labels")
    write_table(out, path)

    print(f"\nSaved {len(out):,} rows ({len(kept_names):,} cells x 168 hours) to {path}")
    print("\nAverage label by hour of day:")
    print(out.groupby("hour")["risk_label"].mean().round(1).to_string())
    cell_avg = out.groupby(["cell_id", "lat", "lng"])["risk_label"].mean().sort_values(ascending=False)
    print("\nTop 5 riskiest cells (lat, lng, avg label):")
    print(cell_avg.head(5).round(1).to_string())


if __name__ == "__main__":
    main()
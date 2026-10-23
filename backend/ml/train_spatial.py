"""
Step 3b - Train the "WHERE" model: baseline risk of a place from what is around it.

Input : counts of nearby bars, shops, stations, parks, ... (location-independent, so it
        can be applied outside Chicago). Latitude/longitude are deliberately NOT used.
Target: each cell's average risk score over the week (0-100).

Honest testing: cells are grouped into ~2 km blocks and whole blocks are held out, so the
model is always scored on neighbourhoods it has never seen. XGBoost and Random Forest are
compared and the better one is kept.

Output: backend/ml/models/spatial_model.joblib
Usage : python backend/ml/train_spatial.py
"""
import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest, RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import GroupKFold
from xgboost import XGBRegressor

from common import MODELS, read_table, table_path, to_baseline_score
from osm_features import FEATURE_COLUMNS


def make_models():
    return {
        "XGBoost": lambda: XGBRegressor(n_estimators=300, learning_rate=0.05, max_depth=4,
                                        subsample=0.8, colsample_bytree=0.8,
                                        random_state=42, n_jobs=-1),
        "RandomForest": lambda: RandomForestRegressor(n_estimators=300, min_samples_leaf=3,
                                                      random_state=42, n_jobs=-1),
    }


def main():
    labels = read_table(table_path("chicago_labels"))
    feats = read_table(table_path("cell_features"))
    target = labels.groupby("cell_id")["risk_label"].mean().rename("baseline")
    data = feats.merge(target, on="cell_id").reset_index(drop=True)
    X, y = data[FEATURE_COLUMNS], data["baseline"]
    groups = (np.floor(data["lat"] / 0.02).astype(int).astype(str) + "_"
              + np.floor(data["lng"] / 0.02).astype(int).astype(str))
    print(f"{len(data):,} cells, {groups.nunique()} neighbourhood blocks, "
          f"target range {y.min():.0f}-{y.max():.0f}")

    cv = GroupKFold(n_splits=5)
    results, oof_all = {}, {}
    oof_mean = np.zeros(len(data))
    for tr, te in cv.split(X, y, groups):
        oof_mean[te] = y.iloc[tr].mean()
    results["Always guess the average"] = (mean_absolute_error(y, oof_mean), r2_score(y, oof_mean))

    for name, make in make_models().items():
        oof = np.zeros(len(data))
        for tr, te in cv.split(X, y, groups):
            m = make()
            m.fit(X.iloc[tr], y.iloc[tr])
            oof[te] = m.predict(X.iloc[te])
        oof_all[name] = oof
        results[name] = (mean_absolute_error(y, oof), r2_score(y, oof))

    print("\nResults on neighbourhoods the model has never seen (lower MAE / higher R2 is better):")
    for name, (mae, r2) in results.items():
        print(f"  {name:<26} MAE={mae:5.2f} points   R2={r2:.3f}")

    best = min(make_models(), key=lambda n: results[n][0])
    print(f"\nBest: {best}")
    model = make_models()[best]()
    model.fit(X, y)

    if hasattr(model, "feature_importances_"):
        imp = pd.Series(model.feature_importances_, index=FEATURE_COLUMNS).sort_values(ascending=False)
        print("\nWhat the model relies on most:")
        print(imp.round(3).to_string())

    oof_sorted = np.sort(oof_all[best])
    p5, p95 = np.percentile(oof_all[best], [5, 95])
    print(f"\nRaw predictions are bunched: 90% of cells fall between {p5:.0f} and {p95:.0f} "
          f"(true range {y.min():.0f}-{y.max():.0f}).")
    cal = to_baseline_score({"oof_sorted": oof_sorted}, oof_all[best])
    share = pd.cut(pd.Series(cal), [-0.1, 39.99, 69.99, 100], labels=["Safe", "Moderate", "Risky"])
    print("After rank calibration, baseline bands: "
          + ", ".join(f"{k} {v:.0%}" for k, v in share.value_counts(normalize=True).items()))

    iso = IsolationForest(n_estimators=200, random_state=42).fit(X)  # flags unusual places

    cells = (labels.groupby("cell_id")
             .agg(lat=("lat", "first"), lng=("lng", "first"),
                  label=("risk_label", "mean"), total_crimes=("total_crimes", "first"))
             .reset_index(drop=True))

    MODELS.mkdir(parents=True, exist_ok=True)
    out = MODELS / "spatial_model.joblib"
    joblib.dump({
        "model": model, "name": best, "features": FEATURE_COLUMNS, "isolation": iso,
        "q01": X.quantile(0.01).to_dict(), "q99": X.quantile(0.99).to_dict(),
        "cv_mae": float(results[best][0]), "cv_r2": float(results[best][1]),
        "baseline_mean": float(y.mean()), "oof_sorted": oof_sorted,
        "median": X.median().to_dict(), "cells": cells,
    }, out)
    print(f"\nSaved {out}")


if __name__ == "__main__":
    main()
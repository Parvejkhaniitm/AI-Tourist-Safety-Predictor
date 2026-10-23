"""
Step 2c - Train the "WHEN" model: how does risk change with hour, weekday, holidays,
weather and daylight?

It predicts the (log) amount of severity-weighted crime in Chicago for a given hour.
We test it on the most recent 90 days it never saw, and compare it to a simple
"average for that hour of the week" guess to prove weather/daylight add real value.

It also learns a conversion: how many 0-100 score points one unit of this model's output is worth,
so the final score can be: place baseline + time adjustment.

Output: backend/ml/models/temporal_model.joblib
Usage : python backend/ml/train_temporal.py
"""
import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, r2_score
from xgboost import XGBRegressor

from common import MODELS, TEMPORAL_FEATURES, read_table, table_path

TEST_DAYS = 90


def main():
    df = read_table(table_path("temporal"))
    df["time"] = pd.to_datetime(df["time"])
    df["y"] = np.log1p(df["severity"])
    df["how"] = df["dow"] * 24 + df["hour"]

    cutoff = df["time"].max() - pd.Timedelta(days=TEST_DAYS)
    train, test = df[df["time"] <= cutoff], df[df["time"] > cutoff]
    print(f"Train: {len(train):,} hours   Test (newest {TEST_DAYS} days): {len(test):,} hours")

    # ---- simple baseline: average per hour-of-week ----
    how_mean = train.groupby("how")["y"].mean()
    base_pred = test["how"].map(how_mean).fillna(train["y"].mean())

    # ---- the model ----
    model = XGBRegressor(n_estimators=400, learning_rate=0.05, max_depth=4,
                         subsample=0.8, colsample_bytree=0.8, random_state=42, n_jobs=-1)
    model.fit(train[TEMPORAL_FEATURES], train["y"])
    pred = model.predict(test[TEMPORAL_FEATURES])

    def report(name, p):
        print(f"  {name:<28} MAE={mean_absolute_error(test['y'], p):.3f}   R2={r2_score(test['y'], p):.3f}")
    print("\nResults on unseen recent data (lower MAE / higher R2 is better):")
    report("Always guess the average", np.full(len(test), train["y"].mean()))
    report("Average per hour-of-week", base_pred)
    report("XGBoost model", pred)
    gain = 1 - mean_absolute_error(test["y"], pred) / mean_absolute_error(test["y"], base_pred)
    print(f"\n  Model vs hour-of-week baseline: {gain:+.1%} error change"
          f" ({'weather/daylight help' if gain > 0 else 'no gain from extra features'})")

    if hasattr(model, "feature_importances_"):
        imp = pd.Series(model.feature_importances_, index=TEMPORAL_FEATURES).sort_values(ascending=False)
        print("\nWhat the model relies on most:")
        print(imp.round(3).to_string())

    # ---- calibration: model units -> score points, using the labels from build_labels.py ----
    labels = read_table(table_path("chicago_labels"))
    label_how = labels.groupby(["dow", "hour"])["risk_label"].mean().reset_index()
    label_how["how"] = label_how["dow"] * 24 + label_how["hour"]
    label_how = label_how.set_index("how")["risk_label"].sort_index()
    train_pred = pd.Series(model.predict(train[TEMPORAL_FEATURES]), index=train.index)
    pred_how = train_pred.groupby(train["how"]).mean().reindex(range(168))
    scale = float(np.polyfit(pred_how.to_numpy(), label_how.reindex(range(168)).to_numpy(), 1)[0])
    ref = float(train_pred.mean())
    if not np.isfinite(scale) or scale <= 0:
        raise SystemExit("Calibration failed (check build_labels output).")
    effect = scale * (pred_how - ref)
    print(f"\nCalibration: 1 model unit = {scale:.1f} score points")
    print(f"Time-of-week effect ranges from {effect.min():+.1f} to {effect.max():+.1f} score points")

    MODELS.mkdir(parents=True, exist_ok=True)
    out = MODELS / "temporal_model.joblib"
    joblib.dump({
        "model": model, "features": TEMPORAL_FEATURES, "ref_log": ref, "scale": scale,
        "background": train[TEMPORAL_FEATURES].sample(300, random_state=0).reset_index(drop=True),
        "feature_median": train[TEMPORAL_FEATURES].median().to_dict(),
        "metrics": {"mae": float(mean_absolute_error(test["y"], pred)),
                    "r2": float(r2_score(test["y"], pred)),
                    "baseline_mae": float(mean_absolute_error(test["y"], base_pred))},
    }, out)
    print(f"\nSaved {out}")


if __name__ == "__main__":
    main()
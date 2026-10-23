"""Risk scoring boundary. Replace baseline with a validated, versioned model artifact."""
from datetime import datetime, timezone


def score(factors):
    available = [item for item in factors if item.get("available")]
    # Neutral baseline keeps the API usable before real, calibrated features exist.
    # It is deliberately not presented as a trained or reliable safety prediction.
    value = 50
    confidence = round(len(available) / max(len(factors), 1), 2)
    reasons = ["This is a baseline estimate; verified live safety feeds are not configured."]
    return {"score": value, "confidence": confidence, "reasons": reasons,
            "analyzedAt": datetime.now(timezone.utc).isoformat(), "modelVersion": "baseline-v1"}

import re
from datetime import datetime, timezone

from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import (create_access_token, create_refresh_token,
                                get_jwt, get_jwt_identity, verify_jwt_in_request, jwt_required)
from sqlalchemy import func

from . import db, jwt
from .models import Analysis, Destination, RevokedToken, User
from .scoring import score

api = Blueprint("api", __name__)


@jwt.token_in_blocklist_loader
def token_revoked(_header, payload):
    return RevokedToken.query.filter_by(jti=payload["jti"]).first() is not None


def error(code, message, status):
    return jsonify({"error": {"code": code, "message": message}}), status


@api.get("/destinations")
def destinations():
    query = str(request.args.get("q", "")).strip()
    rows = Destination.query.filter_by(active=True)
    if query:
        rows = rows.filter(Destination.name.ilike(f"%{query[:80]}%"))
    return jsonify([row.name for row in rows.order_by(Destination.name).limit(20).all()])


@api.post("/auth/register")
def register():
    body = request.get_json(silent=True) or {}
    email = str(body.get("email", "")).strip().lower()
    password = str(body.get("password", ""))
    if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email) or len(password) < 10:
        return error("BAD_REQUEST", "Enter a valid email and a password of at least 10 characters.", 400)
    if User.query.filter(func.lower(User.email) == email).first():
        return error("CONFLICT", "An account with this email already exists.", 409)
    user = User(email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    identity = str(user.id)
    return jsonify({"accessToken": create_access_token(identity), "refreshToken": create_refresh_token(identity), "user": {"id": identity, "email": email}}), 201


@api.post("/auth/login")
def login():
    body = request.get_json(silent=True) or {}
    email = str(body.get("email", "")).strip().lower()
    user = User.query.filter(func.lower(User.email) == email).first()
    if not user or not user.check_password(str(body.get("password", ""))):
        return error("UNAUTHORIZED", "Email or password is incorrect.", 401)
    identity = str(user.id)
    return jsonify({"accessToken": create_access_token(identity), "refreshToken": create_refresh_token(identity), "user": {"id": identity, "email": user.email}})


@api.post("/auth/refresh")
@jwt_required(refresh=True)
def refresh():
    return jsonify({"accessToken": create_access_token(get_jwt_identity())})


@api.post("/auth/logout")
@jwt_required(verify_type=False)
def logout():
    db.session.add(RevokedToken(jti=get_jwt()["jti"]))
    db.session.commit()
    return "", 204


@api.post("/analyze")
def analyze():
    verify_jwt_in_request(optional=True)
    body = request.get_json(silent=True) or {}
    name = str(body.get("destination", "")).strip()
    if len(name) < 2 or len(name) > 180:
        return error("BAD_REQUEST", "destination must be between 2 and 180 characters.", 400)
    destination = Destination.query.filter_by(active=True).filter(func.lower(Destination.name) == name.lower()).first()
    if not destination:
        return error("NOT_FOUND", "Destination not found.", 404)

    factors = build_factors(destination)
    prediction = score(factors)
    identity = get_jwt_identity()
    record = Analysis(destination_id=destination.id, user_id=int(identity) if identity else None,
                      score=prediction["score"], confidence=prediction["confidence"],
                      factors_json=factors, reasons_json=prediction["reasons"],
                      model_version=prediction["modelVersion"])
    db.session.add(record)
    db.session.commit()
    return jsonify({"destination": destination.name, "location": destination.label,
                    "score": prediction["score"], "confidence": prediction["confidence"],
                    "analyzedAt": prediction["analyzedAt"], "factors": factors,
                    "reasons": prediction["reasons"], "analysisId": record.id,
                    "modelVersion": prediction["modelVersion"]})


def build_factors(destination):
    now = datetime.now(timezone.utc)
    daylight = 6 <= now.hour < 18
    factors = [
        {"key": "location", "title": "Location", "text": "Destination location is available; local area safety data is not configured.", "impact": "neutral", "impactLabel": "Not scored", "dataLabel": "Geocoded location", "available": True},
        {"key": "time", "title": "Time and Day", "text": f"{now.strftime('%A, %I:%M %p UTC')}. {'Daylight hours.' if daylight else 'After dark.'}", "impact": "neutral", "impactLabel": "Not scored", "dataLabel": "Analysis time", "available": True, "daylight": daylight},
        {"key": "crowd", "title": "Crowd Density", "text": "Crowd feed is not configured.", "impact": "neutral", "impactLabel": "Not included", "dataLabel": "Unavailable", "available": False},
        {"key": "weather", "title": "Weather", "text": "Weather feed is not configured.", "impact": "neutral", "impactLabel": "Not included", "dataLabel": "Unavailable", "available": False},
        {"key": "incidents", "title": "Historical Incidents", "text": "Verified incident feed is not configured.", "impact": "neutral", "impactLabel": "Not included", "dataLabel": "Unavailable", "available": False},
    ]
    return factors


@api.get("/routes")
def routes():
    name = str(request.args.get("destination", "")).strip()
    start = str(request.args.get("start", "")).strip()
    if len(name) < 2 or len(name) > 180 or len(start) > 180:
        return error("BAD_REQUEST", "A valid destination and optional start are required.", 400)
    destination = Destination.query.filter_by(active=True).filter(func.lower(Destination.name) == name.lower()).first()
    if not destination:
        return error("NOT_FOUND", "Destination not found.", 404)
    # Until a directions provider is configured, return a clear unavailable result
    # rather than inventing distances, times, or safety scores.
    return jsonify({"destination": destination.name, "start": start or "Starting point not provided",
                    "destinationLabel": destination.label, "shortest": None, "safer": None,
                    "available": False, "message": "Route provider is not configured."}), 503


@api.get("/history")
@jwt_required()
def history():
    user_id = int(get_jwt_identity())
    records = Analysis.query.filter_by(user_id=user_id).order_by(Analysis.data_as_of.desc()).limit(50).all()
    return jsonify([{"id": item.id, "destination": item.destination.name, "score": item.score,
                     "analyzedAt": item.data_as_of.isoformat(), "confidence": item.confidence}
                    for item in records])


@api.errorhandler(500)
def internal_error(_exc):
    db.session.rollback()
    current_app.logger.exception("Unhandled API exception")
    return error("SERVER_ERROR", "An unexpected server error occurred.", 500)

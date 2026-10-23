from datetime import datetime, timezone

from werkzeug.security import check_password_hash, generate_password_hash

from . import db


def utcnow():
    return datetime.now(timezone.utc)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(254), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
    analyses = db.relationship("Analysis", back_populates="user", lazy="dynamic")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Destination(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(180), unique=True, nullable=False, index=True)
    label = db.Column(db.String(240), nullable=False)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    active = db.Column(db.Boolean, default=True, nullable=False)


class Analysis(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True, index=True)
    destination_id = db.Column(db.Integer, db.ForeignKey("destination.id"), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    confidence = db.Column(db.Float, nullable=False)
    factors_json = db.Column(db.JSON, nullable=False)
    reasons_json = db.Column(db.JSON, nullable=False)
    data_as_of = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)
    model_version = db.Column(db.String(80), nullable=False, default="baseline-v1")
    user = db.relationship("User", back_populates="analyses")
    destination = db.relationship("Destination")


class Incident(db.Model):
    """Curated, aggregated incident observations; avoid storing identifiable victim data."""
    id = db.Column(db.Integer, primary_key=True)
    destination_id = db.Column(db.Integer, db.ForeignKey("destination.id"), nullable=False, index=True)
    category = db.Column(db.String(80), nullable=False)
    severity = db.Column(db.Integer, nullable=False)
    occurred_at = db.Column(db.DateTime(timezone=True), nullable=False, index=True)
    source = db.Column(db.String(120), nullable=False)
    verified = db.Column(db.Boolean, default=False, nullable=False)


class RevokedToken(db.Model):
    jti = db.Column(db.String(36), primary_key=True)
    revoked_at = db.Column(db.DateTime(timezone=True), default=utcnow, nullable=False)

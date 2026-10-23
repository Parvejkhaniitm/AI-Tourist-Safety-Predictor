import os

from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
jwt = JWTManager()
migrate = Migrate()


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=os.getenv("SECRET_KEY", "dev-only-change-me"),
        JWT_SECRET_KEY=os.getenv("JWT_SECRET_KEY", "dev-only-change-me-too"),
        JWT_ACCESS_TOKEN_EXPIRES=int(os.getenv("JWT_ACCESS_TOKEN_MINUTES", "30")) * 60,
        JWT_REFRESH_TOKEN_EXPIRES=int(os.getenv("JWT_REFRESH_TOKEN_DAYS", "14")) * 86400,
        SQLALCHEMY_DATABASE_URI=os.getenv("DATABASE_URL", "sqlite:///saferoute.db"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        DEMO_DATA=os.getenv("DEMO_DATA", "true").lower() == "true",
    )
    if test_config:
        app.config.update(test_config)

    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)
    origins = [value.strip() for value in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")]
    CORS(app, resources={r"/api/*": {"origins": origins}})

    from .routes import api
    app.register_blueprint(api, url_prefix="/api")

    @app.get("/health")
    def health():
        return {"status": "ok", "service": "saferoute-api"}

    with app.app_context():
        # Creates the starter schema for local use; Flask-Migrate owns later changes.
        db.create_all()
        if app.config["DEMO_DATA"]:
            from .seed import seed_destinations
            seed_destinations()

    return app

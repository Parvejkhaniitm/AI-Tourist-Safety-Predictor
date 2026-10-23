from . import db
from .models import Destination

DEMO_DESTINATIONS = [
    ("India Gate", "India Gate, New Delhi", 28.6129, 77.2295),
    ("Red Fort", "Red Fort, Old Delhi", 28.6562, 77.2410),
    ("Qutub Minar", "Qutub Minar, New Delhi", 28.5245, 77.1855),
    ("Humayun's Tomb", "Humayun's Tomb, Nizamuddin, New Delhi", 28.5933, 77.2507),
    ("Lotus Temple", "Lotus Temple, Kalkaji, New Delhi", 28.5535, 77.2588),
]


def seed_destinations():
    for name, label, lat, lon in DEMO_DESTINATIONS:
        if not Destination.query.filter_by(name=name).first():
            db.session.add(Destination(name=name, label=label, latitude=lat, longitude=lon))
    db.session.commit()

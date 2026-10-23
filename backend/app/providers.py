"""Replace these adapters with licensed, configured data providers when available."""
from datetime import datetime, timezone


class DemoDataProvider:
    """Transparent local fixture provider; every returned value is marked illustrative."""
    def weather(self, destination):
        return None  # Unknown weather must be omitted, never fabricated.

    def crowd(self, destination):
        return None

    def incidents(self, destination):
        return None

    def location(self, destination):
        return {"text": "Geocoded destination; local area profile is not configured.", "impact": "neutral", "dataLabel": "Location only", "available": True}

    def routes(self, start, destination):
        return None


def utc_iso(value=None):
    return (value or datetime.now(timezone.utc)).isoformat()

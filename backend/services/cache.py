"""Tiny in-memory cache with expiry, so repeated requests don't hammer free APIs."""
import time


class TTLCache:
    def __init__(self, ttl=900, maxsize=500):
        self.ttl, self.maxsize, self._d = ttl, maxsize, {}

    def get(self, key):
        item = self._d.get(key)
        if item and item[0] > time.time():
            return item[1]
        self._d.pop(key, None)
        return None

    def set(self, key, value):
        if len(self._d) >= self.maxsize:
            self._d.pop(next(iter(self._d)))
        self._d[key] = (time.time() + self.ttl, value)
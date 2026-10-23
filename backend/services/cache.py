"""TTL cache with Redis backing and a bounded per-process fallback.

Set REDIS_URL to share cache entries between Flask workers/restarts. If Redis is
not configured, its client is missing, or it becomes unavailable, calls remain
available using the in-memory cache. Values are JSON only; never use this cache
for secrets or arbitrary Python objects.
"""
import hashlib
import json
import logging
import os
import threading
import time

log = logging.getLogger("saferoute.cache")
_redis_client = None
_redis_import_error = False
_redis_retry_after = 0.0
_redis_lock = threading.Lock()


def _redis():
    """Get a connected Redis client, retrying unavailable Redis periodically."""
    global _redis_client, _redis_import_error, _redis_retry_after
    url = os.getenv("REDIS_URL", "").strip()
    if not url or time.monotonic() < _redis_retry_after:
        return None
    if _redis_client is not None:
        return _redis_client

    with _redis_lock:
        if _redis_client is not None:
            return _redis_client
        if time.monotonic() < _redis_retry_after:
            return None
        try:
            import redis

            client = redis.Redis.from_url(
                url,
                decode_responses=True,
                socket_connect_timeout=0.25,
                socket_timeout=0.25,
                health_check_interval=30,
            )
            client.ping()
            _redis_client = client
            _redis_import_error = False
            log.info("Redis cache connected.")
            return client
        except ImportError:
            if not _redis_import_error:
                log.warning("REDIS_URL is set but redis-py is not installed; using memory cache.")
                _redis_import_error = True
        except Exception as exc:  # Redis is an optimization, not an app dependency.
            log.warning("Redis cache unavailable (%s); using memory cache.", type(exc).__name__)
        _redis_retry_after = time.monotonic() + 5
        return None


def cache_backend():
    """Return the active cache backend without exposing connection details."""
    return "redis" if _redis() is not None else "memory"


class TTLCache:
    def __init__(self, ttl=900, maxsize=500, namespace="default"):
        self.ttl = int(ttl)
        self.maxsize = int(maxsize)
        self.namespace = namespace
        self._d = {}
        self._lock = threading.Lock()

    def _key(self, key):
        # Hash keys so search text / coordinates are not readable in Redis key names.
        payload = json.dumps(key, sort_keys=True, separators=(",", ":"), default=str)
        digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        return f"saferoute:{self.namespace}:{digest}"

    def get(self, key):
        redis_client = _redis()
        if redis_client is not None:
            try:
                cached = redis_client.get(self._key(key))
                if cached is not None:
                    value = json.loads(cached)
                    self._remember(key, value)
                    return value
            except Exception as exc:
                self._redis_failed(exc)

        with self._lock:
            item = self._d.get(key)
            if item and item[0] > time.monotonic():
                return item[1]
            self._d.pop(key, None)
            return None

    def set(self, key, value):
        self._remember(key, value)
        redis_client = _redis()
        if redis_client is None:
            return
        try:
            redis_client.set(self._key(key), json.dumps(value, separators=(",", ":"), default=str), ex=self.ttl)
        except Exception as exc:
            self._redis_failed(exc)

    def _remember(self, key, value):
        with self._lock:
            if key not in self._d and len(self._d) >= self.maxsize:
                self._d.pop(next(iter(self._d)))
            self._d[key] = (time.monotonic() + self.ttl, value)

    @staticmethod
    def _redis_failed(exc):
        global _redis_client, _redis_retry_after
        with _redis_lock:
            _redis_client = None
            _redis_retry_after = time.monotonic() + 5
        log.warning("Redis cache operation failed (%s); using memory cache.", type(exc).__name__)

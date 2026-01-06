"""
In-memory cache service for alerts
Provides thread-safe LRU caching with statistics tracking
"""

from typing import Optional, Dict, Any
from collections import OrderedDict
from threading import RLock
import logging

from app.models import Alert

logger = logging.getLogger(__name__)


class CacheService:
    """
    Thread-safe in-memory LRU cache for alerts
    """

    def __init__(self, max_size: int = 10000):
        self.max_size = max_size
        self._cache: OrderedDict[str, Alert] = OrderedDict()
        self._lock = RLock()

        # Statistics
        self._hits = 0
        self._misses = 0
        self._evictions = 0
        self._overwrites = 0

        logger.info(f"CacheService initialized (max_size={max_size})")

    # ------------------------------------------------------------------
    # CORE OPERATIONS
    # ------------------------------------------------------------------

    def put(self, key: str, value: Alert) -> None:
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                self._overwrites += 1

            self._cache[key] = value

            if len(self._cache) > self.max_size:
                self._cache.popitem(last=False)
                self._evictions += 1

    def get(self, key: str) -> Optional[Alert]:
        with self._lock:
            if key not in self._cache:
                self._misses += 1
                return None

            self._cache.move_to_end(key)
            self._hits += 1
            return self._cache[key]

    def delete(self, key: str) -> bool:
        with self._lock:
            return self._cache.pop(key, None) is not None

    def clear(self) -> None:
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            self.reset_stats()
            logger.info(f"Cache cleared ({count} alerts removed)")

    # ------------------------------------------------------------------
    # METRICS
    # ------------------------------------------------------------------

    def size(self) -> int:
        with self._lock:
            return len(self._cache)

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            total = self._hits + self._misses
            hit_rate = (self._hits / total * 100) if total else 0.0

            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "hits": self._hits,
                "misses": self._misses,
                "evictions": self._evictions,
                "overwrites": self._overwrites,
                "hit_rate": round(hit_rate, 2),
                "total_requests": total,
            }

    def reset_stats(self) -> None:
        self._hits = 0
        self._misses = 0
        self._evictions = 0
        self._overwrites = 0

    # ------------------------------------------------------------------
    # HELPERS
    # ------------------------------------------------------------------

    def get_all_keys(self) -> list[str]:
        with self._lock:
            return list(self._cache.keys())

    def contains(self, key: str) -> bool:
        with self._lock:
            return key in self._cache

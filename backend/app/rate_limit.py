"""Single-instance token-bucket rate limiter.

Single-instance only — replace with Redis if running > 1 process.
"""

from __future__ import annotations

import math
import time
from collections import defaultdict
from threading import Lock

from .limits import RATE_LIMIT_PER_MINUTE


_WINDOW_SECONDS = 60.0


class TokenBucket:
    def __init__(self, capacity: int, refill_per_second: float) -> None:
        self.capacity = float(capacity)
        self.refill = refill_per_second
        self.tokens = float(capacity)
        self.last_refill = time.monotonic()
        self._lock = Lock()

    def consume(self, amount: float = 1.0) -> tuple[bool, int]:
        with self._lock:
            now = time.monotonic()
            elapsed = now - self.last_refill
            self.tokens = min(self.capacity, self.tokens + elapsed * self.refill)
            self.last_refill = now
            if self.tokens >= amount:
                self.tokens -= amount
                return True, 0
            shortfall = amount - self.tokens
            retry_after = math.ceil(shortfall / self.refill) if self.refill > 0 else 60
            return False, max(1, retry_after)


class RateLimiter:
    def __init__(self, per_minute: int) -> None:
        self.per_minute = per_minute
        self.refill_per_second = per_minute / _WINDOW_SECONDS
        self._buckets: dict[str, TokenBucket] = defaultdict(self._new_bucket)
        self._lock = Lock()

    def _new_bucket(self) -> TokenBucket:
        return TokenBucket(self.per_minute, self.refill_per_second)

    def check(self, key: str) -> tuple[bool, int]:
        with self._lock:
            bucket = self._buckets[key]
        return bucket.consume(1.0)

    def reset(self) -> None:
        with self._lock:
            self._buckets.clear()


rate_limiter = RateLimiter(RATE_LIMIT_PER_MINUTE)

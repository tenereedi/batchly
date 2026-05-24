"""Rate limiting support for job queues."""

import time
from collections import deque
from threading import Lock


class RateLimitExceeded(Exception):
    """Raised when the rate limit has been exceeded."""
    pass


class RateLimiter:
    """Token bucket / sliding window rate limiter.

    Allows at most *max_calls* calls within every *period* seconds.
    """

    def __init__(self, max_calls: int, period: float = 1.0):
        if max_calls <= 0:
            raise ValueError("max_calls must be a positive integer")
        if period <= 0:
            raise ValueError("period must be a positive number")
        self.max_calls = max_calls
        self.period = period
        self._timestamps: deque = deque()
        self._lock = Lock()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def acquire(self, block: bool = True) -> bool:
        """Try to acquire a rate-limit slot.

        If *block* is True (default) the call sleeps until a slot is
        available.  If *block* is False it returns False immediately when
        the limit is exceeded.
        """
        while True:
            with self._lock:
                now = time.monotonic()
                self._evict(now)
                if len(self._timestamps) < self.max_calls:
                    self._timestamps.append(now)
                    return True
                wait_for = self.period - (now - self._timestamps[0])

            if not block:
                return False
            time.sleep(max(wait_for, 0))

    def is_allowed(self) -> bool:
        """Non-blocking check – does not consume a slot."""
        with self._lock:
            self._evict(time.monotonic())
            return len(self._timestamps) < self.max_calls

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _evict(self, now: float) -> None:
        """Remove timestamps that have fallen outside the current window."""
        cutoff = now - self.period
        while self._timestamps and self._timestamps[0] <= cutoff:
            self._timestamps.popleft()

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"RateLimiter(max_calls={self.max_calls}, period={self.period})"
        )

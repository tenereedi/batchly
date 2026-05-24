"""Tests for batchly.rate_limiter."""

import time
import pytest
from batchly.rate_limiter import RateLimiter, RateLimitExceeded


class TestRateLimiter:
    def setup_method(self):
        # A generous limiter used for most tests (5 calls / second)
        self.limiter = RateLimiter(max_calls=5, period=1.0)

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    def test_repr(self):
        r = repr(RateLimiter(max_calls=3, period=2.0))
        assert "RateLimiter" in r
        assert "3" in r
        assert "2.0" in r

    def test_invalid_max_calls_raises(self):
        with pytest.raises(ValueError):
            RateLimiter(max_calls=0, period=1.0)

    def test_invalid_period_raises(self):
        with pytest.raises(ValueError):
            RateLimiter(max_calls=1, period=0)

    # ------------------------------------------------------------------
    # acquire / is_allowed
    # ------------------------------------------------------------------

    def test_acquire_within_limit_returns_true(self):
        limiter = RateLimiter(max_calls=3, period=1.0)
        for _ in range(3):
            assert limiter.acquire() is True

    def test_is_allowed_within_limit(self):
        limiter = RateLimiter(max_calls=3, period=1.0)
        assert limiter.is_allowed() is True

    def test_is_allowed_at_limit_returns_false(self):
        limiter = RateLimiter(max_calls=2, period=60.0)
        limiter.acquire()
        limiter.acquire()
        assert limiter.is_allowed() is False

    def test_non_blocking_acquire_returns_false_when_full(self):
        limiter = RateLimiter(max_calls=2, period=60.0)
        limiter.acquire(block=False)
        limiter.acquire(block=False)
        result = limiter.acquire(block=False)
        assert result is False

    def test_slots_replenish_after_period(self):
        limiter = RateLimiter(max_calls=2, period=0.1)
        limiter.acquire()
        limiter.acquire()
        assert limiter.is_allowed() is False
        time.sleep(0.15)
        assert limiter.is_allowed() is True

    def test_is_allowed_does_not_consume_slot(self):
        limiter = RateLimiter(max_calls=1, period=60.0)
        limiter.is_allowed()
        # slot still available
        assert limiter.acquire(block=False) is True

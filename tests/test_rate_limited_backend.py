"""Tests for batchly.backends.rate_limited_backend."""

import time
import pytest

from batchly.backends.memory import InMemoryBackend
from batchly.backends.rate_limited_backend import RateLimitedBackend
from batchly.rate_limiter import RateLimiter, RateLimitExceeded
from batchly.job import Job


def add(a, b):
    return a + b


class TestRateLimitedBackend:
    def setup_method(self):
        self.inner = InMemoryBackend()
        self.limiter = RateLimiter(max_calls=3, period=1.0)
        self.backend = RateLimitedBackend(
            self.inner, self.limiter, block=False
        )

    def _job(self):
        return Job(add, 1, 2)

    # ------------------------------------------------------------------
    # Delegation
    # ------------------------------------------------------------------

    def test_push_delegates_to_inner(self):
        self.backend.push(self._job())
        assert self.inner.size() == 1

    def test_size_delegates_to_inner(self):
        self.backend.push(self._job())
        assert self.backend.size() == 1

    def test_peek_delegates_to_inner(self):
        job = self._job()
        self.backend.push(job)
        assert self.backend.peek() is job

    def test_is_empty_delegates_to_inner(self):
        assert self.backend.is_empty() is True
        self.backend.push(self._job())
        assert self.backend.is_empty() is False

    def test_clear_delegates_to_inner(self):
        self.backend.push(self._job())
        self.backend.clear()
        assert self.backend.is_empty() is True

    # ------------------------------------------------------------------
    # Rate limiting on pop
    # ------------------------------------------------------------------

    def test_pop_within_limit_returns_job(self):
        job = self._job()
        self.backend.push(job)
        result = self.backend.pop()
        assert result is job

    def test_pop_exceeding_limit_raises(self):
        limiter = RateLimiter(max_calls=2, period=60.0)
        backend = RateLimitedBackend(self.inner, limiter, block=False)
        for _ in range(2):
            backend.push(self._job())
            backend.pop()
        backend.push(self._job())
        with pytest.raises(RateLimitExceeded):
            backend.pop()

    def test_pop_allowed_after_window_expires(self):
        limiter = RateLimiter(max_calls=1, period=0.1)
        backend = RateLimitedBackend(self.inner, limiter, block=False)
        backend.push(self._job())
        backend.push(self._job())
        backend.pop()  # consumes the slot
        time.sleep(0.15)
        result = backend.pop()  # slot should have refreshed
        assert result is not None

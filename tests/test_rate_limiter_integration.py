"""Integration tests: RateLimitedBackend wired into a JobQueue."""

import pytest

from batchly.backends.memory import InMemoryBackend
from batchly.backends.rate_limited_backend import RateLimitedBackend
from batchly.rate_limiter import RateLimiter, RateLimitExceeded
from batchly.queue import JobQueue
from batchly.job import Job


def add(a, b):
    return a + b


def always_fail():
    raise RuntimeError("boom")


class TestRateLimiterIntegration:
    def setup_method(self):
        inner = InMemoryBackend()
        limiter = RateLimiter(max_calls=2, period=60.0)
        rate_backend = RateLimitedBackend(inner, limiter, block=False)
        self.queue = JobQueue(backend=rate_backend)

    # ------------------------------------------------------------------
    # Happy path
    # ------------------------------------------------------------------

    def test_enqueue_and_process_within_limit(self):
        self.queue.enqueue(add, 1, 2)
        self.queue.enqueue(add, 3, 4)
        result1 = self.queue.process_next()
        result2 = self.queue.process_next()
        assert result1 == 3
        assert result2 == 7

    def test_third_dequeue_raises_rate_limit_exceeded(self):
        for _ in range(3):
            self.queue.enqueue(add, 1, 1)
        self.queue.process_next()
        self.queue.process_next()
        with pytest.raises(RateLimitExceeded):
            self.queue.process_next()

    # ------------------------------------------------------------------
    # Queue state is unaffected by rate-limit errors
    # ------------------------------------------------------------------

    def test_queue_size_unchanged_after_rate_limit_error(self):
        for _ in range(3):
            self.queue.enqueue(add, 0, 0)
        self.queue.process_next()
        self.queue.process_next()
        try:
            self.queue.process_next()
        except RateLimitExceeded:
            pass
        # The third job was NOT popped, so size should still be 1
        assert self.queue.size() == 1

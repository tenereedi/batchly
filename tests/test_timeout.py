"""Tests for TimeoutGuard, JobTimeoutError, and TimeoutBackend."""

import time
import pytest

from batchly.job import Job
from batchly.backends.memory import InMemoryBackend
from batchly.backends.timeout_backend import TimeoutBackend
from batchly.timeout import TimeoutGuard, JobTimeoutError


def add(x, y):
    return x + y


def slow_add(x, y):
    time.sleep(5)
    return x + y


class TestTimeoutGuard:
    def test_repr(self):
        g = TimeoutGuard(2.5)
        assert "2.5" in repr(g)

    def test_invalid_timeout_raises(self):
        with pytest.raises(ValueError):
            TimeoutGuard(0)

    def test_negative_timeout_raises(self):
        with pytest.raises(ValueError):
            TimeoutGuard(-1)

    def test_fast_job_does_not_timeout(self):
        guard = TimeoutGuard(2.0)
        result = []
        with guard.enforce():
            result.append(add(1, 2))
        assert result == [3]

    def test_slow_job_raises_timeout_error(self):
        guard = TimeoutGuard(0.1)
        with pytest.raises(JobTimeoutError) as exc_info:
            with guard.enforce():
                time.sleep(1)
        assert exc_info.value.timeout == 0.1

    def test_timeout_error_message(self):
        err = JobTimeoutError(3.0)
        assert "3.0" in str(err)


class TestTimeoutBackend:
    def setup_method(self):
        self._inner = InMemoryBackend()
        self._backend = TimeoutBackend(self._inner, timeout_seconds=2.0)

    def _job(self, fn, *args):
        return Job(fn, args)

    def test_repr(self):
        r = repr(self._backend)
        assert "TimeoutBackend" in r
        assert "2.0" in r

    def test_push_delegates_to_inner(self):
        job = self._job(add, 1, 2)
        self._backend.push(job)
        assert self._backend.size() == 1

    def test_pop_returns_none_when_empty(self):
        assert self._backend.pop() is None

    def test_fast_job_completes_normally(self):
        job = self._job(add, 3, 4)
        self._backend.push(job)
        popped = self._backend.pop()
        assert popped is not None
        result = popped.run()
        assert result == 7

    def test_slow_job_raises_timeout_error(self):
        backend = TimeoutBackend(InMemoryBackend(), timeout_seconds=0.1)
        job = self._job(slow_add, 1, 2)
        backend.push(job)
        popped = backend.pop()
        with pytest.raises(JobTimeoutError):
            popped.run()

    def test_peek_delegates_to_inner(self):
        job = self._job(add, 5, 6)
        self._backend.push(job)
        assert self._backend.peek() is job

    def test_is_empty_delegates_to_inner(self):
        assert self._backend.is_empty()
        self._backend.push(self._job(add, 1, 1))
        assert not self._backend.is_empty()

    def test_clear_delegates_to_inner(self):
        self._backend.push(self._job(add, 1, 1))
        self._backend.clear()
        assert self._backend.size() == 0

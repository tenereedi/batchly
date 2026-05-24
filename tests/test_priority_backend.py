"""Tests for PriorityBackend."""

import pytest

from batchly.backends.priority_backend import PriorityBackend
from batchly.job import Job
from batchly.priority_queue import PriorityLevel


def add(x: int, y: int) -> int:
    return x + y


class TestPriorityBackend:
    def setup_method(self) -> None:
        self.backend = PriorityBackend()

    def _job(self, name: str = "j") -> Job:
        return Job(func=add, args=(1, 2), job_id=name)

    def test_repr(self) -> None:
        r = repr(self.backend)
        assert "PriorityBackend" in r
        assert "size=0" in r

    def test_initial_size_is_zero(self) -> None:
        assert self.backend.size() == 0

    def test_is_empty_initially(self) -> None:
        assert self.backend.is_empty()

    def test_push_increases_size(self) -> None:
        self.backend.push(self._job())
        assert self.backend.size() == 1

    def test_pop_returns_none_when_empty(self) -> None:
        assert self.backend.pop() is None

    def test_peek_returns_none_when_empty(self) -> None:
        assert self.backend.peek() is None

    def test_push_and_pop_respects_priority(self) -> None:
        low = self._job("low")
        high = self._job("high")
        self.backend.push(low, priority=PriorityLevel.LOW)
        self.backend.push(high, priority=PriorityLevel.HIGH)
        assert self.backend.pop() is high
        assert self.backend.pop() is low

    def test_default_priority_used_when_none(self) -> None:
        backend = PriorityBackend(default_priority=PriorityLevel.HIGH)
        j1 = self._job("j1")
        j2 = self._job("j2")
        backend.push(j1)  # uses HIGH by default
        backend.push(j2, priority=PriorityLevel.LOW)
        assert backend.pop() is j1

    def test_peek_does_not_remove(self) -> None:
        job = self._job()
        self.backend.push(job)
        assert self.backend.peek() is job
        assert self.backend.size() == 1

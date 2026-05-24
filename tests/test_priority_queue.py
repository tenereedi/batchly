"""Tests for PriorityJobQueue."""

import pytest

from batchly.job import Job
from batchly.priority_queue import PriorityJobQueue, PriorityLevel


def add(x: int, y: int) -> int:
    return x + y


class TestPriorityJobQueue:
    def setup_method(self) -> None:
        self.queue = PriorityJobQueue()

    def _job(self, name: str = "j") -> Job:
        return Job(func=add, args=(1, 2), job_id=name)

    def test_repr(self) -> None:
        assert "PriorityJobQueue" in repr(self.queue)
        assert "size=0" in repr(self.queue)

    def test_empty_queue_returns_none_on_dequeue(self) -> None:
        assert self.queue.dequeue() is None

    def test_empty_queue_returns_none_on_peek(self) -> None:
        assert self.queue.peek() is None

    def test_size_and_len(self) -> None:
        self.queue.enqueue(self._job("a"))
        assert self.queue.size() == 1
        assert len(self.queue) == 1

    def test_is_empty(self) -> None:
        assert self.queue.is_empty()
        self.queue.enqueue(self._job())
        assert not self.queue.is_empty()

    def test_high_priority_dequeued_first(self) -> None:
        low = self._job("low")
        high = self._job("high")
        self.queue.enqueue(low, priority=PriorityLevel.LOW)
        self.queue.enqueue(high, priority=PriorityLevel.HIGH)
        assert self.queue.dequeue() is high
        assert self.queue.dequeue() is low

    def test_critical_before_normal(self) -> None:
        normal = self._job("normal")
        critical = self._job("critical")
        self.queue.enqueue(normal, priority=PriorityLevel.NORMAL)
        self.queue.enqueue(critical, priority=PriorityLevel.CRITICAL)
        assert self.queue.dequeue() is critical

    def test_fifo_within_same_priority(self) -> None:
        first = self._job("first")
        second = self._job("second")
        self.queue.enqueue(first, priority=PriorityLevel.NORMAL)
        self.queue.enqueue(second, priority=PriorityLevel.NORMAL)
        assert self.queue.dequeue() is first
        assert self.queue.dequeue() is second

    def test_peek_does_not_remove(self) -> None:
        job = self._job()
        self.queue.enqueue(job, priority=PriorityLevel.HIGH)
        assert self.queue.peek() is job
        assert self.queue.size() == 1

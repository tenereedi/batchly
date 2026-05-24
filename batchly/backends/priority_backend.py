"""Priority-aware backend wrapping an inner BaseBackend."""

from __future__ import annotations

from typing import Optional

from batchly.backends.base import BaseBackend
from batchly.job import Job
from batchly.priority_queue import PriorityJobQueue, PriorityLevel


class PriorityBackend(BaseBackend):
    """Backend that dequeues jobs in priority order.

    Jobs pushed with a lower priority integer value are dequeued first.
    Falls back to a plain in-memory priority heap; does not delegate to
    an inner backend so it can be used standalone or composed.
    """

    def __init__(self, default_priority: int = PriorityLevel.NORMAL) -> None:
        self._queue = PriorityJobQueue()
        self.default_priority = default_priority

    def push(self, job: Job, priority: Optional[int] = None) -> None:  # type: ignore[override]
        p = priority if priority is not None else self.default_priority
        self._queue.enqueue(job, priority=p)

    def pop(self) -> Optional[Job]:
        return self._queue.dequeue()

    def peek(self) -> Optional[Job]:
        return self._queue.peek()

    def size(self) -> int:
        return self._queue.size()

    def is_empty(self) -> bool:
        return self._queue.is_empty()

    def __repr__(self) -> str:
        return (
            f"PriorityBackend(size={self.size()}, "
            f"default_priority={self.default_priority})"
        )

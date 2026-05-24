"""Priority queue support for batchly jobs."""

from __future__ import annotations

import heapq
from dataclasses import dataclass, field
from typing import Optional

from batchly.job import Job


class PriorityLevel:
    LOW = 10
    NORMAL = 5
    HIGH = 1
    CRITICAL = 0


@dataclass(order=True)
class PrioritizedJob:
    priority: int
    sequence: int
    job: Job = field(compare=False)

    def __repr__(self) -> str:
        return (
            f"PrioritizedJob(priority={self.priority}, "
            f"job_id={self.job.job_id!r})"
        )


class PriorityJobQueue:
    """A min-heap based priority queue for Jobs."""

    def __init__(self) -> None:
        self._heap: list[PrioritizedJob] = []
        self._counter: int = 0

    def enqueue(self, job: Job, priority: int = PriorityLevel.NORMAL) -> None:
        """Push a job onto the queue with the given priority."""
        entry = PrioritizedJob(
            priority=priority,
            sequence=self._counter,
            job=job,
        )
        heapq.heappush(self._heap, entry)
        self._counter += 1

    def dequeue(self) -> Optional[Job]:
        """Pop the highest-priority (lowest value) job."""
        if not self._heap:
            return None
        return heapq.heappop(self._heap).job

    def peek(self) -> Optional[Job]:
        """Return the highest-priority job without removing it."""
        if not self._heap:
            return None
        return self._heap[0].job

    def size(self) -> int:
        return len(self._heap)

    def is_empty(self) -> bool:
        return len(self._heap) == 0

    def __len__(self) -> int:
        return self.size()

    def __repr__(self) -> str:
        return f"PriorityJobQueue(size={self.size()})"

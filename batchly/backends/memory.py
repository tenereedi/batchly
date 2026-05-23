from collections import deque
from typing import Optional
from batchly.job import Job
from batchly.backends.base import BaseBackend


class InMemoryBackend(BaseBackend):
    """Simple in-memory FIFO backend using a deque."""

    def __init__(self) -> None:
        self._queue: deque[Job] = deque()

    def push(self, job: Job) -> None:
        """Append a job to the end of the queue."""
        self._queue.append(job)

    def pop(self) -> Optional[Job]:
        """Remove and return the leftmost (oldest) job, or None if empty."""
        if not self._queue:
            return None
        return self._queue.popleft()

    def peek(self) -> Optional[Job]:
        """Return the leftmost job without removing it, or None if empty."""
        if not self._queue:
            return None
        return self._queue[0]

    def size(self) -> int:
        return len(self._queue)

    def clear(self) -> None:
        self._queue.clear()

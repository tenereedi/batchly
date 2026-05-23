from collections import deque
from typing import Callable, Optional
from batchly.job import Job, JobStatus


class JobQueue:
    """Simple in-memory job queue with basic enqueue/dequeue operations."""

    def __init__(self, name: str = "default", max_retries: int = 3):
        self.name = name
        self.max_retries = max_retries
        self._queue: deque[Job] = deque()
        self._completed: list[Job] = []
        self._failed: list[Job] = []

    def enqueue(self, func: Callable, *args, **kwargs) -> Job:
        """Create a new Job and add it to the queue."""
        job = Job(func=func, args=args, kwargs=kwargs, max_retries=self.max_retries)
        self._queue.append(job)
        return job

    def dequeue(self) -> Optional[Job]:
        """Remove and return the next job from the queue."""
        if self._queue:
            return self._queue.popleft()
        return None

    def process_next(self) -> Optional[Job]:
        """Process the next job in the queue, handling retries on failure."""
        job = self.dequeue()
        if job is None:
            return None

        job.run()

        if job.status == JobStatus.FAILED and job.can_retry():
            job.status = JobStatus.PENDING
            self._queue.appendleft(job)
        elif job.status == JobStatus.FAILED:
            self._failed.append(job)
        else:
            self._completed.append(job)

        return job

    def process_all(self) -> list[Job]:
        """Process all jobs currently in the queue."""
        processed = []
        while self._queue:
            job = self.process_next()
            if job is not None:
                processed.append(job)
        return processed

    @property
    def size(self) -> int:
        """Return the number of pending jobs in the queue."""
        return len(self._queue)

    def __repr__(self) -> str:
        return (
            f"JobQueue(name={self.name!r}, pending={self.size}, "
            f"completed={len(self._completed)}, failed={len(self._failed)})"
        )

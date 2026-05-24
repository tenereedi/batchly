"""In-process job queue with backend support and hook integration."""

from typing import Optional
from batchly.job import Job, JobStatus
from batchly.backends.base import BaseBackend
from batchly.backends.memory import InMemoryBackend
from batchly.hooks import default_registry


class JobQueue:
    """FIFO job queue backed by a pluggable storage backend."""

    def __init__(self, backend: BaseBackend = None, registry=None):
        self.backend = backend or InMemoryBackend()
        self._registry = registry or default_registry

    def enqueue(self, job: Job) -> Job:
        """Add a job to the queue."""
        self._registry.fire("queue.before_enqueue", job=job)
        self.backend.push(job)
        self._registry.fire("queue.after_enqueue", job=job)
        return job

    def dequeue(self) -> Optional[Job]:
        """Remove and return the next job, or None if empty."""
        self._registry.fire("queue.before_dequeue")
        return self.backend.pop()

    def process_next(self) -> Optional[Job]:
        """Dequeue and run the next job. Returns the job or None."""
        job = self.dequeue()
        if job is None:
            return None
        try:
            job.run()
        except Exception:
            pass
        return job

    def peek(self) -> Optional[Job]:
        """Return the next job without removing it."""
        return self.backend.peek()

    def size(self) -> int:
        """Return the number of jobs currently queued."""
        return self.backend.size()

    def is_empty(self) -> bool:
        """Return True if the queue has no pending jobs."""
        return self.size() == 0

    def drain(self) -> int:
        """Process all queued jobs. Returns the count processed."""
        count = 0
        while not self.is_empty():
            self.process_next()
            count += 1
        return count

    def __repr__(self) -> str:
        return f"JobQueue(backend={self.backend.__class__.__name__}, size={self.size()})"

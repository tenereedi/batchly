"""Backend decorator that routes permanently-failed jobs to a DeadLetterQueue."""

from __future__ import annotations

from typing import Optional

from batchly.backends.base import BaseBackend
from batchly.deadletter import DeadLetterQueue
from batchly.job import Job, JobStatus


class DeadLetterBackend(BaseBackend):
    """Wraps an inner backend and captures exhausted jobs in a DeadLetterQueue.

    When :py:meth:`pop` returns a job whose status is ``FAILED`` and that
    cannot be retried (``can_retry`` is ``False``), the job is automatically
    forwarded to the attached :class:`~batchly.deadletter.DeadLetterQueue`
    instead of being returned to the caller.
    """

    def __init__(self, inner: BaseBackend, dlq: Optional[DeadLetterQueue] = None) -> None:
        self._inner = inner
        self.dlq: DeadLetterQueue = dlq if dlq is not None else DeadLetterQueue()

    # ------------------------------------------------------------------
    # BaseBackend interface
    # ------------------------------------------------------------------

    def push(self, job: Job) -> None:
        self._inner.push(job)

    def pop(self) -> Optional[Job]:
        job = self._inner.pop()
        if job is None:
            return None
        if job.status == JobStatus.FAILED and not job.can_retry():
            self.dlq.add(job, reason=str(job.error) if job.error else "max retries exceeded")
            return None
        return job

    def peek(self) -> Optional[Job]:
        return self._inner.peek()

    def size(self) -> int:
        return self._inner.size()

    def is_empty(self) -> bool:
        return self._inner.is_empty()

    def clear(self) -> None:
        self._inner.clear()

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"DeadLetterBackend(inner={self._inner!r}, "
            f"dlq_size={self.dlq.size()})"
        )

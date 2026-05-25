"""Backend wrapper that enforces per-job execution timeouts."""

from batchly.backends.base import BaseBackend
from batchly.job import Job
from batchly.timeout import TimeoutGuard, JobTimeoutError


class TimeoutBackend(BaseBackend):
    """Wraps an inner backend and enforces a timeout when jobs are executed.

    The timeout is applied inside ``pop`` so that any downstream consumer
    (e.g. ``JobQueue.process_next``) automatically respects the limit.

    Args:
        inner: The backend being wrapped.
        timeout_seconds: Maximum seconds a job's ``run()`` may take.
    """

    def __init__(self, inner: BaseBackend, timeout_seconds: float):
        self._inner = inner
        self._guard = TimeoutGuard(timeout_seconds)

    def __repr__(self) -> str:
        return (
            f"TimeoutBackend(inner={self._inner!r}, "
            f"timeout_seconds={self._guard.seconds})"
        )

    def push(self, job: Job) -> None:
        self._inner.push(job)

    def pop(self) -> Job | None:
        job = self._inner.pop()
        if job is None:
            return None
        # Wrap the job's run method so it raises JobTimeoutError if too slow.
        original_run = job.run

        def timed_run():
            with self._guard.enforce():
                return original_run()

        job.run = timed_run  # type: ignore[method-assign]
        return job

    def peek(self) -> Job | None:
        return self._inner.peek()

    def size(self) -> int:
        return self._inner.size()

    def is_empty(self) -> bool:
        return self._inner.is_empty()

    def clear(self) -> None:
        self._inner.clear()

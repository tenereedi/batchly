"""Job definition with status tracking and retry support."""

import uuid
from enum import Enum
from typing import Callable, Any, Optional
from batchly.retry import RetryPolicy, NoRetry
from batchly.hooks import default_registry


class JobStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"


class Job:
    """Represents a unit of work to be executed by the queue."""

    def __init__(
        self,
        func: Callable,
        args: tuple = (),
        kwargs: dict = None,
        retry_policy: RetryPolicy = None,
        job_id: str = None,
        registry=None,
    ):
        self.func = func
        self.args = args
        self.kwargs = kwargs or {}
        self.retry_policy = retry_policy or NoRetry()
        self.job_id = job_id or str(uuid.uuid4())
        self.status = JobStatus.PENDING
        self.attempts = 0
        self.result: Any = None
        self.error: Optional[Exception] = None
        self._registry = registry or default_registry

    def run(self) -> Any:
        """Execute the job function, updating status and firing hooks."""
        self.status = JobStatus.RUNNING
        self.attempts += 1
        self._registry.fire("job.before_run", job=self)
        try:
            self.result = self.func(*self.args, **self.kwargs)
            self.status = JobStatus.SUCCESS
            self._registry.fire("job.on_success", job=self)
            self._registry.fire("job.after_run", job=self)
            return self.result
        except Exception as exc:
            self.error = exc
            if self.can_retry():
                self.status = JobStatus.RETRYING
                self._registry.fire("job.on_retry", job=self)
            else:
                self.status = JobStatus.FAILED
                self._registry.fire("job.on_failure", job=self)
            self._registry.fire("job.after_run", job=self)
            raise

    def can_retry(self) -> bool:
        """Return True if the job is eligible for another attempt."""
        return self.retry_policy.should_retry(self.attempts, self.error)

    def __repr__(self) -> str:
        return (
            f"Job(id={self.job_id!r}, func={self.func.__name__!r}, "
            f"status={self.status.value}, attempts={self.attempts})"
        )

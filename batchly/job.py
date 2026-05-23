"""Core job definition for batchly."""

import uuid
from enum import Enum
from typing import Any, Callable, Dict, Optional

from batchly.retry import RetryPolicy, NoRetry


class JobStatus(Enum):
    PENDING = 'pending'
    RUNNING = 'running'
    SUCCESS = 'success'
    FAILED = 'failed'


class Job:
    """Represents a single unit of work to be executed by a worker."""

    def __init__(
        self,
        func: Callable,
        *args: Any,
        retry_policy: Optional[RetryPolicy] = None,
        **kwargs: Any,
    ):
        self.id: str = str(uuid.uuid4())
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.retry_policy: RetryPolicy = retry_policy or NoRetry()
        self.status: JobStatus = JobStatus.PENDING
        self.result: Any = None
        self.error: Optional[Exception] = None
        self.attempts: int = 0
        self.metadata: Dict[str, Any] = {}

    def run(self) -> Any:
        """Execute the job function and update status accordingly."""
        self.status = JobStatus.RUNNING
        self.attempts += 1
        try:
            self.result = self.func(*self.args, **self.kwargs)
            self.status = JobStatus.SUCCESS
            return self.result
        except Exception as exc:
            self.error = exc
            self.status = JobStatus.FAILED
            raise

    def can_retry(self) -> bool:
        """Return True if the job is eligible for another attempt."""
        if self.error is None:
            return False
        return self.retry_policy.should_retry(
            attempt=self.attempts,
            exception=self.error,
        )

    def __repr__(self) -> str:
        return (
            f"Job(id={self.id!r}, func={self.func.__name__!r}, "
            f"status={self.status.value!r}, attempts={self.attempts})"
        )

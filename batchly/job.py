from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, Optional
import uuid


class JobStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"


@dataclass
class Job:
    """Represents a single unit of work in the queue."""

    func: Callable
    args: tuple = field(default_factory=tuple)
    kwargs: Dict[str, Any] = field(default_factory=dict)
    job_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: JobStatus = JobStatus.PENDING
    max_retries: int = 3
    retry_count: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    result: Any = None
    error: Optional[str] = None

    def run(self) -> Any:
        """Execute the job's function with its arguments."""
        self.status = JobStatus.RUNNING
        self.started_at = datetime.utcnow()
        try:
            self.result = self.func(*self.args, **self.kwargs)
            self.status = JobStatus.SUCCESS
            return self.result
        except Exception as exc:
            self.error = str(exc)
            if self.retry_count < self.max_retries:
                self.retry_count += 1
                self.status = JobStatus.RETRYING
            else:
                self.status = JobStatus.FAILED
            raise
        finally:
            self.finished_at = datetime.utcnow()

    @property
    def can_retry(self) -> bool:
        """Return True if the job is eligible for another attempt."""
        return self.status == JobStatus.RETRYING

    def __repr__(self) -> str:
        return (
            f"Job(id={self.job_id!r}, func={self.func.__name__!r}, "
            f"status={self.status.value!r}, retries={self.retry_count}/{self.max_retries})"
        )

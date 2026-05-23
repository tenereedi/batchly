"""Retry policies for batchly job queue."""

from dataclasses import dataclass, field
from typing import Optional, Type, Tuple
import time


@dataclass
class RetryPolicy:
    """Defines how a failed job should be retried."""

    max_retries: int = 3
    delay: float = 0.0
    backoff: float = 1.0
    exceptions: Tuple[Type[Exception], ...] = field(default_factory=lambda: (Exception,))

    def get_delay(self, attempt: int) -> float:
        """Calculate delay before the next retry attempt.

        Args:
            attempt: The current retry attempt number (1-based).

        Returns:
            Seconds to wait before retrying.
        """
        return self.delay * (self.backoff ** (attempt - 1))

    def should_retry(self, attempt: int, exc: Optional[Exception] = None) -> bool:
        """Determine whether a job should be retried.

        Args:
            attempt: Number of attempts already made.
            exc: The exception that caused the failure, if any.

        Returns:
            True if the job should be retried, False otherwise.
        """
        if attempt >= self.max_retries:
            return False
        if exc is not None and not isinstance(exc, self.exceptions):
            return False
        return True


class NoRetry(RetryPolicy):
    """Policy that never retries a failed job."""

    def __init__(self) -> None:
        super().__init__(max_retries=0)


class LinearRetry(RetryPolicy):
    """Policy that retries with a constant delay between attempts."""

    def __init__(self, max_retries: int = 3, delay: float = 1.0) -> None:
        super().__init__(max_retries=max_retries, delay=delay, backoff=1.0)


class ExponentialBackoff(RetryPolicy):
    """Policy that retries with exponentially increasing delays."""

    def __init__(
        self,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        backoff: float = 2.0,
    ) -> None:
        super().__init__(max_retries=max_retries, delay=initial_delay, backoff=backoff)

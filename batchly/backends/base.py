from abc import ABC, abstractmethod
from typing import Optional
from batchly.job import Job


class BaseBackend(ABC):
    """Abstract base class for job queue backends."""

    @abstractmethod
    def push(self, job: Job) -> None:
        """Add a job to the backend store."""
        raise NotImplementedError

    @abstractmethod
    def pop(self) -> Optional[Job]:
        """Remove and return the next job, or None if empty."""
        raise NotImplementedError

    @abstractmethod
    def peek(self) -> Optional[Job]:
        """Return the next job without removing it, or None if empty."""
        raise NotImplementedError

    @abstractmethod
    def size(self) -> int:
        """Return the number of jobs currently in the backend."""
        raise NotImplementedError

    @abstractmethod
    def clear(self) -> None:
        """Remove all jobs from the backend."""
        raise NotImplementedError

    def __len__(self) -> int:
        return self.size()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(size={self.size()})"

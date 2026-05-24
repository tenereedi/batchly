"""Dead-letter queue: stores jobs that have exhausted all retry attempts."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from batchly.job import Job


@dataclass
class DeadLetterEntry:
    """A record of a job that permanently failed."""

    job: Job
    failed_at: datetime = field(default_factory=datetime.utcnow)
    reason: str = ""

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"DeadLetterEntry(job_id={self.job.id!r}, "
            f"failed_at={self.failed_at.isoformat()!r}, "
            f"reason={self.reason!r})"
        )


class DeadLetterQueue:
    """Stores jobs that could not be completed after all retries."""

    def __init__(self) -> None:
        self._entries: List[DeadLetterEntry] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add(self, job: Job, reason: str = "") -> DeadLetterEntry:
        """Record *job* as permanently failed."""
        entry = DeadLetterEntry(job=job, reason=reason)
        self._entries.append(entry)
        return entry

    def get_all(self) -> List[DeadLetterEntry]:
        """Return a snapshot of all dead-letter entries."""
        return list(self._entries)

    def find(self, job_id: str) -> Optional[DeadLetterEntry]:
        """Return the entry for *job_id*, or ``None`` if not present."""
        for entry in self._entries:
            if entry.job.id == job_id:
                return entry
        return None

    def remove(self, job_id: str) -> bool:
        """Remove the entry for *job_id*. Returns ``True`` if removed."""
        before = len(self._entries)
        self._entries = [e for e in self._entries if e.job.id != job_id]
        return len(self._entries) < before

    def size(self) -> int:
        """Number of entries currently in the dead-letter queue."""
        return len(self._entries)

    def clear(self) -> None:
        """Remove all entries."""
        self._entries.clear()

    def __repr__(self) -> str:  # pragma: no cover
        return f"DeadLetterQueue(size={self.size()})"

"""Simple metrics collection for job queue statistics."""

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict


@dataclass
class JobMetrics:
    """Aggregated metrics for job processing."""
    total_enqueued: int = 0
    total_succeeded: int = 0
    total_failed: int = 0
    total_retried: int = 0
    total_discarded: int = 0
    errors_by_type: Dict[str, int] = field(default_factory=lambda: defaultdict(int))

    @property
    def total_processed(self) -> int:
        return self.total_succeeded + self.total_failed

    @property
    def success_rate(self) -> float:
        if self.total_processed == 0:
            return 0.0
        return self.total_succeeded / self.total_processed

    def __repr__(self) -> str:
        return (
            f"JobMetrics(enqueued={self.total_enqueued}, "
            f"succeeded={self.total_succeeded}, "
            f"failed={self.total_failed}, "
            f"retried={self.total_retried}, "
            f"discarded={self.total_discarded})"
        )


class MetricsCollector:
    """Collects and exposes job processing metrics."""

    def __init__(self):
        self._metrics = JobMetrics()

    def record_enqueued(self):
        self._metrics.total_enqueued += 1

    def record_success(self):
        self._metrics.total_succeeded += 1

    def record_failure(self, exc: Exception):
        self._metrics.total_failed += 1
        exc_type = type(exc).__name__
        self._metrics.errors_by_type[exc_type] += 1

    def record_retry(self):
        self._metrics.total_retried += 1

    def record_discarded(self):
        self._metrics.total_discarded += 1

    def snapshot(self) -> JobMetrics:
        """Return a copy of current metrics."""
        m = self._metrics
        return JobMetrics(
            total_enqueued=m.total_enqueued,
            total_succeeded=m.total_succeeded,
            total_failed=m.total_failed,
            total_retried=m.total_retried,
            total_discarded=m.total_discarded,
            errors_by_type=defaultdict(int, m.errors_by_type),
        )

    def reset(self):
        self._metrics = JobMetrics()

    def __repr__(self) -> str:
        return f"MetricsCollector({self._metrics!r})"

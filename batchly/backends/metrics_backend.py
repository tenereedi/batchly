"""A backend decorator that wraps any BaseBackend with metrics collection."""

from batchly.backends.base import BaseBackend
from batchly.metrics import MetricsCollector


class MetricsBackend(BaseBackend):
    """Wraps another backend and records push/pop counts via MetricsCollector."""

    def __init__(self, backend: BaseBackend, collector: MetricsCollector):
        self._backend = backend
        self._collector = collector

    def push(self, job) -> None:
        self._backend.push(job)
        self._collector.record_enqueued()

    def pop(self):
        return self._backend.pop()

    def peek(self):
        return self._backend.peek()

    def size(self) -> int:
        return self._backend.size()

    def is_empty(self) -> bool:
        return self._backend.is_empty()

    def clear(self) -> None:
        self._backend.clear()

    def __repr__(self) -> str:
        return (
            f"MetricsBackend(backend={self._backend!r}, "
            f"collector={self._collector!r})"
        )

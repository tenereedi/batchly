"""Integration tests: PriorityBackend wired into JobQueue."""

from batchly.backends.priority_backend import PriorityBackend
from batchly.job import Job, JobStatus
from batchly.priority_queue import PriorityLevel
from batchly.queue import JobQueue

results: list[int] = []


def record(x: int) -> int:
    results.append(x)
    return x


class TestPriorityIntegration:
    def setup_method(self) -> None:
        results.clear()
        self.backend = PriorityBackend()
        self.queue = JobQueue(backend=self.backend)

    def _job(self, value: int, name: str) -> Job:
        return Job(func=record, args=(value,), job_id=name)

    def test_jobs_processed_in_priority_order(self) -> None:
        low_job = self._job(10, "low")
        high_job = self._job(99, "high")
        self.queue.enqueue(low_job, priority=PriorityLevel.LOW)
        self.queue.enqueue(high_job, priority=PriorityLevel.HIGH)
        self.queue.process_next()
        self.queue.process_next()
        assert results == [99, 10]

    def test_critical_job_processed_before_normal(self) -> None:
        normal_job = self._job(1, "normal")
        critical_job = self._job(2, "critical")
        self.queue.enqueue(normal_job, priority=PriorityLevel.NORMAL)
        self.queue.enqueue(critical_job, priority=PriorityLevel.CRITICAL)
        self.queue.process_next()
        assert results == [2]

    def test_completed_status_after_processing(self) -> None:
        job = self._job(5, "j")
        self.queue.enqueue(job, priority=PriorityLevel.NORMAL)
        self.queue.process_next()
        assert job.status == JobStatus.COMPLETED

    def test_queue_empty_after_all_processed(self) -> None:
        for i in range(3):
            self.queue.enqueue(self._job(i, f"j{i}"))
        for _ in range(3):
            self.queue.process_next()
        assert self.backend.is_empty()

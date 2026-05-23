import pytest
from batchly.queue import JobQueue
from batchly.worker import Worker
from batchly.job import JobStatus
from batchly.retry import NoRetry, RetryPolicy


def add(x, y):
    return x + y


def always_fail():
    raise RuntimeError("boom")


class TestWorker:
    def setup_method(self):
        self.queue = JobQueue(retry_policy=NoRetry())
        self.worker = Worker(self.queue, poll_interval=0, max_jobs=5)

    def test_repr(self):
        assert "Worker" in repr(self.worker)
        assert "max_jobs=5" in repr(self.worker)

    def test_processes_single_job(self):
        self.queue.enqueue(add, 1, 2)
        worker = Worker(self.queue, poll_interval=0, max_jobs=1)
        worker.start()
        assert worker.jobs_processed == 1
        assert worker.jobs_succeeded == 1
        assert worker.jobs_failed == 0

    def test_counts_failed_jobs(self):
        self.queue.enqueue(always_fail)
        worker = Worker(self.queue, poll_interval=0, max_jobs=1)
        worker.start()
        assert worker.jobs_processed == 1
        assert worker.jobs_failed == 1
        assert worker.jobs_succeeded == 0

    def test_stops_at_max_jobs(self):
        for _ in range(10):
            self.queue.enqueue(add, 1, 1)
        worker = Worker(self.queue, poll_interval=0, max_jobs=3)
        worker.start()
        assert worker.jobs_processed == 3

    def test_stops_when_queue_empty(self):
        self.queue.enqueue(add, 2, 3)
        self.queue.enqueue(add, 4, 5)
        worker = Worker(self.queue, poll_interval=0, max_jobs=10)
        worker.start()
        assert worker.jobs_processed == 2

    def test_is_not_running_after_start(self):
        self.queue.enqueue(add, 1, 2)
        worker = Worker(self.queue, poll_interval=0, max_jobs=1)
        worker.start()
        assert not worker.is_running

    def test_stop_sets_running_false(self):
        worker = Worker(self.queue, poll_interval=0, max_jobs=100)
        # stop before start has no effect on is_running (already False)
        worker.stop()
        assert not worker.is_running

    def test_mixed_jobs_tracking(self):
        self.queue.enqueue(add, 1, 2)
        self.queue.enqueue(always_fail)
        self.queue.enqueue(add, 3, 4)
        worker = Worker(self.queue, poll_interval=0, max_jobs=3)
        worker.start()
        assert worker.jobs_processed == 3
        assert worker.jobs_succeeded == 2
        assert worker.jobs_failed == 1

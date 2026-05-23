import pytest
from batchly.queue import JobQueue
from batchly.job import JobStatus


def add(a, b):
    return a + b


def always_fail():
    raise RuntimeError("intentional failure")


class TestJobQueue:
    def setup_method(self):
        self.queue = JobQueue(name="test", max_retries=2)

    def test_enqueue_adds_job(self):
        job = self.queue.enqueue(add, 1, 2)
        assert self.queue.size == 1
        assert job.status == JobStatus.PENDING

    def test_dequeue_removes_job(self):
        job = self.queue.enqueue(add, 1, 2)
        dequeued = self.queue.dequeue()
        assert dequeued is job
        assert self.queue.size == 0

    def test_dequeue_empty_queue_returns_none(self):
        assert self.queue.dequeue() is None

    def test_process_next_runs_job(self):
        self.queue.enqueue(add, 3, 4)
        job = self.queue.process_next()
        assert job.status == JobStatus.COMPLETED
        assert job.result == 7

    def test_process_next_moves_to_completed(self):
        self.queue.enqueue(add, 1, 1)
        self.queue.process_next()
        assert len(self.queue._completed) == 1
        assert self.queue.size == 0

    def test_failed_job_requeued_if_can_retry(self):
        self.queue.enqueue(always_fail)
        job = self.queue.process_next()
        assert job.status == JobStatus.PENDING
        assert self.queue.size == 1

    def test_failed_job_moved_to_failed_after_max_retries(self):
        queue = JobQueue(name="test", max_retries=0)
        queue.enqueue(always_fail)
        job = queue.process_next()
        assert job.status == JobStatus.FAILED
        assert len(queue._failed) == 1

    def test_process_all_drains_queue(self):
        for i in range(5):
            self.queue.enqueue(add, i, i)
        processed = self.queue.process_all()
        assert self.queue.size == 0
        assert len(processed) == 5

    def test_process_next_on_empty_returns_none(self):
        assert self.queue.process_next() is None

    def test_repr(self):
        self.queue.enqueue(add, 1, 2)
        assert "test" in repr(self.queue)
        assert "pending=1" in repr(self.queue)

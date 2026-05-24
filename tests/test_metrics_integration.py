"""Integration tests: MetricsCollector wired into JobQueue via hooks."""

import pytest
from batchly.job import Job
from batchly.queue import JobQueue
from batchly.hooks import HookRegistry
from batchly.metrics import MetricsCollector
from batchly.retry import RetryPolicy


def add(x, y):
    return x + y


def always_fail():
    raise RuntimeError("boom")


class TestMetricsIntegration:
    def setup_method(self):
        self.hooks = HookRegistry()
        self.collector = MetricsCollector()
        self.queue = JobQueue(hooks=self.hooks)

        self.hooks.register("job.enqueued", lambda job: self.collector.record_enqueued())
        self.hooks.register("job.succeeded", lambda job: self.collector.record_success())
        self.hooks.register(
            "job.failed",
            lambda job, exc: self.collector.record_failure(exc),
        )
        self.hooks.register("job.retried", lambda job: self.collector.record_retry())
        self.hooks.register(
            "job.discarded", lambda job: self.collector.record_discarded()
        )

    def test_enqueue_increments_metric(self):
        job = Job(add, 1, 2)
        self.queue.enqueue(job)
        assert self.collector.snapshot().total_enqueued == 1

    def test_successful_job_increments_success(self):
        job = Job(add, 3, 4)
        self.queue.enqueue(job)
        self.queue.process_next()
        snap = self.collector.snapshot()
        assert snap.total_succeeded == 1
        assert snap.total_failed == 0

    def test_failed_job_increments_failure(self):
        job = Job(always_fail, retry_policy=RetryPolicy(max_retries=0))
        self.queue.enqueue(job)
        self.queue.process_next()
        snap = self.collector.snapshot()
        assert snap.total_failed == 1
        assert snap.errors_by_type["RuntimeError"] == 1

    def test_success_rate_after_mixed_jobs(self):
        self.queue.enqueue(Job(add, 1, 2))
        self.queue.enqueue(Job(always_fail, retry_policy=RetryPolicy(max_retries=0)))
        self.queue.process_next()
        self.queue.process_next()
        snap = self.collector.snapshot()
        assert snap.success_rate == pytest.approx(0.5)

    def test_multiple_enqueues_tracked(self):
        for _ in range(5):
            self.queue.enqueue(Job(add, 0, 0))
        assert self.collector.snapshot().total_enqueued == 5

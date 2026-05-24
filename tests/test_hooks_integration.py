"""Integration tests verifying hooks fire correctly during job and queue operations."""

import pytest
from batchly.hooks import HookRegistry
from batchly.job import Job, JobStatus
from batchly.queue import JobQueue
from batchly.retry import RetryPolicy


def add(x, y):
    return x + y


def always_fail():
    raise RuntimeError("boom")


class TestHooksIntegration:
    def setup_method(self):
        self.registry = HookRegistry()
        self.events = []

        for event in [
            "job.before_run", "job.after_run",
            "job.on_success", "job.on_failure", "job.on_retry",
            "queue.before_enqueue", "queue.after_enqueue", "queue.before_dequeue",
        ]:
            name = event
            self.registry.register(event, lambda e=name, **kw: self.events.append(e))

    def _make_job(self, func, *args, retry_policy=None):
        return Job(func, args=args, retry_policy=retry_policy, registry=self.registry)

    def _make_queue(self):
        return JobQueue(registry=self.registry)

    def test_success_fires_correct_hooks(self):
        job = self._make_job(add, 1, 2)
        job.run()
        assert "job.before_run" in self.events
        assert "job.on_success" in self.events
        assert "job.after_run" in self.events
        assert "job.on_failure" not in self.events

    def test_failure_fires_on_failure_hook(self):
        job = self._make_job(always_fail)
        with pytest.raises(RuntimeError):
            job.run()
        assert "job.on_failure" in self.events
        assert "job.on_success" not in self.events

    def test_retry_fires_on_retry_hook(self):
        policy = RetryPolicy(max_retries=2)
        job = self._make_job(always_fail, retry_policy=policy)
        with pytest.raises(RuntimeError):
            job.run()
        assert "job.on_retry" in self.events
        assert job.status == JobStatus.RETRYING

    def test_enqueue_fires_queue_hooks(self):
        queue = self._make_queue()
        job = self._make_job(add, 3, 4)
        queue.enqueue(job)
        assert "queue.before_enqueue" in self.events
        assert "queue.after_enqueue" in self.events

    def test_dequeue_fires_before_dequeue_hook(self):
        queue = self._make_queue()
        job = self._make_job(add, 1, 1)
        queue.enqueue(job)
        self.events.clear()
        queue.dequeue()
        assert "queue.before_dequeue" in self.events

    def test_process_next_fires_full_lifecycle(self):
        queue = self._make_queue()
        job = self._make_job(add, 5, 6)
        queue.enqueue(job)
        self.events.clear()
        queue.process_next()
        for expected in ["job.before_run", "job.on_success", "job.after_run"]:
            assert expected in self.events

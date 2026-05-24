"""Tests for DeadLetterBackend — routes exhausted jobs to the DLQ."""

import pytest

from batchly.backends.deadletter_backend import DeadLetterBackend
from batchly.backends.memory import InMemoryBackend
from batchly.deadletter import DeadLetterQueue
from batchly.job import Job, JobStatus
from batchly.retry import NoRetry, RetryPolicy


def _job(max_retries: int = 0) -> Job:
    policy = NoRetry() if max_retries == 0 else RetryPolicy(max_retries=max_retries)
    j = Job(func=lambda: None, args=(), kwargs={}, retry_policy=policy)
    return j


class TestDeadLetterBackend:
    def setup_method(self):
        self.inner = InMemoryBackend()
        self.dlq = DeadLetterQueue()
        self.backend = DeadLetterBackend(inner=self.inner, dlq=self.dlq)

    # ------------------------------------------------------------------
    # push / size / peek
    # ------------------------------------------------------------------

    def test_push_delegates_to_inner(self):
        job = _job()
        self.backend.push(job)
        assert self.inner.size() == 1

    def test_peek_delegates_to_inner(self):
        job = _job()
        self.backend.push(job)
        assert self.backend.peek() is job

    def test_size_delegates_to_inner(self):
        self.backend.push(_job())
        self.backend.push(_job())
        assert self.backend.size() == 2

    # ------------------------------------------------------------------
    # pop — healthy job passes through
    # ------------------------------------------------------------------

    def test_pop_pending_job_passes_through(self):
        job = _job()
        self.backend.push(job)
        result = self.backend.pop()
        assert result is job
        assert self.dlq.size() == 0

    # ------------------------------------------------------------------
    # pop — exhausted FAILED job goes to DLQ
    # ------------------------------------------------------------------

    def test_pop_failed_exhausted_job_goes_to_dlq(self):
        job = _job(max_retries=0)
        job.status = JobStatus.FAILED
        job.error = RuntimeError("boom")
        # retries_left defaults to max_retries; with NoRetry can_retry() is False
        self.backend.push(job)

        result = self.backend.pop()

        assert result is None
        assert self.dlq.size() == 1
        entry = self.dlq.find(job.id)
        assert entry is not None
        assert "boom" in entry.reason

    def test_pop_failed_with_retries_remaining_passes_through(self):
        job = _job(max_retries=3)
        job.status = JobStatus.FAILED
        # retries_left still > 0 so can_retry() is True
        self.backend.push(job)

        result = self.backend.pop()

        assert result is job
        assert self.dlq.size() == 0

    # ------------------------------------------------------------------
    # pop on empty queue
    # ------------------------------------------------------------------

    def test_pop_empty_returns_none(self):
        assert self.backend.pop() is None

    # ------------------------------------------------------------------
    # clear
    # ------------------------------------------------------------------

    def test_clear_delegates_to_inner(self):
        self.backend.push(_job())
        self.backend.clear()
        assert self.inner.size() == 0

    # ------------------------------------------------------------------
    # default DLQ created when none supplied
    # ------------------------------------------------------------------

    def test_default_dlq_created(self):
        backend = DeadLetterBackend(inner=InMemoryBackend())
        assert isinstance(backend.dlq, DeadLetterQueue)

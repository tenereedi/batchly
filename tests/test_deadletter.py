"""Unit tests for DeadLetterQueue and DeadLetterEntry."""

from datetime import datetime

import pytest

from batchly.deadletter import DeadLetterEntry, DeadLetterQueue
from batchly.job import Job, JobStatus
from batchly.retry import NoRetry


def _job(name: str = "noop") -> Job:
    return Job(func=lambda: None, args=(), kwargs={}, retry_policy=NoRetry())


class TestDeadLetterQueue:
    def setup_method(self):
        self.dlq = DeadLetterQueue()

    # ------------------------------------------------------------------
    # Basic state
    # ------------------------------------------------------------------

    def test_initial_size_is_zero(self):
        assert self.dlq.size() == 0

    def test_get_all_empty(self):
        assert self.dlq.get_all() == []

    # ------------------------------------------------------------------
    # add
    # ------------------------------------------------------------------

    def test_add_returns_entry(self):
        job = _job()
        entry = self.dlq.add(job, reason="boom")
        assert isinstance(entry, DeadLetterEntry)
        assert entry.job is job
        assert entry.reason == "boom"

    def test_add_increments_size(self):
        self.dlq.add(_job())
        assert self.dlq.size() == 1
        self.dlq.add(_job())
        assert self.dlq.size() == 2

    def test_entry_failed_at_is_datetime(self):
        entry = self.dlq.add(_job())
        assert isinstance(entry.failed_at, datetime)

    # ------------------------------------------------------------------
    # find
    # ------------------------------------------------------------------

    def test_find_existing_job(self):
        job = _job()
        self.dlq.add(job, reason="err")
        found = self.dlq.find(job.id)
        assert found is not None
        assert found.job.id == job.id

    def test_find_missing_returns_none(self):
        assert self.dlq.find("nonexistent-id") is None

    # ------------------------------------------------------------------
    # remove
    # ------------------------------------------------------------------

    def test_remove_existing_returns_true(self):
        job = _job()
        self.dlq.add(job)
        assert self.dlq.remove(job.id) is True
        assert self.dlq.size() == 0

    def test_remove_missing_returns_false(self):
        assert self.dlq.remove("ghost-id") is False

    # ------------------------------------------------------------------
    # clear
    # ------------------------------------------------------------------

    def test_clear_empties_queue(self):
        self.dlq.add(_job())
        self.dlq.add(_job())
        self.dlq.clear()
        assert self.dlq.size() == 0

    # ------------------------------------------------------------------
    # get_all snapshot
    # ------------------------------------------------------------------

    def test_get_all_returns_copy(self):
        self.dlq.add(_job())
        snapshot = self.dlq.get_all()
        snapshot.clear()
        assert self.dlq.size() == 1

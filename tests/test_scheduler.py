"""Tests for batchly.scheduler."""

import time
from datetime import datetime, timedelta

import pytest

from batchly.queue import JobQueue
from batchly.scheduler import Scheduler, ScheduledJob
from batchly.backends.memory import InMemoryBackend


def add(x, y):
    return x + y


class TestScheduler:
    def setup_method(self):
        self.backend = InMemoryBackend()
        self.queue = JobQueue(backend=self.backend)
        self.scheduler = Scheduler(self.queue, poll_interval=0.05)

    def test_repr(self):
        assert "Scheduler" in repr(self.scheduler)
        assert "pending=0" in repr(self.scheduler)

    def test_schedule_adds_pending_job(self):
        self.scheduler.schedule(add, delay=60, x=1, y=2)
        assert self.scheduler.pending_count == 1

    def test_schedule_at_adds_pending_job(self):
        future = datetime.utcnow() + timedelta(hours=1)
        self.scheduler.schedule_at(add, future, 3, 4)
        assert self.scheduler.pending_count == 1

    def test_tick_dispatches_due_job(self):
        past = datetime.utcnow() - timedelta(seconds=1)
        self.scheduler.schedule_at(add, past, 1, 2)
        dispatched = self.scheduler._tick()
        assert dispatched == 1
        assert self.scheduler.pending_count == 0
        assert self.queue.size() == 1

    def test_tick_does_not_dispatch_future_job(self):
        self.scheduler.schedule(add, delay=3600)
        dispatched = self.scheduler._tick()
        assert dispatched == 0
        assert self.scheduler.pending_count == 1
        assert self.queue.size() == 0

    def test_multiple_jobs_only_due_dispatched(self):
        past = datetime.utcnow() - timedelta(seconds=1)
        future = datetime.utcnow() + timedelta(seconds=3600)
        self.scheduler.schedule_at(add, past, 1, 1)
        self.scheduler.schedule_at(add, future, 2, 2)
        dispatched = self.scheduler._tick()
        assert dispatched == 1
        assert self.scheduler.pending_count == 1

    def test_background_thread_dispatches_job(self):
        past = datetime.utcnow() - timedelta(seconds=1)
        self.scheduler.schedule_at(add, past, 5, 5)
        self.scheduler.start()
        time.sleep(0.2)
        self.scheduler.stop()
        assert self.queue.size() == 1
        assert self.scheduler.pending_count == 0

    def test_scheduled_job_is_due_when_past(self):
        from batchly.job import Job
        job = Job(add, 1, 2)
        past = datetime.utcnow() - timedelta(seconds=10)
        sj = ScheduledJob(job, past)
        assert sj.is_due() is True

    def test_scheduled_job_not_due_when_future(self):
        from batchly.job import Job
        job = Job(add, 1, 2)
        future = datetime.utcnow() + timedelta(seconds=10)
        sj = ScheduledJob(job, future)
        assert sj.is_due() is False

    def test_scheduled_job_repr(self):
        from batchly.job import Job
        job = Job(add, 1, 2)
        future = datetime.utcnow() + timedelta(seconds=10)
        sj = ScheduledJob(job, future)
        assert "ScheduledJob" in repr(sj)

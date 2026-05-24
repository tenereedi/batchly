"""Simple scheduled job support for batchly."""

import time
import threading
from datetime import datetime, timedelta
from typing import Callable, Optional

from batchly.job import Job
from batchly.queue import JobQueue


class ScheduledJob:
    """Wraps a Job with scheduling metadata."""

    def __init__(self, job: Job, run_at: datetime):
        self.job = job
        self.run_at = run_at

    def is_due(self) -> bool:
        return datetime.utcnow() >= self.run_at

    def __repr__(self) -> str:
        return f"ScheduledJob(job={self.job!r}, run_at={self.run_at.isoformat()})"


class Scheduler:
    """Polls scheduled jobs and enqueues them when they are due."""

    def __init__(self, queue: JobQueue, poll_interval: float = 1.0):
        self._queue = queue
        self._poll_interval = poll_interval
        self._scheduled: list[ScheduledJob] = []
        self._lock = threading.Lock()
        self._thread: Optional[threading.Thread] = None
        self._running = False

    def schedule(self, func: Callable, delay: float, *args, **kwargs) -> ScheduledJob:
        """Schedule *func* to run after *delay* seconds."""
        run_at = datetime.utcnow() + timedelta(seconds=delay)
        job = Job(func, *args, **kwargs)
        scheduled = ScheduledJob(job, run_at)
        with self._lock:
            self._scheduled.append(scheduled)
        return scheduled

    def schedule_at(self, func: Callable, run_at: datetime, *args, **kwargs) -> ScheduledJob:
        """Schedule *func* to run at a specific UTC datetime."""
        job = Job(func, *args, **kwargs)
        scheduled = ScheduledJob(job, run_at)
        with self._lock:
            self._scheduled.append(scheduled)
        return scheduled

    def _tick(self) -> int:
        """Enqueue all due jobs. Returns the number of jobs dispatched."""
        dispatched = 0
        with self._lock:
            remaining = []
            for sj in self._scheduled:
                if sj.is_due():
                    self._queue.enqueue(sj.job.func, *sj.job.args, **sj.job.kwargs)
                    dispatched += 1
                else:
                    remaining.append(sj)
            self._scheduled = remaining
        return dispatched

    def start(self) -> None:
        """Start the background polling thread."""
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop the background polling thread."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=self._poll_interval * 2)

    def _run(self) -> None:
        while self._running:
            self._tick()
            time.sleep(self._poll_interval)

    @property
    def pending_count(self) -> int:
        with self._lock:
            return len(self._scheduled)

    def __repr__(self) -> str:
        return f"Scheduler(pending={self.pending_count}, interval={self._poll_interval}s)"

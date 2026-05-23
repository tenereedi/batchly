import time
import logging
from typing import Optional
from batchly.queue import JobQueue
from batchly.job import JobStatus

logger = logging.getLogger(__name__)


class Worker:
    """Processes jobs from a JobQueue, with configurable polling and shutdown."""

    def __init__(
        self,
        queue: JobQueue,
        poll_interval: float = 1.0,
        max_jobs: Optional[int] = None,
    ):
        self.queue = queue
        self.poll_interval = poll_interval
        self.max_jobs = max_jobs
        self._running = False
        self.jobs_processed = 0
        self.jobs_failed = 0
        self.jobs_succeeded = 0

    def start(self) -> None:
        """Start processing jobs until stopped or max_jobs reached."""
        self._running = True
        logger.info("Worker started (max_jobs=%s)", self.max_jobs)

        while self._running:
            if self.max_jobs is not None and self.jobs_processed >= self.max_jobs:
                logger.info("Reached max_jobs limit (%d). Stopping.", self.max_jobs)
                break

            job = self.queue.process_next()

            if job is None:
                logger.debug("No jobs available. Polling in %.1fs.", self.poll_interval)
                time.sleep(self.poll_interval)
                continue

            self.jobs_processed += 1

            if job.status == JobStatus.FAILED:
                self.jobs_failed += 1
                logger.warning("Job %s failed: %s", job.id, job.error)
            else:
                self.jobs_succeeded += 1
                logger.info("Job %s completed successfully.", job.id)

        self._running = False
        logger.info(
            "Worker stopped. processed=%d succeeded=%d failed=%d",
            self.jobs_processed,
            self.jobs_succeeded,
            self.jobs_failed,
        )

    def stop(self) -> None:
        """Signal the worker to stop after the current job."""
        logger.info("Worker stop requested.")
        self._running = False

    @property
    def is_running(self) -> bool:
        return self._running

    def __repr__(self) -> str:
        return (
            f"Worker(poll_interval={self.poll_interval}, "
            f"max_jobs={self.max_jobs}, "
            f"jobs_processed={self.jobs_processed})"
        )

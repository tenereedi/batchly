"""Simple CLI entry point for running a batchly worker."""
import argparse
import importlib
import logging
import sys
from batchly.queue import JobQueue
from batchly.retry import NoRetry, RetryPolicy
from batchly.worker import Worker

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def build_retry_policy(args) -> RetryPolicy:
    if args.no_retry:
        return NoRetry()
    return RetryPolicy(
        max_retries=args.max_retries,
        backoff_base=args.backoff_base,
    )


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="batchly",
        description="Run a batchly worker to process queued jobs.",
    )
    parser.add_argument(
        "--max-jobs",
        type=int,
        default=None,
        help="Maximum number of jobs to process before exiting (default: unlimited).",
    )
    parser.add_argument(
        "--poll-interval",
        type=float,
        default=1.0,
        help="Seconds to wait between polls when the queue is empty (default: 1.0).",
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=3,
        help="Maximum retry attempts per job (default: 3).",
    )
    parser.add_argument(
        "--backoff-base",
        type=float,
        default=2.0,
        help="Exponential backoff base in seconds (default: 2.0).",
    )
    parser.add_argument(
        "--no-retry",
        action="store_true",
        help="Disable retries entirely.",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: INFO).",
    )

    args = parser.parse_args(argv)
    logging.getLogger().setLevel(getattr(logging, args.log_level))

    retry_policy = build_retry_policy(args)
    queue = JobQueue(retry_policy=retry_policy)
    worker = Worker(queue, poll_interval=args.poll_interval, max_jobs=args.max_jobs)

    logger.info("Starting batchly worker — %r", worker)
    try:
        worker.start()
    except KeyboardInterrupt:
        logger.info("Interrupted by user. Shutting down.")
        worker.stop()

    sys.exit(0)


if __name__ == "__main__":
    main()

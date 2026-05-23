"""Middleware support for job processing pipeline."""

from typing import Callable, List, Any
from batchly.job import Job


class MiddlewareChain:
    """Manages a chain of middleware functions applied around job execution."""

    def __init__(self):
        self._middlewares: List[Callable] = []

    def add(self, middleware: Callable) -> None:
        """Register a middleware callable.

        A middleware must accept (job, next_handler) and call next_handler(job)
        to continue the chain.
        """
        self._middlewares.append(middleware)

    def wrap(self, handler: Callable[[Job], Any]) -> Callable[[Job], Any]:
        """Wrap a base handler with all registered middlewares."""
        wrapped = handler
        for middleware in reversed(self._middlewares):
            wrapped = _make_wrapper(middleware, wrapped)
        return wrapped

    def __len__(self) -> int:
        return len(self._middlewares)

    def __repr__(self) -> str:
        names = [getattr(m, '__name__', repr(m)) for m in self._middlewares]
        return f"MiddlewareChain([{', '.join(names)}])"


def _make_wrapper(middleware: Callable, next_handler: Callable) -> Callable:
    """Create a closure that binds middleware with its next handler."""
    def wrapper(job: Job) -> Any:
        return middleware(job, next_handler)
    wrapper.__name__ = getattr(middleware, '__name__', 'middleware')
    return wrapper


def logging_middleware(job: Job, next_handler: Callable) -> Any:
    """Built-in middleware that logs job start and completion."""
    import logging
    logger = logging.getLogger('batchly')
    logger.info("Starting job %s (%s)", job.id, job.func.__name__)
    try:
        result = next_handler(job)
        logger.info("Completed job %s", job.id)
        return result
    except Exception as exc:
        logger.error("Job %s failed: %s", job.id, exc)
        raise


def timing_middleware(job: Job, next_handler: Callable) -> Any:
    """Built-in middleware that records job execution duration on the job."""
    import time
    start = time.monotonic()
    try:
        return next_handler(job)
    finally:
        elapsed = time.monotonic() - start
        job.metadata['duration_seconds'] = round(elapsed, 6)

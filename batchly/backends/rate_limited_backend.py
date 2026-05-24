"""A backend decorator that enforces a rate limit on *pop* operations."""

from batchly.backends.base import BaseBackend
from batchly.rate_limiter import RateLimiter, RateLimitExceeded


class RateLimitedBackend(BaseBackend):
    """Wraps another backend and applies a :class:`RateLimiter` to *pop*.

    Parameters
    ----------
    backend:
        The underlying :class:`BaseBackend` instance.
    rate_limiter:
        A :class:`RateLimiter` instance that controls how quickly jobs
        may be dequeued.
    block:
        When True (default) *pop* blocks until a slot is available.
        When False *pop* raises :class:`RateLimitExceeded` if the limit
        is exceeded.
    """

    def __init__(
        self,
        backend: BaseBackend,
        rate_limiter: RateLimiter,
        block: bool = True,
    ):
        self._backend = backend
        self._limiter = rate_limiter
        self._block = block

    # ------------------------------------------------------------------
    # BaseBackend interface
    # ------------------------------------------------------------------

    def push(self, job) -> None:
        self._backend.push(job)

    def pop(self):
        acquired = self._limiter.acquire(block=self._block)
        if not acquired:
            raise RateLimitExceeded(
                "Rate limit exceeded – try again later."
            )
        return self._backend.pop()

    def peek(self):
        return self._backend.peek()

    def size(self) -> int:
        return self._backend.size()

    def is_empty(self) -> bool:
        return self._backend.is_empty()

    def clear(self) -> None:
        self._backend.clear()

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"RateLimitedBackend(backend={self._backend!r}, "
            f"limiter={self._limiter!r})"
        )

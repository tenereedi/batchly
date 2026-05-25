"""Job execution timeout support for batchly."""

import signal
import threading
from contextlib import contextmanager


class JobTimeoutError(Exception):
    """Raised when a job exceeds its allowed execution time."""

    def __init__(self, timeout: float):
        self.timeout = timeout
        super().__init__(f"Job timed out after {timeout}s")


class TimeoutGuard:
    """Enforces a maximum execution time for a callable.

    Uses SIGALRM on Unix platforms; falls back to a threading-based
    approach on platforms where SIGALRM is unavailable (e.g. Windows).
    """

    def __init__(self, seconds: float):
        if seconds <= 0:
            raise ValueError("timeout must be a positive number")
        self.seconds = seconds
        self._use_signal = hasattr(signal, "SIGALRM")

    def __repr__(self) -> str:
        return f"TimeoutGuard(seconds={self.seconds})"

    @contextmanager
    def enforce(self):
        if self._use_signal:
            yield from self._signal_enforce()
        else:
            yield from self._thread_enforce()

    def _signal_enforce(self):
        def _handler(signum, frame):
            raise JobTimeoutError(self.seconds)

        old_handler = signal.signal(signal.SIGALRM, _handler)
        signal.setitimer(signal.ITIMER_REAL, self.seconds)
        try:
            yield
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)
            signal.signal(signal.SIGALRM, old_handler)

    def _thread_enforce(self):
        exc_holder = []
        done_event = threading.Event()

        def _watchdog():
            if not done_event.wait(timeout=self.seconds):
                exc_holder.append(JobTimeoutError(self.seconds))

        t = threading.Thread(target=_watchdog, daemon=True)
        t.start()
        try:
            yield
        finally:
            done_event.set()
            t.join()
            if exc_holder:
                raise exc_holder[0]

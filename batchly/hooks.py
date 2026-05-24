"""Event hooks system for batchly job lifecycle events."""

from collections import defaultdict
from typing import Callable, Dict, List, Any


VALID_EVENTS = {
    "job.before_run",
    "job.after_run",
    "job.on_success",
    "job.on_failure",
    "job.on_retry",
    "queue.before_enqueue",
    "queue.after_enqueue",
    "queue.before_dequeue",
}


class HookRegistry:
    """Registry for event hooks that fire at job lifecycle points."""

    def __init__(self):
        self._hooks: Dict[str, List[Callable]] = defaultdict(list)

    def register(self, event: str, handler: Callable) -> None:
        """Register a handler for a given event."""
        if event not in VALID_EVENTS:
            raise ValueError(f"Unknown event '{event}'. Valid events: {sorted(VALID_EVENTS)}")
        self._hooks[event].append(handler)

    def unregister(self, event: str, handler: Callable) -> None:
        """Remove a previously registered handler."""
        if event in self._hooks:
            self._hooks[event] = [h for h in self._hooks[event] if h != handler]

    def fire(self, event: str, **kwargs: Any) -> None:
        """Fire all handlers registered for an event."""
        for handler in self._hooks.get(event, []):
            handler(**kwargs)

    def handler_count(self, event: str) -> int:
        """Return the number of handlers registered for an event."""
        return len(self._hooks.get(event, []))

    def clear(self, event: str = None) -> None:
        """Clear handlers for a specific event, or all events if none given."""
        if event is None:
            self._hooks.clear()
        else:
            self._hooks.pop(event, None)

    def __repr__(self) -> str:
        total = sum(len(v) for v in self._hooks.values())
        return f"HookRegistry(events={len(self._hooks)}, handlers={total})"


# Global default registry
default_registry = HookRegistry()

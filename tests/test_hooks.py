"""Tests for the HookRegistry event hooks system."""

import pytest
from batchly.hooks import HookRegistry, VALID_EVENTS


class TestHookRegistry:
    def setup_method(self):
        self.registry = HookRegistry()
        self.calls = []

    def _make_handler(self, name):
        def handler(**kwargs):
            self.calls.append((name, kwargs))
        return handler

    def test_repr(self):
        assert "HookRegistry" in repr(self.registry)

    def test_register_valid_event(self):
        handler = self._make_handler("h1")
        self.registry.register("job.before_run", handler)
        assert self.registry.handler_count("job.before_run") == 1

    def test_register_invalid_event_raises(self):
        with pytest.raises(ValueError, match="Unknown event"):
            self.registry.register("job.nonexistent", lambda: None)

    def test_fire_calls_handler(self):
        handler = self._make_handler("fired")
        self.registry.register("job.on_success", handler)
        self.registry.fire("job.on_success", job_id="abc")
        assert len(self.calls) == 1
        assert self.calls[0] == ("fired", {"job_id": "abc"})

    def test_fire_multiple_handlers(self):
        self.registry.register("job.on_failure", self._make_handler("a"))
        self.registry.register("job.on_failure", self._make_handler("b"))
        self.registry.fire("job.on_failure", job_id="x")
        assert len(self.calls) == 2

    def test_fire_unknown_event_does_not_raise(self):
        # Firing an unregistered-but-valid event should be a no-op
        self.registry.fire("job.before_run")
        assert self.calls == []

    def test_unregister_removes_handler(self):
        handler = self._make_handler("h")
        self.registry.register("job.on_retry", handler)
        self.registry.unregister("job.on_retry", handler)
        self.registry.fire("job.on_retry")
        assert self.calls == []

    def test_clear_specific_event(self):
        self.registry.register("job.on_success", self._make_handler("s"))
        self.registry.register("job.on_failure", self._make_handler("f"))
        self.registry.clear("job.on_success")
        assert self.registry.handler_count("job.on_success") == 0
        assert self.registry.handler_count("job.on_failure") == 1

    def test_clear_all_events(self):
        self.registry.register("job.on_success", self._make_handler("s"))
        self.registry.register("job.on_failure", self._make_handler("f"))
        self.registry.clear()
        assert self.registry.handler_count("job.on_success") == 0
        assert self.registry.handler_count("job.on_failure") == 0

    def test_handler_count_unknown_event(self):
        assert self.registry.handler_count("job.before_run") == 0

    def test_all_valid_events_are_registerable(self):
        for event in VALID_EVENTS:
            self.registry.register(event, self._make_handler(event))
            assert self.registry.handler_count(event) == 1
        self.registry.clear()

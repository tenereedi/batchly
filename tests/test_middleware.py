"""Tests for batchly.middleware."""

import pytest
from batchly.middleware import MiddlewareChain, logging_middleware, timing_middleware
from batchly.job import Job


def add(a, b):
    return a + b


def failing_func():
    raise ValueError("boom")


class TestMiddlewareChain:
    def setup_method(self):
        self.chain = MiddlewareChain()

    def test_empty_chain_executes_handler(self):
        job = Job(add, 2, 3)
        handler = self.chain.wrap(lambda j: j.run())
        handler(job)
        assert job.result == 5

    def test_middleware_is_called(self):
        called = []

        def spy_middleware(job, next_handler):
            called.append(job.id)
            return next_handler(job)

        self.chain.add(spy_middleware)
        job = Job(add, 1, 1)
        wrapped = self.chain.wrap(lambda j: j.run())
        wrapped(job)
        assert job.id in called

    def test_middleware_order_is_preserved(self):
        order = []

        def first(job, next_handler):
            order.append('first')
            return next_handler(job)

        def second(job, next_handler):
            order.append('second')
            return next_handler(job)

        self.chain.add(first)
        self.chain.add(second)
        job = Job(add, 0, 0)
        wrapped = self.chain.wrap(lambda j: j.run())
        wrapped(job)
        assert order == ['first', 'second']

    def test_len_reflects_registered_middlewares(self):
        assert len(self.chain) == 0
        self.chain.add(logging_middleware)
        assert len(self.chain) == 1

    def test_repr_contains_middleware_names(self):
        self.chain.add(logging_middleware)
        assert 'logging_middleware' in repr(self.chain)

    def test_exception_propagates_through_chain(self):
        self.chain.add(logging_middleware)
        job = Job(failing_func)
        wrapped = self.chain.wrap(lambda j: j.run())
        with pytest.raises(ValueError, match='boom'):
            wrapped(job)


class TestBuiltinMiddlewares:
    def test_timing_middleware_sets_duration(self):
        job = Job(add, 5, 5)
        chain = MiddlewareChain()
        chain.add(timing_middleware)
        wrapped = chain.wrap(lambda j: j.run())
        wrapped(job)
        assert 'duration_seconds' in job.metadata
        assert job.metadata['duration_seconds'] >= 0

    def test_timing_middleware_sets_duration_on_failure(self):
        job = Job(failing_func)
        chain = MiddlewareChain()
        chain.add(timing_middleware)
        wrapped = chain.wrap(lambda j: j.run())
        with pytest.raises(ValueError):
            wrapped(job)
        assert 'duration_seconds' in job.metadata

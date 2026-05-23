import pytest
from batchly.job import Job, JobStatus
from batchly.backends.memory import InMemoryBackend


def add(a, b):
    return a + b


class TestInMemoryBackend:
    def setup_method(self):
        self.backend = InMemoryBackend()

    def test_initial_size_is_zero(self):
        assert self.backend.size() == 0
        assert len(self.backend) == 0

    def test_push_increases_size(self):
        job = Job(add, args=[1, 2])
        self.backend.push(job)
        assert self.backend.size() == 1

    def test_pop_returns_job_and_decreases_size(self):
        job = Job(add, args=[1, 2])
        self.backend.push(job)
        result = self.backend.pop()
        assert result is job
        assert self.backend.size() == 0

    def test_pop_empty_returns_none(self):
        assert self.backend.pop() is None

    def test_peek_returns_job_without_removing(self):
        job = Job(add, args=[1, 2])
        self.backend.push(job)
        peeked = self.backend.peek()
        assert peeked is job
        assert self.backend.size() == 1

    def test_peek_empty_returns_none(self):
        assert self.backend.peek() is None

    def test_fifo_order(self):
        job1 = Job(add, args=[1, 2])
        job2 = Job(add, args=[3, 4])
        self.backend.push(job1)
        self.backend.push(job2)
        assert self.backend.pop() is job1
        assert self.backend.pop() is job2

    def test_clear_empties_backend(self):
        self.backend.push(Job(add, args=[1, 2]))
        self.backend.push(Job(add, args=[3, 4]))
        self.backend.clear()
        assert self.backend.size() == 0

    def test_repr_contains_class_and_size(self):
        r = repr(self.backend)
        assert "InMemoryBackend" in r
        assert "size=0" in r

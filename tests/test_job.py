import pytest
from batchly.job import Job, JobStatus


def add(a, b):
    return a + b


def failing_func():
    raise ValueError("intentional failure")


class TestJob:
    def test_default_status_is_pending(self):
        job = Job(func=add, args=(1, 2))
        assert job.status == JobStatus.PENDING

    def test_unique_job_ids(self):
        job1 = Job(func=add)
        job2 = Job(func=add)
        assert job1.job_id != job2.job_id

    def test_successful_run(self):
        job = Job(func=add, args=(3, 4))
        result = job.run()
        assert result == 7
        assert job.status == JobStatus.SUCCESS
        assert job.result == 7
        assert job.error is None
        assert job.started_at is not None
        assert job.finished_at is not None

    def test_failed_run_exhausts_retries(self):
        job = Job(func=failing_func, max_retries=0)
        with pytest.raises(ValueError):
            job.run()
        assert job.status == JobStatus.FAILED
        assert "intentional failure" in job.error

    def test_retrying_status_on_first_failure(self):
        job = Job(func=failing_func, max_retries=2)
        with pytest.raises(ValueError):
            job.run()
        assert job.status == JobStatus.RETRYING
        assert job.retry_count == 1
        assert job.can_retry is True

    def test_can_retry_false_after_max_retries(self):
        job = Job(func=failing_func, max_retries=1)
        with pytest.raises(ValueError):
            job.run()
        assert job.can_retry is True
        with pytest.raises(ValueError):
            job.run()
        assert job.status == JobStatus.FAILED
        assert job.can_retry is False

    def test_repr_contains_key_info(self):
        job = Job(func=add)
        r = repr(job)
        assert "add" in r
        assert job.job_id in r
        assert "pending" in r

    def test_kwargs_passed_correctly(self):
        def greet(name, greeting="Hello"):
            return f"{greeting}, {name}!"

        job = Job(func=greet, args=("World",), kwargs={"greeting": "Hi"})
        assert job.run() == "Hi, World!"

"""Tests for batchly retry policies."""

import pytest
from batchly.retry import RetryPolicy, NoRetry, LinearRetry, ExponentialBackoff


class TestRetryPolicy:
    def test_default_max_retries(self):
        policy = RetryPolicy()
        assert policy.max_retries == 3

    def test_should_retry_within_limit(self):
        policy = RetryPolicy(max_retries=3)
        assert policy.should_retry(0) is True
        assert policy.should_retry(1) is True
        assert policy.should_retry(2) is True

    def test_should_not_retry_at_limit(self):
        policy = RetryPolicy(max_retries=3)
        assert policy.should_retry(3) is False
        assert policy.should_retry(10) is False

    def test_should_retry_matching_exception(self):
        policy = RetryPolicy(max_retries=3, exceptions=(ValueError,))
        assert policy.should_retry(1, ValueError("oops")) is True

    def test_should_not_retry_non_matching_exception(self):
        policy = RetryPolicy(max_retries=3, exceptions=(ValueError,))
        assert policy.should_retry(1, TypeError("wrong type")) is False

    def test_get_delay_no_backoff(self):
        policy = RetryPolicy(delay=2.0, backoff=1.0)
        assert policy.get_delay(1) == pytest.approx(2.0)
        assert policy.get_delay(2) == pytest.approx(2.0)
        assert policy.get_delay(3) == pytest.approx(2.0)

    def test_get_delay_with_backoff(self):
        policy = RetryPolicy(delay=1.0, backoff=2.0)
        assert policy.get_delay(1) == pytest.approx(1.0)
        assert policy.get_delay(2) == pytest.approx(2.0)
        assert policy.get_delay(3) == pytest.approx(4.0)


class TestNoRetry:
    def test_never_retries(self):
        policy = NoRetry()
        assert policy.should_retry(0) is False

    def test_max_retries_is_zero(self):
        policy = NoRetry()
        assert policy.max_retries == 0


class TestLinearRetry:
    def test_constant_delay(self):
        policy = LinearRetry(max_retries=4, delay=0.5)
        assert policy.get_delay(1) == pytest.approx(0.5)
        assert policy.get_delay(2) == pytest.approx(0.5)
        assert policy.get_delay(3) == pytest.approx(0.5)

    def test_respects_max_retries(self):
        policy = LinearRetry(max_retries=2)
        assert policy.should_retry(1) is True
        assert policy.should_retry(2) is False


class TestExponentialBackoff:
    def test_doubles_delay(self):
        policy = ExponentialBackoff(initial_delay=1.0, backoff=2.0)
        assert policy.get_delay(1) == pytest.approx(1.0)
        assert policy.get_delay(2) == pytest.approx(2.0)
        assert policy.get_delay(3) == pytest.approx(4.0)

    def test_default_backoff_factor(self):
        policy = ExponentialBackoff()
        assert policy.backoff == 2.0

    def test_respects_max_retries(self):
        policy = ExponentialBackoff(max_retries=3)
        assert policy.should_retry(2) is True
        assert policy.should_retry(3) is False

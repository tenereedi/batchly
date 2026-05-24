"""Tests for the MetricsCollector and JobMetrics classes."""

import pytest
from batchly.metrics import JobMetrics, MetricsCollector


class TestJobMetrics:
    def test_default_values_are_zero(self):
        m = JobMetrics()
        assert m.total_enqueued == 0
        assert m.total_succeeded == 0
        assert m.total_failed == 0
        assert m.total_retried == 0
        assert m.total_discarded == 0

    def test_total_processed(self):
        m = JobMetrics(total_succeeded=3, total_failed=2)
        assert m.total_processed == 5

    def test_success_rate_zero_when_no_processed(self):
        m = JobMetrics()
        assert m.success_rate == 0.0

    def test_success_rate_calculation(self):
        m = JobMetrics(total_succeeded=8, total_failed=2)
        assert m.success_rate == pytest.approx(0.8)

    def test_repr(self):
        m = JobMetrics(total_enqueued=1)
        assert "JobMetrics" in repr(m)
        assert "enqueued=1" in repr(m)


class TestMetricsCollector:
    def setup_method(self):
        self.collector = MetricsCollector()

    def test_initial_snapshot_is_empty(self):
        snap = self.collector.snapshot()
        assert snap.total_enqueued == 0
        assert snap.total_succeeded == 0

    def test_record_enqueued(self):
        self.collector.record_enqueued()
        self.collector.record_enqueued()
        assert self.collector.snapshot().total_enqueued == 2

    def test_record_success(self):
        self.collector.record_success()
        assert self.collector.snapshot().total_succeeded == 1

    def test_record_failure_increments_count(self):
        self.collector.record_failure(ValueError("oops"))
        snap = self.collector.snapshot()
        assert snap.total_failed == 1

    def test_record_failure_tracks_exception_type(self):
        self.collector.record_failure(ValueError("a"))
        self.collector.record_failure(ValueError("b"))
        self.collector.record_failure(RuntimeError("c"))
        snap = self.collector.snapshot()
        assert snap.errors_by_type["ValueError"] == 2
        assert snap.errors_by_type["RuntimeError"] == 1

    def test_record_retry(self):
        self.collector.record_retry()
        assert self.collector.snapshot().total_retried == 1

    def test_record_discarded(self):
        self.collector.record_discarded()
        assert self.collector.snapshot().total_discarded == 1

    def test_snapshot_is_independent_copy(self):
        snap = self.collector.snapshot()
        self.collector.record_success()
        assert snap.total_succeeded == 0

    def test_reset_clears_all_metrics(self):
        self.collector.record_enqueued()
        self.collector.record_success()
        self.collector.reset()
        snap = self.collector.snapshot()
        assert snap.total_enqueued == 0
        assert snap.total_succeeded == 0

    def test_repr(self):
        assert "MetricsCollector" in repr(self.collector)

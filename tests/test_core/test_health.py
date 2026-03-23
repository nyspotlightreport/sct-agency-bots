"""Tests for core.health module."""

import pytest
from core.health import HealthTracker


class TestHealthTracker:
    def test_initial_state_is_healthy(self):
        ht = HealthTracker("test-health")
        assert ht.is_healthy() is True

    def test_record_success(self):
        ht = HealthTracker("test-health-success")
        failures = ht.record_run(success=True, details="ok", items_processed=5)
        assert failures == 0

    def test_record_failure(self):
        ht = HealthTracker("test-health-fail")
        failures = ht.record_run(success=False, details="error")
        assert failures == 1

    def test_consecutive_failures(self):
        ht = HealthTracker("test-health-consec")
        ht.record_run(success=False, details="err1")
        ht.record_run(success=False, details="err2")
        failures = ht.record_run(success=False, details="err3")
        assert failures == 3
        assert ht.is_healthy() is False

    def test_recovery_resets_failures(self):
        ht = HealthTracker("test-health-recover")
        ht.record_run(success=False, details="err")
        ht.record_run(success=False, details="err")
        ht.record_run(success=True, details="ok")
        assert ht.is_healthy() is True

    def test_stats(self):
        ht = HealthTracker("test-health-stats")
        ht.record_run(success=True, items_processed=10)
        stats = ht.get_stats()
        assert stats["total_runs"] == 1
        assert stats["success_rate"] == 100.0

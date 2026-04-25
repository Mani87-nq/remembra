"""Tests for cold archive and adaptive threshold features."""

import pytest
from unittest.mock import MagicMock

from remembra.temporal.adaptive import (
    AdaptiveConfig,
    AdaptiveThresholdManager,
    SessionContext,
    SessionMode,
    create_adaptive_manager,
)


class TestSessionModes:
    """Test session mode behavior."""

    def test_exploratory_lowers_threshold(self):
        """Exploratory mode should have lower threshold to keep more memories."""
        manager = AdaptiveThresholdManager(MagicMock())

        # Simulate past warmup
        for _i in range(15):
            manager.record_query("user1", result_count=5)

        manager.set_mode("user1", SessionMode.BALANCED)
        balanced = manager.calculate_threshold("user1")

        manager.set_mode("user1", SessionMode.EXPLORATORY)
        exploratory = manager.calculate_threshold("user1")

        assert exploratory < balanced, "Exploratory should have lower threshold"

    def test_operational_raises_threshold(self):
        """Operational mode should have higher threshold to prune more."""
        manager = AdaptiveThresholdManager(MagicMock())

        # Simulate past warmup
        for _i in range(15):
            manager.record_query("user1", result_count=5)

        manager.set_mode("user1", SessionMode.BALANCED)
        balanced = manager.calculate_threshold("user1")

        manager.set_mode("user1", SessionMode.OPERATIONAL)
        operational = manager.calculate_threshold("user1")

        assert operational > balanced, "Operational should have higher threshold"

    def test_warmup_uses_conservative_threshold(self):
        """During warmup, threshold should be conservative (low)."""
        config = AdaptiveConfig(warmup_threshold=0.05)
        manager = AdaptiveThresholdManager(MagicMock(), config=config)

        # First few queries should be in warmup
        manager.record_query("user1", result_count=5)

        session = manager.get_session("user1")
        assert session.is_warmup

        threshold = manager.calculate_threshold("user1")
        assert threshold == config.warmup_threshold


class TestSessionContext:
    """Test session context tracking."""

    def test_session_creation(self):
        """New session should have default values."""
        ctx = SessionContext(user_id="test", project_id="default")

        assert ctx.is_warmup
        assert ctx.queries_count == 0
        assert ctx.avg_quality == 0.5  # Default when no scores

    def test_quality_tracking(self):
        """Quality scores should be tracked correctly."""
        ctx = SessionContext(user_id="test", project_id="default")
        ctx.quality_scores = [0.8, 0.9, 0.7]

        assert ctx.avg_quality == pytest.approx(0.8, rel=0.01)

    def test_results_tracking(self):
        """Results per query should be tracked."""
        ctx = SessionContext(user_id="test", project_id="default")
        ctx.queries_count = 10
        ctx.total_results = 50

        assert ctx.avg_results_per_query == 5.0


class TestAdaptiveThresholdCalculation:
    """Test threshold calculation logic."""

    def test_quality_affects_threshold(self):
        """Higher quality scores should allow higher thresholds."""
        manager = AdaptiveThresholdManager(MagicMock())

        # Exit warmup with low quality
        for _i in range(15):
            manager.record_query("low_user", result_count=5, quality_score=0.3)

        low_threshold = manager.calculate_threshold("low_user")

        # Exit warmup with high quality
        for _i in range(15):
            manager.record_query("high_user", result_count=5, quality_score=0.9)

        high_threshold = manager.calculate_threshold("high_user")

        # High quality should allow higher threshold (more selective)
        assert high_threshold > low_threshold

    def test_density_adjustment(self):
        """High memory density should increase threshold."""
        config = AdaptiveConfig(high_density_threshold=100, density_threshold_boost=0.02)
        manager = AdaptiveThresholdManager(MagicMock(), config=config)

        # Exit warmup
        for _i in range(15):
            manager.record_query("user1", result_count=5)

        manager.set_mode("user1", SessionMode.BALANCED)

        low_density = manager.calculate_threshold("user1", memory_count=50)
        high_density = manager.calculate_threshold("user1", memory_count=500)

        assert high_density > low_density

    def test_threshold_bounds(self):
        """Threshold should always be within configured bounds."""
        config = AdaptiveConfig(min_threshold=0.05, max_threshold=0.3)
        manager = AdaptiveThresholdManager(MagicMock(), config=config)

        # Exit warmup
        for _i in range(15):
            manager.record_query("user1", result_count=5)

        # Try extreme mode
        manager.set_mode("user1", SessionMode.OPERATIONAL)
        threshold = manager.calculate_threshold("user1", memory_count=10000)

        assert threshold >= config.min_threshold
        assert threshold <= config.max_threshold


class TestSessionPersistence:
    """Test session state persistence (requires async)."""

    @pytest.mark.asyncio
    async def test_session_reset(self):
        """Reset should clear all session state."""
        manager = AdaptiveThresholdManager(MagicMock())

        # Build up session state
        for _i in range(20):
            manager.record_query("user1", result_count=5, quality_score=0.8)

        session_before = manager.get_session("user1")
        assert session_before.queries_count == 20

        # Reset
        manager.reset_session("user1")

        session_after = manager.get_session("user1")
        assert session_after.queries_count == 0
        assert session_after.is_warmup


class TestCreateAdaptiveManager:
    """Test factory function."""

    def test_create_with_defaults(self):
        """Factory should create manager with default config."""
        manager = create_adaptive_manager(MagicMock())

        assert isinstance(manager, AdaptiveThresholdManager)
        assert manager.config.base_prune_threshold == 0.1


class TestSessionStats:
    """Test session statistics generation."""

    def test_stats_structure(self):
        """Stats should contain all expected fields."""
        manager = AdaptiveThresholdManager(MagicMock())

        for _i in range(5):
            manager.record_query("user1", result_count=3, quality_score=0.7)

        stats = manager.get_session_stats("user1")

        assert "user_id" in stats
        assert "project_id" in stats
        assert "mode" in stats
        assert "is_warmup" in stats
        assert "queries_count" in stats
        assert "current_threshold" in stats
        assert "avg_quality" in stats

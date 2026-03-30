"""Temporal features: TTL, decay, adaptive thresholds, and historical queries."""

from remembra.temporal.adaptive import (
    AdaptiveConfig,
    AdaptiveThresholdManager,
    SessionContext,
    SessionMode,
    create_adaptive_manager,
    get_adaptive_threshold,
)
from remembra.temporal.decay import (
    DecayConfig,
    calculate_decay_factor,
    calculate_relevance_score,
    should_prune,
)
from remembra.temporal.ttl import calculate_expires_at, parse_ttl

__all__ = [
    # Decay
    "calculate_relevance_score",
    "calculate_decay_factor",
    "should_prune",
    "DecayConfig",
    # TTL
    "parse_ttl",
    "calculate_expires_at",
    # Adaptive thresholds
    "AdaptiveThresholdManager",
    "AdaptiveConfig",
    "SessionContext",
    "SessionMode",
    "create_adaptive_manager",
    "get_adaptive_threshold",
]

"""
Adaptive threshold system for intelligent memory pruning.

Dynamically adjusts prune thresholds based on:
- Session context (exploratory vs operational mode)
- Query patterns and result satisfaction
- Warm-up phase calibration
- User-specific memory density

This prevents aggressive pruning during exploration while allowing
tighter thresholds during focused operational work.
"""

import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

import structlog

log = structlog.get_logger(__name__)


class SessionMode(Enum):
    """Session operating modes affecting threshold behavior."""
    
    EXPLORATORY = "exploratory"  # Browsing, researching - keep more memories
    OPERATIONAL = "operational"  # Focused work - tighter thresholds
    BALANCED = "balanced"        # Default adaptive behavior
    WARMUP = "warmup"           # Initial calibration phase


@dataclass
class AdaptiveConfig:
    """Configuration for adaptive threshold system."""
    
    # Base thresholds
    base_prune_threshold: float = 0.1
    min_threshold: float = 0.05      # Never prune above this relevance
    max_threshold: float = 0.3       # Maximum threshold even in operational mode
    
    # Mode multipliers
    exploratory_multiplier: float = 0.5   # Lower threshold = keep more
    operational_multiplier: float = 1.5   # Higher threshold = prune more
    
    # Warm-up configuration
    warmup_queries: int = 10          # Queries before calibration
    warmup_threshold: float = 0.05    # Conservative during warmup
    
    # Session tracking
    session_timeout_minutes: int = 30
    quality_weight: float = 0.3       # How much result quality affects threshold
    
    # Density-based adjustment
    high_density_threshold: int = 1000    # Memories considered "high density"
    density_threshold_boost: float = 0.02  # Extra threshold per 1000 memories


@dataclass
class SessionContext:
    """Tracks the current session context for adaptive thresholds."""
    
    user_id: str
    project_id: str = "default"
    mode: SessionMode = SessionMode.BALANCED
    session_start: datetime = field(default_factory=datetime.utcnow)
    queries_count: int = 0
    total_results: int = 0
    quality_scores: list[float] = field(default_factory=list)
    last_query: datetime | None = None
    current_threshold: float = 0.1
    
    @property
    def is_warmup(self) -> bool:
        """Check if still in warm-up phase."""
        return self.queries_count < 10
    
    @property
    def avg_quality(self) -> float:
        """Average quality score from recent queries."""
        if not self.quality_scores:
            return 0.5
        # Use last 20 scores for recent average
        recent = self.quality_scores[-20:]
        return sum(recent) / len(recent)
    
    @property
    def avg_results_per_query(self) -> float:
        """Average number of results per query."""
        if self.queries_count == 0:
            return 0
        return self.total_results / self.queries_count


class AdaptiveThresholdManager:
    """
    Manages adaptive pruning thresholds based on session context.
    
    Key behaviors:
    1. WARMUP: Conservative threshold until enough queries to calibrate
    2. EXPLORATORY: Lower threshold, keep more memories accessible
    3. OPERATIONAL: Higher threshold, prune more aggressively
    4. BALANCED: Adapts based on query patterns and result quality
    """
    
    def __init__(
        self,
        database: Any,  # Database instance for persistence
        config: AdaptiveConfig | None = None,
    ) -> None:
        self.db = database
        self.config = config or AdaptiveConfig()
        self._sessions: dict[str, SessionContext] = {}
    
    def _session_key(self, user_id: str, project_id: str = "default") -> str:
        """Generate session lookup key."""
        return f"{user_id}:{project_id}"
    
    def get_session(
        self,
        user_id: str,
        project_id: str = "default",
    ) -> SessionContext:
        """Get or create a session context."""
        key = self._session_key(user_id, project_id)
        
        if key in self._sessions:
            session = self._sessions[key]
            # Check if session expired
            if session.last_query:
                elapsed = datetime.utcnow() - session.last_query
                if elapsed > timedelta(minutes=self.config.session_timeout_minutes):
                    # Session expired, create new one
                    session = SessionContext(user_id=user_id, project_id=project_id)
                    self._sessions[key] = session
        else:
            session = SessionContext(user_id=user_id, project_id=project_id)
            self._sessions[key] = session
        
        return session
    
    def set_mode(
        self,
        user_id: str,
        mode: SessionMode | str,
        project_id: str = "default",
    ) -> None:
        """Explicitly set session mode."""
        session = self.get_session(user_id, project_id)
        if isinstance(mode, str):
            mode = SessionMode(mode)
        session.mode = mode
        
        log.info(
            "session_mode_changed",
            user_id=user_id,
            project_id=project_id,
            mode=mode.value,
        )
    
    def record_query(
        self,
        user_id: str,
        result_count: int,
        quality_score: float | None = None,
        project_id: str = "default",
    ) -> None:
        """
        Record a query for threshold calibration.
        
        Args:
            user_id: User who made the query
            result_count: Number of results returned
            quality_score: User feedback score (0-1), if available
            project_id: Project namespace
        """
        session = self.get_session(user_id, project_id)
        session.queries_count += 1
        session.total_results += result_count
        session.last_query = datetime.utcnow()
        
        if quality_score is not None:
            session.quality_scores.append(quality_score)
        
        # Recalculate threshold
        new_threshold = self.calculate_threshold(user_id, project_id)
        session.current_threshold = new_threshold
    
    def calculate_threshold(
        self,
        user_id: str,
        project_id: str = "default",
        memory_count: int | None = None,
    ) -> float:
        """
        Calculate the current adaptive prune threshold.
        
        The threshold determines the minimum relevance score a memory
        must have to avoid being pruned.
        
        Args:
            user_id: User to calculate for
            project_id: Project namespace
            memory_count: Total memories (for density adjustment)
        
        Returns:
            Adaptive prune threshold (0.0 - 1.0)
        """
        session = self.get_session(user_id, project_id)
        cfg = self.config
        
        # Start with base threshold
        threshold = cfg.base_prune_threshold
        
        # 1. Warm-up phase: be very conservative
        if session.is_warmup:
            threshold = cfg.warmup_threshold
            log.debug(
                "warmup_threshold",
                user_id=user_id,
                queries=session.queries_count,
                threshold=threshold,
            )
            return threshold
        
        # 2. Apply mode multiplier
        mode_multipliers = {
            SessionMode.EXPLORATORY: cfg.exploratory_multiplier,
            SessionMode.OPERATIONAL: cfg.operational_multiplier,
            SessionMode.BALANCED: 1.0,
            SessionMode.WARMUP: 0.5,
        }
        threshold *= mode_multipliers.get(session.mode, 1.0)
        
        # 3. Adjust based on result quality
        # If quality is low, lower threshold to return more results
        # If quality is high, can afford to be more selective
        if session.quality_scores:
            quality_factor = 1.0 + (session.avg_quality - 0.5) * cfg.quality_weight
            threshold *= quality_factor
        
        # 4. Auto-detect mode from query patterns
        if session.mode == SessionMode.BALANCED:
            # High query rate with low results = exploratory
            # Low query rate with focused results = operational
            if session.queries_count > 20:
                if session.avg_results_per_query < 3:
                    # Few results, might be missing things - lower threshold
                    threshold *= 0.8
                elif session.avg_results_per_query > 15:
                    # Too many results, can be more selective
                    threshold *= 1.1
        
        # 5. Density-based adjustment
        if memory_count and memory_count > cfg.high_density_threshold:
            density_boost = (memory_count / cfg.high_density_threshold) * cfg.density_threshold_boost
            threshold += density_boost
        
        # 6. Clamp to valid range
        threshold = max(cfg.min_threshold, min(cfg.max_threshold, threshold))
        
        return round(threshold, 4)
    
    def get_effective_threshold(
        self,
        user_id: str,
        project_id: str = "default",
    ) -> float:
        """Get the current effective threshold for a user."""
        session = self.get_session(user_id, project_id)
        return session.current_threshold
    
    def get_session_stats(
        self,
        user_id: str,
        project_id: str = "default",
    ) -> dict[str, Any]:
        """Get statistics about the current session."""
        session = self.get_session(user_id, project_id)
        
        return {
            "user_id": user_id,
            "project_id": project_id,
            "mode": session.mode.value,
            "is_warmup": session.is_warmup,
            "queries_count": session.queries_count,
            "total_results": session.total_results,
            "avg_results_per_query": round(session.avg_results_per_query, 2),
            "avg_quality": round(session.avg_quality, 3),
            "current_threshold": session.current_threshold,
            "session_duration_minutes": (
                (datetime.utcnow() - session.session_start).total_seconds() / 60
            ),
            "base_threshold": self.config.base_prune_threshold,
        }
    
    async def persist_session(
        self,
        user_id: str,
        project_id: str = "default",
    ) -> None:
        """Persist session state to database."""
        session = self.get_session(user_id, project_id)
        
        try:
            await self.db.conn.execute(
                """
                INSERT INTO adaptive_thresholds (
                    id, user_id, project_id, session_mode, base_threshold,
                    current_threshold, session_start, queries_this_session,
                    avg_result_quality, last_calibration, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(user_id, project_id) DO UPDATE SET
                    session_mode = excluded.session_mode,
                    current_threshold = excluded.current_threshold,
                    queries_this_session = excluded.queries_this_session,
                    avg_result_quality = excluded.avg_result_quality,
                    last_calibration = excluded.last_calibration,
                    updated_at = excluded.updated_at
                """,
                (
                    f"{user_id}:{project_id}",
                    user_id,
                    project_id,
                    session.mode.value,
                    self.config.base_prune_threshold,
                    session.current_threshold,
                    session.session_start.isoformat(),
                    session.queries_count,
                    session.avg_quality if session.quality_scores else None,
                    datetime.utcnow().isoformat(),
                    datetime.utcnow().isoformat(),
                    datetime.utcnow().isoformat(),
                ),
            )
            await self.db.conn.commit()
        except Exception as e:
            log.warning("persist_session_failed", user_id=user_id, error=str(e))
    
    async def load_session(
        self,
        user_id: str,
        project_id: str = "default",
    ) -> SessionContext | None:
        """Load persisted session state from database."""
        try:
            cursor = await self.db.conn.execute(
                """
                SELECT * FROM adaptive_thresholds
                WHERE user_id = ? AND project_id = ?
                """,
                (user_id, project_id),
            )
            row = await cursor.fetchone()
            
            if row:
                data = dict(row)
                session = SessionContext(
                    user_id=user_id,
                    project_id=project_id,
                    mode=SessionMode(data.get("session_mode", "balanced")),
                    queries_count=data.get("queries_this_session", 0),
                    current_threshold=data.get("current_threshold", 0.1),
                )
                
                if data.get("session_start"):
                    session.session_start = datetime.fromisoformat(data["session_start"])
                
                self._sessions[self._session_key(user_id, project_id)] = session
                return session
                
        except Exception as e:
            log.warning("load_session_failed", user_id=user_id, error=str(e))
        
        return None
    
    def reset_session(
        self,
        user_id: str,
        project_id: str = "default",
    ) -> None:
        """Reset session context (start fresh calibration)."""
        key = self._session_key(user_id, project_id)
        if key in self._sessions:
            del self._sessions[key]
        
        log.info("session_reset", user_id=user_id, project_id=project_id)


# Convenience functions for integration
def create_adaptive_manager(database: Any) -> AdaptiveThresholdManager:
    """Create an adaptive threshold manager with default config."""
    return AdaptiveThresholdManager(database)


def get_adaptive_threshold(
    manager: AdaptiveThresholdManager,
    user_id: str,
    project_id: str = "default",
) -> float:
    """Quick helper to get current threshold."""
    return manager.calculate_threshold(user_id, project_id)

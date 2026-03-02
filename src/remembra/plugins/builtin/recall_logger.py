"""Recall logger plugin — logs every recall query for analytics.

Creates an in-memory or SQLite-backed log of what queries are being
asked, how many results they return, and which memories are surfaced.
Useful for understanding user behaviour and improving recall quality.

Configuration::

    {
        "log_to_db": true,
        "log_queries": true,
        "log_results": false
    }
"""

from __future__ import annotations

import logging
from typing import Any

from remembra.plugins.base import RecallEvent, RemembraPlugin

logger = logging.getLogger(__name__)


class RecallLoggerPlugin(RemembraPlugin):
    """Logs recall queries and results for analytics."""

    name = "recall-logger"
    version = "1.0.0"
    description = "Log recall queries for analytics and debugging"
    author = "Remembra"

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(config)
        self._log_queries = self.config.get("log_queries", True)
        self._log_results = self.config.get("log_results", False)
        self._queries: list[dict[str, Any]] = []

    async def on_recall(self, event: RecallEvent) -> RecallEvent:
        entry: dict[str, Any] = {
            "user_id": event.user_id,
            "project_id": event.project_id,
            "result_count": len(event.results),
        }

        if self._log_queries:
            entry["query"] = event.query

        if self._log_results:
            entry["result_ids"] = [r.get("id", "") for r in event.results[:10]]

        self._queries.append(entry)

        # Keep buffer bounded
        if len(self._queries) > 10000:
            self._queries = self._queries[-5000:]

        logger.debug(
            "Recall logged: user=%s results=%d query=%s",
            event.user_id,
            len(event.results),
            event.query[:80] if self._log_queries else "...",
        )
        return event

    def get_stats(self) -> dict[str, Any]:
        """Return recall statistics."""
        total = len(self._queries)
        if total == 0:
            return {"total_queries": 0}

        avg_results = sum(q["result_count"] for q in self._queries) / total
        zero_results = sum(1 for q in self._queries if q["result_count"] == 0)

        return {
            "total_queries": total,
            "avg_results": round(avg_results, 2),
            "zero_result_queries": zero_results,
            "zero_result_rate": round(zero_results / total, 3) if total else 0,
        }

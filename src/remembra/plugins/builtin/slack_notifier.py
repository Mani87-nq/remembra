"""Slack notifier plugin — posts to Slack when important memories are stored.

Configuration::

    {
        "webhook_url": "https://hooks.slack.com/services/...",
        "channel": "#ai-memories",
        "notify_on_conflict": true,
        "min_facts": 1
    }
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from remembra.plugins.base import (
    ConflictEvent,
    MemoryEvent,
    RemembraPlugin,
)

logger = logging.getLogger(__name__)


class SlackNotifierPlugin(RemembraPlugin):
    """Posts Slack messages when memories are stored or conflicts detected."""

    name = "slack-notifier"
    version = "1.0.0"
    description = "Send Slack notifications for memory lifecycle events"
    author = "Remembra"

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(config)
        self._webhook_url = self.config.get("webhook_url", "")
        self._channel = self.config.get("channel", "#ai-memories")
        self._notify_on_conflict = self.config.get("notify_on_conflict", True)
        self._min_facts = self.config.get("min_facts", 1)

    async def on_activate(self) -> None:
        if not self._webhook_url:
            raise ValueError("Slack webhook_url is required in plugin config")
        logger.info("Slack notifier activated for channel %s", self._channel)

    async def on_store(self, event: MemoryEvent) -> MemoryEvent:
        if len(event.extracted_facts) >= self._min_facts:
            text = (
                f":brain: *New memory stored*\n"
                f"User: `{event.user_id}` | Project: `{event.project_id}`\n"
                f"Facts: {len(event.extracted_facts)}\n"
                f"Preview: {event.content[:200]}"
            )
            await self._send(text)
        return event

    async def on_conflict(self, event: ConflictEvent) -> ConflictEvent:
        if self._notify_on_conflict:
            text = (
                f":warning: *Memory conflict detected*\n"
                f"User: `{event.user_id}` | Strategy: `{event.strategy_applied}`\n"
                f"New: {event.new_fact[:150]}\n"
                f"Existing: {event.existing_content[:150]}\n"
                f"Similarity: {event.similarity_score:.2f}"
            )
            await self._send(text)
        return event

    async def _send(self, text: str) -> None:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                await client.post(
                    self._webhook_url,
                    json={"text": text, "channel": self._channel},
                )
        except Exception as e:
            logger.warning("Slack notification failed: %s", e)

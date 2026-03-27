"""Auto-tagger plugin — automatically adds metadata tags to stored memories.

Analyses memory content and appends tags like ``topic:finance``,
``sentiment:positive``, ``priority:high`` to the metadata dict.

Configuration::

    {
        "tag_prefix": "auto",
        "min_content_length": 20,
        "enable_sentiment": true,
        "enable_topic": true,
        "custom_rules": [
            {"pattern": "(?i)\\bbudget\\b|\\bexpense\\b", "tag": "topic:finance"},
            {"pattern": "(?i)\\bdeadline\\b|\\burgent\\b", "tag": "priority:high"}
        ]
    }
"""

from __future__ import annotations

import logging
import re
from typing import Any

from remembra.plugins.base import MemoryEvent, RemembraPlugin

logger = logging.getLogger(__name__)


# Simple keyword lists for tagging (no LLM needed)
_TOPIC_PATTERNS: dict[str, str] = {
    r"(?i)\b(code|function|class|api|bug|deploy)\b": "topic:engineering",
    r"(?i)\b(meeting|standup|agenda|sync|call)\b": "topic:meetings",
    r"(?i)\b(budget|expense|revenue|invoice|payment)\b": "topic:finance",
    r"(?i)\b(hire|candidate|interview|onboard)\b": "topic:recruiting",
    r"(?i)\b(launch|release|ship|milestone)\b": "topic:product",
    r"(?i)\b(customer|feedback|support|ticket)\b": "topic:support",
    r"(?i)\b(research|paper|study|experiment)\b": "topic:research",
}

_PRIORITY_PATTERNS: dict[str, str] = {
    r"(?i)\b(urgent|asap|critical|blocker)\b": "priority:high",
    r"(?i)\b(important|key|essential)\b": "priority:medium",
}

_SENTIMENT_POSITIVE = re.compile(r"(?i)\b(great|excellent|amazing|love|happy|success|win|positive)\b")
_SENTIMENT_NEGATIVE = re.compile(r"(?i)\b(bad|terrible|fail|issue|problem|concern|risk|negative|broken)\b")


class AutoTaggerPlugin(RemembraPlugin):
    """Automatically tags memories with topic, priority, and sentiment."""

    name = "auto-tagger"
    version = "1.0.0"
    description = "Rule-based auto-tagging for memories"
    author = "Remembra"

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(config)
        self._prefix = self.config.get("tag_prefix", "auto")
        self._min_length = self.config.get("min_content_length", 20)
        self._enable_sentiment = self.config.get("enable_sentiment", True)
        self._enable_topic = self.config.get("enable_topic", True)

        # Compile custom rules
        self._custom_rules: list[tuple[re.Pattern[str], str]] = []
        for rule in self.config.get("custom_rules", []):
            try:
                self._custom_rules.append(
                    (
                        re.compile(rule["pattern"]),
                        rule["tag"],
                    )
                )
            except (KeyError, re.error) as e:
                logger.warning("Invalid custom rule: %s", e)

    async def on_store(self, event: MemoryEvent) -> MemoryEvent:
        if len(event.content) < self._min_length:
            return event

        tags: list[str] = []

        # Topic detection
        if self._enable_topic:
            for pattern, tag in _TOPIC_PATTERNS.items():
                if re.search(pattern, event.content):
                    tags.append(tag)

        # Priority detection
        for pattern, tag in _PRIORITY_PATTERNS.items():
            if re.search(pattern, event.content):
                tags.append(tag)

        # Sentiment detection
        if self._enable_sentiment:
            pos = len(_SENTIMENT_POSITIVE.findall(event.content))
            neg = len(_SENTIMENT_NEGATIVE.findall(event.content))
            if pos > neg:
                tags.append("sentiment:positive")
            elif neg > pos:
                tags.append("sentiment:negative")

        # Custom rules
        for compiled, tag in self._custom_rules:
            if compiled.search(event.content):
                tags.append(tag)

        # Deduplicate and add to metadata
        if tags:
            existing = event.metadata.get(f"{self._prefix}_tags", [])
            all_tags = list(set(existing + tags))
            event.metadata[f"{self._prefix}_tags"] = all_tags
            logger.debug("Auto-tagged memory %s: %s", event.memory_id, all_tags)

        return event

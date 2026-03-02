"""
Format-specific memory importers.

Each importer converts a source format into a list of ImportedMemory
records that the bulk import endpoint can process.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ImportedMemory:
    """A single memory extracted from an import source."""

    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    source_format: str = "unknown"
    source_id: str | None = None  # Original ID in source system
    timestamp: str | None = None  # Original creation time


SUPPORTED_FORMATS = ["json", "jsonl", "csv", "chatgpt", "claude", "plaintext"]

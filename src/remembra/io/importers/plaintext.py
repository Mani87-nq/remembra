"""
Plain text and markdown bulk import.

Supports:
  - Single text blob → split into paragraphs
  - Markdown → split on headings (## / ###)
  - Line-delimited text → one memory per non-empty line
  - JSON array of strings
  - JSONL (one JSON string per line)
  - CSV (expects a "content" column)
"""

from __future__ import annotations

import csv
import io
import json
import logging
import re

from remembra.io.importers import ImportedMemory

logger = logging.getLogger(__name__)

MIN_CONTENT_LENGTH = 10


def parse_plaintext(data: str, split_mode: str = "paragraph") -> list[ImportedMemory]:
    """Parse plain text into memories.

    Args:
        data: Raw text content.
        split_mode: How to split — paragraph, line, heading, or none.

    Returns:
        List of ImportedMemory records.
    """
    if split_mode == "line":
        chunks = [line.strip() for line in data.splitlines() if line.strip()]
    elif split_mode == "heading":
        # Split on markdown headings
        chunks = re.split(r"\n(?=#{1,3}\s)", data)
        chunks = [c.strip() for c in chunks if c.strip()]
    elif split_mode == "none":
        chunks = [data.strip()] if data.strip() else []
    else:
        # Default: paragraph (double newline)
        chunks = re.split(r"\n\s*\n", data)
        chunks = [c.strip() for c in chunks if c.strip()]

    memories = [
        ImportedMemory(
            content=chunk,
            source_format="plaintext",
        )
        for chunk in chunks
        if len(chunk) >= MIN_CONTENT_LENGTH
    ]

    logger.info("Parsed %d memories from plaintext (mode=%s)", len(memories), split_mode)
    return memories


def parse_json_array(data: str | bytes) -> list[ImportedMemory]:
    """Parse a JSON array of memory objects or strings.

    Accepts:
      ["string1", "string2"]
    or:
      [{"content": "...", "metadata": {...}}, ...]
    """
    try:
        items = json.loads(data)
    except json.JSONDecodeError as e:
        logger.error("Failed to parse JSON import: %s", e)
        return []

    if not isinstance(items, list):
        items = [items]

    memories: list[ImportedMemory] = []
    for item in items:
        if isinstance(item, str):
            if len(item) >= MIN_CONTENT_LENGTH:
                memories.append(ImportedMemory(content=item, source_format="json"))
        elif isinstance(item, dict):
            content = item.get("content", "")
            if len(content) >= MIN_CONTENT_LENGTH:
                memories.append(
                    ImportedMemory(
                        content=content,
                        metadata=item.get("metadata", {}),
                        source_format="json",
                        source_id=item.get("id"),
                        timestamp=item.get("created_at") or item.get("timestamp"),
                    )
                )

    logger.info("Parsed %d memories from JSON", len(memories))
    return memories


def parse_jsonl(data: str) -> list[ImportedMemory]:
    """Parse JSONL (one JSON object per line)."""
    memories: list[ImportedMemory] = []
    for line in data.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            item = json.loads(line)
            if isinstance(item, str):
                if len(item) >= MIN_CONTENT_LENGTH:
                    memories.append(ImportedMemory(content=item, source_format="jsonl"))
            elif isinstance(item, dict):
                content = item.get("content", "")
                if len(content) >= MIN_CONTENT_LENGTH:
                    memories.append(
                        ImportedMemory(
                            content=content,
                            metadata=item.get("metadata", {}),
                            source_format="jsonl",
                            source_id=item.get("id"),
                            timestamp=item.get("created_at") or item.get("timestamp"),
                        )
                    )
        except json.JSONDecodeError:
            continue

    logger.info("Parsed %d memories from JSONL", len(memories))
    return memories


def parse_csv_import(data: str) -> list[ImportedMemory]:
    """Parse CSV with a 'content' column."""
    reader = csv.DictReader(io.StringIO(data))
    memories: list[ImportedMemory] = []

    for row in reader:
        content = row.get("content", "").strip()
        if len(content) < MIN_CONTENT_LENGTH:
            continue

        metadata = {}
        for key, val in row.items():
            if key not in ("content", "id", "created_at", "timestamp"):
                metadata[key] = val

        memories.append(
            ImportedMemory(
                content=content,
                metadata=metadata,
                source_format="csv",
                source_id=row.get("id"),
                timestamp=row.get("created_at") or row.get("timestamp"),
            )
        )

    logger.info("Parsed %d memories from CSV", len(memories))
    return memories

"""Input sanitization for memory content - defense against prompt injection."""

import hashlib
import re
from dataclasses import dataclass

import structlog

log = structlog.get_logger(__name__)

# Suspicious patterns that may indicate prompt injection attempts
# Each pattern has a weight for trust score reduction
SUSPICIOUS_PATTERNS: list[tuple[str, float, str]] = [
    # Direct instruction overrides
    (r"ignore\s+(all\s+)?previous\s+(instructions?|context)", 0.35, "instruction_override"),
    (r"disregard\s+(all\s+)?(previous\s+)?instructions?", 0.35, "instruction_override"),
    (r"forget\s+(all\s+)?previous\s+(context|instructions?)", 0.35, "instruction_override"),
    (r"ignore\s+all\s+previous", 0.35, "instruction_override"),
    # Role manipulation
    (r"you\s+are\s+now\s+a?", 0.30, "role_manipulation"),
    (r"act\s+as\s+if\s+you", 0.25, "role_manipulation"),
    (r"pretend\s+(that\s+)?you", 0.25, "role_manipulation"),
    (r"your\s+new\s+instructions?\s+(are|is)", 0.35, "role_manipulation"),
    (r"from\s+now\s+on\s+you", 0.25, "role_manipulation"),
    # System prompt extraction
    (r"(what|show|reveal|tell|repeat)\s+(is\s+|me\s+)?your\s+(system\s+)?(prompt|instructions?)", 0.30, "prompt_extraction"),
    (r"ignore\s+the\s+system\s+prompt", 0.35, "prompt_extraction"),
    (r"show\s+me\s+your\s+instructions?", 0.30, "prompt_extraction"),
    # Delimiter manipulation
    (r"```\s*system", 0.20, "delimiter_injection"),
    (r"\[SYSTEM\]", 0.20, "delimiter_injection"),
    (r"<\|im_start\|>", 0.30, "delimiter_injection"),
    (r"<\|im_end\|>", 0.30, "delimiter_injection"),
    # Output manipulation
    (r"output\s+only", 0.15, "output_manipulation"),
    (r"respond\s+with\s+only", 0.15, "output_manipulation"),
    (r"do\s+not\s+add\s+any", 0.15, "output_manipulation"),
    # Memory manipulation specific
    (r"insert\s+this\s+into\s+(your\s+)?memory", 0.25, "memory_manipulation"),
    (r"remember\s+that\s+you\s+must", 0.25, "memory_manipulation"),
    (r"store\s+this\s+as\s+a?\s*fact", 0.20, "memory_manipulation"),
]


@dataclass
class SanitizationResult:
    """Result of content sanitization."""

    content: str  # Original content (we don't modify it, just flag it)
    trust_score: float  # 0.0 to 1.0 (1.0 = fully trusted)
    checksum: str  # SHA-256 hash for integrity verification
    flagged_patterns: list[str]  # List of detected suspicious pattern types
    is_suspicious: bool  # True if trust_score < threshold
    source: str  # Content source (user_input, agent_generated, etc.)


class ContentSanitizer:
    """
    Sanitizes and scores content before storage.

    Defense-in-depth against memory injection attacks (MINJA):
    1. Pattern detection for known injection techniques
    2. Trust scoring based on detected patterns
    3. Integrity checksums for tamper detection
    4. Logging of suspicious content (without storing actual content)

    Note: This does NOT block content - it flags it and reduces trust.
    The application decides how to handle low-trust memories.
    """

    def __init__(
        self,
        trust_threshold: float = 0.5,
        log_suspicious: bool = True,
    ) -> None:
        """
        Initialize sanitizer.

        Args:
            trust_threshold: Score below which content is flagged as suspicious
            log_suspicious: Whether to log warnings for suspicious content
        """
        self.trust_threshold = trust_threshold
        self.log_suspicious = log_suspicious

        # Compile patterns for efficiency
        self._compiled_patterns = [
            (re.compile(pattern, re.IGNORECASE), weight, name) for pattern, weight, name in SUSPICIOUS_PATTERNS
        ]

    @staticmethod
    def compute_checksum(content: str) -> str:
        """Compute SHA-256 checksum of content."""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def analyze(
        self,
        content: str,
        source: str = "user_input",
    ) -> SanitizationResult:
        """
        Analyze content for suspicious patterns and compute trust score.

        Args:
            content: The text content to analyze
            source: Origin of the content (user_input, agent_generated, external_api)

        Returns:
            SanitizationResult with trust score and detected patterns
        """
        trust_score = 1.0
        flagged_patterns: list[str] = []

        # Check each suspicious pattern
        for pattern, weight, pattern_name in self._compiled_patterns:
            if pattern.search(content):
                trust_score -= weight
                if pattern_name not in flagged_patterns:
                    flagged_patterns.append(pattern_name)

        # Clamp trust score to [0.0, 1.0]
        trust_score = max(0.0, min(1.0, trust_score))

        # Compute checksum
        checksum = self.compute_checksum(content)

        # Determine if suspicious
        is_suspicious = trust_score < self.trust_threshold

        # Log if suspicious
        if is_suspicious and self.log_suspicious:
            log.warning(
                "suspicious_content_detected",
                trust_score=round(trust_score, 2),
                flagged_patterns=flagged_patterns,
                content_length=len(content),
                content_preview=content[:50] + "..." if len(content) > 50 else content,
                source=source,
            )

        return SanitizationResult(
            content=content,
            trust_score=trust_score,
            checksum=checksum,
            flagged_patterns=flagged_patterns,
            is_suspicious=is_suspicious,
            source=source,
        )

    def verify_integrity(self, content: str, expected_checksum: str) -> bool:
        """
        Verify content integrity against stored checksum.

        Args:
            content: The content to verify
            expected_checksum: The expected SHA-256 checksum

        Returns:
            True if checksum matches, False if content was tampered with
        """
        actual_checksum = self.compute_checksum(content)
        matches = actual_checksum == expected_checksum

        if not matches:
            log.error(
                "content_integrity_violation",
                expected=expected_checksum[:16] + "...",
                actual=actual_checksum[:16] + "...",
            )

        return matches

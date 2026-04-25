"""Post-meeting summary generator.

Consumes a transcript (list of TranscriptSegment) plus meeting metadata and
produces structured memories ready for MemoryService.store(): decisions
(type=fact), action items (type=task), and key quotes (type=observation).
Also drafts a follow-up email.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any

from remembra.audio_adapter import TranscriptSegment

DECISION_CUES = (
    r"\b(we (decided|agreed|concluded)|let's go with|final (answer|call)|"
    r"the decision is|going forward|we will|we'll)\b"
)
ACTION_CUES = (
    r"\b(i'?ll|i will|you'?ll|you will|we'?ll|we will|can you|please|"
    r"todo|to-do|action item|owner:|by (monday|tuesday|wednesday|thursday|"
    r"friday|next week|eod|tomorrow|end of (day|week)))\b"
)
QUOTE_CUES = (
    r"\b(the key thing|the most important|critically|the risk is|"
    r"the opportunity|the problem is|bottom line)\b"
)
DATE_CUE = re.compile(
    r"\b(by|before|on)\s+"
    r"(today|tomorrow|monday|tuesday|wednesday|thursday|friday|saturday|sunday|"
    r"eod|end of day|end of week|next week|"
    r"\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}(?:/\d{2,4})?)",
    re.IGNORECASE,
)

DECISION_RE = re.compile(DECISION_CUES, re.IGNORECASE)
ACTION_RE = re.compile(ACTION_CUES, re.IGNORECASE)
QUOTE_RE = re.compile(QUOTE_CUES, re.IGNORECASE)


@dataclass
class ExtractedMemory:
    """A proto-memory ready to hand to MemoryService.store()."""

    content: str
    type: str  # "fact" | "task" | "observation"
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_store_payload(self) -> dict[str, Any]:
        return {"content": self.content, "type": self.type, "metadata": dict(self.metadata)}


@dataclass
class PostMeetingResult:
    meeting_id: str
    summary_text: str
    decisions: list[ExtractedMemory]
    action_items: list[ExtractedMemory]
    key_quotes: list[ExtractedMemory]
    follow_up_email: str
    generated_at: str

    def memories(self) -> list[ExtractedMemory]:
        return [*self.decisions, *self.action_items, *self.key_quotes]

    def to_dict(self) -> dict[str, Any]:
        return {
            "meeting_id": self.meeting_id,
            "summary_text": self.summary_text,
            "decisions": [asdict(m) for m in self.decisions],
            "action_items": [asdict(m) for m in self.action_items],
            "key_quotes": [asdict(m) for m in self.key_quotes],
            "follow_up_email": self.follow_up_email,
            "generated_at": self.generated_at,
        }


class PostMeetingProcessor:
    """Rule-based extractor. Deterministic and fast; no LLM dependency.

    If an LLM-backed extractor is wired in later, swap out `_extract_*`.
    """

    def __init__(self, max_items_per_bucket: int = 20) -> None:
        self.max_items = max_items_per_bucket

    def process(
        self,
        transcript: Iterable[TranscriptSegment],
        meeting: dict[str, Any],
    ) -> PostMeetingResult:
        segs = [s for s in transcript if (s.text or "").strip()]
        meeting_id = meeting.get("id") or meeting.get("meeting_id") or ""
        attendees = meeting.get("attendees") or []

        decisions = self._extract_decisions(segs, meeting_id)
        actions = self._extract_actions(segs, meeting_id, attendees)
        quotes = self._extract_quotes(segs, meeting_id)

        summary = self._compose_summary(meeting, decisions, actions, quotes)
        email = self._compose_email(meeting, attendees, decisions, actions)

        return PostMeetingResult(
            meeting_id=str(meeting_id),
            summary_text=summary,
            decisions=decisions[: self.max_items],
            action_items=actions[: self.max_items],
            key_quotes=quotes[: self.max_items],
            follow_up_email=email,
            generated_at=datetime.now(UTC).isoformat(),
        )

    # -------------------------------------------------------------- extraction

    def _extract_decisions(self, segs: list[TranscriptSegment], meeting_id: str) -> list[ExtractedMemory]:
        out: list[ExtractedMemory] = []
        for seg in segs:
            if DECISION_RE.search(seg.text):
                out.append(
                    ExtractedMemory(
                        content=seg.text.strip(),
                        type="fact",
                        metadata={
                            "source": "meeting_decision",
                            "meeting_id": meeting_id,
                            "speaker": seg.speaker,
                            "start": seg.start,
                            "end": seg.end,
                        },
                    )
                )
        return out

    def _extract_actions(
        self,
        segs: list[TranscriptSegment],
        meeting_id: str,
        attendees: list[dict[str, Any]],
    ) -> list[ExtractedMemory]:
        out: list[ExtractedMemory] = []
        for seg in segs:
            if not ACTION_RE.search(seg.text):
                continue
            due = self._extract_due_date(seg.text)
            owner = self._guess_owner(seg, attendees)
            out.append(
                ExtractedMemory(
                    content=seg.text.strip(),
                    type="task",
                    metadata={
                        "source": "meeting_action",
                        "meeting_id": meeting_id,
                        "speaker": seg.speaker,
                        "owner": owner,
                        "due": due,
                        "start": seg.start,
                        "end": seg.end,
                        "status": "open",
                    },
                )
            )
        return out

    def _extract_quotes(self, segs: list[TranscriptSegment], meeting_id: str) -> list[ExtractedMemory]:
        out: list[ExtractedMemory] = []
        for seg in segs:
            text = seg.text.strip()
            if not text:
                continue
            is_cue = bool(QUOTE_RE.search(text))
            is_long = len(text) >= 80
            if is_cue or is_long:
                out.append(
                    ExtractedMemory(
                        content=text,
                        type="observation",
                        metadata={
                            "source": "meeting_quote",
                            "meeting_id": meeting_id,
                            "speaker": seg.speaker,
                            "start": seg.start,
                            "end": seg.end,
                            "confidence": seg.confidence,
                        },
                    )
                )
        # Cap quote volume; prefer cue matches first.
        cues = [m for m in out if m.metadata.get("source") == "meeting_quote" and QUOTE_RE.search(m.content)]
        rest = [m for m in out if m not in cues]
        return cues + rest

    # ---------------------------------------------------------------- helpers

    @staticmethod
    def _extract_due_date(text: str) -> str | None:
        match = DATE_CUE.search(text)
        return match.group(0) if match else None

    @staticmethod
    def _guess_owner(seg: TranscriptSegment, attendees: list[dict[str, Any]]) -> str | None:
        text = seg.text.lower()
        if re.search(r"\bi'?ll\b|\bi will\b", text):
            return f"speaker:{seg.speaker}"
        # "you'll / can you X" → the other speaker, if known
        if re.search(r"\byou'?ll\b|\byou will\b|\bcan you\b", text):
            return f"addressed_to:other_than_{seg.speaker}"
        for a in attendees:
            name = (a.get("name") or "").strip()
            if name and name.lower() in text:
                return a.get("email") or name
        return None

    # --------------------------------------------------------------- rendering

    def _compose_summary(
        self,
        meeting: dict[str, Any],
        decisions: list[ExtractedMemory],
        actions: list[ExtractedMemory],
        quotes: list[ExtractedMemory],
    ) -> str:
        title = meeting.get("summary") or meeting.get("title") or "Meeting"
        when = meeting.get("start") or ""
        parts: list[str] = [f"# Summary: {title}"]
        if when:
            parts.append(f"When: {when}")
        parts.append("")
        parts.append(f"Decisions ({len(decisions)}):")
        for d in decisions[:10]:
            parts.append(f"  - {_short(d.content)}")
        parts.append("")
        parts.append(f"Action items ({len(actions)}):")
        for a in actions[:10]:
            owner = a.metadata.get("owner") or "unassigned"
            due = a.metadata.get("due") or "no date"
            parts.append(f"  - [{owner} / {due}] {_short(a.content)}")
        parts.append("")
        if quotes:
            parts.append(f"Key quotes ({len(quotes)}):")
            for q in quotes[:5]:
                parts.append(f"  > {_short(q.content, 180)}")
        return "\n".join(parts)

    def _compose_email(
        self,
        meeting: dict[str, Any],
        attendees: list[dict[str, Any]],
        decisions: list[ExtractedMemory],
        actions: list[ExtractedMemory],
    ) -> str:
        title = meeting.get("summary") or meeting.get("title") or "our meeting"
        to_line = ", ".join(a.get("email", "") for a in attendees if a.get("email"))

        lines = []
        lines.append(f"To: {to_line}")
        lines.append(f"Subject: Recap — {title}")
        lines.append("")
        lines.append("Hi all,")
        lines.append("")
        lines.append(f"Quick recap of {title}:")
        lines.append("")
        if decisions:
            lines.append("Decisions:")
            for d in decisions[:8]:
                lines.append(f"  • {_short(d.content, 200)}")
            lines.append("")
        if actions:
            lines.append("Action items:")
            for a in actions[:12]:
                owner = a.metadata.get("owner") or "TBD"
                due = a.metadata.get("due") or "TBD"
                lines.append(f"  • ({owner}, due {due}) {_short(a.content, 200)}")
            lines.append("")
        lines.append("Please reply if I missed anything.")
        lines.append("")
        lines.append("Thanks,")
        return "\n".join(lines)


def _short(text: str, limit: int = 140) -> str:
    t = (text or "").strip().replace("\n", " ")
    if len(t) <= limit:
        return t
    return t[: limit - 3] + "..."


def process_meeting(
    transcript: Iterable[TranscriptSegment],
    meeting: dict[str, Any],
) -> PostMeetingResult:
    """Convenience functional entry point."""
    return PostMeetingProcessor().process(transcript, meeting)

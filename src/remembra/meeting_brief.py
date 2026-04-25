"""Pre-meeting brief generator.

Takes a meeting (from calendar_client) plus recalled memories per attendee and
produces a structured brief with citations in both JSON and text form.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any

from remembra.calendar_client import Attendee, CalendarEvent


@dataclass
class Citation:
    memory_id: str
    snippet: str
    stored_at: str | None = None
    score: float | None = None


@dataclass
class AttendeeBrief:
    email: str
    name: str
    company: str | None
    last_interaction: str | None
    open_items: list[str] = field(default_factory=list)
    key_facts: list[str] = field(default_factory=list)
    landmines: list[str] = field(default_factory=list)
    citations: list[Citation] = field(default_factory=list)


@dataclass
class MeetingBrief:
    meeting_id: str
    summary: str
    start: str
    end: str
    location: str | None
    recurrence_note: str | None
    attendees: list[AttendeeBrief]
    generated_at: str
    raw_event: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        return d

    def to_text(self) -> str:
        lines: list[str] = []
        lines.append(f"# Pre-meeting brief: {self.summary}")
        lines.append(f"When: {self.start} → {self.end}")
        if self.location:
            lines.append(f"Where: {self.location}")
        if self.recurrence_note:
            lines.append(f"Recurrence: {self.recurrence_note}")
        lines.append("")
        for a in self.attendees:
            header = f"## {a.name} <{a.email}>"
            if a.company:
                header += f"  —  {a.company}"
            lines.append(header)
            if a.last_interaction:
                lines.append(f"Last interaction: {a.last_interaction}")
            if a.key_facts:
                lines.append("Key facts:")
                for f in a.key_facts:
                    lines.append(f"  - {f}")
            if a.open_items:
                lines.append("Open items:")
                for item in a.open_items:
                    lines.append(f"  - {item}")
            if a.landmines:
                lines.append("Landmines:")
                for lm in a.landmines:
                    lines.append(f"  ! {lm}")
            if a.citations:
                lines.append("Citations:")
                for c in a.citations:
                    snippet = (c.snippet or "").strip().replace("\n", " ")
                    if len(snippet) > 140:
                        snippet = snippet[:137] + "..."
                    lines.append(f"  [{c.memory_id}] {snippet}")
            lines.append("")
        lines.append(f"_Generated at {self.generated_at}_")
        return "\n".join(lines)


class MeetingBriefBuilder:
    """Assemble a MeetingBrief from calendar data + recalled memories."""

    OPEN_ITEM_TYPES = {"task"}
    FACT_TYPES = {"fact"}
    LANDMINE_KEYWORDS = (
        "angry",
        "upset",
        "complaint",
        "escalation",
        "legal",
        "churn",
        "cancel",
        "refund",
        "missed deadline",
        "blocker",
    )

    def __init__(self, max_facts: int = 5, max_citations: int = 5) -> None:
        self.max_facts = max_facts
        self.max_citations = max_citations

    def build(
        self,
        event: CalendarEvent,
        memories_by_attendee: dict[str, list[dict[str, Any]]],
        recurrence: dict[str, Any] | None = None,
    ) -> MeetingBrief:
        attendee_briefs = []
        for a in event.attendees:
            memories = memories_by_attendee.get(a.email, [])
            attendee_briefs.append(self._build_attendee(a, memories))

        recurrence_note = self._format_recurrence(recurrence)

        return MeetingBrief(
            meeting_id=event.id,
            summary=event.summary,
            start=event.start,
            end=event.end,
            location=event.location,
            recurrence_note=recurrence_note,
            attendees=attendee_briefs,
            generated_at=datetime.now(UTC).isoformat(),
            raw_event=event.to_dict(),
        )

    # ------------------------------------------------------------ per-attendee

    def _build_attendee(self, attendee: Attendee, memories: list[dict[str, Any]]) -> AttendeeBrief:
        brief = AttendeeBrief(
            email=attendee.email,
            name=attendee.name,
            company=attendee.company,
            last_interaction=None,
        )

        sorted_mems = sorted(
            memories,
            key=lambda m: _safe_ts(m.get("stored_at") or m.get("created_at")),
            reverse=True,
        )

        if sorted_mems:
            latest = sorted_mems[0]
            snippet = _short(latest.get("content", ""))
            ts = latest.get("stored_at") or latest.get("created_at") or ""
            brief.last_interaction = f"{ts}: {snippet}" if ts else snippet

        for m in sorted_mems:
            mtype = (m.get("type") or m.get("memory_type") or "").lower()
            content = (m.get("content") or "").strip()
            if not content:
                continue

            if mtype in self.OPEN_ITEM_TYPES and not self._is_completed(m):
                brief.open_items.append(_short(content, 160))
            elif mtype in self.FACT_TYPES:
                if len(brief.key_facts) < self.max_facts:
                    brief.key_facts.append(_short(content, 160))

            if any(k in content.lower() for k in self.LANDMINE_KEYWORDS):
                brief.landmines.append(_short(content, 160))

            if len(brief.citations) < self.max_citations:
                brief.citations.append(
                    Citation(
                        memory_id=str(m.get("id") or m.get("memory_id") or ""),
                        snippet=_short(content, 200),
                        stored_at=m.get("stored_at") or m.get("created_at"),
                        score=_safe_float(m.get("score")),
                    )
                )

        return brief

    @staticmethod
    def _is_completed(memory: dict[str, Any]) -> bool:
        status = (memory.get("metadata") or {}).get("status", "")
        return str(status).lower() in {"done", "completed", "closed"}

    @staticmethod
    def _format_recurrence(recurrence: dict[str, Any] | None) -> str | None:
        if not recurrence or not recurrence.get("is_recurring"):
            return None
        past = recurrence.get("past_instances", 0)
        upcoming = recurrence.get("upcoming_instances", 0)
        rules = recurrence.get("recurrence_rules", []) or []
        rule_str = ", ".join(rules) if rules else "recurring"
        return f"{rule_str} (met {past} times previously, {upcoming} upcoming)"


# ---------------------------------------------------------------- helpers


def _safe_ts(value: Any) -> float:
    if not value:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).timestamp()
    except Exception:
        return 0.0


def _safe_float(value: Any) -> float | None:
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _short(text: str, limit: int = 120) -> str:
    t = (text or "").strip().replace("\n", " ")
    if len(t) <= limit:
        return t
    return t[: limit - 3] + "..."


def build_brief(
    event: CalendarEvent,
    memories_by_attendee: dict[str, list[dict[str, Any]]],
    recurrence: dict[str, Any] | None = None,
) -> MeetingBrief:
    """Convenience functional entry point."""
    return MeetingBriefBuilder().build(event, memories_by_attendee, recurrence)

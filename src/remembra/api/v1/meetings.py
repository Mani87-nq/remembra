"""Meeting brief + summary endpoints — /api/v1/meetings/*.

Phase 1. These endpoints are intentionally lightweight: they assemble briefs
and summaries from calendar + memory data. Audio transcription lives in
/api/v1/audio.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Body, HTTPException, Query

from remembra.audio_adapter import TranscriptSegment
from remembra.calendar_client import GoogleCalendarClient
from remembra.meeting_brief import MeetingBriefBuilder
from remembra.post_meeting import PostMeetingProcessor

log = logging.getLogger(__name__)

router = APIRouter(prefix="/meetings", tags=["meetings"])


@router.get("/brief")
async def get_meeting_brief(
    event_id: str = Query(..., description="Google Calendar event ID"),
    calendar_id: str = Query("primary"),
    include_text: bool = Query(True),
) -> dict[str, Any]:
    """Return a pre-meeting brief for the given calendar event.

    Attendee memories are not joined here by default — callers that want
    memory joins should POST to /meetings/brief with `memories_by_attendee`
    or extend this endpoint to call MemoryService.recall per attendee.
    """
    try:
        cal = GoogleCalendarClient()
        event = cal.get_event(event_id, calendar_id=calendar_id)
        recurrence = cal.get_recurring_pattern(event_id, calendar_id=calendar_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - API-dependent
        log.exception("Calendar fetch failed")
        raise HTTPException(status_code=502, detail=f"Calendar error: {exc}") from exc

    builder = MeetingBriefBuilder()
    brief = builder.build(event, memories_by_attendee={}, recurrence=recurrence)

    payload: dict[str, Any] = {"brief": brief.to_dict()}
    if include_text:
        payload["text"] = brief.to_text()
    return payload


@router.post("/brief")
async def post_meeting_brief(body: dict[str, Any] = Body(...)) -> dict[str, Any]:
    """Build a brief from explicit event + memory payload (no Google call).

    Body:
      event:              CalendarEvent.to_dict()
      memories_by_email:  { "<email>": [ {memory}, ... ] }
      recurrence:         optional recurrence summary
    """
    from remembra.calendar_client import Attendee, CalendarEvent

    event_raw = body.get("event")
    if not event_raw:
        raise HTTPException(status_code=400, detail="'event' is required")

    attendees_raw = event_raw.get("attendees", []) or []
    attendees = [Attendee(**a) for a in attendees_raw]
    event = CalendarEvent(
        id=event_raw.get("id", ""),
        summary=event_raw.get("summary", ""),
        description=event_raw.get("description", ""),
        start=event_raw.get("start", ""),
        end=event_raw.get("end", ""),
        location=event_raw.get("location"),
        attendees=attendees,
        organizer_email=event_raw.get("organizer_email"),
        recurrence=event_raw.get("recurrence", []) or [],
        hangout_link=event_raw.get("hangout_link"),
        status=event_raw.get("status", "confirmed"),
    )

    memories_by_attendee = body.get("memories_by_email", {}) or {}
    recurrence = body.get("recurrence")

    brief = MeetingBriefBuilder().build(event, memories_by_attendee, recurrence)
    return {"brief": brief.to_dict(), "text": brief.to_text()}


@router.post("/summarize")
async def summarize_meeting(body: dict[str, Any] = Body(...)) -> dict[str, Any]:
    """Generate decisions, action items, quotes, and follow-up email.

    Body:
      meeting:   { id, summary, start, attendees: [{name, email}, ...] }
      segments:  [ { start, end, speaker, text, confidence }, ... ]
      transcript_path: optional path to audio file; if given we transcribe first
    """
    meeting = body.get("meeting") or {}
    segs_raw = body.get("segments")
    transcript_path = body.get("transcript_path")

    if segs_raw is None and transcript_path:
        from remembra.audio_adapter import AudioAdapter

        adapter = AudioAdapter()
        try:
            segs = adapter.transcribe(transcript_path)
        except RuntimeError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except FileNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
    else:
        segs = [
            TranscriptSegment(
                start=float(s.get("start", 0.0)),
                end=float(s.get("end", 0.0)),
                speaker=s.get("speaker", "speaker_1"),
                text=s.get("text", ""),
                confidence=float(s.get("confidence", 0.0)),
            )
            for s in (segs_raw or [])
        ]

    result = PostMeetingProcessor().process(segs, meeting)
    return result.to_dict()

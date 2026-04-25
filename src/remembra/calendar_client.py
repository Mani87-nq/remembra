"""Google Calendar integration for Remembra Phase 1.

Wraps google-api-python-client with a small surface area suited for
pre-meeting brief generation: upcoming events, attendees, and recurrence.
"""

from __future__ import annotations

import logging
import os
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

log = logging.getLogger(__name__)

GENERIC_EMAIL_DOMAINS = {
    "gmail.com",
    "yahoo.com",
    "outlook.com",
    "hotmail.com",
    "icloud.com",
    "me.com",
    "proton.me",
    "protonmail.com",
    "aol.com",
    "live.com",
    "msn.com",
}


@dataclass
class Attendee:
    """A meeting attendee normalised into entity-like form."""

    email: str
    name: str
    company: str | None
    response_status: str = "needsAction"
    organizer: bool = False
    self: bool = False

    def to_entity(self) -> dict[str, Any]:
        """Shape suitable for storage as a `person` entity."""
        return {
            "type": "person",
            "name": self.name,
            "attributes": {
                "email": self.email,
                "company": self.company,
                "response_status": self.response_status,
                "organizer": self.organizer,
            },
        }


@dataclass
class CalendarEvent:
    """A single calendar event, normalised."""

    id: str
    summary: str
    description: str
    start: str
    end: str
    location: str | None
    attendees: list[Attendee]
    organizer_email: str | None
    recurrence: list[str]
    hangout_link: str | None
    status: str

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["attendees"] = [asdict(a) for a in self.attendees]
        return d


class GoogleCalendarClient:
    """Thin wrapper around the Google Calendar API v3.

    Auth model: pass a path to an OAuth token JSON (from a prior
    InstalledAppFlow run) or rely on GOOGLE_APPLICATION_CREDENTIALS for a
    service account. Both cases use `build("calendar", "v3", ...)`.
    """

    def __init__(
        self,
        token_path: str | None = None,
        credentials_path: str | None = None,
        calendar_id: str = "primary",
        scopes: list[str] | None = None,
    ) -> None:
        self.calendar_id = calendar_id
        self.scopes = scopes or ["https://www.googleapis.com/auth/calendar.readonly"]
        self.token_path = token_path or os.environ.get("REMEMBRA_GOOGLE_TOKEN")
        self.credentials_path = credentials_path or os.environ.get("REMEMBRA_GOOGLE_CREDENTIALS")
        self._service = None

    # ------------------------------------------------------------------- auth

    def _build_service(self) -> Any:
        if self._service is not None:
            return self._service

        try:
            from googleapiclient.discovery import build  # type: ignore
        except ImportError as exc:
            raise RuntimeError(
                "google-api-python-client is required. Install: pip install google-api-python-client google-auth-oauthlib"
            ) from exc

        creds = self._load_credentials()
        self._service = build("calendar", "v3", credentials=creds, cache_discovery=False)
        return self._service

    def _load_credentials(self) -> Any:
        # Try OAuth token first.
        if self.token_path and os.path.exists(self.token_path):
            try:
                from google.auth.transport.requests import Request  # type: ignore
                from google.oauth2.credentials import Credentials  # type: ignore

                creds = Credentials.from_authorized_user_file(self.token_path, self.scopes)
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                return creds
            except Exception as exc:
                log.warning("OAuth token load failed (%s); trying service account", exc)

        # Fall back to service account credentials.
        sa_path = self.credentials_path or os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        if sa_path and os.path.exists(sa_path):
            from google.oauth2 import service_account  # type: ignore

            return service_account.Credentials.from_service_account_file(sa_path, scopes=self.scopes)

        raise RuntimeError(
            "No Google credentials found. Set REMEMBRA_GOOGLE_TOKEN (OAuth) or GOOGLE_APPLICATION_CREDENTIALS (service account)."
        )

    # --------------------------------------------------------------- queries

    def get_upcoming_events(
        self,
        max_results: int = 20,
        lookahead_hours: int = 72,
        calendar_id: str | None = None,
    ) -> list[CalendarEvent]:
        """Return events starting in the next `lookahead_hours`."""
        service = self._build_service()
        now = datetime.now(UTC)
        time_min = now.isoformat()
        time_max = (now + timedelta(hours=lookahead_hours)).isoformat()

        result = (
            service.events()
            .list(
                calendarId=calendar_id or self.calendar_id,
                timeMin=time_min,
                timeMax=time_max,
                maxResults=max_results,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )

        events = []
        for raw in result.get("items", []):
            events.append(self._parse_event(raw))
        return events

    def get_event(self, event_id: str, calendar_id: str | None = None) -> CalendarEvent:
        service = self._build_service()
        raw = service.events().get(calendarId=calendar_id or self.calendar_id, eventId=event_id).execute()
        return self._parse_event(raw)

    def get_event_attendees(self, event_id: str, calendar_id: str | None = None) -> list[Attendee]:
        event = self.get_event(event_id, calendar_id=calendar_id)
        return event.attendees

    def get_recurring_pattern(self, event_id: str, calendar_id: str | None = None) -> dict[str, Any]:
        """Return a human-readable summary of the recurrence rule, if any.

        Also counts how often we've met with this group historically by
        scanning past instances (best-effort; capped at 50 instances).
        """
        service = self._build_service()
        event = self.get_event(event_id, calendar_id=calendar_id)

        pattern: dict[str, Any] = {
            "event_id": event.id,
            "summary": event.summary,
            "recurrence_rules": event.recurrence,
            "is_recurring": bool(event.recurrence),
            "past_instances": 0,
            "upcoming_instances": 0,
            "typical_attendees": [],
        }

        if not event.recurrence:
            return pattern

        try:
            instances = (
                service.events()
                .instances(
                    calendarId=calendar_id or self.calendar_id,
                    eventId=event.id,
                    maxResults=50,
                )
                .execute()
            )
        except Exception as exc:  # pragma: no cover - API-dependent
            log.warning("Failed to fetch recurring instances: %s", exc)
            return pattern

        now = datetime.now(UTC)
        attendee_counts: Counter[str] = Counter()
        for inst in instances.get("items", []):
            start = _parse_dt(inst.get("start", {}))
            if start is None:
                continue
            if start < now:
                pattern["past_instances"] += 1
            else:
                pattern["upcoming_instances"] += 1
            for a in inst.get("attendees", []) or []:
                email = a.get("email")
                if email:
                    attendee_counts[email] += 1

        pattern["typical_attendees"] = [{"email": e, "count": c} for e, c in attendee_counts.most_common(10)]
        return pattern

    # --------------------------------------------------------------- parsing

    def _parse_event(self, raw: dict[str, Any]) -> CalendarEvent:
        attendees = [self._parse_attendee(a) for a in raw.get("attendees", []) or []]
        organizer_email = (raw.get("organizer") or {}).get("email")
        start = _dt_str(raw.get("start", {}))
        end = _dt_str(raw.get("end", {}))
        return CalendarEvent(
            id=raw.get("id", ""),
            summary=raw.get("summary", "(no title)"),
            description=raw.get("description", "") or "",
            start=start,
            end=end,
            location=raw.get("location"),
            attendees=attendees,
            organizer_email=organizer_email,
            recurrence=raw.get("recurrence", []) or [],
            hangout_link=raw.get("hangoutLink"),
            status=raw.get("status", "confirmed"),
        )

    def _parse_attendee(self, raw: dict[str, Any]) -> Attendee:
        email = raw.get("email", "")
        display = raw.get("displayName") or _name_from_email(email)
        return Attendee(
            email=email,
            name=display,
            company=_company_from_email(email),
            response_status=raw.get("responseStatus", "needsAction"),
            organizer=bool(raw.get("organizer", False)),
            self=bool(raw.get("self", False)),
        )


# ------------------------------------------------------------------ helpers


def _dt_str(obj: dict[str, Any]) -> str:
    return obj.get("dateTime") or obj.get("date") or ""


def _parse_dt(obj: dict[str, Any]) -> datetime | None:
    s = _dt_str(obj)
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None


def _name_from_email(email: str) -> str:
    local = email.split("@", 1)[0] if "@" in email else email
    parts = local.replace(".", " ").replace("_", " ").replace("-", " ").split()
    return " ".join(p.capitalize() for p in parts) if parts else email


def _company_from_email(email: str) -> str | None:
    if "@" not in email:
        return None
    domain = email.rsplit("@", 1)[1].lower()
    if domain in GENERIC_EMAIL_DOMAINS:
        return None
    # Strip common public suffixes naively.
    root = domain.split(".")[0]
    return root.capitalize() if root else None

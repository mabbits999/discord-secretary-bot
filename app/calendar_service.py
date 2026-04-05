from __future__ import annotations

import json
from datetime import datetime
from zoneinfo import ZoneInfo

from .config import settings


def create_calendar_event(
    title: str,
    start_iso: str,
    end_iso: str,
    description: str = "",
    location: str = "",
) -> str:
    if not settings.google_service_account_json:
        raise RuntimeError("GOOGLE_SERVICE_ACCOUNT_JSON が未設定です")
    if not settings.calendar_id:
        raise RuntimeError("GOOGLE_CALENDAR_ID が未設定です")

    from google.oauth2 import service_account
    from googleapiclient.discovery import build

    info = json.loads(settings.google_service_account_json)
    creds = service_account.Credentials.from_service_account_info(
        info,
        scopes=["https://www.googleapis.com/auth/calendar"],
    )
    service = build("calendar", "v3", credentials=creds, cache_discovery=False)

    tz = ZoneInfo(settings.timezone)
    start_dt = datetime.fromisoformat(start_iso).replace(tzinfo=tz)
    end_dt = datetime.fromisoformat(end_iso).replace(tzinfo=tz)

    event = {
        "summary": title,
        "description": description,
        "location": location,
        "start": {"dateTime": start_dt.isoformat(), "timeZone": settings.timezone},
        "end": {"dateTime": end_dt.isoformat(), "timeZone": settings.timezone},
    }
    created = service.events().insert(calendarId=settings.calendar_id, body=event).execute()
    return created.get("htmlLink", "作成完了")

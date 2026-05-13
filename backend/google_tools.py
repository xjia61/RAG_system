from typing import Optional

from googleapiclient.discovery import build

from google_auth import get_google_credentials


def create_calendar_event(
    title: str,
    start_time: str,
    end_time: str,
    description: str = "",
    location: str = "",
    timezone: str = "America/Chicago",
    attendee_email: Optional[str] = None,
):
    """
    start_time and end_time should be ISO format, for example:
    2026-05-12T09:00:00
    """

    creds = get_google_credentials()
    service = build("calendar", "v3", credentials=creds)

    event = {
        "summary": title,
        "location": location,
        "description": description,
        "start": {
            "dateTime": start_time,
            "timeZone": timezone,
        },
        "end": {
            "dateTime": end_time,
            "timeZone": timezone,
        },
    }

    if attendee_email:
        event["attendees"] = [{"email": attendee_email}]

    created_event = (
        service.events()
        .insert(
            calendarId="primary",
            body=event,
            sendUpdates="all" if attendee_email else "none",
        )
        .execute()
    )

    return {
        "event_id": created_event.get("id"),
        "html_link": created_event.get("htmlLink"),
        "summary": created_event.get("summary"),
        "start": created_event.get("start"),
        "end": created_event.get("end"),
    }


def create_google_doc(
    title: str,
    body: str,
):
    creds = get_google_credentials()
    docs_service = build("docs", "v1", credentials=creds)

    doc = docs_service.documents().create(
        body={
            "title": title,
        }
    ).execute()

    document_id = doc.get("documentId")

    requests = [
        {
            "insertText": {
                "location": {
                    "index": 1,
                },
                "text": body,
            }
        }
    ]

    docs_service.documents().batchUpdate(
        documentId=document_id,
        body={
            "requests": requests,
        },
    ).execute()

    return {
        "document_id": document_id,
        "title": title,
        "url": f"https://docs.google.com/document/d/{document_id}/edit",
    }
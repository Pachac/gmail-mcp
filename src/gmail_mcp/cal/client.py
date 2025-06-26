from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from datetime import datetime
from datetime import timezone

from pydantic import BaseModel

class CalendarEntry(BaseModel):
    """Model for a calendar entry."""
    id: str
    summary: str
    start: str
    end: str
    description: str | None = None
    location: str | None = None

class CalendryEntryCreate(BaseModel):
    """Model for creating a calendar entry."""
    summary: str
    start: datetime
    end: datetime
    description: str | None = None
    location: str | None = None

def get_calendars(creds):
    """Fetch the list of calendars."""
    service = build("calendar", "v3", credentials=creds)
    try:
        calendar_list = service.calendarList().list().execute()
        return calendar_list.get('items', [])
    except HttpError as error:
        print(f"An error occurred: {error}")
        return []

def get_calendar_entries_by_date(creds, start_date: datetime, end_date: datetime, calendar_id="pachovst@gmail.com"):
    """Fetch calendar entries within a specified date range."""
    start_date = start_date.astimezone(timezone.utc).replace(tzinfo=None)
    end_date = end_date.astimezone(timezone.utc).replace(tzinfo=None)
    print(start_date.isoformat(), end_date.isoformat())
    service = build("calendar", "v3", credentials=creds)
    try:
        events_result = service.events().list(
            calendarId=calendar_id,
            timeMin=start_date.isoformat() + 'Z',
            timeMax=end_date.isoformat() + 'Z',
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        events = events_result.get('items', [])
        return [
            CalendarEntry(
                id=event['id'],
                summary=event.get('summary', 'No Title'),
                start=datetime.fromisoformat(event['start'].get('dateTime', event['start'].get('date'))).isoformat(),
                end=datetime.fromisoformat(event['end'].get('dateTime', event['end'].get('date'))).isoformat(),
                description=event.get('description'),
                location=event.get('location')
            ) for event in events
        ]
    except HttpError as error:
        print(f"An error occurred: {error}")
        return []
    
def create_calendar_entry(creds, entry: CalendryEntryCreate, calendar_id="pachovst@gmail.com") -> CalendarEntry:
    """Create a new calendar entry."""
    service = build("calendar", "v3", credentials=creds)
    start = entry.start.astimezone(timezone.utc).replace(tzinfo=None).isoformat() + 'Z'
    end = entry.end.astimezone(timezone.utc).replace(tzinfo=None).isoformat() + 'Z'
    event = {
        'summary': entry.summary,
        'start': {
            'dateTime': start,
            'timeZone': 'UTC',
        },
        'end': {
            'dateTime': end,
            'timeZone': 'UTC',
        },
        'description': entry.description,
        'location': entry.location
    }
    try:
        created_event = service.events().insert(calendarId=calendar_id, body=event).execute()
        return CalendarEntry(
            id=created_event['id'],
            summary=created_event.get('summary', 'No Title'),
            start=datetime.fromisoformat(created_event['start'].get('dateTime', created_event['start'].get('date'))).isoformat(),
            end=datetime.fromisoformat(created_event['end'].get('dateTime', created_event['end'].get('date'))).isoformat(),
            description=created_event.get('description'),
            location=created_event.get('location')
        )
    except HttpError as error:
        print(f"An error occurred: {error}")
        return None    
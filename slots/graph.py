# slots/services/graph.py
import requests
from datetime import datetime, timezone,time

from zoneinfo import ZoneInfo
from django.conf import settings

IST = ZoneInfo("Asia/Kolkata")


def get_graph_token():
    url = f"https://login.microsoftonline.com/{settings.MICROSOFT_TENANT_ID}/oauth2/v2.0/token"

    data = {
        "client_id": settings.MICROSOFT_CLIENT_ID,
        "client_secret": settings.MICROSOFT_CLIENT_SECRET,
        "scope": settings.GRAPH_API_SCOPE,
        "grant_type": "client_credentials",
    }

    r = requests.post(url, data=data)
    r.raise_for_status()
    return r.json()["access_token"]


def get_interviewer_busy_slots(email, start_ist, end_ist):
    """Fetch ALL busy Outlook events in IST."""

    token = get_graph_token()

    # Convert IST → UTC
    start_utc = start_ist.astimezone(timezone.utc).isoformat()
    end_utc = end_ist.astimezone(timezone.utc).isoformat()

    url = f"https://graph.microsoft.com/v1.0/users/{email}/calendarView"

    params = {
        "startDateTime": start_utc,
        "endDateTime": end_utc,
    }

    headers = {
        "Authorization": f"Bearer {token}",
        "Prefer": 'outlook.timezone="Asia/Kolkata"',
    }

    r = requests.get(url, headers=headers, params=params)
    r.raise_for_status()

    events = r.json().get("value", [])

    busy = []

    for event in events:
        try:
            start = datetime.fromisoformat(event["start"]["dateTime"])
            end = datetime.fromisoformat(event["end"]["dateTime"])

            if start.tzinfo is None:
                start = start.replace(tzinfo=timezone.utc)
            if end.tzinfo is None:
                end = end.replace(tzinfo=timezone.utc)

            busy.append({
                "start": start.astimezone(IST),
                "end": end.astimezone(IST),
                "reason": event.get("subject", "Busy"),
            })

        except:
            continue

    return busy




# def create_teams_meeting(interviewer_email: str, candidate_email: str, start_dt: datetime, end_dt: datetime, subject="Interview"):
#     """
#     Creates an event in interviewer's calendar with Teams meeting.
#     Returns the event JSON (including onlineMeeting joinUrl).
#     start_dt/end_dt are aware datetimes in IST or will be converted to IST strings.
#     """
#     token = get_graph_token()
#     url = f"https://graph.microsoft.com/v1.0/users/{interviewer_email}/events"

#     # Ensure times are ISO with timezone name for the body
#     body = {
#         "subject": subject,
#         "start": {"dateTime": start_dt.astimezone(IST).strftime("%Y-%m-%dT%H:%M:%S"), "timeZone": "India Standard Time"},
#         "end": {"dateTime": end_dt.astimezone(IST).strftime("%Y-%m-%dT%H:%M:%S"), "timeZone": "India Standard Time"},
#         "attendees": [
#             {"emailAddress": {"address": candidate_email, "name": candidate_email}, "type": "required"}
#         ],
#         "isOnlineMeeting": True,
#         "onlineMeetingProvider": "teamsForBusiness",
#         "allowRecording": True,
#         "allowTranscription": True
#     }

#     headers = {
#         "Authorization": f"Bearer {token}",
#         "Content-Type": "application/json"
#     }

#     r = requests.post(url, json=body, headers=headers)
#     r.raise_for_status()
#     return r.json()

def create_teams_meeting(interviewer_email, candidate_email, start_dt, end_dt, subject):
    token = get_graph_token()

    url = f"https://graph.microsoft.com/v1.0/users/{interviewer_email}/onlineMeetings"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    data = {
        "startDateTime": start_dt.isoformat(),
        "endDateTime": end_dt.isoformat(),
        "subject": subject,
        "allowedPresenters": "everyone",
        "participants": {
            "attendees": [
                {
                    "upn": candidate_email,
                    "role": "attendee"
                }
            ]
        },
        "isRecordingEnabled": True,
        "isTranscriptEnabled": True
    }

    resp = requests.post(url, json=data, headers=headers)
    print("Create meeting response:", resp.text)
    return resp.json()


def get_day_range_utc(date_ist):
    day_start_ist = datetime.combine(date_ist, time.min, tzinfo=IST)
    day_end_ist = datetime.combine(date_ist, time.max, tzinfo=IST)

    return (
        day_start_ist.astimezone(timezone.utc),
        day_end_ist.astimezone(timezone.utc)
    )


def fetch_meeting_transcript(organizer_email, meeting_id):
    """Fetch meeting transcript (text) from Microsoft Graph."""
    
    token = get_graph_token()

    url = f"https://graph.microsoft.com/v1.0/users/{organizer_email}/onlineMeetings/{meeting_id}/transcripts"

    headers = {
        "Authorization": f"Bearer {token}"
    }

    r = requests.get(url, headers=headers)

    if not r.ok:
        print("Transcript fetch error:", r.text)
        return None

    transcripts = r.json().get("value", [])

    if not transcripts:
        return None

    transcript_id = transcripts[0]["id"]

    # Fetch transcript content
    url2 = f"https://graph.microsoft.com/v1.0/users/{organizer_email}/onlineMeetings/{meeting_id}/transcripts/{transcript_id}/content"

    r2 = requests.get(url2, headers=headers)

    if not r2.ok:
        print("Transcript content error:", r2.text)
        return None

    return r2.text   # plain text transcript

def fetch_meeting_recording(organizer_email, meeting_id):
    """Fetch meeting recording download URL."""

    token = get_graph_token()

    url = f"https://graph.microsoft.com/v1.0/users/{organizer_email}/onlineMeetings/{meeting_id}"

    headers = {
        "Authorization": f"Bearer {token}"
    }

    r = requests.get(url, headers=headers)

    if not r.ok:
        print("Recording fetch error:", r.text)
        return None

    meeting = r.json()

    # Check if recording link is available
    recording_url = meeting.get("recordingUrl")  # May not always exist

    return recording_url

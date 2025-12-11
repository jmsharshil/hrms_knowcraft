# slots/services/graph.py
import requests
from datetime import datetime, timezone,time

from zoneinfo import ZoneInfo
from django.conf import settings
from dateutil import parser as dateutil_parser
import zoneinfo

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

WINDOWS_TO_IANA = {
    "India Standard Time": "Asia/Kolkata",
    "UTC": "UTC",
    "Pacific Standard Time": "America/Los_Angeles",
    # add others you use...
}

def _localize_graph_datetime(dt_str, tz_str):
    """
    Given Graph's dt_str and tz_str, return an aware datetime.
    dt_str may include offset (ISO) or be naive. tz_str is Graph's timeZone (Windows name).
    """
    # parse with dateutil (handles offset if present)
    dt = dateutil_parser.isoparse(dt_str)

    if dt.tzinfo is not None:
        return dt  # already aware

    # dt is naive — try to derive tz from tz_str
    if tz_str:
        iana = WINDOWS_TO_IANA.get(tz_str) or tz_str  # try using mapping, fall back
        try:
            tz = zoneinfo.ZoneInfo(iana)
        except Exception:
            # fallback to project timezone
            tz = zoneinfo.ZoneInfo(settings.TIME_ZONE)
        return dt.replace(tzinfo=tz)

    # no tz_str provided — fallback to project timezone
    return dt.replace(tzinfo=zoneinfo.ZoneInfo(settings.TIME_ZONE))

def get_interviewer_busy_slots(email, start_ist, end_ist):
    """Fetch ALL busy Outlook events in IST and return aware datetimes converted to IST ZoneInfo objects."""
    token = get_graph_token()

    # Send times to Graph in UTC ISO format (Graph accepts ISO with offset)
    start_utc = start_ist.astimezone(timezone.utc).isoformat()
    end_utc = end_ist.astimezone(timezone.utc).isoformat()

    url = f"https://graph.microsoft.com/v1.0/users/{email}/calendarView"
    params = {"startDateTime": start_utc, "endDateTime": end_utc}
    headers = {
        "Authorization": f"Bearer {token}",
        # Prefer Graph to return values in the specified timezone; still, the API may return dateTime + timeZone separately.
        "Prefer": 'outlook.timezone="Asia/Kolkata"',
    }

    r = requests.get(url, headers=headers, params=params)
    r.raise_for_status()
    events = r.json().get("value", [])

    busy = []
    for event in events:
        try:
            ev_start = event.get("start", {})
            ev_end = event.get("end", {})
            start_dt_str = ev_start.get("dateTime")
            end_dt_str = ev_end.get("dateTime")
            start_tz = ev_start.get("timeZone")
            end_tz = ev_end.get("timeZone")

            if not start_dt_str or not end_dt_str:
                continue

            # Get aware datetimes (respect Graph-provided timezone if naive)
            start_aware = _localize_graph_datetime(start_dt_str, start_tz)
            end_aware = _localize_graph_datetime(end_dt_str, end_tz)

            # Convert to IST (ZoneInfo) for consistent display
            ist = ZoneInfo("Asia/Kolkata")
            start_in_ist = start_aware.astimezone(ist)
            end_in_ist = end_aware.astimezone(ist)

            busy.append({
                "start": start_in_ist,
                "end": end_in_ist,
                "reason": event.get("subject", "Busy"),
            })

        except Exception:
            # skip malformed events but don't crash
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

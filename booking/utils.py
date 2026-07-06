import requests
from datetime import datetime, timedelta
from django.utils.dateparse import parse_datetime as dj_parse_datetime
from django.core.exceptions import ValidationError
from django.utils import timezone
from slots.graph import get_graph_token
from .models import Booking,SystemLock
from slots.models import Interviewer
from zoneinfo import ZoneInfo
from onboarding.utils.sender import send_email
from django.conf import settings
from django.db import transaction
import os
import time
import threading
from onboarding.utils.task_queue import TASK_QUEUE

IST = ZoneInfo("Asia/Kolkata")
BASE_URL = getattr(settings,"BACKEND_URL","https://hireproknowcraft-crhacdc8dxd7dfhh.centralindia-01.azurewebsites.net")

#datetime parser
def parse_datetime(value):
    """
    Accepts:
    - ISO format (2026-03-13T13:00:00 or with timezone)
    - DD-MM-YYYY HH:MM:SS (13-03-2026 13:00:00)

    Converts everything to IST timezone.
    Prevents past datetime booking.
    """

    if not value:
        raise ValidationError("Datetime value is required")

    dt = None

    # 1️⃣ Try ISO format first
    dt = dj_parse_datetime(value)

    # 2️⃣ Try custom format if ISO fails
    if not dt:
        try:
            dt = datetime.strptime(value, "%d-%m-%Y %H:%M:%S")
        except ValueError:
            raise ValidationError(
                "Invalid datetime format. Use ISO format (YYYY-MM-DDTHH:MM:SS) "
                "or DD-MM-YYYY HH:MM:SS"
            )

    # 3️⃣ Make timezone aware
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt, IST)

    # 4️⃣ Convert everything to IST
    dt = dt.astimezone(IST)
    
    # 5️⃣ Prevent past booking
    now_ist = timezone.now().astimezone(IST)

    if dt <= now_ist:
        raise ValidationError("Interview time cannot be in the past")

    return dt

#online interview Scheduling
def create_teams_meeting(organizer_email, attendee_emails, start_dt, end_dt, subject):
    token = get_graph_token()

    url = f"https://graph.microsoft.com/v1.0/users/{organizer_email}/events"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    attendees = [
        {
            "emailAddress": {"address": email},
            "type": "required"
        }
        for email in attendee_emails
    ]

    data = {
        "subject": subject,
        "start": {
            "dateTime": start_dt.isoformat(),
            "timeZone": "Asia/Kolkata"
        },
        "end": {
            "dateTime": end_dt.isoformat(),
            "timeZone": "Asia/Kolkata"
        },
        "attendees": attendees,
        "isOnlineMeeting": True,
        "onlineMeetingProvider": "teamsForBusiness"
    }

    response = requests.post(url, json=data, headers=headers)
    
    if not response.ok:
        print("Graph Error:", response.text)
        return None

    return response.json()

#For In person interview scheduling
def create_calendar_event(organizer_email, attendee_emails, start_dt, end_dt, subject, location=None):
    token = get_graph_token()

    url = f"https://graph.microsoft.com/v1.0/users/{organizer_email}/events"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    attendees = [
        {
            "emailAddress": {"address": email},
            "type": "required"
        }
        for email in attendee_emails
    ]

    data = {
        "subject": subject,
        "start": {
            "dateTime": start_dt.isoformat(),
            "timeZone": "Asia/Kolkata"
        },
        "end": {
            "dateTime": end_dt.isoformat(),
            "timeZone": "Asia/Kolkata"
        },
        "attendees": attendees,
        "location": {
            "displayName": location or "Office"
        }
    }

    response = requests.post(url, json=data, headers=headers)

    if not response.ok:
        print("Graph Error:", response.text)
        return None

    return response.json()

def create_graph_subscription(user_email):
    token = get_graph_token()

    url = "https://graph.microsoft.com/v1.0/subscriptions"

    expiration = (datetime.utcnow() + timedelta(hours=1)).isoformat() + "Z"

    data = {
        "changeType": "updated,deleted",
        "notificationUrl": f"{BASE_URL}/api/booking/webhooks/graph/",
        "resource": f"users/{user_email}/events",
        "expirationDateTime": expiration,
        "clientState": "secureRandomString123"
    }

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    response = requests.post(url, json=data, headers=headers)

    if not response.ok:
        print("Subscription Error:", response.text)
        return None

    return response.json()

def renew_all_subscriptions():
    interviewers = Interviewer.objects.all()

    for interviewer in interviewers:
        create_graph_subscription(interviewer.email)

def update_teams_meeting(organizer_email, event_id, start_dt=None, end_dt=None, subject=None):
    token = get_graph_token()

    url = f"https://graph.microsoft.com/v1.0/users/{organizer_email}/events/{event_id}"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    data = {}

    if subject:
        data["subject"] = subject

    if start_dt:
        data["start"] = {
            "dateTime": start_dt.isoformat(),
            "timeZone": "Asia/Kolkata"
        }

    if end_dt:
        data["end"] = {
            "dateTime": end_dt.isoformat(),
            "timeZone": "Asia/Kolkata"
        }

    response = requests.patch(url, json=data, headers=headers)

    if not response.ok:
        print("Update Error:", response.text)
        return None

    return response.json()

def update_attendees(organizer_email, event_id, attendee_emails):
    token = get_graph_token()

    url = f"https://graph.microsoft.com/v1.0/users/{organizer_email}/events/{event_id}"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    attendees = [
        {
            "emailAddress": {"address": email},
            "type": "required"
        }
        for email in attendee_emails
    ]

    data = {
        "attendees": attendees
    }

    response = requests.patch(url, json=data, headers=headers)

    if not response.ok:
        print("Update Error:", response.text)
        return None

    return response.json()

def cancel_meeting(organizer_email, event_id):
    token = get_graph_token()

    url = f"https://graph.microsoft.com/v1.0/users/{organizer_email}/events/{event_id}"

    headers = {
        "Authorization": f"Bearer {token}"
    }

    response = requests.delete(url, headers=headers)

    if response.status_code != 204:
        print("Cancel Error:", response.text)
        return False

    return True

def reschedule_booking(booking, new_start, new_end):
    update_teams_meeting(
        organizer_email=booking.interviewer.email,
        event_id=booking.meeting_id,
        start_dt=new_start,
        end_dt=new_end
    )

    booking.start = new_start
    booking.end = new_end
    booking.save()

def process_graph_event(notification):
    from slots.models import Interviewer
    from .models import GraphEventLog

    subscription_id = notification.get("subscriptionId")
    resource = notification.get("resource")
    change_type = notification.get("changeType")

    event_id = resource.split("/")[-1]
    interviewer_id = notification.get("clientState")

    # 🔥 DEDUP CHECK
    exists = GraphEventLog.objects.filter(
        event_id=event_id,
        change_type=change_type,
        subscription_id=subscription_id
    ).exists()

    if exists:
        return  # already processed

    # 🔒 LOCK (avoid race condition)
    try:
        GraphEventLog.objects.create(
            event_id=event_id,
            change_type=change_type,
            subscription_id=subscription_id,
            resource=resource
        )
    except:
        return  # duplicate insert → skip

    interviewer = Interviewer.objects.filter(id=interviewer_id).first()
    if not interviewer:
        return

    handle_event(change_type, event_id, interviewer)

def handle_event(change_type, event_id, interviewer):
    booking = Booking.objects.filter(
        meeting_id=event_id,
        interviewer=interviewer
    ).first()

    if not booking:
        return

    if change_type == "deleted":
        if not booking:
            return
        booking.delete()

        send_email(
            subject="Interview Cancelled",
            text="Interview was cancelled from calendar.",
            to=booking.candidate.candidate_email,
            event="interview_cancelled",
            email_type="candidate",
            candidate=booking.candidate
        )

    elif change_type == "updated":
        if not booking:
            return
        event = get_event_details(booking)
        if not event:
            raise Exception("Failed to fetch event")  # 🔥 triggers retry

        start = event.get("start", {}).get("dateTime")
        end = event.get("end", {}).get("dateTime")

        if not start or not end:
            raise Exception("Invalid event data")
        
        new_start = datetime.fromisoformat(start)
        new_end = datetime.fromisoformat(end)

        # 🔥 Only update if actually changed
        if booking.start == new_start and booking.end == new_end:
            return

        booking.start = new_start
        booking.end = new_end
        booking.save()

        send_email(
            subject="Interview Updated",
            text=f"New time: {booking.start}",
            to=booking.candidate.candidate_email,
            event="interview_updated",
            email_type="candidate",
            candidate=booking.candidate
        )

def get_event_details(booking):
        token = get_graph_token()

        url = f"https://graph.microsoft.com/v1.0/users/{booking.interviewer.email}/events/{booking.meeting_id}"

        headers = {
            "Authorization": f"Bearer {token}"
        }

        response = requests.get(url, headers=headers)

        if not response.ok:
            return None

        return response.json()

def check_and_renew_subscription(interviewer_id):
    from slots.models import Interviewer

    interviewer = Interviewer.objects.filter(id=interviewer_id).first()
    if not interviewer:
        return

    now = timezone.now()

    if (
        not interviewer.subscription_expiry or
        interviewer.subscription_expiry <= now + timedelta(minutes=10)
    ):
        create_or_renew_subscription(interviewer)

def renew_subscriptions():
    now = timezone.now()

    interviewers = Interviewer.objects.all()

    for interviewer in interviewers:
        # 🔥 Renew ONLY if expiring soon (within 10 mins)
        if (
            not interviewer.subscription_expiry or
            interviewer.subscription_expiry <= now + timedelta(minutes=10)
        ):
            create_or_renew_subscription(interviewer)

def create_or_renew_subscription(interviewer):
    """
    Create a new Microsoft Graph subscription or renew an existing one
    for an interviewer.
    """

    token = get_graph_token()
    now = timezone.now()

    # If subscription exists and not expiring soon → skip
    if interviewer.subscription_id and interviewer.subscription_expiry and interviewer.subscription_expiry > now + timedelta(minutes=10):
        return {"status": "ok", "message": "Subscription still valid"}

    expiration = (datetime.utcnow() + timedelta(minutes=50)).isoformat() + "Z"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    data = {
        "changeType": "updated,deleted",
        "notificationUrl": f"{BASE_URL}/api/booking/webhooks/graph/",
        "resource": f"users/{interviewer.email}/events",
        "expirationDateTime": expiration,
        "clientState": str(interviewer.id)
    }

    if interviewer.subscription_id:
        # 🔹 Try updating existing subscription
        url = f"https://graph.microsoft.com/v1.0/subscriptions/{interviewer.subscription_id}"
        response = requests.patch(url, json=data, headers=headers)

        if not response.ok:
            print(f"⚠️ Failed to update subscription {interviewer.email}: {response.text}")
            # fallback: create new subscription
            interviewer.subscription_id = None
            return create_or_renew_subscription(interviewer)

        res = response.json()
    else:
        # 🔹 Create new subscription
        url = "https://graph.microsoft.com/v1.0/subscriptions"
        response = requests.post(url, json=data, headers=headers)

        if not response.ok:
            print(f"⚠️ Failed to create subscription {interviewer.email}: {response.text}")
            return None

        res = response.json()

    # ✅ Save subscription info
    interviewer.subscription_id = res.get("id")
    interviewer.subscription_expiry = datetime.fromisoformat(
        res.get("expirationDateTime").replace("Z", "+00:00")
    )
    interviewer.save()

    return res

def get_booking_by_candidate(candidate_id):
    return Booking.objects.filter(
        candidate_id=candidate_id
    ).order_by("-created_at").first()

def delete_subscription(subscription_id):
    token = get_graph_token()

    url = f"https://graph.microsoft.com/v1.0/subscriptions/{subscription_id}"

    headers = {
        "Authorization": f"Bearer {token}"
    }

    requests.delete(url, headers=headers)

def init_graph_subscriptions():
    """
    Initialize or renew Microsoft Graph subscriptions for all interviewers
    safely at server startup, using TASK_QUEUE for async processing.
    """

    # ❌ prevent dev double run with Django autoreload
    if os.environ.get("RUN_MAIN") != "true":
        return

    lock_key = "graph_subscription_init"

    try:
        with transaction.atomic():
            # 🔒 Acquire lock (only one server runs this)
            lock, created = SystemLock.objects.select_for_update().get_or_create(
                key=lock_key
            )

            if not created:
                print("⚠️ Subscription init already done by another instance")
                return

            print("🚀 Running subscription init (single instance)")

            now = timezone.now()
            interviewers = Interviewer.objects.all()

            for interviewer in interviewers:
                # 🔥 Enqueue subscription creation if expiring soon
                if not interviewer.subscription_expiry or interviewer.subscription_expiry <= now + timedelta(minutes=10):
                    TASK_QUEUE.enqueue(create_or_renew_subscription, interviewer)

    except Exception as e:
        print("Startup error:", e)

def periodic_subscription_renewal(interval_minutes=5):
    """
    Background thread to periodically check and renew Microsoft Graph subscriptions
    for all interviewers.
    """
    def run():
        while True:
            try:
                now = timezone.now()
                interviewers = Interviewer.objects.all()

                for interviewer in interviewers:
                    # 🔥 Renew if expiring soon (10 mins)
                    if not interviewer.subscription_expiry or interviewer.subscription_expiry <= now + timedelta(minutes=10):
                        TASK_QUEUE.enqueue(create_or_renew_subscription, interviewer)

            except Exception as e:
                print("Subscription renewal check failed:", e)

            time.sleep(interval_minutes * 60)  # Sleep before next check

    t = threading.Thread(target=run, daemon=True)
    t.start()
    print("✅ Periodic subscription renewal thread started")
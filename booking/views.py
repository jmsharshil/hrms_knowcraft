# booking/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.mail import send_mail
from django.conf import settings
from .serializers import BookingSerializer
from .models import Booking
from slots.models import Interviewer,Slot
from slots.graph import create_teams_meeting
from zoneinfo import ZoneInfo
from slots.availability import TEMP_SLOT_STORAGE
from datetime import datetime, timedelta, date
import requests
from slots.graph import get_graph_token,fetch_meeting_recording,fetch_meeting_transcript
from jobs.serializers import JobApplicationSerializer
from jobs.models import JobApplication
from rest_framework import permissions
from onboarding.utils.sender import send_email,send_text,send_document
from onboarding.utils.resume_attachment import get_resume_attachment
from django.utils.dateparse import parse_datetime as dj_parse_datetime,parse_date
from django.db import transaction
from django.core.exceptions import ValidationError
from django.db.models import Count, Q
from django.utils import timezone

IST = ZoneInfo("Asia/Kolkata")

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

class SendSlotSelectionEmailView(APIView):
    def post(self, request):
        serializer = JobApplicationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)
        candidate = serializer.save()

        interviewer_id = request.data.get("interviewer_id")
        if not interviewer_id:
            return Response({"detail": "interviewer_id is required"}, status=400)

        # Build selection link (candidate chooses interviewer then slot)
        selection_link = (
            f"http://127.0.0.1:8000/api/slots/available/"
            f"?candidate_id={candidate.id}&interviewer_id={interviewer_id}"
        )

        subject = "Choose your interview slot"
        message = f"Hello {candidate.candidate_name},\n\nClick to select your slot:\n{selection_link}\n\nThanks"
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [candidate.candidate_email], fail_silently=False)
        return Response({"detail": "Email sent", "candidate_id": candidate.id})


# class CandidateBookSlotView(APIView):
#     """
#     POST /api/booking/candidate/<candidate_id>/book/
#     Body: {"interviewer_id": "<uuid>", "start": "2025-11-20T15:00:00+05:30", "end": "2025-11-20T15:30:00+05:30"}
#     """
#     def post(self, request, candidate_id):
#         candidate = Candidate.objects.filter(id=candidate_id).first()
#         if not candidate:
#             return Response({"detail": "Candidate not found"}, status=404)

#         interviewer_id = request.data.get("interviewer_id")
#         start_raw = request.data.get("start")
#         end_raw = request.data.get("end")
#         if not (interviewer_id and start_raw and end_raw):
#             return Response({"detail": "interviewer_id, start and end are required"}, status=400)

#         interviewer = Interviewer.objects.filter(id=interviewer_id).first()
#         if not interviewer:
#             return Response({"detail": "Interviewer not found"}, status=404)

#         # parse datetimes
#         start_dt = parser.isoparse(start_raw)
#         end_dt = parser.isoparse(end_raw)

#         # Create Teams meeting
#         event = create_teams_meeting(interviewer.email, candidate.email, start_dt, end_dt, subject=f"Interview: {candidate.full_name}")
#         meeting_id = event.get("id")
#         meeting_link = None
#         # Graph may provide onlineMeeting or onlineMeeting.joinUrl
#         if event.get("onlineMeeting") and event["onlineMeeting"].get("joinUrl"):
#             meeting_link = event["onlineMeeting"]["joinUrl"]
#         elif event.get("onlineMeetingUrl"):
#             meeting_link = event["onlineMeetingUrl"]
#         elif event.get("onlineMeeting") and event["onlineMeeting"].get("joinWebUrl"):
#             meeting_link = event["onlineMeeting"].get("joinWebUrl")

#         # Save booking
#         booking = Booking.objects.create(
#             candidate=candidate,
#             interviewer=interviewer,
#             meeting_id=meeting_id,
#             meeting_link=meeting_link,
#             start=start_dt,
#             end=end_dt
#         )

#         # Send emails
#         start_str = start_dt.astimezone(IST).strftime("%d/%m/%Y %I:%M %p")
#         subject_c = "Interview Confirmed"
#         msg_c = f"Hello {candidate.full_name},\nYour interview is confirmed with {interviewer.name} at {start_str}.\nJoin link: {meeting_link}"
#         send_mail(subject_c, msg_c, settings.DEFAULT_FROM_EMAIL, [candidate.email], fail_silently=False)

#         subject_i = "New Interview Scheduled"
#         msg_i = f"Hello {interviewer.name},\nYou have interview with {candidate.full_name} at {start_str}.\nJoin link: {meeting_link}"
#         send_mail(subject_i, msg_i, settings.DEFAULT_FROM_EMAIL, [interviewer.email], fail_silently=False)

#         serializer = BookingSerializer(booking)
#         return Response(serializer.data, status=201)

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


class CandidateBookSlotView(APIView):
    """
    POST /api/booking/candidate/<candidate_id>/book/
    Body:
    {
        "slot_id": "<uuid>",
        "interviewer_id": "<uuid>"
    }
    """
    permission_classes = [permissions.AllowAny]
    def post(self, request, candidate_id):

        # 1) Validate candidate
        candidate = JobApplication.objects.filter(id=candidate_id).first()
        if not candidate:
            return Response({"detail": "Candidate not found"}, status=404)

        # 2) Validate inputs
        # slot_id = request.data.get("slot_id")
        interviewer_id = request.data.get("interviewer_id")

        # if not slot_id:
        #     return Response({"detail": "slot_id is required"}, status=400)

        if not interviewer_id:
            return Response({"detail": "interviewer_id is required"}, status=400)

        # 3) Validate interviewer
        interviewer = Interviewer.objects.filter(id=interviewer_id).first()
        if not interviewer:
            return Response({"detail": "Invalid interviewer_id"}, status=400)

        # 4) Validate slot
        # slot = Slot.objects.filter(id=slot_id).first()
        # if not slot:
        #     return Response({"detail": "Invalid slot_id"}, status=400)

        # 5) Slot must belong to selected interviewer
        # (your Slot model is M2M: slot.interviewers)
        # if not slot.interviewers.filter(id=interviewer.id).exists():
        #     return Response(
        #         {"detail": "This slot does not belong to selected interviewer"},
        #         status=400
        #     )

        # 6) Slot already booked?
        # if slot.is_booked:
        #     return Response({"detail": "This slot is already booked"}, status=400)

        # 7) Create Teams meeting
        start = request.data.get("start")
        end = request.data.get("end")

        if not start or not end:
            return Response({"detail": "start and end time are required"}, status=400)

        try:
            start_dt = parse_datetime(start)
            end_dt = parse_datetime(end)
        except ValidationError as ve:
            return Response({"details": ve},status=400)
        except:
            return Response({"detail": "Invalid datetime format"}, status=400)

        attendees = [candidate.candidate_email]

        # Add all technical interviewers
        if candidate.status in ['interview_next_2', 'interview_pending_2'] and candidate.job.mrf.technical_interviewers.exists():
            for tech in candidate.job.mrf.technical_interviewers.all():
                if str(tech.id) == str(interviewer_id):
                    continue
                attendees.append(tech.email)

        attendees = list(set(attendees))

        event = create_teams_meeting(
            interviewer.email,
            attendees,
            start_dt,
            end_dt,
            subject=f"Interview: {candidate.candidate_name}"
        )

        if not event:
            return Response({"detail": "Failed to create Teams meeting"}, status=500)

        meeting_link = (
            event.get("onlineMeeting", {}).get("joinUrl")
            or event.get("onlineMeetingUrl")
            or event.get("onlineMeeting", {}).get("joinWebUrl")
            or None
        )

        # 8) Save booking
        booking = Booking.objects.create(
            candidate=candidate,
            interviewer=interviewer,
            meeting_id=event.get("id"),
            meeting_link=meeting_link,
            # slot=slot,         # <-- IMPORTANT
            start=start_dt,
            end=end_dt
        )

        # Mark slot as booked
        # slot.is_booked = True
        # slot.save()

        # 9) Email notifications
        start_str = start_dt.astimezone(IST).strftime("%d/%m/%Y %I:%M %p")

        round = None
        round_name = ""

        designation = candidate.job.mrf.designation.name
        level = get_experience_level(designation)

        BASE_URL = getattr(settings, 'FRONTEND_URL', 'https://knowcrafthrms-djfkb4hseuf0adcy.centralindia-01.azurewebsites.net')
        resume_attachment = get_resume_attachment(candidate)
        # Determine round
        if candidate.status in ['shortlisted', 'interview_pending_1']:
            if candidate.job.mrf.interviewer_email_1:
                round = "hr_round"
                round_name = "HR Round"
            elif candidate.job.mrf.interviewer_email_2:
                round = "technical_round"
                round_name = "Technical Round"
            elif candidate.job.mrf.interviewer_email_3:
                round = "case_study_round"
                round_name = "Case Study Round"
            elif candidate.job.mrf.interviewer_email_final:
                round = "final_round"
                round_name = "Final Round"

        elif candidate.status in ['interview_next_2', 'interview_pending_2']:
            round = "technical_round"
            round_name = "Technical Round"
            if candidate.job.mrf.technical_interviewers.exists():
                for interviewer in candidate.job.mrf.technical_interviewers.all():
                    if str(interviewer.id) == str(interviewer_id):
                        continue
                    base_path = FEEDBACK_PATHS.get(round, {}).get(level, "/api/slots/hrfresher/")

                    feedback_link = (
                        f"{BASE_URL}{base_path}"
                        f"?interview_round={round}&job_application={candidate.id}"
                    )
                    send_email(
                        subject=f"Interview Scheduled - {candidate.candidate_name} ({candidate.job.mrf.designation.name})",
                        text=f"Dear {interviewer.name},\nThis is to inform you that the interview for Mr./Mrs.{candidate.candidate_name} for the role of {candidate.job.mrf.designation.name} has been scheduled on {start_str}.\nPlease find below the MS Teams link and attached candidate’s details.\n Join Link: {meeting_link}\n Feedback link: {feedback_link}",
                        template=f"""
                        <html>
                        <body style="margin:0;padding:0;background-color:#f4f4f7;font-family:Arial,Helvetica,sans-serif;">
                            <table align="center" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width:620px;margin:0 auto;background-color:#f4f4f7;">
                                <tr>
                                    <td align="center" style="padding:30px 15px;">
                                        <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color:#ffffff;border:1px solid #e0e3e9;border-radius:12px;overflow:hidden;box-shadow:0 4px 12px rgba(0,0,0,0.06);">
                                            <!-- Logo -->
                                            <tr>
                                                <td align="center" style="padding:40px 30px 25px 30px;background:#ffffff;">
                                                    <img src="https://hireprostorage.blob.core.windows.net/media/knowcraft_logo.png" alt="Knowcraft Analytics" style="max-width:280px;height:auto;display:block;margin:0 auto;">
                                                </td>
                                            </tr>
                                            <!-- Separator -->
                                            <tr><td style="padding:0 40px;"><hr style="border:0;border-top:1px solid #f0f2f7;margin:0;"></td></tr>
                                            <!-- Content -->
                                            <tr>
                                                <td style="padding:35px 40px 40px 40px;color:#333333;font-size:16px;">
                                                    <h2 style="margin:0 0 22px 0;color:#1f2937;font-size:24px;font-weight:600;">Interview Scheduled — {round_name}</h2>
                                                    <p style="margin:0 0 16px 0;">Dear {interviewer.name},</p>
                                                    <p style="margin:0 0 16px 0;">This is to inform you that the interview for <strong>{candidate.candidate_name}</strong> for the role of <strong>{candidate.job.mrf.designation.name}</strong> has been scheduled on <strong>{start_str}</strong>.</p>
                                                    <p style="margin:0 0 16px 0;">Please find below the MS Teams link and candidate details:</p>
                                                    
                                                    <!-- Clean Link Table -->
                                                    <table style="margin:22px 0;width:100%;border-collapse:collapse;background:#f8fafc;border-radius:8px;overflow:hidden;">
                                                        <tr>
                                                            <td style="padding:16px 20px;width:140px;font-weight:600;color:#475569;border-bottom:1px solid #e2e8f0;">Join Link</td>
                                                            <td style="padding:16px 20px;border-bottom:1px solid #e2e8f0;">
                                                                <a href="{meeting_link}" style="color:#2563eb;text-decoration:underline;font-weight:500;">Join Meeting</a>
                                                            </td>
                                                        </tr>
                                                        <tr>
                                                            <td style="padding:16px 20px;width:140px;font-weight:600;color:#475569;">Resume</td>
                                                            <td style="padding:16px 20px;">
                                                                <a href="{candidate.resume.url}" style="color:#2563eb;text-decoration:underline;font-weight:500;">View / Download Resume</a>
                                                            </td>
                                                        </tr>
                                                    </table>
                                                    
                                                    <p style="margin:25px 0 16px 0;">Please join the meeting on time and keep the candidate’s resume handy.</p>
                                                    <br>
                                                    <p style="margin:20px 0 6px 0;color:#555555;">Warm Regards,</p>
                                                    <p style="margin:0;font-weight:700;color:#1f2937;">Team – HR</p>
                                                    <p style="margin:4px 0 0 0;color:#555555;">Knowcraft Analytics Private Limited</p>
                                                </td>
                                            </tr>
                                            <!-- Footer -->
                                            <tr>
                                                <td style="background:#f8fafc;padding:18px 40px;text-align:center;font-size:13px;color:#64748b;border-top:1px solid #e2e8f0;">
                                                    © 2026 Knowcraft Analytics Private Limited • Confidential
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                            </table>
                        </body>
                        </html>""",
                        to=interviewer.email,
                        attachments=[resume_attachment] if resume_attachment else None
                    )
                    if interviewer.phone:
                        send_text(to=interviewer.phone,text=f"Dear {interviewer.name},\nThis is to inform you that the interview for Mr./Mrs.{candidate.candidate_name} for the role of {candidate.job.mrf.designation.name} has been scheduled on {start_str}.\nPlease find below the MS Teams link and attached candidate’s details.\n Join Link: {meeting_link}")
                        send_document(to=interviewer.phone,text="Candidate Resume",file_url=candidate.resume.url,filename=f'{candidate.candidate_name}_Resume.pdf')

        elif candidate.status in ['interview_next_3', 'interview_pending_3']:
            round = "case_study_round"
            round_name = "Case Study Round"

        elif candidate.status in ['interview_next_final', 'interview_pending_final']:
            round = "final_round"
            round_name = "Final Round"

        elif candidate.status in ['interview_next_management_client', 'interview_pending_management_client']:
            round = "management_client_round"
            round_name = "Management / Client Round"

        # Resolve feedback path
        base_path = FEEDBACK_PATHS.get(round, {}).get(level, "/api/slots/hrfresher/")

        feedback_link = (
            f"{BASE_URL}{base_path}"
            f"?interview_round={round}&job_application={candidate.id}"
        )

        send_email(
            subject=f"Interview Scheduled – {candidate.job.mrf.designation.name} at Knowcraft Analytics Private Limited",
            text=f"""Dear {candidate.candidate_name},\nWe are pleased to inform you have been shortlisted for {round_name} of Interview for the position of {candidate.job.mrf.designation.name} has been scheduled at {start_str}.\nJoin link: {meeting_link}\nKindly ensure that you join the interview via given link on time using a laptop or desktop for a smooth experience.
\nWe look forward to speaking with you.
\nPlease feel free to reach out if you have any questions or require further assistance.
\nWarm regards,
\nTeam-HR
\nKnowcraft Analytics Private Limited""",
            template=f"""<html>
        <body style="margin:0;padding:0;background-color:#f4f4f7;font-family:Arial,Helvetica,sans-serif;">
            <table align="center" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width:620px;margin:0 auto;background-color:#f4f4f7;">
                <tr>
                    <td align="center" style="padding:30px 15px;">
                        <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color:#ffffff;border:1px solid #e0e3e9;border-radius:12px;overflow:hidden;box-shadow:0 4px 12px rgba(0,0,0,0.06);">
                            <!-- Logo -->
                            <tr>
                                <td align="center" style="padding:40px 30px 25px 30px;background:#ffffff;">
                                    <img src="https://hireprostorage.blob.core.windows.net/media/knowcraft_logo.png" alt="Knowcraft Analytics" style="max-width:280px;height:auto;display:block;margin:0 auto;">
                                </td>
                            </tr>
                            <!-- Separator -->
                            <tr><td style="padding:0 40px;"><hr style="border:0;border-top:1px solid #f0f2f7;margin:0;"></td></tr>
                            <!-- Content -->
                            <tr>
                                <td style="padding:35px 40px 45px 40px;color:#333333;font-size:16px;">
                                    <h2 style="margin:0 0 22px 0;color:#1f2937;font-size:24px;font-weight:600;">Interview Scheduled — {round_name}</h2>
                                    <p style="margin:0 0 16px 0;">Dear {candidate.candidate_name},</p>
                                    <p style="margin:0 0 20px 0;">We are pleased to inform you that your <strong>{round_name}</strong> interview for the position of <strong>{candidate.job.mrf.designation.name}</strong> has been scheduled on <strong>{start_str}</strong>.</p>
                                    
                                    <!-- Big Join Button -->
                                    <p style="margin:30px 0 35px 0;text-align:center;">
                                        <a href="{meeting_link}" 
                                        style="background-color:#2563eb;color:#ffffff;padding:16px 36px;text-decoration:none;border-radius:8px;font-weight:600;font-size:17px;display:inline-block;">
                                            Join Interview on MS Teams
                                        </a>
                                    </p>
                                    
                                    <p style="margin:0 0 16px 0;">Kindly ensure you join the interview via the link above on time using a laptop or desktop for the best experience.</p>
                                    <p style="margin:0 0 16px 0;">We look forward to speaking with you.</p>
                                    <p style="margin:0 0 16px 0;">Please feel free to reach out if you have any questions or require further assistance.</p>
                                    <br>
                                    <p style="margin:20px 0 6px 0;color:#555555;">Warm regards,</p>
                                    <p style="margin:0;font-weight:700;color:#1f2937;">Team – HR</p>
                                    <p style="margin:4px 0 0 0;color:#555555;">Knowcraft Analytics Private Limited</p>
                                </td>
                            </tr>
                            <!-- Footer -->
                            <tr>
                                <td style="background:#f8fafc;padding:18px 40px;text-align:center;font-size:13px;color:#64748b;border-top:1px solid #e2e8f0;">
                                    © 2026 Knowcraft Analytics Private Limited
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        </body>
        </html>""",
            to=candidate.candidate_email
        )
        send_text(to=candidate.candidate_phone,text=f"""Dear {candidate.candidate_name},\nWe are pleased to inform you have been shortlisted for {round_name} of Interview for the position of {candidate.job.mrf.designation.name} has been scheduled at {start_str}.\nJoin link: {meeting_link}\nKindly ensure that you join the interview via given link on time using a laptop or desktop for a smooth experience.
\nWe look forward to speaking with you.
\nPlease feel free to reach out if you have any questions or require further assistance.
\nWarm regards,
\nTeam-HR
\nKnowcraft Analytics Private Limited""")
        interviewer,created = Interviewer.objects.get_or_create(id=interviewer_id)
        send_email(
            subject=f"Interview Scheduled - {candidate.candidate_name} ({candidate.job.mrf.designation.name})",
            text=f"Dear {interviewer.name},\nThis is to inform you that the interview for Mr./Mrs.{candidate.candidate_name} for the role of {candidate.job.mrf.designation.name} has been scheduled on {start_str}.\nPlease find below the MS Teams link and attached candidate’s details.\n Join Link: {meeting_link}\n Feedback link: {feedback_link}",
            template=f"""
            <html>
        <body style="margin:0;padding:0;background-color:#f4f4f7;font-family:Arial,Helvetica,sans-serif;">
            <table align="center" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width:620px;margin:0 auto;background-color:#f4f4f7;">
                <tr>
                    <td align="center" style="padding:30px 15px;">
                        <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color:#ffffff;border:1px solid #e0e3e9;border-radius:12px;overflow:hidden;box-shadow:0 4px 12px rgba(0,0,0,0.06);">
                            <!-- Logo -->
                            <tr>
                                <td align="center" style="padding:40px 30px 25px 30px;background:#ffffff;">
                                    <img src="https://hireprostorage.blob.core.windows.net/media/knowcraft_logo.png" alt="Knowcraft Analytics" style="max-width:280px;height:auto;display:block;margin:0 auto;">
                                </td>
                            </tr>
                            <!-- Separator -->
                            <tr><td style="padding:0 40px;"><hr style="border:0;border-top:1px solid #f0f2f7;margin:0;"></td></tr>
                            <!-- Content -->
                            <tr>
                                <td style="padding:35px 40px 40px 40px;color:#333333;font-size:16px;">
                                    <h2 style="margin:0 0 22px 0;color:#1f2937;font-size:24px;font-weight:600;">Interview Scheduled — {round_name}</h2>
                                    <p style="margin:0 0 16px 0;">Dear {interviewer.name},</p>
                                    <p style="margin:0 0 16px 0;">This is to inform you that the interview for <strong>{candidate.candidate_name}</strong> for the role of <strong>{candidate.job.mrf.designation.name}</strong> has been scheduled on <strong>{start_str}</strong>.</p>
                                    <p style="margin:0 0 16px 0;">Please find below the MS Teams link and candidate details:</p>
                                    
                                    <table style="margin:20px 0;width:100%;border-collapse:collapse;">
                                        <tr>
                                            <td style="padding:12px 0;width:140px;font-weight:600;color:#475569;">Join Link:</td>
                                            <td style="padding:12px 0;">
                                                <a href="{meeting_link}" style="color:#2563eb;text-decoration:underline;font-weight:500;">Join Meeting</a>
                                            </td>
                                        </tr>
                                        <tr>
                                            <td style="padding:12px 0;width:140px;font-weight:600;color:#475569;">Feedback Link:</td>
                                            <td style="padding:12px 0;">
                                                <a href="{feedback_link}" style="color:#2563eb;text-decoration:underline;font-weight:500;">Give feedback</a>
                                            </td>
                                        </tr>
                                        <tr>
                                            <td style="padding:12px 0;width:140px;font-weight:600;color:#475569;">Resume:</td>
                                            <td style="padding:12px 0;">
                                                <a href="{candidate.resume.url}" style="color:#2563eb;text-decoration:underline;font-weight:500;">View / Download Resume</a>
                                            </td>
                                        </tr>
                                    </table>
                                    
                                    <p style="margin:25px 0 16px 0;">Kindly join the meeting on time.</p>
                                    <br>
                                    <p style="margin:20px 0 6px 0;color:#555555;">Warm Regards,</p>
                                    <p style="margin:0;font-weight:700;color:#1f2937;">Team – HR</p>
                                    <p style="margin:4px 0 0 0;color:#555555;">Knowcraft Analytics Private Limited</p>
                                </td>
                            </tr>
                            <!-- Footer -->
                            <tr>
                                <td style="background:#f8fafc;padding:18px 40px;text-align:center;font-size:13px;color:#64748b;border-top:1px solid #e2e8f0;">
                                    © 2026 Knowcraft Analytics Private Limited • Confidential
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        </body>
        </html>""",
            to=interviewer.email,
            attachments=[resume_attachment] if resume_attachment else None
        )
        if interviewer.phone:
            send_text(to=interviewer.phone,text=f"Dear {interviewer.name},\nThis is to inform you that the interview for Mr./Mrs.{candidate.candidate_name} for the role of {candidate.job.mrf.designation.name} has been scheduled on {start_str}.\nPlease find below the MS Teams link and attached candidate’s details.\n Join Link: {meeting_link}\n Feedback link: {feedback_link}")
            send_document(to=interviewer.phone,text="Candidate Resume",file_url=candidate.resume.url,filename=f'{candidate.candidate_name}_Resume.pdf')
        candidate.interview_link = meeting_link
        candidate.interviewer_name = interviewer.name
        candidate.interview_scheduled_at = start_dt
        candidate.feedback_link = feedback_link
        candidate.save()
        from onboarding.utils.engine import automation_engine
        if candidate.status == 'shortlisted':
            if candidate.job.mrf.interviewer_email_1:
                automation_engine(candidate,candidate.status,'interview_pending_1')
            elif candidate.job.mrf.interviewer_email_2:
                automation_engine(candidate,candidate.status,'interview_pending_2')
            elif candidate.job.mrf.interviewer_email_3:
                automation_engine(candidate,candidate.status,'interview_pending_3')
            elif candidate.job.mrf.interviewer_email_final:
                automation_engine(candidate,candidate.status,'interview_pending_final')
        elif candidate.status == 'interview_next_2':
            automation_engine(candidate,candidate.status,'interview_pending_2')
        elif candidate.status == 'interview_next_3':
            automation_engine(candidate,candidate.status,'interview_pending_3')
        elif candidate.status == 'interview_next_final':
            automation_engine(candidate,candidate.status,'interview_pending_final')
        elif candidate.status == 'interview_next_management_client':
            automation_engine(candidate, candidate.status, 'interview_pending_management_client')
        return Response(BookingSerializer(booking).data, status=201)

FRESHER_DESIGNATIONS = [
    "Analyst", "Associate", "Advanced Analyst", "Advanced Associate"
]

JUNIOR_DESIGNATIONS = [
    "Senior Analyst I", "Senior Analyst II",
    "Senior Associate I", "Senior Associate II",
    "Team Lead"
]

SENIOR_DESIGNATIONS = [
    "Assistant Manager", "Associate Manager",
    "Manager", "Senior Manager",
    "Associate Vice President"
]

FEEDBACK_PATHS = {
    "hr_round": {
        "fresher": "/api/slots/hrfresher/",
        "junior": "/api/slots/hrjunior/",
        "senior": "/api/slots/hrsenior/",
    },
    "technical_round": {
        "fresher": "/api/slots/techfresher/",
        "junior": "/api/slots/techjunior/",
        "senior": "/api/slots/techsenior/",
    },
    "case_study_round": {
        "fresher": "/api/slots/techfresher/",
        "junior": "/api/slots/techjunior/",
        "senior": "/api/slots/techsenior/",
    },
    "final_round": {
        "fresher": "/api/slots/techfresher/",
        "junior": "/api/slots/techjunior/",
        "senior": "/api/slots/techsenior/",
    },
}

def get_experience_level(designation):
    if designation in FRESHER_DESIGNATIONS:
        return "fresher"
    if designation in JUNIOR_DESIGNATIONS:
        return "junior"
    if designation in SENIOR_DESIGNATIONS:
        return "senior"
    return "fresher"  # safe default


def send_notifications(candidate,start_dt,end_dt,interviewer,location):
    start_str = start_dt.astimezone(IST).strftime("%d/%m/%Y %I:%M %p")

    designation = candidate.job.mrf.designation.name
    level = get_experience_level(designation)

    round = None
    round_name = ""
    resume_attachment = get_resume_attachment(candidate)

    location_str = location.full_address if hasattr(location, 'full_address') else str(location)
    maps_link = location.google_maps_link if hasattr(location, 'google_maps_link') else None

    attendees = [candidate.candidate_email]

    # Add all technical interviewers
    if candidate.status in ['interview_next_2', 'interview_pending_2'] and candidate.job.mrf.technical_interviewers.exists():
        for tech in candidate.job.mrf.technical_interviewers.all():
            if str(tech.id) == str(interviewer.id):
                continue
            attendees.append(tech.email)

    attendees = list(set(attendees))

    event = create_calendar_event(
        interviewer.email,
        attendees,
        start_dt,
        end_dt,
        subject=f"In-Person Interview: {candidate.candidate_name}",
        location= location_str
    )

    if candidate.status in ['shortlisted', 'interview_pending_1']:
        if candidate.job.mrf.interviewer_email_1:
            round = "hr_round"
            round_name = "HR Round"
        elif candidate.job.mrf.interviewer_email_2:
            round = "technical_round"
            round_name = "Technical Round"
        elif candidate.job.mrf.interviewer_email_3:
            round = "case_study_round"
            round_name = "Case Study Round"
        elif candidate.job.mrf.interviewer_email_final:
            round = "final_round"
            round_name = "Final Round"

    elif candidate.status in ['interview_next_2', 'interview_pending_2']:
        round = "technical_round"
        round_name = "Technical Round"
        # 🔹 Notify other technical interviewers
        if candidate.job.mrf.technical_interviewers.exists():
            for tech_interviewer in candidate.job.mrf.technical_interviewers.all():
                if str(tech_interviewer.id) == str(interviewer.id):
                    continue

                base_path = FEEDBACK_PATHS.get(round, {}).get(level, "/api/slots/hrfresher/")
                feedback_link = (
                    f"{settings.FRONTEND_URL}{base_path}"
                    f"?interview_round={round}&job_application={candidate.id}"
                )

                send_email(
                    subject=f"In-Person Interview Scheduled - {candidate.candidate_name}",
                    text=f"""Dear {tech_interviewer.name},

Interview for {candidate.candidate_name} ({designation}) has been scheduled.

Date & Time: {start_str}
Location: {location_str}

Goole Map Link:
{maps_link}

Warm Regards,
Team – HR""",
                    template=f"""
                        <html>
                        <body style="margin:0;padding:0;background-color:#f4f4f7;font-family:Arial,Helvetica,sans-serif;">
                            <table align="center" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width:620px;margin:0 auto;background-color:#f4f4f7;">
                                <tr>
                                    <td align="center" style="padding:30px 15px;">
                                        <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color:#ffffff;border:1px solid #e0e3e9;border-radius:12px;overflow:hidden;box-shadow:0 4px 12px rgba(0,0,0,0.06);">
                                            <!-- Logo -->
                                            <tr>
                                                <td align="center" style="padding:40px 30px 25px 30px;background:#ffffff;">
                                                    <img src="https://hireprostorage.blob.core.windows.net/media/knowcraft_logo.png" alt="Knowcraft Analytics" style="max-width:280px;height:auto;display:block;margin:0 auto;">
                                                </td>
                                            </tr>
                                            <!-- Separator -->
                                            <tr><td style="padding:0 40px;"><hr style="border:0;border-top:1px solid #f0f2f7;margin:0;"></td></tr>
                                            <!-- Content -->
                                            <tr>
                                                <td style="padding:35px 40px 45px 40px;color:#333333;font-size:16px;line-height:1.6;">
                                                    <h2 style="margin:0 0 24px 0;color:#1f2937;font-size:24px;font-weight:600;">Interview Scheduled — {candidate.candidate_name}</h2>
                                                    
                                                    <p style="margin:0 0 16px 0;">Dear <strong>{tech_interviewer.name}</strong>,</p>
                                                    
                                                    <p style="margin:0 0 20px 0;">
                                                        Interview for <strong>{candidate.candidate_name}</strong> (<strong>{designation}</strong>) has been scheduled.
                                                    </p>
                                                    
                                                    <!-- Details Box -->
                                                    <table style="width:100%;border:1px solid #e2e8f0;border-radius:12px;margin:20px 0;padding:20px 24px;">
                                                        <tr>
                                                            <td style="padding:8px 0;font-weight:600;color:#475569;width:140px;">📅 Date & Time</td>
                                                            <td style="padding:8px 0;font-weight:500;">{start_str}</td>
                                                        </tr>
                                                        <tr>
                                                            <td style="padding:8px 0;font-weight:600;color:#475569;">📍 Location</td>
                                                            <td style="padding:8px 0;font-weight:500;"><a href="{maps_link}" target="_blank">{location_str}</a></td>
                                                        </tr>
                                                    </table>                                                       
                                                    <br>
                                                    <p style="margin:20px 0 6px 0;color:#555555;">Warm Regards,</p>
                                                    <p style="margin:0;font-weight:700;color:#1f2937;">Team – HR</p>
                                                    <p style="margin:4px 0 0 0;color:#555555;">Knowcraft Analytics Private Limited</p>
                                                </td>
                                            </tr>
                                            <!-- Footer -->
                                            <tr>
                                                <td style="background:#f8fafc;padding:18px 40px;text-align:center;font-size:13px;color:#64748b;border-top:1px solid #e2e8f0;">
                                                    © 2026 Knowcraft Analytics Private Limited • Confidential
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                            </table>
                        </body>
                        </html>
                    """,
                    to=tech_interviewer.email,
                    attachments=[resume_attachment] if resume_attachment else None
                )
                if tech_interviewer.phone:
                    send_text(to=tech_interviewer.phone,text=f"""Dear {tech_interviewer.name},

Interview for {candidate.candidate_name} ({designation}) has been scheduled.

Date & Time: {start_str}
Location: {location_str}

Goole Map Link:
{maps_link}

Warm Regards,
Team – HR""")
                    send_document(to=interviewer.phone,text="Candidate Resume",file_url=candidate.resume.url,filename=f'{candidate.candidate_name}_Resume.pdf')
    elif candidate.status in ['interview_next_3', 'interview_pending_3']:
        round = "case_study_round"
        round_name = "Case Study Round"
    elif candidate.status in ['interview_next_final', 'interview_pending_final']:
        round = "final_round"
        round_name = "Final Round"
    elif candidate.status in ['interview_next_management_client', 'interview_pending_management_client']:
        round = "management_client_round"
        round_name = "Management / Client Round"

    BASE_URL = getattr(settings, 'FRONTEND_URL')
    base_path = FEEDBACK_PATHS.get(round, {}).get(level, "/api/slots/hrfresher/")

    feedback_link = (
        f"{BASE_URL}{base_path}"
        f"?interview_round={round}&job_application={candidate.id}"
    )

    # ==============================
    # 📧 Candidate Email (In-Person)
    # ==============================
    send_email(
        subject=f"In-Person Interview Scheduled – {designation}",
        text=f"""Dear {candidate.candidate_name},

Your {round_name} interview for the position of {designation} has been scheduled.

📅 Date & Time: {start_str}
📍 Location: {location_str}

Goole Map Link:
{maps_link}

Kindly report 10-15 minutes before the scheduled time.

Warm Regards,
Team – HR
Knowcraft Analytics Private Limited
""",
        to=candidate.candidate_email,
        template=f"""
        <html>
        <body style="margin:0;padding:0;background-color:#f4f4f7;font-family:Arial,Helvetica,sans-serif;">
            <table align="center" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width:620px;margin:0 auto;background-color:#f4f4f7;">
                <tr>
                    <td align="center" style="padding:30px 15px;">
                        <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color:#ffffff;border:1px solid #e0e3e9;border-radius:12px;overflow:hidden;box-shadow:0 4px 12px rgba(0,0,0,0.06);">
                            <!-- Logo -->
                            <tr>
                                <td align="center" style="padding:40px 30px 25px 30px;background:#ffffff;">
                                    <img src="https://hireprostorage.blob.core.windows.net/media/knowcraft_logo.png" alt="Knowcraft Analytics" style="max-width:280px;height:auto;display:block;margin:0 auto;">
                                </td>
                            </tr>
                            <!-- Separator -->
                            <tr><td style="padding:0 40px;"><hr style="border:0;border-top:1px solid #f0f2f7;margin:0;"></td></tr>
                            <!-- Content -->
                            <tr>
                                <td style="padding:35px 40px 45px 40px;color:#333333;font-size:16px;line-height:1.6;">
                                    <h2 style="margin:0 0 24px 0;color:#1f2937;font-size:24px;font-weight:600;">Interview Scheduled — {round_name}</h2>
                                    
                                    <p style="margin:0 0 16px 0;">Dear <strong>{candidate.candidate_name}</strong>,</p>
                                    
                                    <p style="margin:0 0 24px 0;">
                                        Your <strong>{round_name}</strong> interview for the position of <strong>{designation}</strong> has been scheduled.
                                    </p>
                                    
                                    <!-- Details Box -->
                                    <table style="width:100%;background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;margin:20px 0;padding:20px 24px;border-collapse:collapse;">
                                        <tr>
                                            <td style="padding:8px 0;font-weight:600;color:#475569;width:140px;">📅 Date & Time</td>
                                            <td style="padding:8px 0;font-weight:500;">{start_str}</td>
                                        </tr>
                                        <tr>
                                            <td style="padding:8px 0;font-weight:600;color:#475569;">📍 Location</td>
                                            <td style="padding:8px 0;font-weight:500;"><a href="{maps_link}" target="_blank">{location_str}</a></td>
                                        </tr>
                                    </table>
                                    
                                    <p style="margin:0 0 24px 0;color:#1f2937;font-weight:500;">
                                        Kindly report 10–15 minutes before the scheduled time.
                                    </p>
                                    
                                    <p style="margin:0 0 16px 0;">We look forward to meeting you.</p>
                                    
                                    <br>
                                    <p style="margin:20px 0 6px 0;color:#555555;">Warm Regards,</p>
                                    <p style="margin:0;font-weight:700;color:#1f2937;">Team – HR</p>
                                    <p style="margin:4px 0 0 0;color:#555555;">Knowcraft Analytics Private Limited</p>
                                </td>
                            </tr>
                            <!-- Footer -->
                            <tr>
                                <td style="background:#f8fafc;padding:18px 40px;text-align:center;font-size:13px;color:#64748b;border-top:1px solid #e2e8f0;">
                                    © 2026 Knowcraft Analytics Private Limited • Confidential
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        </body>
        </html>
    """
    )

    # SMS
    send_text(
        to=candidate.candidate_phone,
        text=f"""Dear {candidate.candidate_name}, your {round_name} interview for {designation} is scheduled on {start_str} at {location_str}.\n Please arrive early.\n Location: {maps_link}\n - HR"""
    )

    # ==============================
    # 📧 Interviewer Email
    # ==============================
    send_email(
        subject=f"In-Person Interview Scheduled - {candidate.candidate_name}",
        text=f"""Dear {interviewer.name},

The {round_name} interview for {candidate.candidate_name} ({designation}) has been scheduled.

📅 Date & Time: {start_str}
📍 Location: {location_str}

Goole Map Link:
{maps_link}

Feedback Link:
{feedback_link}

Warm Regards,
Team – HR""",
        to=interviewer.email,
        template=f"""
        <html>
        <body style="margin:0;padding:0;background-color:#f4f4f7;font-family:Arial,Helvetica,sans-serif;">
            <table align="center" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width:620px;margin:0 auto;background-color:#f4f4f7;">
                <tr>
                    <td align="center" style="padding:30px 15px;">
                        <table border="0" cellpadding="0" cellspacing="0" width="100%" style="background-color:#ffffff;border:1px solid #e0e3e9;border-radius:12px;overflow:hidden;box-shadow:0 4px 12px rgba(0,0,0,0.06);">
                            <!-- Logo -->
                            <tr>
                                <td align="center" style="padding:40px 30px 25px 30px;background:#ffffff;">
                                    <img src="https://hireprostorage.blob.core.windows.net/media/knowcraft_logo.png" alt="Knowcraft Analytics" style="max-width:280px;height:auto;display:block;margin:0 auto;">
                                </td>
                            </tr>
                            <!-- Separator -->
                            <tr><td style="padding:0 40px;"><hr style="border:0;border-top:1px solid #f0f2f7;margin:0;"></td></tr>
                            <!-- Content -->
                            <tr>
                                <td style="padding:35px 40px 45px 40px;color:#333333;font-size:16px;line-height:1.6;">
                                    <h2 style="margin:0 0 24px 0;color:#1f2937;font-size:24px;font-weight:600;">Interview Scheduled — {candidate.candidate_name}</h2>
                                    
                                    <p style="margin:0 0 16px 0;">Dear <strong>{interviewer.name}</strong>,</p>
                                    
                                    <p style="margin:0 0 20px 0;">
                                        Interview for <strong>{candidate.candidate_name}</strong> (<strong>{designation}</strong>) has been scheduled.
                                    </p>
                                    
                                    <!-- Details Box -->
                                    <table style="width:100%;border:1px solid #e2e8f0;border-radius:12px;margin:20px 0;padding:20px 24px;">
                                        <tr>
                                            <td style="padding:8px 0;font-weight:600;color:#475569;width:140px;">📅 Date & Time</td>
                                            <td style="padding:8px 0;font-weight:500;">{start_str}</td>
                                        </tr>
                                        <tr>
                                            <td style="padding:8px 0;font-weight:600;color:#475569;">📍 Location</td>
                                            <td style="padding:8px 0;font-weight:500;"><a href="{maps_link}" target="_blank">{location_str}</a></td>
                                        </tr>
                                    </table>
                                    
                                    <!-- Feedback Button -->
                                    <p style="margin:30px 0 35px 0;text-align:center;">
                                        <a href="{feedback_link}" 
                                        style="background-color:#2563eb;color:#ffffff;padding:16px 36px;text-decoration:none;border-radius:8px;font-weight:600;font-size:17px;display:inline-block;">
                                            Submit Feedback
                                        </a>
                                    </p>
                                    
                                    <p style="margin:0 0 16px 0;">Please submit your feedback after the interview using the link above.</p>
                                    
                                    <br>
                                    <p style="margin:20px 0 6px 0;color:#555555;">Warm Regards,</p>
                                    <p style="margin:0;font-weight:700;color:#1f2937;">Team – HR</p>
                                    <p style="margin:4px 0 0 0;color:#555555;">Knowcraft Analytics Private Limited</p>
                                </td>
                            </tr>
                            <!-- Footer -->
                            <tr>
                                <td style="background:#f8fafc;padding:18px 40px;text-align:center;font-size:13px;color:#64748b;border-top:1px solid #e2e8f0;">
                                    © 2026 Knowcraft Analytics Private Limited • Confidential
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        </body>
        </html>
    """,
    attachments=[resume_attachment] if resume_attachment else None
    )

    if interviewer.phone:
        send_text(to=interviewer.phone,text=f"""Dear {interviewer.name},

The {round_name} interview for {candidate.candidate_name} ({designation}) has been scheduled.

📅 Date & Time: {start_str}
📍 Location: {location_str}

Goole Map Link:
{maps_link}

Feedback Link:
{feedback_link}

Warm Regards,
Team – HR""")
        send_document(to=interviewer.phone,text="Candidate Resume",file_url=candidate.resume.url,filename=f'{candidate.candidate_name}_Resume.pdf')
    # Update candidate fields
    candidate.interviewer_name = interviewer.name
    candidate.interview_scheduled_at = start_dt
    candidate.feedback_link = feedback_link
    candidate.interview_link = None
    candidate.save()

    # ✅ Same automation logic
    from onboarding.utils.engine import automation_engine

    if candidate.status == 'shortlisted':
        if candidate.job.mrf.interviewer_email_1:
            automation_engine(candidate,candidate.status,'interview_pending_1')
        elif candidate.job.mrf.interviewer_email_2:
            automation_engine(candidate,candidate.status,'interview_pending_2')
        elif candidate.job.mrf.interviewer_email_3:
            automation_engine(candidate,candidate.status,'interview_pending_3')
        elif candidate.job.mrf.interviewer_email_final:
            automation_engine(candidate,candidate.status,'interview_pending_final')
    elif candidate.status == 'interview_next_2':
        automation_engine(candidate, candidate.status, 'interview_pending_2')
    elif candidate.status == 'interview_next_3':
        automation_engine(candidate, candidate.status, 'interview_pending_3')
    elif candidate.status == 'interview_next_final':
        automation_engine(candidate, candidate.status, 'interview_pending_final')
    elif candidate.status == 'interview_next_management_client':
        automation_engine(candidate, candidate.status, 'interview_pending_management_client')

class CandidateBookInPersonInterviewView(APIView):
    """
    POST /api/booking/candidate/book-inperson/

    Body:
    {
        "interviewer_id": "<uuid>",
        "candidate_id": "<uuid>",
        "start": "2026-02-28T11:00:00+05:30",
        "end": "2026-02-28T12:00:00+05:30",
        "location_id": "<uuid>"
    }
    """

    permission_classes = [permissions.AllowAny]

    def post(self, request):

        candidate_id = request.data.get("candidate_id")
        if not candidate_id:
            return Response({"detail": "candidate_id is required"}, status=400)
        try:
            with transaction.atomic():
                candidate = (
                    JobApplication.objects
                    .select_for_update()
                    .filter(id=candidate_id)
                    .first()
                )
                if not candidate:
                    return Response({"detail": "Candidate not found"}, status=404)

                interviewer_id = request.data.get("interviewer_id")
                start = request.data.get("start")
                end = request.data.get("end")
                location_id = request.data.get("location_id")

                from slots.models import InterviewLocation
                location = None
                if location_id:
                    location = InterviewLocation.objects.get(id=location_id)
                else:
                    return Response({"detail": "location is required"}, status=400)

                if not interviewer_id:
                    return Response({"detail": "interviewer_id is required"}, status=400)
                if not start or not end:
                    return Response({"detail": "start and end time are required"}, status=400)
                if not location:
                    return Response({"detail": "location is required"}, status=400)

                interviewer = (
                    Interviewer.objects
                    .select_for_update()
                    .filter(id=interviewer_id)
                    .first()
                )

                if not interviewer:
                    return Response({"detail": "Invalid interviewer_id"}, status=400)

                try:
                    start_dt = parse_datetime(start)
                    end_dt = parse_datetime(end)
                except ValidationError as ve:
                    return Response({"details": ve},status=400)
                except:
                    return Response({"detail": "Invalid datetime format"}, status=400)
                
                if not start_dt or not end_dt:
                    return Response(
                        {"detail": "Invalid datetime format. Use ISO format e.g. 2026-02-28T11:00:00+05:30"},
                        status=400
                    )

                # Make timezone aware if naive
                if timezone.is_naive(start_dt):
                    start_dt = timezone.make_aware(start_dt)

                if timezone.is_naive(end_dt):
                    end_dt = timezone.make_aware(end_dt)

                if start_dt >= end_dt:
                    return Response(
                        {"detail": "End time must be after start time"},
                        status=400
                    )

                # # 🔒 Check interviewer overlap (inside atomic block)
                # interviewer_overlap = Booking.objects.filter(
                #     interviewer=interviewer,
                #     start__lt=end_dt,
                #     end__gt=start_dt
                # ).exists()

                # if interviewer_overlap:
                #     return Response(
                #         {"detail": "Interviewer already booked in this time range"},
                #         status=400
                #     )

                # # 🔒 Check candidate overlap
                # candidate_overlap = Booking.objects.filter(
                #     candidate=candidate,
                #     start__lt=end_dt,
                #     end__gt=start_dt
                # ).exists()

                # if candidate_overlap:
                #     return Response(
                #         {"detail": "Candidate already has an interview scheduled in this time range"},
                #         status=400
                #     )

                # ✅ Create booking
                booking = Booking.objects.create(
                    candidate=candidate,
                    interviewer=interviewer,
                    interview_type="in_person",
                    location=location,
                    start=start_dt,
                    end=end_dt
                )
        except ValidationError as e:
            return Response({"detail": str(e)}, status=400)

        except Exception as e:
            return Response({"detail": str(e)}, status=500)

        try:
            transaction.on_commit(lambda: send_notifications(candidate, start_dt, end_dt, interviewer, location))
        except Exception as e:
            return Response({"Error":"Unable to book an interview:{e}"},status=500)
        return Response(BookingSerializer(booking).data, status=201)

class FetchMeetingData(APIView):
    """
    POST /api/booking/fetch-data/
    Body: {"booking_id": "<uuid>"}
    """

    def post(self, request):
        booking_id = request.data.get("booking_id")
        if not booking_id:
            return Response({"detail": "booking_id required"}, status=400)

        booking = Booking.objects.filter(id=booking_id).first()
        if not booking:
            return Response({"detail": "Booking not found"}, status=404)

        organizer_email = booking.interviewer.email
        meeting_id = booking.meeting_id

        # Fetch transcript text
        transcript_text = fetch_meeting_transcript(organizer_email, meeting_id)

        if transcript_text:
            booking.transcript = transcript_text

        # Fetch recording (download URL)
        recording_url = fetch_meeting_recording(organizer_email, meeting_id)

        if recording_url:
            booking.recording_url = recording_url  # add this field to model

        booking.save()

        return Response({
            "detail": "Fetched successfully",
            "transcript": transcript_text,
            "recording_url": recording_url
        })

class MeetingWebhookView(APIView):
    """
    Microsoft Graph webhook for meeting events:
    - recording ready
    - transcript updated
    """

    def post(self, request):
        # 1) Validation token for Graph
        if "validationToken" in request.query_params:
            return Response(request.query_params["validationToken"], content_type="text/plain")

        value = request.data.get("value", [])
        if not value:
            return Response({"detail": "No notifications"}, status=200)

        token = get_graph_token()

        for item in value:
            resource = item.get("resource", "")

            # Example resource: communications/onlineMeetings('MEETING_ID')
            if "onlineMeetings" in resource:
                meeting_id = resource.split("'")[1]

                try:
                    booking = Booking.objects.get(meeting_id=meeting_id)
                except Booking.DoesNotExist:
                    continue

                # FETCH transcript
                transcript = fetch_meeting_transcript(booking.interviewer.email, meeting_id)

                # FETCH recording
                recording_url = fetch_meeting_recording(booking.interviewer.email, meeting_id)

                if transcript:
                    booking.transcript = transcript

                if recording_url:
                    booking.recording_url = recording_url

                booking.save()

        return Response({"detail": "OK"})

class BranchWiseInterviewReportView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):

        bookings = Booking.objects.all()

        # ---------------------------
        # Date Filtering
        # ---------------------------
        start_date = request.GET.get("start_date")
        end_date = request.GET.get("end_date")

        if start_date:
            start_date = parse_date(start_date)
            bookings = bookings.filter(start__date__gte=start_date)

        if end_date:
            end_date = parse_date(end_date)
            bookings = bookings.filter(start__date__lte=end_date)

        # ---------------------------
        # Company Filtering
        # ---------------------------
        company_id = request.GET.get("company_id")
        if company_id:
            bookings = bookings.filter(location__company_id=company_id)

        # ---------------------------
        # Interviewer Filtering
        # ---------------------------
        interviewer_id = request.GET.get("interviewer_id")
        if interviewer_id:
            bookings = bookings.filter(interviewer_id=interviewer_id)

        # ---------------------------
        # Branch Aggregation
        # ---------------------------
        branch_data = (
            bookings
            .values(
                "location__id",
                "location__name",
                "location__city",
                "location__company__name"
            )
            .annotate(
                total_interviews=Count("id"),
                in_person_count=Count("id", filter=Q(interview_type="in_person")),
                online_count=Count("id", filter=Q(interview_type="online")),
                # ✅ Round-wise breakdown
                hr_round_count=Count("id", filter=Q(candidate__status__in=['shortlisted','interview_pending_1'])),
                technical_round_count=Count("id", filter=Q(candidate__status__in=['interview_next_2','interview_pending_2'])),
                case_study_round_count=Count("id", filter=Q(candidate__status__in=['interview_next_3','interview_pending_3'])),
                final_round_count=Count("id", filter=Q(candidate__status__in=['interview_next_final','interview_pending_final'])),
                management_client_round_count=Count("id", filter=Q(candidate__status__in=['interview_next_management_client','interview_pending_management_client'])),
            )
            .order_by("-total_interviews")
        )

        # ---------------------------
        # Online Interviews (No Branch)
        # ---------------------------
        online_without_branch = bookings.filter(
            interview_type="online",
            location__isnull=True
        ).count()

        return Response({
            "branch_summary": branch_data,
            "online_without_branch": online_without_branch,
            "total_interviews": bookings.count()
        })
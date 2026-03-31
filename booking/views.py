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
import requests
from slots.graph import get_graph_token,fetch_meeting_recording,fetch_meeting_transcript
from jobs.serializers import JobApplicationSerializer
from jobs.models import JobApplication
from rest_framework import permissions
from onboarding.utils.sender import send_email,send_text,send_document
from onboarding.utils.resume_attachment import get_resume_attachment
from django.db import transaction
from django.core.exceptions import ValidationError
from django.db.models import Count, Q
from django.utils import timezone
from django.utils.dateparse import parse_date
from .utils import *
from .email_templates import *

IST = ZoneInfo("Asia/Kolkata")

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

        if not candidate.candidate_email:
            return Response("Candidate Email Not Found!Please Add email in Candidate to continue.",status=400)
    
        attendees = []

        # Add all technical interviewers
        # if candidate.status in ['interview_next_2', 'interview_pending_2'] and candidate.job.mrf.technical_interviewers.exists():
        #     for tech in candidate.job.mrf.technical_interviewers.all():
        #         if str(tech.id) == str(interviewer_id):
        #             continue
        #         attendees.append(tech.email)

        attendee_ids = request.data.get("attendees", [])
        extra_attendees = Interviewer.objects.filter(id__in=attendee_ids)
        for extra in extra_attendees:
            attendees.append(extra.email)
        
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
        try:
            with transaction.atomic():
                booking = Booking.objects.create(
                    candidate=candidate,
                    interviewer=interviewer,
                    meeting_id=event.get("id"),
                    meeting_link=meeting_link,
                    # slot=slot,         # <-- IMPORTANT
                    start=start_dt,
                    end=end_dt
                )
                booking.attendees.set(extra_attendees)
                if not booking:
                    return Response("Unable to book interview.Try again",status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            return Response(f"Unable to book interview:{e}",status=400)
        
        # Mark slot as booked
        # slot.is_booked = True
        # slot.save()

        # 9) Email notifications
        try:
            transaction.on_commit(lambda: send_online_interview_notification(candidate,meeting_link,interviewer_id,start_dt,extra_attendees,end_dt))
        except Exception as e:
            return Response({"Error":f"Unable to book an interview:{e}"},status=500)
        return Response(BookingSerializer(booking).data, status=201)
    
def send_online_interview_notification(candidate,meeting_link,interviewer_id,start_dt,extra_attendees,end_dt):
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
        # if candidate.job.mrf.technical_interviewers.exists():
        #     for interviewer in candidate.job.mrf.technical_interviewers.all():
        #         if str(interviewer.id) == str(interviewer_id):
        #             continue   

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

    for extra in extra_attendees:
        send_email(
        subject=f"Interview Scheduled - {candidate.candidate_name} ({candidate.job.mrf.designation.name})",
        text=f"Dear {extra.name},\nThis is to inform you that the interview for Mr./Mrs.{candidate.candidate_name} for the role of {candidate.job.mrf.designation.name} has been scheduled on {start_str}.\nPlease find below the MS Teams link and attached candidate’s details.\n Join Link: {meeting_link}",
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
                                    <p style="margin:0 0 16px 0;">Dear {extra.name},</p>
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
        to=extra.email,
        attachments=[resume_attachment] if resume_attachment else None
    )
        if extra.phone:
            send_text(to=extra.phone,text=f"Dear {extra.name},\nThis is to inform you that the interview for Mr./Mrs.{candidate.candidate_name} for the role of {candidate.job.mrf.designation.name} has been scheduled on {start_str}.\nPlease find below the MS Teams link and attached candidate’s details.\n Join Link: {meeting_link}")
            send_document(to=extra.phone,text="Candidate Resume",file_url=candidate.resume.url,filename=f'{candidate.candidate_name}_Resume.pdf')

    candidate.interview_link = meeting_link
    candidate.interviewer_name = interviewer.name
    candidate.interview_scheduled_at = start_dt
    candidate.interview_end_at = end_dt
    candidate.feedback_link = feedback_link
    candidate.round_name = round_name
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


def send_notifications(candidate,start_dt,end_dt,interviewer,location,request):
    start_str = start_dt.astimezone(IST).strftime("%d/%m/%Y %I:%M %p")

    designation = candidate.job.mrf.designation.name
    level = get_experience_level(designation)

    round = None
    round_name = ""
    resume_attachment = get_resume_attachment(candidate)

    location_str = location.full_address if hasattr(location, 'full_address') else str(location)
    maps_link = location.google_maps_link if hasattr(location, 'google_maps_link') else None

    if not candidate.candidate_email:
        return Response("Candidate Email Not Found!Please Add email in Candidate to continue.",status=400)
    attendees = []

    # Add all technical interviewers
    # if candidate.status in ['interview_next_2', 'interview_pending_2'] and candidate.job.mrf.technical_interviewers.exists():
    #     for tech in candidate.job.mrf.technical_interviewers.all():
    #         if str(tech.id) == str(interviewer.id):
    #             continue
    #         attendees.append(tech.email)

    attendee_ids = request.data.get("attendees", [])
    extra_attendees = Interviewer.objects.filter(id__in=attendee_ids)
    for extra in extra_attendees:
        attendees.append(extra.email)
        base_path = FEEDBACK_PATHS.get(round, {}).get(level, "/api/slots/hrfresher/")
        send_email(
            subject=f"In-Person Interview Scheduled - {candidate.candidate_name}",
            text=f"""Dear {extra.name},

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
                                            
                                            <p style="margin:0 0 16px 0;">Dear <strong>{extra.name}</strong>,</p>
                                            
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
            to=extra.email,
            attachments=[resume_attachment] if resume_attachment else None
        )
        if extra.phone:
            send_text(to=extra.phone,text=f"""Dear {extra.name},

Interview for {candidate.candidate_name} ({designation}) has been scheduled.

Date & Time: {start_str}
Location: {location_str}

Goole Map Link:
{maps_link}

Warm Regards,
Team – HR""")
            send_document(to=extra.phone,text="Candidate Resume",file_url=candidate.resume.url,filename=f'{candidate.candidate_name}_Resume.pdf')

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
        # if candidate.job.mrf.technical_interviewers.exists():
        #     for tech_interviewer in candidate.job.mrf.technical_interviewers.all():
        #         if str(tech_interviewer.id) == str(interviewer.id):
        #             continue

        #         base_path = FEEDBACK_PATHS.get(round, {}).get(level, "/api/slots/hrfresher/")
        #         feedback_link = (
        #             f"{settings.FRONTEND_URL}{base_path}"
        #             f"?interview_round={round}&job_application={candidate.id}"
        #         )

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
    candidate.interview_end_at = end_dt
    candidate.feedback_link = feedback_link
    candidate.interview_link = None
    candidate.round_name = round_name
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
                attendees = []
                attendee_ids = request.data.get("attendees", [])
                extra_attendees = Interviewer.objects.filter(id__in=attendee_ids)
                for extra in extra_attendees:
                    attendees.append(extra.email)
                
                attendees = list(set(attendees))
                location_str = location.full_address if hasattr(location, 'full_address') else str(location)

                event = create_calendar_event(
                    interviewer.email,
                    attendees,
                    start_dt,
                    end_dt,
                    subject=f"In-Person Interview: {candidate.candidate_name}",
                    location= location_str
                )

                # ✅ Create booking
                booking = Booking.objects.create(
                    candidate=candidate,
                    interviewer=interviewer,
                    interview_type="in_person",
                    location=location,
                    start=start_dt,
                    end=end_dt,
                    meeting_id=event.get("id"),
                )
                booking.attendees.set(extra_attendees)
        except ValidationError as e:
            return Response({"detail": str(e)}, status=400)

        except Exception as e:
            return Response({"detail": str(e)}, status=500)

        try:
            transaction.on_commit(lambda: send_notifications(candidate, start_dt, end_dt, interviewer, location, request))
        except Exception as e:
            return Response({"Error":f"Unable to book an interview:{e}"},status=500)
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

# #Reschedule date-time of the interview
# class RescheduleBookingView(APIView):
#     permission_classes = [permissions.AllowAny]

#     def patch(self, request, candidate_id):
#         booking = get_booking_by_candidate(candidate_id)
#         if not booking:
#             return Response({"detail": "Booking not found"}, status=404)
        
#         candidate = JobApplication.objects.filter(id=candidate_id).first()

#         start = request.data.get("start")
#         end = request.data.get("end")

#         try:
#             start_dt = parse_datetime(start)
#             end_dt = parse_datetime(end)
#         except ValidationError as ve:
#             return Response({"detail": str(ve)}, status=400)

#         # ✅ ALWAYS update Graph (online + in-person)
#         res = update_teams_meeting(
#             organizer_email=booking.interviewer.email,
#             event_id=booking.meeting_id,
#             start_dt=start_dt,
#             end_dt=end_dt
#         )

#         if res is None:
#             return Response({"detail": "Failed to update event"}, status=500)

#         # ✅ Update DB
#         booking.start = start_dt
#         booking.end = end_dt
#         booking.save()

#         candidate.interview_scheduled_at = start_dt
#         candidate.interview_end_at = end_dt
#         candidate.save()

#         # 🔹 Email content differs
#         start_str = start_dt.astimezone(IST).strftime("%d/%m/%Y %I:%M %p")

#         resume_attachment = get_resume_attachment(candidate)

#         if booking.interview_type == "online":
#             html_content = get_interviewer_email_template(
#                 action="rescheduled",
#                 candidate=candidate,
#                 interviewer=booking.interviewer,
#                 start_str=start_str,
#                 meeting_link=booking.meeting_link,
#                 feedback_link=candidate.feedback_link,
#                 resume_attachment_url=candidate.resume.url
#             )
#             send_email(
#                 subject=f"Interview Rescheduled - {candidate.candidate_name} ({candidate.job.mrf.designation.name})",
#                 text=f"Dear {booking.interviewer.name}, your interview scheduled has been rescheduled at {start_str}.\n Join: {booking.meeting_link} \n Give feedback: {candidate.feedback_link}",
#                 template=html_content,
#                 to=booking.interviewer.email,
#                 attachments=[resume_attachment] if resume_attachment else None
#             )
#             if booking.interviewer.phone:
#                 send_text(booking.interviewer.phone,f"Dear {booking.interviewer.name}, your interview scheduled has been rescheduled at {start_str}.\n Join: {booking.meeting_link} \n Give feedback: {candidate.feedback_link}")
#                 send_document(to=booking.interviewer.phone,text="Candidate Resume",file_url=candidate.resume.url,filename=f'{candidate.candidate_name}_Resume.pdf')

#             send_email(
#                 subject=f"Interview Rescheduled – {candidate.job.mrf.designation.name} at Knowcraft Analytics",
#                 text=reschedule_online_interview_text.format(candidate=candidate,start_str=start_str),
#                 template=reschedule_online_interview_template.format(candidate=candidate,start_str=start_str),
#                 to=candidate.candidate_email
#             )
#             if candidate.candidate_phone:
#                 send_text(to=candidate.candidate_phone,text=reschedule_online_interview_text.format(candidate=candidate,start_str=start_str))

#             attendees = booking.attendees.all()
#             if attendees.exists():
#                 for extra in attendees:
#                     send_email(
#                         subject=f"Online Interview Rescheduled - {candidate.candidate_name}",
#                         text=reschedule_online_interview_extra_text.format(candidate=candidate,booking=booking,start_str=start_str,extra=extra),
#                         to=extra.email,
#                         template=reschedule_online_interview_extra_template.format(candidate=candidate,booking=booking,start_str=start_str,extra=extra),
#                         attachments=[resume_attachment] if resume_attachment else None
#                     )
#                     if extra.phone:
#                         send_text(extra.phone,reschedule_online_interview_extra_text.format(candidate=candidate,booking=booking,start_str=start_str,extra=extra))
#         else:
#             location_str = booking.location.full_address if hasattr(booking, 'location') and hasattr(booking.location, 'full_address') else str(booking.location or "")
#             maps_link = booking.location.google_maps_link if hasattr(booking,"location") and hasattr(booking.location, 'google_maps_link') else None

#             send_email(
#                 subject=f"In-Person Interview Rescheduled - {candidate.candidate_name}",
#                 text= reschedule_offline_interview_text.format(booking=booking,candidate=candidate,start_str=start_str,maps_link=maps_link,location_str=location_str),
#                 to=booking.interviewer.email,
#                 template=reschedule_offline_interview_template.format(booking=booking,candidate=candidate,start_str=start_str,maps_link=maps_link,location_str=location_str),
#                 attachments=[resume_attachment] if resume_attachment else None
#             )

#             if booking.interviewer.phone:
#                 send_text(booking.interviewer.phone,f"Dear {booking.interviewer.name}, your interview scheduled has been rescheduled at {start_str}.\n Location: {location_str}\nGoole Map Link: {maps_link} \n Give feedback: {candidate.feedback_link}")
#                 send_document(to=booking.interviewer.phone,text="Candidate Resume",file_url=candidate.resume.url,filename=f'{candidate.candidate_name}_Resume.pdf')

#             send_email(
#                 subject=f"In-Person Interview Rescheduled – {candidate.job.mrf.designation.name}",
#                 text=reschedule_offline_interview_candidate_text.format(candidate=candidate,start_str=start_str,maps_link=maps_link,location_str=location_str),
#                 to=candidate.candidate_email,
#                 template= reschedule_offline_interview_candidate_template.format(candidate=candidate,start_str=start_str,maps_link=maps_link,location_str=location_str)
#             )

#             if candidate.candidate_phone:
#                 send_text(candidate.candidate_phone,reschedule_offline_interview_candidate_text.format(candidate=candidate,start_str=start_str,maps_link=maps_link,location_str=location_str))
            
#             attendees = booking.attendees.all()
#             if attendees.exists():
#                 for extra in attendees:
#                     send_email(
#                         subject=f"In-Person Interview Rescheduled - {candidate.candidate_name}",
#                         text=reschedule_offline_interview_extra_text.format(candidate=candidate,start_str=start_str,extra=extra,location_str=location_str,maps_link=maps_link),
#                         to=extra.email,
#                         template=reschedule_offline_interview_extra_template.format(candidate=candidate,start_str=start_str,extra=extra,location_str=location_str,maps_link=maps_link),
#                         attachments=[resume_attachment] if resume_attachment else None
#                     )
#                     if extra.phone:
#                         send_text(extra.phone,reschedule_offline_interview_extra_text.format(candidate=candidate,start_str=start_str,extra=extra,location_str=location_str,maps_link=maps_link))
        
#         return Response({"detail": "Rescheduled successfully"})

# #Cancel Scheduled Interview
# class CancelBookingView(APIView):
#     permission_classes = [permissions.AllowAny]

#     def delete(self, request, candidate_id):
#         booking = get_booking_by_candidate(candidate_id)
#         if not booking:
#             return Response({"detail": "Booking not found"}, status=404)

#         # ✅ ALWAYS cancel Graph event
#         if not cancel_meeting(booking.interviewer.email, booking.meeting_id):
#             return Response({"detail": "Failed to cancel event"}, status=500)

#         candidate = JobApplication.objects.filter(id=candidate_id).first()

#         # 🔹 Email content differs
#         if booking.interview_type == "online":
#             html_content = get_interviewer_email_template(
#                 action="cancelled",
#                 candidate=candidate,
#                 interviewer=booking.interviewer,
#                 start_str=candidate.interview_scheduled_at,
#                 meeting_link="",
#                 feedback_link="",
#                 resume_attachment_url=""
#             )
#             send_email(
#                 subject=f"Interview Cancelled - {candidate.candidate_name} ({candidate.job.mrf.designation.name})",
#                 text=f"Dear {booking.interviewer.name}, your interview scheduled at {candidate.interview_scheduled_at} has been cancelled.",
#                 template=html_content,
#                 to=booking.interviewer.email
#             )

#             send_email(
#                 subject=f"Interview Cancelled – {candidate.job.mrf.designation.name} at Knowcraft Analytics",
#                 text=cancel_online_interview_text.format(candidate=candidate),
#                 template=cancel_online_interview_template.format(candidate=candidate),
#                 to=candidate.candidate_email
#             )

#             attendees = booking.attendees.all()
#             if attendees.exists():
#                 for extra in attendees:
#                     send_email(
#                         subject=f"Interview Cancelled - {candidate.candidate_name}",
#                         text=cancel_online_interview_extra_text.format(candidate=candidate,extra=extra),
#                         to=extra.email,
#                         template=cancel_online_interview_extra_template.format(candidate=candidate,extra=extra),
#                     )
#                     if extra.phone:
#                         send_text(extra.phone,cancel_online_interview_extra_text.format(candidate=candidate,extra=extra))
            
#         else:
#             location_str = booking.location.full_address if hasattr(booking, 'location') and hasattr(booking.location, 'full_address') else str(booking.location or "")
#             maps_link = booking.location.google_maps_link if hasattr(booking,"location") and hasattr(booking.location, 'google_maps_link') else None

#             send_email(
#                 subject=f"In-Person Interview Cancelled - {candidate.candidate_name}",
#                 text=cancel_offline_interview_text.format(candidate=candidate,booking=booking,location_str=location_str,maps_link=maps_link),
#                 to=booking.interviewer.email,
#                 template=cancel_offline_interview_template.format(candidate=candidate,booking=booking,location_str=location_str,maps_link=maps_link)
#             )

#             send_email(
#                 subject=f"In-Person Interview Cancelled – {candidate.job.mrf.designation.name}",
#                 text=cancel_offline_interview_candidate_text.format(candidate=candidate,location_str=location_str),
#                 to=candidate.candidate_email,
#                 template=cancel_offline_interview_candidate_template.format(candidate=candidate,location_str=location_str)
#             )

#             attendees = booking.attendees.all()
#             if attendees.exists():
#                 for extra in attendees:
#                     send_email(
#                         subject=f"In-Person Interview Cancelled - {candidate.candidate_name}",
#                         text=cancel_offline_interview_extra_text.format(candidate=candidate,extra=extra,location_str=location_str,maps_link=maps_link),
#                         to=extra.email,
#                         template=cancel_offline_interview_extra_template.format(candidate=candidate,extra=extra,location_str=location_str,maps_link=maps_link),
#                     )
#                     if extra.phone:
#                         send_text(extra.phone,cancel_offline_interview_extra_text.format(candidate=candidate,extra=extra,location_str=location_str,maps_link=maps_link))
        

#         if booking.interviewer.phone:
#             send_text(booking.interviewer.phone,f"Dear {booking.interviewer.name}, your interview scheduled at {candidate.interview_scheduled_at} has been cancelled.")
        
#         if candidate.candidate_phone:
#             send_text(to=candidate.candidate_phone,text=cancel_online_interview_text.format(candidate=candidate))
                    
#         candidate.inperson_link = None
#         candidate.interview_link = None
#         candidate.interview_scheduled_at = None
#         candidate.interview_end_at = None
#         candidate.interviewer_name = None
#         candidate.save()

#         booking.delete()

#         return Response({"detail": "Cancelled successfully"})

# #Update Attendess of the scheduled interview
# class UpdateAttendeesView(APIView):
#     def patch(self, request, candidate_id):
#         booking = get_booking_by_candidate(candidate_id)
#         if not booking:
#             return Response({"detail": "Booking not found"}, status=404)

#         attendee_ids = request.data.get("attendees", [])
#         attendees = Interviewer.objects.filter(id__in=attendee_ids)

#         if not attendees:
#             return Response({"Needs to add attendees to update them!"})

#         if not booking.meeting_id:
#             return Response(
#                 {"detail": "No calendar event linked to this booking"},
#                 status=400
#             )
        
#         emails = [a.email for a in attendees]

#         candidate = JobApplication.objects.filter(id=candidate_id).first()
#         emails.append(candidate.candidate_email)

#         res = update_attendees(booking.interviewer.email, booking.meeting_id, emails)
        
#         if res is None:
#             return Response({"detail": "Failed to update attendees"}, status=500)
        
#         resume_attachment = get_resume_attachment(candidate)

#         if booking.interview_type == 'online':
#             html_content = get_interviewer_email_template(
#                 action="attendees_updated",
#                 candidate=candidate,
#                 interviewer=booking.interviewer,
#                 start_str=candidate.interview_scheduled_at,
#                 meeting_link=booking.meeting_link,
#                 feedback_link=candidate.feedback_link,
#                 resume_attachment_url=candidate.resume.url
#             )

#             send_email(
#                 subject=f"Attendees Updated - {candidate.candidate_name} ({candidate.job.mrf.designation.name})",
#                 text=f"Dear {booking.interviewer.name}, your interview attendees has been updated for interview scheduled at {candidate.interview_scheduled_at}",
#                 template=html_content,
#                 to=booking.interviewer.email
#             )
#             if booking.interviewer.phone:
#                 send_text(booking.interviewer.phone,f"Dear {booking.interviewer.name}, your interview attendees has been updated for interview scheduled at {candidate.interview_scheduled_at}")
            
#             for extra in attendees:
#                 send_email(
#                     subject=f"You’ve been added to an Online Interview - {candidate.candidate_name}",
#                     text=attendees_update_online_text.format(candidate=candidate,booking=booking,extra=extra),
#                     to=extra.email,
#                     template=attendees_update_online_template.format(candidate=candidate,booking=booking,extra=extra),
#                     attachments=[resume_attachment] if resume_attachment else None
#                 )
#                 if extra.phone:
#                     send_text(extra.phone,attendees_update_online_text.format(candidate=candidate,booking=booking,extra=extra))

#         else:
#             location_str = booking.location.full_address if hasattr(booking, 'location') and hasattr(booking.location, 'full_address') else str(booking.location or "")
#             maps_link = booking.location.google_maps_link if hasattr(booking,"location") and hasattr(booking.location, 'google_maps_link') else None
#             send_email(
#                 subject=f"In-Person Interview Updated (Attendees) - {candidate.candidate_name}",
#                 text=attendees_update_interviewer_text.format(booking=booking,candidate=candidate,location_str=location_str),
#                 to=booking.interviewer.email,
#                 template=attendees_update_interviewer_template.format(booking=booking,candidate=candidate,location_str=location_str,maps_link=maps_link)
#             )
#             if booking.interviewer.phone:
#                 send_text(booking.interviewer.phone,attendees_update_interviewer_text.format(booking=booking,candidate=candidate,location_str=location_str))
            
#             for extra in attendees:            
#                 send_email(
#                     subject=f"You’ve been added to an Interview - {candidate.candidate_name}",
#                     text=attendees_update_text.format(candidate=candidate,extra=extra,location_str=location_str,maps_link=maps_link),
#                     to=extra.email,
#                     template=attendees_update_template.format(candidate=candidate,extra=extra,location_str=location_str,maps_link=maps_link),
#                     attachments=[resume_attachment] if resume_attachment else None
#                 )
#                 if extra.phone:
#                     send_text(extra.phone,attendees_update_text.format(candidate=candidate,extra=extra,location_str=location_str,maps_link=maps_link))

#         return Response({"detail": "Attendees updated"})

#All in one for the Booked interview api
class ManageBookingView(APIView):
    permission_classes = [permissions.AllowAny]

    def patch(self, request, candidate_id):
        booking = get_booking_by_candidate(candidate_id)
        if not booking:
            return Response({"detail": "Booking not found"}, status=404)

        candidate = JobApplication.objects.filter(id=candidate_id).first()

        start = request.data.get("start")
        end = request.data.get("end")
        attendee_ids = request.data.get("attendees", None)

        updated_fields = []
        attendees = None

        # ================= RESCHEDULE =================
        if start and end:
            try:
                start_dt = parse_datetime(start)
                end_dt = parse_datetime(end)
            except ValidationError as ve:
                return Response({"detail": str(ve)}, status=400)

            res = update_teams_meeting(
                organizer_email=booking.interviewer.email,
                event_id=booking.meeting_id,
                start_dt=start_dt,
                end_dt=end_dt
            )

            if res is None:
                return Response({"detail": "Failed to update event"}, status=500)

            # Update DB
            booking.start = start_dt
            booking.end = end_dt
            booking.save()

            candidate.interview_scheduled_at = start_dt
            candidate.interview_end_at = end_dt
            candidate.reschedule_count += 1
            candidate.save()

            updated_fields.append("rescheduled")

        # ================= UPDATE ATTENDEES =================
        if attendee_ids is not None:
            attendees = Interviewer.objects.filter(id__in=attendee_ids)

            if not attendees.exists():
                return Response({"detail": "Add valid attendees"}, status=400)

            # ✅ Check if actually changed
            existing_ids = set(booking.attendees.values_list("id", flat=True))
            new_ids = set(attendee_ids)

            if existing_ids != new_ids:
                newly_added_attendees = [a for a in attendees if a.id not in existing_ids]

                emails = [a.email for a in attendees]
                emails.append(candidate.candidate_email)

                res = update_attendees(
                    booking.interviewer.email,
                    booking.meeting_id,
                    emails
                )

                if res is None:
                    return Response({"detail": "Failed to update attendees"}, status=500)

                booking.attendees.set(attendees)
                updated_fields.append("attendees_updated")

        # ================= NOTHING PROVIDED =================
        if not updated_fields:
            return Response(
                {"detail": "Provide 'start/end' or 'attendees' to update"},
                status=400
            )

        # ================= NOTIFICATIONS =================
        start_dt = booking.start
        start_str = (
            start_dt.astimezone(IST).strftime("%d/%m/%Y %I:%M %p")
            if start_dt else None
        )

        if "rescheduled" in updated_fields and "attendees_updated" in updated_fields:
            self._send_combined_notifications(booking, candidate, newly_added_attendees, start_str)

        elif "rescheduled" in updated_fields:
            self._send_reschedule_notifications(booking, candidate, start_str)

        elif "attendees_updated" in updated_fields:
            self._send_attendee_notifications(booking, candidate, newly_added_attendees)

        return Response({
            "detail": "Updated successfully",
            "updated": updated_fields
        })

    # ================= CANCEL =================
    def delete(self, request, candidate_id):
        booking = get_booking_by_candidate(candidate_id)
        if not booking:
            return Response({"detail": "Booking not found"}, status=404)

        candidate = JobApplication.objects.filter(id=candidate_id).first()

        if not cancel_meeting(booking.interviewer.email, booking.meeting_id):
            return Response({"detail": "Failed to cancel event"}, status=500)

        self._send_cancel_notifications(booking, candidate)

        candidate.inperson_link = None
        candidate.interview_link = None
        candidate.interview_scheduled_at = None
        candidate.interview_end_at = None
        candidate.interviewer_name = None
        candidate.save()

        booking.delete()

        return Response({"detail": "Cancelled successfully"})

    def _send_reschedule_notifications(self, booking, candidate, start_str):
        resume_attachment = get_resume_attachment(candidate)

        if booking.interview_type == "online":
            html_content = get_interviewer_email_template(
                action="rescheduled",
                candidate=candidate,
                interviewer=booking.interviewer,
                start_str=start_str,
                meeting_link=booking.meeting_link,
                feedback_link=candidate.feedback_link,
                resume_attachment_url=candidate.resume.url
            )
            send_email(
                subject=f"Interview Rescheduled - {candidate.candidate_name} ({candidate.job.mrf.designation.name})",
                text=f"Dear {booking.interviewer.name}, your interview scheduled has been rescheduled at {start_str}.\n Join: {booking.meeting_link} \n Give feedback: {candidate.feedback_link}",
                template=html_content,
                to=booking.interviewer.email,
                attachments=[resume_attachment] if resume_attachment else None
            )
            if booking.interviewer.phone:
                send_text(booking.interviewer.phone,f"Dear {booking.interviewer.name}, your interview scheduled has been rescheduled at {start_str}.\n Join: {booking.meeting_link} \n Give feedback: {candidate.feedback_link}")
                send_document(to=booking.interviewer.phone,text="Candidate Resume",file_url=candidate.resume.url,filename=f'{candidate.candidate_name}_Resume.pdf')

            send_email(
                subject=f"Interview Rescheduled – {candidate.job.mrf.designation.name} at Knowcraft Analytics",
                text=reschedule_online_interview_text.format(candidate=candidate,start_str=start_str),
                template=reschedule_online_interview_template.format(candidate=candidate,start_str=start_str),
                to=candidate.candidate_email
            )
            if candidate.candidate_phone:
                send_text(to=candidate.candidate_phone,text=reschedule_online_interview_text.format(candidate=candidate,start_str=start_str))

            attendees = booking.attendees.all()
            if attendees.exists():
                for extra in attendees:
                    send_email(
                        subject=f"Online Interview Rescheduled - {candidate.candidate_name}",
                        text=reschedule_online_interview_extra_text.format(candidate=candidate,booking=booking,start_str=start_str,extra=extra),
                        to=extra.email,
                        template=reschedule_online_interview_extra_template.format(candidate=candidate,booking=booking,start_str=start_str,extra=extra),
                        attachments=[resume_attachment] if resume_attachment else None
                    )
                    if extra.phone:
                        send_text(extra.phone,reschedule_online_interview_extra_text.format(candidate=candidate,booking=booking,start_str=start_str,extra=extra))
        else:
            location_str = booking.location.full_address if hasattr(booking, 'location') and hasattr(booking.location, 'full_address') else str(booking.location or "")
            maps_link = booking.location.google_maps_link if hasattr(booking,"location") and hasattr(booking.location, 'google_maps_link') else None

            send_email(
                subject=f"In-Person Interview Rescheduled - {candidate.candidate_name}",
                text= reschedule_offline_interview_text.format(booking=booking,candidate=candidate,start_str=start_str,maps_link=maps_link,location_str=location_str),
                to=booking.interviewer.email,
                template=reschedule_offline_interview_template.format(booking=booking,candidate=candidate,start_str=start_str,maps_link=maps_link,location_str=location_str),
                attachments=[resume_attachment] if resume_attachment else None
            )

            if booking.interviewer.phone:
                send_text(booking.interviewer.phone,f"Dear {booking.interviewer.name}, your interview scheduled has been rescheduled at {start_str}.\n Location: {location_str}\nGoole Map Link: {maps_link} \n Give feedback: {candidate.feedback_link}")
                send_document(to=booking.interviewer.phone,text="Candidate Resume",file_url=candidate.resume.url,filename=f'{candidate.candidate_name}_Resume.pdf')

            send_email(
                subject=f"In-Person Interview Rescheduled – {candidate.job.mrf.designation.name}",
                text=reschedule_offline_interview_candidate_text.format(candidate=candidate,start_str=start_str,maps_link=maps_link,location_str=location_str),
                to=candidate.candidate_email,
                template= reschedule_offline_interview_candidate_template.format(candidate=candidate,start_str=start_str,maps_link=maps_link,location_str=location_str)
            )

            if candidate.candidate_phone:
                send_text(candidate.candidate_phone,reschedule_offline_interview_candidate_text.format(candidate=candidate,start_str=start_str,maps_link=maps_link,location_str=location_str))
            
            attendees = booking.attendees.all()
            if attendees.exists():
                for extra in attendees:
                    send_email(
                        subject=f"In-Person Interview Rescheduled - {candidate.candidate_name}",
                        text=reschedule_offline_interview_extra_text.format(candidate=candidate,start_str=start_str,extra=extra,location_str=location_str,maps_link=maps_link),
                        to=extra.email,
                        template=reschedule_offline_interview_extra_template.format(candidate=candidate,start_str=start_str,extra=extra,location_str=location_str,maps_link=maps_link),
                        attachments=[resume_attachment] if resume_attachment else None
                    )
                    if extra.phone:
                        send_text(extra.phone,reschedule_offline_interview_extra_text.format(candidate=candidate,start_str=start_str,extra=extra,location_str=location_str,maps_link=maps_link))
        
    def _send_attendee_notifications(self,booking, candidate, attendees):
        resume_attachment = get_resume_attachment(candidate)

        if booking.interview_type == 'online':
            html_content = get_interviewer_email_template(
                action="attendees_updated",
                candidate=candidate,
                interviewer=booking.interviewer,
                start_str=candidate.interview_scheduled_at,
                meeting_link=booking.meeting_link,
                feedback_link=candidate.feedback_link,
                resume_attachment_url=candidate.resume.url
            )

            send_email(
                subject=f"Attendees Updated - {candidate.candidate_name} ({candidate.job.mrf.designation.name})",
                text=f"Dear {booking.interviewer.name}, your interview attendees has been updated for interview scheduled at {candidate.interview_scheduled_at}",
                template=html_content,
                to=booking.interviewer.email
            )
            if booking.interviewer.phone:
                send_text(booking.interviewer.phone,f"Dear {booking.interviewer.name}, your interview attendees has been updated for interview scheduled at {candidate.interview_scheduled_at}")
            
            for extra in attendees:
                send_email(
                    subject=f"You’ve been added to an Online Interview - {candidate.candidate_name}",
                    text=attendees_update_online_text.format(candidate=candidate,booking=booking,extra=extra),
                    to=extra.email,
                    template=attendees_update_online_template.format(candidate=candidate,booking=booking,extra=extra),
                    attachments=[resume_attachment] if resume_attachment else None
                )
                if extra.phone:
                    send_text(extra.phone,attendees_update_online_text.format(candidate=candidate,booking=booking,extra=extra))

        else:
            location_str = booking.location.full_address if hasattr(booking, 'location') and hasattr(booking.location, 'full_address') else str(booking.location or "")
            maps_link = booking.location.google_maps_link if hasattr(booking,"location") and hasattr(booking.location, 'google_maps_link') else None
            send_email(
                subject=f"In-Person Interview Updated (Attendees) - {candidate.candidate_name}",
                text=attendees_update_interviewer_text.format(booking=booking,candidate=candidate,location_str=location_str),
                to=booking.interviewer.email,
                template=attendees_update_interviewer_template.format(booking=booking,candidate=candidate,location_str=location_str,maps_link=maps_link)
            )
            if booking.interviewer.phone:
                send_text(booking.interviewer.phone,attendees_update_interviewer_text.format(booking=booking,candidate=candidate,location_str=location_str))
            
            for extra in attendees:            
                send_email(
                    subject=f"You’ve been added to an Interview - {candidate.candidate_name}",
                    text=attendees_update_text.format(candidate=candidate,extra=extra,location_str=location_str,maps_link=maps_link),
                    to=extra.email,
                    template=attendees_update_template.format(candidate=candidate,extra=extra,location_str=location_str,maps_link=maps_link),
                    attachments=[resume_attachment] if resume_attachment else None
                )
                if extra.phone:
                    send_text(extra.phone,attendees_update_text.format(candidate=candidate,extra=extra,location_str=location_str,maps_link=maps_link))

    def _send_combined_notifications(self,booking, candidate, attendees, start_str):
        self._send_attendee_notifications(booking, candidate, attendees)
        self._send_reschedule_notifications(booking, candidate, start_str)

    def _send_cancel_notifications(self, booking, candidate):
        if booking.interview_type == "online":
            html_content = get_interviewer_email_template(
                action="cancelled",
                candidate=candidate,
                interviewer=booking.interviewer,
                start_str=candidate.interview_scheduled_at,
                meeting_link="",
                feedback_link="",
                resume_attachment_url=""
            )
            send_email(
                subject=f"Interview Cancelled - {candidate.candidate_name} ({candidate.job.mrf.designation.name})",
                text=f"Dear {booking.interviewer.name}, your interview scheduled at {candidate.interview_scheduled_at} has been cancelled.",
                template=html_content,
                to=booking.interviewer.email
            )

            send_email(
                subject=f"Interview Cancelled – {candidate.job.mrf.designation.name} at Knowcraft Analytics",
                text=cancel_online_interview_text.format(candidate=candidate),
                template=cancel_online_interview_template.format(candidate=candidate),
                to=candidate.candidate_email
            )

            attendees = booking.attendees.all()
            if attendees.exists():
                for extra in attendees:
                    send_email(
                        subject=f"Interview Cancelled - {candidate.candidate_name}",
                        text=cancel_online_interview_extra_text.format(candidate=candidate,extra=extra),
                        to=extra.email,
                        template=cancel_online_interview_extra_template.format(candidate=candidate,extra=extra),
                    )
                    if extra.phone:
                        send_text(extra.phone,cancel_online_interview_extra_text.format(candidate=candidate,extra=extra))
            
        else:
            location_str = booking.location.full_address if hasattr(booking, 'location') and hasattr(booking.location, 'full_address') else str(booking.location or "")
            maps_link = booking.location.google_maps_link if hasattr(booking,"location") and hasattr(booking.location, 'google_maps_link') else None

            send_email(
                subject=f"In-Person Interview Cancelled - {candidate.candidate_name}",
                text=cancel_offline_interview_text.format(candidate=candidate,booking=booking,location_str=location_str,maps_link=maps_link),
                to=booking.interviewer.email,
                template=cancel_offline_interview_template.format(candidate=candidate,booking=booking,location_str=location_str,maps_link=maps_link)
            )

            send_email(
                subject=f"In-Person Interview Cancelled – {candidate.job.mrf.designation.name}",
                text=cancel_offline_interview_candidate_text.format(candidate=candidate,location_str=location_str),
                to=candidate.candidate_email,
                template=cancel_offline_interview_candidate_template.format(candidate=candidate,location_str=location_str)
            )

            attendees = booking.attendees.all()
            if attendees.exists():
                for extra in attendees:
                    send_email(
                        subject=f"In-Person Interview Cancelled - {candidate.candidate_name}",
                        text=cancel_offline_interview_extra_text.format(candidate=candidate,extra=extra,location_str=location_str,maps_link=maps_link),
                        to=extra.email,
                        template=cancel_offline_interview_extra_template.format(candidate=candidate,extra=extra,location_str=location_str,maps_link=maps_link),
                    )
                    if extra.phone:
                        send_text(extra.phone,cancel_offline_interview_extra_text.format(candidate=candidate,extra=extra,location_str=location_str,maps_link=maps_link))
        

        if booking.interviewer.phone:
            send_text(booking.interviewer.phone,f"Dear {booking.interviewer.name}, your interview scheduled at {candidate.interview_scheduled_at} has been cancelled.")
        
        if candidate.candidate_phone:
            send_text(to=candidate.candidate_phone,text=cancel_online_interview_text.format(candidate=candidate))

#teams grapgh api webhook (Not working)
from django.http import HttpResponse
from onboarding.utils.task_queue import TASK_QUEUE

class GraphWebhookView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        data = request.data

        for notification in data.get("value", []):
            # 🔥 Push to background queue
            TASK_QUEUE.enqueue(process_graph_event, notification)

        return Response({"status": "accepted"})

def renew_subscriptions():
    interviewers = Interviewer.objects.all()

    for interviewer in interviewers:
        TASK_QUEUE.enqueue(check_and_renew_subscription, interviewer.id)
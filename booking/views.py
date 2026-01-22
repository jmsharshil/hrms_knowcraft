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
from datetime import datetime, timedelta, date,timezone
import requests
from slots.graph import get_graph_token,fetch_meeting_recording,fetch_meeting_transcript
from jobs.serializers import JobApplicationSerializer
from jobs.models import JobApplication
from rest_framework import permissions


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

def create_teams_meeting(organizer_email, attendee_email, start_dt, end_dt, subject):
    token = get_graph_token()

    url = f"https://graph.microsoft.com/v1.0/users/{organizer_email}/events"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

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
        "attendees": [
            {
                "emailAddress": {"address": attendee_email},
                "type": "required"
            }
        ],
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
        slot_id = request.data.get("slot_id")
        interviewer_id = request.data.get("interviewer_id")

        if not slot_id:
            return Response({"detail": "slot_id is required"}, status=400)

        if not interviewer_id:
            return Response({"detail": "interviewer_id is required"}, status=400)

        # 3) Validate interviewer
        interviewer = Interviewer.objects.filter(id=interviewer_id).first()
        if not interviewer:
            return Response({"detail": "Invalid interviewer_id"}, status=400)

        # 4) Validate slot
        slot = Slot.objects.filter(id=slot_id).first()
        if not slot:
            return Response({"detail": "Invalid slot_id"}, status=400)

        # 5) Slot must belong to selected interviewer
        # (your Slot model is M2M: slot.interviewers)
        if not slot.interviewers.filter(id=interviewer.id).exists():
            return Response(
                {"detail": "This slot does not belong to selected interviewer"},
                status=400
            )

        # 6) Slot already booked?
        if slot.is_booked:
            return Response({"detail": "This slot is already booked"}, status=400)

        # 7) Create Teams meeting
        start_dt = slot.start
        end_dt = slot.end

        event = create_teams_meeting(
            interviewer.email,
            candidate.candidate_email,
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
            slot=slot,         # <-- IMPORTANT
            start=start_dt,
            end=end_dt
        )

        # Mark slot as booked
        slot.is_booked = True
        slot.save()

        # 9) Email notifications
        start_str = start_dt.astimezone(IST).strftime("%d/%m/%Y %I:%M %p")

        send_mail(
            "Interview Confirmed",
            f"Hello {candidate.candidate_name},\nYour interview with {interviewer.name} is confirmed at {start_str}.\nJoin link: {meeting_link}",
            settings.DEFAULT_FROM_EMAIL,
            [candidate.candidate_email],
        )
        round=None
        round_name = ''
        feedback_link_base = ""
        if candidate.status == 'shortlisted' or candidate.status == 'interview_pending_1':
            round = "hr_round"
            round_name = 'HR Round'
            feedback_link_base = "https://knowcrafthrms-djfkb4hseuf0adcy.centralindia-01.azurewebsites.net/api/slots/hr-feedback-form/"
        if candidate.status == 'interview_next_2' or candidate.status == 'interview_pending_2':
            round = "technical_round_1"
            round_name = 'Technical Round 1'
            feedback_link_base = "https://knowcrafthrms-djfkb4hseuf0adcy.centralindia-01.azurewebsites.net/api/slots/technical-feedback-form-one/"
        if candidate.status == 'interview_next_3' or candidate.status == 'interview_pending_3':
            round = "technical_round_2"
            round_name = 'Technical Round 2'
            feedback_link_base = "https://knowcrafthrms-djfkb4hseuf0adcy.centralindia-01.azurewebsites.net/api/slots/technical-feedback-form-two/"
        if candidate.status == 'interview_next_final' or candidate.status == 'interview_pending_final':
            round = "final_round"
            round_name = 'Final Round'
            feedback_link_base = "https://knowcrafthrms-djfkb4hseuf0adcy.centralindia-01.azurewebsites.net/api/slots/final-feedback-form/"
        feedback_link = f"{feedback_link_base}?interview_round={round}&job_application={candidate.id}"
        from onboarding.utils.sender import send_email
        send_email(
            subject="New Interview Scheduled",
            text=f"Hello {interviewer.name},\nYou have an interview with {candidate.candidate_name} at {start_str}.\nJoin link: {meeting_link}\n Feedback link: {feedback_link}",
            template=f"""
            <html>
            <body style="font-family: Arial; color:#333;">
                <h2>Interview Scheduled ({round_name})</h2>
                <p>Dear {interviewer.name},</p>
                <p>You have an interview with {candidate.candidate_name} at {start_str}.</p>
                <p>Join link: {meeting_link}</p>
                <p>Feedback link: {feedback_link}</p>
                <br>
                <p>Regards,
                <br>
                Recruitment System</p>
                </body>
            </html>""",
            to=interviewer.email,
        )

        from onboarding.utils.engine import automation_engine
        if candidate.status == 'shortlisted':
            automation_engine(candidate,candidate.status,'interview_pending_1')
        elif candidate.status == 'interview_next_2':
            automation_engine(candidate,candidate.status,'interview_pending_2')
        elif candidate.status == 'interview_next_3':
            automation_engine(candidate,candidate.status,'interview_pending_3')
        elif candidate.status == 'interview_next_final':
            automation_engine(candidate,candidate.status,'interview_pending_final')
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
